# AGENTS.md

This file is the **agent-facing** guide to the `derez-company` skill suite. It explains how agents should interact with the plugin, the architecture of the system, and how to contribute new skills.

---

## Architecture

The `derez-company` repository is a **single Hermes plugin** that bundles multiple components:

```
derez-company/
├── plugin.yaml              # Hermes plugin manifest — discovery entry point
├── __init__.py              # register(ctx) — hooks, slash commands, skill registration
├── dashboard/
│   ├── manifest.json        # Standard Hermes dashboard manifest (entry, tab, api, css)
│   ├── plugin_api.py        # FastAPI APIRouter — serves report data to the frontend
│   └── dist/
│       ├── index.js         # Frontend JS bundle — renders the Company tab
│       └── style.css        # Minimal CSS reset
├── discovery.py             # Scans company/reports/ for .md files
├── markdown_renderer.py     # Parses markdown into enhanced structure
├── renderer.py              # Transforms into dashboard UI primitives
├── skills/
│   ├── derez-crm/           # CRM data management skill
│   │   └── SKILL.md
│   └── derez-dashboard/     # Dashboard specification skill
│       └── SKILL.md
├── README.md
├── AGENTS.md
└── LICENSE
```

### Layers

1. **Data skills** (`skills/derez-crm/`) — Manage raw data storage. Pure CRUD: create, read, update, search, report. No business logic. Skills are registered via `ctx.register_skill()` in `__init__.py`.
2. **Dashboard plugin** (`dashboard/`) — Standard Hermes dashboard plugin. The `manifest.json` uses the standard schema (`entry`, `tab`, `api`, `css`) that Hermes actually reads. The frontend JS is loaded as an iframe entry. The backend is a FastAPI `APIRouter` mounted automatically by Hermes.
3. **Presentation skills** (`skills/derez-dashboard/SKILL.md`) — These are specifications only. The actual implementation is the dashboard plugin.
4. **Business skills** (future: `derez-marketing`, `derez-sales`) — Use data skills to perform actual work.

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

## How to Use the Plugin

### For agents

When a user asks you to perform a task:

1. Check whether a skill exists for that domain under `skills/`.
2. If it exists, read its `SKILL.md` and follow its instructions.
3. If the skill is a **data skill**, return file paths for further processing.
4. If the skill is a **presentation skill**, its `SKILL.md` is a specification — the actual dashboard implementation lives in `dashboard/`.
5. If no skill exists, note it — the user may want to create one.

### For humans

Install with one command:

```bash
hermes plugins install https://github.com/AquaMCU/derez-company.git
hermes plugins enable derez-company
```

---

## Dashboard Plugin Structure (Standard Hermes Schema)

The `dashboard/manifest.json` uses the standard Hermes dashboard plugin schema, not custom fields. This is critical for compatibility.

### Required manifest fields

```json
{
  "name": "derez-company",
  "label": "Company",
  "icon": "building",
  "tab": { "path": "/company" },
  "entry": "dist/index.js",
  "css": "dist/style.css",
  "api": "plugin_api.py"
}
```

| Field | Purpose |
|---|---|
| `name` | Plugin identifier — must match `plugins.enabled` name |
| `label` | Display name shown in the dashboard tab |
| `icon` | Icon identifier |
| `tab.path` | Route path for the tab (e.g. `/dashboard/company`) |
| `entry` | JS bundle path (relative to `dashboard/`). The frontend loads this as an iframe. |
| `css` | Optional CSS file path |
| `api` | Python file with a FastAPI `APIRouter` named `router`. Hermes mounts this automatically. |

### What NOT to do

The following **custom fields are ignored** by Hermes and must not be used:

```json
{
  "handler_module": "...",   // ✗ NOT read by Hermes
  "handlers": { ... },      // ✗ NOT read by Hermes
  "routes": { ... }         // ✗ NOT read by Hermes
}
```

### How the frontend works

1. Hermes reads `manifest.json` and discovers `entry`, `api`, and `tab`.
2. The frontend loads `dist/index.js` inside an iframe at `/dashboard/company`.
3. The JS bundle calls the plugin API at `/api/plugins/derez-company/`.
4. The API is served by `plugin_api.py` — a FastAPI `APIRouter` that Hermes mounts automatically.
5. The frontend self-renders using inline styles (no external dependencies).

### API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/plugins/derez-company/tabs` | GET | List all discovered report tabs |
| `/api/plugins/derez-company/report/{tab_id}` | GET | Get rendered content for a tab |
| `/api/plugins/derez-company/toc/{tab_id}` | GET | Get table of contents for a tab |
| `/api/plugins/derez-company/scan` | POST | Force rescan of `company/reports/` |
| `/api/plugins/derez-company/search?q=...` | GET | Search across all reports |

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

### Register a new bundled skill

Add it to `plugin.yaml` under the `skills:` list:

```yaml
skills:
  - name: your-skill-name
    path: skills/your-skill-name
    description: What it does
```

The `__init__.py` will call `ctx.register_skill()` for it automatically.

### Design principles

1. **Markdown is the database.** Every record is a single Markdown file with YAML frontmatter.
2. **Configuration is data-driven.** Never hardcode business rules. Read them from Markdown config files.
3. **Strict separation of concerns.** Data skills manage storage. Business skills execute work.
4. **Human-editable at all times.** A human with a text editor should be able to work with the data.
5. **Prefer `rg` for searching.** No databases, no APIs, no indexing services.
6. **Return file paths, not content.** When another agent can do the next step, return the path.

### Naming convention

- Skill directory: `kebab-case`
- Prefix: `derez-` for agent skills (e.g., `derez-crm`, `derez-marketing`, `derez-sales`)
- Data files: `kebab-case.md`

---

## How to Contribute to the Dashboard Plugin

The dashboard is a standard Hermes plugin inside `dashboard/`. To modify it:

1. Edit `dashboard/plugin_api.py` to add or change API endpoints.
2. Edit `dashboard/dist/index.js` to change the frontend rendering.
3. The `manifest.json` uses the standard schema — do not add custom fields.

### Testing locally

```bash
# Install the plugin from local path
ln -s $(pwd) ~/.hermes/plugins/derez-company
hermes plugins enable derez-company
```

Restart Hermes and open the dashboard. The "Company" tab appears at `/dashboard/company`.

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
| Dashboard (`dashboard`) | ✅ Live | Hermes plugin — report discovery & rendering |
| Marketing (`derez-marketing`) | 🚧 In progress | Campaign tracking, content pipelines |
| Sales (`derez-sales`) | 🚧 In progress | Outreach sequencing, deal tracking |
| HR | 📋 Planned | Employee records, onboarding |
| Finance | 📋 Planned | Invoicing, expense tracking |
| Operations | 📋 Planned | Project tracking, task management |

---

## Notes for Agents

- You are reading this file because you are operating in a `derez-company` workspace.
- This entire repository is one Hermes plugin. Skills are bundled inside `skills/` and registered via `plugin.yaml`.
- Before performing any business operation, check whether a skill exists for that domain.
- If a skill exists, read its `SKILL.md` and follow its instructions.
- If no skill exists, ask the user whether they'd like to create one or contribute it.
- Never modify a skill's `SKILL.md` unless you are explicitly asked to improve the skill itself.
- When in doubt, return file paths — the user or another agent can open them.
- For dashboard issues: check `dashboard/manifest.json` uses standard Hermes schema (`entry`, `tab`, `api`), not custom fields.