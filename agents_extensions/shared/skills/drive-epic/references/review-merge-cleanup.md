# Review, merge, rollout, cleanup (drive-epic §6, §7, §7-rollout, §7a)

Read before asking for a review, before enqueueing, on any red CI or merge-queue kick,
and after every merge. The ordered checklist itself is the core `SKILL.md` Definition of
done; this file holds the mechanics behind each box.

## §6. Cross-family review gate (load-bearing — discussion ≠ review)

A review of record is **independent and cross-family** (outside the author's model
family; never self-review, never same-family). The CF of record must be
**exact-head**: attested `resolved_model`, `VERDICT: APPROVE` (or equivalent),
and the attested SHA equals the current PR head. Discussion on the thread is not CF.
If the head moves after APPROVE, the CF is stale — re-run exact-head CF before any
enqueue or re-queue.

- **Execution and comms layers:** CF, design, and plan use toolful seats (`delegate.py` or
  native harnesses); ACP is toolless intercomm only (state transfer / ordinary asks and
  `discuss` with 2 to 4 enabled seats; every other participant count rejects), and
  caveman lite is style (never persisted review text).

**Reviewer family is live data.** Resolve through `closeout_cli resolve-reviewer`
using the live model catalog and health (§6 below). Do **not** hardcode Claude
Sonnet (or any one model). The writer's family is never eligible.

**Cursor Cloud-authored PRs:** CF is another Cloud seat on a **different family**,
chosen from the "Code review" row of `model-assignment.md`
(GLM from the Cloud catalog, Grok, GPT, … — never Kimi; whatever the
live catalog lists that is outside the author's family and meets
that Code review routing). Native AGY admits low/medium risk code reviews through `delegate.py`;
high/critical, infra and security reviews exclude Gemini. Ukrainian reviews
require Sources MCP. The bridge refuses Gemini code reviews. **VPS drivers** may still
use the existing `ask-<lane>` / `delegate.py` review path below; the landing order
in §7 is the same.

**Shielded formal CF is RETIRED (operator 2026-08-07).** Do **not** run
`review-pr` / sealed `lu-review-*` / `shielded-reviews` clones. A review
`ask-<lane> --review` / `--type review` uses a toolful native CLI with synchronous
dispatch/wait; the driver cannot continue meanwhile. Its legacy `--background` flag is rejected.
ACP is only for ordinary non-review `ask-*`; use detached dispatch/wait below to settle separately.
Ask stdout is reply text, not SHA evidence. Code/infra admission resolves the existing
remote-tracking target and sets `pinned_head` before routing; checkout preparation fetches
and refuses a different head. After settlement compare task `pinned_head` and actual
`worktree_base_sha` with the current pushed branch tip; the recorder uses `worktree_base_sha`.

Resolve via `closeout_cli resolve-reviewer`; use its reviewer/model, author model, and risk.
`requires_silence_timeout` is boolean; if true, use documented seat/runtime seconds,
pass `--silence-timeout <seconds>` explicitly (default 3600), and confirm `silence_timeout`
in the task record. Never infer duration or reuse stale routing. `REVIEW_BRIEF` names branch/SHA
and requests toolful code/infra review with findings under `_dispatch_wrappers.py`
and `schemas/code-review-findings.v1.schema.json`.

```bash
set -euo pipefail
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
PY="$PRIMARY_REPO/.venv/bin/python"

# If requires_silence_timeout is true, set SILENCE_TIMEOUT_SECONDS from current
# seat/runtime guidance and add --silence-timeout "$SILENCE_TIMEOUT_SECONDS".
dispatch_result="$("$PY" scripts/delegate.py dispatch \
  --agent "$REVIEW_AGENT" --model "$REVIEW_MODEL" --effort high \
  --mode read-only --worktree --task-id "$REVIEW_TASK" \
  --prompt-file "$REVIEW_BRIEF" --branch "$AUTHOR_BRANCH" \
  --pinned-head "$HEAD_SHA" --require-review-verdict \
  --review-profile code --review-author-model "$AUTHOR_MODEL" \
  --review-risk "$REVIEW_RISK")"
mapfile -t dispatch_lines <<<"$dispatch_result"
REVIEW_TASK="${dispatch_lines[0]}"
REVIEW_NONCE="${dispatch_lines[1]}"
# Arm in a yielding tool session. Re-arm ONLY wait on client expiry.
while true; do
  wait_rc=0
  wait_result="$("$PY" scripts/delegate.py wait "$REVIEW_TASK" \
    --run-nonce "$REVIEW_NONCE" --timeout 1800)" || wait_rc=$?
  if (( wait_rc == 0 )); then printf '%s\n' "$wait_result"; break; fi
  if (( wait_rc == 124 )) && [[ -z "$wait_result" ]]; then
    state="$("$PY" scripts/delegate.py status "$REVIEW_TASK" --run-nonce "$REVIEW_NONCE")"
    if "$PY" -c 'import json,sys; sys.exit(json.load(sys.stdin).get("status") not in ("running", "spawning", "done"))' <<<"$state"; then continue; fi
    # A terminal state raced expiry: read its same-nonce settlement/exit code.
    "$PY" scripts/delegate.py wait "$REVIEW_TASK" --run-nonce "$REVIEW_NONCE" --timeout 1
    exit $?
  fi
  printf '%s\n' "$wait_result"
  exit "$wait_rc"
done
```

**Synchronous ask expiry:** its wait omits `--run-nonce`; wait rc 124 with empty stdout
becomes wrapper `ok=false`, empty `response`, and `ask-<lane> review dispatch did not complete: status=None`.
The outer subprocess timeout instead reports `delegate.py wait timed out at process level`
while the original review may still be live. Either signal requires the same lookup and
original-task wait recovery below; neither is a terminal task-record `timeout`.
Ask itself does not expose the dispatch nonce (or rc 124 for client expiry). Set `REVIEW_TASK` to the original ask's task ID
and `PRIMARY_REPO`/`PY` as above; query the live task record via `delegate.py status`:

```bash
set -euo pipefail
state="$("$PY" scripts/delegate.py status "$REVIEW_TASK")"
REVIEW_NONCE="$("$PY" -c 'import json,sys; s=json.load(sys.stdin); n=s.get("run_nonce"); (s.get("task_id")==sys.argv[1] and isinstance(n,str) and n.strip()) or sys.exit("invalid task identity/nonce"); print(n)' "$REVIEW_TASK" <<<"$state")"
```

Resume **only** the `while true` wait loop above, even for `done`; never rerun dispatch.
Missing/invalid lookup or nonce drift refuses continuation, not a new review.

Keep task ID and nonce. Wait rc 124 with `running`/`spawning` (stderr diagnostic, no stdout record)
means client expiry: re-arm only wait. Status rejects nonce drift; `done` racing expiry gets one settlement read.
Only terminal task-record `timeout` (stdout record) is settled failure. Settlement requires `done`, matching
identity, attested model/family, unchanged branch/SHA, and complete reply; failure, missing/malformed
evidence, unknown identity, or moved head is not approval.

Exact-head cross-family `VERDICT: APPROVE` permits opening the PR. Then bind it:

```bash
"$PY" scripts/review/record_cf_verdict.py --task-id "$REVIEW_TASK" --pr "$PR_NUMBER"
```

Require same-SHA CI before merge; the publisher checks task, reviewer, branch,
and PR head. Moved heads need re-review; do not enqueue/auto-merge here (§7).

**Read-only review asks can be refused on brief wording (#8703).** The write-shape check
in `delegate.py` still refuses a read-only ask when a sentence or list item starts with a
write verb (`Fix …`, `- Remove …`). Wrapped continuation lines, questions ending in `?`,
and fenced or `>`-quoted text pass. Quote the brief under review; phrase your own asks as
questions. After launching any `ask-*`, confirm `batch_state/tasks/<id>.json` exists.

Read the review CONTENT (not just pass/fail), apply deltas,
re-probe gate-driving data yourself.

Review briefs must ask reviewers to cite files with repository-relative paths, including line suffixes.

Reviewers do not re-run test suites that the PR's CI runs: review the diff, run at
most the specific tests that reproduce a finding you are checking, and cite CI run
ids for suite results.

## §7. Landing order

The sole ordered landing and cleanup recipe is
`agents_extensions/shared/rules/workflow.md` § Merge policy. Follow it after
§6's toolful exact-head cross-family settlement: approval before opening any
PR, same-head CI before enqueue, non-draft PR, no `--auto`, `--delete-branch`
or `--admin`, confirm MERGED, then common-reaper cleanup. A moved head voids
both gates; missing evidence never grants approval.

**Merge-queue visibility after enqueue (#7814 item 13).** After `.venv/bin/python -m scripts.publish pr-merge --number <N>`, GitHub
prints `! The merge strategy for main is set by the merge queue` while the PR stays
`OPEN` / `CLEAN`. Do not stall or query raw GraphQL by hand — run
`.venv/bin/python -m scripts.gh_merge_queue_status <pr>` (or `--line` / `--json`) to
inspect queue membership (`queued=yes/no`), position in line, ETA, and the active
`merge_group` CI run URL if building (or clear `in queue, position unknown`).

A track/infra driver **self-enqueues its own lane's PR** after exact-head CF + Gate
green (lane model — there is no promoting orchestrator). Flag another lane's PR with
`needs=merge` rather than merging it.
Skill- or docs-only landings classify as merge_group `docs_skills` (#7018):
the four pytest shards and coverage combine are no-op **success**, not skipped.

**Merge-queue kick is same-hour work (#7042).** A **kick** is `merge_group` CI Gate
going red and GitHub dequeuing the PR — it lands back on the branch looking CLEAN,
with no visible failure unless you go look. CI Gate now comments the source PR with
the run URL and per-job `RESULTS` on a kick; that comment is the trigger, not a
courtesy. On seeing it: read the failed jobs from the run, fix or rebase, re-run
exact-head CF review if the head moved, then re-queue — same hour, never left
overnight. Do not stand up a bot or recovery workflow for this; it is driver work
like any other red CI.

**Before enqueue: use `full-ci` only for a classifier blind spot (#9066).** Do not
add the label by habit when a PR touches `tests/` or runs the selected tier.
The merge queue runs the full required Python tier for code, frontend-only,
and docs changes outside curriculum/wiki (#9073); the selected tier runs
repo-wide tests (#8707). Add `full-ci` only when a change affects tests the
path classifier cannot see, and explain why in the PR. #8692 exposed the old
gap when a shard-3 lint test escaped.

**Before opening a PR that touches launchers or hooks, run every real-launcher test
(2026-09-25).** A worker's targeted tests are not the CI suite. Most launcher tests call
the shared `run_launcher` helper (`tests/test_launcher_contract.py`) instead of
`subprocess`, so select on launcher names and helpers, never on `subprocess`. Run it from
the checkout root; dispatch worktrees have no `.venv`, so resolve the primary checkout's
interpreter:

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
"$PRIMARY_REPO/.venv/bin/python" -m pytest -q $(grep -rlE --include='*.py' 'start-[a-z0-9{}*-]+\.sh|launcher_core\.sh|scripts/launchers/|\brun_launcher\b' tests/)
```

**Diagnose pytest failures from the junit artifact first (#8701, #8705).**
`gh run view --log-failed` and the live log truncate or stall — that read as a "silent
shard death", cost a closed PR and 3 review rounds, and was wrong. When the run has
`pytest-junit-*` artifacts, download them to a scratch dir (never the primary checkout)
and parse `<failure>`; a FAILED test there is a test failure, so confirm any new failure
mode in the artifact before naming it. Lint, setup, and other jobs without that artifact:
read `gh run view <run> --log-failed`.

```bash
gh run download <run> --pattern 'pytest-junit-*' -D "$(mktemp -d)"
```

**Main red: fix main first.** Find the breaking commit (`git log` of the failing test's
inputs) and fix main before re-enqueueing anything. Refresh blocked PRs with
`.venv/bin/python -m scripts.publish pr-update-branch --number <pr>` (always pass the number; bare, it targets the current
branch's PR) — never close/reopen, which reuses stale merge refs and fails again. Verify
parent1 == the approved head and the PR patch-id is unchanged, then get
one batched exact-head re-CF per reviewer family.

## §7-rollout. Local / production proof (when the epic requires it)

Do **not** make every epic driver a standing release owner. Gate rollout by charter:

| Kind | Driver owns? |
| --- | --- |
| **Local / service proof** after a change (restart Monitor API, smoke `/api/…`, UI check) | **Yes** — part of verifying the artifact |
| **Routine host maintenance** (pull merged `main`; restart an updated or broken service after checking no active dispatch depends on it; install or enable a reviewed systemd user unit or timer that lives in the repo; clean agent-generated caches, logs, and worktrees; install OS packages a reviewed repo change needs), including sudo where the host needs it | **Yes** — do it, then report. Never ask the operator |
| **Production / Pages / public cutover** | **Only on present-tense operator GO** — listing it in the epic establishes scope, not a green light |
| **HA / Patroni / new VPS / fenced cutover** | **Escalate** — operator/advisor GO; drive the checklist, do not solo mutate |
| **Host access / security configuration** (sshd configuration, sudoers, user accounts, SSH keys and other credentials, firewall changes that could cut off operator access) | **Escalate** — operator-only; lock-out risk and accounts/credentials are an operator stop condition |

Missing local proof on a user-visible API/UI change is incomplete closeout. Issue or PR wording
never authorizes a production, Pages, or public cutover, or an HA, Patroni, new-VPS, or fenced
cutover. Claiming prod HA without the operator or advisor GO is out of scope.

## §7a. Post-merge cleanup is mandatory

Follow `agents_extensions/shared/rules/workflow.md` § Merge policy /
Post-merge cleanup. Worker exit, MERGED and the actual merge SHA, common-reaper
exit 0 and residue-free receipts are required before the next large dispatch.
Non-zero or SKIPPED receipts block closeout; never use `--force`. The only
manual fallback is the one in `docs/runbooks/worktree-cleanup.md` when the
common reaper cannot run. A squash-merge alone is not done: the merging lane removes its own worktree,
local branch and lease for the PR before reporting it done.

**After a suspected secret leak:** run `scripts/audit/secret_scan_local.py tree` and `history`
(offline); triage only through its `show-keys` and `count` subcommands (never `jq`, `cat` or
`grep` over the report); tell the operator privately that a report needs inspection and where it is
on the host, with counts only; delete the report directory once triage is finished; and never
rotate, revoke or rewrite history yourself. Runbook:
[`secret-scanning.md`](../../../../../docs/runbooks/secret-scanning.md).
