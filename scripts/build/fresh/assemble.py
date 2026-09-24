"""Assembler for fresh build engine Part E3a and E3c-1 (issues #8397, #8430, #8431 r3).

Pure functions for:
- Check 5: draft -> expanded document (plain forms only, step ids on units, provenance)
- Check 9: apply stress -> lesson-<n>.stressed.yaml, Slovnyk, Resursy, locks, frontmatter, render MDX
- Check 11: verify_shippable --fresh

Rule 3 compliance: Zero Cyrillic string literals in this module. All Ukrainian text
comes from records (pack, word store) or the writer's resolved draft.
Rule 4 (R-11) compliance: No forbidden paths.

Provenance Contract (E3c-1 / ADR-011 / Review Contract #8430):

Units and spans (r3 invariant):
- A provenance *unit* is the locator (tab, step, activity, item, block) — the same `unit` a
  resolution receipt names. Its final rendered text is what the renderer emits at that
  location (after stress and print substitution, with `{{uk:...}}` unwrapped and
  `{{gloss:W-n}}` replaced).
- Every expanded-document unit (one resolver unit) becomes exactly one span, in document
  order. `span` is the span's index within its unit; `start`/`end` are character offsets in
  the unit's final rendered text. Spans partition their unit: sorted by `start` they are
  contiguous, start at 0, and their texts concatenate byte for byte to the unit's rendered
  text (no trimming, no whitespace tolerance).
- `role` is the resolver role of the span's expanded unit (`narration`, `quoted_term`,
  `gloss_ref`, `record_print`, `error_text`, `item_option`, ...). Digest alignment uses it
  to reproduce the receipt token sequence per span (see scripts/review/digest/generator.py).
- Receipt offsets are relative to the plain (unstressed) text of the resolver unit, i.e. of
  the span; the digest converts them to unit-relative rendered offsets in one named function
  (`align_receipt_tokens`) before matching `[start, end)`.
- The renderer reports a rendered piece per expanded unit. A unit the renderer did not emit
  fails check 9 closed (`span_location_unrendered`); a rendered piece whose letters differ
  from the stressed unit text fails closed (`span_text_not_in_rendered_output`). No global
  search of the page string is used anywhere.
- Verification runs against what the page receives, i.e. the final MDX after every
  `generate_mdx` transform. The Urok renderer records the byte range of every unit it emits
  (`_UrokWriter` -> `LessonUnitMap`, scripts/generate_mdx/unit_map.py); `generate_mdx`
  carries that map through each transform of the Lesson tab and of the document (frontmatter
  parsing, section clean-up, readings insertion, YouTube embedding, inline activity
  injection, folk blocks, callouts, slug links, bad-form markers, HTML fixes, comment
  removal, story sections, dialogues, duplicate-H1 removal, heading emojis, tab strip and
  wrap, `normalize_mdx`): a unit whose bytes survive unchanged keeps its shifted location, a
  unit a transform removed or rewrote is marked lost with the transform's name. Check 9 then
  reads every unit back at its own location in the final MDX and fails closed: removed ->
  `span_location_unrendered`, rewritten -> `span_text_not_in_rendered_output` (engine layer,
  reason names the transform). Dialogue lines are emitted by the renderer as the page's
  DialogueBox component; their units are the escaped bytes inside the `exchanges` payload,
  decoded back at verification (`CODEC_JS_JSON_STRING`). Urok block text is taken from the
  draft with end-of-line whitespace dropped (`page_text`), the one normalization the page
  applies to prose, so a unit never claims bytes the page has no place for.
- Vpravy units are located in the component props the page's React components consume: the
  activity payload is parsed by `ActivityParser` and serialized by its `_activity_to_mdx`
  (the same call `generate_mdx` makes for every `INJECT_ACTIVITY` marker and for the Vpravy
  tab); the JSX block of every activity is tracked in the same map through the transforms,
  and the `JSON.parse(...)`/string props are read back (`component_props_from_jsx`) from the
  block as it stands in the final MDX. Each unit group (activity, item, block) must equal,
  byte for byte, the prop field that corresponds to its role (`page_field_text`: prompt,
  option n, answer, error text, explanation, instruction). A field the parser or serializer
  dropped or changed fails closed with `span_location_unrendered` (engine layer); a
  transform that rewrote the block fails closed with `span_text_not_in_rendered_output`.
  For every choice span with `is_key` the page's own key (the option flagged `correct`,
  `answer`/`correctForm` equality, `correct` index, `correctIndices`) must agree, else
  `span_key_not_on_page`.
- A string `answer` on quiz / multiple-choice / select / translate / odd-one-out that names
  one of the item's choices (check 4) is a key like the integer `correct`: it is no provenance
  unit, and the payload key is rewritten to the rendered text of the option it names (options
  are never stressed — resolver SKIPPED_ROLES — while an answer unit would be). A translate
  item without options keeps its answer text as a unit; the page offers it as the single
  correct option, where the unit is located.
- Slovnyk entries print the record's own lemma stress (never the resolver's selection), and
  Resursy titles print unstressed; those two tabs are compared accent-stripped against the
  stressed unit text, every other tab must match exactly. The one vpravy exception is the
  error-correction correction (`record_side: correct`): it prints the E- record's `correct`
  text as the pack has it (unstressed), because the ErrorCorrection component compares the
  option chips — never stressed, resolver SKIPPED_ROLES — to `correctForm` byte for byte.

Every span in the final lesson-<n>.provenance.yaml carries:
1. `record_kind` — for `source: record` spans, one of a closed set with its review fix layer:
   - "word"          -> "word_store" (W- prefix: word store records, paradigms, slovnyk entries, store form options,
                                      and `{{gloss:W-n}}` references, which print the record's lemma and gloss)
   - "quote"         -> "pack"       (T- prefix: textbook / literary quotes in urok)
   - "example"       -> "pack"       (EX- prefix: textbook / literary examples in urok)
   - "exercise_text" -> "pack"       (X- prefix: pack exercise records)
   - "error"         -> "pack"       (E- prefix: pack error records in vpravy)
   - "note"          -> "pack"       (N- prefix: style-guide note records)
   - "video"         -> "pack"       (V- prefix: video records in urok or resursy)
   - "resource"      -> "pack"       (cited text / resource records in resursy)
   - null / None     -> "regenerate_lesson" (writer prose)
   Derivation is strictly from the engine record id prefix / pack section, never from text.

2. `record_side` — for error-correction items:
   - The span holding the E- record's incorrect text:
     source="record", ref=<E-id>, record_kind="error", record_side="incorrect"
   - The correction/answer span holding the E- record's correct text:
     source="record", ref=<E-id>, record_kind="error", record_side="correct"
   - null / None elsewhere.
   Blame rule: R2b blames nothing with record_side: incorrect.

3. `option_origin` and `is_key` — for every learner choice span:
   - option_origin: "store" when choices come from engine store-generated form options
     (form-choice; ref carries word record id W-...).
   - option_origin: "writer_typed" otherwise.
   - is_key: true for correct choice(s), false for distractors.
   - null / None for non-choice spans.
   Blame rule: R2b blames nothing with option_origin: writer_typed and is_key: false.

Per-Type Key Rule Table (A1 learner choices):
---------------------------------------------------------------------------------------------------------
Activity Type       Choice Field     Key Identification Rule                     Check 4 Failure Reason
---------------------------------------------------------------------------------------------------------
quiz /              options          1. Dict options: option.correct is True     - No correct option: answer_key_missing
multiple-choice                      2. Int field: item.correct (index)          - Multiple correct options: answer_key_ambiguous
                                     3. Str field: item.answer (text)            - Index out of range: answer_index_out_of_range
                                                                                 - Text not in options: answer_not_in_options
                                                                                 - Text appears >1 in options: answer_key_ambiguous
                                                                                 - correct & answer conflict: answer_key_conflict
                                                                                 - Neither provided: answer_key_missing

fill-in             options          mode == "form-choice":                      - Invalid/missing form: form_choice_options_invalid
(form-choice)                        item.answer matches word form tags          - Duplicate options: form_choice_options_invalid
                                     option_origin: store, ref: word id          - Answer not in options: form_choice_options_invalid

fill-in             options          item.answer (text)                          - Answer not in options: answer_not_in_options
(orthography)                                                                    - Duplicate answer in options: answer_key_ambiguous

error-correction    options          item.correction or item.answer (text)       - Answer not in options: answer_not_in_options
(with choices)                                                                   - Duplicate answer in options: answer_key_ambiguous
                                                                                 - Sentence/error mismatch: error_text_mismatch
                                                                                 - Sentence error count != 1: error_text_ambiguous
                                                                                 - Pack record mismatch: error_ref_mismatch

image-to-letter     options          item.letter (text)                          - Letter not in options: answer_not_in_options
                                                                                 - Duplicate letter in options: answer_key_ambiguous

translate           options          option.correct is True on option dict       - No correct option: answer_key_missing

odd-one-out         words            1. item.correct (integer index)             - Index out of range: answer_index_out_of_range
                                     2. item.answer (word text)                  - Answer not in words: answer_not_in_options
                                                                                 - Duplicate answer in words: answer_key_ambiguous
                                                                                 - correct & answer conflict: answer_key_conflict
                                                                                 - Neither provided: answer_key_missing

pick-syllables      syllables        item/act.correctIndices (integer indices)   - correctIndices empty: answer_key_missing
                                                                                 - Index out of range: answer_index_out_of_range
                                                                                 - Duplicate indices: answer_key_ambiguous

select              options          option.correct is True on option dict       - Correct count < min_correct: select_correct_set_invalid
---------------------------------------------------------------------------------------------------------

Item 4 Implementation Choice (Rendered Text in Provenance):
The final lesson-<n>.provenance.yaml rewrites span text in-place from the renderer's own
per-unit rendered pieces (stressed text, printable form options, unwrapped `{{uk:...}}`,
replaced `{{gloss:W-n}}`, the Slovnyk lemma and the Resursy title). Rationale:
1. Single canonical source of truth for text across all spans.
2. Reviewer quote matching: findings quote directly from the rendered page with stress, so
   exact substring matching against span text is simple and consistent.
3. Downstream tooling (e.g. digest generator, review validators) reads span["text"] without
   schema branching or duplicate keys.
4. Avoids redundant text fields on 99% of spans that do not change under print substitution,
   preserving byte-stability and minimal file footprint.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.path_guard import checked_existing_path
from scripts.curriculum.evidence import lesson_lock, lock
from scripts.curriculum.evidence.sources import Sources
from scripts.curriculum.learner_state.immersion import compute_lesson_immersion_band
from scripts.curriculum.learner_state.planned import PlannedStateError, planned_state
from scripts.curriculum.resolver import codes as resolver_codes
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument, ResolverError
from scripts.curriculum.resolver.stream import resolve
from scripts.generate_mdx.atlas_links import atlas_href_for
from scripts.generate_mdx.converters import (
    DIALOGUE_BOX_CLOSING_LINE,
    DIALOGUE_BOX_DEFAULT_TITLE,
    DIALOGUE_BOX_PAYLOAD_PREFIX,
    DIALOGUE_BOX_PAYLOAD_SUFFIX,
    dialogue_box_header_lines,
)
from scripts.generate_mdx.core import generate_mdx
from scripts.generate_mdx.unit_map import (
    CODEC_JS_JSON_STRING,
    CODEC_PLAIN,
    LOST_REMOVED,
    LessonUnitMap,
    UnitMapError,
    encode_js_json_string,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPANDED_SCHEMA_PATH = REPO_ROOT / "schemas" / "lesson-expanded-v1.schema.json"
PROVENANCE_SCHEMA_PATH = REPO_ROOT / "schemas" / "lesson-provenance-v1.schema.json"

_CACHED_EXPANDED_VALIDATOR: Draft202012Validator | None = None
_CACHED_PROVENANCE_VALIDATOR: Draft202012Validator | None = None

# Failure codes
EXAMPLE_NOT_FOUND = "example_not_found"
TEXT_NOT_FOUND = "text_not_found"
PARADIGM_NOT_FOUND = "paradigm_not_found"
WORD_NOT_FOUND = "word_not_found"
FORM_NOT_FOUND = "form_not_found"
VIDEO_NOT_FOUND = "video_not_found"
ACTIVITY_NOT_FOUND = "activity_not_found"
DRAFT_STATUS_NOT_OK = "draft_status_not_ok"
PRIOR_PLANS_MISSING = "prior_plans_missing"
LOCK_CHECK_FAILED = "lock_check_failed"
LESSON_LOCK_ENTRY_MISSING = "lesson_lock_entry_missing"
LESSON_LOCK_MISMATCH = "lesson_lock_mismatch"
IMMERSION_BAND_FAILED = "immersion_band_failed"
STREAM_BLOCKED = "stream_blocked"


class AssemblerError(Exception):
    """Failure during lesson assembly."""

    def __init__(self, code: str, message: str, layer: str = "pack") -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.layer = layer


def get_expanded_validator(schema_path: Path | None = None) -> Draft202012Validator:
    global _CACHED_EXPANDED_VALIDATOR
    if _CACHED_EXPANDED_VALIDATOR is None:
        path = schema_path or checked_existing_path(REPO_ROOT, EXPANDED_SCHEMA_PATH, "schemas")
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        _CACHED_EXPANDED_VALIDATOR = Draft202012Validator(schema)
    return _CACHED_EXPANDED_VALIDATOR


def get_provenance_validator(schema_path: Path | None = None) -> Draft202012Validator:
    global _CACHED_PROVENANCE_VALIDATOR
    if _CACHED_PROVENANCE_VALIDATOR is None:
        path = schema_path or checked_existing_path(REPO_ROOT, PROVENANCE_SCHEMA_PATH, "schemas")
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        _CACHED_PROVENANCE_VALIDATOR = Draft202012Validator(schema)
    return _CACHED_PROVENANCE_VALIDATOR


def derive_record_kind(ref: str | None, tab: str | None = None) -> str:
    """Derive closed-set record_kind from record identifier prefix and context.

    Emitted set from evidence schemas:
      W-  -> word
      EX- -> example
      X-  -> exercise_text
      E-  -> error
      N-  -> note
      V-  -> video
      T-  -> resource (resursy tab) or quote (urok tab)
    Any unknown prefix fails with unknown_record_prefix (layer engine).
    """
    if not ref:
        raise AssemblerError("unknown_record_prefix", "record identifier is missing", layer="engine")
    if ref.startswith("W-"):
        return "word"
    if ref.startswith("EX-"):
        return "example"
    if ref.startswith("X-"):
        return "exercise_text"
    if ref.startswith("E-"):
        return "error"
    if ref.startswith("N-"):
        return "note"
    if ref.startswith("V-"):
        return "video"
    if ref.startswith("T-"):
        if tab == "resursy":
            return "resource"
        return "quote"
    raise AssemblerError("unknown_record_prefix", f"unknown record prefix in identifier {ref!r}", layer="engine")


def _resolve_single_quiz_key(item: dict[str, Any], opts: list[Any]) -> int | None:
    dict_correct = [i for i, opt in enumerate(opts) if isinstance(opt, dict) and opt.get("correct") is True]
    has_int = "correct" in item and isinstance(item["correct"], int)
    has_str = "answer" in item and isinstance(item["answer"], str)
    if len(dict_correct) > 1:
        raise AssemblerError("answer_key_ambiguous", "multiple options marked correct in quiz", layer="writer")
    resolved: set[int] = set()
    if has_int:
        resolved.add(item["correct"])
    if has_str:
        offered = [opt.get("text") if isinstance(opt, dict) else opt for opt in opts]
        matched = [i for i, opt_txt in enumerate(offered) if opt_txt == item["answer"]]
        if len(matched) > 1:
            raise AssemblerError("answer_key_ambiguous", "answer matches multiple options", layer="writer")
        if matched:
            resolved.add(matched[0])
    if len(dict_correct) == 1:
        resolved.add(dict_correct[0])
    if len(resolved) > 1:
        raise AssemblerError("answer_key_conflict", "conflicting quiz answer keys", layer="writer")
    return next(iter(resolved)) if resolved else None


def strip_accents(text: str) -> str:
    """Strip combining grave (U+0300) and combining acute (U+0301) accents."""
    return text.replace("\u0300", "").replace("\u0301", "")


_UK_MARKUP_RE = re.compile(r"\{\{uk:([^{}\u0300\u0301]+)\}\}")
_GLOSS_MARKUP_RE = re.compile(r"^\{\{gloss:(W-[0-9]+)\}\}$")
_GLOSS_INLINE_RE = re.compile(r"\{\{gloss:(W-[0-9]+)\}\}")

# Check 9 failure codes for the provenance/render agreement (fail closed, engine layer).
SPAN_LOCATION_UNRENDERED = "span_location_unrendered"
SPAN_TEXT_NOT_IN_RENDERED_OUTPUT = "span_text_not_in_rendered_output"
SPAN_KEY_NOT_ON_PAGE = "span_key_not_on_page"
PROVENANCE_UNIT_COUNT_MISMATCH = "provenance_unit_count_mismatch"

# Choice types whose string `answer` names one of the item's choices (check 4) — a key, never
# printed text. A translate item may carry no options; its `answer` is then answer text.
STRING_KEY_ANSWER_TYPES = frozenset({"quiz", "multiple-choice", "select", "translate", "odd-one-out"})


def string_key_answer(act_type: str, item: dict[str, Any]) -> str | None:
    """The item's string `answer` when it is a key naming one of its choices, else None."""
    if act_type not in STRING_KEY_ANSWER_TYPES:
        return None
    answer = item.get("answer")
    choices = item.get("words") if act_type == "odd-one-out" else item.get("options")
    if not isinstance(answer, str) or not isinstance(choices, list):
        return None
    plain = [c.get("text") if isinstance(c, dict) else c for c in choices]
    return answer if plain.count(answer) == 1 else None


def gloss_replacer(words_store: dict[str, Any]) -> Any:
    """Return the renderer's `{{gloss:W-n}}` -> "lemma (gloss)" substitution for one word store.

    The returned callable takes a `_GLOSS_INLINE_RE` match (group 1 is the W- id) and prints the
    record's lemma with its sense gloss; the whole marker is consumed.
    """
    words_by_id = {w["id"]: w for w in words_store.get("words", []) if isinstance(w, dict) and "id" in w}

    def replace_gloss(match: re.Match[str]) -> str:
        wid = match.group(1)
        w_rec = words_by_id.get(wid)
        if w_rec:
            lem = w_rec.get("lemma", "")
            gl = w_rec.get("sense_gloss") or w_rec.get("gloss_en") or ""
            return f"{lem} ({gl})" if gl else lem
        return wid

    return replace_gloss


def render_unit_piece(text: str, replace_gloss: Any) -> str:
    """The renderer's output for one expanded unit's (stressed) text.

    Unwraps `{{uk:...}}` and replaces `{{gloss:W-n}}`; applied per unit so a block's output
    is by construction the concatenation of its units' pieces (the unit->output mapping the
    provenance file is verified against).
    """
    return _GLOSS_INLINE_RE.sub(replace_gloss, _UK_MARKUP_RE.sub(r"\1", text))


# A component prop as `_activity_to_mdx` emits it: `name={JSON.parse(`...`)}` (a JSON payload
# escaped for a template literal by `_dump_safe_json`), `name={"..."}` (a `json.dumps` string)
# or `name="..."` (an `_escape_jsx` string, whose only decoded entity is `&quot;`).
_JSX_PROP_RE = re.compile(
    r'([A-Za-z_][A-Za-z0-9_]*)=(?:\{JSON\.parse\(`((?:[^`\\]|\\.)*)`\)\}|\{("(?:[^"\\]|\\.)*")\}|"([^"]*)")',
    re.DOTALL,
)
_TEMPLATE_ESCAPE_RE = re.compile(r"\\(.)", re.DOTALL)


def component_props_from_jsx(jsx: str) -> dict[str, Any]:
    """Read back the props of the component JSX one activity renders to.

    This is the payload the page's React component receives: `_dump_safe_json` doubles
    backslashes and escapes backticks and `${` for the template literal, which the JS engine
    cooks back to the `json.dumps` text before `JSON.parse`; string props are `json.dumps`
    strings or JSX attribute strings (`&quot;` decoded, no backslash escapes).
    """
    props: dict[str, Any] = {}
    for match in _JSX_PROP_RE.finditer(jsx):
        name, template, json_str, jsx_str = match.groups()
        if template is not None:
            props[name] = json.loads(_TEMPLATE_ESCAPE_RE.sub(r"\1", template))
        elif json_str is not None:
            props[name] = json.loads(json_str)
        else:
            props[name] = jsx_str.replace("&quot;", '"')
    return props


# Where each unit block lives in the component props, per activity type: the prop holding the
# item list, then the item field per block role. `opt` names the list field of learner choices
# and, for dict choices, the text key. Types absent here produce no vpravy units.
_PAGE_ITEM_LIST: dict[str, str] = {
    "quiz": "questions",
    "multiple-choice": "questions",
    "select": "questions",
    "translate": "questions",
    "true-false": "items",
    "fill-in": "items",
    "error-correction": "items",
    "image-to-letter": "items",
    "odd-one-out": "items",
    "unjumble": "items",
    "anagram": "items",
    "divide-words": "items",
}
# An answer block whose text the page carries only as the single option it flags correct.
_KEY_OPTION = "__key_option__"
_PAGE_ITEM_FIELDS: dict[str, dict[str, Any]] = {
    "quiz": {"prompt": "question", "explanation": "explanation", "opt": ("options", "text")},
    "multiple-choice": {"prompt": "question", "explanation": "explanation", "opt": ("options", "text")},
    "select": {"prompt": "question", "explanation": "explanation", "opt": ("options", "text")},
    # A translate item without options: the parser offers the answer text as the one correct option.
    "translate": {"prompt": "source", "answer": _KEY_OPTION, "explanation": "explanation", "opt": ("options", "text")},
    "true-false": {"prompt": "statement", "explanation": "explanation"},
    "fill-in": {"prompt": "sentence", "answer": "answer", "explanation": "explanation", "opt": ("options", None)},
    "error-correction": {
        "prompt": "sentence",
        "error": "errorWord",
        "answer": "correctForm",
        "explanation": "explanation",
        "opt": ("options", None),
    },
    "image-to-letter": {"explanation": "explanation", "opt": ("options", None)},
    "odd-one-out": {"prompt": "prompt", "explanation": "explanation", "opt": ("words", None)},
    "unjumble": {"prompt": "jumbled", "answer": "answer"},
    "anagram": {"answer": "answer"},
    "divide-words": {"answer": "answer"},
}
# Activity-level blocks (item is None): the prop of the same name; pick-syllables choices.
_PAGE_ACTIVITY_FIELDS: dict[str, dict[str, Any]] = {
    "pick-syllables": {"instruction": "instruction", "explanation": "explanation", "opt": ("syllables", None)},
}
_OPT_BLOCK_RE = re.compile(r"^opt_([0-9]+)$")


def _prop_text(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _option_text(choices: Any, index: int, text_key: str | None) -> str | None:
    if not isinstance(choices, list) or not 0 <= index < len(choices):
        return None
    choice = choices[index]
    if text_key is not None:
        return _prop_text(choice.get(text_key)) if isinstance(choice, dict) else None
    return _prop_text(choice)


def page_option_is_key(
    act_type: str, props: dict[str, Any], item_idx: int | None, opt_idx: int, *, key_index: int | None = None
) -> bool | None:
    """Whether the page flags option `opt_idx` as a correct choice, or None when not derivable."""
    if item_idx is None:
        if act_type == "pick-syllables":
            indices = props.get("correctIndices")
            return opt_idx in indices if isinstance(indices, list) else None
        return None
    items = props.get(_PAGE_ITEM_LIST.get(act_type, ""))
    if not isinstance(items, list) or not 0 <= item_idx < len(items) or not isinstance(items[item_idx], dict):
        return None
    item = items[item_idx]
    if act_type in ("quiz", "multiple-choice", "select", "translate"):
        choices = item.get("options")
        if not isinstance(choices, list) or not 0 <= opt_idx < len(choices) or not isinstance(choices[opt_idx], dict):
            return None
        return choices[opt_idx].get("correct") is True
    if act_type == "fill-in":
        return _option_text(item.get("options"), opt_idx, None) == item.get("answer")
    if act_type == "error-correction":
        return _option_text(item.get("options"), opt_idx, None) == item.get("correctForm")
    if act_type == "odd-one-out":
        return item.get("correct") == opt_idx
    if act_type == "image-to-letter" and isinstance(item.get("answer"), str) and "options" not in item:
        # The component offers `[answer, *distractors]`; the located field already encodes the key.
        return opt_idx == key_index
    return None


def page_field_text(
    act_type: str,
    props: dict[str, Any],
    item_idx: int | None,
    block: int | str,
    *,
    key_index: int | None = None,
) -> str | None:
    """The text the page component receives at the field a unit block describes, or None.

    None means the component receives no such field (dropped by the parser or the serializer,
    an out-of-range option, an unknown activity type); the caller fails closed. `key_index` is
    the index of the item's key option per provenance (needed where the component splits the
    choices into an answer and distractors).
    """
    block_key = str(block)
    opt_match = _OPT_BLOCK_RE.match(block_key)
    if item_idx is None:
        if block_key == "instruction":
            return _prop_text(props.get("instruction"))
        fields = _PAGE_ACTIVITY_FIELDS.get(act_type, {})
        if opt_match and "opt" in fields:
            list_name, text_key = fields["opt"]
            return _option_text(props.get(list_name), int(opt_match.group(1)), text_key)
        prop_name = fields.get(block_key)
        return _prop_text(props.get(prop_name)) if prop_name else None

    list_name = _PAGE_ITEM_LIST.get(act_type)
    fields = _PAGE_ITEM_FIELDS.get(act_type)
    if list_name is None or fields is None:
        return None
    items = props.get(list_name)
    if not isinstance(items, list) or not 0 <= item_idx < len(items) or not isinstance(items[item_idx], dict):
        return None
    item = items[item_idx]
    if opt_match:
        if "opt" not in fields:
            return None
        opt_idx = int(opt_match.group(1))
        choices_name, text_key = fields["opt"]
        located = _option_text(item.get(choices_name), opt_idx, text_key)
        if located is None and act_type == "image-to-letter" and key_index is not None:
            # The ImageToLetter component offers `[answer, *distractors]`: the key is the answer
            # field, distractor n is the n-th non-key choice.
            if opt_idx == key_index:
                return _prop_text(item.get("answer"))
            distractors = item.get("distractors")
            distractor_idx = opt_idx - (1 if key_index < opt_idx else 0)
            return _option_text(distractors, distractor_idx, None) if isinstance(distractors, list) else None
        return located
    prop_name = fields.get(block_key)
    if prop_name == _KEY_OPTION:
        choices_name, text_key = fields["opt"]
        choices = item.get(choices_name)
        keyed = (
            [c for c in choices if isinstance(c, dict) and c.get("correct") is True]
            if isinstance(choices, list)
            else []
        )
        return _prop_text(keyed[0].get(text_key)) if len(keyed) == 1 else None
    return _prop_text(item.get(prop_name)) if prop_name else None


def locate_units_in_component_props(
    stressed_doc: dict[str, Any],
    engine_pieces: dict[int, str],
    parsed_activities: dict[str, Any],
    page_jsx: dict[str, list[str]],
    *,
    spans: list[dict[str, Any]] | None = None,
) -> dict[int, str]:
    """Locate every vpravy unit in the props the page component receives.

    `engine_pieces` is the engine's own unit->text mapping for the activity payload it handed
    to the parser (`apply_stress_to_activities`); `parsed_activities` maps activity id to the
    parsed `ActivityParser` object (its type); `page_jsx` maps activity id to the component
    JSX block(s) of that activity as they stand in the final MDX (tracked by `generate_mdx`
    through its transforms, see `scripts/generate_mdx/unit_map.py`). For each unit group
    (activity, item, block) the concatenation of its pieces must equal the corresponding prop
    field of every block, byte for byte; otherwise the group's first unit fails closed with
    `span_location_unrendered`. Returns the located pieces keyed by unit index.
    """
    props_by_activity: dict[str, list[dict[str, Any]]] = {}
    groups: dict[tuple[Any, ...], list[int]] = {}
    for idx, unit in enumerate(stressed_doc.get("units", [])):
        if unit.get("tab") == "vpravy":
            loc_key = (unit.get("tab"), unit.get("step"), unit.get("activity"), unit.get("item"), unit.get("block"))
            groups.setdefault(loc_key, []).append(idx)

    # The provenance key per (activity, item): the option index whose spans carry is_key: true.
    key_index_by_item: dict[tuple[Any, Any], int | None] = {}
    if spans is not None:
        keyed: dict[tuple[Any, Any], set[int]] = {}
        for loc_key in groups:
            _tab, _step, act_id, item_idx, block = loc_key
            opt_match = _OPT_BLOCK_RE.match(str(block))
            if opt_match and any(spans[i].get("is_key") is True for i in groups[loc_key] if i < len(spans)):
                keyed.setdefault((act_id, item_idx), set()).add(int(opt_match.group(1)))
        for item_key, indices_set in keyed.items():
            key_index_by_item[item_key] = next(iter(indices_set)) if len(indices_set) == 1 else None

    located: dict[int, str] = {}
    for loc_key, indices in groups.items():
        _tab, _step, act_id, item_idx, block = loc_key
        first = indices[0]
        act_obj = parsed_activities.get(act_id)
        if act_obj is None:
            raise AssemblerError(
                SPAN_LOCATION_UNRENDERED,
                f"the renderer emitted nothing for unit {first} at {loc_key}: activity {act_id!r} is not on the page",
                layer="engine",
            )
        act_type = str(getattr(act_obj, "type", ""))
        if act_id not in props_by_activity:
            blocks = page_jsx.get(str(act_id)) or []
            if not blocks:
                raise AssemblerError(
                    SPAN_LOCATION_UNRENDERED,
                    f"the renderer emitted nothing for unit {first} at {loc_key}: no {act_type} component for "
                    f"activity {act_id!r} is on the page",
                    layer="engine",
                )
            props_by_activity[act_id] = [component_props_from_jsx(block) for block in blocks]
        pieces = []
        for idx in indices:
            if idx not in engine_pieces:
                raise AssemblerError(
                    SPAN_LOCATION_UNRENDERED,
                    f"the renderer emitted nothing for unit {idx} at {loc_key}",
                    layer="engine",
                )
            pieces.append(engine_pieces[idx])
        expected = "".join(pieces)
        key_index = key_index_by_item.get((act_id, item_idx))
        for props in props_by_activity[act_id]:
            field = page_field_text(act_type, props, item_idx, block, key_index=key_index)
            if field is None:
                raise AssemblerError(
                    SPAN_LOCATION_UNRENDERED,
                    f"unit {first} at {loc_key}: the {act_type} component receives no {block!r} field for item "
                    f"{item_idx} (expected {expected!r})",
                    layer="engine",
                )
            if field != expected:
                raise AssemblerError(
                    SPAN_LOCATION_UNRENDERED,
                    f"unit {first} at {loc_key}: the {act_type} component receives {field!r} in its {block!r} "
                    f"field, not the unit text {expected!r}",
                    layer="engine",
                )
            opt_match = _OPT_BLOCK_RE.match(str(block))
            span_is_key = spans[first].get("is_key") if spans is not None and first < len(spans) else None
            if opt_match and isinstance(span_is_key, bool):
                page_is_key = page_option_is_key(
                    act_type, props, item_idx, int(opt_match.group(1)), key_index=key_index
                )
                if page_is_key is not None and page_is_key != span_is_key:
                    raise AssemblerError(
                        SPAN_KEY_NOT_ON_PAGE,
                        f"unit {first} at {loc_key}: provenance marks is_key={span_is_key} but the {act_type} "
                        f"component flags this choice {'correct' if page_is_key else 'not correct'}",
                        layer="engine",
                    )
        for idx, piece in zip(indices, pieces, strict=True):
            located[idx] = piece
    return located


@dataclass(frozen=True)
class CheckResult:
    check: int
    passed: bool
    step: str | None = None
    activity: str | None = None
    token: str | None = None
    reason: str | None = None
    layer: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"check": self.check, "passed": self.passed}
        if self.step is not None:
            result["step"] = self.step
        if self.activity is not None:
            result["activity"] = self.activity
        if self.token is not None:
            result["token"] = self.token
        if self.reason is not None:
            result["reason"] = self.reason
        if self.layer is not None:
            result["layer"] = self.layer
        return result


_TRAILING_LINE_WHITESPACE_RE = re.compile(r"[ \t]+$", re.MULTILINE)


def page_text(text: str) -> str:
    """Draft or record text as the page can carry it.

    Whitespace at the end of a line is dropped (the site's markdown normalizer strips it,
    MD009); nothing else changes. Urok block text is taken this way at assembly so a unit
    never claims bytes the page has no place for. Vpravy text is not normalized: it reaches
    the page inside component props, where every byte is kept.
    """
    return _TRAILING_LINE_WHITESPACE_RE.sub("", text)


def _split_inline_spans(text: str, default_role: str) -> list[tuple[str, str]]:
    """Split text with inline markup into (role, text) spans.

    Matches {{uk:...}} as quoted_term and {{gloss:W-...}} as gloss_ref.
    All other text receives default_role.
    """
    pattern = re.compile(r"(\{\{uk:[^{}\u0300\u0301]+\}\}|\{\{gloss:W-[0-9]+\}\})")
    parts = pattern.split(text)
    spans: list[tuple[str, str]] = []
    uk_re = re.compile(r"^\{\{uk:([^{}\u0300\u0301]+)\}\}$")
    gloss_re = re.compile(r"^\{\{gloss:(W-[0-9]+)\}\}$")

    for part in parts:
        if not part:
            continue
        uk_match = uk_re.match(part)
        if uk_match:
            spans.append(("quoted_term", strip_accents(uk_match.group(1))))
            continue
        gloss_match = gloss_re.match(part)
        if gloss_match:
            spans.append(("gloss_ref", strip_accents(part)))
            continue
        spans.append((default_role, part))

    return spans


def assemble_expanded_document(
    draft: dict[str, Any],
    plan: dict[str, Any],
    pack: dict[str, Any],
    words_store: dict[str, Any],
    level: str,
    slug: str,
    lesson_n: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Assemble lesson draft into expanded document and provenance structures.

    Returns (expanded_doc_dict, provenance_dict).
    Every unit carries 'step' (plan step id, or None for tabs without steps).
    Plain forms only: quotes, examples, paradigms, glosses have accents stripped.
    Fails closed with named AssemblerError codes on missing records.
    """
    status = draft.get("status")
    if status != "ok":
        raise AssemblerError(DRAFT_STATUS_NOT_OK, f"draft status is {status!r}, expected 'ok'")

    lesson_entry: dict[str, Any] = {}
    for entry in plan.get("lessons", []):
        if isinstance(entry, dict) and entry.get("n") == lesson_n:
            lesson_entry = entry
            break
    if not lesson_entry:
        raise AssemblerError("lesson_not_found", f"lesson {lesson_n} not found in plan")

    words_by_id: dict[str, dict[str, Any]] = {}
    for w in words_store.get("words", []):
        if isinstance(w, dict) and "id" in w:
            words_by_id[w["id"]] = w

    texts_by_id: dict[str, dict[str, Any]] = {}
    for t in pack.get("texts", []):
        if isinstance(t, dict) and "id" in t:
            texts_by_id[t["id"]] = t

    examples_by_id: dict[str, dict[str, Any]] = {}
    for ex in pack.get("examples", []):
        if isinstance(ex, dict) and "id" in ex:
            examples_by_id[ex["id"]] = ex

    videos_by_id: dict[str, dict[str, Any]] = {}
    for v in pack.get("videos", []):
        if isinstance(v, dict) and "id" in v:
            videos_by_id[v["id"]] = v

    paradigms_by_id: dict[str, dict[str, Any]] = {}
    for st in lesson_entry.get("steps", []):
        if isinstance(st, dict) and "paradigm" in st and isinstance(st["paradigm"], dict):
            pid = st["paradigm"].get("id")
            if pid:
                paradigms_by_id[pid] = st["paradigm"]

    errors_by_id: dict[str, dict[str, Any]] = {}
    for e in pack.get("errors", []):
        if isinstance(e, dict) and "id" in e:
            errors_by_id[e["id"]] = e

    units: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []
    block_span_counts: dict[tuple[Any, ...], int] = {}
    block_offsets: dict[tuple[Any, ...], int] = {}

    def add_unit(
        tab: str,
        step: str | None,
        activity: str | None,
        item: int | None,
        block: int | str,
        role: str,
        text: str,
        *,
        source: str = "writer_prose",
        ref: str | None = None,
        record_kind: str | None = None,
        record_side: str | None = None,
        option_origin: str | None = None,
        is_key: bool | None = None,
    ) -> None:
        if role == "gloss_ref":
            # The page prints the word record's lemma and gloss here; the writer only typed the id.
            gloss_match = _GLOSS_MARKUP_RE.match(text)
            if gloss_match is None:
                raise AssemblerError("gloss_ref_malformed", f"gloss reference {text!r} is not {{{{gloss:W-n}}}}")
            source = "record"
            ref = gloss_match.group(1)
        clean = strip_accents(text) if source != "writer_prose" else text
        loc_key = (tab, step, activity, item, block)
        span_idx = block_span_counts.get(loc_key, 0)
        start_off = block_offsets.get(loc_key, 0)
        end_off = start_off + len(clean)
        block_span_counts[loc_key] = span_idx + 1
        block_offsets[loc_key] = end_off

        units.append(
            {
                "tab": tab,
                "step": step,
                "activity": activity,
                "item": item,
                "block": block,
                "role": role,
                "text": clean,
            }
        )
        record_kind = derive_record_kind(ref, tab) if source == "record" else None
        spans.append(
            {
                "tab": tab,
                "step": step,
                "activity": activity,
                "item": item,
                "block": block,
                "span": span_idx,
                "start": start_off,
                "end": end_off,
                "source": source,
                "ref": ref,
                "role": role,
                "text": clean,
                "record_kind": record_kind,
                "record_side": record_side,
                "option_origin": option_origin,
                "is_key": is_key,
            }
        )

    # 1. Tab: urok (Lesson)
    for step in draft.get("steps", []):
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")
        lead_in = step.get("lead_in")
        if lead_in:
            for role, span_text in _split_inline_spans(page_text(lead_in), "narration"):
                add_unit("urok", step_id, None, None, "lead_in", role, span_text, source="writer_prose")

        blocks = step.get("blocks", [])
        for block_idx, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            kind = block.get("kind")

            if kind == "prose":
                prose_text = block.get("text", "")
                for role, span_text in _split_inline_spans(page_text(prose_text), "narration"):
                    add_unit("urok", step_id, None, None, block_idx, role, span_text, source="writer_prose")

            elif kind == "example":
                ref_id = block.get("ref", "")
                ex_rec = examples_by_id.get(ref_id)
                if ex_rec is None:
                    raise AssemblerError(EXAMPLE_NOT_FOUND, f"example record {ref_id} not found in pack")
                ex_text = page_text(str(ex_rec.get("text", "")))
                add_unit("urok", step_id, None, None, block_idx, "record_print", ex_text, source="record", ref=ref_id)

            elif kind == "quote":
                ref_id = block.get("ref", "")
                t_rec = texts_by_id.get(ref_id)
                if t_rec is None:
                    raise AssemblerError(TEXT_NOT_FOUND, f"quote record {ref_id} not found in pack")
                quote_text = page_text(str(t_rec.get("quote", "")))
                add_unit(
                    "urok", step_id, None, None, block_idx, "record_print", quote_text, source="record", ref=ref_id
                )

            elif kind == "paradigm":
                ref_id = block.get("ref", "")
                p_info = paradigms_by_id.get(ref_id)
                if p_info is None:
                    raise AssemblerError(PARADIGM_NOT_FOUND, f"paradigm {ref_id} not found in lesson steps")
                wid = p_info.get("word", "")
                w_rec = words_by_id.get(wid)
                if w_rec is None:
                    raise AssemblerError(
                        WORD_NOT_FOUND, f"word record {wid} for paradigm {ref_id} not found in words store"
                    )
                forms_by_tag = {f.get("tags"): f for f in w_rec.get("forms", []) if isinstance(f, dict)}
                for f_idx, ftag in enumerate(p_info.get("forms", [])):
                    form_entry = forms_by_tag.get(ftag)
                    if form_entry is None:
                        raise AssemblerError(
                            FORM_NOT_FOUND, f"form tag {ftag} not found for word {wid} in paradigm {ref_id}"
                        )
                    p_form_text = str(form_entry.get("form") or form_entry.get("stressed") or "")
                    add_unit(
                        "urok",
                        step_id,
                        None,
                        None,
                        f"paradigm_{block_idx}_{f_idx}",
                        "record_print",
                        p_form_text,
                        source="record",
                        ref=wid,
                    )

            elif kind == "table":
                rows = block.get("rows", [])
                for r_idx, row in enumerate(rows):
                    if isinstance(row, list):
                        for c_idx, cell in enumerate(row):
                            c_str = str(cell)
                            for role, span_text in _split_inline_spans(page_text(c_str), "narration"):
                                add_unit(
                                    "urok",
                                    step_id,
                                    None,
                                    None,
                                    f"table_{block_idx}_{r_idx}_{c_idx}",
                                    role,
                                    span_text,
                                    source="writer_prose",
                                )

            elif kind == "pronunciation":
                pron_text = block.get("text", "")
                for role, span_text in _split_inline_spans(page_text(pron_text), "narration"):
                    add_unit("urok", step_id, None, None, block_idx, role, span_text, source="writer_prose")

            elif kind == "bilingual":
                uk_lines = block.get("uk", [])
                for line_idx, line in enumerate(uk_lines):
                    l_str = str(line)
                    for role, span_text in _split_inline_spans(page_text(l_str), "narration"):
                        add_unit(
                            "urok",
                            step_id,
                            None,
                            None,
                            f"bilingual_{block_idx}_{line_idx}",
                            role,
                            span_text,
                            source="writer_prose",
                        )
                for line_idx, line in enumerate(block.get("en", [])):
                    add_unit(
                        "urok",
                        step_id,
                        None,
                        None,
                        f"bilingual_en_{block_idx}_{line_idx}",
                        "vesum_exempt",
                        str(line),
                        source="writer_prose",
                    )

            elif kind in ("culture", "tip", "summary", "callout"):
                txt = block.get("text", "")
                for role, span_text in _split_inline_spans(page_text(txt), "narration"):
                    add_unit("urok", step_id, None, None, block_idx, role, span_text, source="writer_prose")

            elif kind == "video":
                ref_id = block.get("ref", "")
                vid_rec = videos_by_id.get(ref_id)
                if vid_rec is None:
                    raise AssemblerError(VIDEO_NOT_FOUND, f"video record {ref_id} not found in pack")
                v_lead = block.get("lead_in")
                if v_lead:
                    for role, span_text in _split_inline_spans(page_text(v_lead), "narration"):
                        add_unit(
                            "urok",
                            step_id,
                            None,
                            None,
                            f"video_lead_{block_idx}",
                            role,
                            span_text,
                            source="writer_prose",
                        )

            elif kind == "dialogue":
                dial = draft.get("dialogue") or {}
                for line_idx, line in enumerate(dial.get("lines", [])):
                    if isinstance(line, dict):
                        l_text = str(line.get("text", ""))
                        for role, span_text in _split_inline_spans(page_text(l_text), "dialogue_line"):
                            add_unit(
                                "urok",
                                step_id,
                                None,
                                None,
                                f"dialogue_{line_idx}",
                                role,
                                span_text,
                                source="writer_prose",
                            )
                for line_idx, line in enumerate(dial.get("translation_en") or []):
                    add_unit(
                        "urok",
                        step_id,
                        None,
                        None,
                        f"dialogue_translation_{line_idx}",
                        "vesum_exempt",
                        str(line),
                        source="writer_prose",
                    )

    # Consolidation lead-in
    consol_lead = draft.get("consolidation", {}).get("lead_in")
    if consol_lead:
        for role, span_text in _split_inline_spans(page_text(consol_lead), "narration"):
            add_unit("urok", None, None, None, "consolidation_lead_in", role, span_text, source="writer_prose")

    # 2. Tab: vpravy (Activities)
    act_to_step: dict[str, str] = {}
    for st in lesson_entry.get("steps", []):
        if isinstance(st, dict):
            st_id = st.get("id")
            if st_id:
                for act_ref in st.get("practice", []):
                    if isinstance(act_ref, str):
                        act_to_step[act_ref] = st_id

    for st in draft.get("steps", []):
        if isinstance(st, dict):
            st_id = st.get("id")
            if st_id:
                for bl in st.get("blocks", []):
                    if isinstance(bl, dict) and bl.get("kind") == "activity":
                        act_ref = bl.get("ref")
                        if isinstance(act_ref, str):
                            act_to_step[act_ref] = st_id

    plan_acts_by_id = {
        act["id"]: act for act in lesson_entry.get("activities", []) if isinstance(act, dict) and "id" in act
    }

    for act in draft.get("activities", []):
        if not isinstance(act, dict):
            continue
        act_id = act.get("id")
        if not act_id or act_id not in plan_acts_by_id:
            raise AssemblerError(ACTIVITY_NOT_FOUND, f"draft activity {act_id} not found in plan")
        act_type = plan_acts_by_id[act_id].get("type")
        act_step = act_to_step.get(act_id) if act_id else None
        instr = act.get("instruction")
        if instr:
            for role, span_text in _split_inline_spans(str(instr), "instruction"):
                add_unit("vpravy", act_step, act_id, None, "instruction", role, span_text, source="writer_prose")

        if act_type == "pick-syllables" and "syllables" in act:
            syls = act.get("syllables") or []
            corr_indices = set(act.get("correctIndices") or [])
            for s_idx, syl in enumerate(syls):
                is_key = s_idx in corr_indices
                for role, span_text in _split_inline_spans(str(syl), "item_option"):
                    add_unit(
                        "vpravy",
                        act_step,
                        act_id,
                        None,
                        f"opt_{s_idx}",
                        role,
                        span_text,
                        source="writer_prose",
                        option_origin="writer_typed",
                        is_key=is_key,
                    )
            expl = act.get("explanation")
            if expl and isinstance(expl, str):
                for role, span_text in _split_inline_spans(expl, "instruction"):
                    add_unit("vpravy", act_step, act_id, None, "explanation", role, span_text, source="writer_prose")

        for item_idx, item in enumerate(act.get("items", [])):
            if not isinstance(item, dict):
                continue

            prompt = None
            for key in ("prompt", "sentence", "question", "cue", "statement"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    prompt = val
                    break
            if prompt:
                if act_type == "error-correction":
                    error_ref = item.get("error_ref")
                    err_rec = errors_by_id.get(error_ref) if error_ref else None
                    error_text = err_rec.get("incorrect") if err_rec else item.get("error")
                    if isinstance(error_text, str) and error_text and error_text in prompt:
                        before, after = prompt.split(error_text, 1)
                        for role, span_text in _split_inline_spans(before, "item_prompt"):
                            add_unit(
                                "vpravy", act_step, act_id, item_idx, "prompt", role, span_text, source="writer_prose"
                            )
                        add_unit(
                            "vpravy",
                            act_step,
                            act_id,
                            item_idx,
                            "prompt",
                            "error_text",
                            error_text,
                            source="record",
                            ref=error_ref,
                            record_kind="error",
                            record_side="incorrect",
                        )
                        for role, span_text in _split_inline_spans(after, "item_prompt"):
                            add_unit(
                                "vpravy", act_step, act_id, item_idx, "prompt", role, span_text, source="writer_prose"
                            )
                    else:
                        for role, span_text in _split_inline_spans(prompt, "item_prompt"):
                            add_unit(
                                "vpravy", act_step, act_id, item_idx, "prompt", role, span_text, source="writer_prose"
                            )
                else:
                    for role, span_text in _split_inline_spans(prompt, "item_prompt"):
                        add_unit("vpravy", act_step, act_id, item_idx, "prompt", role, span_text, source="writer_prose")

            # Answer-like candidate fields: only string values are answer text. Booleans
            # (true/false activities) and integers (`correct` as an option index in quiz and
            # odd-one-out items) are keys, not text to resolve, stress or render. A string
            # `answer` on a choice type names one of the options (check 4: answer_not_in_options)
            # and is a key too: the page prints only the option it flags correct, so the option
            # span (is_key: true) carries that text.
            # For error-correction, use the field validated by check 4 (correction, falling back to answer).
            if act_type == "error-correction":
                corr_val = item.get("correction") if item.get("correction") is not None else item.get("answer")
                answer = corr_val if isinstance(corr_val, str) and corr_val.strip() else None
            elif string_key_answer(act_type, item) is not None:
                answer = None
            else:
                answer = None
                for key in ("answer", "correction", "target", "correct", "is_true", "isTrue"):
                    val = item.get(key)
                    if isinstance(val, str) and val.strip():
                        answer = val
                        break
            if answer:
                for role, span_text in _split_inline_spans(answer, "item_answer"):
                    if act_type == "error-correction":
                        error_ref = item.get("error_ref")
                        add_unit(
                            "vpravy",
                            act_step,
                            act_id,
                            item_idx,
                            "answer",
                            role,
                            span_text,
                            source="record",
                            ref=error_ref,
                            record_kind="error",
                            record_side="correct",
                        )
                    else:
                        add_unit("vpravy", act_step, act_id, item_idx, "answer", role, span_text, source="writer_prose")

            if act_type == "odd-one-out" and "words" in item:
                words_list = item.get("words") or []
                corr_idx = item.get("correct") if isinstance(item.get("correct"), int) else None
                ans_str = str(item.get("answer")) if item.get("answer") is not None else None
                for opt_idx, w_val in enumerate(words_list):
                    is_key = (opt_idx == corr_idx) if corr_idx is not None else (str(w_val) == ans_str)
                    for role, span_text in _split_inline_spans(str(w_val), "item_option"):
                        add_unit(
                            "vpravy",
                            act_step,
                            act_id,
                            item_idx,
                            f"opt_{opt_idx}",
                            role,
                            span_text,
                            source="writer_prose",
                            option_origin="writer_typed",
                            is_key=is_key,
                        )
            elif act_type == "pick-syllables" and "syllables" in item:
                syls = item.get("syllables") or []
                corr_indices = set(item.get("correctIndices") or [])
                for opt_idx, syl in enumerate(syls):
                    is_key = opt_idx in corr_indices
                    for role, span_text in _split_inline_spans(str(syl), "item_option"):
                        add_unit(
                            "vpravy",
                            act_step,
                            act_id,
                            item_idx,
                            f"opt_{opt_idx}",
                            role,
                            span_text,
                            source="writer_prose",
                            option_origin="writer_typed",
                            is_key=is_key,
                        )
            else:
                opts = item.get("options") or item.get("choices") or item.get("distractors") or []
                if act_type == "fill-in" and item.get("mode") == "form-choice":
                    word_ref = item.get("record")
                    if not isinstance(word_ref, str) or not word_ref:
                        # Same named reason as check 4: a form-choice item without its word record is
                        # invalid, never a set of writer-typed options.
                        raise AssemblerError(
                            "form_choice_options_invalid",
                            f"form-choice item {item_idx} of {act_id} names no word record",
                            layer="writer",
                        )
                    ans_text = item.get("answer")
                    for opt_idx, opt in enumerate(opts):
                        if isinstance(opt, bool):
                            continue
                        opt_str = str(opt.get("text") if isinstance(opt, dict) else opt)
                        is_key = opt_str == str(ans_text)
                        for role, span_text in _split_inline_spans(opt_str, "item_option"):
                            add_unit(
                                "vpravy",
                                act_step,
                                act_id,
                                item_idx,
                                f"opt_{opt_idx}",
                                role,
                                span_text,
                                source="record",
                                ref=word_ref,
                                record_kind="word",
                                option_origin="store",
                                is_key=is_key,
                            )
                elif opts:
                    for opt_idx, opt in enumerate(opts):
                        if isinstance(opt, bool):
                            continue
                        opt_val = opt.get("text") if isinstance(opt, dict) else opt
                        if opt_val is None or isinstance(opt_val, bool):
                            continue
                        opt_str = str(opt_val)

                        is_key = False
                        if act_type in ("quiz", "multiple-choice"):
                            if "_resolved_key_index" in item:
                                is_key = opt_idx == item["_resolved_key_index"]
                            else:
                                res_key = _resolve_single_quiz_key(item, opts)
                                is_key = opt_idx == res_key
                        elif isinstance(opt, dict) and "correct" in opt:
                            is_key = bool(opt.get("correct"))
                        elif act_type == "fill-in":
                            is_key = opt_str == item.get("answer")
                        elif act_type == "error-correction":
                            corr = item.get("correction") or item.get("answer")
                            is_key = opt_str == str(corr)
                        elif act_type == "image-to-letter":
                            is_key = opt_str == item.get("letter")
                        elif act_type == "translate":
                            if isinstance(opt, dict) and "correct" in opt:
                                is_key = bool(opt.get("correct"))
                            elif "answer" in item:
                                is_key = opt_str == item.get("answer")
                        elif act_type == "select":
                            is_key = bool(opt.get("correct")) if isinstance(opt, dict) else False
                        else:
                            if "correct" in item and isinstance(item["correct"], int):
                                is_key = opt_idx == item["correct"]
                            elif "answer" in item and isinstance(item["answer"], str):
                                is_key = opt_str == item["answer"]

                        for role, span_text in _split_inline_spans(opt_str, "item_option"):
                            add_unit(
                                "vpravy",
                                act_step,
                                act_id,
                                item_idx,
                                f"opt_{opt_idx}",
                                role,
                                span_text,
                                source="writer_prose",
                                option_origin="writer_typed",
                                is_key=is_key,
                            )

            err_txt = None
            for key in ("error", "incorrect"):
                val = item.get(key)
                if val is not None and not isinstance(val, bool) and str(val).strip():
                    err_txt = str(val)
                    break
            if err_txt:
                for role, span_text in _split_inline_spans(err_txt, "error_text"):
                    if act_type == "error-correction":
                        error_ref = item.get("error_ref")
                        add_unit(
                            "vpravy",
                            act_step,
                            act_id,
                            item_idx,
                            "error",
                            role,
                            span_text,
                            source="record",
                            ref=error_ref,
                            record_kind="error",
                            record_side="incorrect",
                        )
                    else:
                        add_unit("vpravy", act_step, act_id, item_idx, "error", role, span_text, source="writer_prose")

            expl = item.get("explanation")
            if expl and isinstance(expl, str):
                for role, span_text in _split_inline_spans(expl, "instruction"):
                    add_unit(
                        "vpravy", act_step, act_id, item_idx, "explanation", role, span_text, source="writer_prose"
                    )

            pairs = item.get("pairs") or []
            for p_idx, pair in enumerate(pairs):
                if isinstance(pair, dict):
                    left = pair.get("left") if not isinstance(pair.get("left"), bool) else None
                    if left is None:
                        left = pair.get("prompt") if not isinstance(pair.get("prompt"), bool) else None
                    right = pair.get("right") if not isinstance(pair.get("right"), bool) else None
                    if right is None:
                        right = pair.get("answer") if not isinstance(pair.get("answer"), bool) else None
                    if left:
                        for role, span_text in _split_inline_spans(str(left), "item_prompt"):
                            add_unit(
                                "vpravy",
                                act_step,
                                act_id,
                                item_idx,
                                f"pair_l_{p_idx}",
                                role,
                                span_text,
                                source="writer_prose",
                            )
                    if right:
                        for role, span_text in _split_inline_spans(str(right), "item_answer"):
                            add_unit(
                                "vpravy",
                                act_step,
                                act_id,
                                item_idx,
                                f"pair_r_{p_idx}",
                                role,
                                span_text,
                                source="writer_prose",
                            )

    # 3. Tab: slovnyk (Vocabulary)
    vocab_inv = lesson_entry.get("inventory", {}).get("vocabulary", {})
    core_items = vocab_inv.get("core", [])
    incidental_items = vocab_inv.get("incidental", [])

    for c in core_items:
        if isinstance(c, dict):
            wid = c.get("evidence")
            if wid:
                w_rec = words_by_id.get(wid)
                if not w_rec:
                    raise AssemblerError(WORD_NOT_FOUND, f"core word {wid} not found in words store")
                lemma = str(w_rec.get("lemma", ""))
                add_unit("slovnyk", None, None, None, f"core_{wid}", "record_print", lemma, source="record", ref=wid)

    for inc in incidental_items:
        wid = inc.get("evidence") if isinstance(inc, dict) else inc
        if isinstance(wid, str):
            w_rec = words_by_id.get(wid)
            if not w_rec:
                raise AssemblerError(WORD_NOT_FOUND, f"incidental word {wid} not found in words store")
            lemma = str(w_rec.get("lemma", ""))
            add_unit("slovnyk", None, None, None, f"inc_{wid}", "record_print", lemma, source="record", ref=wid)

    # 4. Tab: resursy (Resources) - CITED ids only
    cited_text_ids: list[str] = []
    cited_video_ids: list[str] = []
    for st in lesson_entry.get("steps", []):
        if isinstance(st, dict):
            for ev in st.get("evidence", []):
                if isinstance(ev, str):
                    if ev.startswith("T-") and ev not in cited_text_ids:
                        cited_text_ids.append(ev)
                    elif ev.startswith("V-") and ev not in cited_video_ids:
                        cited_video_ids.append(ev)
    for v_entry in lesson_entry.get("videos", []):
        if isinstance(v_entry, dict):
            ev = v_entry.get("evidence")
            if isinstance(ev, str) and ev not in cited_video_ids:
                cited_video_ids.append(ev)

    for cid in cited_text_ids:
        t_rec = texts_by_id.get(cid)
        if t_rec is None:
            raise AssemblerError(TEXT_NOT_FOUND, f"cited text record {cid} not found in pack")
        src = t_rec.get("source", {})
        title = str(src.get("work") or src.get("file") or src.get("author") or cid)
        add_unit("resursy", None, None, None, f"res_{cid}", "record_print", title, source="record", ref=cid)

    for vid in cited_video_ids:
        v_rec = videos_by_id.get(vid)
        if v_rec is None:
            raise AssemblerError(VIDEO_NOT_FOUND, f"cited video record {vid} not found in pack")
        chan = str(v_rec.get("channel") or vid)
        add_unit("resursy", None, None, None, f"res_{vid}", "record_print", chan, source="record", ref=vid)

    expanded_doc = {
        "expanded_schema": 1,
        "lesson": {
            "level": level,
            "slug": slug,
            "n": lesson_n,
        },
        "units": units,
    }

    provenance_doc = {
        "provenance_schema": 1,
        "lesson": {
            "level": level,
            "slug": slug,
            "n": lesson_n,
        },
        "spans": spans,
    }

    return expanded_doc, provenance_doc


def write_expanded_document(
    expanded_doc: dict[str, Any],
    provenance_doc: dict[str, Any],
    output_dir: Path,
    lesson_n: int,
) -> tuple[Path, Path]:
    """Write expanded document with lock sidecar, and provenance document with lock sidecar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    exp_path = output_dir / f"lesson-{lesson_n}.expanded.yaml"
    prov_path = output_dir / f"lesson-{lesson_n}.provenance.yaml"

    prov_validator = get_provenance_validator()
    prov_validator.validate(provenance_doc)

    content_bytes = lock.yaml_bytes(expanded_doc)
    lock.write(exp_path, content_bytes)

    prov_bytes = lock.yaml_bytes(provenance_doc)
    lock.write(prov_path, prov_bytes)

    return exp_path, prov_path


def rendered_units_for_tabs(
    stressed_doc: dict[str, Any],
    *,
    slovnyk_entries: list[tuple[str, dict[str, Any]]],
    resursy_entries: list[tuple[str, str, dict[str, Any]]],
) -> dict[int, str]:
    """Per-unit rendered pieces for the Slovnyk and Resursy tabs.

    Those tabs are built from records, not from units; the unit's location is the entry the
    tab builder produced for the same record id (block `core_<id>` / `inc_<id>` -> the vocab
    entry's lemma, block `res_<id>` -> the resource title). A unit without an entry stays
    unmapped and fails closed in finalize_provenance_from_stressed_units.
    """
    vocab_by_id = {wid: entry for wid, entry in slovnyk_entries}
    resources_by_id = {rid: entry for rid, _section, entry in resursy_entries}
    pieces: dict[int, str] = {}
    for idx, unit in enumerate(stressed_doc.get("units", [])):
        tab = unit.get("tab")
        block = str(unit.get("block", ""))
        if tab == "slovnyk":
            for prefix in ("core_", "inc_"):
                if block.startswith(prefix) and block[len(prefix) :] in vocab_by_id:
                    pieces[idx] = str(vocab_by_id[block[len(prefix) :]].get("lemma", ""))
        elif tab == "resursy" and block.startswith("res_") and block[4:] in resources_by_id:
            pieces[idx] = str(resources_by_id[block[4:]].get("title", ""))
    return pieces


def finalize_provenance_from_stressed_units(
    provenance_doc: dict[str, Any],
    stressed_doc: dict[str, Any],
    rendered_by_unit: dict[int, str],
    *,
    words_store: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rebuild the provenance spans from the renderer's per-unit pieces.

    `rendered_by_unit` maps an expanded-unit index to the text the renderer emitted for it
    (the renderer's own unit->output mapping). Every unit must be present; each piece must
    carry the stressed unit's letters (exactly for urok/vpravy, accent-stripped for the
    record prints: Slovnyk lemma, Resursy title, error-correction correction; see the module
    docstring). Span text, `span`, `start` and `end` are then recomputed so that each unit's
    spans partition its rendered text.
    """
    updated = copy.deepcopy(provenance_doc)
    spans = updated.get("spans", [])
    stressed_units = stressed_doc.get("units", [])
    if len(spans) != len(stressed_units):
        raise AssemblerError(
            PROVENANCE_UNIT_COUNT_MISMATCH,
            f"provenance span count ({len(spans)}) does not match stressed unit count ({len(stressed_units)})",
            layer="engine",
        )
    replace_gloss = gloss_replacer(words_store or {})

    unit_offsets: dict[tuple[Any, ...], int] = {}
    unit_span_counts: dict[tuple[Any, ...], int] = {}
    for idx, (span, unit) in enumerate(zip(spans, stressed_units, strict=True)):
        loc_key = (unit.get("tab"), unit.get("step"), unit.get("activity"), unit.get("item"), unit.get("block"))
        span_loc = (span.get("tab"), span.get("step"), span.get("activity"), span.get("item"), span.get("block"))
        if span_loc != loc_key or span.get("role") != unit.get("role"):
            raise AssemblerError(
                PROVENANCE_UNIT_COUNT_MISMATCH,
                f"provenance span {idx} {span_loc} does not describe stressed unit {idx} {loc_key}",
                layer="engine",
            )
        piece = rendered_by_unit.get(idx)
        if piece is None:
            raise AssemblerError(
                SPAN_LOCATION_UNRENDERED,
                f"the renderer emitted nothing for unit {idx} at {loc_key} ({unit.get('text')!r})",
                layer="engine",
            )
        expected = render_unit_piece(str(unit.get("text", "")), replace_gloss)
        if unit.get("tab") in ("slovnyk", "resursy") or span.get("record_side") == "correct":
            # Record prints (Slovnyk lemma, Resursy title, error-correction correction): the page
            # carries the record's own stress (or none), see docstring.
            agrees = strip_accents(piece) == strip_accents(expected)
        else:
            agrees = piece == expected
        if not agrees:
            raise AssemblerError(
                SPAN_TEXT_NOT_IN_RENDERED_OUTPUT,
                f"unit {idx} at {loc_key} renders as {piece!r}, stressed unit text is {expected!r}",
                layer="engine",
            )
        span_idx = unit_span_counts.get(loc_key, 0)
        start_off = unit_offsets.get(loc_key, 0)
        end_off = start_off + len(piece)
        unit_span_counts[loc_key] = span_idx + 1
        unit_offsets[loc_key] = end_off
        span["span"] = span_idx
        span["start"] = start_off
        span["end"] = end_off
        span["text"] = piece

    validator = get_provenance_validator()
    validator.validate(updated)
    return updated


def check_5_assembly(
    draft: dict[str, Any],
    plan: dict[str, Any],
    pack: dict[str, Any],
    words_store: dict[str, Any],
    level: str,
    slug: str,
    lesson_n: int,
    *,
    output_dir: Path | None = None,
) -> CheckResult:
    """Check 5: Assemble draft to expanded document, validate schema and accent ban."""
    try:
        expanded_doc, provenance_doc = assemble_expanded_document(draft, plan, pack, words_store, level, slug, lesson_n)
    except AssemblerError as exc:
        return CheckResult(check=5, passed=False, reason=f"{exc.code}: {exc.message}", layer=exc.layer)
    except Exception as exc:
        return CheckResult(check=5, passed=False, reason=f"assembly raised: {exc}", layer="writer")

    validator = get_expanded_validator()
    errors = sorted(validator.iter_errors(expanded_doc), key=lambda e: e.path)
    if errors:
        err = errors[0]
        return CheckResult(
            check=5,
            passed=False,
            reason=f"expanded document schema validation failed at {list(err.path)}: {err.message}",
            layer="writer",
        )

    prov_validator = get_provenance_validator()
    prov_errors = sorted(prov_validator.iter_errors(provenance_doc), key=lambda e: e.path)
    if prov_errors:
        err = prov_errors[0]
        return CheckResult(
            check=5,
            passed=False,
            reason=f"provenance document schema validation failed at {list(err.path)}: {err.message}",
            layer="writer",
        )

    for idx, u in enumerate(expanded_doc.get("units", [])):
        txt = u.get("text", "")
        if "\u0300" in txt or "\u0301" in txt:
            return CheckResult(
                check=5,
                passed=False,
                step=u.get("step"),
                activity=u.get("activity"),
                token=txt,
                reason=f"combining accent in unit {idx}: {txt!r}",
                layer="writer",
            )

    try:
        ExpandedDocument.from_data(expanded_doc)
    except ResolverError as err:
        return CheckResult(check=5, passed=False, reason=f"ExpandedDocument rejected: {err.message}", layer="writer")

    if output_dir is not None:
        write_expanded_document(expanded_doc, provenance_doc, output_dir, lesson_n)

    return CheckResult(
        check=5,
        passed=True,
        artifacts={"expanded_doc": expanded_doc, "provenance": provenance_doc},
    )


def apply_stress(expanded_doc: dict[str, Any], stream: Any) -> dict[str, Any]:
    """Apply stress from stream tokens to expanded document units by unit index."""
    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])

    replacements_by_unit: dict[int, list[tuple[int, int, str]]] = {}
    for tok in tokens:
        if not isinstance(tok, dict):
            continue
        selected = tok.get("selected")
        if not isinstance(selected, dict):
            continue
        stressed = selected.get("stressed")
        if not stressed or stressed == "pending":
            continue
        unit_idx = tok.get("unit_index")
        offset = tok.get("offset")
        tok_str = str(tok.get("token", ""))
        if isinstance(unit_idx, int) and isinstance(offset, int) and tok_str:
            replacements_by_unit.setdefault(unit_idx, []).append((offset, len(tok_str), str(stressed)))

    units = copy.deepcopy(expanded_doc.get("units", []))
    for unit_idx, unit in enumerate(units):
        reps = replacements_by_unit.get(unit_idx)
        if not reps:
            continue
        reps.sort(key=lambda item: item[0], reverse=True)
        txt = unit["text"]
        for start, length, stressed_val in reps:
            if start + length <= len(txt):
                txt = txt[:start] + stressed_val + txt[start + length :]
        unit["text"] = txt

    return {
        "stressed_schema": 1,
        "lesson": expanded_doc.get("lesson"),
        "units": units,
    }


def write_stressed_document(stressed_doc: dict[str, Any], output_dir: Path, lesson_n: int) -> Path:
    """Write stressed document with lock sidecar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stressed_path = output_dir / f"lesson-{lesson_n}.stressed.yaml"
    content_bytes = lock.yaml_bytes(stressed_doc)
    lock.write(stressed_path, content_bytes)
    return stressed_path


def build_slovnyk_entries(
    lesson_plan: dict[str, Any],
    words_store: dict[str, Any],
    stream: Any = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Build Slovnyk vocabulary entries (core then incidental) as (word record id, item)."""
    vocab_inv = lesson_plan.get("inventory", {}).get("vocabulary", {})
    core_items = vocab_inv.get("core", [])
    incidental_items = vocab_inv.get("incidental", [])

    words_by_id: dict[str, dict[str, Any]] = {}
    for w in words_store.get("words", []):
        if isinstance(w, dict) and "id" in w:
            words_by_id[w["id"]] = w

    selected_senses: dict[str, str] = {}
    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])
    for tok in tokens:
        if isinstance(tok, dict):
            sel = tok.get("selected")
            if isinstance(sel, dict):
                rec = sel.get("record")
                if rec and rec in words_by_id:
                    w_rec = words_by_id[rec]
                    gloss = w_rec.get("sense_gloss") or w_rec.get("gloss_en") or ""
                    if gloss:
                        selected_senses[rec] = str(gloss)

    entries: list[tuple[str, dict[str, Any]]] = []

    def process_item(wid: str, forms_list: list[str]) -> None:
        if wid not in words_by_id:
            return
        w_rec = words_by_id[wid]
        lemma = str(w_rec.get("lemma", ""))

        # Lemma stress comes from the record's lemma form, never first learner form
        stressed_lemma = lemma
        lemma_form = None
        for f in w_rec.get("forms", []):
            if isinstance(f, dict) and f.get("form") == lemma:
                lemma_form = f
                break

        if lemma_form is not None:
            if lemma_form.get("stress_source") == "pending":
                stressed_lemma = lemma
            elif lemma_form.get("stressed"):
                stressed_lemma = str(lemma_form["stressed"])

        gloss = selected_senses.get(wid) or str(w_rec.get("sense_gloss") or w_rec.get("gloss_en") or "")
        try:
            atlas_href = atlas_href_for(lemma)
        except Exception:
            atlas_href = None

        # Taught forms are the stressed forms of the plan's form tags
        forms_by_tag = {f.get("tags"): f for f in w_rec.get("forms", []) if isinstance(f, dict)}
        taught_forms: list[str] = []
        for ftag in forms_list:
            f_entry = forms_by_tag.get(ftag)
            if f_entry:
                if f_entry.get("stress_source") == "pending" or not f_entry.get("stressed"):
                    taught_forms.append(str(f_entry.get("form", "")))
                else:
                    taught_forms.append(str(f_entry["stressed"]))

        item_entry: dict[str, Any] = {
            "lemma": stressed_lemma,
            "translation": gloss,
            "pos": str(w_rec.get("pos", "")),
            "atlas_href": atlas_href,
        }
        if taught_forms:
            item_entry["forms"] = taught_forms
        entries.append((wid, item_entry))

    for c in core_items:
        if isinstance(c, dict):
            wid = c.get("evidence")
            if wid:
                process_item(wid, c.get("forms", []))

    for inc in incidental_items:
        wid = inc.get("evidence") if isinstance(inc, dict) else inc
        if isinstance(wid, str):
            process_item(wid, [])

    return entries


def build_slovnyk_tab(
    lesson_plan: dict[str, Any],
    words_store: dict[str, Any],
    stream: Any = None,
) -> list[dict[str, Any]]:
    """Build Slovnyk vocabulary items (core and incidental) for this lesson."""
    return [item for _wid, item in build_slovnyk_entries(lesson_plan, words_store, stream)]


def build_resursy_entries(
    lesson_plan: dict[str, Any],
    pack: dict[str, Any],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Build Resursy entries from cited pack records only, as (record id, section, entry)."""
    entries: list[tuple[str, str, dict[str, Any]]] = []

    texts_by_id: dict[str, dict[str, Any]] = {}
    for t in pack.get("texts", []):
        if isinstance(t, dict) and "id" in t:
            texts_by_id[t["id"]] = t

    videos_by_id: dict[str, dict[str, Any]] = {}
    for v in pack.get("videos", []):
        if isinstance(v, dict) and "id" in v:
            videos_by_id[v["id"]] = v

    cited_text_ids: list[str] = []
    cited_video_ids: list[str] = []
    for st in lesson_plan.get("steps", []):
        if isinstance(st, dict):
            for ev in st.get("evidence", []):
                if isinstance(ev, str):
                    if ev.startswith("T-") and ev not in cited_text_ids:
                        cited_text_ids.append(ev)
                    elif ev.startswith("V-") and ev not in cited_video_ids:
                        cited_video_ids.append(ev)
    for v_entry in lesson_plan.get("videos", []):
        if isinstance(v_entry, dict):
            ev = v_entry.get("evidence")
            if isinstance(ev, str) and ev not in cited_video_ids:
                cited_video_ids.append(ev)

    for cid in cited_text_ids:
        t_rec = texts_by_id.get(cid)
        if t_rec:
            src = t_rec.get("source", {})
            title = str(src.get("work") or src.get("file") or src.get("author") or cid)
            author = str(src.get("author") or "")
            page = str(src.get("page") or "")
            entries.append(
                (
                    cid,
                    "books",
                    {
                        "title": title,
                        "author": author,
                        "pages": page,
                        "url": "",
                        "source": cid,
                        "description": str(t_rec.get("supports") or ""),
                    },
                )
            )

    plan_video_uses: dict[str, str] = {}
    for v_entry in lesson_plan.get("videos", []):
        if isinstance(v_entry, dict):
            ev = v_entry.get("evidence")
            if isinstance(ev, str):
                plan_video_uses[ev] = str(v_entry.get("use") or "")

    for vid_id in cited_video_ids:
        vid = videos_by_id.get(vid_id)
        if vid:
            chan = str(vid.get("channel") or vid_id)
            entries.append(
                (
                    vid_id,
                    "youtube",
                    {
                        "title": chan,
                        "url": str(vid.get("url") or ""),
                        "channel": chan,
                        "description": plan_video_uses.get(vid_id) or str(vid.get("use") or ""),
                    },
                )
            )

    return entries


def build_resursy_tab(
    lesson_plan: dict[str, Any],
    pack: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build Resursy external resources dictionary from cited pack records only."""
    result: dict[str, list[dict[str, Any]]] = {}
    for _rid, section, entry in build_resursy_entries(lesson_plan, pack):
        result.setdefault(section, []).append(entry)
    return result


@dataclass(frozen=True)
class _UnitFragment:
    """One expanded unit's contribution to a rendered line: its index and rendered piece."""

    index: int
    piece: str
    codec: str = CODEC_PLAIN


class _UrokWriter:
    """Builds the Urok markdown line by line and records every unit's byte range in it.

    Lines are joined with a newline; the renderer's own trailing blank lines are dropped at
    the end. A unit fragment is emitted exactly as mapped (encoded per its codec), so the
    resulting `LessonUnitMap` is the renderer's own unit->output mapping, not a search.
    """

    def __init__(self) -> None:
        self._lines: list[str] = []
        self._length = 0
        self._ranges: list[tuple[int, int, int, str, str]] = []

    def line(self, *fragments: str | _UnitFragment) -> None:
        position = self._length + (1 if self._lines else 0)
        parts: list[str] = []
        for fragment in fragments:
            if isinstance(fragment, _UnitFragment):
                encoded = (
                    encode_js_json_string(fragment.piece) if fragment.codec == CODEC_JS_JSON_STRING else fragment.piece
                )
                self._ranges.append((fragment.index, position, position + len(encoded), fragment.piece, fragment.codec))
                parts.append(encoded)
                position += len(encoded)
            else:
                parts.append(fragment)
                position += len(fragment)
        self._lines.append("".join(parts))
        self._length = position

    def blank(self) -> None:
        self.line()

    def finish(self) -> tuple[str, LessonUnitMap]:
        while self._lines and self._lines[-1] == "":
            self._lines.pop()
        text = "\n".join(self._lines)
        unit_map = LessonUnitMap(text)
        for index, start, end, piece, codec in self._ranges:
            unit_map.track(index, start, end, piece, codec)
        return text, unit_map


def _render_urok_markdown(
    draft: dict[str, Any],
    stressed_doc: dict[str, Any],
    pack: dict[str, Any],
    words_store: dict[str, Any],
) -> tuple[str, LessonUnitMap]:
    """Render Tab 1 (Urok) markdown from draft and stressed units.

    Returns the markdown and the renderer's unit->output mapping: the byte range and rendered
    piece of every expanded unit it consumed, keyed by unit index. Every block is the
    concatenation of its units' pieces in order. Dialogue lines are emitted as the page's
    DialogueBox component; their units live in the `exchanges` payload (`CODEC_JS_JSON_STRING`).
    """
    stressed_units = stressed_doc.get("units", [])
    replace_gloss = gloss_replacer(words_store)

    unit_indices_by_block: dict[tuple[str | None, str | None, int | str], list[int]] = {}
    for i, u in enumerate(stressed_units):
        key = (u.get("tab"), u.get("step"), u.get("block"))
        unit_indices_by_block.setdefault(key, []).append(i)

    texts_by_id: dict[str, dict[str, Any]] = {}
    for t in pack.get("texts", []):
        if isinstance(t, dict) and "id" in t:
            texts_by_id[t["id"]] = t

    examples_by_id: dict[str, dict[str, Any]] = {}
    for ex in pack.get("examples", []):
        if isinstance(ex, dict) and "id" in ex:
            examples_by_id[ex["id"]] = ex

    videos_by_id: dict[str, dict[str, Any]] = {}
    for v in pack.get("videos", []):
        if isinstance(v, dict) and "id" in v:
            videos_by_id[v["id"]] = v

    def unit_fragments(indices: list[int], codec: str = CODEC_PLAIN) -> list[str | _UnitFragment]:
        return [_UnitFragment(i, render_unit_piece(stressed_units[i]["text"], replace_gloss), codec) for i in indices]

    def block_fragments(
        step_id: str | None, block_key: int | str, fallback: str = "", codec: str = CODEC_PLAIN
    ) -> list[str | _UnitFragment]:
        indices = unit_indices_by_block.get(("urok", step_id, block_key))
        if indices:
            return unit_fragments(indices, codec)
        piece = render_unit_piece(fallback, replace_gloss)
        return [encode_js_json_string(piece) if codec == CODEC_JS_JSON_STRING else piece]

    def joined(cells: list[list[str | _UnitFragment]], separator: str) -> list[str | _UnitFragment]:
        out: list[str | _UnitFragment] = []
        for c_idx, cell in enumerate(cells):
            if c_idx:
                out.append(separator)
            out.extend(cell)
        return out

    w = _UrokWriter()

    for step in draft.get("steps", []):
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")

        lead_in = step.get("lead_in")
        if lead_in:
            w.line(*block_fragments(step_id, "lead_in", lead_in))
            w.blank()

        for block_idx, block in enumerate(step.get("blocks", [])):
            if not isinstance(block, dict):
                continue
            kind = block.get("kind")

            if kind == "prose":
                w.line(*block_fragments(step_id, block_idx, block.get("text", "")))
                w.blank()

            elif kind == "example":
                ref_id = block.get("ref", "")
                ex_rec = examples_by_id.get(ref_id)
                if ex_rec:
                    en = str(ex_rec.get("translation_en") or "")
                    w.line("> ", *block_fragments(step_id, block_idx, str(ex_rec.get("text", ""))))
                    if en:
                        w.line(">")
                        w.line("> *", en, "*")
                    w.blank()

            elif kind == "quote":
                ref_id = block.get("ref", "")
                t_rec = texts_by_id.get(ref_id)
                if t_rec:
                    src = t_rec.get("source", {})
                    author = str(src.get("author") or "")
                    work = str(src.get("work") or "")
                    year = src.get("year")
                    page = src.get("page")
                    attr_parts = [p for p in [author, work, str(year) if year else "", str(page) if page else ""] if p]
                    attr = ", ".join(attr_parts) if attr_parts else str(src.get("file", ""))
                    w.line("> ", *block_fragments(step_id, block_idx, str(t_rec.get("quote", ""))))
                    if attr:
                        w.line(">")
                        w.line("> — *", attr, "*")
                    w.blank()

            elif kind == "paradigm":
                indices = [
                    i
                    for i, u in enumerate(stressed_units)
                    if u.get("tab") == "urok"
                    and u.get("step") == step_id
                    and str(u.get("block", "")).startswith(f"paradigm_{block_idx}_")
                ]
                w.line("| | |")
                w.line("| --- | --- |")
                for u_idx in indices:
                    w.line("| ", *unit_fragments([u_idx]), " |")
                w.blank()

            elif kind == "table":
                rows = block.get("rows", [])
                if rows:
                    header = [
                        block_fragments(step_id, f"table_{block_idx}_0_{c_idx}", str(c))
                        for c_idx, c in enumerate(rows[0])
                    ]
                    w.line("| ", *joined(header, " | "), " |")
                    w.line("| " + " | ".join("---" for _ in header) + " |")
                    for r_idx, row in enumerate(rows[1:], start=1):
                        cells = [
                            block_fragments(step_id, f"table_{block_idx}_{r_idx}_{c_idx}", str(c))
                            for c_idx, c in enumerate(row)
                        ]
                        w.line("| ", *joined(cells, " | "), " |")
                    w.blank()

            elif kind == "pronunciation":
                w.line(*block_fragments(step_id, block_idx, block.get("text", "")))
                w.blank()

            elif kind == "bilingual":
                uk_lines = block.get("uk", [])
                en_lines = block.get("en", [])
                w.line("| | |")
                w.line("| --- | --- |")
                for line_idx, (u_raw, e_raw) in enumerate(zip(uk_lines, en_lines, strict=False)):
                    w.line(
                        "| ",
                        *block_fragments(step_id, f"bilingual_{block_idx}_{line_idx}", str(u_raw)),
                        " | ",
                        *block_fragments(step_id, f"bilingual_en_{block_idx}_{line_idx}", str(e_raw)),
                        " |",
                    )
                w.blank()

            elif kind in ("culture", "callout"):
                w.line("> [!note]")
                w.line("> ", *block_fragments(step_id, block_idx, block.get("text", "")))
                w.blank()

            elif kind == "tip":
                w.line("> [!tip]")
                w.line("> ", *block_fragments(step_id, block_idx, block.get("text", "")))
                w.blank()

            elif kind == "summary":
                w.line("> [!summary]")
                w.line("> ", *block_fragments(step_id, block_idx, block.get("text", "")))
                w.blank()

            elif kind == "video":
                v_lead = block.get("lead_in")
                if v_lead:
                    w.line(*block_fragments(step_id, f"video_lead_{block_idx}", v_lead))
                    w.blank()
                ref_id = block.get("ref", "")
                vid_rec = videos_by_id.get(ref_id)
                if vid_rec:
                    chan = str(vid_rec.get("channel") or "")
                    url = str(vid_rec.get("url") or "")
                    w.line("> [", chan, "](", url, ")")
                    w.blank()

            elif kind == "dialogue":
                # The page's DialogueBox component, with each line's units inside its
                # `exchanges` payload (the same JSX `generate_mdx` builds for legacy dialogues).
                dial = draft.get("dialogue") or {}
                payload: list[str | _UnitFragment] = [DIALOGUE_BOX_PAYLOAD_PREFIX, "["]
                for line_idx, line in enumerate(dial.get("lines", [])):
                    if not isinstance(line, dict):
                        continue
                    if len(payload) > 2:
                        payload.append(",")
                    payload.append('{"speaker":"' + encode_js_json_string(str(line.get("speaker", ""))) + '","text":"')
                    payload.extend(
                        block_fragments(
                            step_id, f"dialogue_{line_idx}", line.get("text", ""), codec=CODEC_JS_JSON_STRING
                        )
                    )
                    payload.append('"}')
                payload.extend(("]", DIALOGUE_BOX_PAYLOAD_SUFFIX))
                for header_line in dialogue_box_header_lines(DIALOGUE_BOX_DEFAULT_TITLE):
                    w.line(header_line)
                w.line(*payload)
                w.line(DIALOGUE_BOX_CLOSING_LINE)
                w.blank()

            elif kind == "activity":
                ref_id = block.get("ref", "")
                if ref_id:
                    w.line(f"<!-- INJECT_ACTIVITY: {ref_id} -->")
                    w.blank()

    consol_lead = draft.get("consolidation", {}).get("lead_in")
    if consol_lead:
        w.line(*block_fragments(None, "consolidation_lead_in", consol_lead))
        w.blank()

    # Only the renderer's own trailing block separators are dropped; a unit's bytes (including
    # edge whitespace) are emitted exactly as mapped, so the mapping describes the output.
    return w.finish()


def apply_stress_to_activities(
    draft_activities: list[dict[str, Any]],
    stressed_doc: dict[str, Any],
    replace_gloss_fn: Any,
    *,
    activity_types: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], dict[int, str]]:
    """Apply stress from stressed units to draft activity fields.

    Returns the stressed activity payloads (the engine's input to the component renderer)
    and the renderer's unit->output mapping: the rendered piece of every expanded unit it
    consumed, keyed by unit index. `activity_types` maps activity id to its plan type; on a
    string-key choice type (STRING_KEY_ANSWER_TYPES) the `answer` key is rewritten to the
    rendered text of the option it names instead of being stressed on its own.
    """
    activity_types = activity_types or {}
    stressed_units = stressed_doc.get("units", [])
    rendered_by_unit: dict[int, str] = {}
    vpravy_indices: dict[tuple[str | None, int | None, int | str], list[int]] = {}
    for i, u in enumerate(stressed_units):
        if u.get("tab") == "vpravy":
            key = (u.get("activity"), u.get("item"), u.get("block"))
            vpravy_indices.setdefault(key, []).append(i)

    def format_act_text(
        act_id: str | None, item_idx: int | None, block_key: int | str, fallback: str, *, record_print: bool = False
    ) -> str:
        indices = vpravy_indices.get((act_id, item_idx, block_key))
        if not indices:
            piece = render_unit_piece(fallback, replace_gloss_fn)
            return strip_accents(piece) if record_print else piece
        pieces = []
        for i in indices:
            piece = render_unit_piece(stressed_units[i]["text"], replace_gloss_fn)
            if record_print:
                # The page prints the record's own text (the pack carries no stress), like the
                # Slovnyk lemma and the Resursy title; see the module docstring.
                piece = strip_accents(piece)
            rendered_by_unit[i] = piece
            pieces.append(piece)
        return "".join(pieces)

    def format_options(act_id: str | None, item_idx: int | None, opts: list[Any]) -> list[Any]:
        new_opts = []
        for opt_idx, opt in enumerate(opts):
            if isinstance(opt, dict) and "text" in opt:
                opt_copy = dict(opt)
                opt_copy["text"] = format_act_text(act_id, item_idx, f"opt_{opt_idx}", opt["text"])
                new_opts.append(opt_copy)
            elif isinstance(opt, str):
                new_opts.append(format_act_text(act_id, item_idx, f"opt_{opt_idx}", opt))
            else:
                new_opts.append(opt)
        return new_opts

    def option_plain_text(opt: Any) -> str | None:
        if isinstance(opt, dict):
            opt = opt.get("text")
        return opt if isinstance(opt, str) else None

    stressed_activities = copy.deepcopy(draft_activities)
    for act, draft_act in zip(stressed_activities, draft_activities, strict=True):
        if not isinstance(act, dict):
            continue
        act_id = act.get("id")
        act_type = str(activity_types.get(str(act_id), act.get("type") or ""))
        if "instruction" in act:
            act["instruction"] = format_act_text(act_id, None, "instruction", act["instruction"])
        if isinstance(act.get("syllables"), list):
            act["syllables"] = format_options(act_id, None, act["syllables"])
        if isinstance(act.get("explanation"), str):
            act["explanation"] = format_act_text(act_id, None, "explanation", act["explanation"])
        draft_items = draft_act.get("items", []) if isinstance(draft_act, dict) else []
        for item_idx, item in enumerate(act.get("items", [])):
            if not isinstance(item, dict):
                continue
            for prompt_key in ("prompt", "sentence", "question", "cue", "statement"):
                if prompt_key in item and isinstance(item[prompt_key], str):
                    item[prompt_key] = format_act_text(act_id, item_idx, "prompt", item[prompt_key])
            draft_item = draft_items[item_idx] if item_idx < len(draft_items) else {}
            key_answer = string_key_answer(act_type, draft_item) if isinstance(draft_item, dict) else None
            for ans_key in ("answer", "correction", "correct", "target", "is_true", "isTrue"):
                if ans_key == "answer" and isinstance(key_answer, str):
                    continue
                if ans_key in item and isinstance(item[ans_key], str):
                    # An error-correction correction is the E- record's `correct` text: the
                    # ErrorCorrection component compares the (never stressed) option chips to it
                    # byte for byte, so it prints as the record has it.
                    item[ans_key] = format_act_text(
                        act_id, item_idx, "answer", item[ans_key], record_print=act_type == "error-correction"
                    )
            for err_key in ("error", "incorrect"):
                if err_key in item and isinstance(item[err_key], str):
                    item[err_key] = format_act_text(act_id, item_idx, "error", item[err_key])
            if "explanation" in item and isinstance(item["explanation"], str):
                item["explanation"] = format_act_text(act_id, item_idx, "explanation", item["explanation"])
            for opt_key in ("options", "choices", "distractors", "words", "syllables"):
                if opt_key in item and isinstance(item[opt_key], list):
                    item[opt_key] = format_options(act_id, item_idx, item[opt_key])
            if isinstance(key_answer, str):
                # The key names a draft option; on the page it must equal that option's rendered
                # text (options are never stressed, see resolver SKIPPED_ROLES), or the component
                # flags no option correct.
                choices_key = "words" if act_type == "odd-one-out" else "options"
                draft_choices = draft_item.get(choices_key)
                rendered_choices = item.get(choices_key)
                if isinstance(draft_choices, list) and isinstance(rendered_choices, list):
                    key_indices = [i for i, opt in enumerate(draft_choices) if option_plain_text(opt) == key_answer]
                    if len(key_indices) == 1 and key_indices[0] < len(rendered_choices):
                        keyed = option_plain_text(rendered_choices[key_indices[0]])
                        if keyed is not None:
                            item["answer"] = keyed
            if "pairs" in item and isinstance(item["pairs"], list):
                for p_idx, pair in enumerate(item["pairs"]):
                    if isinstance(pair, dict):
                        for left_key in ("left", "prompt"):
                            if left_key in pair:
                                pair[left_key] = format_act_text(act_id, item_idx, f"pair_l_{p_idx}", pair[left_key])
                        for right_key in ("right", "answer"):
                            if right_key in pair:
                                pair[right_key] = format_act_text(act_id, item_idx, f"pair_r_{p_idx}", pair[right_key])
    return stressed_activities, rendered_by_unit


def _page_unit_label(key: Any, stressed_doc: dict[str, Any]) -> str:
    """Name a tracked page unit in a check 9 reason: the stressed unit's location or the activity."""
    if isinstance(key, int):
        units = stressed_doc.get("units", [])
        if 0 <= key < len(units):
            unit = units[key]
            loc_key = (unit.get("tab"), unit.get("step"), unit.get("activity"), unit.get("item"), unit.get("block"))
            return f"unit {key} at {loc_key}"
        return f"unit {key}"
    if isinstance(key, tuple) and key and key[0] == "activity":
        return f"activity {key[1]!r} component"
    return repr(key)


def check_9_stress_and_render(
    expanded_doc: dict[str, Any],
    draft: dict[str, Any],
    plan: dict[str, Any],
    pack: dict[str, Any],
    words_store: dict[str, Any],
    stream: Any,
    level: str,
    slug: str,
    lesson_n: int,
    *,
    provenance_doc: dict[str, Any] | None = None,
    repo_root: Path = REPO_ROOT,
    output_dir: Path | None = None,
    site_dir: Path | None = None,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
) -> CheckResult:
    """Check 9: Apply stress, build Slovnyk and Resursy, verify locks, render MDX."""
    try:
        stressed_doc = apply_stress(expanded_doc, stream)
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"stress application raised: {exc}", layer="writer")

    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])
    for tok in tokens:
        if isinstance(tok, dict):
            klass = str(tok.get("class", ""))
            sel = tok.get("selected")
            # A resolved `{{gloss:W-n}}` reference carries no stress of its own (the page prints
            # the record's lemma), so its null `stressed` is not a pending stress.
            if klass == "pending_stress" or (
                isinstance(sel, dict)
                and (sel.get("stressed") is None or sel.get("stressed") == "pending")
                and not klass.startswith("skipped")
                and tok.get("surface") != "gloss_ref"
            ):
                return CheckResult(
                    check=9,
                    passed=False,
                    token=str(tok.get("token", "")),
                    reason="pending stress in stream",
                    layer="word_store",
                )

    lesson_entry: dict[str, Any] = {}
    for entry in plan.get("lessons", []):
        if isinstance(entry, dict) and entry.get("n") == lesson_n:
            lesson_entry = entry
            break
    if not lesson_entry:
        return CheckResult(check=9, passed=False, reason=f"lesson {lesson_n} not found in plan", layer="plan")

    slovnyk_entries = build_slovnyk_entries(lesson_entry, words_store, stream)
    vocab_items = [item for _wid, item in slovnyk_entries]
    resursy_entries = build_resursy_entries(lesson_entry, pack)
    external_resources: dict[str, list[dict[str, Any]]] = {}
    for _rid, section, entry in resursy_entries:
        external_resources.setdefault(section, []).append(entry)

    # Check on-disk lesson lock
    lock_ok, lock_diff = lesson_lock.check_lesson_lock(
        level,
        slug,
        evidence_dir=evidence_dir,
        plans_dir=plans_dir,
        repo_root=repo_root,
    )
    if not lock_ok:
        return CheckResult(
            check=9,
            passed=False,
            reason=f"lessons.lock.yaml check failed: {lock_diff}",
            layer="pack",
        )

    # Compute lesson lock
    try:
        lock_doc = lesson_lock.compute_lesson_lock(
            level,
            slug,
            plan_dict=plan,
            pack_dict=pack,
            words_dict=words_store,
            repo_root=repo_root,
            evidence_dir=evidence_dir,
            plans_dir=plans_dir,
        )
        lessons_lock_sha256 = hashlib.sha256(lock.yaml_bytes(lock_doc)).hexdigest()
        lesson_entry_sha256 = None
        for l_item in lock_doc.get("lessons", []):
            if l_item.get("n") == lesson_n:
                lesson_entry_sha256 = l_item.get("entry_sha256")
                break
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"lesson lock calculation failed: {exc}", layer="pack")

    if not lesson_entry_sha256:
        return CheckResult(
            check=9, passed=False, reason=f"lesson {lesson_n} lock entry not found in computed lock", layer="plan"
        )

    draft_lock_entry = draft.get("inputs", {}).get("lesson_lock_entry_sha256")
    if not draft_lock_entry:
        return CheckResult(
            check=9, passed=False, reason="draft inputs missing lesson_lock_entry_sha256", layer="writer"
        )
    if draft_lock_entry != lesson_entry_sha256:
        return CheckResult(
            check=9,
            passed=False,
            reason=f"draft lesson_lock_entry_sha256 {draft_lock_entry!r} != computed {lesson_entry_sha256!r}",
            layer="writer",
        )

    # Immersion band computation
    arc_ref = plan.get("arc_ref")
    if not isinstance(arc_ref, dict) or "position" not in arc_ref:
        return CheckResult(check=9, passed=False, reason="plan missing arc_ref.position", layer="plan")
    arc_position = int(arc_ref["position"])

    p_root = plans_dir or (repo_root / f"curriculum/l2-uk-en/lesson-plans/{level}")
    e_root = evidence_dir or (repo_root / f"curriculum/l2-uk-en/evidence/{level}")
    try:
        p_state = planned_state(
            level,
            arc_position,
            lesson_n,
            allow_missing_prior=False,
            plans_dir=p_root,
            evidence_dir=e_root,
        )
        if getattr(p_state, "waiver", None):
            return CheckResult(
                check=9,
                passed=False,
                reason=f"{PRIOR_PLANS_MISSING}: {p_state.waiver}",
                layer="plan",
            )
        cumulative_core_count = p_state.cumulative_core_count
    except PlannedStateError as exc:
        code = getattr(exc, "code", PRIOR_PLANS_MISSING)
        return CheckResult(check=9, passed=False, reason=f"{code}: {exc}", layer="plan")
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"planned state computation failed: {exc}", layer="plan")

    try:
        band = compute_lesson_immersion_band(
            track=level,
            arc_position=arc_position,
            lesson_n=lesson_n,
            cumulative_core_count=cumulative_core_count,
        )
        immersion_band_key = band.band_key
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"immersion band computation failed: {exc}", layer="plan")

    plan_lessons = plan.get("lessons", [])
    offset = next(
        (i for i, l in enumerate(plan_lessons) if isinstance(l, dict) and l.get("n") == lesson_n), lesson_n - 1
    )
    base = f"/{level}/{slug}/"
    previous = base if offset == 0 else f"{base}{lesson_n - 1}/"
    following = f"{base}{lesson_n + 1}/" if offset + 1 < len(plan_lessons) else base

    meta_data = {
        "title": str(lesson_entry.get("title", "")),
        "subtitle": str(lesson_entry.get("rationale") or ""),
        "evidence": {
            "lessons_lock_sha256": lessons_lock_sha256,
            "lesson_entry_sha256": lesson_entry_sha256,
        },
        "immersion": immersion_band_key,
        "job": str(lesson_entry.get("job") or ""),
        "prev": previous,
        "next": following,
        "lesson": lesson_n,
        "module_slug": slug,
        # Plan reading passages that name a hosted reading (`title` + `reading_slug`) print as
        # the Lesson tab's reading list, the contract `generate_mdx` already has for `readings`.
        "readings": [entry for entry in lesson_entry.get("reading_passages") or [] if isinstance(entry, dict)],
    }

    urok_md, unit_map = _render_urok_markdown(draft, stressed_doc, pack, words_store)
    replace_gloss = gloss_replacer(words_store)

    plan_acts_by_id = {
        act["id"]: act for act in lesson_entry.get("activities", []) if isinstance(act, dict) and "id" in act
    }

    for draft_act in draft.get("activities", []):
        if isinstance(draft_act, dict):
            act_id = draft_act.get("id")
            if not act_id or act_id not in plan_acts_by_id:
                return CheckResult(
                    check=9,
                    passed=False,
                    reason=f"{ACTIVITY_NOT_FOUND}: draft activity {act_id} not found in plan",
                    layer="plan",
                )

    stressed_activities, activity_pieces = apply_stress_to_activities(
        draft.get("activities", []),
        stressed_doc,
        replace_gloss,
        activity_types={aid: str(act.get("type") or "") for aid, act in plan_acts_by_id.items()},
    )
    from scripts.yaml_activities import ActivityParser

    activity_parser = ActivityParser()
    converted_activities = []
    parsed_by_id: dict[str, Any] = {}
    for act_dict in stressed_activities:
        if not isinstance(act_dict, dict):
            continue
        act_id = act_dict.get("id")
        plan_act = plan_acts_by_id.get(act_id)
        if not plan_act:
            return CheckResult(
                check=9,
                passed=False,
                reason=f"{ACTIVITY_NOT_FOUND}: draft activity {act_id} not found in plan",
                layer="plan",
            )
        act_payload = copy.deepcopy(act_dict)
        act_payload["type"] = plan_act.get("type")
        act_payload["placement"] = plan_act.get("placement")
        if not act_payload.get("title") and plan_act.get("focus"):
            act_payload["title"] = plan_act.get("focus")

        try:
            act_obj = activity_parser._parse_activity(act_payload)
            act_obj.placement = plan_act.get("placement")
            converted_activities.append(act_obj)
            parsed_by_id[str(act_id)] = act_obj
        except Exception as exc:
            return CheckResult(
                check=9,
                passed=False,
                reason=f"activity parsing failed for {act_id}: {exc}",
                layer="writer",
            )

    source_prov = provenance_doc
    if source_prov is None and output_dir is not None:
        prov_path = output_dir / f"lesson-{lesson_n}.provenance.yaml"
        if prov_path.is_file():
            source_prov = yaml.safe_load(prov_path.read_text(encoding="utf-8"))

    try:
        mdx_content = generate_mdx(
            md_content=urok_md,
            module_num=lesson_n,
            yaml_activities=converted_activities,
            meta_data=meta_data,
            vocab_items=vocab_items,
            external_resources=external_resources,
            level=level,
            pipeline_version="v7",
            build_status="draft",
            fresh=True,
            unit_map=unit_map,
        )
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"MDX rendering failed: {exc}", layer="writer")

    # Provenance is verified against what the page receives. Every urok unit is read back at
    # its own location in the final MDX (the renderer's mapping carried through every
    # `generate_mdx` transform); vpravy units are located in the props of the component JSX
    # as it stands in the final MDX.
    try:
        page_units = unit_map.verify(mdx_content)
    except UnitMapError as exc:
        code = SPAN_LOCATION_UNRENDERED if exc.kind == LOST_REMOVED else SPAN_TEXT_NOT_IN_RENDERED_OUTPUT
        return CheckResult(
            check=9,
            passed=False,
            reason=f"{code}: {_page_unit_label(exc.key, stressed_doc)}: {exc.message}",
            layer="engine",
        )
    rendered_by_unit: dict[int, str] = {key: text for key, text in page_units.items() if isinstance(key, int)}
    page_jsx: dict[str, list[str]] = {}
    for key, text in page_units.items():
        if isinstance(key, tuple) and key[0] == "activity":
            page_jsx.setdefault(str(key[1]), []).append(text)
    rendered_by_unit.update(
        rendered_units_for_tabs(stressed_doc, slovnyk_entries=slovnyk_entries, resursy_entries=resursy_entries)
    )
    try:
        rendered_by_unit.update(
            locate_units_in_component_props(
                stressed_doc,
                activity_pieces,
                parsed_by_id,
                page_jsx,
                spans=source_prov.get("spans") if isinstance(source_prov, dict) else None,
            )
        )
    except AssemblerError as exc:
        return CheckResult(check=9, passed=False, reason=f"{exc.code}: {exc.message}", layer=exc.layer)

    if output_dir is not None:
        write_stressed_document(stressed_doc, output_dir, lesson_n)

    # Finalize provenance from stressed units and write with lock sidecar; the site is written
    # only once the provenance describes the page.
    final_prov_doc = None
    if source_prov is not None:
        try:
            final_prov_doc = finalize_provenance_from_stressed_units(
                source_prov,
                stressed_doc,
                rendered_by_unit,
                words_store=words_store,
            )
            if output_dir is not None:
                prov_path = output_dir / f"lesson-{lesson_n}.provenance.yaml"
                prov_bytes = lock.yaml_bytes(final_prov_doc)
                lock.write(prov_path, prov_bytes)
        except AssemblerError as exc:
            return CheckResult(check=9, passed=False, reason=f"{exc.code}: {exc.message}", layer=exc.layer)
        except Exception as exc:
            return CheckResult(check=9, passed=False, reason=f"provenance finalization failed: {exc}", layer="writer")

    if site_dir is not None:
        site_dir.mkdir(parents=True, exist_ok=True)
        mdx_file = site_dir / f"{lesson_n}.mdx"
        lock.atomic_write(mdx_file, mdx_content.encode("utf-8"))

    artifacts: dict[str, Any] = {
        "stressed_doc": stressed_doc,
        "vocab_items": vocab_items,
        "external_resources": external_resources,
        "mdx": mdx_content,
        "meta_data": meta_data,
    }
    if final_prov_doc is not None:
        artifacts["provenance"] = final_prov_doc

    return CheckResult(
        check=9,
        passed=True,
        artifacts=artifacts,
    )


def check_11_render(
    level: str,
    slug: str,
    *,
    astro_build: bool = False,
    module_dir: Path | None = None,
    plan_path: Path | None = None,
) -> CheckResult:
    """Check 11: verify_shippable --fresh on assembled site docs."""
    from scripts.build.verify_shippable import verify as vs_verify

    rep = vs_verify(level, slug, module_dir=module_dir, plan_path=plan_path, astro_build=astro_build, fresh=True)
    passed = bool(rep.get("shippable"))
    return CheckResult(
        check=11,
        passed=passed,
        reason=None if passed else "verify_shippable check 11 reported not shippable",
        layer=None if passed else "render",
        artifacts={"verify_shippable": rep},
    )


def assemble_lesson(
    level: str,
    slug: str,
    lesson_n: int,
    *,
    repo_root: Path | None = None,
    draft_dict: dict[str, Any] | None = None,
    plan_dict: dict[str, Any] | None = None,
    pack_dict: dict[str, Any] | None = None,
    words_dict: dict[str, Any] | None = None,
    output_dir: Path | None = None,
    site_dir: Path | None = None,
    astro_build: bool = False,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
) -> dict[str, Any]:
    """End-to-end assembly pipeline for one lesson (checks 5, 9, 11).

    Refuses site write on failures or open tokens, writing only state files.
    """
    root = repo_root or REPO_ROOT

    paths = lesson_lock.resolve_paths(level, slug, evidence_dir=evidence_dir, plans_dir=plans_dir, repo_root=root)
    state_dir = output_dir or (paths["evidence_dir"] / "_state" / slug)
    target_site_dir = site_dir or (root / "site" / "src" / "content" / "docs" / level / slug)

    plan = plan_dict if plan_dict is not None else yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    pack = pack_dict if pack_dict is not None else yaml.safe_load(paths["pack"].read_text(encoding="utf-8"))
    words_store = words_dict if words_dict is not None else yaml.safe_load(paths["words"].read_text(encoding="utf-8"))

    if draft_dict is None:
        draft_file = state_dir / f"lesson-{lesson_n}.draft.yaml"
        if not draft_file.is_file():
            raise FileNotFoundError(f"Draft file not found: {draft_file}")
        draft = yaml.safe_load(draft_file.read_text(encoding="utf-8"))
    else:
        draft = draft_dict

    if draft.get("status") != "ok":
        return {
            "ok": False,
            "failure": {
                "check": 5,
                "passed": False,
                "reason": f"{DRAFT_STATUS_NOT_OK}: draft status is {draft.get('status')!r}, expected 'ok'",
                "layer": "writer",
            },
        }

    # Check 5: Assembly
    c5 = check_5_assembly(draft, plan, pack, words_store, level, slug, lesson_n, output_dir=state_dir)
    if not c5.passed:
        return {"ok": False, "failure": c5.to_dict()}

    expanded_doc = c5.artifacts["expanded_doc"]

    # Resolver resolution
    try:
        from scripts.curriculum.resolver.stream import allowlist_for_lesson

        allowlist = allowlist_for_lesson(level, slug, lesson_n, evidence_dir=evidence_dir, plans_dir=plans_dir)
    except Exception:
        allowlist = Allowlist.from_records(words_store.get("words", []))

    try:
        sources = Sources()
    except Exception:
        sources = None
    stream = resolve(ExpandedDocument.from_data(expanded_doc), allowlist, sources)

    # Major 4: Check if stream has any failures or open tokens
    stream_failures = list(getattr(stream, "failures", []) or [])
    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])
    blocking_tokens: list[dict[str, Any]] = []
    for tok in tokens:
        if isinstance(tok, dict):
            klass = str(tok.get("class", ""))
            if (
                klass in resolver_codes.FAILURE_CLASSES
                or klass in ("stress_open", "stress_certain_identity_open")
                or klass in resolver_codes.OPEN_CLASSES
                or klass == "pending_stress"
                or (
                    tok.get("selected") is None
                    and not klass.startswith("skipped")
                    and klass != resolver_codes.LETTER_OR_SYLLABLE
                )
            ):
                blocking_tokens.append(tok)

    if stream_failures or blocking_tokens:
        # Refuse site write: write only state files and return report naming blocking tokens
        stressed_doc = apply_stress(expanded_doc, stream)
        write_stressed_document(stressed_doc, state_dir, lesson_n)
        return {
            "ok": False,
            "failure": {
                "check": 9,
                "passed": False,
                "reason": f"stream has {len(blocking_tokens)} blocking token(s) and {len(stream_failures)} failure(s); refusing site write",
                "layer": "stream",
            },
            "check_5": c5.to_dict(),
            "blocking_tokens": [str(t.get("token", "")) for t in blocking_tokens],
            "stream_failures": [str(f) for f in stream_failures],
            "message": f"stream has {len(blocking_tokens)} blocking token(s) and {len(stream_failures)} failure(s); refusing site write",
        }

    # Check 9: Stress and render (clean stream only writes site)
    c9 = check_9_stress_and_render(
        expanded_doc,
        draft,
        plan,
        pack,
        words_store,
        stream,
        level,
        slug,
        lesson_n,
        provenance_doc=c5.artifacts.get("provenance"),
        repo_root=root,
        output_dir=state_dir,
        site_dir=target_site_dir,
        plans_dir=plans_dir,
        evidence_dir=evidence_dir,
    )
    if not c9.passed:
        return {"ok": False, "failure": c9.to_dict()}

    # Check 11: Render shippable
    c11 = check_11_render(
        level,
        slug,
        astro_build=astro_build,
        module_dir=target_site_dir,
        plan_path=paths["plan"],
    )

    return {
        "ok": c5.passed and c9.passed and c11.passed,
        "check_5": c5.to_dict(),
        "check_9": c9.to_dict(),
        "check_11": c11.to_dict(),
        "mdx": c9.artifacts.get("mdx"),
        "frontmatter": c9.artifacts.get("meta_data"),
    }
