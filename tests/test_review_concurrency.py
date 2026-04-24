"""Tests for per-dimension review concurrency resolution.

Before the cap was added, v6_build.py dispatched all 9 review dims
simultaneously, hammering the reviewer provider. `resolve_review_concurrency`
is the pinch point that decides the actual ThreadPoolExecutor width.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.v6_build import (
    REVIEW_DIMENSION_CONCURRENCY_DEFAULT,
    REVIEW_DIMENSIONS,
    resolve_review_concurrency,
)


def test_default_when_no_cli_and_no_env() -> None:
    assert resolve_review_concurrency(None, env_value="") == REVIEW_DIMENSION_CONCURRENCY_DEFAULT


def test_env_var_takes_effect_when_cli_is_none() -> None:
    assert resolve_review_concurrency(None, env_value="5") == 5


def test_cli_overrides_env_var() -> None:
    assert resolve_review_concurrency(2, env_value="9") == 2


def test_cli_value_is_clamped_below_one_to_one() -> None:
    assert resolve_review_concurrency(0) == 1
    assert resolve_review_concurrency(-7) == 1


def test_cli_value_is_clamped_to_num_dimensions() -> None:
    max_dims = len(REVIEW_DIMENSIONS)
    assert resolve_review_concurrency(max_dims + 1) == max_dims
    assert resolve_review_concurrency(10_000) == max_dims


def test_invalid_env_value_falls_back_to_default() -> None:
    assert resolve_review_concurrency(None, env_value="not-a-number") == (
        REVIEW_DIMENSION_CONCURRENCY_DEFAULT
    )


def test_custom_num_dimensions_is_respected() -> None:
    # With only 4 dims, concurrency can't exceed 4 no matter what was requested.
    assert resolve_review_concurrency(20, num_dimensions=4) == 4
    assert resolve_review_concurrency(2, num_dimensions=4) == 2


def test_env_value_zero_is_clamped_up_to_one() -> None:
    assert resolve_review_concurrency(None, env_value="0") == 1


def test_effective_concurrency_cannot_exceed_dim_count() -> None:
    # The guarantee that matters for the ThreadPoolExecutor:
    # max_workers must not exceed len(REVIEW_DIMENSIONS) even under
    # pathological inputs.
    assert resolve_review_concurrency(1000) <= len(REVIEW_DIMENSIONS)
    assert resolve_review_concurrency(None, env_value="1000") <= len(REVIEW_DIMENSIONS)
