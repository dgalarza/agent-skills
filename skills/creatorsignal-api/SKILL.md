---
name: creatorsignal-api
description: >
  Interact with the CreatorSignal API: submit video ideas for AI validation,
  poll for scored Go/Refine/Kill verdicts, manage channels and webhooks, and
  check quota. Use this skill whenever the user mentions CreatorSignal API,
  video idea validation, cs_live_ tokens, validation polling, webhook endpoints,
  or programmatic idea submission.
allowed-tools: Bash(curl:*), Bash(jq:*), Bash(bash:*)
---

# CreatorSignal API

## Resource model

- **Channel** — a YouTube channel linked to your account. Ideas are submitted against a channel.
- **Idea** — a video idea with a title and category. Submitting an idea triggers AI validation.
- **Validation** — the AI research result for an idea. Contains a score (0-100), verdict (go/refine/kill), and a structured report.
- **Webhook Endpoint** — an HTTPS URL that receives validation events so you don't need to poll.

## Authentication

API keys use the format `cs_live_<prefix>_<secret>`. Pass as a Bearer token:

```bash
curl -s https://app.creatorsignal.io/api/v1/me \
  -H "Authorization: Bearer $CS_API_KEY"
```

Before any mutation, verify the key works:

```bash
curl -s -o /dev/null -w "%{http_code}" https://app.creatorsignal.io/api/v1/me \
  -H "Authorization: Bearer $CS_API_KEY"
# 200 = valid, 401 = invalid/revoked/expired
```

Keys are created from Settings > API Keys in your CreatorSignal account. The full key is shown once at creation — store it securely.

## Base URL

All endpoints live under `https://app.creatorsignal.io/api/v1/`.

## Quick operations

```bash
# Check quota
curl -s https://app.creatorsignal.io/api/v1/me \
  -H "Authorization: Bearer $CS_API_KEY" | jq '.quota'

# List channels
curl -s https://app.creatorsignal.io/api/v1/channels \
  -H "Authorization: Bearer $CS_API_KEY" | jq '.channels[] | {id, name}'

# Submit an idea
curl -s -X POST https://app.creatorsignal.io/api/v1/ideas \
  -H "Authorization: Bearer $CS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"idea": {"title": "Topic here", "category": "engineering", "channel_id": 1}}' | jq '.idea.id'

# Poll validation status
curl -s -w "\n%{http_code}" https://app.creatorsignal.io/api/v1/ideas/123/validation \
  -H "Authorization: Bearer $CS_API_KEY"

# List ideas filtered by status
curl -s "https://app.creatorsignal.io/api/v1/ideas?status=validated&per_page=10" \
  -H "Authorization: Bearer $CS_API_KEY" | jq '.ideas[] | {id, title, verdict: .validation.verdict, score: .validation.score}'
```

## Core workflow

The end-to-end flow for validating an idea:

1. **Verify auth** — `GET /api/v1/me` returns 200
2. **Check quota** — confirm `quota.remaining > 0`
3. **Get channels** — `GET /api/v1/channels` to find the target `channel_id`
4. **Submit idea** — `POST /api/v1/ideas` with title, category, channel_id
5. **Poll for results** — `GET /api/v1/ideas/{id}/validation`
   - `202` = in progress, sleep for `Retry-After` seconds (default 10)
   - `200` = done (check `validation.status` for `complete` or `failed`)
6. **Present results** — extract verdict, score, report summary, and recommendations

For polling, use the helper script: `bash scripts/poll-validation.sh <idea_id>`

## Error handling

| HTTP Status | Code | Meaning | Recovery |
|-------------|------|---------|----------|
| 401 | `unauthorized` | Missing or invalid API key | Check `$CS_API_KEY` is set and valid |
| 401 | `key_revoked` | Key was revoked | Create a new key in Settings > API Keys |
| 401 | `key_expired` | Key has expired | Create a new key in Settings > API Keys |
| 402 | `quota_exhausted` | No validations remaining | Wait for quota reset (rolling 30-day window) or upgrade plan |
| 404 | `not_found` | Resource doesn't exist or wrong user | Verify the ID and that it belongs to the authenticated user |
| 422 | `validation_error` | Invalid request body | Check `error.details` for field-level errors |
| 429 | `rate_limited` | Too many requests | Wait `Retry-After` seconds before retrying |

Error responses use two shapes:
- **401/404**: `{"error": {"message": "...", "status": 404}}`
- **402/422/429**: `{"error": {"code": "...", "message": "...", "details": {...}}}`

## API documentation

For full endpoint specs, request/response schemas, and parameter details, see the API docs at [app.creatorsignal.io/api](https://app.creatorsignal.io/api).

For additional reference within this skill:

| Topic | Reference |
|-------|-----------|
| Validation state machine and polling | [references/api-spec-guide.md](references/api-spec-guide.md) |
| Webhook setup, signing, event types | [references/webhook-patterns.md](references/webhook-patterns.md) |

## Execution rules

1. **Always verify auth before mutations** — call `GET /api/v1/me` and confirm 200 before creating ideas or webhook endpoints.
2. **Check quota before POST /ideas** — a 402 after the fact wastes a round-trip. Read `quota.remaining` first.
3. **Respect `Retry-After` headers** — both 202 (polling) and 429 (rate limit) include this header. Never use a fixed sleep.
4. **Cap polling at 12 attempts** — validations typically complete in 30-90 seconds. If still pending after ~2 minutes, report the status and suggest checking back.
5. **Never echo the full API key** — show only the format `cs_live_<prefix>_***` in output. The key is a secret.
6. **Use `jq` for JSON parsing** — never parse JSON with grep/sed/awk.
7. **Set Content-Type on POST/PATCH** — always include `-H "Content-Type: application/json"` with request bodies.

## Composition patterns

- **Quick check**: auth → quota → report remaining validations
- **Full validation**: auth → quota → channels → submit idea → poll → present verdict + recommendations
- **Webhook setup**: auth → create endpoint → store signing secret → test ping → verify delivery
- **Bulk review**: auth → list ideas (filtered by status=validated) → summarize verdicts and scores
- **Idea with webhook**: auth → quota → submit idea with `webhook_url` field → confirm 201
