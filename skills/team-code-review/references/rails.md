# Opinionated Rails Review Profile

Use this profile when reviewing a Rails application. These are Damian Galarza's preferred Rails defaults, not framework-neutral rules. Apply them to the changed behavior and its execution paths. Explicit repository instructions and documented architectural decisions take precedence, but do not discard a concern merely because the repository has not documented it.

Return a finding only when the diff introduces or materially exposes a concrete defect, operational risk, or maintenance cost. A preference that does not affect the change is not a finding.

## Rails shape and boundaries

- Follow Rails conventions before adding custom infrastructure. Prefer the framework's lifecycle, naming, and composition mechanisms unless the code demonstrates a reason to depart from them.
- Keep controllers, jobs, mailers, and callbacks as delivery or lifecycle boundaries. Move multi-step business workflows into explicit collaborators when doing so clarifies transaction ownership, reuse, failure handling, or tests; do not demand a service object by name.
- Give each class or module its own file. Namespace-only wrapper chains may share a file, but nested implementation classes hide dependencies and fight Zeitwerk conventions.
- Check that file paths, constant names, autoload/eager-load configuration, and inflection rules agree. Development autoloading must not conceal a production eager-load failure.
- Prefer explicit collaborators at I/O boundaries. HTTP, storage, email, payment, and other external integrations should centralize request construction, authentication, serialization, response handling, timeouts, and error translation when the change would otherwise duplicate or scatter them.
- Prefer reader methods and normal method dispatch over direct instance-variable reads outside the reader itself. This preserves an interception point for validation, memoization, typing, and tests.

## Persistence and domain state

- Enforce durable invariants in the database as well as the model where concurrency or non-Rails writers can violate them. Inspect nullability, foreign keys, unique and check constraints, indexes, and the behavior of bulk APIs that skip validations and callbacks.
- Trace transaction boundaries across every write and side effect. Avoid external I/O inside a database transaction; ensure jobs and notifications that require committed data are dispatched after commit.
- Treat callbacks as local invariant maintenance, not as a hidden workflow engine. Check ordering, recursion, skipped-callback APIs, rollback behavior, and whether the initiating code can understand the side effects.
- Prefer timestamp-backed state over boolean columns when the domain benefits from knowing when a transition happened. Check predicate semantics, scopes, backfills, and whether repeated transitions are meaningful before accepting a boolean.
- Inspect query cardinality, eager loading, counter caches, pagination, and tenant scoping. Watch for N+1 queries, unbounded relations, per-row writes, unnecessary object allocation, and calculations that belong in SQL.
- Check time handling for application-zone versus UTC semantics, date-boundary behavior, daylight-saving transitions, and comparisons against database timestamps.

## Migrations and deploy safety

- Review migrations as production operations, not only schema transformations. Check table size, locks, statement duration, index creation, constraint validation, and whether a backfill should be separated from the schema change.
- Preserve compatibility across rolling deploys. Old and new application versions may run against the same schema; destructive renames, removals, type changes, and new required values usually need expand-and-contract sequencing.
- Prefer reversible migrations, but do not confuse a syntactic `down` path with safe recovery. State what happens to data and running application versions during rollback.
- Keep `structure.sql` when database features cannot be represented faithfully by `schema.rb`. Review changes to the checked-in schema artifact and ensure migrations reproduce it from an empty database.
- Use Strong Migrations or equivalent safeguards when present. Bypasses such as `safety_assured` require concrete, change-specific justification.

## Requests, authorization, and rendering

- Treat strong parameters as assignment filtering, not authorization. Verify authentication, action-level authorization, record scoping, and tenant ownership for every changed read or write path.
- Trace identifiers supplied through routes, forms, Turbo frames, and JSON APIs. Look for insecure direct object references, mass assignment, unsafe dynamic ordering or SQL, and enumeration across account boundaries.
- Check CSRF behavior, HTTP method semantics, redirects, return URLs, and content negotiation. State-changing actions should not be reachable through GET, and redirects should not accept untrusted external destinations without validation.
- Treat `html_safe`, `raw`, dynamic partial paths, user-authored rich text, and JavaScript interpolation as trust-boundary changes. Verify escaping and sanitization at the final rendering context.
- For Turbo and Stimulus changes, inspect full-page and frame/stream behavior, stable DOM identifiers, duplicate submissions, browser history, validation failures, focus, and no-JavaScript fallbacks where the product requires them.
- For ViewComponent changes, keep rendering logic and variants inside the component boundary, use explicit inputs, and cover meaningful rendered output rather than private implementation details.

## Jobs, caching, and asynchronous behavior

- Assume jobs can be delivered more than once, retried after partial work, and run after records have changed or disappeared. Require idempotent effects or an explicit deduplication strategy where duplicates matter.
- Pass stable identifiers and small serializable values to jobs rather than mutable object graphs. Re-authorize or re-check relevant state at execution time instead of assuming enqueue-time state remains true.
- Calibrate retry, discard, and rescue behavior to the failure. Do not retry permanent validation or authorization failures; preserve useful context without logging secrets or personal data.
- Check queue choice, priority, concurrency limits, transaction commit timing, and operational visibility. A job is not complete merely because it was enqueued.
- Review cache keys for every input that can change the result, including tenant, locale, authorization, variants, and versioned records. Verify invalidation and stampede behavior; never share sensitive cached output across scopes.

## Tests and verification

- Prefer behavioral RSpec coverage at the narrowest useful boundary. Model specs should exercise domain behavior and persistence; request specs should cover routing, authorization, responses, and side effects; system specs should be reserved for browser interactions that lower layers cannot prove.
- Cover success, validation failure, authorization failure, missing records, boundary values, and relevant retry or concurrency behavior. Match the test to the demonstrated risk rather than mechanically adding one example per method.
- Prevent accidental network access in tests. Stub at an owned integration boundary when available and use WebMock for request construction and protocol behavior. Exercise timeouts, malformed responses, non-success statuses, and network failures when the change handles them.
- Use verified partial doubles. Build valid records with FactoryBot when persistence matters, but avoid large factory graphs and `create_list` calls that hide test cost or irrelevant setup.
- Use `ClimateControl.modify` for environment-dependent behavior instead of stubbing `ENV` directly, so changes are scoped and restored reliably.
- Check time-dependent behavior with an explicit clock or Rails time helpers. Include zone and boundary cases when they affect semantics.
- Keep tests order-independent and compatible with randomized execution. Inspect leaked global configuration, cached constants, thread-local state, jobs, files, and database records.

## Damian's quality defaults

Treat these as the preferred baseline when the repository has not intentionally chosen another standard:

- RSpec, FactoryBot, Shoulda Matchers, SimpleCov, WebMock, Capybara, and Selenium for the testing stack.
- Bullet configured to raise on N+1 queries in tests and to report them during development.
- Rails Omakase plus relevant RSpec, FactoryBot, and ViewComponent RuboCop plugins.
- Sorbet `typed: strict` for application and library Ruby, with committed Tapioca gem and DSL RBIs. Review signatures at public boundaries and avoid using `T.untyped` or unsafe casts to silence design problems.
- RubyCritic as a maintainability signal with a high project threshold; use its output to investigate complexity rather than treating the score alone as a defect.
- Brakeman, Bundler Audit, importmap audit when applicable, and bounded dependency requirements. Git dependencies should pin a full commit SHA.
- PostgreSQL with `structure.sql`, Strong Migrations, and explicit database constraints for durable invariants.
- Timestamp-backed state instead of boolean database columns when transition time carries domain value.
- One implementation class or module per file, direct instance-variable reads hidden behind readers, and environment changes in tests isolated with ClimateControl.

Discover the repository's actual commands before running checks. Prefer its aggregate entrypoint, especially `bin/ci`, when available. Otherwise derive focused commands from `Gemfile`, `bin/`, CI workflows, and repository instructions. Report which checks ran and which could not run; do not require a tool that the application has intentionally excluded unless its absence creates a specific risk in the reviewed change.
