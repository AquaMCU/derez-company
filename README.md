# derez-company

**Company-in-a-box skill suite for AI agents.**

A collection of composable, company-agnostic [Hermes](https://github.com/nicksieger/hermes-agent) skills that give AI agents the ability to manage real business operations — CRM, marketing, sales, and more — using plain Markdown files as the database.

Every skill is designed to be:

- **Portable** — works with any agent runtime (Hermes Agent, [derez.ai](https://derez.ai), and others).
- **Composable** — skills are independent and can be mixed and matched.
- **Human-readable** — all data is plain Markdown with YAML frontmatter, editable by humans and machines.
- **One-click installable** — available on [derez.ai](https://derez.ai) and compatible with Hermes Agent.

---

## Skills

| Skill | Area | Status | Description |
|---|---|---|---|
| `derez-crm` | CRM | ✅ Live | Markdown-based CRM data management — leads, funnel, config, reports |
| `derez-marketing` | Marketing | 🚧 Coming soon | Campaign tracking, content pipelines, channel analytics |
| `derez-sales` | Sales | 🚧 Coming soon | Outreach sequencing, deal tracking, sales playbooks |

---

## Structure

```
derez-company/
├── skills/
│   ├── derez-crm/          # CRM skill
│   │   └── SKILL.md
│   ├── derez-marketing/    # (coming soon)
│   └── derez-sales/        # (coming soon)
├── AGENTS.md               # Agent architecture & contribution guide
├── LICENSE
└── README.md
```

When a company installs a skill, the agent creates the corresponding data directory:

```
company/
├── crm/                    # Created by derez-crm
│   ├── config/
│   ├── leads/
│   └── templates/
├── marketing/              # Created by derez-marketing
├── sales/                  # Created by derez-sales
└── reports/
```

---

## Getting Started

### Hermes Agent

1. Add the skill to your Hermes configuration.
2. Reference the skill path in your agent's instructions.
3. The skill handles all CRM data operations — your agent focuses on the actual work.

### [derez.ai](https://derez.ai)

Visit [derez.ai](https://derez.ai), search for the skill, and install with one click. The skill is immediately available for your company workspace.

---

## Design Philosophy

### Markdown is the database

Every record is a single Markdown file. YAML frontmatter stores structured fields; the body contains free-form notes. No database, no API, no lock-in.

### Configuration is data-driven

Skills never hardcode business logic. Funnel stages, statuses, strategies, and sources are all read from Markdown configuration files. Change your process by editing a file.

### Strict separation of concerns

- **Data skills** (`derez-crm`) manage storage, validation, and retrieval. They never perform business-specific work.
- **Business skills** (marketing, sales) interpret data and execute actions. They never manage raw storage.

This keeps skills composable and prevents conflicts between agents.

---

## License

MIT