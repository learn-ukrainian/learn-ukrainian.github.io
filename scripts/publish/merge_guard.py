"""Shared, fail-closed PR merge readiness for the hook and publisher."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import quote

from scripts.ci.advisory_checks import (
    external_advisory_check,
    is_advisory,
    is_external_advisory_run,
    load_advisory_checks,
)
from scripts.common.github_client import GitHubRateLimited
from scripts.opsec.prepublish import PublishBlocked

_FAIL_BUCKETS = {"fail", "failure", "error", "cancel", "canceled", "cancelled", "timed_out", "action_required"}
_PENDING_BUCKETS = {"pending", "queued", "in_progress", "waiting", "expected"}
_PASS_BUCKETS = {"pass", "success", "skipping", "skipped", "neutral"}
_ROLLUP_FAIL = {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "ERROR", "STARTUP_FAILURE"}
_ROLLUP_PENDING = {"IN_PROGRESS", "QUEUED", "PENDING", "WAITING", "EXPECTED", "REQUESTED", "STALE"}
_ROLLUP_PASS = {"SUCCESS", "SKIPPED", "NEUTRAL"}


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


def external_advisory_names(rows: object) -> frozenset[str]:
    """Exact operator-entry names among check rows; each still needs exact-head app proof."""
    if not isinstance(rows, list):
        return frozenset()
    return frozenset(
        row[field]
        for row in rows
        if isinstance(row, dict)
        for field in ("name", "context")
        if external_advisory_check(row.get(field)) is not None
    )


def _complete_page(document: object, key: str) -> bool:
    return (
        isinstance(document, dict)
        and type(document.get("total_count")) is int
        and isinstance(document.get(key), list)
        and document["total_count"] == len(document[key])
    )


def prove_external_advisory(
    repo: object, head: object, names: frozenset[str], get_json: Callable[[str], object]
) -> frozenset[str] | None:
    """``names`` when every same-named record at ``head`` is the entry's GitHub App, else None.

    The check rows carry no app identity, so the exact-head REST check runs supply it.
    A same-named run from another or no app, another head, a same-named commit status
    or an incomplete page cannot be attributed: the whole check state is unverifiable.
    ``get_json(endpoint)`` returns the decoded REST response, or None on failure.
    """
    if not names:
        return frozenset()
    if (
        not isinstance(repo, str)
        or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo)
        or not isinstance(head, str)
        or not re.fullmatch(r"[0-9a-fA-F]{40}", head)
    ):
        return None
    head = head.lower()
    status = get_json(f"repos/{repo}/commits/{head}/status?per_page=100")
    if not _complete_page(status, "statuses") or any(
        not isinstance(row, dict) or not isinstance(row.get("context"), str) or row["context"] in names
        for row in status["statuses"]
    ):
        return None
    for name in sorted(names):
        entry = external_advisory_check(name)
        page = get_json(
            f"repos/{repo}/commits/{head}/check-runs?check_name={quote(name, safe='')}&filter=all&per_page=100"
        )
        if (
            entry is None
            or not _complete_page(page, "check_runs")
            or not page["check_runs"]
            or not all(is_external_advisory_run(entry, run, head) for run in page["check_runs"])
        ):
            return None
    return names


def _exempt(row: dict, advisory: frozenset[str]) -> bool | None:
    """Whether a rollup row is a proven external check run; None for a conflicting identity.

    Only a ``CheckRun`` named exactly as a proven entry, with no commit-status identity,
    is exempt. Any other record claiming a proven name in ``name`` or ``context`` (a
    status, a hybrid or an untyped row) cannot be attributed to the proven GitHub App.
    """
    name, context = row.get("name"), row.get("context")
    if not any(isinstance(value, str) and value in advisory for value in (name, context)):
        return False
    clean = row.get("__typename") == "CheckRun" and context is None and row.get("state") is None
    return True if clean and isinstance(name, str) and name in advisory else None


def _parse_status_rollup_rows(
    rows: object, *, advisory: frozenset[str] = frozenset()
) -> tuple[list[str], list[str]] | None:
    """Parse old-client rollup rows; ``advisory`` holds only proven external names."""
    # Only a list is a check collection; null, {}, "" or false establish nothing.
    if not isinstance(rows, list):
        return None
    if not rows:
        return [], []
    policy = load_advisory_checks()
    named = []
    for row in rows:
        if not isinstance(row, dict):
            return None
        name = _rollup_name(row)
        exempt = _exempt(row, advisory)
        if name is None or exempt is None:
            return None
        # Cancelled runs can retain an unexpanded matrix parent. It is not an
        # executed job and cannot be superseded by the differently named shards.
        # The old-client statusCheckRollup fallback calls the identity workflowName.
        if "${{" not in name and not exempt and not is_advisory(
            name, workflow=row.get("workflowName") or row.get("workflow"), policy=policy
        ):
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


def bound_rollup_states(
    bound: object, head: object, repo: object, get_json: Callable[[str], object]
) -> tuple[list[str], list[str]] | None:
    """Judge a ``headRefOid,statusCheckRollup`` read whose own head is the judged ``head``.

    The rollup and its head arrive in one response, so the judged rows, the App
    provenance and the judged PR head are one commit. A missing, malformed or different
    head (the PR moved since its metadata was read) is unverifiable, never proof.
    """
    if (
        not isinstance(bound, dict)
        or not isinstance(head, str)
        or not isinstance(bound.get("headRefOid"), str)
        or bound["headRefOid"].lower() != head.lower()
    ):
        return None
    rows = bound.get("statusCheckRollup")
    advisory = prove_external_advisory(repo, head, external_advisory_names(rows), get_json)
    return None if advisory is None else _parse_status_rollup_rows(rows, advisory=advisory)


def external_check_states(rows, parse, bound_states):
    """``parse(rows)``, or ``bound_states()`` when a row names an operator entry.

    Ordinary check rows carry no head, so they never grant an exemption themselves: an
    entry name switches the judgment to :func:`bound_rollup_states` at the judged head,
    a newer read. The headless rows must still be a well-formed collection.
    """
    if not external_advisory_names(rows):
        return parse(rows)
    return bound_states() if all(isinstance(row, dict) for row in rows) else None


def parse_checks(rows):
    """Parse gh check buckets with the hook's advisory and unknown-state policy."""
    if not isinstance(rows, list):
        return None
    policy = load_advisory_checks()
    failing, pending = [], []
    for row in rows:
        if not isinstance(row, dict):
            return None
        name = str(row.get("name") or "")
        if "${{" in name or is_advisory(
            name, workflow=row.get("workflow"), policy=policy
        ):
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

    def get_json(endpoint):
        result = runner(
            ["gh", "api", "--method", "GET", endpoint],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        try:
            return json.loads(result.stdout) if result.returncode == 0 else None
        except (TypeError, ValueError):
            return None

    def bound_view():
        result = get(["view", str(number), "--json", "headRefOid,statusCheckRollup"])
        try:
            return json.loads(result.stdout) if result.returncode == 0 else None
        except (TypeError, ValueError):
            return None

    def bound_states(bound):
        return bound_rollup_states(bound, meta["headRefOid"], repo, get_json)

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
        checks = get(["checks", str(number), "--json", "name,bucket,state,workflow"])
        if _checks_json_unsupported(checks):
            bound = bound_view()
            states = external_check_states(
                bound.get("statusCheckRollup") if isinstance(bound, dict) else None,
                _parse_status_rollup_rows,
                lambda: bound_states(bound),
            )
        else:
            try:
                raw_checks = json.loads(checks.stdout)
            except (json.JSONDecodeError, TypeError):
                raw_checks = None
            states = None
            # gh exits 0, 1 (failing) or 8 (pending) after a complete read; any other
            # code is an error or cancellation even when stdout parses.
            if checks.returncode in {0, 1, 8} and isinstance(raw_checks, list) and (
                checks.returncode != 1 or raw_checks
            ):
                states = external_check_states(raw_checks, parse_checks, lambda: bound_states(bound_view()))
        if states is None:
            raise PublishBlocked("OPSEC: merge refused: cannot establish check state.")
        reason = readiness_reason(meta, states)
        if match_head is not None and meta["headRefOid"].lower() != match_head.lower():
            reason = "reviewed head changed"
    except (PublishBlocked, GitHubRateLimited):
        raise
    except Exception:
        raise PublishBlocked("OPSEC: merge readiness unverifiable.") from None
    if reason:
        raise PublishBlocked("OPSEC: merge refused: " + reason + ".")
    return meta["headRefOid"]
