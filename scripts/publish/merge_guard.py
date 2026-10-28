"""Shared, fail-closed PR merge readiness for the hook and publisher."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from urllib.parse import parse_qs, quote

from scripts.ci.advisory_checks import (
    external_advisory_check,
    is_advisory,
    is_external_advisory_run,
    load_advisory_checks,
)
from scripts.common.github_client import GitHubRateLimited
from scripts.github_check_rollup import (
    bind_workflow_runs,
    collapse_status_rollup,
    project_check_runs,
    rollup_identity,
    rollup_timestamp,
)
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


def _rollup_timestamp(row: dict):
    """Keep the hook's existing import bound to the shared timestamp parser."""
    return rollup_timestamp(row)


def _latest_rollup_rows(rows: list[dict]) -> list[dict] | None:
    """Use the shared reducer; ambiguous surviving versions remain unknown."""
    latest = collapse_status_rollup([
        {**row, "workflowName": row.get("workflowName") or row.get("workflow")} for row in rows
    ])
    identities = [rollup_identity(row) or ("unresolved", _rollup_name(row)) for row in latest]
    if any(_rollup_name(row) is None for row in latest) or len(set(identities)) != len(identities):
        return None
    return latest


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


_PAGE_SIZE = 100
_MAX_PAGES = 100


def _read_all_pages(get_json: Callable[[str], object], endpoint: str, key: str) -> dict | None:
    """The whole ``{total_count, key: [...]}`` collection at ``endpoint`` (``per_page=100``), or None.

    GitHub caps a page at 100 records, so a head with more check runs needs ``page=2``
    and on. The first request is the bare ``endpoint``; later ones add ``page=N``. The
    walk fails closed unless the collected records equal ``total_count``: an unreadable
    or malformed page, a short page before the total is reached, a ``total_count`` that
    changes mid-walk, or (across pages) a record without an integer id or a repeated id, is None.
    """
    first = get_json(endpoint)
    if not isinstance(first, dict) or type(first.get("total_count")) is not int or not isinstance(first.get(key), list):
        return None
    total, records = first["total_count"], list(first[key])
    page = 1
    while len(records) < total:
        if len(records) != page * _PAGE_SIZE or page >= _MAX_PAGES:
            return None
        page += 1
        following = get_json(f"{endpoint}&page={page}")
        if (
            not isinstance(following, dict)
            or following.get("total_count") != total
            or not isinstance(following.get(key), list)
            or not following[key]
        ):
            return None
        records.extend(following[key])
    if len(records) != total:
        return None
    if page > 1:
        # Only a multi-page walk can shift under new records; every record must then
        # carry an integer identity so a repeated one cannot stand in for a missed one.
        ids = [row.get("id") if isinstance(row, dict) else None for row in records]
        if any(type(value) is not int for value in ids) or len(set(ids)) != len(ids):
            return None
    return {"total_count": total, key: records}


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
    status = _read_all_pages(get_json, f"repos/{repo}/commits/{head}/status?per_page=100", "statuses")
    if status is None or any(
        not isinstance(row, dict) or not isinstance(row.get("context"), str) or row["context"] in names
        for row in status["statuses"]
    ):
        return None
    for name in sorted(names):
        entry = external_advisory_check(name)
        page = _read_all_pages(
            get_json,
            f"repos/{repo}/commits/{head}/check-runs?check_name={quote(name, safe='')}&filter=all&per_page=100",
            "check_runs",
        )
        if (
            entry is None
            or page is None
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
    names = external_advisory_names(rows)
    advisory = prove_external_advisory(repo, head, names, get_json)
    if advisory is None:
        return None
    # gh's rollup omits workflow/app identity. Both supersession and a single
    # advisory candidate need check runs joined to exact-head Actions runs.
    policy = load_advisory_checks()
    if isinstance(rows, list) and any(
        isinstance(row, dict) and row.get("name") and not row.get("workflowName")
        and (_duplicate_check_names(rows) or row["name"] in policy.names) for row in rows
    ):
        page = _read_all_pages(get_json, f"repos/{repo}/commits/{head}/check-runs?filter=all&per_page=100", "check_runs")
        if page is None:
            return None
        runs = bind_workflow_runs(
            page["check_runs"], head, repo,
            lambda number: get_json(f"repos/{repo}/actions/runs/{number}"),
        )
        if runs is None:
            return None
        # Require every observed check to be in the complete REST snapshot;
        # include extra REST rows too so a newer pending check cannot disappear.
        for row in rows:
            if not isinstance(row, dict):
                return None
            if row.get("__typename") != "CheckRun":
                continue
            details = row.get("detailsUrl")
            # The GitHub adapter projects html_url as detailsUrl. Accept that
            # representation only when its canonical URL binds the REST ID.
            matches = [run for run in runs if run.get("name") == row.get("name") and details and (
                run.get("details_url") == details or (
                    type(run.get("id")) is int and run["id"] > 0
                    and details == run.get("html_url") == f"https://github.com/{repo}/runs/{run['id']}"
                )
            )]
            if len(matches) != 1:
                return None
        rows = project_check_runs(runs) + [row for row in rows if row.get("__typename") != "CheckRun"]
        if external_advisory_names(rows) != names:
            advisory = prove_external_advisory(repo, head, external_advisory_names(rows), get_json)
    return None if advisory is None else _parse_status_rollup_rows(rows, advisory=advisory)


def _duplicate_check_names(rows):
    names = [row.get("name") for row in rows if isinstance(row, dict) and row.get("name")]
    return len(set(names)) != len(names)


def external_check_states(rows, parse, bound_states):
    """``parse(rows)``, or ``bound_states()`` when a row names an operator entry.

    Ordinary check rows carry no head, so they never grant an exemption themselves: an
    entry name switches the judgment to :func:`bound_rollup_states` at the judged head,
    a newer read. The headless rows must still be a well-formed collection.
    """
    duplicates_need_proof = isinstance(rows, list) and _duplicate_check_names(rows) and (
        parse is parse_checks or any(
            isinstance(row, dict) and row.get("name") and not row.get("workflowName") for row in rows
        )
    )
    if not external_advisory_names(rows) and not duplicates_need_proof:
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


def _read_label(endpoint: str) -> str:
    """The class of a guard REST read, without its repository or head."""
    path, _, query = endpoint.partition("?")
    params = parse_qs(query)
    if path.endswith("/status"):
        label = "commit statuses"
    elif path.endswith("/check-runs"):
        label = "named check runs" if "check_name" in params else "check runs"
    elif re.search(r"/actions/runs/\d+$", path):
        label = "actions run"
    else:
        label = "api read"
    return label + (f" page {params['page'][0]}" if params.get("page", [""])[0].isdigit() else "")


def _read_failure(result) -> str:
    """Why a read failed: the client's typed error, gh's HTTP status or the exit code; never output text."""
    observed = getattr(result, "github_result", None)
    error = getattr(observed, "error", None)
    if isinstance(error, str) and re.fullmatch(r"github_[a-z_]+", error):
        status = getattr(observed, "status", None)
        return error + (f" HTTP {status}" if error == "github_http_error" and type(status) is int else "")
    stderr = result.stderr if isinstance(result.stderr, str) else ""
    status = re.search(r"\(HTTP ([0-9]{3})\)|\bHTTP ([0-9]{3})\b", stderr)
    return f"exit {result.returncode}" + (f" HTTP {status[1] or status[2]}" if status else "")


def _collection_shape(label: str) -> Callable[[object], bool]:
    """Whether a decoded guard REST read has its class's shape (the walk judges the content)."""
    key = {"check runs": "check_runs", "named check runs": "check_runs", "commit statuses": "statuses"}.get(
        label.split(" page ")[0]
    )
    if key is None:
        return lambda value: isinstance(value, dict)
    return lambda value: (
        isinstance(value, dict) and type(value.get("total_count")) is int and isinstance(value.get(key), list)
    )


def ensure_merge_ready(repo, number, *, runner, cwd, environment, match_head=None):
    """Read current metadata and checks before any merge write, including private repos.

    Every refusal names the first read that failed (its class and the typed reason), so a
    fail-closed verdict is diagnosable without repeating the reads by hand.
    """
    if environment.get("AGENT_NO_MERGE") == "1":
        raise PublishBlocked("OPSEC: AGENT_NO_MERGE forbids merging.")
    env = {k: v for k, v in environment.items() if k not in {"CLICOLOR_FORCE", "FORCE_COLOR"}}
    env.update(NO_COLOR="1", CLICOLOR="0")
    failed: list[str] = []

    def read(label, argv):
        try:
            return runner(argv, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=15)
        except (PublishBlocked, GitHubRateLimited):
            raise
        except Exception as exc:
            failed.append(f"{label}: {type(exc).__name__}")
            raise

    def get(label, args):
        return read(label, ["gh", "pr", *args, "--repo", repo])

    def decoded(label, result, valid=lambda value: True):
        if result.returncode != 0:
            failed.append(f"{label}: {_read_failure(result)}")
            return None
        try:
            value = json.loads(result.stdout)
        except (TypeError, ValueError):
            failed.append(f"{label}: malformed JSON")
            return None
        if not valid(value):
            failed.append(f"{label}: invalid shape")
        return value

    def get_json(endpoint):
        label = _read_label(endpoint)
        return decoded(label, read(label, ["gh", "api", "--method", "GET", endpoint]), _collection_shape(label))

    def bound_view():
        return decoded(
            "pr view rollup",
            get("pr view rollup", ["view", str(number), "--json", "headRefOid,statusCheckRollup"]),
            lambda value: isinstance(value, dict) and isinstance(value.get("headRefOid"), str)
            and isinstance(value.get("statusCheckRollup"), list),
        )

    def bound_states(bound):
        return bound_rollup_states(bound, meta["headRefOid"], repo, get_json)

    def detail(fallback):
        return f" ({failed[0]})" if failed else f" ({fallback})"

    try:
        meta = decoded(
            "pr view metadata", get("pr view metadata", ["view", str(number), "--json", "number,isDraft,headRefOid"])
        )
        if (
            not isinstance(meta, dict)
            or type(meta.get("number")) is not int
            or meta.get("number") != number
            or not isinstance(meta.get("headRefOid"), str)
            or not re.fullmatch(r"[0-9a-fA-F]{40}", meta["headRefOid"])
        ):
            raise PublishBlocked("OPSEC: merge readiness unverifiable" + detail("pr view metadata: invalid") + ".")
        checks = get("pr checks", ["checks", str(number), "--json", "name,bucket,state,workflow"])
        if _checks_json_unsupported(checks):
            bound = bound_view()
            states = bound_states(bound)
        else:
            try:
                raw_checks = json.loads(checks.stdout)
                parsed = True
            except (json.JSONDecodeError, TypeError):
                raw_checks, parsed = None, False
            states = None
            # gh exits 0, 1 (failing) or 8 (pending) after a complete read; any other
            # code is an error or cancellation even when stdout parses.
            if checks.returncode in {0, 1, 8} and isinstance(raw_checks, list) and (
                checks.returncode != 1 or raw_checks
            ):
                # Modern gh can itself omit historical/same-named runs. Its
                # headless buckets cannot prove workflow/app isolation, even
                # when the returned names are unique. Judge the bound snapshot.
                states = bound_states(bound_view()) if raw_checks else parse_checks(raw_checks)
            elif checks.returncode not in {0, 1, 8} or (checks.returncode and not parsed):
                failed.append(f"pr checks: {_read_failure(checks)}")
            else:
                failed.append("pr checks: " + (
                    "malformed JSON" if not parsed else "empty failing list" if raw_checks == [] else "invalid shape"
                ))
        if states is None:
            raise PublishBlocked(
                "OPSEC: merge refused: cannot establish check state" + detail("no read failed; check rows unverifiable") + "."
            )
        reason = readiness_reason(meta, states)
        if match_head is not None and meta["headRefOid"].lower() != match_head.lower():
            reason = "reviewed head changed"
    except (PublishBlocked, GitHubRateLimited):
        raise
    except Exception as exc:
        raise PublishBlocked("OPSEC: merge readiness unverifiable" + detail(type(exc).__name__) + ".") from None
    if reason:
        raise PublishBlocked("OPSEC: merge refused: " + reason + ".")
    return meta["headRefOid"]
