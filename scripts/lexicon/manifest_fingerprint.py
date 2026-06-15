"""DB-free freshness fingerprint for the Word Atlas manifest.

The enriched Atlas manifest depends on local dictionary databases that CI does
not have. This module fingerprints the inputs CI can see: lexicon source files
and the set of taught vocabulary lemmas.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FINGERPRINT = ROOT / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
LEXICON_CODE_GLOB = "scripts/lexicon/*.py"
VOCABULARY_GLOB = "curriculum/l2-uk-en/*/*/vocabulary.yaml"
LEMMA_FIELDS = ("lemma", "word", "uk", "term")
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


def _entry_lemma(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    for field in LEMMA_FIELDS:
        value = entry.get(field)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def vocabulary_lemmas(root: Path = ROOT) -> list[str]:
    """Return the sorted unique lemma-like values from module vocabulary YAML."""
    lemmas: set[str] = set()
    for path in sorted(root.glob(VOCABULARY_GLOB), key=lambda item: _repo_relative(item, root)):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if not isinstance(raw, list):
            continue
        for entry in raw:
            lemma = _entry_lemma(entry)
            if lemma:
                lemmas.add(lemma)
    return sorted(lemmas)


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
    lemmas = vocabulary_lemmas(root)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "scope": "lexicon code + module vocabulary lemmas; excludes dictionary DB/cache state",
        "inputs": {
            "lexicon_code": code_inputs,
            "vocabulary_lemmas": lemmas,
        },
    }
    return {
        **payload,
        "fingerprint": _sha256_bytes(_canonical_json(payload)),
        "stats": {
            "lexicon_code_files": len(code_inputs),
            "vocabulary_lemmas": len(lemmas),
        },
    }


def write_fingerprint(path: Path = DEFAULT_FINGERPRINT, *, root: Path = ROOT) -> dict[str, Any]:
    """Write the deterministic fingerprint sidecar and return its payload."""
    payload = build_fingerprint(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
