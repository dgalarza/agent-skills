# API Spec Guide

Supplementary details on validation states, pagination, and rate limiting. For full endpoint specs, see the [hosted API docs](https://app.creatorsignal.io/api).

## Validation status state machine

```
pending → researching → synthesizing → complete
                                     → failed
```

- `pending` — validation enqueued, research not started
- `researching` — searching YouTube, Reddit, X, and HN
- `synthesizing` — research complete, generating the report
- `complete` — final report ready with score and verdict
- `failed` — research encountered an error (see `error_message`)

The polling endpoint (`GET /api/v1/ideas/{idea_id}/validation`) returns:
- **202 Accepted** with `Retry-After: 10` while status is `pending`, `researching`, or `synthesizing`
- **200 OK** when status is `complete` or `failed`

## Score and verdict

- **Score**: 0-100 (float), null while in progress
- **Verdict**: `go` (strong idea), `refine` (promising but needs adjustment), `kill` (unlikely to perform) — null while in progress

## Pagination

List endpoints support `page` (default 1) and `per_page` (default 25, max 100) query parameters. Responses include a `meta` object with `page`, `per_page`, `total_count`, and `total_pages`.

## Rate limiting

All responses include `X-RateLimit-Limit`. When exceeded, the API returns `429 Too Many Requests` with a `Retry-After` header.
