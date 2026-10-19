# Lifecycle closeout after an unrecorded push

## Outcome

For #11058, prevent another dispatch from losing its local lifecycle observation when its worktree is removed before PR creation. Recommend capturing the existing observation in the shared removal guard, option D below. This covers dispatch settle and the scheduled clean-pushed reaper. Keep historical recovery strict. The Atlas task remains blocked because its publication evidence does not satisfy the supported worktree-observation contract.

This is a design proposal, not recovery authorization. It changes no code, lifecycle ledger, task record, receipt, reaper eligibility, or behavior-proof requirement. `claude-infra` owns review, approval, implementation follow-up, and landing. Atlas owns its separate behavior evidence for #11039.

## Evidence

The inspected base is `71e64a041b822ad5ccc848c495e3b9b25ff73c06`, fetched from `origin/main` on 2026-10-19. Commands ran in the assigned dispatch worktree. Runtime inputs came from the shared canonical state root, read-only. In the commands below, `PROJECT_PYTHON` means the task-prescribed shared interpreter. It can be located without publishing a host path:

```bash
PROJECT_PYTHON="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/.venv/bin/python"
git fetch origin main
git rev-parse HEAD origin/main
git status --porcelain
gh issue view 11058 --json number,title,body
```

Both revisions were the inspected base in the initial investigation; status was empty. Round two started at local and remote branch head `d2284a21c5d1fc003645d09e33282259c5b1f1d4`, with an empty status. A fresh fetch still resolved `origin/main` to the inspected base. The record reproduction and fixed-window census were rerun during round two. The issue's stop policy prohibits implementing weaker typed-proof requirements before designated approval.

### The real records and refusal

The task is `batch_state/tasks/atlas-10672-cloze-budget-opus.json`. Its carrier identifies `.agent/task-lifecycle/ab3a61ed042f6f43/issue-11039.json`. Its preservation manifest is `batch_state/preserved/atlas-10672-cloze-budget-opus/883241bae5fa49e5a2a1a9367ca09135.manifest.json`.

`task_closeout reconcile` has no dry run. Despite being read-only toward GitHub, `cmd_reconcile` appends and writes the local ledger at [task_closeout.py:1052](../../scripts/orchestration/task_closeout.py#L1052); its arguments at lines 1198 through 1204 offer no write suppression. Therefore this investigation did not invoke it. This read-only reproduction uses the stored observation and the same readiness function:

```bash
"$PROJECT_PYTHON" - <<'PY'
from pathlib import Path
import json
from scripts.orchestration import task_lifecycle as tl
from scripts.fleet.ignored_task_output import verify_retrieval

root = tl.canonical_state_root(Path.cwd())
task = json.loads((root / 'batch_state/tasks/atlas-10672-cloze-budget-opus.json').read_text())
ledger = json.loads((root / '.agent/task-lifecycle/ab3a61ed042f6f43/issue-11039.json').read_text())
manifest = json.loads((root / task['preserved_artifacts']['manifest_path']).read_text())
verify_retrieval(root, manifest)
print('bundle_verification=PASS')
print('record_contains_typed_push', 'pushed_exact_head' in json.dumps(task))
print('record_has_merged_reaper_proof', bool(task.get('worktree_reap_proof')))
print('bundle_json_files', list((root / manifest['location']).rglob('*.json')))
receipt = ledger['observation_receipts'][-1]
print('local_blockers', tl._local_readiness(receipt['observation']['local']))
print('recorded_hard_blockers', receipt['hard_blockers'])
reap = task['worktree_reap']
print('removal', {k: reap.get(k) for k in ['action', 'reason', 'branch', 'dirty', 'error', 'pr']})
for name in ['10672-push.exit', '10672-push.log']:
    text = (root / manifest['location'] / 'batch_state/reports' / name).read_text()
    for line in text.splitlines():
        if name.endswith('.exit') or '[new branch]' in line:
            print(name, line)
PY
```

The bundle verifies. The record contains no typed push status and no `worktree_reap_proof`; the preserved bundle contains no JSON files. Its nine preserved files include `10672-push.exit`, whose bytes are `0\n`, and `10672-push.log`, which contains:

```text
 * [new branch]              HEAD -> claude/atlas-10672-cloze-budget-opus
```

The log also records the OPSEC push scan, pre-push admission waits, and upstream tracking setup. It contains no typed exact-head observation or test-result summary. A successful push is consistent with these bytes; a failed push log would not be sufficient. Neither log alone identifies the pushed SHA or authenticates the implementation worktree.

The preservation receipt records `retention_disposition: retrieved`, `next_condition: none`, `count: 9`, `bytes: 10409`, the task ID, run nonce, worktree-path digest, per-file hashes, location, and manifest locator. `content_sha256` and `retrieval_proof_sha256` both equal `ad30b37a48a44aafe65e1e2860cda51cae342aaae928a9f6d588769e9cd0868c`. `push.log` hashes to `179cf74ca98cf3895f3a2e78dc6ba0e12ca9e7bca134690d3bc5b9294a767c00`; `push.exit` hashes to `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`.

The removal receipt has `action: removed`, `reason: settled clean worktree; branch ref kept`, `branch: claude/atlas-10672-cloze-budget-opus`, `dirty: false`, `error: null`, and `pr: null`. It also holds the path and preservation receipt. It has no merged-PR proof, lifecycle-observation receipt ID, removal timestamp, or independently recorded remote-head value.

The ledger's observation at `2026-10-19T15:25:12Z` is `BLOCKED_WITH_RECEIPT`. All three local flags are false. `_local_readiness` reproduces these exact refusals at [task_lifecycle.py:1422](../../scripts/orchestration/task_lifecycle.py#L1422):

```text
implementation was not observed in a dispatch worktree
the claimed dispatch worktree was absent from git worktree list
the claimed dispatch worktree branch did not match Git authority
```

The stored receipt separately reports missing typed `behavior_proof` for BC-01, BC-02, and BC-03. Repairing local observation would not resolve those blockers or establish BC-04.

The supported command is `recover-local`, not `recover`. Its required inputs at [task_closeout.py:1137](../../scripts/orchestration/task_closeout.py#L1137) are `--state-file`, `--task-record`, `--preserved-manifest`, and `--push-record`. `_recovered_local` requires the typed push at [lifecycle_observation.py:220](../../scripts/orchestration/lifecycle_observation.py#L220), otherwise `RECOVERY_PUSH_UNPROVEN`; it separately requires merged-PR membership proof at line 230, otherwise `RECOVERY_MERGED_PR_UNPROVEN`. Missing input files can refuse earlier as `RECOVERY_INPUT_UNAVAILABLE`. No fabricated input was supplied to reach those later checks.

`recovery_refusal` at [lifecycle_observation.py:269](../../scripts/orchestration/lifecycle_observation.py#L269) rebuilds facts from digest-bound sources on every validation. Changed facts produce `RECOVERY_FACTS_MISMATCH`; mismatched branch or PR ancestry produce `RECOVERY_BRANCH_MISMATCH` or `RECOVERY_PR_HEAD_ANCESTRY_MISMATCH`. The [runbook's recovery contract](../runbooks/worktree-cleanup.md#immediate-cleanup-after-merge) retains both inputs and explicitly rejects a failed push log.

### Publication and worktree custody are different facts

These commands corroborated publication independently of the preserved log:

```bash
gh pr view 11048 --json createdAt,mergedAt,state,headRefOid,headRefName,mergeCommit
git ls-remote origin refs/heads/claude/atlas-10672-cloze-budget-opus
git ls-remote origin refs/pull/11048/head
git merge-base --is-ancestor 28633df608427a6280834532c5f04864e4613362 e921dff2e82244cdf657f7e14d96f142dd499b29
printf 'base_to_head_exit=%s\n' "$?"
git merge-base --is-ancestor e921dff2e82244cdf657f7e14d96f142dd499b29 71e64a041b822ad5ccc848c495e3b9b25ff73c06
printf 'head_to_merge_exit=%s\n' "$?"
git merge-base --is-ancestor e921dff2e82244cdf657f7e14d96f142dd499b29 origin/main
printf 'head_to_main_exit=%s\n' "$?"
```

PR #11048 is `MERGED`. It was created at `2026-10-19T14:52:19Z` and merged at `2026-10-19T15:13:05Z`. Its head is the task's recorded `e921dff2e82244cdf657f7e14d96f142dd499b29`; the forge-reported merge commit is the inspected base. The ancestry results are `base_to_head_exit=0`, `head_to_merge_exit=1`, and `head_to_main_exit=1`. The PR was squash-merged, so its head is not an ancestor of the merge result or current `main`. Pure ancestry cannot prove inclusion here. Inclusion evidence is the forge's merged-PR report binding that head to the merge commit, together with Git's retained `refs/pull/11048/head` value, `e921dff2e82244cdf657f7e14d96f142dd499b29`. The branch query returned no ref, with exit 0, so its current value is absent rather than verified equal. The retained PR ref does not prove the deleted branch's historical value.

The task finished at `2026-10-19T14:29:33.935510+00:00`, before PR creation, and carries the settle-removal receipt. There is no precise removal timestamp. More generally, `pr: null` alone does not prove removal before PR creation: [delegate.py:8858](../../scripts/delegate.py#L8858) constructs that field unconditionally.

An authentic alternative recovery input would need all existing bundle checks, task ID and run-nonce bindings, task head and branch, and canonical path hashing. Git ancestry can bind task base to task head to PR head. For squash merges, inclusion instead needs the independently read forge report binding the merged PR's head to its actual merge commit, checked against the retained PR head ref. It must not require PR-head ancestry to the merge result. An exact branch ref value read from Git after successful push would corroborate the log without relying on a caller's SHA string. Here that historical observation is missing. Accepting the independently read PR ref and same-branch push log instead would require an explicit replacement-evidence rule. Deleted refs must remain absent or unknown, never be recreated as evidence.

Those checks establish publication and inclusion. Worktree custody needs separate evidence. This task does have producer-written corroboration: `worktree_reused: false`, `worktree_layout: dispatch`, a terminal head checkpoint, and a successful guarded removal with the branch read from Git. [delegate.py:12033](../../scripts/delegate.py#L12033) resolves the terminal head before writing its checkpoint; [worktree_claims.py:737](../../scripts/orchestration/worktree_claims.py#L737) guards removal under the worktree lock. These records are stronger than a worker-written path in a log. They do not contain the lifecycle API's registered-worktree observation or an atomic observation joining the removed worktree's head to that checkpoint. An approved B design could evaluate them as replacement custody evidence, with an explicit account of the intervening race. This investigation does not conclude that authentic historical recovery is impossible.

A path string and its SHA-256 alone bind a claim; they do not establish that Git registered the path or that implementation happened there. Hashes detect changes relative to retained records; unsigned files and recomputable manifests do not defeat a writer who can replace the entire evidence set. Any proposed recovery must state which dispatcher and reaper records it trusts, preserve their original bytes, and append a distinct historical receipt rather than manufacture the missing typed inputs.

### The missing producer and capture path

```bash
git grep -n pushed_exact_head
git log origin/main --format='%h %aI %s' -3 -- scripts/orchestration/lifecycle_observation.py
git show 3a750bc7df1:tests/orchestration/test_lifecycle_observation.py
```

There is no production producer of `pushed_exact_head` in the inspected tracked code. The sole writer is the synthetic fixture in [test_lifecycle_observation.py:69](../../tests/orchestration/test_lifecycle_observation.py#L69). Production code consumes the status in recovery and documents its CLI contract. The fixture and consumer arrived in commit `3a750bc7df1b6b8ecece4bf1ccbe79d7d397b022`, on `2026-10-16T03:35:34Z`, through #10758 for #10752. There is consequently no production writer start date to report. Private external wrappers were not exhaustively inventoried.

Consequently, `recover-local` cannot satisfy its push-input contract for production tasks using only the repository's producers. The runbook describes a recovery path those producers cannot currently supply. Infra must either add A's post-push writer or state this limitation in the runbook. D alone does not make recovery reachable, and a new writer cannot supply the missing historical record for Atlas.

The Atlas task ran on October 19, after that change. This is not explained by the task predating the format. Its preserved output is an ordinary successful Git push log and exit file. The OPSEC hook in `scripts/opsec/push_hooks/pre-push` calls `scripts/opsec/git_push.py` before publication; it scans proposed updates and chains validation, and cannot attest the later remote outcome. A protected push and a typed lifecycle push receipt are separate mechanisms.

The more direct defect is missing local capture. Both settle callers reach `_settle_worktree_reap` without `lifecycle_observation.before_reap`: terminal settlement at [delegate.py:12143](../../scripts/delegate.py#L12143), and cleanup after a refused review at [delegate.py:14850](../../scripts/delegate.py#L14850). They reach `_remove_dispatch_worktree` and `worktree_claims.remove_unclaimed_worktree`. Neither that shared removal function nor its Git removal helper invokes lifecycle capture.

The scheduled [worktree-reaper service](../../packaging/systemd/learn-ukrainian-worktree-reaper.service#L13) runs `reap_worktrees --clean-pushed --apply`. This path removes clean, fully pushed dispatch trees with no process or live task and at least 60 minutes of inactivity, subject to its other guards. It requires no PR. [reap_worktrees.py:7498](../../scripts/orchestration/reap_worktrees.py#L7498) calls the same shared removal guard; the module has no lifecycle-observation reference. If capture fails at settle and only settle is changed, this scheduled path can later remove the retained tree without capture. Issue #11058 names the clean-pushed reaper; the Atlas receipt specifically identifies settle removal.

By comparison, [post_task_reap.py:655](../../scripts/fleet/post_task_reap.py#L655) and [merge_closeout.py:450](../../scripts/orchestration/merge_closeout.py#L450) call the existing capture hook while the tree exists. Their coverage misses both settle callers and the clean-pushed reaper. The merged proof producer, `_record_merged_reuse_proof` in `scripts/orchestration/reap_worktrees.py`, is a separate merged-cohort path; settle does not call it.

The `before_reap` docstring at [lifecycle_observation.py:105](../../scripts/orchestration/lifecycle_observation.py#L105) says missing ledgers leave cleanup unchanged, but its code raises `LIFECYCLE_LEDGER_MISSING` when a carrier's ledger is absent. D preserves that refusal and corrects the docstring. No carrier leaves cleanup unchanged; a carrier with a missing ledger retains the tree. These cases need separate tests.

### Thirty-day census

The window is `2026-09-19T16:10:52Z` through `2026-10-19T16:10:52Z`, using `date -u` for its endpoint. Select each task's `finished_at`, falling back to `started_at`; the receipts have no uniform removal timestamp. Count task attempts by task ID and run nonce. Scan the hot directory and recursive archive, including nested archives; hot records take precedence over archived duplicates. Non-task JSON files are excluded. This is a live-store census, not a historical snapshot of PR existence or lifecycle validity.

The following read-only script is the census command:

```bash
"$PROJECT_PYTHON" - <<'PY'
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import json
from scripts.orchestration.task_lifecycle import canonical_state_root
root=canonical_state_root(Path.cwd())
end=datetime.fromisoformat('2026-10-19T16:10:52+00:00')
start=end-timedelta(days=30)
c=Counter(); records={}
files=sorted((root/'batch_state/tasks/archive').rglob('*.json'))
files+=sorted((root/'batch_state/tasks').glob('*.json'))
for f in files:
 try: t=json.loads(f.read_text())
 except (OSError,ValueError): c['unreadable_task_json']+=1; continue
 if not isinstance(t,dict) or not t.get('task_id'): c['non_task_json']+=1; continue
 key=(t['task_id'],t.get('run_nonce'))
 if key in records: c['duplicate_attempt']+=1
 records[key]=t

def typed(v):
 if isinstance(v,dict):
  return v.get('status')=='pushed_exact_head' or any(typed(x) for x in v.values())
 return isinstance(v,list) and any(typed(x) for x in v)

for t in records.values():
 stamp=t.get('finished_at') or t.get('started_at')
 try: dt=datetime.fromisoformat(stamp.replace('Z','+00:00'))
 except (ValueError,TypeError,AttributeError): c['undated']+=1; continue
 if not start<=dt<=end: continue
 c['window_tasks']+=1
 c['task_record_typed' if typed(t) else 'task_record_no_typed']+=1
 r=t.get('worktree_reap') or {}
 if r.get('action')!='removed' or 'pr' not in r or r['pr'] is not None: continue
 c['removed_pr_null']+=1
 if not t.get('task_lifecycle'): continue
 c['cohort']+=1
 c['cohort_read_only' if t.get('mode')=='read-only' else 'cohort_write']+=1
 found=typed(t); unknown=False
 p=t.get('preserved_artifacts') or {}
 if p.get('location'):
  bundle=root/p['location']
  if not bundle.is_relative_to(root/'batch_state/preserved') or not bundle.is_dir():
   c['cohort_bundle_unavailable']+=1;unknown=True
  else:
   for f in bundle.rglob('*.json'):
    if f.is_symlink(): c['cohort_json_symlink']+=1;unknown=True;continue
    try: found=found or typed(json.loads(f.read_text()))
    except (OSError,ValueError): c['cohort_json_unreadable']+=1;unknown=True
 c['cohort_typed' if found else 'cohort_no_typed_found']+=1
 if unknown and not found:c['cohort_absence_unknown']+=1
print('window',start.isoformat(),end.isoformat())
print(json.dumps(dict(sorted(c.items())),sort_keys=True))
PY
```

The round-two replay used the same fixed window. Its raw counter output was:

```json
{"cohort": 100, "cohort_absence_unknown": 1, "cohort_json_unreadable": 1, "cohort_no_typed_found": 100, "cohort_read_only": 1, "cohort_write": 99, "duplicate_attempt": 51, "non_task_json": 4553, "removed_pr_null": 8863, "task_record_no_typed": 12773, "undated": 7, "window_tasks": 12773}
```

Thus 8,863 tasks have the specified removal receipt; 100 also carry lifecycle metadata, comprising 99 write tasks and one read-only task. Zero typed push records were found in that cohort's task records or preserved JSON files. One preserved JSON file is unreadable, so exhaustive absence is unknown for that member. It is `site/src/data/lexicon-manifest.json` in the bundle for `atlas-8327-review-runtime-567`. No candidate bundle was unavailable. No task JSON was unreadable; seven records were undated and excluded. The broader 12,773-task count lacks an embedded typed push status, but that is not a count of 12,773 broken lifecycles or an exhaustive scan for externally held push records. This live-store replay returned three fewer window tasks than the initial investigation; the removal and carrier-cohort counts were unchanged. Carrier presence alone does not prove an existing ledger or missing valid local observation.

## Options table

| Option | Change and owner | Strictness and forgery risk | Test requirement |
| --- | --- | --- | --- |
| A. Emit a typed push record at push or reap time | Infra adds an actual post-push writer, or derives a record from reaper observations. Owners are the push integration and reaper modules. | A post-push writer can preserve real exact-head remote evidence without relaxing recovery. A reap-time writer cannot claim a past successful push step from present remote reachability. Neither supplies missing worktree custody by itself. Caller-written JSON remains forgeable without trusted producer provenance. | Real local remote; failed push; ref moves during push; remote-query failure; crash after acceptance; replay; preservation. Never mark a synthesized reap-time record as a historical push execution. |
| B. Accept corroborated successful logs for recovery | Infra extends `lifecycle_observation.py`, `task_closeout.py`, and the cleanup runbook with a distinct append-only recovery input. | Relaxes both typed push and merged-reaper requirements for this case. Requires the independent publication and custody evidence described above, not merely hashes and a success string. Logs, exit files, path claims, or an entire unsigned bundle can be manufactured. Atlas has dispatcher and removal corroboration, but lacks the atomic local observation and historical exact remote branch value. Accepting replacements needs approval. | Authentic and forged logs; wrong run, task, branch, head, PR, and worktree; deleted or moved refs; symlinks; missing objects; digest changes; checkpoint-to-removal races; replay and later revalidation. Refuse when custody is unproven. |
| C. Preserve the blocked ledger and document disposition | Atlas keeps #11039 open with the missing evidence and Infra dependency; Infra maintains the recovery runbook and owns the historical residual. | Weakens nothing while the ledger stays blocked. Marking it complete or closing it as an exception would create a new policy and must not happen implicitly. A copied status or newly made receipt proves nothing. | Confirm reconciliation still blocks; verify the issue states the owner and dependency without claiming lifecycle completion. |
| D. Capture local facts in the shared removal guard, recommended | Infra extends `worktree_claims.remove_unclaimed_worktree`, under its existing lock, using `lifecycle_observation.py`. This covers both settle callers and the clean-pushed reaper. | Keeps current recovery requirements. Records current Git registration, branch, head, and task binding while observable. Capture failure or a missing carried ledger retains the tree on every covered path. Adds no historical push claim. Compromised ledger writers remain outside the integrity guarantee. | Both settle callers and real clean-pushed removal with a carrier and no PR; exact-head capture before removal or quarantine; failed settle capture still retains on a later scheduled reap; dirty trees and unrelated claims retain; retry and head movement; no-carrier behavior unchanged. |

## Recommendation

Choose D for prevention and use C's existing blocked disposition for the historical Atlas record. Capture the fact that is otherwise destroyed: the registered dispatch worktree and its branch/head. Adding a push producer alone would still leave this task without merged-reaper proof and would not establish worktree custody.

Reuse `before_reap` rather than introducing another evidence format. Put capture inside `worktree_claims.remove_unclaimed_worktree`, under the existing worktree lock, after eligibility and claim checks and before removal or quarantine moves the original registered tree. Bind capture to each applicable task/run and the worktree's actual head. Inspect the current in-memory terminal record and canonical carrier discovery together so an unpublished terminal checkpoint cannot make capture silently miss the task. The refused-review caller passes no terminal record, so discovery must handle that case without inventing a carrier. Reuse a prior observation only when it proves the relevant head; the present `before_reap` shortcut accepts an existing local observation without an explicit current-head comparison. Preserve all common-reaper ownership, preservation, liveness, and dirty-tree guards. A capture or write failure must retain the tree with a typed reason on both settle and subsequent clean-pushed attempts. A capture followed by a failed removal is still a truthful local observation and must be safe to retry.

This is not a one-call insertion with demonstrated correctness. Shared-guard placement, locking, head freshness, pending-record discovery, and clean-pushed quarantine need executable regressions and exact-head cross-family review. Keep that implementation in an Infra follow-up owned by `claude-infra`; this author packet changes only the design note. The follow-up must exercise both settle callers and scheduled clean-pushed removal, rather than merely mocking a hook call. Preserve `LIFECYCLE_LEDGER_MISSING` for a carried but absent ledger and align the hook's docstring with that behavior.

## What must be approved

Sol 6.1's recommendation here proposes D without changing the proof bar. The supplied independent Opus 5.5 review of `d2284a21c5d1fc003645d09e33282259c5b1f1d4` returned `REQUEST_CHANGES` and `DESIGN_APPROVAL: AGREE_WITH_CHANGES`. Its D approval is conditional on correcting the squash-merge evidence and covering the shared removal guard. This revision applies those conditions; exact-head review of the revised document remains pending. Independent exact-head review of the final implementation remains separate. This author packet authorizes no implementation outside its document scope.

Any later choice of B needs explicit agreement by Opus 5.5 and Sol 6.1 on the replacement push evidence, replacement merged-reaper proof, and separate worktree-custody evidence before implementation. Approval must bind the concrete design, including its refusal conditions. Replacing custody evidence with publication alone is a substantive weakening and is not recommended. A new terminal exception or permission to close #11039 without its required evidence also needs designated approval. No option may invent records, rewrite old receipts, change reaper eligibility, or waive Atlas behavior proof within this task.

## Test plan

For this document, run the repository Markdown linter on this file and the four mandatory guards in one foreground process. `git grep -l markdownlint -- .pre-commit-config.yaml .github` returned no matches; `package.json` supplies `lint:md` using `markdownlint-cli2` over `docs/**/*.md`. Use that installed linter with the one changed path. Ruff and module tests do not apply to this Markdown-only change. One protected detached push validates the exact commit; never bypass or start a second push while it is waiting.

The prevention follow-up's candidate suites include `tests/orchestration/test_lifecycle_observation.py`, `tests/test_fleet_post_task_reap.py`, `tests/test_delegate_review_rounds.py`, `tests/orchestration/test_reap_worktrees_clean_pushed.py`, and `tests/orchestration/test_worktree_removal_invariant.py`, selected against its eventual diff. Use real disposable repositories to exercise terminal write-task settle before PR creation, refused-review cleanup, and clean-pushed removal without a PR. Assert that each surviving lifecycle receipt names the exact head and precedes removal or quarantine. A settle capture failure followed by an eligible clean-pushed attempt must still retain the registered tree while capture remains broken. After repair, retry must capture before removal.

Cover an existing stale receipt, concurrent task claims, changed head/branch, write failure, retry after interrupted removal, archived carriers, unpublished terminal records, and quarantine interruption. Separately assert that a carrier with a missing ledger refuses removal with `LIFECYCLE_LEDGER_MISSING`, while a task without a carrier keeps existing behavior. Determine shared-helper importer tests from the final owned paths. Use at most two pytest workers, then Ruff if Python changes. Any B recovery follow-up must also test a squash-merged PR whose head is not an ancestor of the merge commit, using forge merge metadata and the retained PR head ref for inclusion, and reject mismatched PR/head/merge bindings.

An independent reviewer must select additional held-out failures, inspect the exact implementation SHA, and execute the real settle and clean-pushed paths. These are proposed acceptance tests, not tests run by this investigation. A green documentation check or synthetic recovery fixture cannot certify prevention or historical recovery.

## Residuals

The 100-member receipt cohort is an inventory for triage, not 100 proved lifecycle failures. One member's preserved JSON is unreadable; externally held push evidence and each member's ledger health remain unverified. `claude-infra` owns cohort triage and the prevention follow-up, with completion conditioned on reviewed implementation and executable regressions for both settle callers and clean-pushed removal through the shared guard. It also owns the unreachable repository-produced recovery contract: either add a post-push writer or update the runbook to state the limitation. D leaves that producer gap and historical recovery unresolved. The driver must create and link the follow-up before closing #11058.

Atlas retains the authentic #11039 refusal. Its supported current disposition is an open, blocked lifecycle linked to Infra #11058, with publication evidence preserved and separate Atlas-owned BC behavior proof outstanding. `claude-infra` owns the historical recovery decision; Atlas owns behavior evidence and its issue update. Closure requires verified original criteria and supported lifecycle evidence, or a separately approved explicit disposition. This worker did not update or close either issue.

The supplied round-one review is evidence about the prior document head. No exact-head review of this revision, historical recovery, prevention execution, CI, landing, or Atlas behavior certification was performed in this author investigation. The source records and lifecycle ledger were not modified.
