"""#10079: worker scope is read intact from the dispatcher task record."""

from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.agent_runtime.mechanical_admission import MechanicalAdmissionRefused
from scripts.agent_runtime.target_admission import mechanical_scope_digest, mechanical_worker_scope


def record(**changes):
    scope = {
        "family": "mechanical_classification", "role": "classification", "track": "infra-harness",
        "language_lane": False, "review": False, "paths": ["tests/test_example.py"],
        "mode": "read-only", "task_prompt": "Inspect this test.", "prompt_file": None,
        "prompt_file_sha256": None, **changes,
    }
    scope["sha256"] = mechanical_scope_digest(scope)
    return {"mode": "read-only", "mechanical_task": scope}


def test_worker_scope_preserves_recorded_inputs():
    saved = record()
    before = deepcopy(saved)
    assert mechanical_worker_scope(saved, mode="read-only") == {
        "task_family": "mechanical_classification", "task_role": "classification",
        "research_track": "infra-harness", "language_lane": False, "review": False,
        "paths": ["tests/test_example.py"], "task_prompt": "Inspect this test.", "prompt_file": None,
    }
    assert saved == before
    assert mechanical_worker_scope({}, mode="read-only") == {}


@pytest.mark.parametrize("key,value", [
    ("family", "readonly_recon"), ("role", "implementation"), ("track", None),
    ("language_lane", True), ("review", True), ("paths", ["another.py"]),
    ("mode", "workspace-write"), ("task_prompt", "Changed prompt"),
    ("sha256", None), ("prompt_file", "another-file"),
])
def test_changed_inputs_are_refused_even_when_otherwise_eligible(key, value):
    saved = record()
    saved["mechanical_task"][key] = value
    with pytest.raises(MechanicalAdmissionRefused, match="persisted admission inputs changed"):
        mechanical_worker_scope(saved, mode="read-only")


@pytest.mark.parametrize("scope", [[], "not a scope", {}, {"sha256": "incorrect"}])
def test_malformed_scope_is_typed(scope):
    with pytest.raises(MechanicalAdmissionRefused):
        mechanical_worker_scope({"mechanical_task": scope}, mode="read-only")


def test_incomplete_scope_with_valid_digest_is_typed():
    scope = {"mode": "read-only"}
    scope["sha256"] = mechanical_scope_digest(scope)
    with pytest.raises(MechanicalAdmissionRefused):
        mechanical_worker_scope({"mode": "read-only", "mechanical_task": scope}, mode="read-only")


def test_prompt_file_must_still_be_the_dispatched_input(tmp_path):
    import hashlib

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Classify this test.")
    saved = record(prompt_file=str(prompt), prompt_file_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest())
    assert mechanical_worker_scope(saved, mode="read-only")["prompt_file"] == str(prompt)
    prompt.write_text("A different eligible ASCII prompt.")
    with pytest.raises(MechanicalAdmissionRefused):
        mechanical_worker_scope(saved, mode="read-only")
    prompt.unlink()
    with pytest.raises(MechanicalAdmissionRefused):
        mechanical_worker_scope(saved, mode="read-only")
