from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit import code_review_benchmark as bench


def _write_case(tmp_path: Path, *, extra: str = "") -> Path:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    diff = corpus / "sample.diff"
    diff.write_text("diff --git a/sample.py b/sample.py\n", encoding="utf-8")
    case = corpus / "sample.yaml"
    case.write_text(
        f"""case_id: sample
pr_number: 1
title: Sample
diff_path: sample.diff
context: Test context.
gold_findings:
  - id: arg-max
    severity: HIGH
    category: security
    location: sample.py
    description: Test finding.
{extra}""",
        encoding="utf-8",
    )
    return case


def test_cli_parses_single_cell_arguments() -> None:
    families = bench.parse_csv("openai", bench.FAMILIES)
    harnesses = bench.parse_csv("hermes", bench.HARNESSES)
    cases = bench.parse_csv("pr-2031-activity-schema")

    cells = bench.build_matrix(
        families=families,
        harnesses=harnesses,
        models=None,
        efforts=None,
        mcp_states=None,
        smoke=bool(cases),
    )

    assert cells == [bench.Cell("openai", "gpt-5.5", "hermes", "medium", "with_mcp")]


def test_corpus_loader_rejects_malformed_yaml(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "bad.yaml").write_text("case_id: [unterminated\n", encoding="utf-8")

    with pytest.raises(ValueError, match="malformed YAML"):
        bench.load_corpus(corpus)


def test_corpus_loader_reads_valid_case(tmp_path: Path) -> None:
    _write_case(tmp_path)

    cases = bench.load_corpus(tmp_path / "corpus")

    assert cases[0]["case_id"] == "sample"
    assert cases[0]["gold_findings"][0]["severity"] == "HIGH"
    assert "diff --git" in cases[0]["diff"]


def test_scorer_returns_perfect_f1_for_perfect_match() -> None:
    gold = {
        "gold_findings": [
            {
                "id": "arg-max",
                "severity": "HIGH",
                "category": "security",
                "location": "scripts/proxy.py",
                "description": "Uses argv.",
            }
        ]
    }
    verdict = {
        "findings": [
            {
                "id": "large-prompt-argv",
                "severity": "HIGH",
                "category": "security",
                "location": "scripts/proxy.py:27",
                "description": "Large prompts go through argv.",
            }
        ]
    }

    score = bench.score_case(verdict, gold)

    assert score["precision"] == 1.0
    assert score["recall"] == 1.0
    assert score["f1"] == 1.0
    assert score["catastrophic_misses"] == 0


def test_scorer_returns_zero_f1_for_empty_model_output() -> None:
    gold = {
        "gold_findings": [
            {
                "id": "error-envelope",
                "severity": "HIGH",
                "category": "spec-compliance",
                "location": "scripts/proxy.py",
                "description": "Wrong envelope.",
            }
        ]
    }

    score = bench.score_case({"findings": []}, gold)

    assert score["precision"] == 0.0
    assert score["recall"] == 0.0
    assert score["f1"] == 0.0
    assert score["catastrophic_misses"] == 1


def test_scorer_matches_file_not_line_and_rejects_wrong_severity() -> None:
    gold = {
        "gold_findings": [
            {
                "id": "healthz-fork",
                "severity": "MEDIUM",
                "category": "dos-surface",
                "location": "scripts/proxy.py",
                "description": "Forks on health checks.",
            }
        ]
    }
    verdict = {
        "findings": [
            {
                "id": "health-check-dos",
                "severity": "MEDIUM",
                "category": "dos-surface",
                "location": "scripts/proxy.py:999",
                "description": "Same file, shifted line.",
            },
            {
                "id": "health-check-low",
                "severity": "LOW",
                "category": "dos-surface",
                "location": "scripts/proxy.py:10",
                "description": "Wrong severity should not match.",
            },
        ]
    }

    score = bench.score_case(verdict, gold)

    assert score["tp"] == 1
    assert score["fp"] == 1
    assert score["fn"] == 0
    assert score["f1"] == 0.6667


def test_run_cell_uses_injected_runner_and_writes_reportable_json(tmp_path: Path) -> None:
    case_path = _write_case(tmp_path)
    case = bench.load_case(case_path)
    cell = bench.Cell("openai", "gpt-5.5", "native_cli", "medium", "with_mcp")

    def runner(_cell: bench.Cell, _prompt: str) -> bench.HarnessCall:
        payload = [
            {
                "id": "arg-max",
                "severity": "HIGH",
                "category": "security",
                "location": "sample.py:1",
                "description": "Test finding.",
            }
        ]
        return bench.HarnessCall(True, json.dumps(payload), "", 0, 0.1, ("test",))

    record = bench.run_cell(
        out_dir=tmp_path / "out",
        cell=cell,
        cases=[case],
        prompt_template="{DIFF}\n{CONTEXT}",
        harness_runner=runner,
    )

    assert record["scores"]["f1"] == 1.0
    assert bench.cell_path(tmp_path / "out", cell).exists()
