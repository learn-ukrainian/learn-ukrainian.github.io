# Recipes and tool quirks

Each entry is a quirk an earlier CTO session hit, with the way that works. Rules that govern
the same ground (merge policy, recovery, cleanup) stay authoritative in
`agents_extensions/shared/rules/workflow.md` and `docs/runbooks/ci-gate.md`.

## Primary-checkout write guard

The CTO works from the primary checkout, where a PreToolUse guard
(`agents_extensions/shared/hooks/guard-primary-checkout-write.py`) blocks any shell write
whose target it cannot resolve. A variable assigned by `for`, `read`, `$(...)` or inside a
loop is unknown to it, so an inline loop such as `for r in a b; do mkdir -p "$d/$r"; done`
is refused as `unresolved_shell_variable`. Any `$'` in a Bash command is refused outright,
even inside quotes. Ways that work:

- Put loops in a short scratch Python script (or a script file) and run the file; the guard
  parses the command line, not the script.
- Or write literal paths; `cd <scratch>` first and use relative names.
- Do not put `2>&1` inside `cp` arguments, and never put backticks inside an unquoted
  heredoc (they execute).

## Public and private writes

All GitHub writes go through the publisher, which scans every text field before sending:

```bash
.venv/bin/python -m scripts.publish pr-comment --number <N> --body-file <scratch>/c.md
.venv/bin/python -m scripts.publish pr-create --title "<title>" --body-file <file> --head <branch>
.venv/bin/python -m scripts.publish issue-comment --number <N> --body-file <file>
```

Add `--repo learn-ukrainian/learn-ukrainian-infra-private` for the private repo. Raw
`gh pr comment`, `gh pr merge` and similar writes are refused; raw `gh` is for reads. Prefer
`--body-file` over `--body` for anything with quotes or markdown.

## Merging

Enqueue with `.venv/bin/python -m scripts.publish pr-merge --number <N> --match-head <sha>`
after exact-head cross-family APPROVE and green CI on that head (workflow.md § Merge
policy). `pr-merge` also scans GitHub's default squash subject and body, which carry the PR
title and every commit message, even when the merge queue ignores explicit text. A refusal
names the scanned field (`default_subject`, `default_body`, `subject`, `body`): fix the PR
title with `pr-edit`; a flagged commit message needs a new head, which voids approval and
CI. Usually the keeper enqueues approved green PRs on its own; check its journal before
enqueueing by hand.

## Private PRs and the review trigger

The private review trigger only picks up a private PR whose body carries the lifecycle
marker with the author's family:

```
<!-- hramatka-pr-lifecycle:v1 {"author_family": "anthropic"} -->
```

Use `openai`, `anthropic`, `xai` and so on for the actual author. The trigger's review
prompt carries a capped diff and no checkout. A large private PR therefore comes back
`NO_VERDICT` or `REVIEW_INFRA_FAILURE` (two attempts per head, then it stops). That is not
a code finding: seat a toolful reviewer on a detached checkout (next section).

## Reviews on a sibling repo

`delegate.py dispatch --pr` and `--branch` review attach are unsupported for a sibling repo
such as the private one. Instead:

1. Fetch and create a detached worktree at the exact head under the sibling's own
   `.worktrees/dispatch/<agent>/review-<pr>-<sha8>/`.
2. Dispatch the reviewer read-only with `--cwd <that worktree>` and a brief naming the PR,
   the full head SHA and the required `VERDICT:` line. Drop `--pr`, `--branch` and
   `--pinned-head`; the detached checkout pins the head.
3. Post the verdict on the PR with `scripts.publish pr-comment --repo <sibling>` including
   provenance: head SHA, reviewer model, family and harness, author model and family, task
   ID. `record_cf_verdict` works only for branch-pinned reviews.
4. Remove the review worktree as soon as the verdict is posted and the reviewer has exited.

For branch-pinned reviews in this repo, publish with
`.venv/bin/python -m scripts.review.record_cf_verdict --task-id <id> --pr <n>` after the
reviewer exits.

## Reviewer seating

Resolve code and infra reviewers with `.venv/bin/python -m scripts.review.closeout_cli
resolve-reviewer --author-model <model> --review-profile code --risk <risk>` and run the
invocation it returns. The dispatcher hard-substitutes a seat whose budget is near its cap
(for example Sol to another family). When the CTO has ordered that seat's remaining budget
spent and no other seat is eligible, `delegate.py dispatch --force-agent` dispatches the
requested agent without substitution; record the reason in the brief and the verdict
comment. The other path never needs an override: open the PR (a PR may open before
approval) and let the automatic trigger seat the reviewer. Never park work waiting for a
quota reset.

## CI failure on an unrelated diff

One failure on a run whose diff does not touch the failing code is a service or environment
problem: one rerun with evidence, never an issue or a fix task (core.md P4). Before the
rerun or a re-enqueue after a queue ejection, post this marker on the PR through
`pr-comment`; the keeper and the publisher refuse recovery without it:

```
<!-- ci-recovery-evidence {"pr":<N>,"head":"<PR head SHA>","run_id":<run>,"job_ids":[<every failing job>],"tested_sha":"<tested SHA>","failure_evidence":"<log excerpt or JUnit failure>","unrelated_to_diff":"<why: gh pr diff --name-only vs the failing test, code, fixtures, deps, config, workflow>"} -->
```

Then `scripts.publish run-rerun --number <run id>` for a failed branch or merge-group run
(`--number` is the workflow run ID, not the PR number), or `pr-merge --number <N>
--match-head <sha>` to re-enqueue after a queue ejection (the publisher detects the removal
at that head; `--recovery` forces the recovery path). Both also require a recorded
exact-head APPROVED verdict on the PR. One recovery per unchanged approved head; a second failure, or any
doubt that the cause is unrelated, means stop and report. After fixing the base branch use
`scripts.publish pr-update-branch --number <N>`, not `run-rerun`, which retests the old
merge SHA. Full rules: `docs/runbooks/ci-gate.md`.

## Reap before re-dispatch

A finished task still holds its worktree and branch lease. Before dispatching the same
branch again (a fix round), reap it:

```bash
.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id>          # dry run, read the receipt
.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id> --apply
```

A SKIPPED row is not a disposition: find the reason (live process, unpushed work) and
resolve it safely; never force.

## Claude headless calls

`claude -p --bare` skips OAuth and the keychain and authenticates only with an API key; on a
subscription login it fails with "Not logged in". For subscription seats use the fleet
adapter (`delegate.py dispatch --agent claude`) or plain `claude -p`. Reserve `--bare` for
explicit API-key runs.

## Dispatch helpers

Repeated dispatches (a review per PR, a fix round per PR) belong in a scratch Python script
that builds each `delegate.py dispatch` argv from a table and logs stdout and stderr per
task; grep the log for `run_nonce=`, `SUBSTITUTE` and `queued behind` to learn the nonce,
any seat substitution, and queueing. Classify research dimensions for every dispatch
(`--research-role`, `--research-task-family`, `--research-owned-path`) per the
CLAUDE.md research-registry duty.
