---
name: review-loop
description: Run the bounded independent review of one change, from its pushed head to a recorded exact-head verdict, inside full-send or full-stop. Use when the worker that owns a brief, or a driver, needs the review of record for a code, infra or Ukrainian change.
argument-hint: "<branch> [pr <number>]"
---

# Review loop

Take one pushed change to an exact-head cross-family verdict within the review budget, and
record that verdict on the PR. This skill owns rounds, the budget and the finding ledger.
The reviewer's own procedure is `local-code-review`; learner-content review procedure stays
with `track-completion` and `post-build-review`, seated by the `ukrainian` profile below.
ACP discussion is never review.

**Who runs it.** The worker that owns the brief runs it itself (rules core P1), as do the
accountable driver, the integration owner and the CTO. The resolver picks the reviewer; the
runner never picks one, and the resolver never returns a family that authored a commit on the
branch. No eligible reviewer is handled in step 2; nobody substitutes a reviewer of their own
choosing.

**Inputs.** The hand-off record ([delivery](../full-send/references/delivery.md#hand-off-record)):
branch, exact pushed head, base and merge-base, author model of every commit, catalog risk,
budget tier and who set it, the finding ledger and rounds already used.

**Budget, ledger and severity:** [policy](references/policy.md) is the single source. Read it
before round 1 and before every further round.

Recipes run with the primary checkout's interpreter, resolved once
([delivery](../full-send/references/delivery.md#interpreter)):

```bash
PY="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/.venv/bin/python"
```

## Steps

0. **Hand the reviewer an updated head, before round 1 and before every delta round.** Answer the
   PR's outstanding review comments with evidenced dispositions, fix every accepted
   `in_scope_blocker`, and run the relevant checks. Keep tracked P2/P3 follow-ups as they are, and
   escalate a dispute or a scope breaker. A budgeted round is never spent on a defect the author
   already knows. If the change is being discarded for a new approach, skip repairs to the code
   being replaced; the code that stays and its replacement still get checks and exact-head review.
1. **Freeze the round-1 brief** ([brief](references/brief.md)): outcome, acceptance criteria,
   non-goals, threat and input model, dispositions. Record the budget tier
   ([policy](references/policy.md#budget)); later rounds reuse the frozen sections unchanged.
2. **Resolve the target and the reviewer live.** Never pick a fixed model. Derive the review
   profile from the target and record it in the hand-off record (`review.profile`) and the
   frozen brief: `infra` when the change touches the build pipeline, gates, CI, deploy, the
   agent runtime and harness, dispatch, review or routing tooling, or the rules and config that
   govern them; `code` for any other code change. A change that spans both is `infra`.
   A change to learner-facing Ukrainian is `ukrainian`: seat it from
   [ukrainian](references/ukrainian.md), not the resolver.
   `infra` walks a different ladder and excludes code-only seats (Gemini Flash and Muse are
   `review_profiles: [code]` in `scripts/config/model_catalog.yaml`), so the same value goes to
   the resolver (`--review-profile` and `--domain`) and to the dispatch below.

   ```bash
   REVIEW_PROFILE=infra   # or code, as derived above
   "$PY" -m scripts.review.closeout_cli --state-file "$STATE" \
     target --mode branch --branch "$BRANCH" --base "origin/$BASE"
   "$PY" -m scripts.review.closeout_cli --state-file "$STATE" \
     resolve-reviewer --author-model "$AUTHOR_MODEL" --review-profile "$REVIEW_PROFILE" \
     --domain "$REVIEW_PROFILE" --risk "$RISK"
   ```

   Add `--owned-path`, `--subject-seat` or `--subject-family` when the change governs a seat's
   adapter or reviewer hooks (`local-code-review` checklist). Use the returned reviewer, model
   and `requires_silence_timeout`. Exit 1 is fail-closed: no eligible reviewer means escalate
   to the CTO, or use the red-team exception (`workflow.md` § Merge policy) exactly as written
   there. Never review your own work.
3. **Dispatch the reviewer read-only at the exact pushed head**, passing the same
   `$REVIEW_PROFILE`. The dispatcher removes the review worktree when the task settles.

   For bound Contract 1 plan or Contract 2 lesson attempts using `--review-id`, `--attempt-id`
   and `--review-attempt`, follow [Running a bound attempt](../../../../docs/runbooks/formal-review-attempt-isolation.md#running-a-bound-attempt)
   exactly. Do not add `--require-review-verdict` to these bound attempts.

   ```bash
   "$PY" scripts/dispatch.py dispatch \
     --agent "$REVIEW_AGENT" --model "$REVIEW_MODEL" --effort high \
     --mode read-only --worktree --task-id "$REVIEW_TASK" \
     --prompt-file "$REVIEW_BRIEF" --branch "$BRANCH" --pinned-head "$HEAD_SHA" --pr "$PR" \
     --review-profile "$REVIEW_PROFILE" --review-author-model "$AUTHOR_MODEL" --risk "$RISK" \
     --review-mode cross_family --require-review-verdict
   ```

   The dispatcher refuses a review past the PR's round budget, counting every review dispatched
   for the PR whether or not its verdict was recorded ([policy](references/policy.md#budget)).
   Stdout is two lines: the task id, then the run nonce. Record both.
4. **Wait on that task and nonce.** Never re-dispatch.

   ```bash
   "$PY" scripts/dispatch.py wait "$REVIEW_TASK" --run-nonce "$REVIEW_NONCE" --timeout 1800
   ```

   Exit 0: `done`. Exit 124: client expiry while the task still runs; run the same wait again.
   Exit 1: a terminal failure, never approval. Exit 2: a refused request, such as
   `run nonce mismatch`; stop and report it.
5. **Settle.** Read the task JSON: `done`, attested reviewer model and family, and a pinned head
   equal to the current pushed tip. Read the findings themselves, not only the verdict line.
   Give each finding a stable id and a disposition in the ledger ([policy](references/policy.md)).
   Fixes go to the authoring lane (the worker itself when it runs the loop); a driver does not
   patch them in.
6. **Next round or stop.** Start a delta round only if an open blocker, a changed behaviour or a
   moved head needs it, and only after the recorder admits it. Ask the recorder itself before
   dispatching; it applies the clean-merge exemption, a designated grant and the lineage's one
   repair-verification round ([policy](references/policy.md#budget)):

   ```bash
   "$PY" -m scripts.review.record_cf_verdict budget-check --repository "$REPOSITORY" --pr "$PR"
   ```

   Exit 0 admits the round; carry any `repair_round` receipt (its approved and candidate heads,
   class, failed runs or conflicted paths, and `delta_sha256`) into the delta brief, and ask the
   reviewer to APPROVE only with the line `REPAIR_VERIFIED: <delta_sha256>` once it has verified
   that the complete delta is only that repair. Exit 1 is the stop below. A recorded rejection is cleared only at a new
   head ([policy](references/policy.md#clearing-a-recorded-rejection)). The delta brief carries
   the ledger and the fix diff ([brief](references/brief.md#delta-rounds-round-2-and-later)).
7. **Record the verdict on the open PR** (it is open and CI-green at the reviewed head, `full-send` step 4):

   ```bash
   "$PY" -m scripts.review.record_cf_verdict --task-id "$REVIEW_TASK" --pr "$PR"
   ```

   Exit 0 means recorded with a JSON receipt; exit 1 means refused, so nothing is recorded.
   If an accepted P0 or P1 finding lands on a PR that already has a recorded APPROVE, add the
   `hold` label at once: `"$PY" -m scripts.publish pr-edit --number "$PR" --add-labels hold`.

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
- `ukrainian`: the independent cross-family seats named in
  [ukrainian](references/ukrainian.md), with tool-verified findings, seated from that page instead of the resolver; the rest of this skill applies.

## Stop and report

Stop when the current head has a recorded APPROVE and only nits or follow-ups remain, when
`budget-check` refuses the next round, when a dispute is unresolved after two replies, or when a
breaker trips. A head you only need to merge with the base, a CI fix after approval and a
conflict resolution after approval are not stops: `budget-check` admits them while the
exemption or the lineage's repair round applies. A refusal and a tripped breaker escalate to
the CTO with the refusal text; a dispute goes to the operator ([policy](references/policy.md)).
None of them is approval.

Report: exact SHA reviewed, reviewer model, family and harness, verdict, rounds used against
the tier, the ledger with each disposition, diff size before and after review, and who owns
anything still open.

Learned from tstack's `sol-loop` skill (MIT, Theo Browne); the text is our own.
