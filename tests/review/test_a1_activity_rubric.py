"""A1 rubric return and real entry-point integration with synthetic approval only."""

from __future__ import annotations

import copy
import hashlib

import pytest
import yaml

from scripts.build.fresh import activity_rubric as ar
from scripts.build.fresh import manifest, plan_manifest
from scripts.curriculum.evidence import lock
from scripts.review.prompts.eligibility import pin_refusals
from scripts.review.prompts.render import RenderError, render
from scripts.review.receipts.ledger import create_empty_ledger
from scripts.review.validate.validate import _verdict, review_schema_errors, validate_review
from tests.build.test_a1_activity_rubric import ROOT, install_synthetic_approval
from tests.build.test_fresh_e3b2 import _fake_state, _fixture, _rereview_setup, _write
from tests.build.test_fresh_plan_review import fake_verify
from tests.curriculum.test_plan_validate import SLUG
from tests.helpers.plan_review_world import build_env, validate_provisional
from tests.review.test_r1_schema_ledger import LESSON_CHECKS, PLAN_CHECKS, _dump, _record, _review


@pytest.fixture
def registry():
    rubric = ar.validate_rubric((ROOT / ar.RUBRIC_PATH).read_bytes())
    plan = {"lessons": [{"n": 1, "activities": [{"id": "x", "type": "quiz"}, {"id": "grid", "type": "letter-grid"}]}]}
    table = ar.activity_table(plan, rubric)
    return rubric, table


def finding(**overrides):
    value = {
        "id": "F-1",
        "status": "active",
        "dimension": "activity",
        "severity": "MAJOR",
        "claim": "Placeholder defect",
        "locations": [{"activity": "x", "tab": "vpravy", "item": 0, "quote": "alpha"}],
        "evidence": {"receipt": "placeholder"},
        "rubric": {"row": "A1-ACT-016", "clause": "A1-B02"},
    }
    value.update(overrides)
    return value


def test_complete_coverage_and_existing_verdict(registry):
    rubric, table = registry
    review = {"kind": "lesson", "activity_rubric": {"x": "clean", "grid": "clean"}, "findings": []}
    assert ar.review_errors(review, "a1", table, rubric) == []
    review["findings"] = [finding()]
    review["activity_rubric"]["x"] = ["F-1"]
    assert ar.review_errors(review, "a1", table, rubric) == []
    assert _verdict(review["findings"])[0] == "REVISE"


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("missing-map", "coverage keys"),
        ("extra-id", "coverage keys"),
        ("missing-id", "coverage keys"),
        ("clean-finding", "clean cannot"),
        ("unknown-finding", "finding IDs"),
        ("missing-rubric", "requires rubric"),
        ("wrong-row", "wrong row"),
        ("inapplicable", "inapplicable"),
        ("minor-ban", "at least MAJOR"),
        ("minor-condition", "at least MAJOR"),
        ("unknown-clause", "inapplicable"),
        ("no-location", "must name actual"),
        ("unknown-activity", "unknown activity"),
        ("binding-without-activity", "binding needs"),
        ("duplicate-ref", "finding IDs"),
        ("wrong-lesson", "another lesson"),
        ("unsupported-blocker", "requires MAJOR"),
    ],
)
def test_return_evasion_refused(registry, mutation, match):
    rubric, table = registry
    f = finding()
    review = {"kind": "lesson", "activity_rubric": {"x": ["F-1"], "grid": "clean"}, "findings": [f]}
    if mutation == "missing-map":
        review.pop("activity_rubric")
    elif mutation == "extra-id":
        review["activity_rubric"]["extra"] = "clean"
    elif mutation == "missing-id":
        review["activity_rubric"].pop("grid")
    elif mutation == "clean-finding":
        review["activity_rubric"]["x"] = "clean"
    elif mutation == "unknown-finding":
        review["activity_rubric"]["x"] = ["F-99"]
    elif mutation == "missing-rubric":
        f.pop("rubric")
    elif mutation == "wrong-row":
        f["rubric"]["row"] = "A1-ACT-001"
    elif mutation == "inapplicable":
        f["locations"][0]["activity"] = "grid"
        f["rubric"] = {"row": "A1-ACT-009", "clause": "A1-C04"}
        review["activity_rubric"] = {"x": "clean", "grid": ["F-1"]}
    elif mutation in {"minor-ban", "minor-condition"}:
        f["severity"] = "MINOR"
        if mutation == "minor-condition":
            f["rubric"]["clause"] = "A1-C02"
    elif mutation == "unknown-clause":
        f["rubric"]["clause"] = "A1-C99"
    elif mutation == "no-location":
        f["locations"][0].pop("activity")
    elif mutation == "unknown-activity":
        f["locations"][0]["activity"] = "unknown"
    elif mutation == "binding-without-activity":
        f["dimension"] = "learner_fit"
        f["locations"][0].pop("activity")
    elif mutation == "duplicate-ref":
        review["activity_rubric"]["x"] = ["F-1", "F-1"]
    elif mutation == "wrong-lesson":
        review["kind"] = "plan"
        f["locations"][0]["lesson"] = 2
    elif mutation == "unsupported-blocker":
        f["unsupported_by_source"] = {}
        f["severity"] = "BLOCKER"
    assert any(match in error for error in ar.review_errors(review, "a1", table, rubric))


def test_absence_and_nonactivity_dimensions_cannot_evade_binding(registry):
    rubric, table = registry
    f = finding(dimension="learner_fit", locations=[], scope={"tab": "vpravy", "activity": "x"})
    review = {"activity_rubric": {"x": ["F-1"], "grid": "clean"}, "findings": [f]}
    assert not ar.review_errors(review, "a1", table, rubric)
    f.pop("rubric")
    assert ar.review_errors(review, "a1", table, rubric)


def test_a2_return_contract_unchanged():
    prior = _review(kind="lesson", manifest_hash="1" * 64, checks={key: "clean" for key in LESSON_CHECKS}, findings=[])
    assert review_schema_errors(prior) == []
    assert ar.review_errors(prior, "a2", [], None) == []
    prior["activity_rubric"] = {}
    assert ar.review_errors(prior, "a2", [], None)
    prior.pop("activity_rubric")
    prior["findings"] = [finding()]
    assert ar.review_errors(prior, "a2", [], None)


def test_malformed_findings_are_left_to_existing_schema():
    assert ar.review_errors({"findings": None}, "a2", [], None) == []


def test_plan_reused_ids_bind_to_actual_lesson_type(registry):
    rubric, _table = registry
    plan = {
        "lessons": [
            {"n": 1, "activities": [{"id": "x", "type": "quiz"}]},
            {"n": 2, "activities": [{"id": "x", "type": "order"}]},
        ]
    }
    table = ar.activity_table(plan, rubric)
    f = finding(
        locations=[{"lesson": 2, "activity": "x", "quote": "alpha"}], rubric={"row": "A1-ACT-013", "clause": "A1-C04"}
    )
    review = {"kind": "plan", "activity_rubric": {"x": ["F-1"]}, "findings": [f]}
    assert ar.review_errors(review, "a1", table, rubric) == []
    f["rubric"]["row"] = "A1-ACT-016"
    assert ar.review_errors(review, "a1", table, rubric)


def lesson_world(root, monkeypatch, n=1):
    args = _fixture(root)
    install_synthetic_approval(root)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: _fake_state())
    level, slug, plans, evidence, state, pages = args
    path = plans / f"{slug}.yaml"
    plan = yaml.safe_load(path.read_bytes())
    plan["lessons"][n - 1]["activities"] = [{"id": "x", "type": "quiz", "placement": "inline", "focus": "Placeholder"}]
    path.write_bytes(lock.yaml_bytes(plan))
    doc, digest = _write(level, slug, n, state, plans, evidence, pages, root)
    return state / f"lesson-{n}.manifest.yaml", doc, digest


@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
def test_real_entrypoints_render_pinned_rows(tmp_path, monkeypatch, kind):
    if kind == "plan":
        env = build_env(tmp_path)
        install_synthetic_approval(tmp_path)
        monkeypatch.setattr(plan_manifest, "verify_pack_strict", fake_verify())
        assert validate_provisional(env) == 0
        doc, _ = plan_manifest.write_plan_manifest("a1", SLUG, repo_root=tmp_path)
    elif kind == "lesson":
        _, doc, _ = lesson_world(tmp_path, monkeypatch)
    else:
        install_synthetic_approval(tmp_path)
        args, _first, previous, _review_path = _rereview_setup(tmp_path, monkeypatch)
        level, slug, plans, evidence, state, _pages = args
        doc, _ = manifest.write_manifest(
            level,
            slug,
            2,
            lesson_kind="lesson",
            state_dir=state,
            repo_root=tmp_path,
            plans_dir=plans,
            evidence_dir=evidence,
            position=1,
            previous_attempt=previous,
        )
    assert pin_refusals(doc, tmp_path) == []
    result = render(doc, repo_root=tmp_path, review_id="test-review", attempt_id="test-attempt")
    assert "Actual activity ID" in result.prompt and "exact adopted bytes" in result.prompt
    assert tmp_path / ar.RUBRIC_PATH in result.files_read
    assert tmp_path / ar.APPROVAL_PATH in result.files_read


def test_render_missing_pin_pending_drift_and_unmapped(tmp_path, monkeypatch):
    _, doc, _ = lesson_world(tmp_path, monkeypatch)
    bad = copy.deepcopy(doc)
    bad["inputs"].pop("activity_rubric")
    with pytest.raises(RenderError):
        render(bad, repo_root=tmp_path, review_id="r", attempt_id="a")
    approval = tmp_path / ar.APPROVAL_PATH
    approval.write_bytes((ROOT / ar.APPROVAL_PATH).read_bytes())
    doc["inputs"]["activity_rubric_approval"]["sha256"] = hashlib.sha256(approval.read_bytes()).hexdigest()
    with pytest.raises(RenderError, match="pending"):
        render(doc, repo_root=tmp_path, review_id="r", attempt_id="a")
    doc["inputs"].update(install_synthetic_approval(tmp_path))
    candidate = tmp_path / ar.RUBRIC_PATH
    candidate.write_bytes(candidate.read_bytes() + b"\n")
    with pytest.raises(RenderError, match="hash mismatch"):
        render(doc, repo_root=tmp_path, review_id="r", attempt_id="a")
    doc["inputs"].update(install_synthetic_approval(tmp_path))
    pin = doc["inputs"]["plan"]
    path = tmp_path / pin["path"]
    plan = yaml.safe_load(path.read_bytes())
    plan["lessons"][0]["activities"][0]["type"] = "unknown"
    path.write_bytes(lock.yaml_bytes(plan))
    pin["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RenderError, match="unmapped"):
        render(doc, repo_root=tmp_path, review_id="r", attempt_id="a")


def test_manifest_creation_and_freshness_refuse_pending_or_changed_approval(tmp_path, monkeypatch):
    path, _doc, _digest = lesson_world(tmp_path, monkeypatch)
    approval = tmp_path / ar.APPROVAL_PATH
    approval.write_bytes((ROOT / ar.APPROVAL_PATH).read_bytes())
    args = {
        "lesson_kind": "lesson",
        "state_dir": path.parent,
        "repo_root": tmp_path,
        "plans_dir": tmp_path / "curriculum/l2-uk-en/lesson-plans/a1",
        "evidence_dir": tmp_path / "curriculum/l2-uk-en/evidence/a1",
        "position": 1,
    }
    with pytest.raises(manifest.ManifestInputError, match="pending"):
        manifest.write_manifest("a1", "fixture-module", 1, **args)
    with pytest.raises(plan_manifest.PlanReviewError, match="pending"):
        plan_manifest.write_plan_manifest("a1", "fixture-module", repo_root=tmp_path)
    env = build_env(tmp_path / "plan-world")
    install_synthetic_approval(env.root)
    monkeypatch.setattr(plan_manifest, "verify_pack_strict", fake_verify())
    assert validate_provisional(env) == 0
    plan_doc, plan_digest = plan_manifest.write_plan_manifest("a1", SLUG, repo_root=env.root)
    (env.root / ar.APPROVAL_PATH).write_bytes((ROOT / ar.APPROVAL_PATH).read_bytes())
    freshness = plan_manifest.plan_review_freshness(env.root, plan_doc, plan_digest)
    assert freshness.state == "stale"
    assert "activity_rubric" in freshness.stale


def test_a2_active_validator_accepts_prior_return_refuses_new_fields(tmp_path):
    from tests.review.test_r1_schema_ledger import _layout

    paths = _layout(tmp_path)
    _dump(paths["manifest"], {"level": "a2", "recap": False})
    digest = hashlib.sha256(paths["manifest"].read_bytes()).hexdigest()
    prior = _review(kind="lesson", manifest_hash=digest, checks={k: "clean" for k in LESSON_CHECKS}, findings=[])
    _dump(paths["review"], prior)
    result = validate_review(
        paths["review"],
        manifest_path=paths["manifest"],
        lesson_path=paths["lesson"],
        ledger_path=paths["ledger"],
        repo_root=tmp_path,
    )
    assert result.ok and result.verdict == "APPROVE"
    prior["activity_rubric"] = {}
    _dump(paths["review"], prior)
    result = validate_review(
        paths["review"],
        manifest_path=paths["manifest"],
        lesson_path=paths["lesson"],
        ledger_path=paths["ledger"],
        repo_root=tmp_path,
    )
    assert not result.ok


def test_plan_active_validator_uses_pinned_actual_types(tmp_path, monkeypatch):
    env = build_env(tmp_path)
    install_synthetic_approval(tmp_path)
    monkeypatch.setattr(plan_manifest, "verify_pack_strict", fake_verify())
    assert validate_provisional(env) == 0
    _doc, digest = plan_manifest.write_plan_manifest("a1", SLUG, repo_root=tmp_path)
    ledger = tmp_path / "attempt-1.jsonl"
    create_empty_ledger(ledger)
    rubric = ar.validate_rubric((tmp_path / ar.RUBRIC_PATH).read_bytes())
    plan = yaml.safe_load(env.plan_path.read_bytes())
    table = ar.activity_table(plan, rubric)
    review = _review(kind="plan", manifest_hash=digest, checks={k: "clean" for k in PLAN_CHECKS}, findings=[])
    review["activity_rubric"] = {row["activity"]: "clean" for row in table}
    path = tmp_path / "return.yaml"
    _dump(path, review)
    result = validate_review(
        path, manifest_path=env.state_dir / "plan-review.manifest.yaml", ledger_path=ledger, repo_root=tmp_path
    )
    assert result.ok and result.verdict == "APPROVE", result.rejections
    review["activity_rubric"].pop(next(iter(review["activity_rubric"])))
    _dump(path, review)
    result = validate_review(
        path, manifest_path=env.state_dir / "plan-review.manifest.yaml", ledger_path=ledger, repo_root=tmp_path
    )
    assert not result.ok


@pytest.mark.parametrize(
    "severity,unsupported,valid,verdict",
    [
        ("MAJOR", False, True, "REVISE"),
        ("MINOR", False, False, None),
        ("MAJOR", True, True, "REVISE"),
        ("MINOR", True, False, None),
    ],
)
def test_active_validator_enforces_rubric_and_source_severity(
    tmp_path, monkeypatch, severity, unsupported, valid, verdict
):
    manifest_path, _doc, digest = lesson_world(tmp_path, monkeypatch)
    ledger = tmp_path / "attempt-1.jsonl"
    create_empty_ledger(ledger)
    receipt = _record(ledger, manifest=digest, result="no hits" if unsupported else "attested result")
    f = finding(severity=severity)
    f["evidence"]["receipt"] = receipt
    if unsupported:
        f.pop("evidence")
        f["unsupported_by_source"] = {"searches": [{"receipt": receipt, "outcome": "hits_but_no_support"}]}
    checks = {key: "clean" for key in LESSON_CHECKS}
    checks["activity"] = ["F-1"]
    review = _review(kind="lesson", manifest_hash=digest, checks=checks, findings=[f])
    review["activity_rubric"] = {"x": ["F-1"]}
    lesson = tmp_path / "expanded.yaml"
    _dump(lesson, {"units": [{"tab": "vpravy", "activity": "x", "item": 0, "text": "alpha"}]})
    path = tmp_path / "return.yaml"
    _dump(path, review)
    result = validate_review(
        path, manifest_path=manifest_path, lesson_path=lesson, ledger_path=ledger, repo_root=tmp_path
    )
    assert result.ok is valid, result.rejections
    assert result.verdict == verdict
