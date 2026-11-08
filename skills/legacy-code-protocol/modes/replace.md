# Replace

Retire legacy code by swapping in a new implementation: a rewrite, a new library, a new service. Characterization tests become the **parity oracle**: the new code is equivalent when it passes the same tests and matches the old code on real inputs.

The pattern is the **strangler fig**: grow the new implementation behind a seam until the old one can be cut away. When a plan exists, each step below is one of its units.

## 1. Pin the boundary

Run [pin](pin.md) with the test points at the interface callers use, not inside the old code, because the internals are going away. Use golden masters for large outputs.

## 2. Add an interception point

Route every caller through one seam, such as an interface, a facade, or a router, with the old implementation behind it as the default. Follow the [pre-test edit rules](../SKILL.md#pre-test-edits). Search for callers by name and by string, and list any that bypass the seam.

The step is done when every caller goes through the seam and the pinned tests are green.

## 3. Build the new implementation

Build it test-first behind the same seam, running the pinned tests against it. Each failing test is a behavior to match, or a suspected bug for the user to keep or drop. Record each decision.

## 4. Compare on real inputs

Run both implementations on production or production-like inputs: serve the old result, compute the new one, and log every mismatch. Use the project's experiment or flag library when it has one. Keep the new path free of side effects: no writes, emails, or charges while comparing.

Sort each mismatch into a bug in the new code (fix it, and add a test) or behavior in the old code worth dropping (the user decides). The step is done when mismatches stay at zero, or at user-approved differences only, across a sample the user agrees is representative.

## 5. Cut over

Switch callers to the new implementation behind a flag, one caller or traffic slice at a time, with the old path still deployable as the rollback.

## 6. Delete the old code

After the new code has carried full traffic for the period the user agreed, delete the old implementation, the comparison scaffolding, and the flag in one change. Keep the characterization tests that still describe intended behavior, and rename them as intent tests.

## Done

Replace is done when the old code is deleted, every caller runs the new implementation, and every behavior that differs from the old code was approved by the user. Report the approved differences, the mismatch counts from step 4, and anything left behind the seam. Propose [doc updates](../SKILL.md#docs) that describe the new implementation, and remove docs about the old one.
