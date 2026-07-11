# Agent Skills

A collection of skills for AI coding agents. Skills are packaged instructions and scripts that extend agent capabilities.

Skills follow the [Agent Skills](https://agentskills.io/) format.

---

## Installation

```bash
npx skills add dgalarza/agent-skills
```

---

## Skills

| Skill | Description |
|-------|-------------|
| [Buffer](skills/buffer/) | Schedule posts, manage queues, and save ideas via the Buffer social media API |
| [Buttondown](skills/buttondown/) | Manage tags, automations, subscribers, and emails via the Buttondown newsletter API |
| [Conventional Comments](skills/conventional-comments/) | Write structured review feedback using the Conventional Comments format |
| [CreatorSignal API](skills/creatorsignal-api/) | Submit video ideas for AI validation, poll for scored verdicts, manage channels and webhooks via the CreatorSignal API |
| [Team Code Review](skills/team-code-review/) | Dispatch specialist agents to review code and verify every finding before reporting it |

---

## Buffer

```bash
npx skills add dgalarza/agent-skills --skill buffer
```

Requires a `BUFFER_API_TOKEN` environment variable. Generate one at [publish.buffer.com/settings/api](https://publish.buffer.com/settings/api).

```bash
export BUFFER_API_TOKEN=your_token_here
```

See the [Buffer API documentation](https://buffer.com/developers/api) for full API reference.

---

## Buttondown

```bash
npx skills add dgalarza/agent-skills --skill buttondown
```

Requires a `BUTTONDOWN_API_KEY` environment variable. Generate one at [buttondown.com/requests](https://buttondown.com/requests).

```bash
export BUTTONDOWN_API_KEY=your_api_key_here
```

See the [Buttondown API documentation](https://api.buttondown.com/v1/docs) for full API reference.

---

## Conventional Comments

```bash
npx skills add dgalarza/agent-skills --skill conventional-comments
```

Use this skill to write or rewrite code review, document review, design feedback, RFC comments, and editing notes in the [Conventional Comments](https://conventionalcomments.org/) format.

---

## CreatorSignal API

```bash
npx skills add dgalarza/agent-skills --skill creatorsignal-api
```

Requires a `CS_API_KEY` environment variable. Generate one at Settings > API Keys in your [CreatorSignal account](https://app.creatorsignal.io).

```bash
export CS_API_KEY=cs_live_<prefix>_<secret>
```

Includes a polling helper script for validation results and reference docs for webhook integration.

---

## Team Code Review

```bash
npx skills add dgalarza/agent-skills --skill team-code-review
```

Use this skill to dispatch focused reviewers across architecture, readability, testing, maintainability, security, and documentation. The coordinating agent independently verifies every candidate finding before reporting it.

---

## Adding a Skill

Each skill lives in its own directory under `skills/` with a `SKILL.md` file:

```
skills/
└── my-skill/
    └── SKILL.md
```

The `SKILL.md` frontmatter defines the skill name, description, and allowed tools:

```markdown
---
name: my-skill
description: What this skill does and when to use it.
allowed-tools: Bash(curl:*)
---

# Skill instructions...
```

---

## License

MIT
