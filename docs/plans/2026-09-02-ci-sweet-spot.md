# Plan of record: CI sweet-spot (public + private)

**Status:** SETTLED for implementation sequencing (Fable + Sol APPROVE-WITH-EDITS, 2026-09-02)
**Date:** 2026-09-02
**Boards:** public [#7141](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7141) · private [#562](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/issues/562)
**Does not reopen:** two-tier merge queue + sole required `CI Gate` (CTO #7141)

**Advisors:** Claude Fable 5 (`ci-plan-fable`) · GPT-5.6 Sol (`ci-plan-sol`). Both
APPROVE-WITH-EDITS. P0 is land existing fixes, swap the auto-arm token, and prove
the attestor reload — not a CI redesign.

---

## 1. Sweet spot

PR tier stays a ~2-minute fastlane with ruff, secret-scan, changed-test fastlane,
trusted CF, and one Gate. The merge queue keeps the full four pytest shards plus
coverage at ~12 minutes. Recovered time comes from killing **false reds** and
**phantom queues**, not from deleting checks.

## 2. Before snapshot (frozen)

Command (repeat after landing for AFTER):

```bash
.venv/bin/python scripts/ci/ci_timings.py --event pull_request --since 2026-08-25 --limit 40
.venv/bin/python scripts/ci/ci_timings.py --event merge_group --since 2026-08-25 --limit 20
```

Generated `2026-09-02T10:01Z` / `10:02Z`, public workflow `CI`, window since
2026-08-25.

### pull_request (40 completed runs)

| job | n | avg | med | p95 | max |
| --- | --- | --- | --- | --- | --- |
| Pytest fastlane | 40 | 2.1 | 2.3 | 2.6 | 2.8 |
| Secret scan | 40 | 1.5 | 1.6 | 1.7 | 1.8 |
| Ruff | 40 | 0.6 | 0.6 | 0.7 | 0.7 |
| CF attest | 40 | 0.1 | 0.1 | 0.2 | 0.2 |
| CI Gate | 38 | 0.1 | 0.1 | 0.1 | 0.2 |
| **Run wall (success)** | 17 | **0.8** | **0.4** | **5.4** | **5.4** |
| **Run wall (all)** | 40 | **1.7** | **1.8** | **3.3** | **5.4** |

Fastlane is the PR critical path. Do **not** treat a CF-notice change as a
duration win (Sol).

### merge_group (20 completed runs)

| job | n | avg | med | p95 | max |
| --- | --- | --- | --- | --- | --- |
| Python (pytest) [1/4] | 20 | 8.7 | 8.6 | 10.3 | 12.0 |
| Python (pytest) [2/4] | 20 | 7.7 | 7.6 | 8.8 | 8.9 |
| Python (pytest) [3/4] | 20 | 7.8 | 7.8 | 8.7 | 8.8 |
| Python (pytest) [4/4] | 20 | 8.0 | 8.0 | 9.0 | 9.8 |
| Frontend (build + vitest) | 20 | 1.9 | 0.7 | 6.0 | 9.3 |
| Contracts | 20 | 1.7 | 1.7 | 2.0 | 2.3 |
| Secret scan | 20 | 1.6 | 1.6 | 1.8 | 1.9 |
| Coverage floor | 18 | 1.0 | 1.0 | 1.2 | 1.2 |
| **Run wall (success)** | 16 | **12.0** | **11.4** | **15.3** | **15.3** |
| **Run wall (all)** | 20 | **11.6** | **11.3** | **15.2** | **15.3** |

Queue (12 PRs): median **11.4 min**, avg **59.4**, p95 **469.8** because #7577
kicked 3× (470 min). That is [#7586](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7586).

Private process gates are not in this table: product jobs on #629/#631 were
already green; `validate`/`attest` painted them red.

## 3. Inventory

### Public — keep and couple

| Issue | Role |
| --- | --- |
| [#7141](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7141) | CTO board: two-tier MQ, no redesign |
| [#7586](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7586) P0 | auto-arm `GITHUB_TOKEN` enqueue → merge-group CI never starts → 60–470 min eject |
| [#7539](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7539) | intended auto-arm behavior; close **only after** #7586 is live |
| [#7487](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7487) P0 | CF identity (author can self-APPROVE in comment prose) — security slice, after #7586 |
| [#7490](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7490) P1 | MQ latency; **measure only** this drive |
| [#7538](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7538) | slow nightly, not a Gate job — keep, off this drive |

[#7595](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/7595) already landed (`522f3f4a6d`): CF-only Gate notice. Clarity, not speed.

### Public — de-scope, do not close

- [#6977](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6977) cloud-agent pytest as merge gate (the issue already says no)
- [#7173](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7173) already closed (push-to-main dedup)

### Private — same class (green tests, red process)

| Issue / PR | Role |
| --- | --- |
| [#562](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/issues/562) | attestor request failed on otherwise-green PRs. #631 does **not** close all of #562 (also provider failures) |
| [#631](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/pull/631) | paid attest from lifecycle `review` + non-draft; print HTTP status+code |
| [#629](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/pull/629) | stamp missing lifecycle marker; attest stays red until #631 is **deployed** |
| [#624](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/pull/624) | event-driven sweep; blocked on #629 |
| [#497](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/issues/497) | self-hosted vs ubuntu-latest recon — not this drive |
| [#260](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/issues/260) | author-family crypto identity — P2, not this drive |

## 4. Delivery (one PR per outcome)

| # | Outcome | Proof |
| --- | --- | --- |
| 1 | Independent exact-head CF on **#631**, merge, **reload attestor**, canary | a previously-403 `review`+non-draft shape gets a signed receipt; then re-label **#629** |
| 2 | Merge **#629**, then **#624** | missing-marker PRs no longer fail `validate`; sweep does not fail-close the fleet |
| 3 | Fix **#7586** (token that can trigger merge_group) | AFTER timings: kick rate down; no 60-min eject with zero merge_group run |
| 4 | AFTER snapshot | same `ci_timings.py` commands + false-red / attest success counts |

**#7586 before the #7487 identity slice.** Tests-green is not enough to merge #631 (Sol). Merging #631 is not “#562 fixed” until the host process serves the new code (Fable).

## 5. Hard NOs (this drive)

- No merge_group class-skipping (#7141 panel 4–0)
- No dropping secret-scan / ruff / fastlane / CF from the PR tier
- No four pytest shards on `pull_request`
- No new required check besides `CI Gate`
- No attestor → ubuntu-latest migration (#497)
- No cloud-agent merge gate (#6977)
- No counting #7595 as a duration improvement
- Skipped ≠ pending; unknown class → run everything

Overengineering here: new CI machinery (full #7487 evaluator stack, shard rewrites, extra orchestration, dashboards) before the token and lifecycle defects are gone.

## 6. AFTER proof

When items 1–3 have landed, re-run the commands in §2 on a fresh window that includes the landings. Report:

- PR wall p95 (must stay in the ~3–5 min band)
- merge_group wall median/p95 (must stay ~12 / ~15 min unless a later approved shard experiment)
- merge_group kicks and time-in-queue p95 (must drop vs 4 kicks / 469 min in this snapshot)
- private: `validate` missing-marker rate; attest success on `state: review` non-draft PRs
