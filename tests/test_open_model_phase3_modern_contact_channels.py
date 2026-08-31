"""Hostile tests for the #7428 modern Cyrillic-contact metadata freeze."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_modern_contact_channels as channels


def _admission() -> dict[str, object]:
    return json.loads(channels.OUTPUT_PATH.read_text(encoding="utf-8"))


def _rehash(value: dict[str, object]) -> None:
    value["receipt_sha256"] = channels.sha256_bytes(
        channels.canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"})
    )


def test_generated_admission_is_exact_text_free_and_nonadmitting() -> None:
    value = channels.build_contract()
    schema = json.loads(channels.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(value)) == []
    assert value == _admission()
    assert channels.validate_contract(value) == value
    assert channels.main(["--check"]) == 0
    assert [channel["language_identity"] for channel in value["channels"]] == list(channels.MODERN_CLASSES)  # type: ignore[index]
    assert [channel["cell_id"] for channel in value["channels"]] == list(channels.MODERN_CELL_IDS)  # type: ignore[index]
    assert value["status"] == "BLOCKED_PENDING_SOURCE_QUALIFIED_ADJUDICATION"
    assert value["safety_counters"] == {  # type: ignore[index]
        "correction_targets_emitted": 0,
        "dataset_rows_emitted": 0,
        "labels_created": 0,
        "gold_created": 0,
        "provider_requests": 0,
        "training_rows_emitted": 0,
    }
    assert "source_text" not in channels.canonical_bytes(value).decode("utf-8")


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("bindings", "p1", "sha256"), "0" * 64),
        (("bindings", "composite_denominator", "composite_required_cell_count"), 15),
        (("bindings", "composite_denominator", "unknown_rights_blocker_count"), 0),
        (("bindings", "phase3_scope_circularity_firewall", "sha256"), "f" * 64),
    ],
)
def test_validator_rejects_parent_hash_and_denominator_drift(path: tuple[str, ...], replacement: object) -> None:
    value = copy.deepcopy(_admission())
    target: dict[str, object] = value
    for key in path[:-1]:
        target = target[key]  # type: ignore[assignment,index]
    target[path[-1]] = replacement
    _rehash(value)
    with pytest.raises(channels.ModernContactChannelsError):
        channels.validate_contract(value)


def test_build_rejects_parent_artifact_hash_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    original = channels.sha256_file

    def drift(path: Path) -> str:
        if Path(path) == channels.P1_PATH:
            return "0" * 64
        return original(path)

    monkeypatch.setattr(channels, "sha256_file", drift)
    with pytest.raises(channels.ModernContactChannelsError, match=r"phase3_p1_universe_freeze_v1\.json hash drift"):
        channels.build_contract()


def test_build_rejects_seventh_or_lookalike_modern_class(monkeypatch: pytest.MonkeyPatch) -> None:
    original = channels._read_json

    def corrupted(path: Path, label: str) -> dict[str, object]:
        value = original(path, label)
        if Path(path) == channels.P1_PATH:
            value = copy.deepcopy(value)
            value["language_universe"]["modern_contact_classes"].append("russian_cyrillic")  # type: ignore[index]
        return value

    monkeypatch.setattr(channels, "_read_json", corrupted)
    with pytest.raises(channels.ModernContactChannelsError, match="modern language universe drift"):
        channels.build_contract()


@pytest.mark.parametrize(
    ("channel_path", "replacement"),
    [
        (("language_identity",), "russian_cyrillic"),
        (("cell_id",), "modern.russian_cyrillic.unmarked.contact_interference.source_backed_correction"),
        (("source_blocker", "source_unit_identity_sha256"), "a" * 64),
        (("source_blocker", "rights_status"), "granted"),
        (("context_role",), "quotation"),
        (("language_identity_basis",), "script_only"),
        (("script_identity_rule",), "cyrillic_script_is_language_identity"),
        (("adjudication_blocker", "source_qualified_human_record_sha256"), "b" * 64),
        (("adjudication_blocker", "registry_status"), "REGISTERED"),
        (("adjudication_blocker", "model_proposal_may_promote"), True),
        (("status",), "satisfied"),
    ],
)
def test_validator_rejects_language_context_source_and_authority_promotion(
    channel_path: tuple[str, ...], replacement: object
) -> None:
    value = copy.deepcopy(_admission())
    channel = value["channels"][0]  # type: ignore[index]
    target: dict[str, object] = channel
    for key in channel_path[:-1]:
        target = target[key]  # type: ignore[assignment,index]
    target[channel_path[-1]] = replacement
    _rehash(value)
    with pytest.raises(channels.ModernContactChannelsError):
        channels.validate_contract(value)


@pytest.mark.parametrize("counter", ["correction_targets_emitted", "dataset_rows_emitted", "labels_created", "gold_created", "provider_requests", "training_rows_emitted"])
def test_validator_rejects_every_nonzero_output_counter(counter: str) -> None:
    value = copy.deepcopy(_admission())
    value["safety_counters"][counter] = 1  # type: ignore[index]
    _rehash(value)
    with pytest.raises(channels.ModernContactChannelsError):
        channels.validate_contract(value)


def test_validator_rejects_missing_channel_and_rehashed_unknown_fields() -> None:
    missing = copy.deepcopy(_admission())
    missing["channels"] = missing["channels"][:-1]  # type: ignore[index]
    _rehash(missing)
    with pytest.raises(channels.ModernContactChannelsError):
        channels.validate_contract(missing)

    invented = copy.deepcopy(_admission())
    invented["channels"][0]["model_generated_correction_target"] = "opaque"  # type: ignore[index]
    _rehash(invented)
    with pytest.raises(channels.ModernContactChannelsError):
        channels.validate_contract(invented)
