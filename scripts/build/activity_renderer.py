"""Activity YAML → React JSX transformer.

Converts structured activity YAML (intermediate format from activity-v2.schema)
into React component JSX strings for MDX rendering.

Each activity type maps to a specific React component in site/src/components/.
The YAML uses an intermediate format — this module transforms it to match the
exact React component prop interfaces.

Issue: #1043
"""

from __future__ import annotations

import json
import re
from itertools import pairwise
from typing import Any

import regex


def render_activity_to_jsx(activity: dict, *, alphabet: bool = False) -> str:
    """Convert an activity YAML dict to React component JSX string.

    Args:
        activity: Parsed YAML dict matching activity-v2.schema.json
        alphabet: When True, Find-and-Fix chips are repaired for alphabet slugs.

    Returns:
        JSX string ready for insertion into MDX content.
        On unknown type, returns an HTML comment with the type name.
    """
    activity_type = activity.get("type", "")
    renderer = _RENDERERS.get(activity_type)
    if not renderer:
        return f"<!-- Unknown activity type: {activity_type} -->"
    if activity_type == "error-correction":
        return renderer(activity, alphabet=alphabet)
    return renderer(activity)


def get_required_imports(activities: list[dict]) -> list[str]:
    """Return deduplicated import statements for the activity types used.

    Args:
        activities: List of activity dicts (inline + workbook combined)

    Returns:
        List of import statement strings, sorted alphabetically.
    """
    seen: set[str] = set()
    imports: list[str] = []

    for act in activities:
        activity_type = act.get("type", "")
        component = _TYPE_TO_COMPONENT.get(activity_type)
        if component and component not in seen:
            seen.add(component)
            imports.append(
                f"import {component} from '@site/src/components/{component}';"
            )

    return sorted(imports)


# ---------------------------------------------------------------------------
# Type → Component name mapping
# ---------------------------------------------------------------------------

_TYPE_TO_COMPONENT: dict[str, str] = {
    "quiz": "Quiz",
    "fill-in": "FillIn",
    "match-up": "MatchUp",
    "group-sort": "GroupSort",
    "true-false": "TrueFalse",
    "error-correction": "ErrorCorrection",
    "anagram": "Anagram",
    "translate": "Translate",
    "unjumble": "Unjumble",
    "order": "Order",
    "cloze": "Cloze",
    "select": "Select",
    "grammar-identify": "GrammarIdentify",
    "observe": "Observe",
    "classify": "Classify",
    "mark-the-words": "MarkTheWords",
    "highlight-morphemes": "HighlightMorphemes",
    "image-to-letter": "ImageToLetter",
    "letter-grid": "LetterGrid",
    "watch-and-repeat": "WatchAndRepeat",
    "odd-one-out": "OddOneOut",
    "divide-words": "DivideWords",
    "count-syllables": "CountSyllables",
    "pick-syllables": "PickSyllables",
    "phrase-table": "PhraseTable",
    "critical-analysis": "CriticalAnalysis",
    "essay-response": "EssayResponse",
    "source-evaluation": "SourceEvaluation",
    "reading": "ReadingActivity",
    "comparative-study": "ComparativeStudy",
    "ritual-sequencing": "RitualSequencing",
    "variant-comparison": "VariantComparison",
    "motif-formula": "MotifFormula",
    "performance": "PerformanceActivity",
    "authorial-intent": "AuthorialIntent",
    "debate": "Debate",
    "etymology-trace": "EtymologyTrace",
    "translation-critique": "TranslationCritique",
    "transcription": "Transcription",
    "paleography-analysis": "PaleographyAnalysis",
    "dialect-comparison": "DialectComparison",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _j(value: Any) -> str:
    """JSON-encode a value for JSX embedding."""
    return json.dumps(value, ensure_ascii=False)


def _prop(name: str, value: Any) -> str:
    """Build a JSX prop string. Strings become {"..."}, others become {json}."""
    if isinstance(value, str):
        if "\n" in value:
            # MDX chokes on physical newlines inside double quotes. Use template literals.
            safe_val = value.replace('`', '\\`').replace('${', '\\${')
            return f' {name}={{`{safe_val}`}}'
        return f' {name}={{{_j(value)}}}'
    return f' {name}={{{_j(value)}}}'


def _opt_prop(name: str, value: Any | None, default: Any = None) -> str:
    """Build optional prop — returns empty string if value is None/default."""
    if value is None or value == default:
        return ""
    return _prop(name, value)


def _component(name: str, props: str) -> str:
    """Build a self-closing JSX component with client:only directive."""
    return f'<{name} client:only="react"{props} />'


# ---------------------------------------------------------------------------
# Core activity renderers
# ---------------------------------------------------------------------------

class QuizCorrectnessError(ValueError):
    """A quiz item's inputs contradict each other or name no correct option."""


def quiz_correct_indices(item: Any, index: int = 0) -> list[int]:
    """Return the indices of the correct option(s) of one quiz item.

    The schema lets three inputs name the answer: ``options[].correct`` flags,
    the ``correct`` index and the ``answer`` text. Every input present is a
    claim about which options are correct; the result is what all claims
    agree on. Contradicting claims, or no claim at all, raise
    ``QuizCorrectnessError`` -- the first choice is never assumed.
    """
    where = f"quiz item {index}"
    if not isinstance(item, dict):
        raise QuizCorrectnessError(f"{where} is not a mapping: {type(item).__name__}")
    options = item.get("options")
    if not isinstance(options, list) or not options:
        raise QuizCorrectnessError(f"{where} has no options list")
    texts = [opt.get("text") if isinstance(opt, dict) else opt for opt in options]

    claims: dict[str, set[int]] = {}
    flagged = {i for i, opt in enumerate(options) if isinstance(opt, dict) and opt.get("correct")}
    # Flags on a mix of bare strings and objects cannot mark the strings, so
    # they only count as a claim when they name something or cover every option.
    if flagged or all(isinstance(opt, dict) for opt in options):
        claims["options[].correct"] = flagged
    index_claim = item.get("correct")
    if type(index_claim) is int:
        if not 0 <= index_claim < len(options):
            raise QuizCorrectnessError(
                f"{where}: correct={index_claim} out of range (0-{len(options) - 1})"
            )
        claims["correct"] = {index_claim}
    answer = item.get("answer")
    if isinstance(answer, str):
        claims["answer"] = {i for i, text in enumerate(texts) if text == answer}

    if not claims:
        raise QuizCorrectnessError(
            f"{where} names no correct option (needs options[].correct, correct or answer)"
        )
    agreed = set.intersection(*claims.values())
    if not agreed:
        named = "; ".join(f"{name} -> {sorted(found) or 'none'}" for name, found in claims.items())
        raise QuizCorrectnessError(
            f"{where}: correct option is contradicted or unnamed ({named})"
        )
    return sorted(agreed)


class GroupSortNameError(ValueError):
    """A group-sort group carries two different category names."""


def group_sort_group_name(group: Any, index: int = 0) -> str:
    """Return the category name of one group-sort group (``label`` or ``name``).

    When both keys are present they must agree; otherwise whichever is present
    is used.
    """
    if not isinstance(group, dict):
        raise GroupSortNameError(f"group-sort group {index} is not a mapping: {type(group).__name__}")
    label, name = group.get("label"), group.get("name")
    if label and name and label != name:
        raise GroupSortNameError(
            f"group-sort group {index} has label {label!r} and name {name!r}; keep only one"
        )
    return label or name or ""


def _render_quiz(act: dict) -> str:
    """quiz → <Quiz questions={[...]} instruction="..." />

    YAML items have {question|prompt, options[], correct(index)|answer(text)}
    or options[{text, correct}]. React expects {question, options[{text, correct}],
    explanation?}.
    """
    questions = []
    for index, item in enumerate(act.get("items", [])):
        correct = set(quiz_correct_indices(item, index))
        options = [
            {"text": opt.get("text", "") if isinstance(opt, dict) else opt, "correct": i in correct}
            for i, opt in enumerate(item["options"])
        ]
        q: dict[str, Any] = {
            "question": item.get("question") or item.get("prompt", ""),
            "options": options,
        }
        if item.get("explanation"):
            q["explanation"] = item["explanation"]
        questions.append(q)

    props = _prop("questions", questions)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Quiz", props)


def _render_fill_in(act: dict) -> str:
    """fill-in → <FillIn items={[...]} instruction="..." />

    YAML: {sentence, answer, explanation, options?, mode?}
    React: same structure.
    """
    items = []
    for item in act.get("items", []):
        entry: dict[str, Any] = {
            "sentence": item.get("sentence", ""),
            "answer": item.get("answer", ""),
        }
        for key in ("options", "explanation", "mode"):
            if item.get(key):
                entry[key] = item[key]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("FillIn", props)


def _render_match_up(act: dict) -> str:
    """match-up → <MatchUp pairs={[...]} instruction="..." />"""
    pairs = [
        {"left": p.get("left", ""), "right": p.get("right", "")}
        for p in act.get("pairs", [])
    ]
    props = _prop("pairs", pairs)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("MatchUp", props)


def _render_group_sort(act: dict) -> str:
    """group-sort → <GroupSort groups={{...}} instruction="..." />

    YAML: groups[{label|name, items[]}]
    React: groups is {label: items[]} dict.
    """
    groups = {}
    for index, g in enumerate(act.get("groups", [])):
        groups[group_sort_group_name(g, index)] = g.get("items", [])

    props = _prop("groups", groups)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("GroupSort", props)


def _render_true_false(act: dict) -> str:
    """true-false → <TrueFalse items={[...]} instruction="..." />

    YAML: {statement, correct(bool), explanation?}
    React: {statement, isTrue, explanation?}
    """
    items = []
    for item in act.get("items", []):
        correct = item.get("correct")
        if correct is None:
            correct = item.get("is_true")
        if correct is None:
            correct = item.get("isTrue")
        if correct is None:
            correct = item.get("answer", False)
        entry: dict[str, Any] = {
            "statement": item.get("statement", ""),
            "isTrue": bool(correct),
        }
        if item.get("explanation"):
            entry["explanation"] = item["explanation"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("TrueFalse", props)


def _render_error_correction(act: dict, *, alphabet: bool = False) -> str:
    """error-correction → <ErrorCorrection> children (renders per-item).

    React ErrorCorrection uses children, but the wrapper also accepts structured
    items. We render as individual ErrorCorrectionItems with all props.
    Actually, looking at the component, it uses children. We'll render as
    a wrapper with JSON data prop for the items.
    """
    # ErrorCorrection takes children — we pass items as JSON for the generator
    items = []
    for item in act.get("items", []):
        correct_form, options = error_correction_render_values(
            item.get("sentence", ""),
            item.get("error", ""),
            item.get("correction") or item.get("answer", ""),
            item.get("options", []),
            alphabet=alphabet,
        )
        entry = {
            "sentence": item.get("sentence", ""),
            "errorWord": item.get("error", ""),
            "correctForm": correct_form,
            "options": unique_error_correction_options(options),
            "explanation": item.get("explanation", ""),
        }
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("ErrorCorrection", props)


_ERROR_CORRECTION_TOKEN_RE = re.compile(r"\w+(?:[ʼ’'-]\w+)*|[^\w\s]")
_SENTENCE_PUNCTUATION = frozenset({".", "?", "!"})


def _error_correction_middle_tokens(
    sentence: str, candidate: str
) -> tuple[list[str], list[str]]:
    """Return non-overlapping differing token spans for a sentence variant."""
    sentence_tokens = _ERROR_CORRECTION_TOKEN_RE.findall(sentence)
    candidate_tokens = _ERROR_CORRECTION_TOKEN_RE.findall(candidate)
    shared_prefix = 0
    limit = min(len(sentence_tokens), len(candidate_tokens))

    while (
        shared_prefix < limit
        and sentence_tokens[shared_prefix] == candidate_tokens[shared_prefix]
    ):
        shared_prefix += 1

    shared_suffix = 0
    while (
        shared_suffix < len(sentence_tokens) - shared_prefix
        and shared_suffix < len(candidate_tokens) - shared_prefix
        and sentence_tokens[-(shared_suffix + 1)]
        == candidate_tokens[-(shared_suffix + 1)]
    ):
        shared_suffix += 1

    sentence_end = len(sentence_tokens) - shared_suffix if shared_suffix else None
    candidate_end = len(candidate_tokens) - shared_suffix if shared_suffix else None
    return (
        sentence_tokens[shared_prefix:sentence_end],
        candidate_tokens[shared_prefix:candidate_end],
    )


def _word_tokens(tokens: list[str]) -> list[str]:
    """Discard standalone punctuation tokens for error-span comparison."""
    return [token for token in tokens if any(char.isalnum() or char == "_" for char in token)]


def _join_error_correction_tokens(tokens: list[str]) -> str:
    """Rebuild a compact replacement span from tokenized source text."""
    if not tokens:
        return ""

    no_space_before = frozenset(".,!?;:…)]}»")
    no_space_after = frozenset("([{«")
    output = tokens[0]
    for previous, token in pairwise(tokens):
        if token in no_space_before or previous in no_space_after:
            output += token
        else:
            output += f" {token}"
    return output


def _replacement_tokens_for_error(
    sentence: str,
    error: str,
    candidate: str,
    *,
    allow_unchanged: bool = False,
) -> tuple[list[str], list[str]] | None:
    """Find one prefix/suffix-preserving replacement anchored to ``error``."""
    sentence_tokens = _ERROR_CORRECTION_TOKEN_RE.findall(sentence)
    candidate_tokens = _ERROR_CORRECTION_TOKEN_RE.findall(candidate)
    error_words = _word_tokens(_ERROR_CORRECTION_TOKEN_RE.findall(error))
    sentence_word_indexes = [
        index for index, token in enumerate(sentence_tokens)
        if _word_tokens([token])
    ]
    sentence_words = [sentence_tokens[index] for index in sentence_word_indexes]
    if not error_words or len(error_words) > len(sentence_words):
        return None

    matches: list[tuple[list[str], list[str]]] = []
    width = len(error_words)
    for word_start in range(len(sentence_words) - width + 1):
        if sentence_words[word_start:word_start + width] != error_words:
            continue
        token_start = sentence_word_indexes[word_start]
        token_end = sentence_word_indexes[word_start + width - 1] + 1
        prefix = sentence_tokens[:token_start]
        suffix = sentence_tokens[token_end:]
        suffix_start = len(candidate_tokens) - len(suffix)
        if (
            len(candidate_tokens) < len(prefix) + len(suffix)
            or candidate_tokens[:len(prefix)] != prefix
            or candidate_tokens[suffix_start:] != suffix
        ):
            continue

        source_middle = sentence_tokens[token_start:token_end]
        candidate_middle = candidate_tokens[len(prefix):suffix_start]
        if candidate_middle and (
            allow_unchanged or candidate_middle != source_middle
        ):
            matches.append((source_middle, candidate_middle))

    unique_matches = {
        (tuple(source_middle), tuple(candidate_middle))
        for source_middle, candidate_middle in matches
    }
    if len(unique_matches) != 1:
        return None
    source_middle, candidate_middle = unique_matches.pop()
    return list(source_middle), list(candidate_middle)


def derive_error_correction_replacement(
    sentence: object,
    error: object,
    candidate: object,
    *,
    allow_unchanged: bool = False,
) -> str | None:
    """Extract a word or phrase replacement from a full-sentence variant.

    Source activities intentionally store a corrected sentence. The UI needs
    only the replacement for ``errorWord``. A replacement is safe only when
    the differing source span equals the authored error without punctuation.
    Ambiguous data stays untouched.
    """
    if not all(isinstance(value, str) for value in (sentence, error, candidate)):
        return None

    replacement_tokens = _replacement_tokens_for_error(
        sentence, error, candidate, allow_unchanged=allow_unchanged
    )
    if replacement_tokens is None:
        return None
    sentence_middle, candidate_middle = replacement_tokens
    if _word_tokens(sentence_middle) != _word_tokens(
        _ERROR_CORRECTION_TOKEN_RE.findall(error)
    ):
        return None

    replacement = _join_error_correction_tokens(candidate_middle)
    if replacement in _SENTENCE_PUNCTUATION:
        return None
    return replacement or None


def is_punctuation_error_correction(
    sentence: object,
    error: object,
    correction: object,
) -> bool:
    """Return whether this is the explicit sentence-punctuation pass-through."""
    if not all(isinstance(value, str) for value in (sentence, error, correction)):
        return False

    if correction.strip() in _SENTENCE_PUNCTUATION:
        return True

    sentence_middle, correction_middle = _error_correction_middle_tokens(
        sentence, correction
    )
    return (
        not _word_tokens(sentence_middle)
        and not _word_tokens(_ERROR_CORRECTION_TOKEN_RE.findall(error))
        and _join_error_correction_tokens(correction_middle) in _SENTENCE_PUNCTUATION
    )


def error_correction_render_values(
    sentence: object,
    error: object,
    correction: object,
    options: object,
    *,
    alphabet: bool = False,
    is_word: Any | None = None,
) -> tuple[object, object]:
    """Return ErrorCorrection props while preserving non-derivable input.

    ``alphabet=True`` repairs Find-and-Fix chips so VESUM-legal declined
    neighbors are not offered as wrong answers (#7994). Gate and MDX share
    this path so they cannot disagree.
    """
    correct_form = derive_error_correction_replacement(sentence, error, correction)
    # Alphabet assemble may omit ``options``; treat as [] so repair can fill chips.
    opts = options if isinstance(options, list) else ([] if alphabet else options)
    rendered_options = opts
    if isinstance(opts, list):
        rendered_options = [
            derive_error_correction_replacement(
                sentence, error, option, allow_unchanged=True
            ) or option
            for option in opts
        ]
    winner = correct_form or correction
    if alphabet and isinstance(rendered_options, list):
        from scripts.build.alphabet_modules import (
            repair_error_correction_options,
            vesum_is_word,
        )

        rendered_options = repair_error_correction_options(
            error,
            winner,
            rendered_options,
            is_word=is_word or vesum_is_word,
        )
    return winner, rendered_options


def unique_error_correction_options(options: object) -> object:
    """Drop exact repeat chips, first occurrence kept (a cloned winner is one choice)."""
    if not isinstance(options, list):
        return options
    out: list = []
    for option in options:
        if option not in out:
            out.append(option)
    return out


def _render_anagram(act: dict) -> str:
    """anagram → <Anagram items={[...]} instruction="..." />

    YAML: {letters[], answer, hint?}
    React AnagramItem: {scrambled(string, space-separated), answer, hint?}
    """
    items = []
    for item in act.get("items", []):
        letters = item.get("letters", [])
        entry: dict[str, Any] = {
            "scrambled": " ".join(letters),
            "answer": item.get("answer", ""),
        }
        if item.get("hint"):
            entry["hint"] = item["hint"]
        if item.get("explanation"):
            entry["explanation"] = item["explanation"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Anagram", props)


def _render_translate(act: dict) -> str:
    """translate → <Translate questions={[...]} instruction="..." />

    YAML: items[{source, answer?, alternatives?, options[{text, correct}]?}]
    React GeneratorTranslateQuestion: {source, options[{text, correct}]}
    """
    questions = []
    for item in act.get("items", []):
        options = item.get("options", [])
        if not options and item.get("answer"):
            # Build options from answer + alternatives
            correct = item["answer"]
            alts = item.get("alternatives", [])
            options = [{"text": correct, "correct": True}]
            for alt in alts:
                options.append({"text": alt, "correct": False})
        q: dict[str, Any] = {
            "source": item.get("source", ""),
            "options": options,
        }
        if item.get("explanation"):
            q["explanation"] = item["explanation"]
        questions.append(q)

    props = _prop("questions", questions)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Translate", props)


_UNJUMBLE_TOKEN_FIELDS = ("words", "jumbled", "prompt", "scrambled", "letters", "tiles")


def unjumble_tokens(item: dict, index: int = 0) -> list[str]:
    """Return the jumbled tokens of one unjumble item, whichever field carries them.

    A list is taken as-is; a string is split on ``/`` when present, else on
    whitespace.
    """
    for field_name in _UNJUMBLE_TOKEN_FIELDS:
        if field_name not in item:
            continue
        value = item[field_name]
        if isinstance(value, list):
            return [str(token) for token in value]
        if isinstance(value, str):
            separator = "/" if "/" in value else None
            return [token.strip() for token in value.split(separator) if token.strip()]
        raise TypeError(
            f"unjumble item {index} field {field_name!r} must be str or list, "
            f"got {type(value).__name__}"
        )
    raise KeyError(f"unjumble item {index} missing one of: words, jumbled, prompt, scrambled")


def _render_unjumble(act: dict) -> str:
    """unjumble → <Unjumble items={[...]} instruction="..." />

    YAML: {words|jumbled|prompt|scrambled, answer|correct_order[], hint?, explanation}
    React UnjumbleItem: {words(string, slash-separated), answer(string), hint?}
    """
    items = []
    for index, item in enumerate(act.get("items", [])):
        words = unjumble_tokens(item, index)
        correct = item.get("correct_order", [])
        answer = item.get("answer") or " ".join(str(c) for c in correct)
        entry: dict[str, Any] = {
            "words": " / ".join(words),
            "answer": str(answer),
        }
        if item.get("hint"):
            entry["hint"] = item["hint"]
        if item.get("explanation"):
            entry["explanation"] = item["explanation"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Unjumble", props)


def order_correct_indices(items: list, correct_order: list) -> list[int]:
    """Resolve an order item's ``correct_order`` to zero-based indices into ``items``.

    Writers (e.g. codex on m20 a1/my-morning act-3) commonly express the
    answer as the ordered ITEM STRINGS rather than integer indices into
    ``items``. When ``correct_order`` is an exact permutation of UNIQUE items,
    resolve each string to its index -- unambiguous, and a natural authoring
    form we accept rather than HARD-fail at MDX assembly.
    """
    str_items = [str(item) for item in items]
    if (all(isinstance(entry, str) for entry in correct_order)
            and len(str_items) == len(set(str_items))
            and len(correct_order) == len(str_items)
            and set(correct_order) == set(str_items)):
        correct_order = [str_items.index(entry) for entry in correct_order]
    if not all(isinstance(index, int) for index in correct_order):
        raise TypeError("order correct_order must contain integers")
    if any(index < 0 or index >= len(items) for index in correct_order):
        raise ValueError("order correct_order index out of range")
    return list(correct_order)


def _render_order(act: dict) -> str:
    """order → <Order items={[...]} correct_order={[...]} instruction="..." />

    For dialogue/sequence ordering. Items displayed shuffled, learner clicks to reorder.
    """
    items = act.get("items", [])
    props = _prop("items", items)
    props += _prop("correct_order", order_correct_indices(items, act.get("correct_order", [])))
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Order", props)


def _render_cloze(act: dict) -> str:
    """cloze → <Cloze passage="..." blanks={[...]} instruction="..." />

    YAML: {text, blanks[{id, answer, options[]}]?, options[]?}
    React: {passage, blanks[{index, options[], answer}]}
    """
    text = act.get("text", "")
    blanks = []
    for b in act.get("blanks", []):
        blanks.append({
            "index": b.get("id", 0),
            "options": b.get("options", []),
            "answer": b.get("answer", ""),
        })

    props = _prop("passage", text)
    if blanks:
        props += _prop("blanks", blanks)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Cloze", props)


def _render_select(act: dict) -> str:
    """select → <Select questions={[...]} instruction="..." />

    YAML: items[{question, options[{text, correct}]}]
    React GeneratorSelectQuestion: {question, options[{text, correct}]}
    """
    questions = []
    for item in act.get("items", []):
        q: dict[str, Any] = {
            "question": item.get("question", ""),
            "options": item.get("options", []),
        }
        if item.get("explanation"):
            q["explanation"] = item["explanation"]
        questions.append(q)

    props = _prop("questions", questions)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Select", props)


def _render_grammar_identify(act: dict) -> str:
    """grammar-identify → <GrammarIdentify title="..." items={[...]} />

    YAML: {word, task, options[]?, answer?}
    React GrammarItem: {text, form, answer}
    """
    items = []
    for item in act.get("items", []):
        items.append({
            "text": item.get("text") or item.get("sentence") or item.get("word", ""),
            "form": item.get("form") or item.get("task") or act.get("instruction", ""),
            "answer": item.get("answer", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("items", items)
    return _component("GrammarIdentify", props)


def _render_observe(act: dict) -> str:
    """observe → <Observe> children

    React Observe wraps children. We use the ObserveActivity sub-component
    which takes examples[] and prompt directly.
    """
    examples = act.get("examples", [])
    prompt = act.get("prompt", "")

    # ObserveActivity is a named export, but the default export (Observe)
    # wraps children. We'll render with examples/prompt as data props.
    props = _prop("examples", examples)
    props += _opt_prop("prompt", prompt)
    return _component("Observe", props)


def _render_classify(act: dict) -> str:
    """classify → <Classify categories={[...]} instruction="..." />

    YAML: {categories[{label, symbol_hint?, items[]}]}
    React ClassifyCategory: {label, symbolHint?, items[]}
    """
    categories = []
    for cat in act.get("categories", []):
        entry: dict[str, Any] = {
            "label": cat.get("label", ""),
            "items": cat.get("items", []),
        }
        if cat.get("symbol_hint"):
            entry["symbolHint"] = cat["symbol_hint"]
        categories.append(entry)

    props = _prop("categories", categories)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Classify", props)


def _render_mark_the_words(act: dict) -> str:
    """mark-the-words → <MarkTheWords> children

    React MarkTheWords expects children. We pass data as props.
    """
    props = _prop("text", act.get("text", ""))
    props += _prop("targetWords", act.get("target_words", []))
    props += _opt_prop("instruction", act.get("instruction"))
    props += _opt_prop("criteria", act.get("criteria"))
    return _component("MarkTheWords", props)


def _render_highlight_morphemes(act: dict) -> str:
    """highlight-morphemes → <HighlightMorphemes> children

    React expects children. We pass items as data props.
    """
    items = []
    for item in act.get("items", []):
        morphemes = [
            {"text": m.get("text", ""), "type": m.get("type", "")}
            for m in item.get("morphemes", [])
        ]
        if not morphemes and item.get("answer"):
            morphemes = [{"text": item["answer"], "type": item.get("type", "suffix")}]
        items.append({
            "word": item.get("word", ""),
            "morphemes": morphemes,
        })

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("HighlightMorphemes", props)


class ImageToLetterShapeError(ValueError):
    """An image-to-letter item carries neither the schema nor the legacy shape."""


_IMAGE_ASSET_PATH = re.compile(r"[A-Za-z0-9_./-]+\.(?:png|jpe?g|webp|svg)")
_FLAG = regex.compile(r"\p{Regional_Indicator}{2}")
_EMOJI_LEAD = regex.compile(r"\p{Extended_Pictographic}")
_EMOJI_PRESENTATION = regex.compile(r"\p{Emoji_Presentation}")
_VS16 = "\N{VARIATION SELECTOR-16}"


def _is_emoji_cluster(cluster: str) -> bool:
    """One grapheme cluster that renders as a colour picture (flag or emoji)."""
    if _FLAG.fullmatch(cluster):
        return True
    if not _EMOJI_LEAD.match(cluster):
        return False
    # Text-default pictographs (bare (c), (tm)) only render as emoji with U+FE0F.
    return bool(_EMOJI_PRESENTATION.match(cluster)) or cluster[1:2] == _VS16


def image_to_letter_image_kind(value: Any) -> str | None:
    """Classify an image-to-letter ``image`` as ``"asset"``, ``"emoji"`` or ``None`` (invalid).

    JSON Schema cannot express "exactly one emoji", so this function is the
    authoritative rule (the schema only states it in prose): an asset path, or
    exactly one extended grapheme cluster that is a Regional_Indicator pair
    (a flag) or starts with an Extended_Pictographic code point that renders
    as emoji -- Emoji_Presentation, or followed by U+FE0F -- so ZWJ sequences
    and skin tones qualify while bare text-default symbols such as the
    copyright sign do not.
    """
    if not isinstance(value, str) or not value:
        return None
    if _IMAGE_ASSET_PATH.fullmatch(value):
        return "asset"
    clusters = regex.findall(r"\X", value)
    if len(clusters) == 1 and _is_emoji_cluster(clusters[0]):
        return "emoji"
    return None


def image_to_letter_render_values(item: Any, index: int = 0) -> dict[str, Any]:
    """Normalise one image-to-letter item to the React ImageToLetterItem shape.

    Two authoring shapes reach the component ``{emoji, answer, distractors[]}``:
      - schema (activities-a1.schema.json): ``{image, letter, options?}``
      - legacy (direct track, audit fixers): ``{emoji, answer, distractors?}``

    ``options`` lists every choice and includes the letter, so the letter is
    removed from it; the component shuffles ``[answer, *distractors]``.
    """
    if not isinstance(item, dict):
        raise ImageToLetterShapeError(
            f"image-to-letter item {index} must be a mapping, got {type(item).__name__}"
        )
    emoji = item.get("emoji") or item.get("image")
    answer = item.get("answer") or item.get("letter")
    if not emoji or not answer:
        raise ImageToLetterShapeError(
            f"image-to-letter item {index} matches neither the schema shape "
            f"(image, letter, options) nor the legacy shape (emoji, answer, "
            f"distractors); keys present: {sorted(item)}"
        )
    if image_to_letter_image_kind(emoji) is None:
        raise ImageToLetterShapeError(
            f"image-to-letter item {index} image {emoji!r} is neither an asset path "
            f"(png/jpg/jpeg/webp/svg) nor exactly one emoji"
        )
    raw = item.get("distractors") if item.get("distractors") is not None else item.get("options")
    if "options" in item:
        options = item["options"]
        if not isinstance(options, (list, tuple)) or answer not in options:
            raise ImageToLetterShapeError(
                f"image-to-letter item {index} options do not contain letter {answer!r}"
            )
    distractors: list[str] = []
    for option in raw or []:
        if option != answer and option not in distractors:
            distractors.append(option)
    if not distractors:
        raise ImageToLetterShapeError(
            f"image-to-letter item {index} has no choice distinct from letter {answer!r}; "
            f"a learner needs at least one distractor"
        )
    entry: dict[str, Any] = {"emoji": emoji, "answer": answer, "distractors": distractors}
    for key in ("note", "explanation"):
        if item.get(key):
            entry[key] = item[key]
    return entry


def _render_image_to_letter(act: dict) -> str:
    """image-to-letter → <ImageToLetter items={[...]} />

    See :func:`image_to_letter_render_values` for the accepted item shapes.
    """
    items = [
        image_to_letter_render_values(item, index)
        for index, item in enumerate(act.get("items", []))
    ]
    props = _prop("items", items)
    props += _opt_prop("title", act.get("title"))
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("ImageToLetter", props)


def _render_letter_grid(act: dict) -> str:
    """letter-grid → <LetterGrid letters={[...]} />

    YAML and React use same field names: {upper, lower, name?, emoji?, key_word?}
    """
    letters = []
    for entry in act.get("letters", []):
        item: dict[str, Any] = {
            "upper": entry.get("upper", ""),
            "lower": entry.get("lower", ""),
        }
        for field in ("name", "emoji", "key_word", "note", "sound_type"):
            if entry.get(field):
                item[field] = entry[field]
        letters.append(item)

    props = _prop("letters", letters)
    props += _opt_prop("title", act.get("title"))
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("LetterGrid", props)


def _render_watch_and_repeat(act: dict) -> str:
    """watch-and-repeat → <WatchAndRepeat items={[...]} />

    YAML: items[{video, letter?, word?, sound?, note?, explanation?}]
    React WatchAndRepeatItem: {video, letter?, word?, sound?, note?, explanation?}
    """
    items = []
    for item in act.get("items", []):
        entry = {"video": item.get("video", "")}
        if item.get("letter"):
            entry["letter"] = item["letter"]
        if item.get("word"):
            entry["word"] = item["word"]
        if item.get("sound"):
            entry["sound"] = item["sound"]
        if item.get("note"):
            entry["note"] = item["note"]
        if item.get("explanation"):
            entry["explanation"] = item["explanation"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("title", act.get("title"))
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("WatchAndRepeat", props)


def _render_odd_one_out(act: dict) -> str:
    """odd-one-out → <OddOneOut items={[...]} />"""
    items = []
    for item in act.get("items", []):
        words = item.get("words") or item.get("options", [])
        correct = item.get("correct", 0)
        if item.get("answer") in words:
            correct = words.index(item["answer"])
        entry = {
            "words": words,
            "correct": correct,
            "explanation": item.get("explanation", ""),
        }
        items.append(entry)
    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("OddOneOut", props)


def _render_divide_words(act: dict) -> str:
    """divide-words → <DivideWords items={[...]} />"""
    items = []
    for item in act.get("items", []):
        entry = {"word": item.get("word", ""), "answer": item.get("answer", "")}
        if item.get("hint"):
            entry["hint"] = item["hint"]
        if item.get("explanation"):
            entry["explanation"] = item["explanation"]
        items.append(entry)
    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("DivideWords", props)


def _render_count_syllables(act: dict) -> str:
    """count-syllables → <CountSyllables items={[...]} />"""
    items = []
    for item in act.get("items", []):
        entry = {"word": item.get("word", ""), "correct": item.get("correct", 1)}
        if item.get("translation"):
            entry["translation"] = item["translation"]
        if item.get("explanation"):
            entry["explanation"] = item["explanation"]
        items.append(entry)
    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    if act.get("maxCount"):
        props += f' maxCount={{{act["maxCount"]}}}'
    return _component("CountSyllables", props)


def _render_pick_syllables(act: dict) -> str:
    """pick-syllables → <PickSyllables syllables={[...]} correctIndices={[...]} />"""
    props = _prop("syllables", act.get("syllables", []))
    props += _prop("correctIndices", act.get("correctIndices", []))
    props += f' category="{act.get("category", "закриті")}"'
    props += _opt_prop("instruction", act.get("instruction"))
    props += _opt_prop("explanation", act.get("explanation"))
    return _component("PickSyllables", props)


def _render_phrase_table(act: dict) -> str:
    """phrase-table → <PhraseTable groups={[...]} />

    YAML: groups[{label, phrases[str|{phrase, context?, emoji?}]}]
    React PhraseGroup: {label, function(=label), phrases[{phrase, context?, emoji?}]}
    """
    groups = []
    for g in act.get("groups", []):
        phrases = []
        for p in g.get("phrases", []):
            if isinstance(p, str):
                phrases.append({"phrase": p})
            else:
                entry = {"phrase": p.get("phrase", "")}
                if p.get("context"):
                    entry["context"] = p["context"]
                if p.get("emoji"):
                    entry["emoji"] = p["emoji"]
                phrases.append(entry)
        label = g.get("label") or g.get("function", "")
        groups.append({
            "label": label,
            "function": label,
            "phrases": phrases,
        })

    props = _prop("groups", groups)
    props += _opt_prop("title", act.get("title"))
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("PhraseTable", props)


# ---------------------------------------------------------------------------
# Seminar activity renderers
# ---------------------------------------------------------------------------

def _render_critical_analysis(act: dict) -> str:
    """critical-analysis → <CriticalAnalysis title="..." ... />"""
    props = _prop("title", act.get("instruction", act.get("prompt", "")))
    props += _opt_prop("targetText", act.get("target_text"))
    props += _opt_prop("questions", act.get("questions"))
    props += _opt_prop("modelAnswers", act.get("model_answers"))
    return _component("CriticalAnalysis", props)


def _render_essay_response(act: dict) -> str:
    """essay-response → <EssayResponse title="..." prompt="..." ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _prop("prompt", act.get("prompt", ""))
    props += _opt_prop("modelAnswer", act.get("model_answer"))

    # Convert rubric list to string if present
    rubric = act.get("rubric") or act.get("evaluation_criteria")
    if rubric and isinstance(rubric, list):
        if rubric and isinstance(rubric[0], dict):
            # Rubric with criteria/description/points
            rubric_lines = []
            for r in rubric:
                rubric_lines.append(
                    f"- {r.get('criteria', '')}: {r.get('description', '')}"
                )
            props += _prop("rubric", "\n".join(rubric_lines))
        else:
            props += _prop("rubric", "\n".join(f"- {c}" for c in rubric))

    return _component("EssayResponse", props)


def _render_source_evaluation(act: dict) -> str:
    """source-evaluation → <SourceEvaluation ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _prop("sourceText", act.get("source_text", ""))

    metadata = act.get("source_metadata")
    if metadata:
        props += _prop("sourceMetadata", metadata)

    props += _opt_prop("evaluationCriteria", act.get("criteria"))
    props += _opt_prop("guidingQuestions", act.get("guiding_questions"))
    props += _opt_prop("modelEvaluation", act.get("model_evaluation"))
    return _component("SourceEvaluation", props)


def _render_reading(act: dict) -> str:
    """reading → <ReadingActivity title="..." tasks={[...]} ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _opt_prop("text", act.get("passage"))
    props += _opt_prop("source", act.get("source"))
    props += _prop("tasks", act.get("questions", []))
    return _component("ReadingActivity", props)


def _render_comparative_study(act: dict) -> str:
    """comparative-study → <ComparativeStudy ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _opt_prop("itemsToCompare", act.get("items_to_compare"))
    props += _opt_prop("criteria", act.get("criteria"))
    props += _opt_prop("prompt", act.get("prompt"))
    props += _opt_prop("modelAnswer", act.get("model_answer"))
    return _component("ComparativeStudy", props)


def _render_authorial_intent(act: dict) -> str:
    """authorial-intent → <AuthorialIntent ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _prop("excerpt", act.get("excerpt", ""))
    props += _prop("questions", act.get("questions", []))
    props += _prop("modelAnswer", act.get("model_answer", ""))
    return _component("AuthorialIntent", props)


def _render_debate(act: dict) -> str:
    """debate → <Debate ... />

    YAML positions: [{label, arguments[]}]
    React Position: [{name, proponents, argument, evidence?, weaknesses?}]
    """
    positions = []
    for p in act.get("positions", []):
        args = p.get("arguments", [])
        positions.append({
            "name": p.get("label", ""),
            "proponents": "",
            "argument": "\n".join(args) if args else "",
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("debateQuestion", act.get("debate_question", ""))
    props += _prop("positions", positions)
    props += _opt_prop("analysisTasks", act.get("analysis_tasks"))
    return _component("Debate", props)


def _render_etymology_trace(act: dict) -> str:
    """etymology-trace → <EtymologyTrace ... />

    YAML stages: [{period, form, notes?}]
    React EtymologyItem: [{word, modern, evolution}]
    """
    items = []
    for stage in act.get("stages", []):
        items.append({
            "word": stage.get("period", ""),
            "modern": stage.get("form", ""),
            "evolution": stage.get("notes", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("items", items)
    return _component("EtymologyTrace", props)


def _render_translation_critique(act: dict) -> str:
    """translation-critique → <TranslationCritique ... />

    YAML translations: [{text, quality?, translator?, accuracy_score?, notes?}]
    React Translation: [{translator, text, accuracyScore, notes}]
    """
    translations = []
    for t in act.get("translations", []):
        translations.append({
            "translator": t.get("translator", ""),
            "text": t.get("text", ""),
            "accuracyScore": t.get("accuracy_score", 0),
            "notes": t.get("notes", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("original", act.get("original", ""))
    props += _prop("translations", translations)
    props += _opt_prop("focusPoints", act.get("focus_points"))
    return _component("TranslationCritique", props)


def _render_transcription(act: dict) -> str:
    """transcription → <Transcription ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _prop("original", act.get("original", ""))
    props += _prop("answer", act.get("answer", ""))
    props += _opt_prop("hints", act.get("hints"))
    return _component("Transcription", props)


def _render_paleography_analysis(act: dict) -> str:
    """paleography-analysis → <PaleographyAnalysis ... />

    YAML hotspots: [{x, y, label, explanation?}]
    React Hotspot: [{x, y, label, explanation}]
    """
    hotspots = []
    for h in act.get("hotspots", []):
        hotspots.append({
            "x": h.get("x", 0),
            "y": h.get("y", 0),
            "label": h.get("label", ""),
            "explanation": h.get("explanation", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("imageUrl", act.get("image_url", ""))
    props += _prop("hotspots", hotspots)
    return _component("PaleographyAnalysis", props)


def _render_dialect_comparison(act: dict) -> str:
    """dialect-comparison → <DialectComparison ... />

    YAML features: [{feature, variant_a, variant_b, explanation?}]
    React Feature: [{featureName, valueA, valueB, explanation}]
    """
    features = []
    for f in act.get("features", []):
        features.append({
            "featureName": f.get("feature", ""),
            "valueA": f.get("variant_a", ""),
            "valueB": f.get("variant_b", ""),
            "explanation": f.get("explanation", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _opt_prop("instruction", act.get("instruction"))
    props += _prop("textA", act.get("text_a", ""))
    props += _prop("textB", act.get("text_b", ""))
    props += _opt_prop("labelA", act.get("label_a"))
    props += _opt_prop("labelB", act.get("label_b"))
    props += _prop("features", features)
    return _component("DialectComparison", props)


def _render_ritual_sequencing(act: dict) -> str:
    """ritual-sequencing → <RitualSequencing ... />"""
    steps = act.get("steps") or act.get("items", [])
    correct_order = act.get("correct_order", [])
    if correct_order and all(isinstance(index, int) for index in correct_order):
        if min(correct_order) == 1 and max(correct_order) == len(steps):
            correct_order = [index - 1 for index in correct_order]
        elif min(correct_order) < 0 or max(correct_order) >= len(steps):
            raise ValueError(f"ritual-sequencing correct_order index out of bounds: {correct_order}")
    props = _prop("title", act.get("title", ""))
    props += _opt_prop("instruction", act.get("instruction"))
    props += _prop("steps", steps)
    props += _prop("correctOrder", correct_order)
    props += _opt_prop("modelAnswer", act.get("model_answer"))
    return _component("RitualSequencing", props)


def _render_variant_comparison(act: dict) -> str:
    """variant-comparison → <VariantComparison ... />"""
    props = _prop("title", act.get("title", ""))
    props += _opt_prop("instruction", act.get("instruction"))
    props += _prop("variants", act.get("variants", []))
    props += _prop("features", act.get("features", []))
    props += _opt_prop("prompt", act.get("prompt"))
    props += _opt_prop("modelAnswer", act.get("model_answer"))
    return _component("VariantComparison", props)


def _render_motif_formula(act: dict) -> str:
    """motif-formula → <MotifFormula ... />"""
    formulas = []
    for item in act.get("formulas", []):
        if isinstance(item, dict):
            formulas.append(item)
        else:
            formulas.append({"text": str(item)})
    props = _prop("title", act.get("title", ""))
    props += _opt_prop("instruction", act.get("instruction"))
    props += _prop("passage", act.get("passage") or act.get("text", ""))
    props += _prop("formulas", formulas)
    props += _opt_prop("prompt", act.get("prompt"))
    props += _opt_prop("modelAnswer", act.get("model_answer"))
    return _component("MotifFormula", props)


def _render_performance(act: dict) -> str:
    """performance → <PerformanceActivity ... />"""
    props = _prop("title", act.get("title", ""))
    props += _opt_prop("instruction", act.get("instruction"))
    props += _prop("prompt", act.get("prompt", ""))
    props += _opt_prop("fragment", act.get("fragment"))
    props += _opt_prop("selfCheck", act.get("self_check"))
    props += _opt_prop("showRecordButton", act.get("show_record_button"), True)
    props += _opt_prop("modelAnswer", act.get("model_answer"))
    return _component("PerformanceActivity", props)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_RENDERERS: dict[str, Any] = {
    # Core types
    "quiz": _render_quiz,
    "fill-in": _render_fill_in,
    "match-up": _render_match_up,
    "group-sort": _render_group_sort,
    "true-false": _render_true_false,
    "error-correction": _render_error_correction,
    "anagram": _render_anagram,
    "translate": _render_translate,
    "unjumble": _render_unjumble,
    "order": _render_order,
    "cloze": _render_cloze,
    "select": _render_select,
    "grammar-identify": _render_grammar_identify,
    "observe": _render_observe,
    "classify": _render_classify,
    "mark-the-words": _render_mark_the_words,
    "highlight-morphemes": _render_highlight_morphemes,
    "image-to-letter": _render_image_to_letter,
    "letter-grid": _render_letter_grid,
    "watch-and-repeat": _render_watch_and_repeat,
    "odd-one-out": _render_odd_one_out,
    "divide-words": _render_divide_words,
    "count-syllables": _render_count_syllables,
    "pick-syllables": _render_pick_syllables,
    "phrase-table": _render_phrase_table,
    # Seminar types
    "critical-analysis": _render_critical_analysis,
    "essay-response": _render_essay_response,
    "source-evaluation": _render_source_evaluation,
    "reading": _render_reading,
    "comparative-study": _render_comparative_study,
    "ritual-sequencing": _render_ritual_sequencing,
    "variant-comparison": _render_variant_comparison,
    "motif-formula": _render_motif_formula,
    "performance": _render_performance,
    "authorial-intent": _render_authorial_intent,
    "debate": _render_debate,
    "etymology-trace": _render_etymology_trace,
    "translation-critique": _render_translation_critique,
    "transcription": _render_transcription,
    "paleography-analysis": _render_paleography_analysis,
    "dialect-comparison": _render_dialect_comparison,
}
