#!/usr/bin/env python3
"""Enrich the Word Atlas lexicon manifest with source-verified dictionary data.

For each lemma in ``starlight/src/data/lexicon-manifest.json`` this adds an
``enrichment`` block built from DETERMINISTIC local-dictionary lookups (no LLM,
no fabrication):

- **morphology** — full VESUM paradigm (``data/vesum.db``), forms decoded into
  human-readable Ukrainian grammatical labels.
- **meaning** — Грінченко 1907 (pre-Soviet, clean) preferred, СУМ-11 fallback
  (flagged, since it is partially Sovietised — issue #1659).
- **etymology** — ЕСУМ (``data/sources.db``; PoC volume coverage А–Г only).

Every field carries its ``source`` so the UI can attribute it. Lemmas with no
dictionary hit simply get an empty enrichment and the UI keeps its honest
"not yet available" note. Multi-word phrases are skipped for single-lemma
morphology/etymology.

Run from the repo root (needs ``data/`` which is excluded from worktrees)::

    .venv/bin/python scripts/lexicon/enrich_manifest.py
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.verification.vesum import verify_lemma

MANIFEST = ROOT / "starlight" / "src" / "data" / "lexicon-manifest.json"
SOURCES_DB = ROOT / "data" / "sources.db"

# VESUM tag token → human-readable Ukrainian grammatical label.
_TAG_LABELS: dict[str, str] = {
    "v_naz": "називний",
    "v_rod": "родовий",
    "v_dav": "давальний",
    "v_zna": "знахідний",
    "v_oru": "орудний",
    "v_mis": "місцевий",
    "v_kly": "кличний",
    "s": "однина",
    "p": "множина",
    "m": "чол.",
    "f": "жін.",
    "n": "сер.",
    "pres": "теперішній",
    "futr": "майбутній",
    "past": "минулий",
    "impf": "наказовий",
    "impr": "наказовий",
    "inf": "інфінітив",
    "1": "1 ос.",
    "2": "2 ос.",
    "3": "3 ос.",
}

_POS_LABELS: dict[str, str] = {
    "noun": "іменник",
    "verb": "дієслово",
    "adj": "прикметник",
    "adv": "прислівник",
    "numr": "числівник",
    "prep": "прийменник",
    "conj": "сполучник",
    "part": "частка",
    "pron": "займенник",
    "intj": "вигук",
}


def _decode_tag(tag: str) -> str:
    """Turn a raw VESUM tag into a short human label, dropping noise tokens."""
    parts = [p for p in tag.split(":") if p not in {"verb", "noun", "adj", "adv"}]
    labels = [_TAG_LABELS[p] for p in parts if p in _TAG_LABELS]
    # De-dup while preserving order.
    seen: set[str] = set()
    out = [x for x in labels if not (x in seen or seen.add(x))]
    return ", ".join(out)


def _morphology(lemma: str) -> dict | None:
    """Full VESUM paradigm for a single-token lemma, decoded and de-duplicated."""
    if " " in lemma.strip():
        return None  # phrases have no single-lemma paradigm
    try:
        forms = verify_lemma(lemma)
    except Exception:
        return None
    if not forms:
        return None
    pos_raw = forms[0].get("pos") or ""
    seen: set[tuple[str, str]] = set()
    decoded: list[dict[str, str]] = []
    for row in forms:
        form = row.get("word_form") or ""
        label = _decode_tag(row.get("tags") or "")
        key = (form, label)
        if not form or key in seen:
            continue
        seen.add(key)
        decoded.append({"form": form, "label": label})
    if not decoded:
        return None
    return {
        "pos": _POS_LABELS.get(pos_raw, pos_raw),
        "form_count": len(decoded),
        "forms": decoded[:40],
        "source": "VESUM",
    }


def _clean_wiki_def(raw: str) -> str:
    """Strip Вікісловник wiki-markup noise (templates, quote leaks, refs)."""
    text = re.sub(r"\{\{[^{}]*\}\}", "", raw)
    text = re.split(r"\.\s{2,}", text)[0]  # cut a leaked quotation after the def
    text = re.split(r"[|{}\[]", text)[0]  # cut residual template/ref markers
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" .,;:—-")


def _clean_wiki_defs(raw: str | None) -> list[str]:
    try:
        arr = json.loads(raw or "[]")
    except (ValueError, TypeError):
        return []
    out: list[str] = []
    for d in arr:
        cleaned = _clean_wiki_def(str(d))
        if len(cleaned) >= 6 and cleaned not in out:
            out.append(cleaned)
    return out[:3]


def get_apostrophe_variants(word: str) -> list[str]:
    """Generate all apostrophe combinations of a word."""
    variants = {word}
    for char in ["'", "’", "ʼ"]:
        if char in word:
            for replacement in ["'", "’", "ʼ"]:
                variants.add(word.replace(char, replacement))
    return sorted(list(variants))


def _get_wordnet_synonyms(conn: sqlite3.Connection, lemma: str) -> list[str]:
    """Look up synonyms in the ukrajinet table for the lemma."""
    # 1. Get variants by splitting on / and ,
    lemma_variants = []
    for p in lemma.split("/"):
        for pp in p.split(","):
            val = pp.strip()
            if val:
                lemma_variants.append(val)

    # Generate apostrophe variants for the lookup and filtering
    search_variants = []
    for var in lemma_variants:
        search_variants.extend(get_apostrophe_variants(var))
    # Deduplicate search_variants while preserving order
    seen_search = set()
    search_variants = [x for x in search_variants if not (x in seen_search or seen_search.add(x))]

    search_variants_lower = {v.lower() for v in search_variants}

    synonyms_set = set()
    synonyms_ordered = []

    for var in search_variants:
        var_l = var.lower()
        # Query using LIKE.
        cursor = conn.execute("SELECT words FROM ukrajinet WHERE lower(words) LIKE ?", (f"%{var_l}%",))
        for (words_json,) in cursor:
            try:
                words = json.loads(words_json)
            except Exception:
                continue
            cleaned_words = [w.strip() for w in words]
            # Check if any word in the synset matches the search variant (case-insensitively)
            if any(var_l == w.lower() for w in cleaned_words):
                for w in cleaned_words:
                    # Drop the lemma variants
                    if w.lower() not in search_variants_lower and w not in synonyms_set:
                        synonyms_set.add(w)
                        synonyms_ordered.append(w)

    return synonyms_ordered[:8]


def clean_gloss(gloss: str) -> str:
    """Strip the pedagogical 'chunk' annotation from a gloss."""
    if not gloss:
        return gloss
    # Remove " — chunk" or " - chunk" at the end
    res = re.sub(r"\s*[\u2014-]\s*chunk$", "", gloss)
    # Remove " chunk" at the end
    res = re.sub(r"\s+chunk$", "", res)
    # Replace "chunk" word with empty string
    res = re.sub(r"\bchunk\b", "", res)
    # Clean up "— , " or "- , " -> "— "
    res = re.sub(r"([\u2014-])\s*,\s*", r"\1 ", res)
    # Clean up spaces before punctuation
    res = re.sub(r"\s+,", ",", res)
    # Collapse multiple spaces
    res = re.sub(r"\s+", " ", res)
    # Clean up trailing punctuation
    res = re.sub(r"\s*,\s*$", "", res)
    res = re.sub(r"\s*[\u2014-]\s*$", "", res)
    return res.strip()


def clean_html_entities(text: str) -> str:
    """Unescape HTML entities (handling double-escaped ones) and normalise spaces."""
    if not text:
        return text
    u1 = html.unescape(text)
    u2 = html.unescape(u1)
    u2 = u2.replace("\u00a0", " ")
    return u2


def _meaning(conn: sqlite3.Connection, lemma: str) -> dict | None:
    """Modern Ukrainian meaning: Вікісловник (clean, + synonyms) → СУМ-11 fallback.

    Грінченко is intentionally NOT used here — its 1907 Russian glosses are
    surfaced separately as historical *attestation*, not as the primary meaning.
    """
    word = lemma.strip()
    row = None
    for w_var in get_apostrophe_variants(word):
        row = conn.execute(
            "SELECT definitions FROM wiktionary WHERE word = ? LIMIT 1",
            (w_var,),
        ).fetchone()
        if row:
            break

    block = None
    if row:
        defs = _clean_wiki_defs(row[0])
        if defs:
            block = {"definitions": [clean_html_entities(d) for d in defs], "source": "Вікісловник"}
    else:
        for w_var in get_apostrophe_variants(word):
            row = conn.execute(
                "SELECT definition FROM sum11 WHERE word = ? AND definition != '' LIMIT 1",
                (w_var,),
            ).fetchone()
            if row and row[0]:
                block = {
                    "definitions": [clean_html_entities(row[0].strip()[:600])],
                    "source": "СУМ-11",
                    "note": "СУМ-11 — частково засоюзлене видання; перевіряйте ідеологічно навантажені статті.",
                }
                break

    if block:
        syns = _get_wordnet_synonyms(conn, word)
        if syns:
            block["synonyms"] = syns

    return block


def _attestation(conn: sqlite3.Connection, lemma: str) -> dict | None:
    """Грінченко 1907 — historical attestation with Ukrainian usage quotations."""
    word = lemma.strip()
    row = None
    for w_var in get_apostrophe_variants(word):
        row = conn.execute(
            "SELECT definition FROM grinchenko WHERE word = ? AND definition != '' LIMIT 1",
            (w_var,),
        ).fetchone()
        if row:
            break

    if row and row[0]:
        return {"text": clean_html_entities(row[0].strip()[:600]), "source": "Грінченко (1907)"}
    return None


def _etymology(conn: sqlite3.Connection, lemma: str) -> dict | None:
    """ЕСУМ etymology (А–Г PoC coverage), by lemma."""
    word = lemma.strip()
    if " " in word:
        return None
    row = None
    for w_var in get_apostrophe_variants(word):
        row = conn.execute(
            "SELECT etymology_text, vol, page FROM esum_etymology "
            "WHERE lemma = ? AND etymology_text != '' LIMIT 1",
            (w_var,),
        ).fetchone()
        if row:
            break

    if not row or not row[0]:
        return None
    cite = "ЕСУМ"
    if row[1]:
        cite += f", т. {row[1]}"
    if row[2]:
        cite += f", с. {row[2]}"
    return {"text": clean_html_entities(row[0].strip()[:600]), "source": cite}


def enrich() -> tuple[int, int]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    conn = sqlite3.connect(f"file:{SOURCES_DB}?mode=ro", uri=True)
    enriched = 0
    try:
        for entry in manifest["entries"]:
            if "gloss" in entry:
                entry["gloss"] = clean_html_entities(clean_gloss(entry["gloss"]))
            lemma = entry["lemma"]
            block: dict[str, object] = {}
            morph = _morphology(lemma)
            if morph:
                block["morphology"] = morph
            meaning = _meaning(conn, lemma)
            if meaning:
                block["meaning"] = meaning
            attestation = _attestation(conn, lemma)
            if attestation:
                block["attestation"] = attestation
            etym = _etymology(conn, lemma)
            if etym:
                block["etymology"] = etym
            if block:
                block["sources"] = sorted(
                    {v["source"] for v in block.values() if isinstance(v, dict) and v.get("source")}
                )
                entry["enrichment"] = block
                enriched += 1
            else:
                entry.pop("enrichment", None)
    finally:
        conn.close()
    manifest["enrichment_generated"] = True
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return enriched, len(manifest["entries"])


def main() -> None:
    enriched, total = enrich()
    print(f"enriched {enriched}/{total} lexicon entries from VESUM + Грінченко/СУМ + ЕСУМ")


if __name__ == "__main__":
    main()
