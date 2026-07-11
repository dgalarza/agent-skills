---
name: team-code-review
description: Review an agent's own code changes or another contributor's pull request by dispatching specialist agents, verifying every finding, and reporting only evidence-backed issues. Use when the user asks for a code review, PR review, review of a diff, or a multi-agent quality audit.
---

# Team Code Review

Run a read-only, evidence-driven code review with specialist agents. The main agent owns scope, verification, deduplication, severity, and the final report.

## 1. Establish the review target

Determine whether the target is:

- **Own work:** changes produced by the current agent or agent team.
- **Another contributor's pull request:** a PR authored outside the current agent team.

Read the repository instructions first. Identify the exact review base and head, then inspect the complete diff and relevant surrounding code. Do not silently broaden the review to unrelated working-tree changes. If authorship is unclear, infer it from the conversation and PR metadata when available; ask only when the answer changes the workflow and cannot be discovered.

Record explicit non-goals and constraints. Keep the review read-only unless the user separately asks for fixes.

Completion criterion: the review target, authorship branch, base/head, repository guidance, and changed files are known.

## 2. Dispatch the review team

Use subagents when the runtime supports them. Give each specialist the same target, base/head, repository instructions, and read-only constraint. Assign non-overlapping primary lenses:

1. **Architecture and code quality** — assess whether responsibilities and abstractions are coherent; identify duplication or misplaced behavior; check for appropriate API clients, service objects, collaborators, boundaries, and reuse without demanding abstractions that the code does not yet need.
2. **Readability** — assess naming, control flow, local complexity, consistency, error handling, and whether intent is easy to recover from the code.
3. **Testing** — trace each changed behavior to meaningful coverage, including success and failure paths, boundary cases, regressions, and integration points. For HTTP behavior, check request construction, headers/authentication, serialization, response parsing, relevant status codes, malformed responses, timeouts, retries/idempotency where applicable, and network failures. Prefer behavioral tests over implementation-coupled assertions.
4. **Maintainability** — assess coupling, extension cost, dependency direction, operational burden, compatibility, observability, and likely future failure modes.
5. **Security** — trace trust boundaries and data flow; assess authentication, authorization, validation, injection, secret exposure, sensitive logging, dependency risk, unsafe defaults, and failure behavior. Do not inflate hypothetical risks beyond what the code supports.
6. **Documentation** — check public interfaces, setup/configuration, migrations, operational changes, examples, changelog/release notes, and repository architecture or runbook documentation affected by the change.

Ask every specialist to return only actionable findings with:

- severity and confidence;
- exact file and tight line range;
- the concrete failure mode or maintenance cost;
- evidence from the diff and relevant surrounding code;
- a concise remediation direction;
- tests or commands used to validate the claim.

Specialists should omit praise, style preferences without impact, speculative concerns, and findings outside the changed code unless the change directly activates them. They may inspect and run safe checks, but must not edit files or publish review comments.

Run specialists concurrently when capacity allows; batch them when it does not. The main agent must retain enough context and time to verify their work.

Completion criterion: every lens has been investigated and each specialist has either returned candidate findings or explicitly reported no actionable findings.

## 3. Verify every candidate finding

The main agent must independently verify every candidate before reporting it:

1. Open the cited lines and enough surrounding code to understand the execution path.
2. Confirm the issue is introduced by or materially exposed by the target diff.
3. Search for callers, shared abstractions, tests, configuration, generated-code boundaries, and documentation that could invalidate the claim.
4. Reproduce with the narrowest safe test, static check, or concrete reasoning path available.
5. Calibrate severity to actual impact and likelihood.
6. Merge duplicates across specialists and discard unverified, speculative, or non-actionable items.

Do not report a specialist's claim merely because it sounds plausible. The main agent is accountable for every final finding.

Completion criterion: every reported finding has independently checked evidence, an accurate location, a defensible severity, and a concrete impact; every rejected candidate is omitted.

## 4. Report the review

Lead with findings ordered by severity, then confidence. For each finding include:

- a short imperative title;
- severity;
- file and tight line range;
- why it matters in this specific code path;
- the smallest useful remediation direction.

Then include:

- a concise overall assessment;
- testing performed and any checks that could not be run;
- remaining risks or coverage gaps;
- a brief note when no actionable findings were verified.

For **own work**, report the findings directly. Do not fix them unless the user asked for implementation.

For **another contributor's pull request**, provide the verified summary first, then ask whether the user wants a pull request review drafted on their behalf. Do not draft or publish the review before they agree.

If the user agrees to a PR review draft, invoke the `conventional-comments` skill and translate only the verified findings into Conventional Comments. Draft first; publish only with explicit authorization. Preserve severity, precise locations, and the distinction between blocking and non-blocking feedback.

## Review standard

- Review the change in repository context, not as isolated snippets.
- Prefer concrete defects and material design costs over taste.
- Do not confuse missing tests with a proven production defect; describe the actual coverage risk.
- Do not require a pattern such as an API client or service object by name. Recommend it only when it resolves demonstrated duplication, coupling, inconsistency, or testability problems.
- A clean review is valid when all six lenses were investigated and no candidate survived verification.
