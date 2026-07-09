"""Contract-sync pin tests for the active V7 prompt surfaces."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = REPO_ROOT / "scripts" / "build" / "contracts" / "module-contract.md"
CONTRACT_RELATIVE_PATH = "scripts/build/contracts/module-contract.md"
WRITER_PROMPTS = (
    REPO_ROOT / "scripts" / "build" / "phases" / "linear-write.md",
    REPO_ROOT / "scripts" / "build" / "phases" / "linear-write-grok.md",
)
REVIEWER_PROMPT = REPO_ROOT / "scripts" / "build" / "phases" / "linear-review-dim.md"


def test_shared_contract_document_exists() -> None:
    assert CONTRACT_PATH.exists(), (
        f"Shared contract missing at {CONTRACT_PATH}. "
        "The contract is the writer/reviewer alignment source of truth."
    )
    text = CONTRACT_PATH.read_text("utf-8")
    for clause in ("§1", "§2", "§3", "§4", "§5", "§7a"):
        assert clause in text, f"Contract missing clause marker {clause}"


@pytest.mark.parametrize("phrase", [
    "You have learned",
    "Now it's time",
    "Let's review",
    "In this module",
    "By the end",
    "Here's how to",
    "Try this now",
    "Notice that",
])
def test_contract_carries_section_4_allow_list(phrase: str) -> None:
    text = CONTRACT_PATH.read_text("utf-8")
    assert phrase in text


@pytest.mark.parametrize("prompt_path", WRITER_PROMPTS)
def test_active_writer_prompt_references_shared_contract(prompt_path: Path) -> None:
    text = prompt_path.read_text("utf-8")
    assert CONTRACT_RELATIVE_PATH in text
    assert "{SIZE_POLICY}" in text
    assert "never pad" in text.lower() or "do not pad" in text.lower()
    if prompt_path.name == "linear-write.md":
        assert "{SECTION_WORD_BUDGETS}" in text


def test_active_reviewer_prompt_references_shared_contract_and_size_policy() -> None:
    text = REVIEWER_PROMPT.read_text("utf-8")
    assert CONTRACT_RELATIVE_PATH in text
    assert "{IMMERSION_RULE}" in text
    assert "{SIZE_POLICY}" in text
    assert "mechanical word-count gate" in text
    assert "source-backed" in text
    assert "density" in text
    assert "filler/padding" in text


def test_active_reviewer_keeps_dimension_calibration() -> None:
    text = REVIEWER_PROMPT.read_text("utf-8")
    for dim in (
        "engagement",
        "pedagogical",
        "naturalness",
        "decolonization",
        "tone",
    ):
        assert f"`{dim}`" in text
    assert "A1: English scaffolding is expected" in text
    assert "B1/B2/C1/C2" in text


def test_canonical_anchors_registry_exists_and_has_required_keys() -> None:
    import yaml as _yaml

    registry_path = REPO_ROOT / "data" / "canonical_anchors.yaml"
    assert registry_path.exists(), (
        f"Canonical anchors registry missing at {registry_path}"
    )
    data = _yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and "anchors" in data
    assert isinstance(data["anchors"], list) and data["anchors"]
    for anchor in data["anchors"]:
        assert {"id", "topic_uk", "correct"}.issubset(anchor), (
            f"Anchor missing required keys: {anchor}"
        )
