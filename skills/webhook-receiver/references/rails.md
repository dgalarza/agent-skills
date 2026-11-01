# Rails reference

A complete receiver in a Rails app. Replace `Acme` with the provider.
Assumes Rails 6+, ActiveJob, and PostgreSQL.

## Layout

```
config/routes.rb                              post "/acme/callbacks"
app/controllers/acme/callbacks_controller.rb  verify, persist, enqueue, ack
app/models/acme/webhook/request.rb            facade: valid? / parse
app/models/acme/webhook/request/authenticator.rb
app/models/acme/webhook/request/parser.rb
app/models/acme_event.rb                      inbox record
app/models/acme_event/create.rb               insert + enqueue (form object)
app/jobs/acme_jobs/process_webhook_job.rb     load by ID, dispatch
app/models/acme_event/process_webhook.rb      registry: event_type => handler
app/models/acme_event/process_webhook/*.rb    one handler per event type
```

Keeping verification, parsing, persistence, and dispatch in separate small
objects makes each testable without HTTP.

## Migration

```ruby
create_table :acme_events do |t|
  t.string   :event_type, null: false
  t.string   :token,      null: false          # provider's event ID
  t.jsonb    :data,       null: false
  t.datetime :created_at, null: false, default: -> { "CURRENT_TIMESTAMP" }
  t.index :event_type
  t.index :token, unique: true                 # the idempotency gate
end
```

## Controller

```ruby
module Acme
  class CallbacksController < ApplicationController
    skip_before_action :verify_authenticity_token   # provider has no CSRF token
    skip_before_action :require_login               # provider has no session
    skip_after_action  :verify_authorized           # Pundit-style apps only
    before_action :verify_webhook

    def create
      parsed = Acme::Webhook::Request.parse(request)

      AcmeEvent::Create.new(
        events: parsed.events,
        event_tokens: parsed.event_tokens
      ).save

      head :accepted
    end

    private

    def verify_webhook
      return if Acme::Webhook::Request.valid?(request)

      Sentry.capture_message("Unauthorized Acme webhook attempt")
      head :unauthorized
    end
  end
end
```

Notes:

- Skip each default guard explicitly and only here. The skips are the visible
  record that this endpoint authenticates differently.
- If the app has a custom auth layer (tokens, API keys), disable it for this
  controller too, otherwise it will reject provider calls.
- A lighter option is `ActionController::API` as the base class, which has no
  CSRF or session machinery to skip.

## Authenticator

```ruby
module Acme
  module Webhook
    class Request
      class Authenticator
        def self.validate(http_request) = new(http_request).validate

        def initialize(http_request)
          @http_request = http_request
        end

        def validate
          valid_signature?
        end

        private

        attr_reader :http_request

        def valid_signature?
          return false if signature.blank?

          ActiveSupport::SecurityUtils.secure_compare(
            signature,
            computed_signature
          )
        end

        def signature
          http_request.headers["X-Acme-Signature"]
        end

        def computed_signature
          OpenSSL::HMAC.hexdigest(
            "sha256",
            ENV.fetch("ACME_WEBHOOK_SECRET"),   # raises if unset: fails closed
            http_request.raw_post               # raw bytes, not params
          )
        end
      end
    end
  end
end
```

Layering a second factor: when the provider also sends Basic auth, compare the
`Authorization` header against a computed `Basic` value and return
`valid_auth_header? && valid_signature?`.

Use the digest the provider specifies. Prefer SHA-256 over SHA-1 when the
provider offers a choice.

## Parser

```ruby
module Acme
  module Webhook
    class Request
      class Parser
        attr_reader :events, :event_tokens

        def initialize(raw_content)
          @raw_content = raw_content
          @events = []
          @event_tokens = []
        end

        def parse
          items.each do |item|
            @event_tokens << item[:id]
            @events << { event_type: item[:type], token: item[:id], data: item }
          end
        end

        private

        def items
          body = JSON.parse(@raw_content, symbolize_names: true)
          body.is_a?(Array) ? body : [body]
        end
      end
    end
  end
end
```

Some providers group payloads by resource type (`{ cards: [...], transactions: [...] }`).
For those, iterate the keys and flatten. Normalize whatever the provider sends
into the same row shape: `event_type`, `token`, `data`.

## Persist and enqueue (form object)

```ruby
class AcmeEvent
  class Create
    include ActiveModel::Model

    attr_accessor :events, :event_tokens

    validates :events, presence: true
    validates :event_tokens, presence: true

    def save
      return unless valid?

      AcmeEvent.insert_all(events)                       # skips duplicates
      AcmeJobs::ProcessWebhookJob.perform_later(event_tokens)
    end
  end
end
```

Important details:

- **`insert_all` vs `insert_all!`.** `insert_all` issues `ON CONFLICT DO NOTHING`,
  so a re-delivered event is silently skipped and the request still succeeds.
  `insert_all!` raises on a duplicate, which turns provider retries into 500s.
  Use `insert_all` unless you want the raise. Pass `unique_by:` if the table has
  more than one unique index and only one should be ignored.
- `insert_all` skips validations and callbacks. The `valid?` check above covers
  the batch, and the column `null: false` constraints cover each row.
- The job receives tokens, not payloads. Tokens for already-stored events are
  enqueued again on a duplicate delivery. That is intentional, and it relies on
  handlers being idempotent. If you track `processed_at`, filter those out here.
- `perform_later` after the insert: if the enqueue fails the request errors
  (5xx) and the provider retries, and the retry's insert is a no-op while the
  enqueue runs again. With a database-backed queue (Solid Queue, GoodJob), put
  both inside one transaction for atomicity.

## Job and dispatch registry

```ruby
module AcmeJobs
  class ProcessWebhookJob < ApplicationJob
    queue_as :default

    def perform(event_tokens)
      AcmeEvent::ProcessWebhook.call(event_tokens)
    end
  end
end

class AcmeEvent
  class ProcessWebhook
    HANDLERS = {
      "invoice.paid"   => InvoicePaid,
      "invoice.voided" => InvoiceVoided,
    }.freeze

    def self.call(event_tokens) = new(event_tokens).call

    def initialize(event_tokens)
      @event_tokens = event_tokens
    end

    def call
      AcmeEvent.where(event_type: HANDLERS.keys, token: @event_tokens)
               .find_each { |event| HANDLERS.fetch(event.event_type).schedule(event) }
    end
  end
end
```

The `where(event_type: HANDLERS.keys)` filter is how unknown types are ignored:
they stay in the inbox but never dispatch.

To fan out one more level, `ProcessWebhook` enqueues a per-type job
(`ProcessCardEventJob`, `ProcessTransactionEventJob`, ...) for each event via
`Handler.schedule(event)`. That isolates failures: a bad transaction event does
not block card events in the same batch, and each retries on its own. Use it
when batches mix event types or handlers are slow. For a single fast handler,
call it directly.

## Handler base class: guard, then act

```ruby
class AcmeEvent
  class ProcessWebhook
    class BaseEvent
      def self.schedule(event)
        self::JOB_KLASS.perform_later(event)     # GlobalID serializes the record
      end

      def initialize(event)
        @event = event
      end

      private

      attr_reader :event

      def payload
        @payload ||= self.class::EVENT_KLASS.load(event.data)   # value object
      end

      def processable?
        return false if payload.account_id.blank?
        return false if payload.account_id == ENV.fetch("ACME_SYSTEM_ACCOUNT")

        Account.exists?(provider_id: payload.account_id)
      end
    end

    class InvoicePaid < BaseEvent
      JOB_KLASS = AcmeJobs::ProcessInvoicePaidJob
      EVENT_KLASS = Acme::Webhook::Event::Invoice

      def process
        return unless processable?

        invoice = Invoice.find_or_initialize_by(provider_id: payload.invoice_id)
        invoice.update!(state: payload.state, paid_at: payload.occurred_at)   # set, not increment
      end
    end
  end
end
```

Guards in the handler (`processable?`) are authorization for the *effect*:
the event is verified as coming from the provider, but may still refer to an
account you do not manage, a system or test actor, or a record that no longer
exists. Skip those quietly.

`find_or_initialize_by` plus `update!` with absolute values makes a re-run a
no-op. See `idempotency.md` for the other techniques.

Handlers can also gate jobs behind a feature flag in the job base class.
That is useful for dark-launching a receiver, but keep storing events while
the flag is off so nothing is lost.

## Rate limiting (Rack::Attack)

Webhooks arrive in bursts from a handful of IPs and will trip a per-IP throttle.
Safelist the verified path, and require the signature header so the safelist
is not a blanket bypass:

```ruby
Rack::Attack.safelist("acme webhooks") do |req|
  req.has_header?("HTTP_X_ACME_SIGNATURE") &&
    req.path.start_with?("/acme/callbacks")
end
```

The safelist only skips throttling. Verification still runs in the controller.

## Common mistakes

- **Rescue-all in the controller.** A `rescue_from StandardError` that logs and
  reports, then returns without rendering, yields a success-class response
  (204) after a failed write. The provider does not retry and the event is
  lost. Let persistence errors surface as 5xx, or render an explicit 5xx after
  reporting.
- **`insert_all!` for the inbox insert.** A re-delivered batch raises and
  returns 500. Use `insert_all`.
- **Shared secret in the request body compared with `==`.** Compare in
  constant time, and prefer a header signature.
- **No stored raw event.** Without an inbox table, events cannot be replayed
  or audited. Add one.

## Specs to write

- Request spec: valid signature returns 202 and creates the row; invalid
  returns 401 and creates nothing; same payload twice creates one row and
  returns 202 both times; malformed JSON returns 400.
- Authenticator spec: missing header, wrong signature, missing secret env.
- Parser spec: single object, array, empty body, unknown shapes.
- `Create` spec: duplicate tokens are skipped; job enqueued with all tokens.
- Handler spec: guard cases (blank account, system account, unknown account);
  calling `process` twice leaves the same state.
- Job spec: unknown event types are ignored.
