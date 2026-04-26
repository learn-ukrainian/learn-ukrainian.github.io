from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _small_plan() -> dict:
    return {
        "module": "a1-020",
        "level": "A1",
        "sequence": 20,
        "slug": "my-morning",
        "title": "Мій ранок",
        "subtitle": "Зворотні дієслова",
        "word_target": 20,
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 20,
                "points": ["Introduce a morning dialogue."],
            }
        ],
        "references": [{"title": "Караман Grade 10, p.176"}],
    }


def test_plan_check_accepts_a1_20_plan() -> None:
    plan = linear_pipeline.plan_check(
        linear_pipeline.plan_path_for("a1", "my-morning")
    )

    assert plan["module"] == "a1-020"
    assert plan["sequence"] == 20
    assert plan["word_target"] == 1200


def test_plan_check_rejects_missing_required_key(tmp_path: Path) -> None:
    plan = _small_plan()
    plan.pop("references")
    path = tmp_path / "bad.yaml"
    _write_yaml(path, plan)

    with pytest.raises(linear_pipeline.LinearPipelineError, match="references"):
        linear_pipeline.plan_check(path)


def test_render_phase_prompt_fills_registered_tokens() -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)
    context = linear_pipeline.writer_context(
        plan,
        plan_path.read_text(encoding="utf-8"),
        "Knowledge packet excerpt.",
    )

    rendered = linear_pipeline.render_phase_prompt(
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md",
        context,
    )

    assert "{NORTH_STAR}" not in rendered
    assert "{LESSON_CONTRACT}" not in rendered
    assert "{LEVEL}" not in rendered
    assert "TARGET: 15-35% Ukrainian." in rendered


@pytest.mark.parametrize(
    ("writer", "agent_name"),
    [
        ("claude-tools", "claude"),
        ("gemini-tools", "gemini"),
    ],
)
def test_invoke_writer_routes_supported_writers(
    tmp_path: Path,
    writer: str,
    agent_name: str,
) -> None:
    calls = []

    class Result:
        response = "writer output"

    def fake_invoker(agent: str, prompt: str, **kwargs: object) -> Result:
        calls.append((agent, prompt, kwargs))
        return Result()

    response = linear_pipeline.invoke_writer(
        "Write the module.",
        writer=writer,
        cwd=tmp_path,
        invoker=fake_invoker,
    )

    assert response == "writer output"
    assert calls[0][0] == agent_name
    assert calls[0][1] == "Write the module."
    assert calls[0][2]["mode"] == "workspace-write"
    assert calls[0][2]["cwd"] == tmp_path
    assert calls[0][2]["entrypoint"] == "dispatch"
    assert calls[0][2]["model"] == linear_pipeline.WRITER_DEFAULTS[writer]["model"]
    assert calls[0][2]["effort"] == linear_pipeline.WRITER_DEFAULTS[writer]["effort"]
    assert calls[0][2]["tool_config"] == {"output_format": "text"}


def test_invoke_writer_rejects_unknown_writer(tmp_path: Path) -> None:
    with pytest.raises(linear_pipeline.LinearPipelineError, match="Unknown writer"):
        linear_pipeline.invoke_writer("Write the module.", writer="bogus", cwd=tmp_path)


def test_aggregate_llm_review_requires_exact_qg_dims() -> None:
    report = {
        dim: {
            "score": 9.0,
            "evidence": '"Specific quoted evidence."',
            "verdict": "PASS",
        }
        for dim in QG_DIMS
    }
    report["extra"] = {
        "score": 9.0,
        "evidence": '"Specific quoted evidence."',
        "verdict": "PASS",
    }

    with pytest.raises(linear_pipeline.LinearPipelineError, match="extra"):
        linear_pipeline.aggregate_llm_review(report, "A1")


def test_aggregate_llm_review_requires_quoted_evidence() -> None:
    report = {
        dim: {
            "score": 9.0,
            "evidence": '"Specific quoted evidence."',
            "verdict": "PASS",
        }
        for dim in QG_DIMS
    }
    report["tone"]["evidence"] = "Specific but unquoted evidence."

    with pytest.raises(linear_pipeline.LinearPipelineError, match="quoted excerpt"):
        linear_pipeline.aggregate_llm_review(report, "A1")


def test_run_python_qg_passes_structural_fixture(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.yaml"
    module_dir = tmp_path / "my-morning"
    module_dir.mkdir()
    _write_yaml(plan_path, _small_plan())
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "# Мій ранок",
                "",
                "## Діалоги",
                "",
                "This morning pattern is simple and concrete for careful adult",
                "learners. Use **прокидаюся**, **вмиваюся**, **одягаюся**,",
                "and **снідаю** before breakfast today clearly.",
                "",
                "<!-- INJECT_ACTIVITY: act-1 -->",
            ]
        ),
        encoding="utf-8",
    )
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "fill-in",
                "title": "Додайте -ся",
                "items": [
                    {
                        "sentence": "Я вмиваю__.",
                        "answer": "ся",
                        "options": ["ся", "ти", "ми"],
                    }
                ],
            }
        ],
    )
    _write_yaml(
        module_dir / "vocabulary.yaml",
        [
            {
                "lemma": "прокидатися",
                "translation": "to wake up",
                "pos": "verb",
                "usage": "Я прокидаюся.",
            }
        ],
    )
    _write_yaml(
        module_dir / "resources.yaml",
        [{"title": "Караман Grade 10, p.176", "source_ref": "Караман Grade 10, p.176"}],
    )

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    report = linear_pipeline.run_python_qg(
        module_dir,
        plan_path,
        verify_words_fn=fake_verify,
    )

    assert report["gates"]["passed"] is True
    assert report["gates"]["russianisms_clean"]["passed"] is True
    assert report["gates"]["surzhyk_clean"]["passed"] is True
    assert report["gates"]["calques_clean"]["passed"] is True
    assert report["gates"]["paronym_clean"]["passed"] is True
