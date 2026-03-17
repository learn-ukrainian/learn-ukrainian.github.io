"""BatchRunner class -- core orchestrator for the batch Gemini runner.

Manages batch state, checkpoints, module selection, and the main batch loop.
Delegates phase execution and module processing to specialized submodules.
"""

import json
from datetime import datetime

from batch_gemini_config import (
    PROJECT_ROOT,
    get_module_index,
    get_module_paths,
    get_track_config,
)
from batch_utils import (
    BatchLock,
    LockConflictError,
    atomic_write_json,
)

from .constants import FAILURES_DIR, LOCK_DIR, MAX_RETRIES, log
from .execution import _append_log, delete_review_files
from .processing import process_module, process_module_fix
from .prompt import _read_file_safe


class BatchRunner:
    """Orchestrates batch processing of curriculum modules via Gemini CLI."""

    def __init__(self, track, range_str=None, resume=False, from_idx=None,
                 mode="auto", max_consecutive_failures=3, max_failure_rate=0.5,
                 retry_failures=False):
        self.track = track
        self.config = get_track_config(track)
        self.range_str = range_str
        self.resume = resume
        self.from_idx = from_idx
        self.mode = mode
        self.retry_failures = retry_failures
        self.max_consecutive_failures = max_consecutive_failures
        self.max_failure_rate = max_failure_rate

        # State files go into a dedicated directory (not repo root)
        state_dir = PROJECT_ROOT / "batch_state"
        state_dir.mkdir(exist_ok=True)

        self.state_file = state_dir / f"state_{track}.json"
        self.checkpoint_file = state_dir / f"checkpoint_{track}.json"
        self.failure_queue_file = state_dir / "failure_queue.json"
        self.global_error_log = state_dir / f"errors_{track}.log"

        self.state = self._load_state()
        self.checkpoint = self._load_checkpoint()
        self._abort = False
        self._abort_reason = ""

    def _load_state(self):
        """Load batch state from disk, or create initial state."""
        if self.state_file.exists():
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        return {
            "batch": self.track,
            "range": self.range_str,
            "started": datetime.now().isoformat() + "Z",
            "current_module": None,
            "modules": {},
        }

    def _save_state(self):
        """Persist batch state to disk."""
        atomic_write_json(self.state_file, self.state)

    def _load_checkpoint(self):
        """Load checkpoint from disk if resuming."""
        if self.checkpoint_file.exists() and self.resume:
            with open(self.checkpoint_file, encoding="utf-8") as f:
                return json.load(f)
        return {"completed": [], "failed": []}

    def _save_checkpoint(self):
        """Persist checkpoint to disk."""
        atomic_write_json(self.checkpoint_file, self.checkpoint)

    def _log_failure(self, slug, phase, error, prompt_file, output_file):
        """Record a phase failure to the failure queue file."""
        failure = {
            "module": slug,
            "slug": slug,
            "phase": phase,
            "retries": MAX_RETRIES,
            "last_error": str(error)[:500],
            "prompt_file": str(prompt_file),
            "output_file": str(output_file),
            "timestamp": datetime.now().isoformat() + "Z",
        }

        try:
            failures = []
            if self.failure_queue_file.exists():
                failures = json.loads(
                    self.failure_queue_file.read_text(encoding="utf-8")
                )

            # Avoid duplicates -- replace existing entry for same slug+phase
            failures = [
                f for f in failures if not (f["slug"] == slug and f["phase"] == phase)
            ]
            failures.append(failure)

            atomic_write_json(self.failure_queue_file, failures)
        except (OSError, json.JSONDecodeError) as e:
            log.warning(f"Failed to write failure queue: {e}")

    def _get_modules_to_process(self):
        """Get modules from curriculum.yaml (the source of truth for ordering).

        Module N = levels.{track}.modules[N-1] in curriculum.yaml.
        --range: "39" = module 39, "1-10" = modules 1 through 10.
        --from: start from this module number.
        --retry-failures: only re-run modules with "fail" or "running" status in state.
        """
        try:
            idx = get_module_index(self.track)
        except ValueError as e:
            log.error(str(e))
            return []

        log.info(f"Track {self.track}: {idx['total']} modules in curriculum.yaml")

        # --retry-failures: scan state file for failed/stuck modules
        if self.retry_failures:
            modules_state = self.state.get("modules", {})
            retry_slugs = [
                slug for slug, info in modules_state.items()
                if info.get("status") in ("fail", "running")
            ]
            if not retry_slugs:
                log.info("No failed or stuck modules found in state. Nothing to retry.")
                return []
            # Sort by module number for consistent ordering
            slug_to_num = {v: k for k, v in idx["num_to_slug"].items()}
            retry_slugs.sort(key=lambda s: slug_to_num.get(s, 9999))
            log.info(f"Retrying {len(retry_slugs)} failed/stuck modules: {', '.join(retry_slugs)}")
            return retry_slugs

        # Determine which module numbers to process
        all_nums = list(range(1, idx["total"] + 1))

        if self.range_str:
            try:
                if "-" in self.range_str:
                    start, end = map(int, self.range_str.split("-"))
                    all_nums = [n for n in all_nums if start <= n <= end]
                else:
                    num = int(self.range_str)
                    if num not in idx["num_to_slug"]:
                        log.error(f"Module {num} not in {self.track} (range 1-{idx['total']})")
                        return []
                    all_nums = [num]
            except ValueError:
                log.error(f"Invalid range format: {self.range_str}")
                return []

        if self.from_idx is not None:
            all_nums = [n for n in all_nums if n >= self.from_idx]

        # Convert numbers to slugs
        all_plans = [idx["num_to_slug"][n] for n in all_nums]

        # Filter completed if resuming
        if self.resume:
            all_plans = [
                p for p in all_plans if p not in self.checkpoint["completed"]
            ]

        return all_plans

    def _resolve_mode_for_module(self, slug, paths):
        """Determine whether to build or fix a specific module.

        Returns "build" or "fix".
        """
        if self.mode == "build":
            return "build"
        if self.mode == "fix":
            return "fix"
        # auto mode: if .md exists and >500 bytes, use fix; otherwise build
        md_path = paths["md"]
        if md_path.exists() and md_path.stat().st_size > 500:
            return "fix"
        return "build"

    def run_batch(self):
        """Main entry point: process all modules in the batch."""
        try:
            with BatchLock(self.track, LOCK_DIR):
                self._run_batch_inner()
        except LockConflictError as e:
            log.error(f"Cannot start batch: {e}")
            return

    def _run_batch_inner(self):
        """Inner batch loop (called under lock)."""
        modules = self._get_modules_to_process()
        total = len(modules)
        log.info(f"Starting batch for {total} modules in {self.track} (mode={self.mode})")

        for i, slug in enumerate(modules):
            idx = i + 1
            if self.from_idx:
                idx += self.from_idx - 1

            # Skip modules already escalated to Claude -- don't waste Gemini cycles
            esc_file = FAILURES_DIR / self.track / f"{slug}.json"
            if esc_file.exists():
                try:
                    esc_data = json.loads(esc_file.read_text(encoding="utf-8"))
                    if esc_data.get("escalated"):
                        log.info(f"[{idx}/{total}] Skipping {slug} -- escalated to Claude")
                        continue
                except Exception:
                    pass

            paths = get_module_paths(self.track, slug)
            effective_mode = self._resolve_mode_for_module(slug, paths)

            log.info(f"[{idx}/{total}] Processing {slug} (mode={effective_mode})...")
            self.state["current_module"] = idx
            self.state["modules"][slug] = {
                "status": "running",
                "mode": effective_mode,
                "start_time": datetime.now().isoformat() + "Z",
            }
            self._save_state()

            success = process_module_fix(self, slug) if effective_mode == "fix" else process_module(self, slug)

            duration = (
                datetime.now()
                - datetime.fromisoformat(
                    self.state["modules"][slug]["start_time"].replace("Z", "")
                )
            ).total_seconds()
            self.state["modules"][slug]["duration"] = duration
            self.state["modules"][slug]["end_time"] = (
                datetime.now().isoformat() + "Z"
            )

            if success:
                self.state["modules"][slug]["status"] = "pass"
                self.checkpoint["completed"].append(slug)
            else:
                self.state["modules"][slug]["status"] = "fail"
                self.checkpoint["failed"].append(slug)

            self._save_state()
            self._save_checkpoint()

            # --- Graceful abort (e.g., all accounts exhausted) ---
            if self._abort:
                log.error(f"ABORT: {self._abort_reason}")
                self.state["abort_reason"] = self._abort_reason
                self._save_state()
                break

            # --- Error rate abort checks ---
            if self._should_abort_batch(idx, total):
                break

        # Batch summary
        passed = len(self.checkpoint.get("completed", []))
        failed = len(self.checkpoint.get("failed", []))
        processed = passed + failed
        failure_rate = (failed / processed * 100) if processed > 0 else 0

        # Calculate average duration
        durations = [
            m.get("duration", 0) for m in self.state.get("modules", {}).values()
            if m.get("status") in ("pass", "fail") and m.get("duration")
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Save summary stats to state
        self.state["summary"] = {
            "passed": passed,
            "failed": failed,
            "processed": processed,
            "total": total,
            "failure_rate": round(failure_rate, 1),
            "avg_duration_s": round(avg_duration, 1),
            "total_duration_s": round(sum(durations), 1),
        }
        self._save_state()

        log.info(f"Batch complete. State: {self.state_file}")
        log.info(f"  Results: {passed} passed, {failed} failed out of {total} ({failure_rate:.1f}% failure rate)")
        log.info(f"  Avg duration: {avg_duration:.0f}s | Total: {sum(durations):.0f}s")
        if failed:
            failures_path = FAILURES_DIR / self.track
            log.info(f"  Failures saved to: {failures_path}")
            log.info(f"  Review with: .venv/bin/python scripts/batch_gemini_runner.py --failures {self.track}")

        self._generate_summary_report(passed, failed, total, durations)

    def _should_abort_batch(self, current_idx, total):
        """Check if batch should abort due to excessive failures."""
        completed = self.checkpoint.get("completed", [])
        failed = self.checkpoint.get("failed", [])
        processed = len(completed) + len(failed)

        if processed < 3:
            return False  # Need minimum sample size

        # Check consecutive failures
        if self.max_consecutive_failures > 0 and len(failed) >= self.max_consecutive_failures:
            # Look at the last N module results in order
            all_modules = list(self.state.get("modules", {}).items())
            recent = [m[1]["status"] for m in all_modules[-self.max_consecutive_failures:]]
            if all(s == "fail" for s in recent):
                log.error(
                    f"ABORT: {self.max_consecutive_failures} consecutive failures detected. "
                    f"Likely systemic issue. Processed {processed}/{total}."
                )
                self.state["abort_reason"] = f"{self.max_consecutive_failures} consecutive failures"
                self._save_state()
                return True

        # Check failure rate (only after 5+ modules to avoid early noise)
        if self.max_failure_rate > 0 and processed >= 5:
            rate = len(failed) / processed
            if rate > self.max_failure_rate:
                log.error(
                    f"ABORT: Failure rate {rate:.0%} exceeds threshold {self.max_failure_rate:.0%}. "
                    f"{len(failed)} failed out of {processed} processed."
                )
                self.state["abort_reason"] = f"Failure rate {rate:.0%} > {self.max_failure_rate:.0%}"
                self._save_state()
                return True

        return False

    def _generate_summary_report(self, passed, failed, total, durations):
        """Generate and save a JSON summary report for the batch run."""
        report_dir = PROJECT_ROOT / "batch_state"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"report_{self.track}_{timestamp}.json"

        # Find slowest modules
        module_durations = [
            (slug, info.get("duration", 0))
            for slug, info in self.state.get("modules", {}).items()
            if info.get("duration")
        ]
        module_durations.sort(key=lambda x: x[1], reverse=True)
        slowest_5 = [
            {"slug": slug, "duration_s": round(dur, 1)}
            for slug, dur in module_durations[:5]
        ]

        # Failed module list
        failed_modules = [
            slug for slug, info in self.state.get("modules", {}).items()
            if info.get("status") == "fail"
        ]

        processed = passed + failed
        report = {
            "track": self.track,
            "mode": self.mode,
            "timestamp": datetime.now().isoformat() + "Z",
            "results": {
                "passed": passed,
                "failed": failed,
                "processed": processed,
                "total": total,
                "pass_rate": round(passed / processed * 100, 1) if processed else 0,
            },
            "timing": {
                "total_s": round(sum(durations), 1) if durations else 0,
                "avg_s": round(sum(durations) / len(durations), 1) if durations else 0,
                "slowest_5": slowest_5,
            },
            "failed_modules": failed_modules,
            "abort_reason": self.state.get("abort_reason"),
        }

        atomic_write_json(report_file, report)
        log.info(f"  Summary report: {report_file}")

    # Keep these as methods for backward compatibility -- they delegate to module functions
    # but are called by the submodules via runner reference

    def process_module(self, slug):
        """Run all phases for a single module (build mode)."""
        return process_module(self, slug)

    def process_module_fix(self, slug):
        """Audit-driven fix loop for an existing module."""
        return process_module_fix(self, slug)

    def run_phase(self, phase, slug, paths, error_msg=None):
        """Run a single phase with retries."""
        from .execution import run_phase as _run_phase
        return _run_phase(self, phase, slug, paths, error_msg)

    def _read_file_safe(self, path):
        """Read a file, returning empty string if missing or unreadable."""
        return _read_file_safe(path)

    def _generate_prompt(self, phase, slug, paths, error_msg=None):
        """Build a prompt from template + module data."""
        from .prompt import generate_prompt
        return generate_prompt(self, phase, slug, paths, error_msg)

    def _run_audit(self, md_path):
        """Run audit_module.sh and check exit code."""
        from .execution import run_audit
        return run_audit(md_path)

    def _delete_review_files(self, paths, slug):
        """Delete review files from both audit/ and review/ directories."""
        return delete_review_files(paths, slug)

    def _handle_quota_error(self, slug, phase, stderr):
        """Handle 429/quota errors with wait-retry and account rotation."""
        from .execution import handle_quota_error
        return handle_quota_error(self, slug, phase, stderr)

    def _append_log(self, log_path, message):
        """Append a timestamped message to a log file."""
        _append_log(log_path, message)

    def _apply_output(self, phase, output, paths):
        """Parse Gemini output and write to curriculum files."""
        from .execution import apply_output
        return apply_output(phase, output, paths)

    def _apply_fix_output(self, phase, output, paths):
        """Apply fix phase output."""
        from .execution import apply_fix_output
        return apply_fix_output(phase, output, paths)

    def _diagnose_module(self, status_data, paths, slug):
        """Analyze status JSON and decide what action to take."""
        from .processing import _diagnose_module
        return _diagnose_module(status_data, paths, slug)

    def _check_content_gates_pass(self, paths, slug):
        """Check if all content gates pass (anti-gaming: ignore review gate)."""
        from .processing import _check_content_gates_pass
        return _check_content_gates_pass(paths, slug)

    def _read_status_json(self, paths, slug):
        """Read the status JSON for a module."""
        from .processing import _read_status_json
        return _read_status_json(paths, slug)

    def _save_fix_state(self, orch_dir, fix_state):
        """Save fix tracking state to orchestration dir."""
        from .processing import _save_fix_state
        return _save_fix_state(orch_dir, fix_state)

    def _save_failure(self, slug, fix_state, last_status):
        """Save failure details for Claude review."""
        from .processing import _save_failure
        return _save_failure(self, slug, fix_state, last_status)
