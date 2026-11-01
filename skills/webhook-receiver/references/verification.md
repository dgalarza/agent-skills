# Verification

Authenticate every request before parsing or storing it. Providers use one of
a few schemes. Identify which one before writing code.

## Schemes

| Scheme | How it works | Notes |
| --- | --- | --- |
| HMAC of raw body | Provider signs body with a shared secret; sends digest in a header | Most common. Compare digests in constant time |
| HMAC of body + timestamp | Signature covers `timestamp.body`; timestamp in a header | Lets you reject replays older than a tolerance (typically 5 min) |
| HMAC of URL + sorted params | Signature covers the full URL and form params (e.g. Twilio) | Use the provider SDK validator; URL must match what the provider called, including scheme and host behind proxies |
| Basic auth | Static username and password in the `Authorization` header | Weak alone. Combine with a signature when the provider offers both |
| Shared secret in body or query | Provider echoes a secret you configured | Weakest. Secret appears in URLs and logs. Use only when nothing else exists, and still compare in constant time |
| Asymmetric signature | Provider signs with a private key; you verify with their published public key | Rotate by fetching keys; cache them |
| IP allowlist | Only provider IPs may call | Never sufficient alone; ranges change and can be spoofed behind misconfigured proxies |

Prefer layering: a signature plus a second factor (basic auth, IP allowlist)
when the provider supports it. When a provider sends both a Basic auth header
and an HMAC signature, require both and reject if either fails.

## Rules

- **Sign the raw bytes.** Read the body as received, before any JSON parsing or
  framework param handling. Re-serialized JSON differs byte for byte.
- **Check what the provider actually signs.** Some sign the whole body. Others
  sign only part of it, such as the first event in a batch. Read the
  provider docs, and comment any quirk in the code.
- **Constant-time compare.** Use `secure_compare`, `hmac.compare_digest`,
  `crypto.timingSafeEqual`, `subtle.ConstantTimeCompare`, or equivalent. Never `==`.
- **Fail closed.** Missing header means reject. Missing secret configuration
  means raise at boot or on use, never validate against an empty string.
  `ENV.fetch` without a default is the right shape.
- **Reject early.** Verification is the first step. An unverified request must
  not touch the database or the queue.
- **Alert on failures.** A rejected webhook is a signal: misconfigured secret,
  rotated key, or probing. Report it (error tracker, metric), but do not log
  the body or the secret.
- **Replay protection.** When a timestamp is signed, reject requests outside a
  tolerance window. Without one, the event ID unique constraint limits replays
  to no-ops.
- **Secret rotation.** Support two active secrets during rotation if the
  provider allows overlap. Verify against each.

## Pitfalls

- Verifying against `params` or a parsed object instead of raw bytes.
- Middleware that consumes or normalizes the body before your handler sees it.
- Proxy or CDN that rewrites scheme or host, breaking URL-based signatures.
- Framework CSRF protection rejecting the request. Webhooks must skip CSRF, and
  therefore must carry their own authentication.
- Session or user authentication also rejecting the request. Skip it for this
  endpoint only and make the skip explicit.
- Rate limiting by IP throttling the provider. Allowlist verified webhook paths.
  Only allowlist by header presence if verification still runs afterward.
