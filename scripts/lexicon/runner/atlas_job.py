"""Atlas VPS job protocol: plan → submit → status → close (always a result).

Batch kinds run on atlas-runner only. Registry lives under batch_state/atlas-jobs/
(restic-covered). Close writes a result receipt; large artifacts go through
durable_mirror + backup-data.sh. Publish/pointer flip is never this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = "atlas-job.v1"
BATCH_KINDS = frozenset({"reenrich"})
ALLOWED_HOSTS = {"reenrich": frozenset({"atlas-runner"})}
HRAMATKA_ALIASES = frozenset({"hramatka", "vps"})
RESULT_SINKS = frozenset({"git", "restic", "both"})
DRIVER_NEEDLES = (
    "reenrich_thin_manifest_entries",
    "migrate_slovnyk",
    "enrich_offline_20k",
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def registry_dir() -> Path:
    override = os.environ.get("ATLAS_JOB_REGISTRY")
    if override:
        return Path(override)
    return repo_root() / "batch_state" / "atlas-jobs"


def registry_path(job_id: str) -> Path:
    return registry_dir() / f"{job_id}.json"


def result_path(job_id: str) -> Path:
    return registry_dir() / f"{job_id}.result.json"


def unit_name(job_id: str) -> str:
    return f"atlas-job-{job_id}.service"


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
    if not isinstance(job_id, str) or not _SAFE_ID.match(job_id):
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
    if not isinstance(denom, int) or denom < 0:
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
    return errors


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def save_registry(row: dict[str, Any]) -> Path:
    registry_dir().mkdir(parents=True, exist_ok=True)
    path = registry_path(str(row["id"]))
    path.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    return path


def load_registry(job_id: str) -> dict[str, Any] | None:
    path = registry_path(job_id)
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


def running_on_host(host: str) -> list[dict[str, Any]]:
    return [r for r in list_registry() if r.get("host") == host and r.get("state") == "running"]


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


def audit_processes(pgrep_lines: list[str], running_ids: list[str]) -> list[str]:
    """Return untracked driver command lines."""
    tracked = bool(running_ids)
    orphans: list[str] = []
    for line in pgrep_lines:
        text = line.strip()
        if not text or text == "none":
            continue
        if not any(needle in text for needle in DRIVER_NEEDLES):
            continue
        if "pgrep" in text:
            continue
        if not tracked:
            orphans.append(text)
            continue
        if not any(job_id in text or f"atlas-job-{job_id}" in text for job_id in running_ids):
            orphans.append(text)
    return orphans


def _launcher() -> Path:
    return repo_root() / "scripts" / "lexicon" / "runner" / "launch_reenrich_class_b_remote.sh"


def submit(plan: dict[str, Any], *, dry_run: bool = False) -> int:
    errors = validate_plan(plan)
    if errors:
        print("invalid plan:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    job_id = str(plan["id"])
    host = str(plan["host"])
    existing = load_registry(job_id)
    if existing and existing.get("state") == "running":
        print(f"job {job_id} is already running", file=sys.stderr)
        return 2
    busy = running_on_host(host)
    if busy and not dry_run:
        print(f"host {host} already has running job {busy[0].get('id')}", file=sys.stderr)
        return 2
    unit = unit_name(job_id)
    args = list(plan.get("args") or [])
    if "--no-poll" not in args:
        args.append("--no-poll")
    env = os.environ.copy()
    env["ATLAS_RUNNER_HOST"] = host
    env["ATLAS_RE_ENRICH_UNIT"] = unit
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
        "plan_sha256": hashlib.sha256(plan_blob).hexdigest(),
        "denominator": plan["denominator"],
        "result_sink": plan["result_sink"],
        "pointer_write": False,
        "submitted_at": _now(),
        "plan": plan,
    }
    if dry_run:
        print("host", host)
        print("unit", unit)
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
) -> int:
    row = load_registry(job_id)
    if row is None:
        print(f"no registry row for {job_id}", file=sys.stderr)
        return 2
    plan = row.get("plan") if isinstance(row.get("plan"), dict) else {}
    if summary is None:
        summary = {}
    state = interpret_summary(summary, plan)
    receipt = {
        "schema": "atlas-job-result.v1",
        "id": job_id,
        "state": state,
        "host": row.get("host"),
        "unit": row.get("unit"),
        "closed_at": _now(),
        "summary": summary,
        "pulled": not skip_pull,
        "mirror_dir": None,
        "restic": {"attempted": False, "ok": False, "receipt": None},
        "git_pr": None,
    }
    sink = row.get("result_sink") or plan.get("result_sink")
    if sink in {"restic", "both"} and not skip_restic:
        receipt["restic"]["attempted"] = True
        doctor = subprocess.call(
            ["bash", str(repo_root() / "scripts" / "backup-data.sh"), "doctor"],
            cwd=str(repo_root()),
        )
        receipt["restic"]["ok"] = doctor == 0
        receipt["restic"]["receipt"] = "backup-data.sh doctor"
    result_file = result_path(job_id)
    result_file.parent.mkdir(parents=True, exist_ok=True)
    result_file.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    row["state"] = state
    row["closed_at"] = receipt["closed_at"]
    row["result"] = str(result_file)
    save_registry(row)
    print(state, job_id, result_file)
    return 0 if state == "succeeded" else 1


def status(*, host: str, audit: bool = False) -> int:
    if host in HRAMATKA_ALIASES:
        print("status for batch jobs must use atlas-runner", file=sys.stderr)
        return 2
    rows = [r for r in list_registry() if r.get("host") == host]
    for row in rows:
        print(row.get("state"), row.get("id"), row.get("unit"))
    if not audit:
        return 0
    remote = "pgrep -af 'reenrich_thin_manifest_entries|migrate_slovnyk|enrich_offline_20k' || true"
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=12", host, remote],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = (proc.stdout or "").splitlines()
    running_ids = [str(r["id"]) for r in rows if r.get("state") == "running"]
    orphans = audit_processes(lines, running_ids)
    if orphans:
        print("untracked driver process:", file=sys.stderr)
        for line in orphans:
            print(f"  {line}", file=sys.stderr)
        return 2
    return 0


def pull(*, host: str) -> int:
    if host in HRAMATKA_ALIASES:
        print("pull for batch jobs must use atlas-runner", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env["ATLAS_RUNNER_HOST"] = host
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
        return close_job(
            args.job_id,
            summary=summary,
            skip_pull=args.skip_pull,
            skip_restic=args.skip_restic,
        )
    if args.cmd == "list":
        for row in list_registry():
            print(row.get("state"), row.get("id"), row.get("host"))
        return 0
    if args.cmd == "pull":
        return pull(host=args.host)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
