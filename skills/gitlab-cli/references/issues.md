# Issue Operations

## List Issues

```bash
glab issue list                           # Open issues (default)
glab issue list --all                     # All issues
glab issue list --assignee=@me            # Assigned to me
glab issue list --author=username         # By author
glab issue list --label=bug               # By label
glab issue list --milestone="v1.0"        # By milestone
glab issue list --closed                  # Closed issues
glab issue list --confidential            # Confidential issues
glab issue list --search "keyword"        # Search title/description
glab issue list -O json                   # JSON output
```

## Create Issue

```bash
# Interactive
glab issue create

# Non-interactive
glab issue create -t "Issue title"
glab issue create -t "Title" -d "Description"
glab issue create -t "Bug" -l bug,urgent -a username
glab issue create -t "Feature" -m "v2.0" --due-date 2024-12-31
glab issue create -t "Title" --confidential
glab issue create -t "Title" --web        # Open in browser
```

Flags: `-t`/`--title`, `-d`/`--description` (NOT `--body`), `-l` labels, `-a`
assignee, `-m` milestone, `--due-date`, `--confidential`, `--epic`

## View/Manage Issues

```bash
glab issue view 123                       # View issue
glab issue view 123 -w                    # Open in browser
glab issue close 123                      # Close issue
glab issue reopen 123                     # Reopen issue
glab issue update 123 -t "New title"      # Update issue
glab issue note 123 -m "Comment"          # Add comment
glab issue delete 123                     # Delete issue
```
