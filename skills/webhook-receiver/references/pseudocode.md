# Pseudocode

Framework-neutral. Map each function to your stack's equivalent.

```text
# --- HTTP handler: verify, parse, persist, enqueue, ack -------------------

handle POST /webhooks/<provider>(request):
    raw = request.raw_body                       # bytes as received

    if not verify(request.headers, raw):         # step 1
        report("Unauthorized <provider> webhook")   # no body, no secret
        return 401

    try:
        events = parse(raw)                      # step 2: pure, no I/O
    except ParseError:
        log("unparseable <provider> webhook", raw)
        return 400

    if events is empty:
        return 202                               # nothing to do; not an error

    inbox.insert_or_ignore(events)               # step 3: UNIQUE(provider_id)
    queue.enqueue(ProcessJob, ids = [e.id for e in events])   # step 4
    return 202                                   # step 5

# A failure in insert or enqueue is allowed to surface as 5xx so the
# provider retries. Do not catch it and return 2xx.


# --- verification ---------------------------------------------------------

verify(headers, raw):
    secret = config.require("<PROVIDER>_WEBHOOK_SECRET")   # raise if absent
    sig = headers["X-Signature"]
    if sig is blank: return false
    expected = hex(hmac_sha256(secret, raw))
    return constant_time_equals(sig, expected)


# --- parse ----------------------------------------------------------------

parse(raw):
    body = json_parse(raw)
    items = body if is_list(body) else [body]
    return items.map(item -> {
        provider_id: item.id,        # stable provider ID
        event_type:  item.type,
        payload:     item,
    })


# --- worker: load, dispatch, guard, act -----------------------------------

HANDLERS = {
    "invoice.paid":    InvoicePaid,
    "invoice.voided":  InvoiceVoided,
}

ProcessJob.perform(ids):
    for event in inbox.where(provider_id in ids):         # step 6: reload
        handler = HANDLERS[event.event_type]              # step 7
        if handler is none:
            continue                                      # unknown type: ignore
        handler.call(event)

InvoicePaid.call(event):
    invoice = invoices.find(event.payload.invoice_id)
    if invoice is none or invoice.state in (PAID, VOID):  # step 8: guard
        return                                            # also makes re-run a no-op
    current = provider.fetch_invoice(invoice.provider_id) # re-fetch, ignore ordering
    transaction:                                          # step 9: idempotent act
        invoice.update(state: current.state, paid_at: current.paid_at)
        mark_processed(event)
```
