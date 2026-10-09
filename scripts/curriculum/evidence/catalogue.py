"""Catalogue suggestions for lesson requirements; never pack evidence or host bindings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.validate.loader import read_plan_text, retirement_record
from scripts.ingest.resource_catalogue_ingest import MAX_HITS, ResourceCatalogueMissingError

from .sources import Sources


def request_report(plan_path: Path, words_path: Path, source: Sources) -> dict[str, Any]:
    """Record literal free-resource searches, including empty and unavailable results.

    Core, incidental and recycled inventory words constitute each lesson's word
    requirements. Recycled ids are resolved through the level word store. A
    missing plan/store is explicit rather than an assertion of no resources.
    """
    result: dict[str, Any] = {
        "status": "ok",
        "suggestions_only": True,
        "free_only": True,
        "candidate_limit": MAX_HITS,
        "queries": [],
        "notes": [],
    }
    retirement_record(plan_path.parent)
    if not plan_path.is_file():
        result.update(status="not_checked", notes=[{"code": "catalogue_plan_unavailable"}])
        return result
    plan = yaml.safe_load(read_plan_text(plan_path))
    if not isinstance(plan, dict) or not isinstance(plan.get("lessons"), list):
        raise ValueError("catalogue_plan_invalid: expected lesson plan with lessons list")
    words = yaml.safe_load(words_path.read_text(encoding="utf-8")) if words_path.is_file() else {}
    lemmas = {w["id"]: w["lemma"] for w in (words or {}).get("words", [])}
    unavailable = None
    for lesson in plan["lessons"]:
        inventory = lesson.get("inventory") or {}
        vocabulary = inventory.get("vocabulary") or {}
        requirements = [
            ("word", item["lemma"], item.get("evidence"))
            for group in ("core", "incidental")
            for item in vocabulary.get(group, [])
        ]
        requirements.extend(("word", lemmas.get(ref), ref) for ref in vocabulary.get("recycled", []))
        requirements.extend(
            ("letter", letter, None) for letter in (inventory.get("phonetics") or {}).get("letters", [])
        )
        # Preserve attribution across lessons; deduplicate repeated requirements only within one lesson.
        for kind, query, ref in dict.fromkeys(requirements):
            entry = {
                "lesson": lesson["n"],
                "lesson_slug": lesson["slug"],
                "requirement_kind": kind,
                "requirement": query if query is not None else ref,
                "evidence": ref,
                "query": query,
                "status": "ok",
                "candidates": [],
                "query_mode": "letter_index" if kind == "letter" else "text",
            }
            if query is None:
                entry.update(status="not_checked", note={"code": "catalogue_word_unresolved"})
                result["status"] = "not_checked"
            else:
                if unavailable is None:
                    try:
                        hits = source.search_resources(
                            query, mode="letter" if kind == "letter" else "text", free_only=True, limit=MAX_HITS
                        )
                    except (FileNotFoundError, ResourceCatalogueMissingError):
                        unavailable = {"code": "catalogue_unavailable"}
                        result["notes"].append(unavailable)
                    else:
                        entry["candidates"] = [
                            {field: hit[field] for field in ("id", "title", "url", "access", "kind")}
                            for hit in hits
                            if kind != "letter" or query.strip().upper() in hit.get("letters", [])
                        ]
                if unavailable is not None:
                    entry.update(status="not_checked", note=unavailable)
                    result["status"] = "not_checked"
            result["queries"].append(entry)
    return result
