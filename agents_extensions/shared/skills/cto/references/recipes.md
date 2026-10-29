# Recipes and tool quirks

Ways of working earlier CTO sessions settled on. Each procedure lives with its owner; this
file only points there and adds what the CTO seat learned on top.

## Writes and merging

- Delivery follows the `full-send` and `full-stop` skills; publishing follows
  `workflow.md` § Public GitHub publishing; CI recovery follows `docs/runbooks/ci-gate.md`.
- The merge-queue keeper usually enqueues on its own; check its log before enqueueing by
  hand.

## Publish orders

Write every message body with a quoted heredoc `<<'EOF'`. For new orders, put `@UTC@`
in the body and use this scratch helper, with the prescribed interpreter and registered slot:

```bash
cat > "$TMPDIR/order.txt" <<'EOF'
@UTC@ <order body>
EOF
publish_order() {
  local body="$1" recipient="$2" idempotency_key="$3"
  shift 3
  sed "s/@UTC@/$(date -u +%Y-%m-%dT%H:%M:%SZ)/g" "$body" |
    "$PROJECT_PYTHON" -m scripts.fleet_comms channel publish cto - \
      --sender "$LU_INBOX_WORKER" --source cto --recipient "$recipient" \
      --idempotency-key "$idempotency_key" "$@"
}
publish_order "$TMPDIR/order.txt" "<registered-slot>" "<unique-order-key>"
```

`$LU_INBOX_WORKER` is the sender (your consumer identity), never a recipient; the CTO's own
recipient is `claude-cto`.

Preserve required message references per `docs/runbooks/driver-seat-cli-move.md` § 5.

Clear system temp only through `scripts.hygiene.tmp_sweep` (or a reviewed change to it), never
with an ad-hoc deleter: a one-off script that removed `/tmp/tmux-1000` left the context guard
unable to see or restart the seat for 13 hours.

## CI recovery

Before a rerun, identify the first failing step and its terminal error. Verify that passing
comparison runs executed that step. Compare failed paths with the full applicable diff;
follow `docs/runbooks/ci-gate.md` for the one evidenced recovery attempt.

## Reviews

Seat, run and record every code or infra review with the `review-loop` skill; the reviewer
follows `local-code-review`. A review dispatch alone publishes nothing, and the merge-queue
keeper waits for the published verdict.
Name allowed read tools per harness: Codex uses read-only shell; Cursor/Grok uses tracked-file
reads. Read attestation from the task JSON's top-level `resolved_model_known`, `resolved_model`
and `resolved_model_source`; never grep nested status output for these fields.

## Test grants

A grant names each approved test function and its file, the defect class in the test name or
docstring (`docs/best-practices/test-quality.md`), and that no other tests are added.
Classify each granted case before the grant is sent:
- Defect case: reproduces a defect in the code being changed. It must fail on the unfixed code
  and pass after the fix.
- Control case: guards an invariant the change could break on a path the change touches. It
  passes before and after, must exercise the changed path, and names the defect class it would
  catch.
The PR body lists which cases are defect cases and which are controls, with the before and
after result of each. Never require a control case to fail before the fix.

## Worktree disposition before re-dispatch

A finished task's worktree and branch lease end when the dispatcher settles it and removes the
worktree. Before dispatching the same branch again, read its `worktree_disposition`; if the
worktree was retained, remove it only after confirming its content is published
(`workflow.md` § Post-merge cleanup, `docs/runbooks/worktree-cleanup.md`).
A retained worktree with modified tracked files is left for the dispatcher or reported to the
operator. Never discard its changes (or run any other command under "Dangerous Commands" in
`docs/best-practices/gitflow.md`) without the operator's explicit yes, even to satisfy the
guarded remover.

## Dispatch helpers

Record each new in-flight task with `lu-driver-state add --lane cto --kind inflight`, its
owner and done condition. Attach its task ID with `link <id> task <task-id>` and record the
FULL run nonce with `note <id> <text>` so the tracker handoff can re-arm its wait.

Run every dispatch through the scratch table helper. It builds each
`dispatch.py dispatch` argv from a table and logs stdout and stderr per task; grep the log
for `run_nonce=`, `SUBSTITUTE` and `queued behind`. Record the actual substituted identity.
Run Claude-account dispatches from the seat as `env -u CLAUDE_CONFIG_DIR .venv/bin/python
scripts/dispatch.py dispatch ... --claude-account <label>`: the launcher exports
`CLAUDE_CONFIG_DIR` into the seat's shells, and the dispatcher refuses an explicit account
while that ambient value is set (`claude_account_ambient_conflict`).
Use exact owned file paths; never claim a shared subtree for an optional edit.
Before choosing owned paths, `git grep` the changed modules' names in `tests/`, including the
root `tests/*.py` files, and make every file that matches an owned path, so the worker can
update the tests that pin the changed behaviour.
Retained evidence, evaluation material and anything a later session needs goes under
`/home/ops/ops-state/<topic>/` (mode 0700 when private), never a session scratchpad, and the
brief names that path.
Before writing a brief from a tracker item, read its full history with `lu-driver-state show <id>`
(all notes): operator amendments are recorded as notes.
Each brief also sets the worker's follow-up cap: how many follow-up tasks it may start and in
which owned paths (rules core P1).
Briefs state expected eligible PR lines and files; require a one-line size justification
above the `workflow.md` small-batch threshold, including data files.
Limit worker-local checks to Ruff and explicitly named test files for the changed module,
under a 10-minute timeout. Never expand to all importers. PR CI Gate runs admission checks
and the affected tests; the merge-group CI Gate runs the full suite.
