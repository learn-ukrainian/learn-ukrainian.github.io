"""Question and answer exchange for A1 form requirement confirmation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.build.fresh.prompt import _environment
from scripts.curriculum.evidence import lock
from scripts.curriculum.resolver import codes, receipts
from scripts.curriculum.resolver.inputs import ResolverError
from scripts.review.second_seat import IdentityError
from scripts.review.second_seat import writer_family as lesson_writer_family

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _bad(message: str) -> ResolverError:
    return ResolverError(codes.INVALID_ANSWER, message)


def questions_from_draft(draft: dict[str, Any], lesson: dict[str, Any], inputs: dict[str, str]) -> dict[str, Any]:
    """Capture each form item in authored order, including its resolved answer index."""
    from scripts.build.fresh.runner import _choice_key, _choice_text

    questions = []
    by_type = {activity["id"]: activity["type"] for activity in lesson.get("activities") or []}
    for activity in draft.get("activities") or []:
        aid = activity["id"]
        typ = activity.get("type") or by_type.get(aid)
        for index, item in enumerate(activity.get("items") or []):
            if item.get("kind") != "form":
                continue
            raw = item.get("options")
            if not isinstance(raw, list) or not raw:
                raise _bad(f"{aid}/{index}: form options are missing")
            options = [_choice_text(option) for option in raw]
            key = _choice_key(item, typ, raw)
            if any(not isinstance(option, str) for option in options) or key is None or not 0 <= key < len(options):
                raise _bad(f"{aid}/{index}: invalid option or key")
            sentence, demand = receipts.requirement_sentence(item), item.get("requires")
            if not sentence or not isinstance(demand, dict):
                raise _bad(f"{aid}/{index}: invalid sentence or requires")
            questions.append(
                {
                    "activity": aid,
                    "item": index,
                    "sentence": sentence,
                    "options": options,
                    "key_index": key,
                    "requires": demand,
                    "payload_sha256": receipts.requirement_payload_sha256(sentence, options, key, demand),
                }
            )
    return {"lesson": lesson["lesson"], "inputs": inputs, "questions": questions}


def write_questions(state_dir: Path, n: int, batch: dict[str, Any]) -> None:
    questions_path = state_dir / f"lesson-{n}.requires-questions.yaml"
    lock.write(questions_path, lock.yaml_bytes(batch))
    prompt = (
        _environment(PROMPTS_DIR)
        .get_template("requires-confirm.md.j2")
        .render(batch=batch)
    )
    lock.atomic_write(state_dir / f"lesson-{n}.requires-confirm.prompt.md", prompt.encode("utf-8"))


def record_answers(
    batch: dict[str, Any],
    answers: Any,
    *,
    seat: str,
    family: str,
    writer_seat: str,
    writer_family: str,
    state_dir: Path,
    sources: Any = None,
) -> dict[str, Any]:
    """Reject incomplete, reordered, unsupported or internally inconsistent judgements."""
    for value in (seat, family, writer_seat, writer_family):
        receipts._check_seat(value)
    if family.casefold() != receipts.language_seat_family(
        seat, what="reviewer"
    ) or writer_family.casefold() != receipts._seat_family(writer_seat, what="writer"):
        raise _bad("seat and model family disagree")
    try:
        actual_writer_family = lesson_writer_family(state_dir, batch["lesson"]["n"])
    except IdentityError as exc:
        raise _bad(f"lesson writer family unavailable: {exc}") from exc
    if writer_family.casefold() != actual_writer_family:
        raise _bad("writer family disagrees with lesson writer record")
    if family.casefold() == writer_family.casefold():
        raise _bad("reviewer and writer share a model family")
    if not isinstance(answers, dict) or set(answers) != {"answers"} or not isinstance(answers["answers"], list):
        raise _bad("answers must contain exactly one answers list")
    by_locator = {(q["activity"], q["item"]): q for q in batch["questions"]}
    rows = []
    seen = set()
    for answer in answers["answers"]:
        if not isinstance(answer, dict) or set(answer) != {
            "activity",
            "item",
            "decision",
            "reason",
            "requires_forced",
            "options",
        }:
            raise _bad("malformed answer fields")
        locator = (answer["activity"], answer["item"])
        if locator in seen or locator not in by_locator:
            raise _bad(f"duplicate or unknown answer {locator!r}")
        seen.add(locator)
        question = by_locator[locator]
        options = answer["options"]
        if not isinstance(options, list) or len(options) != len(question["options"]):
            raise _bad(f"{locator!r}: wrong option list")
        if [option.get("text") if isinstance(option, dict) else None for option in options] != question["options"]:
            raise _bad(f"{locator!r}: option text or order differs from question")
        key = question["key_index"]
        confirmable = answer["requires_forced"] is True and all(
            option.get("judgement") == ("valid" if i == key else "invalid")
            and isinstance(option.get("evidence"), list)
            and option["evidence"]
            for i, option in enumerate(options)
        )
        if answer["decision"] == "confirm" and not confirmable:
            raise _bad(f"{locator!r}: confirm needs a forced demand and source-backed unique key")
        if answer["decision"] == "deny" and confirmable:
            raise _bad(f"{locator!r}: a fully confirmed judgement must be confirm")
        rows.append(
            {
                "activity": answer["activity"],
                "item": answer["item"],
                "requires": question["requires"],
                "payload_sha256": question["payload_sha256"],
                "decision": answer["decision"],
                "reason": answer["reason"],
                "requires_forced": answer["requires_forced"],
                "options": options,
                "writer": {"seat": writer_seat, "family": actual_writer_family},
                "reviewer": {"seat": seat, "family": family.casefold(), "lane": "language"},
            }
        )
    if seen != set(by_locator):
        raise _bad(f"missing answers: {sorted(set(by_locator) - seen)!r}")
    doc = {"requirements_schema": 2, "lesson": batch["lesson"], "inputs": batch["inputs"], "items": rows}
    receipts.validate_requirement_receipts(doc, sources=sources)
    return doc


def read_answers(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
