---
name: team-code-review
description: Review an agent's own code changes or another contributor's pull request by dispatching specialist agents, verifying every finding, and reporting only evidence-backed issues. Use when the user asks for a code review, PR review, review of a diff, or a multi-agent quality audit.
---

# Team Code Review

Run a read-only, evidence-driven code review with specialist agents. The review coordinator owns scope, verification, deduplication, severity, and the final report. In the steps below, “main agent” means that coordinator, which may be a fresh agent in Herdr rather than the original caller.

## 0. Choose where the review runs

Check whether the caller is inside Herdr:

```bash
test "${HERDR_ENV:-}" = 1
```

- **Inside Herdr:** follow [references/herdr.md](references/herdr.md) to launch a fresh agent of the same kind in a new sibling pane and hand off this review. This is the user's standing preference for this skill, not a general permission to use Herdr for unrelated tasks.
- **Outside Herdr:** run steps 1–4 here without issuing Herdr commands.
- **Already the delegated review coordinator:** when your task explicitly contains `TEAM_CODE_REVIEW_COORDINATOR=1`, skip the pane handoff and run steps 1–4 here. Pass this marker to any specialists that may load this skill as well; it prevents recursive coordinator spawning.

Honor an explicit request to review in the current agent instead. If Herdr or the caller's agent kind cannot be resolved, explain the limitation and ask whether to proceed locally; do not silently substitute a different agent kind.

## 1. Establish the review target

Determine whether the target is:

- **Own work:** changes produced by the current agent or agent team.
- **Another contributor's pull request:** a PR authored outside the current agent team.

Read the repository instructions first. Identify the exact review base and head, then inspect the complete diff and relevant surrounding code. Do not silently broaden the review to unrelated working-tree changes. If authorship is unclear, infer it from the conversation and PR metadata when available; ask only when the answer changes the workflow and cannot be discovered.

Detect the application stack from repository evidence such as dependency manifests, framework configuration, and directory structure. Load any matching review profile before dispatching specialists. For a Rails application, read [references/rails.md](references/rails.md) and incorporate its applicable checks into the specialist assignments. Treat profiles as opinionated investigation guidance, not automatic findings; explicit repository instructions and documented architectural decisions take precedence.

Record explicit non-goals and constraints. Keep the review read-only unless the user separately asks for fixes.

Completion criterion: the review target, authorship branch, base/head, repository guidance, changed files, application stack, and applicable review profiles are known.

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

Run specialists concurrently when capacity allows; batch them when it does not. If the runtime has no subagent facility, the coordinator investigates all six lenses sequentially and discloses that limitation rather than claiming a multi-agent review. The main agent must retain enough context and time to verify their work.

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
