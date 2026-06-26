"""Generate review-only Word Atlas cloze candidates from Tatoeba UK->EN pairs."""

from __future__ import annotations

import argparse
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
SUPPORTED_CASE_RULE_IDS = ("accusative_direct_object", "locative_static_u", "locative_static_na")
SUPPORTED_CASE_RULE_SET = frozenset(SUPPORTED_CASE_RULE_IDS)
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
    min_words: int = 4
    max_words: int = 12
    max_per_lemma: int = 8
    max_per_case_rule: int = 2_000
    max_per_lemma_case_rule: int = 3
    near_duplicate_distance: int = 3
    near_duplicate_ratio: float = 0.16
    limit_pairs: int | None = None


@dataclass
class GenerationReport:
    candidates: list[dict[str, Any]] = field(default_factory=list)
    rejections: Counter[str] = field(default_factory=Counter)

    def reject(self, reason: str, count: int = 1) -> None:
        self.rejections[reason] += count


RussianShadowChecker = Callable[[str], bool]


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


def read_tatoeba_sentences(path: Path, expected_lang: str) -> dict[int, TatoebaSentence]:
    rows: dict[int, TatoebaSentence] = {}
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
        clean_license = _clean_text(license_value)
        if not clean_text:
            continue
        if not clean_license:
            raise ValueError(f"{path}: sentence {sentence_id} missing per-row license; use the detailed export")
        rows[sentence_id] = TatoebaSentence(
            sentence_id=sentence_id,
            lang=expected_lang,
            text=clean_text,
            author=_clean_text(author) or "unknown",
            license=clean_license,
        )
    return rows


def read_tatoeba_links(path: Path) -> list[tuple[int, int]]:
    links: list[tuple[int, int]] = []
    for row in _rows_from_csv(path):
        if isinstance(row, dict):
            raw_left = _dict_value(row, "sentence_id", "sentence id", "left_id", "id")
            raw_right = _dict_value(row, "translation_id", "translation id", "right_id", "translation")
        else:
            if len(row) < 2:
                continue
            raw_left, raw_right = row[0], row[1]
        if raw_left and raw_right:
            links.append((int(str(raw_left)), int(str(raw_right))))
    return links


def read_tatoeba_pairs(uk_sentences: Path, en_sentences: Path, links: Path) -> list[TatoebaPair]:
    uk_rows = read_tatoeba_sentences(uk_sentences, "ukr")
    en_rows = read_tatoeba_sentences(en_sentences, "eng")
    pairs: list[TatoebaPair] = []
    seen: set[tuple[int, int]] = set()
    for left_id, right_id in read_tatoeba_links(links):
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
                surface = _clean_text(_case_form(paradigm, case_name, number))
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


def _russianism_prescreen(text: str, checker: RussianShadowChecker) -> bool:
    if RUSSIANISM_RE.search(text):
        return True
    return any(checker(token.text) for token in _tokens(text))


def _bump_cefr(level: str, steps: int) -> str:
    index = min(CEFR_RANK[level] + steps, len(CEFR_ORDER) - 1)
    return CEFR_ORDER[index]


def assign_sentence_cefr(
    sentence: str,
    tokens: list[TokenSpan],
    verifier: VesumVerifier,
    lemma_levels: dict[str, str],
) -> str | None:
    ranks: list[int] = []
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
            return None
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
) -> GenerationReport:
    config = config or GeneratorConfig()
    report = GenerationReport()
    target_index = _build_target_index(entries, report)
    lemma_levels = _build_lemma_levels(entries)
    seen_hashes: set[str] = set()
    seen_frames: list[str] = []
    accepted: list[dict[str, Any]] = []
    ordered_pairs = sorted(pairs, key=lambda pair: (pair.uk.sentence_id, pair.en.sentence_id))
    if config.limit_pairs is not None:
        ordered_pairs = ordered_pairs[: config.limit_pairs]
    for pair in ordered_pairs:
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
        sentence_cefr = assign_sentence_cefr(sentence, tokens, verifier, lemma_levels)
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
    return report


def write_candidates(candidates: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    parser.add_argument("--vesum-json", type=Path)
    parser.add_argument("--seed", type=int, default=GeneratorConfig.seed)
    parser.add_argument("--max-per-lemma", type=int, default=GeneratorConfig.max_per_lemma)
    parser.add_argument("--max-per-case-rule", type=int, default=GeneratorConfig.max_per_case_rule)
    parser.add_argument("--max-per-lemma-case-rule", type=int, default=GeneratorConfig.max_per_lemma_case_rule)
    parser.add_argument("--limit-pairs", type=int)
    args = parser.parse_args(argv)

    entries = read_manifest(args.manifest)
    pairs = read_tatoeba_pairs(args.uk_sentences, args.en_sentences, args.links)
    verifier: VesumVerifier = JsonVesumVerifier.from_path(args.vesum_json) if args.vesum_json else RealVesumVerifier()
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
    )
    write_candidates(report.candidates, args.out)
    print(f"wrote {len(report.candidates)} candidates to {args.out}")
    for reason, count in sorted(report.rejections.items()):
        print(f"rejected.{reason}={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
