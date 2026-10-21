"""Quota-free sizing, retaining the critic's pre-existing #9565 held-out draft."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from scripts.build.fresh import assemble, runner
from scripts.curriculum.evidence import lock
from scripts.curriculum.resolver.inputs import Allowlist
from tests.build.test_fresh_page_safety import FIXTURE

pytestmark = pytest.mark.reads_content
H1_SHA256 = "73ea2720238389d491067593a8b5f7401754518381c7be4ac5e34246de57a999"


def held_out(target=None):
    raw = (FIXTURE / "inputs.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == H1_SHA256
    data = json.loads(raw)
    lesson = data["plan"]["lessons"][0]
    if target is None:
        lesson.pop("word_target")
    else:
        lesson["word_target"] = target
    return data


def expanded(data):
    document, _ = assemble.assemble_expanded_document(
        data["draft"], data["plan"], data["pack"], data["words"], "a1", "sounds-letters-and-hello", 1
    )
    return document


def test_missing_gloss_still_fails():
    data = held_out()
    doc = expanded(data)
    gloss = next(unit for unit in doc["units"] if unit["role"] == "gloss_ref" and unit["tab"] == "urok")
    rid = gloss["text"].removeprefix("{{gloss:").removesuffix("}}")
    words = copy.deepcopy(data["words"])
    words["words"] = [word for word in words["words"] if word["id"] != rid]
    row = runner.check_6_count(doc, words)
    assert (row["check"], row["status"], row["reason"], row["layer"]) == (6, "failed", "gloss_record_missing", "pack")


@pytest.mark.parametrize("target", [None, 550])
def test_held_out_runner_retains_current_listening_gate(tmp_path, target):
    """The archived draft predates a retained gate; quota removal cannot bypass it.

    Full runner call-site coverage is supplied separately by the complete integration
    fixture in test_fresh_runner; this immutable oracle supplies counts and rendering.
    """
    data = held_out(target)
    state = tmp_path / "state"
    state.mkdir()
    lock.write(state / "lesson-1.draft.yaml", lock.yaml_bytes(data["draft"]))

    report = runner.run_lesson(
        "a1", "sounds-letters-and-hello", 1,
        draft=data["draft"], plan=data["plan"], pack=data["pack"], words=data["words"],
        state_dir=state, repo_root=tmp_path, plans_dir=tmp_path, evidence_dir=tmp_path,
        allowlist=Allowlist.from_records(data["words"]["words"], words_lock="f" * 64),
        sources=object(),
    )
    assert [row["status"] for row in report["checks"][:3]] == ["passed"] * 3, report
    row = report["checks"][3]
    assert (row["check"], row["status"], row["reason"], row["layer"]) == (
        4, "failed", "listening_model_undeclared", "pack"
    )
    assert all(row["status"] == "not_checked" for row in report["checks"][4:])
