"""The review validator's plan mode (#8397 E3c-2, #8430): plan locations and the plan-pinned manifest.

Runs the live validator CLI (``scripts.review.validate.validate.main``) against a
real plan-review manifest written by ``fresh plan-manifest`` in the tmp tree of
tests/helpers/plan_review_world.py. The lesson-mode behaviour these changes must
not move is pinned by tests/review/test_r1_schema_ledger.py, unmodified.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.review.receipts.ledger import create_empty_ledger
from scripts.review.validate import codes
from scripts.review.validate.validate import build_parser, main, validate_review
from tests.build.test_fresh_plan_review import append_comment, fake_verify, make_manifest, run
from tests.curriculum.test_plan_validate import LEVEL, SLUG
from tests.helpers.plan_review_world import Env, build_env
from tests.review.test_r1_schema_ledger import PLAN_CHECKS, _dump, _record, _review

pytestmark = pytest.mark.reads_content


class Case:
    def __init__(self, env: Env, digest: str, out: Path) -> None:
        self.env, self.digest, self.out = env, digest, out
        self.manifest = env.state_dir / "plan-review.manifest.yaml"
        self.review = out / "review.yaml"
        self.ledger = out / "attempt-1.jsonl"
        create_empty_ledger(self.ledger)

    def finding(self, **overrides) -> dict:
        receipt = _record(self.ledger, manifest=self.digest, result="attested result")
        finding = {
            "id": "F-01",
            "status": "active",
            "locations": [{"lesson": 1, "step": "s1", "field": "teach", "quote": "first letter"}],
            "dimension": "plan_defect",
            "severity": "MINOR",
            "claim": "Placeholder claim.",
            "evidence": {"receipt": receipt},
            "expected": "attested",
        }
        finding.update(overrides)
        return finding

    def write_review(self, findings: list[dict], *, kind: str = "plan") -> None:
        checks = {name: "clean" for name in PLAN_CHECKS}
        if findings:
            checks["sequencing"] = [item["id"] for item in findings]
        _dump(self.review, _review(kind=kind, manifest_hash=self.digest, checks=checks, findings=findings))

    def validate(self, *extra: str) -> tuple[int, dict]:
        argv = [str(self.review), "--manifest", str(self.manifest), "--ledger", str(self.ledger), *extra]
        argv += ["--repo-root", str(self.env.root), "--json"]
        return capture(argv)


def capture(argv: list[str]) -> tuple[int, dict]:
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(argv)
    return code, json.loads(buffer.getvalue())


def rejected(payload: dict) -> set[str]:
    return {item["code"] for item in payload["rejections"]}


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> Case:
    monkeypatch.setattr("scripts.build.fresh.plan_manifest.verify_pack_strict", fake_verify())
    env = build_env(tmp_path / "tree")
    digest = make_manifest(env, capsys)
    out = tmp_path / "out"
    out.mkdir()
    return Case(env, digest, out)


def test_a_valid_plan_review_with_a_located_quote_passes(case: Case) -> None:
    case.write_review([case.finding()])
    code, payload = case.validate()
    assert code == 0, payload
    assert payload == {"active_blockers": 0, "active_majors": 0, "ok": True, "rejections": [], "verdict": "APPROVE"}


@pytest.mark.parametrize(
    "location",
    [
        {"lesson": 1, "quote": "Learner can do thing one."},  # a lesson field found by scanning the lesson
        {"lesson": 1, "field": "job", "quote": "thing one"},
        {"lesson": 1, "step": "s2", "quote": "second letter"},
        {"lesson": 1, "step": "s1", "field": "paradigm.forms.0", "quote": "tag-a"},
        {"lesson": 1, "activity": "a1", "field": "focus", "quote": "Checks the letters."},
        {"lesson": 1, "field": "inventory.vocabulary.core.0.lemma", "quote": "lemma-one"},
        {"field": "title", "quote": "Module one title"},
    ],
)
def test_every_plan_location_shape_resolves(case: Case, location: dict) -> None:
    case.write_review([case.finding(locations=[location])])
    code, payload = case.validate()
    assert code == 0, payload


def test_a_quote_outside_the_named_unit_is_rejected(case: Case) -> None:
    for location in (
        {"lesson": 1, "step": "s1", "field": "teach", "quote": "second letter"},  # another step's text
        {"lesson": 1, "step": "s1", "quote": "Fix the errors."},  # an activity's text
        {"lesson": 1, "activity": "a1", "quote": "Fix the errors."},  # another activity's text
        {"lesson": 1, "field": "job", "quote": "not in the plan at all"},
        {"field": "title", "quote": "Lesson one"},  # a lesson title is not the module title
    ):
        case.write_review([case.finding(locations=[location])])
        code, payload = case.validate()
        assert code == 1 and rejected(payload) == {codes.QUOTE_NOT_IN_UNIT}, location


@pytest.mark.parametrize(
    "location",
    [
        {"lesson": 9, "quote": "x"},
        {"lesson": 1, "step": "s404", "quote": "x"},
        {"lesson": 1, "activity": "a404", "quote": "x"},
        {"lesson": 1, "field": "no.such.path", "quote": "x"},
        {"lesson": 1, "field": "steps.7", "quote": "x"},
        {"field": "nothing", "quote": "x"},
    ],
)
def test_a_location_the_plan_does_not_have_is_rejected(case: Case, location: dict) -> None:
    case.write_review([case.finding(locations=[location])])
    code, payload = case.validate()
    assert code == 1 and rejected(payload) == {codes.LOCATION_NOT_IN_PLAN}


def test_an_absence_finding_uses_a_plan_scope(case: Case) -> None:
    for scope in ({"lesson": 1}, {"lesson": 1, "step": "s2"}, {"lesson": 1, "activity": "a1"}):
        case.write_review([case.finding(locations=[], scope=scope)])
        code, payload = case.validate()
        assert code == 0, (scope, payload)
    for scope in ({"lesson": 9}, {"lesson": 1, "step": "s404"}, {"lesson": 1, "activity": "a404"}):
        case.write_review([case.finding(locations=[], scope=scope)])
        code, payload = case.validate()
        assert code == 1 and rejected(payload) == {codes.LOCATION_NOT_IN_PLAN}, scope


@pytest.mark.parametrize(
    "finding",
    [
        {"locations": [{"tab": "urok", "quote": "first letter"}]},  # the lesson shape
        {"locations": [{"lesson": 0, "quote": "x"}]},
        {"locations": [{"lesson": 1, "step": "s1", "activity": "a1", "quote": "x"}]},
        {"locations": [{"step": "s1", "quote": "x"}]},  # a step needs its lesson
        {"locations": [{"lesson": 1, "field": "has space", "quote": "x"}]},
        {"locations": [{"lesson": 1}]},  # no quote
        {"locations": [], "scope": {"tab": "urok"}},  # the lesson scope
        {"locations": [], "scope": {"lesson": 1, "step": "s1", "activity": "a1"}},
        {"locations": [], "scope": None},
    ],
)
def test_a_lesson_shaped_or_malformed_plan_location_is_a_schema_error(case: Case, finding: dict) -> None:
    payload = case.finding(**finding)
    if payload.get("scope") is None:
        payload.pop("scope", None)
    case.write_review([payload])
    code, result = case.validate()
    assert code == 1 and codes.SCHEMA_INVALID in rejected(result), finding


def test_a_plan_location_in_a_lesson_review_is_a_schema_error(tmp_path: Path) -> None:
    from tests.review.test_r1_schema_ledger import LESSON_CHECKS, _layout

    paths = _layout(tmp_path)
    receipt = _record(paths["ledger"], manifest=paths["digest"], result="alpha-item-text is attested")
    finding = {
        "id": "F-01",
        "status": "active",
        "locations": [{"lesson": 1, "quote": "alpha-item-text"}],
        "dimension": "job",
        "severity": "MINOR",
        "claim": "Placeholder claim.",
        "evidence": {"receipt": receipt},
        "expected": "attested",
    }
    checks = {name: "clean" for name in LESSON_CHECKS}
    checks["job"] = ["F-01"]
    _dump(paths["review"], _review(kind="lesson", manifest_hash=paths["digest"], checks=checks, findings=[finding]))
    result = validate_review(
        paths["review"], manifest_path=paths["manifest"], document_path=paths["lesson"], ledger_path=paths["ledger"]
    )
    assert not result.ok and codes.SCHEMA_INVALID in {item.code for item in result.rejections}


def test_a_plan_that_no_longer_matches_the_manifest_is_rejected(case: Case) -> None:
    case.write_review([case.finding()])
    append_comment(case.env.plan_path)
    code, payload = case.validate()
    assert code == 1 and codes.PLAN_BYTES_MISMATCH in rejected(payload)
    # the plan is reported once: as the mismatch, not also as a stale input
    assert codes.PLAN_INPUTS_STALE not in rejected(payload)


def test_an_explicit_document_is_hash_checked_too(case: Case, tmp_path: Path) -> None:
    other = tmp_path / "other-plan.yaml"
    other.write_bytes(case.env.plan_path.read_bytes() + b"# not the pinned plan\n")
    case.write_review([case.finding()])
    code, payload = case.validate("--document", str(other))
    assert code == 1 and codes.PLAN_BYTES_MISMATCH in rejected(payload)
    copy = tmp_path / "copy.yaml"
    copy.write_bytes(case.env.plan_path.read_bytes())
    assert case.validate("--document", str(copy))[0] == 0
    assert case.validate("--lesson", str(copy))[0] == 0  # the old spelling is an alias


def test_a_changed_manifest_input_makes_the_review_stale(case: Case) -> None:
    case.write_review([case.finding()])
    append_comment(case.env.plans_dir / "_arc.yaml")
    code, payload = case.validate()
    assert code == 1 and rejected(payload) == {codes.PLAN_INPUTS_STALE}
    assert "_arc.yaml" in payload["rejections"][0]["message"]


def test_a_kind_mismatch_is_rejected_both_ways(case: Case, tmp_path: Path) -> None:
    case.write_review([], kind="lesson")
    code, payload = case.validate("--document", str(case.env.plan_path))
    assert code == 1 and codes.MANIFEST_KIND_MISMATCH in rejected(payload)

    lesson_manifest = tmp_path / "lesson-manifest.yaml"
    lesson_manifest.write_text("kind: lesson\nrecap: false\n", encoding="utf-8")
    import hashlib

    digest = hashlib.sha256(lesson_manifest.read_bytes()).hexdigest()
    checks = {name: "clean" for name in PLAN_CHECKS}
    _dump(case.review, _review(kind="plan", manifest_hash=digest, checks=checks, findings=[]))
    code, payload = capture(
        [str(case.review), "--manifest", str(lesson_manifest), "--ledger", str(case.ledger), "--json"]
    )
    assert code == 1 and codes.MANIFEST_KIND_MISMATCH in rejected(payload)


def test_a_malformed_plan_manifest_is_rejected(case: Case, tmp_path: Path) -> None:
    manifest = yaml.safe_load(case.manifest.read_bytes())
    del manifest["inputs"]["arc"]
    broken = tmp_path / "broken.yaml"
    broken.write_bytes(yaml.safe_dump(manifest).encode("utf-8"))
    import hashlib

    digest = hashlib.sha256(broken.read_bytes()).hexdigest()
    _dump(
        case.review, _review(kind="plan", manifest_hash=digest, checks={n: "clean" for n in PLAN_CHECKS}, findings=[])
    )
    code, payload = capture(
        [
            str(case.review),
            "--manifest",
            str(broken),
            "--ledger",
            str(case.ledger),
            "--repo-root",
            str(case.env.root),
            "--json",
        ]
    )
    assert code == 1 and codes.PLAN_MANIFEST_INVALID in rejected(payload)


def test_after_promotion_the_review_is_checked_against_the_reviewed_plan(case: Case, capsys) -> None:
    case.write_review([case.finding()])
    assert case.validate()[0] == 0
    (case.env.state_dir / "plan-review.yaml").write_text(
        yaml.safe_dump({"verdict": "APPROVE", "manifest_sha256": case.digest, "attempt_id": "attempt-1"}),
        encoding="utf-8",
    )
    assert run(case.env, capsys, "plan-promote", LEVEL, SLUG)[0] == 0
    # the live plan now differs from the manifest by the promoted evidence_ref.sha256 only:
    # the receipt-proven transition, so the review still validates against the reviewed copy ...
    code, payload = case.validate()
    assert code == 0, payload
    # ... an explicit document must still be exactly the pinned bytes ...
    code, payload = case.validate("--document", str(case.env.plan_path))
    assert code == 1 and codes.PLAN_BYTES_MISMATCH in rejected(payload)
    # ... and any other change after promotion is stale
    append_comment(case.env.plans_dir / "_arc.yaml")
    code, payload = case.validate()
    assert code == 1 and codes.PLAN_INPUTS_STALE in rejected(payload)


def test_document_is_required_for_lesson_reviews_only(case: Case, tmp_path: Path) -> None:
    case.write_review([], kind="lesson")
    with pytest.raises(SystemExit) as excinfo:
        main([str(case.review), "--manifest", str(case.manifest), "--ledger", str(case.ledger)])
    assert excinfo.value.code == 2
    case.write_review([])
    assert case.validate()[0] == 0  # a plan review needs no --document


def test_help_documents_plan_mode_and_keeps_the_lesson_alias(capsys) -> None:
    text = build_parser().format_help()
    assert "--document" in text and "--lesson" in text
    assert "Plan mode" in text and "inputs.plan.sha256" in text
    for code in (
        codes.MANIFEST_KIND_MISMATCH,
        codes.PLAN_BYTES_MISMATCH,
        codes.PLAN_INPUTS_STALE,
        codes.LOCATION_NOT_IN_PLAN,
        codes.PLAN_UNREADABLE,
        codes.PLAN_MANIFEST_INVALID,
    ):
        assert code in text
