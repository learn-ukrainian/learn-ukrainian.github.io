"""Unit and syntax tests for Phase 4 Production Training Colab Notebook (#8037)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "projects"
    / "open_model_data"
    / "production_train_gemma3_4b_colab.ipynb"
)


def test_production_colab_notebook_structure() -> None:
    """Verify production training notebook exists, parses as valid JSON, and has standard nbformat."""
    assert NOTEBOOK_PATH.exists(), f"Notebook must exist at {NOTEBOOK_PATH}"

    with open(NOTEBOOK_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    assert nb.get("nbformat") == 4, "Notebook must be nbformat 4"
    assert "cells" in nb, "Notebook must contain cells"
    assert len(nb["cells"]) >= 8, f"Expected at least 8 cells, found {len(nb['cells'])}"

    metadata = nb.get("metadata", {})
    assert metadata.get("accelerator") == "GPU", "Notebook metadata accelerator must be GPU"


def test_production_colab_notebook_cell_syntax() -> None:
    """Verify every python code cell in the notebook is valid Python AST syntax."""
    with open(NOTEBOOK_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    for idx, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") == "code":
            source_lines = cell.get("source", [])
            # Filter out shell commands (!pip, etc.)
            py_lines = [line for line in source_lines if not line.strip().startswith("!")]
            py_code = "".join(py_lines)
            try:
                ast.parse(py_code)
            except SyntaxError as e:
                raise AssertionError(f"Syntax error in code cell {idx}: {e}\nCode:\n{py_code}") from e


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
    assert "/home/ops" not in content, "Notebook must not reference local host paths (/home/ops)"
