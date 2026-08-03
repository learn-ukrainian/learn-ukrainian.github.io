"""Optional Entire lifecycle capture for unsupported project-runner hosts.

Capture ownership is selected by the physical subprocess host, never by the
model label.  Native Entire hosts therefore never enter this module.  The
private transcript spool exists only while synchronous ``entire hooks`` calls
need it and is deleted after the terminal hook attempt.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root

_LOGGER = logging.getLogger(__name__)
_OWNED_HOSTS = frozenset({"agy", "cursor-headless", "grok", "hermes"})
_SESSION_RE = re.compile(r"^fleet-[0-9a-f]{32}$")
_SAFE_META_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+ -]{0,255}$")
_HOOK_TIMEOUT_SECONDS = 5
_SESSION_END_TIMEOUT_SECONDS = 30
_STALE_SECONDS = 24 * 60 * 60


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_metadata(value: Mapping[str, object]) -> dict[str, str]:
    safe: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key).strip()
        text = str(raw_value or "").strip()
        if not key or not text or not _SAFE_META_RE.fullmatch(text):
            continue
        safe[key[:64]] = text
    return safe


def _status_paths(repo_path: Path) -> set[str]:
    """Return body-free dirty paths, or an empty set outside a Git worktree."""
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(repo_path),
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            ],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if completed.returncode != 0:
        return set()
    paths: set[str] = set()

    def add_path(raw_path: bytes) -> None:
        path = raw_path.decode("utf-8", errors="replace").strip()
        if path and not path.startswith("batch_state/entire/"):
            paths.add(path[:4096])

    records = completed.stdout.split(b"\0")
    index = 0
    while index < len(records):
        raw = records[index]
        index += 1
        if len(raw) < 4:
            continue
        status = raw[:2]
        add_path(raw[3:])
        if b"R" not in status and b"C" not in status:
            continue
        # In porcelain v1 -z output Git reverses ``from -> to`` and emits
        # ``XY to\0from\0``.  The second path has no status prefix.
        if index < len(records):
            add_path(records[index])
            index += 1
    return paths


def _atomic_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    encoded = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    ).encode("utf-8")
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        path.chmod(0o600)
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def _cleanup_stale(root: Path, *, now: float | None = None) -> None:
    cutoff = (time.time() if now is None else now) - _STALE_SECONDS
    try:
        children = list(root.iterdir())
    except OSError:
        return
    for child in children:
        if not child.is_dir() or not _SESSION_RE.fullmatch(child.name):
            continue
        try:
            if child.stat().st_mtime >= cutoff:
                continue
            shutil.rmtree(child)
        except OSError:
            continue


def _capture_root(runtime_repo_root: Path) -> Path:
    return (
        main_checkout_root(runtime_repo_root.resolve())
        / "batch_state"
        / "entire"
        / "fleet-sessions"
        / "v1"
    )


@dataclass
class FleetCapture:
    """One physical runner subprocess attempt."""

    session_id: str
    harness: str
    runner_agent: str
    entrypoint: str
    requested_model: str
    repo_path: Path
    root: Path
    session_dir: Path
    transcript_path: Path
    started_at: str
    baseline_paths: set[str]
    records: list[dict[str, object]] = field(default_factory=list)
    _closed: bool = False

    @classmethod
    def start(
        cls,
        *,
        host_harness: str | None,
        runner_agent: str,
        entrypoint: str,
        requested_model: str,
        prompt: str,
        repo_path: Path,
        runtime_repo_root: Path,
        plan_metadata: Mapping[str, object] | None = None,
    ) -> FleetCapture | None:
        harness = str(host_harness or "").strip().lower()
        if harness not in _OWNED_HOSTS or os.environ.get("ENTIRE_FLEET_CAPTURE_DISABLE") == "1":
            return None
        if shutil.which("entire") is None:
            return None

        root = _capture_root(runtime_repo_root)
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        root.chmod(0o700)
        _cleanup_stale(root)
        session_id = f"fleet-{uuid.uuid4().hex}"
        session_dir = root / session_id
        session_dir.mkdir(mode=0o700)
        session_dir.chmod(0o700)
        transcript_path = session_dir / "transcript.jsonl"
        started_at = _now()

        model_meta: dict[str, object] = {}
        if isinstance(plan_metadata, Mapping):
            raw = plan_metadata.get("entire_fleet")
            if isinstance(raw, Mapping):
                model_meta = dict(raw)
            hermes = plan_metadata.get("hermes")
            if isinstance(hermes, Mapping):
                model_meta.update(
                    {
                        "requested_provider": hermes.get("requested_provider"),
                        "requested_model": hermes.get("requested_model"),
                    }
                )

        requested = str(model_meta.get("requested_model") or requested_model).strip()
        capture = cls(
            session_id=session_id,
            harness=harness,
            runner_agent=str(runner_agent).strip(),
            entrypoint=str(entrypoint).strip(),
            requested_model=requested,
            repo_path=repo_path.resolve(),
            root=root,
            session_dir=session_dir,
            transcript_path=transcript_path,
            started_at=started_at,
            baseline_paths=_status_paths(repo_path),
        )
        try:
            capture.records.extend(
                [
                    {
                        "type": "session",
                        "session_id": session_id,
                        "timestamp": started_at,
                        "repo_path": str(capture.repo_path),
                        "metadata": capture._metadata(model_meta),
                    },
                    {"type": "user", "timestamp": started_at, "text": prompt},
                ]
            )
            _atomic_jsonl(transcript_path, capture.records)
            capture._hook("session-start", metadata=model_meta)
            capture._hook("turn-start", prompt=prompt, metadata=model_meta)
            return capture
        except Exception:
            with contextlib.suppress(OSError):
                shutil.rmtree(session_dir)
            raise

    def _metadata(self, extra: Mapping[str, object] | None = None) -> dict[str, str]:
        values: dict[str, object] = {
            "harness": self.harness,
            "runner_agent": self.runner_agent,
            "entrypoint": self.entrypoint,
            "requested_model": self.requested_model,
        }
        if extra:
            values.update(extra)
        return _safe_metadata(values)

    def _hook(
        self,
        hook: str,
        *,
        prompt: str = "",
        metadata: Mapping[str, object] | None = None,
    ) -> bool:
        entire = shutil.which("entire")
        if not entire:
            return False
        payload: dict[str, object] = {
            "hook_type": hook,
            "session_id": self.session_id,
            "session_ref": str(self.transcript_path),
            "timestamp": _now(),
            "raw_data": self._metadata(metadata),
        }
        if prompt:
            payload["user_prompt"] = prompt
        env = dict(os.environ)
        env["ENTIRE_REPO_ROOT"] = str(self.repo_path)
        env["ENTIRE_FLEET_CAPTURE_ROOT"] = str(self.root)
        try:
            completed = subprocess.run(
                [entire, "hooks", "fleet", hook],
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=(
                    _SESSION_END_TIMEOUT_SECONDS
                    if hook == "session-end"
                    else _HOOK_TIMEOUT_SECONDS
                ),
                env=env,
                cwd=str(self.repo_path),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            _LOGGER.warning("Entire fleet hook %s unavailable: %s", hook, type(exc).__name__)
            return False
        if completed.returncode != 0:
            _LOGGER.warning("Entire fleet hook %s failed rc=%s", hook, completed.returncode)
            return False
        return True

    def finish(
        self,
        *,
        response: str,
        outcome: str,
        returncode: int | None,
        actual_model: str | None = None,
        route_metadata: Mapping[str, object] | None = None,
    ) -> None:
        if self._closed:
            return
        self._closed = True
        actual_known = str(
            (route_metadata or {}).get("actual_model_known", "true")
        ).lower() != "false"
        actual = str(
            actual_model or (self.requested_model if actual_known else "")
        ).strip()
        metadata: dict[str, object] = {
            "actual_model": actual,
            "outcome": str(outcome).strip(),
        }
        if returncode is not None:
            metadata["returncode"] = str(returncode)
        if route_metadata:
            metadata.update(route_metadata)
        ended_at = _now()
        try:
            self.records.append(
                {
                    "type": "assistant",
                    "timestamp": ended_at,
                    "text": response,
                    "model": actual,
                    "metadata": self._metadata(metadata),
                }
            )
            changed_paths = sorted(_status_paths(self.repo_path) - self.baseline_paths)
            for path in changed_paths:
                self.records.append({"type": "file", "path": path, "timestamp": ended_at})
            self.records.append(
                {
                    "type": "terminal",
                    "timestamp": ended_at,
                    "metadata": self._metadata(metadata),
                }
            )
            _atomic_jsonl(self.transcript_path, self.records)
            self._hook("turn-end", metadata=metadata)
            self._hook("session-end", metadata=metadata)
        except Exception as exc:  # Entire is optional and must not change provider behavior.
            _LOGGER.warning("Entire fleet capture finalization failed: %s", type(exc).__name__)
        finally:
            with contextlib.suppress(OSError):
                shutil.rmtree(self.session_dir)


def resolved_route(
    *,
    requested_model: str,
    plan_metadata: Mapping[str, object] | None,
    substitution: Mapping[str, object] | None,
) -> tuple[str, dict[str, object]]:
    """Resolve truthful requested/actual route without inspecting body output."""
    requested = requested_model
    actual = requested_model
    route: dict[str, object] = {}
    if isinstance(plan_metadata, Mapping):
        raw = plan_metadata.get("entire_fleet")
        if isinstance(raw, Mapping):
            requested = str(raw.get("requested_model") or requested).strip()
            known = str(raw.get("actual_model_known", "true")).lower() != "false"
            actual = str(raw.get("actual_model") or (requested if known else "")).strip()
            if not known:
                route["actual_model_known"] = "false"
        hermes = plan_metadata.get("hermes")
        if isinstance(hermes, Mapping):
            route["requested_provider"] = hermes.get("requested_provider") or ""
            requested = str(hermes.get("requested_model") or requested).strip()
            actual = requested
    if isinstance(substitution, Mapping):
        requested = str(substitution.get("requested_model") or requested).strip()
        actual = str(substitution.get("actual_model") or actual).strip()
        route.update(
            {
                "requested_provider": substitution.get("requested_provider") or "",
                "actual_provider": substitution.get("actual_provider") or "",
            }
        )
    route["requested_model"] = requested
    route["actual_model"] = actual
    return actual, route


__all__ = ["FleetCapture", "resolved_route"]
