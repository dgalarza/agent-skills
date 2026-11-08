# Survey

Map an area of legacy code before deciding how to change it. Survey is read-only: production code stays untouched. To learn code by moving it around, use **scratch refactoring**: refactor freely in a throwaway git worktree, then delete it.

Scope is the area the user names: a module, a directory, a feature. When none is named, ask. Whole-repository scoring for agent readiness belongs to `codebase-readiness`, not here.

Write findings to `.legacy/<area>-map.md` as you go.

## 1. Baseline

Run the [baseline](../SKILL.md#baseline) for the area. When the repository has a `codebase-readiness` report (`AGENT_READY_ASSESSMENT.md` in the root), read its test, CI, and architecture findings as input, and check any claim about this area before you record it.

## 2. Entry points and the story

Find how the area is reached: routes, jobs, CLI commands, event handlers, public API, and callers wired by configuration, reflection, or metaprogramming.

Then **tell the story of the system**: three to five sentences on what the area does and why, written for someone new. Where the code disagrees with the story, note it. That gap is often where the design went wrong.

## 3. Structure and coupling

For each file or class in scope, record:

- what it depends on, and what depends on it
- global state, singletons, static access, and I/O done in constructors
- **change coupling**: files that change in the same commits, from `git log --name-only -- <path>`. Coupling that the imports don't show is a hidden dependency.

## 4. Coverage

Run the project's coverage tool on the area when it has one. Otherwise map which tests reference which files, and label that coverage inferred. For each file, record measured, inferred, or none.

## 5. Hotspots and history

Rank files by churn (commit count over the last year or so) against size or complexity. A file that changes often and is large or complex, with no coverage, is a **hotspot**: the place where tests pay back first.

For code that looks wrong, read `git log -L` or `git blame` and the linked commits before judging it. Record the reason when history gives one.

## 6. Seams and blockers

For each hotspot, try to name what stops a test from constructing and calling it, and match it to a symptom in [../references/symptoms.md](../references/symptoms.md). Record the existing **seams** too: interfaces, injected collaborators, overridable methods, module boundaries a test could swap.

List dead-code candidates found along the way. Leave them in place.

## 7. Promote to docs

Propose [doc updates](../SKILL.md#docs) from the map: the story, the entry points, the hidden coupling, the known quirks, and how the area gets under test.

## Done

The survey is done when the doc updates are proposed and the map has:

- the story, and where the code departs from it
- one row per file in scope: dependencies, coverage (measured, inferred, or none), churn, and the blocker to testing it
- the ranked hotspots
- the baseline

Report the hotspots and the two or three facts that most constrain any plan. Offer plan mode as the next step.
