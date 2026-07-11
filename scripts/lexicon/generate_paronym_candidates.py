#!/usr/bin/env python3
"""Generate review-only paronym candidates from VESUM and corpus frequency.

The output is intentionally not consumed by ``enrich_manifest.py``.  Every
generated row carries the gates and evidence needed for a human review pass.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.relation_candidate_common import (
    DEFAULT_ARTIFACT,
    DEFAULT_SOURCES_DB,
    DEFAULT_VESUM_DB,
    FrequencySource,
    VesumIndex,
    iter_edit_pairs,
    levenshtein,
    load_artifact,
    merge_rows,
    normalize_word,
    orthographic_variant,
    shared_prefix_length,
    summarize_rows,
    write_artifact,
)

DEFAULT_MIN_FREQUENCY = 100
DEFAULT_SEED_DISTANCE = 2
PARONYM_POSITIONS = ("adj", "adv", "noun", "verb")


def _parse_pair(value: object) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for raw_pair in str(value or "").split(";"):
        members = [normalize_word(part) for part in raw_pair.split("/")]
        if len(members) == 2 and all(members) and members[0] != members[1]:
            pairs.append((members[0], members[1]))
    return pairs


def load_confirmed_seeds(sources_db: Path) -> list[tuple[str, str, str]]:
    """Read only the existing ZNO/cache seed relations; do not invent seeds."""
    if not sources_db.exists():
        return []
    seeds: list[tuple[str, str, str]] = []
    conn = sqlite3.connect(str(sources_db))
    try:
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(zno_tasks)")}
        if {"task_subtype", "paronym_pair"} <= columns:
            rows = conn.execute(
                "SELECT paronym_pair FROM zno_tasks WHERE task_subtype = 'paronym' OR trim(paronym_pair) != ''"
            )
            for (value,) in rows:
                seeds.extend((first, second, "ЗНО") for first, second in _parse_pair(value))
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(paronyms_cache)")}
        if {"word_a", "word_b"} <= columns:
            rows = conn.execute("SELECT word_a, word_b FROM paronyms_cache")
            seeds.extend(
                (normalize_word(first), normalize_word(second), "paronyms_cache")
                for first, second in rows
                if normalize_word(first) and normalize_word(second)
            )
    finally:
        conn.close()
    deduplicated: dict[tuple[str, str], str] = {}
    for first, second, source in seeds:
        key = tuple(sorted((first, second)))
        deduplicated.setdefault(key, source)
    return [(first, second, source) for (first, second), source in sorted(deduplicated.items())]


def seed_matches(
    first: str,
    second: str,
    seeds: list[tuple[str, str, str]],
    *,
    radius: int = DEFAULT_SEED_DISTANCE,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for seed_first, seed_second, source in seeds:
        left = min(levenshtein(first, seed_first, cutoff=radius), levenshtein(first, seed_second, cutoff=radius))
        right = min(levenshtein(second, seed_first, cutoff=radius), levenshtein(second, seed_second, cutoff=radius))
        if left <= radius and right <= radius:
            matches.append({"pair": [seed_first, seed_second], "source": source, "distance": [left, right]})
    return matches


def generate(
    *,
    vesum_db: Path = DEFAULT_VESUM_DB,
    sources_db: Path = DEFAULT_SOURCES_DB,
    corpus_db: Path | None = DEFAULT_SOURCES_DB,
    frequency_json: Path | None = None,
    min_frequency: int = DEFAULT_MIN_FREQUENCY,
    seed_distance: int = DEFAULT_SEED_DISTANCE,
    sample_seed: int = 4975,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    vesum = VesumIndex(vesum_db)
    try:
        exact = {
            word: positions
            for word, positions in vesum.exact_lemmas(PARONYM_POSITIONS).items()
            if len(word) >= 3
        }
        frequency = FrequencySource(vesum=vesum, corpus_db=corpus_db, frequency_json=frequency_json)
        exact_frequencies = frequency.count_exact_lemmas(exact)
        eligible = {
            word: positions
            for word, positions in exact.items()
            if exact_frequencies.get(word) is not None and exact_frequencies[word] >= min_frequency
        }
        pairs = list(iter_edit_pairs(eligible, max_distance=2))
        candidate_lemmas = {word for first, second, _pos, _distance in pairs for word in (first, second)}
        frequencies = {word: exact_frequencies.get(word) for word in candidate_lemmas}
        seeds = load_confirmed_seeds(sources_db)
        rows: list[dict[str, Any]] = []
        for first, second, pos, distance in pairs:
            freq_first = frequencies.get(first)
            freq_second = frequencies.get(second)
            seed_evidence = seed_matches(first, second, seeds, radius=seed_distance)
            prefix_len = shared_prefix_length(first, second)
            suffix_len = 0
            for left, right in zip(reversed(first), reversed(second), strict=False):
                if left != right:
                    break
                suffix_len += 1
            gate = {
                "vesum_exact_lemma": first in exact and second in exact,
                "same_pos": pos in exact.get(first, set()) and pos in exact.get(second, set()),
                "not_inflectional_variant": not vesum.are_inflectional_variants(first, second),
                "frequency_floor": freq_first is not None and freq_second is not None and freq_first >= min_frequency and freq_second >= min_frequency,
                "not_orthographic_variant": not orthographic_variant(first, second),
                "confusable_stem_or_seed": max(prefix_len, suffix_len) >= 4 or bool(seed_evidence),
            }
            if not all(gate.values()):
                continue
            confidence = "medium" if seed_evidence else "low"
            rows.append(
                {
                    "relation": "paronym",
                    "word_a": first,
                    "word_b": second,
                    "edit_distance": distance,
                    "shared_prefix_len": prefix_len,
                    "shared_suffix_len": suffix_len,
                    "pos": pos,
                    "freq_a": freq_first,
                    "freq_b": freq_second,
                    "frequency_source": frequency.source,
                    "frequency_measure": "exact lemma spelling occurrences in literary_texts",
                    "confidence": confidence,
                    "source": "vesum+literary_corpus",
                    "gate": gate,
                    "evidence": {
                        "algorithm": "same-POS exact VESUM lemmas within Levenshtein distance 1-2",
                        "seed_neighborhood": seed_evidence,
                        "frequency_floor": min_frequency,
                        "confusable_similarity_floor": 4,
                    },
                }
            )
        summary = {
            "candidate_pairs_before_gates": len(pairs),
            "candidate_lemmas": len(candidate_lemmas),
            "seeds": len(seeds),
            "frequency_source": frequency.source,
            "frequency_measure": "exact lemma spelling occurrences in literary_texts",
            "min_frequency": min_frequency,
            "edit_distance_distribution": {str(distance): sum(row["edit_distance"] == distance for row in rows) for distance in (1, 2)},
            "confidence_distribution": {level: sum(row["confidence"] == level for row in rows) for level in ("high", "medium", "low")},
            **summarize_rows(rows, sample_seed=sample_seed),
        }
        return rows, summary
    finally:
        vesum.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--corpus-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--frequency-json", type=Path)
    parser.add_argument("--min-frequency", type=int, default=DEFAULT_MIN_FREQUENCY)
    parser.add_argument("--seed-distance", type=int, default=DEFAULT_SEED_DISTANCE)
    parser.add_argument("--sample-seed", type=int, default=4975)
    parser.add_argument("--out", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args()
    rows, summary = generate(
        vesum_db=args.vesum_db,
        sources_db=args.sources_db,
        corpus_db=args.corpus_db,
        frequency_json=args.frequency_json,
        min_frequency=args.min_frequency,
        seed_distance=args.seed_distance,
        sample_seed=args.sample_seed,
    )
    payload = load_artifact(args.out)
    payload["relations"]["paronyms"] = [
        row for row in payload["relations"]["paronyms"] if row.get("source") != "vesum+literary_corpus"
    ]
    added = merge_rows(payload, "paronyms", rows)
    payload.setdefault("metadata", {})["paronym_generator"] = {
        "config": {"min_frequency": args.min_frequency, "seed_distance": args.seed_distance, "sample_seed": args.sample_seed},
        "summary": {key: value for key, value in summary.items() if key != "samples"},
    }
    write_artifact(payload, args.out)
    print(json.dumps({"added": added, **summary}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
