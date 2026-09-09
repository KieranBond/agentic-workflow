---
name: subagent-delegation
description: Delegate focused work through Pi's subagent tool with isolated context and role-specific models. Use for context-heavy recon, independent parallel tasks, scout-to-plan-to-implement workflows, and a second model's perspective. Covers agent discovery, model preflight, task contracts, and current workflowScript syntax.
---

# Subagent Delegation

Delegate when the child reads a lot but returns a compact answer, or when independent
work benefits from separate context. Handle quick lookups and small edits inline.
Load the installed `pi-subagents` skill for advanced execution and recovery details;
its current tool schema takes precedence over examples here.

## Discover agents and models first

```javascript
subagent({ action: "list", capabilities: true })
subagent({ action: "models" })
```

Only launch executable, non-disabled agents. For an external CLI agent, also require
`runner.available === true`; that checks the executable, not authentication or a
successful launch. `pi --list-models` is a useful CLI cross-check, but the current
session's `action: "models"` registry is authoritative for this launch.

Agent names are roles, not model aliases. Use discovery rather than assuming that
`Explore`, `general-purpose`, `grader`, or `advisor` is an installed canonical name.
`advisor` can be an alias for `oracle`; confirm it before use.

| Role | Typical use | Authority |
|------|-------------|-----------|
| `scout` / `scout-mini` | Locate code and return source-backed context | Read-only |
| `planner` | Turn findings and requirements into a plan | Read-only |
| `reviewer` / `review-*` | Inspect changes from a defined angle | Read-only |
| `worker` / `worker-xhigh` | Implement an approved, bounded change | One writer |
| `oracle` | Escalate a hard decision with inherited context | Advisory |

These are local conventions, not guaranteed package defaults. Check the tools and
resolved model shown by discovery, especially when project profiles shadow user ones.

## Model policy

Keep exact model choices in user/project profiles or `settings.json` under
`subagents.agentOverrides`, not repeated in skill prose. A per-run `model` override
wins over those defaults, so omit it unless the task needs a deliberate alternative.

- Use a fast, capable tier for recon and mechanical tasks.
- Use a capable engineering tier for planning and implementation.
- Use a strong tier for serious review; preserve a second provider family in panels.
- Use the top reasoning tier for bounded hard-decision critique, not every child.

When setting a model, copy an exact **provider/id** from the live registry for every
provider, including Anthropic. Short and dated IDs may both be listed; registry
membership proves resolution, not a successful verified response. A short alias can
launch successfully but fail `model_verification_failed` when the provider reports
a dated response ID. Pin the tested dated ID in the profile, or independently verify
and declare the exact mapping in `modelResponseAliases` in
`~/.pi/agent/extensions/subagent/config.json`. That setting accepts response IDs; it
does not rewrite requests and does not apply retroactively to resumed runs. A provider
404 is a separate failure. Do not invent dates, accept unrelated model identities,
or change providers silently. Thinking can be an agent
`thinking` setting or a supported `:level` suffix on the per-run model string.

A safe smoke test asks the selected agent to read one disposable fixture and return
its token. Check the child result, resolved model, tool call, and provider error;
`list` or a model-name self-report is not launch proof. Do not claim full workflow
verification from a smoke test.

External runners own their models. Do not pass Pi's provider-qualified IDs, thinking,
context, skills, tool budgets, or other native options to a Claude/Codex/Cursor CLI
profile unless its runner contract supports them.

## Task contract

Every fresh child needs: objective; explicit repo/cwd/ref; relevant files and
constraints; authority boundary; success criteria and validation; expected output;
and stop/ask conditions. Give reviewers the exact diff command and permission to
read surrounding code. Do not assume they see the parent conversation.

Use `context: "fresh"` for independent reviews. `fork` inherits persisted parent
history and is useful for advisory continuity, not as a substitute for a clear brief.
Keep one writer per cwd/worktree. Concurrent writers need separate branches and
worktrees even when their intended files differ. Reviewer reports can use managed
output artifacts without permission to edit project files.

## Launch shapes

Use a direct call for one bounded child:

```javascript
subagent({
  agent: "scout",
  async: true,
  context: "fresh",
  task: "Read-only: locate JWT validation in pkg/auth/. Return file:line evidence and any bypasses. Do not edit or start services."
})
```

For parallel or multi-step work, make **one top-level async workflow call** and
launch all children inside it. Legacy top-level `tasks` and `chain` are unsupported.

```javascript
subagent({
  async: true,
  context: "fresh",
  workflowScript: `
    const results = await runs.all([
      { key: "auth", agent: "scout", task: "Read-only: map JWT validation in pkg/auth/. Return file:line evidence.", output: "auth.md" },
      { key: "limits", agent: "scout", task: "Read-only: map rate limiting in pkg/middleware/. Return file:line evidence.", output: "limits.md" }
    ]);
    const summary = [];
    for (let i = 0; i < results.length; i += 1) {
      summary.push({ ok: results[i].ok, outputReference: results[i].outputReference });
    }
    return summary;
  `
})
```

`runs.all` returns an ordered array, not an object keyed by lane name. For sequential
work, await a result and pass its output to the next child; `{previous}` is not the
current chaining API. Stop a dependent stage when its predecessor fails.

```javascript
subagent({
  async: true,
  context: "fresh",
  workflowScript: `
    const scan = await runs.run("scan", {
      agent: "scout", task: "Read-only: map session persistence and return file:line evidence."
    });
    if (!scan.ok) return scan;
    return await runs.run("plan", {
      agent: "planner", task: "Read-only: plan Redis-backed session caching using these findings: " + scan.output,
      output: "plan.md"
    });
  `
})
```

Keep workflow helpers synchronous or use top-level `await`; nested async functions,
arrows, and methods are rejected. Validate saved scripts with
`subagent({ action: "validate", workflowScriptPath: "<path>" })` before execution.
Declare `output` when a handoff must persist and return its `outputReference`,
`outputPathMapping`, or `artifactPaths`, rather than an invented file path.

## Completion and failure

Ordinary async runs notify the parent. Continue independent work or yield; do not
poll, sleep, or call `bg_wait` just to wait for a native subagent. Inspect a particular
run with `subagent({ action: "status", id: "<run-id>" })` when needed.

Treat model, workflow, startup, extension, and tool-loading failures as infrastructure
blockers. Report the exact error, run/status, cwd and git/worktree state. Capture a
partial diff or verify the worktree is clean before a clear same-protocol retry.
Do not switch to an external CLI, foreground agent, `interactive_shell`, or `pi -ne`
as an implicit fallback. Ask the owner before changing execution mode.
