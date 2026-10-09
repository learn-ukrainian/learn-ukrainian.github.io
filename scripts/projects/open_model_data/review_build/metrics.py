"""Exact catalog-prefix and repetition shares; source text supplies no diversity."""

import re
import unicodedata
from collections import Counter
from fractions import Fraction

from .catalog import Catalog
from .errors import require


def tokens(template: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFC", template).casefold().replace("'", "’")
    return tuple(re.findall(r"[^\W\d_]+(?:’[^\W\d_]+)*", normalized))


def _shares(counter: Counter, count: int) -> dict:
    frequencies = sorted(counter.values(), reverse=True)
    return {
        "distinct": len(counter),
        "top1": [max(frequencies, default=0), count],
        "top5": [sum(frequencies[:5]), count],
    }


def _bounded(shares: dict, first: str, five: str | None = None) -> bool:
    return Fraction(*shares["top1"]) <= Fraction(first) and (
        five is None or Fraction(*shares["top5"]) <= Fraction(five)
    )


def measure(line_ids: list[str], catalog: Catalog) -> dict:
    count = len(line_ids)
    if count == 0:
        return {"N": 0, "status": "missing_coverage"}
    sequences = [tokens(catalog.template(i)) for i in line_ids]
    prefix = catalog.data["prefix_metric"]
    repetition = catalog.data["repetition_metric"]
    require(
        prefix["id"] == "instruction-prefix.v1-draft" and repetition["id"] == "instruction-repetition.v1-draft",
        "metric_spec",
    )
    # Versions pin thresholds: configuration cannot quietly lower the bar.
    require(
        prefix["prefix_lengths"] == [1, 4]
        and prefix["top1_max"] == 0.15
        and prefix["top5_max"] == 0.6
        and repetition["ngram_length"] == 8
        and repetition["whole_template_top1_max"] == 0.15
        and repetition["whole_template_top5_max"] == 0.6
        and repetition["suffix_top1_max"] == 0.6
        and repetition["ngram_record_share_max"] == 0.6,
        "metric_spec",
    )
    grams = Counter()
    for sequence in sequences:
        grams.update(set(sequence[i : i + 8] for i in range(max(1, len(sequence) - 7))))
    result = {
        "N": count,
        "prefix1": _shares(Counter(s[:1] for s in sequences), count),
        "prefix4": _shares(Counter(s[:4] for s in sequences), count),
        "ids": _shares(Counter(line_ids), count),
        "templates": _shares(Counter(sequences), count),
        "suffix8": _shares(Counter(s[-8:] for s in sequences), count),
        "ngram8": _shares(grams, count),
    }
    passed = all(_bounded(result[key], "0.15", "0.60") for key in ("prefix1", "prefix4", "ids", "templates"))
    passed = passed and _bounded(result["suffix8"], "0.60") and _bounded(result["ngram8"], "0.60")
    result["status"] = "insufficient_evidence" if count < 10 else "PASS" if passed else "FAIL"
    return result
