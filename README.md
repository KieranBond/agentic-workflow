# Agentic Workflow

A portable [Pi](https://github.com/earendil-works/pi) package for code review, GitLab/Jira/Sentry workflows, Excalidraw diagrams, skill development, and prose cleanup.

## Included resources

### Review workflows

- `pr-review` — parallel seven-agent review panel
- `mr-triage` — review, classify, fix, test, and push a GitLab MR
- `subagent-delegation` — current Pi subagent orchestration patterns
- Seven read-only `review-*` agents under `agents/`

### Tool workflows

- `gitlab-cli`
- `jira-cli`
- `sentry`
- `excalidraw`

### Authoring workflows

- `skill-creator`
- `stop-slop`

## Install

The tested versions are Node.js `22.21.1`, Pi `0.85.1`, `pi-subagents` `0.66.0`, and `pi-mcp-adapter` `2.32.1`. The Node version is also pinned in `.tool-versions`.

```bash
npm install --global @earendil-works/pi-coding-agent@0.85.1
pi install npm:pi-subagents@0.66.0
pi install npm:pi-mcp-adapter@2.32.1
pi install git:git@github.com:KieranBond/agentic-workflow.git@v0.1.1
```

The SSH form works for private repositories after GitHub authentication. Once the repository is public, `git:github.com/KieranBond/agentic-workflow@v0.1.1` also works.

For a new machine, run the pinned bootstrap instead:

```bash
git clone git@github.com:KieranBond/agentic-workflow.git
cd agentic-workflow
./scripts/bootstrap.sh
```

The script installs code only. It does not copy credentials, sessions, private MCP configuration, or employer-owned settings.

## Configuration

Reviewer agents inherit the active Pi model by default, so the package works with one configured provider. For a stronger mixed-model panel, merge [`config/subagent-overrides.example.json`](config/subagent-overrides.example.json) into `~/.pi/agent/settings.json` and replace any unavailable model IDs with exact IDs from:

```text
subagent({ action: "models" })
```

Required external tools depend on the skill:

| Skill | Requirement |
| --- | --- |
| `pr-review`, `mr-triage` | `pi-subagents`; seven packaged review agents |
| `mr-triage`, `gitlab-cli` | authenticated `glab`; `jq` |
| `jira-cli` | authenticated `jira` CLI |
| `sentry` | `~/.sentryclirc` with a Sentry URL and token |
| `excalidraw` | `pi-mcp-adapter` and a separately configured `excalidraw` MCP server |
| `skill-creator` | Python 3; PyYAML 6.0.3 for `quick_validate.py` |

Herdr integration in `mr-triage` is optional and activates only when the user explicitly requests it and Herdr is already installed.

Keep credentials outside this repository.

## Develop

```bash
./scripts/validate.sh
./scripts/smoke-install.sh
npm pack --dry-run
```

The smoke test uses a temporary Pi configuration and installs this checkout as a local package. It does not use model credentials or invoke a provider.

## Licensing

Repository code is MIT-licensed unless a file states otherwise. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for bundled and adapted work.
