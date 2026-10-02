"""Promoting positions in order keeps every later plan review of record valid (#8425).

A plan-validate report pins every plan at an earlier arc position (rule 4). The
one change of such a plan that must not stale the later review is its own
promotion: ``evidence_ref.sha256`` set to its pack's, proven by its receipt and
reviewed copy. The fixture is the plan-review world of
tests/helpers/plan_review_world.py widened to three positions: ``mod-zero`` (1),
``mod-half`` (2) and the reviewed module ``mod-one`` (3). The earlier two are
promoted with the artifacts ``plan-promote`` publishes (reviewed copy, receipt,
promoted bytes); ``mod-one`` is reviewed and promoted through the live CLI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import plan_manifest
from scripts.build.fresh.cli import main as cli_main
from scripts.build.fresh.plan_promote import _publish
from scripts.curriculum.evidence import lock
from scripts.curriculum.validate.scope import compute_scope, write_scope_sidecar
from tests.curriculum.test_plan_validate import LEVEL, PRIOR_SLUG, SLUG
from tests.helpers.plan_review_world import STALE_SHA, Env, build_env, git, sha, validate_provisional

pytestmark = pytest.mark.reads_content

MIDDLE_SLUG = "mod-half"
PLANS = f"curriculum/l2-uk-en/lesson-plans/{LEVEL}"
PRIOR_REL = f"{PLANS}/{PRIOR_SLUG}.yaml"
MIDDLE_REL = f"{PLANS}/{MIDDLE_SLUG}.yaml"
OWN_REL = f"{PLANS}/{SLUG}.yaml"


def _dump(data: object) -> bytes:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False).encode("utf-8")


def _give_pack(env: Env, slug: str, plan: dict) -> dict:
    """An earlier plan with its own pack and a provisional (stale) evidence_ref, as before its promotion."""
    pack = env.evidence_dir / f"{slug}.yaml"
    pack.write_bytes(_dump({"evidence_schema": 1, "module": f"{LEVEL}/{slug}", "texts": [{"id": "T-001"}]}))
    lock.write(pack, pack.read_bytes())
    plan["evidence_ref"] = {"path": f"curriculum/l2-uk-en/evidence/{LEVEL}/{slug}.yaml", "sha256": STALE_SHA}
    return plan


def three_position_env(root: Path) -> Env:
    env = build_env(root, git_repo=False)
    prior = yaml.safe_load((env.plans_dir / f"{PRIOR_SLUG}.yaml").read_bytes())
    middle = {**prior, "slug": MIDDLE_SLUG, "arc_ref": {"level": LEVEL, "position": 2}}
    middle["lessons"] = [{**prior["lessons"][0], "slug": "middle-lesson"}]
    middle["lessons"][0]["steps"] = [{**prior["lessons"][0]["steps"][0]}]
    middle["lessons"][0]["steps"][0]["introduces"] = {"letters": [], "grammar": [], "vocabulary": ["W-007"]}
    for slug, plan in ((PRIOR_SLUG, prior), (MIDDLE_SLUG, middle)):
        (env.plans_dir / f"{slug}.yaml").write_bytes(_dump(_give_pack(env, slug, plan)))

    plan = yaml.safe_load(env.plan_path.read_bytes())
    plan["arc_ref"]["position"] = 3
    env.plan_path.write_bytes(_dump(plan))
    arc_path = env.plans_dir / "_arc.yaml"
    arc = yaml.safe_load(arc_path.read_bytes())
    own = arc["positions"][1]
    middle_record = {**arc["positions"][0], "position": 2, "slug": MIDDLE_SLUG, "job": f"Job of {MIDDLE_SLUG}."}
    arc["positions"] = [arc["positions"][0], middle_record, {**own, "position": 3}]
    arc["est_lessons_total"] = 6
    arc_path.write_bytes(_dump(arc))
    grammar_path = env.plans_dir / "_grammar.yaml"
    registry = yaml.safe_load(grammar_path.read_bytes())
    for record in registry:
        record["introduced_at"]["position"] = 3
    grammar_path.write_bytes(_dump(registry))
    write_scope_sidecar(env.plan_path, SLUG, compute_scope(plan, LEVEL, SLUG))

    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "baseline")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return env


def promote_earlier(env: Env, slug: str) -> None:
    """Publish what ``plan-promote`` publishes for an earlier position: reviewed copy, receipt, promoted plan."""
    plan_path = env.plans_dir / f"{slug}.yaml"
    reviewed = plan_path.read_bytes()
    pack_sha = sha(env.evidence_dir / f"{slug}.yaml")
    promoted = plan_manifest.promoted_plan_bytes(reviewed, pack_sha)
    directory = plan_manifest.state_dir(env.root, LEVEL, slug)
    directory.mkdir(parents=True, exist_ok=True)
    reviewed_sha = plan_manifest.sha256_bytes(reviewed)
    receipt = {
        "manifest_sha256": "e" * 64,
        "reviewed_plan_sha256": reviewed_sha,
        "promoted_plan_sha256": plan_manifest.sha256_bytes(promoted),
        "pack_sha256": pack_sha,
        "attempt_id": f"attempt-{slug}",
        "promoted_at": "2026-10-02T05:00:00+00:00",
    }
    _publish(
        [
            (directory / f"plan-reviewed.{reviewed_sha}.yaml", reviewed, 0o644),
            (directory / plan_manifest.RECEIPT_NAME, lock.yaml_bytes(receipt), 0o644),
            (plan_path, promoted, 0o644),
        ]
    )


def run(env: Env, capsys, *args: str) -> tuple[int, str, str]:
    capsys.readouterr()
    code = cli_main([*args, "--repo-root", str(env.root)])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def status(env: Env, capsys) -> dict:
    return json.loads(run(env, capsys, "plan-review-status", LEVEL, SLUG)[1])


@pytest.fixture
def reviewed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> Env:
    """The three-position world with ``mod-one`` APPROVED; nothing promoted yet."""
    from tests.build.test_fresh_plan_review import fake_verify

    monkeypatch.setattr(plan_manifest, "verify_pack_strict", fake_verify())
    env = three_position_env(tmp_path)
    assert validate_provisional(env) == 0
    report = json.loads((env.state_dir / plan_manifest.VALIDATE_REPORT_NAME).read_text(encoding="utf-8"))
    assert {PRIOR_REL, MIDDLE_REL} <= set(report["inputs"])  # the later report pins both earlier plans
    code, out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 0, err
    digest = json.loads(out)["manifest_sha256"]
    (env.state_dir / plan_manifest.REVIEW_NAME).write_text(
        yaml.safe_dump({"verdict": "APPROVE", "manifest_sha256": digest, "attempt_id": "attempt-1"}), encoding="utf-8"
    )
    assert status(env, capsys)["state"] == "reviewed_pending_promotion"
    return env


def test_promoting_three_positions_in_order_keeps_every_later_review_valid(reviewed: Env, capsys) -> None:
    env = reviewed
    for slug in (PRIOR_SLUG, MIDDLE_SLUG):
        before = (env.plans_dir / f"{slug}.yaml").read_bytes()
        promote_earlier(env, slug)
        assert (env.plans_dir / f"{slug}.yaml").read_bytes() != before
        document = status(env, capsys)
        assert (document["state"], document["stale"]) == ("reviewed_pending_promotion", {}), document
    code, out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 0, err
    assert json.loads(out)["already_promoted"] is False
    document = status(env, capsys)
    assert (document["state"], document["stale"]) == ("reviewed_promoted", {})


def _rewrite_receipt(env: Env, slug: str, **changes: str) -> None:
    path = plan_manifest.state_dir(env.root, LEVEL, slug) / plan_manifest.RECEIPT_NAME
    receipt = yaml.safe_load(path.read_bytes())
    receipt.update(changes)
    path.write_bytes(lock.yaml_bytes(receipt))


def _edit_beyond_evidence_ref(env: Env) -> None:
    """The promoted earlier plan plus one more edit, the receipt rewritten to name the edited bytes."""
    path = env.plans_dir / f"{PRIOR_SLUG}.yaml"
    path.write_bytes(path.read_bytes() + b"# edited after the promotion\n")
    _rewrite_receipt(env, PRIOR_SLUG, promoted_plan_sha256=sha(path))


def _unpromoted_evidence_ref_edit(env: Env) -> None:
    """evidence_ref.sha256 changed exactly as a promotion would, but with no receipt."""
    path = env.plans_dir / f"{PRIOR_SLUG}.yaml"
    path.write_bytes(plan_manifest.promoted_plan_bytes(path.read_bytes(), sha(env.evidence_dir / f"{PRIOR_SLUG}.yaml")))


def _reviewed_copy_removed(env: Env) -> None:
    next(plan_manifest.state_dir(env.root, LEVEL, PRIOR_SLUG).glob("plan-reviewed.*")).unlink()


def _receipt_of_another_plan(env: Env) -> None:
    _rewrite_receipt(env, PRIOR_SLUG, reviewed_plan_sha256="f" * 64)


def _pack_changed_after_promotion(env: Env) -> None:
    pack = env.evidence_dir / f"{PRIOR_SLUG}.yaml"
    pack.write_bytes(pack.read_bytes() + b"# changed\n")
    lock.write(pack, pack.read_bytes())


#: name -> (promote the prior plan first?, mutation, the reason the stale entry must carry)
EARLIER_CHANGES = {
    "edited_beyond_evidence_ref": (True, _edit_beyond_evidence_ref, "more than evidence_ref.sha256"),
    "no_receipt": (False, _unpromoted_evidence_ref_edit, "no promotion receipt"),
    "reviewed_copy_removed": (True, _reviewed_copy_removed, "reviewed plan copy is missing or altered"),
    "receipt_of_another_plan": (True, _receipt_of_another_plan, "does not map the reviewed plan hash"),
    "pack_changed_after_promotion": (True, _pack_changed_after_promotion, "the pack is not the pack"),
}


@pytest.mark.parametrize("name", list(EARLIER_CHANGES))
def test_an_unproven_earlier_plan_change_still_stales_the_later_review(reviewed: Env, capsys, name: str) -> None:
    env = reviewed
    promote_first, mutate, why = EARLIER_CHANGES[name]
    if promote_first:
        promote_earlier(env, PRIOR_SLUG)
    mutate(env)
    document = status(env, capsys)
    assert document["state"] == "stale", document
    assert why in document["stale"][PRIOR_REL], document
    before = env.plan_path.read_bytes()
    code, _out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 1
    assert json.loads(err.strip().splitlines()[-1])["code"] == plan_manifest.INPUTS_CHANGED_SINCE_REVIEW
    assert env.plan_path.read_bytes() == before


def test_the_own_plan_is_never_excused_as_an_earlier_plan(reviewed: Env, capsys) -> None:
    """Without the own manifest's transition, the module's own promoted plan is a change of the report's input."""
    env = reviewed
    assert run(env, capsys, "plan-promote", LEVEL, SLUG)[0] == 0
    report = env.state_dir / plan_manifest.VALIDATE_REPORT_NAME
    problems = plan_manifest.validate_report_problems(env.root, LEVEL, SLUG, report)
    assert problems == {OWN_REL: "changed since the plan-validate report read it"}
