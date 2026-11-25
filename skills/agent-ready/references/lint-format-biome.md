# Lint and Format Baseline: Biome for TypeScript and JavaScript

When a TypeScript or JavaScript repository has **no linter and no formatter**, set up [Biome](https://biomejs.dev). It is one dev dependency that lints, formats, and sorts imports. It reads `.gitignore`, and `biome ci` gives one CI command with changed-file scoping.

Never replace an existing linter or formatter. A repository with ESLint, Prettier, oxlint, dprint, or Biome already configured keeps its setup. If the user asks to move from ESLint or Prettier to Biome, treat it as a separate, opt-in PR. In testing (Biome 2.6.9), `biome migrate eslint` converted explicit rules. It dropped `eslint:recommended`, the typescript-eslint presets, and the `complexity` rule, and set `"preset": "none"`. Review the migrated config rule by rule, and run both tools until their results agree.

## Detection

The repository qualifies only when all of these hold:

```bash
ls package.json >/dev/null 2>&1                                   # JS/TS project
ls .eslintrc* eslint.config.* .oxlintrc.json biome.json biome.jsonc \
   .prettierrc* prettier.config.* dprint.json .dprint.json 2>/dev/null   # must print nothing
grep -E '"(eslintConfig|prettier)"\s*:' package.json                # must print nothing
grep -E '"(eslint|prettier|@biomejs/biome|oxlint|dprint)"' package.json  # must print nothing
```

In a monorepo, check each workspace package as well as the root. Set Biome up at the root only when no package has its own linter or formatter. Otherwise report the mixed state and stop.

## Setup

Ask before installing, and show the plan: the dev dependency, the config, the one-time reformat commit, the suppression pass, the scripts, and CI.

```bash
npm install --save-dev --save-exact @biomejs/biome   # or the project's package manager; pin exactly
npx biome init                                         # writes biome.json with the current version's defaults
```

Keep the generated `biome.json`: the recommended preset, the formatter, organize imports, and VCS integration with `useIgnoreFile`. Make two edits:

- Set `vcs.defaultBranch` to the repository's default branch, so `--changed` works without `--since`.
- Leave `complexity/noExcessiveCognitiveComplexity` off. It is not in the recommended preset. Fallow owns complexity in the quality gate (see `quality-gates-pattern.md`), and two tools gating the same property report every finding twice.

Leave the type-aware rules off by default. In Biome 2.6.9, `noFloatingPromises` is still a nursery rule. It is not enabled by the recommended preset or by `"domains": { "types": "recommended" }`, and works only when set explicitly. Mention it as an opt-in. Do not present Biome as a replacement for typescript-eslint's type-checked rules.

Biome lints the `<script>` blocks of Vue files. Astro and Svelte support is partial. In those projects, say that template syntax is not linted.

## Rollout: format once, then suppress legacy lint debt

1. **Format in its own commit.** Run `npx biome format --write .` and `npx biome check --write .`, which applies safe fixes and sorts imports. Commit the result as `style: format with Biome` and add that commit's SHA to `.git-blame-ignore-revs`, so `git blame` skips it. Never apply `--unsafe` fixes in this commit.
2. **Show what remains.** Run `npx biome lint --error-on-warnings`. Present the diagnostics grouped by rule and top files, and ask which are cheap to fix now. Fixing is better than suppressing.
3. **Suppress the rest, with a reason, after explicit confirmation.** `npx biome lint --suppress --reason="legacy lint debt; fix when touched"` writes a `// biome-ignore <rule>: <reason>` comment above each remaining violation. `--suppress` cannot be combined with `--write`.
4. **Gate with `--error-on-warnings`.** Biome reports a suppression that no longer matches anything as `suppressions/unused`, a warning. With `--error-on-warnings`, fixing suppressed debt fails CI until the stale comment is removed, so the suppressed set only shrinks. Warning-level rules such as `noExplicitAny` also block new code.

Agents may remove an unused suppression. Agents must not add a `biome-ignore` comment to get past CI. Write both rules into AGENTS.md.

## Commands

Add scripts that call exactly what CI calls:

```json
"lint": "biome ci --error-on-warnings",
"lint:fix": "biome check --write",
"format": "biome format --write"
```

Put `npm run lint` in the AGENTS.md build/test/lint one-liners and the Definition of Done. In the pre-push hook of an existing hook framework, prefer `biome ci --error-on-warnings --changed`.

## CI

Add a step to the existing workflow, or a job:

```yaml
- uses: actions/setup-node@v4
  with: { node-version: '22', cache: 'npm' }
- run: npm ci
- run: npx biome ci --error-on-warnings --reporter=github
```

`--reporter=github` annotates the PR diff. Run the full tree in CI, not `--changed`: the unused-suppression check only works on a full run. Never add `continue-on-error`.

## Verified behavior (Biome 2.6.9)

| Scenario | Result |
|----------|--------|
| Unformatted file, lint error, or unsorted imports | `biome ci` exits 1 |
| New `any` (warning level) with `--error-on-warnings` | exits 1 |
| Legacy violations after `lint --suppress` | exits 0 |
| Suppressed violation fixed, comment left behind | `suppressions/unused`; exits 1 with `--error-on-warnings` |
| `--changed --since=main` | checks only files changed on the branch |
