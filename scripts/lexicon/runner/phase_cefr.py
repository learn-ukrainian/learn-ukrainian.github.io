"""Phase 1 — sealed full-cohort CEFR precompute (#5230 / foundation for #5331).

Preserves ``_prepare_cefr_estimates`` cohort-quantile semantics EXACTLY:

- Collect non-PULS Ukrainian single-word lemmas from the full cohort.
- Rank by GRAC relative frequency (desc), then casefold key.
- Band into A1/A2/B1/B2/C1 by ``min(4, int(index * 5 / total))``.

Chunks receive only their sealed CEFR row + the run-phase seal hash.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import CEFR_ALGORITHM_VERSION, PhaseSeal, canonical_json

_UKRAINIAN_WORD_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ'’ʼ-]+$")
_BANDS = ("A1", "A2", "B1", "B2", "C1")


def _has_whitespace(text: str) -> bool:
    return any(ch.isspace() for ch in text)


def sealed_cefr_precompute(
    *,
    lemmas: Iterable[str],
    puls_cefr_fn: Callable[[str], dict[str, str] | None],
    grac_lookup_key_fn: Callable[[str], str],
    grac_cache: dict[str, Any],
    output_db: Path,
) -> PhaseSeal:
    """Compute sealed CEFR estimates for the complete non-PULS cohort."""
    words: list[str] = []
    for lemma in lemmas:
        word = grac_lookup_key_fn(lemma)
        if not word or _has_whitespace(word) or not _UKRAINIAN_WORD_RE.fullmatch(word):
            continue
        if puls_cefr_fn(lemma):
            continue
        words.append(word)

    unique_words = sorted(set(words), key=str.casefold)
    scored: list[tuple[str, float, int, str]] = []
    for word in unique_words:
        row = grac_cache.get(word)
        if not isinstance(row, dict):
            continue
        rel_freq = float(row.get("rel_freq") or 0.0)
        freq = int(row.get("freq") or 0)
        if rel_freq <= 0.0 or freq <= 0:
            continue
        scored.append((word, rel_freq, freq, str(row.get("word") or word)))

    scored.sort(key=lambda item: (-item[1], item[0].casefold()))
    total = len(scored)

    output_db.parent.mkdir(parents=True, exist_ok=True)
    if output_db.exists():
        output_db.unlink()
    conn = sqlite3.connect(output_db)
    try:
        conn.executescript(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE cefr_estimates (
                word_key TEXT PRIMARY KEY,
                level TEXT NOT NULL,
                rel_freq REAL NOT NULL,
                freq INTEGER NOT NULL,
                grac_word TEXT NOT NULL,
                rank INTEGER NOT NULL,
                total INTEGER NOT NULL
            );
            """
        )
        rows_out: list[dict[str, Any]] = []
        if total:
            for index, (word, rel_freq, freq, grac_word) in enumerate(scored):
                band_index = min(4, int(index * len(_BANDS) / total))
                level = _BANDS[band_index]
                conn.execute(
                    """
                    INSERT INTO cefr_estimates(
                        word_key, level, rel_freq, freq, grac_word, rank, total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (word, level, rel_freq, freq, grac_word, index + 1, total),
                )
                rows_out.append(
                    {
                        "word_key": word,
                        "level": level,
                        "rel_freq": rel_freq,
                        "freq": freq,
                        "grac_word": grac_word,
                        "rank": index + 1,
                        "total": total,
                    }
                )
        seal_payload = {
            "algorithm_version": CEFR_ALGORITHM_VERSION,
            "rows": rows_out,
        }
        seal_sha = hashlib.sha256(canonical_json(seal_payload).encode("utf-8")).hexdigest()
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("seal_sha256", seal_sha),
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("algorithm_version", CEFR_ALGORITHM_VERSION),
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("row_count", str(len(rows_out))),
        )
        conn.commit()
    finally:
        conn.close()
    return PhaseSeal(
        phase="cefr_precompute",
        seal_sha256=seal_sha,
        algorithm_version=CEFR_ALGORITHM_VERSION,
        row_count=len(rows_out),
    )


def load_sealed_cefr_map(path: Path) -> dict[str, dict[str, Any]]:
    """Load sealed CEFR rows keyed by GRAC word key (same shape as engine cache)."""
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        out: dict[str, dict[str, Any]] = {}
        for row in conn.execute(
            "SELECT word_key, level, rel_freq, freq, grac_word, rank, total FROM cefr_estimates"
        ):
            out[str(row[0])] = {
                "level": str(row[1]),
                "rel_freq": float(row[2]),
                "freq": int(row[3]),
                "grac_word": str(row[4]),
                "rank": int(row[5]),
                "total": int(row[6]),
            }
        return out
    finally:
        conn.close()


def estimated_cefr_from_seal(
    lemma: str,
    sealed: dict[str, dict[str, Any]],
    *,
    grac_lookup_key_fn: Callable[[str], str],
    source_label: str,
) -> dict[str, str] | None:
    """Mirror ``_estimated_cefr`` using a sealed map."""
    word = grac_lookup_key_fn(lemma)
    estimate = sealed.get(word)
    if not estimate:
        return None
    level = str(estimate["level"])
    rel_freq = float(estimate["rel_freq"])
    rank = int(estimate["rank"])
    total = int(estimate["total"])
    return {
        "level": level,
        "source": source_label,
        "text": f"{level} (орієнтовно / estimated; GRAC {rel_freq:.2f}/million, rank {rank}/{total})",
    }


def apply_sealed_cefr_to_engine_cache(
    sealed: dict[str, dict[str, Any]],
    engine_cache: dict[str, dict[str, Any]],
) -> None:
    """Replace the in-process CEFR estimate cache with sealed cohort rows."""
    engine_cache.clear()
    engine_cache.update(sealed)
