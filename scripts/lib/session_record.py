#!/usr/bin/env python3
"""Persist exact, private Claude Code session/runtime metadata."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__:
    from scripts.lib.context_profiles import resolve_profile
else:
    from context_profiles import resolve_profile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = 1
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
ALLOWED_RECORD_KEYS = {
    "schema_version",
    "session_id",
    "created_at",
    "updated_at",
    "transcript_path",
    "transcript_path_provenance",
    "session_source",
    "agent_type",
    "observed_model_id",
    "observed_model_provenance",
    "observed_context_window_tokens",
    "observed_context_window_provenance",
    "requested_profile_id",
    "effective_profile_id",
    "profile_resolution_reason",
    "profile_trusted",
    "effective_model_id",
    "effective_context_window_tokens",
    "auto_compact_capacity_tokens",
    "cold_start_profile",
    "cold_start_budget_tokens",
    "rollover_warning_percentages",
    "expected_profile_id",
    "expected_model_id",
    "expected_context_window_tokens",
    "model_mismatch",
    "window_mismatch",
    "actual_context_window_tokens",
    "actual_context_window_provenance",
    "last_update_provenance",
}


class SessionRecordError(ValueError):
    """A session record or its canonical state location is invalid."""


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def validate_session_id(session_id: str) -> bool:
    return bool(SESSION_ID_RE.fullmatch(session_id))


def validate_transcript_path(path_str: str) -> bool:
    if not path_str or "\x00" in path_str:
        return False
    path = Path(path_str)
    return path.is_absolute() and ".." not in path.parts


def canonical_state_root(project_root: Path = PROJECT_ROOT) -> Path:
    """Return the primary checkout that owns shared per-session runtime state."""
    env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        env.pop(name, None)
    result = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(project_root),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    common_dir_raw = result.stdout.strip()
    if result.returncode != 0 or not common_dir_raw:
        detail = result.stderr.strip() or "git did not report a common directory"
        raise SessionRecordError(f"cannot discover canonical session state root: {detail}")
    common_dir = Path(common_dir_raw)
    if not common_dir.is_absolute() or common_dir.name != ".git":
        raise SessionRecordError(
            f"cannot derive canonical checkout from Git common directory: {common_dir_raw!r}"
        )
    return common_dir.parent.resolve()


def sessions_dir(*, state_root: Path | None = None) -> Path:
    root = state_root.resolve() if state_root is not None else canonical_state_root()
    return root / ".agent" / "sessions"


def get_record_path(session_id: str, *, state_root: Path | None = None) -> Path:
    if not validate_session_id(session_id):
        raise SessionRecordError(f"invalid session_id: {session_id!r}")
    return sessions_dir(state_root=state_root) / f"{session_id}.json"


def _validate_record(record: Any, *, expected_session_id: str | None = None) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise SessionRecordError("session record must be a JSON object")
    unknown = sorted(set(record) - ALLOWED_RECORD_KEYS)
    if unknown:
        raise SessionRecordError(f"session record contains unsupported fields: {', '.join(unknown)}")
    if record.get("schema_version") != SCHEMA_VERSION:
        raise SessionRecordError(f"session record schema_version must be {SCHEMA_VERSION}")
    session_id = record.get("session_id")
    if not isinstance(session_id, str) or not validate_session_id(session_id):
        raise SessionRecordError("session record has an invalid session_id")
    if expected_session_id is not None and session_id != expected_session_id:
        raise SessionRecordError(
            f"session record identity mismatch: expected {expected_session_id!r}, got {session_id!r}"
        )
    transcript_path = record.get("transcript_path")
    if transcript_path is not None and (
        not isinstance(transcript_path, str) or not validate_transcript_path(transcript_path)
    ):
        raise SessionRecordError("session record has an invalid transcript_path")
    for field in (
        "observed_context_window_tokens",
        "effective_context_window_tokens",
        "expected_context_window_tokens",
        "actual_context_window_tokens",
        "auto_compact_capacity_tokens",
        "cold_start_budget_tokens",
    ):
        value = record.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            raise SessionRecordError(f"session record field {field} must be a non-negative integer")
    return dict(record)


def read_record(
    session_id: str, *, state_root: Path | None = None
) -> dict[str, Any] | None:
    path = get_record_path(session_id, state_root=state_root)
    if not path.exists():
        return None
    if not path.is_file():
        raise SessionRecordError(f"session record path is not a file: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SessionRecordError(f"cannot read session record {path}: {exc}") from exc
    return _validate_record(raw, expected_session_id=session_id)


def write_record(
    session_id: str,
    record: dict[str, Any],
    *,
    state_root: Path | None = None,
) -> Path:
    validated = _validate_record(record, expected_session_id=session_id)
    path = get_record_path(session_id, state_root=state_root)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        path.parent.chmod(0o700)

    fd, tmp_name = tempfile.mkstemp(prefix=f".{session_id}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(validated, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        path.chmod(0o600)
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            tmp_path.unlink()
    return path


def _positive_window(value: int | None, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SessionRecordError(f"{field} must be a positive integer")
    return value


def update_session(
    session_id: str,
    transcript_path: str | None = None,
    source: str | None = None,
    observed_model: str | None = None,
    agent_type: str | None = None,
    profile_id: str | None = None,
    provenance: str = "update",
    *,
    observed_context_window: int | None = None,
    transcript_path_provenance: str | None = None,
    observed_model_provenance: str | None = None,
    observed_context_window_provenance: str | None = None,
    state_root: Path | None = None,
) -> dict[str, Any]:
    """Merge official observations and a launcher route into one fail-closed record."""
    if not validate_session_id(session_id):
        raise SessionRecordError(f"invalid session_id: {session_id!r}")
    observed_context_window = _positive_window(
        observed_context_window, "observed_context_window"
    )
    record = read_record(session_id, state_root=state_root) or {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "created_at": _timestamp(),
    }

    if transcript_path is not None:
        if not validate_transcript_path(transcript_path):
            raise SessionRecordError(
                f"transcript_path must be an absolute path without traversal: {transcript_path!r}"
            )
        # Keep Claude Code's official absolute path byte-for-byte. Resolving it
        # rewrites macOS /var paths to /private/var and breaks exact correlation.
        record["transcript_path"] = transcript_path
        record["transcript_path_provenance"] = transcript_path_provenance or provenance
    if source is not None:
        record["session_source"] = source
    if agent_type is not None:
        record["agent_type"] = agent_type
    if observed_model is not None:
        record["observed_model_id"] = observed_model
        record["observed_model_provenance"] = observed_model_provenance or provenance
    if observed_context_window is not None:
        record["observed_context_window_tokens"] = observed_context_window
        record["observed_context_window_provenance"] = (
            observed_context_window_provenance or provenance
        )

    requested_profile_id = profile_id if profile_id is not None else record.get("requested_profile_id")
    observed_model_id = record.get("observed_model_id")
    profile = resolve_profile(requested_profile_id, observed_model_id)
    effective_window = profile["main_context_window_tokens"]
    expected_window = profile["expected_main_context_window_tokens"]
    observed_window = record.get("observed_context_window_tokens")

    record.update(
        {
            "requested_profile_id": profile["requested_profile_id"],
            "effective_profile_id": profile["profile_id"],
            "profile_resolution_reason": profile["resolution_reason"],
            "profile_trusted": profile["trusted"],
            "effective_model_id": profile["main_model_id"],
            "effective_context_window_tokens": effective_window,
            "auto_compact_capacity_tokens": profile["auto_compact_capacity_tokens"],
            "cold_start_profile": profile["cold_start_profile"],
            "cold_start_budget_tokens": profile["cold_start_budget_tokens"],
            "rollover_warning_percentages": profile["rollover_warning_percentages"],
            "expected_profile_id": profile["expected_profile_id"],
            "expected_model_id": profile["expected_main_model_id"],
            "expected_context_window_tokens": expected_window,
            "model_mismatch": profile["model_mismatch"],
            "window_mismatch": bool(
                observed_window
                and expected_window
                and observed_window != expected_window
            ),
            "last_update_provenance": provenance,
            "updated_at": _timestamp(),
        }
    )
    if observed_window:
        record["actual_context_window_tokens"] = observed_window
        record["actual_context_window_provenance"] = record.get(
            "observed_context_window_provenance", provenance
        )
    elif profile["trusted"] and effective_window > 0:
        record["actual_context_window_tokens"] = effective_window
        record["actual_context_window_provenance"] = "declared-profile"
    else:
        record["actual_context_window_tokens"] = None
        record["actual_context_window_provenance"] = "unavailable"

    write_record(session_id, record, state_root=state_root)
    return record


def append_to_env_file(
    record: dict[str, Any],
    *,
    env_file: Path | None = None,
    state_root: Path | None = None,
) -> None:
    """Append shell-safe, project-private session facts for later Bash calls."""
    record = _validate_record(record)
    target_raw = os.environ.get("CLAUDE_ENV_FILE") if env_file is None else os.fspath(env_file)
    if not target_raw:
        return
    target = Path(target_raw)
    if not target.is_absolute() or not target.parent.is_dir():
        raise SessionRecordError("CLAUDE_ENV_FILE must be an absolute path with an existing parent")
    record_path = get_record_path(record["session_id"], state_root=state_root)
    values = {
        "LEARN_UKRAINIAN_SESSION_ID": record["session_id"],
        "LEARN_UKRAINIAN_SESSION_RECORD": os.fspath(record_path),
        "LEARN_UKRAINIAN_TRANSCRIPT_PATH": record.get("transcript_path", ""),
        "LEARN_UKRAINIAN_PROFILE_ID": record.get("effective_profile_id", "fallback"),
        "LEARN_UKRAINIAN_REQUESTED_PROFILE_ID": record.get("requested_profile_id", ""),
        "LEARN_UKRAINIAN_MAIN_MODEL_ID": record.get("effective_model_id", "unknown"),
        "LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS": record.get(
            "effective_context_window_tokens", 0
        ),
        "LEARN_UKRAINIAN_OBSERVED_MODEL_ID": record.get("observed_model_id", ""),
        "LEARN_UKRAINIAN_OBSERVED_CONTEXT_WINDOW_TOKENS": record.get(
            "observed_context_window_tokens", ""
        ),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write("# learn-ukrainian session runtime\n")
        for name, value in values.items():
            handle.write(f"export {name}={shlex.quote(str(value))}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--session-id", required=True)
    update_parser.add_argument("--transcript-path")
    update_parser.add_argument("--source")
    update_parser.add_argument("--observed-model")
    update_parser.add_argument("--observed-context-window", type=int)
    update_parser.add_argument("--agent-type")
    update_parser.add_argument("--profile-id")
    update_parser.add_argument("--provenance", default="cli")
    update_parser.add_argument("--transcript-path-provenance")
    update_parser.add_argument("--observed-model-provenance")
    update_parser.add_argument("--observed-context-window-provenance")
    update_parser.add_argument("--append-env", action="store_true")

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("--session-id", required=True)
    get_parser.add_argument("--field")
    args = parser.parse_args()

    try:
        if args.command == "update":
            record = update_session(
                session_id=args.session_id,
                transcript_path=args.transcript_path,
                source=args.source,
                observed_model=args.observed_model,
                observed_context_window=args.observed_context_window,
                agent_type=args.agent_type,
                profile_id=args.profile_id,
                provenance=args.provenance,
                transcript_path_provenance=args.transcript_path_provenance,
                observed_model_provenance=args.observed_model_provenance,
                observed_context_window_provenance=args.observed_context_window_provenance,
                state_root=args.state_root,
            )
            if args.append_env:
                append_to_env_file(record, state_root=args.state_root)
            print(json.dumps(record, indent=2, sort_keys=True))
            return 0

        record = read_record(args.session_id, state_root=args.state_root)
        if record is None:
            raise SessionRecordError(f"record not found for session {args.session_id}")
        if args.field:
            if args.field not in record:
                raise SessionRecordError(f"field not found in session record: {args.field}")
            value = record[args.field]
            print(json.dumps(value) if isinstance(value, (dict, list, bool)) else value)
        else:
            print(json.dumps(record, indent=2, sort_keys=True))
        return 0
    except (OSError, SessionRecordError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
