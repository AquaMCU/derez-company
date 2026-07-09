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
| `dashboard` | Dashboard | ✅ Live | Hermes dashboard plugin — auto-discovers and renders reports from `company/reports/` |
| `derez-marketing` | Marketing | 🚧 Coming soon | Campaign tracking, content pipelines, channel analytics |
| `derez-sales` | Sales | 🚧 Coming soon | Outreach sequencing, deal tracking, sales playbooks |

---

## Structure

```
derez-company/
├── skills/
│   ├── dashboard/           # Hermes dashboard plugin
│   │   └── SKILL.md
│   ├── derez-crm/           # CRM data skill
│   │   └── SKILL.md
│   ├── derez-marketing/     # (coming soon)
│   └── derez-sales/         # (coming soon)
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

### One-command install

```bash
hermes plugins install https://github.com/AquaMCU/derez-company.git
```

This clones the repo into `~/.hermes/plugins/derez-company/`, registers all bundled skills, and activates the Company Reports Dashboard tab.

After install, enable the plugin:

```bash
hermes plugins enable derez-company
```

Restart Hermes. The **Company** tab appears in the dashboard, and bundled skills (`derez-crm`, `derez-dashboard`) are available to your agent.

### Manual install

```bash
git clone https://github.com/AquaMCU/derez-company.git ~/.hermes/plugins/derez-company
hermes plugins enable derez-company
```

### [derez.ai](https://derez.ai)

Visit [derez.ai](https://derez.ai), search for "derez-company", and install with one click.

---

## Design Philosophy

### Markdown is the database

Every record is a single Markdown file. YAML frontmatter stores structured fields; the body contains free-form notes. No database, no API, no lock-in.

### Configuration is data-driven

Skills never hardcode business logic. Funnel stages, statuses, strategies, and sources are all read from Markdown configuration files. Change your process by editing a file.

### Strict separation of concerns

- **Data skills** (`derez-crm`) manage storage, validation, and retrieval. They never perform business-specific work.
- **Business skills** (marketing, sales) interpret data and execute actions. They never manage raw storage.
- **Presentation skills** (`dashboard`) render data into UIs. They consume reports and files but never modify them.

This keeps skills composable and prevents conflicts between agents.

---

## License

MIT