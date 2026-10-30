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
OVERRIDE_ENV = {**ENV, "LEARN_UK_SECRETS_OK": "1"}
ALTERNATIVES = ("exact numeric PIDs read in an earlier command", "harness's own stop tool")

# Backticks nested past the shared parser's depth limit.
DEEP = ":"
for _ in range(17):
    DEEP = "`" + DEEP.replace("\\", "\\\\").replace("`", r"\`") + "`"
DEEP = "echo " + DEEP
# Review F7: kills Bash decodes from these spellings, beside a part too deep to read.
F7_KILLS = [
    "pki\\\nll -f worker",
    r"$'\x70kill' -f worker",
    "pgre\\\np -f worker | xargs kill",
    r"$'\x70grep' -f worker | xargs kill",
    r'''bash -c "$'\x70kill' -f worker"''',
    r"""bash -c '$'"'"'\x70kill'"'"' -f worker'""",
    r'''echo "$($'\x70kill' -f worker)"''',
    r'''bash -c "$'\x70grep' -f worker | xargs kill"''',
    r'''echo "$($'\x70grep' -f worker | xargs kill)"''',
    "sh -c 'pki\\\nll -f worker'",
    r"$'pkill\400' -f worker",
    r"$'pgrep\400' -f worker | xargs kill",
    r"$'\560kill' -f worker",
    r"$'\560grep' -f worker | xargs kill",
    r"$'p\153ill\0suffix' -f worker",
]
# Review F7, too: shell options the reader does not model hide the child script.
F7_SHELL_OPTIONS = [
    "bash +e -c 'pkill -f worker'",
    """bash +e -c 'echo "'""",
    "bash +x -c 'pkill -f worker'",
    "bash +o posix -c 'pkill -f worker'",
    "bash -e +x -c 'pkill -f worker'",
    "sudo -n bash +e -c 'pkill -f worker'",
    "env -u REVIEW_UNUSED bash +e -c 'pkill -f worker'",
    """pgrep -f worker | xargs bash +e -c 'kill "$1"' _""",
    r"bash \+e -c 'pkill -f worker'",
    r"bash -e \+x -c 'pkill -f worker'",
    r"bash \+o posix -c 'pkill -f worker'",
    r"bash \-e -c 'pkill -f worker'",
    r"bash -o posix \+e -c 'pkill -f worker'",
    r"bash \+O extglob -c 'pkill -f worker'",
    "bash $FLAGS -c 'pkill -f worker'",
    "FLAGS='e -c pkill${IFS}-f${IFS}worker'; bash +$FLAGS",
    "FLAGS='-c pkill${IFS}-f${IFS}worker'; bash ${FLAGS}",
    "bash $(printf '%s' '-c pkill${IFS}-f${IFS}worker')",
    "FLAGS='errexit -c'; bash -o $FLAGS 'pkill -f worker'",
    "FLAGS='extglob -c'; bash -eO $FLAGS 'pkill -f worker'",
    "FLAGS='/dev/null -c'; bash --rcfile $FLAGS 'pkill -f worker'",
    "bash +O $(printf 'extglob -c') 'pkill -f worker'",
    "bash -o {errexit,-c} 'pkill -f worker'",
    "bash -o ${REVIEW_UNUSED-} errexit -c 'pkill -f worker'",
    "set -- -c 'pkill -f worker'; bash \"$@\"",
    "set -- pipefail -c 'pkill -f worker'; bash -o \"$@\"",
    "set -- -c 'pkill -f worker'; sh \"${@:1}\"",
    "args=(-c 'pkill -f worker'); bash \"${args[@]}\"",
    "set -- c 'pkill -f worker'; bash \"-$@\"",
    "set -- extglob -c 'pkill -f worker'; bash +O \"$@\"",
    "set -- /dev/null -c 'pkill -f worker'; bash --init-file \"$@\"",
    "bash -c -e 'pkill -f worker'",
    "bash -c -o pipefail 'pkill -f worker'",
    "bash -c -- 'pkill -f worker'",
    "bash -c \"$OPT\" 'pkill -f worker'",
    "bash -rcfile /dev/null -c 'pkill -f worker'",
    "bash -restricted -c 'pkill -f worker'",
    "OLDPWD=-c; bash ~- 'pkill -f worker'",
    "PWD=-c; bash ~+ 'pkill -f worker'",
    "HOME=-c; bash ~ 'pkill -f worker'",
    "OLDPWD=-c; bash -e ~- 'pkill -f worker'",
    "OLDPWD=-c; bash ~- 'pgrep -f worker | xargs kill'",
]
# Review F10: ANSI-C escapes whose Bash meaning the decoder does not model.
F10_ANSI_C = [
    r"$'p\153ill\0suffix' -f worker",
    r"$'p\147rep\0suffix' -f worker | xargs kill",
    r"$'\560kill' -f worker",
    r"$'\560grep' -f worker | xargs kill",
    r"$'pkill\400' -f worker",
    r"$'pgrep\400' -f worker | xargs kill",
    r"pkill $'\455f' worker",
    r"pgrep $'\455f' worker | xargs kill",
    r"$'\x70kill' -f worker",
]


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
        ("bash -e -c 'echo ok'", False),
        ('bash "$HOME/run.sh"', False),
        ("bash -o pipefail +O extglob -c 'echo ok'", False),
        ("bash --norc --noprofile -c 'echo ok'", False),
        ('bash -c "echo $X" _ y', False),
        (r"printf $'ok\t\x41\101\n'", False),
    ]
    + [(command, True) for command in F7_SHELL_OPTIONS + F10_ANSI_C]
    + [(kill + "; " + DEEP, True) for kill in F7_KILLS]
    + [(DEEP + "; " + kill, True) for kill in F7_KILLS],
)
def test_self_matching_process_kill(command: str, refused: bool) -> None:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    hook = ROOT / "agents_extensions/shared/hooks/guard-secret-print.py"
    # The secret-output override never changes a process-kill decision.
    for env in (ENV, OVERRIDE_ENV):
        result = subprocess.run(
            [sys.executable, str(hook)], input=payload, text=True, capture_output=True, env=env, timeout=10
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
            env=OVERRIDE_ENV,
            timeout=10,
        )
        assert_decision(harness, native.returncode, native.stdout, native.stderr, not refused)
        for phrase in ALTERNATIVES if refused else ():
            assert phrase in native.stderr
