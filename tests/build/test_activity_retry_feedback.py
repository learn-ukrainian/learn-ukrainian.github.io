from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

dispatch = importlib.import_module("build.dispatch")
v6_build = importlib.import_module("build.v6_build")

VALID_ACTIVITY_YAML = yaml.safe_dump(
    {
        "version": "1.0",
        "module": "retry-feedback",
        "level": "a1",
        "inline": [{
            "id": "quiz-intro",
            "type": "quiz",
            "instruction": "Оберіть",
            "items": [{"question": "Це ____.", "options": ["кіт", "пес"], "correct": 0}],
        }],
        "workbook": [{
            "id": "match-words",
            "type": "match-up",
            "instruction": "З'єднайте",
            "pairs": [{"left": word, "right": "known"} for word in ["кіт", "пес"] * 3],
        }],
    },
    allow_unicode=True,
    sort_keys=False,
) + "\n# " + ("padding " * 260)


def _write_activity_fixture(tmp_path: Path) -> tuple[Path, Path, str, str]:
    level = "a1"
    slug = "retry-feedback"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    (curriculum_root / level / "orchestration" / slug).mkdir(parents=True)
    (curriculum_root / "plans" / level).mkdir(parents=True)
    (tmp_path / "schemas").mkdir()
    phases_dir = tmp_path / "scripts" / "build" / "phases"
    phases_dir.mkdir(parents=True)
    (curriculum_root / "plans" / level / f"{slug}.yaml").write_text(
        yaml.safe_dump(
            {
                "title": "Retry Feedback",
                "vocabulary_hints": {"required": ["кіт", "пес"]},
            },
            allow_unicode=True,
        ),
        "utf-8",
    )
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.write_text("## Intro\n\nкіт і пес\n\n<!-- INJECT_ACTIVITY: quiz-intro -->\n", "utf-8")
    (phases_dir / "v6-activities.md").write_text(
        "<retry-feedback>\n{UNGROUNDED_FEEDBACK}\n</retry-feedback>\n",
        "utf-8",
    )
    shutil.copy(
        Path(__file__).resolve().parents[2] / "schemas" / "activity-v2.schema.json",
        tmp_path / "schemas" / "activity-v2.schema.json",
    )
    return curriculum_root, content_path, level, slug


def _run_step_activities(tmp_path: Path, monkeypatch, feedback: str | None) -> str:
    curriculum_root, content_path, level, slug = _write_activity_fixture(tmp_path)
    captured: dict[str, str] = {}

    def fake_dispatch(prompt: str, *args, **kwargs):
        captured["prompt"] = prompt
        return True, VALID_ACTIVITY_YAML

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(v6_build, "PHASES_DIR", tmp_path / "scripts" / "build" / "phases")
    monkeypatch.setattr(dispatch, "dispatch_agent", fake_dispatch)
    output_path = v6_build.step_activities(
        content_path,
        level,
        8,
        slug,
        writer="gemini-tools",
        max_retries=0,
        ungrounded_feedback=feedback,
    )
    assert output_path is not None
    return captured["prompt"]


def test_step_activities_omits_prevalidate_failure_on_first_pass(tmp_path, monkeypatch):
    assert "PRE-VALIDATE FAILED" not in _run_step_activities(tmp_path, monkeypatch, None)


def test_step_activities_includes_prevalidate_feedback_on_retry(tmp_path, monkeypatch):
    assert "DO NOT use invented answers again." in _run_step_activities(
        tmp_path,
        monkeypatch,
        "DO NOT use invented answers again.",
    )


def test_step_activity_pre_validate_returns_persisted_payload(tmp_path, monkeypatch):
    curriculum_root, content_path, level, slug = _write_activity_fixture(tmp_path)
    activities_dir = curriculum_root / level / "activities"
    activities_dir.mkdir()
    (activities_dir / f"{slug}.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "module": slug,
                "level": level,
                "inline": [{
                    "id": "quiz-intro",
                    "type": "fill-in",
                    "instruction": "Вставте слово",
                    "items": [{"sentence": "Це ____.", "answer": "гриб"}],
                }],
                "workbook": [],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        "utf-8",
    )
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    ok, payload = v6_build.step_activity_pre_validate(content_path, level, slug)

    validation_path = curriculum_root / level / "orchestration" / slug / "activity-pre-validation.json"
    assert ok is False
    assert payload == json.loads(validation_path.read_text("utf-8"))
    assert payload["ungrounded_answers"][0]["word"] == "гриб"
    assert payload["required_vocab_missing"] == ["кіт", "пес"]
