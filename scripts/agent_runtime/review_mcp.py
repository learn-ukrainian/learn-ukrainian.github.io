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

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.common.repo_root import resolve_repo_root

ENV_ATTEMPT_ID = "LU_REVIEW_ATTEMPT_ID"
ENV_MANIFEST_SHA256 = "LU_REVIEW_MANIFEST_SHA256"
ENV_LEDGER_PATH = "LU_REVIEW_LEDGER_PATH"
ENV_KEYS = (ENV_ATTEMPT_ID, ENV_MANIFEST_SHA256, ENV_LEDGER_PATH)

SUPPORTED_HARNESSES: frozenset[str] = frozenset({"claude", "grok", "grok-build", "cursor", "kimicc"})

UNSUPPORTED_HARNESS_REASONS: dict[str, str] = {
    "agy": "AGY has one global MCP config (~/.gemini/config/mcp_config.json) without per-invocation MCP config support",
    "gemini": "Gemini has one global MCP config without per-invocation MCP config support",
    "codex": "Codex internal read-only sandbox cancels unapproved stdio MCP calls and cannot configure per-attempt stdio servers with environment variables",
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
        harness: Agent harness name (e.g. 'claude', 'grok', 'cursor').
        receipts_root: Optional override for the receipts base directory (used in tests).

    Returns:
        ReviewMcpPlan containing the written config path and adapter options.

    Raises:
        ValueError: If tokens are invalid or harness is unsupported.
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
    alt_sidecar_path = review_dir / f"{attempt_id}.sha256"
    config_path = review_dir / f"{attempt_id}.mcp.json"

    # Create empty ledger if absent (0 bytes, 0o644)
    if not ledger_path.exists():
        ledger_path.write_bytes(b"")
        ledger_path.chmod(0o644)

    # Create sidecar containing empty SHA-256 + newline (0o644)
    sidecar_bytes = f"{_EMPTY_SHA256}\n".encode("ascii")
    sidecar_path.write_bytes(sidecar_bytes)
    sidecar_path.chmod(0o644)
    # Also write alt sidecar <attempt_id>.sha256 for convention compatibility
    alt_sidecar_path.write_bytes(sidecar_bytes)
    alt_sidecar_path.chmod(0o644)

    # Write per-attempt MCP config defining ONLY sources over stdio
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
    config_path.write_text(json.dumps(config_payload, indent=2) + "\n", encoding="utf-8")
    config_path.chmod(0o644)

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
