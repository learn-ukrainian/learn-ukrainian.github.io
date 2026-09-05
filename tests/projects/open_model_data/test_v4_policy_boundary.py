"""Fixed policy is checked at real stage entrypoints, not by field equality."""

from __future__ import annotations

import importlib
import inspect
import json

import pytest
from learn_ukrainian_v4_runtime import resources
from learn_ukrainian_v4_runtime import v4_a7_private_ledger as ledger
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused

STAGES = [
    "a7_original_row_factory",
    "a8_admission_assembly",
    "a9_evaluation_package",
    "a10_pilot_review_gate",
    "a11_silver_release_gate",
    "a12_gold_overlay_gate",
    "a13_cleanup_recovery",
]


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("mutation", ["stale_top", "stale_completion", "missing_top"])
def test_stage_entrypoint_refuses_stale_or_missing_active_policy(stage, mutation):
    from learn_ukrainian_v4_runtime import v4_trust_authority as trust

    module = importlib.import_module("learn_ukrainian_v4_runtime.v4_" + stage)
    name = "data/projects/open_model_data/admission/dataset_v4_" + stage + "_receipt_v1.json"
    receipt = json.loads(resources.read_bytes(name))
    active = trust.load_production_trust_policy()[1]
    receipt["trust_policy_sha256"] = active if mutation == "stale_completion" else "f" * 64
    if mutation != "stale_top":
        receipt[stage.split("_", 1)[0] + "_completions"] = [{"trust_policy_sha256": "f" * 64}]
    if mutation == "missing_top":
        receipt.pop("trust_policy_sha256")
    with pytest.raises(ValueError, match="policy is not active"):
        module.validate_receipt_independently(receipt)


def test_admission_default_off_precedes_any_private_input_read(monkeypatch):
    monkeypatch.delenv("HRAMATKA_V4_ADMISSION_ENABLED", raising=False)
    arguments = {name: None for name in inspect.signature(ledger.construct_completion).parameters}
    with pytest.raises(OperationRefused, match="admission_disabled"):
        ledger.construct_completion(**arguments)
