#!/usr/bin/env python3
"""Measure fill_local vs full-enrich CEFR / relation alignment (#5331).

Historical LIVE path divergences (pre-fix):

1. **CEFR** — ``scripts/atlas/fill_local.py`` cleared
   ``enrich_manifest._CEFR_ESTIMATE_LEVEL_BY_KEY`` and never rebuilt it.
   Full ``enrich()`` runs ``_prepare_cefr_estimates`` (or the sealed CEFR phase)
   over the cohort, so non-PULS lemmas get GRAC quantile bands.

2. **Relations** — full ``enrich()`` precomputes pointer maps with reciprocal
   closure and passes them into ``enrich_entry``. Pre-fix ``fill_local`` called
   ``enrich_entry`` without pointer args, so only per-lemma forward extractors
   ran (reciprocal edges onto other cohort headwords were absent).

3. **Synonym kwarg** — ``enrich_entry`` accepted ``pointer_synonym_relations``
   but did not merge them (mphdict-only) until the #5331 wire-up.

This module measures those gaps **offline** on a fixed synthetic cohort (≤50
lemmas by default) without rewriting the live gitignored manifest. Prefer the
committed hermetic builder over live ``data/`` so CI stays OOM-safe.

After the fill_local + enrich_entry fix, the **fixed** path (prepare CEFR +
closed pointer maps, matching live ``fill_local``) should report zero
``missing_on_fill`` and zero ``only_on_enrich`` edge deltas for the synthetic
cohort. The **legacy** path is retained so the pre-fix divergence remains
reproducible for regression notes.

Usage::

    .venv/bin/python scripts/atlas/measure_fill_enrich_divergence.py
    .venv/bin/python scripts/atlas/measure_fill_enrich_divergence.py --json /tmp/div.json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from scripts.lexicon import enrich_manifest as em

DEFAULT_COHORT_SIZE = 50
RELATION_KINDS = ("synonym", "antonym", "homonym", "paronym")
_ALPHABET = "абвгдежзиклмнопрстуфхцчшщюяєіїґ"


def _lemma_at(index: int) -> str:
    n = index + 1
    chars: list[str] = []
    while n:
        n, rem = divmod(n - 1, len(_ALPHABET))
        chars.append(_ALPHABET[rem])
    return "тест" + "".join(reversed(chars))


def build_synthetic_entries(n: int = DEFAULT_COHORT_SIZE) -> list[dict[str, Any]]:
    """Build a fixed ≤50 lemma cohort with PULS, synonym, and antonym coverage."""
    if n < 12:
        raise ValueError("cohort size must be at least 12 to cover PULS + relation pairs")
    if n > 50:
        raise ValueError("cohort size must be ≤50 for the CI-safe fixture")
    entries: list[dict[str, Any]] = []
    for i in range(n):
        lemma = _lemma_at(i)
        entries.append(
            {
                "lemma": lemma,
                "url_slug": lemma,
                "pos": "noun" if i % 3 else "verb",
                "gloss": f"gloss-{i % 7}",
            }
        )
    return entries


def build_synthetic_sources(path: Path, entries: list[dict[str, Any]]) -> None:
    """Write an offline sources.sqlite slice for the synthetic cohort."""
    if path.exists():
        path.unlink()
    n = len(entries)
    puls_end = min(10, n)
    synonym_start = puls_end
    # Even-aligned pairs inside the remaining middle third.
    synonym_end = min(n, synonym_start + max(0, ((n - synonym_start) // 3) * 2))
    if synonym_end % 2 != synonym_start % 2:
        synonym_end -= 1
    antonym_start = synonym_end
    antonym_end = min(n, antonym_start + max(0, ((n - antonym_start) // 2) * 2))
    if antonym_end % 2 != antonym_start % 2:
        antonym_end -= 1

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
            """
        )
        for i in range(puls_end):
            lemma = str(entries[i]["lemma"])
            conn.execute(
                "INSERT INTO puls_cefr(word, level, text) VALUES (?, 'A1', ?)",
                (lemma, f"PULS {lemma}"),
            )
        for i in range(synonym_start, synonym_end, 2):
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
        for i in range(antonym_start, antonym_end, 2):
            a = str(entries[i]["lemma"])
            b = str(entries[i + 1]["lemma"])
            # One-directional pointer only — reciprocal comes from by_headword closure.
            conn.execute(
                "INSERT INTO sum11(word, definition, text) VALUES (?, ?, ?)",
                (a, f"протилежне {b}.", f"протилежне {b}."),
            )
        conn.commit()
    finally:
        conn.close()


def build_synthetic_grac(entries: list[dict[str, Any]], *, puls_count: int = 10) -> dict[str, Any]:
    """GRAC frequency rows for non-PULS lemmas (enables estimated CEFR bands)."""
    out: dict[str, Any] = {}
    for i, entry in enumerate(entries):
        if i < puls_count:
            continue
        lemma = str(entry["lemma"])
        key = em._grac_lookup_key(lemma)
        rel = float(1000 - i)
        out[key] = {"word": lemma, "freq": int(rel * 1000), "rel_freq": rel}
    return out


@contextmanager
def _vesum_always_valid() -> Iterator[None]:
    """Hermetic VESUM gate so synthetic lemmas form valid relation ends."""
    original_valid = em._vesum_valid_synonym
    original_analyses = em._vesum_word_analyses
    em._vesum_valid_synonym = lambda term: bool(term)  # type: ignore[assignment]
    em._vesum_word_analyses = lambda word: ((word, "noun"),)  # type: ignore[assignment]
    try:
        yield
    finally:
        em._vesum_valid_synonym = original_valid
        em._vesum_word_analyses = original_analyses


@contextmanager
def _engine_state(grac_cache: dict[str, Any]) -> Iterator[None]:
    """Isolate mutable enrich_manifest globals for a measurement run."""
    previous_cefr = dict(em._CEFR_ESTIMATE_LEVEL_BY_KEY)
    previous_grac = em._GRAC_FREQUENCY_CACHE_DATA
    em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    em._GRAC_FREQUENCY_CACHE_DATA = dict(grac_cache)
    try:
        with _vesum_always_valid():
            yield
    finally:
        em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
        em._CEFR_ESTIMATE_LEVEL_BY_KEY.update(previous_cefr)
        em._GRAC_FREQUENCY_CACHE_DATA = previous_grac


def _entry_key(lemma: str) -> str | None:
    return em._canonical_synonym_term(lemma)


def _relation_edge_key(source: str, relation: dict[str, Any]) -> tuple[str, str, str]:
    target = str(relation.get("item") or relation.get("word") or "")
    direction = str(relation.get("direction") or "forward")
    return (source, target, direction)


def _edge_stats(by_headword: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    edges: list[tuple[str, str, str]] = []
    for source, relations in by_headword.items():
        for relation in relations:
            edges.append(_relation_edge_key(source, relation))
    reciprocal = sum(1 for _s, _t, direction in edges if direction == "reciprocal")
    return {
        "headwords_with_edges": len(by_headword),
        "edges": len(edges),
        "reciprocal_edges": reciprocal,
        "forward_edges": len(edges) - reciprocal,
        "edge_keys": sorted(edges),
    }


def fill_local_style_relations(
    conn: sqlite3.Connection,
    entries: list[dict[str, Any]],
    *,
    has_sum11_flags: bool,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Per-lemma extractors only — pre-fix fill_local / enrich_entry None-pointer path."""
    out: dict[str, dict[str, list[dict[str, Any]]]] = {kind: {} for kind in RELATION_KINDS}
    for entry in entries:
        lemma = str(entry.get("lemma") or "")
        key = _entry_key(lemma)
        if not key:
            continue
        synonym = em._definition_pointer_relations(
            conn, lemma, has_sum11_flags=has_sum11_flags
        )
        if synonym:
            out["synonym"][key] = synonym
        antonym = em._definition_antonym_relations(
            conn, lemma, has_sum11_flags=has_sum11_flags
        )
        if antonym:
            out["antonym"][key] = antonym
        homonym = em._homonym_relations(conn, lemma)
        if homonym:
            out["homonym"][key] = homonym
        paronym = em._paronym_relations(conn, lemma)
        if paronym:
            out["paronym"][key] = paronym
    return out


def enrich_style_relations(
    conn: sqlite3.Connection,
    manifest: dict[str, Any],
    *,
    has_sum11_flags: bool,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Run-level by_headword maps with reciprocal closure (full enrich / fixed fill_local)."""
    return {
        "synonym": em._definition_pointer_relations_by_headword(
            conn, manifest, has_sum11_flags=has_sum11_flags
        ),
        "antonym": em._definition_antonym_relations_by_headword(
            conn, manifest, has_sum11_flags=has_sum11_flags
        ),
        "homonym": em._homonym_relations_by_headword(conn, manifest),
        "paronym": em._paronym_relations_by_headword(conn, manifest),
    }


def _cefr_delta(
    lemmas: list[str],
    fill_cefr: dict[str, dict[str, str] | None],
    enrich_cefr: dict[str, dict[str, str] | None],
    *,
    prepared_estimate_keys: int,
) -> dict[str, Any]:
    missing_on_fill: list[str] = []
    level_divergent: list[dict[str, Any]] = []
    fill_present = 0
    enrich_present = 0
    enrich_estimated = 0
    for lemma in lemmas:
        fill_block = fill_cefr.get(lemma)
        enrich_block = enrich_cefr.get(lemma)
        if fill_block:
            fill_present += 1
        if enrich_block:
            enrich_present += 1
            if str(enrich_block.get("source") or "") == em._CEFR_ESTIMATED_SOURCE:
                enrich_estimated += 1
        if enrich_block and not fill_block:
            missing_on_fill.append(lemma)
        elif (
            fill_block
            and enrich_block
            and str(fill_block.get("level") or "") != str(enrich_block.get("level") or "")
        ):
            level_divergent.append(
                {
                    "lemma": lemma,
                    "fill_level": fill_block.get("level"),
                    "enrich_level": enrich_block.get("level"),
                    "fill_source": fill_block.get("source"),
                    "enrich_source": enrich_block.get("source"),
                }
            )
    return {
        "fill_present": fill_present,
        "enrich_present": enrich_present,
        "enrich_estimated": enrich_estimated,
        "missing_on_fill_count": len(missing_on_fill),
        "missing_on_fill_lemmas": missing_on_fill,
        "level_divergent_count": len(level_divergent),
        "level_divergent": level_divergent,
        "prepared_estimate_keys": prepared_estimate_keys,
    }


def _relation_delta(
    fill_relations: dict[str, dict[str, list[dict[str, Any]]]],
    enrich_relations: dict[str, dict[str, list[dict[str, Any]]]],
) -> dict[str, Any]:
    relation_delta: dict[str, Any] = {}
    for kind in RELATION_KINDS:
        fill_stats = _edge_stats(fill_relations.get(kind, {}))
        enrich_stats = _edge_stats(enrich_relations.get(kind, {}))
        fill_keys = set(fill_stats.pop("edge_keys"))
        enrich_keys = set(enrich_stats.pop("edge_keys"))
        only_enrich = sorted(enrich_keys - fill_keys)
        only_fill = sorted(fill_keys - enrich_keys)
        relation_delta[kind] = {
            "fill_local": fill_stats,
            "enrich": enrich_stats,
            "edges_only_on_enrich": len(only_enrich),
            "edges_only_on_fill": len(only_fill),
            "reciprocal_only_on_enrich": sum(
                1 for _s, _t, direction in only_enrich if direction == "reciprocal"
            ),
            "sample_only_on_enrich": [
                {"source": s, "target": t, "direction": d} for s, t, d in only_enrich[:8]
            ],
        }
    return relation_delta


def measure_divergence(
    entries: list[dict[str, Any]],
    sources_db: Path,
    grac_cache: dict[str, Any],
    *,
    open_conn: Callable[[Path], sqlite3.Connection] | None = None,
) -> dict[str, Any]:
    """Compare fill_local paths vs full-enrich-style CEFR + relation precomputes.

    Returns a JSON-serializable summary. Numbers come only from the executed paths.

    ``fixed`` mirrors post-#5331 ``fill_local`` (prepare CEFR + closed pointer maps).
    ``legacy`` mirrors the pre-fix clear-only / per-lemma-extractor path.
    """
    if not entries:
        raise ValueError("entries must be non-empty")
    if len(entries) > 50:
        raise ValueError("measure at most 50 lemmas (CI-safe cohort cap)")

    manifest = {"entries": [dict(entry) for entry in entries]}
    lemmas = [str(entry.get("lemma") or "") for entry in entries]
    connect = open_conn or (lambda path: sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True))

    with _engine_state(grac_cache):
        conn = connect(sources_db)
        try:
            has_sum11 = em._sum11_has_flag_columns(conn)

            # --- legacy fill_local CEFR path: clear estimates, do not rebuild ---
            em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
            legacy_fill_cefr: dict[str, dict[str, str] | None] = {}
            for lemma in lemmas:
                legacy_fill_cefr[lemma] = em._cefr(conn, lemma)

            # --- fixed fill_local / full enrich CEFR path: prepare cohort quantiles ---
            em._prepare_cefr_estimates(conn, manifest)
            fixed_fill_cefr: dict[str, dict[str, str] | None] = {}
            enrich_cefr: dict[str, dict[str, str] | None] = {}
            for lemma in lemmas:
                block = em._cefr(conn, lemma)
                fixed_fill_cefr[lemma] = block
                enrich_cefr[lemma] = block

            legacy_fill_relations = fill_local_style_relations(
                conn, entries, has_sum11_flags=has_sum11
            )
            fixed_fill_relations = enrich_style_relations(
                conn, manifest, has_sum11_flags=has_sum11
            )
            enrich_relations = fixed_fill_relations
            prepared_estimate_keys = len(em._CEFR_ESTIMATE_LEVEL_BY_KEY)
        finally:
            conn.close()

    legacy_cefr = _cefr_delta(
        lemmas,
        legacy_fill_cefr,
        enrich_cefr,
        prepared_estimate_keys=0,
    )
    fixed_cefr = _cefr_delta(
        lemmas,
        fixed_fill_cefr,
        enrich_cefr,
        prepared_estimate_keys=prepared_estimate_keys,
    )
    legacy_relations = _relation_delta(legacy_fill_relations, enrich_relations)
    fixed_relations = _relation_delta(fixed_fill_relations, enrich_relations)

    return {
        "schema": "fill-enrich-divergence-v2",
        "issue": 5331,
        "lemmas_compared": len(lemmas),
        "lemmas": lemmas,
        # Top-level keys keep the fixed path (post-#5331 fill_local) as primary.
        "cefr": fixed_cefr,
        "relations": fixed_relations,
        "legacy": {
            "cefr": legacy_cefr,
            "relations": legacy_relations,
        },
        "notes": {
            "fixed_path": (
                "Post-#5331 fill_local prepares _CEFR_ESTIMATE_LEVEL_BY_KEY via "
                "_prepare_cefr_estimates and passes closed pointer maps into "
                "enrich_entry; synonym pointers merge via _merge_synonym_relations. "
                "On the same cohort as full enrich, missing_on_fill and "
                "only_on_enrich should be zero."
            ),
            "legacy_path": (
                "Pre-fix fill_local cleared CEFR estimates without rebuild and "
                "called enrich_entry without pointer_* maps (forward extractors only). "
                "legacy.* preserves those pre-fix numbers for regression notes."
            ),
            "single_slug_residual": (
                "Single-slug fill_local only closes relations within the fill "
                "cohort (that slug set). Full-atlas reciprocity still needs a "
                "full-cohort or #5230 sealed relation map."
            ),
        },
    }


def run_default_measurement(cohort_size: int = DEFAULT_COHORT_SIZE) -> dict[str, Any]:
    """Build the hermetic ≤50 cohort in a temp dir and measure divergence."""
    entries = build_synthetic_entries(cohort_size)
    with tempfile.TemporaryDirectory(prefix="fill-enrich-div-") as tmp:
        tmp_path = Path(tmp)
        sources = tmp_path / "sources.sqlite"
        build_synthetic_sources(sources, entries)
        grac = build_synthetic_grac(entries, puls_count=min(10, len(entries)))
        return measure_divergence(entries, sources, grac)


def format_summary(result: dict[str, Any]) -> str:
    """Human-readable one-screen summary of a measurement result."""
    cefr = result["cefr"]
    legacy_cefr = result.get("legacy", {}).get("cefr", {})
    lines = [
        f"lemmas_compared {result['lemmas_compared']}",
        (
            f"cefr(fixed) missing_on_fill={cefr['missing_on_fill_count']} "
            f"fill_present={cefr['fill_present']} enrich_present={cefr['enrich_present']} "
            f"enrich_estimated={cefr['enrich_estimated']} "
            f"level_divergent={cefr['level_divergent_count']}"
        ),
    ]
    if legacy_cefr:
        lines.append(
            f"cefr(legacy) missing_on_fill={legacy_cefr['missing_on_fill_count']} "
            f"fill_present={legacy_cefr['fill_present']} "
            f"enrich_present={legacy_cefr['enrich_present']}"
        )
    for kind in RELATION_KINDS:
        rel = result["relations"][kind]
        lines.append(
            f"relations.{kind}(fixed) "
            f"fill_edges={rel['fill_local']['edges']} "
            f"enrich_edges={rel['enrich']['edges']} "
            f"only_on_enrich={rel['edges_only_on_enrich']} "
            f"reciprocal_only_on_enrich={rel['reciprocal_only_on_enrich']}"
        )
        legacy_rel = result.get("legacy", {}).get("relations", {}).get(kind)
        if legacy_rel:
            lines.append(
                f"relations.{kind}(legacy) "
                f"fill_edges={legacy_rel['fill_local']['edges']} "
                f"enrich_edges={legacy_rel['enrich']['edges']} "
                f"only_on_enrich={legacy_rel['edges_only_on_enrich']}"
            )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure fill_local vs enrich CEFR/relation divergence (#5331)."
    )
    parser.add_argument(
        "--cohort-size",
        type=int,
        default=DEFAULT_COHORT_SIZE,
        help=f"Synthetic cohort size (12–50, default {DEFAULT_COHORT_SIZE}).",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Write full JSON summary to this path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 12 <= args.cohort_size <= 50:
        raise SystemExit("--cohort-size must be between 12 and 50")
    result = run_default_measurement(args.cohort_size)
    print(format_summary(result))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote json={args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
