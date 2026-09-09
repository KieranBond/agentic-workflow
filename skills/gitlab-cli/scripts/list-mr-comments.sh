#!/bin/bash
set -euo pipefail

MR_NUMBER="${1:?Usage: list-mr-comments.sh <MR_NUMBER>}"

glab api "projects/:id/merge_requests/${MR_NUMBER}/discussions" | jq -r '
  .[]
  | select([.notes[] | select(.type == "DiffNote" and .resolvable and (.resolved | not) and (.system | not))] | length > 0)
  | . as $d
  | $d.notes[]
  | select(.type == "DiffNote" and (.system | not))
  | "\($d.id): \(.position.new_path // .position.old_path):\(.position.new_line // .position.old_line)\n  [\(.author.username)] \(.body)\n"
'
