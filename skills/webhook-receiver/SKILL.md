---
name: webhook-receiver
description: Design, implement, or review inbound webhook handling that is verified, idempotent, and asynchronous. Use when adding a webhook endpoint or callback receiver for any provider (payments, messaging, analytics, CMS, CRM), when a provider is retrying or timing out, when webhook processing is slow or loses events, or when auditing an existing webhook handler. Language and framework agnostic, with a Rails reference.
---

# Webhook Receiver

A webhook endpoint does four things and nothing else: **verify, persist, enqueue,
acknowledge.** All business logic runs later, in a job, against the stored record.

The provider is an untrusted caller that retries on any non-2xx or timeout, may
deliver the same event more than once, and may deliver events out of order. The
design below is what makes that safe.

## The pipeline

```
request ──► 1 verify ──► 2 parse ──► 3 persist (dedupe) ──► 4 enqueue ──► 5 ack 2xx
                │                                                              │
            reject 401                                           later, in a worker:
                                                       6 load ► 7 dispatch ► 8 guard ► 9 act
```

Steps 1–5 happen in the request. Steps 6–9 happen in the worker.

### In the request

1. **Verify before reading anything.** Authenticate against the *raw* request body
   and headers. Reject with 401/403 and alert on failure. See
   `references/verification.md` for schemes and pitfalls.
2. **Parse into normalized records.** One row per event, with a stable provider
   event ID, an event type, and the full original payload. Reject malformed
   bodies. Keep parsing free of side effects and external calls.
3. **Persist before anything else.** Insert the records into an inbox table with a
   unique constraint on the provider event ID. This is the idempotency gate and
   the durable log. The insert must tolerate duplicates (insert-or-ignore), not
   crash on them.
4. **Enqueue a job carrying IDs, not payloads.** Pass the event IDs. The worker
   reloads from the database, so the stored row is the source of truth and the
   job payload stays small.
5. **Acknowledge fast.** Return 202 (or 200) as soon as the record is stored and
   the job is enqueued. Target well under the provider's timeout, typically
   under a second. No provider API calls, no business logic, no fan-out inline.

### In the worker

6. **Load by ID** from the inbox table. Never trust data carried in the job.
7. **Dispatch through a registry** mapping event type to handler. Unknown types
   are ignored, not errors. New event types are a one-line addition.
8. **Guard before acting.** Check the event is still relevant: the target
   record exists, is in a state that allows the change, and is not a test or
   system actor you intend to skip. Re-fetch current state from the provider
   when ordering matters (see `references/idempotency.md`).
9. **Act idempotently.** The handler must be safe to run twice. Use upserts,
   `find_or_create` on a natural key, or state-transition checks. Assume at-least-once delivery
   *and* at-least-once job execution.

## Non-negotiable rules

| Rule | Why |
| --- | --- |
| Verify on the raw body, with constant-time comparison | Parsed-then-reserialized JSON changes bytes; `==` leaks timing |
| Fail closed if the secret is missing | A blank secret must not validate a blank signature |
| Never put the secret in a query string or log it | URLs and logs leak |
| Unique constraint on the provider event ID | Application-level "check then insert" races |
| Duplicates are a success, not an error | A 5xx on a duplicate makes the provider retry forever |
| 2xx only after the event is durably stored and enqueued | Otherwise a crash loses the event with no retry |
| No inline business logic or outbound calls | Slow responses trigger retries, which create duplicates |
| Jobs take IDs and reload | Stale or oversized payloads in the queue |
| Handlers tolerate re-run and reordering | Queues are at-least-once; providers do not guarantee order |
| Unknown event types are ignored and logged | Providers add event types without notice |

## Response codes

| Situation | Respond | Provider behavior |
| --- | --- | --- |
| Verified, stored, enqueued (including duplicate) | 202 / 200 | Stops retrying |
| Bad or missing signature | 401 / 403 | Usually stops or alerts; alert on your side |
| Malformed body | 400 | Provider stops retrying; log the raw body |
| Storage or queue unavailable | 5xx | Provider retries. This is the one case where retry is desired |

Do not swallow a persistence failure and return 2xx. Do not return 5xx for a
handler bug, because that belongs in the worker where it retries with backoff
and can alert without involving the provider.

## Workflow

1. **Read the provider's docs** for: signature scheme, retry policy, timeout,
   event ID field, ordering guarantees, batching, and whether payloads are thin
   (ID only) or fat (full object).
2. **Inspect the codebase** for an existing receiver and copy its conventions
   (inbox table naming, queue, error reporting, auth-skipping idiom). Prefer
   extending an existing pattern to introducing a new one.
3. **Design the inbox table**: provider event ID (unique), event type, payload
   (JSON), received-at, and optionally processed-at, status, and attempt count.
4. **Implement verification** against the raw body, then parse, persist, enqueue, ack.
5. **Write the handler registry and one handler**, with the guard and an
   idempotent action.
6. **Test the failure modes**, not just the happy path (checklist below).
7. **Add operational hooks**: alert on signature failures, on queue depth, and on
   events stuck unprocessed.

## Test checklist

- Valid signature is accepted and returns 2xx; the row exists and the job is enqueued.
- Missing, wrong, and truncated signatures return 401 and write nothing.
- Missing secret configuration fails closed.
- The same payload delivered twice yields one row and one effect, and still returns 2xx.
- A batch containing one already-seen and one new event stores only the new one
  and processes both safely.
- Malformed JSON returns 400 and writes nothing.
- Unknown event type is stored (or ignored) and does not raise.
- Running the job twice produces the same end state.
- Out-of-order delivery (later event first) does not corrupt state.
- The request does no outbound HTTP (assert in test, or inspect).

## Review checklist

When auditing an existing receiver, flag each of these:

- Business logic or API calls in the controller or request thread.
- Verification that reads parsed params instead of the raw body.
- Non-constant-time comparison, or a secret in the URL or body.
- No unique index on the event ID, or a check-then-insert race.
- A rescue-all that returns 2xx after a failed write (silent event loss).
- A duplicate that raises (500) instead of being ignored.
- Job payload carrying the event body instead of IDs.
- Handler that cannot safely run twice.
- No inbox table, so events cannot be replayed or audited.
- Rate limiting that can throttle the provider's legitimate retries
  (allowlist verified webhook paths instead of by IP alone).
- No alerting on verification failures.

## References

- `references/verification.md`: signature schemes, raw-body handling, replay protection, pitfalls.
- `references/idempotency.md`: inbox table design, dedupe, handler idempotency, ordering, replay.
- `references/rails.md`: complete Rails reference.
- `references/pseudocode.md`: the same pattern in framework-neutral pseudocode.
