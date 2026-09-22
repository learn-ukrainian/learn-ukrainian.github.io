"""Tests for fresh build engine Part E2 writer call, fence stripping, schema validation, and R-11 (#8431 r3)."""

from __future__ import annotations

import copy
import json
import re
import stat
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh.draft_schema import DraftValidationError, validate_draft
from scripts.build.fresh.preflight import PreflightResult
from scripts.build.fresh.writer import (
    WriterCallError,
    dispatch_writer,
    parse_and_validate_reply,
    strip_markdown_fence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures" / "fresh"


@pytest.fixture
def a1_valid_fixture():
    draft = yaml.safe_load((FIXTURES / "lesson-draft-a1-valid.yaml").read_text(encoding="utf-8"))
    types = json.loads((FIXTURES / "lesson-draft-a1-types.json").read_text(encoding="utf-8"))
    return draft, types


@pytest.fixture
def passing_preflight():
    return PreflightResult(passed=True, status="ok", gaps=[], homographs=[], homograph_count=0)


def test_strip_markdown_fence(a1_valid_fixture):
    """Strip surrounding markdown code fence if present (with or without 'yaml' tag)."""
    draft, _ = a1_valid_fixture
    raw_yaml = yaml.safe_dump(draft, allow_unicode=True)

    # 1. Without fence
    assert strip_markdown_fence(raw_yaml) == raw_yaml.strip()

    # 2. With ```yaml ... ``` fence
    fenced_yaml = f"```yaml\n{raw_yaml}\n```"
    assert strip_markdown_fence(fenced_yaml) == raw_yaml.strip()

    # 3. With plain ``` ... ``` fence
    fenced_plain = f"```\n{raw_yaml}\n```"
    assert strip_markdown_fence(fenced_plain) == raw_yaml.strip()

    # 4. With surrounding whitespace
    fenced_ws = f"  \n```yaml\n{raw_yaml}\n```\n  "
    assert strip_markdown_fence(fenced_ws) == raw_yaml.strip()


def test_parse_and_validate_reply_success(a1_valid_fixture):
    """parse_and_validate_reply strips fence, parses YAML, and validates against draft schema."""
    draft, types = a1_valid_fixture
    raw_yaml = yaml.safe_dump(draft, allow_unicode=True)
    fenced_reply = f"```yaml\n{raw_yaml}\n```"

    parsed = parse_and_validate_reply(fenced_reply, level="a1", plan_activity_types=types)
    assert parsed["draft_schema"] == 1
    assert parsed["status"] == "ok"


def test_combining_accent_in_english_narration_fails(a1_valid_fixture):
    """A combining accent inside English narration fails the schema gate (§3, Finding 12)."""
    draft, types = a1_valid_fixture
    assert validate_draft(draft, level="a1", activity_types=types) == []

    mutated = copy.deepcopy(draft)

    # Inject combining acute (U+0301) into English narration text
    accented_text = "English text with an accent: cafe\u0301."
    mutated["steps"][0]["blocks"][0]["text"] = accented_text

    errors = validate_draft(mutated, level="a1", activity_types=types)
    assert len(errors) == 1
    err = errors[0]
    # The E1 draft schema rejects U+0300/U+0301 via regex pattern at the schema layer (Finding 12)
    assert err.check == "schema"
    assert err.path == "/steps/0/blocks/0"
    assert accented_text in err.reason


def test_bilingual_arrays_unequal_length_fails(a1_valid_fixture):
    """bilingual block uk and en arrays of unequal length fail schema gate (§2)."""
    draft, types = a1_valid_fixture
    mutated = copy.deepcopy(draft)

    found = False
    for step in mutated["steps"]:
        for block in step.get("blocks", []):
            if block.get("kind") == "bilingual":
                block["en"] = ["Only one English line"]
                block["uk"] = ["First Ukrainian line", "Second Ukrainian line"]
                found = True
                break
        if found:
            break
    assert found is True

    errors = validate_draft(mutated, level="a1", activity_types=types)
    assert len(errors) > 0
    checks = {e.check for e in errors}
    assert "bilingual_equal_length" in checks


def test_writer_seat_validation(tmp_path, passing_preflight):
    """The writer seat must be explicitly one of {claude, codex, agy, grok}."""
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid writer 'unknown_seat'"):
        dispatch_writer(
            writer="unknown_seat",
            level="a1",
            slug="mod-1",
            lesson_n=1,
            prompt_file=prompt_file,
            prompt_sha256="0" * 64,
            output_dir=tmp_path / "out",
            preflight_result=passing_preflight,
        )


def test_dispatch_refuses_without_passing_preflight(tmp_path):
    """Finding 4: dispatch_writer structurally refuses unless preflight passed."""
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    failed_pre = PreflightResult(passed=False, status="evidence_gap", gaps=[], homographs=[], homograph_count=0)
    with pytest.raises(WriterCallError, match="preflight verification did not pass"):
        dispatch_writer(
            writer="agy",
            level="a1",
            slug="mod-1",
            lesson_n=1,
            prompt_file=prompt_file,
            prompt_sha256="0" * 64,
            output_dir=tmp_path / "out",
            preflight_result=failed_pre,
        )

    with pytest.raises(WriterCallError, match="preflight verification did not pass"):
        dispatch_writer(
            writer="agy",
            level="a1",
            slug="mod-1",
            lesson_n=1,
            prompt_file=prompt_file,
            prompt_sha256="0" * 64,
            output_dir=tmp_path / "out",
            preflight_result=None,
        )


def test_writer_call_with_fake_seat(tmp_path, a1_valid_fixture, passing_preflight):
    """The writer call tested with a fake seat script that returns a fixture draft."""
    draft, types = a1_valid_fixture
    raw_yaml = yaml.safe_dump(draft, allow_unicode=True)

    fake_seat_script = tmp_path / "fake_seat.py"
    fake_seat_script.write_text(
        f"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--task-id", required=True)
parser.add_argument("--prompt-file", required=True)
parser.add_argument("--result-file", required=True)
args = parser.parse_args()

result_path = Path(args.result_file)
result_path.parent.mkdir(parents=True, exist_ok=True)
result_path.write_text('''```yaml
{raw_yaml}
```''', encoding="utf-8")
""",
        encoding="utf-8",
    )

    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Test prompt content", encoding="utf-8")
    output_dir = tmp_path / "out_state"

    res = dispatch_writer(
        writer="agy",
        level="a1",
        slug="test-slug",
        lesson_n=2,
        prompt_file=prompt_file,
        prompt_sha256="a" * 64,
        output_dir=output_dir,
        preflight_result=passing_preflight,
        attempt=1,
        plan_activity_types=types,
        fake_seat=fake_seat_script,
        repo_root=tmp_path,
    )

    assert res["writer"] == "agy"
    assert res["task_id"] == "write-a1-test-slug-2-1"
    assert res["prompt_sha256"] == "a" * 64
    assert res["model"] == "gemini-3.8-flash-high"

    # Verify state files exist and file permissions are 0o644
    draft_file = output_dir / "lesson-2.draft.yaml"
    raw_file = output_dir / "lesson-2.raw.txt"
    meta_file = output_dir / "lesson-2.writer.yaml"

    assert draft_file.is_file()
    assert raw_file.is_file()
    assert meta_file.is_file()
    assert stat.S_IMODE(raw_file.stat().st_mode) == 0o644
    assert stat.S_IMODE(meta_file.stat().st_mode) == 0o644

    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert meta["writer"] == "agy"
    assert meta["model"] == "gemini-3.8-flash-high"
    assert meta["task_id"] == "write-a1-test-slug-2-1"
    assert meta["attempt"] == 1


def test_writer_call_schema_failure_saves_provenance(tmp_path, passing_preflight):
    """Finding 11: When schema validation fails, raw reply and writer metadata are still saved."""
    fake_seat_script = tmp_path / "fake_seat_invalid.py"
    fake_seat_script.write_text(
        """
import argparse
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument("--task-id", required=True)
parser.add_argument("--prompt-file", required=True)
parser.add_argument("--result-file", required=True)
args = parser.parse_args()
Path(args.result_file).write_text("invalid_draft: true\\nstatus: ok\\n", encoding="utf-8")
""",
        encoding="utf-8",
    )

    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Test prompt", encoding="utf-8")
    output_dir = tmp_path / "out_state"

    with pytest.raises(DraftValidationError):
        dispatch_writer(
            writer="claude",
            level="a1",
            slug="test-slug",
            lesson_n=1,
            prompt_file=prompt_file,
            prompt_sha256="b" * 64,
            output_dir=output_dir,
            preflight_result=passing_preflight,
            attempt=1,
            fake_seat=fake_seat_script,
            repo_root=tmp_path,
        )

    # Finding 11: Even though validation failed, raw file and writer metadata MUST exist!
    raw_file = output_dir / "lesson-1.raw.txt"
    meta_file = output_dir / "lesson-1.writer.yaml"
    assert raw_file.is_file(), "raw reply must be preserved on schema validation failure"
    assert meta_file.is_file(), "writer metadata must be preserved on schema validation failure"
    assert stat.S_IMODE(raw_file.stat().st_mode) == 0o644
    assert stat.S_IMODE(meta_file.stat().st_mode) == 0o644

    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert meta["writer"] == "claude"
    assert meta["model"] == "claude-sonnet-5"


def test_real_dispatch_path_with_fake_delegate(tmp_path, a1_valid_fixture, passing_preflight):
    """Finding 7: Test the real dispatch path through fake delegate.py, checking argv, wait, and status."""
    draft, types = a1_valid_fixture
    raw_yaml = yaml.safe_dump(draft, allow_unicode=True)

    calls_log = tmp_path / "delegate_calls.jsonl"
    fake_delegate_script = tmp_path / "fake_delegate.py"

    fake_delegate_script.write_text(
        f"""
import json
import sys
from pathlib import Path

repo_root = Path({str(tmp_path)!r})
calls_log = Path({str(calls_log)!r})

argv = sys.argv[1:]
with open(calls_log, "a", encoding="utf-8") as f:
    f.write(json.dumps({{"argv": argv}}) + "\\n")

cmd = argv[0] if argv else ""
if cmd == "dispatch":
    # Parse task-id
    task_id = argv[argv.index("--task-id") + 1]
    task_state = repo_root / f"batch_state/tasks/{{task_id}}.json"
    task_state.parent.mkdir(parents=True, exist_ok=True)
    task_state.write_text(json.dumps({{"task_id": task_id, "status": "running", "model": "test-delegate-model"}}), encoding="utf-8")
    sys.exit(0)

elif cmd == "wait":
    task_id = argv[1]
    task_state = repo_root / f"batch_state/tasks/{{task_id}}.json"
    result_file = repo_root / f"batch_state/tasks/{{task_id}}.result"
    result_file.parent.mkdir(parents=True, exist_ok=True)
    result_file.write_text('''```yaml
{raw_yaml}
```''', encoding="utf-8")
    task_state.write_text(json.dumps({{"task_id": task_id, "status": "done", "resolved_model": "gpt-6-astra"}}), encoding="utf-8")
    sys.exit(0)

sys.exit(1)
""",
        encoding="utf-8",
    )

    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Test prompt for delegate", encoding="utf-8")
    output_dir = tmp_path / "out_state"

    res = dispatch_writer(
        writer="codex",
        level="a1",
        slug="delegate-test",
        lesson_n=3,
        prompt_file=prompt_file,
        prompt_sha256="c" * 64,
        output_dir=output_dir,
        preflight_result=passing_preflight,
        attempt=1,
        plan_activity_types=types,
        delegate_script=fake_delegate_script,
        repo_root=tmp_path,
    )

    assert res["writer"] == "codex"
    assert res["model"] == "gpt-6-astra"

    # Assert argument lists recorded
    lines = [json.loads(line) for line in calls_log.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 2, f"Expected 2 delegate calls (dispatch and wait), got {len(lines)}"

    dispatch_argv = lines[0]["argv"]
    assert dispatch_argv[0] == "dispatch"
    assert "--agent" in dispatch_argv and dispatch_argv[dispatch_argv.index("--agent") + 1] == "codex"
    assert "--mode" in dispatch_argv and dispatch_argv[dispatch_argv.index("--mode") + 1] == "read-only"
    assert "--worktree" in dispatch_argv
    assert (
        "--task-id" in dispatch_argv
        and dispatch_argv[dispatch_argv.index("--task-id") + 1] == "write-a1-delegate-test-3-1"
    )
    assert "--prompt-file" in dispatch_argv and dispatch_argv[dispatch_argv.index("--prompt-file") + 1] == str(
        prompt_file
    )
    assert "--research-role" in dispatch_argv and dispatch_argv[dispatch_argv.index("--research-role") + 1] == "writer"

    wait_argv = lines[1]["argv"]
    assert wait_argv[0] == "wait"
    assert wait_argv[1] == "write-a1-delegate-test-3-1"
    assert "--timeout" in wait_argv


def test_real_dispatch_path_wait_failure(tmp_path, a1_valid_fixture, passing_preflight):
    """Finding 7: dispatch_writer fails when wait reports non-zero exit code or non-done status."""
    fake_delegate_script = tmp_path / "fake_delegate_failing.py"
    fake_delegate_script.write_text(
        """
import sys
cmd = sys.argv[1] if len(sys.argv) > 1 else ""
if cmd == "dispatch":
    sys.exit(0)
elif cmd == "wait":
    sys.exit(1)
sys.exit(1)
""",
        encoding="utf-8",
    )

    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Test prompt", encoding="utf-8")

    with pytest.raises(WriterCallError, match=r"delegate\.py wait failed"):
        dispatch_writer(
            writer="codex",
            level="a1",
            slug="delegate-fail",
            lesson_n=1,
            prompt_file=prompt_file,
            prompt_sha256="d" * 64,
            output_dir=tmp_path / "out",
            preflight_result=passing_preflight,
            delegate_script=fake_delegate_script,
            repo_root=tmp_path,
        )


def test_r11_forbidden_paths_grep():
    """R-11 grep test: scripts/build/fresh/ never opens or references v1 plans, v1 levels, or wiki packets (#8431, Finding 10)."""
    fresh_dir = REPO_ROOT / "scripts" / "build" / "fresh"
    forbidden_terms = [
        "curriculum/l2-uk-en/plans/",
        "curriculum/l2-uk-en/a1-v1/",
        "curriculum/l2-uk-en/a2-v1/",
        "curriculum/l2-uk-en/b1-v1/",
        "curriculum/l2-uk-en/b2-v1/",
        "curriculum/l2-uk-en/<level>-v1/",
        "wiki_packet",
        "wiki/packets",
    ]

    all_files = list(fresh_dir.glob("*.py")) + list(fresh_dir.glob("prompts/*.j2")) + list(fresh_dir.glob("*.yaml"))

    for fpath in all_files:
        text = fpath.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in text:
                assert fpath.name == "prompt.py", f"Forbidden term {term!r} found in {fpath}"
                # In prompt.py, forbidden terms may only appear in FORBIDDEN_V1_PATTERNS
                assert "FORBIDDEN_V1_PATTERNS" in text
                # Ensure no blanket exemption: count occurrences
                occurrences = text.count(term)
                assert occurrences <= 1, f"Term {term!r} occurs {occurrences} times in prompt.py"


def test_nothing_typed_no_cyrillic_in_engine_code():
    """Nothing typed rule: No Ukrainian/Cyrillic string literals in Python engine code or templates under scripts/build/fresh/ (#8431, Finding 10)."""
    fresh_dir = REPO_ROOT / "scripts" / "build" / "fresh"
    cyrillic_pattern = re.compile(r"[\u0400-\u04FF]")

    all_files = list(fresh_dir.glob("*.py")) + list(fresh_dir.glob("prompts/*.j2"))

    for fpath in all_files:
        text = fpath.read_text(encoding="utf-8")
        cyrillic_matches = cyrillic_pattern.findall(text)
        assert len(cyrillic_matches) == 0, (
            f"{fpath.name} contains {len(cyrillic_matches)} Cyrillic characters: {cyrillic_matches[:5]}"
        )
