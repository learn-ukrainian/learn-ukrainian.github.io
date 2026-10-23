"""Reachability checks for task-scoped instruction and fragile mode routing."""
import re
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "agents_extensions/shared/skills"



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
