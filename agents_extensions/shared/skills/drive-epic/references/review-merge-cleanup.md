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

**Reviewer family is live data.** Pick the reviewer from the live Cursor Cloud
catalog and the served `/api/rules` reviewer-seat rule. Do **not** hardcode Claude
Sonnet (or any one model). The writer's family is never eligible.

**Cursor Cloud-authored PRs:** CF is another Cloud seat on a **different family**,
chosen from the "Code review" row of `model-assignment.md`
(GLM from the Cloud catalog, Grok, GPT, … — never Kimi; whatever the
live catalog lists that is outside the author's family and meets
that Code review routing). Gemini/AGY reviews Ukrainian only, never code
(operator 2026-09-25). **VPS drivers** may still
use the existing `ask-<lane>` / `delegate.py` review path below; the landing order
in §7 is the same.

**Shielded formal CF is RETIRED (operator 2026-08-07).** Do **not** run
`review-pr` / sealed `lu-review-*` / `shielded-reviews` clones — the CLI fails
closed. Use lightweight direct review:

```bash
printf '%s\n' "Cross-family review of PR #<N> at head <SHA>: VERDICT + findings." | \
  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-<lane> - \
    --task-id review-<N> --type review
# Post the exact-head verdict on the PR (attest resolved_model + SHA).
# Do not enqueue or auto-merge here — landing order is §7.
```

This command line is unchanged, but the transport underneath it is not ACP
(operator 2026-08-23, #7155): `--type review` / `--review` / `--pr` / `--branch`
route to a headless native CLI with tools (`delegate.py dispatch --agent <lane>
--worktree`, `gh`/pytest available), never the tool-less `--deny-all --no-fs
--no-terminal` chat transport. ACP stays for ordinary, non-review `ask-*`.

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

## §7. Merge discipline

PRs only — never commit or merge to `main` directly.

**Binding public landing order (operator 2026-08-30 / #7450; CF-attest retired
2026-09-03; CF-before-CI clarified 2026-09-18):** The
forge does not enforce independent review, so the driver verifies both gates
itself. Auto-merge / enqueue is **not** review; PRs have reached `main` that
way with empty reviews. Drivers follow this order:

0. **CF review-fix before CI (binding).** Push the branch. Run exact-head CF
   via `ask-<lane> --branch <name>` (or equivalent). Fix → re-CF until
   `VERDICT: APPROVE` on the tip. **Do not open any PR** (draft or ready)
   while CF is open or while iterating findings — CI also runs on
   draft PRs, so a draft still burns Gate during the fix loop. Open the PR only after CF APPROVE; CI
   runs once on that tip.
1. **Independent cross-family exact-head CF** — attested `resolved_model`,
   different family from the author, APPROVE on the tip (post on the PR once
   open, bound to that SHA).
2. **Open the PR** → **CI Gate green** on that **same** head.
3. **Merge queue only after both.** Enqueue then; never before.

**Never auto-merge or enqueue first.** Never treat `.venv/bin/python -m scripts.publish pr-merge --auto` as a
substitute for CF. Do **not** arm `--auto` and wait for Gate. Never enqueue a
**draft**. Blocking CI red → never `--admin`-bypass.

```bash
# Only after §7 steps 1 and 2 on this exact head. Never --auto.
.venv/bin/python -m scripts.publish pr-merge --number <N>

# Check merge-queue status / position / ETA after enqueue (#7814 item 13):
.venv/bin/python -m scripts.gh_merge_queue_status <pr>
```

**Never pass `--delete-branch` to `.venv/bin/python -m scripts.publish pr-merge --number <N>` while this repo uses a merge queue** —
deleting the head ref mid-queue can close the PR without landing (known failure mode).
The remote branch is deleted only after `gh pr view` shows `MERGED`, by §7a closeout.

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

## §7a. Post-merge cleanup is mandatory (binding — operator 2026-08-07)

**A squash-merge is not done until cleanup proves free of that PR's residue.** Chat
promises do not bind; this section does. Leaving dispatch worktrees or tmp residue
after merge is a process defect (ENOSPC / disk full is the known failure mode).

**Order after `gh pr view <N>` shows `MERGED`:**

1. **Confirm** merge SHA.
2. **`merge_closeout` first** — after all processes have left the target worktree(s), run:
   ```bash
   .venv/bin/python -m scripts.orchestration.merge_closeout <N> --apply
   ```
   This one command proves the PR is `MERGED`, finds every worktree tied to it (by
   branch or exact merged head SHA — detached review-checkout siblings included),
   reaps each through the P0 reaper (`--merged`/`merged_pr_only`, exact `--worktree`,
   no second deletion hand, no `--force`), and proves the remote and local branch are
   both gone. It exits non-zero on any residual — treat that exit as a blocker, not
   permission to retry with `--force`.
3. **Manual fallback only** — if `merge_closeout` cannot run, follow
   [`worktree-cleanup.md`](../../../../../docs/runbooks/worktree-cleanup.md) for the
   kill switch, rescue restore, and allowlisted dual paths before using
   `git worktree remove`.
4. **Issues** — close every issue the PR names with evidence, or post a comment after
   the merge naming exactly what remains and what it waits on (core Definition of done).
5. **Branches** — `merge_closeout --apply` deletes the pull request's remote and
   local branch. A squash merge still counts: the old tip is the PR head, not a
   commit on `main`. Agent scratch refs (`*/review-*`, `rescue/*`, `pr-*`) are not
   a pull request head; the hygiene sweep deletes them when they have no open PR,
   and a later review round deletes the earlier round's branch. Do not leave those
   refs behind. Run `.venv/bin/python -m scripts.hygiene.branch_sweep --json` for the
   session branch sweep; add `--apply` only after reviewing its receipts. Then run
   `git fetch --prune`.
6. **Prove** — `df -h /` and `git worktree list` show no zombie for that PR.

**After a suspected secret leak:** run `scripts/audit/secret_scan_local.py tree` and `history`
(offline); triage only through its `show-keys` and `count` subcommands (never `jq`, `cat` or
`grep` over the report); tell the operator privately that a report needs inspection and where it is
on the host, with counts only; delete the report directory once triage is finished; and never
rotate, revoke or rewrite history yourself. Runbook:
[`secret-scanning.md`](../../../../../docs/runbooks/secret-scanning.md).
