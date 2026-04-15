"""Tests for shared immersion source of truth across config, pipeline, and audit."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.config import (
    get_a1_immersion_range,
    get_a2_immersion_range,
    get_b1_immersion_range,
)
from config import get_immersion_range, get_immersion_rule
from pipeline.config_tables import IMMERSION_RULES


def test_audit_ranges_delegate_to_shared_config():
    assert get_a1_immersion_range(1) == get_immersion_range("a1", 1)
    assert get_a1_immersion_range(35) == get_immersion_range("a1", 35)
    assert get_a2_immersion_range(4) == get_immersion_range("a2", 4)
    assert get_a2_immersion_range(51) == get_immersion_range("a2", 51)
    assert get_b1_immersion_range(3) == get_immersion_range("b1", 3)
    assert get_b1_immersion_range(10) == get_immersion_range("b1", 10)


def test_pipeline_rule_map_is_derived_from_shared_config():
    assert IMMERSION_RULES["a2-bridge"] == get_immersion_rule("a2", 1)
    assert IMMERSION_RULES["a2-m21-50"] == get_immersion_rule("a2", 30)
    assert IMMERSION_RULES["b1-m01-05"] == get_immersion_rule("b1", 3)
    assert IMMERSION_RULES["b1-core"] == get_immersion_rule("b1", 10)


def test_b1_early_and_core_rules_differ():
    early = get_immersion_rule("b1", 3)
    core = get_immersion_rule("b1", 10)

    assert "TARGET: 75-100% Ukrainian." in early
    assert "TARGET: 85-100% Ukrainian." in core
    assert early != core
