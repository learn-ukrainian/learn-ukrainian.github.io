"""Hermetic tests for the Phase 3 private rule-author capture bridge."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_rule_author_packets as packets
from scripts.projects.open_model_data import phase3_rule_author_runner as runner


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")


def _role() -> dict[str, object]:
    return {"seats": [{"role_id": "rule_author_extractor", "assignment_state": "assigned_verified", "controller_identity_id": "controller_author", "controller_identity_attested": True}], "task_bindings": [{"role_id": "rule_author_extractor", "controller_identity_id": "controller_author", "reserved_task_id": "author-task", "status": "identity_attested_pre_artifact"}]}


def _item(number: int) -> dict[str, object]:
    digest = f"{number:x}" * 64
    source_id = f"rule_author_source:{digest}"
    return {"schema_version": "phase3_rule_author_source_item_v1", "source_item_id": source_id, "family_id": "ua_gec", "frozen_unit": {"family_id": "ua_gec", "unit_id": f"unit-{number}", "unit_sha256": "a" * 64}, "source_document_identity": "ua_gec_document:" + "b" * 64, "locator": {"kind": "local", "opaque_locator_sha256": "c" * 64}, "source_span": {"start": 0, "end": 1}, "source_sha256": "d" * 64, "source_text": "x", "corrected_text": "y", "metadata": {"annotation_layer": "F", "partition": "train", "annotator_identity_sha256": "e" * 64, "is_native": 1, "source_lang": "uk"}, "candidate_signals": [], "clearance_sha256": "f" * 64, "near_duplicate_policy_fingerprint_sha256": "0" * 64}


def _packet(number: int) -> dict[str, object]:
    item = _item(number)
    return {"schema_version": "phase3_rule_author_packet_v1", "packet_id": "rule_author_packet:" + f"{number:x}" * 64, "ordinal": number, "clearance_sha256": "f" * 64, "near_duplicate_policy_fingerprint_sha256": "0" * 64, "query_plan_sha256": "1" * 64, "byte_count": 1, "oversize_singleton": False, "items": [item]}


def _paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    bundle_path, role_path = tmp_path / "bundle.json", tmp_path / "role.json"
    _write(role_path, _role())
    bundle = {"schema_version": "phase3_rule_author_packet_bundle_v1", "bundle_id": "rule_author_bundle:" + "2" * 64, "clearance": {"receipt_sha256": "3" * 64, "file_sha256": "4" * 64}, "source_freeze": {"receipt_sha256": "5" * 64, "merged_main_sha": "6" * 40}, "evaluation_contract_sha256": "7" * 64, "coverage_contract_sha256": "8" * 64, "role_contract_sha256": runner.sha256_file(role_path), "near_duplicate_policy_fingerprint_sha256": "0" * 64, "compiler": {"implementation_version": "phase3_rule_author_packet_compiler_v1", "script_sha256": runner.sha256_file(runner.ROOT / packets.SCRIPT_PATH), "query_plan_sha256": packets._query_plan_sha256(), "max_items": 24, "max_utf8_bytes": 196608}, "packets": [_packet(1), _packet(2)]}
    _write(bundle_path, bundle)
    return bundle_path, role_path, tmp_path / "private", tmp_path / "receipt.json"


def _output(entry: dict[str, object], valid: bool = True) -> bytes:
    if not valid:
        return b"not-json"
    item_id = "rule_author_source:" + ("1" if entry["ordinal"] == 1 else "2") * 64
    proposal = {"proposal_id": "p", "source_item_id": item_id, "source_span": {"start": 0, "end": 1}, "primary_source_role": "correction", "secondary_source_roles": [], "claim_type": "candidate", "phenomenon": "fixture", "mechanism": "literal", "matcher": {"kind": "literal", "pattern": "x", "abstention": ["none"]}, "incorrect_pattern": "x", "replacements": ["y"], "scope": "attached", "exceptions": [], "controls": [], "protections": [], "abstentions": [], "evidence_refs": [item_id], "consumer_views": [], "dissent_or_alternatives": []}
    return json.dumps({"proposals": [proposal], "abstentions": [], "limitations": [], "parse_state": "parsed"}, separators=(",", ":")).encode()


def _executor(valid: bool = True):
    def invoke(command: list[str], stdin: bytes) -> None:
        assert stdin.startswith(b"You are the assigned Phase 3 rule-author extractor")
        output = Path(command[command.index("--output-path") + 1])
        ordinal = int(output.stem)
        output.write_bytes(_output({"ordinal": ordinal}, valid))
    return invoke


def test_prepare_and_full_capture_are_private_and_schema_valid(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)
    manifest = runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    assert len(manifest["packets"]) == 2
    result = runner.run(bundle_path=bundle, role_path=role, private_dir=private, receipt_path=receipt, exact_model="gemini-3.6-flash-high", executor=_executor())
    assert result["complete"] is True and result["no_leakage"] is True
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    Draft202012Validator.check_schema(json.loads(runner.SCHEMA_PATH.read_text()))
    assert runner.verify(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")["ok"] is True


def test_malformed_output_is_unparsed_not_a_proposal(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)
    result = runner.run(bundle_path=bundle, role_path=role, private_dir=private, receipt_path=receipt, exact_model="gemini-3.6-flash-high", max_packets=1, executor=_executor(False))
    assert result["unparsed_count"] == 1 and result["proposal_count"] == 0 and result["complete"] is False


def test_tampered_attachment_rejects_resume(tmp_path: Path) -> None:
    bundle, role, private, _ = _paths(tmp_path)
    manifest = runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    (private / manifest["packets"][0]["attachment"]).write_text("{}", encoding="utf-8")
    os.chmod(private / manifest["packets"][0]["attachment"], 0o600)
    with pytest.raises(runner.RuleAuthorRunnerError, match="attachment hash drift"):
        runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")


def test_resume_reuses_exact_prepared_files(tmp_path: Path) -> None:
    bundle, role, private, _ = _paths(tmp_path)
    first = runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    assert runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high") == first


def test_verify_rejects_a_prepared_only_or_partial_run(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)
    runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    with pytest.raises(runner.RuleAuthorRunnerError, match="incomplete"):
        runner.verify(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=receipt,
        exact_model="gemini-3.6-flash-high",
        max_packets=1,
        executor=_executor(),
    )
    with pytest.raises(runner.RuleAuthorRunnerError, match="incomplete"):
        runner.verify(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")


def test_permissions_symlink_and_aliases_fail_closed(tmp_path: Path) -> None:
    bundle, role, private, _ = _paths(tmp_path)
    manifest = runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    os.chmod(private / manifest["packets"][0]["prompt"], 0o400)
    with pytest.raises(runner.RuleAuthorRunnerError, match="0600"):
        runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    os.chmod(private / manifest["packets"][0]["prompt"], 0o600)
    os.symlink(private / "manifest.json", private / "evil")
    with pytest.raises(runner.RuleAuthorRunnerError, match="symlink"):
        runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    alias = tmp_path / "alias"
    os.symlink(private, alias)
    with pytest.raises(runner.RuleAuthorRunnerError, match="symlink"):
        runner.prepare(bundle_path=bundle, role_path=role, private_dir=alias, exact_model="gemini-3.6-flash-high")


def test_symlinked_ancestor_canonicalizes_but_leaf_symlink_is_rejected(tmp_path: Path) -> None:
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked"
    os.symlink(real_parent, linked_parent)
    bundle, role, private, _ = _paths(linked_parent)
    manifest = runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    assert (real_parent / "private" / "manifest.json").exists() and manifest["author"]["task_id"] == "author-task"
    leaf_alias = linked_parent / "bundle-leaf-alias.json"
    os.symlink(bundle, leaf_alias)
    with pytest.raises(runner.RuleAuthorRunnerError, match="symlink"):
        runner.prepare(bundle_path=leaf_alias, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")


def test_role_binding_drift_rejects_resume(tmp_path: Path) -> None:
    bundle, role, private, _ = _paths(tmp_path)
    runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    changed = _role()
    changed["task_bindings"][0]["reserved_task_id"] = "other-task"  # type: ignore[index]
    _write(role, changed)
    with pytest.raises(runner.RuleAuthorRunnerError, match="role-contract binding"):
        runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")


def test_canary_never_claims_full_completion_then_full_union_can(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)
    canary = runner.run(bundle_path=bundle, role_path=role, private_dir=private, receipt_path=receipt, exact_model="gemini-3.6-flash-high", max_packets=1, executor=_executor())
    assert canary["canary"] is True and canary["complete"] is False
    full = runner.run(bundle_path=bundle, role_path=role, private_dir=private, receipt_path=receipt, exact_model="gemini-3.6-flash-high", executor=_executor())
    assert full["canary"] is False and full["complete"] is True and full["attempted_count"] == 2


def test_full_then_canary_rerun_preserves_completed_receipt(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)
    full = runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=receipt,
        exact_model="gemini-3.6-flash-high",
        executor=_executor(),
    )
    rerun = runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=receipt,
        exact_model="gemini-3.6-flash-high",
        max_packets=1,
        executor=_executor(),
    )
    assert rerun["complete"] is True and rerun["canary"] is False
    assert {key: rerun[key] for key in ("attempted_count", "parsed_count", "unparsed_count", "failed_count")} == {
        key: full[key] for key in ("attempted_count", "parsed_count", "unparsed_count", "failed_count")
    }


def test_command_is_only_the_fixed_agy_bridge_shape(tmp_path: Path) -> None:
    bundle, role, private, _ = _paths(tmp_path)
    manifest = runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    command = runner.command_for(manifest["packets"][0], manifest, private)
    assert command[1:4] == [str(runner.ROOT / "scripts/ai_agent_bridge/__main__.py"), "ask-agy", "-"]
    assert "--review" not in command and "--task-id" in command and "--to-model" in command and "--data" in command and "--output-path" in command
    assert str(private / manifest["packets"][0]["prompt"]) not in command
    prompt = (private / manifest["packets"][0]["prompt"]).read_text(encoding="utf-8")
    assert "matcher.kind must equal the proposal's mechanism value" in prompt and "both literal" in prompt


def test_cross_packet_source_is_rejected(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)

    def cross_packet(command: list[str], stdin: bytes) -> None:
        del stdin
        output = Path(command[command.index("--output-path") + 1])
        output.write_bytes(_output({"ordinal": 2}))

    result = runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=receipt,
        exact_model="gemini-3.6-flash-high",
        max_packets=1,
        executor=cross_packet,
    )
    assert result["unparsed_count"] == 1 and result["proposal_count"] == 0


def test_tampered_resume_and_unexpected_file_fail_closed(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)
    runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=receipt,
        exact_model="gemini-3.6-flash-high",
        max_packets=1,
        executor=_executor(),
    )
    raw = private / "raw/1.raw"
    raw.write_bytes(b"tampered")
    os.chmod(raw, 0o600)
    with pytest.raises(runner.RuleAuthorRunnerError, match="resume record"):
        runner.run(
            bundle_path=bundle,
            role_path=role,
            private_dir=private,
            receipt_path=receipt,
            exact_model="gemini-3.6-flash-high",
            max_packets=1,
            executor=_executor(),
        )
    other_bundle, other_role, other_private, _ = _paths(tmp_path / "other")
    other_private.mkdir(mode=0o700)
    (other_private / "unexpected").write_text("x", encoding="utf-8")
    os.chmod(other_private / "unexpected", 0o600)
    with pytest.raises(runner.RuleAuthorRunnerError, match="unexpected"):
        runner.prepare(
            bundle_path=other_bundle,
            role_path=other_role,
            private_dir=other_private,
            exact_model="gemini-3.6-flash-high",
        )


def test_receipt_is_public_safe_and_execution_aliases_fail(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)
    result = runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=receipt,
        exact_model="gemini-3.6-flash-high",
        max_packets=1,
        executor=_executor(),
    )
    forbidden = {"packet_id", "source_item_id", "locator", "fingerprint", "source_text", "corrected_text", "raw_response", "response"}

    def all_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | set().union(*(all_keys(child) for child in value.values()))
        if isinstance(value, list):
            return set().union(*(all_keys(child) for child in value))
        return set()

    assert result["no_leakage"] is True and not (all_keys(result) & forbidden)
    second_bundle, second_role, second_private, second_receipt = _paths(tmp_path / "alias")

    def aliased_output(command: list[str], stdin: bytes) -> None:
        del stdin
        output = Path(command[command.index("--output-path") + 1])
        target = output.parent / "target"
        target.write_bytes(b"{}")
        os.symlink(target, output)

    with pytest.raises(runner.RuleAuthorRunnerError, match="aliased"):
        runner.run(
            bundle_path=second_bundle,
            role_path=second_role,
            private_dir=second_private,
            receipt_path=second_receipt,
            exact_model="gemini-3.6-flash-high",
            max_packets=1,
            executor=aliased_output,
        )


def test_execution_error_and_bundle_alias_fail_closed(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)

    def unavailable(command: list[str], stdin: bytes) -> None:
        del command, stdin
        raise OSError("bridge unavailable")

    result = runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=receipt,
        exact_model="gemini-3.6-flash-high",
        executor=unavailable,
    )
    assert result["failed_count"] == 2 and result["unparsed_count"] == 2
    assert result["complete"] is False and result["canary"] is False
    record_path = private / "records/1.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["execution_error"] = "edited-after-capture"
    record_path.write_text(json.dumps(record, separators=(",", ":")) + "\n", encoding="utf-8")
    os.chmod(record_path, 0o600)
    with pytest.raises(runner.RuleAuthorRunnerError, match="self-integrity"):
        runner.verify(bundle_path=bundle, role_path=role, private_dir=private, exact_model="gemini-3.6-flash-high")
    alias = tmp_path / "bundle-alias.json"
    os.symlink(bundle, alias)
    with pytest.raises(runner.RuleAuthorRunnerError, match="symlink"):
        runner.prepare(bundle_path=alias, role_path=role, private_dir=tmp_path / "other-private", exact_model="gemini-3.6-flash-high")


def test_valid_json_before_nonzero_exit_cannot_complete_or_succeed_canary(tmp_path: Path) -> None:
    bundle, role, private, receipt = _paths(tmp_path)

    class NonzeroResult:
        returncode = 7

    def writes_valid_then_fails(command: list[str], stdin: bytes) -> NonzeroResult:
        del stdin
        output = Path(command[command.index("--output-path") + 1])
        output.write_bytes(_output({"ordinal": int(output.stem)}))
        return NonzeroResult()

    result = runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=receipt,
        exact_model="gemini-3.6-flash-high",
        executor=writes_valid_then_fails,
    )
    assert result["parsed_count"] == 2 and result["failed_count"] == 2
    assert result["complete"] is False and result["canary_succeeded"] is False


def test_exact_model_must_be_the_catalog_canonical_agy_gemini_model(tmp_path: Path) -> None:
    bundle, role, private, _ = _paths(tmp_path)
    with pytest.raises(runner.RuleAuthorRunnerError, match="canonical AGY Gemini"):
        runner.prepare(bundle_path=bundle, role_path=role, private_dir=private, exact_model="claude-test")


def test_receipt_cannot_overwrite_inputs_or_private_files(tmp_path: Path) -> None:
    bundle, role, private, _ = _paths(tmp_path)
    with pytest.raises(runner.RuleAuthorRunnerError, match="protected"):
        runner.run(
            bundle_path=bundle,
            role_path=role,
            private_dir=private,
            receipt_path=bundle,
            exact_model="gemini-3.6-flash-high",
            max_packets=1,
            executor=_executor(),
        )
    with pytest.raises(runner.RuleAuthorRunnerError, match="outside"):
        runner.run(
            bundle_path=bundle,
            role_path=role,
            private_dir=private,
            receipt_path=private / "receipt.json",
            exact_model="gemini-3.6-flash-high",
            max_packets=1,
            executor=_executor(),
        )


def test_public_receipt_does_not_chmod_its_existing_parent(tmp_path: Path) -> None:
    bundle, role, private, _ = _paths(tmp_path)
    destination = tmp_path / "public"
    destination.mkdir(mode=0o700)
    os.chmod(destination, 0o700)
    runner.run(
        bundle_path=bundle,
        role_path=role,
        private_dir=private,
        receipt_path=destination / "receipt.json",
        exact_model="gemini-3.6-flash-high",
        max_packets=1,
        executor=_executor(),
    )
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    assert stat.S_IMODE((destination / "receipt.json").stat().st_mode) == 0o600
