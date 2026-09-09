---
name: sentry
description: >
  Investigate and debug Sentry issues using the Sentry REST API. Use when the user
  pastes a Sentry issue URL, asks to look up a Sentry issue, asks to scan a project
  for Sentry errors, or mentions debugging production errors tracked in Sentry.
  Triggers: Sentry URLs containing "/issues/", "check sentry", "sentry errors",
  "scan for issues", "production errors", "what's firing in sentry".
---

# Sentry Issue Investigation

Investigate Sentry issues and scan projects for errors using
`scripts/sentry_api.py`.

## Prerequisites

Config file `~/.sentryclirc` must exist:

```ini
[defaults]
url=https://your-sentry-instance.example.com/

[auth]
token=sntryu_...
```

## Workflows

### 1. Investigate a Sentry Issue URL

When the user pastes a Sentry URL:

```bash
uv run <skill-dir>/scripts/sentry_api.py issue "<URL>"
```

Then get context field distributions if the issue has repeated events:

```bash
uv run <skill-dir>/scripts/sentry_api.py events "<URL>" --field <field_name> --limit 100
```

Pick `--field` from the context keys shown in the issue output (e.g.
`extension_alert_type`, `error_message`).

After gathering data:

1. Identify the error message, exception type, and relevant context fields
2. Use `Grep` to find the error string in the local codebase
3. Read the source file to understand the code path
4. Propose a fix with rationale

### 2. Scan a Project for Issues

Infer the project slug from the current git remote name (e.g. `origin` URL's
repo name). Then:

```bash
uv run <skill-dir>/scripts/sentry_api.py list --project <project-slug> --limit 25
```

Present the issues as a table and ask the user which to investigate. Then follow
workflow 1.

Optional flags:

- `--org <slug>` (default: `sentry`)
- `--environment <env>` (default: `live`)
- `--query "<sentry query>"` (default:
  `is:unresolved issue.priority:[high, medium]`)

## Script Reference

All commands use `uv run <skill-dir>/scripts/sentry_api.py`.

| Command                                                                | Purpose                                                            |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `issue <url>`                                                          | Fetch issue metadata, latest event, stack trace, tags, breadcrumbs |
| `events <url> [--field F] [--limit N]`                                 | Fetch N events; optionally aggregate by context field F            |
| `list --project P [--org O] [--environment E] [--query Q] [--limit N]` | List issues matching filters                                       |
