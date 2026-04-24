# Postmortem Management

Sister doc to [`adr-management.md`](adr-management.md) and
[`decision-journal.md`](decision-journal.md). Decisions record temporary policy.
ADRs record durable architecture. Postmortems record bugs that taught us
something expensive enough that the next engineer should not rediscover it.

## The split

| Question | Where it goes |
|---|---|
| "What is our current policy on X?" — might change in 90 days | **Decision** in `docs/decisions/decisions.yaml` |
| "Why does the code look this way?" — permanent structural choice | **ADR** in `docs/architecture/adr/` |
| "Why did this specific bug happen and how do we stop a repeat?" | **Postmortem** in `docs/bug-autopsies/` |

If you are deciding what to do next, write a decision. If you are explaining a
structural choice, write an ADR. If production or the build pipeline already
failed and you found the class of failure, write a postmortem.

## When to write a postmortem

Write a postmortem when the bug is likely to recur or when the debugging path
was expensive enough to preserve.

Strong signals:

- The bug was architectural: cache invalidation, prompt contract drift,
  review/build loop behavior, indexing, persistence, or orchestration state.
- The bug broke production output, publishing, review gates, CI, or the local
  development loop.
- The same category has already happened once before.
- The fix required more than 30 minutes of diagnosis.
- The root cause was not obvious from the final code diff.
- The prevention belongs in a test, hook, invariant, or written process.

Do not write a postmortem for:

- Typos.
- One-line syntax errors.
- Formatting-only fixes.
- Broken local commands where the only lesson is "run the right command."
- Flaky model output that has no actionable prevention.
- Trivial dependency bumps with no system lesson.

The threshold is not blame and not drama. The threshold is whether the record
will save a future engineer from repeating the same investigation.

## Required fields

Every new postmortem must include these four fields:

- **Symptom** — what broke, from the user's or operator's point of view.
- **Root cause** — the underlying bug, design flaw, missing invariant, or
  mismatch that made the symptom possible.
- **Prevention** — what stops this category from recurring.
- **Links** — at minimum the GitHub issue and the commit SHA that shipped the
  fix.

Historical files in `docs/bug-autopsies/` use a few older variants such as
`What Broke`, `Why`, `Files Changed`, and `See also`. The checker accepts those
so we do not spend a PR doing mechanical backfill. New files should use the
template below.

## Template

```markdown
# Bug Autopsy: {short title}

## Symptom

What broke? Write this in observable terms:

- What did the user, builder, reviewer, or CI job see?
- Which command, issue, module, or workflow exposed it?
- What made the failure confusing or expensive?

## Root cause

Why did it happen?

- Name the code path, prompt, config, or process that caused it.
- Distinguish the trigger from the underlying design flaw.
- Include file paths and function names when they matter.

## Fix

What changed?

- Summarize the implementation.
- Link the test, hook, or invariant added with the fix.
- Call out anything intentionally left out of scope.

## Prevention

What stops this class of bug from coming back?

- A regression test.
- A pre-commit or SessionStart check.
- A schema or manifest invariant.
- A documented operating rule only when automation is not practical.

## Links

- Issue: #{issue-number}
- Fix: {commit-sha}
- PR: #{pr-number}
```

One page is better than five. A postmortem should preserve the debug lesson,
not replay the entire debugging session.

## Lifecycle

```
[ bug diagnosed ] ──► [ write postmortem ] ──► [ reference from fix commit ]
                                                   │
                                                   └──► [ INDEX.md updated ]
```

### Written

Write the postmortem while the failure is still fresh. The useful details are
the first ones to disappear: exact symptom wording, misleading hypotheses,
hidden assumptions, and the concrete invariant that would have caught it.

The postmortem can be committed with the fix when the prevention is clear. If
the bug is still under investigation, write a draft in the PR body or issue
first, then land the durable version when the fix ships.

### Referenced

The fix commit or PR should reference the postmortem. That gives future readers
two paths:

- From code to context: the commit explains why the invariant exists.
- From context to code: the postmortem links to the shipped fix.

Do not rely on chat history as the only explanation. Chat is useful during the
incident and poor as an archive.

### Closed

A postmortem is closed when:

- The fix has shipped.
- The prevention exists or the postmortem explicitly explains why prevention is
  procedural.
- The `docs/bug-autopsies/INDEX.md` entry exists.
- `scripts/audit/check_postmortems.py` passes.

The index is regenerated by the checker. Do not hand-sort the table.

## Index

`docs/bug-autopsies/INDEX.md` is the quick lookup surface. It is intentionally
short: date, issue, category, summary. The detail belongs in the individual
postmortem file.

The checker owns the content between:

```markdown
<!-- INDEX-START -->
...
<!-- INDEX-END -->
```

Everything outside those sentinels is hand-written context and must be
preserved verbatim. If the checker changes prose outside the sentinel block,
that is a bug in the checker.

## Automation

Script: `scripts/audit/check_postmortems.py`.

Default mode validates all `docs/bug-autopsies/*.md` files except `INDEX.md`.
If validation passes, it regenerates the index table. Validation failures exit
with code `1`.

### `--quiet`

SessionStart uses quiet mode:

```bash
.venv/bin/python -m scripts.audit.check_postmortems --quiet
```

Quiet mode prints nothing on success. On failure it prints only the specific
errors, one per line, so the hook can surface the problem without dumping a
full report into every session.

### `--regenerate-index`

Use this when you want to refresh `INDEX.md` even while a draft postmortem is
still missing required fields:

```bash
.venv/bin/python -m scripts.audit.check_postmortems --regenerate-index
```

The exit code still reflects validation status. Regeneration is not a way to
hide an incomplete postmortem.

## SessionStart integration

`claude_extensions/hooks/session-setup.sh` runs the checker alongside decision
and ADR hygiene checks:

- Decisions first.
- ADRs second.
- Postmortems third.

Clean postmortems are silent. Missing required fields are surfaced as session
issues with a pointer back to this policy.

## Anti-patterns

- **Blame assignment** — The postmortem is about the system property that let
  the bug happen. "Agent did something dumb" is not a root cause.
- **"Shouldn't have done that" lectures** — Prevention must be concrete. Add a
  test, hook, schema check, or documented threshold.
- **Missing prevention** — A postmortem without prevention is just a story.
- **Confusing trigger with root cause** — "PR #123 changed X" may be the
  trigger. The root cause is the missing invariant that allowed X to break Y.
- **Hand-editing the index table** — Run the checker and review the generated
  diff.
- **Writing a postmortem for every bug** — This creates noise. Use the threshold.
- **Burying links in prose** — Put issue and commit links in `## Links` so the
  checker and future readers can find them.

## Rule of thumb

If the fix taught you a reusable debugging lesson, write the postmortem. If the
only lesson is "be more careful," do not write one until you can name the
mechanism that would have made care unnecessary.

---

*Codified 2026-04-24 after postmortem governance was identified as the missing
third automation surface. Accompanying automation:
`scripts/audit/check_postmortems.py`. Wired into SessionStart via
`claude_extensions/hooks/session-setup.sh`.*
