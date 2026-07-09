# AGENTS.md

This file is the **agent-facing** guide to the `derez-company` skill suite. It explains how agents should interact with the skills, the architecture of the system, and how to contribute new skills.

---

## Architecture

The `derez-company` suite follows a **layered agent architecture**:

```
┌─────────────────────────────────────────────┐
│            User / Company Agent             │  Orchestrates tasks
├─────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │derez-crm │  │marketing │  │  sales   │  │  Composable skills
│  │ (data)   │  │(business)│  │(business)│  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│            Markdown Filesystem              │  Single source of truth
│     company/crm/  company/marketing/ ...     │
└─────────────────────────────────────────────┘
```

### Layers

1. **Data skills** — Manage raw data storage (`derez-crm`). These are pure CRUD: create, read, update, search, report. No business logic.
2. **Business skills** — Use data skills to perform actual work (marketing campaigns, sales outreach, etc.). They call data skills via the agent runtime.
3. **Orchestrator** — The user's company agent decides which skills to invoke based on the task.

---

## Agent Interaction Rules

### Data skills return file paths, not content

When a data skill is asked for leads, it returns a list of file paths. The calling agent is responsible for opening and reading the files.

```
# Correct
company/crm/leads/acme-corp.md
company/crm/leads/john-smith.md

# Incorrect
Lead: John Smith, Company: Acme Corp, Status: warm...
```

This keeps data skills focused on indexing and prevents them from becoming bottlenecks.

### Skills are company-agnostic

No skill in this repository contains company-specific logic, branding, or strategy. Skills are installed into a company workspace. The company agent provides the context.

### Business skills never write raw storage

A marketing skill does not write to `company/crm/leads/`. It calls the CRM skill to create or update leads. This prevents conflicts between agents.

### Skills use `rg` for searching

All searching is done with `ripgrep` (`rg`). This is fast, works on Markdown files, and requires no indexing.

---

## How to Use a Skill

### For agents

When a user asks you to perform a task:

1. Identify which skill(s) are relevant.
2. Read the skill's `SKILL.md` for instructions.
3. Follow the skill's storage layout, format, and query rules.
4. If the skill is a **data skill**, return file paths for further processing.
5. If the skill is a **business skill**, execute the task according to its playbook.

### For humans

Install a skill from [derez.ai](https://derez.ai) or add it to your Hermes configuration. Then tell your agent which skills are available.

---

## How to Contribute a New Skill

### File structure

```
skills/your-skill-name/
└── SKILL.md
```

### SKILL.md requirements

Every skill must have a `SKILL.md` that defines:

| Section | Required | Description |
|---|---|---|
| `# Skill: <name>` | ✅ | The skill's identifier |
| `## Purpose` | ✅ | What the skill does and does not do |
| `## Storage Layout` | ✅ | The directory structure the skill manages |
| `## Responsibilities` | ✅ | Explicit list of allowed and forbidden actions |
| `## Format` | ✅ | Data format (YAML frontmatter, Markdown body) |
| Query behavior | ✅ | How agents should search and retrieve data |

### Design principles

1. **Markdown is the database.** Every record is a single Markdown file with YAML frontmatter.
2. **Configuration is data-driven.** Never hardcode business rules. Read them from Markdown config files.
3. **Strict separation of concerns.** Data skills manage storage. Business skills execute work.
4. **Human-editable at all times.** A human with a text editor should be able to work with the data.
5. **Prefer `rg` for searching.** No databases, no APIs, no indexing services.
6. **Return file paths, not content.** When another agent can do the next step, return the path.

### Naming convention

- Skill directory: `kebab-case`
- Prefix: `derez-` (e.g., `derez-crm`, `derez-marketing`, `derez-sales`)
- Data files: `kebab-case.md`

---

## Testing

Skills in this repository are tested on:

- **Hermes Agent** — The open-source agent runtime by Nick Sieger.
- **[derez.ai](https://derez.ai)** — The hosted platform where skills are available for one-click install.

Before submitting a new skill, verify it works correctly in both environments.

---

## Roadmap

| Area | Status | Notes |
|---|---|---|
| CRM (`derez-crm`) | ✅ Live | Core data management complete |
| Marketing (`derez-marketing`) | 🚧 In progress | Campaign tracking, content pipelines |
| Sales (`derez-sales`) | 🚧 In progress | Outreach sequencing, deal tracking |
| HR | 📋 Planned | Employee records, onboarding |
| Finance | 📋 Planned | Invoicing, expense tracking |
| Operations | 📋 Planned | Project tracking, task management |

---

## Notes for Agents

- You are reading this file because you are operating in a `derez-company` workspace.
- Before performing any business operation, check whether a skill exists for that domain.
- If a skill exists, read its `SKILL.md` and follow its instructions.
- If no skill exists, ask the user whether they'd like to create one or contribute it.
- Never modify a skill's `SKILL.md` unless you are explicitly asked to improve the skill itself.
- When in doubt, return file paths — the user or another agent can open them.