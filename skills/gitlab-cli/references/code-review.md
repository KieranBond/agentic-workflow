# MR Comments and Code Review

## IMPORTANT: When Reviewing MRs, Always Use Inline Comments

When asked to review an MR, **strongly prefer inline comments on specific
lines** over general MR comments. This provides better context for the author
and makes issues easier to address.

## List Unresolved Comments

```bash
scripts/list-mr-comments.sh <MR_NUMBER>
```

Output format: `discussion_id: file:line` followed by `[author] comment`

## Add General MR Comment

```bash
glab mr note 777 -m "Comment text here"
```

## Add Inline Comments on Specific Lines (Preferred for Code Review)

Use the `mr-inline-comment.sh` script to add comments directly to specific lines
in an MR:

```bash
scripts/mr-inline-comment.sh <MR_NUMBER> <FILE_PATH> <LINE_NUMBER> "<COMMENT_BODY>"
```

The script automatically:

- Fetches the required SHA values from the MR
- Validates the file exists in the diff
- Creates the inline comment via the GitLab API
- Provides helpful error messages if the line is not in the diff context

### Examples

```bash
# Simple inline comment
scripts/mr-inline-comment.sh 777 src/utils/helper.ts 42 "This should be const instead of let"

# Comment with markdown formatting
scripts/mr-inline-comment.sh 777 src/types.d.ts 10 "**Type Safety:** This should use \`Nullable<string>\`"

# Multi-line comment (use stdin with -)
cat << 'EOF' | scripts/mr-inline-comment.sh 777 src/handler.ts 42 -
**Bug:** Missing null check here.

**Suggestion:**
\`\`\`typescript
if (value == null) return
\`\`\`
EOF
```

### Batch Comments for Code Review

When reviewing multiple issues, call the script for each:

```bash
# Comment 1: Type issue
scripts/mr-inline-comment.sh 777 src/types.d.ts 10 \
  "**Type Safety:** This should use \`Nullable<string>\` instead of \`string\`."

# Comment 2: Logic issue
scripts/mr-inline-comment.sh 777 src/handler.ts 42 \
  "**Bug:** Missing null check here - \`value\` can be undefined."

# Comment 3: Test coverage
scripts/mr-inline-comment.sh 777 src/feature.ts 88 \
  "**Test Gap:** This error path needs test coverage."
```

### List Files in the Diff

To see which files you can comment on:

```bash
glab api "projects/:id/merge_requests/<MR_IID>/diffs" | jq -r '.[].new_path'
```

**Note:** You can only comment on lines that are part of the diff context. For
issues in unchanged code, use a general MR comment instead.

<details>
<summary>Advanced: Raw API for Inline Comments</summary>

If you need more control, you can use the GitLab API directly:

```bash
# 1. Get version SHAs
VERSION_INFO=$(glab api "projects/:id/merge_requests/777/versions" | jq '.[0]')
BASE_SHA=$(echo "$VERSION_INFO" | jq -r '.base_commit_sha')
START_SHA=$(echo "$VERSION_INFO" | jq -r '.start_commit_sha')
HEAD_SHA=$(echo "$VERSION_INFO" | jq -r '.head_commit_sha')

# 2. Create inline comment
glab api -X POST "projects/:id/merge_requests/777/discussions" \
  -f body="Comment text here" \
  -f "position[base_sha]=$BASE_SHA" \
  -f "position[start_sha]=$START_SHA" \
  -f "position[head_sha]=$HEAD_SHA" \
  -f "position[position_type]=text" \
  -f "position[new_path]=path/to/file.ts" \
  -f "position[new_line]=42"
```

**Parameters:**

- `new_path` - File path as shown in the diff
- `new_line` - Line number in the NEW version of the file
- `old_line` - (Optional) Line number in the OLD version (for deleted/modified
  lines)

</details>

## Code Review Best Practices

1. **Always prefer inline comments** - They show exactly where the issue is
2. **Use general comments only for:**
   - Summary of findings
   - Issues in files not changed by the MR
   - Architectural/design concerns that span multiple files
3. **Format inline comments clearly:**
   - Start with issue type: `**Bug:**`, `**Issue:**`, `**Suggestion:**`,
     `**Question:**`
   - Include code suggestions in fenced code blocks
   - Explain the impact/risk when relevant
