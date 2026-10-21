from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

pytestmark = [pytest.mark.docs_skills, pytest.mark.reads_content]

from scripts.orchestration import prompt_contracts as contracts

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("agents_extensions/shared/prompt-contracts/manifests/curriculum-lifecycle.module.v1.yaml")
REGISTRY = Path("agents_extensions/shared/prompt-contracts/registry.v1.yaml")
CORE_CONTEXT = {
    "track": "a1",
    "slug": "introductions",
    "family": "core",
    "phase": "build",
    "module_state": "unbuilt",
    "evidence_identity": "a" * 64,
}


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


def test_resolution_is_identical_across_clean_repository_roots(tmp_path: Path) -> None:
    first = _copy_contract_repo(tmp_path / "first")
    second = _copy_contract_repo(tmp_path / "second")

    assert _resolve_core(first).to_record() == _resolve_core(second).to_record()


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
