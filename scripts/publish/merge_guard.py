"""Shared, fail-closed PR merge readiness for the hook and publisher."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime

from scripts.opsec.prepublish import PublishBlocked

ADVISORY_NAME_MARKERS = ("advisory",)
_FAIL_BUCKETS = {"fail", "failure", "error", "cancel", "canceled", "cancelled", "timed_out", "action_required"}
_PENDING_BUCKETS = {"pending", "queued", "in_progress", "waiting", "expected"}
_PASS_BUCKETS = {"pass", "success", "skipping", "skipped", "neutral"}
_ROLLUP_FAIL = {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "ERROR", "STARTUP_FAILURE"}
_ROLLUP_PENDING = {"IN_PROGRESS", "QUEUED", "PENDING", "WAITING", "EXPECTED", "REQUESTED", "STALE"}
_ROLLUP_PASS = {"SUCCESS", "SKIPPED", "NEUTRAL"}


def _is_advisory(name: str) -> bool:
    low = name.lower()
    return any(m in low for m in ADVISORY_NAME_MARKERS)


def _checks_json_unsupported(out: subprocess.CompletedProcess[str]) -> bool:
    """Recognize gh 2.46.0's unsupported ``pr checks --json`` response only."""
    if out.returncode != 1 or (out.stdout or "").strip():
        return False
    lines = [
        line.strip() for line in re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", out.stderr or "").splitlines() if line.strip()
    ]
    return (
        len(lines) >= 4
        and lines[0] == "unknown flag: --json"
        and re.fullmatch(r"Usage:\s+gh pr checks \[<number> \| <url> \| <branch>\] \[flags\]", lines[1])
        and lines[2] == "Flags:"
        and not any("--json" in line for line in lines[2:])
        and all(line.startswith("-") for line in lines[3:])
    )


def _rollup_value(value: object) -> str:
    return value.strip().upper() if isinstance(value, str) else ""


def _rollup_name(row: dict) -> str | None:
    for field in ("name", "context"):
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _rollup_timestamp(row: dict) -> datetime | None:
    for field in ("startedAt", "createdAt", "updatedAt", "completedAt"):
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            # Treat timestamps without an offset as UTC.
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    return None


def _latest_rollup_rows(rows: list[dict]) -> list[dict] | None:
    latest: dict[tuple[str, ...], tuple[datetime | None, dict]] = {}
    for row in rows:
        name = _rollup_name(row)
        if name is None:
            return None
        context = row.get("context")
        workflow = row.get("workflowName") or row.get("workflow")
        if isinstance(context, str) and context.strip():
            key = ("context", context.strip())
        elif isinstance(workflow, str) and workflow.strip():
            key = ("check", name, workflow.strip())
        else:
            key = ("unresolved", name)
            if key in latest:
                return None
        timestamp = _rollup_timestamp(row)
        previous = latest.get(key)
        if previous is not None:
            if timestamp is None or previous[0] is None:
                return None
            if timestamp < previous[0]:
                continue
            if timestamp == previous[0]:
                return None
        latest[key] = (timestamp, row)
    return [row for _timestamp, row in latest.values()]


def _parse_status_rollup_rows(rows: list) -> tuple[list[str], list[str]] | None:
    if not rows:
        return [], []
    named = []
    for row in rows:
        if not isinstance(row, dict):
            return None
        name = _rollup_name(row)
        if name is None:
            return None
        # Cancelled runs can retain an unexpanded matrix parent. It is not an
        # executed job and cannot be superseded by the differently named shards.
        if "${{" not in name and not _is_advisory(name):
            named.append(row)
    latest = _latest_rollup_rows(named)
    if latest is None:
        return None
    failing: list[str] = []
    pending: list[str] = []
    for row in latest:
        name = _rollup_name(row)
        assert name is not None
        state = _rollup_value(row.get("state"))
        if state:
            if row.get("status") not in (None, "") or row.get("conclusion") not in (None, ""):
                return None
            result = state
        else:
            status = _rollup_value(row.get("status"))
            conclusion = _rollup_value(row.get("conclusion"))
            if conclusion in _ROLLUP_FAIL or status in _ROLLUP_FAIL:
                result = "FAILURE"
            elif status in _ROLLUP_PENDING:
                if conclusion:
                    return None
                result = "PENDING"
            elif status == "COMPLETED" and conclusion in _ROLLUP_PASS:
                result = "SUCCESS"
            else:
                return None
        if result in _ROLLUP_FAIL:
            failing.append(name)
        elif result in _ROLLUP_PENDING:
            pending.append(name)
        elif result not in _ROLLUP_PASS:
            return None
    return failing, pending


def parse_checks(rows):
    """Parse gh check buckets with the hook's advisory and unknown-state policy."""
    if not isinstance(rows, list):
        return None
    failing, pending = [], []
    for row in rows:
        if not isinstance(row, dict):
            return None
        name = str(row.get("name") or "")
        if "${{" in name or _is_advisory(name):
            continue
        bucket = str(row.get("bucket") or row.get("state") or "").lower()
        if bucket in _FAIL_BUCKETS:
            failing.append(name)
        elif bucket in _PENDING_BUCKETS:
            pending.append(name)
        elif bucket not in _PASS_BUCKETS:
            return None
    return failing, pending


def readiness_reason(meta, states):
    """A reason to refuse, or None for a ready PR; applies to every repository."""
    if not isinstance(meta, dict) or type(meta.get("isDraft")) is not bool:
        return "draft status unverifiable"
    if meta["isDraft"]:
        return "PR is a DRAFT"
    if states is None:
        return "check states unverifiable"
    failing, pending = states
    if failing:
        return "FAILING checks"
    if pending:
        return "checks still running"
    return None


def ensure_merge_ready(repo, number, *, runner, cwd, environment, match_head=None):
    """Read current metadata and checks before any merge write, including private repos."""
    if environment.get("AGENT_NO_MERGE") == "1":
        raise PublishBlocked("OPSEC: AGENT_NO_MERGE forbids merging.")
    env = {k: v for k, v in environment.items() if k not in {"CLICOLOR_FORCE", "FORCE_COLOR"}}
    env.update(NO_COLOR="1", CLICOLOR="0")

    def get(args):
        return runner(
            ["gh", "pr", *args, "--repo", repo],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )

    try:
        meta_result = get(["view", str(number), "--json", "number,isDraft,headRefOid"])
        meta = json.loads(meta_result.stdout) if meta_result.returncode == 0 else None
        if (
            not isinstance(meta, dict)
            or type(meta.get("number")) is not int
            or meta.get("number") != number
            or not isinstance(meta.get("headRefOid"), str)
            or not re.fullmatch(r"[0-9a-fA-F]{40}", meta["headRefOid"])
        ):
            raise ValueError("invalid metadata")
        checks = get(["checks", str(number), "--json", "name,bucket,state"])
        if _checks_json_unsupported(checks):
            rollup = get(["view", str(number), "--json", "statusCheckRollup"])
            states = (
                _parse_status_rollup_rows(json.loads(rollup.stdout)["statusCheckRollup"])
                if rollup.returncode == 0
                else None
            )
        else:
            raw_checks = None
            try:
                raw_checks = json.loads(checks.stdout)
                states = parse_checks(raw_checks)
            except (json.JSONDecodeError, TypeError):
                states = None
            if checks.returncode not in {0, 1, 8} or (
                checks.returncode == 1
                and isinstance(raw_checks, list)
                and not raw_checks
            ):
                states = None
        if states is None:
            raise PublishBlocked("OPSEC: merge refused: cannot establish check state.")
        reason = readiness_reason(meta, states)
        if match_head is not None and meta["headRefOid"].lower() != match_head.lower():
            reason = "reviewed head changed"
    except PublishBlocked:
        raise
    except Exception:
        raise PublishBlocked("OPSEC: merge readiness unverifiable.") from None
    if reason:
        raise PublishBlocked("OPSEC: merge refused: " + reason + ".")
    return meta["headRefOid"]
