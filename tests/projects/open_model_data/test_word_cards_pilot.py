"""W1b runner regressions; real frozen inputs plus the existing synthetic Atlas world."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.atlas import allocate_pilot_identities as allocator
from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_foundation as foundation
from scripts.common.scratch import ensure_scratch_root
from scripts.projects.open_model_data.word_cards import rehearsal
from tests.test_word_card_assembly import SYNTHETIC_ALLOCATION_DIGEST, build_world, make_inputs


@pytest.fixture
def frozen():
    return (
        foundation.load(rehearsal.ROOT / "registry/atlas/pilot/pilot-v1.json"),
        foundation.load(rehearsal.ROOT / "registry/atlas/identity/registry.json"),
    )


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    world = build_world()
    world.units[0]["categories"].append("withdrawal_rehearsal_candidate")
    monkeypatch.setattr(allocator, "ASSEMBLY_ALLOCATION_DIGEST", SYNTHETIC_ALLOCATION_DIGEST)
    inputs = make_inputs(world, tmp_path)
    inputs.hashes["frozen_rows_verified"] = 12
    monkeypatch.setattr(rehearsal, "MANIFEST_SHA256", foundation.digest(inputs.manifest))
    monkeypatch.setattr(rehearsal, "REGISTRY_SHA256", foundation.digest(inputs.registry))
    monkeypatch.setattr(rehearsal, "DENOMINATOR", {"cards": 9, "locators": 83, "source_rows": 12})
    try:
        yield inputs
    finally:
        world.sources.close()
        world.vesum.close()
        world.raw.close()


def test_committed_w1a_inputs_have_fixed_pins_and_inventory(frozen):
    manifest, registry = frozen
    rehearsal.check_frozen_inputs(manifest, registry)
    entries, _ = assembly.pilot_allocation(manifest, registry)
    assert len(entries) == 150
    assert len({entry["card_id"] for entry in entries.values()}) == 150
    assert len(manifest["selection"]["source_records"]) == 272
    assert rehearsal.DENOMINATOR == {"cards": 150, "locators": 3163, "source_rows": 272}
    assert rehearsal.W1A_SHA == "c5d5909282c98dbb04fc8e71c7c59a7167b2ae2c"


@pytest.mark.parametrize("damage", ["selection", "rehash", "card_id", "record_id", "snapshot"])
def test_frozen_input_tampering_refuses(frozen, damage):
    manifest, registry = copy.deepcopy(frozen)
    if damage in {"selection", "rehash"}:
        manifest["selection"]["units"].pop()
        if damage == "rehash":
            manifest["selection_content_sha256"] = foundation.digest(manifest["selection"])
            manifest["manifest_sha256"] = foundation.digest({
                k: v for k, v in manifest.items() if k != "manifest_sha256"})
    elif damage == "card_id":
        first, second = registry["entries"][:2]
        first["card_id"], second["card_id"] = second["card_id"], first["card_id"]
    elif damage == "record_id":
        first, second = registry["source_records"][:2]
        first["source_record_id"], second["source_record_id"] = second["source_record_id"], first["source_record_id"]
    else:
        registry["source_records"][0]["correspondence"][0]["snapshot_id"] = "foreign-snapshot"
    with pytest.raises(foundation.Refusal, match="differs from frozen W1a baseline"):
        rehearsal.check_frozen_inputs(manifest, registry)


def test_runner_verifies_locators_identities_and_all_withdrawals_deterministically(synthetic):
    before = foundation.digest([synthetic.manifest, synthetic.registry])
    first = rehearsal.run_rehearsal(synthetic)
    second = rehearsal.run_rehearsal(synthetic)
    assert first == second
    assert first["passed"] is True
    assert first["observed"] == {"cards": 9, "locators": 83, "source_rows": 12}
    assert first["verification"]["locators"] == {"passed": True, "checked": 83, "errors": {}}
    assert first["verification"]["identity_binding"]["passed"] is True
    assert first["verification"]["source_records"]["passed"] is True
    assert first["verification"]["determinism"]["passed"] is True
    assert set(first["withdrawal"]["scenarios"]) == {
        "source_record", "source", "overlap_source_then_record", "overlap_record_then_source",
        "content_stress_set", "content_paradigm_slot", "assertion_id_fallback",
    }
    assert all(s["assertions_suppressed"] > 0 and s["withdrawn_build_verifies"]
               and s["rebuild_with_selectors_identical"] and s["lifted_selector_restores_baseline"]
               for s in first["withdrawal"]["scenarios"].values())
    assert foundation.digest([synthetic.manifest, synthetic.registry]) == before


@pytest.mark.parametrize("damage", [
    "locator", "identity", "source_binding", "nondeterministic", "assertion_count", "card_count", "source_row_count",
])
def test_bad_baseline_never_runs_withdrawals(synthetic, monkeypatch, damage):
    real_build = assembly.build
    calls = 0

    def damaged_build(inputs):
        nonlocal calls
        calls += 1
        result = real_build(inputs)
        result["cards"] = copy.deepcopy(result["cards"])
        card = next(iter(result["cards"].values()))
        if damage == "locator":
            card["assertions"][0]["locator"] = "ulif:entry:999999#missing"
        elif damage == "identity":
            card["key_at_creation"]["spelling"] = "foreign"
        elif damage == "source_binding":
            assertion = next(a for a in card["assertions"] if a["source_id"] != "vesum")
            assertion["source_record_id"] = "sr_foreign"
        elif damage == "nondeterministic":
            result["build_id"] = f"altered-{calls}"
        elif damage == "assertion_count":
            card["assertions"].pop()
        elif damage == "card_count":
            result["cards"].pop(card["card_id"])
        return result

    def forbidden_withdrawal(_inputs):
        pytest.fail("withdrawal ran after baseline failure")

    if damage == "source_row_count":
        synthetic.hashes["frozen_rows_verified"] = 11
    monkeypatch.setattr(assembly, "build", damaged_build)
    monkeypatch.setattr(rehearsal.verifier, "rehearse", forbidden_withdrawal)
    report = rehearsal.run_rehearsal(synthetic)
    assert report["passed"] is False
    assert report["withdrawal"] == {"passed": False, "reason": "baseline_verification_failed", "scenarios": {}}
    if damage in {"assertion_count", "card_count", "source_row_count"}:
        assert report["denominator_passed"] is False
    else:
        assert report["verification"]["passed"] is False


@pytest.mark.parametrize("damage", ["failed_rollback", "missing_scenario"])
def test_withdrawal_failure_or_incomplete_coverage_cannot_pass(synthetic, monkeypatch, damage):
    real_rehearse = rehearsal.verifier.rehearse

    def damaged_withdrawal(inputs):
        outcome = real_rehearse(inputs)
        if damage == "failed_rollback":
            outcome["passed"] = False
            outcome["scenarios"]["source_record"]["lifted_selector_restores_baseline"] = False
        else:
            outcome["scenarios"].pop("assertion_id_fallback")
        return outcome

    monkeypatch.setattr(rehearsal.verifier, "rehearse", damaged_withdrawal)
    report = rehearsal.run_rehearsal(synthetic)
    assert report["verification"]["passed"] is True
    assert report["passed"] is False
    assert report["scenario_coverage_passed"] is (damage != "missing_scenario")


@pytest.mark.parametrize("invalid", ["manifest", "registry", "json"])
def test_cli_refuses_before_source_reads_and_preserves_receipt(frozen, tmp_path, monkeypatch, capsys, invalid):
    manifest, registry = copy.deepcopy(frozen)
    if invalid == "manifest":
        manifest["selection"]["units"].pop()
    else:
        registry["entries"][0]["card_id"] = "wc_foreign"
    manifest_path, registry_path = tmp_path / "manifest.json", tmp_path / "registry.json"
    manifest_path.write_text("{" if invalid == "json" else json.dumps(manifest), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    receipt = output / "pilot-rehearsal.json"
    receipt.write_bytes(b"retained evidence")

    def forbidden_load(*args, **kwargs):
        pytest.fail("source loading ran before frozen-input refusal")

    monkeypatch.setattr(assembly, "load_inputs", forbidden_load)
    assert rehearsal.main(["--manifest", str(manifest_path), "--registry", str(registry_path),
                           "--output", str(output)]) == 1
    assert capsys.readouterr().err.startswith("REFUSED: ")
    assert receipt.read_bytes() == b"retained evidence"


@pytest.mark.parametrize("failed", [False, True])
def test_cli_writes_receipt_and_returns_check_status(synthetic, tmp_path, monkeypatch, capsys, failed):
    manifest, registry = tmp_path / "manifest.json", tmp_path / "registry.json"
    manifest.write_text(json.dumps(synthetic.manifest), encoding="utf-8")
    registry.write_text(json.dumps(synthetic.registry), encoding="utf-8")
    monkeypatch.setattr(assembly, "load_inputs", lambda *args: synthetic)
    if failed:
        synthetic.hashes["frozen_rows_verified"] = 11
    with tempfile.TemporaryDirectory(dir=ensure_scratch_root()) as directory:
        assert rehearsal.main(["--manifest", str(manifest), "--registry", str(registry),
                               "--sources-db", str(tmp_path / "sources.sqlite"),
                               "--vesum-db", str(tmp_path / "vesum.sqlite"),
                               "--atlas-db", str(tmp_path / "atlas.sqlite"), "--output", directory]) == int(failed)
        report = json.loads(capsys.readouterr().out)
        assert json.loads((Path(directory) / "pilot-rehearsal.json").read_text()) == report
        assert report["passed"] is (not failed)


def test_cli_rejects_tracked_output_before_loading_sources(frozen, monkeypatch, capsys):
    def forbidden_load(*args, **kwargs):
        pytest.fail("sources opened for refused output")

    monkeypatch.setattr(assembly, "load_inputs", forbidden_load)
    assert rehearsal.main(["--output", str(rehearsal.ROOT / "scripts")]) == 1
    assert "Output must be outside the repository or in an ignored tree" in capsys.readouterr().err


@pytest.mark.parametrize("store", ["sources", "vesum", "atlas"])
def test_cli_refuses_relative_database_paths_before_loading(store, monkeypatch, capsys, tmp_path):
    def forbidden_load(*args, **kwargs):
        pytest.fail("sources opened with a relative database path")

    monkeypatch.setattr(assembly, "load_inputs", forbidden_load)
    output = tmp_path / "uncreated-output"
    assert rehearsal.main([f"--{store}-db", "data/relative.sqlite", "--output", str(output)]) == 1
    assert capsys.readouterr().err == "REFUSED: Source database paths must be absolute\n"
    assert not output.exists()


def test_module_help_and_usage_are_executable():
    command = [sys.executable, "-m", "scripts.projects.open_model_data.word_cards.rehearsal"]
    help_result = subprocess.run([*command, "--help"], capture_output=True, text=True, check=False, timeout=60)
    assert help_result.returncode == 0
    assert all(text in help_result.stdout for text in ("--output", "--sources-db", "Outputs:", "Exit codes:"))
    usage = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
    assert usage.returncode == 2
    assert "--output" in usage.stderr
