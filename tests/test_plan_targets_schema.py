import importlib.util
import sys
from pathlib import Path

import yaml

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "migrations"
    / "2026-05-13-add-plan-targets.py"
)
SPEC = importlib.util.spec_from_file_location("add_plan_targets", SCRIPT_PATH)
add_plan_targets = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = add_plan_targets
SPEC.loader.exec_module(add_plan_targets)


def test_valid_plan_targets_block_parses():
    plan = {
        "targets": {
            "new_vocabulary": ["кіт", "мама"],
            "new_grammar": ["Це + іменник"],
            "recycle_vocabulary": ["так"],
        }
    }

    targets = add_plan_targets.PlanTargets.from_plan(plan)

    assert targets.new_vocabulary == ["кіт", "мама"]
    assert targets.new_grammar == ["Це + іменник"]
    assert targets.recycle_vocabulary == ["так"]


def test_plan_without_targets_falls_back_to_vocabulary_hints_required():
    plan = {"vocabulary_hints": {"required": ["кіт (cat)", "Добрий день (hello) — chunk"]}}

    targets = add_plan_targets.PlanTargets.from_plan(plan)

    assert targets.new_vocabulary == ["кіт", "Добрий день"]


def test_migration_dry_run_prints_expected_diff(tmp_path, capsys):
    path = tmp_path / "plan.yaml"
    path.write_text(
        "module: a1-999\n"
        "vocabulary_hints:\n"
        "  required:\n"
        "  - кіт (cat)\n"
        "activity_hints: []\n",
        encoding="utf-8",
    )

    changed = add_plan_targets.process_path(path, dry_run=True)
    output = capsys.readouterr().out

    assert changed is True
    assert "+targets:" in output
    assert "+  new_vocabulary:" in output
    assert '+    - "кіт"' in output
    assert path.read_text(encoding="utf-8").startswith("module: a1-999")


def test_migration_writes_atomically_and_preserves_key_order(tmp_path):
    path = tmp_path / "plan.yaml"
    path.write_text(
        "module: a1-999\n"
        "vocabulary_hints:\n"
        "  required:\n"
        "  - мама (mother)\n"
        "activity_hints: []\n",
        encoding="utf-8",
    )

    changed = add_plan_targets.process_path(path, dry_run=False)
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    assert changed is True
    assert data["targets"]["new_vocabulary"] == ["мама"]
    assert list(data).index("targets") == list(data).index("vocabulary_hints") + 1
    assert list(data).index("activity_hints") == list(data).index("targets") + 1
    assert not list(tmp_path.glob("*.tmp"))
