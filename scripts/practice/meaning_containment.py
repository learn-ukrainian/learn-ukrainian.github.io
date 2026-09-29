"""Removal-only admission of meanings in the published practice deck (#9160).

This module never cleans a Ukrainian dictionary article into a new meaning.
An unsupported meaning is represented by two empty display fields so grammar,
stress and other independent practice can remain available.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path
from typing import Any

# Individually identified wrong senses and fragments in the three independent
# language reviews. Quarantine the displayed meaning, not the lexeme or its
# independently keyed non-meaning exercises.
REVIEWED_WRONG_LEMMAS = frozenset({
    "вгору", "тобто", "турецький", "тур", "перебувати", "запланований", "нощно",
    "садка", "прикладка", "сонорний", "зачин", "держава", "кілька", "постав",
    "хрещеник", "звільнення", "виснаження", "грецький", "надмірність",
    "плюнути", "горщик", "меткий", "цілина", "багацько", "друзяка",
    "славно", "хай", "комплект", "піт", "дрова", "гетьман", "хрестини",
    "чайна", "іній", "тихіший", "посинілий", "постарілий", "ялинковий",
    "доповідач", "ясна", "чхання",
    "абітурієнт", "гаразд", "відмова", "хвалити", "узутий", "шумно",
    "розуміння", "коробка", "кардіолог", "джаз", "над", "по", "битися",
    "проте", "малі", "недержавний", "путін", "адрес", "город",
    "гуртожиток", "дебати", "себе", "хтось", "ніхто",
})
_YEAR = re.compile(r"(?<!\d)(?:19[2-8]\d|199[01])(?!\d)")
_HEADER = re.compile(
    r"(?:^|\s)(?:Прикм\.|Присл\.|Дієприкм\.|Дієпр\.|Зменш\.|"
    r"Абстр\.\s*ім\.|Однокр\.|Стос\.|Пестл\.|Збірн\.|Жін\.|"
    r"Вищ\.\s*ст\.|Дія\s+за\s+знач\.|Стан\s+за\s+знач\.|"
    r"Те\s+саме,?\s+що|Див\.)\s",
    re.IGNORECASE,
)
_ARTICLE = re.compile(r"(?:\d+\s*》|\|\||◇|‖|[¹²³⁴⁵⁶⁷⁸⁹⁰]|\b[IVX]{1,3}\s*[-–])")
_QUOTE = re.compile(r"[«»“”„\"\[\]]")
_EN_META = re.compile(r"\b(?:Conjugation:|Synonym of|Initialism of|Augm|Sławno)\b", re.I)
_EN_FRAGMENT = re.compile(
    r"^(?:masculine|feminine|neuter|plural|comparative|superlative)\s+(?:possessive|form)\s+of\b"
    r"|^short form of\b|^with (?:pronoun|adverb)\b|^introducing (?:an? )?\w+ clause\b"
    r"|^indicating (?:time|place)\b|^used to (?:intensify|introduce|form)\b"
    r"|^(?:(?:a |an |the )?(?:(?:intensified|alternative(?: letter-case)?|diminutive|endearing|"
    r"dialectal|short|long|obsolete|archaic|rare|specific) )?|used as a friendly )form of\b"
    r"|^(?:(?:female|male) )?equivalent of\b"
    r"|^(?:(?:a |an )?specific )?spelling of\b"
    r"|^(?:synonym|initialism|abbreviation|inflection|variant|diminutive) of\b",
    re.I,
)
_EN_LABEL = re.compile(r"^(?:(?:numeral|adjective|adverb|noun|verb|pronoun|particle|anatomy)\s*:\s*|numeral\s+)", re.I)
_REVERSE_SOURCE_MARKERS = ("e2u", "reverse", "en→uk", "en->uk")
_SENSE_QUALIFIER = re.compile(r"^([A-Za-z][A-Za-z' -]*?) \(([a-z][a-z' -]*(?: [a-z][a-z' -]*){0,7})\)$")
_GRAMMAR_QUALIFIER = re.compile(r"\b(?:attributive|adjective|adverb|noun|verb|plural|singular|transitive|intransitive|dated|archaic)\b", re.I)


def _key(text: str) -> str:
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", text.casefold()).strip(" .,:;")


def _english_key(text: str) -> str:
    key = _key(text)
    for british, american in (("grey", "gray"), ("colour", "color"), ("centre", "center"),
                              ("theatre", "theater"), ("metre", "meter"), ("organise", "organize"),
                              ("realise", "realize"), ("practise", "practice")):
        key = re.sub(rf"\b{british}\b", american, key)
    return key


def english(text: str) -> bool:
    latin = sum("LATIN" in unicodedata.name(char, "") for char in text)
    cyrillic = sum("CYRILLIC" in unicodedata.name(char, "") for char in text)
    return latin > cyrillic


def english_head(text: str) -> str:
    """Take only an existing English head, dropping dictionary metadata.

    This never translates or repairs Ukrainian article text. A remaining
    cross-reference or grammatical instruction is not a learner meaning.
    """
    text = re.sub(r"\s+", " ", text).strip().strip("“”„\"'‘’")
    text = re.split(r"\bConjugation\s*:", text, maxsplit=1, flags=re.I)[0].strip()
    if any("CYRILLIC" in unicodedata.name(char, "") for char in text):
        return ""
    text = re.sub(r"^\d+\s*[.)]\s*", "", text)
    text = re.sub(r"^\([^)]*\)\s*", "", text)
    text = re.split(r"[;,(\[]", text, maxsplit=1)[0].strip()
    text = _EN_LABEL.sub("", text).strip(" .:;,-")
    if re.fullmatch(r"to [a-z-]+ once", text, re.I):
        text = text.removesuffix(" once")
    return "" if _EN_FRAGMENT.search(text) else text


def qualified_english_part(part: str) -> str:
    """Keep a literal source qualifier when it distinguishes a learner sense."""
    part = re.sub(r"\s+", " ", part).strip()
    match = _SENSE_QUALIFIER.fullmatch(part)
    if not match or _GRAMMAR_QUALIFIER.search(match.group(2)):
        return ""
    return part


def atlas_part_display(part: str) -> str:
    """A qualified part is atomic; never publish its ambiguous bare head."""
    if "(" in part or ")" in part:
        return qualified_english_part(part)
    return english_head(part)


def _balla_head(head: str) -> str:
    head = re.sub(r"^(?:to |be )", "", head.casefold()).strip()
    head = re.sub(r"^have (breakfast|lunch|dinner|supper)$", r"\1", head)
    return re.sub(r" (?:something|someone|somebody)$", "", head)


def split_english_alternatives(text: str) -> list[str]:
    """Split separators only outside balanced round or square qualifiers."""
    parts: list[str] = []
    start = 0
    stack: list[str] = []
    for index, char in enumerate(text):
        if char in "([":
            stack.append(")" if char == "(" else "]")
        elif char in ")]":
            if char == ")" and not stack and index > 0 and text[index - 1].isdigit():
                continue
            if not stack or stack[-1] != char:
                return [text]
            stack.pop()
        elif char in ",;/" and not stack:
            parts.append(text[start:index].strip())
            start = index + 1
    if stack:
        return [text]
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def atlas_english_parts(text: str) -> list[str]:
    """Carry an Atlas infinitive marker over a bare verb alternative."""
    parts = split_english_alternatives(text)
    if parts and parts[0].casefold().startswith("to "):
        return [parts[0], *("to " + part if re.fullmatch(r"[a-z-]+", part, re.I) else part
                            for part in parts[1:])]
    return parts


def candidate_balla_heads(entries: list[dict[str, Any]]) -> set[str]:
    """Collect every head the builder might select, including Ukrainian-Atlas rows."""
    heads: set[str] = set()
    for entry in entries:
        candidates: list[str] = atlas_english_parts(str(entry.get("gloss") or ""))
        enrichment = entry.get("enrichment")
        enrichment = enrichment if isinstance(enrichment, dict) else {}
        translation = enrichment.get("translation")
        translation = translation if isinstance(translation, dict) else {}
        source_en = translation.get("en")
        if isinstance(source_en, str):
            candidates.append(source_en)
        elif isinstance(source_en, list):
            candidates.extend(item for item in source_en if isinstance(item, str))
        senses = entry.get("senses")
        if isinstance(senses, list):
            for sense in senses:
                if not isinstance(sense, dict):
                    continue
                learner_en = sense.get("learner_en")
                if isinstance(learner_en, str):
                    candidates.append(learner_en)
                elif isinstance(learner_en, list):
                    candidates.extend(item for item in learner_en if isinstance(item, str))
        meaning = enrichment.get("meaning")
        if isinstance(meaning, dict) and "kaikki" in str(meaning.get("source") or "").casefold():
            definitions = meaning.get("definitions")
            if isinstance(definitions, list):
                candidates.extend(item for item in definitions if isinstance(item, str))
        heads.update(head for candidate in candidates for part in split_english_alternatives(candidate)
                     if (head := english_head(part)) and english(head))
    return heads


def load_balla_definitions(heads: set[str], path: Path) -> dict[str, list[str]]:
    """Read English-to-Ukrainian reverse evidence for the exact candidate heads."""
    if not heads:
        return {}
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as conn:
        return {
            head: [str(row[0]) for row in conn.execute(
                "SELECT definition FROM balla_en_uk WHERE word=? COLLATE NOCASE", (head,)
            )]
            for head in sorted({_balla_head(head) for head in heads if head})
        }


def _balla_maps_lemma(definitions: list[str], lemma: str) -> bool:
    # Balla examples use ~ for the English head. Their Ukrainian translations
    # are not direct head mappings (e.g. electron microscope = електронний ...).
    token = re.compile(rf"(?<![А-Яа-яІіЇїЄєҐґ]){re.escape(lemma)}(?![А-Яа-яІіЇїЄєҐґ])", re.I)
    return any(token.search(section.split("~", 1)[0].split(" — ", 1)[0])
               for definition in definitions for section in re.split(r"(?<!\w)\d+\)", definition))


def _lemma_forms(entry: dict[str, Any]) -> set[str]:
    forms = {str(entry.get("lemma") or "")}
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return forms
    morphology = enrichment.get("morphology")
    if isinstance(morphology, dict) and isinstance(morphology.get("forms"), list):
        forms.update(str(item.get("form") or "") for item in morphology["forms"] if isinstance(item, dict))
    pedagogy = enrichment.get("verb_pedagogy")
    partner = pedagogy.get("aspect_partner") if isinstance(pedagogy, dict) else None
    if isinstance(partner, dict) and isinstance(partner.get("lemma"), str):
        forms.add(partner["lemma"])
    cards = enrichment.get("definition_cards")
    if isinstance(cards, list):
        for card in cards:
            if not isinstance(card, dict) or str(card.get("id") or "").casefold() not in {"sum20", "vts"}:
                continue
            for definition in card.get("definitions") or []:
                if not isinstance(definition, str):
                    continue
                match = re.search(r"\bдив\.\s+([А-Яа-яІіЇїЄєҐґ\u0301]+)", definition, re.I)
                if match:
                    forms.add(_key(match.group(1)))
                lemma = str(entry.get("lemma") or "")
                if lemma.startswith("про") and "док." in definition[:100]:
                    forms.add(lemma[3:])
    return {form for form in forms if form}


def _balla_synonym_bridge(entry: dict[str, Any], definitions: list[str]) -> bool:
    """Confirm an older reverse synonym in this lemma's own forward definition."""
    enrichment = entry.get("enrichment")
    cards = enrichment.get("definition_cards") if isinstance(enrichment, dict) else None
    if not isinstance(cards, list):
        return False
    reverse_terms = {
        _key(word) for item in definitions for word in re.findall(
            r"[А-Яа-яІіЇїЄєҐґ\u0301]{6,}", item.split("~", 1)[0].split(" — ", 1)[0]
        )
    }
    reverse_terms.discard(_key(str(entry.get("lemma") or "")))
    for card in cards:
        if not isinstance(card, dict) or str(card.get("id") or "").casefold() not in {"sum20", "vts"}:
            continue
        for definition in card.get("definitions") or []:
            if not isinstance(definition, str):
                continue
            first_sense = re.split(r"\b2\s*[》.]", definition, maxsplit=1)[0]
            if reverse_terms & {_key(word) for word in re.findall(r"[А-Яа-яІіЇїЄєҐґ\u0301]{6,}", first_sense)}:
                return True
    return False


def independent_english_support(
    entry: dict[str, Any], displayed: str, balla: dict[str, list[str]], sense: dict[str, Any] | None = None,
) -> bool:
    """Require same-lemma evidence, including explicit source variants and recorded forms."""
    head = english_head(displayed)
    lookup = _balla_head(head)
    spellings = {lookup}
    if "grey" in lookup:
        spellings.add(lookup.replace("grey", "gray"))
    if "gray" in lookup:
        spellings.add(lookup.replace("gray", "grey"))
    definitions = [item for spelling in spellings for item in balla.get(spelling, [])]
    forms = _lemma_forms(entry)
    balla_matches = any(_balla_maps_lemma(definitions, form) for form in forms)
    enrichment = entry.get("enrichment")
    enrichment = enrichment if isinstance(enrichment, dict) else {}
    translation = enrichment.get("translation")
    translation = translation if isinstance(translation, dict) else {}
    source = str(translation.get("source") or "").casefold()
    candidates = translation.get("en")
    candidates = [candidates] if isinstance(candidates, str) else candidates
    candidates = candidates if isinstance(candidates, list) else []
    direct = any(token in source for token in ("dmklinger", "kaikki", "slovnyk.me")) and any(
        isinstance(candidate, str) and (
            _key(re.sub(r"^\s*\([^)]*\)\s*", "", candidate)) == _key(displayed)
            or ("(" not in displayed and english_candidates_support_display([candidate], displayed))
        ) for candidate in candidates
    )
    if sense is not None and any(token in str(sense.get("source") or "").casefold() for token in ("dmklinger", "kaikki")):
        sense_candidates = sense.get("learner_en")
        sense_candidates = [sense_candidates] if isinstance(sense_candidates, str) else sense_candidates
        if isinstance(sense_candidates, list):
            direct = direct or english_candidates_support_display(sense_candidates, displayed)
    meaning = enrichment.get("meaning")
    meaning = meaning if isinstance(meaning, dict) else {}
    definitions_en = meaning.get("definitions")
    if "kaikki" in str(meaning.get("source") or "").casefold() and isinstance(definitions_en, list):
        direct = direct or english_candidates_support_display(definitions_en, displayed)
    source_groups = [candidate for candidate in candidates if isinstance(candidate, str)]
    if isinstance(definitions_en, list) and "kaikki" in str(meaning.get("source") or "").casefold():
        source_groups.extend(item for item in definitions_en if isinstance(item, str))
    related_balla = any(
        english_candidates_support_display([candidate], displayed)
        and any(_balla_maps_lemma(balla.get(_balla_head(english_head(part)), []), form)
                for part in split_english_alternatives(candidate) for form in forms)
        for candidate in source_groups
    )
    if definitions and not balla_matches and not related_balla and not _balla_synonym_bridge(entry, definitions):
        return False
    return bool(balla_matches or related_balla or direct)


def _candidate_alternatives(candidate: str) -> set[str]:
    """Extract literal alternatives only; never synthesize a translation."""
    candidate = re.split(r"\s+Conjugation:", candidate, flags=re.I)[0]
    candidate = re.sub(r"^\s*\([^)]*\)\s*", "", candidate)
    if any("CYRILLIC" in unicodedata.name(char, "") for char in candidate):
        return set()
    alternatives = [english_head(part) for part in split_english_alternatives(candidate)]
    return {_english_key(part) for part in alternatives if part and english(part)}


def english_candidates_support_display(candidates: list[Any], display: str, *, allow_embedded: bool = False) -> bool:
    """The displayed head must be supported by an attributed candidate."""
    target = _english_key(display)
    if qualified_english_part(display) and any(
        isinstance(candidate, str) and _english_key(re.sub(r"^\s*\([^)]*\)\s*", "", candidate)) == target
        for candidate in candidates
    ):
        return True
    options = set().union(*(_candidate_alternatives(candidate) for candidate in candidates if isinstance(candidate, str)))
    if not target:
        return False
    if target in options:
        return True
    if not allow_embedded:
        return False
    if len(target) >= 4 and any(option.startswith(target + " ") for option in options):
        return True
    words = set(re.findall(r"[a-z]+", target)) - {"a", "an", "the", "to", "of", "be"}
    if not words:
        return False
    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        head = english_head(candidate)
        head_words = set(re.findall(r"[a-z]+", head.casefold()))
        all_words = set(re.findall(r"[a-z]+", candidate.casefold()))
        if len(words) == 1:
            word = next(iter(words))
            if re.search(rf"\bor\s+(?:[a-z]+\s+){{0,2}}{re.escape(word)}\b", head, re.I):
                return True
            continue
        if words <= all_words and words & head_words:
            return True
    return False


def _first_learner_head_supports(first: str, displayed: str) -> bool:
    if english_candidates_support_display([first], displayed, allow_embedded=True):
        return True
    if any(_english_key(part) == _english_key(displayed) for part in re.findall(r"\[([^]]+)\]", first)):
        return True
    first_verb = re.match(r"^to ([a-z-]+)\b", english_head(first), re.I)
    display_verb = re.match(r"^to ([a-z-]+)\b", english_head(displayed), re.I)
    return bool(first_verb and display_verb and first_verb.group(1).casefold() == display_verb.group(1).casefold())


def meaning_problem(text: str, lemma: str, sum11: list[str] | None = None) -> str | None:
    """Return the first reason a complete displayed field must be removed."""
    if not text.strip():
        return "missing"
    if lemma.casefold() in REVIEWED_WRONG_LEMMAS:
        return "reviewed_wrong_sense"
    if english(text) and (_EN_FRAGMENT.search(text) or _EN_LABEL.match(text)):
        return "dictionary_fragment"
    if english(text) and any("CYRILLIC" in unicodedata.name(char, "") or char.isdigit() for char in text):
        return "dictionary_fragment"
    if _YEAR.search(text):
        return "dated_citation"
    if ("(" in text or ")" in text) and not qualified_english_part(text):
        return "parenthesized_citation"
    if _QUOTE.search(text):
        return "example_quotation"
    if _ARTICLE.search(text) or _HEADER.search(text):
        return "dictionary_fragment"
    if _EN_META.search(text):
        return "dictionary_fragment"
    if not english(text):
        # A second sentence in a raw article is commonly an example or another
        # sense. Do not cut it into an invented Ukrainian definition.
        if re.search(r"[.!?]\s+\S", text) or re.match(r"\s*[А-ЯІЇЄҐ]{2,}\b", text):
            return "dictionary_fragment"
        if re.search(r"\b(?:приск\.|перен\.|заст\.|розм\.|діал\.|ч\.|ж\.|с\.)\s", text, re.I):
            return "dictionary_fragment"
    key = _key(text)
    if key and any(key == _key(definition) or (len(key) >= 24 and key in _key(definition)) for definition in sum11 or []):
        return "same_word_sum11"
    return None


def source_bound_meaning(
    entry: dict[str, Any], displayed: str, clean: str, sense: dict[str, Any] | None,
    sum11: list[str] | None = None, level: str | None = None,
    balla: dict[str, list[str]] | None = None,
) -> tuple[dict[str, str] | None, str | None]:
    """Admit only existing display text bound to an attributed matching field."""
    lemma = str(entry.get("lemma") or "")
    for field in (displayed, clean):
        problem = meaning_problem(field, lemma, sum11)
        if problem:
            return None, problem
    if english(displayed) != english(clean):
        return None, "field_language_mismatch"
    if sense is not None:
        source = str(sense.get("source") or "").strip()
        if english(displayed) and any(token in source.casefold() for token in _REVERSE_SOURCE_MARKERS):
            return None, "unsupported_english_source"
        if english(displayed) and not independent_english_support(entry, displayed, balla or {}, sense):
            return None, "unsupported_independent_head"
        field = "learner_en" if english(displayed) else "learner_uk"
        candidates = sense.get(field)
        if isinstance(candidates, str):
            candidates = [candidates]
        matched = isinstance(candidates, list) and (
            english_candidates_support_display(candidates, displayed)
            if english(displayed)
            else any(isinstance(candidate, str) and _key(displayed) == _key(candidate) for candidate in candidates)
        )
        if level == "A1" and english(displayed) and english(str(entry.get("gloss") or "")):
            matched = matched and _english_key(displayed) == _english_key(
                english_head(split_english_alternatives(str(entry["gloss"]))[0])
            )
        if source and matched and (english(displayed) or source.casefold() in {"sum20_vetted", "vts_vetted", "ulif_checked"}):
            return {"source": source, "field": f"senses.{field}"}, None
        return None, "unbound_sense"
    enrichment = entry.get("enrichment")
    enrichment = enrichment if isinstance(enrichment, dict) else {}
    if not english(displayed):
        # Legacy Ukrainian article text has no explicit sense ID. A verbatim,
        # single-definition card is the only safe non-derived legacy binding.
        cards = enrichment.get("definition_cards")
        if isinstance(cards, list):
            matches = [
                card for card in cards if isinstance(card, dict)
                and str(card.get("id") or "").casefold() in {"sum20", "vts"}
                and card.get("definitions") == [displayed]
            ]
            if len(matches) == 1 and _key(displayed) == _key(str(entry.get("gloss") or "")):
                return {"source": str(matches[0].get("source") or matches[0].get("id")),
                        "field": "enrichment.definition_cards.definitions"}, None
        return None, "unbound_ukrainian"
    translation = enrichment.get("translation")
    translation = translation if isinstance(translation, dict) else {}
    source = str(translation.get("source") or "").strip()
    if not source or any(token in source.casefold() for token in _REVERSE_SOURCE_MARKERS):
        return None, "unsupported_english_source"
    if not independent_english_support(entry, displayed, balla or {}):
        return None, "unsupported_independent_head"
    # A dictionary's reverse candidates cannot bind a Ukrainian display to a
    # sense. Existing English display text is the needed sense anchor.
    original = str(entry.get("gloss") or "")
    candidates = translation.get("en")
    if isinstance(candidates, str):
        candidates = [candidates]
    if not isinstance(candidates, list) or not english_candidates_support_display(
        candidates, displayed, allow_embedded=level not in {None, "A1"}
    ):
        return None, "unattributed_english"
    if english(original):
        # A translation-list sub-sense cannot displace the Atlas lexeme head.
        atlas_parts = atlas_english_parts(original)
        if level == "A1":
            atlas_parts = atlas_parts[:1]
        atlas_heads = [atlas_part_display(part) for part in atlas_parts]
        if not any(_english_key(displayed) == _english_key(head) for head in atlas_heads if head):
            return None, "unbound_english_sense"
        if source.casefold() == "learner_english_gloss" and candidates and not _first_learner_head_supports(
            candidates[0], displayed
        ):
            return None, "unbound_english_sense"
    else:
        # A Ukrainian lexeme gloss provides no machine-readable English sense
        # alignment. A single attributed translation head is the only safe
        # legacy anchor at the beginner levels; multi-sense lists stay withheld.
        heads = {_key(english_head(candidate)) for candidate in candidates if isinstance(candidate, str)}
        heads.discard("")
        if level not in {"A1", "A2"} or heads != {_key(displayed)}:
            return None, "unbound_english_sense"
    return {"source": source, "field": "enrichment.translation.en"}, None


def load_sum11_definitions(words: set[str], path: Path) -> dict[str, list[str]]:
    """Read selected same-word rows; a supplied invalid database is an error."""
    if not words:
        return {}
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as conn:
        definitions: dict[str, list[str]] = {}
        for word in sorted(words):
            # SQLite NOCASE folds ASCII only. Dictionary headwords can differ
            # from a displayed lemma in Ukrainian capitalization.
            variants = tuple(dict.fromkeys((word, word.casefold(), word.upper(), word.title())))
            # The installed word index is NOCASE; an IN query without its
            # collation scans the full table for every lemma.
            values: list[str] = []
            for variant in variants:
                rows = conn.execute("SELECT definition FROM sum11 WHERE word=? COLLATE NOCASE", (variant,))
                values.extend(str(row[0]) for row in rows)
            definitions[word] = list(dict.fromkeys(values))
        return definitions
