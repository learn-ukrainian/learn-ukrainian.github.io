"""plan-validate --provisional-pack, --write-report and the plan_bytes override (#8397 E3c-2).

Every case runs the live CLI (``validate_main``) or ``validate_plan`` against the
plan-review fixture world of tests/helpers/plan_review_world.py: a tmp curriculum
tree that is a git repository with origin/main at HEAD.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.validate import codes
from scripts.curriculum.validate.validate import main as validate_main
from scripts.curriculum.validate.validate import validate_plan
from tests.curriculum.test_plan_validate import LEVEL, SLUG
from tests.helpers.plan_review_world import STALE_SHA, Env, build_env, git, sha, validate_provisional

pytestmark = pytest.mark.reads_content


@pytest.fixture
def env(tmp_path: Path) -> Env:
    return build_env(tmp_path)


def _report(env: Env) -> dict:
    return json.loads((env.state_dir / "plan-validate.report.json").read_text(encoding="utf-8"))


def test_provisional_pack_passes_a_stale_evidence_ref_and_records_both_hashes(env: Env, capsys) -> None:
    assert validate_main([LEVEL, SLUG, "--plan", str(env.plan_path)]) == 1
    assert codes.PACK_HASH_MISMATCH in capsys.readouterr().out

    assert validate_provisional(env) == 0
    report = _report(env)
    assert report["mode"] == "provisional"
    assert report["status"] == "pass"
    assert report["failures"] == []
    pending = [item for item in report["not_checked"] if item["code"] == codes.PENDING_PROMOTION]
    assert len(pending) == 1
    assert STALE_SHA in pending[0]["message"]
    assert sha(env.pack_path) in pending[0]["message"]


def test_provisional_pack_still_fails_every_other_rule(env: Env) -> None:
    plan = yaml.safe_load(env.plan_path.read_bytes())
    plan["lessons"][0]["steps"][0]["evidence"].append("T-404")
    env.plan_path.write_bytes(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False).encode("utf-8"))
    report = validate_plan(LEVEL, SLUG, plan_path=env.plan_path, provisional_pack=True)
    assert {outcome.code for outcome in report.failures} == {codes.UNKNOWN_PACK_ID}
    # a pack whose bytes disagree with its own lock is not excused by the provisional mode
    env.pack_path.write_bytes(env.pack_path.read_bytes() + b"# edited\n")
    stale = validate_plan(LEVEL, SLUG, plan_path=env.plan_path, provisional_pack=True)
    assert codes.PACK_LOCK_MISMATCH in {outcome.code for outcome in stale.failures}


def test_a_matching_evidence_ref_has_nothing_pending(env: Env) -> None:
    plan = yaml.safe_load(env.plan_path.read_bytes())
    plan["evidence_ref"]["sha256"] = sha(env.pack_path)
    env.plan_path.write_bytes(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False).encode("utf-8"))
    assert validate_provisional(env) == 0
    assert codes.PENDING_PROMOTION not in {item["code"] for item in _report(env)["not_checked"]}


@pytest.mark.parametrize("extra", [["--strict"], ["--allow-missing-prior"], ["--strict", "--allow-missing-prior"]])
def test_provisional_pack_refuses_strict_and_waivers(env: Env, extra: list[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        validate_main([LEVEL, SLUG, "--plan", str(env.plan_path), "--provisional-pack", *extra])
    assert excinfo.value.code == 2
    assert not (env.state_dir / "plan-validate.report.json").exists()


def test_provisional_pack_and_write_report_refuse_all(env: Env) -> None:
    for flag in ("--provisional-pack", "--write-report"):
        with pytest.raises(SystemExit) as excinfo:
            validate_main([LEVEL, "--all", flag])
        assert excinfo.value.code == 2


def test_write_report_bytes_mode_and_inputs(env: Env) -> None:
    assert validate_provisional(env) == 0
    path = env.state_dir / "plan-validate.report.json"
    first = path.read_bytes()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert first.endswith(b"\n")
    document = json.loads(first)
    assert first.decode("utf-8") == json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

    assert validate_provisional(env) == 0
    assert path.read_bytes() == first  # deterministic

    inputs = document["inputs"]
    base = f"curriculum/l2-uk-en/lesson-plans/{LEVEL}"
    ev = f"curriculum/l2-uk-en/evidence/{LEVEL}"
    expected = {
        f"{base}/{SLUG}.yaml": env.plan_path,
        f"{base}/_arc.yaml": env.plans_dir / "_arc.yaml",
        f"{base}/_grammar.yaml": env.plans_dir / "_grammar.yaml",
        f"{base}/_scope/{SLUG}.yaml": env.plans_dir / "_scope" / f"{SLUG}.yaml",
        f"{base}/mod-zero.yaml": env.plans_dir / "mod-zero.yaml",
        f"{ev}/{SLUG}.yaml": env.pack_path,
        f"{ev}/{SLUG}.yaml.lock": Path(f"{env.pack_path}.lock"),
        f"{ev}/_words.yaml": env.words_path,
        f"{ev}/_words.yaml.lock": Path(f"{env.words_path}.lock"),
    }
    for relative, file in expected.items():
        assert inputs[relative] == sha(file), relative
    assert "schemas/module-plan-v2.schema.json" in inputs
    assert f"schemas/activities-{LEVEL}.schema.json" in inputs
    assert "schemas/arc.schema.json" in inputs
    assert "docs/epics/fresh-build-a1-arc.md" in inputs


def test_report_records_only_earlier_positions_as_prior_plan_inputs(env: Env) -> None:
    later = env.plans_dir / "mod-later.yaml"
    plan = yaml.safe_load((env.plans_dir / "mod-zero.yaml").read_bytes())
    plan["slug"], plan["arc_ref"]["position"] = "mod-later", 3
    later.write_bytes(yaml.safe_dump(plan, sort_keys=False).encode("utf-8"))
    validate_provisional(env)
    inputs = _report(env)["inputs"]
    assert f"curriculum/l2-uk-en/lesson-plans/{LEVEL}/mod-zero.yaml" in inputs
    assert f"curriculum/l2-uk-en/lesson-plans/{LEVEL}/mod-later.yaml" not in inputs


def test_a_failing_run_still_writes_its_report(env: Env) -> None:
    plan = yaml.safe_load(env.plan_path.read_bytes())
    plan["minutes"] = 60
    env.plan_path.write_bytes(yaml.safe_dump(plan, sort_keys=False).encode("utf-8"))
    assert validate_provisional(env) == 1
    assert _report(env)["status"] == "fail"


def test_provisional_mode_runs_the_append_only_registry_check(env: Env) -> None:
    registry = env.plans_dir / "_grammar.yaml"
    records = yaml.safe_load(registry.read_bytes())
    records[0]["point"] = "A point rewritten after the merge base."
    registry.write_bytes(yaml.safe_dump(records, allow_unicode=True, sort_keys=False).encode("utf-8"))
    plan = yaml.safe_load(env.plan_path.read_bytes())
    plan["lessons"][0]["inventory"]["grammar"][0]["point"] = records[0]["point"]
    env.plan_path.write_bytes(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False).encode("utf-8"))
    git(env.root, "add", "-A")
    git(env.root, "commit", "-q", "-m", "edit the merged point")

    provisional = validate_plan(LEVEL, SLUG, plan_path=env.plan_path, provisional_pack=True)
    assert codes.REGISTRY_APPEND_ONLY_VIOLATION in {outcome.code for outcome in provisional.failures}
    final = validate_plan(LEVEL, SLUG, plan_path=env.plan_path)
    assert codes.REGISTRY_APPEND_ONLY_VIOLATION not in {outcome.code for outcome in final.failures}


def test_plan_bytes_override_replaces_the_file_bytes(env: Env) -> None:
    on_disk = env.plan_path.read_bytes()
    promoted = yaml.safe_load(on_disk)
    promoted["evidence_ref"]["sha256"] = sha(env.pack_path)
    override = yaml.safe_dump(promoted, allow_unicode=True, sort_keys=False).encode("utf-8")
    assert codes.PACK_HASH_MISMATCH in {o.code for o in validate_plan(LEVEL, SLUG, plan_path=env.plan_path).failures}
    report = validate_plan(LEVEL, SLUG, plan_path=env.plan_path, plan_bytes=override)
    assert report.ok, report.render_text()
    assert env.plan_path.read_bytes() == on_disk
    from hashlib import sha256

    assert report.inputs[f"curriculum/l2-uk-en/lesson-plans/{LEVEL}/{SLUG}.yaml"] == sha256(override).hexdigest()


def produced_provisional_codes(root: Path) -> set[str]:
    """The codes the provisional mode produces, for the every-code-is-produced registry test."""
    env = build_env(root)
    return validate_plan(LEVEL, SLUG, plan_path=env.plan_path, provisional_pack=True).codes()
