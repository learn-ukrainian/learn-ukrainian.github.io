"""Atlas VPS job protocol: plan → submit → status → close (always a result).

**systemd on the host is truth; the local registry is a journal/mirror.**

Batch kinds run on atlas-runner only. Registry lives under batch_state/atlas-jobs/
(restic-covered). Close writes a fail-closed result receipt; large artifacts go
through durable_mirror + backup-data.sh. Publish/pointer flip is never this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

SCHEMA = "atlas-job.v1"
RESULT_SCHEMA = "atlas-job-result.v1"
BATCH_KINDS = frozenset({"reenrich"})
ALLOWED_HOSTS = {"reenrich": frozenset({"atlas-runner"})}
HRAMATKA_ALIASES = frozenset({"hramatka", "vps"})
RESULT_SINKS = frozenset({"git", "restic", "both"})
RESUME_MODES = frozenset({"idempotent", "checkpoint", "never"})
DRIVER_NEEDLES = (
    "reenrich_thin_manifest_entries",
    "migrate_slovnyk",
    "enrich_offline_20k",
)
SUMMARY_REQUIRED_KEYS = frozenset(
    {
        "targets",
        "consecutive_misses",
        "filled_translation",
        "circuit_breaker_tripped",
    }
)
GIT_RECEIPT_ALLOWLIST = frozenset(
    {
        "schema",
        "id",
        "state",
        "host",
        "unit",
        "kind",
        "closed_at",
        "summary",
        "pulled",
        "backup",
        "delivery",
        "issue",
        "git_pr",
        "workdir",
        "plan_sha256",
        "denominator",
        "exit_status",
    }
)
GIT_RECEIPT_MAX_BYTES = 10_240
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
_ABS_PATH = re.compile(r"(^|[\s\"'])/(?:Users|home|var|tmp|opt|etc)/")
_CRED_HINT = re.compile(
    r"(?i)(password|secret|api[_-]?key|token|authorization|private[_-]?key)\s*[:=]"
)
_HOSTNAME_HINT = re.compile(
    r"(?i)\b(?:[a-z0-9-]+\.)+(?:internal|local|lan|corp|example)\b|\b\d{1,3}(?:\.\d{1,3}){3}\b"
)
DEFAULT_TIMEOUT_SECONDS = 86400
DEFAULT_RUN_ROOT = "/home/ops/atlas-runner"

_HOST = None  # set via set_host_adapter(); typed as HostAdapter | None


class HostAdapter(Protocol):
    """Host-side truth for atlas-job-* units (injectable for hermetic tests)."""

    def list_atlas_job_units(self, host: str) -> list[dict[str, Any]]:
        """Return unit rows: name, active, sub, main_pid."""

    def read_exit_status(self, host: str, work_dir: str) -> dict[str, Any] | None:
        """Read work_dir/exit-status.json from the host, if present."""

    def pgrep_drivers(self, host: str) -> list[str]:
        """Secondary orphan signal: pgrep driver command lines."""

    def reachable(self, host: str) -> bool:
        """True when SSH (or fake) host checks can run."""


@dataclass
class FakeHostAdapter:
    """In-memory host adapter for unit tests (fail-closed by default)."""

    units: list[dict[str, Any]] = field(default_factory=list)
    exit_status_by_workdir: dict[str, dict[str, Any]] = field(default_factory=dict)
    pgrep_lines: list[str] = field(default_factory=list)
    online: bool = True

    def list_atlas_job_units(self, host: str) -> list[dict[str, Any]]:
        del host
        if not self.online:
            raise ConnectionError("host unreachable")
        return list(self.units)

    def read_exit_status(self, host: str, work_dir: str) -> dict[str, Any] | None:
        del host
        if not self.online:
            raise ConnectionError("host unreachable")
        return self.exit_status_by_workdir.get(work_dir)

    def pgrep_drivers(self, host: str) -> list[str]:
        del host
        if not self.online:
            raise ConnectionError("host unreachable")
        return list(self.pgrep_lines)

    def reachable(self, host: str) -> bool:
        del host
        return self.online


class SshHostAdapter:
    """Production adapter: BatchMode SSH to the named host alias."""

    def list_atlas_job_units(self, host: str) -> list[dict[str, Any]]:
        remote = (
            "systemctl --user list-units 'atlas-job-*.service' --all --no-legend --no-pager "
            "--plain 2>/dev/null || true"
        )
        proc = _ssh(host, remote)
        if proc.returncode not in {0, 1}:
            raise ConnectionError(f"systemctl list-units failed on {host}: rc={proc.returncode}")
        rows: list[dict[str, Any]] = []
        for line in (proc.stdout or "").splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            name, _load, active, sub = parts[0], parts[1], parts[2], parts[3]
            if not name.startswith("atlas-job-"):
                continue
            main_pid = self._main_pid(host, name)
            rows.append(
                {
                    "name": name,
                    "active": active,
                    "sub": sub,
                    "main_pid": main_pid,
                }
            )
        return rows

    def _main_pid(self, host: str, unit: str) -> int | None:
        proc = _ssh(
            host,
            f"systemctl --user show {unit} --property=MainPID --value 2>/dev/null || true",
        )
        text = (proc.stdout or "").strip()
        if text.isdigit() and int(text) > 0:
            return int(text)
        return None

    def read_exit_status(self, host: str, work_dir: str) -> dict[str, Any] | None:
        remote = (
            "python3 - <<'PY'\n"
            "from pathlib import Path\n"
            f"p = Path({work_dir!r}) / 'exit-status.json'\n"
            "print(p.read_text() if p.is_file() else '')\n"
            "PY"
        )
        proc = _ssh(host, remote)
        if proc.returncode != 0:
            raise ConnectionError(f"exit-status read failed on {host}: rc={proc.returncode}")
        text = (proc.stdout or "").strip()
        if not text:
            return None
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("exit-status.json must be an object")
        return data

    def pgrep_drivers(self, host: str) -> list[str]:
        remote = (
            "pgrep -af 'reenrich_thin_manifest_entries|migrate_slovnyk|enrich_offline_20k' || true"
        )
        proc = _ssh(host, remote)
        if proc.returncode not in {0, 1}:
            raise ConnectionError(f"pgrep failed on {host}: rc={proc.returncode}")
        return (proc.stdout or "").splitlines()

    def reachable(self, host: str) -> bool:
        proc = _ssh(host, "true")
        return proc.returncode == 0


def _ssh(host: str, remote: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=12", host, remote],
        capture_output=True,
        text=True,
        check=False,
    )


def get_host_adapter() -> HostAdapter:
    return _HOST if _HOST is not None else SshHostAdapter()


def set_host_adapter(adapter: HostAdapter | None) -> None:
    global _HOST
    _HOST = adapter


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def registry_dir() -> Path:
    override = os.environ.get("ATLAS_JOB_REGISTRY")
    if override:
        return Path(override)
    return repo_root() / "batch_state" / "atlas-jobs"


def require_safe_job_id(job_id: object) -> str:
    """Reject non-token job ids before any filesystem path join.

    Raises ValueError when ``job_id`` is not a str matching ``_SAFE_ID``.
    Returns the matched token (``Match.group(0)``), never the raw argument,
    so path joins are not fed a CodeQL-tainted string.
    """
    if not isinstance(job_id, str):
        raise ValueError("job_id must be a filesystem/systemd-safe token")
    matched = _SAFE_ID.fullmatch(job_id)
    if matched is None:
        raise ValueError("job_id must be a filesystem/systemd-safe token")
    return matched.group(0)


def _run_root() -> Path:
    return Path(os.environ.get("ATLAS_RUN_ROOT", DEFAULT_RUN_ROOT))


def _safe_id_token(part: str) -> str:
    """Return ``_SAFE_ID`` match text for a path segment, or raise."""
    matched = _SAFE_ID.fullmatch(part)
    if matched is None:
        raise ValueError("workdir must be a safe token path")
    return matched.group(0)


def require_safe_workdir(workdir: object) -> str:
    """Fail closed for plan/registry workdirs used in path and SSH contexts.

    Rejects ``..``, absolute paths outside ``ATLAS_RUN_ROOT`` / default run
    root, and any path whose segments are not ``_SAFE_ID`` tokens.
    Returns a newly constructed path from validated tokens (or
    ``str(resolved)`` for absolute paths under the run root), never the
    original relative ``workdir`` string.
    """
    if not isinstance(workdir, str) or not workdir:
        raise ValueError("workdir must be a non-empty safe token path")
    if "\0" in workdir:
        raise ValueError("workdir must not contain null bytes")
    raw = Path(workdir)
    if ".." in raw.parts:
        raise ValueError("workdir must not contain ..")
    run_root = _run_root().resolve()
    if raw.is_absolute():
        resolved = raw.resolve()
        try:
            rel = resolved.relative_to(run_root)
        except ValueError as exc:
            raise ValueError("workdir must be under ATLAS_RUN_ROOT") from exc
        if not rel.parts:
            raise ValueError("workdir must be a subdirectory of ATLAS_RUN_ROOT")
        safe_rel = [_safe_id_token(part) for part in rel.parts]
        return str(run_root.joinpath(*safe_rel))
    safe_parts: list[str] = []
    for part in raw.parts:
        if part in {".", ""}:
            raise ValueError("workdir must be a safe token path")
        safe_parts.append(_safe_id_token(part))
    return str(Path(*safe_parts))


def registry_path(job_id: str) -> Path:
    safe = require_safe_job_id(job_id)
    return registry_dir() / f"{safe}.json"


def result_path(job_id: str) -> Path:
    safe = require_safe_job_id(job_id)
    return registry_dir() / f"{safe}.result.json"


def git_receipt_path(job_id: str) -> Path:
    safe = require_safe_job_id(job_id)
    return registry_dir() / "receipts" / f"{safe}.json"


def restic_block_path() -> Path:
    return registry_dir() / ".restic-sink-blocked"


def unit_name(job_id: str) -> str:
    safe = require_safe_job_id(job_id)
    return f"atlas-job-{safe}.service"


def work_dir_for(job_id: str, plan: dict[str, Any] | None = None) -> str:
    safe = require_safe_job_id(job_id)
    if plan and isinstance(plan.get("workdir"), str) and plan["workdir"]:
        return require_safe_workdir(plan["workdir"])
    run_root = str(_run_root()).rstrip("/")
    return f"{run_root}/run-atlas-job-{safe}"


def local_pull_dir(job_id: str) -> Path:
    safe = require_safe_job_id(job_id)
    return registry_dir() / "pulled" / safe


def mirror_dir_for(job_id: str) -> Path:
    safe = require_safe_job_id(job_id)
    return repo_root() / "data" / "lexicon" / "runner-mirror" / safe


def load_plan(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("plan must be a JSON object")
    return data


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    job_id = plan.get("id")
    if not isinstance(job_id, str) or _SAFE_ID.fullmatch(job_id) is None:
        errors.append("id must be a filesystem/systemd-safe token")
    host = plan.get("host")
    if host not in {"atlas-runner", "hramatka"}:
        errors.append("host must be atlas-runner or hramatka")
    kind = plan.get("kind")
    if kind not in BATCH_KINDS:
        errors.append(f"kind must be one of {sorted(BATCH_KINDS)}")
    elif host is not None and host not in ALLOWED_HOSTS[kind]:
        errors.append(f"kind {kind} cannot run on {host}")
    if host in HRAMATKA_ALIASES and kind in BATCH_KINDS:
        errors.append("batch kinds must not target hramatka/vps")
    if plan.get("pointer_write") is not False:
        errors.append("pointer_write must be false (publish is a separate gate)")
    sink = plan.get("result_sink")
    if sink not in RESULT_SINKS:
        errors.append("result_sink must be git, restic, or both")
    denom = plan.get("denominator")
    if not isinstance(denom, int) or isinstance(denom, bool) or denom < 0:
        errors.append("denominator must be an integer >= 0")
    success = plan.get("success")
    if not isinstance(success, dict):
        errors.append("success must be an object")
    else:
        if "circuit_breaker" not in success:
            errors.append("success.circuit_breaker is required")
        if "min_filled" not in success:
            errors.append("success.min_filled is required")
    args = plan.get("args", [])
    if args is not None and not (
        isinstance(args, list) and all(isinstance(a, str) for a in args)
    ):
        errors.append("args must be a list of strings")
    slugs = plan.get("slugs_file")
    if slugs is not None and not isinstance(slugs, str):
        errors.append("slugs_file must be a string path when set")
    issue = plan.get("issue")
    if not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0:
        errors.append("issue must be a positive GitHub campaign/kind issue number")
    resume = plan.get("resume", "never")
    if resume not in RESUME_MODES:
        errors.append(f"resume must be one of {sorted(RESUME_MODES)}")
    timeout = plan.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        errors.append("timeout_seconds must be a positive integer")
    workdir = plan.get("workdir")
    if workdir is not None:
        try:
            require_safe_workdir(workdir)
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def save_registry(row: dict[str, Any]) -> Path:
    registry_dir().mkdir(parents=True, exist_ok=True)
    path = registry_path(str(row["id"]))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def load_registry(job_id: str) -> dict[str, Any] | None:
    path = registry_path(require_safe_job_id(job_id))
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"corrupt registry row: {path}")
    return data


def list_registry() -> list[dict[str, Any]]:
    root = registry_dir()
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        if path.name.endswith(".result.json"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rows.append(data)
    return rows


def restic_sink_blocked() -> bool:
    return restic_block_path().is_file()


def set_restic_sink_blocked(reason: str) -> None:
    registry_dir().mkdir(parents=True, exist_ok=True)
    restic_block_path().write_text(
        json.dumps({"blocked_at": _now(), "reason": reason}, indent=2) + "\n",
        encoding="utf-8",
    )


def clear_restic_sink_blocked() -> None:
    path = restic_block_path()
    if path.is_file():
        path.unlink()


def running_on_host(host: str) -> list[dict[str, Any]]:
    return [r for r in list_registry() if r.get("host") == host and r.get("state") == "running"]


def active_host_units(host: str, adapter: HostAdapter | None = None) -> list[dict[str, Any]]:
    host_adapter = adapter or get_host_adapter()
    units = host_adapter.list_atlas_job_units(host)
    return [
        u
        for u in units
        if u.get("active") in {"active", "activating", "reloading"}
        or str(u.get("sub", "")).startswith("running")
    ]


def summary_has_evidence(summary: dict[str, Any] | None) -> bool:
    if not isinstance(summary, dict) or not summary:
        return False
    return SUMMARY_REQUIRED_KEYS.issubset(summary.keys())


def interpret_summary(summary: dict[str, Any], plan: dict[str, Any]) -> str:
    """Map a launcher summary onto succeeded|failed."""
    if summary.get("circuit_breaker_tripped"):
        return "failed"
    targets = summary.get("targets")
    misses = summary.get("consecutive_misses")
    if isinstance(targets, int) and isinstance(misses, int) and targets > 0 and misses == targets:
        return "failed"
    filled = summary.get("filled_translation")
    min_filled = (plan.get("success") or {}).get("min_filled", 0)
    if isinstance(filled, int) and isinstance(min_filled, int) and filled < min_filled:
        return "failed"
    want_cb = (plan.get("success") or {}).get("circuit_breaker", False)
    if want_cb is False and summary.get("circuit_breaker_tripped"):
        return "failed"
    return "succeeded"


def audit_processes(
    pgrep_lines: list[str],
    running_ids: list[str] | None = None,
    *,
    tracked: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Return untracked driver command lines.

    Prefer systemd MainPID / workdir / unit markers. ``running_ids`` alone is
    retained for back-compat but is not enough when the cmdline omits the job id.
    """
    tracked_rows = list(tracked or [])
    if running_ids and not tracked_rows:
        tracked_rows = [{"id": job_id} for job_id in running_ids]
    orphans: list[str] = []
    for line in pgrep_lines:
        text = line.strip()
        if not text or text == "none":
            continue
        if not any(needle in text for needle in DRIVER_NEEDLES):
            continue
        if "pgrep" in text:
            continue
        if _line_matches_tracked(text, tracked_rows):
            continue
        orphans.append(text)
    return orphans


def _line_matches_tracked(text: str, tracked_rows: list[dict[str, Any]]) -> bool:
    if not tracked_rows:
        return False
    for row in tracked_rows:
        job_id = str(row.get("id") or "")
        unit = str(row.get("unit") or "")
        workdir = str(row.get("workdir") or "")
        main_pid = row.get("main_pid")
        if job_id and (job_id in text or f"atlas-job-{job_id}" in text):
            return True
        if unit and unit in text:
            return True
        if workdir and workdir in text:
            return True
        if isinstance(main_pid, int) and main_pid > 0:
            first = text.split(None, 1)[0]
            if first.isdigit() and int(first) == main_pid:
                return True
    return False


def _launcher() -> Path:
    return repo_root() / "scripts" / "lexicon" / "runner" / "launch_reenrich_class_b_remote.sh"


def _python_bin() -> str:
    override = os.environ.get("ATLAS_RE_ENRICH_PYTHON")
    if override:
        return override
    # Resolve primary checkout .venv via shared git common dir (layout A).
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(repo_root()),
            text=True,
        ).strip()
        common_path = Path(common)
        if not common_path.is_absolute():
            common_path = (repo_root() / common_path).resolve()
        primary = common_path.parent
        candidate = primary / ".venv" / "bin" / "python"
        if candidate.is_file():
            return str(candidate)
    except (OSError, subprocess.CalledProcessError):
        pass
    fallback = repo_root() / ".venv" / "bin" / "python"
    return str(fallback)


def _run_backup_doctor() -> int:
    return subprocess.call(
        ["bash", str(repo_root() / "scripts" / "backup-data.sh"), "doctor"],
        cwd=str(repo_root()),
    )


def validate_git_receipt(receipt: dict[str, Any]) -> list[str]:
    """Reject (don't warn) receipts that violate the public-repo schema cap."""
    errors: list[str] = []
    unknown = sorted(set(receipt) - GIT_RECEIPT_ALLOWLIST)
    if unknown:
        errors.append(f"disallowed fields: {unknown}")
    blob = json.dumps(receipt, sort_keys=True, ensure_ascii=False).encode("utf-8")
    if len(blob) > GIT_RECEIPT_MAX_BYTES:
        errors.append(f"receipt exceeds {GIT_RECEIPT_MAX_BYTES} bytes ({len(blob)})")

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}" if path else key)
            return
        if isinstance(value, list):
            for idx, child in enumerate(value):
                walk(child, f"{path}[{idx}]")
            return
        if not isinstance(value, str):
            return
        if _ABS_PATH.search(value):
            errors.append(f"absolute path at {path}")
        if _CRED_HINT.search(value):
            errors.append(f"credential-like text at {path}")
        if _HOSTNAME_HINT.search(value):
            errors.append(f"hostname/IP at {path}")

    walk(receipt, "")
    return errors


def build_git_receipt(full: dict[str, Any]) -> dict[str, Any]:
    capped = {key: full[key] for key in GIT_RECEIPT_ALLOWLIST if key in full}
    # Never embed remote absolute workdirs in the public receipt.
    if isinstance(capped.get("workdir"), str) and capped["workdir"].startswith("/"):
        capped["workdir"] = f"run-atlas-job-{capped.get('id', 'job')}"
    errors = validate_git_receipt(capped)
    if errors:
        raise ValueError("; ".join(errors))
    return capped


def write_git_receipt(job_id: str, receipt: dict[str, Any]) -> Path:
    capped = build_git_receipt(receipt)
    path = git_receipt_path(job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(capped, indent=2) + "\n", encoding="utf-8")
    return path


def _receipt_locator(path: Path, job_id: str) -> str:
    try:
        return str(path.relative_to(repo_root()))
    except ValueError:
        return f"batch_state/atlas-jobs/receipts/{job_id}.json"


def run_restic_sink(
    job_id: str,
    *,
    source_dir: Path,
    skip: bool = False,
) -> dict[str, Any]:
    """Run durable_mirror snapshot then backup-data.sh backup --execute."""
    backup: dict[str, Any] = {"attempted": False, "ok": False, "snapshot_id": None, "error": None}
    if skip:
        backup["error"] = "skipped"
        return backup
    backup["attempted"] = True
    doctor = _run_backup_doctor()
    if doctor != 0:
        backup["error"] = "backup-data.sh doctor failed"
        set_restic_sink_blocked(backup["error"])
        return backup
    mirror = mirror_dir_for(job_id)
    mirror.parent.mkdir(parents=True, exist_ok=True)
    py = os.environ.get("ATLAS_RE_ENRICH_PYTHON") or _python_bin()
    snap = subprocess.run(
        [
            py,
            str(repo_root() / "scripts" / "lexicon" / "runner" / "durable_mirror.py"),
            "snapshot",
            "--source",
            str(source_dir),
            "--mirror-dir",
            str(mirror),
        ],
        cwd=str(repo_root()),
        capture_output=True,
        text=True,
        check=False,
    )
    if snap.returncode != 0:
        backup["error"] = (snap.stderr or snap.stdout or "durable_mirror snapshot failed").strip()[
            :500
        ]
        set_restic_sink_blocked(str(backup["error"]))
        return backup
    backup_proc = subprocess.run(
        ["bash", str(repo_root() / "scripts" / "backup-data.sh"), "backup", "--execute"],
        cwd=str(repo_root()),
        capture_output=True,
        text=True,
        check=False,
    )
    if backup_proc.returncode != 0:
        backup["error"] = (backup_proc.stderr or backup_proc.stdout or "backup --execute failed").strip()[
            :500
        ]
        set_restic_sink_blocked(str(backup["error"]))
        return backup
    snapshot_id = _extract_snapshot_id(backup_proc.stdout or "")
    if not snapshot_id:
        snapshot_id = _extract_snapshot_id(backup_proc.stderr or "")
    if not snapshot_id:
        backup["error"] = "backup completed without snapshot_id"
        set_restic_sink_blocked(str(backup["error"]))
        return backup
    backup["ok"] = True
    backup["snapshot_id"] = snapshot_id
    backup["error"] = None
    clear_restic_sink_blocked()
    return backup


def _extract_snapshot_id(text: str) -> str | None:
    match = re.search(r"\b([0-9a-f]{64})\b", text)
    return match.group(1) if match else None


def submit(plan: dict[str, Any], *, dry_run: bool = False, host_adapter: HostAdapter | None = None) -> int:
    errors = validate_plan(plan)
    if errors:
        print("invalid plan:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    job_id = str(plan["id"])
    host = str(plan["host"])
    sink = plan.get("result_sink")
    if sink in {"restic", "both"} and restic_sink_blocked() and not dry_run:
        print(
            "restic sink blocked until backup-data.sh doctor is green "
            f"({restic_block_path()})",
            file=sys.stderr,
        )
        return 2
    existing = load_registry(job_id)
    if existing and existing.get("state") == "running":
        print(f"job {job_id} is already running", file=sys.stderr)
        return 2
    adapter = host_adapter or get_host_adapter()
    if not dry_run:
        try:
            if not adapter.reachable(host):
                print(f"host {host} unreachable", file=sys.stderr)
                return 2
            busy_units = active_host_units(host, adapter)
        except (ConnectionError, OSError, ValueError) as exc:
            print(f"host unit check failed: {exc}", file=sys.stderr)
            return 2
        if busy_units:
            print(
                f"host {host} already has active unit {busy_units[0].get('name')} "
                "(systemd is the mutex; registry is journal only)",
                file=sys.stderr,
            )
            return 2
        journal_busy = running_on_host(host)
        if journal_busy:
            # Journal says running but host has no unit — reconcile hole; still refuse.
            print(
                f"registry journal has running job {journal_busy[0].get('id')} "
                "with no active host unit; close/reconcile before submit",
                file=sys.stderr,
            )
            return 2
    unit = unit_name(job_id)
    workdir = work_dir_for(job_id, plan)
    args = list(plan.get("args") or [])
    if "--no-poll" not in args:
        args.append("--no-poll")
    env = os.environ.copy()
    env["ATLAS_RUNNER_HOST"] = host
    env["ATLAS_RE_ENRICH_UNIT"] = unit
    env["ATLAS_RE_ENRICH_WORK_DIR"] = workdir
    env["ATLAS_RE_ENRICH_OUT_DIR"] = str(local_pull_dir(job_id))
    env["ATLAS_JOB_EXIT_STATUS_FILE"] = f"{workdir}/exit-status.json"
    env["ATLAS_RE_ENRICH_RUNTIME_MAX_SEC"] = str(
        plan.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    )
    env["ATLAS_RE_ENRICH_RESTART"] = "no"
    slugs = plan.get("slugs_file")
    if isinstance(slugs, str) and slugs:
        env["ATLAS_RE_ENRICH_RESIDUAL"] = slugs
    cmd = ["bash", str(_launcher()), *args]
    plan_blob = json.dumps(plan, sort_keys=True).encode()
    row = {
        "id": job_id,
        "state": "submitted" if dry_run else "running",
        "host": host,
        "kind": plan["kind"],
        "unit": unit,
        "workdir": workdir,
        "issue": plan["issue"],
        "plan_sha256": hashlib.sha256(plan_blob).hexdigest(),
        "denominator": plan["denominator"],
        "result_sink": plan["result_sink"],
        "pointer_write": False,
        "resume": plan.get("resume", "never"),
        "timeout_seconds": plan.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
        "submitted_at": _now(),
        "plan": plan,
    }
    if dry_run:
        print("host", host)
        print("unit", unit)
        print("workdir", workdir)
        print("cmd", " ".join(cmd))
        if slugs:
            print("slugs_file", slugs)
        return 0
    save_registry(row)
    rc = subprocess.call(cmd, cwd=str(repo_root()), env=env)
    if rc != 0:
        row["state"] = "rejected"
        row["submit_exit"] = rc
        save_registry(row)
    return rc


def close_job(
    job_id: str,
    *,
    summary: dict[str, Any] | None = None,
    skip_pull: bool = False,
    skip_restic: bool = False,
    host_adapter: HostAdapter | None = None,
) -> int:
    job_id = require_safe_job_id(job_id)
    row = load_registry(job_id)
    if row is None:
        print(f"no registry row for {job_id}", file=sys.stderr)
        return 2
    plan = row.get("plan") if isinstance(row.get("plan"), dict) else {}
    host = str(row.get("host") or plan.get("host") or "atlas-runner")
    workdir = str(row.get("workdir") or work_dir_for(job_id, plan))
    adapter = host_adapter or get_host_adapter()

    exit_status: dict[str, Any] | None = None
    try:
        exit_status = adapter.read_exit_status(host, workdir)
    except (ConnectionError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"exit-status read failed: {exc}", file=sys.stderr)

    has_summary = summary_has_evidence(summary)
    if not has_summary and not exit_status:
        receipt = _base_receipt(row, job_id, plan, workdir)
        receipt["state"] = "needs_finalize"
        receipt["summary"] = summary if isinstance(summary, dict) else {}
        receipt["pulled"] = False
        receipt["backup"] = {"attempted": False, "ok": False, "snapshot_id": None, "error": "not attempted"}
        receipt["delivery"] = "failed"
        _seal_receipt(job_id, row, receipt, registry_state="needs_finalize")
        print("needs_finalize", job_id, "missing summary evidence and exit-status", file=sys.stderr)
        return 1

    if has_summary:
        assert summary is not None
        job_state = interpret_summary(summary, plan)
    else:
        # Exit status alone cannot prove success.
        job_state = "failed"
        if _exit_status_ok(exit_status):
            job_state = "needs_finalize"
        summary = summary if isinstance(summary, dict) else {}

    if exit_status and not _exit_status_ok(exit_status) and job_state == "succeeded":
        job_state = "failed"

    pulled = False
    pull_error: str | None = None
    if not skip_pull:
        pull_rc = pull(host=host, job_id=job_id, workdir=workdir)
        pulled = pull_rc == 0
        if not pulled:
            pull_error = f"pull failed rc={pull_rc}"
    else:
        pull_error = "skipped"

    sink = row.get("result_sink") or plan.get("result_sink")
    backup = {"attempted": False, "ok": False, "snapshot_id": None, "error": "not required"}
    if sink in {"restic", "both"}:
        source = local_pull_dir(job_id)
        if not source.is_dir():
            source.mkdir(parents=True, exist_ok=True)
            # Minimal local evidence so mirror has something when pull was skipped in tests.
            (source / "close-marker.json").write_text(
                json.dumps({"id": job_id, "closed_at": _now()}) + "\n",
                encoding="utf-8",
            )
        backup = run_restic_sink(job_id, source_dir=source, skip=skip_restic)

    receipt = _base_receipt(row, job_id, plan, workdir)
    receipt["state"] = job_state
    receipt["summary"] = summary if isinstance(summary, dict) else {}
    receipt["pulled"] = pulled
    if pull_error:
        receipt["pull_error"] = pull_error
    receipt["exit_status"] = exit_status
    receipt["backup"] = backup
    # Keep legacy key as alias for older readers (same object).
    receipt["restic"] = {
        "attempted": backup.get("attempted"),
        "ok": backup.get("ok"),
        "receipt": backup.get("snapshot_id") or backup.get("error"),
    }

    delivery_ok = True
    if sink in {"restic", "both"} and not skip_restic and not backup.get("ok"):
        delivery_ok = False
    if sink in {"git", "both"}:
        try:
            git_path = write_git_receipt(job_id, receipt)
            receipt["git_pr"] = _receipt_locator(git_path, job_id)
        except ValueError as exc:
            delivery_ok = False
            receipt["git_pr"] = None
            receipt["git_error"] = str(exc)
            print(f"git receipt rejected: {exc}", file=sys.stderr)
    else:
        # Even for restic-only, land a schema-capped local receipt for visibility.
        try:
            git_path = write_git_receipt(job_id, receipt)
            receipt["git_pr"] = _receipt_locator(git_path, job_id)
        except ValueError as exc:
            receipt["git_pr"] = None
            receipt["git_error"] = str(exc)
            delivery_ok = False

    receipt["delivery"] = "ok" if delivery_ok else "failed"
    # Never delete remote workdir — especially on backup failure.
    receipt["workdir_retained"] = True

    registry_state = job_state
    _seal_receipt(job_id, row, receipt, registry_state=registry_state)
    print(registry_state, job_id, result_path(job_id))
    if job_state == "succeeded" and delivery_ok:
        return 0
    return 1


def _base_receipt(
    row: dict[str, Any], job_id: str, plan: dict[str, Any], workdir: str
) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA,
        "id": job_id,
        "state": "failed",
        "host": row.get("host"),
        "unit": row.get("unit"),
        "kind": row.get("kind") or plan.get("kind"),
        "issue": row.get("issue") or plan.get("issue"),
        "workdir": workdir,
        "plan_sha256": row.get("plan_sha256"),
        "denominator": row.get("denominator") or plan.get("denominator"),
        "closed_at": _now(),
        "summary": {},
        "pulled": False,
        "mirror_dir": None,
        "backup": {"attempted": False, "ok": False, "snapshot_id": None, "error": None},
        "delivery": "failed",
        "git_pr": None,
        "exit_status": None,
    }


def _seal_receipt(
    job_id: str, row: dict[str, Any], receipt: dict[str, Any], *, registry_state: str
) -> None:
    result_file = result_path(job_id)
    result_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = result_file.with_suffix(result_file.suffix + ".tmp")
    tmp.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    tmp.replace(result_file)
    row["state"] = registry_state
    row["closed_at"] = receipt["closed_at"]
    row["result"] = str(result_file)
    save_registry(row)


def _exit_status_ok(exit_status: dict[str, Any] | None) -> bool:
    if not exit_status:
        return False
    code = exit_status.get("exit_status", exit_status.get("exit_code"))
    if code in {0, "0"}:
        return True
    return exit_status.get("service_result") == "success"


def reconcile_row(
    row: dict[str, Any],
    *,
    host_units: list[dict[str, Any]],
    host_adapter: HostAdapter | None = None,
) -> dict[str, Any]:
    """Reconcile journal row against host units. Mutates and persists when needed."""
    if row.get("state") != "running":
        return row
    unit = str(row.get("unit") or "")
    active_names = {str(u.get("name")) for u in host_units if _unit_is_active(u)}
    if unit in active_names:
        return row
    # Unit inactive while journal says running.
    adapter = host_adapter or get_host_adapter()
    workdir = str(row.get("workdir") or work_dir_for(str(row["id"]), row.get("plan") or {}))
    host = str(row.get("host") or "atlas-runner")
    exit_status = None
    try:
        exit_status = adapter.read_exit_status(host, workdir)
    except (ConnectionError, OSError, ValueError, json.JSONDecodeError):
        exit_status = None
    resume = row.get("resume") or (row.get("plan") or {}).get("resume") or "never"
    new_state = "crashed" if exit_status is None and resume == "never" else "needs_finalize"
    row["state"] = new_state
    row["reconciled_at"] = _now()
    if exit_status is not None:
        row["exit_status"] = exit_status
    save_registry(row)
    return row


def _unit_is_active(unit: dict[str, Any]) -> bool:
    return unit.get("active") in {"active", "activating", "reloading"} or str(
        unit.get("sub", "")
    ).startswith("running")


def status(*, host: str, audit: bool = False, host_adapter: HostAdapter | None = None) -> int:
    if host in HRAMATKA_ALIASES:
        print("status for batch jobs must use atlas-runner", file=sys.stderr)
        return 2
    adapter = host_adapter or get_host_adapter()
    try:
        if not adapter.reachable(host):
            print(f"host {host} unreachable", file=sys.stderr)
            return 2
        host_units = adapter.list_atlas_job_units(host)
    except (ConnectionError, OSError, ValueError) as exc:
        print(f"host status failed: {exc}", file=sys.stderr)
        return 2

    rows = [r for r in list_registry() if r.get("host") == host]
    for row in rows:
        if row.get("state") == "running":
            row = reconcile_row(row, host_units=host_units, host_adapter=adapter)
        print(row.get("state"), row.get("id"), row.get("unit"), row.get("workdir"))

    if restic_sink_blocked():
        print("restic-sink-blocked", restic_block_path(), file=sys.stderr)

    if not audit:
        return 0

    # Primary orphan test: systemd MainPID / unit membership.
    tracked: list[dict[str, Any]] = []
    for row in rows:
        if row.get("state") != "running":
            continue
        unit = str(row.get("unit") or "")
        main_pid = None
        for host_unit in host_units:
            if host_unit.get("name") == unit:
                main_pid = host_unit.get("main_pid")
                break
        tracked.append(
            {
                "id": row.get("id"),
                "unit": unit,
                "workdir": row.get("workdir"),
                "main_pid": main_pid,
            }
        )

    try:
        lines = adapter.pgrep_drivers(host)
    except (ConnectionError, OSError) as exc:
        print(f"audit pgrep failed: {exc}", file=sys.stderr)
        return 2

    orphans = audit_processes(lines, tracked=tracked)
    # Also flag active host units with no journal row.
    journal_units = {str(r.get("unit")) for r in rows if r.get("state") == "running"}
    for host_unit in host_units:
        if not _unit_is_active(host_unit):
            continue
        name = str(host_unit.get("name") or "")
        if name and name not in journal_units:
            orphans.append(f"untracked-unit:{name}")

    if orphans:
        print("untracked driver process:", file=sys.stderr)
        for line in orphans:
            print(f"  {line}", file=sys.stderr)
        return 2
    return 0


def pull(
    *,
    host: str,
    job_id: str | None = None,
    workdir: str | None = None,
) -> int:
    if host in HRAMATKA_ALIASES:
        print("pull for batch jobs must use atlas-runner", file=sys.stderr)
        return 2
    if job_id is not None:
        job_id = require_safe_job_id(job_id)
    if workdir:
        workdir = require_safe_workdir(workdir)
    env = os.environ.copy()
    env["ATLAS_RUNNER_HOST"] = host
    if workdir:
        env["ATLAS_RE_ENRICH_WORK_DIR"] = workdir
    if job_id:
        env["ATLAS_RE_ENRICH_OUT_DIR"] = str(local_pull_dir(job_id))
        unit = unit_name(job_id)
        env["ATLAS_RE_ENRICH_UNIT"] = unit
    return subprocess.call(
        ["bash", str(_launcher()), "--pull-only"],
        cwd=str(repo_root()),
        env=env,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate a plan JSON")
    p_val.add_argument("plan", type=Path)

    p_sub = sub.add_parser("submit", help="Validate, register, and launch")
    p_sub.add_argument("plan", type=Path)
    p_sub.add_argument("--dry-run", action="store_true")

    p_st = sub.add_parser("status", help="List registry rows; optional untracked audit")
    p_st.add_argument("--host", default="atlas-runner")
    p_st.add_argument("--audit", action="store_true")

    p_close = sub.add_parser("close", help="Seal a result receipt for a registered job")
    p_close.add_argument("job_id")
    p_close.add_argument("--summary-file", type=Path)
    p_close.add_argument("--skip-pull", action="store_true")
    p_close.add_argument("--skip-restic", action="store_true")

    sub.add_parser("list", help="List registry rows")

    p_pull = sub.add_parser("pull", help="Pull work-dir artifacts (no pointer flip)")
    p_pull.add_argument("--host", default="atlas-runner")
    p_pull.add_argument("--job-id")

    args = parser.parse_args(argv)
    if args.cmd == "validate":
        plan = load_plan(args.plan)
        errors = validate_plan(plan)
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 2
        print("ok", plan.get("id"), plan.get("host"), plan.get("kind"))
        return 0
    if args.cmd == "submit":
        return submit(load_plan(args.plan), dry_run=args.dry_run)
    if args.cmd == "status":
        return status(host=args.host, audit=args.audit)
    if args.cmd == "close":
        summary = None
        if args.summary_file:
            summary = json.loads(args.summary_file.read_text(encoding="utf-8"))
        try:
            return close_job(
                args.job_id,
                summary=summary,
                skip_pull=args.skip_pull,
                skip_restic=args.skip_restic,
            )
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
    if args.cmd == "list":
        for row in list_registry():
            print(row.get("state"), row.get("id"), row.get("host"))
        return 0
    if args.cmd == "pull":
        try:
            if args.job_id:
                require_safe_job_id(args.job_id)
            workdir = None
            if args.job_id:
                row = load_registry(args.job_id)
                if row:
                    workdir = str(row.get("workdir") or "")
            return pull(host=args.host, job_id=args.job_id, workdir=workdir or None)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
