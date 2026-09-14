# Herdr review handoff

Use this only for the initial caller inside Herdr, not an agent already assigned `TEAM_CODE_REVIEW_COORDINATOR=1`.

## Discover the caller

Load the `herdr` skill and follow its session checks, CLI discovery, layout, and safety rules. If that skill is unavailable, verify `HERDR_ENV=1` and read `herdr --skill`. The installed CLI is authoritative; inspect `herdr --help`, `herdr agent`, and `herdr pane` before controlling panes.

Resolve the calling pane explicitly, never the UI-focused pane:

```bash
herdr pane current --current
herdr agent get <caller-pane-id>
```

Read the caller pane ID from `.result.pane.pane_id` and its recognized agent kind from `.result.agent.agent` in the agent-get response. Confirm the kind is supported by the installed `herdr agent` command. “Same type” means the same agent runtime/kind: pi → pi, Claude Code → claude, Codex → codex. Do not infer it from the underlying model provider, agent name, or another pane. Do not resume or clone the caller's conversation; the reviewer should have fresh context.

If detection fails, explain the problem and ask how to proceed rather than guessing a kind.

## Prepare an exact handoff

Before launching, resolve enough scope to make the task self-contained:

- Absolute repository/worktree path and caller working directory.
- Own-work versus another contributor's PR, including PR URL/number if applicable.
- Resolved base/head commit SHAs for a committed review.
- For uncommitted work, explicitly state whether staged, unstaged, and untracked files are included, and identify the intended files/hunks. Do not substitute `HEAD` for the working-tree diff or include unrelated edits.
- User constraints, non-goals, relevant context from the conversation, and known checks already run.
- Absolute path to this installation's `team-code-review/SKILL.md` so the child loads the same version.

The child can discover repository instructions and stack profiles itself. Do not perform the full review before delegating. Keep the reviewed files unchanged while it works; if the target changes, resolve the new scope and rerun the affected review rather than presenting stale findings.

## Launch one fresh coordinator

Inspect the caller's layout. Split right when wide, down when narrow/tall, keeping the caller's cwd and focus:

```bash
herdr pane layout --pane <caller-pane-id>
herdr pane split --current --direction <right-or-down> --cwd "$PWD" --no-focus
```

Read the new pane ID from `.result.pane.pane_id`. Choose a unique valid agent name after checking `herdr agent list`, then start the detected caller kind in that new shell pane:

```bash
herdr agent start <reviewer-name> --kind <caller-kind> --pane <new-pane-id>
```

Do not create a workspace, tab, worktree, or additional coordinator panes unless requested. Do not bypass approval or permission controls. If startup fails, inspect the created pane before retrying; avoid duplicate agents.

Submit a self-contained prompt through `herdr agent prompt`, safely quoted as a single argument, with this structure:

```text
TEAM_CODE_REVIEW_COORDINATOR=1
You are the delegated review coordinator, not the implementation agent.
Read <absolute-skill-path> and execute team-code-review steps 1–4 on the target below. Skip the initial Herdr handoff; do not spawn another coordinator. Use native subagents for specialists if available; otherwise investigate the six lenses sequentially and disclose that limitation. Pass the coordinator marker to specialists that may load the skill.
Target: <repository, authorship branch, PR if applicable, exact base/head or working-tree scope>
Context and constraints: <relevant caller context>
Keep the review read-only: do not edit source, stage, commit, fix findings, or draft/publish PR comments. Verify candidate findings and return the complete report, including checks performed and limitations, here in the pane.
```

## Collect and return the report

Use `herdr agent prompt <reviewer-name> <prompt> --wait --timeout 120000`. A timeout is not completion: inspect `agent get` and `agent read`, then continue with `agent wait` as needed rather than resubmitting the review. For `blocked`, inspect the requested approval/question and surface anything requiring the user; do not automatically approve it. An `unknown` state is not proof of completion either.

Read the completed report with `herdr agent read <reviewer-name> --source recent-unwrapped --lines 200`. Confirm the report actually finished; an idle/done startup state alone is not a completed review. If output is truncated on the alternate screen, follow the Herdr skill's fallback: ask the reviewer to save the complete report to a temporary Markdown file and return its path, then read that file. Do not request file output in the initial prompt.

Relay the verified findings, assessment, checks, and limitations to the user, identifying the reviewer pane. The delegated coordinator is responsible for specialist verification; do not claim to have independently repeated its checks in the caller. For another contributor's PR, ask the user in the original conversation before drafting or publishing anything. Leave the pane available for inspection; do not close it automatically.
