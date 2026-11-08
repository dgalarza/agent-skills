# Pin

Lock what the code does now with characterization tests, so a later change can be checked against it. Pin changes no behavior. Its only production edits are seams.

Start with the [baseline](../SKILL.md#baseline).

## 1. Identify change points

Name each function, method, or module that the coming work will edit. When a plan exists, take them from the unit. Read each one and its direct callers.

The step is done when every change point is listed with its `file:line`.

## 2. Sketch effects and find test points

For each change point, trace what it can affect:

- return values
- mutated arguments and fields
- global or static state
- I/O: database writes, files, network, logs, emitted events
- the callers that read any of these

Follow effects outward until they are observable at an interface a test can call. That place is the **test point**. Prefer a **pinch point**: one test point where a few tests detect the effects of several change points.

Search for callers by name and by string. Dynamic dispatch, reflection, metaprogramming, callbacks, and configuration-driven wiring all hide callers from a symbol search.

The step is done when every change point has its effects and test points written down. Effects that can't be observed anywhere are listed as gaps.

## 3. Break dependencies at the test point

Try to construct and call the test point in the harness as it is. When that fails, break the dependency at a **seam**: a place where behavior can be changed without editing the code at that place. There are two reasons to break a dependency:

- **Sensing:** the test can't see what the code did.
- **Separation:** the test can't run the code on its own.

Follow the [pre-test edit rules](../SKILL.md#pre-test-edits).

The step is done when a test constructs and calls each test point and runs in the harness.

## 4. Characterize

Write characterization tests at each test point that pin what the code does now, not what it should do. Details are in [../references/characterization-tests.md](../references/characterization-tests.md).

1. Write an assertion you expect to be wrong, run it, read the actual value in the failure, and pin that value.
2. Confirm the test **senses** the code. Briefly break the change point, for example by returning a constant, and watch the test go red. Then restore the code, and confirm with `git diff` on that file that only your intended edits remain.
3. Cover the behavior the coming change touches and the paths beside it that the change could disturb. The area of change is enough, not the whole class.
4. Pin surprising behavior exactly as it is. Name the test after what the code does, and add the behavior to the suspected-bugs list.

A characterization test passes as soon as its value is pinned. That is the exception to the `tdd` rule that a test passing immediately is suspect. The sensing check takes the place of the red step.

## Done

Pin is done when every effect from step 2 has a passing test that was seen red once, or is listed as a gap, and the suite matches the baseline.

Report the change points and test points, the seams and the technique used for each, the tests added and the command that runs them, the gaps, and the suspected bugs. Propose [doc updates](../SKILL.md#docs) for what pin learned: the seams that worked, the fixtures, and the pinned quirks.
