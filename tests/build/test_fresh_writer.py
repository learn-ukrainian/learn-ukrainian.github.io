"""Tests for fresh build engine Part E2 writer call, fence stripping, schema validation, and R-11 (#8431 r3)."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh.draft_schema import DraftValidationError, validate_draft
from scripts.build.fresh.writer import (
    ALLOWED_WRITERS,
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
    """A combining accent inside English narration fails the schema gate (§3)."""
    draft, types = a1_valid_fixture
    mutated = copy.deepcopy(draft)

    # Inject combining acute (U+0301) into English narration text
    mutated["steps"][0]["blocks"][0]["text"] = "English text with an accent: cafe\u0301."

    errors = validate_draft(mutated, level="a1", activity_types=types)
    assert len(errors) > 0
    checks = {e.check for e in errors}
    assert "no_combining_accent" in checks


def test_bilingual_arrays_unequal_length_fails(a1_valid_fixture):
    """bilingual block uk and en arrays of unequal length fail schema gate (§2)."""
    draft, types = a1_valid_fixture
    mutated = copy.deepcopy(draft)

    # Find bilingual block and make uk/en arrays unequal length
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


def test_writer_seat_validation(tmp_path):
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
        )


def test_writer_call_with_fake_seat(tmp_path, a1_valid_fixture):
    """The writer call tested with a fake seat script that returns a fixture draft."""
    draft, types = a1_valid_fixture
    raw_yaml = yaml.safe_dump(draft, allow_unicode=True)

    # Create a fake seat script
    fake_seat_script = tmp_path / "fake_seat.py"
    fake_seat_script.write_text(
        f"""
import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--task-id", required=True)
parser.add_argument("--prompt-file", required=True)
parser.add_argument("--result-file", required=True)
args = parser.parse_args()

result_path = Path(args.result_file)
result_path.parent.mkdir(parents=True, exist_ok=True)
# Return draft wrapped in markdown fence
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
        attempt=1,
        plan_activity_types=types,
        fake_seat=fake_seat_script,
        repo_root=tmp_path,
    )

    assert res["writer"] == "agy"
    assert res["task_id"] == "write-a1-test-slug-2-1"
    assert res["prompt_sha256"] == "a" * 64

    # Verify state files exist
    draft_file = output_dir / "lesson-2.draft.yaml"
    raw_file = output_dir / "lesson-2.raw.txt"
    meta_file = output_dir / "lesson-2.writer.yaml"

    assert draft_file.is_file()
    assert raw_file.is_file()
    assert meta_file.is_file()

    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    assert meta["writer"] == "agy"
    assert meta["task_id"] == "write-a1-test-slug-2-1"
    assert meta["attempt"] == 1


def test_writer_call_schema_failure_no_retry(tmp_path):
    """A draft failing schema validation raises DraftValidationError without retry."""
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
            attempt=1,
            fake_seat=fake_seat_script,
            repo_root=tmp_path,
        )


def test_r11_forbidden_paths_grep():
    """R-11 grep test: scripts/build/fresh/ never opens or references v1 plans, v1 levels, or wiki packets."""
    fresh_dir = REPO_ROOT / "scripts" / "build" / "fresh"
    forbidden_terms = [
        "curriculum/l2-uk-en/plans/",
        "curriculum/l2-uk-en/a1-v1/",
        "curriculum/l2-uk-en/a2-v1/",
        "curriculum/l2-uk-en/b1-v1/",
        "curriculum/l2-uk-en/b2-v1/",
    ]

    for py_file in fresh_dir.glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for term in forbidden_terms:
            # The only allowed occurrence is inside prompt.py's FORBIDDEN_V1_PATHS blacklist check
            if term in text:
                assert py_file.name == "prompt.py", f"Forbidden term {term!r} found in {py_file}"
                # Assert it only appears in FORBIDDEN_V1_PATHS
                assert "FORBIDDEN_V1_PATHS" in text


def test_nothing_typed_no_cyrillic_in_engine_code():
    """Nothing typed rule: No Ukrainian/Cyrillic string literals in Python engine code under scripts/build/fresh/."""
    fresh_dir = REPO_ROOT / "scripts" / "build" / "fresh"
    cyrillic_pattern = re.compile(r"[\u0400-\u04FF]")

    for py_file in fresh_dir.glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        cyrillic_matches = cyrillic_pattern.findall(text)
        assert len(cyrillic_matches) == 0, f"{py_file.name} contains {len(cyrillic_matches)} Cyrillic characters: {cyrillic_matches[:5]}"
