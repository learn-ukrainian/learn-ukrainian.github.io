"""Per-attempt stdio sources MCP launcher and receipt ledger provisioner.

Issue: #8517 (Refs #8430, #8397)

Provisions a per-attempt MCP configuration and empty receipt ledger for review
seats. Formal reviews require audit-grade receipts recorded over stdio via
attempt-specific environment variables:
- LU_REVIEW_ATTEMPT_ID
- LU_REVIEW_MANIFEST_SHA256
- LU_REVIEW_LEDGER_PATH

The generated MCP configuration defines exclusively a `sources` server started
over stdio from the primary checkout's virtual environment and server script,
bypassing the shared streamable-HTTP daemon (127.0.0.1:8766).

Note: Ledger creation and sidecar management will be consolidated once R1
(cursor/impl-review-r1-schema-ledger) merges to main.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.common.repo_root import resolve_repo_root

ENV_ATTEMPT_ID = "LU_REVIEW_ATTEMPT_ID"
ENV_MANIFEST_SHA256 = "LU_REVIEW_MANIFEST_SHA256"
ENV_LEDGER_PATH = "LU_REVIEW_LEDGER_PATH"
ENV_KEYS = (ENV_ATTEMPT_ID, ENV_MANIFEST_SHA256, ENV_LEDGER_PATH)

SUPPORTED_HARNESSES: frozenset[str] = frozenset({"claude", "cursor"})

UNSUPPORTED_HARNESS_REASONS: dict[str, str] = {
    "agy": "AGY has one global MCP config (~/.gemini/config/mcp_config.json) without per-invocation MCP config support",
    "gemini": "Gemini has one global MCP config without per-invocation MCP config support",
    "codex": "not yet proven",
    "grok": "not yet proven",
    "grok-build": "not yet proven",
    "kimicc": "not yet supported",
    "kimi": "Native Kimi Code reads global profile config and cannot take a per-attempt stdio config",
    "grok-hermes": "Hermes-routed agents read global ~/.hermes/config.yaml and cannot take a per-attempt stdio config",
    "deepseek": "Hermes-routed agents read global ~/.hermes/config.yaml and cannot take a per-attempt stdio config",
    "qwen": "Hermes-routed agents read global ~/.hermes/config.yaml and cannot take a per-attempt stdio config",
}

_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@dataclass(frozen=True)
class ReviewMcpPlan:
    """Plan and options for running a review attempt with isolated stdio sources MCP."""

    config_path: Path
    adapter_options: dict[str, Any]
    ledger_path: Path
    sidecar_path: Path
    manifest_sha256: str
    review_id: str
    attempt_id: str
    harness: str

    @property
    def mcp_config_path(self) -> Path:
        return self.config_path

    @property
    def strict_mcp_config(self) -> bool:
        return True


def prepare_review_attempt(
    review_id: str,
    attempt_id: str,
    manifest_path: Path | str,
    harness: str,
    *,
    receipts_root: Path | None = None,
) -> ReviewMcpPlan:
    """Prepare the per-attempt stdio sources MCP config, empty ledger, and sidecar.

    Args:
        review_id: Identifier of the formal review job.
        attempt_id: Unique attempt identifier.
        manifest_path: Path to the review manifest YAML.
        harness: Agent harness name (e.g. 'claude', 'cursor').
        receipts_root: Optional override for the receipts base directory (used in tests).

    Returns:
        ReviewMcpPlan containing the written config path and adapter options.

    Raises:
        ValueError: If tokens are invalid or harness is unsupported.
        FileExistsError: If ledger, sidecar, or config already exists.
        FileNotFoundError: If manifest_path does not exist.
    """
    if not isinstance(review_id, str) or not _TOKEN_RE.match(review_id):
        raise ValueError(f"invalid review_id: {review_id!r}")
    if not isinstance(attempt_id, str) or not _TOKEN_RE.match(attempt_id):
        raise ValueError(f"invalid attempt_id: {attempt_id!r}")

    canonical_harness = (harness or "").lower().strip()
    if canonical_harness in UNSUPPORTED_HARNESS_REASONS:
        raise ValueError(
            f"review attempt refused for {canonical_harness}: {UNSUPPORTED_HARNESS_REASONS[canonical_harness]} (#8517)"
        )
    if canonical_harness not in SUPPORTED_HARNESSES:
        raise ValueError(f"review attempt refused for unsupported harness {canonical_harness!r} (#8517)")

    manifest_file = Path(manifest_path).resolve()
    if not manifest_file.is_file():
        raise FileNotFoundError(f"review manifest file not found: {manifest_file}")

    manifest_bytes = manifest_file.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    # Primary checkout root: resolved via repository helper scripts.common.repo_root
    primary_root = resolve_repo_root(Path(__file__), 2)
    python_bin = primary_root / ".venv" / "bin" / "python"
    sources_server = primary_root / ".mcp" / "servers" / "sources" / "server.py"

    base_dir = receipts_root if receipts_root is not None else (primary_root / "batch_state" / "review-receipts")
    review_dir = base_dir / review_id
    review_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = review_dir / f"{attempt_id}.jsonl"
    sidecar_path = review_dir / f"{attempt_id}.jsonl.sha256"
    config_path = review_dir / f"{attempt_id}.mcp.json"

    # Driver settlement 5: create ledger, sidecar, and config with O_EXCL; refuse if any already exists
    if ledger_path.exists() or sidecar_path.exists() or config_path.exists():
        raise FileExistsError(
            f"review attempt {attempt_id!r} already exists for review {review_id!r}"
        )

    sidecar_bytes = f"{_EMPTY_SHA256}\n".encode("ascii")
    config_payload = {
        "mcpServers": {
            "sources": {
                "command": str(python_bin),
                "args": [str(sources_server)],
                "env": {
                    ENV_ATTEMPT_ID: attempt_id,
                    ENV_MANIFEST_SHA256: manifest_sha256,
                    ENV_LEDGER_PATH: str(ledger_path),
                },
            }
        }
    }
    config_bytes = (json.dumps(config_payload, indent=2) + "\n").encode("utf-8")

    created_paths: list[Path] = []
    try:
        # Create empty ledger (0 bytes, 0o644) exclusively
        fd_ledger = os.open(ledger_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        os.close(fd_ledger)
        created_paths.append(ledger_path)

        # Create sidecar containing empty SHA-256 + newline exclusively
        fd_sidecar = os.open(sidecar_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd_sidecar, "wb") as handle:
            handle.write(sidecar_bytes)
        created_paths.append(sidecar_path)

        # Create config exclusively
        fd_config = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd_config, "wb") as handle:
            handle.write(config_bytes)
        created_paths.append(config_path)
    except FileExistsError as exc:
        for path in reversed(created_paths):
            with contextlib.suppress(OSError):
                path.unlink(missing_ok=True)
        raise FileExistsError(
            f"review attempt {attempt_id!r} already exists for review {review_id!r}"
        ) from exc
    except BaseException:
        for path in reversed(created_paths):
            with contextlib.suppress(OSError):
                path.unlink(missing_ok=True)
        raise

    adapter_options: dict[str, Any] = {
        "mcp_config_path": str(config_path),
        "strict_mcp_config": True,
        "mcp_server_names": ["sources"],
    }

    return ReviewMcpPlan(
        config_path=config_path,
        adapter_options=adapter_options,
        ledger_path=ledger_path,
        sidecar_path=sidecar_path,
        manifest_sha256=manifest_sha256,
        review_id=review_id,
        attempt_id=attempt_id,
        harness=canonical_harness,
    )
