#!/usr/bin/env python3
"""Phase 5.1: Automated Evaluation Suite for Ukrainian Linguistic Decolonization (ULDR #8050).

Evaluates aligned models against held-out partitions, enforcing 5 hard production gates:
  Gate 1: Calque Elimination Rate (>= 90.0%) on held-out CORRECT cases
  Gate 2: Harmful-Edit Rate (<= 1.0% exact 95% Clopper-Pearson upper bound on >= 300 PRESERVE cases)
  Gate 3: Span Integrity Gate (100% preservation of non-target sentence tokens)
  Gate 4: Citation Whitelist Gate (100% approved Ukrainian authorities, 0% hallucinated citations)
  Gate 5: High-Frequency Calque Floor (100% recall on top 50 pervasive Russianisms)

Supports:
  1. Direct offline scoring of generated predictions JSONL files
  2. Live PyTorch / Hugging Face Transformers model / adapter inference
  3. Deterministic contract verification mode for CI
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scipy.stats import beta

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_HELDOUT_PATH = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "partitions"
    / "heldout_evaluation_suite_1000.jsonl"
)

# Approved Ukrainian reference authorities for Gate 4 (unanchored for prose citation detection)
APPROVED_CITATION_PATTERNS = [
    re.compile(r"\bвесум(?:у|ом|і|а)?\b", re.IGNORECASE),
    re.compile(r"\bvesum\b", re.IGNORECASE),
    # Modern decolonized СУМ-20 only. Bilodid's Russian-Soviet occupation СУМ-11 (1970–1980)
    # is permanently quarantined for contrastive Sovietization analysis only; never accepted
    # as an approved positive authority for authentic Ukrainian vocabulary (Issue #8054).
    re.compile(r"\bсум-20\b", re.IGNORECASE),
    re.compile(r"\bправопис(?:у|ом|і)?(?:\s+(?:2019|1992|1928))?\b", re.IGNORECASE),
    re.compile(r"\bантоненк[оа]-давидович\w*\b", re.IGNORECASE),
    re.compile(r"«?як\s+ми\s+говоримо»?", re.IGNORECASE),
    re.compile(r"\bгрінченк\w*\b", re.IGNORECASE),
    re.compile(r"словарь\s+української\s+мови", re.IGNORECASE),
    re.compile(r"\bуліф\b", re.IGNORECASE),
    re.compile(r"словники\s+україни", re.IGNORECASE),
    re.compile(r"\bкараванськ\w*\b", re.IGNORECASE),
    re.compile(r"\bпономарів\w*\b", re.IGNORECASE),
    re.compile(r"\bмон(?:\s+україни)?\b", re.IGNORECASE),
    re.compile(r"\bпідручник\w*\b", re.IGNORECASE),
    re.compile(r"\bua-gec\b", re.IGNORECASE),
    re.compile(r"\bшевченк\w*\b", re.IGNORECASE),
    re.compile(r"\bфранк\w*\b", re.IGNORECASE),
    re.compile(r"\bкримськ\w*\b", re.IGNORECASE),
    re.compile(r"\bсинявськ\w*\b", re.IGNORECASE),
    re.compile(r"\bкурило\b", re.IGNORECASE),
    re.compile(r"\bголоскевич\w*\b", re.IGNORECASE),
]

# Approved Ukrainian reference authorities for Gate 4 (anchored to validate complete entity identity)
APPROVED_AUTHORITY_REGEXES = [
    re.compile(
        r"^(?:(?:словник(?:и|а|у|ом|і)?|корпус(?:и|а|у|ом|і)?|довідник(?:и|а|у|ом|і)?|баз(?:а|и|і|ою|ами|ах)?(?:\s+даних)?)\s+)?(?:весум(?:у|ом|і|а)?|vesum)(?:\s+(?:онлайн|on-line|\d+))?$",
        re.IGNORECASE,
    ),
    # Modern decolonized СУМ-20 only (Bilodid's Russian-Soviet occupation СУМ-11 permanently purged, Issue #8054).
    re.compile(
        r"^(?:(?:академічн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?|тлумачн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?)\s+)?(?:(?:словник(?:и|ів|ам|ами|ах|а|у|ом|і)?)\s+)?(?:сум|sum)[\s\-–—\u2010-\u2015]*20(?:\s+(?:онлайн|on-line|\d+))?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:(?:словник(?:и|ів|ам|ами|ах|а|у|ом|і)?)\s+)?(?:академічн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?\s+)?(?:словник\s+)?української\s+мови\s+(?:[ву]\s+20\s+томах|20[-–—\u2010-\u2015]?томн\w*)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:(?:чинн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?|новий|нового|новому|академічн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?|українськ(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?|офіційн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?)\s+)*правопис(?:у|ом|і)?(?:\s+(?:2019|1992|1928|1946|1960))?(?:\s+року)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:(?:прац(?:я|і|ею|ей|ям|ями|ях)?|книг(?:а|и|і|у|ою|ам|ами|ах)?)\s+)?(?:(?:борис(?:а|у|ом|ові|і)?)\s+)?антоненк[оа]-давидович(?:а|ем|еві|у|і)?(?:\s+«?як\s+ми\s+говоримо»?)?$",
        re.IGNORECASE,
    ),
    re.compile(r"^«?як\s+ми\s+говоримо»?$", re.IGNORECASE),
    re.compile(
        r"^(?:(?:словник(?:и|ів|ам|ами|ах|а|у|ом|і)?)\s+)?(?:(?:борис(?:а|у|ом|ові|і)?)\s+)?грінченк(?:о|а|у|ом|і)?(?:\s+словарь\s+української\s+мови)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^словарь\s+української\s+мови(?:\s+(?:грінченк(?:о|а|у|ом|і)?|1907(?:\s+року)?))?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:уліф(?:\s+нан\s+україни)?|словники\s+україни(?:\s+(?:on-line|онлайн))?)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:(?:словник(?:и|ів|ам|ами|ах|а|у|ом|і)?)\s+)?(?:(?:святослав(?:а|у|ом|ові|і)?)\s+)?караванськ(?:ого|ому|им|ий)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:(?:професор(?:а|у|ом|ові|і|и|ів|ам|ами|ах)?)\s+)?(?:(?:олександр(?:а|у|ом|ові|і)?)\s+)?пономар(?:ів|ьова|ьову|ьовим|ьові)?(?:\s+«?культура\s+слова»?)?$",
        re.IGNORECASE,
    ),
    re.compile(r"^«?культура\s+слова»?$", re.IGNORECASE),
    re.compile(
        r"^(?:мон(?:\s+україни)?|міністерств(?:о|а|у|ом|і)\s+освіти\s+і\s+науки(?:\s+україни)?)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:(?:шкільн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?|академічн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?)\s+)?підручник(?:и|а|у|ом|і)?(?:\s+з\s+української\s+мови)?(?:\s+для\s+(?:[1-9]|1[0-1])\s+класу)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:(?:корпус(?:и|ів|ам|ами|ах|а|у|ом|і)?)\s+)?ua-gec$",
        re.IGNORECASE,
    ),
    re.compile(r"^(?:(?:тарас(?:а|у|ом|ові|і)?)\s+)?шевченк(?:о|а|у|ом|і)?$", re.IGNORECASE),
    re.compile(r"^(?:(?:іван(?:а|у|ом|ові|і)?)\s+)?франк(?:о|а|у|ом|і)?$", re.IGNORECASE),
    re.compile(r"^(?:(?:агатангел(?:а|у|ом|ові|і)?)\s+)?кримськ(?:ого|ому|им|ий)?$", re.IGNORECASE),
    re.compile(r"^(?:(?:олекс(?:а|и|і|у|ею|ові)?)\s+)?синявськ(?:ого|ому|им|ий)?$", re.IGNORECASE),
    re.compile(r"^(?:(?:олен(?:а|и|і|у|ою)?)\s+)?курил(?:о|а|у|ом|і)$", re.IGNORECASE),
    re.compile(r"^голоскевич(?:а|ем|еві|у|і)?$", re.IGNORECASE),
    re.compile(
        r"^(?:кумех|граматичн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?\s+словник\s+української\s+мови)$",
        re.IGNORECASE,
    ),
]


def is_approved_authority(name: str) -> bool:
    """Validate authority against approved reference whitelist using anchored matching."""
    clean = name.strip().strip("«»\"'“”‘’")
    clean_norm = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015]", "-", clean).strip()
    # Reject ambiguous bare 'Словник української мови' or 'СУМ' without 20-volume qualification
    if re.match(
        r"^(?:академічн(?:ий|ого|ому|им|ім|і|их|ними|а|ої|ій|у|ою|е)?\s+)?словник\s+української\s+мови$",
        clean_norm,
        re.IGNORECASE,
    ):
        return False
    if clean_norm.upper() in ("СУМ", "SUM") or re.match(r"^(?:СУМ|SUM)[\s\-–—\u2010-\u2015]*11$", clean_norm, re.IGNORECASE):
        return False
    if re.match(
        r"^(?:академічн\w*\s+)?словник\w*\s+української\s+мови\s+(?:[ву]\s+(?:11|одинадцят\w*)\s+том\w*|11[\s\-–—\u2010-\u2015]?томн\w*|одинадцятитомн\w*|\((?:[ву]\s+)?11\s+том\w*\))$",
        clean_norm,
        re.IGNORECASE,
    ):
        return False
    if re.match(
        r"^(?:11[\s\-–—\u2010-\u2015]?томн\w*|одинадцятитомн\w*)\s+(?:академічн\w*\s+)?словник\w*\s+української\s+мови$",
        clean_norm,
        re.IGNORECASE,
    ):
        return False
    return any(p.match(clean) or p.match(clean_norm) for p in APPROVED_AUTHORITY_REGEXES)


# Blacklisted hallucinated, foreign, or Russian-Soviet occupation citations (Gate 4 violations)
PROHIBITED_CITATION_PATTERNS = [
    # Permanent Quarantine: Bilodid's Russian-Soviet occupation СУМ-11 (1970–1980)
    # is permanently prohibited from positive-authority citation (Issue #8054).
    re.compile(r"\b(?:сум|sum)[\s\-–—\u2010-\u2015]*11\b", re.IGNORECASE),
    re.compile(
        r"\b(?:академічн\w*\s+)?"
        r"словник\w*\s+української\s+мови"
        r"\s+(?:[ву]\s+(?:11|одинадцят\w*)\s+том\w*|11[\s\-–—\u2010-\u2015]?томн\w*|одинадцятитомн\w*|\((?:[ву]\s+)?11\s+том\w*\))",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:11[\s\-–—\u2010-\u2015]?томн\w*|одинадцятитомн\w*)\s+(?:академічн\w*\s+)?словник\w*\s+української\s+мови\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bбілодід\w*\b", re.IGNORECASE),
    re.compile(r"\bcobuild\b", re.IGNORECASE),
    re.compile(r"\blexicallab\b", re.IGNORECASE),
    re.compile(r"\bcollins\b", re.IGNORECASE),
    re.compile(r"\bmerriam-webster\b", re.IGNORECASE),
    re.compile(r"\boxford\b", re.IGNORECASE),
    re.compile(r"\bcambridge\b", re.IGNORECASE),
    re.compile(r"\bожегов\w*\b", re.IGNORECASE),
    re.compile(r"\bдаль\w*\b", re.IGNORECASE),
    re.compile(r"\bрозенталь\w*\b", re.IGNORECASE),
    re.compile(r"\bбрэ\b", re.IGNORECASE),
    re.compile(r"\bбсэ\b", re.IGNORECASE),
]

# Top 50 pervasive Ukrainian calques for Gate 5 floor
HIGH_FREQUENCY_CALQUES = [
    "приймати участь",
    "на протязі",
    "приймати міри",
    "в залежності",
    "в першу чергу",
    "мати місце",
    "кинутися в очі",
    "відігравати значення",
    "мати значення",
    "більша половина",
    "підняти питання",
    "заключити договір",
    "по крайній мірі",
    "в кінці кінців",
    "з цих пір",
    "до цих пір",
    "так як",
    "не дивлячись на",
    "у любий час",
    "слідуючий",
    "бажаючий",
    "діючий",
    "пануючий",
    "правлячий",
    "ведучий",
    "оточуюче середовище",
    "під відкритим небом",
    "понести збитки",
    "дати знати",
    "нанести удар",
    "оказати допомогу",
    "співпадати",
    "відноситися",
    "рахувати що",
    "складати враження",
    "кидатися у вічі",
    "прийти до висновку",
    "потерпіти поразку",
    "вибачаюся",
    "на рахунок цього",
    "за рахунок",
    "вірно",
    "влучний вираз",
    "вступати в силу",
    "приводити до",
    "здавати іспит",
    "складати іспит",
    "підвести підсумки",
    "попередити хворобу",
    "залишити в спокої",
]


@dataclass
class ParsedTurn:
    """Parsed model generation separating internal Chain-of-Thought from user response."""

    raw_text: str
    thought_text: str
    final_response: str
    has_thought: bool
    is_valid_format: bool
    format_error: str | None = None


def parse_model_output(raw_output: str) -> ParsedTurn:
    """Robustly parse model output into thought process and final response."""
    text = raw_output.strip()
    if not text:
        return ParsedTurn(
            raw_text="",
            thought_text="",
            final_response="",
            has_thought=False,
            is_valid_format=False,
            format_error="empty_output",
        )

    # Check for <thought> tags
    thought_match = re.search(r"<thought>(.*?)(?:</thought>|$)", text, flags=re.DOTALL | re.IGNORECASE)
    if thought_match:
        thought_content = thought_match.group(1).strip()
        has_closing = "</thought>" in text.lower()
        if not has_closing:
            # Model truncated before closing thought tag
            return ParsedTurn(
                raw_text=text,
                thought_text=thought_content,
                final_response="",
                has_thought=True,
                is_valid_format=False,
                format_error="unclosed_thought_tag",
            )

        final_content = text[thought_match.end() :].strip()
        return ParsedTurn(
            raw_text=text,
            thought_text=thought_content,
            final_response=final_content,
            has_thought=True,
            is_valid_format=bool(final_content),
            format_error=None if final_content else "missing_final_response_after_thought",
        )

    # Markdown thought block fallback: ```thought ... ```
    md_thought = re.search(r"```thought\s*(.*?)(?:```|$)", text, flags=re.DOTALL | re.IGNORECASE)
    if md_thought:
        thought_content = md_thought.group(1).strip()
        final_content = text[md_thought.end() :].strip()
        return ParsedTurn(
            raw_text=text,
            thought_text=thought_content,
            final_response=final_content,
            has_thought=True,
            is_valid_format=bool(final_content),
            format_error=None if final_content else "missing_final_response_after_md_thought",
        )

    # Direct final response (no thought block)
    return ParsedTurn(
        raw_text=text,
        thought_text="",
        final_response=text,
        has_thought=False,
        is_valid_format=True,
        format_error=None,
    )


def exact_clopper_pearson_upper(k: int, n: int, alpha: float = 0.05) -> float:
    """Exact one-sided 95% Clopper-Pearson upper confidence limit for binomial proportion."""
    if n <= 0:
        return 1.0
    if k >= n:
        return 1.0
    return float(beta.ppf(1.0 - alpha, k + 1, n - k))


def normalize_tokens(s: str) -> list[str]:
    """Normalize text into lower-case alphanumeric tokens, stripping accents."""
    s_clean = re.sub(r"[\u0300\u0301]", "", s)
    return [t.lower() for t in re.findall(r"[А-Яа-яЇїІіЄєҐґA-Za-z0-9]+", s_clean)]


def is_contiguous_subsequence(sub: list[str], seq: list[str]) -> bool:
    """Check if sub is an exact contiguous subsequence of seq."""
    if not sub:
        return True
    sub_len = len(sub)
    if sub_len > len(seq):
        return False
    return any(seq[i : i + sub_len] == sub for i in range(len(seq) - sub_len + 1))


def check_span_integrity(input_text: str, output_text: str, target_term: str) -> tuple[bool, str]:
    """Verify that text outside the target span is preserved without collateral mutations."""
    if not input_text or not output_text:
        return False, "empty_input_or_output"

    in_tokens = normalize_tokens(input_text)
    out_tokens = normalize_tokens(output_text)
    target_tokens = normalize_tokens(target_term)

    if not in_tokens or not target_tokens:
        return True, "valid_short"

    # Identify where target_tokens occur in in_tokens
    target_len = len(target_tokens)
    target_idx = -1
    for i in range(len(in_tokens) - target_len + 1):
        if in_tokens[i : i + target_len] == target_tokens:
            target_idx = i
            break

    if target_idx == -1:
        # Target not found in input (e.g. prompt format without exact sentence)
        return True, "target_not_in_input"

    # Non-target prefix and suffix must be preserved exactly
    prefix_in = in_tokens[:target_idx]
    suffix_in = in_tokens[target_idx + target_len :]

    # Required length check: output tokens must contain at least prefix and suffix non-overlapping
    min_required_len = len(prefix_in) + len(suffix_in)
    if len(out_tokens) < min_required_len:
        return False, f"span_truncation: output length {len(out_tokens)} shorter than non-target prefix+suffix {min_required_len}"

    # Check exact prefix match in out_tokens
    if prefix_in:
        out_prefix = out_tokens[: len(prefix_in)]
        if out_prefix != prefix_in:
            return False, f"prefix_mutation: expected {prefix_in!r}, got {out_prefix!r}"

    # Check exact suffix match in out_tokens
    if suffix_in:
        out_suffix = out_tokens[len(out_tokens) - len(suffix_in) :]
        if out_suffix != suffix_in:
            return False, f"suffix_mutation: expected {suffix_in!r}, got {out_suffix!r}"

    return True, "intact"


QUOTED_ENTITY_RE = r"(?:«[^»]+»|\"[^\"]+\"|“[^”]+”|‘[^’]+’|'[^']+')"
KEYWORD_AUTHORITY_RE = (
    r"(?:(?:чинн\w*|академічн\w*|офіційн\w*|нов\w*|стар\w*)\s+)?"
    r"(?:[Пп]равопис\w*|[Сс]ловник\w*|[Кк]орпус\w*|[Дд]овідник\w*|[Бб]аз\w*)"
    r"(?:\s+(?:української\s+мови(?:\s+(?:[ву]\s+\d+\s+томах|том(?:и|ів|ам|ами|ах|а|у|ом|і)?\s+\d+|\d+))?|«[^»]+»|\"[^\"]+\"|“[^”]+”|‘[^’]+’|'[^']+'|[A-ZА-ЯІЇЄҐa-zA-Z][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*|\d+))?"
)
LATIN_OR_ACRONYM_RE = (
    r"(?:[a-zA-Z][a-zA-Z0-9’'\-]*(?:\s+[a-zA-Z0-9’'\-]+)*|"
    r"[А-ЯІЇЄҐ]{2,}(?:[\s\-–—\u2010-\u2015]+[0-9А-ЯІЇЄҐ]+)?)"
)
INSTRUMENTAL_NAME_RE = (
    r"(?:[A-ZА-ЯІЇЄҐ][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*(?:ом|ем|ям|ою|ею|єю|овим|євим|им|ім)\b)"
)
GENITIVE_NAME_RE = (
    r"(?:[A-ZА-ЯІЇЄҐ][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*(?:кса|ака|яка|нка|нга|нта|рда|рта|нда|льда|вича|овича|евича|ьова|ьові|ова|ева|ого|ього|ів|ей|ові|єві|у|ю)\b)"
)
ANY_CAP_NAME_RE = (
    r"[A-ZА-ЯІЇЄҐa-zA-Z][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*(?:-[A-ZА-ЯІЇЄҐ0-9][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*)*"
    r"(?:\s+[A-ZА-ЯІЇЄҐ0-9][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*)*"
)

PARTICIPLE_CLAUSE_RE = (
    r"(?:описан\w*|зазначен\w*|вказан\w*|наведен\w*|подан\w*|згадан\w*|розглянут\w*|використан\w*|проілюстрован\w*)"
)

SUBJECT_PREDICATE_VERBS = r"(?:є|належить|вживається|пишеться|має|було|буде|вважається|становить|означає|визнано)"
SUBJECT_MODIFIERS_RE = r"(?:не|також|теж|цілком|зовсім|вже|ще)"
SUBJECT_VERB_CLAUSE = rf"(?:(?:\s+{SUBJECT_MODIFIERS_RE})*\s+{SUBJECT_PREDICATE_VERBS}\b)"
SUBJECT_CAP_NOUN_RE = r"[A-ZА-ЯІЇЄҐa-zA-Z][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*"
SUBJECT_ANY_NOUN_RE = rf"(?:{QUOTED_ENTITY_RE}|{SUBJECT_CAP_NOUN_RE})"
SUBJECT_NOUNS = (
    rf"(?:{QUOTED_ENTITY_RE}(?:\s*,\s*{QUOTED_ENTITY_RE})*(?:\s+(?:та|і|й|and|or)\s+{SUBJECT_ANY_NOUN_RE})+"
    rf"|{SUBJECT_ANY_NOUN_RE}(?:\s+(?:та|і|й|and|or)\s+{SUBJECT_ANY_NOUN_RE})*"
    rf"|{SUBJECT_ANY_NOUN_RE})"
)
SUBJECT_CLAUSE_LOOKAHEAD = (
    rf"{SUBJECT_NOUNS}"
    rf"(?:\s*,\s*[^,]+,)*"
    rf"{SUBJECT_VERB_CLAUSE}"
)

ENTITY_CITATION_RE = rf"(?:{QUOTED_ENTITY_RE}|{KEYWORD_AUTHORITY_RE}|{ANY_CAP_NAME_RE})"

# Primary authority entity directly following the preposition
PRIMARY_ENTITY_INSTRUMENTAL_RE = (
    rf"(?:{QUOTED_ENTITY_RE}|{KEYWORD_AUTHORITY_RE}|{LATIN_OR_ACRONYM_RE}|{INSTRUMENTAL_NAME_RE})"
)
PRIMARY_ENTITY_GENITIVE_RE = (
    rf"(?:{QUOTED_ENTITY_RE}|{KEYWORD_AUTHORITY_RE}|{LATIN_OR_ACRONYM_RE}|{GENITIVE_NAME_RE})"
)

# Coordinate authority entity following a comma or conjunction
ENTITY_CITATION_INSTRUMENTAL_RE = PRIMARY_ENTITY_INSTRUMENTAL_RE
ENTITY_CITATION_GENITIVE_RE = PRIMARY_ENTITY_GENITIVE_RE

CONJ_COORD_RE = rf"(?:\s+(?:та|і|й|and|or)\s+{ENTITY_CITATION_RE})"
DIRECT_CONJ_INSTRUMENTAL_RE = rf"(?:\s+(?:та|і|й|and|or)\s+{ENTITY_CITATION_INSTRUMENTAL_RE})"
DIRECT_CONJ_GENITIVE_RE = rf"(?:\s+(?:та|і|й|and|or)\s+{ENTITY_CITATION_GENITIVE_RE})"

PLURAL_COORD_RE = rf"(?:(?:\s*,\s*|\s+(?:та|і|й|and|or)\s+){ENTITY_CITATION_RE})"

COMMA_COORD_INSTRUMENTAL_RE = (
    rf"(?!\s*,\s*(?!\s){SUBJECT_CLAUSE_LOOKAHEAD})"
    rf"(?:\s*,\s*{ENTITY_CITATION_INSTRUMENTAL_RE}"
    rf"(?:(?:\s*,\s*(?!\s*(?!\s){SUBJECT_CLAUSE_LOOKAHEAD})|\s+(?:та|і|й|and|or)\s+){ENTITY_CITATION_INSTRUMENTAL_RE})*"
    rf"(?!\s*,\s*(?!\s*(?!\s){SUBJECT_CLAUSE_LOOKAHEAD}){ENTITY_CITATION_INSTRUMENTAL_RE})"
    rf"(?!\s+(?:та|і|й|and|or)\b)"
    rf"(?=\s*,\s*(?!\s)))"
)

COMMA_COORD_GENITIVE_RE = (
    rf"(?!\s*,\s*(?!\s){SUBJECT_CLAUSE_LOOKAHEAD})"
    rf"(?:\s*,\s*{ENTITY_CITATION_GENITIVE_RE}"
    rf"(?:(?:\s*,\s*(?!\s*(?!\s){SUBJECT_CLAUSE_LOOKAHEAD})|\s+(?:та|і|й|and|or)\s+){ENTITY_CITATION_GENITIVE_RE})*"
    rf"(?!\s*,\s*(?!\s*(?!\s){SUBJECT_CLAUSE_LOOKAHEAD}){ENTITY_CITATION_GENITIVE_RE})"
    rf"(?!\s+(?:та|і|й|and|or)\b)"
    rf"(?=\s*,\s*(?!\s)))"
)

DIRECT_ZA_ACRONYM_RE = r"(?:[A-ZА-ЯІЇЄҐ]{2,}(?:[\s\-–—\u2010-\u2015]+[0-9A-ZА-ЯІЇЄҐ]+)?)"
DIRECT_ZA_PROPER_NAME_RE = (
    r"(?:[A-ZА-ЯІЇЄҐ][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*"
    r"(?:ом|ем|ям|ою|ею|єю|овим|євим|им|ім|кса|ака|яка|нка|нга|нта|рда|рта|нда|льда|вича|овича|евича|ьова|ьові|ова|ева|ого|ього|ів|ей|ові|єві|а|я|у|ю)\b)"
)

CITATION_MENTION_PATTERNS = [
    # 1. "... dictionary" or "... словник" (case-insensitive name preceding dictionary keyword)
    re.compile(
        r"\b(?!(?:у|в|за|по|до|на|з|із|зі|згідно|відповідно|зокрема|цей|цього|цьому|кожен|кожний|який|якого|інший|іншого)\b)"
        r"([a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ’'\-]+(?:\s+[a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ’'\-]+)*\s+(?:dictionary|corpus|lexicon|словник\w*|корпус\w*|довідник\w*))\b",
        re.IGNORECASE,
    ),
    # 2a. Plural keyword with comma or conjunction coordinates: "словники ВЕСУМ, Zorblax"
    re.compile(
        rf"\b((?:[Сс]ловник(?:и|ами|ах)|[Кк]орпус(?:и|ами|ах)|[Дд]овідник(?:и|ами|ах)|[Бб]аз(?:и|ами|ах))\s+{ENTITY_CITATION_RE}(?:{PLURAL_COORD_RE})*)"
        r"(?!\w)"
    ),
    # 2b. Singular keyword with conjunction coordinates: "словник ВЕСУМ та Zorblax"
    re.compile(
        rf"\b((?:[Сс]ловник\w*|[Кк]орпус\w*|[Дд]овідник\w*|[Бб]аз\w*)\s+{ENTITY_CITATION_RE}(?:{CONJ_COORD_RE})*)"
        r"(?!\w)"
    ),
    # 3a. Instrumental introductory attribution phrases: "згідно з <Entities>"
    re.compile(
        rf"\b[Зз]гідно\s+(?:з|із|зі)\s+"
        rf"(?:(?:словник\w*|корпус\w*|довідник\w*|баз\w*)\s+)?({PRIMARY_ENTITY_INSTRUMENTAL_RE}(?:{DIRECT_CONJ_INSTRUMENTAL_RE}+|{COMMA_COORD_INSTRUMENTAL_RE})*)"
        r"(?!\w)"
    ),
    # 3b. Genitive introductory attribution phrases: "відповідно до <Entities>", "за даними <Entities>", etc.
    re.compile(
        rf"\b(?:[Вв]ідповідно\s+до|[Зз]а\s+даними|[Зз]а\s+версією)\s+"
        rf"(?:(?:словник\w*|корпус\w*|довідник\w*|баз\w*)\s+)?({PRIMARY_ENTITY_GENITIVE_RE}(?:{DIRECT_CONJ_GENITIVE_RE}+|{COMMA_COORD_GENITIVE_RE})*)"
        r"(?!\w)"
    ),
    # 3c. Direct introductory attribution phrases: "За <Entities>," (e.g. "За СУМ-11, це правильно.")
    re.compile(
        rf"\b[Зз]а\s+(?!(?:даними|версією|словами|правилами|твердженням|потреби|бажанням|наявності|замовчуванням|змоги|необхідності)\b)"
        rf"(?:(?:словник\w*|корпус\w*|довідник\w*|баз\w*)\s+)?"
        rf"({QUOTED_ENTITY_RE}|{KEYWORD_AUTHORITY_RE}|{DIRECT_ZA_ACRONYM_RE}|{DIRECT_ZA_PROPER_NAME_RE})\s*,"
    ),
    # 4. Parenthetical citations: "(СУМ-11)" or "(джерело: ВЕСУМ)"
    re.compile(
        rf"\((?:(?:[Дд]жерело|[Зз]а|[Дд]ив\.?):\s*)?({QUOTED_ENTITY_RE}|{KEYWORD_AUTHORITY_RE}|{LATIN_OR_ACRONYM_RE})\)"
    ),
]


def verify_citation_whitelist(text: str) -> tuple[bool, list[str], list[str]]:
    """Verify citations against whitelist; detect hallucinated foreign sources and reject unapproved authorities."""
    found_approved: list[str] = []
    found_prohibited: list[str] = []
    found_unapproved: list[str] = []

    norm_text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015]", "-", text)
    for pat in PROHIBITED_CITATION_PATTERNS:
        m = pat.findall(text)
        if m:
            found_prohibited.extend(m)
        m_norm = pat.findall(norm_text)
        if m_norm:
            found_prohibited.extend(m_norm)

    for pat in APPROVED_CITATION_PATTERNS:
        m = pat.findall(text)
        if m:
            found_approved.extend(m)

    # True whitelist: check for any cited authority entity mentions that are not approved
    for cpat in CITATION_MENTION_PATTERNS:
        for match in cpat.finditer(text):
            citation_span = match.group(1).strip() if match.lastindex else match.group(0).strip()
            # Split coordinate lists (e.g. "VESUM and zorblax dictionary", "ВЕСУМ та Zorblax", "ВЕСУМ, Zorblax")
            keyword_m = re.search(
                r"\s+(?:dictionary|corpus|lexicon|словник\w*|корпус\w*|довідник\w*)$",
                citation_span,
                re.IGNORECASE,
            )
            if keyword_m:
                names_part = citation_span[: keyword_m.start()].strip()
                kw = keyword_m.group(0).strip()
                names = re.split(r"\s*,\s*|\s+(?:and|or|та|і|й)\s+", names_part)
                for name in names:
                    name = name.strip()
                    full_name = f"{name} {kw}"
                    if is_approved_authority(full_name) or is_approved_authority(name):
                        found_approved.append(full_name)
                    else:
                        found_unapproved.append(full_name)
            else:
                # E.g. "словник Zorblax", "словниками ВЕСУМ та Zorblax", "словниками ВЕСУМ, Zorblax"
                clean_span = re.sub(
                    r"^(?:[Сс]ловник\w*|[Кк]орпус\w*|[Дд]овідник\w*|[Бб]аз\w*)\s+",
                    "",
                    citation_span,
                )
                sub_entities = re.split(r"\s*,\s*|\s+(?:та|і|й|and|or)\s+", clean_span)
                for ent in sub_entities:
                    ent = re.sub(
                        r"^(?:[Сс]ловник\w*|[Кк]орпус\w*|[Дд]овідник\w*|[Бб]аз\w*)\s+",
                        "",
                        ent.strip(),
                    )
                    clean_ent = ent.strip().strip("«»\"'“”‘’")
                    if clean_ent:
                        if is_approved_authority(clean_ent) or is_approved_authority(ent.strip()):
                            found_approved.append(clean_ent)
                        else:
                            found_unapproved.append(clean_ent)

    all_violations = sorted(list(set(found_prohibited + found_unapproved)))
    is_clean = len(all_violations) == 0
    return is_clean, sorted(list(set(found_approved))), all_violations


@dataclass
class CaseEvaluationResult:
    """Individual test case evaluation output."""

    eval_id: str
    case_type: str  # "CORRECT" or "PRESERVE"
    target_term: str
    is_valid_format: bool
    format_error: str | None
    calque_eliminated: bool
    harmful_edit: bool
    span_integrity_pass: bool
    span_integrity_note: str
    citation_clean: bool
    hallucinated_citations: list[str]
    approved_citations: list[str]
    is_high_frequency_calque: bool
    details: str = ""


# Standard Ukrainian academic benchmarks for Eval-UA-tion 1.0
STANDARD_ACADEMIC_BENCHMARKS = ("mmlu_ua", "arc_ua", "hellaswag_ua", "gsm8k_ua")


@dataclass
class BenchmarkTaskResult:
    """Individual academic benchmark task evaluation comparison."""

    benchmark: str
    base_score: float
    aligned_score: float
    relative_change_pct: float
    degradation_pct: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AcademicNonInferiorityReport:
    """Evaluation summary for Eval-UA-tion 1.0 academic non-inferiority suite."""

    tasks: list[BenchmarkTaskResult]
    overall_passed: bool
    max_allowed_degradation_pct: float
    worst_degradation_pct: float
    benchmark_count: int


PREFERRED_METRIC_KEYS = (
    "acc_norm,none",
    "acc_norm",
    "acc,none",
    "acc",
    "exact_match,none",
    "exact_match",
    "f1,none",
    "f1",
    "accuracy",
    "score",
)
SUPPORTED_SCORE_METRIC_NAMES = (
    "acc",
    "acc_norm",
    "accuracy",
    "exact_match",
    "em",
    "f1",
    "macro_f1",
    "micro_f1",
    "bleu",
    "rouge",
    "rouge1",
    "rouge2",
    "rougel",
    "rouge_l",
    "mc1",
    "mc2",
    "perplexity",
    "ppl",
    "loss",
    "score",
)
EXCLUDED_METRIC_SUBSTRINGS = (
    "stderr",
    "std_err",
    "_err",
    "error",
    "std",
    "runtime",
    "seconds",
    "samples_per_second",
    "sample",
    "count",
    "duration",
    "time",
    "step",
    "epoch",
    "size",
    "seed",
    "total",
    "num",
    "id",
)


def is_supported_score_metric(key: str) -> bool:
    """Check if key represents an explicit recognized score metric, rejecting metadata."""
    k = key.strip().lower()
    metric_id = k.split(",")[0].strip()
    if any(ex in metric_id for ex in EXCLUDED_METRIC_SUBSTRINGS):
        return False
    if metric_id in SUPPORTED_SCORE_METRIC_NAMES:
        return True
    return bool(re.match(r"^pass@\d+$", metric_id))


def extract_benchmark_score(entry: Any, preferred_key: str | None = None) -> tuple[float, str]:
    """Extract a numeric accuracy/score and metric name from an entry (float, int, or dict).

    Returns (score, metric_name).
    Rejects non-finite values (NaN, Inf), metadata keys, and ambiguous/error metrics.
    """
    if isinstance(entry, (int, float)):
        val = float(entry)
        if not math.isfinite(val):
            raise ValueError(f"Non-finite benchmark score encountered: {entry}")
        return val, "raw_score"

    if isinstance(entry, dict):
        if preferred_key and preferred_key in entry and is_supported_score_metric(preferred_key):
            val = entry[preferred_key]
            if isinstance(val, (int, float)):
                fval = float(val)
                if not math.isfinite(fval):
                    raise ValueError(f"Non-finite score for key '{preferred_key}': {val}")
                return fval, preferred_key

        # First, search preferred keys in priority order
        for key in PREFERRED_METRIC_KEYS:
            if key in entry and isinstance(entry[key], (int, float)):
                fval = float(entry[key])
                if not math.isfinite(fval):
                    raise ValueError(f"Non-finite score for key '{key}': {entry[key]}")
                return fval, key

        # Filter out known non-score / error / metadata metrics and require recognized score metric
        clean_candidates = {
            k: float(v)
            for k, v in entry.items()
            if isinstance(v, (int, float)) and is_supported_score_metric(k)
        }
        if len(clean_candidates) == 1:
            k, v = next(iter(clean_candidates.items()))
            if not math.isfinite(v):
                raise ValueError(f"Non-finite score for key '{k}': {v}")
            return v, k

        if not clean_candidates:
            raise ValueError(f"No valid metric score found in benchmark entry: {list(entry.keys())}")
        raise ValueError(f"Ambiguous metrics in benchmark entry: {list(clean_candidates.keys())}")

    raise ValueError(f"Invalid benchmark entry type: {type(entry).__name__}")


def extract_matching_benchmark_scores(
    base_entry: Any,
    aligned_entry: Any,
) -> tuple[float, float, str]:
    """Extract scores for base and aligned benchmarks using an exact matching metric.

    Raises ValueError if no matching metric is present in both entries,
    if either score is non-finite (NaN, Inf), or if entries are invalid.
    """
    if isinstance(base_entry, (int, float)) and isinstance(aligned_entry, (int, float)):
        bval = float(base_entry)
        aval = float(aligned_entry)
        if not (math.isfinite(bval) and math.isfinite(aval)):
            raise ValueError(f"Non-finite score encountered: base={bval}, aligned={aval}")
        return bval, aval, "raw_score"

    if isinstance(base_entry, dict) and isinstance(aligned_entry, dict):
        # 1. Search preferred keys in priority order present in BOTH entries
        for key in PREFERRED_METRIC_KEYS:
            if key in base_entry and key in aligned_entry:
                bval = base_entry[key]
                aval = aligned_entry[key]
                if isinstance(bval, (int, float)) and isinstance(aval, (int, float)):
                    fbval = float(bval)
                    faval = float(aval)
                    if not (math.isfinite(fbval) and math.isfinite(faval)):
                        raise ValueError(f"Non-finite score for matching key '{key}': base={bval}, aligned={aval}")
                    return fbval, faval, key

        # 2. Search clean common score metrics present in BOTH entries
        clean_common = [
            k
            for k in base_entry
            if k in aligned_entry
            and isinstance(base_entry[k], (int, float))
            and isinstance(aligned_entry[k], (int, float))
            and is_supported_score_metric(k)
        ]
        if len(clean_common) == 1:
            k = clean_common[0]
            fbval = float(base_entry[k])
            faval = float(aligned_entry[k])
            if not (math.isfinite(fbval) and math.isfinite(faval)):
                raise ValueError(f"Non-finite score for matching key '{k}': base={fbval}, aligned={faval}")
            return fbval, faval, k

        if not clean_common:
            raise ValueError(
                f"No matching score metric found between base {list(base_entry.keys())} and aligned {list(aligned_entry.keys())}"
            )
        raise ValueError(f"Ambiguous matching metrics between base and aligned results: {clean_common}")

    raise ValueError(
        f"Mismatched or invalid benchmark entry types: base={type(base_entry).__name__}, aligned={type(aligned_entry).__name__}"
    )


def evaluate_academic_non_inferiority(
    base_results: dict[str, Any],
    aligned_results: dict[str, Any],
    max_degradation_pct: float = 2.0,
    required_benchmarks: Sequence[str] = STANDARD_ACADEMIC_BENCHMARKS,
) -> AcademicNonInferiorityReport:
    """Evaluate Eval-UA-tion 1.0 academic non-inferiority across Ukrainian benchmarks.

    Compares aligned model scores against base foundation weights.
    Every required benchmark must be present in both result sets.
    Fails if performance degradation on any evaluated benchmark exceeds max_degradation_pct (default: 2.0%)
    or if any score is non-finite (NaN / Inf).
    """
    tasks: list[BenchmarkTaskResult] = []
    worst_degradation = 0.0

    base_benchmarks = (
        base_results.get("results", base_results) if isinstance(base_results, dict) else base_results
    )
    aligned_benchmarks = (
        aligned_results.get("results", aligned_results) if isinstance(aligned_results, dict) else aligned_results
    )

    if not isinstance(base_benchmarks, dict) or not isinstance(aligned_benchmarks, dict):
        return AcademicNonInferiorityReport(
            tasks=[],
            overall_passed=False,
            max_allowed_degradation_pct=max_degradation_pct,
            worst_degradation_pct=100.0,
            benchmark_count=0,
        )

    # Every required benchmark MUST be evaluated
    benchmarks_to_evaluate = list(required_benchmarks)
    # Include any additional common benchmarks present in both inputs
    for b in sorted(base_benchmarks.keys()):
        if b in aligned_benchmarks and b not in benchmarks_to_evaluate:
            benchmarks_to_evaluate.append(b)

    overall_passed = True

    for bname in benchmarks_to_evaluate:
        if bname not in base_benchmarks or bname not in aligned_benchmarks:
            tasks.append(
                BenchmarkTaskResult(
                    benchmark=bname,
                    base_score=0.0,
                    aligned_score=0.0,
                    relative_change_pct=-100.0,
                    degradation_pct=100.0,
                    passed=False,
                    details={"error": f"Required benchmark '{bname}' missing from one or both result sets"},
                )
            )
            overall_passed = False
            worst_degradation = max(worst_degradation, 100.0)
            continue

        try:
            base_score, aligned_score, metric_name = extract_matching_benchmark_scores(
                base_benchmarks[bname], aligned_benchmarks[bname]
            )
        except ValueError as exc:
            tasks.append(
                BenchmarkTaskResult(
                    benchmark=bname,
                    base_score=0.0,
                    aligned_score=0.0,
                    relative_change_pct=-100.0,
                    degradation_pct=100.0,
                    passed=False,
                    details={"error": str(exc)},
                )
            )
            overall_passed = False
            worst_degradation = max(worst_degradation, 100.0)
            continue

        if not (math.isfinite(base_score) and math.isfinite(aligned_score)):
            tasks.append(
                BenchmarkTaskResult(
                    benchmark=bname,
                    base_score=base_score,
                    aligned_score=aligned_score,
                    relative_change_pct=-100.0,
                    degradation_pct=100.0,
                    passed=False,
                    details={"error": "Non-finite score encountered"},
                )
            )
            overall_passed = False
            worst_degradation = max(worst_degradation, 100.0)
            continue

        metric_id = metric_name.split(",")[0].strip().lower()
        is_lower_better = metric_id in ("perplexity", "ppl", "loss")
        if is_lower_better:
            # For lower-is-better metrics (perplexity, ppl, loss), higher aligned score is degradation
            if base_score > 0:
                rel_change = ((aligned_score - base_score) / base_score) * 100.0
            else:
                rel_change = 0.0 if aligned_score <= base_score else 100.0
            degradation = max(0.0, rel_change)
        else:
            # For higher-is-better metrics (accuracy, f1, etc.), lower aligned score is degradation
            if base_score > 0:
                rel_change = ((aligned_score - base_score) / base_score) * 100.0
            else:
                rel_change = 0.0 if aligned_score >= base_score else -100.0
            degradation = max(0.0, -rel_change)

        passed = degradation <= (max_degradation_pct + 1e-7)

        if not passed:
            overall_passed = False
        worst_degradation = max(worst_degradation, degradation)

        tasks.append(
            BenchmarkTaskResult(
                benchmark=bname,
                base_score=base_score,
                aligned_score=aligned_score,
                relative_change_pct=rel_change,
                degradation_pct=degradation,
                passed=passed,
                details={"metric": metric_name},
            )
        )

    if not tasks:
        overall_passed = False

    return AcademicNonInferiorityReport(
        tasks=tasks,
        overall_passed=overall_passed,
        max_allowed_degradation_pct=max_degradation_pct,
        worst_degradation_pct=worst_degradation,
        benchmark_count=len(tasks),
    )


@dataclass
class EvaluationSummary:
    """Complete evaluation report with gate compliance statuses."""

    timestamp: str
    total_cases: int
    format_valid_count: int
    format_error_count: int

    # Gate 1: Calque Elimination
    correct_cases_total: int
    correct_eliminated_count: int
    calque_elimination_rate: float
    gate1_pass: bool

    # Gate 2: Harmful Edit Rate
    preserve_cases_total: int
    preserve_harmful_edits: int
    harmful_edit_rate: float
    clopper_pearson_upper: float
    gate2_pass: bool

    # Gate 3: Span Integrity
    span_integrity_checked: int
    span_integrity_violations: int
    span_integrity_rate: float
    gate3_pass: bool

    # Gate 4: Citation Whitelist
    citation_violations_count: int
    citation_hallucination_rate: float
    gate4_pass: bool

    # Gate 5: High-Frequency Calque Floor
    high_freq_total: int
    high_freq_eliminated: int
    high_freq_recall: float
    high_freq_floor: int
    high_freq_distinct_covered: int
    gate5_pass: bool

    # Overall Verdict
    all_gates_pass: bool
    results: list[dict[str, Any]] = field(default_factory=list)
    academic_non_inferiority: AcademicNonInferiorityReport | None = None


def evaluate_prediction(
    eval_case: dict[str, Any],
    raw_model_response: str,
) -> CaseEvaluationResult:
    """Evaluate a single model generation against ground truth case specifications."""
    eval_id = eval_case.get("eval_id", "unknown")
    case_type = eval_case.get("case_type", "CORRECT").upper()
    target_term = eval_case.get("target_term", "").strip()
    input_text = eval_case.get("input_text", "")

    parsed = parse_model_output(raw_model_response)

    # Citations check
    cit_clean, approved_cits, prohibited_cits = verify_citation_whitelist(raw_model_response)

    # High-frequency calque check
    is_high_freq = any(hf.lower() in target_term.lower() or target_term.lower() in hf.lower() for hf in HIGH_FREQUENCY_CALQUES)

    if not parsed.is_valid_format:
        return CaseEvaluationResult(
            eval_id=eval_id,
            case_type=case_type,
            target_term=target_term,
            is_valid_format=False,
            format_error=parsed.format_error,
            calque_eliminated=False,
            harmful_edit=(case_type == "PRESERVE"),
            span_integrity_pass=False,
            span_integrity_note="format_error",
            citation_clean=cit_clean,
            hallucinated_citations=prohibited_cits,
            approved_citations=approved_cits,
            is_high_frequency_calque=is_high_freq,
            details=f"Format error: {parsed.format_error}",
        )

    # Evaluate based on case type
    target_norm = normalize_tokens(target_term)
    resp_tokens = normalize_tokens(parsed.final_response)

    # Check if target is in final response
    target_in_final = False
    if target_norm:
        t_len = len(target_norm)
        for i in range(len(resp_tokens) - t_len + 1):
            if resp_tokens[i : i + t_len] == target_norm:
                target_in_final = True
                break

    expected_replacement = eval_case.get("expected_replacement")
    exp_clean = expected_replacement.strip().strip("–—\"'«» .,") if expected_replacement else ""
    exp_tokens = normalize_tokens(exp_clean) if exp_clean else []

    if case_type == "CORRECT":
        # Calque must NOT be recommended or preserved in the final output,
        # AND the valid correction/expected replacement must be present as a contiguous sequence.
        # This prevents scoring arbitrary substitutions (e.g. 'XYZ') as successful.
        resp_lower = parsed.final_response.lower()
        t_lower = target_term.lower()

        has_valid_replacement = False
        if exp_clean:
            if exp_tokens and is_contiguous_subsequence(exp_tokens, resp_tokens):
                has_valid_replacement = True
        else:
            has_valid_replacement = bool(resp_tokens)

        if not target_in_final:
            calque_eliminated = has_valid_replacement
        else:
            # Calque is present in final response: check whether it is critiqued/contrasted or endorsed
            is_affirmed = any(
                p in resp_lower
                for p in (
                    f"правильно: {t_lower}",
                    f"правильно «{t_lower}»",
                    f"вживайте «{t_lower}»",
                    f"вживайте {t_lower}",
                    f"«{t_lower}» є нормативн",
                    f"{t_lower} є нормативн",
                )
            )
            is_critiqued = any(
                m in resp_lower
                for m in (
                    f"замість «{t_lower}»",
                    f"замість \"{t_lower}\"",
                    f"замість {t_lower}",
                    f"не «{t_lower}»",
                    f"не {t_lower}",
                    f"уникайте «{t_lower}»",
                    f"уникайте {t_lower}",
                    f"«{t_lower}» є калькою",
                    f"«{t_lower}» — калька",
                    f"форма «{t_lower}» є штучною",
                    f"форма «{t_lower}» не є",
                    "калька",
                    "калькою",
                    "росіянізм",
                    "помилка",
                )
            )
            if is_affirmed:
                calque_eliminated = False
            elif is_critiqued:
                calque_eliminated = has_valid_replacement
            else:
                calque_eliminated = False

        # Check span integrity if input was a sentence
        span_pass, span_note = check_span_integrity(input_text, parsed.final_response, target_term)

        return CaseEvaluationResult(
            eval_id=eval_id,
            case_type="CORRECT",
            target_term=target_term,
            is_valid_format=True,
            format_error=None,
            calque_eliminated=calque_eliminated,
            harmful_edit=not span_pass,  # collateral mutation outside target counts as harmful
            span_integrity_pass=span_pass,
            span_integrity_note=span_note,
            citation_clean=cit_clean,
            hallucinated_citations=prohibited_cits,
            approved_citations=approved_cits,
            is_high_frequency_calque=is_high_freq,
            details="Calque eliminated" if calque_eliminated else "Calque still present or uncorrected in final response",
        )

    else:  # PRESERVE
        # Standard word must be kept; model must not replace or condemn it
        # If the target is missing from final response or mutated, harmful edit occurred
        harmful_edit = not target_in_final

        # Also check whether model condemned the authentic word as a calque or error.
        # Condemnation and negation are evaluated per clause to prevent unrelated normative
        # statements from globally masking explicit target condemnation.
        if not harmful_edit:
            thought_and_resp = (parsed.thought_text + " " + parsed.final_response).lower()
            t_lower = target_term.lower()
            t_quoted = rf"[«\"“‘\']{re.escape(t_lower)}[»\"”’\']"
            t_bare = rf"\b{re.escape(t_lower)}\b"
            t_anaphor = r"(?:(?:це|дане|зазначене)\s+(?:слово|термін)\b)"
            t_token = rf"(?:{t_quoted}|{t_bare}|{t_anaphor})"
            left_b = r"(?:\b|(?<=[\s«\"“‘\'(^]))(?<!інше\s)(?<!іншого\s)(?<!іншим\s)(?<!нового\s)(?<!інший\s)"

            clauses = [c.strip() for c in re.split(r"[.,\n;!?]+", thought_and_resp) if c.strip()]
            for clause in clauses:
                mentions_target = (
                    f"«{t_lower}»" in clause
                    or f"\"{t_lower}\"" in clause
                    or f"слово {t_lower}" in clause
                    or f"термін {t_lower}" in clause
                    or f"форма {t_lower}" in clause
                    or f"«{t_lower}" in clause
                    or (t_lower in clause and any(kw in clause for kw in ("кальк", "росіянізм", "помилк", "суржик", "замін", "уникай", "виправ", "ненормативн")))
                )
                if not mentions_target:
                    continue

                adj_filler = r"(?:(?:очевидн\w*|груб\w*|явн\w*|типов\w*|неприпустим\w*|стилістичн\w*|лексичн\w*)\s+)?"

                # 1. Calque condemnation vs negation
                copula_calque = bool(
                    re.search(
                        rf"{left_b}{t_token}\s+(?:(?:—|–|-|:)\s+(?:(?:це|є)\s+)?|(?:є|було|вважається|становить)\s+){adj_filler}кальк\w*",
                        clause,
                    )
                ) or any(
                    cp in clause
                    for cp in (
                        f"«{t_lower}» є калькою",
                        f"«{t_lower}» — калька",
                        f"«{t_lower}» – калька",
                        f"«{t_lower}»: калька",
                        f"слово {t_lower} є калькою",
                        f"слово {t_lower} — калька",
                        f"слово {t_lower} – калька",
                        f"слово {t_lower}: калька",
                    )
                )
                negates_calque = bool(
                    re.search(
                        rf"{left_b}{t_token}\s+(?:(?:—|–|-|:)\s+(?:це\s+)?не\s+(?:є\s+)?|не\s+(?:є|було|вважається|становить)?\s*){adj_filler}кальк\w*",
                        clause,
                    )
                ) or bool(
                    re.search(rf"{left_b}{t_token}\s+не\s+(?:є\s+)?кальк\w*", clause)
                )

                # 2. Russianism condemnation vs negation
                copula_russianism = bool(
                    re.search(
                        rf"{left_b}{t_token}\s+(?:(?:—|–|-|:)\s+(?:(?:це|є)\s+)?|(?:є|було|вважається|становить)\s+){adj_filler}росіянізм\w*",
                        clause,
                    )
                ) or any(
                    cp in clause
                    for cp in (
                        f"«{t_lower}» є росіянізмом",
                        f"«{t_lower}» — росіянізм",
                        f"«{t_lower}» – росіянізм",
                        f"«{t_lower}»: росіянізм",
                        f"слово {t_lower} є росіянізмом",
                        f"слово {t_lower} — росіянізм",
                    )
                )
                negates_russianism = bool(
                    re.search(
                        rf"{left_b}{t_token}\s+(?:(?:—|–|-|:)\s+(?:це\s+)?не\s+(?:є\s+)?|не\s+(?:є|було|вважається|становить)?\s*){adj_filler}росіянізм\w*",
                        clause,
                    )
                ) or bool(
                    re.search(rf"{left_b}{t_token}\s+не\s+(?:є\s+)?росіянізм\w*", clause)
                )

                # 3. Error / surzhyk / artificial / unnormative condemnation vs negation
                copula_other = bool(
                    re.search(
                        rf"{left_b}{t_token}\s+(?:(?:—|–|-|:)\s+(?:(?:це|є)\s+)?|(?:є|було|вважається|становить)\s+){adj_filler}(?:помилк\w*|суржик\w*|ненормативн\w*|штучн\w*)",
                        clause,
                    )
                ) or (f"помилкове вживання «{t_lower}»" in clause)
                negates_other = bool(
                    re.search(
                        rf"{left_b}{t_token}\s+(?:(?:—|–|-|:)\s+(?:це\s+)?не\s+(?:є\s+)?|не\s+(?:є|було|вважається|становить)?\s*){adj_filler}(?:помилк\w*|суржик\w*|ненормативн\w*|штучн\w*)",
                        clause,
                    )
                ) or bool(
                    re.search(
                        rf"{left_b}{t_token}\s+не\s+(?:є\s+)?(?:помилк\w*|суржик\w*|ненормативн\w*|штучн\w*)",
                        clause,
                    )
                )

                # 4. Replacement instruction vs replacement negation targeting t_token
                directive_replace = bool(
                    re.search(
                        rf"(?<!не\s)(?<!не\sслід\s)(?<!не\sварто\s)(?<!не\sтреба\s)(?<!не\sпотрібно\s)(?<!не\sнеобхідно\s)"
                        rf"(?:замініть|замінити|уникайте|уникати|виправте|виправити|"
                        rf"(?:слід|варто|потрібно|необхідно|треба)\s+(?:замінити|замінювати|уникати|виправити|виправляти)|"
                        rf"(?:потребує|вимагає)\s+(?:заміни|виправлення))\s+(?:слово\s+|вживання\s+)?{t_token}",
                        clause,
                    )
                ) or bool(
                    re.search(
                        rf"{t_token}\s+(?<!не\s)(?<!не\sслід\s)(?<!не\sварто\s)(?<!не\sтреба\s)(?<!не\sпотрібно\s)"
                        rf"(?:потребує\s+(?:заміни|виправлення)|вимагає\s+заміни|(?:слід|варто|потрібно|необхідно|треба)\s+(?:замінити|замінювати|уникати|виправити|виправляти))",
                        clause,
                    )
                )
                negates_replace = bool(
                    re.search(
                        rf"не\s+(?:слід|варто|потрібно|необхідно|треба)?\s*(?:замінювати|замінити|уникати|виправляти|виправити)\s+(?:слово\s+|вживання\s+)?{t_token}",
                        clause,
                    )
                ) or bool(
                    re.search(
                        rf"(?:не\s+потребує|не\s+вимагає)\s+(?:заміни|виправлення)\s+(?:слово\s+|вживання\s+)?{t_token}",
                        clause,
                    )
                ) or bool(
                    re.search(
                        rf"{t_token}\s+(?:не\s+потребує\s+(?:заміни|виправлення)|не\s+вимагає\s+заміни|не\s+(?:слід|варто|потрібно|необхідно|треба)?\s*(?:замінювати|замінити|уникати|виправляти|виправити))",
                        clause,
                    )
                )

                has_unnegated_condemnation = (
                    (copula_calque and not negates_calque)
                    or (copula_russianism and not negates_russianism)
                    or (copula_other and not negates_other)
                    or (directive_replace and not negates_replace)
                )

                if has_unnegated_condemnation:
                    harmful_edit = True
                    break

        span_pass, span_note = check_span_integrity(input_text, parsed.final_response, target_term)

        return CaseEvaluationResult(
            eval_id=eval_id,
            case_type="PRESERVE",
            target_term=target_term,
            is_valid_format=True,
            format_error=None,
            calque_eliminated=False,
            harmful_edit=harmful_edit,
            span_integrity_pass=span_pass,
            span_integrity_note=span_note,
            citation_clean=cit_clean,
            hallucinated_citations=prohibited_cits,
            approved_citations=approved_cits,
            is_high_frequency_calque=is_high_freq,
            details="Authentic word preserved" if not harmful_edit else "Harmful over-correction detected",
        )


def run_evaluation_suite(
    eval_cases: list[dict[str, Any]],
    predictions: dict[str, str],
    min_high_freq_floor: int = 50,
    academic_report: AcademicNonInferiorityReport | None = None,
) -> EvaluationSummary:
    """Run full evaluation suite across all provided cases and predictions."""
    results: list[CaseEvaluationResult] = []

    for case in eval_cases:
        eid = case.get("eval_id")
        raw_resp = predictions.get(eid, "")
        res = evaluate_prediction(case, raw_resp)
        results.append(res)

    total_cases = len(results)
    format_valid = sum(1 for r in results if r.is_valid_format)
    format_errors = total_cases - format_valid

    # Gate 1 metrics
    correct_cases = [r for r in results if r.case_type == "CORRECT"]
    correct_total = len(correct_cases)
    correct_eliminated = sum(1 for r in correct_cases if r.calque_eliminated)
    calque_elim_rate = (correct_eliminated / correct_total) if correct_total > 0 else 0.0
    gate1_pass = calque_elim_rate >= 0.90

    # Gate 2 metrics
    preserve_cases = [r for r in results if r.case_type == "PRESERVE"]
    preserve_total = len(preserve_cases)
    preserve_harmful = sum(1 for r in preserve_cases if r.harmful_edit)
    harmful_rate = (preserve_harmful / preserve_total) if preserve_total > 0 else 0.0
    cp_upper = exact_clopper_pearson_upper(preserve_harmful, preserve_total)
    gate2_pass = cp_upper <= 0.01 and preserve_total >= 300

    # Gate 3 metrics (Span integrity)
    span_checked = sum(1 for r in results if r.span_integrity_note != "target_not_in_input")
    span_violations = sum(1 for r in results if not r.span_integrity_pass)
    span_rate = (span_checked - span_violations) / span_checked if span_checked > 0 else 1.0
    gate3_pass = span_violations == 0

    # Gate 4 metrics (Citation whitelist)
    citation_violations = sum(1 for r in results if not r.citation_clean)
    citation_hallucination_rate = citation_violations / total_cases if total_cases > 0 else 0.0
    gate4_pass = citation_violations == 0

    # Gate 5 metrics (High-Frequency Calque Floor: distinct required calques covered)
    hf_cases = [r for r in correct_cases if r.is_high_frequency_calque]
    hf_total = len(hf_cases)
    hf_eliminated = sum(1 for r in hf_cases if r.calque_eliminated)
    hf_recall = (hf_eliminated / hf_total) if hf_total > 0 else 0.0

    # Count distinct canonical HIGH_FREQUENCY_CALQUES that were evaluated and eliminated
    covered_distinct_calques = {
        hf
        for hf in HIGH_FREQUENCY_CALQUES
        if any(
            normalize_tokens(r.target_term) == normalize_tokens(hf)
            and r.calque_eliminated
            for r in hf_cases
        )
    }
    hf_distinct_count = len(covered_distinct_calques)
    gate5_pass = (hf_distinct_count >= min_high_freq_floor) and (hf_recall >= 1.0)

    all_gates = gate1_pass and gate2_pass and gate3_pass and gate4_pass and gate5_pass
    if academic_report is not None:
        all_gates = all_gates and academic_report.overall_passed

    return EvaluationSummary(
        timestamp=datetime.now(UTC).isoformat(),
        total_cases=total_cases,
        format_valid_count=format_valid,
        format_error_count=format_errors,
        correct_cases_total=correct_total,
        correct_eliminated_count=correct_eliminated,
        calque_elimination_rate=calque_elim_rate,
        gate1_pass=gate1_pass,
        preserve_cases_total=preserve_total,
        preserve_harmful_edits=preserve_harmful,
        harmful_edit_rate=harmful_rate,
        clopper_pearson_upper=cp_upper,
        gate2_pass=gate2_pass,
        span_integrity_checked=span_checked,
        span_integrity_violations=span_violations,
        span_integrity_rate=span_rate,
        gate3_pass=gate3_pass,
        citation_violations_count=citation_violations,
        citation_hallucination_rate=citation_hallucination_rate,
        gate4_pass=gate4_pass,
        high_freq_total=hf_total,
        high_freq_eliminated=hf_eliminated,
        high_freq_recall=hf_recall,
        high_freq_floor=min_high_freq_floor,
        high_freq_distinct_covered=hf_distinct_count,
        gate5_pass=gate5_pass,
        all_gates_pass=all_gates,
        results=[asdict(r) for r in results],
        academic_non_inferiority=academic_report,
    )


def format_markdown_report(summary: EvaluationSummary) -> str:
    """Generate human-readable Markdown evaluation report for PRs and model cards."""
    status_icon = "✅ PASS" if summary.all_gates_pass else "❌ FAIL"
    g1_icon = "✅ PASS" if summary.gate1_pass else "❌ FAIL"
    g2_icon = "✅ PASS" if summary.gate2_pass else "❌ FAIL"
    g3_icon = "✅ PASS" if summary.gate3_pass else "❌ FAIL"
    g4_icon = "✅ PASS" if summary.gate4_pass else "❌ FAIL"
    g5_icon = "✅ PASS" if summary.gate5_pass else "❌ FAIL"

    report_lines = [
        "# ULDR Phase 5.1 Evaluation Audit Report",
        ">",
        f"> **Evaluation Timestamp:** `{summary.timestamp}`",
        f"> **Overall Gate Verdict:** **{status_icon}**",
        f"> **Total Evaluated Cases:** `{summary.total_cases}` (`{summary.format_valid_count}` format-valid, `{summary.format_error_count}` format-errors)",
        "",
        "---",
        "",
        "## 1. Quality Gate Scorecard",
        "",
        "| Production Gate | Target Threshold | Measured Score | Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Gate 1: Calque Elimination Rate** | >= 90.0% | **{summary.calque_elimination_rate * 100:.2f}%** ({summary.correct_eliminated_count}/{summary.correct_cases_total}) | {g1_icon} |",
        f"| **Gate 2: Harmful-Edit Rate** | <= 1.0% (Clopper-Pearson 95%) | **{summary.harmful_edit_rate * 100:.2f}%** (Upper bound: **{summary.clopper_pearson_upper * 100:.2f}%**, N={summary.preserve_cases_total}) | {g2_icon} |",
        f"| **Gate 3: Span Integrity Gate** | 100% (0 mutations outside span) | **{summary.span_integrity_rate * 100:.2f}%** ({summary.span_integrity_violations} violations) | {g3_icon} |",
        f"| **Gate 4: Citation Whitelist Gate** | 0% foreign hallucinations | **{summary.citation_violations_count}** violations (rate: {summary.citation_hallucination_rate * 100:.2f}%) | {g4_icon} |",
        f"| **Gate 5: High-Frequency Calque Floor** | 100% on top 50 calques ({summary.high_freq_floor} distinct required) | **{summary.high_freq_recall * 100:.2f}%** ({summary.high_freq_distinct_covered}/{summary.high_freq_floor} distinct covered, {summary.high_freq_eliminated}/{summary.high_freq_total} total) | {g5_icon} |",
    ]

    if summary.academic_non_inferiority:
        acad = summary.academic_non_inferiority
        acad_status_icon = "✅ PASS" if acad.overall_passed else "❌ FAIL"
        report_lines.extend([
            "",
            "---",
            "",
            "## 2. Academic Non-Inferiority Suite (Eval-UA-tion 1.0)",
            f"> **Academic Suite Verdict:** **{acad_status_icon}** (Worst degradation: **{acad.worst_degradation_pct:.2f}%**, Max allowed: **{acad.max_allowed_degradation_pct:.2f}%**)",
            "",
            "| Academic Benchmark | Base Score | Aligned Score | Relative Change | Max Degradation | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for task in acad.tasks:
            t_icon = "✅ PASS" if task.passed else "❌ FAIL"
            change_str = f"{task.relative_change_pct:+.2f}%"
            report_lines.append(
                f"| **{task.benchmark.upper()}** | {task.base_score:.4f} | {task.aligned_score:.4f} | {change_str} | <= {acad.max_allowed_degradation_pct:.2f}% | {t_icon} |"
            )

    report_lines.extend([
        "",
        "---",
        "",
        "## 3. Gate Definitions & Statistical Criteria" if summary.academic_non_inferiority else "## 2. Gate Definitions & Statistical Criteria",
        "* **Gate 1 (Calque Elimination):** Measures eradication of Russianisms and calques in final recommendations on held-out cases.",
        "* **Gate 2 (Harmful Edits):** Exact one-sided 95% Clopper-Pearson binomial upper bound U = Beta^-1(0.95; k+1, n-k) <= 0.01 on >= 300 clean controls.",
        "* **Gate 3 (Span Integrity):** Prevents collocation hallucinations (*побитися об заклад* -> *побитися об друга*). Tokens outside designated error spans must not be mutated.",
        "* **Gate 4 (Citation Whitelist):** Rejects hallucinated foreign dictionaries (*COBUILD*, *LexicalLab*). Only approved authorities (ВЕСУМ, СУМ-20, Правопис 2019, Антоненко-Давидович, Грінченко, УЛІФ, UA-GEC) permitted.",
        "* **Gate 5 (High-Frequency Calque Floor):** Requires 100% recall on the 50 most common Ukrainian calques (*приймати участь*, *на протязі*, *приймати міри*).",
    ])
    if summary.academic_non_inferiority:
        report_lines.append(
            "* **Academic Non-Inferiority (Eval-UA-tion 1.0):** Ukrainian benchmark integration (MMLU-UA, ARC-UA, HellaSwag-UA, GSM8k-UA) guaranteeing <= 2.0% degradation against base foundation weights."
        )

    return "\n".join(report_lines) + "\n"


def main() -> int:
    """CLI entrypoint for evaluation harness."""
    parser = argparse.ArgumentParser(description="ULDR Phase 5.1 Evaluation Suite")
    parser.add_argument("--heldout", type=Path, default=DEFAULT_HELDOUT_PATH, help="Path to held-out evaluation JSONL")
    parser.add_argument("--predictions", type=Path, default=None, help="Path to model predictions JSONL")
    parser.add_argument("--output-json", type=Path, default=Path("evaluation_report.json"), help="Output JSON path")
    parser.add_argument("--output-md", type=Path, default=Path("evaluation_report.md"), help="Output Markdown path")
    parser.add_argument("--min-high-freq-floor", type=int, default=50, help="Minimum high-frequency calques required")
    parser.add_argument("--base-benchmarks", type=Path, default=None, help="Path to base model academic benchmark JSON")
    parser.add_argument("--aligned-benchmarks", type=Path, default=None, help="Path to aligned model academic benchmark JSON")
    parser.add_argument("--max-degradation-pct", type=float, default=2.0, help="Maximum allowed degradation percentage (default: 2.0%%)")
    parser.add_argument("--self-test", action="store_true", help="Run self-test contract verification")
    args = parser.parse_args()

    if args.self_test:
        print("Running Phase 5.1 evaluation harness self-test...")
        test_cases = [
            {
                "eval_id": "test_correct_01",
                "case_type": "CORRECT",
                "target_term": "бажаючий",
                "input_text": "Коротка порада: бажаючий чи охочий?",
                "expected_replacement": "охочий",
            },
            {
                "eval_id": "test_preserve_01",
                "case_type": "PRESERVE",
                "target_term": "матеріал",
                "input_text": "Чи коректно вживати термін «матеріал» у науковій праці?",
                "expected_replacement": None,
            },
        ]
        test_preds = {
            "test_correct_01": "<thought>1. Діагностика: слово бажаючий є калькою.\n2. ВЕСУМ: охочий.</thought>Правильно вживати «охочий» замість «бажаючий».",
            "test_preserve_01": "<thought>1. Діагностика: матеріал є нормативним словом.</thought>Термін «матеріал» є нормативним, залишаємо без змін.",
        }

        # Verify academic non-inferiority evaluation self-test
        sample_base = {"mmlu_ua": 0.6500, "arc_ua": 0.5800, "hellaswag_ua": 0.6200, "gsm8k_ua": 0.4500}
        sample_aligned_pass = {"mmlu_ua": 0.6480, "arc_ua": 0.5850, "hellaswag_ua": 0.6150, "gsm8k_ua": 0.4480}
        sample_aligned_fail = {"mmlu_ua": 0.6000, "arc_ua": 0.5800, "hellaswag_ua": 0.6200, "gsm8k_ua": 0.4500}
        acad_pass = evaluate_academic_non_inferiority(sample_base, sample_aligned_pass, max_degradation_pct=2.0)
        acad_fail = evaluate_academic_non_inferiority(sample_base, sample_aligned_fail, max_degradation_pct=2.0)
        assert acad_pass.overall_passed is True, "Self-test failed: academic non-inferiority should pass"
        assert acad_fail.overall_passed is False, "Self-test failed: academic non-inferiority should fail"

        summary = run_evaluation_suite(test_cases, test_preds, min_high_freq_floor=1, academic_report=acad_pass)
        print(f"Self-test complete: Gate 1 Pass: {summary.gate1_pass}, Format valid: {summary.format_valid_count}, Academic Non-Inferiority Pass: {summary.academic_non_inferiority.overall_passed if summary.academic_non_inferiority else 'N/A'}")
        return 0

    if not args.predictions:
        print("Error: --predictions <path.jsonl> or --self-test required.", file=sys.stderr)
        return 1

    if not args.heldout.exists():
        print(f"Error: Held-out file {args.heldout} does not exist.", file=sys.stderr)
        return 1

    academic_report = None
    if args.base_benchmarks or args.aligned_benchmarks:
        if not (args.base_benchmarks and args.aligned_benchmarks):
            print("Error: Both --base-benchmarks and --aligned-benchmarks are required when evaluating academic non-inferiority.", file=sys.stderr)
            return 1
        base_data = json.loads(args.base_benchmarks.read_text(encoding="utf-8"))
        aligned_data = json.loads(args.aligned_benchmarks.read_text(encoding="utf-8"))
        academic_report = evaluate_academic_non_inferiority(
            base_data, aligned_data, max_degradation_pct=args.max_degradation_pct
        )

    eval_cases = [json.loads(line) for line in args.heldout.read_text(encoding="utf-8").splitlines() if line.strip()]

    # Load predictions
    preds_raw = [json.loads(line) for line in args.predictions.read_text(encoding="utf-8").splitlines() if line.strip()]
    predictions = {p.get("eval_id") or p.get("id"): p.get("prediction") or p.get("output") or p.get("response") for p in preds_raw}

    summary = run_evaluation_suite(
        eval_cases,
        predictions,
        min_high_freq_floor=args.min_high_freq_floor,
        academic_report=academic_report,
    )

    args.output_json.write_text(json.dumps(asdict(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    md_content = format_markdown_report(summary)
    args.output_md.write_text(md_content, encoding="utf-8")

    print(md_content)
    return 0 if summary.all_gates_pass else 2


if __name__ == "__main__":
    sys.exit(main())
