"""Forward notebook ``ask-*`` to the canonical job-host plane over SSH (#7172).

The Mac/notebook primary checkout is a **client**. When the local fleet-comms
sqlite has been retired (``READ_ME_CANONICAL_ON_JOB_HOST.txt``), ordinary ACP
asks must not open ``AuthorityService`` locally — that raises
``PlaneRootAnchorError``. Instead, when the notebook tunnel / services role is
configured, re-run the same ``ask-*`` on the job-host checkout where the
canonical plane lives.

This is not a second Monitor, not a local shadow plane, and not a new control
surface. It reuses the existing BatchMode SSH path that ``services.sh`` and
``job_host_exec`` already use for notebook clients.

Never prints SSH host aliases, IPs, or remote absolute paths.
"""

from __future__ import annotations

import base64
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.fleet_comms.paths import (
    RETIRED_LOCAL_PLANE_MESSAGE,
    local_plane_is_retired,
)

# Loop-prevention: set on the remote ask so a misconfigured job-host retire
# marker cannot bounce forever.
ENV_FORWARD_DONE = "LU_ASK_JOB_HOST_FORWARD"

# Prefer the job-dispatch aliases (canonical plane host); fall back to the
# services.sh notebook-role host used for tunneled Mac clients.
ENV_JOB_HOST = "LU_JOB_DISPATCH_HOST"
ENV_JOB_HOST_FALLBACK = "ATLAS_RUNNER_HOST"
ENV_SERVICES_HOST = "LU_SERVICES_SSH_HOST"
ENV_JOB_REPO = "LU_JOB_REPO"
ENV_SERVICES_REPO = "LU_SERVICES_REMOTE_ROOT"
DEFAULT_SERVICES_REPO = "/home/ops/learn-ukrainian"

REMOTE_PATH_EXPORT = 'export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$PATH"'
# Generous wall clock: seat profiles go up to 1800s (kimi); transport grace on top.
DEFAULT_SSH_TIMEOUT_SECONDS = 2100.0


class AskForwardError(RuntimeError):
    """Notebook ask cannot open the retired local plane and cannot forward."""


@dataclass(frozen=True, slots=True)
class AskForwardTarget:
    """Resolved SSH destination. Values stay in-memory; never log them."""

    host: str
    remote_repo: str


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def ask_forward_already_done() -> bool:
    """True when this process is already the job-host leg of a forward."""
    return _env(ENV_FORWARD_DONE) == "1"


def resolve_ask_forward_target() -> AskForwardTarget | None:
    """Return the job-host SSH target when notebook forward config is present.

    Configured means an SSH Host alias plus an absolute remote checkout —
    the same contract ``services.sh`` / ``job_host_exec`` use. Returns None
    when the operator has not wired the notebook client yet.
    """
    host = _env(ENV_JOB_HOST) or _env(ENV_JOB_HOST_FALLBACK) or _env(ENV_SERVICES_HOST)
    if not host:
        return None
    repo = _env(ENV_JOB_REPO) or _env(ENV_SERVICES_REPO) or DEFAULT_SERVICES_REPO
    if not repo.startswith("/"):
        return None
    return AskForwardTarget(host=host, remote_repo=repo)


def format_ask_forward_refusal(*, configured: bool) -> str:
    """Human one-liner naming the reroute; never includes host aliases or paths."""
    if configured:
        return (
            f"{RETIRED_LOCAL_PLANE_MESSAGE} "
            "ask-* forward to the job-host plane failed; fix the SSH tunnel "
            f"({ENV_JOB_HOST}/{ENV_SERVICES_HOST}) and retry — never chmod the stub."
        )
    return (
        f"{RETIRED_LOCAL_PLANE_MESSAGE} "
        "To ask from this notebook, set "
        f"{ENV_JOB_HOST} (or {ENV_SERVICES_HOST}) and {ENV_JOB_REPO} "
        f"(or {ENV_SERVICES_REPO}) so ask-* can forward over the existing "
        "tunnel / services.sh notebook role. "
        "Alternatively: ssh to the job host and run ask-* there."
    )


def should_attempt_ask_forward(*, repo_root: Path | None = None) -> bool:
    """True when a notebook ask must forward instead of opening local sqlite."""
    if ask_forward_already_done():
        return False
    return local_plane_is_retired(repo_root=repo_root)


def _build_remote_ask_script(
    *,
    command_target: str,
    remote_repo: str,
    task_id: str,
    source: str | None,
    model: str | None,
    effort: str | None,
    data: str | None,
    hard_timeout: int | None,
    prompt: str,
) -> bytes:
    """Build a bash-stdin program that runs ask-* on the job host.

    The prompt and optional --data body travel only in this stdin script
    (base64), never on the local ``ssh`` argv. Remote temp files are 0600 and
    cleaned on EXIT/signal. ``ENV_FORWARD_DONE=1`` prevents a second hop.
    """
    argv = [
        ".venv/bin/python",
        "scripts/ai_agent_bridge/__main__.py",
        f"ask-{command_target}",
        "-",
        "--task-id",
        task_id,
        "--stdout-only",
    ]
    if source:
        argv.extend(["--from", source])
    if model:
        argv.extend(["--to-model", model])
    if effort:
        argv.extend(["--effort", effort])
    if hard_timeout is not None:
        # Seat profile / explicit ceiling: pass via env so argparse stays stable
        # across seats that lack a dedicated timeout flag spelling.
        pass

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "payload_paths=()",
        "_cleanup() {",
        "  local status=$1",
        '  if ((${#payload_paths[@]})) && ! rm -f -- "${payload_paths[@]}"; then',
        '    [ "$status" -eq 0 ] && status=1',
        "  fi",
        '  exit "$status"',
        "}",
        "_on_exit() {",
        "  local status=$?",
        "  trap - EXIT HUP INT TERM",
        '  _cleanup "$status"',
        "}",
        "_on_signal() {",
        "  local signal=$1",
        "  trap - EXIT HUP INT TERM",
        '  _cleanup "$((128 + signal))"',
        "}",
        "trap _on_exit EXIT",
        "trap '_on_signal 1' HUP",
        "trap '_on_signal 2' INT",
        "trap '_on_signal 15' TERM",
        "umask 077",
    ]

    prompt_b64 = base64.b64encode(prompt.encode("utf-8")).decode("ascii")
    lines.extend(
        [
            "LU_ASK_PROMPT=$(mktemp /tmp/lu-ask-prompt.XXXXXX)",
            'payload_paths+=("$LU_ASK_PROMPT")',
            f"printf '%s' {shlex.quote(prompt_b64)} | base64 -d > \"$LU_ASK_PROMPT\"",
        ]
    )

    data_binding: str | None = None
    if data is not None:
        data_b64 = base64.b64encode(data.encode("utf-8")).decode("ascii")
        lines.extend(
            [
                "LU_ASK_DATA=$(mktemp /tmp/lu-ask-data.XXXXXX)",
                'payload_paths+=("$LU_ASK_DATA")',
                f"printf '%s' {shlex.quote(data_b64)} | base64 -d > \"$LU_ASK_DATA\"",
            ]
        )
        argv.extend(["--data", "__LU_REMOTE_VAR:LU_ASK_DATA"])
        data_binding = "LU_ASK_DATA"

    quoted_parts: list[str] = []
    for part in argv:
        if part.startswith("__LU_REMOTE_VAR:"):
            var = part.split(":", 1)[1]
            if data_binding is not None and var != data_binding:
                raise AskForwardError("ask forward internal payload binding mismatch")
            quoted_parts.append(f'"${var}"')
        else:
            quoted_parts.append(shlex.quote(part))
    remote_cmd = " ".join(quoted_parts)

    exports = [
        REMOTE_PATH_EXPORT,
        f"export {ENV_FORWARD_DONE}=1",
    ]
    if hard_timeout is not None:
        exports.append(f"export LU_ASK_FORWARD_HARD_TIMEOUT={int(hard_timeout)}")

    prefix = " && ".join(exports)
    lines.append(
        f"{prefix} && cd {shlex.quote(remote_repo)} && "
        f"{remote_cmd} < \"$LU_ASK_PROMPT\""
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _build_ssh_argv(host: str) -> list[str]:
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=12",
        host,
        "bash -s",
    ]


def _result_from_forward(
    *,
    participant: str,
    response: str,
    stderr_excerpt: str | None,
    returncode: int | None,
    model: str | None,
    effort: str | None,
    duration_s: float,
) -> Any:
    """Build a runner-shaped Result without importing the heavy runner module early."""
    from scripts.agent_runtime.result import Result

    ok = returncode == 0
    return Result(
        ok=ok,
        agent=participant,
        model=model or participant,
        mode="read-only",
        response=response,
        stderr_excerpt=None if ok else (stderr_excerpt or "ask forward failed"),
        duration_s=duration_s,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=returncode,
        effort=effort or "unknown",
        transport_metadata={"Via": "job-host-forward", "Agent": participant},
        transport_outcome="replied" if ok else "error",
    )


def forward_compat_ask(
    command_target: str,
    content: str,
    *,
    task_id: str,
    source: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    data: str | None = None,
    output_path: str | None = None,
    stdout_only: bool = False,
    hard_timeout: int | None = None,
    participant: str | None = None,
) -> Any:
    """SSH one ordinary ask-* onto the job host and return a Result-shaped object.

    Raises ``AskForwardError`` (clean message, no host leakage) when config or
    transport is missing. Never opens local sqlite and never sets the Mac as a
    voter or CP server.
    """
    import time

    target = resolve_ask_forward_target()
    if target is None:
        raise AskForwardError(format_ask_forward_refusal(configured=False))

    prompt = content
    if data:
        # Keep the attached body on the remote via --data file; still fold into
        # the prompt hash path by sending data separately (matches local ask).
        pass

    script = _build_remote_ask_script(
        command_target=command_target,
        remote_repo=target.remote_repo,
        task_id=task_id,
        source=source,
        model=model,
        effort=effort,
        data=data,
        hard_timeout=hard_timeout,
        prompt=prompt,
    )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            _build_ssh_argv(target.host),
            check=False,
            input=script,
            capture_output=True,
            timeout=(
                float(hard_timeout) + 60.0
                if hard_timeout is not None
                else DEFAULT_SSH_TIMEOUT_SECONDS
            ),
        )
    except FileNotFoundError as exc:
        raise AskForwardError(
            format_ask_forward_refusal(configured=True)
            + " (ssh client missing)"
        ) from exc
    except PermissionError as exc:
        raise AskForwardError(
            format_ask_forward_refusal(configured=True)
            + " (ssh not executable)"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AskForwardError(
            format_ask_forward_refusal(configured=True)
            + " (SSH transport timed out)"
        ) from exc

    duration_s = time.monotonic() - started
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    rc = int(completed.returncode)

    # OPSEC: never echo host aliases; strip common ssh banners if present.
    stderr_excerpt = None
    if rc != 0:
        cleaned = stderr.strip()
        if cleaned:
            # Bound and scrub anything that looks like a path or Host alias.
            lines = [
                line
                for line in cleaned.splitlines()
                if target.host not in line and target.remote_repo not in line
            ]
            stderr_excerpt = ("\n".join(lines) or "ask forward failed")[:500]
        else:
            stderr_excerpt = "ask forward failed"

    agent = participant or command_target
    result = _result_from_forward(
        participant=agent,
        response=stdout,
        stderr_excerpt=stderr_excerpt,
        returncode=rc,
        model=model,
        effort=effort,
        duration_s=duration_s,
    )

    response = str(getattr(result, "response", ""))
    if output_path:
        Path(output_path).write_text(response, encoding="utf-8")
    if stdout_only or response:
        # Match local _run_compat_ask_impl printing so CLI callers see the body.
        sys.stdout.write(response if response.endswith("\n") or not response else response + "\n")
        sys.stdout.flush()
    print(
        f"deprecated ask-{command_target}: ACP transport via job-host forward; "
        f"outcome={getattr(result, 'transport_outcome', None) or 'error'}",
        file=sys.stderr,
    )
    # Surface remote stderr diagnostics without host leakage.
    if stderr_excerpt:
        print(stderr_excerpt, file=sys.stderr)
    return result


def maybe_forward_compat_ask(
    command_target: str,
    content: str,
    *,
    task_id: str,
    source: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    data: str | None = None,
    output_path: str | None = None,
    stdout_only: bool = False,
    hard_timeout: int | None = None,
    participant: str | None = None,
    repo_root: Path | None = None,
) -> Any | None:
    """Forward when the local plane is retired; otherwise return None.

    When retired but forward config is missing, raises ``AskForwardError`` with
    a human message so callers never surface a raw ``PlaneRootAnchorError``.
    """
    if not should_attempt_ask_forward(repo_root=repo_root):
        # Already on the job-host leg with a retire marker still present: refuse
        # cleanly rather than recurse or open a stub.
        if ask_forward_already_done() and local_plane_is_retired(repo_root=repo_root):
            raise AskForwardError(RETIRED_LOCAL_PLANE_MESSAGE)
        return None
    return forward_compat_ask(
        command_target,
        content,
        task_id=task_id,
        source=source,
        model=model,
        effort=effort,
        data=data,
        output_path=output_path,
        stdout_only=stdout_only,
        hard_timeout=hard_timeout,
        participant=participant,
    )
