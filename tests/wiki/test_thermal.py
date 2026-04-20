from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki import dense_rerank, thermal


def test_nsprocessinfo_thermal_state_falls_back_to_nominal_on_failure(monkeypatch) -> None:
    def fake_cdll(_path: str):
        raise OSError("missing")

    monkeypatch.setattr(thermal.ctypes, "CDLL", fake_cdll)

    assert thermal.nsprocessinfo_thermal_state() == 0


def test_thermal_controller_promotes_to_warm_after_three_regressed_epochs() -> None:
    controller = dense_rerank._ThermalEpochController(ms_per_token_ewma=10.0)

    for _ in range(2):
        tier, sleep_s = dense_rerank._advance_thermal_epoch(
            controller,
            ms_per_token=12.0,
            thermal_state=0,
        )
        assert tier == "cool"
        assert sleep_s == 0.0

    tier, sleep_s = dense_rerank._advance_thermal_epoch(
        controller,
        ms_per_token=12.0,
        thermal_state=0,
    )

    assert tier == "warm"
    assert sleep_s == 1.5


def test_thermal_controller_promotes_to_hot_on_critical() -> None:
    controller = dense_rerank._ThermalEpochController()

    tier, sleep_s = dense_rerank._advance_thermal_epoch(
        controller,
        ms_per_token=10.0,
        thermal_state=3,
    )

    assert tier == "hot"
    assert sleep_s == 5.0


def test_thermal_controller_demotes_after_five_nominal_epochs() -> None:
    controller = dense_rerank._ThermalEpochController(tier="warm", ms_per_token_ewma=10.0)

    for _ in range(4):
        tier, sleep_s = dense_rerank._advance_thermal_epoch(
            controller,
            ms_per_token=10.0,
            thermal_state=0,
        )
        assert tier == "warm"
        assert sleep_s == 1.5

    tier, sleep_s = dense_rerank._advance_thermal_epoch(
        controller,
        ms_per_token=10.0,
        thermal_state=0,
    )

    assert tier == "cool"
    assert sleep_s == 0.0


def test_thermal_controller_does_not_throttle_on_fair() -> None:
    controller = dense_rerank._ThermalEpochController(ms_per_token_ewma=10.0)

    tier, sleep_s = dense_rerank._advance_thermal_epoch(
        controller,
        ms_per_token=10.0,
        thermal_state=1,
    )

    assert tier == "cool"
    assert sleep_s == 0.0
