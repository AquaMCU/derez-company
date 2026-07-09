# Skill: `derez-crm`

## Purpose

`derez-crm` is a generic Markdown CRM data management skill for Hermes.

It is **company-agnostic** and **never performs company-specific work** (email drafting, research, outreach, sales strategy, etc.). Its only responsibility is managing CRM data stored as Markdown files.

The skill acts as the source of truth for CRM information while allowing other Hermes skills to perform the actual work.

---

# Storage Layout

```
company/
├── crm/
│   ├── config/
│   │   ├── funnel.md
│   │   ├── strategies.md
│   │   ├── sources.md
│   │   ├── statuses.md
│   │   └── affiliates.md
│   │
│   ├── leads/
│   │   ├── acme-corp.md
│   │   ├── john-smith.md
│   │   └── ...
│   │
│   └── templates/
│       └── lead.md
│
└── reports/
    └── crm.md
```

---

# Source of Truth

Every lead is stored as a single Markdown file.

The YAML frontmatter is authoritative.

The Markdown body contains free-form notes.

---

# Lead Format

```md
---
name: John Smith
company: Acme Corp

status: warm

funnel: discovery

next_date: 2026-07-15

strategy:
  - outbound
  - linkedin

source: referral

affiliate_code: AFF-001

owner:

value: 2500

probability: 40

created: 2026-07-01
updated: 2026-07-08
last_contact: 2026-07-08

tags:
  - saas
  - us

---

# Notes

Interested in AI automation.

Waiting until next week.
```

---

# Default Status List

```
cold
warm
hot
won
lost
blacklisted
```

---

# Funnel Configuration

Configured in

```
company/crm/config/funnel.md
```

Example

```md
lead
contacted
qualified
discovery
proposal
negotiation
won
lost
```

The skill never hardcodes funnel stages.

It always reads the configuration.

---

# Strategy Configuration

```
company/crm/config/strategies.md
```

Example

```md
outbound
cold_email
linkedin
affiliate
conference
partner
content
referral
```

---

# Source Configuration

```
company/crm/config/sources.md
```

Example

```md
website
twitter
reddit
linkedin
conference
affiliate
referral
cold_email
```

---

# Affiliate Configuration

```
company/crm/config/affiliates.md
```

Optional.

Defines valid affiliate codes.

---

# Status Configuration

```
company/crm/config/statuses.md
```

Default

```md
cold
warm
hot
won
lost
blacklisted
```

---

# Reports

CRM reports are written to

```
company/reports/crm.md
```

The report contains exactly these sections.

```
# CRM Report

## Funnel Report

## Affiliate Report

## Strategy Performance

## Source Performance
```

No other sections are created unless requested.

---

# Responsibilities

The skill may

* create leads
* update leads
* archive leads
* rename leads
* move leads
* update YAML fields
* append notes
* generate CRM reports
* validate configuration
* search CRM data

The skill may NOT

* draft emails
* research companies
* summarize businesses
* perform outreach
* create marketing content
* generate company-specific recommendations
* contact customers
* interpret sales strategy

Those responsibilities belong to other Hermes skills.

---

# Searching

Searching is performed using **ripgrep (rg)**.

Examples

Find all warm leads

```
rg "^status: warm$" company/crm/leads
```

Find proposal stage

```
rg "^funnel: proposal$" company/crm/leads
```

Find affiliate

```
rg "^affiliate_code: AFF-001$" company/crm/leads
```

Find source

```
rg "^source: referral$" company/crm/leads
```

---

# Query Behavior

The skill never returns large lead summaries.

If another agent requests leads, only return file paths.

Example

User

> Show all leads I need to work on today.

Response

```
company/crm/leads/acme-corp.md
company/crm/leads/john-smith.md
company/crm/leads/example.md
```

The next agent is responsible for opening those files.

This keeps the CRM skill focused on indexing rather than interpretation.

---

# Updating Leads

When modifying a lead

* preserve existing notes
* preserve unknown YAML fields
* update `updated`
* never remove fields unless explicitly requested
* keep YAML keys ordered
* maintain valid Markdown

---

# Creating Leads

New leads are created inside

```
company/crm/leads/
```

Filename

```
company-name.md
```

or

```
person-name.md
```

using kebab-case.

---

# CRM Report Generation

The report is regenerated when requested.

Output file

```
company/reports/crm.md
```

Sections

## Funnel Report

Counts leads by funnel stage.

Example

```
Lead ............. 15
Qualified ........ 8
Discovery ........ 6
Proposal ......... 4
Negotiation ...... 2
Won .............. 12
Lost ............. 7
```

---

## Affiliate Report

Groups by affiliate code.

Displays

* total leads
* won
* lost
* active

---

## Strategy Performance

Groups by strategy.

Displays

* leads
* active
* won
* lost

---

## Source Performance

Groups by source.

Displays

* leads
* active
* won
* lost

---

# Design Principles

* Markdown is the database.
* YAML frontmatter is authoritative.
* Configuration is data-driven.
* No company-specific logic.
* One lead per file.
* Human-editable at all times.
* Prefer `rg` for searching.
* Return file paths instead of lead contents whenever another agent can perform the next step.
* Keep responsibilities strictly limited to CRM data management.
