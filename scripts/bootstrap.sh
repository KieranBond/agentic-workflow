#!/usr/bin/env bash
set -euo pipefail

PI_VERSION="0.85.1"
SUBAGENTS_VERSION="0.66.0"
MCP_ADAPTER_VERSION="2.32.1"
WORKFLOW_SOURCE="${AGENTIC_WORKFLOW_SOURCE:-git:git@github.com:KieranBond/agentic-workflow.git@v0.1.1}"

if command -v asdf >/dev/null 2>&1; then
  npm_cmd=(asdf exec npm)
elif command -v npm >/dev/null 2>&1; then
  npm_cmd=(npm)
else
  printf 'error: npm is required; install Node.js 22 first\n' >&2
  exit 1
fi

printf '[bootstrap] installing Pi %s\n' "$PI_VERSION"
"${npm_cmd[@]}" install --global "@earendil-works/pi-coding-agent@$PI_VERSION"
if command -v asdf >/dev/null 2>&1; then
  asdf reshim nodejs
fi
hash -r

if ! command -v pi >/dev/null 2>&1; then
  printf 'error: pi is not on PATH after installation\n' >&2
  exit 1
fi

printf '[bootstrap] installing pi-subagents %s\n' "$SUBAGENTS_VERSION"
pi install "npm:pi-subagents@$SUBAGENTS_VERSION"

printf '[bootstrap] installing pi-mcp-adapter %s\n' "$MCP_ADAPTER_VERSION"
pi install "npm:pi-mcp-adapter@$MCP_ADAPTER_VERSION"

printf '[bootstrap] installing workflow package from %s\n' "$WORKFLOW_SOURCE"
pi install "$WORKFLOW_SOURCE"

if [[ -n "${PRIVATE_PI_PACKAGE_SOURCE:-}" ]]; then
  printf '[bootstrap] installing private Pi package from configured source\n'
  pi install "$PRIVATE_PI_PACKAGE_SOURCE"
fi

actual_pi_version="$(pi --version)"
if [[ "$actual_pi_version" != "$PI_VERSION" ]]; then
  printf 'error: expected Pi %s, found %s\n' "$PI_VERSION" "$actual_pi_version" >&2
  exit 1
fi

cat <<'CHECKLIST'

Bootstrap complete. Authenticate services on this machine; do not copy credential files:

  1. Start Pi and use /login for each model provider you intend to use.
  2. Run `gh auth login` if the workflow repository remains private.
  3. Run `glab auth login` before using GitLab skills.
  4. Run `jira init` before using the Jira skill.
  5. Create `~/.sentryclirc` locally before using the Sentry skill.
  6. Configure the Excalidraw MCP server locally; never commit its credentials.
  7. Optionally merge config/subagent-overrides.example.json into
     ~/.pi/agent/settings.json after confirming every model ID with
     `subagent({ action: "models" })`.

Set PRIVATE_PI_PACKAGE_SOURCE before rerunning this script to install an approved
private workflow package without hard-coding its repository in this public repo.
CHECKLIST
