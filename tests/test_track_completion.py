"""State, freshness, routing, and idempotency tests for track completion."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "agents_extensions"
    / "shared"
    / "skills"
    / "track-completion"
    / "scripts"
    / "track_completion.py"
)
SPEC = importlib.util.spec_from_file_location("track_completion_for_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
tc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tc
SPEC.loader.exec_module(tc)


def _config() -> dict[str, Any]:
    family = {
        "plan_review_skill": "plan-review",
        "plan_fix_skill": "apply-plan-fixes",
        "build_command": [".venv/bin/python", "builder.py", "{track}", "{slug}", "--no-resume"],
        "plan_validation_commands": [
            [".venv/bin/python", "validate.py", "{track}/{slug}"]
        ],
        "shippability_command": [".venv/bin/python", "ship.py", "{track}", "{slug}"],
    }
    return {
        "workflow_version": "1.0.0",
        "ledger_schema_version": "track-completion.ledger.v1",
        "config_schema_version": "track-completion.config.v1",
        "manifest_path": "curriculum/l2-uk-en/curriculum.yaml",
        "readiness_profiles_path": "agents_extensions/shared/curriculum-lifecycle/config/readiness-profiles.v1.yaml",
        "readiness_profiles_schema_path": "agents_extensions/shared/curriculum-lifecycle/schema/readiness-profiles.v1.schema.json",
        "runtime_root": "batch_state/track-completion",
        "lease_seconds": 3600,
        "family_for_manifest_type": {"core": "core", "track": "seminar", "seminar": "seminar"},
        "families": {"core": family, "seminar": family},
        "track_overrides": {
            "folk": {
                "forbidden_reviewer_families": ["deepseek"],
                "allowed_reviewer_groups": ["openai", "anthropic"],
            }
        },
        "review_family_groups": {
            "anthropic": "anthropic",
            "claude": "anthropic",
            "codex": "openai",
            "deepseek": "deepseek",
            "gemini": "google",
            "gpt": "openai",
            "human": "human",
            "xai": "xai",
        },
        "routing": {
            "plan_categories": ["plan_adherence"],
            "audit_tooling_categories": ["protocol", "reviewer_unverified"],
            "built_artifact_categories": ["language", "pedagogy", "tone"],
            "audit_tooling_id_prefixes": ["packet-", "reviewer-"],
        },
        "identity_paths": ["workflow.txt"],
    }


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _install_certification_profiles(repo: Path) -> None:
    for relative in (
        "agents_extensions/shared/curriculum-lifecycle/config/readiness-profiles.v1.yaml",
        "agents_extensions/shared/curriculum-lifecycle/schema/readiness-profiles.v1.schema.json",
    ):
        source = ROOT / relative
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


@pytest.fixture
def fake_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    ledger_root = tmp_path / "ledgers"
    manifest = {
        "levels": {
            "a1": {"type": "core", "modules": ["core-built", "core-unbuilt"]},
            "bio": {
                "type": "track",
                "modules": ["seminar-built", "seminar-unbuilt", "seminar-partial"],
            },
            "folk": {"type": "seminar", "modules": ["folk-built"]},
        }
    }
    _write(
        repo / "curriculum/l2-uk-en/curriculum.yaml",
        yaml.safe_dump(manifest, sort_keys=False),
    )
    for track, slugs in {
        "a1": ("core-built", "core-unbuilt"),
        "bio": ("seminar-built", "seminar-unbuilt", "seminar-partial"),
        "folk": ("folk-built",),
    }.items():
        for sequence, slug in enumerate(slugs, start=1):
            _write(
                repo / f"curriculum/l2-uk-en/plans/{track}/{slug}.yaml",
                yaml.safe_dump({"level": track, "slug": slug, "sequence": sequence}),
            )
    for track, slug in (("a1", "core-built"), ("bio", "seminar-built"), ("folk", "folk-built")):
        _write(
            repo / f"curriculum/l2-uk-en/{track}/{slug}/module.md",
            f"# {slug}\n\nНавчальний текст для перевірки завершення.\n",
        )
    _write(
        repo / "curriculum/l2-uk-en/bio/seminar-partial/activities.yaml",
        "[]\n",
    )
    _write(repo / "workflow.txt", "workflow-v1\n")
    _install_certification_profiles(repo)
    config_path = tmp_path / "track-completion.yaml"
    config_path.write_text(yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8")
    return repo, config_path, ledger_root


def _start(
    fake_repo: tuple[Path, Path, Path], selector: str, *, owner: str = "codex/test"
) -> tuple[Path, dict[str, Any]]:
    repo, config_path, ledger_root = fake_repo
    return tc.start_run(
        selector,
        owner=owner,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )


def _result(
    snapshot: tc.TargetSnapshot,
    repo: Path,
    *,
    status: str,
    reviewer_family: str = "gemini",
    finding_id: str = "language-finding",
    category: str = "language",
    location: str | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    if status != "PASS":
        findings.append(
            {
                "id": finding_id,
                "source": "semantic",
                "category": category,
                "severity": "medium" if status == "REVISE" else "high",
                "message": f"Synthetic {finding_id}",
                "location": location or snapshot.review_files["content"],
            }
        )
    return {
        "review_protocol_version": "3.0.0",
        "deterministic_contract_version": "1.2.1",
        "semantic_prompt_version": "3.0.0",
        "track_policy_version": "1.4.0",
        "prompt_sha256": "1" * 64,
        "reproducibility_key": "2" * 64,
        "target": {
            "track": snapshot.track,
            "slug": snapshot.slug,
            "files": snapshot.review_files,
        },
        "source_hashes": {
            name: tc.sha256_file(repo / path)
            for name, path in sorted(snapshot.review_files.items())
        },
        "reviewer": {
            "agent": "fixture",
            "family": reviewer_family,
            "model": "fixture-model",
            "effort": "high",
            "capabilities": ["text"],
        },
        "findings": findings,
        "combined_disposition": {"status": status},
    }


def _result_file(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps({"fixture": name}), encoding="utf-8")
    return path


def _certification_artifact(
    tmp_path: Path,
    name: str,
    inputs: dict[str, Any],
    kind: str,
    **extra: Any,
) -> Path:
    value: dict[str, Any] = {
        "schema_version": "certification-evidence.v1",
        "kind": kind,
        "target": inputs["target"],
        "profile": inputs["profile"],
        "preparation_identity": inputs["preparation_identity"],
        "learner_hashes": inputs["learner_hashes"],
    }
    if kind == "post-build":
        value["pbr"] = {
            "adapter": "post-build-review.v3",
            "verdict": "PASS",
            "raw_response_sha256": "a" * 64,
            "workflow_hashes": inputs["workflow_hashes"],
        }
    elif kind == "independent-review":
        value.update(
            {
                "mutation_identity": inputs["mutation_identity"],
                "review": {
                    "author_families": ["codex"],
                    "reviewer_family": "gemini",
                    "reviewer_group": "google",
                    "verdict": "PASS",
                    "material_findings": [],
                    "resolution_state": "RESOLVED",
                    "raw_response_sha256": "b" * 64,
                },
            }
        )
    elif kind == "integration":
        value.update(
            {
                "mutation_identity": inputs["mutation_identity"],
                "integration": {
                    "issue": 5156,
                    "branch": "codex/5156-certification-chain",
                    "worktree": ".worktrees/dispatch/codex/5156-certification-chain",
                    "commit": "c" * 40,
                    "pr": 5156,
                    "ci_gate": "PASS",
                    "review_gate": "PASS",
                    "merge_sha": "d" * 40,
                    "telemetry": {"applicable": False, "receipt": None},
                    "cleanup": {"state": "COMPLETE"},
                },
            }
        )
    value.update(extra)
    path = tmp_path / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_resolution_covers_core_and_seminar_built_unbuilt_partial(
    fake_repo: tuple[Path, Path, Path],
) -> None:
    repo, config_path, ledger_root = fake_repo
    before = sorted(path.relative_to(repo) for path in repo.rglob("*"))

    resolved = {
        selector: tc.inspect_target(selector, repo_root=repo, config_path=config_path)
        for selector in (
            "a1/core-built",
            "a1/core-unbuilt",
            "bio/seminar-built",
            "bio/seminar-unbuilt",
            "bio/seminar-partial",
        )
    }

    assert resolved["a1/core-built"]["target"]["family"] == "core"
    assert resolved["bio/seminar-built"]["target"]["family"] == "seminar"
    assert resolved["a1/core-built"]["module_state"] == "BUILT"
    assert resolved["a1/core-unbuilt"]["module_state"] == "UNBUILT"
    assert resolved["bio/seminar-unbuilt"]["module_state"] == "UNBUILT"
    assert resolved["bio/seminar-partial"]["module_state"] == "PARTIAL"
    assert "--no-resume" in resolved["bio/seminar-unbuilt"]["commands"]["build_command"]
    assert sorted(path.relative_to(repo) for path in repo.rglob("*")) == before
    assert not ledger_root.exists()
    with pytest.raises(tc.CompletionError, match="not active"):
        tc.inspect_target("retired/ghost", repo_root=repo, config_path=config_path)


def test_unbuilt_plan_build_transitions_are_leased_and_idempotent(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    repo, config_path, ledger_root = fake_repo
    path, ledger = _start(fake_repo, "a1/core-unbuilt")
    run_id = ledger["run"]["run_id"]
    assert ledger["state"] == "PLAN_REVIEW_REQUIRED"

    same_path, same = _start(fake_repo, "a1/core-unbuilt")
    assert same_path == path
    assert same["run"]["run_id"] == run_id
    with pytest.raises(tc.CompletionError, match="lease is held"):
        _start(fake_repo, "a1/core-unbuilt", owner="codex/other")

    evidence = tmp_path / "plan-review.json"
    evidence.write_text('{"verdict":"PASS"}\n', encoding="utf-8")
    plan_path = repo / "curriculum/l2-uk-en/plans/a1/core-unbuilt.yaml"
    original_plan = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(original_plan + "notes: unrecorded drift\n", encoding="utf-8")
    with pytest.raises(tc.CompletionError, match="Unrecorded plan/workflow drift"):
        tc.record_plan_review(
            "a1/core-unbuilt",
            run_id=run_id,
            verdict="PASS",
            evidence=evidence,
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
    plan_path.write_text(original_plan, encoding="utf-8")
    _, ledger = tc.record_plan_review(
        "a1/core-unbuilt",
        run_id=run_id,
        verdict="PASS",
        evidence=evidence,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "BUILD_REQUIRED"

    _write(
        repo / "curriculum/l2-uk-en/a1/core-unbuilt/module.md",
        "# Новий модуль\n\nЗавершений навчальний текст.\n",
    )
    _, ledger = tc.record_build(
        "a1/core-unbuilt",
        run_id=run_id,
        author_family="codex",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "POST_BUILD_REVIEW_REQUIRED"
    assert ledger["author_families"] == ["codex"]


def test_review_rejects_unrecorded_drift_and_routes_plan_findings(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, stale_ledger = _start(fake_repo, "bio/seminar-built")
    snapshot = tc.resolve_target(
        "bio/seminar-built", repo_root=repo, config=tc.load_config(config_path)
    )
    stale_result = _result(snapshot, repo, status="PASS")
    stale_path = _result_file(tmp_path, "stale.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: stale_result)
    content = repo / snapshot.review_files["content"]
    content.write_text(content.read_text(encoding="utf-8") + "Зміна без запису.\n", encoding="utf-8")

    with pytest.raises(tc.CompletionError, match="Unrecorded target/workflow drift"):
        tc.record_review(
            "bio/seminar-built",
            run_id=stale_ledger["run"]["run_id"],
            result_path=stale_path,
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )

    fresh_repo, fresh_config, fresh_ledgers = _fresh_fixture_from(tmp_path / "fresh")
    _, ledger = tc.start_run(
        "bio/seminar-built",
        owner="codex/test",
        repo_root=fresh_repo,
        config_path=fresh_config,
        ledger_root=fresh_ledgers,
    )
    snapshot = tc.resolve_target(
        "bio/seminar-built", repo_root=fresh_repo, config=tc.load_config(fresh_config)
    )
    plan_result = _result(
        snapshot,
        fresh_repo,
        status="REVISE",
        category="plan_adherence",
        location=snapshot.review_files["plan"],
    )
    plan_path = _result_file(tmp_path, "plan-finding.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: plan_result)
    _, ledger = tc.record_review(
        "bio/seminar-built",
        run_id=ledger["run"]["run_id"],
        result_path=plan_path,
        repo_root=fresh_repo,
        config_path=fresh_config,
        ledger_root=fresh_ledgers,
    )
    assert ledger["state"] == "REPAIR_REQUIRED"
    assert ledger["routing"]["owners"] == ["plan_workflow"]


def _fresh_fixture_from(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create the same fixture without depending on pytest fixture internals."""
    repo = tmp_path / "repo"
    ledger_root = tmp_path / "ledgers"
    _write(
        repo / "curriculum/l2-uk-en/curriculum.yaml",
        yaml.safe_dump(
            {"levels": {"bio": {"type": "track", "modules": ["seminar-built"]}}},
            sort_keys=False,
        ),
    )
    _write(
        repo / "curriculum/l2-uk-en/plans/bio/seminar-built.yaml",
        "level: bio\nslug: seminar-built\nsequence: 1\n",
    )
    _write(
        repo / "curriculum/l2-uk-en/bio/seminar-built/module.md",
        "# Семінар\n\nНавчальний текст для перевірки.\n",
    )
    _write(repo / "workflow.txt", "workflow-v1\n")
    _install_certification_profiles(repo)
    config_path = tmp_path / "track-completion.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8")
    return repo, config_path, ledger_root


def test_unchanged_source_material_flip_enters_and_exits_instability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, config_path, ledger_root = _fresh_fixture_from(tmp_path)
    _, ledger = tc.start_run(
        "bio/seminar-built",
        owner="codex/test",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    run_id = ledger["run"]["run_id"]
    snapshot = tc.resolve_target(
        "bio/seminar-built", repo_root=repo, config=tc.load_config(config_path)
    )
    first = _result(snapshot, repo, status="REVISE", finding_id="first-finding")
    second = _result(snapshot, repo, status="REVISE", finding_id="second-finding")
    first_path = _result_file(tmp_path, "first.json")
    second_path = _result_file(tmp_path, "second.json")
    results = {first_path: first, second_path: second}
    monkeypatch.setattr(tc, "_load_post_build_result", lambda path: results[path])

    _, ledger = tc.record_review(
        "bio/seminar-built",
        run_id=run_id,
        result_path=first_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "REPAIR_REQUIRED"
    _, ledger = tc.record_review(
        "bio/seminar-built",
        run_id=run_id,
        result_path=second_path,
        stability_check=True,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "REVIEWER_INSTABILITY"

    evidence = tmp_path / "adjudication.md"
    evidence.write_text("Use a different reviewer route.\n", encoding="utf-8")
    _, ledger = tc.record_instability_adjudication(
        "bio/seminar-built",
        run_id=run_id,
        evidence=evidence,
        summary="The unchanged-source reviewer identity produced conflicting findings.",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "POST_BUILD_REVIEW_REQUIRED"


def test_cross_family_review_gate_and_publication(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "a1/core-unbuilt")
    run_id = ledger["run"]["run_id"]
    plan_evidence = tmp_path / "plan.json"
    plan_evidence.write_text("{}\n", encoding="utf-8")
    tc.record_plan_review(
        "a1/core-unbuilt",
        run_id=run_id,
        verdict="PASS",
        evidence=plan_evidence,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    _write(
        repo / "curriculum/l2-uk-en/a1/core-unbuilt/module.md",
        "# Модуль\n\nСвіжий навчальний матеріал.\n",
    )
    _, ledger = tc.record_build(
        "a1/core-unbuilt",
        run_id=run_id,
        author_family="codex",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    snapshot = tc.resolve_target(
        "a1/core-unbuilt", repo_root=repo, config=tc.load_config(config_path)
    )
    passing = _result(snapshot, repo, status="PASS")
    result_path = _result_file(tmp_path, "pass.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: passing)
    _, ledger = tc.record_review(
        "a1/core-unbuilt",
        run_id=run_id,
        result_path=result_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "INDEPENDENT_REVIEW_REQUIRED"

    review_evidence = tmp_path / "review.md"
    review_evidence.write_text("Independent review passed.\n", encoding="utf-8")
    with pytest.raises(tc.CompletionError, match="author model family"):
        tc.record_independent_review(
            "a1/core-unbuilt",
            run_id=run_id,
            reviewer_family="gpt",
            verdict="PASS",
            evidence=review_evidence,
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
    _, ledger = tc.record_independent_review(
        "a1/core-unbuilt",
        run_id=run_id,
        reviewer_family="gemini",
        verdict="PASS",
        evidence=review_evidence,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "PUBLISH_REQUIRED"
    _, ledger = tc.record_published(
        "a1/core-unbuilt",
        run_id=run_id,
        pr=5144,
        merge_sha="a" * 40,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "COMPLETE"
    assert ledger["run"]["status"] == "completed"


def test_legacy_qg_sidecar_cannot_advance_completion(
    fake_repo: tuple[Path, Path, Path]
) -> None:
    repo, config_path, _ledger_root = fake_repo
    legacy = repo / "curriculum/l2-uk-en/bio/seminar-built/llm_qg.json"
    legacy.write_text('{"aggregate":{"verdict":"PASS"}}\n', encoding="utf-8")

    _, ledger = _start(fake_repo, "bio/seminar-built")
    snapshot = tc.resolve_target(
        "bio/seminar-built", repo_root=repo, config=tc.load_config(config_path)
    )

    assert ledger["state"] == "POST_BUILD_REVIEW_REQUIRED"
    assert "llm_qg" not in snapshot.observed_files


def test_historical_post_build_result_cannot_advance_current_ledger() -> None:
    historical = (
        ROOT
        / "tests"
        / "fixtures"
        / "post_build_review"
        / "bio-oleksandr-bilash.result.v2.json"
    )

    with pytest.raises(tc.CompletionError, match="historical"):
        tc._load_post_build_result(historical)


def test_strict_projection_certifies_disabled_core_only_from_current_evidence(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "a1/core-built")
    preparation = "e" * 64
    inputs = tc.certification_inputs(
        "a1/core-built", preparation_identity=preparation, repo_root=repo, config_path=config_path, ledger=ledger
    )
    evidence = _certification_artifact(tmp_path, "pbr.json", inputs, "post-build")
    tc.record_certification_evidence(
        "a1/core-built", run_id=ledger["run"]["run_id"], evidence=evidence,
        repo_root=repo, config_path=config_path, ledger_root=ledger_root,
    )

    assert tc.certification_projection(
        "a1/core-built", preparation_identity=preparation, repo_root=repo,
        config_path=config_path, ledger_root=ledger_root,
    )["state"] == "CERTIFIED_FINAL"
    (repo / "curriculum/l2-uk-en/a1/core-built/module.md").write_text("# changed\n", encoding="utf-8")
    assert tc.certification_projection(
        "a1/core-built", preparation_identity=preparation, repo_root=repo,
        config_path=config_path, ledger_root=ledger_root,
    )["state"] == "POST_BUILD_REVIEW_REQUIRED"


def test_pending_qg_and_armed_qg_evidence_fail_closed(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    repo, config_path, ledger_root = fake_repo
    # B1 receives the strict CORE profile rather than A1/A2's disabled production gate.
    manifest = yaml.safe_load((repo / "curriculum/l2-uk-en/curriculum.yaml").read_text(encoding="utf-8"))
    manifest["levels"]["b1"] = {"type": "core", "modules": ["strict-built"]}
    _write(repo / "curriculum/l2-uk-en/curriculum.yaml", yaml.safe_dump(manifest, sort_keys=False))
    _write(repo / "curriculum/l2-uk-en/plans/b1/strict-built.yaml", "level: b1\n")
    _write(repo / "curriculum/l2-uk-en/b1/strict-built/module.md", "# B1\n")
    _, ledger = tc.start_run("b1/strict-built", owner="codex/test", repo_root=repo, config_path=config_path, ledger_root=ledger_root)
    preparation = "f" * 64
    inputs = tc.certification_inputs("b1/strict-built", preparation_identity=preparation, repo_root=repo, config_path=config_path, ledger=ledger)
    pbr = _certification_artifact(tmp_path, "b1-pbr.json", inputs, "post-build")
    tc.record_certification_evidence("b1/strict-built", run_id=ledger["run"]["run_id"], evidence=pbr, repo_root=repo, config_path=config_path, ledger_root=ledger_root)
    assert tc.certification_projection("b1/strict-built", preparation_identity=preparation, repo_root=repo, config_path=config_path, ledger_root=ledger_root)["state"] == "PBR_PASS_QG_PENDING"

    shadow = _certification_artifact(tmp_path, "shadow.json", inputs, "post-build")
    payload = json.loads(shadow.read_text(encoding="utf-8"))
    payload["kind"] = "production-qg"
    payload.pop("pbr")
    payload["qg"] = {"adapter": "production-qg.v1", "shadow": True}
    shadow.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(tc.certification.CertificationEvidenceError):
        tc.certification.read_evidence(shadow)


def test_armed_canary_requires_exact_repository_arming_and_qg_evidence(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    repo, config_path, ledger_root = fake_repo
    profiles = repo / "agents_extensions/shared/curriculum-lifecycle/config/readiness-profiles.v1.yaml"
    config = yaml.safe_load(profiles.read_text(encoding="utf-8"))
    qg_profile = config["profiles"]["core"]["certification"]["production_qg"]
    qg_profile.update(
        {
            "mode": "armed-canary",
            "qualification_artifact": "docs/qualification.md",
            "human_arming_artifact": "docs/arming.md",
        }
    )
    _write(repo / "docs/qualification.md", "qualified\n")
    _write(repo / "docs/arming.md", "armed\n")
    profiles.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    _, ledger = _start(fake_repo, "a1/core-built")
    preparation = "1" * 64
    inputs = tc.certification_inputs("a1/core-built", preparation_identity=preparation, repo_root=repo, config_path=config_path, ledger=ledger)
    pbr = _certification_artifact(tmp_path, "armed-pbr.json", inputs, "post-build")
    tc.record_certification_evidence("a1/core-built", run_id=ledger["run"]["run_id"], evidence=pbr, repo_root=repo, config_path=config_path, ledger_root=ledger_root)
    qg = {
        "schema_version": "certification-evidence.v1",
        "kind": "production-qg",
        "target": inputs["target"],
        "profile": inputs["profile"],
        "preparation_identity": preparation,
        "learner_hashes": inputs["learner_hashes"],
        "qg": {
            "adapter": "production-qg.v1", "shadow": False, "cache_regate": "available", "identity": inputs["qg_identity"],
            "reviewer": {"family": "google", "model": "fixture", "route": "canary-route", "lineage": "fixture-v1"},
            "raw_response_sha256": "2" * 64,
            "qualification_sha256": tc.sha256_file(repo / "docs/qualification.md"),
            "human_arming_sha256": tc.sha256_file(repo / "docs/arming.md"),
            "canary": {"status": "PASS", "route": "canary-route"}, "budget": {"status": "WITHIN_BUDGET", "cost": 0},
            "circuit": "CLOSED", "run_id": "run", "attempt_id": "attempt", "completion": "COMPLETE", "verdict": "PASS",
            "findings": [], "tool_events": [], "fact_checks": [],
        },
    }
    qg_path = tmp_path / "armed-qg.json"
    qg_path.write_text(json.dumps(qg), encoding="utf-8")
    tc.record_certification_evidence("a1/core-built", run_id=ledger["run"]["run_id"], evidence=qg_path, repo_root=repo, config_path=config_path, ledger_root=ledger_root)

    assert tc.certification_projection("a1/core-built", preparation_identity=preparation, repo_root=repo, config_path=config_path, ledger_root=ledger_root)["state"] == "CERTIFIED_FINAL"
    _write(repo / "docs/arming.md", "changed arming\n")
    assert tc.certification_projection("a1/core-built", preparation_identity=preparation, repo_root=repo, config_path=config_path, ledger_root=ledger_root)["state"] == "PRODUCTION_QG_REQUIRED"
