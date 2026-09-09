# CI/CD Operations

## Pipeline Status

```bash
glab ci status                            # Current branch pipeline
glab ci status -b main                    # Specific branch
glab ci status --live                     # Real-time updates
glab ci status --compact                  # Compact view
```

## Interactive Pipeline Viewer

```bash
glab ci view                              # Interactive TUI
glab ci view main                         # Specific branch
glab ci view -p 12345                     # Specific pipeline ID
glab ci view -w                           # Open in browser
```

Controls: `Enter` toggle logs, `Esc/q` close, `Ctrl+R` retry, `Ctrl+D` cancel,
`Ctrl+Q` quit

## Job Operations

```bash
glab ci retry                             # Interactive job selection
glab ci retry 224356863                   # Retry by job ID
glab ci retry lint                        # Retry by job name
glab ci trace                             # Trace running job
glab ci list                              # List pipelines
glab ci run                               # Trigger new pipeline
glab ci cancel                            # Cancel pipeline
glab ci lint                              # Validate .gitlab-ci.yml
```

## Pipeline Management

```bash
glab ci list                              # List recent pipelines
glab ci get 12345                         # Get pipeline details
glab ci delete 12345                      # Delete pipeline
```
