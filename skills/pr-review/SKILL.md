---
name: pr-review
description: Run a multi-agent code review of a diff by fanning out seven specialized sub-agents in parallel — one each for correctness, security (incl. org/tenant isolation), performance, test coverage, and design/maintainability, plus an independent cross-model reviewer and a meticulous fresh-eyes reviewer — then synthesize their findings into one deduplicated, severity-ranked report. Use this whenever the user asks to review a PR, MR, branch, diff, or "my changes," wants a thorough code review before merging, or asks "what's wrong with this change." Prefer this over a single-pass inline review for anything beyond a trivial diff, because parallel specialists on varied models catch far more than one reviewer reading top-to-bottom.
---

# PR Review

## Overview

This skill reviews a set of changes with a **panel of specialized sub-agents running in parallel**, each on a deliberately chosen model. A single reviewer reading a diff top-to-bottom spreads its attention thin and anchors on the first thing it notices. Seven independent reviewers, including cross-model and fresh-eyes passes, catch more problems without sharing one context or one set of assumptions.

You determine the changeset, fan out the panel in one async `workflowScript`, then merge their findings into one prioritized report. The reviewers do not modify project files.

## The panel

| Agent | Concern | Model tier |
|-------|---------|------------|
| `review-correctness` | logic bugs, edge cases, error handling, concurrency | Strong review |
| `review-security` | injection, authz, secrets, **org/tenant isolation** | Strong review |
| `review-performance` | queries, allocations, blocking calls, scale | Engineering |
| `review-tests` | coverage of changed lines, edge cases, test quality | Coverage scan |
| `review-design` | API/naming, maintainability, codebase consistency | Engineering |
| `review-crossmodel` | independent whole-diff review; second family when configured | Independent |
| `review-fresh-eyes` | meticulous second pass for anything the panel could overlook | Strong review |

Reviewer profiles inherit the active Pi model by default. For stronger independence,
configure exact models under `subagents.agentOverrides` in user or project settings
and put `review-crossmodel` on a second provider family. Inspect the resolved mapping
with `subagent({ action: "models" })`. If only one provider is configured, run the
full independent panel on that provider and disclose the missing model diversity.

## Setup (run once)

Install this package and `pi-subagents`; the seven reviewer profiles are exposed by
the package manifest, so no symlinks or global agent copies are required.

Before execution, call `subagent({ action: "list", capabilities: true })` and
confirm all seven reviewers are executable and non-disabled. Check the live models
with `subagent({ action: "models" })`. Discovery proves configuration, not a working
provider request. Diagnose unknown names, shadowing, or model failures before launch;
do not silently replace a failed reviewer with a different execution mode.

## Workflow

### 1. Determine the changeset

Figure out exactly what's being reviewed and express it as a git range the agents can run themselves:

- **If the user gave a range or refs** (e.g. "review abc123..def456", "review against develop"), use that.
- **Otherwise auto-detect the base branch**, preferring the first that exists: `develop`, then `main`, then `master`. Determine the merge-base and review the branch's own commits:
  ```bash
  base=$(for b in develop main master; do git show-ref -q --verify "refs/heads/$b" && echo "$b" && break; done)
  range="$(git merge-base "$base" HEAD)...HEAD"
  ```
- **If the interesting changes are uncommitted**, review the working tree instead — tell each agent to run `git diff` (unstaged) and `git diff --cached` (staged) rather than a range.

Sanity-check the diff isn't empty before fanning out:
```bash
git --no-pager diff --stat "$range"
```
If it's huge (hundreds of files), tell the user and offer to scope to a subdirectory or a subset of commits — a focused review beats a diluted one.

### 2. Fan out the panel (one async workflow)

Give every reviewer the same exact changeset and let it run git itself. Substitute
the repository path and resolved range below; use the working-tree commands instead
when appropriate. All children use fresh context and remain read-only.

```javascript
subagent({
  async: true,
  context: "fresh",
  cwd: "<REPO>",
  workflowScript: `
    const scope = "Read-only review: run git diff <RANGE> and inspect surrounding code. Do not edit, commit, publish, or delegate. Report source-backed findings on changed lines as [SEVERITY] file:line / Issue / Fix. ";
    const panel = [
      { key: "correctness", agent: "review-correctness", task: scope + "Focus on correctness, error handling, and concurrency.", output: "correctness.md" },
      { key: "security", agent: "review-security", task: scope + "Focus on security, including tenant isolation where applicable.", output: "security.md" },
      { key: "performance", agent: "review-performance", task: scope + "Focus on performance and scale.", output: "performance.md" },
      { key: "tests", agent: "review-tests", task: scope + "Focus on test coverage and test quality.", output: "tests.md" },
      { key: "design", agent: "review-design", task: scope + "Focus on design and maintainability.", output: "design.md" },
      { key: "crossmodel", agent: "review-crossmodel", task: scope + "Review holistically and independently.", output: "crossmodel.md" },
      { key: "fresh-eyes", agent: "review-fresh-eyes", task: scope + "Once again, check over everything again with fresh eyes looking for any blunders, mistakes, errors, oversights, omissions, problems, misconceptions, bugs, etc. Be SUPER thorough and meticulous!", output: "fresh-eyes.md" }
    ];
    const results = await runs.all(panel);
    const summary = [];
    for (let i = 0; i < results.length; i += 1) {
      summary.push({
        concern: panel[i].key,
        ok: results[i].ok,
        output: results[i].output,
        outputReference: results[i].outputReference,
        runId: results[i].runId
      });
    }
    return summary;
  `
})
```

`runs.all` returns an ordered array. Await it before reading results. Return control
while the native async run is active; completion will notify the parent. A failed
reviewer is missing coverage, not a clean finding list. Report the exact failure and
run/cwd/git state, then use only a clear same-protocol retry after checking the tree.
Do not approve with an incomplete required panel.

### 3. Synthesize into one report

Each agent returns findings as `[SEVERITY] file:line / Issue / Fix`. Merge them:

1. **Deduplicate.** When multiple agents flag the same line for the same root cause, keep one entry and note which lenses caught it (e.g. "flagged by security + cross-model"). Agreement across agents is a strong signal — surface it.
2. **Rank by severity** (BLOCKER → MAJOR → MINOR → NIT), then group by file within each tier.
3. **Drop the "nothing found" lines** — those just confirm a clean concern; mention clean concerns in one summary line.
4. **Don't inflate.** If the panel found little, say so. The goal is a report the author trusts, not a long one.

Use this report structure:

```
# Code Review — <range or description>

**Scope:** <N files, +X/-Y lines> · **Panel:** correctness, security, performance, tests, design, cross-model, fresh-eyes
**Verdict:** <Block / Approve with changes / Approve> — <one-line rationale>

## Blockers
- **`file.go:123`** <issue> — <fix> _(correctness, cross-model)_

## Major
- **`file.go:45`** <issue> — <fix> _(security)_

## Minor
- ...

## Nits
- ...

## Clean
Performance, tests, and fresh-eyes panels found no issues in the changed lines.
```

If there are zero blockers and majors, lead with the verdict and keep the rest short.

## Notes

- **Read-only:** every reviewer agent is read-only and instructed to keep bash to `git diff`/`git log`/`git show`. This skill never modifies code. If the user then wants fixes, that's a separate step (delegate to `worker` or do it inline).
- **Tuning the panel:** prompts live at `agents/review-*.md`. Prefer user/project settings overrides for local model policy so package updates do not reset it. Check configured concurrency and spawn limits instead of assuming a fixed cap.
- **Model IDs:** use an exact provider-qualified ID from the live registry, including for Anthropic. Verify both launch and response-model identity; some short aliases return a dated ID. Keep dated pins or explicitly attested response aliases in configuration, not speculative aliases in task text.
- **Focused concerns on purpose:** the five specialist agents each keep one lens. The cross-model and fresh-eyes agents stay holistic and independent so they can catch problems that fall between those lenses.
- For the general principles behind delegating to sub-agents (modes, model choice, task scoping), see the `subagent-delegation` skill.
- **Composed by `mr-triage`:** the autonomous GitLab MR loop reuses this panel as its review step, then triages and fixes the findings. Changes to the `review-*` agents affect both skills.
