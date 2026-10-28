"""Frozen judge prompt, judge planning in both orders, and verdict validation.

Every judge sees every task twice: A as Text 1 (order ``AB``) and B as Text 1
(order ``BA``). Texts are relabelled 1 and 2 so a judge never sees the blind
A/B labels; each verdict is mapped back to A/B here and to writers only at
unblinding. Failed, unrun and abstaining judgements are kept as records.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

import jsonschema

from scripts.eval.uk_preamble.common import SEATS, HarnessError, Seat, sha256_text
from scripts.eval.uk_preamble.prompts import JUDGE_CRITERIA as PREAMBLE_CRITERIA
from scripts.eval.uk_preamble.prompts import extract_json
from scripts.eval.uk_preamble.runner import TaskSpec, load_raw, render
from scripts.eval.uk_preamble.scoring import task_state

from .core import Manifest

TASK_PREFIX = "ukab"
ORDERS = {"AB": ("A", "B"), "BA": ("B", "A")}  # order -> (side shown as Text 1, side shown as Text 2)
# The preamble harness's four criteria, plus pedagogy and plan fidelity (fact check against the plan).
JUDGE_CRITERIA = (*PREAMBLE_CRITERIA, "pedagogy", "plan_fidelity")
SEVERITIES = ("P0", "P1", "P2")
PREFERENCES = ("1", "2", "tie", "abstain")

_NULLABLE_CRITERION = {"type": ["integer", "null"], "minimum": 1, "maximum": 5}
_TEXT_VERDICT = {
    "type": "object",
    "additionalProperties": False,
    "required": ["criteria", "score", "errors"],
    "properties": {
        "criteria": {
            "type": "object",
            "additionalProperties": False,
            "required": list(JUDGE_CRITERIA),
            "properties": dict.fromkeys(JUDGE_CRITERIA, _NULLABLE_CRITERION),
        },
        "score": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["quote", "correction", "kind", "severity"],
                "properties": {
                    "quote": {"type": "string"},
                    "correction": {"type": "string"},
                    "kind": {"enum": ["language", "stress", "fact", "pedagogy", "task"]},
                    "severity": {"enum": list(SEVERITIES)},
                },
            },
        },
    },
}
JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "text_1", "text_2", "preferred", "rationale", "sources_checked"],
    "properties": {
        "id": {"type": "string"},
        "text_1": _TEXT_VERDICT,
        "text_2": _TEXT_VERDICT,
        "preferred": {"enum": list(PREFERENCES)},
        "rationale": {"type": "string"},
        "sources_checked": {"type": "boolean"},
    },
}

JUDGE_INSTRUCTIONS = f"""# Task: blind judgement of two Ukrainian lesson sections

Two anonymous writers each wrote one learner-facing lesson section from the same writing prompt and module \
plan, both given below. Their texts are Text 1 and Text 2. The order is random and carries no information; \
do not try to work out who wrote which.

Judge each text on its own first, then compare them. Criteria, each scored 1 (poor) to 5 (excellent):
- naturalness: idiomatic, native-like Ukrainian without calques, Russianisms or surzhyk;
- correctness: grammar, agreement, case government and spelling by Правопис 2019, and correct stress marks;
- task_fit: does what the writing prompt asks (the section, length, format, stress marking, language of explanations);
- level_fit: vocabulary and structures suit the plan's CEFR level;
- pedagogy: clear explanations, sound progression and useful practice for this learner at this point of the plan;
- plan_fidelity: covers the plan's section (vocabulary, situations, grammar focus) and states no fact the plan \
does not support.

Fact check: compare every factual claim (people, places, dates, history, culture, and claims about the \
language itself) with the plan; a claim the plan does not support, or that is wrong, is an error of kind `fact`.

Errors: list every error with the exact quote from the text, the correction, its kind (language, stress, fact, \
pedagogy, task) and its severity: P0 = would teach the learner something wrong (wrong form, wrong fact, a \
Russianism presented as correct); P1 = a clear defect that does not mislead; P2 = style or minor.

SCORE per text, 1 to 10, anchored on the errors: 10 = no errors; 7-9 = only P2 errors; 4-6 = at least one \
P1 and no P0; 1-3 = a P0 or off-task.

Requirements for the judgement:
- Judge quality, not length: a longer or shorter text earns nothing for its length alone.
- `preferred` is "1", "2" or "tie"; use "abstain" only when you cannot judge, and say why in `rationale`. \
A score or criterion you cannot judge is null.
- When your environment provides the Sources tools (VESUM, stress, Russianism checks), verify word forms, \
stress and suspected Russianisms with them, not from memory, and set `sources_checked` to true; otherwise false.
- `rationale` is at most three sentences; `id` is the comparison id given below.
- The answer is one JSON object that matches the output schema below and nothing else: no prose, no Markdown fence.

Criteria keys: {", ".join(JUDGE_CRITERIA)}.
"""


def template_sha256() -> str:
    """Hash of the judge instructions and schema; frozen with the results directory."""
    return sha256_text(json.dumps([JUDGE_INSTRUCTIONS, JUDGE_SCHEMA], ensure_ascii=False, sort_keys=True))


def build_judge_prompt(comparison_id: str, prompt_text: str, plan_text: str, text_1: str, text_2: str) -> str:
    schema = json.dumps(JUDGE_SCHEMA, ensure_ascii=False, indent=2)
    parts = [
        JUDGE_INSTRUCTIONS.strip(),
        f"Output schema:\n```json\n{schema}\n```",
        f"Comparison id: {comparison_id}",
        f"<writing_prompt>\n{prompt_text.strip()}\n</writing_prompt>",
        f"<plan>\n{plan_text.strip()}\n</plan>",
        f"<text_1>\n{text_1.strip()}\n</text_1>",
        f"<text_2>\n{text_2.strip()}\n</text_2>",
    ]
    return "\n\n".join(parts) + "\n"


def resolve_judges(seat_ids: Sequence[str], writer_families: Sequence[str]) -> list[Seat]:
    """Judge seats, each required to be outside every writer's model family."""
    judges = []
    for seat_id in dict.fromkeys(seat_ids):
        if seat_id not in SEATS:
            raise HarnessError(f"unknown judge seat {seat_id!r}; known: {', '.join(SEATS)}")
        seat = SEATS[seat_id]
        if seat.family in writer_families:
            raise HarnessError(f"judge {seat_id} is in a writer's family ({seat.family}); judges must be outside them")
        judges.append(seat)
    return judges


def plan_judge_tasks(manifest: Manifest, judges: Sequence[Seat], run_tag: str, block: str) -> list[TaskSpec]:
    """One task per judge, lesson task and order; the prompt carries the rules core block first."""
    tasks = []
    for judge in judges:
        for task in manifest.tasks:
            for order, (first, second) in ORDERS.items():
                prompt = render(
                    build_judge_prompt(
                        task.task_id, task.prompt_text, task.plan_text, task.texts[first], task.texts[second]
                    ),
                    block,
                )
                task_id = (
                    f"{TASK_PREFIX}-{run_tag}-{judge.code}-{task.task_id}-{order.lower()}-{sha256_text(prompt)[:8]}"
                )
                meta = {"lesson_task": task.task_id, "order": order, "text_1": first, "text_2": second}
                tasks.append(TaskSpec(task_id, judge, "judge", None, 1, (task.task_id,), prompt, meta))
    return tasks


def validate_verdict(response_text: str | None, comparison_id: str) -> tuple[dict[str, Any] | None, str | None]:
    if response_text is None:
        return None, "no response"
    try:
        entry = extract_json(response_text)
    except ValueError as exc:
        return None, f"unparseable response: {exc}"
    errors = sorted(jsonschema.Draft202012Validator(JUDGE_SCHEMA).iter_errors(entry), key=lambda e: list(e.path))
    if errors:
        where = "/".join(str(part) for part in errors[0].absolute_path) or "<answer>"
        return None, f"schema violation at {where}: {errors[0].message}"
    if entry["id"] != comparison_id:
        return None, f"answer id {entry['id']!r} is not {comparison_id!r}"
    return entry, None


def score_judgements(results: Any, tasks: Sequence[TaskSpec]) -> list[dict[str, Any]]:
    """Every planned judgement, mapped back to blind sides A/B; failures and abstentions are kept."""
    records = []
    for spec in tasks:
        raw = load_raw(results, spec.task_id)
        meta = spec.meta
        record = {
            "dispatch_task_id": spec.task_id,
            "judge": spec.seat.seat_id,
            "judge_family": spec.seat.family,
            "task_id": meta["lesson_task"],
            "order": meta["order"],
            "task_state": task_state(raw),
        }
        if raw is None:
            entry, reason = None, "task not run"
        elif not raw.get("accepted"):
            entry = None
            reason = raw.get("identity_problem") or raw.get("condition_problem") or f"task status {raw.get('status')}"
        else:
            entry, reason = validate_verdict(raw.get("response_text"), meta["lesson_task"])
        if entry is None:
            records.append({**record, "failed": True, "reason": reason, "preferred": None, "texts": None})
            continue
        side_of = {"1": meta["text_1"], "2": meta["text_2"]}
        texts = {side_of[n]: entry[f"text_{n}"] for n in ("1", "2")}
        preferred = side_of.get(entry["preferred"], entry["preferred"])
        records.append(
            {
                **record,
                "failed": False,
                "reason": None,
                "preferred": preferred,
                "preferred_position": entry["preferred"],
                "texts": texts,
                "rationale": entry["rationale"],
                "sources_checked": entry["sources_checked"],
            }
        )
    return records
