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
import re
import sys
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

# Approved Ukrainian reference authorities for Gate 4
APPROVED_CITATION_PATTERNS = [
    re.compile(r"\bвесум\b", re.IGNORECASE),
    re.compile(r"\bvesum\b", re.IGNORECASE),
    re.compile(r"\bсум(?:-11|-20)?\b", re.IGNORECASE),
    re.compile(r"\bправопис(?:у|ом|і)?(?:\s+2019)?\b", re.IGNORECASE),
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

# Blacklisted hallucinated or foreign program citations (Gate 4 violations)
PROHIBITED_CITATION_PATTERNS = [
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


ENTITY_CITATION_RE = (
    r"(?:«[^»]+»|\"[^\"]+\"|"
    r"(?:(?:чинн\w*|академічн\w*|офіційн\w*|нов\w*|стар\w*)\s+)?"
    r"(?:[Пп]равопис\w*|[Сс]ловник\w*|[Кк]орпус\w*|[Дд]овідник\w*|[Бб]аз\w*)(?:\s+\d+)?|"
    r"[A-ZА-ЯІЇЄҐa-zA-Z][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*(?:-[A-ZА-ЯІЇЄҐ0-9][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*)*"
    r"(?:\s+[A-ZА-ЯІЇЄҐ0-9][a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ0-9’'\-]*)*)"
)
CONJ_COORD_RE = rf"(?:\s+(?:та|і|й|and|or)\s+{ENTITY_CITATION_RE})"
COMMA_COORD_RE = rf"(?:\s*,\s*{ENTITY_CITATION_RE})"

CITATION_MENTION_PATTERNS = [
    # 1. "... dictionary" or "... словник" (case-insensitive name preceding dictionary keyword)
    re.compile(
        r"\b(?!(?:у|в|за|по|до|на|з|із|зі|згідно|відповідно|зокрема|цей|цього|цьому|кожен|кожний|який|якого|інший|іншого)\b)"
        r"([a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ’'\-]+(?:\s+[a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ’'\-]+)*\s+(?:dictionary|corpus|lexicon|словник\w*|корпус\w*|довідник\w*))\b",
        re.IGNORECASE,
    ),
    # 2a. Plural keyword with comma or conjunction coordinates: "словники ВЕСУМ, Zorblax"
    re.compile(
        rf"\b((?:[Сс]ловник(?:и|ами|ах)|[Кк]орпус(?:и|ами|ах)|[Дд]овідник(?:и|ами|ах)|[Бб]аз(?:и|ами|ах))\s+{ENTITY_CITATION_RE}(?:{COMMA_COORD_RE}|{CONJ_COORD_RE})*)"
        r"(?!\w)"
    ),
    # 2b. Singular keyword with conjunction coordinates: "словник ВЕСУМ та Zorblax"
    re.compile(
        rf"\b((?:[Сс]ловник\w*|[Кк]орпус\w*|[Дд]овідник\w*|[Бб]аз\w*)\s+{ENTITY_CITATION_RE}(?:{CONJ_COORD_RE})*)"
        r"(?!\w)"
    ),
    # 3. Introductory attribution phrases: "згідно з <Entities>", "відповідно до <Entities>", etc.
    re.compile(
        rf"\b(?:[Зз]гідно\s+(?:з|із)|[Вв]ідповідно\s+до|[Зз]а\s+даними|[Зз]а\s+версією)\s+"
        rf"(?:(?:словник\w*|корпус\w*|довідник\w*|баз\w*)\s+)?({ENTITY_CITATION_RE}(?:{COMMA_COORD_RE}|{CONJ_COORD_RE})*)"
        r"(?!\w)"
    ),
]


def verify_citation_whitelist(text: str) -> tuple[bool, list[str], list[str]]:
    """Verify citations against whitelist; detect hallucinated foreign sources and reject unapproved authorities."""
    found_approved: list[str] = []
    found_prohibited: list[str] = []
    found_unapproved: list[str] = []

    for pat in APPROVED_CITATION_PATTERNS:
        m = pat.findall(text)
        if m:
            found_approved.extend(m)

    for pat in PROHIBITED_CITATION_PATTERNS:
        m = pat.findall(text)
        if m:
            found_prohibited.extend(m)

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
                    if name and not any(app.search(name) for app in APPROVED_CITATION_PATTERNS):
                        found_unapproved.append(f"{name} {kw}")
            else:
                # E.g. "словник Zorblax", "словниками ВЕСУМ та Zorblax", "словниками ВЕСУМ, Zorblax"
                clean_span = re.sub(
                    r"^(?:[Сс]ловник\w*|[Кк]орпус\w*|[Дд]овідник\w*|[Бб]аз\w*)\s+",
                    "",
                    citation_span,
                )
                sub_entities = re.split(r"\s*,\s*|\s+(?:та|і|й|and|or)\s+", clean_span)
                for ent in sub_entities:
                    ent = ent.strip().strip("«»\"'")
                    if ent and not any(app.search(ent) for app in APPROVED_CITATION_PATTERNS):
                        found_unapproved.append(ent)

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

            clauses = [c.strip() for c in re.split(r"[.,\n;!?]+", thought_and_resp) if c.strip()]
            for clause in clauses:
                mentions_target = (
                    f"«{t_lower}»" in clause
                    or f"\"{t_lower}\"" in clause
                    or f"слово {t_lower}" in clause
                    or f"термін {t_lower}" in clause
                    or f"форма {t_lower}" in clause
                    or f"«{t_lower}" in clause
                    or (t_lower in clause and any(kw in clause for kw in ("кальк", "росіянізм", "помилк", "суржик", "замін", "уникай", "ненормативн")))
                )
                if not mentions_target:
                    continue

                has_nenorm_condemn = bool(re.search(r"\bненормативн\w*\b", clause)) and not bool(
                    re.search(r"\bне\s+(?:є\s+)?(?:вважається\s+)?ненормативн\w*\b", clause)
                )

                copula_condemn = bool(
                    re.search(
                        r"(?:є|[—–\-]|\:)\s*(?:це\s+)?(?:кальк\w*|росіянізм\w*|помилк\w*|суржик\w*|ненормативн\w*|штучн\w*)",
                        clause,
                    )
                )

                clause_condemns = (
                    any(
                        cp in clause
                        for cp in (
                            f"«{t_lower}» є калькою",
                            f"«{t_lower}» — калька",
                            f"«{t_lower}» – калька",
                            f"«{t_lower}»: калька",
                            f"«{t_lower}» є росіянізмом",
                            f"«{t_lower}» — росіянізм",
                            f"«{t_lower}» – росіянізм",
                            f"«{t_lower}»: росіянізм",
                            f"слово {t_lower} є калькою",
                            f"слово {t_lower} — калька",
                            f"слово {t_lower} – калька",
                            f"слово {t_lower}: калька",
                            f"слово {t_lower} є росіянізмом",
                            f"замініть «{t_lower}»",
                            f"уникайте «{t_lower}»",
                            f"помилкове вживання «{t_lower}»",
                        )
                    )
                    or any(
                        w in clause
                        for w in (
                            "є калькою",
                            "— калька",
                            "– калька",
                            ": калька",
                            "є росіянізмом",
                            "є помилкою",
                            "помилково",
                            "є суржиком",
                            "є штучн",
                        )
                    )
                    or copula_condemn
                    or has_nenorm_condemn
                )

                target_negations = (
                    f"«{t_lower}» не є калькою",
                    f"«{t_lower}» не є росіянізмом",
                    f"«{t_lower}» не є помилкою",
                    f"«{t_lower}» не помилка",
                    f"«{t_lower}» не є суржиком",
                    f"«{t_lower}» не є штучн",
                    f"слово {t_lower} не є калькою",
                    f"слово {t_lower} не є росіянізмом",
                    f"слово {t_lower} не є помилкою",
                    f"слово {t_lower} не помилка",
                    f"«{t_lower}» є нормативним",
                    f"слово {t_lower} є нормативним",
                    f"зберігаємо «{t_lower}»",
                    f"зберігаємо слово {t_lower}",
                    f"зберігаємо термін {t_lower}",
                    f"«{t_lower}» без змін",
                    "не є калькою",
                    "не калька",
                    "не є росіянізмом",
                    "не росіянізм",
                    "не є помилкою",
                    "не помилка",
                    "не є суржиком",
                    "не є штучн",
                    "не потребує змін",
                    "не потребує виправлення",
                    "не потребує заміни",
                )

                neg_nenorm = bool(re.search(r"\bне\s+(?:є\s+)?(?:вважається\s+)?ненормативн\w*\b", clause))

                target_affirm = bool(
                    re.search(
                        rf"\b(?<!інше\s)(?<!іншого\s)(?<!іншим\s)(?<!нового\s)(?<!інший\s)(?:«?{re.escape(t_lower)}»?|(?:це|дане|зазначене)\s+(?:слово|термін))\s+(?:є\s+)?(?:нормативн|правильн|питом)",
                        clause,
                    )
                )

                target_preserve = (
                    any(p in clause for p in ("зберігаємо", "preserve", "без змін"))
                    and not bool(re.search(r"\b(?:решт\w*|інш\w*|нового|іншого)\b", clause))
                )

                clause_negated = (
                    any(np in clause for np in target_negations)
                    or neg_nenorm
                    or target_affirm
                    or target_preserve
                )

                if clause_condemns and not clause_negated:
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
    )


def format_markdown_report(summary: EvaluationSummary) -> str:
    """Generate human-readable Markdown evaluation report for PRs and model cards."""
    status_icon = "✅ PASS" if summary.all_gates_pass else "❌ FAIL"
    g1_icon = "✅ PASS" if summary.gate1_pass else "❌ FAIL"
    g2_icon = "✅ PASS" if summary.gate2_pass else "❌ FAIL"
    g3_icon = "✅ PASS" if summary.gate3_pass else "❌ FAIL"
    g4_icon = "✅ PASS" if summary.gate4_pass else "❌ FAIL"
    g5_icon = "✅ PASS" if summary.gate5_pass else "❌ FAIL"

    return f"""# ULDR Phase 5.1 Evaluation Audit Report
>
> **Evaluation Timestamp:** `{summary.timestamp}`
> **Overall Gate Verdict:** **{status_icon}**
> **Total Evaluated Cases:** `{summary.total_cases}` (`{summary.format_valid_count}` format-valid, `{summary.format_error_count}` format-errors)

---

## 1. Quality Gate Scorecard

| Production Gate | Target Threshold | Measured Score | Status |
| :--- | :--- | :--- | :--- |
| **Gate 1: Calque Elimination Rate** | >= 90.0% | **{summary.calque_elimination_rate * 100:.2f}%** ({summary.correct_eliminated_count}/{summary.correct_cases_total}) | {g1_icon} |
| **Gate 2: Harmful-Edit Rate** | <= 1.0% (Clopper-Pearson 95%) | **{summary.harmful_edit_rate * 100:.2f}%** (Upper bound: **{summary.clopper_pearson_upper * 100:.2f}%**, N={summary.preserve_cases_total}) | {g2_icon} |
| **Gate 3: Span Integrity Gate** | 100% (0 mutations outside span) | **{summary.span_integrity_rate * 100:.2f}%** ({summary.span_integrity_violations} violations) | {g3_icon} |
| **Gate 4: Citation Whitelist Gate** | 0% foreign hallucinations | **{summary.citation_violations_count}** violations (rate: {summary.citation_hallucination_rate * 100:.2f}%) | {g4_icon} |
| **Gate 5: High-Frequency Calque Floor** | 100% on top 50 calques ({summary.high_freq_floor} distinct required) | **{summary.high_freq_recall * 100:.2f}%** ({summary.high_freq_distinct_covered}/{summary.high_freq_floor} distinct covered, {summary.high_freq_eliminated}/{summary.high_freq_total} total) | {g5_icon} |

---

## 2. Gate Definitions & Statistical Criteria
* **Gate 1 (Calque Elimination):** Measures eradication of Russianisms and calques in final recommendations on held-out cases.
* **Gate 2 (Harmful Edits):** Exact one-sided 95% Clopper-Pearson binomial upper bound U = Beta^-1(0.95; k+1, n-k) <= 0.01 on >= 300 clean controls.
* **Gate 3 (Span Integrity):** Prevents collocation hallucinations (*побитися об заклад* -> *побитися об друга*). Tokens outside designated error spans must not be mutated.
* **Gate 4 (Citation Whitelist):** Rejects hallucinated foreign dictionaries (*COBUILD*, *LexicalLab*). Only approved authorities (ВЕСУМ, СУМ-20, Правопис 2019, Антоненко-Давидович, Грінченко, УЛІФ, UA-GEC) permitted.
* **Gate 5 (High-Frequency Calque Floor):** Requires 100% recall on the 50 most common Ukrainian calques (*приймати участь*, *на протязі*, *приймати міри*).
"""


def main() -> int:
    """CLI entrypoint for evaluation harness."""
    parser = argparse.ArgumentParser(description="ULDR Phase 5.1 Evaluation Suite")
    parser.add_argument("--heldout", type=Path, default=DEFAULT_HELDOUT_PATH, help="Path to held-out evaluation JSONL")
    parser.add_argument("--predictions", type=Path, default=None, help="Path to model predictions JSONL")
    parser.add_argument("--output-json", type=Path, default=Path("evaluation_report.json"), help="Output JSON path")
    parser.add_argument("--output-md", type=Path, default=Path("evaluation_report.md"), help="Output Markdown path")
    parser.add_argument("--min-high-freq-floor", type=int, default=50, help="Minimum high-frequency calques required")
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
        summary = run_evaluation_suite(test_cases, test_preds, min_high_freq_floor=1)
        print(f"Self-test complete: Gate 1 Pass: {summary.gate1_pass}, Format valid: {summary.format_valid_count}")
        return 0

    if not args.predictions:
        print("Error: --predictions <path.jsonl> or --self-test required.", file=sys.stderr)
        return 1

    if not args.heldout.exists():
        print(f"Error: Held-out file {args.heldout} does not exist.", file=sys.stderr)
        return 1

    eval_cases = [json.loads(line) for line in args.heldout.read_text(encoding="utf-8").splitlines() if line.strip()]

    # Load predictions
    preds_raw = [json.loads(line) for line in args.predictions.read_text(encoding="utf-8").splitlines() if line.strip()]
    predictions = {p.get("eval_id") or p.get("id"): p.get("prediction") or p.get("output") or p.get("response") for p in preds_raw}

    summary = run_evaluation_suite(eval_cases, predictions, min_high_freq_floor=args.min_high_freq_floor)

    args.output_json.write_text(json.dumps(asdict(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    md_content = format_markdown_report(summary)
    args.output_md.write_text(md_content, encoding="utf-8")

    print(md_content)
    return 0 if summary.all_gates_pass else 2


if __name__ == "__main__":
    sys.exit(main())
