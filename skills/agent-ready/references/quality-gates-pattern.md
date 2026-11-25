# Regression-Aware Quality Gate Pattern

The cross-language pattern the `quality-gates` mode installs. It is deliberately tool-agnostic: the project's native analyzers produce findings, a small baseline layer decides what is new, and CI blocks on that decision. The pattern is the same whether the analyzer is RuboCop, golangci-lint, ESLint, or PMD.

## The Contract

Three commands, identical locally and in CI:

| Command | Purpose | Exit code | Who runs it |
|---------|---------|-----------|-------------|
| `report` | Show every finding grouped as new / worsened / stale / baselined, with changed-file attribution | always 0 | anyone, any time |
| `check` | Fail on new or worsened findings, on stale baseline entries, or on an unreviewed baseline | 1 on failure | CI on every PR; agents before marking work done |
| `baseline` | Create or extend the baseline (needs `--reason`, then human approval); `--prune` removes stale entries and tightens improved metrics | 2 on refusal | humans create/extend/approve; anyone may prune |

Semantics the gate must satisfy (these are what the tests prove):

1. **Unchanged legacy debt passes.** Findings recorded in the baseline do not fail `check`, even when they move to other line numbers.
2. **New or worsened debt fails.** A finding not in the baseline fails. A baselined finding whose count grew, or whose tracked metric (complexity value, duplicated lines) increased, fails.
3. **Stale entries are removed.** When debt is fixed, `check` reports the entry as stale and fails until `baseline --prune` removes it, so the baseline only ever shrinks. Pruning never needs review because it only tightens.
4. **Baselines are reviewed, not blindly blessed.** Creating or extending a baseline requires a written reason, prints a review summary (counts by rule, top files), refuses to run in CI, and leaves the baseline in an unreviewed state that fails `check` until a human approves it with their name. The baseline file is CODEOWNERS-protected.
5. **Merge-base aware.** Findings are attributed to files changed since `git merge-base <base> HEAD`, not since the tip of main; `--changed-only` scopes fast local runs to that set. CI checks out with full history so the merge-base resolves.
6. **Tool failure is not a pass.** A check whose command exits non-zero without producing findings is an error that fails the gate.

## Two Ways to Get There

### Option A: the analyzer has a native baseline or diff mode

Use it. No custom baseline layer is needed; the three commands become thin wrappers.

| Tool | Native mechanism | Notes |
|------|------------------|-------|
| golangci-lint | `issues.new-from-merge-base: origin/main` (or `new-from-rev`) | Complexity (`gocyclo`, `gocognit`), duplication (`dupl`), dead code (`unused`) all in one tool. Merge-base aware out of the box. Stale handling is automatic (no baseline file) |
| detekt | `detekt --baseline detekt-baseline.xml`; `--create-baseline` | Baseline is XML; prune by regenerating after fixes. Review the diff of the baseline file in PRs |
| PHPStan | `--generate-baseline` + `reportUnmatchedIgnoredErrors: true` | The `reportUnmatchedIgnoredErrors` flag is what makes stale entries fail; without it the baseline only grows |
| RuboCop | `.rubocop_todo.yml` + `--regenerate-todo` after fixes | Only counts as regression-aware if the todo file is regenerated (pruned) when offenses are fixed. Pair with `Metrics/*` cops for complexity |
| SonarQube / SonarCloud | New-code quality gate | Vendor-hosted; the local `check` must still exist for agents |

Wrap them so the contract holds: `report` runs the tool in its normal mode, `check` runs it in baseline/diff mode, `baseline` regenerates with `--reason` recorded in the commit message and the PR. Add the review requirement via CODEOWNERS on the baseline file.

### Option B: the analyzer has no baseline mode

Use `assets/quality-gate.py` (stdlib Python, committed to the target repo as `scripts/quality-gate.py`). It runs each configured analyzer, parses one finding per line, fingerprints findings by `check | rule | file | message-without-numbers` (so line numbers and metric values do not affect identity), and compares to `.quality-baseline.json`.

Config, `.quality-gate.json`:

```json
{
  "version": 1,
  "base_ref": "origin/main",
  "baseline": ".quality-baseline.json",
  "checks": {
    "complexity":  { "command": "...", "format": "unix" },
    "duplication": { "command": "...", "format": "jsonl" },
    "dead-code":   { "command": "...", "format": "jsonl", "metric": false }
  }
}
```

Each check's command must print **one finding per line** in one of two formats:

- `unix`: `path:line[:col]: message [rule]` -- what ESLint `-f unix`, RuboCop `-f emacs`, ruff `--output-format concise`, and gcc-style tools emit. A trailing `[rule]` or `(rule)` becomes the rule id; otherwise the check name is used.
- `jsonl`: `{"file": ..., "line": ..., "rule": ..., "message": ...}` per line -- produce it from any tool's JSON output with `jq -c` or a one-line Python adapter.

The first integer in a message is tracked as a metric (a complexity value, a duplicated-line count). A higher value than the baseline is "worsened". Set `"metric": false` on checks whose messages contain incidental numbers (dead-code reports, for instance).

## Adapter Recipes

Each recipe emits the contract format. Test every command by hand before writing it into the config.

**TypeScript / JavaScript -- default: [fallow](https://github.com/fallow-rs/fallow)**

Fallow is one Rust binary, distributed on npm, that covers all three properties. It reports complexity (`fallow health`), duplication (`fallow dupes`), and dead code (`fallow dead-code`: unused files, exports, types, members, and dependencies). It needs no TypeScript compiler, and its 100+ framework plugins find entry points without configuration. Use it for TS/JS projects unless the project already gates a property with another tool; see "Existing TS/JS tools" below.

Use Option B with the shipped adapter, `assets/fallow-adapter.mjs`, installed as `scripts/fallow-adapter.mjs`. The adapter runs fallow with `--format json`, emits the contract's jsonl, exits 0 when fallow's exit 1 only means "findings", and exits 2 on a real tool failure (exit >= 2, unparseable output).

```bash
npm install --save-dev fallow            # Node.js 22+; pin it so CI and local runs match
cp "<skill-dir>/assets/fallow-adapter.mjs" scripts/fallow-adapter.mjs
```

`.fallowrc.json`. Write it **before** saving the baseline. Changing entry points, ignores, or rules afterwards changes the findings and leaves stale baseline entries.

```json
{
  "$schema": "./node_modules/fallow/schema.json",
  "ignorePatterns": ["scripts/fallow-adapter.mjs"]
}
```

Add `entry`, `ignoreDependencies`, `health.maxCyclomatic` (default 20), `health.maxCognitive` (default 15), or `duplicates.minTokens` (default 50) only when the defaults are wrong for the project. `npx fallow recommend` proposes a config without writing files. Rules set to `"warn"` in `rules` are reported by fallow but do not gate, because the adapter keeps only error-severity findings.

`.quality-gate.json` checks:

```json
"complexity":  { "command": "node scripts/fallow-adapter.mjs complexity",  "format": "jsonl" },
"duplication": { "command": "node scripts/fallow-adapter.mjs duplication", "format": "jsonl" },
"dead-code":   { "command": "node scripts/fallow-adapter.mjs dead-code",   "format": "jsonl", "metric": false }
```

Extra adapter arguments pass through to fallow, for example `--production` or `--workspace <name>` for one monorepo package. The adapter emits one finding per function per exceeded dimension (`complexity-cyclomatic`, `complexity-cognitive`), with the measured value as the tracked metric. It emits one finding per clone instance with the duplicated line count as the metric, and one finding per dead-code item keyed by name, not line.

Why Option B and not fallow's native baselines: fallow has `--save-baseline`, `--fail-on-stale-baseline`, `--fail-on-baseline-growth`, and `fallow baselines prune`. Tested on fallow 3.48.0, they cover new findings, line moves, stale entries, and pruning. They do not fail when a baselined function gets more complex, because health baselines match by file or function and category, not by value. Duplication also gates only with `--fail-on-issues`. `fallow audit` scopes to changed files and passed both the worsened-function and new-duplication cases in testing. Use `audit` as an agent's local review aid, not as the blocking gate.

Leave CRAP out of the gate (`health.maxCrap`) unless the project passes `--coverage`. Without coverage the score is a static estimate.

`npx fallow agent install` (Claude Code, Codex, Cursor) writes an AGENTS.md task map, installs fallow skills, registers an MCP server, and adds git commit/push hooks. Offer it only as an optional extra, after showing its `--dry-run` output, because it edits AGENTS.md and hooks that this skill also manages.

**Existing TS/JS tools.** When the project already gates one property with ESLint complexity, jscpd, or knip, keep that tool for that property and use fallow only for the uncovered ones. If the user wants one analyzer, `npx fallow migrate` converts knip and jscpd configs. Run both tools until their findings agree, then remove the old one in its own PR. The recipes for those tools:

```bash
# complexity (unix): ESLint's own rule, threshold from the project's config
npx eslint . -f unix --rule 'complexity: ["error", 10]' --no-inline-config || true
# cognitive complexity if eslint-plugin-sonarjs is installed
npx eslint . -f unix --rule 'sonarjs/cognitive-complexity: ["error", 15]' || true
# duplication (jsonl) via jscpd
npx jscpd . --reporters json --output .jscpd-out --silent >/dev/null 2>&1; \
  jq -c '.duplicates[] | {file: .firstFile.name, line: .firstFile.start, rule: "duplicate-block", message: ("\(.lines) lines duplicated with " + .secondFile.name)}' .jscpd-out/jscpd-report.json
# dead code (jsonl) via knip -- reliable enough to block on
npx knip --reporter json 2>/dev/null | jq -c '.files[]? as $f | {file: $f, rule: "unused-file", message: "unused file"}, (.issues[]? | .file as $file | .exports[]? | {file: $file, line: .line, rule: "unused-export", message: ("unused export " + .name)})'
```

**Ruby / Rails**

```bash
# complexity (unix): only the Metrics cops; leave style to the normal rubocop run
bundle exec rubocop --only Metrics/CyclomaticComplexity,Metrics/PerceivedComplexity,Metrics/AbcSize,Metrics/MethodLength -f emacs || true
# duplication (unix) via flay: "path:line: N similar code" lines
bundle exec flay -d app lib 2>/dev/null | awk '/^  [^ ]+:[0-9]+/ {split($1,a,":"); print a[1] ":" a[2] ": similar code (" score ") [flay]"} /^[0-9]+\)/ {score=$1}'
# dead code (jsonl) via debride with a curated whitelist
bundle exec debride --rails --whitelist .debride-whitelist app lib 2>/dev/null | awk '/^  [A-Za-z]/ {print "{\"file\": \"" $NF "\", \"rule\": \"unused-method\", \"message\": \"" $1 " possibly unused\"}"}' | sed 's/:[0-9]*"}/"}/'
```

**Python**

```bash
# complexity (unix): ruff's C901 with the project threshold
ruff check . --select C901 --output-format concise --no-fix || true
# or radon for cognitive/cyclomatic detail
radon cc . -n C -s --json | python3 -c 'import json,sys; d=json.load(sys.stdin); [print(json.dumps({"file": f, "line": b["lineno"], "rule": "complexity", "message": f"{b[\"name\"]} has complexity {b[\"complexity\"]}"})) for f, bs in d.items() for b in bs]'
# duplication (jsonl) via pylint
pylint --disable=all --enable=duplicate-code --output-format=json . 2>/dev/null | python3 -c 'import json,sys; [print(json.dumps({"file": m["path"], "line": m["line"], "rule": "duplicate-code", "message": m["message"].splitlines()[0]})) for m in json.load(sys.stdin)]'
# dead code (unix) via vulture with a whitelist; metric: false
vulture . whitelist.py --min-confidence 80 || true
```

**Go** -- use Option A. Enable `gocyclo`, `gocognit`, `dupl`, and `unused` in `.golangci.yml`, set `issues.new-from-merge-base: origin/main`, and make `check` = `golangci-lint run` and `report` = `golangci-lint run --new=false`.

**Java / Kotlin** -- detekt: Option A with `--baseline`. PMD: Option B with `pmd check -d src -R rulesets/... -f json` piped through `jq -c '.files[] | .filename as $f | .violations[] | {file: $f, line: .beginline, rule: .rule, message: .description}'`, and `pmd cpd --minimum-tokens 100 --format csv` mapped to jsonl.

**Rust** -- `cargo clippy --message-format=json -- -W clippy::cognitive_complexity` piped through `jq -c 'select(.reason=="compiler-message") | .message | select(.code != null) | {file: .spans[0].file_name, line: .spans[0].line_start, rule: .code.code, message: .message}'`; dead code via `cargo machete` (jsonl adapter) or `-W dead_code` from the same clippy stream.

**PHP / Laravel** -- PHPStan: Option A. `phpmd src json cleancode,codesize` and `phpcpd --log-pmd` for complexity/duplication through Option B.

## Baseline Review Protocol

The baseline is where debt gets blessed, so its creation is the one step that must not be automated away:

1. Run `report` first. Present the findings grouped by rule and top files. Ask which of them are cheap to fix now -- fixing before baselining is always preferred over blessing.
2. Run `baseline --reason "<why this debt is accepted for now>" --dry-run` and show the candidate summary.
3. Only on explicit confirmation, run it without `--dry-run`. The baseline is written in an **unreviewed** state and `check` fails until approved.
4. Open a PR containing `.quality-baseline.json`, `.quality-gate.json`, the engine, CI, docs, and tests. A reviewer inspects the accepted debt, then runs `baseline --approve --reviewed-by "<name>"` and pushes.
5. Add the baseline file to CODEOWNERS so extending it always requires a named reviewer.

Agents may run `check`, `report`, and `baseline --prune`. Agents must never run `baseline` (create/extend) or `--approve`. Write that into AGENTS.md.

## CI Shape

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }              # merge-base needs history
- run: git fetch origin ${{ github.base_ref || 'main' }}
- run: python3 scripts/quality-gate.py check   # GITHUB_ACTIONS is set, so findings annotate the diff
```

Never `continue-on-error`. Never regenerate the baseline in CI (`baseline` refuses when `CI` is set). See `assets/quality-gate-ci-template.yml`.

## Tests of the Gate

`assets/quality-gate-test-template.sh` runs against the installed gate with a temporary copy of the baseline and proves the three properties without touching the real baseline:

- clean tree → `check` passes
- a synthetic debt fixture (one function over the complexity threshold, written in the project's language) → `check` fails and names the file
- a stale entry injected into the temporary baseline → `check` reports it, `baseline --prune` removes it, `check` passes

Wire it into the project's test command so the gate is exercised on every CI run. The engine template itself is covered by the unit tests in the agent-ready plugin (`plugins/agent-ready/tests/`).

## Debt Fixture Snippets

One function over a threshold of 10, for the test template's "new debt fails" case. Fallow's default cyclomatic threshold is 20, so a fallow fixture needs at least 21 branches. This one has cyclomatic 22 and cognitive 21:

```
TS fallow  : export function qgFixture(n: number) { if (n===1) return 1; if (n===2) return 2; if (n===3) return 3; if (n===4) return 4; if (n===5) return 5; if (n===6) return 6; if (n===7) return 7; if (n===8) return 8; if (n===9) return 9; if (n===10) return 10; if (n===11) return 11; if (n===12) return 12; if (n===13) return 13; if (n===14) return 14; if (n===15) return 15; if (n===16) return 16; if (n===17) return 17; if (n===18) return 18; if (n===19) return 19; if (n===20) return 20; if (n===21) return 21; return 0; }
TS eslint  : export function qgFixture(n: number) { if (n===1) return 1; if (n===2) return 2; if (n===3) return 3; if (n===4) return 4; if (n===5) return 5; if (n===6) return 6; if (n===7) return 7; if (n===8) return 8; if (n===9) return 9; if (n===10) return 10; if (n===11) return 11; return 0; }
Ruby       : def qg_fixture(n) = n == 1 ? 1 : n == 2 ? 2 : n == 3 ? 3 : n == 4 ? 4 : n == 5 ? 5 : n == 6 ? 6 : n == 7 ? 7 : n == 8 ? 8 : n == 9 ? 9 : n == 10 ? 10 : n == 11 ? 11 : 0
Python     : def qg_fixture(n):\n    if n == 1: return 1\n    if n == 2: return 2\n    ... (12 branches)
Go         : func qgFixture(n int) int { switch n { case 1: return 1; ... case 12: return 12 }; return 0 }
```

Adapt the branch count to the project's configured threshold plus two.
