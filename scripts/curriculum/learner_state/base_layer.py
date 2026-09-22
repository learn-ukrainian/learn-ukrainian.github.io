"""Base layer contract and resolution against the level word store (issue #8414).

The base layer is a request file for the word store:
  curriculum/l2-uk-en/evidence/<level>/_base.request.yaml
(schema evidence-words-request-v1), built into _words.yaml with ids allocated like
any record.

How base_ids are found: joins each request line on (lemma, pos, entry) against
_words.yaml. entry is required in the request whenever the store has more than one
record for (lemma, pos). A line that matches zero or several records fails
base_layer_unresolved naming the line. Missing _base.request.yaml or records fails
base_layer_missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import codes

REPO_ROOT = Path(__file__).resolve().parents[3]


class BaseLayerError(Exception):
    """Failure outcome in base layer resolution."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _matches_entry(store_entry: Any, req_entry: dict[str, Any] | None) -> bool:
    """Check if a word store entry matches the request line entry disambiguation."""
    if req_entry is None:
        return True
    if not isinstance(store_entry, dict):
        return False
    source = req_entry.get("source")
    if source == "vesum":
        return store_entry.get("source") == "vesum" and store_entry.get("entry_id") == req_entry.get("entry_id")
    if source == "ulif":
        req_hi = req_entry.get("homonym_index")
        if store_entry.get("source") != "ulif":
            return False
        store_key = store_entry.get("key")
        return isinstance(store_key, (list, tuple)) and len(store_key) >= 2 and store_key[1] == req_hi
    return store_entry == req_entry


def resolve_base_ids(
    level: str,
    *,
    evidence_dir: Path | None = None,
    words_path: Path | None = None,
    base_request_path: Path | None = None,
) -> tuple[str, ...]:
    """Join each request line in _base.request.yaml against _words.yaml.

    Returns the tuple of resolved W- IDs sorted for determinism.
    Raises BaseLayerError with code BASE_LAYER_MISSING or BASE_LAYER_UNRESOLVED.
    """
    evidence_root = evidence_dir or (REPO_ROOT / f"curriculum/l2-uk-en/evidence/{level}")
    base_request_path = base_request_path or (evidence_root / "_base.request.yaml")
    words_path = words_path or (evidence_root / "_words.yaml")

    if not base_request_path.is_file():
        raise BaseLayerError(
            codes.BASE_LAYER_MISSING,
            f"base layer request file does not exist: {base_request_path}",
        )
    if not words_path.is_file():
        raise BaseLayerError(
            codes.BASE_LAYER_MISSING,
            f"level word store file does not exist: {words_path}",
        )

    try:
        req_data = yaml.safe_load(base_request_path.read_text(encoding="utf-8"))
    except Exception as err:
        raise BaseLayerError(
            codes.BASE_LAYER_MISSING,
            f"base layer request {base_request_path} is not valid YAML: {err}",
        ) from err

    try:
        words_data = yaml.safe_load(words_path.read_text(encoding="utf-8"))
    except Exception as err:
        raise BaseLayerError(
            codes.BASE_LAYER_MISSING,
            f"word store {words_path} is not valid YAML: {err}",
        ) from err

    if not isinstance(req_data, dict) or not isinstance(req_data.get("words"), list) or not req_data["words"]:
        raise BaseLayerError(
            codes.BASE_LAYER_MISSING,
            f"base layer request {base_request_path} has missing or empty words list",
        )

    if not isinstance(words_data, dict) or not isinstance(words_data.get("words"), list):
        raise BaseLayerError(
            codes.BASE_LAYER_MISSING,
            f"word store {words_path} has missing or malformed words list",
        )

    store_words: list[dict[str, Any]] = words_data["words"]
    resolved_ids: list[str] = []

    for idx, req_line in enumerate(req_data["words"]):
        if not isinstance(req_line, dict):
            raise BaseLayerError(
                codes.BASE_LAYER_MISSING,
                f"base layer request line {idx + 1} in {base_request_path} is not a mapping",
            )
        lemma = req_line.get("lemma")
        pos = req_line.get("pos")
        req_entry = req_line.get("entry")
        line_desc = f"line {idx + 1} (lemma={lemma!r}, pos={pos!r}, entry={req_entry!r})"

        if not lemma or not pos:
            raise BaseLayerError(
                codes.BASE_LAYER_MISSING,
                f"base layer {line_desc} missing required lemma or pos",
            )

        # Candidates matching lemma and pos
        candidates = [w for w in store_words if isinstance(w, dict) and w.get("lemma") == lemma and w.get("pos") == pos]

        # If entry is specified, disambiguate with it
        if req_entry is not None:
            candidates = [c for c in candidates if _matches_entry(c.get("entry"), req_entry)]

        if len(candidates) != 1:
            raise BaseLayerError(
                codes.BASE_LAYER_UNRESOLVED,
                f"base layer {line_desc} matched {len(candidates)} records in {words_path} "
                "(expected exactly 1; entry disambiguation required if multiple exist)",
            )

        matched_id = candidates[0].get("id")
        if not matched_id or not str(matched_id).startswith("W-"):
            raise BaseLayerError(
                codes.BARE_LEMMA,
                f"base layer {line_desc} resolved to non-word-store id {matched_id!r}",
            )
        resolved_ids.append(str(matched_id))

    return tuple(sorted(set(resolved_ids)))
