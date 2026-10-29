"""Defect class: a full-command-line process kill can match its own shell."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("command", "refused"),
    [
        ("pkill -f worker", True),
        ("pkill --full worker", True),
        ("pkill -9 -f worker", True),
        ("pkill -TERM -fx worker", True),
        ("command /usr/bin/pkill -f worker", True),
        ("pgrep -f worker | kill", True),
        ("pgrep --full worker | xargs kill", True),
        ("pgrep -f worker | xargs -r -n 1 /bin/kill -TERM", True),
        ("pgrep -f worker | sort -u | xargs kill", True),
        ("kill $(pgrep -f worker)", True),
        ('kill "$(pgrep --full worker)"', True),
        ("kill `pgrep -f worker`", True),
        ("$(pkill -f worker)", True),
        ("bash -c 'pkill -f worker'", True),
        ('bash -c "kill $(pgrep -f worker)"', True),
        ("LEARN_UK_SECRETS_OK=1 pkill -f worker", True),
        ("pgrep -f worker", False),
        ("pgrep --full worker | sort", False),
        ("pgrep -f worker | xargs echo kill", False),
        ("pgrep -f worker; kill 12345", False),
        ("pkill worker", False),
        ("pkill -x worker", False),
        ("kill -TERM 12345 12346", False),
        ("pgrep worker | xargs kill", False),
        ("pkill -- -foo", False),
        ('echo "pkill -f worker; pgrep -f worker | xargs kill"', False),
        ("printf '%s\\n' 'kill $(pgrep -f worker)'", False),
        ('git commit -m "refuse pkill -f and pgrep --full | kill"', False),
        ("cat <<'EOF'\npkill -f worker\nkill $(pgrep -f worker)\nEOF", False),
        ("cat <<EOF\npkill -f worker\nEOF", False),
    ],
)
def test_self_matching_process_kill(command: str, refused: bool) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "agents_extensions/shared/hooks/guard-secret-print.py")],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        env={key: value for key, value in os.environ.items() if key != "LEARN_UK_SECRETS_OK"},
        timeout=10,
    )
    assert result.returncode == (2 if refused else 0), result.stderr
    if refused:
        assert "exact numeric PIDs read in an earlier command" in result.stderr
        assert "harness's own stop tool" in result.stderr
