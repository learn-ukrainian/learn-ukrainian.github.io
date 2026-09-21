"""Canonical typed sanctioned Sources handlers, backed only by Sources-owned IO."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.types import TextContent

from learn_ukrainian_v4_runtime.operation_auth import HEX64, OperationRefused
from learn_ukrainian_v4_runtime.tool_result_envelope import enrich_typed_outcome
from learn_ukrainian_v4_runtime.v4_canonical_authority_store import immutable_evidence_identifier
from learn_ukrainian_v4_runtime.vesum_presentation import tag_gloss

_backend = None


def configure_backend(resource):
    global _backend
    _backend = resource


def backend():
    if _backend is None:
        raise OperationRefused("Sources backend unavailable")
    return _backend


def _typed_identifier(namespace: str, typed_result: dict[str, Any]) -> str:
    version = backend().source_version()
    if not isinstance(version, str) or not HEX64.fullmatch(version):
        raise OperationRefused("Sources version unproved")
    return immutable_evidence_identifier(namespace=namespace, source_version=version, typed_result=typed_result)


def _is_archaic(tags: str | None) -> bool:
    """Helper to check if 'arch' tag exists in VESUM tag string."""
    if not tags:
        return False
    return "arch" in tags.split(":")


async def handle_check_modern_form(args: dict):
    word = args.get("word")
    query = {"word": word}
    if not isinstance(word, str) or not word.strip():
        prose = json.dumps(
            {
                "tool": "check_modern_form",
                "disposition": "invalid_input",
                "success": False,
                "evidence_identifiers": [],
            },
            ensure_ascii=False,
        )
        outcome = {
            "tool": "check_modern_form",
            "disposition": "invalid_input",
            "success": False,
            "evidence_identifiers": [],
        }
        enrich_typed_outcome(outcome, query=query, match_count=0, hits=[], summary_prose=prose)
        return [TextContent(type="text", text=prose)], outcome

    verify_word = backend().verify_word
    matches = await asyncio.to_thread(verify_word, word, None)
    if not matches:
        payload = {
            "is_modern_codified": False,
            "has_archaic_form": False,
            "has_only_archaic_form": False,
            "error": "Word not found in VESUM.",
        }
        prose = json.dumps(payload, ensure_ascii=False)
        outcome = {
            "tool": "check_modern_form",
            "disposition": "not_found",
            "success": False,
            "evidence_identifiers": [],
            "result": payload,
        }
        enrich_typed_outcome(outcome, query=query, match_count=0, hits=[], summary_prose=prose)
        return [TextContent(type="text", text=prose)], outcome

    has_archaic = False
    has_modern = False
    for m in matches:
        if _is_archaic(m.get("tags")):
            has_archaic = True
        else:
            has_modern = True
    payload = {
        "is_modern_codified": has_modern,
        "has_archaic_form": has_archaic,
        "has_only_archaic_form": has_archaic and not has_modern,
    }
    success = has_modern is True
    identifiers = [_typed_identifier("vesum", {"word": word, "matches": matches, "result": payload})] if success else []
    prose = json.dumps(payload, ensure_ascii=False)
    # Envelope hits follow the empty triple when disposition is negative/empty:
    # VESUM rows remain in result/supporting_records for V4, not in consumer hits.
    hits = list(matches) if success else []
    outcome = {
        "tool": "check_modern_form",
        "disposition": "supported" if success else "negative",
        "success": success,
        "evidence_identifiers": identifiers,
        "result": payload,
        "supporting_records": {"word": word, "matches": matches},
    }
    enrich_typed_outcome(outcome, query=query, match_count=len(hits), hits=hits, summary_prose=prose)
    return [TextContent(type="text", text=prose)], outcome


def _analysis_counts(hits: list[dict[str, Any]]) -> str:
    lemma_count = len({hit["lemma"] for hit in hits})
    analysis_label = "analysis" if len(hits) == 1 else "analyses"
    lemma_label = "lemma" if lemma_count == 1 else "lemmas"
    return f"{len(hits)} {analysis_label} ({lemma_count} distinct {lemma_label})"


def _vesum_response(outcome: dict, *, query: dict, hits: list[dict], prose: str):
    """Present analysis rows without mutating V4 result or evidence hash inputs."""
    presented = [
        {**hit, "is_archaic": _is_archaic(hit.get("tags")), "tag_gloss": tag_gloss(hit.get("tags"))}
        for hit in hits
    ]
    prose = f"{_analysis_counts(presented)}\n\n{prose}"
    enrich_typed_outcome(outcome, query=query, match_count=len(presented), hits=presented, summary_prose=prose)
    outcome["lemma_count"] = len({hit["lemma"] for hit in presented})
    return [TextContent(type="text", text=prose)], outcome


async def handle_verify_word(args: dict):
    word = args.get("word")
    pos_filter = args.get("pos_filter")
    query = {"word": word, "pos_filter": pos_filter}
    if not isinstance(word, str) or not word.strip():
        prose = "invalid_input: word is required"
        outcome = {"tool": "verify_word", "disposition": "invalid_input", "success": False, "evidence_identifiers": []}
        return _vesum_response(outcome, query=query, hits=[], prose=prose)

    verify_word = backend().verify_word
    matches = await asyncio.to_thread(verify_word, word, pos_filter)
    typed_result = {"word": word, "pos_filter": pos_filter, "matches": matches}
    if not matches:
        prose = f"'{word}' — NOT FOUND in VESUM. This word form may not exist in standard Ukrainian."
        outcome = {
            "tool": "verify_word",
            "disposition": "not_found",
            "success": False,
            "evidence_identifiers": [],
            "result": typed_result,
        }
        return _vesum_response(outcome, query=query, hits=[], prose=prose)

    identifier = _typed_identifier("vesum", typed_result)
    lines = [f"'{word}' — matches in VESUM:\n"]
    for m in matches:
        tags = m.get("tags") or ""
        archaic = _is_archaic(tags)
        lines.append(
            f"- **lemma**: {m.get('lemma')}  |  **pos**: {m.get('pos')}  |  **tags**: `{tags}`  |  **is_archaic**: {archaic}"
        )
    prose = "\n".join(lines)
    outcome = {
        "tool": "verify_word",
        "disposition": "supported",
        "success": True,
        "evidence_identifiers": [identifier],
        "result": typed_result,
    }
    return _vesum_response(outcome, query=query, hits=matches, prose=prose)


async def handle_verify_words(args: dict):
    words = args.get("words")
    pos_filter = args.get("pos_filter")
    query = {"words": words, "pos_filter": pos_filter}
    if not isinstance(words, list) or not words or not all(isinstance(item, str) and item.strip() for item in words):
        prose = "invalid_input: words must be a nonempty list"
        outcome = {"tool": "verify_words", "disposition": "invalid_input", "success": False, "evidence_identifiers": []}
        return _vesum_response(outcome, query=query, hits=[], prose=prose)

    verify_words = backend().verify_words
    results = await asyncio.to_thread(verify_words, words, pos_filter)
    found = 0
    lines = [f"Batch verification: {len(words)} words\n"]
    hit_rows = [
        {**match, "word": word}
        for word in dict.fromkeys(words)
        for match in results.get(word, [])
    ]
    for word in words:
        matches = results.get(word, [])
        if matches:
            found += 1
            tags_str = ", ".join(f"{m['lemma']}({m['pos']})" for m in matches[:3])
            lines.append(f"- **{word}** — FOUND ({_analysis_counts(matches)}): {tags_str}")
        else:
            lines.append(f"- **{word}** — NOT FOUND")
    lines.insert(1, f"Found: {found}/{len(words)}\n")
    all_supported = found == len(words)
    typed_result = {"words": words, "pos_filter": pos_filter, "found": found, "total": len(words), "matches": results}
    identifiers = [_typed_identifier("vesum", typed_result)] if all_supported else []
    prose = "\n".join(lines)
    outcome = {
        "tool": "verify_words",
        "disposition": "supported" if all_supported else "partial",
        "success": all_supported,
        "evidence_identifiers": identifiers,
        "result": typed_result,
    }
    return _vesum_response(outcome, query=query, hits=hit_rows, prose=prose)


async def handle_verify_lemma(args: dict):
    lemma = args.get("lemma")
    query = {"lemma": lemma}
    if not isinstance(lemma, str) or not lemma.strip():
        prose = "invalid_input: lemma is required"
        outcome = {"tool": "verify_lemma", "disposition": "invalid_input", "success": False, "evidence_identifiers": []}
        return _vesum_response(outcome, query=query, hits=[], prose=prose)

    verify_lemma = backend().verify_lemma
    forms = await asyncio.to_thread(verify_lemma, lemma)

    if not forms:
        prose = f"Lemma '{lemma}' — NOT FOUND in VESUM."
        outcome = {
            "tool": "verify_lemma",
            "disposition": "not_found",
            "success": False,
            "evidence_identifiers": [],
            "result": {"lemma": lemma, "forms": []},
        }
        return _vesum_response(outcome, query=query, hits=[], prose=prose)

    # Group forms by POS for readability
    by_pos: dict[str, list] = {}
    has_archaic_forms = False
    for f in forms:
        is_archaic = _is_archaic(f.get("tags"))
        if is_archaic:
            has_archaic_forms = True
        f["is_archaic"] = is_archaic
        by_pos.setdefault(f.get("pos", "unknown"), []).append(f)

    lines = [f"'{lemma}' — forms across {len(by_pos)} POS (has_archaic_forms: {has_archaic_forms}):\n"]
    for pos, pos_forms in by_pos.items():
        lines.append(f"### {pos} ({len(pos_forms)} forms)")
        for f in pos_forms:
            tags = f.get("tags") or ""
            is_archaic = f.get("is_archaic", False)
            lines.append(f"- {f.get('word_form')}  |  `{tags}`  |  **is_archaic**: {is_archaic}")
        lines.append("")
    prose = "\n".join(lines)
    typed_result = {"lemma": lemma, "forms": forms}
    identifier = _typed_identifier("vesum", typed_result)
    outcome = {
        "tool": "verify_lemma",
        "disposition": "supported",
        "success": True,
        "evidence_identifiers": [identifier],
        "result": typed_result,
    }
    hits = [{**form, "lemma": lemma} for form in forms]
    return _vesum_response(outcome, query=query, hits=hits, prose=prose)


async def handle_verify_stress(args: dict):
    word = args.get("word")
    pos = args.get("pos")
    tags = args.get("tags")
    query = {"word": word, "pos": pos, "tags": tags}
    if not isinstance(word, str) or not word.strip():
        prose = json.dumps({"status": "invalid_input"}, ensure_ascii=False)
        outcome = {
            "tool": "verify_stress",
            "disposition": "invalid_input",
            "success": False,
            "evidence_identifiers": [],
        }
        enrich_typed_outcome(outcome, query=query, match_count=0, hits=[], summary_prose=prose)
        return [TextContent(type="text", text=prose)], outcome

    verify_stress = backend().verify_stress
    payload = await asyncio.to_thread(verify_stress, word, pos, tags)
    status = payload.get("status") if isinstance(payload, dict) else None
    success = (
        status == "ok"
        and isinstance(payload.get("matches"), list)
        and len(payload.get("matches") or []) == 1
        and payload.get("unresolvable_by_tags") is not True
    )
    if status == "invalid_input":
        disposition = "invalid_input"
    elif status == "not_found":
        disposition = "not_found"
    elif status == "ambiguous" or not success:
        disposition = (
            "ambiguous"
            if status == "ambiguous" or (isinstance(payload, dict) and payload.get("unresolvable_by_tags"))
            else "negative"
        )
        success = False
    else:
        disposition = "supported"
    identifiers = [_typed_identifier("sources", payload)] if success else []
    hits = list(payload.get("matches") or []) if isinstance(payload, dict) else []
    prose = json.dumps(payload, indent=2, ensure_ascii=False)
    outcome = {
        "tool": "verify_stress",
        "disposition": disposition,
        "success": success,
        "evidence_identifiers": identifiers,
        "result": payload,
    }
    enrich_typed_outcome(outcome, query=query, match_count=len(hits), hits=hits, summary_prose=prose)
    return [TextContent(type="text", text=prose)], outcome
