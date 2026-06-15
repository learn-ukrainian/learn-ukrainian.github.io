"""DB-free freshness fingerprint for the Word Atlas manifest.

The enriched Atlas manifest depends on local dictionary databases that CI does
not have. This module fingerprints the lexicon source files CI can see.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FINGERPRINT = ROOT / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
LEXICON_CODE_GLOB = "scripts/lexicon/*.py"
SCHEMA_VERSION = 1


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def lexicon_code_inputs(root: Path = ROOT) -> list[dict[str, str]]:
    """Return sorted lexicon Python source content hashes."""
    root = root.resolve()
    files = sorted(root.glob(LEXICON_CODE_GLOB), key=lambda path: _repo_relative(path, root))
    return [
        {
            "path": _repo_relative(path, root),
            "sha256": _sha256_bytes(path.read_bytes()),
        }
        for path in files
        if path.is_file()
    ]


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def build_fingerprint(root: Path = ROOT) -> dict[str, Any]:
    """Build the deterministic sidecar payload."""
    code_inputs = lexicon_code_inputs(root)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "scope": "lexicon code only; excludes module vocabulary and dictionary DB/cache state",
        "inputs": {
            "lexicon_code": code_inputs,
        },
    }
    return {
        **payload,
        "fingerprint": _sha256_bytes(_canonical_json(payload)),
        "stats": {
            "lexicon_code_files": len(code_inputs),
        },
    }


def write_fingerprint(path: Path = DEFAULT_FINGERPRINT, *, root: Path = ROOT) -> dict[str, Any]:
    """Write the deterministic fingerprint sidecar and return its payload."""
    payload = build_fingerprint(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
