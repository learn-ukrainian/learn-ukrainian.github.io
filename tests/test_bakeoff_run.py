from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.audit import bakeoff_run


def _completed(argv: list[str], returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout="", stderr="")


def _fake_runner(calls: list[list[str]], slug: str = "my-morning"):
    def run(argv: Any) -> subprocess.CompletedProcess[str]:
        command = [str(part) for part in argv]
        calls.append(command)
        script = Path(command[1]).name
        if script == "v7_build.py" and "--dry-run" not in command:
            out_dir = Path(command[command.index("--out") + 1])
            telemetry = Path(command[command.index("--telemetry-out") + 1])
            out_dir.mkdir(parents=True, exist_ok=True)
            telemetry.parent.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{slug}.mdx").write_text(
                "---\nlevel: A1\nslug: my-morning\n---\n\n# Мій ранок\n",
                encoding="utf-8",
            )
            with telemetry.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event": "phase_writer_summary"}) + "\n")
        elif script == "v7_review.py":
            telemetry = Path(command[command.index("--telemetry-out") + 1])
            telemetry.parent.mkdir(parents=True, exist_ok=True)
            with telemetry.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event": "phase_review_summary"}) + "\n")
        elif script == "bakeoff_aggregate.py":
            bakeoff_dir = Path(command[command.index("--bakeoff-dir") + 1])
            (bakeoff_dir / "REPORT.md").write_text("# Report\n", encoding="utf-8")
        return _completed(command)

    return run


def _plan_payload() -> dict[str, object]:
    return {
        "module": "a1-020",
        "level": "A1",
        "sequence": 20,
        "slug": "my-morning",
        "title": "Мій ранок",
        "subtitle": "Зворотні дієслова",
        "word_target": 1200,
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 1200,
                "points": ["Introduce a morning dialogue."],
            }
        ],
        "references": [{"title": "Fixture source"}],
    }


def test_bakeoff_run_invokes_write_and_review_steps_in_order(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[list[str]] = []
    bakeoff_dir = tmp_path / "bakeoff"
    monkeypatch.setattr(bakeoff_run, "run_command", _fake_runner(calls))

    exit_code = bakeoff_run.main(
        [
            "--bakeoff-dir",
            str(bakeoff_dir),
            "--level",
            "a1",
            "--slug",
            "my-morning",
            "--writers",
            "gemini-tools,claude-tools",
            "--skip-aggregate",
        ]
    )

    scripts = [Path(call[1]).name for call in calls]

    assert exit_code == 0
    assert scripts == [
        "v7_build.py",
        "v7_build.py",
        "v7_build.py",
        "v7_review.py",
        "v7_review.py",
    ]
    assert "--dry-run" in calls[0]
    assert calls[0][calls[0].index("--writer") + 1] == "gemini-tools"
    assert calls[1][calls[1].index("--writer") + 1] == "gemini-tools"
    assert calls[1][calls[1].index("--out") + 1] == str(bakeoff_dir / "gemini")
    assert calls[1][calls[1].index("--telemetry-out") + 1] == str(
        bakeoff_dir / "gemini.write.jsonl"
    )
    assert calls[3][calls[3].index("--content") + 1] == str(bakeoff_dir / "gemini.md")
    assert calls[3][calls[3].index("--reviewer") + 1] == "claude-tools"
    assert calls[4][calls[4].index("--content") + 1] == str(bakeoff_dir / "claude.md")
    assert calls[4][calls[4].index("--reviewer") + 1] == "gemini-tools"


@pytest.mark.parametrize(
    ("initial_jsonl", "expected_gemini_rerun"),
    [
        (json.dumps({"event": "phase_writer_summary"}) + "\n", False),
        (json.dumps({"event": "module_start"}) + "\n", True),
        (None, True),
        ("", True),
    ],
)
def test_bakeoff_run_resume_writer_requires_terminal_event(
    tmp_path: Path,
    monkeypatch,
    initial_jsonl: str | None,
    expected_gemini_rerun: bool,
) -> None:
    calls: list[list[str]] = []
    bakeoff_dir = tmp_path / "bakeoff"
    bakeoff_dir.mkdir()
    telemetry = bakeoff_dir / "gemini.write.jsonl"
    if initial_jsonl is not None:
        telemetry.write_text(initial_jsonl, encoding="utf-8")
    monkeypatch.setattr(bakeoff_run, "run_command", _fake_runner(calls))

    exit_code = bakeoff_run.main(
        [
            "--bakeoff-dir",
            str(bakeoff_dir),
            "--level",
            "a1",
            "--slug",
            "my-morning",
            "--writers",
            "gemini-tools,claude-tools",
            "--resume",
            "--writers-only",
            "--skip-aggregate",
        ]
    )

    full_build_writers = [
        call[call.index("--writer") + 1]
        for call in calls
        if Path(call[1]).name == "v7_build.py" and "--dry-run" not in call
    ]

    assert exit_code == 0
    assert ("gemini-tools" in full_build_writers) is expected_gemini_rerun
    assert "claude-tools" in full_build_writers
    if expected_gemini_rerun:
        assert telemetry.read_text(encoding="utf-8") == (
            json.dumps({"event": "phase_writer_summary"}) + "\n"
        )
    else:
        assert full_build_writers == ["claude-tools"]


@pytest.mark.parametrize(
    ("initial_jsonl", "expected_gemini_claude_rerun"),
    [
        (json.dumps({"event": "phase_review_summary"}) + "\n", False),
        (json.dumps({"event": "module_start"}) + "\n", True),
        (None, True),
        ("", True),
    ],
)
def test_bakeoff_run_resume_review_requires_terminal_event(
    tmp_path: Path,
    monkeypatch,
    initial_jsonl: str | None,
    expected_gemini_claude_rerun: bool,
) -> None:
    calls: list[list[str]] = []
    bakeoff_dir = tmp_path / "bakeoff"
    bakeoff_dir.mkdir()
    (bakeoff_dir / "gemini.md").write_text("# Gemini module\n", encoding="utf-8")
    (bakeoff_dir / "claude.md").write_text("# Claude module\n", encoding="utf-8")
    telemetry = bakeoff_dir / "gemini-claude.review.jsonl"
    if initial_jsonl is not None:
        telemetry.write_text(initial_jsonl, encoding="utf-8")
    monkeypatch.setattr(bakeoff_run, "run_command", _fake_runner(calls))

    exit_code = bakeoff_run.main(
        [
            "--bakeoff-dir",
            str(bakeoff_dir),
            "--level",
            "a1",
            "--slug",
            "my-morning",
            "--writers",
            "gemini-tools,claude-tools",
            "--resume",
            "--reviewers-only",
            "--skip-aggregate",
        ]
    )

    review_pairs = [
        (
            Path(call[call.index("--content") + 1]).name,
            call[call.index("--reviewer") + 1],
        )
        for call in calls
        if Path(call[1]).name == "v7_review.py"
    ]

    assert exit_code == 0
    assert (("gemini.md", "claude-tools") in review_pairs) is expected_gemini_claude_rerun
    assert ("claude.md", "gemini-tools") in review_pairs
    if expected_gemini_claude_rerun:
        assert telemetry.read_text(encoding="utf-8") == (
            json.dumps({"event": "phase_review_summary"}) + "\n"
        )


def test_bakeoff_run_writer_timeout_continues_next_writer(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    calls: list[list[str]] = []
    bakeoff_dir = tmp_path / "bakeoff"

    def run(argv: Any) -> subprocess.CompletedProcess[str]:
        command = [str(part) for part in argv]
        calls.append(command)
        script = Path(command[1]).name
        if script == "v7_build.py" and "--dry-run" not in command:
            writer = command[command.index("--writer") + 1]
            if writer == "gemini-tools":
                return subprocess.CompletedProcess(
                    command,
                    124,
                    stdout="",
                    stderr="writer_timeout",
                )
            out_dir = Path(command[command.index("--out") + 1])
            telemetry = Path(command[command.index("--telemetry-out") + 1])
            out_dir.mkdir(parents=True, exist_ok=True)
            telemetry.parent.mkdir(parents=True, exist_ok=True)
            (out_dir / "my-morning.mdx").write_text("# Мій ранок\n", encoding="utf-8")
            telemetry.write_text(
                json.dumps({"event": "phase_writer_summary"}) + "\n",
                encoding="utf-8",
            )
        return _completed(command)

    monkeypatch.setattr(bakeoff_run, "run_command", run)

    exit_code = bakeoff_run.main(
        [
            "--bakeoff-dir",
            str(bakeoff_dir),
            "--level",
            "a1",
            "--slug",
            "my-morning",
            "--writers",
            "gemini-tools,claude-tools",
            "--writers-only",
            "--skip-aggregate",
        ]
    )

    captured = capsys.readouterr()
    full_build_writers = [
        call[call.index("--writer") + 1]
        for call in calls
        if Path(call[1]).name == "v7_build.py" and "--dry-run" not in call
    ]

    assert exit_code == 1
    assert full_build_writers == ["gemini-tools", "claude-tools"]
    assert "timeout: writer_timeout" in captured.err


def test_bakeoff_run_preflight_missing_plan_exits_1(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        bakeoff_run.linear_pipeline,
        "plan_path_for",
        lambda _level, _slug: tmp_path / "missing.yaml",
    )
    monkeypatch.setattr(
        bakeoff_run,
        "run_command",
        lambda _argv: (_ for _ in ()).throw(AssertionError("runner called")),
    )

    exit_code = bakeoff_run.main(
        [
            "--bakeoff-dir",
            str(tmp_path / "bakeoff"),
            "--level",
            "a1",
            "--slug",
            "my-morning",
            "--writers",
            "gemini-tools",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "missing plan" in captured.err


def test_bakeoff_run_preflight_missing_packet_exits_1(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(bakeoff_run.linear_pipeline, "_wiki_article_paths", lambda *_args: [])
    monkeypatch.setattr(
        bakeoff_run,
        "run_command",
        lambda _argv: (_ for _ in ()).throw(AssertionError("runner called")),
    )

    exit_code = bakeoff_run.main(
        [
            "--bakeoff-dir",
            str(tmp_path / "bakeoff"),
            "--level",
            "a1",
            "--slug",
            "my-morning",
            "--writers",
            "gemini-tools",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "missing wiki packet" in captured.err


def test_bakeoff_run_preflight_unknown_writer_exits_1(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        bakeoff_run,
        "run_command",
        lambda _argv: (_ for _ in ()).throw(AssertionError("runner called")),
    )

    exit_code = bakeoff_run.main(
        [
            "--bakeoff-dir",
            str(tmp_path / "bakeoff"),
            "--level",
            "a1",
            "--slug",
            "my-morning",
            "--writers",
            "bogus-tools",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unknown writer" in captured.err


def test_bakeoff_run_aggregate_gets_normalized_writer_list(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[list[str]] = []
    bakeoff_dir = tmp_path / "bakeoff"
    monkeypatch.setattr(bakeoff_run, "run_command", _fake_runner(calls))

    exit_code = bakeoff_run.main(
        [
            "--bakeoff-dir",
            str(bakeoff_dir),
            "--level",
            "a1",
            "--slug",
            "my-morning",
            "--writers",
            "gemini-tools,codex-tools,claude-tools",
            "--writers-only",
        ]
    )

    aggregate_call = next(call for call in calls if Path(call[1]).name == "bakeoff_aggregate.py")

    assert exit_code == 0
    assert aggregate_call[aggregate_call.index("--writers") + 1] == "gemini,gpt55,claude"


def test_bakeoff_run_preflight_accepts_fixture_plan(
    tmp_path: Path,
    monkeypatch,
) -> None:
    plan_path = tmp_path / "my-morning.yaml"
    plan_path.write_text(yaml.safe_dump(_plan_payload()), encoding="utf-8")
    monkeypatch.setattr(
        bakeoff_run.linear_pipeline,
        "plan_path_for",
        lambda _level, _slug: plan_path,
    )
    monkeypatch.setattr(
        bakeoff_run.linear_pipeline,
        "_wiki_article_paths",
        lambda *_args: [tmp_path / "my-morning.md"],
    )

    assert bakeoff_run._preflight("a1", "my-morning", ["gemini-tools"]) == []
