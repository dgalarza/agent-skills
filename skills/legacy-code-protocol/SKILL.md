---
name: legacy-code-protocol
description: Protocol for working in legacy code, meaning existing code with few or no tests, or code nobody understands. Modes - survey maps an unfamiliar area (structure, coupling, coverage, hotspots, seams); plan sequences the work into stacked PRs and tickets; pin locks current behavior with characterization tests; change makes one change safely through seams and test-first edits; replace swaps in a new implementation using characterization tests as the parity oracle; review audits a pull request that touches legacy code. Based on Michael Feathers' Working Effectively with Legacy Code. For new code, or code already covered by tests, use tdd.
---

# Legacy Code Protocol

Treat code without tests as legacy, however clean it looks: without tests, no one can tell whether a change makes it better or worse. Treat code nobody on the team understands the same way, tested or not. Apply the method of Michael Feathers' *Working Effectively with Legacy Code*: understand the code, pin what it does now, then change it on purpose.

The core tension is the **legacy code dilemma**. Changing code safely needs tests, and getting tests in often needs changes to the code. Resolve it this way: every edit made before tests exist is small, mechanical, and behavior-preserving. Once an area is pinned, switch to ordinary `tdd`.

## Modes

Pick the mode from the request. Open its file and follow its steps.

| Mode | Use when | File |
|------|----------|------|
| **survey** | The area is unfamiliar, or the user wants the lay of the land before deciding anything | [modes/survey.md](modes/survey.md) |
| **plan** | The work is bigger than one change: adding missing tests, then changing, refactoring, or splitting the code | [modes/plan.md](modes/plan.md) |
| **pin** | Behavior must be locked before someone changes it: an upgrade, a migration, a rewrite, a hand-off | [modes/pin.md](modes/pin.md) |
| **change** | One concrete change to untested code | [modes/change.md](modes/change.md) |
| **replace** | The old code is being retired for a rewrite, a new library, or a new service | [modes/replace.md](modes/replace.md) |
| **review** | A pull request or diff touches legacy code | [modes/review.md](modes/review.md) |

Modes chain: survey feeds plan, and each step of a plan runs as pin, change, or replace. When the user names a mode, use it. When a change request lands on code you have not surveyed and the area spans more than a few files, run survey first and say so.

## Work files

Survey and plan write Markdown files that later modes and later sessions read: `.legacy/<area>-map.md` and `.legacy/<area>-plan.md` in the repository root. Leave them uncommitted unless the user asks to commit them: add `.legacy/` to `.git/info/exclude` so later commits don't sweep them in. Read existing ones before starting, and update them rather than starting over.

## Docs

Work files are scratch. Facts the next agent will need, whatever its task, belong in the repository's docs. Each mode ends by promoting what it verified, so every legacy task leaves its area more agent-ready.

Use the repository's existing docs layout. When it has none, use the `agent-ready` layout:

| Finding | Destination |
|---------|-------------|
| The area's story, entry points, hidden coupling, and invariants | `docs/architecture/<area>.md`, linked from `ARCHITECTURE.md` |
| Business workflows the code implements | `docs/DOMAIN.md` |
| Domain terms whose meaning is settled | `CONTEXT.md` |
| How to get the area under test: the command, the seams, the fixtures, how nondeterminism is pinned | `docs/guides/testing.md` |
| Why odd code exists, and surprising behavior that was pinned | the area doc, under "Known quirks" |
| Pointers to new docs, and the test command when it is missing | one line each in `AGENTS.md` |

Suspected bugs go to tickets or the report, not docs.

- Promote only what a test run, the code, or git history confirmed. Label inferred facts as inferred.
- Stay inside the area. For a full scaffold across the repository, point the user to `agent-ready`.
- Propose the doc changes and write them after the user agrees. Commit them on their own, apart from code.

## Baseline

Every mode that runs tests starts here.

1. Read the repository instructions and find the project's test command. Run the narrowest subset that covers the area.
2. Record the result:
   - **Green:** continue.
   - **Red:** list the tests that fail before any edit. Leave them as they are and report them. If a failing test covers a change point, stop and ask the user how to proceed.
   - **Flaky:** rerun to identify the flaky tests. Treat them as no coverage, and list them.
   - **No runnable harness:** check whether the language's standard runner works here. If one dev dependency and one config file would set it up, propose that to the user before adding it. Otherwise stop and ask, or use Sprout or Wrap (see [modes/change.md](modes/change.md)) and say the host code stays untested.

The baseline is recorded when it names the command that ran plus the failing and flaky tests, or "none".

## Pre-test edits

Rules for any production edit made before tests cover it:

- One technique per edit, chosen by symptom from [references/symptoms.md](references/symptoms.md) and applied as in [references/dependency-breaking.md](references/dependency-breaking.md).
- **Preserve signatures.** Copy parameter lists exactly. Move code by cut and paste rather than retyping it.
- **Lean on the compiler.** Let the type checker, compiler, or linter find every site an edit touches. In dynamic languages, search for the name, then run the code.
- Production paths keep their current defaults. The real collaborator stays the default, and the seam only adds a way to substitute it.
- An awkward seam is acceptable. Clean it up after tests exist.

## Guardrails

- Keep the diff to the current goal or plan unit: its change points, the seams that brought them under test, and the tests. List other cleanup as follow-ups: formatting, renames, style, dead code, outdated patterns.
- Pin and report suspected bugs. Fix one only when the user asks, because callers may depend on it.
- Keep the kinds of edit apart: seams, characterization tests, the change, refactoring, docs. Give each its own commit, so a reviewer can check that the earlier ones preserve behavior.
- State coverage only for tests that ran. Label anything inferred as inferred.
