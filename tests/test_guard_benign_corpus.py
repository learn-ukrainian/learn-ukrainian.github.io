"""Compare the pre-9115 guard-test corpus with the main hook baseline."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK_DIR = REPO / "agents_extensions/shared/hooks"
BASELINE = "28a4243544954335d0d6edafa6f727beb1a5981f"
GUARDS = (
    "admin_merge",
    "pr_merge",
    "branch_switch_in_main",
    "secret_print",
    "primary_checkout_write",
)
HOOK_FILES = (*[f"guard-{name.replace('_', '-')}.py" for name in GUARDS], "shell_shlex.py")

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


def _literal_corpus() -> list[str]:
    values = set(BENIGN_COMMANDS)
    for name in GUARDS:
        source = subprocess.run(
            ["git", "show", f"{BASELINE}:tests/test_guard_{name}.py"],
            cwd=REPO,
            capture_output=True,
            check=True,
            text=True,
            timeout=30,
        ).stdout
        tree = ast.parse(source)
        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        }
        values.update(
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and "{payload}" not in node.value  # A parameterized template is not a command.
        )
    return sorted(values)


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


def _baseline_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "baseline_hooks"
    directory.mkdir()
    for name in HOOK_FILES:
        source = subprocess.run(
            ["git", "show", f"{BASELINE}:agents_extensions/shared/hooks/{name}"],
            cwd=REPO,
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout
        (directory / name).write_bytes(source)
    return directory


def test_all_literal_commands_have_no_new_guard_blocks(tmp_path: Path) -> None:
    commands = _literal_corpus()
    baseline = _probe(_baseline_dir(tmp_path), commands)
    head = _probe(HOOK_DIR, commands)
    changed = [
        (guard, command)
        for guard in GUARDS
        for command, was_blocked, is_blocked in zip(commands, baseline[guard], head[guard], strict=True)
        if was_blocked != is_blocked
    ]
    assert not changed, f"{len(commands)} literal commands; changed decisions: {changed[:10]!r}"


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
