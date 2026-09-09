# Repository, API, and Cross-Repo Operations

## Repository Operations

```bash
glab repo view                            # View current repo info
glab repo view owner/repo                 # View specific repo
glab repo clone owner/repo                # Clone repository
glab repo fork owner/repo                 # Fork repository
glab repo create my-project               # Create new project
glab repo list                            # List your repos
glab repo search "query"                  # Search repos
glab repo archive owner/repo              # Archive repo
```

## API Access

Direct GitLab API access for advanced operations:

```bash
# REST API
glab api projects/:id                     # Get project info
glab api projects/:fullpath/releases      # List releases
glab api issues --paginate                # Paginated results
glab api projects/:id/members -X POST -f username=user -f access_level=30

# GraphQL
glab api graphql -f query='{ currentUser { username } }'
glab api graphql -f query='
  query {
    project(fullPath: "owner/repo") {
      name
      issues { count }
    }
  }
'
```

Placeholders: `:id`, `:fullpath`, `:branch`, `:namespace`, `:repo`, `:user`

## Output Formats (command-specific)

`glab` output flags are not fully consistent across subcommands. Always check
`--help` when scripting.

```bash
# Merge requests (list/view)
glab mr list -F json

# Issues (list uses -O, view uses -F)
glab issue list -O json
glab issue view 123 -F json

# Pagination
--paginate                                # Fetch all pages
-P 50                                     # Items per page
-p 2                                      # Page number
```

## Common Patterns

```bash
# Create MR with explicit metadata, then verify description
glab mr create -t "PROJ-123: Title" -d "Description" --remove-source-branch --yes
glab mr view <MR_ID> -F json | jq -r '.title, .description'

# Quick pipeline check and retry failed jobs
glab ci status && glab ci retry

# Find my open MRs needing attention
glab mr list --assignee=@me --reviewer=@me

# Create bug issue and assign to self
glab issue create -t "Bug: description" -l bug -a @me

# Checkout, review, and merge MR
glab mr checkout 123 && glab mr view 123 -c && glab mr merge 123 -y

# View pipeline for specific MR
glab ci view -b feature-branch
```

## Cross-Repository Operations

```bash
glab mr list -R owner/other-repo          # Different repo
glab issue list -g my-group               # Group-level
glab mr create -H fork/repo               # From fork
```
