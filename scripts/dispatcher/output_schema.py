"""Bind dispatcher schemas using the native adapters' checked parent reads."""

import os
from json import JSONDecodeError
from pathlib import Path

from jsonschema.exceptions import SchemaError

from scripts.agent_runtime.adapters._output_schema import load_output_schema
from scripts.agent_runtime.attempt_safe_read import AttemptReadError, safe_read_attempt_file
from scripts.dispatcher.store import digest


def load(options):
    try:
        return load_output_schema(options)
    except (AttemptReadError, SchemaError, UnicodeError, JSONDecodeError) as exc:
        raise ValueError("output schema is unsafe or invalid") from exc


def bind(raw_path: str, repo: Path) -> dict[str, str]:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
        if not Path(os.path.abspath(candidate)).is_relative_to(repo.resolve()):
            raise ValueError("relative output schema must be inside the repository")
    candidate = Path(os.path.abspath(candidate))
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ValueError("output schema is not a readable file") from exc
    if resolved != candidate:
        raise ValueError("output schema path must not traverse symlinks")
    root = candidate.parent
    try:
        payload = safe_read_attempt_file(candidate, trusted_root=root)
    except AttemptReadError as exc:
        raise ValueError("output schema is not a readable regular file") from exc
    options = dict(output_schema_path=str(candidate), output_schema_sha256=digest(payload), review_write_root=str(root))
    load(options)
    return options
