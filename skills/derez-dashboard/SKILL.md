# Skill: Company Reports Dashboard

## Goal

Create a Hermes dashboard plugin named **Company**.

The plugin automatically discovers every report inside:

```
company/reports/
```

and exposes each report as its own dashboard tab.

Examples:

```
company/reports/
    crm.md
    sales.md
    customers.md
    competitors.md
    hiring.md
```

becomes

```
Company
├── CRM
├── Sales
├── Customers
├── Competitors
└── Hiring
```

Each tab displays the rendered contents of its corresponding markdown file.

---

## Requirements

### Report Discovery

On initialization:

1. Scan `company/reports`.
2. Find every `.md` file.
3. Ignore hidden files.
4. Sort alphabetically.
5. Watch the directory for changes.
6. If a file is added or removed, update the tabs automatically.

---

### Tab Naming

Use the filename without extension.

Examples

```
crm.md
→ CRM

sales_pipeline.md
→ Sales Pipeline

customer-success.md
→ Customer Success
```

Convert:

- `_`
- `-`

into spaces.

Title Case everything except common acronyms.

Known acronyms:

- CRM
- ERP
- API
- AI
- HR
- KPI
- OKR
- SaaS

---

### Rendering

Reports contain completely unstructured markdown.

The plugin should render markdown beautifully using Hermes' native markdown components.

Support:

- headings
- tables
- bullet lists
- numbered lists
- task lists
- quotes
- code blocks
- mermaid diagrams (if Hermes supports them)
- images
- links
- emojis
- callouts
- horizontal rules

Never display raw markdown.

---

### Hermes Presentation Style

The goal is not merely rendering markdown.

Present the report in the Hermes dashboard style.

Use Hermes UI primitives including:

- Cards
- Sections
- Containers
- Panels
- Typography
- Alerts
- Accordions
- Tables
- Metrics
- Timeline (where applicable)

The UI should feel like a first-class Hermes dashboard rather than a document viewer.

---

### Automatic Enhancement

While preserving the markdown content, automatically improve presentation.

Examples:

# Tables

Render as responsive Hermes data tables.

# Metrics

If a section contains values like

```
Revenue: $5.2M
Customers: 128
Growth: 32%
```

promote them into metric cards.

# Status

Render statuses as badges.

Examples

```
Active
Blocked
Delayed
Done
Critical
```

become colored badges.

# Callouts

Render

```
NOTE
WARNING
IMPORTANT
TODO
```

using Hermes callout components.

# Lists

Long lists become grouped cards when appropriate.

# Links

Internal links should navigate within Hermes.

External links open safely in new tabs.

---

### Search

Provide search inside the Company dashboard.

The search filters:

- report tabs
- headings
- text

---

### Table of Contents

Every report should automatically generate a floating table of contents from headings.

---

### Deep Linking

Support URLs like

```
/dashboard/company/crm

/dashboard/company/sales

/dashboard/company/customers
```

Opening the URL selects the appropriate tab.

---

### Refresh

Provide a refresh action that rescans the directory.

---

### Empty State

If no reports exist:

Display a friendly Hermes empty state.

Example:

```
No company reports found.

Add markdown files to:

company/reports
```

Include an icon.

---

### Error State

If a markdown file cannot be read:

Show a Hermes error panel containing

- filename
- error
- retry button

The remaining reports should continue working.

---

### Performance

Large markdown files should:

- load lazily
- render incrementally if supported
- cache rendered output
- refresh when the source changes

---

### Accessibility

Follow Hermes accessibility conventions.

Support:

- keyboard navigation
- ARIA labels
- focus management
- high contrast themes

---

### Theme Support

Fully support:

- Light mode
- Dark mode

using Hermes theme tokens only.

No hardcoded colors.

---

### Architecture

Implement as a standard Hermes plugin.

Recommended structure:

```
company-dashboard/
    plugin.ts
    routes.ts
    discovery.ts
    markdown.ts
    parser.ts
    renderer.tsx
    components/
        ReportView.tsx
        Metrics.tsx
        TOC.tsx
        EmptyState.tsx
        ErrorState.tsx
```

---

### Future Compatibility

The discovery layer should make it easy to later support additional report formats such as

- .md
- .mdx
- .txt
- .json
- .yaml

without changing the dashboard UI.

---

## Desired User Experience

The Company dashboard should feel like a native Hermes module.

Users should simply drop markdown files into:

```
company/reports/
```

and immediately see professionally presented reports inside Hermes, each as its own tab, with polished navigation, rich rendering, automatic visual enhancements, search, deep-linking, and live updates—without requiring any configuration or manual registration.
