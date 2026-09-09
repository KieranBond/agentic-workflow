#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

python3 scripts/validate.py

while IFS= read -r script; do
  bash -n "$script"
done < <(find . -type f -name '*.sh' -not -path './.git/*' | sort)

(
  cd skills/skill-creator
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
)

printf 'Shell syntax and Python unit tests passed.\n'
