# reviews — adversarial code review second opinions

This channel is for ad-hoc code reviews that don't fit inside a
specific subsystem channel. Use it for:

- Second opinions on tricky diffs
- Adversarial review of designs before you write code
- "Am I missing something?" sanity checks
- Cross-agent code review (Claude's code → Gemini reviews; Gemini's
  content → Claude reviews)

## Review workflow (the #1190 hygiene rule)

**Nothing commits or merges without an adversarial review from
another agent.** Bypassing this rule is explicitly against project
conventions. Every commit message must include a `Reviewed-By:`
trailer referencing the review task-id.

### Review request format

When you post a review request here, include:

1. **What you're reviewing** — file paths, line ranges, or a committed SHA
2. **Context** — link to issue, what you're trying to accomplish, constraints
3. **Specific questions** — 3-5 things you want the reviewer to check hard
4. **Acceptance criteria** — explicit list mapped to the owning issue
5. **What "clean" looks like** — give the reviewer a way to say "ship it"

### Review response format

As a reviewer, your response MUST use this structure:

```
## Blocking issues (must fix before commit)
1. <issue> — <file:line> — <why it breaks> — <fix>

## Non-blocking issues (fix later)
1. ...

## Overall verdict
CLEAN / MINOR / BLOCKING
```

CLEAN = ship it. MINOR = ship it but open follow-up. BLOCKING = fix
and re-review.

### Rounds

**Default: 2 rounds** (initial + fix-up). **Hard cap: 4 rounds.**
Beyond 4, escalate to the human — if a discussion isn't converging,
the problem is usually ill-defined, not the debate depth.

## Non-negotiables

1. **Cite evidence.** Every blocker claim gets a file:line citation.
2. **Be honest.** CLEAN sign-off is fine if the code is clean — don't invent nits to look thorough.
3. **Push back on vague briefs.** If the request doesn't map to ACs or doesn't include a "what's clean" definition, reject it.
4. **Track the review task-id in the commit.** The commit message must reference the review's task-id so future debugging can trace the audit trail.
