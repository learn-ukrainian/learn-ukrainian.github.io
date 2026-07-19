"""Generate review-only Word Atlas cloze candidates from Tatoeba UK->EN pairs."""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = PROJECT_ROOT / "scripts" / "audit"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(AUDIT_DIR) not in sys.path:
    sys.path.insert(0, str(AUDIT_DIR))

from generate_practice_deck import (
    CASE_RULES,
    CEFR_ORDER,
    CEFR_RANK,
    NUMBER_KEYS,
    JsonVesumVerifier,
    RealVesumVerifier,
    VesumVerifier,
    _case_form,
    _cefr_level,
    _clean_text,
    _cloze_candidate_ok_for_level,
    _match_cases,
    _paradigm,
    _plain,
    _verify_discriminative_form,
    _vesum_pos,
    read_manifest,
)

from scripts.lexicon.heritage_classifier import _check_russian_shadow

DEFAULT_OUT = Path("site/src/data/lexicon-practice-cloze-tatoeba-review-candidates.json")
DEFAULT_LICENSE = "CC-BY 2.0 FR"
SUPPORTED_CASE_RULE_IDS = ("accusative_direct_object", "locative_static_u", "locative_static_na")
SUPPORTED_CASE_RULE_SET = frozenset(SUPPORTED_CASE_RULE_IDS)
MANIFEST_CASE_LABEL_BY_RULE_ID = {
    "accusative_direct_object": "знахідний",
    "locative_static_u": "місцевий",
    "locative_static_na": "місцевий",
}
UK_TOKEN_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’-][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*")
EN_DASH_RE = re.compile(r"\s+")
LICENSE_RE = re.compile(r"\b(?:CC0|CC[- ]BY(?:\s+2\.0\s+FR)?)\b", re.IGNORECASE)
RUSSIANISM_RE = re.compile(
    r"\b(?:сейчас|конечно|пожалуйста|вообще|нравится|мероприятие|давай|нє|шо)\b",
    re.IGNORECASE,
)
BLOCKED_REGISTER_RE = re.compile(
    r"\b(?:бляд\w*|хуй\w*|пизд\w*|сучар\w*|аще|сей|оный|треба перевірити|needs native check)\b",
    re.IGNORECASE,
)
FUNCTION_LEMMAS = frozenset(
    {
        "і",
        "й",
        "а",
        "але",
        "або",
        "та",
        "у",
        "в",
        "на",
        "з",
        "зі",
        "до",
        "для",
        "по",
        "про",
        "не",
        "це",
        "цей",
        "ця",
        "цю",
        "ту",
        "той",
        "те",
        "ті",
        "моє",
        "моя",
        "мій",
        "я",
        "ти",
        "він",
        "вона",
        "ми",
        "ви",
        "вони",
    }
)
ACCUSATIVE_PREPOSITIONS = frozenset({"у", "в", "на", "за", "про", "через", "під", "над", "по", "крізь"})
COMPLEXITY_TOKENS = frozenset({"який", "яка", "яке", "які", "коли", "якщо", "щоб", "тому"})


@dataclass(frozen=True)
class TatoebaSentence:
    sentence_id: int
    lang: str
    text: str
    author: str
    license: str


@dataclass(frozen=True)
class TatoebaPair:
    uk: TatoebaSentence
    en: TatoebaSentence


@dataclass(frozen=True)
class TokenSpan:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class TargetForm:
    lemma: str
    lemma_id: str
    lemma_plain: str
    pos: str | None
    word_cefr: str
    rule_id: str
    case_name: str
    number: str
    surface: str
    surface_plain: str


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 3797
    min_words: int = 3
    max_words: int = 16
    max_unknown_tokens: int = 4
    max_per_lemma: int = 10_000
    max_per_case_rule: int = 10_000
    max_per_lemma_case_rule: int = 10_000
    near_duplicate_distance: int = 3
    near_duplicate_ratio: float = 0.16
    limit_pairs: int | None = None


@dataclass
class GenerationReport:
    candidates: list[dict[str, Any]] = field(default_factory=list)
    rejections: Counter[str] = field(default_factory=Counter)
    pairs_processed: int = 0
    target_form_keys: int = 0
    target_forms: int = 0
    lemma_with_targets: int = 0

    def reject(self, reason: str, count: int = 1) -> None:
        self.rejections[reason] += count


RussianShadowChecker = Callable[[str], bool]


def require_existing_path(path: Path, label: str) -> Path:
    """Fail closed with an actionable message when a required input is missing."""
    resolved = path.expanduser()
    if not resolved.exists():
        raise FileNotFoundError(
            f"missing {label}: {resolved}\n"
            "Hydrate/download the real Phase-1 inputs before generation. "
            "See docs/atlas/tatoeba-cloze-yield-report.md § Phase 1 retry runbook."
        )
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} is not a file: {resolved}")
    return resolved


def check_russian_shadow(token: str) -> bool:
    matches, _detail = _check_russian_shadow(token)
    return matches


def _detect_delimiter(path: Path) -> str:
    sample = path.read_text(encoding="utf-8").splitlines()[:3]
    joined = "\n".join(sample)
    return "\t" if joined.count("\t") >= joined.count(",") else ","


def _rows_from_csv(path: Path) -> Iterable[list[str] | dict[str, str]]:
    delimiter = _detect_delimiter(path)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        first = next(reader, None)
        if not first:
            return
        has_header = bool(first) and (not first[0].strip().isdigit())
        if has_header:
            dict_reader = csv.DictReader(handle, fieldnames=first, delimiter=delimiter)
            yield from dict_reader
        else:
            yield first
            yield from reader


def _dict_value(row: dict[str, str], *keys: str) -> str | None:
    lowered = {key.strip().lower(): value for key, value in row.items()}
    for key in keys:
        value = _clean_text(lowered.get(key))
        if value:
            return value
    return None


def _row_license(values: Iterable[str]) -> str | None:
    for value in values:
        text = _clean_text(value)
        if text and LICENSE_RE.search(text):
            return text
    return None


def read_cc0_sentence_ids(path: Path | None) -> set[int]:
    """Load Tatoeba sentences_CC0 export IDs (id is the first column)."""
    if path is None:
        return set()
    ids: set[int] = set()
    for row in _rows_from_csv(path):
        if isinstance(row, dict):
            raw_id = _dict_value(row, "id", "sentence_id", "sentence id")
        else:
            if not row:
                continue
            raw_id = row[0]
        if not raw_id:
            continue
        try:
            ids.add(int(str(raw_id).strip()))
        except ValueError:
            continue
    return ids


def _resolve_sentence_license(
    path: Path,
    sentence_id: int,
    license_value: str | None,
    *,
    default_license: str | None,
    cc0_ids: set[int],
) -> str:
    clean_license = _clean_text(license_value)
    if clean_license:
        return clean_license
    if sentence_id in cc0_ids:
        return "CC0"
    if default_license:
        return default_license
    raise ValueError(
        f"{path}: sentence {sentence_id} missing per-row license. "
        "Detailed Tatoeba exports omit license; pass --default-license "
        f"{DEFAULT_LICENSE!r} and optionally --cc0-sentences sentences_CC0.csv."
    )


def read_tatoeba_sentences(
    path: Path,
    expected_lang: str,
    *,
    default_license: str | None = None,
    cc0_ids: set[int] | None = None,
) -> dict[int, TatoebaSentence]:
    rows: dict[int, TatoebaSentence] = {}
    cc0_ids = cc0_ids or set()
    for row in _rows_from_csv(path):
        if isinstance(row, dict):
            raw_id = _dict_value(row, "id", "sentence_id", "sentence id")
            lang = _dict_value(row, "lang", "language") or expected_lang
            text = _dict_value(row, "text", "sentence")
            author = _dict_value(row, "author", "username", "user") or "unknown"
            license_value = _dict_value(row, "license", "licence") or _row_license(row.values())
        else:
            if len(row) < 3:
                continue
            raw_id, lang, text = row[0], row[1], row[2]
            author = _clean_text(row[3]) if len(row) > 3 else "unknown"
            license_value = _row_license(row[3:])
        if _clean_text(lang) != expected_lang:
            continue
        sentence_id = int(str(raw_id))
        clean_text = _clean_text(text)
        if not clean_text:
            continue
        clean_license = _resolve_sentence_license(
            path,
            sentence_id,
            license_value,
            default_license=default_license,
            cc0_ids=cc0_ids,
        )
        rows[sentence_id] = TatoebaSentence(
            sentence_id=sentence_id,
            lang=expected_lang,
            text=clean_text,
            author=_clean_text(author) or "unknown",
            license=clean_license,
        )
    return rows


def _iter_tatoeba_link_ids(path: Path) -> Iterable[tuple[int, int]]:
    # Fast path for the weekly Tatoeba links export (two integer columns, no header).
    # csv.reader over ~28M rows dominated Phase-1 load time.
    with path.open(encoding="utf-8") as handle:
        first = handle.readline()
        if not first:
            return
        first_cells = first.rstrip("\n").split("\t" if "\t" in first else ",")
        has_header = bool(first_cells) and (not first_cells[0].strip().isdigit())
        if not has_header and len(first_cells) >= 2:
            with contextlib.suppress(ValueError):
                yield int(first_cells[0]), int(first_cells[1])
            delimiter = "\t" if "\t" in first else ","
            for line in handle:
                cells = line.rstrip("\n").split(delimiter)
                if len(cells) < 2:
                    continue
                with contextlib.suppress(ValueError):
                    yield int(cells[0]), int(cells[1])
            return
    # Headered/dict fallback for fixtures and alternate exports.
    for row in _rows_from_csv(path):
        if isinstance(row, dict):
            raw_left = _dict_value(row, "sentence_id", "sentence id", "left_id", "id")
            raw_right = _dict_value(row, "translation_id", "translation id", "right_id", "translation")
        else:
            if len(row) < 2:
                continue
            raw_left, raw_right = row[0], row[1]
        if not raw_left or not raw_right:
            continue
        with contextlib.suppress(ValueError):
            yield int(str(raw_left)), int(str(raw_right))


def read_tatoeba_links(path: Path) -> list[tuple[int, int]]:
    return list(_iter_tatoeba_link_ids(path))


def read_tatoeba_pairs(
    uk_sentences: Path,
    en_sentences: Path,
    links: Path,
    *,
    default_license: str | None = None,
    cc0_ids: set[int] | None = None,
) -> list[TatoebaPair]:
    uk_rows = read_tatoeba_sentences(
        uk_sentences,
        "ukr",
        default_license=default_license,
        cc0_ids=cc0_ids,
    )
    en_rows = read_tatoeba_sentences(
        en_sentences,
        "eng",
        default_license=default_license,
        cc0_ids=cc0_ids,
    )
    pairs: list[TatoebaPair] = []
    seen: set[tuple[int, int]] = set()
    # Stream links and keep only UK↔EN pairs. Materializing the full 28M-row
    # links export first dominated Phase-1 wall time on real data.
    for left_id, right_id in _iter_tatoeba_link_ids(links):
        if left_id in uk_rows and right_id in en_rows:
            pair_key = (left_id, right_id)
            pair = TatoebaPair(uk=uk_rows[left_id], en=en_rows[right_id])
        elif right_id in uk_rows and left_id in en_rows:
            pair_key = (right_id, left_id)
            pair = TatoebaPair(uk=uk_rows[right_id], en=en_rows[left_id])
        else:
            continue
        if pair_key in seen:
            continue
        seen.add(pair_key)
        pairs.append(pair)
    return sorted(pairs, key=lambda pair: (pair.uk.sentence_id, pair.en.sentence_id))


def _tokens(text: str) -> list[TokenSpan]:
    return [TokenSpan(match.group(0), match.start(), match.end()) for match in UK_TOKEN_RE.finditer(text)]


def _verify_token(verifier: VesumVerifier, token: str) -> list[dict[str, Any]]:
    lower = token.casefold()
    forms = [token] if token == lower else [token, lower]
    verified = verifier.verify_words(forms)
    return verified.get(token) or verified.get(lower) or []


def _manifest_lemma_id(entry: dict[str, Any], lemma: str) -> str:
    for key in ("lemmaId", "lemma_id", "url_slug", "slug", "id"):
        value = _clean_text(entry.get(key))
        if value:
            return value
    return _plain(lemma).replace(" ", "-")


def _build_lemma_levels(entries: list[dict[str, Any]]) -> dict[str, str]:
    levels: dict[str, str] = {}
    for entry in entries:
        lemma = _clean_text(entry.get("lemma"))
        level = _cefr_level(entry)
        if lemma and level:
            levels[_plain(lemma)] = level
    return levels


def _manifest_case_form(paradigm: dict[str, Any], rule_id: str, case_name: str, number: str) -> str | None:
    return _case_form(paradigm, MANIFEST_CASE_LABEL_BY_RULE_ID.get(rule_id, case_name), number) or _case_form(
        paradigm,
        case_name,
        number,
    )


def _build_target_index(
    entries: list[dict[str, Any]],
    report: GenerationReport,
) -> dict[str, list[TargetForm]]:
    index: dict[str, list[TargetForm]] = defaultdict(list)
    for entry in entries:
        lemma = _clean_text(entry.get("lemma"))
        word_cefr = _cefr_level(entry)
        if not lemma or not word_cefr:
            continue
        if len(_tokens(lemma)) != 1:
            report.reject("multiword_lemma")
            continue
        lemma_plain = _plain(lemma)
        paradigm = _paradigm(entry)
        pos = _clean_text(entry.get("pos"))
        lemma_id = _manifest_lemma_id(entry, lemma)
        for rule_id in SUPPORTED_CASE_RULE_IDS:
            rule = CASE_RULES[rule_id]
            case_name = str(rule["case"])
            for number in NUMBER_KEYS:
                surface = _clean_text(_manifest_case_form(paradigm, rule_id, case_name, number))
                if not surface:
                    continue
                surface_plain = _plain(surface)
                if surface_plain == lemma_plain:
                    report.reject("surface_equals_lemma")
                    continue
                if len(_tokens(surface)) != 1:
                    report.reject("target_punctuation_or_multiword")
                    continue
                index[surface_plain].append(
                    TargetForm(
                        lemma=lemma,
                        lemma_id=lemma_id,
                        lemma_plain=lemma_plain,
                        pos=pos,
                        word_cefr=word_cefr,
                        rule_id=rule_id,
                        case_name=case_name,
                        number=number,
                        surface=surface,
                        surface_plain=surface_plain,
                    )
                )
    return index


def _previous_plain(tokens: list[TokenSpan], index: int) -> str | None:
    if index <= 0:
        return None
    return _plain(tokens[index - 1].text)


def _rule_trigger_matches(target: TargetForm, tokens: list[TokenSpan], token_index: int) -> bool:
    previous = _previous_plain(tokens, token_index)
    if target.rule_id == "locative_static_u":
        return previous in {"у", "в"}
    if target.rule_id == "locative_static_na":
        return previous == "на"
    if target.rule_id == "accusative_direct_object":
        return previous not in ACCUSATIVE_PREPOSITIONS
    return False


def _lemma_occurrence_count(tokens: list[TokenSpan], target: TargetForm, verifier: VesumVerifier) -> int:
    count = 0
    for token in tokens:
        matches = _verify_token(verifier, token.text)
        if any(_plain(str(match.get("lemma") or "")) == target.lemma_plain for match in matches):
            count += 1
    return count


def _is_unambiguous_target(target: TargetForm, verifier: VesumVerifier) -> bool:
    if not _verify_discriminative_form(
        target.lemma_plain,
        target.pos,
        target.surface,
        target.case_name,
        verifier,
    ):
        return False
    matches = verifier.verify_words([target.surface], _vesum_pos(target.pos)).get(target.surface, [])
    return len(matches) == 1 and _match_cases(matches[0]) == {target.case_name}


def _blank_sentence(sentence: str, token: TokenSpan) -> str:
    return f"{sentence[: token.start]}___{sentence[token.end :]}"


def _normalized_frame(sentence: str) -> str:
    normalized = _plain(sentence).replace("___", "__blank__")
    normalized = re.sub(r"[^\w\s_]+", "", normalized, flags=re.UNICODE)
    return EN_DASH_RE.sub(" ", normalized).strip()


def _levenshtein_at_most(left: str, right: str, cutoff: int) -> int:
    if abs(len(left) - len(right)) > cutoff:
        return cutoff + 1
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        row_min = current[0]
        for right_index, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            value = min(previous[right_index] + 1, current[right_index - 1] + 1, previous[right_index - 1] + cost)
            current.append(value)
            row_min = min(row_min, value)
        if row_min > cutoff:
            return cutoff + 1
        previous = current
    return previous[-1]


def _is_near_duplicate(frame: str, existing_frames: list[str], config: GeneratorConfig) -> bool:
    for existing in existing_frames:
        cutoff = max(config.near_duplicate_distance, int(max(len(frame), len(existing)) * config.near_duplicate_ratio))
        if _levenshtein_at_most(frame, existing, cutoff) <= cutoff:
            return True
    return False


def _blocked_register(text: str) -> bool:
    return bool(BLOCKED_REGISTER_RE.search(text))


def _russianism_prescreen(text: str, _checker: RussianShadowChecker) -> bool:
    return bool(RUSSIANISM_RE.search(text))


def _bump_cefr(level: str, steps: int) -> str:
    index = min(CEFR_RANK[level] + steps, len(CEFR_ORDER) - 1)
    return CEFR_ORDER[index]


def assign_sentence_cefr(
    sentence: str,
    tokens: list[TokenSpan],
    verifier: VesumVerifier,
    lemma_levels: dict[str, str],
    max_unknown_tokens: int = 4,
) -> str | None:
    ranks: list[int] = []
    unknown_tokens = 0
    for token in tokens:
        token_plain = _plain(token.text)
        if token_plain in FUNCTION_LEMMAS:
            continue
        matches = _verify_token(verifier, token.text)
        token_levels = [
            lemma_levels[_plain(str(match.get("lemma") or ""))]
            for match in matches
            if _plain(str(match.get("lemma") or "")) in lemma_levels
        ]
        if not token_levels:
            unknown_tokens += 1
            if unknown_tokens > max_unknown_tokens:
                return None
            continue
        ranks.append(max(CEFR_RANK[level] for level in token_levels))
    if not ranks:
        return None
    level = CEFR_ORDER[max(ranks)]
    token_plains = {_plain(token.text) for token in tokens}
    complexity_steps = 0
    if len(tokens) > 10:
        complexity_steps += 1
    if COMPLEXITY_TOKENS.intersection(token_plains) or ";" in sentence or ":" in sentence:
        complexity_steps += 1
    return _bump_cefr(level, complexity_steps)


def _candidate_for_pair(
    pair: TatoebaPair,
    target: TargetForm,
    token: TokenSpan,
    sentence_cefr: str,
) -> dict[str, Any]:
    return {
        "lemma": target.lemma,
        "lemmaId": target.lemma_id,
        "sentence": _blank_sentence(pair.uk.text, token),
        "blankCase": target.case_name,
        "form": target.surface,
        "number": target.number,
        "caseRuleId": target.rule_id,
        "clozeEn": pair.en.text,
        "cefr": sentence_cefr,
        "provenance": {
            "status": "tatoeba",
            "path": f"tatoeba:{pair.uk.sentence_id}",
            "license": pair.uk.license,
            "author": pair.uk.author,
            "sentenceId": pair.uk.sentence_id,
            "enSentenceId": pair.en.sentence_id,
            "enAuthor": pair.en.author,
            "enLicense": pair.en.license,
        },
    }


def _candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, str, str, int]:
    provenance = candidate.get("provenance") if isinstance(candidate.get("provenance"), dict) else {}
    sentence_id = int(provenance.get("sentenceId") or 0)
    return (
        CEFR_RANK.get(str(candidate.get("cefr") or ""), len(CEFR_RANK)),
        str(candidate.get("lemmaId") or ""),
        str(candidate.get("caseRuleId") or ""),
        sentence_id,
    )


def _apply_caps(
    candidates: list[dict[str, Any]],
    report: GenerationReport,
    config: GeneratorConfig,
) -> list[dict[str, Any]]:
    shuffled = list(candidates)
    random.Random(config.seed).shuffle(shuffled)
    lemma_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    lemma_rule_counts: Counter[tuple[str, str]] = Counter()
    selected: list[dict[str, Any]] = []
    for candidate in shuffled:
        lemma_id = str(candidate.get("lemmaId") or "")
        rule_id = str(candidate.get("caseRuleId") or "")
        lemma_rule = (lemma_id, rule_id)
        if lemma_counts[lemma_id] >= config.max_per_lemma:
            report.reject("cap_lemma")
            continue
        if rule_counts[rule_id] >= config.max_per_case_rule:
            report.reject("cap_case_rule")
            continue
        if lemma_rule_counts[lemma_rule] >= config.max_per_lemma_case_rule:
            report.reject("cap_lemma_case_rule")
            continue
        lemma_counts[lemma_id] += 1
        rule_counts[rule_id] += 1
        lemma_rule_counts[lemma_rule] += 1
        selected.append(candidate)
    return sorted(selected, key=_candidate_sort_key)


def generate_tatoeba_cloze_candidates(
    entries: list[dict[str, Any]],
    pairs: Iterable[TatoebaPair],
    verifier: VesumVerifier,
    config: GeneratorConfig | None = None,
    russian_shadow_checker: RussianShadowChecker = check_russian_shadow,
    progress_every: int | None = None,
    progress_stream: Any | None = None,
) -> GenerationReport:
    config = config or GeneratorConfig()
    report = GenerationReport()
    target_index = _build_target_index(entries, report)
    report.target_form_keys = len(target_index)
    report.target_forms = sum(len(forms) for forms in target_index.values())
    report.lemma_with_targets = len({form.lemma_id for forms in target_index.values() for form in forms})
    lemma_levels = _build_lemma_levels(entries)
    seen_hashes: set[str] = set()
    seen_frames: list[str] = []
    accepted: list[dict[str, Any]] = []
    ordered_pairs = sorted(pairs, key=lambda pair: (pair.uk.sentence_id, pair.en.sentence_id))
    if config.limit_pairs is not None:
        ordered_pairs = ordered_pairs[: config.limit_pairs]
    total_pairs = len(ordered_pairs)
    report.pairs_processed = total_pairs
    progress_stream = sys.stderr if progress_stream is None else progress_stream
    if progress_every:
        print(
            f"progress.start pairs={total_pairs} target_keys={report.target_form_keys} "
            f"target_forms={report.target_forms} lemmas_with_targets={report.lemma_with_targets}",
            file=progress_stream,
            flush=True,
        )
    for pair_index, pair in enumerate(ordered_pairs, start=1):
        if progress_every and pair_index % progress_every == 0:
            print(
                f"progress.pairs={pair_index}/{total_pairs} accepted={len(accepted)}",
                file=progress_stream,
                flush=True,
            )
        if not _clean_text(pair.en.text):
            report.reject("missing_en_pair")
            continue
        sentence = pair.uk.text
        tokens = _tokens(sentence)
        if not config.min_words <= len(tokens) <= config.max_words:
            report.reject("sentence_length")
            continue
        if "___" in sentence:
            report.reject("existing_blank")
            continue
        if _blocked_register(sentence):
            report.reject("blocked_register")
            continue
        if _russianism_prescreen(sentence, russian_shadow_checker):
            report.reject("russianism_prescreen")
            continue
        sentence_cefr = assign_sentence_cefr(
            sentence,
            tokens,
            verifier,
            lemma_levels,
            max_unknown_tokens=config.max_unknown_tokens,
        )
        if sentence_cefr is None:
            report.reject("sentence_cefr_unknown")
            continue
        for token_index, token in enumerate(tokens):
            token_targets = target_index.get(_plain(token.text), [])
            for target in token_targets:
                if target.rule_id not in SUPPORTED_CASE_RULE_SET:
                    report.reject("unsupported_case_rule")
                    continue
                if not _rule_trigger_matches(target, tokens, token_index):
                    report.reject("unsupported_trigger")
                    continue
                if _lemma_occurrence_count(tokens, target, verifier) != 1:
                    report.reject("single_target_occurrence")
                    continue
                if not _is_unambiguous_target(target, verifier):
                    report.reject("vesum_ambiguous")
                    continue
                candidate = _candidate_for_pair(pair, target, token, sentence_cefr)
                if not _cloze_candidate_ok_for_level(candidate, target.word_cefr):
                    report.reject("sentence_cefr_above_word")
                    continue
                frame = _normalized_frame(candidate["sentence"])
                frame_hash = hashlib.sha256(frame.encode("utf-8")).hexdigest()
                if frame_hash in seen_hashes:
                    report.reject("exact_duplicate")
                    continue
                if _is_near_duplicate(frame, seen_frames, config):
                    report.reject("near_duplicate")
                    continue
                seen_hashes.add(frame_hash)
                seen_frames.append(frame)
                accepted.append(candidate)
    report.candidates = _apply_caps(accepted, report, config)
    if progress_every:
        print(
            f"progress.done pairs={total_pairs} candidates={len(report.candidates)}",
            file=progress_stream,
            flush=True,
        )
    return report


def write_candidates(candidates: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_yield_summary(report: GenerationReport) -> dict[str, Any]:
    by_case = Counter(str(candidate.get("caseRuleId") or "") for candidate in report.candidates)
    by_cefr = Counter(str(candidate.get("cefr") or "") for candidate in report.candidates)
    by_license = Counter(
        str((candidate.get("provenance") or {}).get("license") or "")
        if isinstance(candidate.get("provenance"), dict)
        else ""
        for candidate in report.candidates
    )
    return {
        "pairs_processed": report.pairs_processed,
        "candidates": len(report.candidates),
        "target_form_keys": report.target_form_keys,
        "target_forms": report.target_forms,
        "lemmas_with_targets": report.lemma_with_targets,
        "by_case_rule": dict(sorted(by_case.items())),
        "by_cefr": dict(sorted(by_cefr.items(), key=lambda item: CEFR_RANK.get(item[0], 99))),
        "by_license": dict(sorted(by_license.items())),
        "rejections": dict(sorted(report.rejections.items())),
    }


def format_yield_report_markdown(
    summary: dict[str, Any],
    *,
    title: str = "Tatoeba Cloze Yield Report",
    run_date: str | None = None,
    notes: list[str] | None = None,
) -> str:
    lines = [f"# {title}", ""]
    if run_date:
        lines.extend([f"Run date: {run_date}", ""])
    if notes:
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.extend(
        [
            "## Summary",
            "",
            "| Metric | Count |",
            "| --- | ---: |",
            f"| Pairs processed | {summary.get('pairs_processed', 0)} |",
            f"| Target form keys | {summary.get('target_form_keys', 0)} |",
            f"| Target forms | {summary.get('target_forms', 0)} |",
            f"| Lemmas with targets | {summary.get('lemmas_with_targets', 0)} |",
            f"| Candidates emitted | {summary.get('candidates', 0)} |",
            "",
            "By case rule:",
            "",
            "| caseRuleId | Candidates |",
            "| --- | ---: |",
        ]
    )
    for rule_id, count in (summary.get("by_case_rule") or {}).items():
        lines.append(f"| `{rule_id}` | {count} |")
    lines.extend(["", "By emitted sentence CEFR:", "", "| CEFR | Candidates |", "| --- | ---: |"])
    for level, count in (summary.get("by_cefr") or {}).items():
        lines.append(f"| {level} | {count} |")
    lines.extend(["", "By license:", "", "| License | Candidates |", "| --- | ---: |"])
    for license_name, count in (summary.get("by_license") or {}).items():
        lines.append(f"| {license_name or '(missing)'} | {count} |")
    lines.extend(["", "Full rejection breakdown:", "", "| Rejection | Count |", "| --- | ---: |"])
    for reason, count in (summary.get("rejections") or {}).items():
        lines.append(f"| `{reason}` | {count} |")
    lines.append("")
    return "\n".join(lines)


def write_yield_report(summary: dict[str, Any], path: Path, *, markdown: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json" or not markdown:
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    path.write_text(
        format_yield_report_markdown(summary),
        encoding="utf-8",
    )


def main(
    argv: list[str] | None = None,
    russian_shadow_checker: RussianShadowChecker = check_russian_shadow,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--uk-sentences", type=Path, required=True)
    parser.add_argument("--en-sentences", type=Path, required=True)
    parser.add_argument("--links", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--yield-report",
        type=Path,
        help="Write machine yield summary (.json) or markdown report (.md).",
    )
    parser.add_argument("--vesum-json", type=Path)
    parser.add_argument(
        "--default-license",
        default=None,
        help=(
            "Fill missing per-row licenses from detailed Tatoeba exports. "
            f"Recommended real-data value: {DEFAULT_LICENSE!r}."
        ),
    )
    parser.add_argument(
        "--cc0-sentences",
        type=Path,
        help="Optional sentences_CC0.csv export; those IDs get license CC0 when license is missing.",
    )
    parser.add_argument("--seed", type=int, default=GeneratorConfig.seed)
    parser.add_argument("--max-per-lemma", type=int, default=GeneratorConfig.max_per_lemma)
    parser.add_argument("--max-per-case-rule", type=int, default=GeneratorConfig.max_per_case_rule)
    parser.add_argument("--max-per-lemma-case-rule", type=int, default=GeneratorConfig.max_per_lemma_case_rule)
    parser.add_argument("--limit-pairs", type=int)
    parser.add_argument(
        "--progress-every",
        type=int,
        default=0,
        help="Emit pair progress to stderr every N pairs (0 disables).",
    )
    args = parser.parse_args(argv)

    manifest_path = require_existing_path(args.manifest, "Atlas manifest")
    uk_path = require_existing_path(args.uk_sentences, "Tatoeba UK sentences")
    en_path = require_existing_path(args.en_sentences, "Tatoeba EN sentences")
    links_path = require_existing_path(args.links, "Tatoeba links")
    vesum_json_path = require_existing_path(args.vesum_json, "VESUM JSON fixture") if args.vesum_json else None
    cc0_path = require_existing_path(args.cc0_sentences, "Tatoeba CC0 sentences") if args.cc0_sentences else None

    if vesum_json_path is None:
        vesum_db = PROJECT_ROOT / "data" / "vesum.db"
        if not vesum_db.exists():
            raise FileNotFoundError(
                f"missing real VESUM db for generation: {vesum_db}\n"
                "Symlink or copy the hydrated main-checkout data/vesum.db into this worktree, "
                "or pass --vesum-json for fixture-only runs."
            )

    entries = read_manifest(manifest_path)
    cc0_ids = read_cc0_sentence_ids(cc0_path)
    pairs = read_tatoeba_pairs(
        uk_path,
        en_path,
        links_path,
        default_license=args.default_license,
        cc0_ids=cc0_ids,
    )
    print(
        f"loaded entries={len(entries)} pairs={len(pairs)} cc0_ids={len(cc0_ids)}",
        flush=True,
    )
    verifier: VesumVerifier = (
        JsonVesumVerifier.from_path(vesum_json_path) if vesum_json_path else RealVesumVerifier()
    )
    report = generate_tatoeba_cloze_candidates(
        entries,
        pairs,
        verifier,
        GeneratorConfig(
            seed=args.seed,
            max_per_lemma=args.max_per_lemma,
            max_per_case_rule=args.max_per_case_rule,
            max_per_lemma_case_rule=args.max_per_lemma_case_rule,
            limit_pairs=args.limit_pairs,
        ),
        russian_shadow_checker=russian_shadow_checker,
        progress_every=args.progress_every or None,
    )
    write_candidates(report.candidates, args.out)
    summary = build_yield_summary(report)
    if args.yield_report:
        write_yield_report(summary, args.yield_report)
        print(f"wrote yield report to {args.yield_report}", flush=True)
    print(
        "targets."
        f"keys={report.target_form_keys} forms={report.target_forms} "
        f"lemmas={report.lemma_with_targets}",
        flush=True,
    )
    print(f"wrote {len(report.candidates)} candidates to {args.out}", flush=True)
    for reason, count in sorted(report.rejections.items()):
        print(f"rejected.{reason}={count}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
