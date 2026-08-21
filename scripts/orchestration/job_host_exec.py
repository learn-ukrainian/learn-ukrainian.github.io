#!/usr/bin/env python3
"""Run a command on a VPS worker checkout over BatchMode SSH.

Notebook orchestrators keep talking to tunneled ``127.0.0.1`` APIs. Both
occupancy hosts are the worker pool: agent CLIs and long Python jobs run
on either box. The job host also holds Monitor and fleet-comms. The
teacher host also holds the teacher product — workers stay out of
``/opt/hramatka`` and ``/srv``, and occupancy headroom decides who takes
the next job. Notebook ``delegate.py dispatch`` is the fallback only when
**every** VPS worker host is unavailable or full. This helper never prints
host aliases, IPs, or occupancy env.

SSH aliases stay in operator env (not git):

- ``LU_DISPATCH_SSH`` — ``opaque-id=ssh-alias,...``
- ``LU_JOB_DISPATCH_HOST`` / ``ATLAS_RUNNER_HOST`` — job-host fallback
- ``LU_TEACHER_DISPATCH_HOST`` — teacher-host fallback
- ``LU_JOB_REPO`` / ``LU_TEACHER_REPO`` — absolute remote checkouts

Remote PATH always includes ``$HOME/.local/bin`` and ``$HOME/.opencode/bin``.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Literal

from scripts.fleet_comms.paths import RETIRED_LOCAL_MARKER
from scripts.guardrails.worktree_containment import resolve_main_root

ENV_HOST = "LU_JOB_DISPATCH_HOST"
ENV_HOST_FALLBACK = "ATLAS_RUNNER_HOST"
ENV_TEACHER_HOST = "LU_TEACHER_DISPATCH_HOST"
ENV_DISPATCH_SSH = "LU_DISPATCH_SSH"
ENV_REPO = "LU_JOB_REPO"
ENV_TEACHER_REPO = "LU_TEACHER_REPO"
ENV_ALLOW_NOTEBOOK = "LU_ALLOW_NOTEBOOK_DISPATCH"
ENV_OCCUPANCY_HOST = "LU_JOB_OCCUPANCY_HOST_ID"
ENV_MEM_FULL = "LU_JOB_MEM_FULL_PCT"
ENV_DISK_FULL = "LU_JOB_DISK_FULL_PCT"
REMOTE_PATH_EXPORT = 'export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$PATH"'
_REMOTE_VAR_PREFIX = "__LU_REMOTE_VAR:"
# Canonical SSH Host names already used by atlas_job (public repo contract).
DEFAULT_JOB_SSH = "atlas-runner"
DEFAULT_TEACHER_SSH = "hramatka"
DEFAULT_JOB_REPO = "/home/ops/services/learn-ukrainian"
DEFAULT_TEACHER_REPO = "/home/ops/learn-ukrainian"
DEFAULT_MEM_FULL_PCT = 85.0
DEFAULT_DISK_FULL_PCT = 85.0
_MONITOR_DEFAULT = "http://127.0.0.1:8765"
_MISSING = object()
TEACHER_HOST_ID = "host-teacher"
JOB_HOST_ID = "host-job"

Placement = Literal["notebook", "vps"]
PlacementReason = Literal[
    "no_retire_marker",
    "allow_env",
    "unavailable",
    "full",
    "available",
]
_COPY_FILE_FLAGS = {
    "--prompt-file": "prompt",
    "--lifecycle-file": "lifecycle",
    "--output-schema": "output-schema",
}


class SshTransportError(OSError):
    """Raised when the local ssh client cannot be started."""


def notebook_block_message(*, host_id: str | None = None) -> str:
    where = f" ({host_id})" if host_id else ""
    return (
        f"a VPS worker host{where} is available; spawn workers there. "
        f"Run: {ENV_DISPATCH_SSH}=<opaque=alias,...> {ENV_REPO}=<remote-checkout> "
        ".venv/bin/python scripts/orchestration/job_host_exec.py -- "
        ".venv/bin/python scripts/delegate.py dispatch ... "
        "Notebook spawn is allowed only when every VPS worker host is "
        f"unavailable or full (or {ENV_ALLOW_NOTEBOOK}=1)."
    )


def job_dispatch_host() -> str:
    return (
        os.environ.get(ENV_HOST, "").strip()
        or os.environ.get(ENV_HOST_FALLBACK, "").strip()
        or DEFAULT_JOB_SSH
    )


def job_dispatch_repo() -> str:
    repo = os.environ.get(ENV_REPO, "").strip() or DEFAULT_JOB_REPO
    if not repo.startswith("/"):
        raise ValueError(f"{ENV_REPO} must be an absolute remote path")
    return repo


def _parse_opaque_map(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for part in raw.split(","):
        item = part.strip()
        if not item or "=" not in item:
            continue
        opaque, alias = item.split("=", 1)
        opaque = opaque.strip()
        alias = alias.strip()
        if opaque and alias:
            mapping[opaque] = alias
    return mapping


def ssh_alias_for_host_id(host_id: str) -> str:
    mapped = _parse_opaque_map(os.environ.get(ENV_DISPATCH_SSH, ""))
    if host_id in mapped:
        return mapped[host_id]
    if host_id == TEACHER_HOST_ID:
        return os.environ.get(ENV_TEACHER_HOST, "").strip() or DEFAULT_TEACHER_SSH
    if host_id == JOB_HOST_ID:
        return job_dispatch_host()
    raise ValueError(f"no SSH alias configured for occupancy host {host_id}")


def repo_for_host_id(host_id: str) -> str:
    if host_id == TEACHER_HOST_ID:
        teacher_repo = os.environ.get(ENV_TEACHER_REPO, "").strip() or DEFAULT_TEACHER_REPO
        if not teacher_repo.startswith("/"):
            raise ValueError(f"{ENV_TEACHER_REPO} must be an absolute remote path")
        return teacher_repo
    return job_dispatch_repo()


def _monitor_base() -> str:
    return os.environ.get("DELEGATE_MONITOR_API", _MONITOR_DEFAULT).rstrip("/")


def _threshold(env_name: str, default: float) -> float:
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if value <= 0 or value > 100:
        return default
    return value


def fetch_occupancy(*, timeout: float = 2.0) -> dict[str, Any] | None:
    """Read tunneled occupancy. None means the board is not available."""
    url = f"{_monitor_base()}/api/occupancy?fresh=true"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (
        OSError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
        ValueError,
        UnicodeDecodeError,
    ):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _pool_host_ids(hosts: dict[str, Any]) -> list[str]:
    restricted = os.environ.get(ENV_OCCUPANCY_HOST, "").strip()
    if restricted:
        return [restricted]
    return [key for key in hosts if isinstance(hosts.get(key), dict)]


def classify_host_entry(host: dict[str, Any] | None) -> Literal["available", "unavailable", "full"]:
    if not isinstance(host, dict):
        return "unavailable"
    status = str(host.get("status") or "unavailable")
    if status == "unavailable":
        return "unavailable"
    if status not in {"fresh", "stale"}:
        return "unavailable"
    mem = host.get("mem") if isinstance(host.get("mem"), dict) else {}
    disk = host.get("disk") if isinstance(host.get("disk"), dict) else {}
    mem_pct = mem.get("pct")
    disk_pct = disk.get("pct")
    cpu_count = host.get("cpu_count") or 1
    loadavg = host.get("loadavg") if isinstance(host.get("loadavg"), list) else []
    load1 = loadavg[0] if loadavg else 0.0
    if isinstance(mem_pct, (int, float)) and float(mem_pct) >= _threshold(ENV_MEM_FULL, DEFAULT_MEM_FULL_PCT):
        return "full"
    if isinstance(disk_pct, (int, float)) and float(disk_pct) >= _threshold(ENV_DISK_FULL, DEFAULT_DISK_FULL_PCT):
        return "full"
    try:
        cores = float(cpu_count)
        load = float(load1)
    except (TypeError, ValueError):
        cores, load = 1.0, 0.0
    if cores > 0 and load >= cores:
        return "full"
    if status == "stale" and mem_pct is None and disk_pct is None:
        return "unavailable"
    return "available"


def _pressure(host: dict[str, Any]) -> float:
    mem = host.get("mem") if isinstance(host.get("mem"), dict) else {}
    disk = host.get("disk") if isinstance(host.get("disk"), dict) else {}
    mem_pct = float(mem.get("pct") or 0.0)
    disk_pct = float(disk.get("pct") or 0.0)
    cpu_count = host.get("cpu_count") or 1
    loadavg = host.get("loadavg") if isinstance(host.get("loadavg"), list) else []
    try:
        load1 = float(loadavg[0]) if loadavg else 0.0
        cores = max(float(cpu_count), 1.0)
    except (TypeError, ValueError, IndexError):
        load1, cores = 0.0, 1.0
    return mem_pct + disk_pct + (load1 / cores) * 100.0


def pick_worker_host(payload: dict[str, Any] | None) -> tuple[str | None, Literal["available", "unavailable", "full"]]:
    """Choose the least-loaded available VPS. Notebook only if none qualify."""
    if not isinstance(payload, dict):
        return None, "unavailable"
    hosts = payload.get("hosts")
    if not isinstance(hosts, dict) or not hosts:
        return None, "unavailable"
    saw_full = False
    available: list[tuple[str, dict[str, Any]]] = []
    for host_id in _pool_host_ids(hosts):
        entry = hosts.get(host_id)
        if not isinstance(entry, dict):
            continue
        state = classify_host_entry(entry)
        if state == "available":
            available.append((host_id, entry))
        elif state == "full":
            saw_full = True
    if available:
        available.sort(key=lambda item: (_pressure(item[1]), item[0]))
        return available[0][0], "available"
    if saw_full:
        return None, "full"
    return None, "unavailable"


def classify_worker_host(payload: dict[str, Any] | None, *, host_id: str | None = None) -> Literal["available", "unavailable", "full"]:
    """Classify one occupancy host, or the picked pool host when ``host_id`` is omitted."""
    if host_id is not None:
        if not isinstance(payload, dict):
            return "unavailable"
        hosts = payload.get("hosts")
        if not isinstance(hosts, dict):
            return "unavailable"
        return classify_host_entry(hosts.get(host_id) if isinstance(hosts.get(host_id), dict) else None)
    _picked, state = pick_worker_host(payload)
    return state


def decide_dispatch_placement(
    *,
    repo_root: Path | None = None,
    occupancy: Any = _MISSING,
) -> tuple[Placement, PlacementReason, str | None]:
    """Where a notebook ``delegate.py dispatch`` may spawn.

    ``vps`` means refuse Darwin spawn and name the opaque occupancy host.
    ``notebook`` is allowed when the retire marker is absent, the operator
    opted in, or every VPS worker host is unavailable or full.
    """
    if os.environ.get(ENV_ALLOW_NOTEBOOK, "").strip() == "1":
        return "notebook", "allow_env", None
    root = Path(repo_root) if repo_root is not None else resolve_main_root(Path.cwd())
    marker = root / "batch_state" / "fleet-comms" / "v1" / RETIRED_LOCAL_MARKER
    sibling = root / "batch_state" / "fleet-comms" / RETIRED_LOCAL_MARKER
    if not marker.is_file() and not sibling.is_file():
        return "notebook", "no_retire_marker", None
    payload = fetch_occupancy() if occupancy is _MISSING else occupancy
    host_id, capacity = pick_worker_host(payload if isinstance(payload, dict) else None)
    if capacity == "available" and host_id:
        return "vps", "available", host_id
    return "notebook", capacity, None


def notebook_dispatch_blocked(*, repo_root: Path | None = None, occupancy: Any = _MISSING) -> str | None:
    """Return an error when this checkout must not spawn Darwin workers."""
    placement, _reason, host_id = decide_dispatch_placement(repo_root=repo_root, occupancy=occupancy)
    if placement == "vps":
        return notebook_block_message(host_id=host_id)
    return None


def build_remote_command(
    argv: list[str],
    *,
    remote_repo: str,
    extra_exports: list[str] | None = None,
) -> str:
    if not argv:
        raise ValueError("remote command is empty")
    parts: list[str] = []
    for part in argv:
        if part.startswith(_REMOTE_VAR_PREFIX):
            var = part[len(_REMOTE_VAR_PREFIX) :]
            if not var.isidentifier():
                raise ValueError(f"invalid remote payload variable {var!r}")
            parts.append(f'"${var}"')
        else:
            parts.append(shlex.quote(part))
    quoted = " ".join(parts)
    prefix = REMOTE_PATH_EXPORT
    for item in extra_exports or []:
        prefix = f"{prefix} && {item}"
    return f"{prefix} && cd {shlex.quote(remote_repo)} && {quoted}"


def _flag_value(argv: list[str], index: int, flag: str) -> tuple[str | None, int]:
    item = argv[index]
    if item == flag and index + 1 < len(argv):
        return argv[index + 1], index + 2
    prefix = f"{flag}="
    if item.startswith(prefix):
        return item.split("=", 1)[1], index + 1
    return None, index


def _remote_payload_preamble(kind: str, contents: bytes, *, seq: int) -> tuple[str, str]:
    ident = kind.replace("-", "_")
    var = f"LU_DISPATCH_{ident.upper()}_{seq}"
    encoded = base64.b64encode(contents).decode("ascii")
    preamble = (
        f"umask 077 && {var}=$(mktemp /tmp/lu-dispatch-{kind}.XXXXXX) && "
        f"printf '%s' {shlex.quote(encoded)} | base64 -d > \"${var}\""
    )
    return preamble, f"{_REMOTE_VAR_PREFIX}{var}"


def materialize_local_dispatch_argv(
    argv: list[str],
    *,
    stdin_body: bytes | None = None,
) -> tuple[list[str], bytes | None, str | None]:
    """Rewrite notebook-only paths so SSH does not send Darwin paths.

    File payloads (``--prompt-file``, ``--lifecycle-file``, ``--output-schema``)
    are written to unique private ``mktemp`` files on the remote host via a
    fail-closed base64 preamble so remote argparse still sees a real file
    (sparse-checkout inference reads ``--prompt-file`` before stdin).
    ``--prompt -`` is rewritten to a remote ``--prompt-file`` after the notebook
    stdin body is captured.
    ``--cwd`` is rejected: a Darwin working directory is not a VPS checkout.
    A notebook ``--worktree PATH`` is rewritten to bare ``--worktree`` so the
    remote checkout creates its own isolation.
    """
    out: list[str] = []
    preambles: list[str] = []
    seq = 0
    i = 0
    while i < len(argv):
        cwd_path, next_i = _flag_value(argv, i, "--cwd")
        if cwd_path is not None:
            raise ValueError(
                f"--cwd {cwd_path!r} is a notebook path and cannot be forwarded "
                "to a VPS worker; omit --cwd or pass --worktree so the remote "
                "checkout isolates itself"
            )
        prompt_val, next_i = _flag_value(argv, i, "--prompt")
        if prompt_val is not None:
            if prompt_val == "-":
                if stdin_body is None:
                    raise ValueError(
                        "--prompt - cannot be forwarded without the prompt body; "
                        "pass --prompt-file"
                    )
                preamble, remote_path = _remote_payload_preamble("prompt", stdin_body, seq=seq)
                seq += 1
                preambles.append(preamble)
                out.extend(["--prompt-file", remote_path])
            else:
                out.extend(["--prompt", prompt_val])
            i = next_i
            continue
        copied = False
        for flag, kind in _COPY_FILE_FLAGS.items():
            file_path, next_i = _flag_value(argv, i, flag)
            if file_path is None:
                continue
            body = Path(file_path).read_bytes()
            preamble, remote_path = _remote_payload_preamble(kind, body, seq=seq)
            seq += 1
            preambles.append(preamble)
            out.extend([flag, remote_path])
            i = next_i
            copied = True
            break
        if copied:
            continue
        if argv[i] == "--worktree" and i + 1 < len(argv) and not argv[i + 1].startswith("-"):
            out.append("--worktree")
            i += 2
            continue
        if argv[i].startswith("--worktree="):
            out.append("--worktree")
            i += 1
            continue
        out.append(argv[i])
        i += 1
    return out, None, (" && ".join(preambles) if preambles else None)


def materialize_local_prompt_argv(argv: list[str]) -> tuple[list[str], bytes | None]:
    """Rewrite local ``--prompt-file`` to ``--prompt -`` so SSH can carry the body."""
    rest, stdin, _preamble = materialize_local_dispatch_argv(argv)
    return rest, stdin


def notebook_fallback_after_forward(rc: int | None, *, error: BaseException | None = None) -> bool:
    """True only for SSH transport failure, so the notebook may spawn.

    Occupancy miss/full is decided before forward. Payload errors
    (missing local files, ``--cwd``, bad host config) must fail closed —
    they are not a reason to spawn on Darwin. Missing or unexecutable ``ssh``
    is classified by ``SshTransportError`` from the exec site
    (``FileNotFoundError`` / ``PermissionError``), not by filename basename.
    """
    if isinstance(error, SshTransportError):
        return True
    if error is not None:
        return False
    return rc == 255


def forward_dispatch(*, host_id: str, argv: list[str]) -> int:
    """SSH a notebook ``delegate.py dispatch`` onto the chosen VPS and spawn there.

    Remote spawn sets ``LU_ALLOW_NOTEBOOK_DISPATCH=1`` so the worker checkout
    does not try to forward again.
    """
    if len(argv) < 2:
        raise ValueError("dispatch argv is empty")
    alias = ssh_alias_for_host_id(host_id)
    repo = repo_for_host_id(host_id)
    payload = list(argv[1:])
    stdin_body: bytes | None = None
    idx = 0
    while idx < len(payload):
        prompt_val, next_idx = _flag_value(payload, idx, "--prompt")
        if prompt_val == "-":
            stdin_body = sys.stdin.buffer.read()
            break
        idx = next_idx if prompt_val is not None else idx + 1
    rest, _stdin, preamble = materialize_local_dispatch_argv(payload, stdin_body=stdin_body)
    extra_exports = [f"export {ENV_ALLOW_NOTEBOOK}=1"]
    if preamble:
        extra_exports.append(preamble)
    remote = build_remote_command(
        [".venv/bin/python", "scripts/delegate.py", *rest],
        remote_repo=repo,
        extra_exports=extra_exports,
    )
    try:
        completed = subprocess.run(
            build_ssh_argv(alias, remote),
            check=False,
        )
    except (FileNotFoundError, PermissionError) as exc:
        raise SshTransportError(str(exc)) from exc
    return int(completed.returncode)


def build_ssh_argv(host: str, remote_command: str) -> list[str]:
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=12",
        host,
        remote_command,
    ]


def _delegate_dispatch_argv(remote_argv: list[str]) -> list[str] | None:
    """Return ``[scripts/delegate.py, dispatch, ...]`` when this is a dispatch."""
    try:
        idx = remote_argv.index("scripts/delegate.py")
    except ValueError:
        return None
    rest = remote_argv[idx:]
    if len(rest) < 2 or rest[1] != "dispatch":
        return None
    return rest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="job_host_exec.py",
        description=(
            "Execute a command on a VPS worker checkout over BatchMode SSH.\n"
            "Use it to place long Python jobs and agent dispatches on occupancy "
            "hosts; do not use it to start a second Monitor or reopen retired Mac sqlite."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/orchestration/job_host_exec.py -- "
            ".venv/bin/python scripts/delegate.py dispatch --agent codex "
            "--task-id review-123 --prompt-file brief.md --mode read-only\n"
            "  .venv/bin/python scripts/orchestration/job_host_exec.py "
            "--host-id host-job -- .venv/bin/python -m pytest tests/orchestration/test_job_host_exec.py\n\n"
            "Outputs:\n"
            "  Runs the remote command in the occupancy checkout. Dispatch argv "
            "is rewritten so notebook --prompt-file/--lifecycle-file/--output-schema "
            "bodies land in remote /tmp and LU_ALLOW_NOTEBOOK_DISPATCH=1 prevents "
            "a second forward hop.\n\n"
            "Exit codes:\n"
            "  0 on successful remote completion; 2 on CLI misuse, missing host, "
            "or notebook payload errors; 255 on SSH transport failure "
            "(missing/unexecutable ssh, or ssh rc 255); other codes are the "
            "remote command.\n\n"
            "Related:\n"
            "  Occupancy: GET /api/occupancy\n"
            "  Dispatch: scripts/delegate.py\n"
            "  Issue: #7062\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host-id",
        default=None,
        help="Opaque occupancy host_id (default: pick least-loaded available VPS)",
    )
    parser.add_argument(
        "remote_argv",
        nargs=argparse.REMAINDER,
        help="Command to run after -- on the remote checkout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    remote_argv = list(args.remote_argv)
    if remote_argv and remote_argv[0] == "--":
        remote_argv = remote_argv[1:]
    if not remote_argv:
        parser.error("pass a remote command after --")
    host_id = args.host_id
    try:
        if not host_id:
            payload = fetch_occupancy()
            host_id, capacity = pick_worker_host(payload)
            if capacity != "available" or not host_id:
                print(f"error: no VPS worker host available ({capacity})", file=sys.stderr)
                return 2
        dispatch_argv = _delegate_dispatch_argv(remote_argv)
        if dispatch_argv is not None:
            try:
                return forward_dispatch(host_id=host_id, argv=dispatch_argv)
            except SshTransportError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 255
            except (ValueError, FileNotFoundError, PermissionError) as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
        alias = ssh_alias_for_host_id(host_id)
        repo = repo_for_host_id(host_id)
        ssh_argv = build_ssh_argv(alias, build_remote_command(remote_argv, remote_repo=repo))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        completed = subprocess.run(ssh_argv, check=False)
    except (FileNotFoundError, PermissionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 255
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
