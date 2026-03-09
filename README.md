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
