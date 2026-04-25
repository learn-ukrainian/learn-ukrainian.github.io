from __future__ import annotations

import re
import sys
from importlib import import_module
from pathlib import Path

import yaml

WORKTREE_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = WORKTREE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

config_tables = import_module("pipeline.config_tables")

PROMPT_PATH = SCRIPTS_DIR / "build" / "phases" / "v6-activities.md"
PLAN_PATH = (
    WORKTREE_ROOT
    / "curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml"
)

ALPHABET = tuple("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ")

def _assemble_prompt(tmp_path: Path, markers: tuple[str, ...] = ("quiz-one", "fill-two", "match-three")) -> str:
    del tmp_path
    marker_count = len(markers)
    activity_config = config_tables.get_activity_config("a1", 1, slug="test-module")
    markers_text = "\n".join(
        f"- `<!-- INJECT_ACTIVITY: {marker} -->`" for marker in markers
    )
    prompt = PROMPT_PATH.read_text("utf-8")
    replacements = {
        "{MODULE_NUM}": "1",
        "{TOPIC_TITLE}": "Test Module",
        "{LEVEL}": "a1",
        "{MODULE_SLUG}": "test-module",
        "{INJECTION_MARKERS}": markers_text,
        "{PLAN_ACTIVITY_HINTS}": "- type: quiz\n  focus: test",
        "{PLAN_VOCABULARY}": "required:\n- звук\n- літера",
        "{MODULE_CONTENT}": "## Test\n\nзвук літера мама",
        "{TOOL_INSTRUCTIONS}": "",
        "{LEVEL_CONTEXT}": "",
        "{PEDAGOGY_PATTERNS}": "",
        "{LETTER_MODULE_ACTIVE}": "true",
        "{SEMINAR_TYPE_REFERENCE}": "",
        "{ITEM_MINIMUMS_TABLE}": "",
        "{TOTAL_TARGET}": activity_config["TOTAL_TARGET"],
        "{INLINE_MIN}": str(marker_count),
        "{INLINE_MAX}": str(marker_count),
        "{WORKBOOK_MIN}": activity_config["WORKBOOK_MIN"],
        "{WORKBOOK_MAX}": activity_config["WORKBOOK_MAX"],
        "{INLINE_ALLOWED_TYPES}": activity_config["INLINE_ALLOWED_TYPES"],
        "{WORKBOOK_ALLOWED_TYPES}": activity_config["WORKBOOK_ALLOWED_TYPES"],
        "{INLINE_PRIORITY_TYPES}": activity_config["INLINE_PRIORITY_TYPES"],
        "{WORKBOOK_PRIORITY_TYPES}": activity_config["WORKBOOK_PRIORITY_TYPES"],
        "{ITEMS_MIN}": activity_config["ITEMS_MIN"],
        "{MIN_TYPES_UNIQUE}": "4",
        "{VOCAB_COUNT_TARGET}": activity_config["VOCAB_COUNT_TARGET"],
        "{FORBIDDEN_ACTIVITY_TYPES}": activity_config["FORBIDDEN_ACTIVITY_TYPES"],
        "{ALLOWED_ACTIVITY_TYPES}": activity_config["ALLOWED_ACTIVITY_TYPES"],
        "{REQUIRED_TYPES}": activity_config["REQUIRED_TYPES"],
        "{ACTIVITY_COUNT_TARGET}": activity_config["TOTAL_TARGET"],
        "{PRIORITY_TYPES}": activity_config["PRIORITY_TYPES"],
    }
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)
    return prompt


def _split_types(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def test_prompt_forbidden_and_recommended_lists_are_disjoint(tmp_path: Path) -> None:
    prompt = _assemble_prompt(tmp_path)
    forbidden = _split_types(re.search(r"FORBIDDEN at this level:\*\* (.+)", prompt).group(1))
    inline_priority = _split_types(re.search(r"Inline priority \(preferred\):\*\* (.+)", prompt).group(1))
    workbook_priority = _split_types(re.search(r"Workbook priority \(preferred\):\*\* (.+)", prompt).group(1))

    assert forbidden.isdisjoint(inline_priority)
    assert forbidden.isdisjoint(workbook_priority)


def test_non_seminar_prompt_omits_seminar_type_reference(tmp_path: Path) -> None:
    prompt = _assemble_prompt(tmp_path)

    assert "### Seminar types" not in prompt
    assert "- **critical-analysis**: Required: id, prompt" not in prompt


def test_type_diversity_substitutes_positive_integer(tmp_path: Path) -> None:
    prompt = _assemble_prompt(tmp_path)

    assert "{MIN_TYPES_UNIQUE}" not in prompt
    match = re.search(r"at least \*\*(\d+)\*\* distinct activity types", prompt)
    assert match is not None
    assert int(match.group(1)) > 0


def test_inline_min_and_max_match_marker_count(tmp_path: Path) -> None:
    prompt = _assemble_prompt(tmp_path, markers=("one", "two", "three", "four"))
    build_source = (SCRIPTS_DIR / "build" / "v6_build.py").read_text("utf-8")

    match = re.search(r"\| Inline \(lesson tab\) \| (\d+) \| (\d+) \|", prompt)
    assert match is not None
    assert match.groups() == ("4", "4")
    assert "Inline activity count: exactly 4" in prompt
    assert "inline_min = inline_max = str(marker_count)" in build_source


def test_new_grounding_and_vocab_blocks_present_in_template() -> None:
    prompt = PROMPT_PATH.read_text("utf-8")

    for block in ("required-vocab-coverage", "strict-grounding", "letter-module-exception"):
        assert prompt.count(f"<{block}>") == 1
        assert prompt.count(f"</{block}>") == 1


def test_a1_1_plan_has_letter_module_alphabet_vocab_and_key_words() -> None:
    plan = yaml.safe_load(PLAN_PATH.read_text("utf-8"))
    recommended = plan["vocabulary_hints"]["recommended"]
    letter_entries = {
        item["word"]: item["key_word"]
        for item in recommended
        if isinstance(item, dict) and "word" in item and "key_word" in item
    }

    assert plan["letter_module"] is True
    assert tuple(letter_entries) == ALPHABET
    assert all(letter_entries[letter] for letter in ALPHABET)
