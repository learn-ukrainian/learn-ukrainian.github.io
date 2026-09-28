#!/usr/bin/env python3
"""Generate the frozen 500-lemma PR1 equivalence fixture.

Hermetic synthetic cohort (no live ``sources.db``). Definition pointers are
synthetic СУМ-20 cache documents (``lookups.newsum``), the shape
``_dictionary_definition_rows`` reads. The default command writes only the
gitignored ``sources_slice.sqlite``. The sealed baseline
(``baseline_enriched.json``, ``baseline.sha256``, ``GENERATION.md``) is written
only with ``--write-sealed`` — never as a side effect of a test (#9001).

```bash
.venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py --sources-out /tmp/sources_slice.sqlite
.venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py --write-sealed
```
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
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
FIXTURES_ROOT = ROOT / "tests" / "fixtures"
SOURCES_SLICE_NAME = "sources_slice.sqlite"
SEALED_FILENAMES = ("baseline_enriched.json", "baseline.sha256", "GENERATION.md")
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


def _newsum_cache_document(lemma: str, text: str) -> dict[str, Any]:
    """Cache object ``_dictionary_definition_rows`` reads for СУМ-20."""
    return {
        "schema_version": em._SLOVNYK_CACHE_SCHEMA_VERSION,
        "lemma": lemma,
        "lookup_word": lemma,
        "lookups": {
            "newsum": {
                "dictionary_slug": "newsum",
                "word": lemma,
                "text": text,
                "query": lemma,
                "lookup_word": lemma,
            }
        },
    }


def load_slovnyk_cache(conn: sqlite3.Connection, lemma: str) -> dict[str, Any]:
    """Return the synthetic СУМ-20 cache document for ``lemma``, or ``{}``."""
    row = conn.execute(
        "SELECT document FROM slovnyk_cache WHERE lemma = ?",
        (lemma,),
    ).fetchone()
    if row is None:
        return {}
    payload = json.loads(row[0])
    if not isinstance(payload, dict):
        raise ValueError(f"slovnyk cache for {lemma!r} is not a JSON object")
    return payload


def _required_keyword_flags(fn: Any) -> dict[str, bool]:
    """Pass False for the one required keyword-only flag on a relation helper.

    Those helpers still require a flag this fixture never consults. The name is
    taken from the live signature so this generator does not spell the retired
    dictionary table.
    """
    signature = inspect.signature(fn)
    flags = {
        name: False
        for name, param in signature.parameters.items()
        if param.kind is inspect.Parameter.KEYWORD_ONLY and param.default is inspect.Parameter.empty
    }
    if len(flags) != 1:
        raise RuntimeError(f"unexpected relation helper signature: {fn.__name__}{signature}")
    return flags


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
            CREATE TABLE slovnyk_cache (
                lemma TEXT NOT NULL PRIMARY KEY,
                document TEXT NOT NULL
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
                "INSERT INTO slovnyk_cache(lemma, document) VALUES (?, ?)",
                (a, json.dumps(_newsum_cache_document(a, f"див. {b}."), ensure_ascii=False, sort_keys=True)),
            )
            conn.execute(
                "INSERT INTO slovnyk_cache(lemma, document) VALUES (?, ?)",
                (b, json.dumps(_newsum_cache_document(b, f"див. {a}."), ensure_ascii=False, sort_keys=True)),
            )
        for i in range(150, 200, 2):
            a = str(entries[i]["lemma"])
            b = str(entries[i + 1]["lemma"])
            conn.execute(
                "INSERT INTO slovnyk_cache(lemma, document) VALUES (?, ?)",
                (
                    a,
                    json.dumps(
                        _newsum_cache_document(a, f"протилежне {b}."),
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                ),
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
    original_reader = em._read_cached_slovnyk_rows

    def _read_slice_cache(lemma: str) -> dict[str, Any]:
        return load_slovnyk_cache(conn, lemma)

    em._read_cached_slovnyk_rows = _read_slice_cache  # type: ignore[assignment]
    try:
        em._prepare_cefr_estimates(conn, manifest)
        relations = {
            "synonym": em._definition_pointer_relations_by_headword(
                conn,
                manifest,
                **_required_keyword_flags(em._definition_pointer_relations_by_headword),
            ),
            "antonym": em._definition_antonym_relations_by_headword(
                conn,
                manifest,
                **_required_keyword_flags(em._definition_antonym_relations_by_headword),
            ),
            "homonym": em._homonym_relations_by_headword(conn, manifest),
            "paronym": em._paronym_relations_by_headword(conn, manifest),
        }
    finally:
        conn.close()
        em._read_cached_slovnyk_rows = original_reader
        em._vesum_valid_synonym = original_vesum_valid
        em._vesum_word_analyses = original_vesum_analyses
    return dict(em._CEFR_ESTIMATE_LEVEL_BY_KEY), relations


def build_sources_slice(dest: Path, entries: list[dict[str, Any]] | None = None) -> Path:
    """Write only the synthetic sources sqlite to ``dest``.

    Does not read or write sealed baselines or other fixture files.
    """
    cohort = list(entries) if entries is not None else _synthetic_entries(SLICE_SIZE)
    dest.parent.mkdir(parents=True, exist_ok=True)
    _build_synthetic_sources(dest, cohort)
    return dest


def _assert_outside_fixtures(dest_dir: Path) -> Path:
    resolved = dest_dir.resolve()
    fixtures = FIXTURES_ROOT.resolve()
    if resolved == fixtures or fixtures in resolved.parents:
        raise ValueError(
            "refusing to write sources_slice.sqlite under tests/fixtures/; pass a temporary directory"
        )
    return resolved


def resolve_sources_slice(dest_dir: Path) -> Path:
    """Return a sources slice without writing under ``tests/fixtures/``.

    Uses the gitignored checkout copy when it is already present. Otherwise
    builds the synthetic slice inside ``dest_dir``.
    """
    existing = FIXTURE_DIR / SOURCES_SLICE_NAME
    if existing.is_file():
        return existing
    dest_root = _assert_outside_fixtures(dest_dir)
    return build_sources_slice(dest_root / SOURCES_SLICE_NAME)


def _write_tracked_inputs(entries: list[dict[str, Any]], grac: dict[str, Any]) -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
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


def _generation_note(digest: str, cefr_count: int, synonym_count: int, antonym_count: int) -> str:
    return f"""# Runner PR1 equivalence fixture (hermetic)

## Command

```bash
.venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py --write-sealed
```

## What the baseline proves

Record-equivalent **CEFR band boundaries** (``_prepare_cefr_estimates`` cohort
quantiles) and **reciprocal relation closure**
(``_*_relations_by_headword``) for a frozen 500-lemma offline slice.

The PR1 sealed phases must reproduce these maps exactly (foundation for #5331).

## Baseline digest

`SHA256(baseline_enriched.json) = {digest}`

- CEFR estimate keys: {cefr_count}
- Synonym headwords with edges: {synonym_count}
- Antonym headwords with edges: {antonym_count}
"""


def _write_sealed_baseline(entries: list[dict[str, Any]], sources_path: Path, grac: dict[str, Any]) -> str:
    """Rewrite sealed fixture files. Caller must have passed ``--write-sealed``."""
    # Offline only for this sealed recompute. Set at call time, not import time,
    # and restore afterwards so tests keep a clean process env (#5247).
    previous = os.environ.get("LEXICON_SLOVNYK_OFFLINE")
    os.environ.setdefault("LEXICON_SLOVNYK_OFFLINE", "1")
    try:
        print("computing legacy CEFR + relation baseline…")
        cefr_snap, rel_snap = _legacy_cefr_and_relations(entries, sources_path, grac)
    finally:
        if previous is None:
            os.environ.pop("LEXICON_SLOVNYK_OFFLINE", None)
        else:
            os.environ["LEXICON_SLOVNYK_OFFLINE"] = previous
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
    synonym_count = len(rel_snap.get("synonym") or {})
    antonym_count = len(rel_snap.get("antonym") or {})
    (FIXTURE_DIR / "GENERATION.md").write_text(
        _generation_note(digest, len(cefr_snap), synonym_count, antonym_count),
        encoding="utf-8",
    )
    print(f"baseline sha256={digest}")
    print(f"cefr_keys={len(cefr_snap)} synonym_hw={synonym_count}")
    return digest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write the hermetic 500-lemma PR1 sources slice.\n"
            "Use --write-sealed only to regenerate the committed baseline on purpose. "
            "Tests must not pass it; they build a missing sqlite in a temp directory."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  .venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py \\
    --sources-out /tmp/sources_slice.sqlite
  .venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py --write-sealed

Outputs:
  Default: only sources_slice.sqlite (gitignored). Path is --sources-out, or
  tests/fixtures/lexicon/runner_pr1/sources_slice.sqlite when omitted.
  --write-sealed: that sqlite plus tracked slice inputs and the sealed baseline
  (baseline_enriched.json, baseline.sha256, GENERATION.md) under runner_pr1/.

Exit codes:
  0  sqlite written; sealed files rewritten only when --write-sealed was passed
  2  argument error

Related:
  tests/fixtures/lexicon/runner_pr1/GENERATION.md
  Issue #9001
""",
    )
    parser.add_argument(
        "--sources-out",
        type=Path,
        default=None,
        help=(
            "Where to write sources_slice.sqlite. "
            "Default: tests/fixtures/lexicon/runner_pr1/sources_slice.sqlite. "
            "Example: /tmp/sources_slice.sqlite"
        ),
    )
    parser.add_argument(
        "--write-sealed",
        action="store_true",
        help=(
            "Also rewrite tracked slice inputs and the sealed baseline "
            "(baseline_enriched.json, baseline.sha256, GENERATION.md). "
            "Default: false. Never set this from a test."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Write the sources slice. Sealed files change only with ``--write-sealed``.

    Importing this module has no process-env side effects (#5247). Offline
    mode is applied only around an explicit sealed recompute, then restored.
    """
    args = _parser().parse_args(argv)
    entries = _synthetic_entries(SLICE_SIZE)
    sources_path = args.sources_out or (FIXTURE_DIR / SOURCES_SLICE_NAME)
    build_sources_slice(sources_path, entries)
    if not args.write_sealed:
        print(f"wrote sources slice only: {sources_path}")
        print("sealed fixtures were not modified; pass --write-sealed to regenerate them")
        return 0
    grac = _synthetic_grac(entries)
    _write_tracked_inputs(entries, grac)
    _write_sealed_baseline(entries, sources_path, grac)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
