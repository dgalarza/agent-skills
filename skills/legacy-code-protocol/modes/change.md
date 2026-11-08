# Change

Make one change to untested code without changing anything else it does.

## 1. Pin the area

Run [pin](pin.md) for the change points. Skip it only for change points that existing tests already cover, and confirm that coverage with the sensing check from pin step 4.

## 2. Make the change

With the area pinned, use `tdd` for the new behavior: red, green, refactor, one behavior at a time. The baseline recorded by pin replaces `tdd`'s baseline check. Compare against it, and continue past failures that were already there.

Some characterization tests pin behavior the request deliberately changes. Update each of those in a red step: change the expectation to the new behavior, watch it fail, then make it pass. Every other characterization test stays green and unedited.

When a change point can't be brought under test in the time available, keep the new code testable anyway:

- **Sprout Method or Sprout Class:** write the new logic as a new function or class, test-driven, and call it from the old code with a one-line insertion.
- **Wrap Method or Wrap Class:** keep the old behavior under a new name, and add a method or decorator with the original name that calls the old behavior and the new one.

Record the host as untested.

## 3. Refactor under green

Refactor only inside the covered area, and only to support the change or to remove duplication it introduced. Run the tests after each step.

## Done

The change is done when:

- every change point is pinned by characterization tests that were seen red once, or is a host left alone by Sprout or Wrap,
- the new behavior was built test-first,
- the diff follows the [guardrails](../SKILL.md#guardrails), and
- the suite matches the baseline, apart from the intended changes.

Report what pin reports, plus the hosts left untested by Sprout or Wrap and the follow-up cleanup left out of the diff.
