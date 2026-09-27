"""The plan-review manifest, plan-promote and plan-review-status through the live fresh CLI (#8397 E3c-2).

Every case drives ``scripts.build.fresh.cli.main`` against the tmp curriculum
tree of tests/helpers/plan_review_world.py. ``pack-verify --strict`` is replaced
by a fake at the one seam the manifest step calls it through
(``plan_manifest.verify_pack_strict``); the real function is exercised, with a
fake Sources, in ``test_real_pack_verify_function_is_called_strictly``.
"""

from __future__ import annotations

import json
import re
import stat
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh import plan_manifest
from scripts.build.fresh.cli import main as cli_main
from scripts.curriculum.evidence import codes, lock, sources
from tests.curriculum.test_plan_validate import LEVEL, SLUG
from tests.helpers.plan_review_world import STALE_SHA, Env, build_env, git, sha, validate_provisional

pytestmark = pytest.mark.reads_content

MANIFEST_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "plan-review-manifest-v1.schema.json"
PLANS = f"curriculum/l2-uk-en/lesson-plans/{LEVEL}"
EVIDENCE = f"curriculum/l2-uk-en/evidence/{LEVEL}"
STATE = f"{EVIDENCE}/_state/{SLUG}"
REQUIREMENTS = "docs/epics/fresh-build-requirements.md"
ARC_SOURCE = "docs/epics/fresh-build-a1-arc.md"


def fake_verify(status: str = "ok", errors: tuple[str, ...] = (), calls: list | None = None):
    def verify(level: str, slug: str, **kwargs) -> dict:
        if calls is not None:
            calls.append({"level": level, "slug": slug, **kwargs})
        return {
            "status": status,
            "level": level,
            "slug": slug,
            "module": f"{level}/{slug}",
            "texts_count": 3,
            "errors_count": 1,
            "errors": list(errors),
            "warnings": [],
            "reports": [],
            "chunk_id_moved": [],
            "not_checked": [],
        }

    return verify


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Env:
    monkeypatch.setattr(plan_manifest, "verify_pack_strict", fake_verify())
    return build_env(tmp_path)


def run(env: Env, capsys, *args: str) -> tuple[int, str, str]:
    capsys.readouterr()
    code = cli_main([*args, "--repo-root", str(env.root)])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def make_manifest(env: Env, capsys) -> str:
    """plan-validate --provisional-pack --write-report, then plan-manifest; returns the manifest sha256."""
    assert validate_provisional(env) == 0
    code, out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 0, err
    return json.loads(out)["manifest_sha256"]


def approve(env: Env, digest: str, *, verdict: str = "APPROVE") -> None:
    (env.state_dir / "plan-review.yaml").write_text(
        yaml.safe_dump({"verdict": verdict, "manifest_sha256": digest, "attempt_id": "attempt-1"}), encoding="utf-8"
    )


@pytest.fixture
def approved(env: Env, capsys) -> tuple[Env, str]:
    digest = make_manifest(env, capsys)
    approve(env, digest)
    return env, digest


def error(err: str) -> dict:
    return json.loads(err.strip().splitlines()[-1])


def append_comment(path: Path) -> None:
    path.write_bytes(path.read_bytes() + b"# changed after the review\n")


def snapshot(env: Env) -> dict[str, bytes]:
    return {
        path.relative_to(env.root).as_posix(): path.read_bytes()
        for path in sorted(env.root.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }


# --- plan-manifest -------------------------------------------------------------------------


def test_manifest_is_schema_valid_and_rerun_is_byte_identical(env: Env, capsys) -> None:
    digest = make_manifest(env, capsys)
    current = env.state_dir / "plan-review.manifest.yaml"
    manifest = yaml.safe_load(current.read_bytes())
    Draft202012Validator(json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))).validate(manifest)
    assert manifest["kind"] == "plan"
    assert (manifest["level"], manifest["slug"], manifest["position"]) == (LEVEL, SLUG, 2)
    assert manifest["learner_state"]["source"] == "planned_state"
    assert len(manifest["learner_state"]["sha256"]) == 64
    assert {name: entry["path"] for name, entry in manifest["inputs"].items()} == {
        "plan": f"{PLANS}/{SLUG}.yaml",
        "pack": f"{EVIDENCE}/{SLUG}.yaml",
        "pack_lock": f"{EVIDENCE}/{SLUG}.yaml.lock",
        "words": f"{EVIDENCE}/_words.yaml",
        "words_lock": f"{EVIDENCE}/_words.yaml.lock",
        "learner_state": f"{STATE}/plan-review.learner-state.yaml",
        "requirements": REQUIREMENTS,
        "arc": f"{PLANS}/_arc.yaml",
        "arc_source": ARC_SOURCE,
        "decisions": f"{PLANS}/_decisions.yaml",
        "scope": f"{PLANS}/_scope/{SLUG}.yaml",
        "grammar": f"{PLANS}/_grammar.yaml",
        "validate_report": f"{STATE}/plan-validate.report.json",
        "pack_verify_report": f"{STATE}/pack-verify.report.json",
    }
    for entry in manifest["inputs"].values():
        assert entry["sha256"] == sha(env.root / entry["path"])
    assert lock.check(env.pack_path) and lock.check(env.words_path)
    assert (env.state_dir / "plan-review.manifest.sha256").read_text(encoding="ascii") == f"{digest}\n"
    assert lock.yaml_bytes(manifest) == current.read_bytes()
    assert (env.state_dir / "manifests" / "plan" / f"{digest}.yaml").read_bytes() == current.read_bytes()
    assert sha(current) == digest

    first = snapshot(env)
    code, out, _err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 0 and json.loads(out)["manifest_sha256"] == digest
    assert snapshot(env) == first


def test_materialized_prior_state_is_the_state_the_identity_hashes(env: Env, capsys) -> None:
    from scripts.build.fresh.manifest import learner_state_sha256
    from scripts.curriculum.learner_state.planned import planned_state

    make_manifest(env, capsys)
    manifest = yaml.safe_load((env.state_dir / "plan-review.manifest.yaml").read_bytes())
    state_path = env.state_dir / "plan-review.learner-state.yaml"
    state = planned_state(LEVEL, 2, 1, plans_dir=env.plans_dir, evidence_dir=env.evidence_dir)
    document = yaml.safe_load(state_path.read_bytes())
    assert document == {"learner_state": state.to_dict()}
    assert state_path.read_bytes() == lock.yaml_bytes({"learner_state": state.to_dict()})
    assert lock.check(state_path)  # its lock sidecar
    assert manifest["learner_state"]["sha256"] == learner_state_sha256(state)
    assert manifest["inputs"]["learner_state"] == {
        "path": f"{STATE}/plan-review.learner-state.yaml",
        "sha256": sha(state_path),
    }


def test_a_words_file_that_disagrees_with_its_lock_is_refused_naming_it(env: Env, capsys, monkeypatch) -> None:
    make_manifest(env, capsys)
    append_comment(env.words_path)  # bytes no longer match the lock sidecar
    monkeypatch.setattr(plan_manifest, "validate_report_problems", lambda *a, **kw: {})
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1
    refusal = error(err)
    assert refusal["code"] == plan_manifest.LOCK_MISMATCH and f"{EVIDENCE}/_words.yaml" in refusal["paths"]
    assert not (env.state_dir / "plan-review.manifest.yaml").exists()


def test_manifest_runs_pack_verify_strictly_on_the_exact_pack_and_stores_its_report(
    env: Env, capsys, monkeypatch
) -> None:
    calls: list = []
    monkeypatch.setattr(plan_manifest, "verify_pack_strict", fake_verify(calls=calls))
    make_manifest(env, capsys)
    assert [(call["level"], call["slug"]) for call in calls] == [(LEVEL, SLUG)]
    assert calls[0]["evidence_dir"] == env.evidence_dir.resolve() and calls[0]["plans_dir"] == env.plans_dir.resolve()
    path = env.state_dir / "pack-verify.report.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    report = json.loads(path.read_bytes())
    assert report["strict"] is True and report["status"] == "ok" and report["errors"] == []
    assert report["pack"] == {"path": f"{EVIDENCE}/{SLUG}.yaml", "sha256": sha(env.pack_path)}
    assert report["pack_lock"] == {"path": f"{EVIDENCE}/{SLUG}.yaml.lock", "sha256": sha(Path(f"{env.pack_path}.lock"))}
    assert path.read_text(encoding="utf-8") == json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def test_a_changed_input_changes_the_manifest_sha(env: Env, capsys) -> None:
    first = make_manifest(env, capsys)
    (env.plans_dir / "_decisions.yaml").write_text("decisions: [changed]\n", encoding="utf-8")
    code, out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 0, err
    second = json.loads(out)["manifest_sha256"]
    assert second != first
    history = env.state_dir / "manifests" / "plan"
    assert {path.name for path in history.iterdir()} == {f"{first}.yaml", f"{second}.yaml"}


@pytest.mark.parametrize(
    ("name", "relative"),
    [
        ("decisions", f"{PLANS}/_decisions.yaml"),
        ("grammar", f"{PLANS}/_grammar.yaml"),
        ("arc", f"{PLANS}/_arc.yaml"),
        ("requirements", REQUIREMENTS),
        ("arc_source", ARC_SOURCE),
        ("scope", f"{PLANS}/_scope/{SLUG}.yaml"),
        ("pack_lock", f"{EVIDENCE}/{SLUG}.yaml.lock"),
        ("words_lock", f"{EVIDENCE}/_words.yaml.lock"),
        ("validate_report", f"{STATE}/plan-validate.report.json"),
    ],
)
def test_a_missing_input_fails_naming_its_path(env: Env, capsys, name: str, relative: str) -> None:
    make_manifest(env, capsys)
    assert (env.state_dir / "plan-review.manifest.yaml").exists()
    (env.root / relative).unlink()
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1
    refusal = error(err)
    assert refusal["code"] == plan_manifest.INPUT_MISSING
    assert relative in refusal["paths"] and relative in refusal["reason"]
    # the stale pointer is gone: nothing reads an old manifest as current
    assert not (env.state_dir / "plan-review.manifest.yaml").exists()
    assert not (env.state_dir / "plan-review.manifest.sha256").exists()


def test_a_final_mode_report_is_refused(env: Env, capsys) -> None:
    plan = yaml.safe_load(env.plan_path.read_bytes())
    plan["evidence_ref"]["sha256"] = sha(env.pack_path)
    env.plan_path.write_bytes(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False).encode("utf-8"))
    from scripts.curriculum.validate.validate import main as validate_main

    assert validate_main([LEVEL, SLUG, "--plan", str(env.plan_path), "--write-report"]) == 0
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1
    refusal = error(err)
    assert refusal["code"] == plan_manifest.VALIDATE_REPORT_REFUSED
    assert "provisional" in refusal["reason"]


def test_a_failing_report_is_refused(env: Env, capsys) -> None:
    plan = yaml.safe_load(env.plan_path.read_bytes())
    plan["lessons"][0]["steps"][0]["evidence"].append("T-404")
    env.plan_path.write_bytes(yaml.safe_dump(plan, sort_keys=False).encode("utf-8"))
    assert validate_provisional(env) == 1
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1
    assert error(err)["code"] == plan_manifest.VALIDATE_REPORT_REFUSED
    assert "not a clean pass" in error(err)["reason"]


def test_a_stale_passing_report_is_refused_naming_the_changed_input(env: Env, capsys) -> None:
    assert validate_provisional(env) == 0
    append_comment(env.plans_dir / "_grammar.yaml")  # still parses, but is no longer the file the report read
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1
    refusal = error(err)
    assert refusal["code"] == plan_manifest.VALIDATE_REPORT_REFUSED
    assert f"{PLANS}/_grammar.yaml" in refusal["paths"]


def test_a_failing_pack_verify_is_refused_and_its_report_is_kept(env: Env, capsys, monkeypatch) -> None:
    monkeypatch.setattr(plan_manifest, "verify_pack_strict", fake_verify("failed", ("quote_mismatch: T-001 changed",)))
    assert validate_provisional(env) == 0
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1
    assert error(err)["code"] == plan_manifest.PACK_VERIFY_REFUSED
    report = json.loads((env.state_dir / "pack-verify.report.json").read_bytes())
    assert report["status"] == "failed" and report["errors"] == ["quote_mismatch: T-001 changed"]
    assert not (env.state_dir / "plan-review.manifest.yaml").exists()


def test_a_pack_changed_while_verifying_is_refused(env: Env, capsys, monkeypatch) -> None:
    def verify_and_edit(level, slug, **kwargs):
        env.pack_path.write_bytes(env.pack_path.read_bytes() + b"# edited mid-run\n")
        return fake_verify()(level, slug, **kwargs)

    monkeypatch.setattr(plan_manifest, "verify_pack_strict", verify_and_edit)
    assert validate_provisional(env) == 0
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1 and error(err)["code"] == plan_manifest.PACK_CHANGED_DURING_VERIFY


def test_a_stale_pack_verify_report_is_refused(env: Env, capsys) -> None:
    make_manifest(env, capsys)
    report_path = env.state_dir / "pack-verify.report.json"
    assert plan_manifest.pack_verify_problems(env.root, LEVEL, SLUG, report_path) == {}
    env.pack_path.write_bytes(env.pack_path.read_bytes() + b"# edited\n")
    lock.write(env.pack_path)  # the lock is consistent again, but the report verified other bytes
    problems = plan_manifest.pack_verify_problems(env.root, LEVEL, SLUG, report_path)
    assert f"{EVIDENCE}/{SLUG}.yaml" in problems and f"{EVIDENCE}/{SLUG}.yaml.lock" in problems
    report = json.loads(report_path.read_bytes())
    report.update(status="failed", errors=["x"])
    report_path.write_bytes(plan_manifest.json_bytes(report))
    assert str(report_path.relative_to(env.root).as_posix()) in plan_manifest.pack_verify_problems(
        env.root, LEVEL, SLUG, report_path
    )


def test_a_pack_that_is_not_the_declared_one_is_refused(env: Env, capsys) -> None:
    plan = yaml.safe_load(env.plan_path.read_bytes())
    plan["evidence_ref"]["path"] = f"{EVIDENCE}/elsewhere.yaml"
    env.plan_path.write_bytes(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False).encode("utf-8"))
    (env.evidence_dir / "elsewhere.yaml").write_bytes(env.pack_path.read_bytes())
    assert validate_provisional(env) == 1  # the declared pack has no lock
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1 and error(err)["code"] == plan_manifest.PACK_PATH_MISMATCH


def test_missing_prior_plan_refuses_instead_of_waiving(env: Env, capsys) -> None:
    make_manifest(env, capsys)
    (env.plans_dir / "mod-zero.yaml").unlink()
    code, _out, err = run(env, capsys, "plan-manifest", LEVEL, SLUG)
    assert code == 1
    assert f"{PLANS}/mod-zero.yaml" in error(err)["paths"]


class _FakeSources:
    """The slice of ``Sources`` a pack citing no rows needs: snapshot observability and close."""

    sources_db = Path("sources.db")

    def snapshot_report(self) -> dict:
        return {"journal_mode": "wal", "wal_bytes": 0, "wal_bytes_start": 0, "snapshot_seconds": 0.0}

    def close(self) -> None:
        pass


def write_pack(tmp_path: Path, **built_with: str) -> None:
    """A locked, schema-valid pack citing no rows; ``built_with`` overrides the rows-v2 identity fields."""
    pack = {
        "evidence_schema": 1,
        "module": f"{LEVEL}/x",
        "built_with": {
            "mcp_commit": "0" * 40,
            # rows-v2: built_with.sources_db aggregates the cited rows' digests; none cited → sha256("[]")
            "sources_db_scheme": sources.SOURCES_DB_SCHEME,
            "sources_db": sources.aggregate_digest([]),
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
            "standard_sha256": "0" * 64,
            **built_with,
        },
        "texts": [],
        "exercises": [],
        "examples": [],
        "errors": [],
        "notes": [],
        "videos": [],
        "standard": [],
    }
    (tmp_path / "x.yaml").write_bytes(yaml.safe_dump(pack).encode("utf-8"))
    lock.write(tmp_path / "x.yaml")


def test_real_pack_verify_function_is_called_strictly(tmp_path: Path) -> None:
    write_pack(tmp_path)
    result = plan_manifest.verify_pack_strict(
        LEVEL, "x", evidence_dir=tmp_path, plans_dir=tmp_path, sources_instance=_FakeSources()
    )
    assert result["status"] == "ok" and result["errors"] == []
    assert result["sources_db_scheme"] == sources.SOURCES_DB_SCHEME
    # a pack still carrying the retired file digest (file-v1) is refused under --strict, never waived
    write_pack(tmp_path, sources_db_scheme=sources.LEGACY_SOURCES_DB_SCHEME, sources_db="0" * 64)
    legacy = plan_manifest.verify_pack_strict(
        LEVEL, "x", evidence_dir=tmp_path, plans_dir=tmp_path, sources_instance=_FakeSources()
    )
    assert legacy["status"] == "failed" and legacy["errors"][0].startswith(f"{codes.LEGACY_IDENTITY}:")
    # strict is not negotiable: the refusal --strict --offline gets from verify_pack proves the flag reached it
    refused = plan_manifest.verify_pack_strict(
        LEVEL, "x", evidence_dir=tmp_path, plans_dir=tmp_path, sources_instance=_FakeSources(), offline=True
    )
    assert refused["status"] == "failed" and "--strict and --offline" in refused["errors"][0]


# --- plan-promote --------------------------------------------------------------------------


def paths_of(err: str) -> list[str]:
    return error(err)["paths"]


def edit_pack(env: Env) -> None:
    append_comment(env.pack_path)
    lock.write(env.pack_path)


def edit_words(env: Env) -> None:
    append_comment(env.words_path)
    lock.write(env.words_path)


def edit_learner_state(env: Env) -> None:
    prior = env.plans_dir / "mod-zero.yaml"
    plan = yaml.safe_load(prior.read_bytes())
    plan["lessons"][0]["inventory"]["vocabulary"]["core"] = [{"lemma": "lemma-nine", "evidence": "W-009"}]
    prior.write_bytes(yaml.safe_dump(plan, sort_keys=False).encode("utf-8"))


#: name -> (mutation, the path the refusal must name). One entry per manifest input kind,
#: the words lock and the arc included, plus the planned learner state.
INPUT_CHANGES = {
    "plan": (lambda env: append_comment(env.plan_path), f"{PLANS}/{SLUG}.yaml"),
    "pack": (edit_pack, f"{EVIDENCE}/{SLUG}.yaml"),
    "pack_lock": (edit_pack, f"{EVIDENCE}/{SLUG}.yaml.lock"),
    "words": (edit_words, f"{EVIDENCE}/_words.yaml"),
    "words_lock": (edit_words, f"{EVIDENCE}/_words.yaml.lock"),
    "arc": (lambda env: append_comment(env.plans_dir / "_arc.yaml"), f"{PLANS}/_arc.yaml"),
    "requirements": (lambda env: append_comment(env.root / REQUIREMENTS), REQUIREMENTS),
    "arc_source": (lambda env: append_comment(env.root / ARC_SOURCE), ARC_SOURCE),
    "decisions": (lambda env: append_comment(env.plans_dir / "_decisions.yaml"), f"{PLANS}/_decisions.yaml"),
    "scope": (lambda env: append_comment(env.plans_dir / "_scope" / f"{SLUG}.yaml"), f"{PLANS}/_scope/{SLUG}.yaml"),
    "grammar": (lambda env: append_comment(env.plans_dir / "_grammar.yaml"), f"{PLANS}/_grammar.yaml"),
    "validate_report": (
        lambda env: append_comment(env.state_dir / "plan-validate.report.json"),
        f"{STATE}/plan-validate.report.json",
    ),
    "pack_verify_report": (
        lambda env: append_comment(env.state_dir / "pack-verify.report.json"),
        f"{STATE}/pack-verify.report.json",
    ),
    "learner_state": (edit_learner_state, "learner_state"),
    "learner_state_file": (
        lambda env: append_comment(env.state_dir / "plan-review.learner-state.yaml"),
        f"{STATE}/plan-review.learner-state.yaml",
    ),
}


def test_promote_changes_only_evidence_ref_and_writes_the_copy_and_receipt(approved, capsys) -> None:
    env, digest = approved
    before = env.plan_path.read_bytes()
    pack_sha = sha(env.pack_path)
    assert before.count(STALE_SHA.encode()) == 1
    code, out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 0, err
    after = env.plan_path.read_bytes()
    assert after == before.replace(STALE_SHA.encode(), pack_sha.encode())  # the byte diff is that one value
    receipt = json.loads(out)
    assert receipt["already_promoted"] is False
    stored = yaml.safe_load((env.state_dir / "plan-promotion.yaml").read_bytes())
    assert set(stored) == {
        "manifest_sha256",
        "reviewed_plan_sha256",
        "promoted_plan_sha256",
        "pack_sha256",
        "attempt_id",
        "promoted_at",
    }
    assert stored["manifest_sha256"] == digest
    assert stored["reviewed_plan_sha256"] == plan_manifest.sha256_bytes(before)
    assert stored["promoted_plan_sha256"] == plan_manifest.sha256_bytes(after)
    assert (stored["pack_sha256"], stored["attempt_id"]) == (pack_sha, "attempt-1")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00", stored["promoted_at"])
    reviewed = env.state_dir / f"plan-reviewed.{stored['reviewed_plan_sha256']}.yaml"
    assert reviewed.read_bytes() == before
    assert yaml.safe_load(after)["evidence_ref"]["sha256"] == pack_sha


def test_promote_twice_reports_already_promoted(approved, capsys) -> None:
    env, _digest = approved
    assert run(env, capsys, "plan-promote", LEVEL, SLUG)[0] == 0
    promoted = env.plan_path.read_bytes()
    code, out, _err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 0 and json.loads(out)["already_promoted"] is True
    assert env.plan_path.read_bytes() == promoted


def _nothing_published(env: Env, before: bytes) -> None:
    assert env.plan_path.read_bytes() == before
    assert not (env.state_dir / "plan-promotion.yaml").exists()
    assert not list(env.state_dir.glob("plan-reviewed.*"))


def test_promote_refuses_without_a_review_or_without_approve(env: Env, capsys) -> None:
    digest = make_manifest(env, capsys)
    before = env.plan_path.read_bytes()
    code, _out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 1 and error(err)["code"] == plan_manifest.REVIEW_MISSING
    approve(env, digest, verdict="REVISE")
    code, _out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 1 and error(err)["code"] == plan_manifest.REVIEW_NOT_APPROVED
    _nothing_published(env, before)


def test_promote_refuses_a_review_of_another_manifest(env: Env, capsys) -> None:
    digest = make_manifest(env, capsys)
    approve(env, digest)
    before = env.plan_path.read_bytes()
    (env.plans_dir / "_decisions.yaml").write_text("decisions: [changed]\n", encoding="utf-8")
    assert run(env, capsys, "plan-manifest", LEVEL, SLUG)[0] == 0  # a new attempt: the approved manifest is not current
    code, _out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 1 and error(err)["code"] == plan_manifest.MANIFEST_HASH_MISMATCH
    _nothing_published(env, before)
    approve(env, "0" * 64)
    code, _out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 1 and error(err)["code"] == plan_manifest.MANIFEST_HASH_MISMATCH


@pytest.mark.parametrize("name", list(INPUT_CHANGES))
def test_promote_refuses_when_any_manifest_input_changed(approved, capsys, name: str) -> None:
    env, _digest = approved
    mutate, expected = INPUT_CHANGES[name]
    mutate(env)
    before = env.plan_path.read_bytes()
    code, _out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 1
    refusal = error(err)
    assert refusal["code"] == plan_manifest.INPUTS_CHANGED_SINCE_REVIEW
    assert expected in refusal["paths"], refusal
    _nothing_published(env, before)


def test_promote_refuses_when_strict_validation_of_the_promoted_bytes_fails(approved, capsys) -> None:
    env, _digest = approved
    before = env.plan_path.read_bytes()
    git(env.root, "update-ref", "-d", "refs/remotes/origin/main")  # --strict needs the merge base
    code, _out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 1
    refusal = error(err)
    assert refusal["code"] == plan_manifest.PROMOTED_PLAN_INVALID and "merge_base_unavailable" in refusal["reason"]
    _nothing_published(env, before)


@pytest.mark.parametrize("failing", ["plan-reviewed", "plan-promotion", "mod-one.yaml"])
def test_an_injected_write_failure_leaves_no_partial_promotion(approved, capsys, monkeypatch, failing: str) -> None:
    env, _digest = approved
    before = env.plan_path.read_bytes()
    real = lock.atomic_write

    def flaky(path, content, **kwargs):
        if failing in Path(path).name:
            raise OSError("disk full")
        return real(path, content, **kwargs)

    monkeypatch.setattr(lock, "atomic_write", flaky)
    code, _out, err = run(env, capsys, "plan-promote", LEVEL, SLUG)
    assert code == 1
    assert error(err)["code"] == plan_manifest.PROMOTION_FAILED
    _nothing_published(env, before)
    monkeypatch.setattr(lock, "atomic_write", real)
    assert run(env, capsys, "plan-promote", LEVEL, SLUG)[0] == 0  # the same review still promotes


@pytest.mark.parametrize(
    "written",
    [
        b"evidence_ref:\n  path: p\n  sha256: %s\n",
        b"evidence_ref:\n  path: p\n  sha256: '%s'\n",
        b'evidence_ref:\n  path: p\n  sha256: "%s"\n',
        b"evidence_ref: {path: p, sha256: %s}\n",
        b"# comment\nevidence_ref:\n  sha256: %s  # trailing\n  path: p\nother: 1\n",
    ],
)
def test_promoted_plan_bytes_is_a_single_value_edit(written: bytes) -> None:
    new = "1234" * 16  # digits only: a plain scalar could read back as a number, which must never happen
    source = written % STALE_SHA.encode()
    edited = plan_manifest.promoted_plan_bytes(source, new)
    assert yaml.safe_load(edited)["evidence_ref"]["sha256"] == new
    assert isinstance(yaml.safe_load(edited)["evidence_ref"]["sha256"], str)
    prefix = source.index(STALE_SHA.encode())
    assert edited[:prefix] == source[:prefix]
    assert edited[prefix:].count(b"\n") == source[prefix:].count(b"\n")
    plain = plan_manifest.promoted_plan_bytes(source, "cd34" * 16)
    assert plain.replace(b"cd34" * 16, STALE_SHA.encode()) == source


# --- plan-review-status --------------------------------------------------------------------


def status(env: Env, capsys, *extra: str) -> tuple[int, dict]:
    code, out, _err = run(env, capsys, "plan-review-status", LEVEL, SLUG, *extra)
    return code, json.loads(out)


def test_status_walks_from_unreviewed_to_promoted(env: Env, capsys) -> None:
    code, document = status(env, capsys)
    assert code == 1 and document["state"] == "unreviewed"
    digest = make_manifest(env, capsys)
    approve(env, digest, verdict="REVISE")
    assert status(env, capsys)[1]["state"] == "not_approved"
    approve(env, digest)
    code, document = status(env, capsys)
    assert code == 0 and document["state"] == "reviewed_pending_promotion"
    assert status(env, capsys, "--require-promoted")[0] == 1
    assert run(env, capsys, "plan-promote", LEVEL, SLUG)[0] == 0
    code, document = status(env, capsys, "--require-promoted")
    assert code == 0
    assert document == {"attempt_id": "attempt-1", "manifest_sha256": digest, "stale": {}, "state": "reviewed_promoted"}


def test_status_before_promotion_is_stale_after_any_input_change(approved, capsys) -> None:
    env, _digest = approved
    append_comment(env.plans_dir / "_arc.yaml")
    code, document = status(env, capsys)
    assert code == 1 and document["state"] == "stale" and f"{PLANS}/_arc.yaml" in document["stale"]


POST_PROMOTION = {
    **{name: change for name, change in INPUT_CHANGES.items()},
    "receipt_promoted_hash": (
        lambda env: (env.state_dir / "plan-promotion.yaml").write_text(
            (env.state_dir / "plan-promotion.yaml")
            .read_text(encoding="utf-8")
            .replace("promoted_plan_sha256: ", "promoted_plan_sha256: 0"),
            encoding="utf-8",
        ),
        f"{PLANS}/{SLUG}.yaml",
    ),
    "evidence_ref_changed_again": (
        lambda env: env.plan_path.write_bytes(
            env.plan_path.read_bytes().replace(sha(env.pack_path).encode(), b"cd34" * 16)
        ),
        f"{PLANS}/{SLUG}.yaml",
    ),
    "reviewed_copy_removed": (
        lambda env: next(env.state_dir.glob("plan-reviewed.*")).unlink(),
        f"{PLANS}/{SLUG}.yaml",
    ),
}


@pytest.mark.parametrize("name", list(POST_PROMOTION))
def test_status_of_a_promoted_plan_is_stale_after_any_further_change(approved, capsys, name: str) -> None:
    env, _digest = approved
    assert run(env, capsys, "plan-promote", LEVEL, SLUG)[0] == 0
    assert status(env, capsys, "--require-promoted")[1]["state"] == "reviewed_promoted"
    mutate, expected = POST_PROMOTION[name]
    mutate(env)
    code, document = status(env, capsys)
    assert code == 1 and document["state"] == "stale", document
    assert expected in document["stale"], document


def test_a_promotion_does_not_excuse_a_words_lock_or_arc_change_alone(approved, capsys) -> None:
    env, _digest = approved
    assert run(env, capsys, "plan-promote", LEVEL, SLUG)[0] == 0
    edit_words(env)
    append_comment(env.plans_dir / "_arc.yaml")
    stale = status(env, capsys)[1]["stale"]
    assert f"{EVIDENCE}/_words.yaml.lock" in stale and f"{PLANS}/_arc.yaml" in stale
    assert f"{PLANS}/{SLUG}.yaml" not in stale  # the plan transition itself is still proven


def test_a_receipt_rewritten_to_match_an_edited_plan_proves_nothing(approved, capsys) -> None:
    """The receipt's promoted hash alone is not the proof: the live plan must be the reviewed plan plus the pack hash."""
    env, _digest = approved
    assert run(env, capsys, "plan-promote", LEVEL, SLUG)[0] == 0
    append_comment(env.plan_path)
    receipt_path = env.state_dir / "plan-promotion.yaml"
    receipt = yaml.safe_load(receipt_path.read_bytes())
    receipt["promoted_plan_sha256"] = sha(env.plan_path)
    receipt_path.write_bytes(lock.yaml_bytes(receipt))
    code, document = status(env, capsys)
    assert code == 1 and f"{PLANS}/{SLUG}.yaml" in document["stale"]
    assert "more than evidence_ref.sha256" in document["stale"][f"{PLANS}/{SLUG}.yaml"]


@pytest.mark.parametrize("path", ["/etc/passwd", "../outside.yaml"])
def test_a_manifest_naming_a_path_outside_the_repository_is_invalid(approved, path: str) -> None:
    env, _digest = approved
    manifest = yaml.safe_load((env.state_dir / "plan-review.manifest.yaml").read_bytes())
    manifest["inputs"]["arc"]["path"] = path
    with pytest.raises(plan_manifest.PlanReviewError) as excinfo:
        plan_manifest.validate_manifest_document(manifest)
    assert excinfo.value.code == plan_manifest.MANIFEST_INVALID
