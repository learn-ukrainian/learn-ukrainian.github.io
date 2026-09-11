"""Reachability checks for task-scoped instruction and fragile mode routing."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "agents_extensions/shared/skills"


def test_split_skill_references_are_reachable_from_their_entrypoint() -> None:
    for name in ("entire-context", "task-family-manager", "thread-rollover", "track-completion"):
        entry = SKILLS / name / "SKILL.md"
        links = re.findall(r"\]\((references/[^)]+)\)", entry.read_text())
        assert links, name
        for target in links:
            reference = entry.parent / target
            assert reference.is_file(), reference
            assert reference.read_text().strip(), reference
        assert set(links) == {str(p.relative_to(entry.parent)) for p in (entry.parent / "references").glob("*.md")}


def test_task_scope_selector_keeps_canonical_sources_and_phase_gates_reachable() -> None:
    selector = ROOT / "agents_extensions/shared/rules/task-scoped-reading.md"
    text = selector.read_text()
    for target in re.findall(r"`((?:agents_extensions|docs)/[^`]+\.md)`", text):
        if "<name>" in target:
            assert all((p / "SKILL.md").is_file() for p in SKILLS.iterdir() if p.is_dir())
        else:
            assert (ROOT / target).is_file(), target
    for consumer in (ROOT / "AGENTS.md", ROOT / "agents_extensions/shared/rules/_load-via-api.md",
                     ROOT / "agents_extensions/shared/rules/workflow.md"):
        assert "task-scoped-reading.md" in consumer.read_text()
    for required in ("operator-expectations.md", "critical-rules.md", "delegate-must-use-worktree.md",
                     "non-negotiable-rules.md", "model-assignment.md", "fleet-comms-coordination.md",
                     "cross-family", "required CI"):
        assert required in text


def test_task_family_native_inventory_does_not_bypass_planner_pin_precondition() -> None:
    entry = (SKILLS / "task-family-manager/SKILL.md").read_text()
    manifest = (SKILLS / "task-family-manager/references/manifest.md").read_text()
    assert "list_archived_threads" in entry
    assert "pinnedThreads" in entry
    assert "--confirm-pin-unknown <TASK_UUID>" in manifest
    assert "not a claim that the" in manifest
