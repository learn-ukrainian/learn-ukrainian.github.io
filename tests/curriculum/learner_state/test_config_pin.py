"""Config pin test for immersion policies and vocabulary knees (issue #8414).

Verifies that IMMERSION_POLICIES and _ULP_VOCAB_KNEE_PER_BAND in scripts/config.py
remain byte-identical to the recorded sha256 of their repr.
"""

from __future__ import annotations

import hashlib

import pytest

import scripts.config as cfg

pytestmark = pytest.mark.reads_content

# #10105: approved R1-R12 wrapper; counterpart approval in critic-10105-design.result
# bound to proposal sha256 8b19ff61d94aab699d0431177ec315ed2032f5c7257b52e9258e5e9b8f96832c.
# Author: gpt-6.1-sol/high via codex dispatch; counterpart: claude-opus-5-5/high via claude dispatch.
# Explicit R1-R12 counterpart approval accepted unchanged; design input, not implementation CF.
EXPECTED_IMMERSION_POLICIES_SHA256 = "05cea5f7a232be696d04f05f04fabd43f07b0d4d986fb09199e6d6ce1d1b74eb"
EXPECTED_ULP_VOCAB_KNEE_SHA256 = "d14ee93f068cf98eb76db16294b42b06a888583bf660beadd4580bd04b9a2ab5"


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


def test_use_ulp_immersion_derivation_pinned() -> None:
    """Pin the live derivation toggle in scripts/config.py."""
    assert cfg.USE_ULP_IMMERSION_DERIVATION is True
