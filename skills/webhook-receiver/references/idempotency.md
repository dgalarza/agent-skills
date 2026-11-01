# Idempotency and ordering

Assume every event can arrive more than once, and in any order. Idempotency
has two layers, and both are needed.

## Layer 1: dedupe at ingest (inbox table)

Store each event in a table with a **unique constraint on the provider's event
ID**. The database is the arbiter. Do not check-then-insert in application code.

```
webhook_events
  id            primary key
  provider_id   text, NOT NULL, UNIQUE      -- provider's event/message/token ID
  event_type    text, NOT NULL, indexed
  payload       json(b), NOT NULL           -- full original event
  received_at   timestamp, NOT NULL
  processed_at  timestamp, NULL             -- optional
  attempts      int, default 0              -- optional
```

- **Insert-or-ignore** (`INSERT ... ON CONFLICT DO NOTHING`, `INSERT IGNORE`,
  `insertMany` with ordered false). A duplicate is a no-op and the request still
  succeeds.
- Without insert-or-ignore, a duplicate raises, the provider sees a 5xx, and it
  retries indefinitely.
- If the provider has no stable event ID, derive one: hash of the raw payload,
  or a composite of resource ID, event type, and provider timestamp. State the
  derivation in a comment.
- Namespace the ID by provider (or use one table per provider) so IDs from
  different sources cannot collide.
- Batches: insert all events in one statement, enqueue one job with all IDs.
  Already-seen events in the batch are skipped at insert but their IDs are
  still safe to enqueue, because the handler is idempotent (layer 2).

The inbox table also gives you an audit log, replay (re-enqueue by ID or type),
and debugging evidence that survives handler bugs.

## Layer 2: idempotent handlers

The queue is at-least-once too. A job can run twice after a crash, a timeout,
or a retry. Write handlers so the second run changes nothing.

| Technique | Use when |
| --- | --- |
| Upsert on a natural key | Creating a record derived from the event (`find_or_initialize_by(token:)`, `ON CONFLICT DO UPDATE`) |
| Set, don't increment | Write the resulting state, not a delta. `status = 'active'`, not `count += 1` |
| State-transition check | Only move forward from allowed states; no-op otherwise |
| Processed marker | Record `processed_at` (or a side-effect idempotency key) in the same transaction as the effect |
| Idempotency key on outbound calls | Pass the event ID as the key to any provider you call from the handler |
| Transaction around effect + marker | Prevents the effect committing without the marker, or the reverse |

Side effects that cannot be made idempotent (sending email, charging a card)
need an explicit dedupe record keyed by event ID, checked and written in one
transaction with the decision to send.

## Ordering

Providers rarely guarantee order, and retries reorder further. Do not assume
`updated` arrives after `created`.

- **Prefer thin handling.** Treat the event as a notification. Re-fetch the
  current resource from the provider API in the worker, and reconcile against
  that. Ordering stops mattering because you always read latest state.
  (This is the reason handlers run in the worker, where outbound calls are allowed.)
- **Compare timestamps or versions.** If the payload carries a version or
  occurred-at, ignore events older than the state you already hold.
- **Make transitions monotonic.** Define legal state transitions and refuse
  backward moves.
- **Handle out-of-order creation.** An `updated` event for a record you have not
  seen yet should fetch it, or retry later, not fail permanently.

## Failure and retry in the worker

- Let handler exceptions propagate so the job system retries with backoff.
- Retries are safe only because of layer 2.
- Cap retries, then dead-letter and alert. Do not drop silently.
- Monitor unprocessed rows (`processed_at IS NULL` older than N minutes) if you
  track processing state.

## Replay

Because payloads are stored, a fixed bug can be replayed: select rows by type
or time range and re-enqueue their IDs. This only works if handlers are
idempotent, so test replay explicitly.
