#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v pi >/dev/null 2>&1; then
  printf 'error: pi is required for the smoke install\n' >&2
  exit 1
fi

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/agent"

PI_CODING_AGENT_DIR="$scratch/agent" pi install "$root"
package_list="$(PI_CODING_AGENT_DIR="$scratch/agent" pi list)"
printf '%s\n' "$package_list"

if ! grep -Fq "$root" <<<"$package_list"; then
  printf 'error: temporary Pi configuration did not list %s\n' "$root" >&2
  exit 1
fi

printf 'Local package smoke install passed.\n'
