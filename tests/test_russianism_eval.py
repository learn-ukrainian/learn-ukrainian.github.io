from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import yaml

from scripts.ai_agent_bridge import _claude
from scripts.audit import russianism_eval


def _prompt_payload() -> dict:
    return {
        "version": 1,
        "prompts": [
            {
                "id": "p1",
                "category": "translation",
                "prompt_text": "Translate a short email to Ukrainian.",
                "expected_calque_categories": ["participation calque"],
                "notes": "Fixture prompt one.",
            },
            {
                "id": "p2",
                "category": "business",
                "prompt_text": "Write a Ukrainian business update.",
                "expected_calque_categories": ["receive/get calque"],
                "notes": "Fixture prompt two.",
            },
        ],
    }


def _write_prompts(tmp_path: Path, payload: dict | None = None) -> Path:
    path = tmp_path / "prompts.yaml"
    path.write_text(
        yaml.safe_dump(payload or _prompt_payload(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


class FakeCaller:
    def __init__(self, outputs: dict[tuple[str, str], str] | None = None):
        self.outputs = outputs or {}
        self.calls: list[tuple[str, str]] = []

    def plan(self, prompt: russianism_eval.PromptCase, model: str) -> russianism_eval.BridgeCall:
        family = russianism_eval._family_for_model(model)
        return russianism_eval.BridgeCall(
            prompt_id=prompt.id,
            model=model,
            family=family,
            task_id=f"fake-run-{prompt.id}-{model}",
            argv=[".venv/bin/python", "scripts/ai_agent_bridge/__main__.py", f"ask-{family}"],
            stdin=prompt.prompt_text if family != "claude" else None,
        )

    def __call__(self, prompt: russianism_eval.PromptCase, model: str) -> tuple[russianism_eval.BridgeCall, str]:
        self.calls.append((prompt.id, model))
        output = self.outputs[(prompt.id, model)]
        return self.plan(prompt, model), output


def test_load_prompts_validates_required_schema(tmp_path: Path) -> None:
    path = _write_prompts(tmp_path)

    prompts = russianism_eval.load_prompts(path)

    assert [prompt.id for prompt in prompts] == ["p1", "p2"]
    assert prompts[0].expected_calque_categories == ["participation calque"]


def test_load_prompts_rejects_duplicate_ids(tmp_path: Path) -> None:
    payload = _prompt_payload()
    payload["prompts"][1]["id"] = "p1"
    path = _write_prompts(tmp_path, payload)

    with pytest.raises(ValueError, match="duplicate prompt id"):
        russianism_eval.load_prompts(path)


def test_dry_run_prints_matrix_without_calling_agents(tmp_path: Path, capsys) -> None:
    prompts_path = _write_prompts(tmp_path)
    fake = FakeCaller()

    exit_code = russianism_eval.main(
        [
            "--prompts",
            str(prompts_path),
            "--models",
            "claude-opus-4-7,gpt-5.5",
            "--dry-run",
            "--max-parallel",
            "2",
        ],
        caller=fake,
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert fake.calls == []
    assert "Dry run: prompts=2 models=2 dispatches=4" in stdout
    assert "DRY-RUN prompt=p1 model=claude-opus-4-7" in stdout
    assert "DRY-RUN prompt=p2 model=gpt-5.5" in stdout
    assert "No agent calls were made." in stdout


def test_run_eval_scores_known_russicisms(tmp_path: Path) -> None:
    prompts = russianism_eval.load_prompts(_write_prompts(tmp_path))[:1]
    outputs = {
        ("p1", "gpt-5.5"): "Він буде приймати участь. Вони хочуть получати лист. Вообще це важливо.",
        ("p1", "claude-opus-4-7"): "Він братиме участь. Вони хочуть отримати лист. Загалом це важливо.",
    }

    rows = russianism_eval.run_eval(
        prompts,
        ["gpt-5.5", "claude-opus-4-7"],
        tmp_path / "out",
        max_parallel=1,
        caller=FakeCaller(outputs),
    )

    by_model = {row.model: row for row in rows}
    assert by_model["gpt-5.5"].russicism_count == 3
    assert by_model["gpt-5.5"].combined_rate_per_100_words > 0
    assert by_model["claude-opus-4-7"].russicism_count == 0


def test_write_outputs_generates_report_summary_and_scores(tmp_path: Path) -> None:
    prompts_path = _write_prompts(tmp_path)
    prompts = russianism_eval.load_prompts(prompts_path)[:1]
    rows = russianism_eval.run_eval(
        prompts,
        ["gpt-5.5"],
        tmp_path / "out",
        max_parallel=1,
        caller=FakeCaller({("p1", "gpt-5.5"): "Він приймати участь і получати лист."}),
    )

    russianism_eval.write_outputs(tmp_path / "out", prompts_path, rows, ["gpt-5.5"])

    assert (tmp_path / "out" / "REPORT.md").exists()
    assert (tmp_path / "out" / "outputs.jsonl").exists()
    summary = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["prompt_count"] == 1
    assert summary["dispatch_count"] == 1
    assert summary["model_summaries"]["gpt-5.5"]["russicism_count"] == 2
    with (tmp_path / "out" / "scores.csv").open(encoding="utf-8") as handle:
        scores = list(csv.DictReader(handle))
    assert scores[0]["prompt_id"] == "p1"
    assert scores[0]["model"] == "gpt-5.5"


def test_report_includes_sample_bad_outputs(tmp_path: Path) -> None:
    prompts_path = _write_prompts(tmp_path)
    prompts = russianism_eval.load_prompts(prompts_path)[:1]
    rows = russianism_eval.run_eval(
        prompts,
        ["gpt-5.5"],
        tmp_path / "out",
        max_parallel=1,
        caller=FakeCaller({("p1", "gpt-5.5"): "Мені нравитися цей самий кращий варіант."}),
    )
    russianism_eval.write_outputs(tmp_path / "out", prompts_path, rows, ["gpt-5.5"])

    report = (tmp_path / "out" / "REPORT.md").read_text(encoding="utf-8")
    assert "## Leaderboard" in report
    assert "## Sample Bad Outputs" in report
    assert "нравитися" in report


def test_optional_gec_checker_is_included(monkeypatch, tmp_path: Path) -> None:
    prompts = russianism_eval.load_prompts(_write_prompts(tmp_path))[:1]

    monkeypatch.setattr(
        russianism_eval,
        "CHECK_UA_GEC_CALQUES",
        lambda text: [{"type": "UA_GEC_CALQUE", "issue": "synthetic calque"}],
    )

    row = russianism_eval.score_output(
        prompts[0],
        "gpt-5.5",
        "codex",
        "task-1",
        "Чистий український текст.",
    )

    assert row.russicism_count == 0
    assert row.gec_calque_count == 1
    assert row.findings[0]["source"] == "check_ua_gec_calques"


def test_bridge_caller_builds_family_specific_commands() -> None:
    prompt = russianism_eval.PromptCase(
        id="p1",
        category="translation",
        prompt_text="Translate.",
        expected_calque_categories=[],
        notes="Fixture.",
    )
    caller = russianism_eval.BridgeCaller("run")

    claude = caller.plan(prompt, "claude-opus-4-7")
    codex = caller.plan(prompt, "gpt-5.5")
    gemini = caller.plan(prompt, "gemini-3.1-pro-preview")

    assert claude.argv[2] == "ask-claude"
    assert "--to-model" in claude.argv
    assert claude.argv[claude.argv.index("--to-model") + 1] == "claude-opus-4-7"
    assert codex.argv[2] == "ask-codex"
    assert codex.stdin == "Translate."
    assert "--to-model" in codex.argv
    assert gemini.argv[2] == "ask-gemini"
    assert "--stdout-only" in gemini.argv
    assert gemini.argv[gemini.argv.index("--model") + 1] == "gemini-3.1-pro-preview"


def test_claude_bridge_extracts_target_model_metadata() -> None:
    msg = {"data": json.dumps({"to_model": "claude-sonnet-4-5"})}

    assert _claude._extract_target_model(msg) == "claude-sonnet-4-5"
    assert _claude._extract_target_model({"data": "{bad json"}) is None
