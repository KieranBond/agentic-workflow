#!/bin/bash
set -euo pipefail

# Add an inline comment to a specific line in a GitLab MR diff
#
# Usage:
#   mr-inline-comment.sh <MR_NUMBER> <FILE_PATH> <LINE_NUMBER> <COMMENT_BODY>
#   mr-inline-comment.sh <MR_NUMBER> <FILE_PATH> <LINE_NUMBER> -  # read body from stdin
#
# Examples:
#   mr-inline-comment.sh 777 src/utils/helper.ts 42 "This should be const instead of let"
#   echo "Multi-line\ncomment" | mr-inline-comment.sh 777 src/utils/helper.ts 42 -
#
# Note: LINE_NUMBER refers to the line in the NEW version of the file.
# You can only comment on lines that are part of the diff context.

MR_NUMBER="${1:?Usage: mr-inline-comment.sh <MR_NUMBER> <FILE_PATH> <LINE_NUMBER> <COMMENT_BODY>}"
FILE_PATH="${2:?Missing FILE_PATH}"
LINE_NUMBER="${3:?Missing LINE_NUMBER}"
COMMENT_BODY="${4:?Missing COMMENT_BODY (use - for stdin)}"

# Read from stdin if body is "-"
if [[ "$COMMENT_BODY" == "-" ]]; then
  COMMENT_BODY=$(cat)
fi

if [[ -z "$COMMENT_BODY" ]]; then
  echo "Error: Comment body cannot be empty" >&2
  exit 1
fi

# Fetch the latest diff version SHAs
VERSION_JSON=$(glab api "projects/:id/merge_requests/${MR_NUMBER}/versions" | jq '.[0]')

if [[ "$VERSION_JSON" == "null" ]] || [[ -z "$VERSION_JSON" ]]; then
  echo "Error: Could not fetch MR version info. Is MR ${MR_NUMBER} valid?" >&2
  exit 1
fi

read -r BASE_SHA START_SHA HEAD_SHA < <(
  echo "$VERSION_JSON" | jq -r '[.base_commit_sha, .start_commit_sha, .head_commit_sha] | @tsv'
)

if [[ -z "$BASE_SHA" ]] || [[ "$BASE_SHA" == "null" ]]; then
  echo "Error: Could not extract SHA values from version info" >&2
  exit 1
fi

DIFFS_JSON=$(glab api "projects/:id/merge_requests/${MR_NUMBER}/diffs")
FILE_IN_DIFF=$(echo "$DIFFS_JSON" | jq -r --arg path "$FILE_PATH" '.[] | select(.new_path == $path) | .new_path')

if [[ -z "$FILE_IN_DIFF" ]]; then
  echo "Error: File '${FILE_PATH}' not found in MR diff." >&2
  echo "Available files:" >&2
  echo "$DIFFS_JSON" | jq -r '.[].new_path' >&2
  exit 1
fi

# Create the inline comment
RESULT=$(glab api -X POST "projects/:id/merge_requests/${MR_NUMBER}/discussions" \
  -f body="$COMMENT_BODY" \
  -f "position[base_sha]=$BASE_SHA" \
  -f "position[start_sha]=$START_SHA" \
  -f "position[head_sha]=$HEAD_SHA" \
  -f "position[position_type]=text" \
  -f "position[new_path]=$FILE_PATH" \
  -f "position[new_line]=$LINE_NUMBER" 2>&1) || {
    echo "Error creating comment: $RESULT" >&2
    # Common error: line not in diff context
    if echo "$RESULT" | grep -q "400\|position"; then
      echo "" >&2
      echo "Hint: Line ${LINE_NUMBER} may not be within the diff context." >&2
      echo "GitLab only allows comments on lines that appear in the diff." >&2
    fi
    exit 1
  }

# Extract and display the created comment URL
DISCUSSION_ID=$(echo "$RESULT" | jq -r '.id // empty')
if [[ -n "$DISCUSSION_ID" ]]; then
  echo "Created inline comment on ${FILE_PATH}:${LINE_NUMBER}"
  echo "Discussion ID: ${DISCUSSION_ID}"
else
  echo "Comment created (could not extract discussion ID)"
  echo "$RESULT" | jq -r '.notes[0].body // empty' | head -1
fi
