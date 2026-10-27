---
name: review-loop
description: Run the bounded independent review of one change, from its pushed head to a recorded exact-head verdict, inside full-send or full-stop. Use when a driver needs the review of record for a code or infra change; a worker asks its driver instead.
argument-hint: "<branch> [pr <number>]"
---

# Review loop

Take one pushed change to an exact-head cross-family verdict within the review budget, and
record that verdict on the PR. This skill owns rounds, the budget and the finding ledger.
The reviewer's own procedure is `local-code-review`; learner-content review stays with
`track-completion` and `post-build-review`. ACP discussion is never review.

**Who runs it.** The accountable driver, the integration owner or the CTO. A worker does not
dispatch reviewers (rules core P1): it sends its driver a review request through Fleet Comms
with the branch, exact head and hand-off record, then waits for the verdict.

**Inputs.** The hand-off record ([delivery](../full-send/references/delivery.md#hand-off-record)):
branch, exact pushed head, base and merge-base, author model of every commit, catalog risk,
budget tier and who set it, the finding ledger and rounds already used.

**Budget, ledger and severity:** [policy](references/policy.md) is the single source. Read it
before round 1 and before every further round.

## Steps

1. **Freeze the round-1 brief** ([brief](references/brief.md)): outcome, acceptance criteria,
   non-goals, threat and input model, dispositions. The reviewer or the CTO records the budget
   tier before round 1. Later rounds reuse the frozen sections unchanged.
2. **Resolve the target and the reviewer live.** Never pick a fixed model.

   ```bash
   .venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE" \
     target --mode branch --branch "$BRANCH" --base "origin/$BASE"
   .venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE" \
     resolve-reviewer --author-model "$AUTHOR_MODEL" --review-profile code --risk "$RISK"
   ```

   Add `--owned-path`, `--subject-seat` or `--subject-family` when the change governs a seat's
   adapter or reviewer hooks (`local-code-review` checklist). Use the returned reviewer, model
   and `requires_silence_timeout`. Exit 1 is fail-closed: no eligible reviewer means escalate
   to the CTO, or use the red-team exception (`workflow.md` § Merge policy) exactly as written
   there. Never review your own work.
3. **Dispatch the reviewer read-only at the exact pushed head.**
   Requires #11785 (v2 protected review). Until it is merged on your base, launch and settle
   with the `delegate.py` recipe in drive-epic §6
   ([review-merge-cleanup](../drive-epic/references/review-merge-cleanup.md)).

   ```bash
   .venv/bin/python scripts/dispatch.py dispatch \
     --agent "$REVIEW_AGENT" --model "$REVIEW_MODEL" --effort high \
     --mode read-only --worktree --task-id "$REVIEW_TASK" \
     --prompt-file "$REVIEW_BRIEF" --branch "$BRANCH" --pinned-head "$HEAD_SHA" \
     --review-profile code --review-author-model "$AUTHOR_MODEL" --risk "$RISK" \
     --review-mode cross_family --require-review-verdict
   ```

   Stdout is two lines: the task id, then the run nonce. Record both.
4. **Wait on that task and nonce.** Never re-dispatch.

   ```bash
   .venv/bin/python scripts/dispatch.py wait "$REVIEW_TASK" --run-nonce "$REVIEW_NONCE" --timeout 1800
   ```

   Exit 0: `done`. Exit 124: client expiry while the task still runs; run the same wait again.
   Exit 1: a terminal failure, never approval. Exit 2: a refused request, such as
   `run nonce mismatch`; stop and report it.
5. **Settle.** Read the task JSON: `done`, attested reviewer model and family, and a pinned head
   equal to the current pushed tip. Read the findings themselves, not only the verdict line.
   Give each finding a stable id and a disposition in the ledger ([policy](references/policy.md)).
   Fixes go to the authoring lane; the driver does not patch them in.
6. **Next round or stop.** Start a delta round only if the budget allows it and an open blocker,
   a changed behaviour or a moved head needs it. The delta brief carries the ledger and the fix
   diff ([brief](references/brief.md#delta-rounds-round-2-and-later)).
7. **Record the verdict once a PR exists** (the PR may already be open, `workflow.md:195`):

   ```bash
   .venv/bin/python -m scripts.review.record_cf_verdict --task-id "$REVIEW_TASK" --pr "$PR"
   ```

   Exit 0 means recorded with a JSON receipt; exit 1 means refused, so nothing is recorded.
   If an accepted P0 or P1 finding lands on a PR that already has a recorded APPROVE, add the
   `hold` label at once: `.venv/bin/python -m scripts.publish pr-edit --number "$PR" --add-labels hold`.

## Always true, whatever the round

- `SECURITY_VERDICT FAIL` blocks. INCONCLUSIVE, `BLOCKED`, timeout, error or no reply is never
  approval. A moved head voids the verdict.
- The `local-code-review` Step 6 breakers apply in every round.
- A decline needs file:line or test evidence and never clears a blocking verdict.

## Muse second reader (advisory)

On a PR with catalog risk `critical`, the driver may add Muse Wonder Full as a second,
read-only reader. Its findings enter the same ledger and are triaged like any other finding.
It is advisory: it is not a gate, it never replaces or outvotes the reviewer of record, and its
silence or approval proves nothing. Making it mandatory needs the operator's approval.

## Review profiles

- `code` and `infra`: this skill as written.
- **EXTENSION POINT — `ukrainian` profile (not yet active).** A follow-up will define it after
  a qualification run: two independent reviewers, with findings verified through the Sources
  MCP. Until that follow-up lands, Ukrainian review keeps its current route
  (drive-epic §6 Ukrainian content variant; `ukrainian-linguistics.md` §8). Do not apply a
  `ukrainian` loop policy from this note.

## Stop and report

Stop when the current head has a recorded APPROVE with no open blocker, when the budget is
exhausted, when a dispute reaches its second exchange, or when a breaker trips. The last three
escalate to the CTO; none of them is approval.

Report: exact SHA reviewed, reviewer model, family and harness, verdict, rounds used against
the tier, the ledger with each disposition, diff size before and after review, and who owns
anything still open.

Learned from tstack's `sol-loop` skill (MIT, Theo Browne); the text is our own.
