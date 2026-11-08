# Plan

Turn a goal into an ordered sequence of small, verifiable units, then into pull requests and tickets. Plan mode writes no production code.

Read `.legacy/<area>-map.md`. When it is missing or the goal reaches outside it, run [survey](survey.md) first. Write the plan to `.legacy/<area>-plan.md`.

## 1. Goal and end state

State the goal in one or two sentences, and the end state that shows it is met: the behavior added, the structure reached, the coverage required. Say what is out of scope.

## 2. Test points

From the map, choose where tests will sense the work. Prefer a **pinch point**: one test point where a few tests detect the effects of many change points. When the area is too tangled for one, choose **interception points** close to each change.

## 3. Units

Order the work in this sequence. Drop a stage the goal does not need, and merge stages when the whole job is small.

1. **Docs:** the [doc updates](../SKILL.md#docs) survey proposed. A docs-only pull request carries no behavior risk, so it can land first.
2. **Harness:** a runner or fixtures the tests need.
3. **Seams:** behavior-preserving dependency breaks at the test points, following the [pre-test edit rules](../SKILL.md#pre-test-edits).
4. **Pin:** characterization tests at the test points.
5. **Change:** the new behavior, test-first. Where a host can't be brought under test in time, use Sprout or Wrap.
6. **Refactor or replace:** structural work under green tests. When the goal is to retire the code rather than reshape it, plan the steps of [replace](replace.md) as the units instead. For a class that is too big, group its methods by responsibility and extract one group at a time. For a monster method, use Break Out Method Object, then extract methods from the object.
7. **Follow-ups:** cleanup kept out of the earlier units, such as deleting dead code.

For each unit, record:

- what it changes
- why it is safe: the behavior-preserving argument for seams, or the tests that guard it
- its test points and the command that verifies it
- how to roll it back
- the units it depends on

## 4. Pull requests

Map units to pull requests, usually one unit each. Dependent units form a stack: use the `stacked-prs` skill when it is available. Units that don't depend on each other become separate, parallel pull requests. Each seam pull request states its safety argument in the description, because no test proves it yet.

## 5. Tickets

Offer to split the plan into tickets, one per pull request or per unit.

1. Find the tracker. Look for tracker tools in the session (Linear, Jira, GitHub Issues through `gh`), ticket IDs in branch names and commit messages, and tracker references in the repository docs. When the evidence names one tracker, use it and say which. When it names none or several, ask the user which tracker to use, or whether to skip tickets.
2. Check for a skill that writes issues or tickets, and use it when one exists. Otherwise draft each ticket in the plan file: title, context linking the map and plan, acceptance criteria stated as tests that must pass, and the tickets it is blocked by.
3. File tickets only after the user approves the plan.

## Done

The plan is done when every unit has a safety argument and a verification command, every unit belongs to a pull request, and tickets are drafted or the user declined them. Present the plan and stop for approval. Each approved unit then runs as [pin](pin.md) or [change](change.md). A Refactor unit runs as change, with the structural goal as the change, guarded by the tests from an earlier pin unit.
