"""Reachability checks for task-scoped instruction and fragile mode routing."""
import re
import shlex
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


def test_rollover_archive_only_route_contains_native_result_and_reconciliation() -> None:
    archive = (SKILLS / "thread-rollover/references/archive.md").read_text()
    for command in ("native-action", "record-native-result", "reconcile-native"):
        assert command in archive
    for boundary in ("--action archive", "--succeeded", "--failed", "readback is pending"):
        assert boundary in archive
    assert "exactly as for title" not in archive


def test_rollover_resume_routes_pending_native_prerequisite_without_new_replacement() -> None:
    reference = SKILLS / "thread-rollover/references/resume.md"
    body = reference.read_text()
    assert "[preparation](prepare.md)" in body
    assert "never create another replacement" in body
    prepare = reference.parent / "prepare.md"
    assert prepare.is_file()
    for command in ("record-native-result", "reconcile-native", "bind-replacement"):
        assert command in prepare.read_text()


def test_workflow_monitor_reference_resolves_from_canonical_source() -> None:
    workflow = ROOT / "agents_extensions/shared/rules/workflow.md"
    body = workflow.read_text()
    target = re.search(r"\[\x60docs/MONITOR-API.md\x60\]\(([^)]+)\)", body)
    assert target is not None
    assert (workflow.parent / target[1]).resolve() == ROOT / "docs/MONITOR-API.md"
    assert (workflow.parent / target[1]).is_file()



def test_documented_archive_failure_command_parses_with_real_cli() -> None:
    from scripts.orchestration.thread_handoff import build_parser

    text = (SKILLS / "thread-rollover/references/archive.md").read_text()
    blocks = re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
    failures = [block for block in blocks if "record-native-result" in block and "--failed" in block]
    assert len(failures) == 1
    command = failures[0].replace("\\\n", " ").strip()
    substitutions = {
        "<lineage-id>": "codex-test-lineage",
        "<rollover-id>": "rollover-test-archive",
        "<actual native failure>": "Native archive returned an error",
        "<tool-backed evidence of the attempted archive and its failure>": "set_thread_archived returned error for the exact predecessor",
    }
    for placeholder, value in substitutions.items():
        command = command.replace(placeholder, value)
    words = shlex.split(command)
    assert words[:2] == [".venv/bin/python", "scripts/orchestration/thread_handoff.py"]
    arguments = build_parser().parse_args(words[2:])
    assert arguments.action == "archive"
    assert arguments.succeeded is False
    assert arguments.error == substitutions["<actual native failure>"]
    assert arguments.evidence == substitutions["<tool-backed evidence of the attempted archive and its failure>"]
