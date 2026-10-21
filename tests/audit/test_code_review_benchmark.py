from __future__ import annotations

import json
import subprocess
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


def test_raw_response_persistence(tmp_path: Path) -> None:
    case_path = _write_case(tmp_path)
    case = bench.load_case(case_path)
    cell = bench.Cell("openai", "gpt-5.5", "native_cli", "medium", "with_mcp")
    long_tail = "x" * 9000
    model_finding = {
        "id": "arg-max",
        "severity": "HIGH",
        "category": "security",
        "location": "sample.py:1",
        "description": "Test finding.",
    }
    raw_response = json.dumps([model_finding]) + long_tail

    def runner(_cell: bench.Cell, _prompt: str) -> bench.HarnessCall:
        return bench.HarnessCall(True, raw_response, "", 0, 0.1, ("test",))

    bench.run_cell(
        out_dir=tmp_path / "out",
        cell=cell,
        cases=[case],
        prompt_template="{DIFF}\n{CONTEXT}",
        harness_runner=runner,
    )

    data = json.loads(bench.cell_path(tmp_path / "out", cell).read_text(encoding="utf-8"))
    judgment = data["judgments"][0]

    assert judgment["model_findings"] == [model_finding]
    assert judgment["raw_response"] == raw_response[:8000]
    assert judgment["raw_response_truncated"] is True
    assert judgment["raw_response_chars"] == len(raw_response)


def test_native_codex_rejects_old_model_before_subprocess(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unapproved Codex model reached subprocess")
    monkeypatch.setattr(bench, "run_subprocess", forbidden)
    cell = bench.Cell("openai", "gpt-5.5", "native_cli", "medium", "with_mcp")
    with pytest.raises(ValueError, match=r"only gpt-6\.1-sol"):
        bench.run_native_cli(cell, "prompt")


def test_native_codex_accepts_approved_model():
    cell = bench.Cell("openai", "gpt-6.1-sol", "native_cli", "medium", "with_mcp")
    command = bench.build_native_command(cell, "prompt")
    assert command[command.index("--model") + 1] == "gpt-6.1-sol"


def test_native_claude_runs_without_background_work(monkeypatch):
    """The headless Claude lane carries the #9690 controls from the adapter (#9750)."""
    from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES

    calls = []

    def run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="verdict", stderr="")

    monkeypatch.setenv("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS", "0")
    monkeypatch.setattr(bench.subprocess, "run", run)
    cell = bench.Cell("anthropic", "claude-opus-5-5", "native_cli", "high", "no_mcp")
    assert bench.run_native_cli(cell, "prompt").ok
    ((cmd, kwargs),) = calls
    denies = cmd.index("--disallowedTools")
    assert cmd[denies + 1].split(",") == list(HEADLESS_BACKGROUND_TOOL_DENIES)
    assert denies < cmd.index("--") and cmd[-1] == "prompt"
    assert kwargs["env"].items() >= HEADLESS_BACKGROUND_ENV.items()


def test_native_codex_gets_no_claude_background_controls(monkeypatch):
    calls = []
    monkeypatch.setattr(bench, "run_subprocess", lambda cmd, **kwargs: calls.append((cmd, kwargs)) or "result")
    bench.run_native_cli(bench.Cell("openai", "gpt-6.1-sol", "native_cli", "medium", "no_mcp"), "prompt")
    ((cmd, kwargs),) = calls
    assert "--disallowedTools" not in cmd
    assert kwargs["headless_claude"] is False
