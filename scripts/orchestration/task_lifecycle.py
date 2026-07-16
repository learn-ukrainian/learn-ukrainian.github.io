"""Canonical fleet task lifecycle, evidence, and closeout projection.

The module is deliberately split from the GitHub CLI adapter.  Everything here
is deterministic over a validated task-identity envelope, an immutable AC/evidence
ledger, and an injected observation.  Remote reads and explicitly authorized
mutations live in :mod:`scripts.orchestration.task_closeout`.
"""

from __future__ import annotations

import fcntl
import fnmatch
import hashlib
import json
import os
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from scripts.orchestration import task_identity

SCHEMA_VERSION = "task-lifecycle.v1"
AC_SCHEMA_VERSION = "acceptance-criteria.v1"
OBSERVATION_SCHEMA_VERSION = "task-closeout-observation.v1"
TERMINAL_GOALS = frozenset({"merge", "deploy", "certify"})
STATES = (
    "ISSUE_LINKED",
    "ACS_FINALIZED",
    "IMPLEMENTATION_READY",
    "PR_OPEN",
    "REVIEW_REQUESTED",
    "CHANGES_REQUESTED",
    "REVIEW_PASSED",
    "CI_PASSED",
    "MERGED",
    "DEPLOYED",
    "CERTIFIED",
    "ISSUE_CLOSED",
    "CLEANED_UP",
    "BLOCKED_WITH_RECEIPT",
)
STATE_RANK = {state: index for index, state in enumerate(STATES[:-1])}
EVIDENCE_TYPES = frozenset(
    {
        "command",
        "test",
        "review",
        "behavior_proof",
        "ci",
        "github",
        "deployment",
        "certification",
        "follow_up",
        "cleanup",
        "document",
    }
)
CURRENT_HEAD_EVIDENCE = EVIDENCE_TYPES - {"follow_up", "cleanup"}
PROTECTED_PATH_PATTERNS = (
    ".python-version",
    ".yamllint",
    ".markdownlint.json",
    "curriculum/l2-uk-en/**/status/*.json",
    "curriculum/l2-uk-en/**/audit/*-review.md",
    "curriculum/l2-uk-en/**/review/*-review.md",
    "docs/*-STATUS.md",
    "data/telemetry/**",
)
FORBIDDEN_RECEIPT_PATH_MARKERS = (
    "/status/",
    "/audit/",
    "/review/",
    "-review.md",
    "/telemetry/",
    "/data/telemetry/",
)

_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _ROOT / "agents_extensions" / "shared" / "schemas" / "task-lifecycle.v1.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_VALIDATOR = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())
_AC_RE = re.compile(
    r"^- \[(?P<checked>[ xX])\] \*\*(?P<id>[A-Z][A-Z0-9_-]{1,31})\*\*\s+[—-]\s+(?P<text>.+?)\s*$"
)
_SAFE_FAMILY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")


class LifecycleError(ValueError):
    """The lifecycle ledger or requested transition violates the contract."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    payload = value if isinstance(value, str) else canonical_json(value)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _clean_text(value: Any, label: str, *, maximum: int = 4000) -> str:
    cleaned = " ".join(str(value or "").split())
    if not cleaned:
        raise LifecycleError(f"{label} must be non-empty")
    if len(cleaned) > maximum:
        raise LifecycleError(f"{label} exceeds {maximum} characters")
    return cleaned


def _issue_url(repository: str, number: int) -> str:
    return f"https://github.com/{repository}/issues/{number}"


def _pr_url(repository: str, number: int) -> str:
    return f"https://github.com/{repository}/pull/{number}"


def lifecycle_id(identity: Mapping[str, Any]) -> str:
    canonical = task_identity.validate_identity(identity)
    issue = canonical.get("github_issue_number")
    if issue is None:
        raise LifecycleError("non-trivial lifecycle work requires a GitHub issue")
    return digest(
        {
            "repository": canonical["repository"],
            "issue": issue,
            "stream_epic": canonical["stream_epic"],
        }
    )


def parse_issue_acceptance_criteria(body: str) -> list[dict[str, Any]]:
    """Parse stable-ID issue checkboxes in their authoritative order."""
    criteria: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_line in str(body or "").splitlines():
        match = _AC_RE.fullmatch(raw_line.strip())
        if not match:
            continue
        ac_id = match.group("id")
        if ac_id in seen:
            raise LifecycleError(f"duplicate acceptance criterion ID in issue body: {ac_id}")
        seen.add(ac_id)
        criteria.append(
            {
                "id": ac_id,
                "text": _clean_text(match.group("text"), f"acceptance criterion {ac_id}"),
                "checked": match.group("checked").lower() == "x",
            }
        )
    if not criteria:
        raise LifecycleError("issue body has no stable-ID acceptance criteria")
    return criteria


def ac_content_hash(criteria: list[Mapping[str, Any]]) -> str:
    projection = [
        {
            "id": item["id"],
            "text": item["text"],
            "applicable": item["applicable"],
            "due_state": item["due_state"],
            "required_evidence": list(item["required_evidence"]),
            "behavior_proof_required": item["behavior_proof_required"],
        }
        for item in criteria
    ]
    return digest(projection)


def build_ac_snapshot(
    issue_body: str,
    policy: Mapping[str, Mapping[str, Any]],
    *,
    finalized_at: str,
) -> dict[str, Any]:
    parsed = parse_issue_acceptance_criteria(issue_body)
    parsed_ids = [item["id"] for item in parsed]
    policy_ids = list(policy)
    missing = [ac_id for ac_id in parsed_ids if ac_id not in policy]
    extra = [ac_id for ac_id in policy_ids if ac_id not in parsed_ids]
    if missing or extra:
        raise LifecycleError(f"AC policy mismatch: missing={missing}, extra={extra}")

    criteria: list[dict[str, Any]] = []
    for item in parsed:
        ac_id = item["id"]
        spec = policy[ac_id]
        due_state = str(spec.get("due_state") or "")
        if due_state not in STATE_RANK or due_state in {
            "ISSUE_LINKED",
            "ACS_FINALIZED",
            "PR_OPEN",
            "REVIEW_REQUESTED",
            "CHANGES_REQUESTED",
        }:
            raise LifecycleError(f"{ac_id}: invalid evidence due state {due_state!r}")
        required = list(spec.get("required_evidence") or [])
        if not required or any(kind not in EVIDENCE_TYPES for kind in required):
            raise LifecycleError(f"{ac_id}: required_evidence must contain supported evidence types")
        if len(required) != len(set(required)):
            raise LifecycleError(f"{ac_id}: required_evidence contains duplicates")
        criteria.append(
            {
                "id": ac_id,
                "text": item["text"],
                "applicable": bool(spec.get("applicable", True)),
                "due_state": due_state,
                "required_evidence": required,
                "behavior_proof_required": bool(spec.get("behavior_proof_required", False)),
            }
        )
    return {
        "schema_version": AC_SCHEMA_VERSION,
        "content_hash": ac_content_hash(criteria),
        "finalized_at": finalized_at,
        "criteria": criteria,
    }


def build_lifecycle(
    identity: Mapping[str, Any],
    *,
    author_family: str,
    ac_snapshot: Mapping[str, Any],
    required_checks: list[str],
    now: str,
    pr_number: int | None = None,
    migration_source: str = "explicit",
    legacy: bool = False,
) -> dict[str, Any]:
    canonical_identity = task_identity.validate_identity(identity)
    terminal_goal = canonical_identity["terminal_goal"]
    if terminal_goal not in TERMINAL_GOALS:
        raise LifecycleError("implementation lifecycle requires terminal goal merge, deploy, or certify")
    issue = canonical_identity.get("github_issue_number")
    epic = canonical_identity.get("stream_epic")
    if issue is None or epic is None:
        raise LifecycleError("implementation lifecycle requires an issue linked to one stream epic")
    family = _clean_text(author_family, "author family", maximum=100)
    if not _SAFE_FAMILY_RE.fullmatch(family):
        raise LifecycleError("author family contains unsupported characters")
    checks = [_clean_text(value, "required check", maximum=200) for value in required_checks]
    if not checks or len(checks) != len(set(checks)):
        raise LifecycleError("required checks must be a non-empty unique list")
    snapshot = deepcopy(dict(ac_snapshot))
    ledger = {
        "schema_version": SCHEMA_VERSION,
        "lifecycle_id": lifecycle_id(canonical_identity),
        "identity": canonical_identity,
        "terminal_goal": terminal_goal,
        "current_state": "ISSUE_LINKED",
        "author_family": family,
        "pr": {
            "number": pr_number,
            "url": _pr_url(canonical_identity["repository"], pr_number) if pr_number else None,
        },
        "ac_snapshot": snapshot,
        "evidence": [],
        "required_checks": checks,
        "remaining_scope": {
            "status": "none",
            "summary": "",
            "follow_up_issue": None,
            "follow_up_stream_epic": None,
            "evidence_ids": [],
        },
        "observation_receipts": [],
        "mutation_receipts": [],
        "created_at": now,
        "updated_at": now,
        "migration": {
            "source": _clean_text(migration_source, "migration source", maximum=100),
            "legacy": legacy,
            "migrated_at": now if legacy else None,
        },
    }
    return validate_lifecycle(ledger)


def _schema_errors(payload: Mapping[str, Any]) -> list[str]:
    errors = sorted(_VALIDATOR.iter_errors(payload), key=lambda item: list(item.absolute_path))
    rendered: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        rendered.append(f"{location}: {error.message}")
    return rendered


def _evidence_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in record.items() if key != "id"}


def _receipt_event_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in record.items() if key != "id"}


def _validate_behavior_proof_reference_shape(details: Mapping[str, Any]) -> dict[str, str]:
    reference = details.get("behavior_proof_receipt")
    if not isinstance(reference, Mapping):
        raise LifecycleError(
            "behavior-proof evidence requires details.behavior_proof_receipt"
        )
    required = {"receipt_path", "receipt_sha256", "input_sha256", "target_sha"}
    if set(reference) != required:
        raise LifecycleError(
            "behavior-proof receipt reference requires only receipt_path, receipt_sha256, "
            "input_sha256, and target_sha"
        )
    normalized = {key: str(reference.get(key) or "") for key in sorted(required)}
    receipt_path = Path(normalized["receipt_path"]).expanduser()
    if not receipt_path.is_absolute():
        raise LifecycleError("behavior-proof receipt path must be absolute")
    slash_path = str(receipt_path).replace("\\", "/")
    if any(marker in slash_path for marker in FORBIDDEN_RECEIPT_PATH_MARKERS):
        raise LifecycleError("behavior-proof receipt path is a forbidden generated-artifact path")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", normalized["receipt_sha256"]):
        raise LifecycleError("behavior-proof receipt digest must be sha256:<64 lowercase hex>")
    if not re.fullmatch(r"[0-9a-f]{64}", normalized["input_sha256"]):
        raise LifecycleError("behavior-proof target-input fingerprint must be 64 lowercase hex")
    if not re.fullmatch(r"[0-9a-f]{40}", normalized["target_sha"]):
        raise LifecycleError("behavior-proof target SHA must be 40 lowercase hex")
    return normalized


def validate_lifecycle(payload: Mapping[str, Any]) -> dict[str, Any]:
    errors = _schema_errors(payload)
    if errors:
        raise LifecycleError(f"task lifecycle schema violation at {errors[0]}")
    ledger = deepcopy(dict(payload))
    identity = task_identity.validate_identity(ledger["identity"])
    if ledger["lifecycle_id"] != lifecycle_id(identity):
        raise LifecycleError("lifecycle ID does not match the exact task identity")
    if ledger["terminal_goal"] != identity["terminal_goal"]:
        raise LifecycleError("lifecycle terminal goal does not match task identity")
    if identity.get("github_issue_number") is None or identity.get("stream_epic") is None:
        raise LifecycleError("task lifecycle identity requires issue and stream epic")
    pr_number = ledger["pr"]["number"]
    expected_pr_url = _pr_url(identity["repository"], pr_number) if pr_number else None
    if ledger["pr"]["url"] != expected_pr_url:
        raise LifecycleError("PR URL does not match repository and PR number")
    snapshot = ledger["ac_snapshot"]
    criteria = snapshot["criteria"]
    ids = [item["id"] for item in criteria]
    if len(ids) != len(set(ids)):
        raise LifecycleError("AC snapshot contains duplicate stable IDs")
    if snapshot["content_hash"] != ac_content_hash(criteria):
        raise LifecycleError("AC snapshot content hash is stale or forged")
    for criterion in criteria:
        if criterion["behavior_proof_required"] and "behavior_proof" not in criterion[
            "required_evidence"
        ]:
            raise LifecycleError(
                f"{criterion['id']}: behavior-proof-required AC must require behavior_proof evidence"
            )
    criteria_by_id = {item["id"]: item for item in criteria}
    evidence_ids: set[str] = set()
    for record in ledger["evidence"]:
        if record["id"] != digest(_evidence_payload(record)):
            raise LifecycleError(f"evidence {record['id']} digest is invalid")
        if record["id"] in evidence_ids:
            raise LifecycleError(f"duplicate evidence record: {record['id']}")
        evidence_ids.add(record["id"])
        if record["ac_id"] not in criteria_by_id:
            raise LifecycleError(f"evidence targets unknown AC: {record['ac_id']}")
        subject = record["subject"]
        if subject["repository"] != identity["repository"]:
            raise LifecycleError("evidence repository does not match task identity")
        if subject["issue"] != identity["github_issue_number"]:
            raise LifecycleError("evidence issue does not match task identity")
        if subject["pr"] != pr_number:
            raise LifecycleError("evidence PR does not match lifecycle binding")
        if record["type"] == "review":
            details = record["details"]
            required = {"author_family", "reviewer_family", "verdict"}
            if not required.issubset(details):
                raise LifecycleError("review evidence requires author_family, reviewer_family, and verdict")
            if details["author_family"] != ledger["author_family"]:
                raise LifecycleError("review evidence author family does not match lifecycle")
            if details["reviewer_family"] == details["author_family"]:
                raise LifecycleError("review evidence is not outside the author model family")
            if details["verdict"] != "pass":
                raise LifecycleError("review evidence verdict must be pass")
        if record["type"] == "behavior_proof":
            reference = _validate_behavior_proof_reference_shape(record["details"])
            if subject["commit"] is None or reference["target_sha"] != subject["commit"]:
                raise LifecycleError(
                    "behavior-proof receipt target SHA does not match its evidence subject"
                )
    for evidence_id in ledger["remaining_scope"]["evidence_ids"]:
        if evidence_id not in evidence_ids:
            raise LifecycleError("remaining-scope evidence ID is not present in the evidence ledger")
    remaining = ledger["remaining_scope"]
    if remaining["status"] == "none":
        if remaining["follow_up_issue"] is not None or remaining["follow_up_stream_epic"] is not None:
            raise LifecycleError("remaining scope none cannot carry a follow-up issue")
    elif remaining["status"] == "open":
        if not remaining["summary"].strip():
            raise LifecycleError("open remaining scope requires a summary")
    else:
        if not remaining["summary"].strip() or not remaining["follow_up_issue"]:
            raise LifecycleError("transferred scope requires a summary and follow-up issue")
        if not remaining["follow_up_stream_epic"] or not remaining["evidence_ids"]:
            raise LifecycleError("transferred scope requires one stream epic and evidence")
    observation_ids: set[str] = set()
    for receipt in ledger["observation_receipts"]:
        if receipt["id"] != digest(_receipt_event_payload(receipt)):
            raise LifecycleError("observation receipt digest is invalid")
        if receipt["id"] in observation_ids:
            raise LifecycleError("duplicate observation receipt")
        observation_ids.add(receipt["id"])
    mutation_ids: set[str] = set()
    for receipt in ledger["mutation_receipts"]:
        if receipt["id"] != digest(_receipt_event_payload(receipt)):
            raise LifecycleError("mutation receipt digest is invalid")
        if receipt["id"] in mutation_ids:
            raise LifecycleError("duplicate mutation receipt event")
        mutation_ids.add(receipt["id"])
    return ledger


def bind_pr(payload: Mapping[str, Any], *, pr_number: int, now: str) -> dict[str, Any]:
    ledger = validate_lifecycle(payload)
    if pr_number < 1:
        raise LifecycleError("PR number must be positive")
    existing = ledger["pr"]["number"]
    if existing is not None and existing != pr_number:
        raise LifecycleError("lifecycle is already bound to a different PR")
    if existing == pr_number:
        return ledger
    ledger["pr"] = {
        "number": pr_number,
        "url": _pr_url(ledger["identity"]["repository"], pr_number),
    }
    ledger["updated_at"] = now
    return validate_lifecycle(ledger)


def add_evidence(
    payload: Mapping[str, Any],
    *,
    ac_id: str,
    evidence_type: str,
    summary: str,
    url: str | None,
    commit: str | None,
    details: Mapping[str, Any] | None,
    recorded_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ledger = validate_lifecycle(payload)
    if evidence_type not in EVIDENCE_TYPES:
        raise LifecycleError(f"unsupported evidence type: {evidence_type}")
    if ac_id not in {item["id"] for item in ledger["ac_snapshot"]["criteria"]}:
        raise LifecycleError(f"unknown acceptance criterion: {ac_id}")
    pr_number = ledger["pr"]["number"]
    if pr_number is None:
        raise LifecycleError("bind the lifecycle to a PR before recording evidence")
    if commit is not None and not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise LifecycleError("evidence commit must be a full lowercase Git SHA")
    record: dict[str, Any] = {
        "ac_id": ac_id,
        "type": evidence_type,
        "summary": _clean_text(summary, "evidence summary"),
        "url": url,
        "subject": {
            "repository": ledger["identity"]["repository"],
            "issue": ledger["identity"]["github_issue_number"],
            "pr": pr_number,
            "commit": commit,
        },
        "details": deepcopy(dict(details or {})),
        "recorded_at": recorded_at,
    }
    record["id"] = digest(record)
    for existing in ledger["evidence"]:
        if existing["id"] == record["id"]:
            return ledger, existing
    ledger["evidence"].append(record)
    ledger["updated_at"] = recorded_at
    return validate_lifecycle(ledger), record


def set_remaining_scope(
    payload: Mapping[str, Any],
    *,
    status: str,
    summary: str = "",
    follow_up_issue: int | None = None,
    follow_up_stream_epic: int | None = None,
    evidence_ids: list[str] | None = None,
    now: str,
) -> dict[str, Any]:
    ledger = validate_lifecycle(payload)
    if status not in {"none", "open", "transferred"}:
        raise LifecycleError("remaining scope status must be none, open, or transferred")
    ledger["remaining_scope"] = {
        "status": status,
        "summary": " ".join(summary.split()),
        "follow_up_issue": follow_up_issue,
        "follow_up_stream_epic": follow_up_stream_epic,
        "evidence_ids": list(evidence_ids or []),
    }
    ledger["updated_at"] = now
    return validate_lifecycle(ledger)


def canonical_state_root(repo_root: Path) -> Path:
    """Return the primary checkout shared by all linked worktrees."""
    completed = _run_git(repo_root, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    common = Path(completed.strip())
    if not common.is_absolute():
        common = (repo_root / common).resolve()
    if common.name != ".git":
        raise LifecycleError(f"cannot derive primary checkout from Git common directory: {common}")
    return common.parent.resolve()


def lifecycle_path(repo_root: Path, identity: Mapping[str, Any]) -> Path:
    canonical = task_identity.validate_identity(identity)
    issue = canonical.get("github_issue_number")
    if issue is None:
        raise LifecycleError("lifecycle path requires a GitHub issue")
    repository_digest = hashlib.sha256(canonical["repository"].encode("utf-8")).hexdigest()[:16]
    return canonical_state_root(repo_root) / ".agent" / "task-lifecycle" / repository_digest / f"issue-{issue}.json"


def load_lifecycle(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LifecycleError(f"lifecycle ledger not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"cannot read lifecycle ledger {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise LifecycleError("lifecycle ledger must contain a JSON object")
    return validate_lifecycle(payload)


def write_lifecycle(path: Path, payload: Mapping[str, Any]) -> None:
    ledger = validate_lifecycle(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@contextmanager
def lifecycle_lock(path: Path) -> Iterator[None]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def carrier_projection(payload: Mapping[str, Any], *, state_file: str | None = None) -> dict[str, Any]:
    ledger = validate_lifecycle(payload)
    receipts = ledger["observation_receipts"]
    return {
        "schema_version": "task-lifecycle-carrier.v1",
        "lifecycle_id": ledger["lifecycle_id"],
        "identity": ledger["identity"],
        "terminal_goal": ledger["terminal_goal"],
        "pr": ledger["pr"],
        "ac_snapshot": ledger["ac_snapshot"],
        "remaining_scope": ledger["remaining_scope"],
        "current_state": ledger["current_state"],
        "latest_receipt_id": receipts[-1]["id"] if receipts else None,
        "state_file": state_file,
    }


def render_carrier_prompt(carrier: Mapping[str, Any]) -> str:
    return (
        "\n[task lifecycle — authoritative carrier]\n"
        "This task is bound to the following shared lifecycle ledger. Preserve it through "
        "delegation and final receipts; do not infer completion from worker status alone.\n"
        f"{json.dumps(dict(carrier), ensure_ascii=False, sort_keys=True)}\n"
    )


def _run_git(repo_root: Path, args: list[str]) -> str:
    import subprocess

    completed = subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "git command failed").strip()
        raise LifecycleError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def protected_paths(paths: list[str]) -> list[str]:
    return sorted(
        {
            path
            for path in paths
            if any(fnmatch.fnmatch(path, pattern) for pattern in PROTECTED_PATH_PATTERNS)
        }
    )


def observe_local_git(
    repo_root: Path,
    *,
    head_sha: str | None,
    branch: str | None,
    worktree: str | None,
) -> dict[str, Any]:
    """Collect deterministic local Git/worktree closeout facts.

    Missing post-merge refs are expected.  Pre-merge hygiene remains durable in
    the earlier observation receipt; post-merge collection focuses on cleanup.
    """
    root = repo_root.resolve()
    primary = canonical_state_root(root)
    primary_clean = not bool(_run_git(primary, ["status", "--short"]))
    worktree_rows = _run_git(primary, ["worktree", "list", "--porcelain"]).splitlines()
    worktree_records: list[dict[str, str]] = []
    current_record: dict[str, str] = {}
    for line in [*worktree_rows, ""]:
        if not line:
            if current_record:
                worktree_records.append(current_record)
                current_record = {}
            continue
        key, _, value = line.partition(" ")
        current_record[key] = value
    resolved_worktree = str(Path(worktree).resolve()) if worktree else None
    selected_worktree = next(
        (
            record
            for record in worktree_records
            if resolved_worktree
            and str(Path(record.get("worktree", "")).resolve()) == resolved_worktree
        ),
        None,
    )
    worktree_present = selected_worktree is not None
    actual_worktree_branch = (
        str(selected_worktree.get("branch") or "").removeprefix("refs/heads/")
        if selected_worktree
        else None
    ) or None
    worktree_branch_matches = bool(
        worktree_present
        and actual_worktree_branch
        and (not branch or actual_worktree_branch == branch)
    )
    dispatch_worktree_used = bool(
        worktree_present
        and resolved_worktree
        and "/.worktrees/dispatch/" in resolved_worktree.replace("\\", "/")
        and Path(resolved_worktree).resolve() != primary
    )
    local_branch_present = False
    remote_branch_present = False
    if branch:
        local_branch_present = bool(
            _run_git(primary, ["for-each-ref", "--format=%(refname)", f"refs/heads/{branch}"])
        )
        remote_branch_present = bool(
            _run_git(primary, ["for-each-ref", "--format=%(refname)", f"refs/remotes/origin/{branch}"])
        )

    commits: list[dict[str, Any]] = []
    changed_paths: list[str] = []
    if head_sha:
        try:
            base = _run_git(root, ["merge-base", "origin/main", head_sha])
            changed_raw = _run_git(root, ["diff", "--name-only", f"{base}..{head_sha}"])
            changed_paths = [line for line in changed_raw.splitlines() if line]
            log = _run_git(root, ["log", "--format=%H%x1f%B%x1e", f"{base}..{head_sha}"])
            for record in log.split("\x1e"):
                if not record.strip() or "\x1f" not in record:
                    continue
                sha, message = record.strip().split("\x1f", 1)
                trailers = [
                    line.strip()
                    for line in message.splitlines()
                    if line.strip().lower().startswith("x-agent:")
                ]
                commits.append({"sha": sha, "x_agent_trailers": trailers})
        except LifecycleError:
            # The immutable pre-merge receipt remains the authority for hygiene
            # when squash merge/branch deletion makes the old comparison absent.
            pass
    return {
        "primary_checkout": str(primary),
        "primary_clean": primary_clean,
        "dispatch_worktree_used": dispatch_worktree_used,
        "worktree": resolved_worktree,
        "worktree_present": worktree_present,
        "actual_worktree_branch": actual_worktree_branch,
        "worktree_branch_matches": worktree_branch_matches,
        "branch": branch,
        "local_branch_present": local_branch_present,
        "remote_branch_present": remote_branch_present,
        "commits": commits,
        "changed_paths": changed_paths,
        "forbidden_paths": protected_paths(changed_paths),
    }


def _observation_material(observation: Any) -> Any:
    if isinstance(observation, dict):
        return {
            key: _observation_material(value)
            for key, value in observation.items()
            if key not in {"observed_at", "generated_at"}
        }
    if isinstance(observation, list):
        return [_observation_material(value) for value in observation]
    return observation


def _ledger_projection_material(ledger: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "lifecycle_id": ledger["lifecycle_id"],
        "terminal_goal": ledger["terminal_goal"],
        "pr": ledger["pr"],
        "ac_hash": ledger["ac_snapshot"]["content_hash"],
        "evidence_ids": [item["id"] for item in ledger["evidence"]],
        "remaining_scope": ledger["remaining_scope"],
        "required_checks": ledger["required_checks"],
    }


def _behavior_proof_reference_error(
    record: Mapping[str, Any], *, head_sha: str | None
) -> str | None:
    try:
        reference = _validate_behavior_proof_reference_shape(record["details"])
    except LifecycleError as exc:
        return str(exc)
    target_sha = reference["target_sha"]
    if head_sha and target_sha != head_sha:
        return "behavior-proof receipt is not bound to the current PR head"
    path = Path(reference["receipt_path"]).expanduser()
    try:
        receipt_bytes = path.read_bytes()
        receipt = json.loads(receipt_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        return f"behavior-proof receipt is unreadable: {exc}"
    actual_digest = "sha256:" + hashlib.sha256(receipt_bytes).hexdigest()
    if actual_digest != reference["receipt_sha256"]:
        return "behavior-proof receipt digest does not match the referenced file"
    if not isinstance(receipt, dict) or receipt.get("schema_version") != "code-review-receipt.v1":
        return "behavior-proof reference is not a canonical code-review receipt"
    target = receipt.get("target")
    if not isinstance(target, dict):
        return "behavior-proof receipt has no canonical target"
    if target.get("head_sha") != target_sha:
        return "behavior-proof receipt target SHA does not match the evidence reference"
    if target.get("input_sha256") != reference["input_sha256"]:
        return "behavior-proof receipt target-input fingerprint does not match the reference"
    if receipt.get("final_disposition") != "clean" or receipt.get("exit_code") != 0:
        return "behavior-proof receipt is not a clean canonical closeout"
    author = receipt.get("author") or {}
    reviewer = receipt.get("reviewer") or {}
    if not author.get("family") or not reviewer.get("family"):
        return "behavior-proof receipt lacks concrete author/reviewer families"
    if str(author["family"]).lower() == str(reviewer["family"]).lower():
        return "behavior-proof receipt is not outside the author model family"
    proof = receipt.get("behavior_proof")
    if not isinstance(proof, dict) or proof.get("schema_version") != "behavior-proof.v1":
        return "behavior-proof receipt lacks the canonical behavior-proof.v1 envelope"
    for surface_name in ("source_aware", "source_blind"):
        surface = proof.get(surface_name)
        if not isinstance(surface, dict) or surface.get("status") not in {"pass", "n/a"}:
            return f"behavior-proof receipt has no passing/applicable {surface_name} surface"
        if surface["status"] == "n/a":
            reason = str(surface.get("reason") or surface.get("rationale") or "").strip()
            if not reason:
                return f"behavior-proof receipt has an unexplained n/a {surface_name} surface"
        if surface["status"] == "pass":
            clauses = surface.get("clauses")
            if not isinstance(clauses, list) or not any(
                isinstance(clause, dict)
                and clause.get("target_input_sha256") == reference["input_sha256"]
                for clause in clauses
            ):
                return f"behavior-proof receipt {surface_name} clauses are not target-bound"
    return None


def _evidence_status(
    ledger: Mapping[str, Any],
    *,
    head_sha: str | None,
    comment_urls: set[str],
) -> tuple[dict[str, set[str]], list[str]]:
    valid: dict[str, set[str]] = {}
    invalid: list[str] = []
    for record in ledger["evidence"]:
        kind = record["type"]
        commit = record["subject"]["commit"]
        if kind in CURRENT_HEAD_EVIDENCE and head_sha and commit != head_sha:
            invalid.append(f"{record['ac_id']}: {kind} evidence is not bound to current PR head")
            continue
        if kind == "behavior_proof":
            reference_error = _behavior_proof_reference_error(record, head_sha=head_sha)
            if reference_error:
                invalid.append(f"{record['ac_id']}: {reference_error}")
                continue
        if kind == "review" and (not record["url"] or record["url"] not in comment_urls):
            invalid.append(f"{record['ac_id']}: review receipt URL is absent from authoritative PR comments")
            continue
        valid.setdefault(record["ac_id"], set()).add(kind)
    return valid, invalid


def _criteria_due_blockers(
    ledger: Mapping[str, Any],
    valid_evidence: Mapping[str, set[str]],
    *,
    target_state: str,
) -> list[str]:
    target_rank = STATE_RANK[target_state]
    blockers: list[str] = []
    for item in ledger["ac_snapshot"]["criteria"]:
        if not item["applicable"] or STATE_RANK[item["due_state"]] > target_rank:
            continue
        missing = sorted(set(item["required_evidence"]) - valid_evidence.get(item["id"], set()))
        if missing:
            blockers.append(f"{item['id']}: missing typed evidence {', '.join(missing)}")
    return blockers


def _latest_premerge_local(ledger: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for receipt in reversed(ledger["observation_receipts"]):
        local = (receipt.get("observation") or {}).get("local")
        if not isinstance(local, dict):
            continue
        if (
            local.get("dispatch_worktree_used")
            and local.get("worktree_present")
            and local.get("worktree_branch_matches")
            and local.get("commits")
        ):
            return local
    return None


def _local_readiness(local: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not local.get("primary_clean"):
        blockers.append("primary checkout is not clean")
    if not local.get("dispatch_worktree_used"):
        blockers.append("implementation was not observed in a dispatch worktree")
    if not local.get("worktree_present"):
        blockers.append("the claimed dispatch worktree was absent from git worktree list")
    if not local.get("worktree_branch_matches"):
        blockers.append("the claimed dispatch worktree branch did not match Git authority")
    commits = local.get("commits") or []
    if not commits:
        blockers.append("no task commits were available for X-Agent validation")
    for commit in commits:
        trailers = commit.get("x_agent_trailers") or []
        if len(trailers) != 1 or not str(trailers[0]).split(":", 1)[-1].strip():
            blockers.append(f"commit {commit.get('sha', 'unknown')} lacks exactly one valid X-Agent trailer")
    forbidden = local.get("forbidden_paths") or []
    if forbidden:
        blockers.append(f"forbidden/generated paths changed: {', '.join(forbidden)}")
    return blockers


def _review_passed(ledger: Mapping[str, Any], valid_evidence: Mapping[str, set[str]]) -> bool:
    review_records = [record for record in ledger["evidence"] if record["type"] == "review"]
    return any("review" in valid_evidence.get(record["ac_id"], set()) for record in review_records)


def _checks_status(required: list[str], checks: list[Mapping[str, Any]]) -> tuple[bool, bool, list[str]]:
    by_name: dict[str, Mapping[str, Any]] = {}
    for check in checks:
        by_name[str(check.get("name") or "")] = check
    missing = [name for name in required if name not in by_name]
    pending = [name for name in required if name in by_name and by_name[name].get("status") != "COMPLETED"]
    failed = [
        name
        for name in required
        if name in by_name
        and by_name[name].get("status") == "COMPLETED"
        and by_name[name].get("conclusion") not in {"SUCCESS", "NEUTRAL", "SKIPPED"}
    ]
    return not (missing or pending or failed), bool(pending or missing), failed


def evaluate(payload: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    ledger = validate_lifecycle(payload)
    if observation.get("schema_version") != OBSERVATION_SCHEMA_VERSION:
        raise LifecycleError("unsupported closeout observation schema")
    github = observation.get("github")
    local = observation.get("local")
    if not isinstance(github, Mapping) or not isinstance(local, Mapping):
        raise LifecycleError("observation requires github and local objects")
    issue = github.get("issue") or {}
    pr = github.get("pr") or {}
    identity = ledger["identity"]
    hard: list[str] = []
    waiting: list[str] = []
    actions: list[str] = []
    last_success = "ISSUE_LINKED"

    if github.get("error"):
        hard.append(f"GitHub observation failed: {github['error']}")

    if github.get("repository") != identity["repository"]:
        hard.append("authoritative GitHub repository does not match task identity")
    registered_epics = github.get("registered_stream_epics")
    if not isinstance(registered_epics, list) or identity["stream_epic"] not in registered_epics:
        hard.append("identity stream epic is absent from the registered issue-stream epics")
    if issue.get("number") != identity["github_issue_number"]:
        hard.append("authoritative GitHub issue does not match task identity")
    if issue.get("url") != identity["github_issue_url"]:
        hard.append("authoritative GitHub issue URL does not match task identity")
    if issue.get("parent_epic") != identity["stream_epic"]:
        hard.append("issue is not linked to the identity's exact registered stream epic")

    issue_criteria: list[dict[str, Any]] = []
    try:
        issue_criteria = parse_issue_acceptance_criteria(str(issue.get("body") or ""))
    except LifecycleError as exc:
        hard.append(str(exc))
    if issue_criteria:
        snapshot_projection = [
            {"id": item["id"], "text": item["text"]}
            for item in ledger["ac_snapshot"]["criteria"]
        ]
        issue_projection = [{"id": item["id"], "text": item["text"]} for item in issue_criteria]
        if issue_projection != snapshot_projection:
            hard.append("issue acceptance criteria drift from the immutable AC snapshot")
        else:
            last_success = "ACS_FINALIZED"

    expected_pr = ledger["pr"]["number"]
    head_sha = pr.get("head_sha") if isinstance(pr, Mapping) else None
    comment_urls = {
        str(comment.get("url"))
        for comment in github.get("comments") or []
        if isinstance(comment, Mapping) and comment.get("url")
    }
    valid_evidence, invalid_evidence = _evidence_status(
        ledger, head_sha=head_sha, comment_urls=comment_urls
    )
    hard.extend(invalid_evidence)

    readiness_local = local
    prior_local = _latest_premerge_local(ledger)
    if prior_local is not None and (
        not local.get("commits")
        or not local.get("worktree_present")
        or not local.get("worktree_branch_matches")
    ):
        readiness_local = prior_local
    readiness_blockers = _local_readiness(readiness_local)
    readiness_blockers.extend(
        _criteria_due_blockers(ledger, valid_evidence, target_state="IMPLEMENTATION_READY")
    )
    if not readiness_blockers and last_success == "ACS_FINALIZED":
        last_success = "IMPLEMENTATION_READY"
    elif last_success == "ACS_FINALIZED":
        hard.extend(readiness_blockers)

    if expected_pr is None:
        waiting.append("PR is not yet bound to the lifecycle ledger")
        actions.append("bind the exact PR number")
    elif pr.get("number") != expected_pr or pr.get("url") != ledger["pr"]["url"]:
        hard.append("authoritative PR does not match the lifecycle binding")
    else:
        pr_state = str(pr.get("state") or "").upper()
        if pr_state == "OPEN":
            last_success = "PR_OPEN"
            if pr.get("is_draft"):
                waiting.append("PR remains a draft")
                actions.append("mark the PR ready for review before requesting the gate")
        requested_changes = bool(pr.get("requested_changes"))
        if requested_changes:
            last_success = "CHANGES_REQUESTED"
            hard.append("unresolved requested changes remain on the PR")
            actions.append("address requested changes and obtain fresh current-head review")
        elif pr_state == "OPEN":
            review_ok = _review_passed(ledger, valid_evidence)
            if not review_ok:
                last_success = "REVIEW_REQUESTED"
                waiting.append("independent outside-author-family review is pending")
                actions.append("record a current-head outside-family review receipt")
            else:
                review_due = _criteria_due_blockers(
                    ledger, valid_evidence, target_state="REVIEW_PASSED"
                )
                if review_due:
                    hard.extend(review_due)
                else:
                    last_success = "REVIEW_PASSED"
                    auto_enabled = pr.get("auto_merge_enabled_at")
                    review_times = [
                        record["recorded_at"]
                        for record in ledger["evidence"]
                        if record["type"] == "review"
                        and "review" in valid_evidence.get(record["ac_id"], set())
                    ]
                    if auto_enabled and review_times and auto_enabled < max(review_times):
                        hard.append("auto-merge was armed before the verified review gate")
                checks_ok, checks_waiting, checks_failed = _checks_status(
                    ledger["required_checks"], list(pr.get("checks") or [])
                )
                if checks_failed:
                    hard.append(f"required CI failed: {', '.join(checks_failed)}")
                elif checks_waiting:
                    waiting.append("required CI is pending")
                elif checks_ok:
                    ci_due = _criteria_due_blockers(
                        ledger, valid_evidence, target_state="CI_PASSED"
                    )
                    if ci_due:
                        hard.extend(ci_due)
                    else:
                        last_success = "CI_PASSED"
                        waiting.append("reviewed green PR remains open")
                        actions.append("arm or await auto-merge, then reconcile the merged PR")

        if pr_state == "MERGED":
            review_ok = _review_passed(ledger, valid_evidence)
            checks_ok, checks_waiting, checks_failed = _checks_status(
                ledger["required_checks"], list(pr.get("checks") or [])
            )
            if not review_ok:
                hard.append("merged PR lacks verified current-head outside-family review")
            else:
                auto_enabled = pr.get("auto_merge_enabled_at")
                review_times = [
                    record["recorded_at"]
                    for record in ledger["evidence"]
                    if record["type"] == "review"
                    and "review" in valid_evidence.get(record["ac_id"], set())
                ]
                if auto_enabled and review_times and auto_enabled < max(review_times):
                    hard.append("auto-merge was armed before the verified review gate")
            if checks_failed:
                hard.append(f"merged PR has failed required CI: {', '.join(checks_failed)}")
            elif checks_waiting:
                waiting.append("merged PR still has pending required CI")
            if not pr.get("merge_sha"):
                hard.append("GitHub reports merged PR without a merge commit")
            elif review_ok and checks_ok:
                review_due = _criteria_due_blockers(
                    ledger, valid_evidence, target_state="REVIEW_PASSED"
                )
                ci_due = _criteria_due_blockers(
                    ledger, valid_evidence, target_state="CI_PASSED"
                )
                merged_due = _criteria_due_blockers(
                    ledger, valid_evidence, target_state="MERGED"
                )
                boundary_due = list(dict.fromkeys([*review_due, *ci_due, *merged_due]))
                if boundary_due:
                    hard.extend(boundary_due)
                else:
                    last_success = "MERGED"
        elif pr_state == "CLOSED":
            hard.append("PR closed without merge")

    goal = ledger["terminal_goal"]
    deployments = github.get("deployments") or []
    deployed = any(
        item.get("state") == "SUCCESS" and item.get("sha") in {pr.get("merge_sha"), pr.get("head_sha")}
        for item in deployments
        if isinstance(item, Mapping)
    )
    if last_success == "MERGED" and goal in {"deploy", "certify"}:
        if deployed:
            deploy_due = _criteria_due_blockers(
                ledger, valid_evidence, target_state="DEPLOYED"
            )
            if deploy_due:
                hard.extend(deploy_due)
            else:
                last_success = "DEPLOYED"
        else:
            waiting.append("terminal goal requires deployment")
            actions.append("deploy the merged commit and record authoritative evidence")
    certified = any(
        record["type"] == "certification"
        and "certification" in valid_evidence.get(record["ac_id"], set())
        for record in ledger["evidence"]
    )
    if last_success == "DEPLOYED" and goal == "certify":
        if certified:
            certify_due = _criteria_due_blockers(
                ledger, valid_evidence, target_state="CERTIFIED"
            )
            if certify_due:
                hard.extend(certify_due)
            else:
                last_success = "CERTIFIED"
        else:
            waiting.append("terminal goal requires certification")
            actions.append("record certification evidence bound to the deployed commit")

    remote_goal_state = {"merge": "MERGED", "deploy": "DEPLOYED", "certify": "CERTIFIED"}[goal]
    goal_reached = STATE_RANK.get(last_success, -1) >= STATE_RANK[remote_goal_state]
    remaining = ledger["remaining_scope"]
    if remaining["status"] == "open":
        hard.append("remaining scope is open and has not been transferred")
        actions.append("create and reciprocally link a single-stream follow-up issue")
    elif remaining["status"] == "transferred":
        follow_up = github.get("follow_up") or {}
        if follow_up.get("number") != remaining["follow_up_issue"]:
            hard.append("authoritative follow-up issue does not match transferred scope")
        if follow_up.get("parent_epic") != remaining["follow_up_stream_epic"]:
            hard.append("follow-up issue does not have the exact transferred stream epic")
        if remaining["follow_up_stream_epic"] not in (registered_epics or []):
            hard.append("follow-up issue epic is absent from the registered issue-stream epics")
        if not follow_up.get("reciprocal_links_verified"):
            hard.append("original and follow-up issues are not reciprocally linked")

    checked = {item["id"]: item["checked"] for item in issue_criteria}
    preclose_missing = _criteria_due_blockers(
        ledger, valid_evidence, target_state=remote_goal_state
    )
    preclose_unchecked = [
        item["id"]
        for item in ledger["ac_snapshot"]["criteria"]
        if item["applicable"]
        and STATE_RANK[item["due_state"]] <= STATE_RANK[remote_goal_state]
        and not checked.get(item["id"], False)
    ]
    if str(issue.get("state") or "").upper() == "CLOSED":
        if not goal_reached or preclose_missing or preclose_unchecked or remaining["status"] == "open":
            hard.append("issue closed before terminal goal and pre-close AC proof were complete")
        else:
            last_success = "ISSUE_CLOSED"
            close_due = _criteria_due_blockers(
                ledger, valid_evidence, target_state="ISSUE_CLOSED"
            )
            if close_due:
                hard.extend(close_due)
    elif goal_reached:
        waiting.append("merged/deployed work is not yet reconciled to an actually closed issue")
        actions.append("sync evidenced AC checkboxes, then explicitly close the issue")

    cleanup_ok = (
        not local.get("worktree_present")
        and not local.get("local_branch_present")
        and not local.get("remote_branch_present")
    )
    if last_success == "ISSUE_CLOSED":
        if cleanup_ok:
            cleanup_due = _criteria_due_blockers(
                ledger, valid_evidence, target_state="CLEANED_UP"
            )
            all_unchecked = [
                item["id"]
                for item in ledger["ac_snapshot"]["criteria"]
                if item["applicable"] and not checked.get(item["id"], False)
            ]
            if cleanup_due:
                hard.extend(cleanup_due)
            if all_unchecked:
                hard.append(f"applicable issue ACs remain unchecked: {', '.join(all_unchecked)}")
            if not cleanup_due and not all_unchecked:
                last_success = "CLEANED_UP"
        else:
            waiting.append("merged task branch or dispatch worktree still requires cleanup")
            actions.append("remove the exact worktree and local/remote task branches")

    if hard and not actions:
        actions.append(
            f"owner {ledger['author_family']}: resolve the listed hard blockers and reconcile again"
        )
    if hard:
        state = "BLOCKED_WITH_RECEIPT"
        disposition = "blocked"
    else:
        state = last_success
        if state == "CLEANED_UP":
            disposition = "complete"
        elif waiting:
            disposition = "waiting"
        else:
            disposition = "ready"
    return {
        "state": state,
        "last_success_state": last_success,
        "disposition": disposition,
        "hard_blockers": list(dict.fromkeys(hard)),
        "waiting": list(dict.fromkeys(waiting)),
        "next_actions": list(dict.fromkeys(actions)),
        "valid_evidence": {key: sorted(value) for key, value in valid_evidence.items()},
        "preclose_missing_evidence": preclose_missing,
        "preclose_unchecked": preclose_unchecked,
        "goal_reached": goal_reached,
    }


def reconcile(
    payload: Mapping[str, Any],
    observation: Mapping[str, Any],
    *,
    now: str,
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    ledger = validate_lifecycle(payload)
    result = evaluate(ledger, observation)
    observation_digest = digest(_observation_material(observation))
    receipt_material = {
        "observation_digest": observation_digest,
        "observed_at": str(observation.get("observed_at") or now),
        "owner": ledger["author_family"],
        "state": result["state"],
        "disposition": result["disposition"],
        "hard_blockers": result["hard_blockers"],
        "waiting": result["waiting"],
        "next_actions": result["next_actions"],
        "observation": {
            **deepcopy(dict(observation)),
            "projection": {
                "last_success_state": result["last_success_state"],
                "goal_reached": result["goal_reached"],
                "valid_evidence": result["valid_evidence"],
            },
        },
    }
    replay_key = digest(
        {
            "observation": observation_digest,
            "ledger": _ledger_projection_material(ledger),
            "result": {
                key: receipt_material[key]
                for key in ("state", "disposition", "hard_blockers", "waiting", "next_actions")
            },
        }
    )
    for existing in ledger["observation_receipts"]:
        existing_key = (existing.get("observation") or {}).get("replay_key")
        if existing_key == replay_key:
            return ledger, existing, True
    receipt_material["observation"]["replay_key"] = replay_key
    receipt = {"id": digest(receipt_material), **receipt_material}
    ledger["observation_receipts"].append(receipt)
    ledger["current_state"] = result["state"]
    ledger["updated_at"] = now
    return validate_lifecycle(ledger), receipt, False


def mutation_operation_id(payload: Mapping[str, Any], action: str) -> str:
    ledger = validate_lifecycle(payload)
    if action not in {"sync-acs", "arm-auto-merge", "close-issue"}:
        raise LifecycleError(f"unsupported mutation action: {action}")
    return digest(
        {
            "lifecycle_id": ledger["lifecycle_id"],
            "action": action,
            "pr": ledger["pr"],
            "ac_hash": ledger["ac_snapshot"]["content_hash"],
            "evidence_ids": [item["id"] for item in ledger["evidence"]],
            "remaining_scope": ledger["remaining_scope"],
        }
    )


def mutation_status(payload: Mapping[str, Any], operation_id: str) -> str | None:
    ledger = validate_lifecycle(payload)
    events = [event for event in ledger["mutation_receipts"] if event["operation_id"] == operation_id]
    return events[-1]["status"] if events else None


def append_mutation_event(
    payload: Mapping[str, Any],
    *,
    operation_id: str,
    action: str,
    status: str,
    authorized_by: str,
    requested_at: str,
    completed_at: str | None,
    remote_mutation_performed: bool,
    detail: str,
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    ledger = validate_lifecycle(payload)
    event_material = {
        "operation_id": operation_id,
        "action": action,
        "status": status,
        "authorized_by": _clean_text(authorized_by, "mutation authorizer", maximum=200),
        "requested_at": requested_at,
        "completed_at": completed_at,
        "remote_mutation_performed": remote_mutation_performed,
        "detail": " ".join(detail.split()),
    }
    event = {"id": digest(event_material), **event_material}
    for existing in ledger["mutation_receipts"]:
        if existing["id"] == event["id"]:
            return ledger, existing, True
    ledger["mutation_receipts"].append(event)
    ledger["updated_at"] = completed_at or requested_at
    return validate_lifecycle(ledger), event, False


def migrate_legacy(
    payload: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
    policy: Mapping[str, Mapping[str, Any]],
    issue_body: str,
    required_checks: list[str],
    author_family: str,
    now: str,
) -> dict[str, Any]:
    """Migrate an older unversioned ledger without rewriting proof history."""
    if payload.get("schema_version") == SCHEMA_VERSION:
        return validate_lifecycle(payload)
    snapshot = build_ac_snapshot(issue_body, policy, finalized_at=now)
    migrated = build_lifecycle(
        identity,
        author_family=author_family,
        ac_snapshot=snapshot,
        required_checks=required_checks,
        now=now,
        pr_number=payload.get("pr_number"),
        migration_source=str(payload.get("schema_version") or "unversioned"),
        legacy=True,
    )
    for key in ("evidence", "observation_receipts", "mutation_receipts"):
        value = payload.get(key)
        if isinstance(value, list):
            migrated[key] = deepcopy(value)
    migrated["updated_at"] = now
    return validate_lifecycle(migrated)
