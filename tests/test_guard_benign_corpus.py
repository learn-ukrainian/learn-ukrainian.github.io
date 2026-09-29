"""Compare the pre-9115 guard-test corpus with pinned baseline decisions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK_DIR = REPO / "agents_extensions/shared/hooks"
GUARDS = (
    "admin_merge",
    "pr_merge",
    "branch_switch_in_main",
    "secret_print",
    "primary_checkout_write",
)

# CI checks out one commit, so the historical commit is unavailable there.
# This fixture was generated from commit 28a4243544954335d0d6edafa6f727beb1a5981f:
# its test-module string literals and the old hooks' decisions on those strings.
BASELINE_FIXTURE = json.loads((REPO / "tests/fixtures/guard_9115_baseline.json").read_text(encoding="utf-8"))
BASELINE_COMMANDS = BASELINE_FIXTURE["commands"]
BASELINE_INDEX = {command: index for index, command in enumerate(BASELINE_COMMANDS)}

BENIGN_COMMANDS = (
    "git status",
    "git commit -F - <<'EOF'\nmessage with << text\nEOF\ngit status",
    "git commit -m \"$(cat <<'EOF'\nmessage with << text\nEOF\n)\"\ngit status",
    "python3 -c '\nprint(\"<<\")\n'\ngit status",
    "gh pr create --body \"$(cat <<'EOF'\nbody with << text\nEOF\n)\"",
    "cat > ./batch_state/guard-corpus.sh <<'EOF'\n#!/bin/bash\necho '<<'\nEOF",
    "echo $((1<<3))\ngit status",
    'for ((i=0;i<1<<1;i++)); do echo "$i"; done\ngit status',
)

# These literals were added after the baseline commit. Pin their allow decisions as well;
# a later parser change must not turn harmless quoted/comment text into a block.
HEAD_ONLY_BENIGN_COMMANDS = (
    "echo $(printf '%s' '# gh pr merge 5 --admin')",
    'echo $(printf "%s" "# gh pr merge 5 --admin")',
    "echo $(printf '%s' $# ${#var} a#b)",
    r"echo \`gh pr merge 5 --admin\`",
    "echo 'literal `gh pr merge 5 --admin`'",
    "echo `printf '%s' '# value'`",
)


EXPECTED_PROSE_FLIPS = {
    (row["guard"], BASELINE_COMMANDS[row["command_index"]]): (row["before"], row["after"])
    for row in BASELINE_FIXTURE["expected_prose_flips"]
}


def _literal_corpus() -> list[str]:
    return [command for command in BASELINE_COMMANDS if command not in HEAD_ONLY_BENIGN_COMMANDS]


def _baseline_decisions(commands: list[str]) -> dict[str, list[bool]]:
    return {
        guard: [bits[BASELINE_INDEX[command]] == "1" for command in commands]
        for guard, bits in BASELINE_FIXTURE["baseline_decisions"].items()
    }


def _probe(hook_dir: Path, commands: list[str]) -> dict[str, list[bool]]:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--probe", str(hook_dir)],
        input=json.dumps(commands),
        text=True,
        capture_output=True,
        cwd=REPO,
        check=True,
        timeout=120,
    )
    return json.loads(result.stdout)


def test_baseline_fixture_covers_all_guards_and_commands() -> None:
    assert BASELINE_FIXTURE["baseline_commit"] == "28a4243544954335d0d6edafa6f727beb1a5981f"
    assert len(BASELINE_COMMANDS) == 1498
    assert len(_literal_corpus()) == 1492
    assert sorted(set(BASELINE_COMMANDS)) == BASELINE_COMMANDS
    assert set(BASELINE_FIXTURE["baseline_decisions"]) == set(GUARDS)
    assert all(
        len(bits) == len(BASELINE_COMMANDS) and set(bits) <= {"0", "1"}
        for bits in BASELINE_FIXTURE["baseline_decisions"].values()
    )
    assert set(BENIGN_COMMANDS) | set(HEAD_ONLY_BENIGN_COMMANDS) <= set(BASELINE_COMMANDS)


def test_all_literal_commands_have_no_new_guard_blocks() -> None:
    commands = _literal_corpus()
    baseline = _baseline_decisions(commands)
    head = _probe(HOOK_DIR, commands)
    changed = {
        (guard, command): (was_blocked, is_blocked)
        for guard in GUARDS
        for command, was_blocked, is_blocked in zip(commands, baseline[guard], head[guard], strict=True)
        if was_blocked != is_blocked
    }
    assert changed == EXPECTED_PROSE_FLIPS, f"{len(commands)} baseline literals; changed decisions: {changed!r}"


def test_head_only_benign_literals_have_no_new_blocks() -> None:
    commands = sorted(set(BENIGN_COMMANDS) | set(HEAD_ONLY_BENIGN_COMMANDS))
    baseline = _baseline_decisions(commands)
    head = _probe(HOOK_DIR, commands)
    newly_blocked = [
        (guard, command)
        for guard in GUARDS
        for command, was_blocked, is_blocked in zip(commands, baseline[guard], head[guard], strict=True)
        if not was_blocked and is_blocked
    ]
    assert not newly_blocked, f"head-only benign allow-to-block flips: {newly_blocked!r}"


def _probe_child(hook_dir: Path, commands: list[str]) -> dict[str, list[bool]]:
    import importlib.util

    sys.path.insert(0, str(hook_dir))
    modules = {}
    for name in GUARDS:
        path = hook_dir / f"guard-{name.replace('_', '-')}.py"
        spec = importlib.util.spec_from_file_location(f"corpus_{name}", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[name] = module

    verdicts: dict[str, list[bool]] = {name: [] for name in GUARDS}
    for command in commands:
        admin = modules["admin_merge"]
        verdicts["admin_merge"].append(
            any(admin._admin_merge_args(segment) is not None for segment in admin._segments(command))
        )
        pr = modules["pr_merge"]
        verdicts["pr_merge"].append(any(pr._merge_args(segment) is not None for segment in pr._segments(command)))
        branch = modules["branch_switch_in_main"]
        verdicts["branch_switch_in_main"].append(
            any(branch._segment_is_dangerous(segment) is not None for segment in branch._segments(command))
        )
        secret = modules["secret_print"]
        verdicts["secret_print"].append(bool(secret._scan_command(command, set())))
        write = modules["primary_checkout_write"]
        verdicts["primary_checkout_write"].append(bool(write.bash_write_targets(command)))
    return verdicts


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--probe":
    print(json.dumps(_probe_child(Path(sys.argv[2]), json.load(sys.stdin))))
