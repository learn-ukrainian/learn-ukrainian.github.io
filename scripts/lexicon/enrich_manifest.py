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

import json
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


def _meaning(conn: sqlite3.Connection, lemma: str) -> dict | None:
    """Grinchenko 1907 (preferred) → СУМ-11 fallback, by headword."""
    word = lemma.strip()
    row = conn.execute(
        "SELECT definition FROM grinchenko WHERE word = ? AND definition != '' LIMIT 1",
        (word,),
    ).fetchone()
    if row and row[0]:
        return {"text": row[0].strip()[:600], "source": "Грінченко (1907)"}
    row = conn.execute(
        "SELECT definition FROM sum11 WHERE word = ? AND definition != '' LIMIT 1",
        (word,),
    ).fetchone()
    if row and row[0]:
        return {
            "text": row[0].strip()[:600],
            "source": "СУМ-11",
            "note": "СУМ-11 — частково засоюзлене видання; перевіряйте ідеологічно навантажені статті.",
        }
    return None


def _etymology(conn: sqlite3.Connection, lemma: str) -> dict | None:
    """ЕСУМ etymology (А–Г PoC coverage), by lemma."""
    if " " in lemma.strip():
        return None
    row = conn.execute(
        "SELECT etymology_text, vol, page FROM esum_etymology "
        "WHERE lemma = ? AND etymology_text != '' LIMIT 1",
        (lemma.strip(),),
    ).fetchone()
    if not row or not row[0]:
        return None
    cite = "ЕСУМ"
    if row[1]:
        cite += f", т. {row[1]}"
    if row[2]:
        cite += f", с. {row[2]}"
    return {"text": row[0].strip()[:600], "source": cite}


def enrich() -> tuple[int, int]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    conn = sqlite3.connect(f"file:{SOURCES_DB}?mode=ro", uri=True)
    enriched = 0
    try:
        for entry in manifest["entries"]:
            lemma = entry["lemma"]
            block: dict[str, object] = {}
            morph = _morphology(lemma)
            if morph:
                block["morphology"] = morph
            meaning = _meaning(conn, lemma)
            if meaning:
                block["meaning"] = meaning
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
