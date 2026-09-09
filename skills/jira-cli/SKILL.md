---
name: jira-cli
description: Jira issue management via the `jira` CLI tool. Use when working with Jira tickets - creating issues, listing/searching issues, viewing issue details, transitioning status (e.g., "In Progress", "Done"), assigning users, adding comments, managing sprints, or any Jira-related task. Triggers on requests like "create a Jira ticket", "list my issues", "move ticket to In Progress", "assign issue to me".
---

# Jira CLI

Interactive command-line tool for Atlassian Jira. Requires prior `jira init`
setup.

## Authentication

The API token can be provided via:

1. **Keychain** (recommended) - Most secure; token retrieved automatically
2. **Environment variable** - `JIRA_API_TOKEN`
3. **`.netrc` file**

If commands work without `JIRA_API_TOKEN` set, keychain is configured. Do not
assume the env var is required.

## Quick Reference

```bash
# Identity
jira me                              # Get current username

# Issues
jira issue list                      # List recent issues
jira issue list -a$(jira me)         # My assigned issues
jira issue view ISSUE-1              # View issue details
jira issue create                    # Create (interactive)
jira issue create -tBug -s"Summary" -yHigh -b"Description" --no-input

# Status/Assignment
jira issue move ISSUE-1 "In Progress"
jira issue move ISSUE-1 Done -RFixed
jira issue assign ISSUE-1 $(jira me) # Assign to self
jira issue assign ISSUE-1 x          # Unassign

# Comments (body is positional arg, NOT -b)
jira issue comment add ISSUE-1 "Short comment"
cat <<'EOF' | jira issue comment add ISSUE-1   # Multi-line
Long comment here.
EOF

# Navigation
jira open ISSUE-1                    # Open in browser
```

## Issue Operations

### List Issues

```bash
jira issue list                           # Recent issues
jira issue list -a$(jira me)              # Assigned to me
jira issue list -r$(jira me)              # Reported by me
jira issue list -s"To Do"                 # By status
jira issue list -yHigh                    # By priority
jira issue list -tBug                     # By type
jira issue list --created -7d             # Created last 7 days
jira issue list --created month           # Created this month
jira issue list -lbackend                 # By label
jira issue list -w                        # Issues I'm watching
jira issue list -q "summary ~ cli"        # Raw JQL query
jira issue list --plain                   # Plain text output (for scripts)
jira issue list --plain --no-headers      # No headers (for parsing)
```

Combine flags:
`jira issue list -a$(jira me) -yHigh -s"In Progress" --created month`

### View Issue

```bash
jira issue view ISSUE-1              # Full details
jira issue view ISSUE-1 --comments 5 # Include 5 recent comments
```

### Create Issue

```bash
# Interactive
jira issue create

# Non-interactive
jira issue create -tTask -s"Summary" -b"Description" --no-input
jira issue create -tBug -s"Bug title" -yHigh -lurgent -b"Steps to reproduce" --no-input

# With epic parent
jira issue create -tStory -s"Story title" -PEPIC-42 --no-input
```

Flags: `-t` type, `-s` summary, `-b` body, `-y` priority, `-l` label, `-a`
assignee, `-P` parent/epic, `--fix-version`

**Gotcha — hangs without a TTY.** `jira issue create` (and other write commands)
**hang indefinitely when run without a controlling TTY** — in a backgrounded
shell or any non-interactive agent harness — because the CLI blocks on a stdin
read even with `--no-input`. Run in the foreground and redirect stdin from
`/dev/null`:

```bash
jira issue create --no-input -tTask -s"Summary" -b"Body" </dev/null
```

Create one issue per command. Don't batch several creates into one long-running
block — harnesses tend to background long blocks, which triggers the hang.

### Edit Issue

```bash
jira issue edit ISSUE-1 -s"New summary" --no-input
jira issue edit ISSUE-1 -yHigh -lnew-label --no-input
jira issue edit ISSUE-1 --label -old --label new  # Remove old, add new
```

### Move/Transition Status

```bash
jira issue move ISSUE-1 "In Progress"
jira issue move ISSUE-1 "Done"
jira issue move ISSUE-1 Done -RFixed              # With resolution
jira issue move ISSUE-1 Done --comment "Completed"
jira issue move ISSUE-1 Done -a$(jira me)         # Assign while moving
```

### Assign Issue

```bash
jira issue assign ISSUE-1 $(jira me)    # Assign to self
jira issue assign ISSUE-1 "John Doe"    # Assign to user
jira issue assign ISSUE-1 default       # Default assignee
jira issue assign ISSUE-1 x             # Unassign
```

### Comments

**Important:** `comment add` does NOT support `-b`. The comment body is a
positional argument or piped via stdin/template. Do not confuse with
`issue create -b` which sets the issue body.

```bash
# Short comment — positional argument (second arg after ISSUE-KEY)
jira issue comment add ISSUE-1 "Comment text"

# Long/multi-line comment — use heredoc piped to stdin (preferred)
cat <<'EOF' | jira issue comment add ISSUE-1
Multi-line comment body here.

Supports **markdown** formatting.
EOF

# Long comment — write to temp file, pass via --template
TMPFILE=$(mktemp) && cat <<'EOF' > "$TMPFILE"
Long comment body with **markdown**.
EOF
jira issue comment add ISSUE-1 --template "$TMPFILE" && rm -f "$TMPFILE"

# From existing file
jira issue comment add ISSUE-1 --template /path/to/file.md

# Simple pipe
echo "Comment from stdin" | jira issue comment add ISSUE-1
```

### Link Issues

```bash
jira issue link ISSUE-1 ISSUE-2 Blocks
jira issue link ISSUE-1 ISSUE-2 "is blocked by"
jira issue unlink ISSUE-1 ISSUE-2
```

### Clone/Delete

```bash
jira issue clone ISSUE-1
jira issue clone ISSUE-1 -s"New summary" -a$(jira me)
jira issue delete ISSUE-1
jira issue delete ISSUE-1 --cascade  # Include subtasks
```

## Epics

```bash
jira epic list                        # List epics
jira epic list --table                # Table view
jira epic list EPIC-1                 # Issues in epic
jira epic create -n"Epic Name" -s"Summary" -b"Description"
jira epic add EPIC-1 ISSUE-1 ISSUE-2  # Add issues to epic
jira epic remove ISSUE-1 ISSUE-2      # Remove from epic
```

## Sprints

```bash
jira sprint list                      # List sprints
jira sprint list --current            # Current sprint issues
jira sprint list --current -a$(jira me)
jira sprint list --prev               # Previous sprint
jira sprint list --next               # Next sprint
jira sprint list SPRINT_ID            # Specific sprint
jira sprint add SPRINT_ID ISSUE-1     # Add to sprint
```

## Output Formats

```bash
--plain          # Plain text (no interactive UI)
--no-headers     # Skip headers
--columns key,summary,status  # Select columns
--raw            # JSON output
--csv            # CSV output
```

## Query Gotchas (Important)

```bash
# 1) Avoid ORDER BY inside `-q` JQL in jira-cli.
# Some versions return parse errors like "Expecting ',' but got 'ORDER'".
# Prefer CLI sorting flags instead.
jira issue list -q "project = PROJ AND issuetype = Bug AND created >= -24h" \
  --order-by created --reverse --plain

# 2) For "last 24 hours", prefer `--created -24h`.
# (jira-cli supports d/h/m units, e.g. -10d, -24h, -90m)
jira issue list -q "project = PROJ AND issuetype = Bug" --created -24h --plain

# 3) If relative windows look suspicious, rerun with absolute timestamp.
# macOS:
SINCE=$(date -v-24H '+%Y-%m-%d %H:%M')
# Linux:
SINCE=$(date -d '24 hours ago' '+%Y-%m-%d %H:%M')
jira issue list -q "project = PROJ AND issuetype = Bug AND created >= '$SINCE'" --plain

# 4) For automation/parsing, use stable output flags.
jira issue list -q "project = PROJ" --plain --no-headers --columns key,summary,status,assignee,created
```

Notes:

- `jira issue list` exits with code `1` when no results are found. Treat this as
  an empty result set, not always a command failure.
- Jira/JQL time filters are evaluated in Jira's configured timezone, which may
  differ from local shell output.

Recommended workflow for time-based asks:

1. Start with `--created -24h` plus `--plain --columns ...`.
2. If results look off (too many/too few), rerun with an absolute timestamp
   window.
3. Use `--order-by created --reverse` for deterministic output order.
4. Validate boundary tickets by exact `created` timestamps.

## Common Patterns

```bash
# My open high-priority issues
jira issue list -a$(jira me) -yHigh -s~Done

# Unassigned issues created this week
jira issue list -ax --created week

# Quick status update
jira issue move ISSUE-1 "In Progress" && jira issue assign ISSUE-1 $(jira me)

# Create and assign bug
jira issue create -tBug -s"Bug title" -yHigh -a$(jira me) --no-input
```
