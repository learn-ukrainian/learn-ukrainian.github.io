"""Regression test for the agy bridge model-selection bug.

`ask-agy --to-model "Gemini 3.1 Pro (High)"` silently ran flash because
`_extract_target_model` queried a `to_model` COLUMN that never existed in the
`messages` schema. `send_message` stores `to_model` inside the `data` JSON blob,
so the read must come from there (ported from kubedojo's fixed bridge).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ai_agent_bridge._agy import _extract_target_model


def test_pro_slug_round_trips_from_data_blob():
    msg = {"id": 1, "data": json.dumps({"to_model": "gemini-3.1-pro-high"})}
    assert _extract_target_model(msg) == "gemini-3.1-pro-high"


def test_display_label_round_trips():
    msg = {"id": 2, "data": json.dumps({"to_model": "Gemini 3.1 Pro (High)"})}
    assert _extract_target_model(msg) == "Gemini 3.1 Pro (High)"


def test_data_with_other_keys_but_no_to_model_returns_none():
    msg = {"id": 3, "data": json.dumps({"from_model": "claude"})}
    assert _extract_target_model(msg) is None


def test_missing_or_empty_data_returns_none():
    assert _extract_target_model({"id": 4, "data": None}) is None
    assert _extract_target_model({"id": 5, "data": ""}) is None
    assert _extract_target_model({"id": 6}) is None


def test_malformed_json_returns_none_not_raise():
    assert _extract_target_model({"id": 7, "data": "{not json"}) is None


def test_empty_to_model_value_returns_none():
    msg = {"id": 8, "data": json.dumps({"to_model": ""})}
    assert _extract_target_model(msg) is None
