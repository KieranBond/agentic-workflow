---
name: mr-triage
description: >
  Autonomous review-and-triage loop for a single GitLab MR. Runs the pr-review
  panel, including its dedicated fresh-eyes pass, over the MR diff, merges panel
  findings with every unresolved MR
  discussion, and triages each into actionable / nit / ambiguous: actionable
  findings are auto-fixed (test-gated), committed, and pushed; nits are handled
  silently with reasons in the report; ambiguous items pass through an autonomy
  ladder before being deferred as open MR discussions for the author. Loops
  until nothing remains but deferred items. Use when the user says "mr-triage",
  "triage this MR", "triage the review comments", "address the review
  feedback", "run the review loop", or pastes a GitLab MR URL asking for a
  review that also fixes what it finds. Accepts an MR URL/IID as argument or
  detects the current branch's MR. Never touches threads a human has
  participated in.
---

# MR Triage

Review-and-fix loop for one GitLab MR. Each round: run the `pr-review` panel
over the MR diff, fetch every unresolved discussion, triage panel findings and
existing threads together, auto-fix what's clearly actionable (gated on the
test suite), silently handle nits, and run everything ambiguous through the
autonomy ladder before deferring it. The loop ends when the only things left
are deferred items — open MR discussions flagged for the author — plus a
terminal report that reconciles every finding and thread into exactly one
bucket.

## Hard rules

1. **Human threads are untouchable.** Any discussion where any note was
   written by a real person is deferred: no fix, no resolve, no reply.
   Responses to humans come from the MR author, in person.
2. **Never reply to a thread.** The only thread mutations this skill performs
   are *creating* new inline discussions and *resolving* automated ones.
   Reasoning lives in the report and in commit messages, not in replies.
3. **No summary comment.** The verdict and audit trail go to the terminal
   report only. The MR gets inline discussions and fix commits, nothing else.
4. **Comments post as the user** (no bot banner), but every body this skill
   posts ends with the invisible marker `<!-- mr-triage -->` on its own line
   so later rounds and future runs can tell their own comments from the
   author's real ones. Never omit it — without it, rule 1 would defer our own
   comments forever.
5. **Every auto-fix is test-gated.** No push without a green test run.
6. **When in doubt, defer.** A deferred item is recoverable; a wrong push or a
   wrongly-resolved human thread is not.

## Workflow

### Step 0: Preflight

Resolve the MR:

- `$ARGUMENTS` is a URL (`https://gitlab.../<project-path>/-/merge_requests/<iid>`):
  parse project path and IID.
- `$ARGUMENTS` is a bare IID (`123` or `!123`): use with the current repo.
- No argument: `glab mr view --output json` for the current branch.

Fetch the MR and record its fields:

```bash
glab api "projects/:id/merge_requests/<iid>" \
  | jq '{iid, state, source_branch, target_branch, web_url,
         head_sha: .diff_refs.head_sha, base_sha: .diff_refs.base_sha,
         start_sha: .diff_refs.start_sha}'
```

(For a URL pointing at another project, replace `:id` with the URL-encoded
project path throughout.)

Then verify, stopping with a clear message on any failure:

- MR state is `opened` — a merged/closed MR has nothing to triage.
- The local repo matches the MR's project and the working tree is **clean**.
- Check out the source branch and pull; local HEAD must equal the MR head SHA.
- **Discover the test command**, first match wins: `justfile` → `just test`;
  `Makefile` with a test target → `make test`; `package.json` with
  `scripts.test` → `pnpm test` (or the repo's package manager);
  `pyproject.toml` → `uv run pytest`; `Cargo.toml` → `cargo test`; `go.mod` →
  `go test ./...`. If nothing matches, ask the user for the command once and
  use it for the whole run. If they say "no tests", every auto-fix is demoted
  one rung on the autonomy ladder (just-do-it → recommend-and-do,
  recommend-and-do → stop-and-ask).

Initialize run state: `panel_marker_sha = null`, `deferred = []`, `round = 0`,
counts all zero.

### Step 1: Run the panel (gated)

Run the panel when `panel_marker_sha` is `null` (first round) **or** HEAD ≠
`panel_marker_sha` and `git diff <marker>..HEAD --name-only` touches at least
one non-doc file (anything other than `*.md`, `*.txt`, or pure whitespace).
Otherwise log `panel: skip (no substantive changes since <sha>)` and go to
Step 2.

Follow the **`pr-review` skill** for the panel itself — same seven `review-*`
agents, same parallel fan-out, same synthesis — with the range
`origin/<target_branch>...HEAD`. Include the upstream `fresh-eyes.md` prompt
verbatim in the `review-fresh-eyes` task, matching `pr-review`'s fan-out
example. Two overrides:

- Skip pr-review's report presentation; keep the merged, deduplicated,
  severity-ranked finding list (`[SEVERITY] file:line / Issue / Fix`, with
  convergence noted) as this round's `panel_findings`.
- Record the verdict tier for the report: **BLOCKED** (any BLOCKER) /
  **REQUEST CHANGES** (2+ MAJOR) / **APPROVE WITH NITS** (some MINOR/NIT) /
  **APPROVE** (clean).

**Watching the panel live (optional — Herdr).** The panel uses `pr-review`'s
single async `workflowScript` with `runs.all`, fresh contexts, and discovered
agent/model profiles. Native status and completion notifications work without
Herdr. Only when the user explicitly asks for Herdr and
`test "${HERDR_ENV:-}" = 1` passes, mirror the run into a sibling pane. The
pane observes the existing run; it never launches a replacement panel:

1. Keep the run ID and async directory returned by the native launch.
2. Split a read-only sibling pane without stealing focus and tail the run's
   logs (see the `herdr` skill for exact command syntax — verify `HERDR_ENV`
   first, parse IDs from the JSON, never touch panes you didn't create):
   ```bash
   pane=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus \
     | jq -r '.result.pane.pane_id')
   logs=$(find "$ASYNC_DIR" -name '*.log' 2>/dev/null)
   herdr pane run "$pane" "tail -n +1 -F \"$ASYNC_DIR/events.jsonl\" $logs"
   ```
   `events.jsonl` is the reliable spine (all children stream to it); per-child
   output logs are a bonus and may appear a beat after the split as agents warm
   up.
3. Yield for the native completion notification, then read the structured
   results and synthesize as `pr-review` specifies. Use `subagent` with
   `action: "status"` and the run ID for a targeted inspection. Do not call
   `subagent_wait` (not a current tool), poll, or scrape the pane for findings.
4. Leave the pane in place; the user can scroll the reviewers' work and close it
   themselves.

If Herdr is not active, use the same native async panel without a mirror.
An infrastructure failure stops the affected review path: report the exact error,
run/status and repo/cwd/worktree/branch/ref, then verify the tree or capture its
partial diff before a same-protocol retry. Do not switch to a CLI or foreground
agent without explicit owner approval.

Set `panel_marker_sha = HEAD`.

### Step 2: Fetch every unresolved discussion

```bash
glab api "projects/:id/merge_requests/<iid>/discussions?per_page=100" --paginate \
  | jq '[.[] | select(.notes[0].system == false)
        | select(any(.notes[]; .resolvable == true and .resolved == false))
        | {id: .id,
           path: .notes[0].position.new_path,
           line: .notes[0].position.new_line,
           participants: [.notes[] | {username: .author.username,
             marked: (.body | contains("<!-- mr-triage -->"))}],
           body_head: (.notes[0].body[:1500]),
           body_truncated: ((.notes[0].body | length) > 1500),
           reply_count: (.notes | length - 1)}]'
```

Bodies are trimmed to 1500 chars for classification; refetch the full body
only for the one thread you are about to fix.

**Classify participants.** A note is *automated* if its body carries the
`<!-- mr-triage -->` marker, or its author is a bot account (username ends in
`-bot`/`_bot`/`[bot]`, matches `project_*_bot*`/`group_*_bot*` token users, or
is a known review bot — renovate, dependabot, coderabbit, danger, gitlab-bot).
If **any** note in a discussion is neither, the whole thread is **human**:
defer it untouched, whoever opened it. If you can't confidently classify a
participant, treat them as human.

### Step 3: Triage everything

The triage set is this round's `panel_findings` plus every unresolved
automated thread not already in `deferred`. Nothing is skipped — every item
ends in exactly one bucket: **fixed**, **nit**, **promoted**, or **deferred**.

**Actionable** — all of: severity BLOCKER or MAJOR (convergent findings count
as one tier higher confidence); the fix is concrete enough that a reader knows
exactly what to change; the change is localised (one file or a small set of
tightly-related edits); no new design decisions, dependencies, or scope
change. → Queue the fix.

**Nit** — MINOR/NIT severity, style-only, speculative, duplicate of another
item, or already addressed on HEAD. → Panel finding: record in the report with
a one-line reason, don't post it. Existing automated thread: resolve it,
reason in the report.

**Ambiguous** — everything else: architectural judgement, broad scope, design
decisions required. → Run the autonomy ladder (below). *Just do it* /
*recommend-and-do* → queue the fix, count as **promoted** (recommend-and-do
entries must record the alternative considered: "did X because Y — the
alternative was Z"). *Stop-and-ask* → **defer**: post it as an open inline
discussion (if it isn't already a thread), add it to `deferred`, and move on.
Deferral never blocks the loop.

#### The autonomy ladder (for ambiguous items only)

- **Just do it** — the outcome is unambiguously better and there is
  essentially one sensible way to get there: trivial, reversible, improves the
  four rules of simple design (passes the tests; expresses every idea; says
  everything once; no superfluous parts).
- **Do it, but recommend** — more than one reasonable solution exists. Make
  the call you'd defend, and surface the fork prominently in the report so the
  author can redirect cheaply.
- **Stop and ask** — the change would violate one of the four rules, requires
  a genuine design decision, or you simply can't tell which outcome is better.
  Doubt about whether a fix is safe to apply *is* the stop-and-ask signal.

The ladder never applies to human threads — those are always deferred, no
matter how trivial the fix looks.

### Step 4: Post inline discussions

Before touching the code, post one inline discussion per **queued fix from a
panel finding** and per **deferred panel finding** (existing threads already
have a home; nits are report-only). Anchor to the diff:

```bash
glab api "projects/:id/merge_requests/<iid>/discussions" -X POST \
  -f "body=<severity> <issue — fix>

<!-- mr-triage -->" \
  -f "position[position_type]=text" \
  -f "position[base_sha]=<base_sha>" -f "position[start_sha]=<start_sha>" \
  -f "position[head_sha]=<head_sha>" \
  -f "position[new_path]=<file>" -F "position[new_line]=<line>"
```

Use the `diff_refs` captured at the start of this round. If the API rejects
the position (line not in the diff), post the same body as an unpositioned
discussion prefixed with `` `file:line` ``. Record each created discussion id
against its finding.

### Step 5: Fix, test, push, resolve

For each queued fix (refetch the full thread body first if it was truncated):

1. Apply the edit. One commit per fix:
   `fix: address review — <short description>`.
2. After all fixes are applied, run the discovered test command **once**. If
   it fails, bisect to the offending fix, revert that commit, and reclassify
   its item as stop-and-ask (deferred, with "auto-fix broke tests: <one-line
   failure>" as the reason). Re-run until green.
3. Push to the source branch.
4. Resolve each fixed item's discussion (the one just posted, or the
   pre-existing automated thread):

```bash
glab api "projects/:id/merge_requests/<iid>/discussions/<discussion_id>" \
  -X PUT -F resolved=true
```

Also resolve the nit-bucket threads from Step 3 now. Record every resolution
in the report with the commit SHA or the one-line nit reason — since threads
get no replies, the report is the only audit trail.

### Step 6: Loop or terminate

Increment `round`. Go back to Step 1 when work happened this round (any fix
pushed) **and** `round < 3`. Terminate when any of:

- Nothing was fixed or promoted this round — only deferred items remain.
- Round cap (3 panel rounds) reached. Anything still actionable is reported as
  `remaining actionable (cap hit)` — never silently dropped.
- The MR became merged/closed (recheck state each round).
- The user interrupts.

### Step 7: Report

Print the terminal report — the MR itself carries only commits, resolved
threads, and the open deferred discussions:

```
# MR Triage — !<iid> <title>

**Rounds:** <n> · **Panel verdict (final):** <tier> · **Pushed:** <n> commits
**Buckets:** fixed=<n> nits=<n> promoted=<n> deferred=<n> (<a> ambiguous, <h> human)

## Fixed
- `file:line` <finding> — <commit sha> _(reviewer tags)_

## Promoted (ambiguous → acted; shout to redirect)
- `file:line` did <X> because <Y> — alternative was <Z> — <commit sha>

## Nits (handled silently)
- `file:line` <reason>

## Deferred — needs you
- `file:line` <one-line question / why it stopped> — <discussion link>

## Human threads (untouched)
- `file:line` @<author> — <one-line summary>
```

Counts must reconcile: every panel finding and every unresolved thread fetched
appears in exactly one section.

## Narration

Before each step, emit one terse present-tense line so a watching user can
follow along: `[mr-triage] round 2 — panel: 3 findings (1 MAJOR); threads: 5
(2 human deferred)`. Narrate mid-step for anything slower than a few seconds
(panel fan-out, test run, push). A silent 30-second gap is the failure mode.

## Dependencies & degradation

- **`pr-review` skill + its packaged `review-*` agents** — discover executable
  agents and inspect resolved models before launching. If profiles are missing,
  verify this package and `pi-subagents` are installed; do not create global
  symlinks as a fallback. Do not treat a failed required panel as approval to
  fix or push. Report the blocker; a triage-only report requires an explicit
  owner decision.
- **Herdr (optional):** used only when explicitly requested and active. Without
  it, the panel still runs asynchronously with native status and completion.
  Load the `herdr` skill before using its commands.
- **`glab`** authenticated against the GitLab instance. If posting fails
  (permissions), fall back to report-only mode: apply fixes and push, list
  everything else in the terminal report, and say clearly that nothing was
  posted or resolved.
- **Dirty tree / diverged branch / push rejected:** stop and tell the user;
  never stash, force-push, or rebase on their behalf.
- **No test command and user provides none:** demote all fixes one ladder rung
  (see Step 0) — unverified pushes are how a triage loop loses trust.
