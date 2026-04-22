"""Phase execution, Gemini calling, output application, and audit.

Handles running individual build phases, calling the gemini-cli binary,
parsing and applying output to curriculum files, and running audits.
"""

import json
import subprocess
import time
from datetime import datetime

import yaml
from agent_runtime.adapters.gemini import resolve_gemini_auth_mode
from agent_runtime.errors import (
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from agent_runtime.runner import invoke as runtime_invoke
from batch_gemini_config import PROJECT_ROOT
from batch_utils import ErrorCategory, ExponentialBackoff, classify_error
from gemini_output import (
    extract_delimited,
    extract_yaml,
    find_complete_pairs,
    has_any_end_marker,
)
from slug_utils import review_path as _review_path
from slug_utils import to_bare_slug

from .constants import (
    AUDIT_SCRIPT,
    MAX_RETRIES,
    QUOTA_MAX_RETRIES,
    QUOTA_RETRY_WAIT_SECONDS,
    TIMEOUT_SECONDS,
    log,
)
from .prompt import _read_file_safe, generate_prompt
from .utils import (
    _get_active_gemini_account,
    _get_all_gemini_accounts,
    _log_api_usage,
    _switch_gemini_account,
)


def run_phase(runner, phase, slug, paths, error_msg=None):
    """Run a single phase with retries.

    Args:
        runner: BatchRunner instance.
        phase: Phase identifier (int or string like 'fix', 'fix-content').
        slug: Module slug.
        paths: Dict of module file paths.
        error_msg: Optional error message from previous attempt.

    Returns:
        True if phase succeeded, False otherwise.
    """
    orch_dir = paths["orchestration"]
    prompt_file = orch_dir / f"phase-{phase}-prompt.md"
    output_file = orch_dir / f"phase-{phase}-output.md"
    error_log = orch_dir / "errors.log"

    retry_count = 0
    # Keep error_msg from parameter (used by fix-activities to pass audit errors)

    while retry_count <= MAX_RETRIES:
        if retry_count > 0:
            log.info(f"    Retry {retry_count}/{MAX_RETRIES}...")
            runner.state["modules"][slug]["retry"] = retry_count
            runner._save_state()

        prompt_content = generate_prompt(runner, phase, slug, paths, error_msg)
        if not prompt_content:
            log.warning(f"    No template for phase {phase}, skipping.")
            return True

        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt_content)

        # Call Gemini with the prompt file content
        result = call_gemini(prompt_file, runner.track, slug=slug, phase=phase, retry=retry_count)

        if result["returncode"] != 0:
            stderr = result["stderr"]
            category = classify_error(
                result["returncode"], stderr,
                result.get("elapsed_ms", 0), TIMEOUT_SECONDS * 1000,
            )

            if category == ErrorCategory.QUOTA:
                resolved = handle_quota_error(runner, slug, phase, stderr)
                if resolved:
                    # Retry this phase with (potentially new) account
                    retry_count += 1
                    continue
                else:
                    # All accounts exhausted -- graceful abort
                    runner._save_checkpoint()
                    runner._abort = True
                    runner._abort_reason = "All Gemini accounts exhausted"
                    return False

            if category == ErrorCategory.PERMANENT:
                log.error(f"    Permanent error (no retry): {stderr[:300]}")
                runner._log_failure(slug, phase, stderr[:500], prompt_file, output_file)
                return False

            error_msg = f"Gemini exit code {result['returncode']}.\nStderr: {stderr[:500]}"
            _append_log(
                error_log,
                f"Phase {phase} Retry {retry_count} Gemini Error:\n{error_msg}",
            )
            _append_log(
                runner.global_error_log,
                f"[{slug}] Phase {phase} Gemini Error: {error_msg[:200]}",
            )
            retry_count += 1
            continue

        output = result["stdout"]

        # Truncation detection -- check for end delimiters
        if not has_any_end_marker(output):
            # For fix phase: check if at least one complete section pair exists
            # (start AND end). If so, accept partial output and apply what we can.
            complete_pairs = find_complete_pairs(
                output, ["CONTENT", "ACTIVITIES", "VOCABULARY", "CHANGES"]
            )

            if phase in ("fix", "fix-content", "fix-activities") and complete_pairs:
                log.warning(f"    Partial output accepted: {', '.join(complete_pairs)} complete (others truncated).")
            else:
                log.warning("    Output truncated (missing end delimiter).")
                error_msg = "Your output was truncated (missing end delimiter). Please continue exactly where you left off, starting from the last complete sentence."
                retry_count += 1
                continue

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)

        # Apply output to actual curriculum files
        apply_output(phase, output, paths)

        # Validation: content/activity phases trigger audit
        if phase in runner.config.get("validation_phases", []):
            audit_result = run_audit(paths["md"])
            if audit_result["passed"]:
                log.info(f"    Phase {phase} passed audit.")
                return True
            else:
                error_msg = audit_result["errors"]
                log.warning(f"    Phase {phase} failed audit.")
                # Save audit report snapshot
                review_file = _review_path(paths["md"].parent, slug)
                if review_file.exists():
                    orch_review = (
                        orch_dir / f"phase-{phase}-audit-retry-{retry_count}.md"
                    )
                    with open(orch_review, "w", encoding="utf-8") as f:
                        f.write(_read_file_safe(review_file))

                _append_log(
                    error_log,
                    f"Phase {phase} Retry {retry_count} Audit Failed:\n{error_msg[:1000]}",
                )
                _append_log(
                    runner.global_error_log,
                    f"[{slug}] Phase {phase} Audit Failed (Retry {retry_count})",
                )
                retry_count += 1
        elif phase in ("fix", "fix-content", "fix-activities"):
            # Fix phases: run audit to verify fixes worked
            audit_result = run_audit(paths["md"])
            if audit_result["passed"]:
                log.info(f"    {phase} phase passed audit.")
            return True
        else:
            # Non-validation phases (research, review) pass through
            return True

    # All retries failed
    runner._log_failure(slug, phase, error_msg, prompt_file, output_file)
    return False


def call_gemini(prompt_file, track, slug="unknown", phase="unknown", retry=0):
    """Call gemini-cli with the prompt file content. Returns parsed output + stats."""
    # Read the prompt file and pass content via -p
    prompt_content = prompt_file.read_text(encoding="utf-8")

    start_time = time.monotonic()
    try:
        # Load-bearing: route through the shared runtime so batch_gemini_runner
        # inherits the Gemini fallback ladder's per-rung env stripping,
        # 429 auto-fallover across model/auth rungs, and API cooldown awareness.
        result = runtime_invoke(
            "gemini",
            prompt_content,
            mode="read-only",
            cwd=PROJECT_ROOT,
            task_id=_runtime_task_id(track, slug, phase, retry),
            tool_config={"auth_mode": resolve_gemini_auth_mode()},
            entrypoint="dispatch",
            hard_timeout=TIMEOUT_SECONDS,
        )
        return _runtime_result_to_legacy_payload(
            result, track=track, slug=slug, phase=phase, retry=retry,
        )
    except AgentTimeoutError:
        return _timeout_payload(start_time, TIMEOUT_SECONDS)
    except (AgentUnavailableError, RateLimitedError) as exc:
        return _runtime_error_payload(exc, start_time)


def apply_output(phase, output, paths):
    """Parse Gemini output and write to curriculum files."""
    if phase == 0:  # Research
        content = extract_delimited(output, "RESEARCH")
        if content:
            paths["research"].parent.mkdir(parents=True, exist_ok=True)
            with open(paths["research"], "w", encoding="utf-8") as f:
                f.write(content)

    elif phase == 1:  # Meta
        content = extract_delimited(output, "META_OUTLINE")
        if content:
            meta_data = {}
            if paths["meta"].exists():
                with open(paths["meta"], encoding="utf-8") as f:
                    meta_data = yaml.safe_load(f) or {}

            try:
                outline_data = yaml.safe_load(content)
                meta_data.update(outline_data)
                with open(paths["meta"], "w", encoding="utf-8") as f:
                    yaml.dump(
                        meta_data, f, allow_unicode=True, sort_keys=False
                    )
            except yaml.YAMLError as e:
                log.error(f"Failed to parse meta YAML: {e}")

    elif phase == 2:  # Content
        content = extract_delimited(output, "CONTENT")
        if content:
            with open(paths["md"], "w", encoding="utf-8") as f:
                f.write(content)

    elif phase == 3:  # Activities
        act_data = extract_yaml(output, "ACTIVITIES")
        if act_data is not None:
            paths["activities"].parent.mkdir(parents=True, exist_ok=True)
            with open(paths["activities"], "w", encoding="utf-8") as f:
                yaml.dump(act_data, f, allow_unicode=True, sort_keys=False)
        elif extract_delimited(output, "ACTIVITIES") is not None:
            log.error("Failed to parse activities YAML")

        # Also check for vocabulary block
        vocab_data = extract_yaml(output, "VOCABULARY")
        if vocab_data is not None:
            paths["vocabulary"].parent.mkdir(parents=True, exist_ok=True)
            with open(paths["vocabulary"], "w", encoding="utf-8") as f:
                yaml.dump(vocab_data, f, allow_unicode=True, sort_keys=False)
        elif extract_delimited(output, "VOCABULARY") is not None:
            log.error("Failed to parse vocabulary YAML")

    elif phase == 5:  # Review
        content = extract_delimited(output, "REVIEW")
        if content:
            rev_path = _review_path(paths["md"].parent, paths["md"].stem)
            rev_path.parent.mkdir(parents=True, exist_ok=True)
            with open(rev_path, "w", encoding="utf-8") as f:
                f.write(content)

    elif phase in ("fix", "fix-content", "fix-activities"):
        apply_fix_output(phase, output, paths)


def apply_fix_output(phase, output, paths):
    """Apply fix phase output (shared logic for fix, fix-content, fix-activities)."""
    orch_dir = paths["orchestration"]

    # Content fixes (fix and fix-content phases)
    if phase in ("fix", "fix-content"):
        new_content = extract_delimited(output, "CONTENT")
        if new_content is not None:
            if len(new_content) >= 100:
                with open(paths["md"], "w", encoding="utf-8") as f:
                    f.write(new_content)
                log.info("    Applied content fixes.")
            else:
                log.warning(f"    Content fix too short ({len(new_content)} chars), skipping.")

    # Activities fixes (fix and fix-activities phases)
    if phase in ("fix", "fix-activities"):
        act_content = extract_delimited(output, "ACTIVITIES")
        if act_content is not None:
            if len(act_content) >= 50:
                try:
                    act_data = yaml.safe_load(act_content)
                    paths["activities"].parent.mkdir(parents=True, exist_ok=True)
                    with open(paths["activities"], "w", encoding="utf-8") as f:
                        yaml.dump(act_data, f, allow_unicode=True, sort_keys=False)
                    log.info("    Applied activities fixes.")
                except yaml.YAMLError as e:
                    log.error(f"    Failed to parse fixed activities YAML: {e}")
            else:
                log.warning(f"    Activities fix too short ({len(act_content)} chars), skipping.")

    # Vocabulary fixes (fix and fix-activities phases)
    if phase in ("fix", "fix-activities"):
        vocab_content = extract_delimited(output, "VOCABULARY")
        if vocab_content is not None:
            if len(vocab_content) >= 50:
                try:
                    vocab_data = yaml.safe_load(vocab_content)
                    paths["vocabulary"].parent.mkdir(parents=True, exist_ok=True)
                    with open(paths["vocabulary"], "w", encoding="utf-8") as f:
                        yaml.dump(vocab_data, f, allow_unicode=True, sort_keys=False)
                    log.info("    Applied vocabulary fixes.")
                except yaml.YAMLError as e:
                    log.error(f"    Failed to parse fixed vocabulary YAML: {e}")
            else:
                log.warning(f"    Vocabulary fix too short ({len(vocab_content)} chars), skipping.")

    # Save changes report
    changes_content = extract_delimited(output, "CHANGES")
    if changes_content:
        suffix = {"fix": "fix", "fix-content": "fix-content", "fix-activities": "fix-activities"}
        changes_file = orch_dir / f"{suffix[phase]}-changes.md"
        with open(changes_file, "w", encoding="utf-8") as f:
            f.write(changes_content)


def run_audit(md_path):
    """Run audit_module.sh and check exit code."""
    cmd = [str(AUDIT_SCRIPT), str(md_path)]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        stdout = res.stdout.decode("utf-8", errors="replace") if isinstance(res.stdout, bytes) else res.stdout
        return {
            "passed": res.returncode == 0,
            "errors": stdout if res.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "errors": "Audit timed out after 120s",
        }


def handle_quota_error(runner, slug, phase, stderr):
    """Handle 429/quota errors with wait-retry and account rotation.

    Returns True if we should retry (waited or switched account).
    Returns False if all accounts exhausted (caller should exit).
    """
    all_accounts = _get_all_gemini_accounts()
    current = _get_active_gemini_account()

    # First: try waiting (transient server overload) with exponential backoff
    backoff = ExponentialBackoff(
        base=QUOTA_RETRY_WAIT_SECONDS, max_wait=600, jitter=0.2
    )
    for attempt in range(1, QUOTA_MAX_RETRIES + 1):
        wait = backoff.wait_time(attempt)
        log.warning(
            f"  Quota/capacity error on {current}. "
            f"Waiting {wait:.0f}s before retry ({attempt}/{QUOTA_MAX_RETRIES})..."
        )
        time.sleep(wait)

        # Probe the current account through the runtime so auth-mode
        # resolution and env stripping match the real batch call path.
        if _gemini_capacity_probe(runner.track, slug, phase):
            log.info(f"  Capacity restored for {current}. Resuming.")
            return True

    # Waiting didn't help -- try switching accounts
    log.warning(f"  Account {current} exhausted after {QUOTA_MAX_RETRIES} waits.")

    if len(all_accounts) <= 1:
        log.error("  No other accounts available. Saving checkpoint.")
        return False

    # Find next account in rotation
    try:
        current_idx = all_accounts.index(current)
    except ValueError:
        current_idx = -1

    tried_accounts = {current}
    for i in range(1, len(all_accounts)):
        next_idx = (current_idx + i) % len(all_accounts)
        next_account = all_accounts[next_idx]
        if next_account in tried_accounts:
            continue
        tried_accounts.add(next_account)

        log.info(f"  Trying account: {next_account}")
        if _switch_gemini_account(next_account):
            # Test the new account
            if _gemini_capacity_probe(runner.track, slug, phase):
                log.info(f"  Account {next_account} works. Resuming batch.")
                return True
            else:
                log.warning(f"  Account {next_account} also failing.")

    log.error("  All accounts exhausted. Saving checkpoint and exiting.")
    return False


def delete_review_files(paths, slug):
    """Delete review files from both audit/ and review/ directories."""
    bare = to_bare_slug(slug)
    base_dir = paths["md"].parent
    deleted = False
    # Check both dirs during transition period
    for subdir in ("audit", "review"):
        rp = base_dir / subdir / f"{bare}-review.md"
        if rp.exists():
            rp.unlink()
            deleted = True
    return deleted


def _append_log(log_path, message):
    """Append a timestamped message to a log file."""
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now().isoformat()}] {message}\n")


def _runtime_task_id(track, slug, phase, retry, purpose="call"):
    """Build a stable task identifier for runtime usage records."""
    return f"batch-gemini-runner:{purpose}:{track}:{slug}:{phase}:retry-{retry}"


def _timeout_payload(start_time, timeout_seconds):
    """Preserve the legacy timeout return shape from direct subprocess.run."""
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    return {
        "returncode": -1,
        "stdout": "",
        "stderr": f"Timeout expired ({timeout_seconds}s)",
        "gemini_json": {},
        "elapsed_ms": elapsed_ms,
    }


def _runtime_error_payload(exc, start_time):
    """Map runtime exceptions onto the legacy non-zero subprocess payload."""
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    stderr = exc.reason or str(exc) if isinstance(exc, RateLimitedError) else str(exc)
    return {
        "returncode": 1,
        "stdout": "",
        "stderr": stderr,
        "gemini_json": {},
        "elapsed_ms": elapsed_ms,
    }


def _parse_gemini_runtime_response(raw_response):
    """Parse runtime Gemini output, preserving the legacy JSON contract when possible."""
    if not raw_response.strip():
        return "", {}
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError:
        return raw_response, {}
    if isinstance(payload, dict):
        return payload.get("response", raw_response), payload
    return raw_response, {}


def _build_runtime_usage_payload(result, gemini_json, elapsed_ms):
    """Backfill the legacy batch usage logger from runtime results.

    Exact token counters are only available when the runtime response is a
    Gemini `-o json` payload. Otherwise we still preserve model + latency
    continuity for the batch usage ledger without inventing token splits.
    """
    if gemini_json:
        return gemini_json
    return {
        "response": result.response,
        "stats": {
            "models": {
                result.model: {
                    "api": {
                        "totalLatencyMs": elapsed_ms,
                    },
                },
            },
        },
    }


def _runtime_result_to_legacy_payload(result, *, track, slug, phase, retry, log_usage=True):
    """Translate runtime Result into the historical batch_gemini_runner dict."""
    elapsed_ms = int(result.duration_s * 1000)
    stdout_text, gemini_json = _parse_gemini_runtime_response(result.response or "")
    if result.ok and log_usage:
        _log_api_usage(
            track,
            slug,
            phase,
            retry,
            _build_runtime_usage_payload(result, gemini_json, elapsed_ms),
            elapsed_ms,
        )
    return {
        "returncode": result.returncode if result.returncode is not None else (0 if result.ok else 1),
        "stdout": stdout_text,
        "stderr": result.stderr_excerpt or "",
        "gemini_json": gemini_json,
        "elapsed_ms": elapsed_ms,
    }


def _gemini_capacity_probe(track, slug, phase):
    """Probe the current Gemini subscription account through the runtime."""
    try:
        result = runtime_invoke(
            "gemini",
            "Say OK",
            mode="read-only",
            cwd=PROJECT_ROOT,
            task_id=_runtime_task_id(track, slug, phase, 0, purpose="probe"),
            tool_config={"auth_mode": "subscription"},
            entrypoint="dispatch",
            hard_timeout=30,
        )
        payload = _runtime_result_to_legacy_payload(
            result, track=track, slug=slug, phase=phase, retry=0, log_usage=False,
        )
        return payload["returncode"] == 0
    except AgentTimeoutError:
        return False
    except (AgentUnavailableError, RateLimitedError):
        return False
