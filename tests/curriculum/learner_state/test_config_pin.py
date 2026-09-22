"""Config pin test for immersion policies and vocabulary knees (issue #8414).

Verifies that IMMERSION_POLICIES and _ULP_VOCAB_KNEE_PER_BAND in scripts/config.py
remain byte-identical to the recorded sha256 of their repr.
"""

from __future__ import annotations

import hashlib

import pytest

import scripts.config as cfg

pytestmark = pytest.mark.reads_content

# Recorded on 2026-09-22
EXPECTED_IMMERSION_POLICIES_SHA256 = "c6f88ca92d60bc7dd2d8cdca047f7c5841132a17edf3dfd7d133eb3ad3d96152"
EXPECTED_ULP_VOCAB_KNEE_SHA256 = "d16470e56cc19064de60b8ade1dfe6569018d3ebe8d2576ad838601539d3bd0b"


def test_immersion_policies_pinned_hash() -> None:
    actual = hashlib.sha256(repr(cfg.IMMERSION_POLICIES).encode("utf-8")).hexdigest()
    assert actual == EXPECTED_IMMERSION_POLICIES_SHA256, (
        f"IMMERSION_POLICIES in scripts/config.py changed! Expected sha256 {EXPECTED_IMMERSION_POLICIES_SHA256}, got {actual}"
    )


def test_ulp_vocab_knees_pinned_hash() -> None:
    actual = hashlib.sha256(repr(cfg._ULP_VOCAB_KNEE_PER_BAND).encode("utf-8")).hexdigest()
    assert actual == EXPECTED_ULP_VOCAB_KNEE_SHA256, (
        f"_ULP_VOCAB_KNEE_PER_BAND in scripts/config.py changed! Expected sha256 {EXPECTED_ULP_VOCAB_KNEE_SHA256}, got {actual}"
    )
