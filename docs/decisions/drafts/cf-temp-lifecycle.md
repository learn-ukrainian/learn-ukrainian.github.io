# Design Note: Formal CF Review Temp Roots & Worktree Reaper Lifecycle

**Status:** Draft / Proposed Design  
**Issue:** #6412  
**Target Branch:** `agy/hramatka-6412-design-agy`  
**Date:** 2026-08-06  
**Authors:** AGY / Antigravity Design Agent  

---

## 1. Context & Problem Diagnosis (Verified)

Formal Code Review (CF) snapshots (`$TMPDIR/lu-review-snap-*`, `$TMPDIR/lu-review-exec-*`, `$TMPDIR/lu-review-write-*`, `$TMPDIR/lu-review-view-*`, `$TMPDIR/lu-review-git-*`) each duplicate repository source state (~700MB per full-monorepo copy). On 2026-08-06, accumulated orphan snapshots filled the machine disk to 100% (~20GB of orphans; machine dropped to 1.3GiB free space).

Inspection of the codebase confirms four design vulnerabilities:

1. **Cleanup coupled strictly to `finally` blocks in single-process execution:**
   - In [`scripts/ai_agent_bridge/_review_worktree.py:2905`](scripts/ai_agent_bridge/_review_worktree.py#L2905) (`provision_review_worktree`), [`line 3021`](scripts/ai_agent_bridge/_review_worktree.py#L3021) (`_provision_local_review_worktree`), and [`line 3055`](scripts/ai_agent_bridge/_review_worktree.py#L3055), temporary directory cleanup (`_cleanup_review_resources` at [`line 2727`](scripts/ai_agent_bridge/_review_worktree.py#L2727)) runs strictly in Python `finally:` blocks.
   - If the process suffers an uncatchable termination (`SIGKILL` / `kill -9`), system OOM kill, hardware power loss, or execution thrash, Python process execution halts instantly. The `finally:` block never executes, stranding multi-hundred-megabyte temp roots indefinitely.

2. **Inadequate orphan sweeper backstop:**
   - The only current cleanup backstop is `sweep_review_temp_orphans()` in [`scripts/review/isolation.py:337`](scripts/review/isolation.py#L337).
   - It reaps roots **only if older than 48 hours** (`REVIEW_TEMP_ORPHAN_MAX_AGE_S = 48 * 60 * 60` in [`scripts/review/isolation.py:56`](scripts/review/isolation.py#L56)).
   - It is invoked **only at the start of a new formal CF review** (calls in [`_review_worktree.py:2780`](scripts/ai_agent_bridge/_review_worktree.py#L2780) and [`line 3042`](scripts/ai_agent_bridge/_review_worktree.py#L3042)).
   - There is no scheduled background sweeper for review temp roots, nor any disk-pressure monitoring.

3. **Sentinel marker lacks owner identity:**
   - Current roots write an anonymous sentinel string `lu-review-root-v1:<random_nonce>` via `_write_review_temp_root_marker` in [`scripts/review/isolation.py:82-104`](scripts/review/isolation.py#L82-L104).
   - Because the marker lacks owner PID, process start time, or machine identity, an external janitor cannot distinguish an actively running 5-minute-old review from a crashed 5-minute-old orphan killed by `SIGKILL`.

4. **Worktree reaper brittle failure modes:**
   - Scheduled worktree hygiene runs via launchd job `com.learn-ukrainian.worktree-cleanup` ([`scripts/orchestration/install_worktree_cleanup_launchd.py:12`](scripts/orchestration/install_worktree_cleanup_launchd.py#L12)), calling [`scripts/orchestration/scheduled_worktree_cleanup.py`](scripts/orchestration/scheduled_worktree_cleanup.py).
   - In [`scheduled_worktree_cleanup.py:362-369`](scripts/orchestration/scheduled_worktree_cleanup.py#L362-L369), if `git fetch --prune origin` fails or times out (120s), the ENTIRE hygiene run aborts immediately (`result["errors"].append("fetch failed; cleanup skipped"); return result`).
   - Detached-HEAD review worktrees are skipped even when their underlying dispatch task record in `batch_state/tasks/{task_id}.json` is terminal (`done`/`failed`/`no_deliverable`).
   - `needs_finalize` task statuses prevent reaping ([`scripts/orchestration/reap_worktrees.py:350`](scripts/orchestration/reap_worktrees.py#L350)) without emitting any operator-visible alerts.

---

## 2. Failure Modes & Safety Guarantees (FIRST-CLASS)

The design prioritizes safety above all: **a live review must NEVER be reaped mid-CF under any circumstances.** Reaping an active review root invalidates isolation evidence, corrupts the reviewer execution workspace, and causes false review failures.

| Failure Scenario | Risk | Structural Prevention Mechanism |
| :--- | :--- | :--- |
| **False-Positive Active Review Reap (Catastrophic)** | Sweeper prematurely deletes a temp root belonging to an active, ongoing CF review. | **Owner-Liveness Triple Fencing (PID + `started_at` + `machine_id`).** The sweeper reads `.lu-review-root.json`. A root is considered active if `kill(pid, 0)` succeeds **AND** process start time (`ps` / `psutil`) matches `owner_pid_started_at` **AND** `machine_id` matches local host. Reaping is strictly forbidden if the process is alive. |
| **PID Recycling Race** | Owner process dies; OS re-assigns the exact same PID to a newly spawned, unrelated process. | **Exact Start-Time Matching.** Standard POSIX `kill(pid, 0)` is insufficient because PIDs recycle. The sweeper compares `owner_pid_started_at` (microseconds/epoch timestamp from `ProcessSnapshot`). If PID exists but start time differs, the recorded owner is proven dead and the root is safely reaped. |
| **TOCTOU Sweep Race** | Sweeper checks liveness, owner process exits 1ms later, or sweeper decides to delete right as a new review process starts. | **FD-Pinned Double Check & Marker Age Fencing.** 1) Newly created roots get a 60-second grace window during which dead-owner checks are suppressed unless the owner process is confirmed non-existent via `ESRCH`. 2) Re-evaluate liveness immediately before `rmtree`. 3) Verification of root descriptor using `O_NOFOLLOW` (mirroring [`scripts/review/isolation.py:69-79`](scripts/review/isolation.py#L69-L79)). |
| **SIGKILL Process Termination** | Review runner receives `SIGKILL` (`kill -9`) or system OOM kill. Process signal handlers cannot run. | **Out-of-Process Liveness Sweeping.** Because `SIGKILL` prevents `finally:` cleanup, the scheduled janitor (`com.learn-ukrainian.worktree-cleanup`) inspects manifests in `$TMPDIR`. Since the owner PID is dead (ESRCH), the janitor reaps the root at the next run regardless of root age. |
| **Unreadable / Corrupt Manifest** | Root created but process crashed before manifest write, or disk corruption occurred. | **48-Hour Fallback Rule.** Manifest-less or unreadable roots fall back to the age rule (`mtime > 48h` in normal mode, `> 1h` in disk-pressure mode). Unmarked roots are never reaped by prefix alone. |
| **Disk 100% Full (Write Lock Failure)** | Machine disk hits 100% free space, preventing creation of atomic lock files or receipts. | **Read-Only Inspection + Non-Blocking Atomic Unlink.** The sweeper can scan, parse JSON manifests, and call `rmtree` without allocating new disk blocks. Receipt writing failure is logged to `sys.stderr` without aborting the deletion loop. |
| **Network / Git Fetch Timeout** | Scheduled hygiene job `git fetch` hangs due to network failure or GitHub rate-limiting. | **Soft-Degradation Execution Path.** `git fetch` failure will log an error to the receipt but **proceed** to local hygiene phases (worktree reaping, local branch pruning, review temp root sweeping). |

---

## 3. R1 — Owner-Liveness Manifest for Temp Roots

### 3.1 Metadata Schema (`.lu-review-root.json`)

To enable deterministic, age-independent orphan detection, every review temp root created by `create_review_temp_root` in [`scripts/review/isolation.py:106`](scripts/review/isolation.py#L106) will contain a JSON manifest file named `.lu-review-root.json` alongside the existing sentinel file `.lu-review-root`.

```json
{
  "schema_version": "lu-review-root-v2",
  "nonce": "a1b2c3d4e5f6...64hex",
  "created_at": "2026-08-06T23:33:25Z",
  "created_at_epoch": 1786059205.123,
  "prefix": "lu-review-snap-",
  "owner_pid": 48291,
  "owner_pid_started_at": 1786059100.456,
  "owner_machine_id": "mac-mini-m2-01.local",
  "context": {
    "engine": "claude",
    "mode": "branch",
    "target_branch": "feature/xyz"
  }
}
```

### 3.2 Fencing & Liveness Semantics

The liveness probe reuses the exact process liveness and start-time fencing semantics established in [`scripts/orchestration/thread_handoff.py:809-940`](scripts/orchestration/thread_handoff.py#L809-L940) (`_process_is_alive`, `_process_is_zombie`, `_evaluate_owner_liveness`).

1. **Local Machine Fencing:** If `owner_machine_id` does not match the current host, the root cannot be probed via local PID and falls back to age-based evaluation.
2. **PID Liveness Check:** Call `os.kill(owner_pid, 0)`.
   - If `ProcessLookupError` (ESRCH): Owner is **DEAD**.
   - If `PermissionError` (EPERM): Process exists but owned by another user. Proceed to start-time check.
   - If success: Verify zombie status using `ps -o stat= -p <pid>`. Confirmed zombies (`Z` state) are treated as **DEAD** (citing [`thread_handoff.py:827-848`](scripts/orchestration/thread_handoff.py#L827-L848)).
3. **Start-Time Matching:** Inspect process start time via `ps -o lstart= -p <pid>` or `psutil.Process(pid).create_time()`.
   - Compare `snapshot.started_at` with `owner_pid_started_at`.
   - If start time matches (within ±1.0s resolution tolerance): Owner is **ALIVE**. Sweeper MUST skip.
   - If start time differs: PID was recycled by the OS for a new process. Recorded owner is **DEAD**.

### 3.3 Foreign & Legacy Manifest-Less Roots

- If `.lu-review-root.json` is missing or unparseable (e.g. legacy roots created prior to v2), the sweeper falls back to the legacy age rule (`REVIEW_TEMP_ORPHAN_MAX_AGE_S = 48h`).
- In disk-pressure mode (R3), the fallback age threshold for unmanifested roots drops to **1 hour**.

---

## 4. R2 — Janitor Consolidation & Race Mitigation

### 4.1 Integration into Scheduled Hygiene

Instead of creating a new background daemon, review-temp orphan sweeping is consolidated into the existing launchd job `com.learn-ukrainian.worktree-cleanup` ([`scripts/orchestration/install_worktree_cleanup_launchd.py:12`](scripts/orchestration/install_worktree_cleanup_launchd.py#L12)), which runs every 4 hours via [`scripts/orchestration/scheduled_worktree_cleanup.py`](scripts/orchestration/scheduled_worktree_cleanup.py).

`scheduled_worktree_cleanup.py` will execute `sweep_review_temp_orphans()` as part of its pipeline, recording results (`roots_reaped`, `bytes_freed`, `errors`) into the structured receipt JSON.

The inline call to `sweep_review_temp_orphans()` at the start of formal CF reviews in [`_review_worktree.py:2780`](scripts/ai_agent_bridge/_review_worktree.py#L2780) is **retained** as a fast pre-flight check.

### 4.2 TOCTOU Race Prevention Architecture

To prevent Time-of-Check to Time-of-Use (TOCTOU) races between checking process liveness and deleting directory trees:

```
[Sweeper Loop]
    │
    ├── 1. Read .lu-review-root.json manifest
    ├── 2. Is root created < 60 seconds ago?
    │            │
    │            ├── YES ──► Is owner PID confirmed non-existent via ESRCH?
    │            │                 │
    │            │                 ├── YES ──► Proceed to Step 4 (Double Check)
    │            │                 └── NO (Alive / EPERM / Unconfirmed) ──► SKIP (Grace Period)
    │            │
    │            └── NO ──► Proceed to Step 3
    │
    ├── 3. Evaluate Owner Liveness (PID + started_at)
    │            │
    │            ├── ALIVE / UNCHECKABLE ────────► SKIP
    │            │
    │            └── DEAD
    │                  │
    ├── 4. Re-Verify Liveness Probe (Double Check immediately before rmtree)
    │            │
    │            ├── Owner became Alive / Unconfirmed? ────────► SKIP
    │            │
    │            └── Confirmed Dead (ESRCH / PID mismatch)
    │                  │
    └── 5. Remove Tree via remove_review_temp_tree() (O_NOFOLLOW FD-pinned)
```

---

## 5. R3 — Disk-Pressure Mode

### 5.1 Configuration & Thresholds

Disk-pressure thresholds are specified via environment configuration or configuration file, **never hardcoded**:
- Environment Variable: `LU_REVIEW_TEMP_MIN_FREE_GB` (Default: `10.0` GB).
- Config Path: `config/hygiene.yaml` (`review_temp_min_free_gb: 10.0`).

### 5.2 Escalation Rules

When `shutil.disk_usage(tmp_dir).free < threshold_bytes`:

1. **Immediate Dead-Owner Sweep:** Reap ALL dead-owner temp roots immediately, regardless of root creation time (bypassing the 60s grace window for all dead-owner classifications, including recycled PIDs and zombie processes, whereas normal mode only bypasses grace for ESRCH-confirmed dead owners).
2. **Aggressive Unmanifested Sweep:** Reduce the manifest-less fallback age cutoff from **48 hours** down to **1 hour**.
3. **Loud Alerting:** Emit a high-priority alert payload to the Monitor API / system log (`MonitorAPI.notify_disk_pressure`).

---

## 6. R4 — Signal Hardening

### 6.1 Handlers & Signal Coverage

`provision_review_worktree` and `provision_local_review_snapshot` in [`scripts/ai_agent_bridge/_review_worktree.py`](scripts/ai_agent_bridge/_review_worktree.py) will register explicit signal handlers for interceptable process termination signals:
- `SIGTERM` (15)
- `SIGINT` (2)
- `SIGHUP` (1)
- Python `atexit` callbacks

### 6.2 Signal Handling Architecture

```python
# Pseudocode illustration for signal hardening in review runner
@contextlib.contextmanager
def _hardened_review_scope(roots: tuple[Path, ...]):
    def _signal_handler(signum, frame):
        _cleanup_review_resources(state=None, roots=roots)
        sys.exit(128 + signum)
    
    previous_handlers = {}
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        previous_handlers[sig] = signal.signal(sig, _signal_handler)
    try:
        yield
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
```

### 6.3 Handling `SIGKILL` (`kill -9`)

`SIGKILL` cannot be caught or handled by process code. The signal hardening layer acknowledges this fundamental OS constraint: `SIGKILL` relies 100% on the R1/R2 scheduled out-of-process janitor to reap the abandoned root once the PID has terminated.

---

## 7. R5 — Worktree Reaper Robustness

### 7.1 Fetch Timeout Degradation

Currently in [`scripts/orchestration/scheduled_worktree_cleanup.py:362-369`](scripts/orchestration/scheduled_worktree_cleanup.py#L362-L369):

```python
# CURRENT BROKEN BEHAVIOR:
fetch = _run_git(repo_root, "fetch", "--prune", "origin")
if fetch.returncode != 0:
    result["errors"].append("fetch failed; cleanup skipped")
    return result
```

**Refactored Robust Behavior:**

If `git fetch` fails or times out:
1. Append warning to `result["warnings"]` (e.g. `"fetch_failed_degraded_to_local_only: timeout after 120s"`).
2. **DO NOT RETURN EARLY.** Proceed to run all local-only hygiene tasks:
   - Worktree pruning (`git worktree prune`)
   - Reaping settled/detached worktrees
   - Sweeping gone-upstream local branches with local ancestry checks
   - Review temp root orphan sweeping

### 7.2 Terminal-Task Detached Workspaces

In [`scripts/orchestration/reap_worktrees.py:475-497`](scripts/orchestration/reap_worktrees.py#L475-L497), detached HEAD worktrees are evaluated for age > 24.0h.

**Refactored Behavior:**
If a detached worktree has an associated task ID (`_dispatch_task_id`), read `batch_state/tasks/{task_id}.json`. If `status` is in `("done", "failed", "no_deliverable")` AND the worktree is clean, classify as reapable **immediately** without waiting for the 24-hour age threshold.

**Active IDs Unspecified (`active_ids=None`):**
When `active_ids` is `None` (e.g. during standalone or offline janitor invocations where no active-process registry is passed), any detached worktree whose underlying task is confirmed terminal (`done`, `failed`, `no_deliverable`) in `batch_state/tasks/{task_id}.json` is treated as reapable (`active_ids is None or task_id not in active_ids`). This is safe and defensible because task state in JSON is the authoritative source of task settlement when no active-process filter is active.

### 7.3 Visible `needs_finalize` Reporting

Worktrees skipped because their task status is `needs_finalize` ([`reap_worktrees.py:350`](scripts/orchestration/reap_worktrees.py#L350)) will be explicitly surfaced in `build_receipt()` under `summary["needs_finalize_worktrees"]` and printed in the janitor log output to alert operators.

---

## 8. R6 — APFS Clonefile Cheap Snapshots (Phase 2 Design & Measurement Plan)

### 8.1 Concept & Potential Benefit

On macOS APFS filesystems, `copyfile()` with `CLONEFILE` flags or `cp -c` creates Copy-on-Write (COW) directory entries.
- Current cost: Materializing a 700MB snapshot copies 700MB of data to disk (~2-5 seconds, 700MB disk usage).
- APFS Clonefile cost: ~0 bytes initial physical storage, <50ms allocation time.

### 8.2 Measurement Protocol

Before committing to APFS clonefile implementation in Phase 2, the following parameters must be benchmarked:
1. **Creation Duration:** Measure time to create snapshot via `cp -c` vs object-store blob extraction.
2. **Disk Usage:** Verify physical allocation via `du -sk` vs `du -sk -A`.
3. **Git Behavior Risks:** Validate how `git status`, index lock, and diff operations behave inside a cloned snapshot directory when files are modified during review.
4. **Cross-Volume Fallback:** Ensure strict fallback to standard copying when `$TMPDIR` is mounted on a non-APFS volume or ramdisk.

---

## 9. Comprehensive Mutation Test Strategy

Every safety guard introduced must have a dedicated test that **FAILS** if the guard is removed or mutated.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MUTATION TEST MATRIX                          │
├──────────────────────────┬──────────────────────┬───────────────────────┤
│ Target Guard             │ Mutation Applied     │ Expected Test Outcome │
├──────────────────────────┼──────────────────────┼───────────────────────┤
│ 1. Live Owner Fencing    │ Force probe=DEAD     │ TEST FAILS (Asserts   │
│                          │                      │ active root retained) │
├──────────────────────────┼──────────────────────┼───────────────────────┤
│ 2. PID Start-Time Match  │ Ignore start time    │ TEST FAILS (Asserts   │
│                          │                      │ recycled PID reaped)  │
├──────────────────────────┼──────────────────────┼───────────────────────┤
│ 3. 60s Grace Window      │ Remove grace check   │ TEST FAILS (Asserts   │
│                          │                      │ fresh root with LIVE  │
│                          │                      │ owner is protected)   │
├──────────────────────────┼──────────────────────┼───────────────────────┤
│ 4. Disk Pressure Escal.  │ Hardcode 48h limit   │ TEST FAILS (Asserts   │
│                          │                      │ aggressive sweep)     │
├──────────────────────────┼──────────────────────┼───────────────────────┤
│ 5. Signal Handler Cleanup│ Remove SIGTERM trap  │ TEST FAILS (Asserts   │
│                          │                      │ signal removes root)  │
├──────────────────────────┼──────────────────────┼───────────────────────┤
│ 6. Fetch Timeout Degrad. │ Retain early return  │ TEST FAILS (Asserts   │
│                          │                      │ local hygiene runs)   │
├──────────────────────────┼──────────────────────┼───────────────────────┤
│ 7. Terminal Task Reaper  │ Require 24h wait     │ TEST FAILS (Asserts   │
│                          │                      │ instant task reap)    │
├──────────────────────────┼──────────────────────┼───────────────────────┤
│ 8. needs_finalize Log    │ Omit summary key     │ TEST FAILS (Asserts   │
│                          │                      │ receipt summary item) │
└──────────────────────────┴──────────────────────┴───────────────────────┘
```

### Specific Test Specifications

1. **`test_sweep_reaps_dead_owner_root_immediately`**
   - Setup: Create temp root with `.lu-review-root.json` containing a non-existent/dead PID (e.g. 999999 returning `ESRCH`). Age = 5 seconds.
   - Assert: `sweep_review_temp_orphans()` reaps root immediately in normal mode via the ESRCH-confirmed-dead grace bypass branch.
   - Mutation check: If code is modified to require age > 48h for all roots or unconditionally skip roots < 60s without checking ESRCH, test FAILS.

2. **`test_sweep_preserves_live_owner_root`**
   - Setup: Create temp root with `.lu-review-root.json` containing `os.getpid()` and current process `started_at`. Age = 100 hours.
   - Assert: Root is preserved.
   - Mutation check: If liveness check is bypassed, test FAILS.

3. **`test_sweep_reaps_recycled_pid_root`**
   - Setup: Create temp root with `os.getpid()` but `owner_pid_started_at = 1.0` (mismatched start time).
   - Assert: Sweeper detects PID recycling and reaps root.
   - Mutation check: If start-time matching is removed, test FAILS.

4. **`test_disk_pressure_escalates_sweeper`**
   - Setup: Mock free disk space < 10GB. Create manifest-less root aged 2 hours.
   - Assert: Root is reaped under disk pressure.
   - Mutation check: If disk pressure check is removed, test FAILS.

5. **`test_fetch_failure_degrades_gracefully`**
   - Setup: Mock `_run_git("fetch")` returning exit code 128 (timeout).
   - Assert: `scheduled_worktree_cleanup` records fetch error in receipt but continues worktree prune and review temp sweep.
   - Mutation check: If early return on fetch error is restored, test FAILS.

---

## 10. Summary & Implementation Order (Phase 1 → Phase 2)

- **Phase 1 (Immediate Implementation after Design Approval):**
  1. Implement manifest writing (`.lu-review-root.json`) in `scripts/review/isolation.py`.
  2. Upgrade `sweep_review_temp_orphans()` with PID + start-time liveness checking.
  3. Integrate sweeper into `scripts/orchestration/scheduled_worktree_cleanup.py`.
  4. Implement disk-pressure monitoring and signal hardening.
  5. Refactor `scheduled_worktree_cleanup.py` fetch degradation and terminal task reaping.
  6. Add full mutation test suite in `tests/review/test_temp_lifecycle.py`.

- **Phase 2 (Future Optimization):**
  1. Measure APFS clonefile snapshot performance and git compatibility.
  2. Implement `cp -c` snapshot path if measurements confirm zero-risk speedups.
