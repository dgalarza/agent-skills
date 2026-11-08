# Characterization Tests

A characterization test pins what code does now, including behavior that looks wrong, so a later change can be checked against it.

## The loop

1. Call the test point with a chosen input inside the harness.
2. Write an assertion you expect to be wrong, such as a placeholder value.
3. Run it. The failure message shows the actual value.
4. Replace the placeholder with the actual value. The test passes.
5. Check that it **senses**: briefly break the change point, for example by returning a constant or deleting a branch, and watch the test go red. Restore the code, confirm with `git diff` that only your intended edits remain, and see the test pass.

A test that stays green when the code is broken is pinning nothing. Change its input or its assertion until the sensing check goes red.

## Choosing inputs

Read the change point and pick inputs that drive each branch the change will touch:

- the ordinary path
- each conditional the change sits inside or next to
- boundaries: empty, zero, one, the largest realistic value, missing or null fields
- error paths a caller can actually reach

Stop when every effect listed in the effect sketch has an assertion. Characterize the area of change, not the whole class.

## Observing effects

| Effect | How to sense it |
|--------|-----------------|
| Return value | Assert on it directly |
| Mutated argument or field | Assert on the object after the call |
| Call to a collaborator | Pass a fake that records calls and arguments |
| Database write | Use the project's test database or fixtures if it has them. Otherwise, break the dependency and record the write |
| Log or emitted event | Capture it with the framework's test helpers, or a recording fake |
| Intermediate state in a long method | Add a **sensing variable**: a field the method sets at the point of interest, read by the test, removed once the method has been split into testable pieces |

## Large outputs

When a test point produces a large output, such as a rendered report, a serialized payload, or a generated file, pin the whole output as a **golden master**:

1. Capture the output to a file committed beside the test.
2. Assert that the output equals the file.
3. Remove sources of noise first: timestamps, random IDs, ordering of unordered collections. Inject a fixed clock and seed, or normalize the output before comparing.

Use the project's snapshot or approval-testing library when it has one.

## Nondeterminism

Pin time, randomness, generated IDs, and environment reads before characterizing. Each is a dependency. Break it with the techniques in [dependency-breaking.md](dependency-breaking.md), usually Parameterize Constructor or Extract and Override Call. A characterization test that passes only sometimes is worse than no test.

## Suspected bugs

When the pinned value looks wrong:

- Pin it as it is. Callers may depend on it.
- Name the test after what the code does, for example `returns zero when quantity is negative`, not `handles negative quantity`.
- Add a short comment that marks the behavior as suspected, and list it in the summary.

Change that behavior only when the user asks for the fix. The fix then goes through a normal `tdd` red step: change the expectation, watch it fail, make it pass.

## Afterwards

Keep characterization tests after the change. They are the regression net for the next person. When intent-revealing tests later cover the same behavior, remove the characterization tests they replace.
