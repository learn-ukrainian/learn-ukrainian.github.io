"""Convert the frozen v2 evaluation set (JSON Lines) into the harness set format (#9623).

Source lines (one JSON object each)::

    {"id", "kind": "review", "level", "text", "errors": [...], "correct_spans": [...]}
    {"id", "kind": "writing", "task", "level", "topic", "genre", "length_words": {"min", "max"}, "register"}

The conversion is a pure re-labelling: offsets, spans, accepted forms and text are copied
verbatim, never normalised or repaired. A source line that cannot be mapped (an unknown error
type, a missing field) is refused with its line number and rule; nothing is written. A converted
set that the harness loader rejects is still written and reported as invalid, by item id and rule.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .common import HarnessError, enclosing_work_tree, sha256_bytes, sha256_file, write_private_json
from .dataset import SetError, SetProblem, load_set, protocol_shortfalls, set_problems

# Source error ``type`` -> harness ``error_type``. Anything else is refused, never guessed.
ERROR_TYPE_MAP: dict[str, str] = {
    "spelling_pravopys_2019": "spelling",
    "agreement": "agreement",
    "numeral_noun": "numeral-noun",
    "vocative": "vocative",
    "aspect": "aspect",
    "case_government": "case-government",
    "prepositional_calques": "prepositional-calque",
    "active_participle_calques": "active-participle-calque",
    "passive_reflexive_calques": "passive-reflexive-calque",
    "bureaucratic_noun_chains": "noun-chain",
    "lexical_russianism": "lexical-russianism",
    "lexical_calque": "other",
    "surzhyk": "surzhyk",
    "paronyms": "paronym",
    "english_calques": "english-calque",
    "semantically_wrong_combinations": "wrong-combination",
}

# The harness writing task has no topic, genre or register field, so they are appended to the
# instruction in one short Ukrainian sentence: "Тема: …; жанр: …; регістр: …."
_WRITING_META = (("topic", "Тема"), ("genre", "жанр"), ("register", "регістр"))

_ERROR_KEYS = ("span", "type", "corrections", "origin", "start", "end")
_CORRECT_KEYS = ("span", "stratum", "start", "end")


@dataclass(frozen=True)
class SourceProblem:
    """A source line that cannot be converted; ``line`` is 1-based, ``rule`` never carries text."""

    line: int
    item: str | None
    rule: str


@dataclass
class Conversion:
    data: dict[str, Any] | None
    problems: list[SourceProblem] = field(default_factory=list)


def require_outside_work_tree(path: Path) -> Path:
    """The resolved ``path``, refused when it lies inside any Git work tree (the results-directory check)."""
    resolved = path.expanduser().resolve()
    tree = enclosing_work_tree(resolved)
    if tree is not None:
        raise HarnessError(
            f"output {resolved} is inside the Git work tree {tree}; the private set must live outside every repository"
        )
    return resolved


def _source_lines(raw: bytes) -> list[tuple[int, str]]:
    """Non-blank lines with 1-based numbers. Split on LF only: U+2028 and friends may sit raw inside strings."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HarnessError(f"input is not valid UTF-8 (byte {exc.start})") from exc
    return [(n, line) for n, line in enumerate(text.split("\n"), start=1) if line.strip()]


def _convert_review(src: dict[str, Any], item_id: str, line: int, problems: list[SourceProblem]) -> dict[str, Any]:
    def refuse(rule: str) -> None:
        problems.append(SourceProblem(line, item_id, rule))

    if not isinstance(src.get("text"), str):
        refuse("review-text")
    errors, protected = [], []
    for n, err in enumerate(_list(src, "errors", refuse), start=1):
        if not isinstance(err, dict) or any(key not in err for key in _ERROR_KEYS):
            refuse("error-fields")
            continue
        error_type = ERROR_TYPE_MAP.get(err["type"]) if isinstance(err["type"], str) else None
        if error_type is None:
            refuse("error-type-unknown")
            continue
        if not isinstance(err["corrections"], list):
            refuse("error-corrections")
            continue
        errors.append(
            {
                "id": f"{item_id}-e{n}",
                "start": err["start"],
                "end": err["end"],
                "span": err["span"],
                "error_type": error_type,
                "accepted": err["corrections"],
                "origin": err["origin"],
            }
        )
    for n, span in enumerate(_list(src, "correct_spans", refuse), start=1):
        if not isinstance(span, dict) or any(key not in span for key in _CORRECT_KEYS):
            refuse("correct-span-fields")
            continue
        protected.append(
            {
                "id": f"{item_id}-p{n}",
                "start": span["start"],
                "end": span["end"],
                "span": span["span"],
                "kind": span["stratum"],
            }
        )
    return {"id": item_id, "text": src.get("text"), "errors": errors, "protected": protected}


def _list(src: dict[str, Any], key: str, refuse) -> list[Any]:
    value = src.get(key)
    if not isinstance(value, list):
        refuse(f"{key}-not-list")
        return []
    return value


def _convert_writing(src: dict[str, Any], item_id: str, line: int, problems: list[SourceProblem]) -> dict[str, Any]:
    task = src.get("task")
    bounds = src.get("length_words")
    if not isinstance(task, str):
        problems.append(SourceProblem(line, item_id, "writing-task"))
        task = ""
    if not isinstance(bounds, dict) or bounds.get("min") is None or bounds.get("max") is None:
        problems.append(SourceProblem(line, item_id, "writing-length-words"))
        bounds = {}
    parts = [
        f"{label}: {value.strip()}"
        for key, label in _WRITING_META
        if isinstance(value := src.get(key), str) and value.strip()
    ]
    instruction = f"{task.rstrip()} {'; '.join(parts)}." if parts else task
    return {
        "id": item_id,
        "level": src.get("level"),
        "instruction": instruction,
        "min_words": bounds.get("min"),
        "max_words": bounds.get("max"),
    }


def convert_source(raw: bytes, set_id: str) -> Conversion:
    """Map v2 JSON Lines bytes to a harness set dict; ``data`` is None when any line is refused."""
    problems: list[SourceProblem] = []
    review: list[dict[str, Any]] = []
    writing: list[dict[str, Any]] = []
    for line, content in _source_lines(raw):
        try:
            src = json.loads(content)
        except ValueError:
            problems.append(SourceProblem(line, None, "json-syntax"))
            continue
        item_id = src.get("id") if isinstance(src, dict) else None
        if not isinstance(item_id, str) or not item_id.strip():
            problems.append(SourceProblem(line, None, "item-id"))
            continue
        kind = src.get("kind")
        if kind == "review":
            review.append(_convert_review(src, item_id, line, problems))
        elif kind == "writing":
            writing.append(_convert_writing(src, item_id, line, problems))
        else:
            problems.append(SourceProblem(line, item_id, "item-kind-unknown"))
    if problems:
        return Conversion(None, problems)
    return Conversion({"set_id": set_id, "review": review, "writing": writing})


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(entry.get(key)) for entry in items).items()))


def validate_converted(path: Path, data: dict[str, Any]) -> tuple[list[SetProblem], list[str]]:
    """The harness's own loader and Protocol v2 minimums on the written file: (problems, shortfalls)."""
    problems = set_problems(data)
    try:
        eval_set = load_set(path)
    except SetError as exc:
        if not problems:  # the collector and the loader must agree; never report a refused set as clean
            problems.append(SetProblem(None, exc.rule))
        return problems, []
    except HarnessError:
        problems.append(SetProblem(None, "set-unreadable"))
        return problems, []
    return problems, protocol_shortfalls(eval_set)


def convert_file(input_path: Path, output_path: Path, set_id: str) -> tuple[int, dict[str, Any]]:
    """Convert, write owner-only, validate. Returns (exit code, report); raises HarnessError on refusal."""
    if not set_id.strip():
        raise HarnessError("--set-id must not be empty")
    output = require_outside_work_tree(output_path)
    source = input_path.expanduser().resolve()
    if output == source:
        raise HarnessError("--output must differ from --input")
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise HarnessError(f"cannot read input {source}: {exc.strerror or exc}") from exc
    conversion = convert_source(raw, set_id)
    if conversion.data is None:
        detail = "; ".join(
            f"line {p.line} item {p.item or '-'}: {p.rule}"
            for p in sorted(conversion.problems, key=lambda p: (p.line, p.rule))
        )
        raise HarnessError(f"input refused, nothing written: {detail}")
    data = conversion.data
    write_private_json(output, data)
    problems, shortfalls = validate_converted(output, data)
    errors = [err for item in data["review"] for err in item["errors"]]
    protected = [span for item in data["review"] for span in item["protected"]]
    valid = not problems and not shortfalls
    report = {
        "valid": valid,
        "set_id": set_id,
        "items": {"review": len(data["review"]), "writing": len(data["writing"])},
        "errors_by_type": _count_by(errors, "error_type"),
        "protected_by_kind": _count_by(protected, "kind"),
        "problems": [{"item": p.item, "rule": p.rule} for p in problems],
        "protocol_shortfalls": shortfalls,
        "input_sha256": sha256_bytes(raw),
        "output_sha256": sha256_file(output),
    }
    return (0 if valid else 1), report
