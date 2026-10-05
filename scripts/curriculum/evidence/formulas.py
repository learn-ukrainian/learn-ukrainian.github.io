"""Fixed formula definitions and exact token-to-lexical-part evidence (#9582)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata

from scripts.curriculum.resolver.tokenize import lookup_form, tokenize

from . import sources

METHOD = "formula_row.v1"
TERMINAL = frozenset("!.?…")


def definition(word: dict) -> dict:
    """Canonical formula definition; aliases are evidence-free search keys."""
    return {"text": word["text"], "parts": word["parts"], "aliases": word.get("aliases", [])}


def definition_digest(word: dict) -> str:
    return hashlib.sha256(
        json.dumps(definition(word), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def headword(text: str) -> str:
    # Candidate equality preserves internal spelling; lookup_form is only for VESUM.
    stripped = unicodedata.normalize("NFD", text).replace("\u0301", "").replace("\u0300", "")
    return " ".join(unicodedata.normalize("NFC", stripped).casefold().split())


def printed_headword(text: str) -> str:
    return headword(text.rstrip().rstrip("".join(sorted(TERMINAL))))


def tokens(text: str) -> list:
    """Permit whitespace between original Cyrillic tokens, closed terminal marks."""
    result = tokenize(text)
    if not result or any(t.kind != "cyrillic" for t in result):
        raise ValueError("formula_tokens_invalid")
    cursor = 0
    for token in result:
        if any(not c.isspace() for c in text[cursor : token.start]):
            raise ValueError("formula_punctuation_invalid")
        cursor = token.end
    if any(not c.isspace() and c not in TERMINAL for c in text[cursor:]):
        raise ValueError("formula_punctuation_invalid")
    return result


def validate(word: dict, records: dict[str, dict], api: sources.Sources) -> None:
    """Verify live paradigms without altering forms or learner-state permissions."""

    def check_cycles(current: dict, visiting: set[str]) -> None:
        for part in current.get("parts", []):
            wid = part["word"]
            if wid in visiting:
                raise ValueError("formula_part_cycle")
            child = records.get(wid)
            if child and child.get("kind") == "formula":
                check_cycles(child, visiting | {wid})

    check_cycles(word, {word["id"]} if word.get("id") else set())
    run = tokens(word["text"])
    if [t.text for t in run] != [p["form"] for p in word["parts"]]:
        raise ValueError("formula_token_parts_mismatch")
    for token, part in zip(run, word["parts"], strict=True):
        if part["word"] == word.get("id"):
            raise ValueError("formula_part_cycle")
        record = records.get(part["word"])
        if record is None or record.get("retired"):
            raise ValueError("formula_part_missing_or_retired")
        if record.get("kind") == "formula":
            raise ValueError("formula_part_non_lexical")
        entry = record.get("entry")
        if not isinstance(entry, dict) or entry.get("source") not in {"vesum", "ulif"}:
            raise ValueError("formula_part_ambiguous")
        try:
            groups = api.inspect_lemma_forms(record["lemma"], record["pos"]).forms_by_entry
            if entry["source"] == "vesum":
                forms = groups.get(entry["entry_id"], [])
            else:
                ulif = api.ulif_entries([record["lemma"]]).raw.get(record["lemma"], [])
                checked = sorted(ulif, key=lambda r: r["homonym_index"])
                if not api.ulif_group_checked(checked) or len(checked) != len(groups):
                    raise ValueError("formula_part_entry_invalid")
                position = next(
                    (i for i, r in enumerate(checked) if [r["canonical_headword"], r["homonym_index"]] == entry["key"]),
                    None,
                )
                if position is None:
                    raise ValueError("formula_part_entry_invalid")
                forms = groups[sorted(groups)[position]]
        except (OSError, sqlite3.Error) as exc:
            raise ValueError("formula_vesum_unavailable") from exc
        except ValueError as exc:
            if "source_unavailable" in str(exc):
                raise ValueError("formula_vesum_unavailable") from exc
            raise
        if not forms:
            raise ValueError("formula_part_entry_invalid")
        if not any(lookup_form(f["word_form"]).casefold() == token.lookup.casefold() for f in forms):
            raise ValueError("formula_part_form_invalid")
    for alias in word.get("aliases", []):
        try:
            result = api.verify_words([lookup_form(alias).casefold()]).raw
        except (OSError, ValueError, sqlite3.Error) as exc:
            raise ValueError("formula_vesum_unavailable") from exc
        item = result.get(lookup_form(alias).casefold(), [])
        if not item:
            raise ValueError("formula_alias_unattested")
        if len(tokens(alias)) != 1 or headword(alias) != headword(tokens(alias)[0].text):
            raise ValueError("formula_alias_invalid")
    if word.get("definition_sha256") != definition_digest(word):
        raise ValueError("formula_definition_invalid")


def resolve_request(request: dict, records: dict[str, dict]) -> dict:
    run = tokens(request["text"])
    if len(run) != len(request["parts"]):
        raise ValueError("formula_token_parts_mismatch")
    parts = []
    for token, part in zip(run, request["parts"], strict=True):
        hits = [
            w
            for w in records.values()
            if w.get("kind") != "formula"
            and not w.get("retired")
            and w.get("lemma") == sources.normalize_spelling(part["lemma"])
            and w.get("pos") == part["pos"]
        ]
        pin = part.get("entry")
        if pin:
            hits = [
                w
                for w in hits
                if w.get("entry") == pin
                or (
                    pin.get("source") == "ulif"
                    and isinstance(w.get("entry"), dict)
                    and w["entry"].get("source") == "ulif"
                    and w["entry"]["key"][1] == pin.get("homonym_index")
                )
            ]
        if not hits:
            raise ValueError("formula_part_entry_invalid" if pin else "formula_part_missing_or_retired")
        if len(hits) != 1:
            raise ValueError("formula_part_ambiguous")
        parts.append({"word": hits[0]["id"], "form": token.text})
    word = {"kind": "formula", "text": request["text"], "parts": parts, "entry": {"source": "formula"}}
    if "aliases" in request:
        word["aliases"] = request["aliases"]
    if request.get("note"):
        word["note"] = request["note"]
    word["definition_sha256"] = definition_digest(word)
    return word
