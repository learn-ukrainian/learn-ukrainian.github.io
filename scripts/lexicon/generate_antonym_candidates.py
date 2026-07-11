#!/usr/bin/env python3
"""Generate review-only morphological-negation antonym candidates."""

from __future__ import annotations

import argparse
import json
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
    load_artifact,
    merge_rows,
    normalize_word,
    summarize_rows,
    write_artifact,
)

AFFIXES = ("не-", "без-", "анти-", "проти-")
ALLOWED_POSITIONS = ("adj", "adv", "noun")
DEFAULT_MIN_FREQUENCY = 2


def generate(
    *,
    vesum_db: Path = DEFAULT_VESUM_DB,
    corpus_db: Path | None = DEFAULT_SOURCES_DB,
    frequency_json: Path | None = None,
    min_frequency: int = DEFAULT_MIN_FREQUENCY,
    sample_seed: int = 4975,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    vesum = VesumIndex(vesum_db)
    try:
        exact = vesum.exact_lemmas(ALLOWED_POSITIONS)
        bases = sorted(exact)
        possible: list[tuple[str, str, str, str]] = []
        for base in bases:
            for affix in AFFIXES:
                prefix = affix[:-1]
                if base.startswith(prefix):
                    continue
                negated = normalize_word(prefix + base)
                common_positions = sorted(exact.get(base, set()) & exact.get(negated, set()))
                for pos in common_positions:
                    possible.append((base, negated, affix, pos))

        frequency = FrequencySource(vesum=vesum, corpus_db=corpus_db, frequency_json=frequency_json)
        frequencies = frequency.count({word for base, negated, _affix, _pos in possible for word in (base, negated)})
        rows: list[dict[str, Any]] = []
        for base, negated, affix, pos in possible:
            freq_base = frequencies.get(base)
            freq_negated = frequencies.get(negated)
            base_is_rare = freq_base is None or freq_base < min_frequency
            negated_is_rare = freq_negated is None or freq_negated < min_frequency
            confidence = "high" if not base_is_rare and not negated_is_rare else "low"
            rows.append(
                {
                    "relation": "antonym",
                    "word": base,
                    "antonym": negated,
                    "affix": affix,
                    "pos": pos,
                    "confidence": confidence,
                    "freq_word": freq_base,
                    "freq_antonym": freq_negated,
                    "frequency_source": frequency.source,
                    "source": "vesum+morphological_negation",
                    "gate": {
                        "vesum_exact_lemma": base in exact and negated in exact,
                        "same_pos": pos in exact.get(base, set()) and pos in exact.get(negated, set()),
                        "base_is_real_lemma": vesum.verify_exact(base, pos),
                        "negative_is_real_lemma": vesum.verify_exact(negated, pos),
                        "base_not_prefixed_with_affix": not base.startswith(affix[:-1]),
                    },
                    "evidence": {
                        "algorithm": "valid VESUM lemma + valid VESUM prefixed lemma with shared POS",
                        "frequency_floor": min_frequency,
                        "rare_base_or_negative": base_is_rare or negated_is_rare,
                    },
                }
            )
        summary = {
            "candidate_pairs_before_frequency_review": len(rows),
            "affix_distribution": {affix: sum(row["affix"] == affix for row in rows) for affix in AFFIXES},
            "pos_distribution": {pos: sum(row["pos"] == pos for row in rows) for pos in ALLOWED_POSITIONS},
            "confidence_distribution": {level: sum(row["confidence"] == level for row in rows) for level in ("high", "low")},
            "frequency_source": frequency.source,
            "min_frequency": min_frequency,
            **summarize_rows(rows, sample_seed=sample_seed),
        }
        return rows, summary
    finally:
        vesum.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--corpus-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--frequency-json", type=Path)
    parser.add_argument("--min-frequency", type=int, default=DEFAULT_MIN_FREQUENCY)
    parser.add_argument("--sample-seed", type=int, default=4975)
    parser.add_argument("--out", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args()
    rows, summary = generate(
        vesum_db=args.vesum_db,
        corpus_db=args.corpus_db,
        frequency_json=args.frequency_json,
        min_frequency=args.min_frequency,
        sample_seed=args.sample_seed,
    )
    payload = load_artifact(args.out)
    payload["relations"]["antonyms"] = [
        row for row in payload["relations"]["antonyms"] if row.get("source") != "vesum+morphological_negation"
    ]
    added = merge_rows(payload, "antonyms", rows)
    payload.setdefault("metadata", {})["antonym_generator"] = {
        "config": {"min_frequency": args.min_frequency, "sample_seed": args.sample_seed},
        "summary": {key: value for key, value in summary.items() if key != "samples"},
    }
    write_artifact(payload, args.out)
    print(json.dumps({"added": added, **summary}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
