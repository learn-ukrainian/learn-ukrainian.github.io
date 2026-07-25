# CI Gate reboot day — a GitHub transient misdiagnosed as a file defect, and a hang the timeout could not see

**Date:** 2026-07-25 · **Epic:** #4707 · **Issues:** #5762 #5768 #5771 #5772 #5773 #5776
**PRs:** #5766 (reboot) · #5770 (yaml) · #5758 (lease) · #5760 (comms) · #5774 (push guard) · #5775 (fold)

Sibling of [`ci-hang-unbounded-jobs.md`](ci-hang-unbounded-jobs.md) (#5740). That autopsy covered
unbounded jobs; this one covers the day the gate was rebuilt, and the four separate ways the system
lied to the people trying to fix it.

---

## 1. What broke, in one line each

| # | Defect | Cost |
| --- | --- | --- |
| 1 | A GitHub-side transient was diagnosed as "GitHub rejects our workflow file" | ~1 session + a 15-commit bisect chasing a defect that never existed |
| 2 | `pytest` hangs at 95% of the suite; **no job had `timeout-minutes`**, so the gate never reported | 2 days of "CI is just slow" |
| 3 | A cross-family review verdict of **CHANGES REQUIRED** was recorded in a handoff as **"ADVISOR PASS"** | nearly merged a lease bug that deletes a live session's lease |
| 4 | `ask-* --background` acks the reviewer's reply **on the requester's behalf** | 4/4 replies invisible; almost certainly the mechanism behind #3 |

---

## 2. The transient (#5766)

**Symptom.** Five workflow runs on one SHA: `conclusion: failure`, `jobs: []`, `check_suite`
`latest_check_runs_count: 0`, a 22-byte empty logs zip, no annotations, and `gh run view` saying
*"This run likely failed because of a workflow file issue."*

**The inherited conclusion:** the file is rejected — reproduced on `pull_request`, `workflow_dispatch`
and `gh run rerun`, so "the FILE is rejected, not the event". A 15-commit bisect branch was built to
find the offending construct.

**Why that was wrong, from evidence already in hand.** Three of the five failing workflows —
`content-ci.yml`, `security-audit.yml`, `zizmor.yml` — were **byte-identical to `origin/main`**:

```
git diff --name-status origin/main origin/claude/ci-reboot -- .github/
M	.github/workflows/ci.yml
A	.github/workflows/hygiene.yml
```

and `Content CI` **passed** on two other branches inside the same 25-minute window. A file cannot be
valid on one branch and rejected on another. `actionlint` and CodeQL also passed on the failing SHA.

**Proof.** An **empty commit** — byte-identical tree — made all five start normally, three hours later.

### Durable rule

> `conclusion: failure` + `jobs: []` + an empty logs zip + *"likely failed because of a workflow file
> issue"* **can be a GitHub-side transient**. Push an empty commit and re-observe **before** diagnosing
> the file. The tell that it is not the file: sibling workflows the branch never modified fail
> identically, while those same files pass on another branch.

Third member of a family that all present as "the branch is broken":

1. this transient;
2. rerunning a run whose pinned SHA was orphaned by a rebase → `run_attempt: 2, jobs: []`;
3. a stale committed fingerprint on `main` that every branch inherits (#5765, #5746).

None is a branch defect. **Diagnostic order: suspect `main`, then suspect the platform, then suspect
the branch.**

---

## 3. The hang (#5776) — still open

```
15:54:23  tests/wiki/test_ukrainian_wiki_corpus.py::test_main_cli_encode_flag_wires_ingest_to_manifest
(23 minutes of complete silence)
16:17:14  ##[error]The operation was canceled.        <- the newly added 45-minute cap
          Terminate orphan process: pid (2544) (python), (2545), (2548)
```

Reproduced on two independent runs; the suite reaches **95%** first.

**Measured boundaries:**

| Command | Result |
| --- | --- |
| that node alone | **1 passed in 0.57s** |
| `pytest tests/wiki -n 2 --timeout=90` | 105 passed, 15.57s, **no hang** |
| `pytest tests/wiki/test_t1_t2_pipeline.py tests/wiki/test_ukrainian_wiki_corpus.py` | 15 passed, 10.8s, **no hang** |

So it is an **interaction with full-suite state**, not a bad test.

### The part that matters: `--timeout=120` was set and never fired — under BOTH methods

This is the crux, and it inverted the investigation. Three independent advisors converged:

- The controller's "starts" line proves **dispatch**, not that the worker armed its timer. A stall
  before or after that boundary is **outside** the per-test timeout.
- pytest-timeout's watchdog dumps to stderr, which under xdist is a **pipe to the controller**. If that
  pipe is full because the controller is not reading, the watchdog **blocks on the write** and never
  reaches `os._exit`. *The safety net hangs on the same deadlock it exists to report.*
- The timeout lives in **workers**. A **controller-side** hang is structurally invisible to it.
- "The timeout never fired" may itself be wrong: it may have fired, killed the worker via `os._exit`,
  and the report been lost with the dying worker's unforwarded stream.

**Therefore the leading theory is the xdist control plane, not any test.**

### Two of my own claims that the panel falsified

1. *"`MLXEncoderBridge.__init__` may leave a partially-started child."* **Wrong.**
   `check_mlx_availability()` raises **before** any `Popen`; `_process` is set to `None`. The real
   footgun is `_read_response` → `process.stdout.readline()` **with no timeout** — a production defect
   independent of this hang.
2. *"The test monkeypatches the encoder, so the global lock is irrelevant."* **Wrong.** `encode_texts`
   holds `_ENCODER_LOCK` around `encoder.encode(...)`, so patching `_get_encoder` does not avoid it.
3. Also wrong: inferring the *same-worker predecessor* from the controller's log order. Under xdist the
   previous line was scheduled, not necessarily run next on that worker.

### Containment shipped

- `timeout-minutes` on all six jobs (there were **none** — GitHub's 6-hour default applied, so the
  required gate could never report at all).
- `--timeout-method` `signal` → `thread`.
- `--durations=25` (free; it is also the runtime profile the fast-PR/nightly split has been blocked on).
- The single node `--deselect`ed, **by name, with an open issue** — not a path filter, so it cannot grow
  and does not reintroduce changed-files selection.

---

## 4. The review gate inverted a verdict (#5758) and the mechanism behind it (#5773)

A session handoff recorded #5758 as *"ADVISOR PASS (round 3 — all 7 findings cleared). Merge on
green."* When CI went green the recorded next step was to merge.

Probed instead:

- `gh pr view 5758 --json reviews` → **empty**. `--json comments` → **empty**.
- The only advisor artifact on disk opened: **"Advisor verdict: CHANGES REQUIRED"**, 7 blocking findings.

Re-review at head found finding 2 still live: `_same_owner_identity_confirmed` returned `True` for
**any** lease whose identity was uncheckable, so a v2 lease with no liveness fields kept its
generation — and a dying predecessor's `SessionEnd` could then delete the **successor's live lease**.
Exactly the double-driving the generation fence exists to prevent, leaking where the lease is least
verifiable.

**Root cause of the inversion — #5773.** `ask-* --background` delivers the reviewer's reply **and acks
it on the requester's behalf**, so it never appears in the inbox. Reproduced 4/4. Tokens spent, answer
invisible. A driver who cannot see the verdict writes down what they remember.

Recovery, until fixed: the reply id appears **only** in
`.mcp/servers/message-broker/logs/ask-<id>.log`; then `ai_agent_bridge read <reply-id>`.

### Process fix adopted immediately

**Publish every verdict onto the PR.** A verdict that lives only in a gitignored local file is not an
auditable gate. All six verdicts this session are now PR comments.

---

## 5. Our own guards produced four false positives in one day

| Guard | False positive |
| --- | --- |
| `guard-push-pytest` | Judged **every worktree push as a push from `main`**, against main's diff — blocked an *empty* commit claiming "includes Python/test-trigger changes" (#5771, fixed #5774) |
| `guard-push-pytest` | Matched the **words** "git push" inside a quoted markdown argument, because backticks parsed as command substitution — **still open** |
| `guard-primary-checkout-write` | Read the `>` of a markdown blockquote inside a heredoc as a shell redirect, blocking a `gh pr comment` — **still open**. Workaround: `--body-file` |
| `guard-pr-merge` | Cannot read cwd from a compound command (working as designed; use a literal `cd` or `-R owner/repo`) |

**Why this is not cosmetic.** The only escape from each is `SKIP_*=1`. A guard that fires on correct
behaviour trains every agent and the operator to disable it reflexively — and then it is not guarding
anything. **The false positive is the mechanism by which a guard loses its teeth.**

### And the fix for the first one shipped three bypasses of its own

Cross-family review caught all three, each in the dangerous direction — each would have let an
**untested push to `main`** through:

1. Only the **first** `cd` was honoured → `cd worktree && cd main && git push` judged in the worktree.
2. The git-env strip missed `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`,
   `GIT_COMMON_DIR`; an invalid value makes the probe fail, and a failed probe read as "nothing to guard".
3. `pushd`/`popd` move the shell too and were not modelled.

**The pattern, stated so it is not repeated: I kept testing the false positive that annoyed me, rather
than the direction the guard exists to block.** A guard's tests must attack it from the side of the
thing it is supposed to stop.

---

## 6. One lane's unowned regression silently blocked the whole repo (#5772)

`Frontend E2E` had been red on `main` for days: the practice CTAs rendered with their bottom edge at
**932px on a 768px viewport**. `guard-pr-merge` refuses any merge with a red check ("red is red" —
correct policy). So a single unowned layout regression blocked **every** merge, including the CI reboot.

It was tracked nowhere. It was "known" only inside a gitignored session handoff.

**Rule:** a known-failing check that has no issue, no owner and no expiry is indistinguishable from an
unknown one, and it devalues every other red check. If it is known, it has an issue number.

Fixed by measuring the real page and pairing the deck preview with the session panel at ≥1024px →
CTAs at 645px, 123px of headroom, DOM order untouched.

---

## Root cause

Four independent defects, but one shared shape: **every one of them made a failure look like something
else**, and each cost far more in misdirection than in repair.

| Defect | Presented as | Actually |
| --- | --- | --- |
| GitHub transient | "our workflow file is invalid" | a platform blip; the tree was fine |
| pytest hang + no `timeout-minutes` | "CI is just slow" | wedged, and structurally unable to report |
| verdict recorded from memory | "reviewed and approved" | CHANGES REQUIRED, 7 blocking findings |
| `--background` ask swallowing its reply | "the reviewer hasn't answered yet" | it answered; the answer was auto-acked |

The unifying cause is **absent or misleading failure signals**, not absent engineering:

1. **No bounded failure.** No job carried `timeout-minutes`, so an unbounded hang produced *no verdict
   at all* rather than a red one. A gate that can hang forever cannot report, and a system that cannot
   report trains people to guess.
2. **A safety net that shares the failure it reports.** pytest-timeout's watchdog dumps to a pipe the
   xdist controller must be reading — so the instrument deadlocks on the same condition it exists to
   surface, and its silence is indistinguishable from health.
3. **Unauditable review state.** Verdicts lived in gitignored local files, so the only durable record
   was a human sentence in a handoff — which inverted. Combined with (4), the driver could not see the
   verdict even when it existed.
4. **Guards that fire on correct behaviour.** Four false positives in one day, each escapable only via
   `SKIP_*=1`. A guard that cries wolf is disabled by reflex, and then it is not a guard.

The through-line: **the system's honesty about its own failures was the defect.** Every fix below adds
a signal or removes a lie; none of them makes the underlying machinery faster or cleverer.

## Prevention

| Prevention | Status |
| --- | --- |
| `timeout-minutes` on every CI job | **done** (#5766) |
| A workflow-level hang must name itself (thread-method timeout, faulthandler) | partial — faulthandler with `exit=True` per worker still to add |
| Publish every review verdict onto the PR | **adopted**; needs a lint to enforce |
| `ask-* --background` must not ack the requester's reply | **#5773 open** |
| Guard tests must attack from the blocked direction, not the annoying direction | **done for #5774**; audit the other guards |
| Every known-failing check carries an issue + owner + expiry | **rule adopted**; needs enforcement |
| Timeout on `MLXEncoderBridge._read_response` readline; bounded `_ENCODER_LOCK` acquire | **open — do regardless of the hang repro** |
| `SOURCES_MCP_NO_MLX=1` on CI so a missing monkeypatch cannot open a real bridge | **open** |

---

## Appendix A — advisor panel, verbatim

Three independent seats were asked whether the hang is properly fixable or whether quarantine is the
honest end state, and were explicitly invited to say the effort was not worth it. Reproduced in full
because the reasoning is more valuable than the conclusion.

**Consensus:** quarantine is legitimate operational triage for the *gate*; it is **not** a legitimate
end state for the encoder/MLX I/O shapes. All three rejected re-hiding the ~282 newly-enabled tests.

**Disagreement, unresolved:** Sol would keep all 282 required and quarantine only empirically failing
nodes; Gemini would re-quarantine them behind a `@pytest.mark.unvetted` + nightly drain; Grok proposes
a middle path — required gate minus a tiny issue-tracked deselect list, plus a **non-blocking soak
lane** promoted after N green runs. **Adopted: Grok's Option C.**

### Seat 1 — GPT-5.6-Sol (`gpt-5.6-sol`)

My judgment: this is diagnosable, but give it at most two instrumented full-suite CI runs. Keep the single-node quarantine meanwhile. If those runs show an xdist/controller-only failure without a practical code fix, stop chasing causality and run this 0.57-second test in a separate serial `-n 0` job. Isolation is an honest endpoint; permanent deselection is not.

Why both timeout methods can stay silent:

- The controller’s “starts” line proves dispatch, not that the worker entered `pytest_runtest_protocol` and armed its timer. An execnet/controller stall before or after that boundary is outside the per-test timeout.
- A C extension holding the GIL prevents both Python signal handling and the timer thread from running. An ordinary `RLock.acquire()` or pipe read releases the GIL, so those do not explain the thread method failing.
- Both methods suppress themselves when pytest-timeout thinks a debugger is active. Run once with `--timeout-disable-debugger-detection`.
- Crucially, pytest-timeout 2.4’s thread callback does capture suspension, terminal output, and several flushes before `os._exit(1)`. A capture/output-pipe deadlock can therefore hang the watchdog itself before it reaches `_exit`.

The MLX theory is weak as stated. In the current code, `MLXEncoderBridge.__init__` calls `check_mlx_availability()` before creating or starting a subprocess; the subprocess starts lazily during encoding. A 16GB rejection cannot leave a partially started MLX child. `_ENCODER_LOCK` is process-local, so it cannot be held “across workers”; exceptions inside `with _ENCODER_LOCK` release it normally. It remains plausible only if an earlier test on the same worker leaked a live thread holding it. The preceding failed test shown by the controller is not necessarily the preceding test on that worker.

Fastest localization:

1. Cheap smoke test: repeatedly run the failing T1/T2 node followed by the target under `-n 0`, then `-n 1`. This tests the proposed neighbour directly.
2. Do one instrumented full run with fixed `-n 2`, `--timeout-disable-debugger-detection`, and an outer shell timeout shorter than the job cap.
3. Record per-worker `{timestamp, pid, worker_id, nodeid, protocol_start/protocol_finish}` to worker-specific files, flushing each record. This identifies the actual same-worker predecessor chain.
4. Arm `faulthandler.dump_traceback_later()` around each test, writing to `RUNNER_TEMP/faulthandler-{pid}.log`, and upload those files with an always-run step.
5. Replay the exact node sequence from the stuck worker under `-n 0`; if it reproduces, delta-debug that ordered prefix. If not, try `-n 1`, then `-n 2`. `-n 1` distinguishes xdist protocol involvement from concurrency.
6. Use `--dist loadfile` only as a diagnostic axis after that. Blind collection-order bisection is inefficient because xdist scheduling depends on timing. `pytest-randomly` is not installed in this checkout, so `-p no:randomly` adds nothing.
7. Use `py-spy` only if the file-backed faulthandler dump fails; ptrace permissions make it a less reliable first instrument.

A one-shot `dump_traceback_later(120, exit=False)` at session startup is wrong: it fires two minutes into a 40-minute suite. Arm/cancel it per test, or use `repeat=True`. It runs from a CPython watchdog thread and can expose a GIL deadlock where pytest-timeout cannot. A conftest hook runs inside each xdist worker, but write directly to unique files—sending dumps through xdist/capture could reproduce the suspected blocked channel.

I recommend against re-quarantining all 282 tests. Keep them visible and required; quarantine only empirically failing/hanging nodes with an owner, issue, and expiry. A blanket cohort ignore recreates the precise blind spot the reboot removed. If failures become numerous, add a temporary separately reported cohort job, but do not silently stop running them.

Repository inspection was read-only; no files changed. Final status: `main...origin/main [behind 2]`, otherwise clean.


### Seat 2 — Gemini 3.1 Pro (`gemini-3.1-pro-high`)

Here is the strategic assessment and actionable plan for the pytest-xdist hang.

---

### 1. Is this properly diagnosable, or is quarantine the honest end state?

**Quarantine immediately to unblock main, but diagnose the root cause in parallel.**

Quarantining the un-vetted test block (or the specific failing/hanging cluster) is **not "papering over"** — it is standard engineering triage to restore a broken CI gate. Keeping main red while chasing a obscure concurrency bug burns team velocity and operator patience.

However, **do not abandon the diagnosis**. A hang that bypasses `pytest-timeout` under *both* `signal` and `thread` methods indicates a structural failure in your process/IPC setup. If left unrooted, it *will* return in another test module later.

---

### 2. Why would `pytest-timeout` fail to fire under BOTH methods?

`pytest-timeout` operates inside the xdist worker process during test item execution (`setup`, `call`, `teardown`). There are three distinct failure modes where it becomes completely blind:

1. **The Hang Occurs Outside `pytest-timeout` Scope (Teardown / Cleanup / Atexit / Process Exit):**
   `pytest-timeout` arms a timer at test start and **disarms it when test `teardown` finishes**. If `test_t1_t2_pipeline` failed and triggered an unhandled exception, resource cleanup, `gc.collect()`, `atexit` handler, or lock release failure *after* test teardown completed (or while transitioning worker state to pick up `test_ukrainian_wiki_corpus`), `pytest-timeout` has already disarmed itself. The worker process hangs, but pytest-timeout thinks the test finished.
2. **Watchdog Stderr Write Deadlock (`thread` method failure):**
   `pytest-timeout`’s timer thread calls `faulthandler.dump_traceback()` and `os._exit(1)`. `faulthandler` writes to FD 2 (stderr). Under `pytest-xdist`, worker FD 1/2 are redirected to pipes connected to the controller or `execnet` IPC. If the pipe OS buffer (64KB on Linux) is full because the `execnet` IPC receiver is blocked or deadlocked on another channel, **the watchdog thread blocks on `write(2, ...)` and never reaches `os._exit(1)`**.
3. **C-Extension / GIL / System Call Deadlock (`signal` method failure):**
   `SIGALRM` (signal method) delivers a signal to the process, but Python signal handlers only execute when Python bytecode instructions run. If a thread is stuck inside C/C++ native code (e.g., PyTorch/MLX/C bindings, native mutexes, or `waitpid` syscall without GIL release), Python signal handlers will **never execute**.

---

### 3. The Fastest Deterministic Reproduction Plan

Rather than burning 40-minute CI runs, use this 4-step local isolation sequence:

#### Step A: Reproduce exact test order without xdist IPC overhead
Run the two target test files sequentially in a single process (`-n 0`) with stdout unbuffered (`-s`) and explicit timeout:
```bash
.venv/bin/python -m pytest tests/wiki/test_t1_t2_pipeline.py tests/wiki/test_ukrainian_wiki_corpus.py -n 0 -s --timeout=15
```
*If this hangs, you have a 2-second local repro.*

#### Step B: Binary search collection order
If Step A doesn't hang, the leak originates earlier in the suite. Export the exact collection sequence from a full run:
```bash
.venv/bin/python -m pytest --collect-only -q > collection_order.txt
```
Run `pytest` feeding chunks of `collection_order.txt` into `-n 2` to narrow down the contaminating predecessor test.

#### Step C: Inspect the stuck PID on CI or local
Add a debug step in CI (or run locally) using `py-spy` or `faulthandler`:
```yaml
- name: Dump stuck stack traces
  if: cancelled() || failure()
  run: |
    for pid in $(pgrep -f pytest); do
      echo "=== STACK TRACE FOR PID $pid ==="
      py-spy dump --pid $pid || true
    done
```
`py-spy` reads process memory out-of-band via `process_vm_readv` and **bypasses GIL, locks, and full stdout/stderr pipes entirely**.

---

### 4. Is `faulthandler.dump_traceback_later()` in conftest the right instrument?

**Yes — but only with `exit=True`.**

If you use `faulthandler.dump_traceback_later(120, exit=False)`, it will dump stack traces to stderr, but if the process is deadlocked on IPC writes, it won't terminate the process.

**The correct conftest pattern:**
In `tests/conftest.py` (or root `conftest.py`):
```python
import faulthandler
import sys

def pytest_configure(config):
    # Dumps C-level stack trace directly to OS stderr (FD 2) and force-kills the process with _exit(1)
    # after 180 seconds of total worker inactivity (covers setup, teardown, atexit, GC).
    faulthandler.dump_traceback_later(180, repeat=False, file=sys.__stderr__, exit=True)
```
- `file=sys.__stderr__` writes directly to the underlying OS file descriptor 2, bypassing Python-level io wrappers.
- `exit=True` executes `os._exit(1)` at the C level, terminating the xdist worker regardless of held Python locks or GIL status.

---

### 5. Structural Recommendation: The 282 Never-Run Tests

**Re-quarantine the 282 un-vetted tests under a managed pytest mark, NOT a CI script `--ignore` list.**

Deleting the hardcoded `--ignore=` list in the same PR that rebooted CI was a scope-coupling mistake. Merging 281 un-vetted tests into main simultaneously creates too many surface variables.

**Action Plan:**
1. **Apply a pytest mark:** Annotate un-vetted test files or directories with `@pytest.mark.unvetted` (or configure via `pytest.ini` `testpaths` / `norecursedirs`).
2. **Exclude from Main Gate:** Set main CI workflow to run:
   ```bash
   pytest tests -m "not unvetted" -n auto
   ```
3. **Dedicated Drain Job:** Create a separate, non-blocking scheduled/nightly GitHub Action job running `pytest -m "unvetted"`.
4. **Batch Promotion:** Drain the 282 tests in batches of 30–50 into main as they pass inspection and performance checks.

---

### Summary Checklist to Execute Now

1. **Immediate (unblock CI):** Mark `test_t1_t2_pipeline.py` and un-vetted tests with `not unvetted` filter; merge to green the main CI gate.
2. **Diagnostic (find root cause):**
   - Add `faulthandler.dump_traceback_later(180, file=sys.__stderr__, exit=True)` to root `conftest.py`.
   - Run local/CI trace with `py-spy dump --pid <pid>` when stuck to capture the exact deadlock (likely `_ENCODER_LOCK` held across a failed test exception or C-level subprocess pipe block in MLX bridge).


### Seat 3 — Grok 4.5 (`grok-4.5`)

I'll ground this in the actual hang suspects and pytest-timeout/xdist behavior, then give a plain go/no-go strategy.# Verdict (plain)

**Diagnosable enough to either fix or disprove the main theories — not worth an open-ended multi-day hunt.**

**Honest end state for the *required* gate: quarantine (or split-job) and move on.**  
Do **not** treat “root-cause this full-suite xdist hang before anything else merges” as the next two days of work. You already paid the outage cost; the next unit of value is a **green, bounded gate**, not a perfect post-mortem.

Spend **≤½ day of instrumented localization**. If you don’t get a stack that names a wait site, **stop**. Keep the deselect + issue. Ship the control-plane reboot.

That is not papering over product risk if CI never needs real MLX/embeddings and the hanging node is already correctly stubbed when run alone. It *is* papering over if you leave unbounded `readline()` / global encoder locks as permanent production shapes — fix those **structurally**, without needing the 12k-test repro.

---

## 1. Properly fixable vs quarantine

| Path | Worth it? |
| --- | --- |
| Unblock required CI via `--deselect` of the hung node (done) | **Yes — keep it** |
| Job `timeout-minutes` + pytest-timeout (done) | **Yes — permanent** |
| Prove timeout silence class with stacks (½ day) | **Yes — one burst** |
| Full binary-search of 12k-node order dependence on laptop/CI | **No** unless stacks point there |
| Re-ignore all ~282 newly-enabled tests forever | **No** (see §5) |
| Harden encoder/MLX I/O so hangs can’t be silent | **Yes — independent of repro** |

**Judgement:** Quarantine is a legitimate **operational** end state for this flake. It is not a legitimate **code** end state for `dense_rerank` / `MLXEncoderBridge` process I/O. Split those concerns.

---

## 2. Why pytest-timeout can stay silent under *both* methods

Your mental model should flip: **a pure Python `threading.RLock` wait inside the worker’s test call almost cannot explain dual silence.**

- Waiting on `threading.RLock` **releases the GIL**.
- `--timeout-method=thread` runs a watchdog thread that should dump stacks and `os._exit`.
- So if nothing fired for **23 minutes** with `--timeout=120`, either:
  1. **the timed process was not the stuck one**, or  
  2. **timeout fired but never made it into the job log**, or  
  3. **timeout was never armed for that node**, or  
  4. something rarer (whole process non-runnable / plugin not loaded).

### Class of hang invisible to both SIGALRM and thread watchdog (as *observed* silence)

| Class | Why timeout looks dead | Fits your facts? |
| --- | --- | --- |
| **A. xdist controller hang** (execnet / result protocol) | Timeout lives in **workers**. Controller waits forever; last log line is last scheduled nodeid. Job hits `timeout-minutes`. Orphans = controller + 2 workers. | **Best fit** |
| **B. Worker timeout *did* fire via `os._exit`** | Worker dies uncleanly; **controller never gets a report**; timeout dump may be lost on the dying worker’s unforwarded stream. Log = silence until job cancel. | **Very plausible** — “timeout never fired” may be wrong; “we never *saw* it” may be right |
| **C. Hang outside call phase** | Setup/teardown/fixture/session, or block while **sending the finished report** after the test body returned → per-test timer already stopped. | Plausible |
| **D. Full capture / pipe deadlock** between worker and controller | Worker blocked in write; controller not reading; classic distributed deadlock. Thread timeout *should* still kill worker unless hang is controller-side (back to A). | Possible hybrid with A |
| **E. RLock held across fork** | Child inherits held lock with no owner → permanent block on acquire. Thread timeout still usually fires *in that process* unless you’re looking at the wrong PID. | Secondary |
| **F. Global lock as the *mechanism* but not the *timeout silence*** | Earlier test starts real encoder path; later test blocks on `_ENCODER_LOCK` / `_io_lock` / `stdout.readline()`. Timeout should fire on that worker **unless** A/B apply. | Your suspect #1 is still live for *hang*, weak as sole explanation of *silence* |

### Code-grounded note on your suspects

1. **`_ENCODER_LOCK`** — real, used in `_get_encoder`, `encode_query`, and **`encode_texts` holds the lock around `encoder.encode(...)`**. Monkeypatching `_get_encoder` does **not** skip that lock in `encode_texts`. So a stuck encode on another thread/path can block the “faked” CLI test on lock acquire.

2. **`MLXEncoderBridge.__init__`** — **does not** `Popen` in `__init__`. It only `check_mlx_availability()` (raises on 16GB) then sets `_process = None`. Partial-init-orphan is **weak**. Real hang surface is later: `_read_response` → **`process.stdout.readline()` with no timeout**. That is a production footgun whether or not this CI hang is it.

3. **`test_t1_t2_pipeline`** — calls real `search_sources` → `ThreadPoolExecutor` over corpora → dense paths. Failure immediately before the hang is **suspicious as shared-state polluter**, not proof. Subset `tests/wiki` alone not hanging means you need **cross-package** pollution or **ordering × xdist schedule**, not “wiki file is toxic alone.”

**Crux answer:** Dual timeout silence is strongest evidence the failure mode is **xdist control-plane / worker-death / reporting**, not “Python lock wait inside a healthy worker that pytest-timeout is actively timing.” Treat the hung nodeid as **last log line**, not as proven sole root cause.

---

## 3. Fastest deterministic localization (cheap → expensive)

Do **not** start with full 40‑min binary search. Force a **stack** first.

### Phase 0 — Prove the timeout harness (15 min, local)

```bash
.venv/bin/python -m pytest --timeout=5 --timeout-method=thread \
  -p no:xdist -c /dev/null -q \
  -c <(echo $'import time\ndef test_hang():\n    time.sleep(60)\n') 
# or a one-off test file that only sleeps
```

Confirm you see a timeout failure and a stack. Then:

```bash
.venv/bin/python -m pytest --trace-config 2>&1 | rg -i 'timeout|xdist'
```

If CI never loaded `pytest-timeout`, the mystery is boring and fixed by pinning `addopts` / install. Don’t skip this.

### Phase 1 — Split the fault plane (1–2 short runs)

| Run | Command intent | Interpretation |
| --- | --- | --- |
| **1a** | Full suite **`-n 0`** (or `-p no:xdist`) with timeout + job cap | Hang **gone** → xdist/protocol or multi-worker shared process state. Hang **stays** → true test-order / module-global. |
| **1b** | Full suite **`-n 2 --dist loadfile`** | Hang **gone** → cross-file interleaving. Hang **stays** → within-file or session-global. |
| **1c** | Full suite **`-n 2 --dist loadscope`** | Same idea, class/module scope. |
| **1d** | `tests/wiki` + **one other heavy area** at a time (api, audit, build) under `-n 2` | Cheaper than 12k bisect; you already know wiki-alone is clean. |

**If 1a kills the hang:** stop chasing RLock narratives as primary; chase **xdist worker lifecycle + unclean exit**. Cheapest “fix” may be `execnet`/`-n 0` for wiki encode tests only, or mark them `xdist_group` serial — not a full suite rewrite.

### Phase 2 — Stacks while stuck (this is the real diagnostic)

On CI (or a long local run), while the job is still in the silent window:

1. **`ps -ef`** → identify controller vs workers (you already know 3 PIDs).
2. **`py-spy dump --pid <each>`** (or `thread` / `gdb -p` + `py-bt`) on **all three**.  
   - Controller stuck in execnet/read → class A.  
   - Worker stuck in `readline` / lock / monkeypatch path → class F.  
   - Worker dead, controller waiting → class B.
3. **`faulthandler.dump_traceback_later`** (see §4) so the next hang self-documents without SSH.

Only if stacks are ambiguous do a **collection-order bisect** (`-p no:randomly`, reverse, or half the nodeids). Binary search without stacks is how you burn another day.

### Phase 3 — Targeted code probes (no full suite)

These are **unit-level** and worth doing even if you never repro the CI hang:

```text
- encode_texts / cold_encode: try_acquire lock with timeout; never block forever
- MLXEncoderBridge._read_response: select/poll + timeout; kill worker on expiry
- CI env: SOURCES_MCP_NO_MLX=1 (or equivalent) so _get_encoder cannot open a real bridge
- autouse fixture in tests/wiki: reset dense_rerank globals + close encoder after each test
```

Your hanging test already fakes the encoder; **CI must not be one missing monkeypatch away from a real worker**.

**Laptop policy:** Prefer **CI with py-spy in a `timeout` step** over full local suite. One instrumented CI run > five blind 40‑min runs.

---

## 4. Is `faulthandler.dump_traceback_later(120, exit=False)` right?

**Yes as an instrument; no as the only kill switch.**

| Concern | Answer |
| --- | --- |
| Prints stacks where pytest-timeout was silent? | **Often yes for class A/B** if hang is wrong process or timeout report was lost — *but only if it runs in the process that’s stuck*. |
| Per xdist worker? | **Per process.** Register in `pytest_configure` / `pytest_sessionstart` so **each worker** installs it. Controller needs its own install (conftest runs there too for the controller process). |
| `exit=False` | Good for **diagnosis** (keep process for py-spy). Bad for **CI liveness** — prefer **`exit=True`** (or job `timeout-minutes`) so the gate fails closed. |
| vs pytest-timeout | faulthandler is lower-level (CPython). It can dump even when plugins are confused. It still cannot dump a process that isn’t running Python. |
| Better combo | `PYTHONFAULTHANDLER=1` + `faulthandler.dump_traceback_later(90, exit=True)` in worker **and** controller + keep pytest-timeout + job cap. |

Sketch:

```python
# tests/conftest.py
import faulthandler, os, sys

def pytest_configure(config):
    faulthandler.enable(file=sys.stderr, all_threads=True)
    # exit=True: fail closed if something wedges without pytest-timeout reporting
    faulthandler.dump_traceback_later(90, repeat=True, file=sys.stderr, exit=True)
```

Also log `os.getpid()` + xdist worker id at session start so the dump is attributable.

---

## 5. Structural: re-quarantine ~282 never-run tests?

### Option A — Big ignore list again  
**Recreates the failure mode you just deleted** (planner hardcoded ignores, main-breaking drift, false confidence).

### Option B — Required gate runs *everything*, hope for the best  
**What just burned two days.** Wrong for a 2‑core GHA runner mid-control-plane reboot.

### Option C — **Recommended**

1. **Required job:** full suite **minus** a **tiny, issue-tracked deselect list** (hung nodes only; currently one is fine). Hard `timeout-minutes`, pytest-timeout, faulthandler.
2. **Non-blocking (or `continue-on-error` / separate optional check) “soak” job:** the set of tests that were on the old ignore/never-run list, same timeouts, nightly or on label. Promote into required only after green N times.
3. **Do not** encode that set as a permanent “these tests don’t exist” list with no expiry. Encode it as **`ci-quarantine.txt` + issue + owner + review date`**, with a lint that fails if an entry has no issue.

That is **not** recreating the old ignore list. The old list was “required CI pretends these aren’t code.” The new list is “required CI is honest about what’s green; soak CI is honest about what’s unvetted.”

**Commit:** **C.** Quarantine **nodes that hang or poison**, not **whole historical ignore groups**. The ~282 get a **soak lane**, not a silent deletion from reality.

---

## Concrete plan (what I would do Monday)

**Stop conditions written first:** gate green on required path; ≤4 hours diagnostic budget; no third full blind suite.

1. **Keep** deselect of  
   `test_main_cli_encode_flag_wires_ingest_to_manifest`  
   until stacks say otherwise. Land the gate. Operator is right to be done bleeding.

2. **Pin observability (PR, small):**
   - `addopts` or CI flags: `--timeout=120 --timeout-method=thread`
   - faulthandler later dump `exit=True` in conftest
   - `SOURCES_MCP_NO_MLX=1` on CI pytest (belt)
   - on hang path: `ps` + `py-spy dump` all python PIDs in a `if: cancelled()` / wrapping script before teardown (best-effort)

3. **½-day diagnostic only if operator still cares:**
   - Phase 0 harness proof  
   - Phase 1a `-n 0` vs `-n 2`  
   - One instrumented CI run with py-spy/faulthandler  
   - **Then decide:** fix named wait site, or leave deselect + soak.

4. **Structural fixes without full repro (do these anyway):**
   - Timeout on MLX `readline` + kill worker  
   - Encoder lock acquire with timeout / never hold lock across process I/O longer than needed  
   - `tests/wiki` autouse: `_close_encoder()` + clear `_ENCODER` / caches  
   - Mark encode/CLI tests that touch globals as **serial** (`xdist_group` or no-xdist file)

5. **Do not** re-hardcode ~282 ignores into the required gate. Soak job only.

---

## Bottom line for Claude-Infra / operator

- **Is quarantine papering over?** For the **gate**: no — it’s correct risk management after a control-plane reboot. For **MLX/encoder I/O**: yes if you stop there with no timeouts on `readline` / no CI `NO_MLX`.
- **Is the hang “properly fixable”?** Fixable **if** you get one stack; **not** worth unbounded chase without one. Dual timeout silence points at **xdist/controller or lost worker death**, which makes “debug by deselecting one test until green” a rational strategy.
- **Effort not worth it:** multi-day full-suite order bisect on a laptop. **Effort worth it:** job bounds (done), one deselect (done), faulthandler/py-spy once, harden MLX read + CI `NO_MLX`, soak lane for never-run tests.

If the operator is close to abandoning: **abandon the open-ended hang hunt, not the CI reboot.** Ship quarantine + bounds + soak; treat a stack-backed fix as opportunistic follow-up, not a merge blocker.

