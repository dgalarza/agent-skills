# Webhook Patterns

Webhooks deliver validation results in real time, eliminating the need for polling. CreatorSignal signs every delivery with HMAC-SHA256 so consumers can verify authenticity.

## Creating a webhook endpoint

```bash
curl -s -X POST https://app.creatorsignal.io/api/v1/webhook_endpoints \
  -H "Authorization: Bearer $CS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_endpoint": {
      "url": "https://example.com/webhooks/creatorsignal",
      "description": "Production webhook"
    }
  }' | jq '.'
```

The response includes `signing_secret` — **shown only once at creation time**. Store it securely:

```json
{
  "webhook_endpoint": {
    "id": 301,
    "url": "https://example.com/webhooks/creatorsignal",
    "description": "Production webhook",
    "enabled": true,
    "consecutive_failures": 0,
    "disabled_at": null,
    "signing_secret": "whsec_abc123def456...",
    "created_at": "2026-03-15T09:00:00Z"
  }
}
```

Maximum 10 endpoints per account. URLs must be HTTPS (no private IPs, no localhost).

## Event types

| Event | When | Payload includes |
|-------|------|-----------------|
| `validation.completed` | Validation finishes successfully | idea summary, verdict, score, report URL |
| `validation.failed` | Validation encounters an error | idea summary, error message |
| `ping` | Test ping from dashboard or API | empty data |

## Webhook payload structure

```json
{
  "id": "evt_abc123def456",
  "type": "validation.completed",
  "created_at": "2026-04-12T14:31:15Z",
  "data": {
    "idea": {
      "id": 123,
      "title": "Building AI Agents with Claude Code",
      "category": "AI Engineering",
      "status": "validated"
    },
    "validation": {
      "id": 456,
      "status": "complete",
      "score": 78.5,
      "verdict": "go",
      "started_at": "2026-04-12T14:30:00Z",
      "completed_at": "2026-04-12T14:31:15Z"
    }
  }
}
```

## Signature verification

Every delivery includes these headers:

```
X-CreatorSignal-Signature: sha256=<hex_digest>
X-CreatorSignal-Event: validation.completed
X-CreatorSignal-Delivery: evt_abc123def456
X-CreatorSignal-Timestamp: 1712930475
```

The signature is computed as `HMAC-SHA256(signing_secret, "#{timestamp}.#{body}")`.

### Verifying with bash

```bash
#!/usr/bin/env bash
# Verify a CreatorSignal webhook signature
# Usage: verify-signature.sh <signing_secret> <timestamp> <body>

SIGNING_SECRET="$1"
TIMESTAMP="$2"
BODY="$3"

EXPECTED=$(echo -n "${TIMESTAMP}.${BODY}" | openssl dgst -sha256 -hmac "$SIGNING_SECRET" | awk '{print $NF}')
echo "sha256=${EXPECTED}"
```

Compare the output against the `X-CreatorSignal-Signature` header value. Use constant-time comparison in production to prevent timing attacks.

### Replay protection

The timestamp is included in the signed payload. Consumers should reject deliveries where the timestamp is more than 5 minutes old:

```bash
CURRENT=$(date +%s)
WEBHOOK_TS="1712930475"  # from X-CreatorSignal-Timestamp header
DIFF=$(( CURRENT - WEBHOOK_TS ))
if [ "$DIFF" -gt 300 ]; then
  echo "Webhook too old — possible replay attack" >&2
  exit 1
fi
```

## Testing a webhook endpoint

Send a test `ping` event to verify your endpoint is reachable and correctly verifying signatures:

```bash
curl -s -X POST https://app.creatorsignal.io/api/v1/webhook_endpoints/301/test \
  -H "Authorization: Bearer $CS_API_KEY" | jq '.'
```

Response:

```json
{
  "message": "Test ping queued",
  "delivery_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

## Auto-disable behavior

If an endpoint fails 5 consecutive deliveries (across all events), it is automatically disabled:
- `enabled` set to `false`
- `disabled_at` set to the time of auto-disable
- User notified via email

The `consecutive_failures` counter resets to 0 on any successful delivery.

### Re-enabling a disabled endpoint

```bash
curl -s -X PATCH https://app.creatorsignal.io/api/v1/webhook_endpoints/301 \
  -H "Authorization: Bearer $CS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"webhook_endpoint": {"enabled": true}}' | jq '.'
```

Re-enabling resets the consecutive failure counter.

## Per-idea webhook URL

Instead of (or in addition to) registered endpoints, pass a `webhook_url` when submitting an idea:

```bash
curl -s -X POST https://app.creatorsignal.io/api/v1/ideas \
  -H "Authorization: Bearer $CS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "idea": {
      "title": "Topic here",
      "category": "engineering",
      "channel_id": 1,
      "webhook_url": "https://example.com/hooks/one-off"
    }
  }'
```

The per-idea URL receives the validation result **in addition to** any registered webhook endpoints. It uses the same HMAC signing. The URL must be HTTPS with no private IPs.

## Delivery and retry schedule

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 1 minute |
| 3 | 5 minutes |
| 4 | 30 minutes |
| 5 | 2 hours (final) |

A delivery is considered successful on any HTTP 2xx response within 10 seconds.
