"""Constrained questions: one per open token, batched per lesson.

Each question carries the unit's text, the token with its offset, and the
competing readings copied from the word records (id, lemma, pos, gloss,
stressed spelling of the matching form, form tags). One language-lane call
answers the batch. `stress_open` questions are blocking: no stress may be
printed before the answer. `stress_certain_identity_open` ones are not: the
stress is safe, and identity decides gloss, Atlas link and observed state.
`proposal` stays null: no tagger is wired in, and a tagger may only order
candidates, never select one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.evidence import lock

from . import codes
from .inputs import Allowlist, ExpandedDocument, ResolverError
from .stream import ResolutionStream

REPO_ROOT = Path(__file__).resolve().parents[3]
QUESTIONS_SCHEMA = REPO_ROOT / "schemas/constrained-questions-v1.schema.json"


def question_id(number: int) -> str:
    return f"Q-{number:03d}"


def build_questions(stream: ResolutionStream, expanded: ExpandedDocument, allowlist: Allowlist) -> dict[str, Any]:
    questions = []
    for token in stream.open_tokens():
        candidates = []
        for reading in token["readings"]:
            record = allowlist.records[reading["record"]]
            candidates.append(
                {
                    "record": reading["record"],
                    "lemma": record["lemma"],
                    "pos": record["pos"],
                    "gloss_en": record.get("gloss_en"),
                    "stressed": reading["stressed"],
                    "forms": list(reading["forms"]),
                }
            )
        questions.append(
            {
                "id": question_id(len(questions) + 1),
                "unit": token["unit"],
                "offset": token["offset"],
                "token": token["token"],
                "sentence": expanded.units[token["unit_index"]].text,
                "blocking": token["class"] == codes.STRESS_OPEN,
                "candidates": candidates,
                "proposal": None,
            }
        )
    return {
        "questions_schema": 1,
        "lesson": dict(stream.lesson),
        "inputs": dict(stream.inputs),
        "questions": questions,
    }


def validate_questions(doc: Any) -> None:
    schema = json.loads(QUESTIONS_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        raise ResolverError(codes.INVALID_INPUT, f"questions batch at {list(first.absolute_path)}: {first.message}")


def write_questions(path: Path, doc: dict[str, Any]) -> str:
    validate_questions(doc)
    return lock.write(Path(path), lock.yaml_bytes(doc))


def load_questions(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not lock.check(path):
        raise ResolverError(codes.LOCK_MISMATCH, f"questions batch {str(path)!r} is absent or disagrees with its lock")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_questions(doc)
    return doc
