#!/usr/bin/env python3
"""Deterministic UK-writing bakeoff scorer.

Scores a candidate's probe output (three `## SECTION N` blocks) on OBJECTIVE
signals reused from the existing QG infra — no LLM:

- VESUM validity: share of content tokens present in VESUM (real UK forms).
- Russicism rate: VESUM-gated pymorphy3 russian-shadow (``_russian_shadow_check``)
  MINUS heritage attestation (Grinchenko/ESUM) so genuine archaisms are not
  counted. This is the decolonization signal.
- VESUM-unknown rate: tokens absent from VESUM (proper nouns excluded).
- Immersion / English discipline vs the per-level ``SurfacePolicy``
  (A1 scaffolding OK → A2 receding warn 0.45 → B1+ warn 0.08/fail 0.18 →
  seminar warn 0.05/fail 0.12).

The three probe sections map to the three routing profiles:
    SECTION 1 → a2  (English-support immersion)
    SECTION 2 → b2  (pure immersion)
    SECTION 3 → seminar (culture content)

Usage: python -m scripts.audit.probe_uk_writing_score <candidate_output.md>
Needs data/vesum.db + data/sources.db (gitignored).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit._judge_eval_lib import (
    _heritage_check,
    _russian_shadow_check,
    _text_tokens,
    _vesum_unknown,
)
from scripts.audit.content_surface_gates import (
    _LATIN_WORD_RE,
    _english_led_findings,
    _mask_ignored_regions,
    _mask_tags,
    policy_for_level,
)
from scripts.verification.vesum import verify_words

# Profile per probe section. Section 3 uses a seminar track code ("folk") so
# policy_for_level returns the stricter _SEMINAR_POLICY (warn 0.05 / fail 0.12).
SECTION_LEVELS = {1: "a2", 2: "b2", 3: "folk"}

_CYRILLIC_WORD_RE = re.compile(r"[А-Яа-яЄєІіЇїҐґ'ʼʼ-]{2,}")
_SECTION_RE = re.compile(r"^\s*#{1,6}\s*SECTION\s*(\d)", re.IGNORECASE)

# VESUM indexes the ASCII apostrophe (U+0027). A writer that emits a typographic
# apostrophe (U+2019 ’, U+02BC ʼ, …) makes valid words like «з'являються» miss
# VESUM and get FALSE-flagged as russicisms / VESUM-unknown. Normalize before
# every check and report the non-canonical count separately — it is an
# orthographic-normalization need, NOT a quality defect.
_NONSTANDARD_APOS = (0x2019, 0x2018, 0x02BC, 0x02B9, 0x0060)
_APOS_TRANS = {code: 0x27 for code in _NONSTANDARD_APOS}

# A real UK word has a vowel. Drops junk tokens the tokenizer captures — e.g.
# «---» (markdown rule) — that pymorphy3 otherwise false-flags as russian.
_UK_VOWELS = frozenset("аеиіоуюяєїАЕИІОУЮЯЄЇ")


def _is_word(token: str) -> bool:
    return any(ch in _UK_VOWELS for ch in token)


def split_sections(text: str) -> dict[int, str]:
    """Split a candidate output into {section_index: body} by `## SECTION N`."""
    parts: dict[int, str] = {}
    current: int | None = None
    buf: list[str] = []
    for line in text.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            if current is not None:
                parts[current] = "\n".join(buf).strip()
            current = int(match.group(1))
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        parts[current] = "\n".join(buf).strip()
    return parts


def latin_ratio(text: str) -> tuple[int, int, float]:
    """Return (latin_words, cyrillic_words, latin/(latin+cyrillic))."""
    latin = len(_LATIN_WORD_RE.findall(text))
    cyr = len(_CYRILLIC_WORD_RE.findall(text))
    total = latin + cyr
    return latin, cyr, (latin / total if total else 0.0)


def score_section(text: str, level: str) -> dict:
    policy = policy_for_level(level)
    nonstandard_apostrophes = sum(text.count(chr(code)) for code in _NONSTANDARD_APOS)
    text = text.translate(_APOS_TRANS)
    tokens = _text_tokens(text)
    n = len(tokens)
    matches = verify_words(tokens) if tokens else {}
    valid = sum(1 for t in tokens if matches.get(t))
    unknown = [u for u in _vesum_unknown(text) if _is_word(u)]
    shadow = _russian_shadow_check(text)
    attested = {a["token"] for a in _heritage_check(text)}
    russicisms = [
        r
        for r in shadow.get("triggered_tokens", [])
        if r["token"] not in attested and _is_word(r["token"])
    ]

    latin, cyr, ratio = latin_ratio(text)
    masked = _mask_tags(_mask_ignored_regions(text))
    english_led = _english_led_findings(masked, policy=policy, source="probe")

    warn, fail = policy.english_ratio_warn, policy.english_ratio_fail
    if fail is not None and ratio >= fail:
        immersion = "FAIL"
    elif warn is not None and ratio >= warn:
        immersion = "WARN"
    else:
        immersion = "OK"

    return {
        "level": level,
        "content_tokens": n,
        "vesum_valid_pct": round(100 * valid / n, 1) if n else 0.0,
        "vesum_unknown": len(unknown),
        "vesum_unknown_tokens": unknown[:25],
        "russicisms": len(russicisms),
        "russicism_tokens": [r["token"] for r in russicisms],
        "russicism_available": shadow.get("available", False),
        "nonstandard_apostrophes": nonstandard_apostrophes,
        "latin_words": latin,
        "cyrillic_words": cyr,
        "latin_ratio": round(ratio, 3),
        "english_led_lines": len(english_led),
        "immersion_verdict": immersion,
        "immersion_policy": {"warn": warn, "fail": fail},
    }


def score_output(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    sections = split_sections(text)
    result: dict = {"file": str(path), "sections": {}}
    for idx, level in SECTION_LEVELS.items():
        body = sections.get(idx)
        if body:
            result["sections"][str(idx)] = score_section(body, level)
        else:
            result["sections"][str(idx)] = {"error": "section missing", "level": level}
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Score a UK-writing bakeoff candidate output.")
    ap.add_argument("file", type=Path, help="Candidate output file (## SECTION 1/2/3)")
    args = ap.parse_args()
    print(json.dumps(score_output(args.file), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
