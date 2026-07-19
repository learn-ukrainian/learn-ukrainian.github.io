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
SCRIPT = ROOT / "agents_extensions" / "shared" / "skills" / "track-completion" / "scripts" / "track_completion.py"
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
        "plan_validation_commands": [[".venv/bin/python", "validate.py", "{track}/{slug}"]],
        "shippability_command": [".venv/bin/python", "ship.py", "{track}", "{slug}"],
    }
    return {
        "workflow_version": "1.0.0",
        "ledger_schema_version": "track-completion.ledger.v1",
        "config_schema_version": "track-completion.config.v1",
        "manifest_path": "curriculum/l2-uk-en/curriculum.yaml",
        "certification_profiles_path": "agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml",
        "certification_profiles_schema_path": "agents_extensions/shared/curriculum-lifecycle/schema/certification-profiles.v1.schema.json",
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
        "certification_identity_paths": {
            "pbr": ["workflow.txt"],
            "production_qg": {
                name: ["workflow.txt"]
                for name in (
                    "gate",
                    "profile",
                    "prompt",
                    "checker",
                    "checker_config",
                    "policy",
                    "schema",
                    "tool",
                    "routing",
                    "canary",
                    "cost",
                    "circuit",
                    "resume",
                )
            },
        },
    }


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bundle(repo: Path, track: str, slug: str, content: str) -> None:
    directory = repo / "curriculum/l2-uk-en" / track / slug
    _write(directory / "module.md", content)
    for filename in ("activities.yaml", "vocabulary.yaml", "resources.yaml"):
        _write(directory / filename, "[]\n")


def _install_lifecycle_contracts(repo: Path) -> None:
    shutil.copytree(
        ROOT / "agents_extensions/shared/curriculum-lifecycle",
        repo / "agents_extensions/shared/curriculum-lifecycle",
        dirs_exist_ok=True,
    )
    shutil.copytree(
        ROOT / "agents_extensions/shared/prompt-contracts",
        repo / "agents_extensions/shared/prompt-contracts",
    )
    active = set(yaml.safe_load((repo / "curriculum/l2-uk-en/curriculum.yaml").read_text())["levels"])
    prompt_profiles_path = repo / "agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml"
    prompt_profiles = yaml.safe_load(prompt_profiles_path.read_text(encoding="utf-8"))
    prompt_profiles["selectors"]["tracks"] = {
        track: profile for track, profile in prompt_profiles["selectors"]["tracks"].items() if track in active
    }
    prompt_profiles_path.write_text(yaml.safe_dump(prompt_profiles, sort_keys=False), encoding="utf-8")
    certification_path = repo / "agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml"
    certification = yaml.safe_load(certification_path.read_text(encoding="utf-8"))
    certification["selectors"]["tracks"] = {
        track: profile for track, profile in certification["selectors"]["tracks"].items() if track in active
    }
    certification_path.write_text(yaml.safe_dump(certification, sort_keys=False), encoding="utf-8")


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
            "folk": {"type": "track", "modules": ["folk-built"]},
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
                yaml.safe_dump(
                    {
                        "module": f"{track}-{sequence:03d}",
                        "level": track.upper(),
                        "sequence": sequence,
                        "slug": slug,
                        "title": "Навчальний модуль",
                        "subtitle": "Перевірка життєвого циклу",
                        "word_target": 100,
                        "content_outline": [
                            {
                                "section": "Зміст",
                                "words": 100,
                                "points": ["Перевірити перехід між станами."],
                            }
                        ],
                        "references": [{"title": "Тестове джерело"}],
                    },
                    sort_keys=False,
                ),
            )
    for track, slug in (("a1", "core-built"), ("bio", "seminar-built"), ("folk", "folk-built")):
        _write_bundle(
            repo,
            track,
            slug,
            f"# {slug}\n\nНавчальний текст для перевірки завершення.\n",
        )
    _write(
        repo / "curriculum/l2-uk-en/bio/seminar-partial/activities.yaml",
        "[]\n",
    )
    _write(repo / "workflow.txt", "workflow-v1\n")
    _install_lifecycle_contracts(repo)
    config_path = tmp_path / "track-completion.yaml"
    config_path.write_text(yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8")
    return repo, config_path, ledger_root


def _start(
    fake_repo: tuple[Path, Path, Path],
    selector: str,
    *,
    owner: str = "codex/test",
    terminal_goal: str = "certify",
) -> tuple[Path, dict[str, Any]]:
    repo, config_path, ledger_root = fake_repo
    return tc.start_run(
        selector,
        owner=owner,
        terminal_goal=terminal_goal,
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
    quality_score = 10.0 if status == "PASS" else 8.0
    return {
        "schema_version": "post-build-review.result.v6",
        "review_protocol_version": "4.0.0",
        "deterministic_contract_version": "1.2.1",
        "semantic_prompt_version": "4.0.0",
        "track_policy_version": "1.6.0",
        "prompt_sha256": "1" * 64,
        "reproducibility_key": "2" * 64,
        "target": {
            "track": snapshot.track,
            "slug": snapshot.slug,
            "files": snapshot.review_files,
        },
        "source_hashes": {name: tc.sha256_file(repo / path) for name, path in sorted(snapshot.review_files.items())},
        "reviewer": {
            "agent": "fixture",
            "family": reviewer_family,
            "model": "fixture-model",
            "effort": "high",
            "capabilities": ["text"],
        },
        "semantic_response": {"raw_sha256": "3" * 64},
        "semantic": {
            "quality_dimensions": {
                dimension: {"score": quality_score}
                for dimension in ("pedagogical", "naturalness", "decolonization", "engagement", "tone")
            }
        },
        "findings": findings,
        "combined_disposition": {"status": status},
    }


def _result_file(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps({"fixture": name}), encoding="utf-8")
    return path


def _prepare_review(
    selector: str, run_id: str, result: dict[str, Any], *, repo: Path, config_path: Path, ledger_root: Path
) -> None:
    reviewer = result["reviewer"]
    tc.prepare_semantic_review(
        selector,
        run_id=run_id,
        protocol_version=result["review_protocol_version"],
        prompt_sha256=result["prompt_sha256"],
        schema_sha256=tc.sha256_bytes(result["schema_version"].encode("utf-8")),
        reviewer_family=reviewer["family"],
        reviewer_model=reviewer["model"],
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )


def test_current_certification_profiles_require_post_build_review_v5() -> None:
    path = ROOT / "agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert config["profiles"]
    assert {(profile["version"], profile["pbr"]["adapter"]) for profile in config["profiles"].values()} == {
        ("2.0.0", "post-build-review.v5")
    }


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
            "adapter": "post-build-review.v5",
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
                    "premerge": {
                        "mdx_drift": "PASS",
                        "source_parity": "PASS",
                        "forward_parity": "PASS",
                        "verify_shippable": "PASS",
                        "deterministic_audits": "PASS",
                        "focused_tests": "PASS",
                        "artifact_scope": "PASS",
                        "agent_trailer": "PASS",
                        "forbidden_files": "PASS",
                    },
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


def test_new_and_existing_modules_converge_on_the_same_post_build_gate(
    fake_repo: tuple[Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, existing = _start(fake_repo, "a1/core-built")
    _, new = _start(fake_repo, "a1/core-unbuilt")
    assert existing["state"] == "POST_BUILD_REVIEW_REQUIRED"
    assert new["state"] == "PLAN_REVIEW_REQUIRED"

    plan_evidence = tmp_path / "new-plan-review.json"
    plan_evidence.write_text('{"verdict":"PASS"}\n', encoding="utf-8")
    _, new = tc.record_plan_review(
        "a1/core-unbuilt",
        run_id=new["run"]["run_id"],
        verdict="PASS",
        evidence=plan_evidence,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    _write_bundle(
        repo,
        "a1",
        "core-unbuilt",
        "# Новий модуль\n\nЗавершений навчальний текст.\n",
    )
    _, new = tc.record_build(
        "a1/core-unbuilt",
        run_id=new["run"]["run_id"],
        author_family="codex",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert new["state"] == "POST_BUILD_REVIEW_REQUIRED"

    existing_snapshot = tc.resolve_target("a1/core-built", repo_root=repo, config=tc.load_config(config_path))
    new_snapshot = tc.resolve_target("a1/core-unbuilt", repo_root=repo, config=tc.load_config(config_path))
    existing_result_path = _result_file(tmp_path, "existing-post-build-pass.json")
    new_result_path = _result_file(tmp_path, "new-post-build-pass.json")
    results = {
        existing_result_path: _result(existing_snapshot, repo, status="PASS"),
        new_result_path: _result(new_snapshot, repo, status="PASS"),
    }
    monkeypatch.setattr(tc, "_load_post_build_result", lambda path: results[path])
    _prepare_review(
        "a1/core-built",
        existing["run"]["run_id"],
        results[existing_result_path],
        repo=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    _prepare_review(
        "a1/core-unbuilt",
        new["run"]["run_id"],
        results[new_result_path],
        repo=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )

    _, existing = tc.record_review(
        "a1/core-built",
        run_id=existing["run"]["run_id"],
        result_path=existing_result_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    _, new = tc.record_review(
        "a1/core-unbuilt",
        run_id=new["run"]["run_id"],
        result_path=new_result_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )

    assert existing["reviews"][-1]["status"] == "PASS"
    assert new["reviews"][-1]["status"] == "PASS"
    assert existing["state"] == "AWAITING_PRODUCTION_QG_ARMING"
    assert new["state"] == "INDEPENDENT_REVIEW_REQUIRED"
    assert new["author_families"] == ["codex"]


def test_certification_config_rejects_retired_track_selector(
    fake_repo: tuple[Path, Path, Path],
) -> None:
    repo, config_path, _ledger_root = fake_repo
    certification_path = repo / "agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml"
    certification = yaml.safe_load(certification_path.read_text(encoding="utf-8"))
    certification["selectors"]["tracks"]["lit-doc"] = "seminar-pending"
    certification_path.write_text(yaml.safe_dump(certification, sort_keys=False), encoding="utf-8")

    with pytest.raises(tc.CompletionError, match="inactive tracks: lit-doc"):
        tc.inspect_target("a1/core-built", repo_root=repo, config_path=config_path)


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

    _write_bundle(
        repo,
        "a1",
        "core-unbuilt",
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
    build_event = next(item for item in ledger["history"] if item["event"] == "BUILD_RECORDED")
    consumed_identity = build_event["details"]["preparation_identity"]
    assert len(consumed_identity) == 64

    history_length = len(ledger["history"])
    _, replayed = tc.record_build(
        "a1/core-unbuilt",
        run_id=run_id,
        author_family="codex",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert len(replayed["history"]) == history_length
    inputs = tc.certification_inputs(
        "a1/core-unbuilt",
        repo_root=repo,
        config_path=config_path,
        ledger=replayed,
    )
    assert inputs["preparation_identity"] == consumed_identity
    with pytest.raises(tc.CompletionError, match="Current preparation does not require a rebuild"):
        tc.request_preparation_rebuild(
            "a1/core-unbuilt",
            run_id=run_id,
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )

    profiles = repo / "agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml"
    profiles.write_text(profiles.read_text(encoding="utf-8") + "# preparation drift\n", encoding="utf-8")
    with pytest.raises(
        tc.CompletionError,
        match="built-preparation-drift; PREPARATION_IDENTITY_DRIFT:preparation",
    ):
        tc.certification_inputs(
            "a1/core-unbuilt",
            repo_root=repo,
            config_path=config_path,
            ledger=replayed,
        )

    _, rebuild_required = tc.request_preparation_rebuild(
        "a1/core-unbuilt",
        run_id=run_id,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert rebuild_required["state"] == "BUILD_REQUIRED"
    rebuild_event = rebuild_required["history"][-1]
    assert rebuild_event["event"] == "PREPARATION_REBUILD_REQUIRED"
    assert rebuild_event["details"]["consumed_preparation_identity"] == consumed_identity
    assert rebuild_event["details"]["current_preparation_identity"] != consumed_identity
    _, rebuild_replay = tc.request_preparation_rebuild(
        "a1/core-unbuilt",
        run_id=run_id,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert len(rebuild_replay["history"]) == len(rebuild_required["history"])

    with pytest.raises(tc.CompletionError, match="Build produced no fresh target/workflow identity"):
        tc.record_build(
            "a1/core-unbuilt",
            run_id=run_id,
            author_family="codex",
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
    content = repo / "curriculum/l2-uk-en/a1/core-unbuilt/module.md"
    content.write_text(content.read_text(encoding="utf-8") + "Оновлений матеріал.\n", encoding="utf-8")
    _, rebuilt = tc.record_build(
        "a1/core-unbuilt",
        run_id=run_id,
        author_family="codex",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    rebuilt_inputs = tc.certification_inputs(
        "a1/core-unbuilt",
        repo_root=repo,
        config_path=config_path,
        ledger=rebuilt,
    )
    assert rebuilt_inputs["preparation_identity"] == rebuild_event["details"]["current_preparation_identity"]


def test_certification_rejects_built_bundle_without_consumed_preparation_identity(
    fake_repo: tuple[Path, Path, Path],
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "a1/core-built")

    with pytest.raises(
        tc.CompletionError,
        match="built-preparation-drift; PREPARATION_IDENTITY_MISSING:audit_tooling",
    ):
        tc.certification_inputs(
            "a1/core-built",
            repo_root=repo,
            config_path=config_path,
            ledger=ledger,
        )

    projection = tc.certification_projection(
        "a1/core-built",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert projection["state"] == "POST_BUILD_REVIEW_REQUIRED"
    assert projection["post_build"] == "preparation-stale"
    assert projection["final"] == "not-certified"

    _, rebuild_required = tc.request_preparation_rebuild(
        "a1/core-built",
        run_id=ledger["run"]["run_id"],
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert rebuild_required["state"] == "BUILD_REQUIRED"
    assert rebuild_required["history"][-1]["details"]["consumed_preparation_identity"] is None

    with pytest.raises(tc.CompletionError, match="Build produced no fresh target/workflow identity"):
        tc.record_build(
            "a1/core-built",
            run_id=ledger["run"]["run_id"],
            author_family="codex",
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
    content = repo / "curriculum/l2-uk-en/a1/core-built/module.md"
    content.write_text(content.read_text(encoding="utf-8") + "Перебудований матеріал.\n", encoding="utf-8")
    _, rebuilt = tc.record_build(
        "a1/core-built",
        run_id=ledger["run"]["run_id"],
        author_family="codex",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    inputs = tc.certification_inputs(
        "a1/core-built",
        repo_root=repo,
        config_path=config_path,
        ledger=rebuilt,
    )
    assert len(inputs["preparation_identity"]) == 64


def test_preparation_rebuild_routing_rejects_incomplete_inputs_and_learner_drift(
    fake_repo: tuple[Path, Path, Path],
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, bio_ledger = _start(fake_repo, "bio/seminar-built")
    with pytest.raises(
        tc.CompletionError,
        match="Preparation requirements must pass before routing the bundle to rebuild",
    ):
        tc.request_preparation_rebuild(
            "bio/seminar-built",
            run_id=bio_ledger["run"]["run_id"],
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )

    _, core_ledger = _start(fake_repo, "a1/core-built")
    content = repo / "curriculum/l2-uk-en/a1/core-built/module.md"
    content.write_text(content.read_text(encoding="utf-8") + "Незаписана зміна.\n", encoding="utf-8")
    with pytest.raises(
        tc.CompletionError,
        match="Unrecorded learner-artifact drift must be adjudicated",
    ):
        tc.request_preparation_rebuild(
            "a1/core-built",
            run_id=core_ledger["run"]["run_id"],
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )


def test_preparation_rebuild_from_awaiting_production_qg_arming_clears_stale_fields(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, config_path, ledger_root = fake_repo
    path, core_ledger = _start(fake_repo, "a1/core-built")
    run_id = core_ledger["run"]["run_id"]
    assert core_ledger["state"] == "POST_BUILD_REVIEW_REQUIRED"
    snapshot = tc.resolve_target("a1/core-built", repo_root=repo, config=tc.load_config(config_path))
    post_build = _result(snapshot, repo, status="PASS")
    post_build_path = _result_file(tmp_path, "post-build-pass.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: post_build)
    _prepare_review("a1/core-built", run_id, post_build, repo=repo, config_path=config_path, ledger_root=ledger_root)
    _, core_ledger = tc.record_review(
        "a1/core-built",
        run_id=run_id,
        result_path=post_build_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert core_ledger["state"] == "AWAITING_PRODUCTION_QG_ARMING"

    core_ledger["routing"] = {"owners": ["built_artifact"], "findings": []}
    core_ledger["publication"] = {
        "pr": 5255,
        "merge_sha": "a" * 40,
        "recorded_at": "2026-07-15T00:00:00Z",
    }
    core_ledger["production_qg_authorization"] = {
        "qualification_path": "qualification.json",
        "qualification_sha256": "b" * 64,
        "human_arming_path": "human-arming.json",
        "human_arming_sha256": "c" * 64,
        "approval_id": "deploy-approval-5255",
        "route": {"family": "gemini", "model": "fixture", "effort": "high"},
    }
    tc._atomic_write_json(path, core_ledger)

    profiles = repo / "agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml"
    profiles.write_text(profiles.read_text(encoding="utf-8") + "# preparation drift\n", encoding="utf-8")

    _, rebuilt = tc.request_preparation_rebuild(
        "a1/core-built",
        run_id=run_id,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert rebuilt["state"] == "BUILD_REQUIRED"
    rebuild_event = rebuilt["history"][-1]
    assert rebuild_event["event"] == "PREPARATION_REBUILD_REQUIRED"
    assert rebuilt["routing"] is None
    assert rebuilt["publication"] is None
    assert rebuilt["production_qg_authorization"] is None


def test_review_rejects_unrecorded_drift_and_routes_plan_findings(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, stale_ledger = _start(fake_repo, "bio/seminar-built")
    snapshot = tc.resolve_target("bio/seminar-built", repo_root=repo, config=tc.load_config(config_path))
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
    snapshot = tc.resolve_target("bio/seminar-built", repo_root=fresh_repo, config=tc.load_config(fresh_config))
    plan_result = _result(
        snapshot,
        fresh_repo,
        status="REVISE",
        category="plan_adherence",
        location=snapshot.review_files["plan"],
    )
    plan_path = _result_file(tmp_path, "plan-finding.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: plan_result)
    _prepare_review(
        "bio/seminar-built",
        ledger["run"]["run_id"],
        plan_result,
        repo=fresh_repo,
        config_path=fresh_config,
        ledger_root=fresh_ledgers,
    )
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


def test_learner_level_meta_policy_finding_routes_to_built_artifact() -> None:
    result = {
        "combined_disposition": {"status": "REVISE"},
        "findings": [
            {
                "id": "learner-workflow-leakage-learner-level-meta-1",
                "issue_id": "LEARNER_LEVEL_META_LEAKAGE",
                "source": "track_policy",
                "category": "learner_level_meta_leakage",
                "severity": "medium",
                "location": "curriculum/l2-uk-en/bio/example/module.md:31",
            }
        ],
    }

    routing = tc.route_findings(result, config=_config())

    assert routing == {
        "owners": ["built_artifact"],
        "findings": [
            {
                "finding_id": "learner-workflow-leakage-learner-level-meta-1",
                "category": "learner_level_meta_leakage",
                "location": "curriculum/l2-uk-en/bio/example/module.md:31",
                "owner": "built_artifact",
            }
        ],
    }


def test_assessment_gap_uses_category_owner_before_plan_evidence_location() -> None:
    result = {
        "combined_disposition": {"status": "REVISE"},
        "findings": [
            {
                "id": "objective-two-subskills-unelicited",
                "issue_id": "OBJECTIVE_ASSESSMENT_GAP",
                "source": "semantic",
                "category": "pedagogy",
                "severity": "high",
                "location": "curriculum/l2-uk-en/plans/bio/example.yaml:148",
            }
        ],
    }

    routing = tc.route_findings(result, config=_config())

    assert routing == {
        "owners": ["built_artifact"],
        "findings": [
            {
                "finding_id": "objective-two-subskills-unelicited",
                "category": "pedagogy",
                "location": "curriculum/l2-uk-en/plans/bio/example.yaml:148",
                "owner": "built_artifact",
            }
        ],
    }


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
    _install_lifecycle_contracts(repo)
    config_path = tmp_path / "track-completion.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8")
    return repo, config_path, ledger_root


def test_unchanged_source_stability_repeat_is_rejected_by_bounded_review_budget(
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
    snapshot = tc.resolve_target("bio/seminar-built", repo_root=repo, config=tc.load_config(config_path))
    first = _result(snapshot, repo, status="REVISE", finding_id="first-finding")
    second = _result(snapshot, repo, status="REVISE", finding_id="second-finding")
    first_path = _result_file(tmp_path, "first.json")
    second_path = _result_file(tmp_path, "second.json")
    results = {first_path: first, second_path: second}
    monkeypatch.setattr(tc, "_load_post_build_result", lambda path: results[path])
    _prepare_review("bio/seminar-built", run_id, first, repo=repo, config_path=config_path, ledger_root=ledger_root)

    _, ledger = tc.record_review(
        "bio/seminar-built",
        run_id=run_id,
        result_path=first_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "REPAIR_REQUIRED"
    before = json.loads(json.dumps(ledger))
    with pytest.raises(tc.CompletionError, match="Expected state SEMANTIC_REVIEW"):
        tc.record_review(
            "bio/seminar-built",
            run_id=run_id,
            result_path=second_path,
            stability_check=True,
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
    assert (
        tc.read_json(
            tc.ledger_path_for(snapshot, repo_root=repo, config=tc.load_config(config_path), ledger_root=ledger_root)
        )
        == before
    )


def test_cross_family_review_gate_and_publication(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "a1/core-unbuilt", terminal_goal="merge")
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
    _write_bundle(
        repo,
        "a1",
        "core-unbuilt",
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
    snapshot = tc.resolve_target("a1/core-unbuilt", repo_root=repo, config=tc.load_config(config_path))
    passing = _result(snapshot, repo, status="PASS")
    passing["semantic_response"] = {"raw_sha256": "f" * 64}
    result_path = _result_file(tmp_path, "pass.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: passing)
    _prepare_review("a1/core-unbuilt", run_id, passing, repo=repo, config_path=config_path, ledger_root=ledger_root)
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
    assert ledger["state"] == "INDEPENDENT_REVIEW_REQUIRED"
    inputs = tc.certification_inputs("a1/core-unbuilt", repo_root=repo, config_path=config_path, ledger=ledger)
    independent = _certification_artifact(
        tmp_path,
        "strict-independent.json",
        inputs,
        "independent-review",
        diff_sha256="e" * 64,
    )
    _, ledger = tc.record_certification_evidence(
        "a1/core-unbuilt",
        run_id=run_id,
        evidence=independent,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "PUBLISH_REQUIRED"
    _, ledger = tc.record_published(
        "a1/core-unbuilt",
        run_id=run_id,
        pr=5156,
        merge_sha="d" * 40,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "INTEGRATION_REQUIRED"
    integration = _certification_artifact(
        tmp_path,
        "strict-integration.json",
        inputs,
        "integration",
        diff_sha256="e" * 64,
        independent_evidence_sha256=tc.sha256_file(independent),
    )
    _, ledger = tc.record_certification_evidence(
        "a1/core-unbuilt",
        run_id=run_id,
        evidence=integration,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "COMPLETE"
    assert ledger["run"]["status"] == "completed"


def test_bounded_ledger_records_initial_repair_final_and_one_time_semantic_reuse(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "a1/core-unbuilt")
    run_id = ledger["run"]["run_id"]
    plan_evidence = tmp_path / "bounded-plan.json"
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
    _write_bundle(repo, "a1", "core-unbuilt", "# Модуль\n\nПочатковий навчальний текст.\n")
    _, ledger = tc.record_build(
        "a1/core-unbuilt",
        run_id=run_id,
        author_family="codex",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    snapshot = tc.resolve_target("a1/core-unbuilt", repo_root=repo, config=tc.load_config(config_path))
    initial = _result(snapshot, repo, status="REVISE", reviewer_family="gemini")
    initial_path = _result_file(tmp_path, "bounded-initial.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: initial)
    _prepare_review("a1/core-unbuilt", run_id, initial, repo=repo, config_path=config_path, ledger_root=ledger_root)
    _, ledger = tc.record_review(
        "a1/core-unbuilt",
        run_id=run_id,
        result_path=initial_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    bounded = ledger["bounded_completion"]
    assert bounded["run"]["reviews"][0]["phase"] == "INITIAL"
    assert bounded["run"]["measurements"]["model_call_count"] == 1
    assert bounded["run"]["measurements"]["repair_count"] == 0
    assert bounded["remaining_budgets"] == {"semantic_reviews": 1, "consolidated_repairs": 1}

    content = repo / snapshot.review_files["content"]
    content.write_text(content.read_text(encoding="utf-8") + "Консолідоване виправлення.\n", encoding="utf-8")
    _, ledger = tc.record_change(
        "a1/core-unbuilt",
        run_id=run_id,
        owner_kind="built_artifact",
        author_family="codex",
        summary="Applied the one consolidated learner repair.",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    bounded = ledger["bounded_completion"]
    assert bounded["run"]["repairs"][0]["invalidated_evidence_ids"] == [tc.sha256_file(initial_path)]
    assert bounded["run"]["reviews"][0]["valid"] is False
    assert bounded["run"]["measurements"]["repair_count"] == 1
    assert bounded["remaining_budgets"] == {"semantic_reviews": 1, "consolidated_repairs": 0}

    refreshed = tc.resolve_target("a1/core-unbuilt", repo_root=repo, config=tc.load_config(config_path))
    final = _result(refreshed, repo, status="PASS", reviewer_family="gemini")
    final["semantic_response"] = {
        "raw_sha256": "f" * 64,
        "byte_count": 12,
        "contract_status": "valid",
    }
    final_path = _result_file(tmp_path, "bounded-final.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: final)
    _prepare_review("a1/core-unbuilt", run_id, final, repo=repo, config_path=config_path, ledger_root=ledger_root)
    _, ledger = tc.record_review(
        "a1/core-unbuilt",
        run_id=run_id,
        result_path=final_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    bounded = ledger["bounded_completion"]
    assert [review["phase"] for review in bounded["run"]["reviews"]] == ["INITIAL", "FINAL"]
    assert bounded["run"]["measurements"]["model_call_count"] == 2
    assert bounded["remaining_budgets"] == {"semantic_reviews": 0, "consolidated_repairs": 0}
    assert bounded["semantic_review_reuse"]["review_result_sha256"] == tc.sha256_file(final_path)
    assert ledger["state"] == "AWAITING_PRODUCTION_QG_ARMING"
    projection = tc.certification_projection(
        "a1/core-unbuilt", repo_root=repo, config_path=config_path, ledger_root=ledger_root
    )
    assert projection["independent_review"] == "reused-canonical-semantic-review"

    (repo / "workflow.txt").write_text("workflow-deferred\n", encoding="utf-8")
    _, ledger = tc.record_change(
        "a1/core-unbuilt",
        run_id=run_id,
        owner_kind="audit_tooling",
        author_family="codex",
        summary="Queue the post-build workflow revision for a later run.",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "AWAITING_PRODUCTION_QG_ARMING"
    assert ledger["bounded_completion"]["remaining_budgets"] == {"semantic_reviews": 0, "consolidated_repairs": 0}
    assert ledger["deferred_workflow_drift"][-1]["classification"] == "AUDIT_TOOLING_DEFERRED"

    before = json.loads(json.dumps(ledger))
    content.write_text(content.read_text(encoding="utf-8") + "Друге виправлення.\n", encoding="utf-8")
    with pytest.raises(tc.CompletionError, match="REPAIR_BUDGET_EXHAUSTED"):
        tc.record_change(
            "a1/core-unbuilt",
            run_id=run_id,
            owner_kind="built_artifact",
            author_family="codex",
            summary="Forbidden second learner repair.",
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
    persisted = tc.read_json(
        tc.ledger_path_for(refreshed, repo_root=repo, config=tc.load_config(config_path), ledger_root=ledger_root)
    )
    assert persisted == before


@pytest.mark.parametrize("repair_state", ["PUBLISH_REQUIRED", "INTEGRATION_REQUIRED"])
def test_post_review_drift_can_be_recorded_and_restarts_post_build_review(
    fake_repo: tuple[Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    repair_state: str,
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "a1/core-unbuilt")
    run_id = ledger["run"]["run_id"]
    plan_evidence = tmp_path / "plan-review.json"
    plan_evidence.write_text('{"verdict":"PASS"}\n', encoding="utf-8")
    tc.record_plan_review(
        "a1/core-unbuilt",
        run_id=run_id,
        verdict="PASS",
        evidence=plan_evidence,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    _write_bundle(repo, "a1", "core-unbuilt", "# Модуль\n\nСвіжий навчальний матеріал.\n")
    _, ledger = tc.record_build(
        "a1/core-unbuilt",
        run_id=run_id,
        author_family="codex",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    snapshot = tc.resolve_target("a1/core-unbuilt", repo_root=repo, config=tc.load_config(config_path))
    passing = _result(snapshot, repo, status="PASS", reviewer_family="codex")
    passing["semantic_response"] = {"raw_sha256": "f" * 64}
    result_path = _result_file(tmp_path, "integration-pass.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: passing)
    _prepare_review("a1/core-unbuilt", run_id, passing, repo=repo, config_path=config_path, ledger_root=ledger_root)
    _, ledger = tc.record_review(
        "a1/core-unbuilt",
        run_id=run_id,
        result_path=result_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    review_evidence = tmp_path / "independent-review.md"
    review_evidence.write_text("Independent review passed.\n", encoding="utf-8")
    _, ledger = tc.record_independent_review(
        "a1/core-unbuilt",
        run_id=run_id,
        reviewer_family="anthropic",
        verdict="PASS",
        evidence=review_evidence,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert ledger["state"] == "INDEPENDENT_REVIEW_REQUIRED"
    ledger["state"] = repair_state
    tc._atomic_write_json(
        tc.ledger_path_for(
            snapshot,
            repo_root=repo,
            config=tc.load_config(config_path),
            ledger_root=ledger_root,
        ),
        ledger,
    )

    content = repo / snapshot.review_files["content"]
    content.write_text(content.read_text(encoding="utf-8") + "Інтеграційне виправлення.\n", encoding="utf-8")
    with pytest.raises(tc.CompletionError, match="Expected state CONSOLIDATED_REPAIR"):
        tc.record_change(
            "a1/core-unbuilt",
            run_id=run_id,
            owner_kind="built_artifact",
            author_family="codex",
            summary="Regenerated the learner surface after the integration gate exposed drift.",
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )


def test_legacy_qg_sidecar_cannot_advance_completion(fake_repo: tuple[Path, Path, Path]) -> None:
    repo, config_path, _ledger_root = fake_repo
    legacy = repo / "curriculum/l2-uk-en/bio/seminar-built/llm_qg.json"
    legacy.write_text('{"aggregate":{"verdict":"PASS"}}\n', encoding="utf-8")

    _, ledger = _start(fake_repo, "bio/seminar-built")
    snapshot = tc.resolve_target("bio/seminar-built", repo_root=repo, config=tc.load_config(config_path))

    assert ledger["state"] == "POST_BUILD_REVIEW_REQUIRED"
    assert "llm_qg" not in snapshot.observed_files


def test_legacy_review_history_requires_explicit_bounded_migration(fake_repo: tuple[Path, Path, Path]) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "bio/seminar-built")
    run_id = ledger["run"]["run_id"]
    ledger.pop("bounded_completion")
    ledger["reviews"].append(
        {
            "result_path": "/outside/legacy.json",
            "result_sha256": "a" * 64,
            "reproducibility_key": "b" * 64,
            "stability_key": "c" * 64,
            "material_fingerprint": "d" * 64,
            "status": "PASS",
            "reviewer_family": "gemini",
            "reviewer_model": "legacy",
            "target_identity_sha256": ledger["current_identity"]["sha256"],
        }
    )
    snapshot = tc.resolve_target("bio/seminar-built", repo_root=repo, config=tc.load_config(config_path))
    tc._atomic_write_json(
        tc.ledger_path_for(snapshot, repo_root=repo, config=tc.load_config(config_path), ledger_root=ledger_root),
        ledger,
    )
    with pytest.raises(tc.CompletionError, match="Legacy ledger requires migrate-bounded-completion"):
        _prepare_review(
            "bio/seminar-built",
            run_id,
            _result(snapshot, repo, status="PASS"),
            repo=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
    _, migrated = tc.migrate_bounded_completion(
        "bio/seminar-built", run_id=run_id, repo_root=repo, config_path=config_path, ledger_root=ledger_root
    )
    assert migrated["state"] == "MIGRATION_REQUIRED"
    assert migrated["history"][-1]["details"] == {"legacy_review_count": 1, "recovery": "start-later-bounded-run"}


def _advance_built_module_to_pending_review_state(
    fake_repo: tuple[Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pending_state: str,
) -> tuple[str, dict[str, Any]]:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "bio/seminar-built")
    run_id = ledger["run"]["run_id"]
    if pending_state == "INDEPENDENT_REVIEW_REQUIRED":
        workflow = repo / "workflow.txt"
        workflow.write_text("workflow-before-review\n", encoding="utf-8")
        _, ledger = tc.record_change(
            "bio/seminar-built",
            run_id=run_id,
            owner_kind="audit_tooling",
            author_family="codex",
            summary="Bind the authored module to the pre-review workflow.",
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
        snapshot = tc.resolve_target(
            "bio/seminar-built",
            repo_root=repo,
            config=tc.load_config(config_path),
        )
        passing = _result(snapshot, repo, status="PASS")
        passing["semantic_response"] = {"raw_sha256": "f" * 64}
        result_path = _result_file(tmp_path, "pending-review-pass.json")
        monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: passing)
        _prepare_review(
            "bio/seminar-built", run_id, passing, repo=repo, config_path=config_path, ledger_root=ledger_root
        )
        _, ledger = tc.record_review(
            "bio/seminar-built",
            run_id=run_id,
            result_path=result_path,
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )
    assert ledger["state"] == pending_state
    return run_id, ledger


@pytest.mark.parametrize(
    "pending_state",
    ["POST_BUILD_REVIEW_REQUIRED"],
)
def test_pending_review_states_accept_workflow_only_audit_tooling_refresh(
    fake_repo: tuple[Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pending_state: str,
) -> None:
    repo, config_path, ledger_root = fake_repo
    run_id, ledger = _advance_built_module_to_pending_review_state(fake_repo, tmp_path, monkeypatch, pending_state)
    original_target_hashes = ledger["current_identity"]["target_hashes"]

    workflow = repo / "workflow.txt"
    workflow.write_text("workflow-refresh\n", encoding="utf-8")
    _, refreshed = tc.record_change(
        "bio/seminar-built",
        run_id=run_id,
        owner_kind="audit_tooling",
        author_family="codex",
        summary="Integrated a new post-build review protocol before its pending review.",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )

    assert refreshed["state"] == pending_state
    assert refreshed["current_identity"]["target_hashes"] == original_target_hashes
    assert refreshed["current_identity"]["workflow_hashes"] == ledger["current_identity"]["workflow_hashes"]
    assert refreshed["deferred_workflow_drift"][-1]["classification"] == "AUDIT_TOOLING_DEFERRED"


@pytest.mark.parametrize(
    "pending_state",
    ["POST_BUILD_REVIEW_REQUIRED"],
)
@pytest.mark.parametrize(
    ("drift_kind", "error"),
    [
        ("target", "unchanged target hashes"),
        ("layout", "unchanged module layout and state"),
        ("module_state", "unchanged module layout and state"),
    ],
)
def test_pending_review_audit_refresh_rejects_non_workflow_drift(
    fake_repo: tuple[Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pending_state: str,
    drift_kind: str,
    error: str,
) -> None:
    repo, config_path, ledger_root = fake_repo
    run_id, _ledger = _advance_built_module_to_pending_review_state(fake_repo, tmp_path, monkeypatch, pending_state)
    (repo / "workflow.txt").write_text("workflow-refresh\n", encoding="utf-8")
    if drift_kind == "target":
        content = repo / "curriculum/l2-uk-en/bio/seminar-built/module.md"
        content.write_text(
            content.read_text(encoding="utf-8") + "Незаписана зміна.\n",
            encoding="utf-8",
        )
    else:
        changed_value = "flat" if drift_kind == "layout" else "PARTIAL"
        real_build_identity = tc.build_identity

        def drifted_identity(*args: object, **kwargs: object) -> dict[str, Any]:
            identity = real_build_identity(*args, **kwargs)
            identity[drift_kind] = changed_value
            payload = {key: identity[key] for key in ("module_state", "layout", "target_hashes", "workflow_hashes")}
            identity["sha256"] = tc.sha256_bytes(tc.stable_json(payload).encode("utf-8"))
            return identity

        monkeypatch.setattr(tc, "build_identity", drifted_identity)

    with pytest.raises(tc.CompletionError, match=error):
        tc.record_change(
            "bio/seminar-built",
            run_id=run_id,
            owner_kind="audit_tooling",
            author_family="codex",
            summary="Must not disguise non-workflow drift as review tooling.",
            repo_root=repo,
            config_path=config_path,
            ledger_root=ledger_root,
        )


def test_qg_arming_boundary_accepts_review_tooling_refresh(
    fake_repo: tuple[Path, Path, Path],
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "bio/seminar-built")
    run_id = ledger["run"]["run_id"]
    snapshot = tc.resolve_target("bio/seminar-built", repo_root=repo, config=tc.load_config(config_path))
    path = tc.ledger_path_for(
        snapshot,
        repo_root=repo,
        config=tc.load_config(config_path),
        ledger_root=ledger_root,
    )
    ledger["state"] = "AWAITING_PRODUCTION_QG_ARMING"
    ledger["publication"] = {
        "pr": 123,
        "merge_sha": "a" * 40,
        "recorded_at": "2026-01-01T00:00:00+00:00",
    }
    tc._atomic_write_json(path, ledger)
    original_target_hashes = ledger["current_identity"]["target_hashes"]

    (repo / "workflow.txt").write_text("workflow-v2\n", encoding="utf-8")
    _, refreshed = tc.record_change(
        "bio/seminar-built",
        run_id=run_id,
        owner_kind="audit_tooling",
        author_family="codex",
        summary="Upgraded the versioned post-build review before production QG arming.",
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )

    assert refreshed["state"] == "AWAITING_PRODUCTION_QG_ARMING"
    assert refreshed["current_identity"]["target_hashes"] == original_target_hashes
    assert refreshed["publication"] == ledger["publication"]
    assert refreshed["production_qg_authorization"] == ledger["production_qg_authorization"]
    assert refreshed["deferred_workflow_drift"][-1]["classification"] == "AUDIT_TOOLING_DEFERRED"


def test_historical_post_build_result_cannot_advance_current_ledger() -> None:
    historical = ROOT / "tests" / "fixtures" / "post_build_review" / "bio-oleksandr-bilash.result.v2.json"

    with pytest.raises(tc.CompletionError, match="historical"):
        tc._load_post_build_result(historical)


def test_certification_never_accepts_a_second_post_build_gate(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    repo, config_path, ledger_root = fake_repo
    _start(fake_repo, "a1/core-built")
    fabricated = tmp_path / "fabricated-pbr.json"
    fabricated.write_text(
        json.dumps(
            {
                "schema_version": "certification-evidence.v1",
                "kind": "post-build",
                "target": "a1/core-built",
                "profile": {"id": "core", "version": "1.0.0"},
                "preparation_identity": "a" * 64,
                "learner_hashes": {"content": "b" * 64},
                "pbr": {"verdict": "PASS"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(tc.certification.CertificationEvidenceError):
        tc.certification.read_evidence(fabricated)
    assert (
        tc.certification_projection("a1/core-built", repo_root=repo, config_path=config_path, ledger_root=ledger_root)[
            "final"
        ]
        == "not-certified"
    )


def test_projection_uses_only_bound_canonical_pbr_review(
    fake_repo: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, config_path, ledger_root = fake_repo
    _, ledger = _start(fake_repo, "a1/core-built")
    snapshot = tc.resolve_target("a1/core-built", repo_root=repo, config=tc.load_config(config_path))
    inputs = {
        "target": "a1/core-built",
        "profile": {"id": "core", "version": "1.0.0"},
        "preparation_identity": "1" * 64,
        "learner_hashes": {"content": tc.sha256_file(repo / snapshot.review_files["content"])},
        "plan_hash": tc.sha256_file(repo / snapshot.review_files["plan"]),
        "workflow_hashes": {"workflow.txt": tc.sha256_file(repo / "workflow.txt")},
        "pbr_dependency_identity": "2" * 64,
        "profile_config": {"production_qg": {"mode": "disabled"}},
        "qg_identity": {},
    }
    result = _result(snapshot, repo, status="PASS")
    result["semantic_response"] = {"raw_sha256": "3" * 64}
    result_path = _result_file(tmp_path, "canonical.json")
    monkeypatch.setattr(tc, "_load_post_build_result", lambda _path: result)
    monkeypatch.setattr(tc, "certification_inputs", lambda *_args, **_kwargs: inputs)
    _prepare_review(
        "a1/core-built", ledger["run"]["run_id"], result, repo=repo, config_path=config_path, ledger_root=ledger_root
    )
    _, updated = tc.record_review(
        "a1/core-built",
        run_id=ledger["run"]["run_id"],
        result_path=result_path,
        repo_root=repo,
        config_path=config_path,
        ledger_root=ledger_root,
    )
    assert updated["reviews"][-1]["certification"]["raw_response_sha256"] == "3" * 64
    assert (
        tc.certification_projection("a1/core-built", repo_root=repo, config_path=config_path, ledger_root=ledger_root)[
            "state"
        ]
        == "AWAITING_PRODUCTION_QG_ARMING"
    )
    updated["reviews"][-1]["certification"]["dependency_identity"] = "4" * 64
    assert tc._current_pbr_reviews(updated, inputs)[0] is False


def test_projection_has_no_caller_controlled_preparation_identity() -> None:
    assert "preparation_identity" not in tc.certification_projection.__annotations__
    assert "preparation_identity" not in tc.certification_inputs.__annotations__
    assert "preparation_identity" not in tc.request_preparation_rebuild.__annotations__


def test_pages_deploy_installs_schema_runtime_and_emits_exact_head_marker() -> None:
    workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
    trigger_block = workflow.split("on:\n", 1)[1].split("permissions:\n", 1)[0]

    assert "jsonschema==4.26.0" in workflow
    assert "learn-ukrainian-deployment-${GITHUB_SHA}.txt" in workflow
    assert "printf '%s\\n' \"$GITHUB_SHA\"" in workflow
    assert "workflow_dispatch:" in trigger_block
    assert "push:" not in trigger_block
