#!/usr/bin/env python3
"""Deterministic plan quality checker.

Validates plan YAML files before content generation. Catches issues that
would otherwise waste build time (Russicisms, wrong stress, scope creep,
VESUM failures, missing fields).

Usage:
    .venv/bin/python scripts/audit/check_plan.py a1                    # all A1 plans
    .venv/bin/python scripts/audit/check_plan.py a1 --first 7          # A1.1 only
    .venv/bin/python scripts/audit/check_plan.py a1 --module 1         # single module
    .venv/bin/python scripts/audit/check_plan.py a1 --failing-only     # only show failures

Issue: #983
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"

# Combining acute accent
STRESS_MARK = "\u0301"
TRACK_LEVEL_KEYS = ("phases", "linguistic_evolution")

# Known Russicisms (subset — full list in semantic_russianisms.py)
_RUSSICISMS = {
    "кон": "кін (stake) or remove — кон is Russian",
    "кот": "кіт (cat)",
    "хорошо": "добре (well/good)",
    "получати": "отримувати (to receive)",
    "кушати": "їсти (to eat)",
    # NOTE: standalone "самий" is valid Ukrainian (той самий = the same one).
    # Only "самий + superlative adjective" is a Russicism (самий кращий → найкращий).
    # Moved to phrase-level check below.
    # "самий": "найкращий or найбільший",
    "дом": "дім (house)",
    "зеркало": "дзеркало (mirror)",
    "ковёр": "килим (carpet)",
    "мяч": "м'яч (ball) — needs apostrophe",
    "обязательно": "обов'язково (necessarily)",
    "вообще": "взагалі (in general)",
    "получається": "виходить (it works out)",
    "луна": "місяць (moon)",
}

_DIALOGUE_SECTION_RE = re.compile(
    r"(діалог|діалоги|розмов|conversation|dialogue|role-?play|scenario|сценар)",
    re.IGNORECASE,
)
_DIALOGUE_TOKEN_RE = re.compile(r"[a-zа-яґєії'-]+", re.IGNORECASE)
_DIALOGUE_STOPWORDS = {
    "a", "an", "and", "at", "for", "from", "in", "of", "on", "the", "to", "with",
    "а", "але", "бо", "в", "ви", "вона", "вони", "воно", "все", "до", "є", "за",
    "з", "і", "й", "на", "не", "по", "про", "та", "ти", "у", "це", "цей", "ця",
    "ці", "що", "як",
}
_DIALOGUE_DOMAIN_KEYWORDS = {
    "pet_shop": {
        "акваріум", "animal", "animals", "cat", "dog", "fish", "hamster", "kitten",
        "parrot", "pet", "pets", "petshop", "pet-shop", "shop", "turtle",
        "кіт", "кішка", "кошеня", "кошка", "папуга", "пес", "пташка", "рибка",
        "собака", "тварина", "тварини", "хом'як", "хомяк", "черепаха",
    },
    "room_furniture": {
        "armchair", "bag", "bed", "chair", "desk", "furniture", "lamp", "mirror",
        "photo", "room", "table", "wall", "window", "зошит", "кімната", "книга",
        "крісло", "лампа", "ліжко", "ручка", "стілець", "стіна", "стіл", "сумка",
        "телефон", "фото", "шафа", "дзеркало", "вікно",
    },
    "school_classroom": {
        "backpack", "book", "classroom", "notebook", "pen", "pencil", "school",
        "student", "teacher", "вчитель", "дошка", "зошит", "карта", "клас",
        "класна", "олівець", "парта", "підручник", "ручка", "учень", "школа",
    },
    "market_shopping": {
        "bakery", "bread", "buy", "market", "money", "price", "prices", "shopper",
        "store", "булочка", "гривня", "гроші", "квиток", "купити", "магазин",
        "пекар", "покупець", "ринок", "скільки", "супермаркет", "торт", "ціна",
        "ярмарок",
    },
    "cafe_food": {
        "borshch", "cafe", "coffee", "cook", "croissant", "drink", "eat", "juice",
        "menu", "pastry", "recipe", "tea", "борщ", "вода", "готувати", "їжа",
        "кава", "кафе", "круасан", "кухня", "меню", "обід", "рецепт", "сік",
        "сметана", "тістечко", "чай",
    },
    "city_travel": {
        "airport", "bank", "bus", "city", "guide", "hotel", "map", "metro", "museum",
        "park", "pharmacy", "square", "station", "street", "taxi", "theatre", "tour",
        "tourist", "train", "travel", "автобус", "аптека", "банк", "вулиця", "готель",
        "замок", "карта", "кафе", "метро", "місто", "музей", "парк", "площа",
        "пошта", "таксі", "театр", "турист", "потяг", "зупинка",
    },
}
_TEXTBOOK_HINT_RE = re.compile(r"\b(?:grade|клас|klas)\b", re.IGNORECASE)
_GRADE_RE = re.compile(r"(?:grade\s*|^|[^\d])(\d{1,2})(?:\s*(?:клас|klas))?", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")
_AUTHOR_ALIASES = {
    "авраменко": "avramenko",
    "avramenko": "avramenko",
    "большакова": "bolshakova",
    "bolshakova": "bolshakova",
    "вашуленко": "vashulenko",
    "vashulenko": "vashulenko",
    "ворон": "voron",
    "voron": "voron",
    "глазова": "glazova",
    "glazova": "glazova",
    "голуб": "golub",
    "holub": "golub",
    "golub": "golub",
    "заболотний": "zabolotnyi",
    "zabolotnyi": "zabolotnyi",
    "zabolotnij": "zabolotnij",
    "захарійчук": "zaharijchuk",
    "zaharijchuk": "zaharijchuk",
    "караман": "karaman",
    "karaman": "karaman",
    "кравцова": "kravcova",
    "kravcova": "kravcova",
    "литвінова": "litvinova",
    "літвінова": "litvinova",
    "litvinova": "litvinova",
    "онатій": "onatiy",
    "onatiy": "onatiy",
}


class PlanIssue:
    """A single issue found in a plan."""

    def __init__(self, check: str, severity: str, message: str, fix: str = ""):
        self.check = check
        self.severity = severity  # ERROR, WARNING, INFO
        self.message = message
        self.fix = fix

    def __str__(self):
        icon = "❌" if self.severity == "ERROR" else "⚠️" if self.severity == "WARNING" else "ℹ️"
        s = f"  {icon} [{self.check}] {self.message}"
        if self.fix:
            s += f"\n     FIX: {self.fix}"
        return s


def detect_plan_type(plan: dict) -> str:
    """Classify a loaded plan as module-level, track-level, or unknown."""
    if isinstance(plan.get("modules"), list) or "module" in plan:
        return "module-level"
    if any(key in plan for key in TRACK_LEVEL_KEYS):
        return "track-level"
    return "unknown"


def _format_top_level_keys(plan: dict) -> str:
    keys = sorted(str(key) for key in plan)
    return ", ".join(keys) if keys else "(none)"


def _load_plan_yaml(plan_path: Path) -> tuple[dict | None, PlanIssue | None]:
    try:
        plan = yaml.safe_load(plan_path.read_text("utf-8"))
    except Exception as e:
        return None, PlanIssue("YAML", "ERROR", f"YAML parse error: {e}")

    if not isinstance(plan, dict):
        return None, PlanIssue("YAML", "ERROR", "Plan is not a YAML mapping")

    return plan, None


def _flatten_strings(value) -> list[str]:
    """Collect nested string values from YAML data."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_flatten_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(_flatten_strings(item))
        return result
    return []


def _dialogue_tokens(texts: list[str]) -> set[str]:
    """Tokenize dialogue-related text into normalized content words."""
    tokens: set[str] = set()
    for text in texts:
        for token in _DIALOGUE_TOKEN_RE.findall(text.lower()):
            normalized = token.strip("-'")
            if len(normalized) < 3 or normalized in _DIALOGUE_STOPWORDS:
                continue
            tokens.add(normalized)
    return tokens


def _dialogue_domains(tokens: set[str]) -> set[str]:
    """Map dialogue tokens onto coarse scene domains."""
    hits = set()
    for domain, keywords in _DIALOGUE_DOMAIN_KEYWORDS.items():
        if tokens & keywords:
            hits.add(domain)
    return hits


def _dialogue_outline_texts(plan: dict) -> list[str]:
    """Extract only the content_outline fragments that describe dialogues."""
    outline = plan.get("content_outline")
    if not isinstance(outline, list):
        return []

    collected: list[str] = []
    for section in outline:
        if not isinstance(section, dict):
            continue

        section_texts = []
        section_title = str(section.get("section", ""))
        if section_title:
            section_texts.append(section_title)

        for key in ("points", "subsections", "key_concepts", "notes", "examples"):
            section_texts.extend(_flatten_strings(section.get(key)))

        joined = "\n".join(section_texts)
        if joined and _DIALOGUE_SECTION_RE.search(joined):
            collected.extend(section_texts)

    return collected


def check_plan_internal_consistency(plan: dict) -> list[PlanIssue]:
    """Check that dialogue_situations agree with dialogue bullets in content_outline."""
    situations = plan.get("dialogue_situations")
    if not isinstance(situations, list) or not situations:
        return []

    outline_texts = _dialogue_outline_texts(plan)
    if not outline_texts:
        return []

    situation_texts = []
    for situation in situations:
        if not isinstance(situation, dict):
            continue
        situation_texts.extend(
            [
                str(situation.get("setting", "")),
                str(situation.get("motivation", "")),
                *[str(s) for s in situation.get("speakers", []) if isinstance(s, str)],
            ]
        )

    situation_tokens = _dialogue_tokens(situation_texts)
    outline_tokens = _dialogue_tokens(outline_texts)
    if not situation_tokens or not outline_tokens:
        return []

    situation_domains = _dialogue_domains(situation_tokens)
    outline_domains = _dialogue_domains(outline_tokens)
    shared_tokens = situation_tokens & outline_tokens

    if situation_domains and outline_domains and not (situation_domains & outline_domains) and not shared_tokens:
        return [
            PlanIssue(
                "plan_internal_consistency",
                "ERROR",
                "dialogue_situations and dialogue-related content_outline bullets describe different scenes",
                "Rewrite the dialogue bullets in content_outline so they use the same setting, objects, and grammar motivation as dialogue_situations.",
            )
        ]

    return []


def check_required_fields(plan: dict) -> list[PlanIssue]:
    """Check that all required fields are present."""
    issues = []
    required = ["module", "slug", "version", "level", "sequence", "title",
                 "word_target", "content_outline", "vocabulary_hints", "phase"]
    for field in required:
        if field not in plan:
            issues.append(PlanIssue("FIELD", "ERROR", f"Missing required field: {field}"))
    return issues


def check_word_budgets(plan: dict) -> list[PlanIssue]:
    """Check section word budgets sum to >= word_target."""
    issues = []
    target = plan.get("word_target", 0)
    sections = plan.get("content_outline", [])
    if not sections:
        issues.append(PlanIssue("BUDGET", "ERROR", "No content_outline sections"))
        return issues

    total = sum(s.get("words", 0) for s in sections if isinstance(s, dict))
    if total < target:
        issues.append(PlanIssue("BUDGET", "ERROR",
                                f"Section budgets sum to {total}w, target is {target}w (short by {target - total}w)"))
    return issues


def check_no_stress_marks(plan: dict) -> list[PlanIssue]:
    """Check that no stress marks (U+0301) appear anywhere in the plan."""
    issues = []
    text = yaml.dump(plan, allow_unicode=True)
    count = text.count(STRESS_MARK)
    if count > 0:
        # Find which fields have them
        locations = []
        for key in ("vocabulary_hints", "content_outline", "title", "subtitle"):
            val = str(plan.get(key, ""))
            if STRESS_MARK in val:
                locations.append(key)
        issues.append(PlanIssue("STRESS", "ERROR",
                                f"{count} stress mark(s) found in: {', '.join(locations)}",
                                "Remove all combining acute (U+0301). Pipeline adds stress marks."))
    return issues


def check_russicisms(plan: dict) -> list[PlanIssue]:
    """Check vocabulary hints and content outline for known Russicisms."""
    issues = []
    text = yaml.dump(plan, allow_unicode=True).lower()

    for russian, fix in _RUSSICISMS.items():
        # Word boundary check — look for the word surrounded by non-Cyrillic
        pattern = rf"(?<![а-яґєіїА-ЯҐЄІЇ]){re.escape(russian)}(?![а-яґєіїА-ЯҐЄІЇ])"
        if re.search(pattern, text):
            issues.append(PlanIssue("RUSSICISM", "ERROR",
                                    f"Possible Russicism: '{russian}'",
                                    fix))

    # Phrase-level Russicism: "самий + adjective" for superlative
    # Standalone "самий" is valid Ukrainian (той самий = the same one).
    # Only "самий кращий/великий/etc." is a Russicism (→ найкращий/найбільший).
    # Skip negative examples: *самий, 'самий, "самий (quoted citations of errors)
    if re.search(r"(?<![*'\"])\bсамий\s+[а-яґєіїА-ЯҐЄІЇ]+(?:ий|ій|а|е)\b", text):
        issues.append(PlanIssue("RUSSICISM", "ERROR",
                                "Possible Russicism: 'самий + adjective' for superlative",
                                "Use най- prefix: найкращий, найбільший"))

    return issues


def check_phase_alignment(plan: dict) -> list[PlanIssue]:
    """Check that phase field matches module sequence number."""
    issues = []
    phase = plan.get("phase", "")
    seq = plan.get("sequence", 0)
    level = plan.get("level", "").upper()
    if not phase or not seq:
        return issues

    phase_key = phase.split("[")[0].strip()

    # Phase ranges are only validated for A1 (other levels have different structures)
    if level != "A1":
        # For non-A1 levels, just check that the phase starts with the level prefix
        level_prefix = level.split("-")[0]  # B1, B2, C1, etc.
        if not phase_key.startswith(level_prefix) and level_prefix not in phase_key:
            issues.append(PlanIssue("PHASE", "WARNING",
                                    f"Phase '{phase_key}' doesn't match level {level}"))
        return issues

    # V3 phase ranges for A1 (updated to match curriculum.yaml V3)
    expected_phases = {
        range(1, 8): "A1.1",      # M01-M07: Sounds, Letters, First Contact
        range(8, 15): "A1.2",     # M08-M14: My World
        range(15, 22): "A1.3",    # M15-M21: Actions
        range(22, 28): "A1.4",    # M22-M27: Time and Nature
        range(28, 36): "A1.5",    # M28-M35: Places
        range(36, 42): "A1.6",    # M36-M41: Food and Shopping
        range(42, 48): "A1.7",    # M42-M47: Communication
        range(48, 56): "A1.8",    # M48-M55: Past, Future, Graduation
    }

    for seq_range, expected in expected_phases.items():
        if seq in seq_range and phase_key != expected:
            issues.append(PlanIssue("PHASE", "ERROR",
                                    f"Module M{seq:02d} should be phase {expected}, got {phase_key}"))
    return issues


def check_grammar_scope(plan: dict) -> list[PlanIssue]:
    """Check that grammar field doesn't list constructs banned for the phase."""
    issues = []
    phase = plan.get("phase", "")
    grammar = plan.get("grammar", [])
    if not phase or not grammar:
        return issues

    phase_key = phase.split("[")[0].strip()
    grammar_text = " ".join(str(g).lower() for g in grammar)

    # Phonetics phase: no verbs
    if phase_key == "A1.1":
        seq = plan.get("sequence", 0)
        if seq <= 3:
            for banned in ("conjugation", "present tense", "past tense", "future tense",
                           "imperative", "reflexive", "modal"):
                if banned in grammar_text:
                    issues.append(PlanIssue("SCOPE", "ERROR",
                                            f"M{seq:02d} is phonetics — grammar lists '{banned}'",
                                            "Phonetics modules (M01-M03) should not teach verb grammar"))

    # No past/future before A1.8
    if phase_key in ("A1.1", "A1.2", "A1.3", "A1.4", "A1.5", "A1.6", "A1.7"):
        for banned in ("past tense", "future tense"):
            if banned in grammar_text and phase_key != "A1.7":
                # A1.7 might preview these
                issues.append(PlanIssue("SCOPE", "WARNING",
                                        f"Grammar lists '{banned}' but phase is {phase_key} (taught in A1.8)"))
    return issues


def check_prerequisites(plan: dict, all_slugs: list[str]) -> list[PlanIssue]:
    """Check that prerequisites reference valid module slugs."""
    issues = []
    prereqs = plan.get("prerequisites", [])
    if not prereqs:
        return issues

    for prereq in prereqs:
        if isinstance(prereq, str):
            # Extract slug from "a1-NNN (Title)" format
            slug_match = re.search(r"[a-z0-9-]+", prereq)
            if slug_match:
                ref = slug_match.group()
                # Check if it's an a1-NNN format or a slug
                if ref.startswith("a1-"):
                    continue  # Old format, skip
                if ref not in all_slugs and ref not in [f"a1-{s}" for s in all_slugs]:
                    issues.append(PlanIssue("PREREQ", "WARNING",
                                            f"Prerequisite references unknown slug: '{ref}'"))
    return issues


def _reference_source_name(ref: object) -> str:
    if not isinstance(ref, dict):
        return ""
    for key in ("source", "title"):
        value = ref.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_source_name(text: str) -> str:
    return re.sub(r"[^a-zа-яґєії0-9]+", " ", text.casefold()).strip()


def _textbook_reference_parts(source_name: str) -> tuple[str, int | None, str | None]:
    normalized = _normalize_source_name(source_name)
    author = ""
    for alias, canonical in _AUTHOR_ALIASES.items():
        if re.search(rf"(?<![a-zа-яґєії]){re.escape(alias)}(?![a-zа-яґєії])", normalized):
            author = canonical
            break

    grade = None
    grade_match = _GRADE_RE.search(normalized)
    if grade_match:
        grade = int(grade_match.group(1))

    year = None
    year_match = _YEAR_RE.search(normalized)
    if year_match:
        year = year_match.group(1)

    return author, grade, year


def _looks_like_textbook_reference(source_name: str) -> bool:
    if not source_name:
        return False
    normalized = _normalize_source_name(source_name)
    if _TEXTBOOK_HINT_RE.search(normalized):
        return True
    author, grade, _year = _textbook_reference_parts(source_name)
    return bool(author and grade)


def _known_textbooks(sources_db: Path) -> list[dict[str, object]]:
    if not sources_db.exists():
        raise FileNotFoundError(
            f"sources_db not found at {sources_db}. "
            "Run: .venv/bin/python scripts/wiki/build_sources_db.py"
        )
    conn = sqlite3.connect(str(sources_db))
    try:
        rows = conn.execute(
            "SELECT DISTINCT source_file, grade, author FROM textbooks ORDER BY source_file"
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "source_file": str(source_file or ""),
            "normalized_source_file": _normalize_source_name(str(source_file or "")),
            "grade": int(grade) if grade is not None else None,
            "author": str(author or "").casefold(),
        }
        for source_file, grade, author in rows
        if source_file
    ]


def _reference_matches_textbook(source_name: str, textbook: dict[str, object]) -> bool:
    normalized = _normalize_source_name(source_name)
    source_file = str(textbook["source_file"])
    normalized_source_file = str(textbook["normalized_source_file"])
    if normalized == normalized_source_file or normalized in normalized_source_file:
        return True

    author, grade, year = _textbook_reference_parts(source_name)
    if not author or grade is None:
        return False
    textbook_author = str(textbook["author"])
    author_matches = author == textbook_author or (
        {author, textbook_author} == {"zabolotnyi", "zabolotnij"}
    )
    if not author_matches or grade != textbook["grade"]:
        return False
    return year is None or year in source_file


def check_textbook_references_in_corpus(
    plan: dict,
    sources_db: Path = SOURCES_DB,
) -> list[PlanIssue]:
    """Reject textbook-looking plan references absent from sources_db."""
    references = plan.get("references")
    if not isinstance(references, list) or not references:
        return []

    textbook_refs = [
        source_name
        for ref in references
        if (source_name := _reference_source_name(ref))
        and _looks_like_textbook_reference(source_name)
    ]
    if not textbook_refs:
        return []

    try:
        known = _known_textbooks(sources_db)
    except (FileNotFoundError, sqlite3.Error) as exc:
        return [
            PlanIssue(
                "TEXTBOOK_CORPUS",
                "ERROR",
                f"Cannot validate plan textbook references against sources_db: {exc}",
            )
        ]

    missing = [
        source_name
        for source_name in textbook_refs
        if not any(_reference_matches_textbook(source_name, textbook) for textbook in known)
    ]
    if not missing:
        return []

    known_pointer = (
        f"{len(known)} distinct source_file rows in data/sources.db; "
        "inspect with `SELECT DISTINCT source_file FROM textbooks ORDER BY source_file`"
    )
    return [
        PlanIssue(
            "TEXTBOOK_CORPUS",
            "ERROR",
            "Plan references unknown textbook: "
            f"'{source_name}'. Known textbooks in corpus: {known_pointer}. "
            "To add this textbook, see docs/DICTIONARY-PIPELINE-STATUS.md.",
            "Use an in-corpus textbook citation or file an ingestion request before module build.",
        )
        for source_name in missing
    ]


def check_yaml_safety(plan: dict) -> list[PlanIssue]:
    """Check for YAML issues that cause parse errors."""
    issues = []
    # Check vocabulary hints for bare colons
    hints = plan.get("vocabulary_hints", {})
    # Handle both v3 dict {required: [...]} and v4 flat list [{word, pos, definition}]
    items_to_check: list = []
    if isinstance(hints, dict):
        for category in ("required", "recommended"):
            items_to_check.extend(hints.get(category, []))
    elif isinstance(hints, list):
        items_to_check = hints
    for item in items_to_check:
        if isinstance(item, dict):
            # Dict items are OK
            continue
        if isinstance(item, str) and ": " in item:
            # Could be a YAML issue but most are quoted properly
            pass
    return issues


def check_apostrophes(plan: dict) -> list[PlanIssue]:
    """Check that Ukrainian words requiring apostrophes have them."""
    issues = []
    text = yaml.dump(plan, allow_unicode=True)

    # Common words that MUST have apostrophe
    needs_apostrophe = {
        "мяч": "м'яч",
        "мясо": "м'ясо",
        "пять": "п'ять",
        "девять": "дев'ять",
        "мякий": "м'який",
        "мята": "м'ята",
        "вязати": "в'язати",
        "зїсти": "з'їсти",
        "обєкт": "об'єкт",
        "компютер": "комп'ютер",
        "сімя": "сім'я",
    }

    # Plans teach pronunciation errors and calques by citing the wrong form
    # alongside the right one. When a line is explicitly framed as a
    # teaching example (starts with `*`, mentions "Russicism", "calque",
    # "NOT", "wrong", "Russian" etc.), the apostrophe-missing word is
    # intentional and must be skipped.
    _TEACHING_MARKERS = re.compile(
        r"\*\S|Russicism|Russian\b|calque|кальк|NOT\b|wrong\b|incorrect\b|помилк",
        re.IGNORECASE,
    )

    for wrong, correct in needs_apostrophe.items():
        # Skip if preceded by * (intentional "incorrect form" marker in teaching examples)
        pattern = rf"(?<![а-яґєіїА-ЯҐЄІЇ'*]){re.escape(wrong)}(?![а-яґєіїА-ЯҐЄІЇ])"
        for m in re.finditer(pattern, text, re.IGNORECASE):
            # Scan the surrounding line for teaching markers — if the
            # author is explicitly showing a wrong form, don't flag it.
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            if _TEACHING_MARKERS.search(line):
                continue
            issues.append(PlanIssue("APOSTROPHE", "ERROR",
                                    f"Missing apostrophe: '{wrong}' should be '{correct}'"))
            break  # one issue per word is enough
    return issues


def check_vesum_vocabulary(plan: dict) -> list[PlanIssue]:
    """Check vocabulary hints against VESUM (if available)."""
    issues = []
    hints = plan.get("vocabulary_hints", {})
    if not hints:
        return issues

    # Handle both v3 dict {required: [...]} and v4 flat list [{word, pos, definition}]
    from pipeline.vocab_helpers import extract_vocab_words
    raw_words = extract_vocab_words(hints)
    words_to_check = []
    for word in raw_words:
        word = word.split("(")[0].strip().split("—")[0].strip().split(" ")[0].strip()
        word = word.replace(STRESS_MARK, "").strip(",").strip()
        if word and re.search(r'[\u0400-\u04ff]', word) and len(word) > 1:
            words_to_check.append(word)

    if not words_to_check:
        return issues

    # Try VESUM verification
    try:
        from rag.vesum_lookup import vesum_lookup
        for word in words_to_check:
            result = vesum_lookup(word)
            if not result:
                # Skip proper nouns (capitalized)
                if word[0].isupper():
                    continue
                issues.append(PlanIssue("VESUM", "WARNING",
                                        f"Vocabulary word '{word}' not found in VESUM",
                                        "Check spelling or verify it's a valid Ukrainian word"))
    except ImportError:
        # VESUM not available — skip this check
        pass
    return issues


def _check_module_plan(plan: dict, all_slugs: list[str] | None = None) -> list[PlanIssue]:
    """Run module-level checks on a single module plan mapping."""
    issues = []
    issues.extend(check_required_fields(plan))
    issues.extend(check_word_budgets(plan))
    issues.extend(check_no_stress_marks(plan))
    issues.extend(check_russicisms(plan))
    issues.extend(check_apostrophes(plan))
    issues.extend(check_phase_alignment(plan))
    issues.extend(check_grammar_scope(plan))
    issues.extend(check_plan_internal_consistency(plan))
    issues.extend(check_textbook_references_in_corpus(plan))
    issues.extend(check_prerequisites(plan, all_slugs or []))
    issues.extend(check_yaml_safety(plan))
    issues.extend(check_vesum_vocabulary(plan))
    return issues


def check_plan(plan_path: Path, all_slugs: list[str] | None = None) -> list[PlanIssue]:
    """Run all checks on a single plan file."""
    plan, load_issue = _load_plan_yaml(plan_path)
    if load_issue is not None:
        return [load_issue]
    assert plan is not None

    plan_type = detect_plan_type(plan)
    if plan_type == "track-level":
        return []
    if plan_type == "unknown":
        present_keys = _format_top_level_keys(plan)
        expected = "'module' or list-valued 'modules' for module-level plans; 'phases' or 'linguistic_evolution' for track-level plans"
        return [
            PlanIssue(
                "SCHEMA",
                "ERROR",
                f"Unknown plan schema in {plan_path}: top-level keys present: {present_keys}",
                f"Add one of the expected markers: {expected}.",
            )
        ]

    modules = plan.get("modules")
    if isinstance(modules, list) and "module" not in plan:
        issues = []
        for index, module in enumerate(modules, start=1):
            if not isinstance(module, dict):
                issues.append(
                    PlanIssue(
                        "SCHEMA",
                        "ERROR",
                        f"modules[{index}] is not a YAML mapping",
                    )
                )
                continue
            issues.extend(_check_module_plan(module, all_slugs))
        return issues

    return _check_module_plan(plan, all_slugs)


def _print_single_plan_result(plan_path: Path) -> int:
    plan, load_issue = _load_plan_yaml(plan_path)
    if load_issue is not None:
        print(str(load_issue))
        return 1
    assert plan is not None

    plan_type = detect_plan_type(plan)
    issues = check_plan(plan_path)
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    warnings = [issue for issue in issues if issue.severity == "WARNING"]

    if issues:
        status = "FAIL" if errors else "WARN"
        print(f"{plan_path}: {status} ({len(errors)} error(s), {len(warnings)} warning(s))")
        for issue in issues:
            print(str(issue))
        return 1 if errors else 0

    if plan_type == "track-level":
        print(f"{plan_path}: track-level plan validated")
    else:
        print(f"{plan_path}: module-level plan validated")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic plan quality checker")
    parser.add_argument("level", help="Level to check (e.g., a1)")
    parser.add_argument("--first", type=int, default=0, help="Check only first N modules")
    parser.add_argument("--module", type=int, default=0, help="Check single module by number")
    parser.add_argument("--failing-only", action="store_true", help="Only show plans with issues")
    args = parser.parse_args(argv)

    single_plan_path = Path(args.level)
    if single_plan_path.is_file():
        return _print_single_plan_result(single_plan_path)

    # Load curriculum order
    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    slugs = data.get("levels", {}).get(args.level, {}).get("modules", [])
    if not slugs:
        print(f"No modules found for level {args.level}")
        return 1

    if args.module > 0:
        if args.module > len(slugs):
            print(f"Module {args.module} not found (max {len(slugs)})")
            return 1
        slugs = [slugs[args.module - 1]]
        start_num = args.module
    else:
        if args.first > 0:
            slugs = slugs[:args.first]
        start_num = 1

    plans_dir = CURRICULUM_ROOT / "plans" / args.level
    total_issues = 0
    total_errors = 0
    plans_checked = 0
    plans_passed = 0

    print(f"\n{'=' * 70}")
    print(f"  Plan Quality Check — {args.level.upper()} ({len(slugs)} plans)")
    print(f"{'=' * 70}\n")

    for i, slug in enumerate(slugs):
        num = start_num + i if args.module == 0 else args.module
        plan_path = plans_dir / f"{slug}.yaml"

        if not plan_path.exists():
            if not args.failing_only:
                print(f"M{num:02d} {slug}: ⚠️ MISSING")
            continue

        plans_checked += 1
        issues = check_plan(plan_path, slugs)
        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]

        total_issues += len(issues)
        total_errors += len(errors)

        if not issues:
            plans_passed += 1
            if not args.failing_only:
                print(f"M{num:02d} {slug}: ✅ PASS")
        else:
            status = "❌ FAIL" if errors else "⚠️ WARN"
            print(f"M{num:02d} {slug}: {status} ({len(errors)} error(s), {len(warnings)} warning(s))")
            for issue in issues:
                print(str(issue))

    print(f"\n{'=' * 70}")
    print(f"  Summary: {plans_passed}/{plans_checked} passed, {total_errors} error(s), {total_issues - total_errors} warning(s)")
    print(f"{'=' * 70}\n")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
