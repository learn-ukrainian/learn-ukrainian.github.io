"""Prompt renderer and rendered-prompt validator (#8431 r3 §8.1).

Renders the lesson writer prompt from four inputs:
1. Plan entry
2. Cited evidence records
3. Learner state + immersion payload
4. Fixed style card
plus per-type activity item shapes rendered from the level schema and the draft schema summary.

The rendered-prompt check validates (#8431 §8.1):
- no unresolved placeholders ({{ ... }} not in valid inline markup, {% ... %}, TODO, None)
- no path, pattern, or text of a v1 plan or forbidden v1 path (-v1/, /plans/, etc.)
- uncited-id scan covers the WHOLE rendered prompt minus only the delimited schema exemplar
- nothing from another lesson by id: no record id and no lesson number outside this lesson's
  plan entry (except the recap's declared built lessons 1..N-1); the lesson-number scan skips the
  delimited cited-record block, whose source prose names the source's lessons, not this curriculum's (#9185)
- the delimited learner-state block is byte-identical to the block the planned state renders (letters,
  grammar ids with their points, word ids with their lemmas); its ids are admitted only inside it (#9182)
- the style card hash exists and matches disk
- the prompt sha256 is computed and recorded
"""

from __future__ import annotations

import functools
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Any

import jinja2
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from scripts.build.fresh.candidates import record_candidates
from scripts.build.fresh.draft_schema import (
    activity_definitions,
    activity_payload_schema,
)
from scripts.build.fresh.immersion import ImmersionPayload, compute_immersion_payload
from scripts.curriculum.learner_state.planned import PlannedState
from scripts.curriculum.validate.registry import load_registry

__all__ = [
    "RenderedPromptCheckResult",
    "check_rendered_prompt",
    "cited_record_views",
    "compute_immersion_payload",
    "extract_plan_citations",
    "get_activity_item_shapes",
    "grammar_points",
    "learner_state_block",
    "learner_state_view",
    "render_lesson_prompt",
    "render_recap_prompt",
    "style_card_info",
]

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = Path(__file__).parent / "prompts"
CARDS_DIR = REPO_ROOT / "docs" / "style-cards"

BAND_CARD_MAP = {
    "a1": "a1",
    "a2": "a2",
    "b1": "b1plus",
    "b2": "b1plus",
}

#: Valid inline markup pattern for allowed double braces:
#: {{gloss:W-...}}, {{uk:...}}, or {{<digits>}} for activity blanks.
VALID_DOUBLE_BRACE_RE = re.compile(r"^\{\{(?:gloss:(?:W-[0-9]+|W-[.…]+)|uk:[^{}\u0300\u0301]+|[0-9]+)\}\}$")

#: Prose references to a lesson number, and the ``lesson: {n: ...}`` shape of the schema exemplar.
LESSON_PROSE_RES = (re.compile(r"\b[Ll]esson\s+#?(\d+)\b"), re.compile(r"\b[Ll]esson-(\d+)\b"))
LESSON_NUMBER_RES = (*LESSON_PROSE_RES, re.compile(r"\blesson:\s*(?:\{[^}]*|\n[ ]*)n:\s*(\d+)"))

SCHEMA_EXEMPLAR_BEGIN = "<!-- BEGIN SCHEMA_SUMMARY_EXEMPLAR -->"
SCHEMA_EXEMPLAR_END = "<!-- END SCHEMA_SUMMARY_EXEMPLAR -->"

LEARNER_STATE_BEGIN = "<!-- BEGIN LEARNER_STATE -->"
LEARNER_STATE_END = "<!-- END LEARNER_STATE -->"
LEARNER_STATE_TEMPLATE = "_learner-state.md.j2"

CITED_RECORDS_BEGIN = "<!-- BEGIN CITED_RECORDS -->"
CITED_RECORDS_END = "<!-- END CITED_RECORDS -->"

EVIDENCE_PACK_SCHEMA = REPO_ROOT / "schemas" / "evidence-pack-v1.schema.json"

#: Record kind by id prefix: the ``<kind>_record`` definitions of the pack schema (their id patterns),
#: plus the word store's ``W-`` records.
RECORD_KINDS = {
    "W": "word",
    "T": "text",
    "X": "exercise",
    "EX": "example",
    "E": "error",
    "N": "note",
    "V": "video",
    "S": "standard",
    "U": "unsupported",
}

#: A record id in the shapes the schemas define: every ``RECORD_KINDS`` prefix (the pack kinds and ``W-<n>``) and
#: paradigm ``P-<n>`` (module-plan-v2), and grammar ``G-<level>-<nnn>``. A token that only starts like one
#: (``P-looking``, a video id ``W-1rCu0indE``) is not a record id (#9185).
RECORD_ID_RE = re.compile(
    r"\b(?:(?:"
    + "|".join(sorted({*RECORD_KINDS, "P"}, key=lambda p: (-len(p), p)))
    + r")-[0-9]+|G-[a-z0-9]+-[0-9]{3})\b"
)

#: Word-store fields the cited-records section reads (``gloss`` and ``forms`` are optional).
WORD_RECORD_FIELDS = ("lemma", "pos")

#: Source-dict fields printed as attribution, in order, per pack source kind (null and empty values are omitted).
SOURCE_FIELDS = {
    "textbook": (("author", ""), ("file", ""), ("grade", "grade "), ("page", "page ")),
    "literary": (("author", ""), ("work", ""), ("year", ""), ("file", ""), ("page", "page ")),
}

# Forbidden v1 path patterns per review finding 5 and §8.1
FORBIDDEN_V1_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"curriculum/l2-uk-en/(?:[a-c][1-2]|[a-z0-9]+)-v1/"),
    re.compile(r"curriculum/l2-uk-en/plans/"),
    re.compile(r"curriculum/l2-uk-en/plans\b"),
    re.compile(r"\b(?:[a-c][1-2]|[a-z][0-9])-v1/"),
    re.compile(r"(?:^|[\s/])-v1/"),
    re.compile(r"(?<!lesson-)plans/(?:[a-c][1-2]|[a-z0-9]+)/"),
    re.compile(r"(?<!lesson-)plans/"),
    re.compile(r"lesson-plans/[^/\s]+-v1(?:/|\b)"),
)


@dataclass(frozen=True)
class RenderedPromptCheckResult:
    """Result of check 0: rendered-prompt check (#8431 §8.1)."""

    passed: bool
    errors: list[str]
    prompt_sha256: str
    card_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": list(self.errors),
            "prompt_sha256": self.prompt_sha256,
            "card_sha256": self.card_sha256,
        }


def style_card_info(level: str, cards_dir: Path | None = None) -> tuple[Path, str, str]:
    """Retrieve the style card path, content, and sha256 for a given level."""
    root = cards_dir or CARDS_DIR
    lvl = level.lower().split("-")[0] if "-" in level else level.lower()
    card_base = BAND_CARD_MAP.get(lvl, "b1plus")
    card_path = root / f"{card_base}.md"
    sidecar_path = root / f"{card_base}.sha256"
    if root.name == "style-cards" and root.parent.name == "docs":
        from scripts.build.fresh.path_guard import checked_existing_path

        card_path = checked_existing_path(root.parent.parent, card_path, "docs/style-cards")
        sidecar_path = checked_existing_path(root.parent.parent, sidecar_path, "docs/style-cards")

    if not card_path.is_file():
        raise FileNotFoundError(f"style card not found: {card_path}")

    card_bytes = card_path.read_bytes()
    computed_sha = hashlib.sha256(card_bytes).hexdigest()

    if sidecar_path.is_file():
        sidecar_text = sidecar_path.read_text(encoding="utf-8").strip()
        sidecar_sha = sidecar_text.split()[0]
        if sidecar_sha != computed_sha:
            raise ValueError(
                f"style card sidecar mismatch for {card_path.name}: recorded {sidecar_sha}, actual {computed_sha}"
            )

    return card_path, card_bytes.decode("utf-8"), computed_sha


def get_activity_item_shapes(level: str, schemas_dir: Path | None = None) -> dict[str, Any]:
    """Render per-type activity item shapes for prompt formatting."""
    definitions = activity_definitions(level, schemas_dir)
    shapes: dict[str, Any] = {}
    for act_type, full_def in definitions.items():
        payload_schema = activity_payload_schema(full_def)
        properties = {}
        for prop, prop_def in payload_schema.get("properties", {}).items():
            properties[prop] = {
                "type": prop_def.get("type", "any"),
                "description": prop_def.get("description", ""),
            }
        shapes[act_type] = {
            "required": payload_schema.get("required", []),
            "properties": properties,
        }
    return shapes


def extract_plan_citations(plan_entry: dict[str, Any]) -> set[str]:
    """Collect all record IDs cited directly in the plan entry."""
    cited: set[str] = set()

    for step in plan_entry.get("steps", []):
        for field in ("explains", "evidence"):
            for item in step.get(field) or []:
                cited.add(str(item))
        ref = step.get("ref")
        if ref:
            cited.add(str(ref))
        paradigm = step.get("paradigm")
        if isinstance(paradigm, dict):
            if "id" in paradigm:
                cited.add(str(paradigm["id"]))
            if "word" in paradigm:
                cited.add(str(paradigm["word"]))

    for act in plan_entry.get("activities", []):
        for eref in act.get("error_refs") or []:
            cited.add(str(eref))
        cited.update(act.get("targets") or [])
        for selection in act.get("learner_reads") or []:
            cited.add(selection if isinstance(selection, str) else selection["ref"])
        if act.get("model"):
            cited.add(str(act["model"]))

    dialogue = plan_entry.get("dialogue")
    if isinstance(dialogue, dict):
        for ev in dialogue.get("evidence") or []:
            cited.add(str(ev))
        for spk in dialogue.get("speakers") or []:
            if isinstance(spk, dict) and "evidence" in spk:
                cited.add(str(spk["evidence"]))
        for plc in dialogue.get("places") or []:
            if isinstance(plc, dict) and "evidence" in plc:
                cited.add(str(plc["evidence"]))

    inv = plan_entry.get("inventory") or {}
    vocab = inv.get("vocabulary") or {}
    for item in vocab.get("core", []):
        if isinstance(item, dict) and "evidence" in item:
            cited.add(str(item["evidence"]))
    for item in vocab.get("incidental", []):
        if isinstance(item, dict) and "evidence" in item:
            cited.add(str(item["evidence"]))
    for r in vocab.get("recycled") or []:
        cited.add(str(r))

    for g in inv.get("grammar", []):
        if isinstance(g, dict) and "id" in g:
            cited.add(str(g["id"]))

    for vid in plan_entry.get("videos", []):
        if isinstance(vid, dict) and "evidence" in vid:
            cited.add(str(vid["evidence"]))

    return cited


def _plan_lesson_numbers(value: Any) -> set[int]:
    """Lesson numbers the plan entry's own text states (a rationale citing "ULP S1 lesson 10", a focus modelled on
    "lesson 2 a5"): part of this lesson's binding input, like the record ids it cites (#9185)."""
    if isinstance(value, str):
        return {int(m.group(1)) for pattern in LESSON_PROSE_RES for m in pattern.finditer(value)}
    items = value.values() if isinstance(value, Mapping) else value if isinstance(value, list) else ()
    return set().union(*(_plan_lesson_numbers(item) for item in items))


def _render_form_candidates(plan_entry: dict[str, Any], cited_records: dict[str, Any], *, level: str = "a1") -> str:
    """Show only cited store forms; the item demand selects the usable subset."""
    if not any(act.get("type") in {"fill-in", "quiz", "multiple-choice"} for act in plan_entry.get("activities", [])):
        return ""
    lines = [
        "## Form-choice candidate bank",
        "",
        (
            "Use one form from its bound record per option. State only the `requires` the sentence forces, "
            "not the key's features. If another reading fits (partitive genitive after request, offer, "
            "consumption or permission requests; genitive of negation; animate accusative/genitive syncretism), "
            "rewrite the context to force one reading or drop the item; never remove a `requires` group to repair it. "
            "A finite verb slot names `VerbForm: Fin` in `requires`; a plural slot omits `Gender` "
            "because plural forms carry no gender. Choose one admitted key. Each distractor must be "
            "a form that the sentence rules out by a feature the form itself carries. "
            "`tests_feature` names one focus group; the reviewer judges whether the distractors "
            "really make the learner choose along that focus. "
            "The engine generates the item-specific subset and checks every written option."
            if level == "a1"
            else "Use one form from its bound record per option. State the complete slot `requires`; "
            "choose one admitted key and distractors that differ in `tests_feature`. "
            "The engine generates the item-specific subset and checks every written option."
        ),
        "",
    ]
    found = False
    for record_id, record in sorted(cited_records.items()):
        if not record_id.startswith("W-") or not isinstance(record, dict):
            continue
        for candidate in record_candidates({**record, "id": record_id}):
            analyses = "; ".join(
                f"{analysis['tags']} [{', '.join(analysis['features'])}]" for analysis in candidate["analyses"]
            )
            lines.append(f"- `{record_id}`: `{candidate['form']}` — {analyses}")
            found = True
    if not found:
        return ""
    return "\n".join(lines) + "\n"


def grammar_points(registry_path: Path, level: str) -> dict[str, str]:
    """Grammar id -> point text from the level registry (``lesson-plans/<level>/_grammar.yaml``); {} when absent."""
    failures: list[Any] = []
    loaded = load_registry(registry_path, level, failures)
    if failures:
        raise ValueError(f"grammar registry {registry_path} is invalid: {[str(f) for f in failures]}")
    return {} if loaded is None else {record.id: record.point for record in loaded[0]}


def _state_dict(learner_state: PlannedState | dict[str, Any]) -> dict[str, Any]:
    return learner_state.to_dict() if isinstance(learner_state, PlannedState) else dict(learner_state)


def _id_key(identifier: str) -> tuple[str, int, str]:
    """Order W-2 before W-10 (numeric suffix), then by the full id."""
    match = re.match(r"^(.*?)(\d+)$", identifier)
    return (match.group(1), int(match.group(2)), identifier) if match else (identifier, -1, identifier)


def _letter_key(item: tuple[str, dict[str, int]]) -> tuple[int, int]:
    """Order by (position, lesson); the stable sort keeps the plans' introduction order within a lesson."""
    _, introduced = item
    return int(introduced.get("position", 0)), int(introduced.get("lesson", 0))


def learner_state_view(
    learner_state: PlannedState | dict[str, Any],
    word_store: Mapping[str, Any] | None,
    points: Mapping[str, str] | None,
) -> dict[str, Any]:
    """The complete planned state before this lesson, as the writer reads it (#9182).

    Built from the ``to_dict()`` document the lesson reviewer receives and ``learner_state_sha256``
    hashes; it only adds each word's lemma from the word store and each grammar id's point from the
    grammar registry. An id with no lemma or point fails the render: the writer must see the whole state.
    """
    state = _state_dict(learner_state)
    lemmas = {
        rec["id"]: rec.get("lemma")
        for rec in (word_store or {}).get("words") or []
        if isinstance(rec, dict) and "id" in rec
    }
    points = points or {}
    base = set(state.get("base_ids") or [])
    core = set(state.get("core_ids") or {}) - base
    names = set(state.get("name_ids") or {}) - base - core
    unresolved: list[str] = []

    def words(ids: set[str]) -> list[dict[str, str]]:
        rows = [{"id": wid, "lemma": lemmas.get(wid) or ""} for wid in sorted(ids, key=_id_key)]
        unresolved.extend(row["id"] for row in rows if not row["lemma"])
        return rows

    view = {
        "letters": [letter for letter, _ in sorted((state.get("letters") or {}).items(), key=_letter_key)],
        "grammar": [
            {"id": gid, "point": points.get(gid) or ""} for gid in sorted(state.get("grammar_ids") or {}, key=_id_key)
        ],
        "base": words(base),
        "core": words(core),
        "names": words(names),
    }
    unresolved.extend(row["id"] for row in view["grammar"] if not row["point"])
    if unresolved:
        raise ValueError(f"learner_state_unresolved: no lemma or grammar point for {unresolved}")
    view["word_count"] = len(base) + len(core) + len(names)
    return view


@functools.cache
def _pack_required_fields() -> dict[str, tuple[str, ...]]:
    """Kind -> required fields of every ``<kind>_record`` definition in the evidence-pack v1 schema."""
    defs = json.loads(EVIDENCE_PACK_SCHEMA.read_text(encoding="utf-8"))["$defs"]
    return {
        name.removesuffix("_record"): tuple(spec["required"]) for name, spec in defs.items() if name.endswith("_record")
    }


def _format_source(source: Mapping[str, Any]) -> str:
    """One attribution line from a pack record's ``source`` dict; a null or empty field is left out."""
    if "table" in source:
        return f"{source['table']} row {source['id']}"
    kind = source.get("kind")
    if kind not in SOURCE_FIELDS:
        raise ValueError(f"cited_record_invalid: unknown source kind {kind!r} in {sorted(source)}")
    parts = [f"{label}{source[key]}" for key, label in SOURCE_FIELDS[kind] if source.get(key) not in (None, "")]
    return f"{kind}: {', '.join(parts)}"


def cited_record_views(cited_records: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Each cited record with its kind and formatted source, as the cited-records section renders it (#9185).

    The kind comes from the id prefix; the fields are the schema's (``schemas/evidence-pack-v1.schema.json``)
    or the word store's. An unknown kind or a missing field fails the render: nothing is dumped raw.
    """
    required = {**_pack_required_fields(), "word": WORD_RECORD_FIELDS}
    views = []
    for record_id, record in cited_records.items():
        kind = RECORD_KINDS.get(str(record_id).split("-", 1)[0])
        if kind is None or kind not in required:
            raise ValueError(f"cited_record_invalid: {record_id!r} is not a known record kind")
        missing = [field for field in required[kind] if field != "id" and field not in record]
        if missing:
            raise ValueError(f"cited_record_invalid: {kind} record {record_id!r} lacks {missing}")
        source = record.get("source")
        views.append(
            {
                "id": record_id,
                "kind": kind,
                "record": record,
                "source": _format_source(source) if isinstance(source, Mapping) else None,
            }
        )
    return views


def _fenced(text: str) -> str:
    """A fenced block holding ``text`` byte for byte; the fence outruns any backtick run inside it."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}text\n{text}\n{fence}"


def _unrendered_record_kind(record_id: str, kind: str) -> str:
    raise ValueError(f"cited_record_invalid: no rendering for {kind} record {record_id!r}")


def _literal_json(value: Any) -> str:
    """JSON for Markdown writer prompts, preserving Ukrainian and apostrophes verbatim."""
    return json.dumps(value, ensure_ascii=False)


def _environment(prompts_dir: Path | None) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(prompts_dir or PROMPTS_DIR)),
        undefined=StrictUndefined,
        autoescape=jinja2.select_autoescape(
            enabled_extensions=("html", "htm", "xml"), default_for_string=False, default=False
        ),
    )
    env.filters["fenced"] = _fenced
    env.filters["literal_json"] = _literal_json
    env.globals["unrendered_record_kind"] = _unrendered_record_kind
    return env


def learner_state_block(
    learner_state: PlannedState | dict[str, Any],
    word_store: Mapping[str, Any] | None,
    points: Mapping[str, str] | None,
    *,
    prompts_dir: Path | None = None,
) -> str:
    """The exact text between the learner-state markers that both writer prompts render for this state."""
    rendered = (
        _environment(prompts_dir)
        .get_template(LEARNER_STATE_TEMPLATE)
        .render(taught=learner_state_view(learner_state, word_store, points))
    )
    return rendered.split(LEARNER_STATE_BEGIN, 1)[1].split(LEARNER_STATE_END, 1)[0]


def _block_difference(expected: str, found: str) -> str:
    """Name the first line where the prompt's learner-state block departs from the state's rendering."""
    want, got = expected.splitlines(), found.splitlines()
    for number, (a, b) in enumerate(zip_longest(want, got, fillvalue="<no line>"), start=1):
        if a != b:
            return f"learner_state_mismatch: block line {number} is {b!r}; the planned state renders {a!r}"
    return "learner_state_mismatch: the block differs from the planned state's rendering in whitespace"


def render_lesson_prompt(
    plan_entry: dict[str, Any],
    cited_records: dict[str, Any],
    learner_state: PlannedState | dict[str, Any],
    immersion: ImmersionPayload | dict[str, Any],
    *,
    level: str,
    slug: str,
    lesson_n: int,
    style_card_path: Path | None = None,
    schemas_dir: Path | None = None,
    plan_sha256: str = "0" * 64,
    pack_lock: str = "0" * 64,
    words_lock: str = "0" * 64,
    lesson_lock_entry_sha256: str = "0" * 64,
    learner_state_sha256: str = "0" * 64,
    prompts_dir: Path | None = None,
    word_store: Mapping[str, Any] | None = None,
    grammar_registry: Mapping[str, str] | None = None,
) -> str:
    """Render the lesson writer prompt for a standard lesson.

    ``word_store`` (the loaded ``_words.yaml``) and ``grammar_registry`` (grammar id -> point, see
    ``grammar_points``) resolve the lemmas and grammar points of the learner-state section.
    """
    env = _environment(prompts_dir)
    template = env.get_template("lesson-writer.md.j2")

    if style_card_path is not None:
        card_path = Path(style_card_path)
        card_bytes = card_path.read_bytes()
        card_sha256 = hashlib.sha256(card_bytes).hexdigest()
        card_content = card_bytes.decode("utf-8")
        card_name = card_path.name
    else:
        card_path, card_content, card_sha256 = style_card_info(level)
        card_name = card_path.name

    shapes = get_activity_item_shapes(level, schemas_dir)

    l_state = _state_dict(learner_state)
    l_state["allowed_ids_count"] = (
        len(learner_state.all_allowed_ids)
        if isinstance(learner_state, PlannedState)
        else len(l_state.get("base_ids", [])) + len(l_state.get("core_ids", {})) + len(l_state.get("name_ids", {}))
    )

    imm_dict = immersion.to_dict() if isinstance(immersion, ImmersionPayload) else dict(immersion)

    pe = dict(plan_entry)
    if "lesson" not in pe:
        pe["lesson"] = {"module": f"{level}/{slug}", "n": lesson_n}

    rendered = template.render(
        plan_entry=pe,
        level=level,
        slug=slug,
        cited_records=cited_record_views(cited_records),
        learner_state=l_state,
        taught=learner_state_view(learner_state, word_store, grammar_registry),
        immersion=imm_dict,
        style_card_name=card_name,
        style_card_content=card_content,
        style_card_sha256=card_sha256,
        activity_item_shapes=shapes,
        plan_sha256=plan_sha256,
        pack_lock=pack_lock,
        words_lock=words_lock,
        lesson_lock_entry_sha256=lesson_lock_entry_sha256,
        learner_state_sha256=learner_state_sha256,
    )
    candidates = _render_form_candidates(pe, cited_records, level=level)
    return rendered + ("\n" + candidates if candidates else "")


def render_recap_prompt(
    plan_entry: dict[str, Any],
    built_lessons: list[dict[str, Any]],
    cited_records: dict[str, Any],
    learner_state: PlannedState | dict[str, Any],
    immersion: ImmersionPayload | dict[str, Any],
    *,
    level: str,
    slug: str,
    lesson_n: int,
    style_card_path: Path | None = None,
    schemas_dir: Path | None = None,
    plan_sha256: str = "0" * 64,
    pack_lock: str = "0" * 64,
    words_lock: str = "0" * 64,
    lesson_lock_entry_sha256: str = "0" * 64,
    learner_state_sha256: str = "0" * 64,
    prompts_dir: Path | None = None,
    word_store: Mapping[str, Any] | None = None,
    grammar_registry: Mapping[str, str] | None = None,
) -> str:
    """Render the recap lesson prompt receiving built lessons 1..N-1 (``word_store`` and
    ``grammar_registry`` as in ``render_lesson_prompt``)."""
    env = _environment(prompts_dir)
    template = env.get_template("lesson-recap-writer.md.j2")

    if style_card_path is not None:
        card_path = Path(style_card_path)
        card_bytes = card_path.read_bytes()
        card_sha256 = hashlib.sha256(card_bytes).hexdigest()
        card_content = card_bytes.decode("utf-8")
        card_name = card_path.name
    else:
        card_path, card_content, card_sha256 = style_card_info(level)
        card_name = card_path.name

    shapes = get_activity_item_shapes(level, schemas_dir)

    l_state = _state_dict(learner_state)
    l_state["allowed_ids_count"] = (
        len(learner_state.all_allowed_ids)
        if isinstance(learner_state, PlannedState)
        else len(l_state.get("base_ids", [])) + len(l_state.get("core_ids", {})) + len(l_state.get("name_ids", {}))
    )

    imm_dict = immersion.to_dict() if isinstance(immersion, ImmersionPayload) else dict(immersion)

    pe = dict(plan_entry)
    if "lesson" not in pe:
        pe["lesson"] = {"module": f"{level}/{slug}", "n": lesson_n}

    rendered = template.render(
        plan_entry=pe,
        level=level,
        slug=slug,
        built_lessons=built_lessons,
        cited_records=cited_record_views(cited_records),
        learner_state=l_state,
        taught=learner_state_view(learner_state, word_store, grammar_registry),
        immersion=imm_dict,
        style_card_name=card_name,
        style_card_content=card_content,
        style_card_sha256=card_sha256,
        activity_item_shapes=shapes,
        plan_sha256=plan_sha256,
        pack_lock=pack_lock,
        words_lock=words_lock,
        lesson_lock_entry_sha256=lesson_lock_entry_sha256,
        learner_state_sha256=learner_state_sha256,
    )
    candidates = _render_form_candidates(pe, cited_records, level=level)
    return rendered + ("\n" + candidates if candidates else "")


def check_rendered_prompt(
    rendered_prompt: str,
    plan_entry: dict[str, Any],
    style_card_path: Path,
    *,
    is_recap: bool = False,
    built_lessons: list[dict[str, Any]] | None = None,
    learner_state: PlannedState | dict[str, Any] | None = None,
    word_store: Mapping[str, Any] | None = None,
    grammar_registry: Mapping[str, str] | None = None,
    prompts_dir: Path | None = None,
) -> RenderedPromptCheckResult:
    """Run deterministic check 0 on the rendered prompt (#8431 §8.1).

    ``learner_state``, ``word_store`` and ``grammar_registry`` are what the prompt was rendered from; the
    learner-state block must equal the block they render, byte for byte (#9182).
    """
    errors: list[str] = []

    # 1. No unresolved placeholders
    if "{%" in rendered_prompt or "%}" in rendered_prompt:
        errors.append("unresolved_placeholder: unrendered Jinja statement tag ({% or %}) found in prompt")

    all_braces = re.findall(r"\{\{[^{}]*\}\}", rendered_prompt)
    for token in all_braces:
        if not VALID_DOUBLE_BRACE_RE.match(token):
            errors.append(f"unresolved_placeholder: invalid or unrendered double braces: {token!r}")

    for marker in ("<TODO>", "[TODO]", "<MISSING>", "__PLACEHOLDER__", "TODO:"):
        if marker in rendered_prompt:
            errors.append(f"unresolved_placeholder: placeholder token {marker!r} found in prompt")

    if re.search(r"\bNone\b", rendered_prompt) and not re.search(r"type:\s*None", rendered_prompt):
        for line in rendered_prompt.splitlines():
            if ": None" in line and not line.strip().startswith("#"):
                errors.append(f"unresolved_placeholder: template variable rendered as 'None': {line.strip()!r}")

    # 2. No path, slug or text of a v1 plan using path patterns (#8431 §8.1, Finding 5)
    for pat in FORBIDDEN_V1_PATTERNS:
        match = pat.search(rendered_prompt)
        if match:
            errors.append(
                f"forbidden_v1_path: prompt contains v1 path reference matching {pat.pattern!r}: {match.group(0)!r}"
            )

    # 3. Delimited schema-summary exemplar block and whole-prompt uncited-id scan (#8431 §8.1, Finding 5)
    if SCHEMA_EXEMPLAR_BEGIN not in rendered_prompt or SCHEMA_EXEMPLAR_END not in rendered_prompt:
        errors.append("missing_schema_summary_marker: schema-summary exemplar block delimiters missing from prompt")
        prompt_for_id_scan = rendered_prompt
    else:
        # Strip only the delimited exemplar block; scan remainder of whole prompt
        before, rest = rendered_prompt.split(SCHEMA_EXEMPLAR_BEGIN, 1)
        after = rest.split(SCHEMA_EXEMPLAR_END, 1)[1]
        prompt_for_id_scan = before + "\n" + after

    # 3b. The learner-state block is exactly the planned state's rendering; its ids are admitted only inside it (#9182)
    if LEARNER_STATE_BEGIN not in prompt_for_id_scan or LEARNER_STATE_END not in prompt_for_id_scan:
        errors.append("missing_learner_state_marker: learner-state block delimiters missing from prompt")
    else:
        before, rest = prompt_for_id_scan.split(LEARNER_STATE_BEGIN, 1)
        block, after = rest.split(LEARNER_STATE_END, 1)
        prompt_for_id_scan = before + "\n" + after
        if learner_state is None:
            errors.append("learner_state_unverified: the check needs the learner state the prompt was rendered from")
        else:
            try:
                expected = learner_state_block(learner_state, word_store, grammar_registry, prompts_dir=prompts_dir)
            except ValueError as err:
                errors.append(str(err))
            else:
                if block != expected:
                    errors.append(_block_difference(expected, block))

    plan_citations = extract_plan_citations(plan_entry)
    found_ids = set(RECORD_ID_RE.findall(prompt_for_id_scan))
    for fid in sorted(found_ids):
        if fid not in plan_citations:
            errors.append(f"uncited_record_id: record {fid!r} appears in prompt but is not cited in the plan entry")

    # 4. Nothing from another lesson by id or number (Finding 5)
    current_lesson_n = plan_entry.get("lesson", {}).get("n") or plan_entry.get("n")
    allowed_lesson_numbers = _plan_lesson_numbers(plan_entry)
    if current_lesson_n is not None:
        allowed_lesson_numbers.add(int(current_lesson_n))

    if not is_recap:
        if "## Built Lessons of this Module" in rendered_prompt or "### Built Lesson" in rendered_prompt:
            errors.append("unauthorized_lesson_content: non-recap prompt contains built lessons of other lessons")
    else:
        if built_lessons:
            for bl in built_lessons:
                bl_n = bl.get("n")
                if bl_n is not None:
                    allowed_lesson_numbers.add(int(bl_n))
                    if current_lesson_n is not None and bl_n >= current_lesson_n:
                        errors.append(
                            f"recap_invalid_built_lesson: recap includes lesson {bl_n} >= current lesson {current_lesson_n}"
                        )

    # Check for unauthorized lesson numbers across the prompt, except the ones the plan entry states, and excluding
    # the schema exemplar and the cited records, whose source prose - a `supports` line, a video's `use`, quoted
    # lesson notes - names lessons of the source, not of this curriculum (#9185)
    prompt_for_lesson_scan = prompt_for_id_scan
    if CITED_RECORDS_BEGIN not in prompt_for_id_scan or CITED_RECORDS_END not in prompt_for_id_scan:
        errors.append("missing_cited_records_marker: cited-records block delimiters missing from prompt")
    else:
        before, rest = prompt_for_id_scan.split(CITED_RECORDS_BEGIN, 1)
        prompt_for_lesson_scan = before + "\n" + rest.split(CITED_RECORDS_END, 1)[1]
    for lpat in LESSON_NUMBER_RES:
        for m in lpat.finditer(prompt_for_lesson_scan):
            lnum = int(m.group(1))
            if lnum not in allowed_lesson_numbers:
                errors.append(
                    f"unauthorized_lesson_number: lesson number {lnum} appears in prompt but does not belong to this lesson or allowed recap lessons"
                )

    # 5. The style card hash exists and matches
    if not style_card_path.is_file():
        errors.append(f"card_hash_missing: style card file {style_card_path} does not exist")
        card_sha256 = ""
    else:
        card_sha256 = hashlib.sha256(style_card_path.read_bytes()).hexdigest()
        if card_sha256 not in rendered_prompt:
            errors.append(f"card_hash_mismatch: prompt does not record expected card sha256 {card_sha256}")

    # 6. Record prompt sha256
    prompt_sha256 = hashlib.sha256(rendered_prompt.encode("utf-8")).hexdigest()

    return RenderedPromptCheckResult(
        passed=(len(errors) == 0),
        errors=errors,
        prompt_sha256=prompt_sha256,
        card_sha256=card_sha256,
    )
