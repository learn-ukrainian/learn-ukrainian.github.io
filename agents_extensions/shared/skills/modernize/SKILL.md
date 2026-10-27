---
name: modernize
description: Decide whether an old PR or branch still belongs on today's base and bring it up to date, or scope one bounded modernization of an area. Use when asked to modernize, refresh or rebase old work; it ends in a hand-off record for full-send or full-stop.
argument-hint: "<pr <number> | branch <name> | area <paths> <outcome>> [then full-send|full-stop]"
---

# Modernize

Modernize the idea, not only the branch. A clean rebase does not prove the change still
belongs in the product, and "no conflicts" is never proof that it is current.

**Who may run it.** A driver, or a worker under a brief that names the target. Modernizing
authorizes rebasing and updating this task's branch. It does not authorize merging, closing,
changing the base branch or widening scope; closing is a driver or CTO act.

**Chain.** `modernize branch codex/x then full-stop`, `modernize area scripts/foo then
full-send`. Without a chain, stop after the verdict and the hand-off record.

Use a dispatch worktree; treat changes already in another worktree as their owner's.

## Input A — an old PR or branch

1. **Record the starting point** after fetching the base and the head:

   ```bash
   git fetch origin
   gh pr view "$PR" --json state,title,body,baseRefName,headRefName,headRefOid,mergeable,statusCheckRollup,reviews,closingIssuesReferences
   OLD_HEAD="$(git rev-parse "origin/$BRANCH")"
   MERGE_BASE="$(git merge-base "origin/$BASE" "$OLD_HEAD")"
   ```

   Use the PR's actual base, not an assumed one. Record state, head, merge-base, checks and
   reviews.
2. **State the original goal in one sentence**, from the title, body, linked issue, commits,
   review threads and the full diff.
3. **Inspect what changed on the base since it diverged**, beyond overlapping lines:

   ```bash
   git diff --name-only "$MERGE_BASE" "$OLD_HEAD"
   git log --oneline "$MERGE_BASE..origin/$BASE" -- $(git diff --name-only "$MERGE_BASE" "$OLD_HEAD")
   gh pr list --state all --search "<symptom or path>"
   ```

   Ask: was the same problem solved elsewhere? Did APIs, schemas or ownership boundaries move?
   Was the touched code deleted or simplified on purpose? Would landing it restore old
   behaviour or create a second way to do the same thing? Is the benefit still worth its cost?
4. **Choose one verdict before pushing anything:**
   - **MODERNIZE** — the goal is still useful and the shape is right. Rebase onto the fetched
     base in a fresh branch at the recorded head, resolving conflicts by the current intent and
     the base's newer invariants. If a conflict exposes a design disagreement, stop and
     reconsider the verdict.
   - **REWORK** — the goal is valid but the shape is wrong. Write the smallest credible rework
     plan. A new design or contract goes to designated approval (rules core P6) first.
   - **SUPERSEDED** — obsolete, solved elsewhere, or not worth its cost. Cite the evidence and
     recommend closing; the driver or CTO decides. Do not rebase an obsolete branch.
5. **For MODERNIZE, prove no intent was lost**, then push with a lease bound to the head you
   recorded:

   ```bash
   git range-diff "$MERGE_BASE..$OLD_HEAD" "origin/$BASE..HEAD"
   git push --force-with-lease="refs/heads/$BRANCH:$OLD_HEAD" origin "HEAD:refs/heads/$BRANCH"
   ```

   Run the focused checks for the touched area and separate real failures from pre-existing
   ones. If the lease fails, someone pushed: fetch and reassess, never overwrite. The rebased
   head needs a `review-loop` delta and fresh CI.

## Input B — a bounded area

For owned paths plus one modernization outcome (never an open-ended cleanup campaign): state
the outcome and the owned paths, check the current callers and requirements of those paths on
the fetched base (`git grep`, the linked issue, the rules that govern them), name the non-goals,
and write the hand-off record directly. No divergent branch is needed.

## Hand-off and report

On MODERNIZE or REWORK, write the hand-off record
([delivery](../full-send/references/delivery.md#hand-off-record)) and start the chained
delivery skill. Lead the report with the verdict and the reason, then: meaningful base
changes, conceptual conflicts (or that none were found), the rebase and push result, checks
run, and the remaining decision. Keep observed facts apart from judgement.

Learned from tstack's `modernize` skill (MIT, Theo Browne); the text is our own.
