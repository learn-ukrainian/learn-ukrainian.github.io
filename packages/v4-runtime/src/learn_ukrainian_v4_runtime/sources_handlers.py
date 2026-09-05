"""Canonical typed sanctioned Sources handlers, backed only by Sources-owned IO."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.types import TextContent

from learn_ukrainian_v4_runtime.operation_auth import HEX64, OperationRefused
from learn_ukrainian_v4_runtime.v4_canonical_authority_store import immutable_evidence_identifier

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
    if not isinstance(word, str) or not word.strip():
        outcome = {
            "tool": "check_modern_form",
            "disposition": "invalid_input",
            "success": False,
            "evidence_identifiers": [],
        }
        return [TextContent(type="text", text=json.dumps(outcome, ensure_ascii=False))], outcome

    verify_word = backend().verify_word
    matches = await asyncio.to_thread(verify_word, word, None)
    if not matches:
        payload = {
            "is_modern_codified": False,
            "has_archaic_form": False,
            "has_only_archaic_form": False,
            "error": "Word not found in VESUM.",
        }
        outcome = {
            "tool": "check_modern_form",
            "disposition": "not_found",
            "success": False,
            "evidence_identifiers": [],
            "result": payload,
        }
        return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))], outcome

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
    outcome = {
        "tool": "check_modern_form",
        "disposition": "supported" if success else "negative",
        "success": success,
        "evidence_identifiers": identifiers,
        "result": payload,
    }
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))], outcome


async def handle_verify_word(args: dict):
    word = args.get("word")
    pos_filter = args.get("pos_filter")
    if not isinstance(word, str) or not word.strip():
        outcome = {"tool": "verify_word", "disposition": "invalid_input", "success": False, "evidence_identifiers": []}
        return [TextContent(type="text", text="invalid_input: word is required")], outcome

    verify_word = backend().verify_word
    matches = await asyncio.to_thread(verify_word, word, pos_filter)
    typed_result = {"word": word, "pos_filter": pos_filter, "matches": matches}
    if not matches:
        outcome = {
            "tool": "verify_word",
            "disposition": "not_found",
            "success": False,
            "evidence_identifiers": [],
            "result": typed_result,
        }
        return [
            TextContent(
                type="text", text=f"'{word}' — NOT FOUND in VESUM. This word form may not exist in standard Ukrainian."
            )
        ], outcome

    identifier = _typed_identifier("vesum", typed_result)
    outcome = {
        "tool": "verify_word",
        "disposition": "supported",
        "success": True,
        "evidence_identifiers": [identifier],
        "result": typed_result,
    }
    lines = [f"'{word}' — {len(matches)} match(es) in VESUM:\n"]
    for m in matches:
        tags = m.get("tags") or ""
        archaic = _is_archaic(tags)
        lines.append(
            f"- **lemma**: {m.get('lemma')}  |  **pos**: {m.get('pos')}  |  **tags**: `{tags}`  |  **is_archaic**: {archaic}"
        )
    return [TextContent(type="text", text="\n".join(lines))], outcome


async def handle_verify_words(args: dict):
    words = args.get("words")
    pos_filter = args.get("pos_filter")
    if not isinstance(words, list) or not words or not all(isinstance(item, str) and item.strip() for item in words):
        outcome = {"tool": "verify_words", "disposition": "invalid_input", "success": False, "evidence_identifiers": []}
        return [TextContent(type="text", text="invalid_input: words must be a nonempty list")], outcome

    verify_words = backend().verify_words
    results = await asyncio.to_thread(verify_words, words, pos_filter)
    found = 0
    lines = [f"Batch verification: {len(words)} words\n"]
    supported_results: dict[str, list] = {}
    for word in words:
        matches = results.get(word, [])
        if matches:
            found += 1
            supported_results[word] = matches
            tags_str = ", ".join(f"{m['lemma']}({m['pos']})" for m in matches[:3])
            lines.append(f"- **{word}** — FOUND ({len(matches)} match): {tags_str}")
        else:
            lines.append(f"- **{word}** — NOT FOUND")
    lines.insert(1, f"Found: {found}/{len(words)}\n")
    all_supported = found == len(words)
    typed_result = {"words": words, "pos_filter": pos_filter, "found": found, "total": len(words), "matches": results}
    identifiers = [_typed_identifier("vesum", typed_result)] if all_supported else []
    outcome = {
        "tool": "verify_words",
        "disposition": "supported" if all_supported else "partial",
        "success": all_supported,
        "evidence_identifiers": identifiers,
        "result": typed_result,
    }
    return [TextContent(type="text", text="\n".join(lines))], outcome


async def handle_verify_lemma(args: dict):
    lemma = args.get("lemma")
    if not isinstance(lemma, str) or not lemma.strip():
        outcome = {"tool": "verify_lemma", "disposition": "invalid_input", "success": False, "evidence_identifiers": []}
        return [TextContent(type="text", text="invalid_input: lemma is required")], outcome

    verify_lemma = backend().verify_lemma
    forms = await asyncio.to_thread(verify_lemma, lemma)

    if not forms:
        outcome = {
            "tool": "verify_lemma",
            "disposition": "not_found",
            "success": False,
            "evidence_identifiers": [],
            "result": {"lemma": lemma, "forms": []},
        }
        return [TextContent(type="text", text=f"Lemma '{lemma}' — NOT FOUND in VESUM.")], outcome

    # Group forms by POS for readability
    by_pos: dict[str, list] = {}
    has_archaic_forms = False
    for f in forms:
        is_archaic = _is_archaic(f.get("tags"))
        if is_archaic:
            has_archaic_forms = True
        f["is_archaic"] = is_archaic
        by_pos.setdefault(f.get("pos", "unknown"), []).append(f)

    lines = [f"'{lemma}' — {len(forms)} form(s) across {len(by_pos)} POS (has_archaic_forms: {has_archaic_forms}):\n"]
    for pos, pos_forms in by_pos.items():
        lines.append(f"### {pos} ({len(pos_forms)} forms)")
        for f in pos_forms:
            tags = f.get("tags") or ""
            is_archaic = f.get("is_archaic", False)
            lines.append(f"- {f.get('word_form')}  |  `{tags}`  |  **is_archaic**: {is_archaic}")
        lines.append("")
    typed_result = {"lemma": lemma, "forms": forms}
    identifier = _typed_identifier("vesum", typed_result)
    outcome = {
        "tool": "verify_lemma",
        "disposition": "supported",
        "success": True,
        "evidence_identifiers": [identifier],
        "result": typed_result,
    }
    return [TextContent(type="text", text="\n".join(lines))], outcome


async def handle_verify_stress(args: dict):
    word = args.get("word")
    pos = args.get("pos")
    tags = args.get("tags")
    if not isinstance(word, str) or not word.strip():
        outcome = {
            "tool": "verify_stress",
            "disposition": "invalid_input",
            "success": False,
            "evidence_identifiers": [],
        }
        return [TextContent(type="text", text=json.dumps({"status": "invalid_input"}, ensure_ascii=False))], outcome

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
    outcome = {
        "tool": "verify_stress",
        "disposition": disposition,
        "success": success,
        "evidence_identifiers": identifiers,
        "result": payload,
    }
    return [TextContent(type="text", text=json.dumps(payload, indent=2, ensure_ascii=False))], outcome
