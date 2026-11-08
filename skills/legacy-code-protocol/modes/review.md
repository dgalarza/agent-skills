# Review

Audit a pull request or diff that touches legacy code. The question is whether each edit made before tests existed preserves behavior, and whether the tests would catch a break.

## 1. Classify the edits

Sort each commit, or each hunk when commits are mixed, into one kind: seam, characterization test, change, refactor, or docs. A commit that mixes kinds is a finding, because a reviewer can't check its behavior-preserving parts on their own.

## 2. Check each kind

- **Seams:** each follows the [pre-test edit rules](../SKILL.md#pre-test-edits). Compare signatures and moved bodies against the base branch line by line. Confirm the production default is unchanged.
- **Characterization tests:** run them. For each test point, break the change point briefly and confirm a test goes red, then restore it. Look for unpinned time, randomness, or IDs, and for suspected bugs that were silently fixed instead of pinned.
- **Change:** the new behavior has tests that exercise it. Characterization tests edited for the change cover only behavior the request meant to change.
- **Refactor:** it sits inside the covered area, and the tests are green before and after it.

## 3. Check scope

Flag edits outside the change points, their seams, and their tests. Flag coverage claims that no test run supports. Check that docs the diff touches match the code, and flag docs about the area that the diff made stale.

## Done

The review is done when every commit has a kind, every test point got the sensing check, and every finding names a `file:line` and the evidence for it. When `team-code-review` or `conventional-comments` is available, use it to format and post the findings.
