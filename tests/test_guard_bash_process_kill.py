"""Defect class: a full-command-line process kill can match its own shell."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_secret_print_hook import ADAPTER, HARNESS_NAMES, assert_decision, event

ROOT = Path(__file__).resolve().parents[1]
ENV = {key: value for key, value in os.environ.items() if key != "LEARN_UK_SECRETS_OK"}
ALTERNATIVES = ("exact numeric PIDs read in an earlier command", "harness's own stop tool")


def nested_backticks(levels: int) -> str:
    """Backticks nested past the shared parser's depth limit."""
    body = ":"
    for _ in range(levels):
        body = "`" + body.replace("\\", "\\\\").replace("`", r"\`") + "`"
    return body


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
        ('pgrep -f worker | while read p; do kill "$p"; done', True),
        ('pgrep -f worker | while read -r; do kill "$REPLY"; done', True),
        ('for p in $(pgrep -f worker); do kill "$p"; done', True),
        ("pgrep -f worker | xargs sudo kill", True),
        ("pgrep -f worker | xargs env kill", True),
        ("pgrep -f worker | xargs -r timeout 5 kill", True),
        ("pgrep -f worker | xargs -I % sh -c 'kill %'", True),
        ("kill $(pgrep -f worker)", True),
        ('kill "$(pgrep --full worker)"', True),
        ("kill `pgrep -f worker`", True),
        ("$(pkill -f worker)", True),
        ("bash -c 'pkill -f worker'", True),
        ('bash -c "kill $(pgrep -f worker)"', True),
        ("LEARN_UK_SECRETS_OK=1 pkill -f worker", True),
        ('while read p; do kill "$p"; done < <(pgrep -f worker)', True),
        ('while read p; do kill "$p"; done <<< "$(pgrep -f worker)"', True),
        ('pgrep -f worker | { read p; kill "$p"; }', True),
        ('pgrep -f worker | (while read p; do kill "$p"; done)', True),
        ('if pgrep -fq worker; then for p in $(pgrep -f worker); do kill "$p"; done; fi', True),
        ("pids=$(pgrep -f worker); kill $pids", True),
        ('pid=$(pgrep -f worker) && kill "$pid"', True),
        ('pgrep -af worker | while read l; do kill "${l%% *}"; done', True),
        ('arr=($(pgrep -f worker)); kill "${arr[@]}"', True),
        ("sudo -n pkill -f worker", True),
        ("exec -a worker pkill -f worker", True),
        ("pgrep -f worker | xargs sudo -u root kill", True),
        ("sudo -n pgrep -f worker | xargs kill", True),
        ("exec -a sh pkill -f worker", True),
        ("pkill -f worker; " + "xargs " * 11 + "sh -c ':'", True),
        ("pkill -f worker; echo " + "$(" * 12 + ":" + ")" * 12, True),
        ("sudo 2>/dev/null -n pkill -f worker", True),
        ("env -u 2>/dev/null X pkill -f worker", True),
        ("pgrep -f worker | xargs sh -c 'echo x; kill $1' _", True),
        (r"$'\x70kill' -f worker; echo " + nested_backticks(17), True),
        ("pgrep -f worker", False),
        ("pgrep --full worker | sort", False),
        ("pgrep -f worker | xargs echo kill", False),
        ("pgrep -f worker | xargs env echo kill", False),
        ('sudo -n echo "pkill" "-f" worker', False),
        ("xargs " * 11 + "sh -c ':'", False),
        ('pgrep -f worker | while read p; do echo "$p"; done', False),
        ('pgrep -f worker | while read -r; do echo "$REPLY"; done', False),
        ('for p in $(pgrep -f worker); do echo "$p"; done', False),
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
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    hook = ROOT / "agents_extensions/shared/hooks/guard-secret-print.py"
    result = subprocess.run(
        [sys.executable, str(hook)], input=payload, text=True, capture_output=True, env=ENV, timeout=10
    )
    assert result.returncode == (2 if refused else 0), result.stderr
    for phrase in ALTERNATIVES if refused else ():
        assert phrase in result.stderr
    for harness in HARNESS_NAMES:
        native = subprocess.run(
            [sys.executable, str(ADAPTER), "--harness", harness],
            input=json.dumps(event(harness, command)),
            text=True,
            capture_output=True,
            env=ENV,
            timeout=10,
        )
        assert_decision(harness, native.returncode, native.stdout, native.stderr, not refused)
        for phrase in ALTERNATIVES if refused else ():
            assert phrase in native.stderr
