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
# Review F7, too: one case per shell form that hid a -c script. Before the
# script, every word must be a plain literal of letters, digits and dashes.
F7_SHELL_OPTIONS = [
    "bash +e -c 'pkill -f worker'",
    """pgrep -f worker | xargs bash +e -c 'kill "$1"' _""",
    r"bash -e \+x -c 'pkill -f worker'",
    "bash $FLAGS -c 'pkill -f worker'",
    "FLAGS='e -c pkill${IFS}-f${IFS}worker'; bash +$FLAGS",
    "bash $(printf '%s' '-c pkill${IFS}-f${IFS}worker')",
    "FLAGS='errexit -c'; bash -o $FLAGS 'pkill -f worker'",
    "bash -o {errexit,-c} 'pkill -f worker'",
    "bash -o ${REVIEW_UNUSED-} errexit -c 'pkill -f worker'",
    "set -- -c 'pkill -f worker'; bash \"$@\"",
    "set -- pipefail -c 'pkill -f worker'; bash -o \"$@\"",
    "set -- c 'pkill -f worker'; bash \"-$@\"",
    "bash -c -e 'pkill -f worker'",
    "bash -c \"$OPT\" 'pkill -f worker'",
    "bash -rcfile /dev/null -c 'pkill -f worker'",
    "bash -posix -c 'pkill -f worker'",
    "OLDPWD=-c; bash ~- 'pkill -f worker'",
    "pgrep -f worker; bash -c kill",
    "bash -e'c' 'pkill -f worker'",
    "pgrep -f worker; bash -posix -c 'kill' _",
    "bash -c 'pkill worker --'full _",
    "pkill '-f'\"\" worker",
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

# #12118: forms that hid a kill from the text reader, kills resolved against the
# live table, and selections the table cannot answer.
I12118_REFUSED = [
    "'sudo'\"\" pkill -f worker",
    "'command'\"\" pkill -f worker",
    "pgrep -f worker | xargs 'env'\"\" kill",
    "eval 'pkill -f worker'",
    'eval "$(echo pkill -f worker)"',
    "env -S 'pkill -f worker'",
    "echo 'pkill -f worker' | bash",
    "bash <<'EOF'\npkill -f worker\nEOF",
    ". /dev/stdin <<'EOF'\npkill -f worker\nEOF",
    'K=pkill; "$K" -f worker',
    "printf '%s%s -f worker\\n' pki ll | bash",
    "pkill --ful worker",
    "pgrep --ful worker | xargs kill",
    "setsid pkill -f worker",
    "find /dev/null -name command -o -path -v -o -exec pkill -f worker \\;",
    "killall bash",
    "kill $$",
    "kill -9 $PPID",
    "kill 0",
    "kill -9 -1",
    'pkill -f "$PATTERN"',
    'pgrep -f "$P" | xargs kill',
    "pkill -USR1 -H -x python",
    # Review F3/F4: a computed command word beside a kill, at any depth.
    'D=:; D=cd; "$D" /proc/$$; printf r2hidden > comm; pkill -x r2hidden; :',
    'D=:; D=pushd; "$D" /proc/$$; "$D" /dev; P=:; P=popd; "$P"; printf r2hidden > comm; pkill -x r2hidden; :',
    'D=:; D=cd; builtin "$D" /proc/$$; printf r2hidden > comm; pkill -x r2hidden',
    'D=:; D=cd; "$D" scripts/lib; bash driver_scope.sh',
    'cd "$(printf /dev)"; bash no-such-script-12118.sh',
    'L=:; L=sudo; "$L" -u nobody bash -c "pkill -u nobody -x bash; :"',
    'L=:; L=doas; "$L" -u nobody bash -c "killall -u nobody bash; :"',
    "L=:; L=sudo; \"$L\" -u nobody bash -c 'kill $(pgrep -U nobody -x bash); :'",
    'L=:; L=sudo; eval \'"$L" -u nobody bash -c "pkill -u nobody -x bash; :"\'',
    'L=:; L=sudo; find /dev/null -exec "$L" -u nobody bash -c "pkill -u nobody -x bash; :" \\;',
    # Review F5: computed wrapper paths and predicted substitutions count too.
    'P=/usr/bin; "$P"/env -S "pkill -f" worker',
    'P=/usr/bin; "$P"/env -S "bash -c" "pkill -f worker"; pkill -x no-such-process-12118',
    "$(echo cd) /dev; pkill -x no-such-process-12118",
    "bash -c '`echo cd` /dev; pkill -x no-such-process-12118'",
    'find /dev/null -exec "$(echo sudo)" -u nobody bash -c "pkill -u nobody -x bash" \\;',
    # Review round 4: a redirection target shaped like an assignment before the command word.
    'D=cd; > X=Y "$D" /dev; pkill -x no-such-process-12118',
    'T=true; > X=Y "$T"; pkill -x no-such-process-12118',
    'P=/usr/bin; 2> X=Y "$P"/env pkill -x no-such-process-12118',
    'T=/usr/bin; >X=Y "$T"/timeout 1 pkill -x no-such-process-12118; :',
    "P=/usr/bin; > X=Y \"$P\"/env -C /proc/self bash -c 'printf r4guard12118 > comm; pkill -x r4guard12118; :'",
]
I12118_ALLOWED = [
    "pkill -x no-such-process-12118",
    "pgrep -x no-such-process-12118 | xargs kill",
    "killall no-such-process-12118",
    "pkill -P 1 -x no-such-process-12118",
    # A wrapper before a shell running an existing script with no kill in it.
    "timeout 120 bash scripts/ci/linux_fs_parity.sh",
    # Review F3/F4: a computed command word without a kill is unaffected.
    'D=:; D=cd; "$D" /dev; pgrep -x no-such-process-12118',
    '[ -n "$(pgrep -x no-such-process-12118)" ] && pkill -x no-such-process-12118',
    # Review F6: computed data, assignments and option values are not command words.
    'printf "%s\\n" "$(echo ok)"; pkill -x no-such-process-12118',
    "X=$(echo ok); pkill -x no-such-process-12118",
    'T=1; timeout "$T" true; pkill -x no-such-process-12118',
    'E=env; echo "$E" -S hi',
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
        # #12118: these kills are resolved against the live table, so their targets
        # are a name no process holds and PIDs above the Linux ceiling.
        ("pgrep -f worker; kill 4194305", False),
        ("pkill no-such-process-12118", False),
        ("pkill -x no-such-process-12118", False),
        ("kill -TERM 4194305 4194306", False),
        ("pgrep no-such-process-12118 | xargs kill", False),
        ("pkill -- -foo", False),
        ('echo "pkill -f worker; pgrep -f worker | xargs kill"', False),
        ("printf '%s\\n' 'kill $(pgrep -f worker)'", False),
        ('git commit -m "refuse pkill -f and pgrep --full | kill"', False),
        ("cat <<'EOF'\npkill -f worker\nkill $(pgrep -f worker)\nEOF", False),
        ("cat <<EOF\npkill -f worker\nEOF", False),
        ("bash -e -c 'echo ok'", False),
        ('bash ./run.sh "$@"', False),
        ("bash -o pipefail -O extglob -c 'echo ok'", False),
        ("bash --norc --noprofile -c 'echo ok'", False),
        ('bash -c "echo $X" _ y', False),
        (r"printf $'ok\t\x41\101\n'", False),
    ]
    + [(command, True) for command in F7_SHELL_OPTIONS + F10_ANSI_C + I12118_REFUSED]
    + [(command, False) for command in I12118_ALLOWED]
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


@pytest.mark.parametrize("command", ["bash -c 'en'\"v\" _", "bash -c 'pr'\"intenv\" _"])
def test_spliced_secret_script_refused(command: str) -> None:
    """#12118: a shell script spliced from quote fragments is read whole by the secret scan."""
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    hook = ROOT / "agents_extensions/shared/hooks/guard-secret-print.py"
    result = subprocess.run(
        [sys.executable, str(hook)], input=payload, text=True, capture_output=True, env=ENV, timeout=10
    )
    assert result.returncode == 2, result.stderr
    assert "would print shell environment values" in result.stderr
