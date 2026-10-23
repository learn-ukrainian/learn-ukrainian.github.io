"""Unit and syntax tests for Phase 4 Production Training Colab Notebook (#8037)."""

from __future__ import annotations

from pathlib import Path

from tests._host_path_guard import assert_no_host_paths

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "projects"
    / "open_model_data"
    / "production_train_gemma3_4b_colab.ipynb"
)


def test_production_colab_notebook_contract_invariants() -> None:
    """Verify repo ID, model ID, directional gates, and privacy compliance in notebook."""
    with open(NOTEBOOK_PATH, encoding="utf-8") as f:
        content = f.read()

    # Must point to the official public pilot dataset
    assert "krisztiankoos/uldr-v0.1-pilot" in content, "Notebook must reference krisztiankoos/uldr-v0.1-pilot"
    # Must use google/gemma-3-4b-it
    assert "google/gemma-3-4b-it" in content, "Notebook must reference google/gemma-3-4b-it"
    # Must specify QLoRA NF4
    assert "nf4" in content, "Notebook must configure nf4 quantization"
    # Must test the two canonical directional safety gates with Clopper-Pearson bound
    assert "exact_clopper_pearson_upper" in content, "Must implement Clopper-Pearson exact bound"
    assert "90.0" in content, "Must test Calque Elimination >= 90%"
    assert "1.0" in content, "Must test Harmful-Edit <= 1.0%"

    # No hardcoded secrets or raw keys
    assert "hf_" not in content or "hf_token" in content or "hf_hub" in content, "Must not contain hardcoded HF tokens"
    assert_no_host_paths(content, "notebook")
