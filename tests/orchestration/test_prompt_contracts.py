from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest
import yaml

from scripts.lint import lint_prompts
from scripts.orchestration import prompt_contracts as contracts

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("agents_extensions/shared/prompt-contracts/manifests/curriculum-lifecycle.module.v1.yaml")
PROFILES = Path("agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml")
REGISTRY = Path("agents_extensions/shared/prompt-contracts/registry.v1.yaml")
INPUT_SCHEMA = Path("agents_extensions/shared/prompt-contracts/schema/curriculum-lifecycle-input.v1.schema.json")
COMMON_FRAGMENT = Path("agents_extensions/shared/prompt-contracts/fragments/curriculum-lifecycle-common.md")
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/prompt_contracts"

CORE_CONTEXT = {
    "track": "a1",
    "slug": "introductions",
    "family": "core",
    "phase": "build",
    "module_state": "unbuilt",
    "evidence_identity": "a" * 64,
}
SEMINAR_CONTEXT = {
    "track": "bio",
    "slug": "lesia-ukrainka",
    "family": "seminar",
    "phase": "certify",
    "module_state": "built",
    "evidence_identity": "b" * 64,
}

QUALIFICATION_PROFILES = (
    (
        "core-a1",
        "a1",
        "core",
        "A1 CORE policy",
        "A2 CORE policy",
        "f551ca42295b8fd7f5e675919c5d0c71e96bd1c57dffa1a65062c48045d759d0",
    ),
    (
        "core-a2",
        "a2",
        "core",
        "A2 CORE policy",
        "A1 CORE policy",
        "9c467a36ac927fd7995911ede4ceb438243aea38f4204d3fdcef564a4c51c3d5",
    ),
    (
        "core-b1",
        "b1",
        "core",
        "B1 CORE policy",
        "B2 CORE policy",
        "767ec0a4f22068b405697bf5625c4b1716118c28cbf86872ddfaa19492962910",
    ),
    (
        "core-b2",
        "b2",
        "core",
        "B2 CORE policy",
        "B1 CORE policy",
        "199e1dd75d0a434ee1733b03b28fd3222366455ae6e76a5ea40f847e4bb63a2c",
    ),
    (
        "core-c1",
        "c1",
        "core",
        "C1 CORE policy",
        "C2 CORE policy",
        "1135b02e5a1d34fac272520e36cbde732eeff1db3ce9ffcaa9f9f78b30d110a3",
    ),
    (
        "core-c2",
        "c2",
        "core",
        "C2 CORE policy",
        "C1 CORE policy",
        "528ff17188bf18d6c8dac22330d0462eb9c32de03ad7d317aaac4841cf1a8f86",
    ),
    (
        "seminar-bio",
        "bio",
        "seminar",
        "BIO seminar policy",
        "FOLK seminar policy",
        "8bd17b01de7d9d470dd53cde7228353b9cfdf57a4ba75250ea7425b1a448e3f5",
    ),
    (
        "seminar-folk",
        "folk",
        "seminar",
        "FOLK seminar policy",
        "BIO seminar policy",
        "f2014bfd5d5b3e56c1eef4d7c15b23d962202035f75a9eb44d2785e3c6bd9e74",
    ),
)


def _copy_contract_repo(destination: Path) -> Path:
    for relative in (
        Path("agents_extensions/shared/prompt-contracts"),
        Path("agents_extensions/shared/rules/operator-expectations.md"),
        Path("agents_extensions/shared/rules/workflow.md"),
        Path("curriculum/l2-uk-en/curriculum.yaml"),
    ):
        source = REPO_ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copyfile(source, target)
    return destination


def _load_yaml(repo_root: Path, relative: Path) -> dict:
    value = yaml.safe_load((repo_root / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_yaml(repo_root: Path, relative: Path, value: dict) -> None:
    (repo_root / relative).write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _resolve_core(repo_root: Path = REPO_ROOT) -> contracts.ResolvedPrompt:
    return contracts.resolve_profile("core", context=CORE_CONTEXT, repo_root=repo_root)


def test_contract_audit_consumes_complete_p0_responsibility_inventory() -> None:
    report = contracts.audit_contracts(repo_root=REPO_ROOT)

    assert report["canonical_source_root"] == "agents_extensions/shared/prompt-contracts"
    assert report["docs_prompts_executable_authority"] is False
    assert report["legacy_inventory_count"] == 39
    assert report["classified_inventory_count"] == 39
    assert report["unclassified_inventory"] == []
    assert report["legacy_entry_points_removed"] == 0
    assert report["legacy_entry_points_deprecated"] == 39
    assert report["legacy_operator_entry_points"] == 0
    assert report["canonical_invocation"] == "Use $curriculum-lifecycle for <track>."


def test_legacy_migration_hashes_fail_on_silent_prompt_drift(tmp_path: Path) -> None:
    migration = contracts.load_legacy_migration(repo_root=REPO_ROOT)
    legacy_root = tmp_path / "orchestrators"
    shutil.copytree(REPO_ROOT / contracts.LEGACY_PROMPT_ROOT, legacy_root)

    rogue = legacy_root / "unregistered.txt"
    rogue.write_text("not migration-classified\n", encoding="utf-8")
    with pytest.raises(contracts.PromptContractError, match="inventory drift"):
        contracts.validate_legacy_prompt_files(migration, legacy_root)
    rogue.unlink()

    assert len(contracts.validate_legacy_prompt_files(migration, legacy_root)) == 39
    target = legacy_root / "hist/suite-orchestrator.md"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(contracts.PromptContractError, match="byte hashes changed"):
        contracts.validate_legacy_prompt_files(migration, legacy_root)


def test_active_tracks_resolve_from_manifest_without_a_second_roster() -> None:
    manifest = _load_yaml(REPO_ROOT, Path("curriculum/l2-uk-en/curriculum.yaml"))
    resolved = contracts.active_track_profiles(repo_root=REPO_ROOT)

    assert set(resolved) == set(manifest["levels"])
    assert resolved["a1"] == "core-a1"
    assert resolved["c2"] == "core-c2"
    assert resolved["bio"] == "seminar-bio"
    assert resolved["folk"] == "seminar-folk"
    assert resolved["hist"] == "seminar-generic"
    assert {"history", "lit-doc", "lit-crimea"}.isdisjoint(resolved)


def test_new_manifest_track_uses_typed_family_default(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    manifest_path = Path("curriculum/l2-uk-en/curriculum.yaml")
    manifest = _load_yaml(repo_root, manifest_path)
    manifest["levels"]["new-seminar"] = {"type": "track", "modules": ["pilot"]}
    _write_yaml(repo_root, manifest_path, manifest)

    resolved = contracts.active_track_profiles(repo_root=repo_root)

    assert resolved["new-seminar"] == "seminar-generic"


def test_frozen_legacy_linter_does_not_require_a_suite_for_new_tracks(
    tmp_path: Path,
) -> None:
    legacy_root = tmp_path / "orchestrators"
    shutil.copytree(REPO_ROOT / "docs/prompts/orchestrators", legacy_root)
    manifest_path = tmp_path / "curriculum.yaml"
    manifest = _load_yaml(REPO_ROOT, Path("curriculum/l2-uk-en/curriculum.yaml"))
    manifest["levels"]["new-seminar"] = {"type": "track", "modules": ["pilot"]}
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    migration_path = tmp_path / "legacy-prompt-migration.v1.yaml"
    migration_path.write_text("schema_version: 1\n", encoding="utf-8")

    violations = lint_prompts.scan_orchestrator_suites(
        root=legacy_root,
        manifest_path=manifest_path,
        migration_path=migration_path,
    )

    missing_rules = {
        "ORCH_ACTIVE_TRACK_MISSING_PROMPT",
        "ORCH_ACTIVE_TRACK_MISSING_SUITE",
    }
    assert missing_rules.isdisjoint({item["rule"] for item in violations})


def test_stale_prompt_track_selector_fails_closed(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    manifest_path = Path("curriculum/l2-uk-en/curriculum.yaml")
    manifest = _load_yaml(repo_root, manifest_path)
    del manifest["levels"]["folk"]
    _write_yaml(repo_root, manifest_path, manifest)

    with pytest.raises(contracts.PromptContractError, match="inactive tracks: folk"):
        contracts.active_track_profiles(repo_root=repo_root)


def test_track_resolution_uses_exact_selected_profile() -> None:
    context = {
        "track": "a1",
        "slug": "pilot",
        "family": "core",
        "phase": "build",
        "module_state": "unbuilt",
        "evidence_identity": "a" * 64,
    }

    resolved = contracts.resolve_track_profile("a1", context=context, repo_root=REPO_ROOT)

    assert resolved.profile_id == "core-a1"
    assert "A1 CORE policy" in resolved.rendered_prompt


@pytest.mark.parametrize(
    ("profile_id", "context", "golden_name", "expected_sha256"),
    [
        (
            "core",
            CORE_CONTEXT,
            "core.golden.md",
            "c69c397a05112848c3d9a17726f51bcffdbc482e6a0485129f07ca6703c9657a",
        ),
        (
            "seminar",
            SEMINAR_CONTEXT,
            "seminar.golden.md",
            "371d34e6429515f698588dd4331924591d722bc52c4696f189fc5483c967ad17",
        ),
    ],
)
def test_core_and_seminar_exact_byte_goldens(
    profile_id: str,
    context: dict,
    golden_name: str,
    expected_sha256: str,
) -> None:
    resolved = contracts.resolve_profile(profile_id, context=context, repo_root=REPO_ROOT)
    golden_bytes = (GOLDEN_ROOT / golden_name).read_bytes()

    assert resolved.rendered_prompt.encode("utf-8") == golden_bytes
    assert resolved.prompt_sha256 == expected_sha256
    assert hashlib.sha256(golden_bytes).hexdigest() == expected_sha256


@pytest.mark.parametrize(
    ("variant", "context"),
    [("core", CORE_CONTEXT), ("seminar", SEMINAR_CONTEXT)],
)
def test_current_contract_keeps_generic_variant_compatibility(
    variant: str,
    context: dict,
) -> None:
    resolved = contracts.resolve_prompt(
        "curriculum-lifecycle.module",
        variant=variant,
        context=context,
        repo_root=REPO_ROOT,
    )

    assert resolved.version == "1.1.0"


@pytest.mark.parametrize(
    ("profile_id", "track", "family", "required_marker", "forbidden_marker", "expected_sha256"),
    QUALIFICATION_PROFILES,
)
def test_qualification_profiles_have_exact_level_or_track_policy_without_cross_leakage(
    profile_id: str,
    track: str,
    family: str,
    required_marker: str,
    forbidden_marker: str,
    expected_sha256: str,
) -> None:
    context = {
        "track": track,
        "slug": "pilot",
        "family": family,
        "phase": "build",
        "module_state": "unbuilt",
        "evidence_identity": "a" * 64,
    }

    resolved = contracts.resolve_profile(profile_id, context=context, repo_root=REPO_ROOT)

    assert resolved.version == "1.1.0"
    assert resolved.prompt_sha256 == expected_sha256
    assert required_marker in resolved.rendered_prompt
    assert forbidden_marker not in resolved.rendered_prompt
    assert resolved.fragment_ids == (
        "contract.base",
        profile_id.replace("seminar-", "track.seminar-").replace("core-", "level.core-"),
    )


def test_resolution_is_identical_across_clean_repository_roots(tmp_path: Path) -> None:
    first = _copy_contract_repo(tmp_path / "first")
    second = _copy_contract_repo(tmp_path / "second")

    assert _resolve_core(first).to_record() == _resolve_core(second).to_record()


def test_profile_rejects_raw_prompt_text(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    profiles = _load_yaml(repo_root, PROFILES)
    profiles["profiles"]["core"]["prompt_text"] = "bypass the registry"
    _write_yaml(repo_root, PROFILES, profiles)

    with pytest.raises(contracts.PromptContractError, match="Additional properties"):
        contracts.load_profiles(repo_root=repo_root)


def test_input_schema_rejects_undeclared_context_values() -> None:
    context = {**CORE_CONTEXT, "raw_prompt": "bypass"}

    with pytest.raises(contracts.PromptContractError, match="prompt input failed schema"):
        contracts.resolve_profile("core", context=context, repo_root=REPO_ROOT)


def test_schema_without_identity_fails_closed(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    schema_path = repo_root / INPUT_SCHEMA
    schema_path.write_text(
        schema_path.read_text(encoding="utf-8").replace(
            '  "$id": "curriculum-lifecycle-input.v1",\n',
            "",
        ),
        encoding="utf-8",
    )

    with pytest.raises(contracts.PromptContractError, match=r"must declare a non-empty \$id"):
        _resolve_core(repo_root)


def test_output_schema_accepts_typed_payload_and_rejects_unknown_fields() -> None:
    resolved = _resolve_core()
    valid = {
        "status": "ready",
        "findings": [],
        "next_action": "certify",
        "evidence_identity": CORE_CONTEXT["evidence_identity"],
    }
    contracts.validate_output(resolved, valid, repo_root=REPO_ROOT)

    with pytest.raises(contracts.PromptContractError, match="prompt output failed schema"):
        contracts.validate_output(resolved, {**valid, "commentary": "not declared"}, repo_root=REPO_ROOT)


def test_missing_fragment_fails_closed(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    manifest = _load_yaml(repo_root, MANIFEST)
    manifest["fragments"]["contract.base"]["path"] = "agents_extensions/shared/missing.md"
    _write_yaml(repo_root, MANIFEST, manifest)

    with pytest.raises(contracts.PromptContractError, match="required prompt contract file is missing"):
        _resolve_core(repo_root)


def test_prompt_fragment_outside_canonical_source_fails_closed(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    bypass = repo_root / "docs/prompts/bypass.md"
    bypass.parent.mkdir(parents=True)
    bypass.write_text("# Unregistered authority\n", encoding="utf-8")
    manifest = _load_yaml(repo_root, MANIFEST)
    manifest["fragments"]["contract.base"]["path"] = "docs/prompts/bypass.md"
    _write_yaml(repo_root, MANIFEST, manifest)

    with pytest.raises(contracts.PromptContractError, match="must live under agents_extensions/shared"):
        _resolve_core(repo_root)


def test_include_cycle_fails_closed(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    manifest = _load_yaml(repo_root, MANIFEST)
    manifest["fragments"]["contract.base"]["includes"] = ["family.core"]
    _write_yaml(repo_root, MANIFEST, manifest)

    with pytest.raises(contracts.PromptContractError, match="prompt include cycle"):
        _resolve_core(repo_root)


def test_duplicate_inclusion_fails_closed(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    manifest = _load_yaml(repo_root, MANIFEST)
    manifest["variants"]["core"]["roots"] = ["family.core", "contract.base"]
    _write_yaml(repo_root, MANIFEST, manifest)

    with pytest.raises(contracts.PromptContractError, match="duplicate fragment inclusion"):
        _resolve_core(repo_root)


def test_conflicting_sections_fail_closed(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    manifest = _load_yaml(repo_root, MANIFEST)
    manifest["fragments"]["contract.base"]["section"] = "family-policy"
    _write_yaml(repo_root, MANIFEST, manifest)

    with pytest.raises(contracts.PromptContractError, match="conflicting prompt section"):
        _resolve_core(repo_root)


@pytest.mark.parametrize("extra_text", ["\n{{secret}}\n", "\n{{broken-name}}\n"])
def test_undeclared_or_malformed_placeholders_fail_closed(tmp_path: Path, extra_text: str) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    fragment = repo_root / COMMON_FRAGMENT
    fragment.write_text(fragment.read_text(encoding="utf-8").rstrip("\n") + extra_text, encoding="utf-8")

    with pytest.raises(
        contracts.PromptContractError,
        match=r"undeclared input placeholders|unresolved or malformed placeholder",
    ):
        _resolve_core(repo_root)


def test_resolved_record_detects_rendered_prompt_tampering() -> None:
    record = _resolve_core().to_record()
    record["rendered_prompt"] += "tampered\n"

    with pytest.raises(contracts.PromptContractError, match="does not match current exact contract bytes"):
        contracts.verify_record(record, repo_root=REPO_ROOT)


def test_policy_bytes_change_identity_without_changing_rendered_prompt(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    before = _resolve_core(repo_root)
    policy = repo_root / "agents_extensions/shared/rules/workflow.md"
    policy.write_text(policy.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    after = _resolve_core(repo_root)

    assert after.rendered_prompt == before.rendered_prompt
    assert after.prompt_sha256 == before.prompt_sha256
    assert after.identity_sha256 != before.identity_sha256


def test_explicit_historical_version_survives_current_version_change(tmp_path: Path) -> None:
    repo_root = _copy_contract_repo(tmp_path / "repo")
    baseline = contracts.resolve_prompt(
        "curriculum-lifecycle.module",
        version="1.0.0",
        variant="core",
        context=CORE_CONTEXT,
        repo_root=repo_root,
    )
    v2_path = MANIFEST.with_name("curriculum-lifecycle.module.v2.yaml")
    v2 = _load_yaml(repo_root, MANIFEST)
    v2["version"] = "1.1.0"
    _write_yaml(repo_root, v2_path, v2)
    registry = _load_yaml(repo_root, REGISTRY)
    prompt = registry["prompts"]["curriculum-lifecycle.module"]
    prompt["current"] = "1.1.0"
    prompt["versions"]["1.1.0"] = v2_path.as_posix()
    _write_yaml(repo_root, REGISTRY, registry)

    historical = contracts.resolve_prompt(
        "curriculum-lifecycle.module",
        version="1.0.0",
        variant="core",
        context=CORE_CONTEXT,
        repo_root=repo_root,
    )
    current = contracts.resolve_prompt(
        "curriculum-lifecycle.module",
        variant="core",
        context=CORE_CONTEXT,
        repo_root=repo_root,
    )

    assert historical.rendered_prompt == baseline.rendered_prompt
    assert historical.prompt_sha256 == baseline.prompt_sha256
    assert historical.version == "1.0.0"
    assert current.version == "1.1.0"
    assert current.identity_sha256 != historical.identity_sha256
