"""Prompt renderer and rendered-prompt validator (#8431 r3 §8.1).

Renders the lesson writer prompt from four inputs:
1. Plan entry
2. Cited evidence records
3. Learner state + immersion payload
4. Fixed style card
plus per-type activity item shapes rendered from the level schema and the draft schema summary.

The rendered-prompt check validates (#8431 §8.1):
- no unresolved placeholders ({{ ... }} not in valid inline markup, {% ... %}, TODO, None)
- no path or text of a v1 plan or curriculum/l2-uk-en/<level>-v1/
- no record id outside the plan entry's citations
- nothing from another lesson except the recap's built lessons
- the style card hash exists and matches disk
- the prompt sha256 is computed and recorded
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from scripts.build.fresh.draft_schema import (
    activity_definitions,
    activity_payload_schema,
)
from scripts.build.fresh.immersion import ImmersionPayload, compute_immersion_payload
from scripts.curriculum.learner_state.planned import PlannedState

__all__ = [
    "RenderedPromptCheckResult",
    "check_rendered_prompt",
    "compute_immersion_payload",
    "extract_plan_citations",
    "get_activity_item_shapes",
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

RECORD_ID_RE = re.compile(r"\b(?:W|EX|T|E|V|P|G|X|S)-[0-9a-zA-Z_-]+\b")
FORBIDDEN_V1_PATHS = (
    "curriculum/l2-uk-en/plans/",
    "curriculum/l2-uk-en/a1-v1/",
    "curriculum/l2-uk-en/a2-v1/",
    "curriculum/l2-uk-en/b1-v1/",
    "curriculum/l2-uk-en/b2-v1/",
    "curriculum/l2-uk-en/<level>-v1/",
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
) -> str:
    """Render the lesson writer prompt for a standard lesson."""
    p_dir = prompts_dir or PROMPTS_DIR
    env = Environment(
        loader=FileSystemLoader(str(p_dir)),
        undefined=StrictUndefined,
        autoescape=False,
    )
    template = env.get_template("lesson-writer.md.j2")

    card_path, card_content, card_sha256 = style_card_info(level)
    shapes = get_activity_item_shapes(level, schemas_dir)

    l_state = learner_state.to_dict() if isinstance(learner_state, PlannedState) else dict(learner_state)
    l_state["allowed_ids_count"] = (
        len(learner_state.all_allowed_ids)
        if isinstance(learner_state, PlannedState)
        else len(l_state.get("base_ids", [])) + len(l_state.get("core_ids", {})) + len(l_state.get("name_ids", {}))
    )

    imm_dict = immersion.to_dict() if isinstance(immersion, ImmersionPayload) else dict(immersion)

    # Ensure plan_entry has module key
    pe = dict(plan_entry)
    if "lesson" not in pe:
        pe["lesson"] = {"module": f"{level}/{slug}", "n": lesson_n}

    rendered = template.render(
        plan_entry=pe,
        level=level,
        slug=slug,
        cited_records=cited_records,
        learner_state=l_state,
        immersion=imm_dict,
        style_card_name=card_path.name,
        style_card_content=card_content,
        style_card_sha256=card_sha256,
        activity_item_shapes=shapes,
        plan_sha256=plan_sha256,
        pack_lock=pack_lock,
        words_lock=words_lock,
        lesson_lock_entry_sha256=lesson_lock_entry_sha256,
        learner_state_sha256=learner_state_sha256,
    )
    return rendered


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
) -> str:
    """Render the recap lesson prompt receiving built lessons 1..N-1."""
    p_dir = prompts_dir or PROMPTS_DIR
    env = Environment(
        loader=FileSystemLoader(str(p_dir)),
        undefined=StrictUndefined,
        autoescape=False,
    )
    template = env.get_template("lesson-recap-writer.md.j2")

    card_path, card_content, card_sha256 = style_card_info(level)
    shapes = get_activity_item_shapes(level, schemas_dir)

    l_state = learner_state.to_dict() if isinstance(learner_state, PlannedState) else dict(learner_state)
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
        cited_records=cited_records,
        learner_state=l_state,
        immersion=imm_dict,
        style_card_name=card_path.name,
        style_card_content=card_content,
        style_card_sha256=card_sha256,
        activity_item_shapes=shapes,
        plan_sha256=plan_sha256,
        pack_lock=pack_lock,
        words_lock=words_lock,
        lesson_lock_entry_sha256=lesson_lock_entry_sha256,
        learner_state_sha256=learner_state_sha256,
    )
    return rendered


def check_rendered_prompt(
    rendered_prompt: str,
    plan_entry: dict[str, Any],
    style_card_path: Path,
    *,
    is_recap: bool = False,
    built_lessons: list[dict[str, Any]] | None = None,
) -> RenderedPromptCheckResult:
    """Run deterministic check 0 on the rendered prompt (#8431 §8.1)."""
    errors: list[str] = []

    # 1. No unresolved placeholders
    # Unrendered Jinja statements:
    if "{%" in rendered_prompt or "%}" in rendered_prompt:
        errors.append("unresolved_placeholder: unrendered Jinja statement tag ({% or %}) found in prompt")

    # Double braces that are not valid markup:
    all_braces = re.findall(r"\{\{[^{}]*\}\}", rendered_prompt)
    for token in all_braces:
        if not VALID_DOUBLE_BRACE_RE.match(token):
            errors.append(f"unresolved_placeholder: invalid or unrendered double braces: {token!r}")

    for marker in ("<TODO>", "[TODO]", "<MISSING>", "__PLACEHOLDER__", "TODO:"):
        if marker in rendered_prompt:
            errors.append(f"unresolved_placeholder: placeholder token {marker!r} found in prompt")

    # Detect leaked None values from missing variables in template
    if re.search(r"\bNone\b", rendered_prompt) and not re.search(r"type:\s*None", rendered_prompt):
        # Check if None is part of an unrendered template field
        for line in rendered_prompt.splitlines():
            if ": None" in line and not line.strip().startswith("#"):
                errors.append(f"unresolved_placeholder: template variable rendered as 'None': {line.strip()!r}")

    # 2. No path, slug or text of a v1 plan or curriculum/l2-uk-en/<level>-v1/
    for forbidden in FORBIDDEN_V1_PATHS:
        if forbidden in rendered_prompt:
            errors.append(f"forbidden_v1_path: prompt contains v1 path reference {forbidden!r}")

    # 3. No record id outside the plan entry's citations (within cited records section)
    plan_citations = extract_plan_citations(plan_entry)
    records_section_match = re.search(
        r"## 2\. Cited Evidence Records(.*?)(?:---|\n## 3\.)",
        rendered_prompt,
        re.DOTALL,
    ) or re.search(
        r"## 3\. Cited Evidence Records(.*?)(?:---|\n## 4\.)",
        rendered_prompt,
        re.DOTALL,
    )
    if records_section_match:
        records_text = records_section_match.group(1)
        found_ids = set(RECORD_ID_RE.findall(records_text))
        for fid in found_ids:
            if fid not in plan_citations:
                errors.append(
                    f"uncited_record_id: record {fid!r} appears in cited records but is not cited in the plan entry"
                )

    # 4. Nothing from another lesson except the recap's built lessons
    current_lesson_n = plan_entry.get("lesson", {}).get("n") or plan_entry.get("n")
    if not is_recap:
        if "## Built Lessons of this Module" in rendered_prompt or "### Built Lesson" in rendered_prompt:
            errors.append("unauthorized_lesson_content: non-recap prompt contains built lessons of other lessons")
    else:
        # In recap prompt, built_lessons are expected
        if built_lessons:
            for bl in built_lessons:
                bl_n = bl.get("n")
                if bl_n is not None and current_lesson_n is not None and bl_n >= current_lesson_n:
                    errors.append(
                        f"recap_invalid_built_lesson: recap includes lesson {bl_n} >= current lesson {current_lesson_n}"
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
