from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from scripts.orchestration import curriculum_readiness as readiness
from scripts.orchestration import prompt_contracts
from scripts.orchestration.prompt_contracts import (
    load_active_tracks,
    resolve_profile_selectors,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BIO_SLUG = "borys-hrinchenko"


def _copy(repo_root: Path, relative: str | Path) -> None:
    relative = Path(relative)
    source = REPO_ROOT / relative
    target = repo_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def _copy_contracts(repo_root: Path) -> None:
    _copy(repo_root, "agents_extensions/shared/curriculum-lifecycle")
    _copy(repo_root, "agents_extensions/shared/prompt-contracts")


def _bio_fixture(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    _copy_contracts(repo_root)
    for relative in (
        "curriculum/l2-uk-en/curriculum.yaml",
        "curriculum/l2-uk-en/bio/promotion-evidence.yaml",
        f"curriculum/l2-uk-en/plans/bio/{BIO_SLUG}.yaml",
        f"curriculum/l2-uk-en/bio/discovery/{BIO_SLUG}.yaml",
        f"docs/research/bio/{BIO_SLUG}.md",
        f"wiki/figures/{BIO_SLUG}.md",
        f"wiki/figures/{BIO_SLUG}.sources.yaml",
    ):
        _copy(repo_root, relative)
    return repo_root


def _write_manifest(repo_root: Path, track: str, manifest_type: str, slug: str) -> None:
    path = repo_root / readiness.MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "levels": {track: {"type": manifest_type, "modules": [slug]}},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    profiles_path = repo_root / "agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml"
    profiles = yaml.safe_load(profiles_path.read_text(encoding="utf-8"))
    selected = profiles["selectors"]["tracks"].get(track)
    profiles["selectors"]["tracks"] = {track: selected} if selected else {}
    profiles["selectors"]["manifest_types"] = {
        manifest_type: profiles["selectors"]["manifest_types"][manifest_type]
    }
    profiles_path.write_text(yaml.safe_dump(profiles, sort_keys=False), encoding="utf-8")
    readiness_path = repo_root / readiness.CONFIG_PATH
    readiness_config = yaml.safe_load(readiness_path.read_text(encoding="utf-8"))
    readiness_selected = readiness_config["selectors"]["tracks"].get(track)
    readiness_config["selectors"]["tracks"] = (
        {track: readiness_selected} if readiness_selected else {}
    )
    readiness_config["selectors"]["manifest_types"] = {
        manifest_type: readiness_config["selectors"]["manifest_types"][manifest_type]
    }
    readiness_path.write_text(yaml.safe_dump(readiness_config, sort_keys=False), encoding="utf-8")


def _create_bundle(repo_root: Path, track: str, slug: str) -> None:
    directory = repo_root / "curriculum" / "l2-uk-en" / track / slug
    directory.mkdir(parents=True, exist_ok=True)
    for filename in readiness.MODULE_BUNDLE_FILES:
        (directory / filename).write_text(f"fixture: {filename}\n", encoding="utf-8")


def test_bio_profile_expresses_complete_preparation_without_track_branches() -> None:
    config = readiness.load_config(repo_root=REPO_ROOT)
    bio = config["profiles"]["bio"]
    requirement_ids = {item["id"] for item in bio["requirements"]}
    validators = {
        validator
        for requirement in bio["requirements"]
        for option in requirement["options"]
        for validator in option["validators"]
    }

    assert requirement_ids == {
        "dossier",
        "dossier-grounding",
        "plan",
        "reading-or-rights",
        "wiki-document",
        "wiki-sources",
        "wiki-grounding",
        "wiki-quote-verification",
        "image-rights",
        "discovery",
    }
    assert {
        "bio-dossier-xref",
        "plan-check",
        "readings-present",
        "manual-gate",
        "wiki-completeness",
        "bio-wiki-subject",
        "bio-discovery-integrity",
    } <= validators
    assert set(config["profiles"]) == {"core", "seminar", "bio"}
    assert all("certification" not in profile for profile in config["profiles"].values())
    engine_source = (REPO_ROOT / "scripts/orchestration/curriculum_readiness.py").read_text(encoding="utf-8")
    assert 'track == "bio"' not in engine_source
    assert "llm_qg" not in engine_source
    assert "sqlite" not in engine_source


def test_all_active_tracks_resolve_readiness_certification_and_prompt_profiles() -> None:
    active = load_active_tracks(REPO_ROOT)
    readiness_config = readiness.load_config(repo_root=REPO_ROOT)
    readiness_profiles = resolve_profile_selectors(
        selectors=readiness_config["selectors"],
        profile_families={
            profile_id: profile["family"]
            for profile_id, profile in readiness_config["profiles"].items()
        },
        active_tracks=active,
        label="readiness test",
    )
    certification_path = (
        REPO_ROOT
        / "agents_extensions/shared/curriculum-lifecycle/config/certification-profiles.v1.yaml"
    )
    certification = yaml.safe_load(certification_path.read_text(encoding="utf-8"))
    certification_profiles = resolve_profile_selectors(
        selectors=certification["selectors"],
        profile_families={
            profile_id: profile["family"]
            for profile_id, profile in certification["profiles"].items()
        },
        active_tracks=active,
        label="certification test",
    )
    semantic_profiles = prompt_contracts.active_track_profiles(repo_root=REPO_ROOT)

    assert set(readiness_profiles) == set(active)
    assert set(certification_profiles) == set(active)
    assert set(semantic_profiles) == set(active)
    assert readiness_profiles["bio"] == "bio"
    assert certification_profiles["bio"] == "bio-pending"
    assert semantic_profiles["a1"] == "core-a1"
    assert semantic_profiles["folk"] == "seminar-folk"


def test_prepared_unbuilt_bio_uses_real_validators_and_exact_sources(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["profile_id"] == "bio"
    assert result["module_state"] == "unbuilt"
    assert result["preparation_state"] == "current"
    assert result["state"] == "prepared-plan"
    assert result["next_action"] == "build"
    assert result["findings"] == []
    assert all(requirement["passed"] for requirement in result["requirements"])
    assert len(result["preparation_identity"]) == 64
    readiness.validate_result(result, repo_root=repo_root)


def test_preparation_identity_is_stable_across_clean_repository_roots(tmp_path: Path) -> None:
    first_root = _bio_fixture(tmp_path / "first")
    second_root = _bio_fixture(tmp_path / "second")

    first = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=first_root)
    second = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=second_root)

    assert first["preparation_identity"] == second["preparation_identity"]
    assert first["sources"] == second["sources"]


def test_registered_prompt_profile_bytes_are_preparation_identity_inputs(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    before = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    prompt_profiles = repo_root / "agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml"
    prompt_profiles.write_text(prompt_profiles.read_text(encoding="utf-8") + "# identity change\n", encoding="utf-8")

    after = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert after["state"] == before["state"]
    assert after["preparation_identity"] != before["preparation_identity"]


def test_missing_bio_evidence_fails_closed_with_preparation_owner(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    (repo_root / f"docs/research/bio/{BIO_SLUG}.md").unlink()

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["state"] == "preparation-required"
    assert result["next_action"] == "prepare"
    finding = next(item for item in result["findings"] if item["id"] == "PREPARATION_DOSSIER")
    assert finding["owner"] == "preparation"


def test_reviewed_active_hold_is_a_terminal_stop_with_a_blocker_receipt(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    registry_path = repo_root / "curriculum/l2-uk-en/bio/promotion-evidence.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["entries"][BIO_SLUG]["hold"] = {
        "status": "pass",
        "reviewer_family": "codex",
        "date": "2026-07-19",
        "evidence_url": "https://example.test/reviewed-hold",
        "active": True,
        "reason": "The terminal factual review found an unresolved source conflict.",
        "owner": "bio-preparation-controller",
        "checked_evidence": ["immutable packet review and adopted source set"],
        "unblock_condition": "A stable authoritative source resolves the conflict.",
    }
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["preparation_state"] == "missing"
    assert result["state"] == "preparation-required"
    assert result["next_action"] == "stop"
    assert "PREPARATION_HOLD_ACTIVE" in {item["id"] for item in result["findings"]}
    readiness.validate_result(result, repo_root=repo_root)

    _create_bundle(repo_root, "bio", BIO_SLUG)
    built = readiness.evaluate_preparation(
        "bio",
        BIO_SLUG,
        consumed_preparation_identity=result["preparation_identity"],
        repo_root=repo_root,
    )

    assert built["module_state"] == "built"
    assert built["preparation_state"] == "missing"
    assert built["state"] == "preparation-required"
    assert built["next_action"] == "stop"
    assert "PREPARATION_HOLD_ACTIVE" in {item["id"] for item in built["findings"]}
    readiness.validate_result(built, repo_root=repo_root)


def test_missing_plan_routes_to_plan_owner(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    (repo_root / f"curriculum/l2-uk-en/plans/bio/{BIO_SLUG}.yaml").unlink()

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["state"] == "missing-plan"
    assert result["next_action"] == "plan"
    finding = next(item for item in result["findings"] if item["id"] == "PREPARATION_PLAN")
    assert finding["owner"] == "plan"


def test_built_module_is_current_only_with_consumed_preparation_identity(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    prepared = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    _create_bundle(repo_root, "bio", BIO_SLUG)

    missing_link = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    current = readiness.evaluate_preparation(
        "bio",
        BIO_SLUG,
        consumed_preparation_identity=prepared["preparation_identity"],
        repo_root=repo_root,
    )

    assert missing_link["state"] == "built-preparation-drift"
    assert "PREPARATION_IDENTITY_MISSING" in {item["id"] for item in missing_link["findings"]}
    assert current["state"] == "built-current"
    assert current["preparation_state"] == "current"
    assert current["next_action"] == "certify"


def test_preparation_change_invalidates_build_pbr_and_qg_identities(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    prepared = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    consumed = prepared["preparation_identity"]
    before = {
        evidence_class: readiness.dependent_evidence_identity(
            evidence_class,
            consumed,
            {"artifact": "fixture-v1"},
        )
        for evidence_class in readiness.DEPENDENT_EVIDENCE_CLASSES
    }
    _create_bundle(repo_root, "bio", BIO_SLUG)
    dossier = repo_root / f"docs/research/bio/{BIO_SLUG}.md"
    dossier.write_text(dossier.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    drifted = readiness.evaluate_preparation(
        "bio",
        BIO_SLUG,
        consumed_preparation_identity=consumed,
        repo_root=repo_root,
    )
    after = {
        evidence_class: readiness.dependent_evidence_identity(
            evidence_class,
            drifted["preparation_identity"],
            {"artifact": "fixture-v1"},
        )
        for evidence_class in readiness.DEPENDENT_EVIDENCE_CLASSES
    }

    assert drifted["state"] == "built-preparation-drift"
    assert drifted["preparation_identity"] != consumed
    assert before.keys() == after.keys()
    assert all(before[key] != after[key] for key in before)


@pytest.mark.parametrize(
    ("track", "manifest_type", "slug", "plan_source", "expected_profile"),
    [
        ("a1", "core", "sounds-letters-and-hello", "plans/a1/sounds-letters-and-hello.yaml", "core"),
        ("hist", "track", "trypillian-civilization", "plans/hist/trypillian-civilization.yaml", "seminar"),
    ],
)
def test_unbuilt_core_and_generic_seminar_profile_seams(
    tmp_path: Path,
    track: str,
    manifest_type: str,
    slug: str,
    plan_source: str,
    expected_profile: str,
) -> None:
    repo_root = tmp_path / track
    _copy_contracts(repo_root)
    _write_manifest(repo_root, track, manifest_type, slug)
    _copy(repo_root, f"curriculum/l2-uk-en/{plan_source}")

    result = readiness.evaluate_preparation(track, slug, repo_root=repo_root)

    assert result["profile_id"] == expected_profile
    assert result["module_state"] == "unbuilt"
    assert result["state"] == "prepared-plan"
    assert result["next_action"] == "build"


def test_off_manifest_target_fails_with_authority_owner(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)

    result = readiness.evaluate_preparation("bio", "not-in-curriculum", repo_root=repo_root)

    assert result["state"] == "off-manifest"
    assert result["next_action"] == "stop"
    assert result["preparation_identity"] is None
    assert result["findings"] == [
        {
            "id": "OFF_MANIFEST_TARGET",
            "category": "authority",
            "severity": "blocker",
            "summary": "Target is not an active curriculum manifest member",
            "owner": "authority",
        }
    ]


def test_legacy_qg_files_and_mtimes_are_not_readiness_inputs(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    before = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    module_dir = repo_root / "curriculum/l2-uk-en/bio" / BIO_SLUG
    module_dir.mkdir(parents=True)
    (module_dir / "llm_qg.json").write_text('{"terminal_verdict":"PASS"}\n', encoding="utf-8")
    (module_dir / "qg_evidence.json").write_text('{"passed":true}\n', encoding="utf-8")
    (module_dir / "legacy-qg.sqlite3").write_bytes(b"not a database")
    after = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert after["state"] == before["state"]
    assert after["preparation_identity"] == before["preparation_identity"]
    assert not any("qg" in source["path"].lower() or "sqlite" in source["path"].lower() for source in after["sources"])


def test_partial_bundle_stops_for_built_artifact_recovery(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    module_dir = repo_root / "curriculum/l2-uk-en/bio" / BIO_SLUG
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("# Partial\n", encoding="utf-8")

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["state"] == "partial-bundle"
    assert result["next_action"] == "stop"
    assert "PARTIAL_LEARNER_BUNDLE" in {item["id"] for item in result["findings"]}


def test_config_rejects_raw_prose_and_unknown_selector(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _copy_contracts(repo_root)
    config_path = repo_root / readiness.CONFIG_PATH
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["profiles"]["core"]["prompt_text"] = "free-form bypass"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(readiness.ReadinessError, match="Additional properties"):
        readiness.load_config(repo_root=repo_root)

    _copy_contracts(repo_root := tmp_path / "selector")
    config_path = repo_root / readiness.CONFIG_PATH
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["selectors"]["tracks"]["bio"] = "missing-profile"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(readiness.ReadinessError, match="unknown profile"):
        readiness.load_config(repo_root=repo_root)


def test_readiness_config_rejects_retired_track_selector(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _copy_contracts(repo_root)
    _copy(repo_root, "curriculum/l2-uk-en/curriculum.yaml")
    config_path = repo_root / readiness.CONFIG_PATH
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["selectors"]["tracks"]["lit-doc"] = "seminar"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(readiness.ReadinessError, match="inactive tracks: lit-doc"):
        readiness.load_config(repo_root=repo_root)


def test_readiness_contract_rejects_certification_policy_declarations(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _copy_contracts(repo_root)
    config_path = repo_root / readiness.CONFIG_PATH
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["profiles"]["core"]["certification"] = {"production_qg": {"mode": "armed-canary"}}
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(readiness.ReadinessError, match="Additional properties"):
        readiness.load_config(repo_root=repo_root)


def test_dependent_identity_rejects_unknown_evidence_class() -> None:
    with pytest.raises(readiness.ReadinessError, match="unsupported dependent evidence class"):
        readiness.dependent_evidence_identity("legacy-qg", "a" * 64, {"artifact": "v1"})
