#!/usr/bin/env python3
"""Generate the frozen 500-lemma PR1 equivalence fixture + baseline.

Hermetic synthetic cohort (no live ``sources.db``). Baseline captures the
**legacy** single-run CEFR cohort-quantile map and reciprocal relation closure
(the #5331 contract). Side-DB builders are exercised against the same sources.

```bash
.venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py
```
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.lexicon import enrich_manifest as em

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "lexicon" / "runner_pr1"
SLICE_SIZE = 500
_ALPHABET = "абвгдежзиклмнопрстуфхцчшщюяєіїґ"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lemma_at(index: int) -> str:
    n = index + 1
    chars: list[str] = []
    while n:
        n, rem = divmod(n - 1, len(_ALPHABET))
        chars.append(_ALPHABET[rem])
    return "тест" + "".join(reversed(chars))


def _synthetic_entries(n: int = SLICE_SIZE) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for i in range(n):
        lemma = _lemma_at(i)
        entries.append(
            {
                "lemma": lemma,
                "url_slug": lemma,
                "pos": "noun" if i % 3 else "verb",
                "gloss": f"gloss-{i % 17}",
            }
        )
    return entries


def _build_synthetic_sources(path: Path, entries: list[dict[str, Any]]) -> None:
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE puls_cefr (
                word TEXT NOT NULL,
                guideword TEXT DEFAULT '',
                level TEXT DEFAULT '',
                pos TEXT DEFAULT '',
                type TEXT DEFAULT '',
                text TEXT NOT NULL DEFAULT '',
                source TEXT DEFAULT ''
            );
            CREATE TABLE sum11 (
                word TEXT NOT NULL,
                definition TEXT NOT NULL DEFAULT '',
                text TEXT NOT NULL DEFAULT '',
                sovietization_risk INTEGER NOT NULL DEFAULT 0,
                sovietization_keywords TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE balla_en_uk (
                word TEXT NOT NULL,
                definition TEXT NOT NULL DEFAULT '',
                text TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE dmklinger_uk_en (
                word TEXT NOT NULL,
                pos TEXT,
                translations TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE wiktionary (
                word TEXT NOT NULL,
                definitions TEXT DEFAULT '',
                synonyms TEXT DEFAULT '',
                antonyms TEXT DEFAULT ''
            );
            """
        )
        for i in range(50):
            lemma = str(entries[i]["lemma"])
            conn.execute(
                "INSERT INTO puls_cefr(word, level, text) VALUES (?, 'A1', ?)",
                (lemma, f"PULS {lemma}"),
            )
        for i in range(50, 150, 2):
            a = str(entries[i]["lemma"])
            b = str(entries[i + 1]["lemma"])
            conn.execute(
                "INSERT INTO sum11(word, definition, text) VALUES (?, ?, ?)",
                (a, f"див. {b}.", f"див. {b}."),
            )
            conn.execute(
                "INSERT INTO sum11(word, definition, text) VALUES (?, ?, ?)",
                (b, f"див. {a}.", f"див. {a}."),
            )
        for i in range(150, 200, 2):
            a = str(entries[i]["lemma"])
            b = str(entries[i + 1]["lemma"])
            conn.execute(
                "INSERT INTO sum11(word, definition, text) VALUES (?, ?, ?)",
                (a, f"протилежне {b}.", f"протилежне {b}."),
            )
        for i in range(200, 220):
            lemma = str(entries[i]["lemma"])
            conn.execute(
                "INSERT INTO dmklinger_uk_en(word, pos, translations) VALUES (?, 'n', ?)",
                (lemma, json.dumps([f"en-{i}"])),
            )
            conn.execute(
                "INSERT INTO balla_en_uk(word, definition) VALUES (?, ?)",
                (f"english{i}", lemma),
            )
        conn.commit()
    finally:
        conn.close()


def _synthetic_grac(entries: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for i, entry in enumerate(entries):
        if i < 50:
            continue
        lemma = str(entry["lemma"])
        key = em._grac_lookup_key(lemma)
        rel = float(1000 - i)
        out[key] = {"word": lemma, "freq": int(rel * 1000), "rel_freq": rel}
    return out


def _legacy_cefr_and_relations(
    entries: list[dict[str, Any]],
    sources_db: Path,
    grac: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Baseline = current single-run CEFR + by_headword relation maps."""
    em._BALLA_SIDE_DB = None
    em._DMKLINGER_SIDE_DB = None
    em._DMKLINGER_INDEX = None
    em._BALLA_REVERSE_INDEX.clear()
    em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    em._GRAC_FREQUENCY_CACHE_DATA = grac
    original_vesum_valid = em._vesum_valid_synonym
    original_vesum_analyses = em._vesum_word_analyses
    em._vesum_valid_synonym = lambda term: bool(term)  # type: ignore[assignment]
    em._vesum_word_analyses = lambda word: ((word, "noun"),)  # type: ignore[assignment]

    manifest = {"entries": [dict(e) for e in entries]}
    em._normalize_manifest_entries(manifest)
    conn = sqlite3.connect(f"file:{sources_db.resolve().as_posix()}?mode=ro", uri=True)
    try:
        has_sum11 = em._sum11_has_flag_columns(conn)
        em._prepare_cefr_estimates(conn, manifest)
        relations = {
            "synonym": em._definition_pointer_relations_by_headword(
                conn, manifest, has_sum11_flags=has_sum11
            ),
            "antonym": em._definition_antonym_relations_by_headword(
                conn, manifest, has_sum11_flags=has_sum11
            ),
            "homonym": em._homonym_relations_by_headword(conn, manifest),
            "paronym": em._paronym_relations_by_headword(conn, manifest),
        }
    finally:
        conn.close()
        em._vesum_valid_synonym = original_vesum_valid
        em._vesum_word_analyses = original_vesum_analyses
    return dict(em._CEFR_ESTIMATE_LEVEL_BY_KEY), relations


def main() -> int:
    # Offline by default when run as a script. Must NOT run at import time —
    # importing this module from tests must have zero process-env side effects
    # (CI env-leak class #5247).
    os.environ.setdefault("LEXICON_SLOVNYK_OFFLINE", "1")
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    entries = _synthetic_entries(SLICE_SIZE)
    sources_path = FIXTURE_DIR / "sources_slice.sqlite"
    _build_synthetic_sources(sources_path, entries)
    grac = _synthetic_grac(entries)
    (FIXTURE_DIR / "grac_frequency_slice.json").write_text(
        json.dumps(grac, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lemma200 = str(entries[200]["lemma"])
    kaikki = {
        em.kaikki_lookup_key(lemma200): {
            "ipa": ["/ˈslɔ.vo/"],
            "glosses": ["word"],
        }
    }
    (FIXTURE_DIR / "kaikki_slice.json").write_text(
        json.dumps(kaikki, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (FIXTURE_DIR / "slice_input.json").write_text(
        json.dumps({"entries": entries}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("computing legacy CEFR + relation baseline…")
    cefr_snap, rel_snap = _legacy_cefr_and_relations(entries, sources_path, grac)
    baseline = {
        "schema": "runner-pr1-equivalence-v1",
        "slice_size": SLICE_SIZE,
        "cefr_estimates": cefr_snap,
        "relations": rel_snap,
        "entry_lemmas": [str(e["lemma"]) for e in entries],
    }
    baseline_text = json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (FIXTURE_DIR / "baseline_enriched.json").write_text(baseline_text, encoding="utf-8")
    digest = _sha256_bytes(baseline_text.encode("utf-8"))
    (FIXTURE_DIR / "baseline.sha256").write_text(digest + "\n", encoding="utf-8")
    (FIXTURE_DIR / "GENERATION.md").write_text(
        f"""# Runner PR1 equivalence fixture (hermetic)

## Command

```bash
.venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py
```

## What the baseline proves

Record-equivalent **CEFR band boundaries** (``_prepare_cefr_estimates`` cohort
quantiles) and **reciprocal relation closure**
(``_*_relations_by_headword``) for a frozen 500-lemma offline slice.

The PR1 sealed phases must reproduce these maps exactly (foundation for #5331).

## Baseline digest

`SHA256(baseline_enriched.json) = {digest}`

- CEFR estimate keys: {len(cefr_snap)}
- Synonym headwords with edges: {len(rel_snap.get("synonym") or {})}
- Antonym headwords with edges: {len(rel_snap.get("antonym") or {})}
""",
        encoding="utf-8",
    )
    print(f"baseline sha256={digest}")
    print(f"cefr_keys={len(cefr_snap)} synonym_hw={len(rel_snap.get('synonym') or {})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
