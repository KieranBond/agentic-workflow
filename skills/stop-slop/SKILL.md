---
name: stop-slop
description: Remove AI writing patterns from any prose. Use this skill whenever you're drafting, editing, or reviewing text that will be read by humans — docs, emails, PR descriptions, release notes, README files, Slack messages, or any other written content. Invoke it when the user says "edit this", "clean up my writing", "make this less AI", "review this draft", "stop-slop", or when you notice your own output contains filler phrases, passive voice, throat-clearing openers, vague declaratives, or adverb stacking. Also use proactively when generating non-trivial prose — don't wait to be asked.
---

# Stop Slop

Eliminate predictable AI writing patterns from prose. Adapted from
[hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) (MIT).

## Core Rules

These eight rules eliminate most slop. Understand the _why_ behind each — that
lets you apply good judgment in edge cases rather than pattern-matching
mechanically.

1. **Cut filler phrases.** Throat-clearing openers and emphasis crutches waste
   the reader's time before the point arrives. State the point.

2. **Break formulaic structures.** Binary contrasts ("not X, but Y"), negative
   listings, and dramatic fragmentation signal AI writing more than almost
   anything else. If you find yourself writing "Not because X. Because Y." —
   rewrite it.

3. **Use active voice.** Passive voice hides who does what. "The report was
   written" makes readers work harder for no reason. Name the actor.

4. **Be specific.** Vague declaratives ("the implications are significant") are
   filler dressed up as insight. Replace them with the specific thing.

5. **Put the reader in the room.** Write in second person ("you"), not
   narrator-from-a-distance ("people tend to", "teams often find"). "You don't
   sit down and decide to..." beats "Nobody designed this."

6. **Vary rhythm.** Stacked short sentences and em-dash-heavy constructions both
   read as performative. Mix lengths. Use commas and periods instead of em
   dashes.

7. **Trust readers.** Softening, permission-granting ("and that's okay"), and
   hand-holding all signal distrust of the reader's intelligence. State facts
   directly.

8. **Cut quotables.** If a sentence sounds like a LinkedIn pull-quote, rewrite
   it.

## Reference Files

For the full lists of specific patterns to cut, read these as needed:

- `references/phrases.md` — Throat-clearing openers, emphasis crutches, jargon,
  adverbs, meta-commentary, vague declaratives
- `references/structures.md` — Binary contrasts, negative listings, dramatic
  fragmentation, false agency, passive voice, rhythm traps, before/after
  examples

Load the reference file relevant to the type of edit you're doing. If you're
reviewing a full draft, load both.

## Process

**When editing someone's text:**

1. Read the full text first — understand the intent before cutting anything
2. Load `references/phrases.md` and `references/structures.md`
3. Apply the core rules, using the reference tables for specific patterns
4. Return the edited text with a brief note on the main patterns you cut (so the
   writer learns)

**When reviewing your own output before delivering:**

1. Run the quick checks below
2. If any fail, revise before sending

**When generating prose from scratch:** Apply the rules as you write rather than
editing after. It's faster.

## Quick Checks

Before delivering any prose:

- [ ] No adverbs (-ly words: really, simply, genuinely, actually, deeply...)
- [ ] No passive voice — every sentence has a named actor
- [ ] No throat-clearing openers (see `references/phrases.md`)
- [ ] No binary contrasts ("not X, but Y")
- [ ] No vague declaratives ("the implications are significant")
- [ ] No em dashes
- [ ] Sentence lengths vary — no staccato stacking
- [ ] No meta-commentary ("in this section, we will...")
- [ ] "You" not "people" or "teams" or "users" (unless writing about a third
      party)

## Scoring (optional, for full drafts)

Rate 1–10 on each:

- **Directness**: Points stated without setup
- **Rhythm**: Length and structure vary
- **Trust**: No hand-holding or softening
- **Authenticity**: No clichés or jargon theater
- **Density**: Every word earns its place

Below 35/50: revise.
