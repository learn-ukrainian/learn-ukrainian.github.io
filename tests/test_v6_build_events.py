"""Tests for v6 build stdout event streaming (#1180)."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import textwrap
import types
from datetime import datetime
from pathlib import Path

import pytest
import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

orch_index = importlib.import_module("build.orch_index")
quick_verify = importlib.import_module("build.quick_verify")
v6_build = importlib.import_module("build.v6_build")


REVIEW_RAW = """\
| 1. Plan adherence | 9/10 | grounded |
| 2. Linguistic accuracy | 9/10 | accurate |
| 3. Pedagogical quality | 9/10 | clear |
| 4. Vocabulary coverage | 9/10 | on target |
| 5. Exercise quality | 9/10 | aligned |
| 6. Engagement & tone | 9/10 | engaging |
| 7. Structural integrity | 9/10 | solid |
| 8. Cultural accuracy | 9/10 | appropriate |
| 9. Dialogue & conversation quality | 9/10 | natural |

Verdict: PASS
"""


def _write_manifest(curriculum_root: Path, level: str, slugs: list[str]) -> None:
    curriculum_root.mkdir(parents=True, exist_ok=True)
    manifest = {"levels": {level: {"modules": slugs}}}
    (curriculum_root / "curriculum.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        "utf-8",
    )


def _event_lines(output: str) -> list[dict]:
    events = []
    for line in output.splitlines():
        if line.startswith("{\"event\""):
            events.append(json.loads(line))
    return events


def _single_module_tree(tmp_path: Path, level: str = "a2", slug: str = "a2-bridge") -> Path:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    _write_manifest(curriculum_root, level, [slug])
    level_dir = curriculum_root / level
    (level_dir / "orchestration").mkdir(parents=True, exist_ok=True)
    level_dir.mkdir(parents=True, exist_ok=True)
    plan_path = curriculum_root / "plans" / level / f"{slug}.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": 1,
                "slug": slug,
                "level": level,
                "sequence": 1,
                "title": slug.replace("-", " ").title(),
                "word_target": 2200,
                "phase": f"{level.upper()}.1",
                "content_outline": [
                    {"section": "Intro", "words": 1700},
                    {"section": "Summary", "words": 500},
                ],
                "vocabulary_hints": {"required": ["місто (city)"]},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )
    return curriculum_root


def test_emit_event_writes_json_line(capsys: pytest.CaptureFixture[str]) -> None:
    v6_build.emit_event("foo", slug="x", score=9.5)

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1

    event = json.loads(lines[0])
    assert event["event"] == "foo"
    assert event["slug"] == "x"
    assert event["score"] == 9.5
    assert datetime.fromisoformat(event["ts"]).tzinfo is not None


def test_emit_event_uses_default_str_for_non_serializable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = Path("/tmp/example")

    v6_build.emit_event("foo", payload=payload)

    event = json.loads(capsys.readouterr().out.strip())
    assert event["payload"] == str(payload)


def test_step_review_emits_review_score_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    level = "a2"
    slug = "a2-bridge"
    curriculum_root = _single_module_tree(tmp_path, level=level, slug=slug)
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.write_text("# Lesson\n\nУкраїнський текст.\n", "utf-8")

    plan_path = curriculum_root / "plans" / level / f"{slug}.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("title: A2 Bridge\nword_target: 1200\n", "utf-8")

    phases_dir = tmp_path / "scripts" / "build" / "phases"
    phases_dir.mkdir(parents=True, exist_ok=True)
    (phases_dir / "v6-review.md").write_text(
        "Review {TOPIC_TITLE}\n\n{GENERATED_CONTENT}\n",
        "utf-8",
    )

    import build.dispatch as dispatch

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "PHASES_DIR", phases_dir)
    monkeypatch.setattr(v6_build, "_build_vesum_report", lambda *args, **kwargs: "")
    monkeypatch.setattr(v6_build, "_save_structured_findings", lambda *args, **kwargs: None)
    monkeypatch.setattr(dispatch, "dispatch_agent", lambda *args, **kwargs: (True, REVIEW_RAW))

    passed, score, raw = v6_build.step_review(content_path, level, 1, slug, writer="claude")

    assert passed is True
    assert score == 9.0
    assert raw == REVIEW_RAW

    review_events = [
        event for event in _event_lines(capsys.readouterr().out)
        if event["event"] == "review_score"
    ]
    assert len(review_events) == 1
    assert review_events[0]["level"] == level
    assert review_events[0]["slug"] == slug
    assert review_events[0]["round"] == 1
    assert review_events[0]["score"] == 9.0


def test_main_emits_batch_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    _write_manifest(curriculum_root, "a2", ["a2-bridge", "dative-verbs"])

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "_should_skip_batch_module", lambda *args, **kwargs: (False, ""))
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "a2", "1", "--range", "2", "--step", "check", "--writer", "gemini"],
    )

    with pytest.raises(SystemExit) as exc:
        v6_build.main()

    assert exc.value.code == 0
    events = _event_lines(capsys.readouterr().out)
    assert events[0]["event"] == "batch_start"
    assert events[0]["total"] == 2
    assert events[-1]["event"] == "batch_done"
    assert events[-1]["succeeded"] == 2
    assert events[-1]["failed"] == 0


def test_main_emits_module_failed_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    curriculum_root = _single_module_tree(tmp_path)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "step_check", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "a2", "1", "--step", "check", "--writer", "gemini"],
    )

    with pytest.raises(SystemExit) as exc:
        v6_build.main()

    assert exc.value.code == 1
    events = _event_lines(capsys.readouterr().out)
    assert events[0]["event"] == "module_start"
    assert events[1]["event"] == "module_failed"
    assert events[1]["phase"] == "check"
    assert events[1]["error"] == "Build FAILED at Step 2 (plan check)"


def test_main_emits_module_done_after_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    curriculum_root = _single_module_tree(tmp_path)
    content_path = curriculum_root / "a2" / "a2-bridge.md"
    content_path.write_text("# Lesson\n\nУкраїнський текст.\n", "utf-8")

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: (True, 9.6, "Verdict: PASS\n"))
    monkeypatch.setattr(v6_build, "step_publish", lambda *args, **kwargs: True)
    monkeypatch.setattr(quick_verify, "_check_toxic_tokens", lambda text: [])
    monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "a2", "1", "--step", "review", "--writer", "gemini"],
    )

    v6_build.main()

    events = _event_lines(capsys.readouterr().out)
    event_types = [event["event"] for event in events]
    assert "phase_done" in event_types
    assert event_types[-1] == "module_done"
    module_done = events[-1]
    assert module_done["slug"] == "a2-bridge"
    assert module_done["final_score"] == 9.6
    assert module_done["ok"] is True


def test_main_persists_skipped_optional_phases_as_satisfied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    curriculum_root = _single_module_tree(tmp_path)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "_inject_abetka_activities", lambda *args, **kwargs: None)
    monkeypatch.setattr(v6_build, "_post_process_content", lambda *args, **kwargs: 0)
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "_get_failing_audit_gates", lambda *args, **kwargs: ("pass", []))
    monkeypatch.setattr(v6_build, "step_check", lambda *args, **kwargs: True)

    def fake_research(level: str, module_num: int, slug: str) -> Path:
        packet_path = curriculum_root / level / "research" / f"{slug}-knowledge-packet.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text("# Packet\n", "utf-8")
        return packet_path

    def fake_write(level: str, module_num: int, slug: str, packet_path: Path | None, **kwargs) -> Path:
        content_path = curriculum_root / level / f"{slug}.md"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_text("# Lesson\n\nУкраїнський текст.\n", "utf-8")
        return content_path

    def fake_activities(content_path: Path, level: str, module_num: int, slug: str, **kwargs) -> Path:
        activity_path = curriculum_root / level / "activities" / f"{slug}.yaml"
        activity_path.parent.mkdir(parents=True, exist_ok=True)
        activity_path.write_text("- type: quiz\n", "utf-8")
        return activity_path

    def fake_vocab(content_path: Path, level: str, module_num: int, slug: str, **kwargs) -> Path:
        vocab_path = curriculum_root / level / "vocabulary" / f"{slug}.yaml"
        vocab_path.parent.mkdir(parents=True, exist_ok=True)
        vocab_path.write_text("- term: місто\n", "utf-8")
        return vocab_path

    monkeypatch.setattr(v6_build, "step_research", fake_research)
    monkeypatch.setattr(v6_build, "step_write_with_retry", fake_write)
    monkeypatch.setattr(v6_build, "step_activities", fake_activities)
    monkeypatch.setattr(v6_build, "step_repair", lambda *args, **kwargs: (True, False))
    monkeypatch.setattr(v6_build, "step_verify_exercises", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_vocab", fake_vocab)
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: (True, 9.6, "Verdict: PASS\n"))
    monkeypatch.setattr(v6_build, "step_publish", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_audit", lambda *args, **kwargs: True)
    monkeypatch.setattr(quick_verify, "_check_toxic_tokens", lambda text: [])
    monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "a2", "1", "--step", "all", "--writer", "gemini", "--no-skeleton"],
    )

    assert v6_build.main() is True

    state_path = curriculum_root / "a2" / "orchestration" / "a2-bridge" / "state.json"
    state = json.loads(state_path.read_text("utf-8"))

    assert state["phases"]["skeleton"]["status"] == "skipped"
    assert state["phases"]["pre-verify"]["status"] == "skipped"
    assert v6_build._all_phases_complete("a2", "a2-bridge") is True


@pytest.mark.parametrize(
    ("level", "slug", "verify_result", "stress_result", "phase_name", "expected_status"),
    [
        ("a2", "a2-bridge", "degraded", "skipped", "verify", "degraded"),
        ("a1", "a1-bridge", "complete", "degraded", "stress", "degraded"),
    ],
)
def test_main_persists_only_successful_verify_and_stress_phases_as_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    level: str,
    slug: str,
    verify_result: str,
    stress_result: str,
    phase_name: str,
    expected_status: str,
) -> None:
    curriculum_root = _single_module_tree(tmp_path, level=level, slug=slug)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "_inject_abetka_activities", lambda *args, **kwargs: None)
    monkeypatch.setattr(v6_build, "_post_process_content", lambda *args, **kwargs: 0)
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "_get_failing_audit_gates", lambda *args, **kwargs: ("pass", []))
    monkeypatch.setattr(v6_build, "step_check", lambda *args, **kwargs: True)

    def fake_research(level: str, module_num: int, slug: str) -> Path:
        packet_path = curriculum_root / level / "research" / f"{slug}-knowledge-packet.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text("# Packet\n", "utf-8")
        return packet_path

    def fake_write(level: str, module_num: int, slug: str, packet_path: Path | None, **kwargs) -> Path:
        content_path = curriculum_root / level / f"{slug}.md"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_text("# Lesson\n\nУкраїнський текст.\n", "utf-8")
        return content_path

    def fake_activities(content_path: Path, level: str, module_num: int, slug: str, **kwargs) -> Path:
        activity_path = curriculum_root / level / "activities" / f"{slug}.yaml"
        activity_path.parent.mkdir(parents=True, exist_ok=True)
        activity_path.write_text("- type: quiz\n", "utf-8")
        return activity_path

    def fake_vocab(content_path: Path, level: str, module_num: int, slug: str, **kwargs) -> Path:
        vocab_path = curriculum_root / level / "vocabulary" / f"{slug}.yaml"
        vocab_path.parent.mkdir(parents=True, exist_ok=True)
        vocab_path.write_text("- term: місто\n", "utf-8")
        return vocab_path

    monkeypatch.setattr(v6_build, "step_research", fake_research)
    monkeypatch.setattr(v6_build, "step_write_with_retry", fake_write)
    monkeypatch.setattr(v6_build, "step_activities", fake_activities)
    monkeypatch.setattr(v6_build, "step_repair", lambda *args, **kwargs: (True, False))
    monkeypatch.setattr(v6_build, "step_verify_exercises", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_vocab", fake_vocab)
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: verify_result)
    monkeypatch.setattr(v6_build, "step_annotate", lambda *args, **kwargs: stress_result)
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: (True, 9.6, "Verdict: PASS\n"))
    monkeypatch.setattr(v6_build, "step_publish", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_audit", lambda *args, **kwargs: True)
    monkeypatch.setattr(quick_verify, "_check_toxic_tokens", lambda text: [])
    monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", level, "1", "--step", "all", "--writer", "gemini", "--no-skeleton"],
    )

    assert v6_build.main() is True

    state_path = curriculum_root / level / "orchestration" / slug / "state.json"
    state = json.loads(state_path.read_text("utf-8"))
    assert state["phases"][phase_name]["status"] == expected_status
    assert v6_build._all_phases_complete(level, slug) is False

    phase_events = [
        event for event in _event_lines(capsys.readouterr().out)
        if event["event"] == "phase_done" and event["phase"] == phase_name
    ]
    assert phase_events[-1]["status"] == expected_status
    assert phase_events[-1]["ok"] is False


def test_step_audit_rejects_status_file_without_mtime_advance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    curriculum_root = _single_module_tree(tmp_path)
    content_path = curriculum_root / "a2" / "a2-bridge.md"
    content_path.write_text("# Lesson\n\nУкраїнський текст.\n", "utf-8")

    status_path = curriculum_root / "a2" / "status" / "a2-bridge.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps({"overall": {"status": "pass"}, "gates": {}}),
        "utf-8",
    )
    original_mtime = 1_700_000_000
    os.utime(status_path, (original_mtime, original_mtime))

    def fake_audit_module(*args, **kwargs) -> bool:
        status_path.write_text(
            json.dumps({"overall": {"status": "pass"}, "gates": {}}),
            "utf-8",
        )
        os.utime(status_path, (original_mtime, original_mtime))
        return True

    fake_audit_core = types.ModuleType("audit.core")
    fake_audit_core.audit_module = fake_audit_module

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setitem(sys.modules, "audit.core", fake_audit_core)

    assert v6_build.step_audit(content_path, "a2", "a2-bridge") is False
    assert not status_path.exists()


def test_main_blocks_publish_when_audit_crashes_with_stale_passing_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    curriculum_root = _single_module_tree(tmp_path)
    content_path = curriculum_root / "a2" / "a2-bridge.md"
    content_path.write_text("# Lesson\n\nУкраїнський текст.\n", "utf-8")

    status_path = curriculum_root / "a2" / "status" / "a2-bridge.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps({"overall": {"status": "pass"}, "gates": {}}),
        "utf-8",
    )

    published: list[str] = []

    def fake_audit_module(*args, **kwargs) -> bool:
        raise RuntimeError("audit crashed")

    fake_audit_core = types.ModuleType("audit.core")
    fake_audit_core.audit_module = fake_audit_module

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "step_publish", lambda *args, **kwargs: published.append("publish") or True)
    monkeypatch.setattr(v6_build, "step_repair", lambda *args, **kwargs: (True, False))
    monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "audit.core", fake_audit_core)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "a2", "1", "--step", "publish", "--writer", "gemini"],
    )

    assert v6_build.main() is False
    assert published == []
    assert not status_path.exists()


@pytest.mark.parametrize(
    ("word_target", "expected_error"),
    [
        (None, "word_target missing or non-numeric"),
        ("not-a-number", "word_target missing or non-numeric"),
        (0, "word_target must be greater than zero"),
    ],
)
def test_run_pre_build_gate_rejects_invalid_word_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    word_target: object,
    expected_error: str,
) -> None:
    curriculum_root = _single_module_tree(tmp_path)
    plan_path = curriculum_root / "plans" / "a2" / "a2-bridge.yaml"
    plan_data = yaml.safe_load(plan_path.read_text("utf-8"))

    if word_target is None:
        plan_data.pop("word_target", None)
    else:
        plan_data["word_target"] = word_target

    plan_path.write_text(
        yaml.safe_dump(plan_data, sort_keys=False, allow_unicode=True),
        "utf-8",
    )

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    assert v6_build._run_pre_build_gate("a2", "a2-bridge") is False
    assert expected_error in capsys.readouterr().out


@pytest.mark.parametrize("step_name", ["write", "review", "publish"])
def test_main_blocks_plan_consuming_single_steps_on_pre_build_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    step_name: str,
) -> None:
    curriculum_root = _single_module_tree(tmp_path)
    plan_path = curriculum_root / "plans" / "a2" / "a2-bridge.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": 1,
                "slug": "a2-bridge",
                "level": "a2",
                "sequence": 1,
                "title": "A2 Bridge",
                "word_target": 1200,
                "phase": "A2.1",
                "content_outline": [{"section": "Intro", "words": 1200}],
                "vocabulary_hints": {"required": ["місто (city)"]},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)

    called_steps: list[str] = []

    monkeypatch.setattr(
        v6_build,
        "step_write_with_retry",
        lambda *args, **kwargs: called_steps.append("write"),
    )
    monkeypatch.setattr(
        v6_build,
        "step_review",
        lambda *args, **kwargs: called_steps.append("review"),
    )
    monkeypatch.setattr(
        v6_build,
        "step_publish",
        lambda *args, **kwargs: called_steps.append("publish"),
    )
    monkeypatch.setattr(orch_index, "generate_index", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "a2", "1", "--step", step_name, "--writer", "gemini"],
    )

    with pytest.raises(SystemExit) as exc:
        v6_build.main()

    assert exc.value.code == 1
    assert called_steps == []

    events = _event_lines(capsys.readouterr().out)
    assert events[0]["event"] == "module_start"
    assert events[-1]["event"] == "module_failed"
    assert events[-1]["phase"] == "check"
    assert events[-1]["error"] == "Build FAILED at Step 2 (plan check)"


def test_main_returns_false_and_releases_lock_when_review_halts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    curriculum_root = _single_module_tree(tmp_path)
    content_path = curriculum_root / "a2" / "a2-bridge.md"
    content_path.write_text("# Lesson\n\nУкраїнський текст.\n", "utf-8")

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)

    releases: list[str] = []

    def track_release(self) -> None:
        releases.append("released")

    reviews = iter([
        (False, 6.5, "Verdict: FAIL\n"),
        (False, 6.0, "Verdict: FAIL\n"),
    ])

    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", track_release)
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(reviews))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "a2", "1", "--step", "review", "--writer", "gemini"],
    )

    result = v6_build.main()

    assert result is False
    assert releases == ["released"]
    events = _event_lines(capsys.readouterr().out)
    assert events[0]["event"] == "module_start"
    assert events[-1]["event"] == "module_failed"
    assert events[-1]["phase"] == "review"


def test_main_releases_lock_when_publish_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    curriculum_root = _single_module_tree(tmp_path)
    content_path = curriculum_root / "a2" / "a2-bridge.md"
    content_path.write_text("# Lesson\n\nУкраїнський текст.\n", "utf-8")

    releases: list[str] = []

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: releases.append("released"))
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: (True, 9.6, "Verdict: PASS\n"))
    monkeypatch.setattr(v6_build, "step_publish", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(quick_verify, "_check_toxic_tokens", lambda text: [])
    monkeypatch.setattr(
        sys,
        "argv",
        ["v6_build.py", "a2", "1", "--step", "review", "--writer", "gemini"],
    )

    with pytest.raises(RuntimeError, match="boom"):
        v6_build.main()

    assert releases == ["released"]


def test_subprocess_event_stream_is_line_buffered(tmp_path: Path) -> None:
    curriculum_root = _single_module_tree(tmp_path)
    helper_path = tmp_path / "run_v6_check.py"
    helper_path.write_text(
        textwrap.dedent(
            f"""
            import sys
            import time
            from pathlib import Path

            project_root = Path({str(v6_build.PROJECT_ROOT)!r})
            curriculum_root = Path(sys.argv[1])
            sys.path.insert(0, str(project_root / "scripts"))

            import build.orch_index as orch_index
            import build.v6_build as v6_build

            v6_build.CURRICULUM_ROOT = curriculum_root
            v6_build.ModuleBuildLock.acquire = lambda self: True
            v6_build.ModuleBuildLock.release = lambda self: None

            def fake_check(*args, **kwargs):
                time.sleep(0.3)
                return True

            def fake_generate_index(*args, **kwargs):
                time.sleep(0.3)
                return None

            v6_build.step_check = fake_check
            orch_index.generate_index = fake_generate_index
            sys.argv = ["v6_build.py", "a2", "1", "--step", "check", "--writer", "gemini"]
            v6_build.main()
            """
        ).strip()
        + "\n",
        "utf-8",
    )

    proc = subprocess.Popen(
        [str(v6_build.PROJECT_ROOT / ".venv" / "bin" / "python"), str(helper_path), str(curriculum_root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    assert proc.stdout is not None

    first_line = proc.stdout.readline().strip()
    assert first_line.startswith("{\"event\"")
    first_event = json.loads(first_line)
    assert first_event["event"] == "module_start"
    assert proc.poll() is None

    second_event = None
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        stripped = line.strip()
        if stripped.startswith("{\"event\""):
            event = json.loads(stripped)
            if event["event"] == "phase_done":
                second_event = event
                break

    assert second_event is not None
    assert second_event["phase"] == "check"
    assert proc.poll() is None

    stdout, stderr = proc.communicate(timeout=5)
    assert proc.returncode == 0, stderr
    remaining_events = _event_lines(stdout)
    assert not any(event["event"] == "module_done" for event in remaining_events)
