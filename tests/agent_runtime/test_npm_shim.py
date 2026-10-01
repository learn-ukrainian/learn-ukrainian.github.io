"""The agent npm/npx shim refuses installs through a symlinked node_modules (#9460).

Each scratch layout mirrors a dispatch worktree: a primary checkout with real
``node_modules`` and ``site/node_modules`` holding a sentinel file, and a
worktree under ``.worktrees/dispatch/`` whose folders are symlinks to them. A
fake ``npm``/``npx`` behind the shim records each call and, for tree-writing
commands, empties the target ``node_modules`` the way ``npm ci`` does; no
network and no real install is involved.

Failing-before proof: every refusal test asserts the fake was never invoked and
the sentinel survived. Without the shim (``test_unguarded_fake_npm_destroys_the_sentinel``)
the same calls reach the fake and the sentinel is deleted.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime import npm_guard

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIM_SOURCE = REPO_ROOT / "scripts" / "agent_runtime" / "shims" / "npm"
GUARD_SOURCE = REPO_ROOT / "scripts" / "agent_runtime" / "npm_guard.py"
SENTINEL = "sentinel.txt"

FAKE_TOOL = r"""#!/usr/bin/env bash
# Fake npm/npx: log the call, emulate `npm ci` emptying its target, echo, exit.
tool="$(basename "$0")"
printf '%s\t%s\t%s\n' "$tool" "$PWD" "$*" >> "$FAKE_NPM_LOG"
target="$PWD"
command=""
args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
  case "${args[$i]}" in
    --prefix | -C) target="${args[$((i + 1))]}"; i=$((i + 1)) ;;
    --prefix=* | -C=*) target="${args[$i]#*=}" ;;
    -*) ;;
    *) [[ -z "$command" ]] && command="${args[$i]}" ;;
  esac
done
if [[ "$tool" == "npm" ]]; then
  case "$command" in
    ci | install | i | update | prune | dedupe | uninstall)
      rm -rf "$target"/node_modules/* "$target"/node_modules/.[!.]* 2>/dev/null
      ;;
    run)
      if [[ -n "${FAKE_RUN_SCRIPT:-}" ]]; then
        sh -c "$FAKE_RUN_SCRIPT"
        exit $?
      fi
      ;;
  esac
fi
echo "fake-$tool-stdout $*"
echo "fake-$tool-stderr" >&2
exit "${FAKE_NPM_EXIT:-0}"
"""

# The issue's denominator: every command at every location.
DENOMINATOR = [
    ["ci"],
    ["install"],
    ["i"],
    ["update"],
    ["prune"],
    ["dedupe"],
    ["uninstall", "left-pad"],
]

# npm aliases, abbreviations and other tree-writing commands, at root and site/.
EQUIVALENTS = [
    ["ci", "--ignore-scripts"],
    ["clean-install"],
    ["install-ci-test"],
    ["add", "left-pad"],
    ["rm", "left-pad"],
    ["up"],
    ["upgrade"],
    ["inst"],
    ["dedu"],
    ["installTest"],
    ["rebuild"],
    ["link"],
    ["audit", "fix"],
]

READ_ONLY = [
    ["audit"],
    ["ls"],
    ["run", "build"],
    ["run", "ci"],
    ["test"],
    ["view", "left-pad"],
    ["exec", "eslint"],
    ["--version"],
    [],
    ["help", "install"],
    ["outdated"],
]


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture()
def layout(tmp_path: Path) -> dict[str, Path]:
    """Scratch primary + dispatch worktree with symlinked node_modules folders."""
    tooling = tmp_path / "tooling"
    shim_dir = tooling / "scripts" / "agent_runtime" / "shims"
    shim_dir.mkdir(parents=True)
    shutil.copy2(SHIM_SOURCE, shim_dir / "npm")
    (shim_dir / "npx").symlink_to("npm")
    shutil.copy2(GUARD_SOURCE, tooling / "scripts" / "agent_runtime" / "npm_guard.py")
    (tooling / ".venv" / "bin").mkdir(parents=True)
    (tooling / ".venv" / "bin" / "python").symlink_to(sys.executable)

    fake_bin = tmp_path / "fakebin"
    fake_bin.mkdir()
    for name in ("npm", "npx"):
        fake = fake_bin / name
        fake.write_text(FAKE_TOOL, encoding="utf-8")
        fake.chmod(0o755)

    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    _write_json(primary / "package.json", {"name": "primary", "workspaces": ["packages/*"]})
    for folder in (primary / "node_modules", primary / "site" / "node_modules"):
        folder.mkdir(parents=True)
        (folder / SENTINEL).write_text("keep\n", encoding="utf-8")
        (folder / "dep").mkdir()

    worktree = primary / ".worktrees" / "dispatch" / "agent" / "task"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: ../../../../.git/worktrees/task\n", encoding="utf-8")
    _write_json(worktree / "package.json", {"name": "worktree", "workspaces": ["packages/*"]})
    _write_json(worktree / "packages" / "kit" / "package.json", {"name": "@lu/kit"})
    _write_json(worktree / "site" / "package.json", {"name": "site"})
    (worktree / "site" / "src").mkdir()
    (worktree / "node_modules").symlink_to(primary / "node_modules")
    (worktree / "site" / "node_modules").symlink_to(primary / "site" / "node_modules")

    return {
        "tmp": tmp_path,
        "shim_dir": shim_dir,
        "fake_bin": fake_bin,
        "primary": primary,
        "worktree": worktree,
        "log": tmp_path / "fake-npm.log",
    }


def _make_real(layout: dict[str, Path]) -> None:
    """Replace the worktree's symlinks with real, worktree-local folders."""
    for relative in ("node_modules", "site/node_modules"):
        link = layout["worktree"] / relative
        link.unlink()
        link.mkdir()
        (link / "local.txt").write_text("local\n", encoding="utf-8")


def _run(
    layout: dict[str, Path],
    tool: str,
    args: list[str],
    cwd: Path,
    extra_env: dict[str, str] | None = None,
    *,
    shim: bool = True,
):
    tool_path = (layout["shim_dir"] if shim else layout["fake_bin"]) / tool
    path_entries = [str(layout["shim_dir"]), str(layout["fake_bin"]), "/usr/bin", "/bin"]
    env = {"PATH": os.pathsep.join(path_entries), "HOME": str(layout["tmp"]), "FAKE_NPM_LOG": str(layout["log"])}
    env.update(extra_env or {})
    return subprocess.run(
        [str(tool_path), *args], cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=60
    )


def _sentinels_intact(layout: dict[str, Path]) -> bool:
    primary = layout["primary"]
    return (primary / "node_modules" / SENTINEL).is_file() and (primary / "site" / "node_modules" / SENTINEL).is_file()


def _fake_calls(layout: dict[str, Path]) -> list[str]:
    return layout["log"].read_text(encoding="utf-8").splitlines() if layout["log"].exists() else []


def _assert_refused(layout: dict[str, Path], proc: subprocess.CompletedProcess[str]) -> None:
    assert proc.returncode == 1, proc.stderr
    assert "refused" in proc.stderr and "#9460" in proc.stderr
    assert "unlink " in proc.stderr and "Safe alternative" in proc.stderr
    assert _fake_calls(layout) == []
    assert _sentinels_intact(layout)


# Locations: (cwd relative to the worktree, extra args placing the target).
LOCATIONS = {
    "root": (".", []),
    "site": ("site", []),
    "site-subdir": ("site/src", []),
    "workspace-member": ("packages/kit", []),
    "prefix-space": (".", ["--prefix", "site"]),
    "prefix-eq": (".", ["--prefix=site"]),
    "C-space": (".", ["-C", "site"]),
    "C-eq": (".", ["-C=site"]),
    "prefix-up-to-root": ("site", ["--prefix", ".."]),
    "C-up-to-root": ("site/src", ["-C", "../.."]),
    "workspace-name": (".", ["--workspace", "@lu/kit"]),
    "workspace-path": (".", ["-w", "packages/kit"]),
    "workspaces-all": (".", ["--workspaces"]),
    "workspace-site": (".", ["--workspace=site"]),
}


@pytest.mark.parametrize("command", DENOMINATOR, ids=" ".join)
@pytest.mark.parametrize("location", sorted(LOCATIONS))
def test_destructive_command_through_symlink_is_refused(layout, command, location):
    relative_cwd, placement = LOCATIONS[location]
    proc = _run(layout, "npm", [*command, *placement], layout["worktree"] / relative_cwd)
    _assert_refused(layout, proc)


@pytest.mark.parametrize("command", EQUIVALENTS, ids=" ".join)
@pytest.mark.parametrize("relative_cwd", [".", "site"])
def test_equivalent_tree_writers_through_symlink_are_refused(layout, command, relative_cwd):
    _assert_refused(layout, _run(layout, "npm", command, layout["worktree"] / relative_cwd))


@pytest.mark.parametrize(
    "args",
    [
        ["--prefix", "site", "ci"],
        ["--loglevel", "info", "install"],
        ["--logl", "info", "ci"],
        ["-d", "ci"],
        ["--silent", "ci"],
        ["--no-audit", "ci"],
        ["--audit", "false", "install"],
        ["--workspaces", "ci"],
        ["--color", "always", "ci"],
        ["--global", "false", "ci"],
        ["--no-global", "ci"],
        ["ci", "--location=project"],
    ],
    ids=" ".join,
)
def test_options_before_or_around_the_command_are_parsed_like_npm(layout, args):
    _assert_refused(layout, _run(layout, "npm", args, layout["worktree"]))


@pytest.mark.parametrize(
    "tool,args",
    [
        ("npx", ["npm", "ci"]),
        ("npx", ["npm@10", "install"]),
        ("npx", ["--yes", "npm", "ci", "--ignore-scripts"]),
        ("npx", ["-p", "npm", "-c", "npm ci"]),
        ("npx", ["--package=npm", "--", "npm", "ci"]),
        ("npx", ["-c", "echo start && npm ci"]),
        ("npx", ["yarn"]),
        ("npx", ["pnpm", "install"]),
        ("npx", ["npx", "npm", "ci"]),
        ("npm", ["exec", "--", "npm", "ci"]),
        ("npm", ["x", "npm", "ci"]),
        ("npm", ["exec", "-c", "npm install"]),
    ],
    ids=lambda value: value if isinstance(value, str) else " ".join(value),
)
def test_package_managers_launched_through_npx_are_refused(layout, tool, args):
    _assert_refused(layout, _run(layout, tool, args, layout["worktree"]))


@pytest.mark.parametrize("args", [["npm", "ls"], ["--prefix", "site", "npm", "audit"]], ids=" ".join)
def test_npx_inner_read_only_npm_passes(layout, args):
    proc = _run(layout, "npx", args, layout["worktree"])
    assert proc.returncode == 0, proc.stderr
    assert len(_fake_calls(layout)) == 1


@pytest.mark.parametrize("args", READ_ONLY, ids=lambda value: " ".join(value) or "bare")
@pytest.mark.parametrize("relative_cwd", [".", "site"])
def test_read_only_commands_pass_through_unchanged(layout, args, relative_cwd):
    cwd = layout["worktree"] / relative_cwd
    proc = _run(layout, "npm", args, cwd, {"FAKE_NPM_EXIT": "7"})
    assert proc.returncode == 7
    assert proc.stdout == f"fake-npm-stdout {' '.join(args)}\n"
    assert proc.stderr == "fake-npm-stderr\n"
    assert _fake_calls(layout) == [f"npm\t{cwd}\t{' '.join(args)}"]
    assert _sentinels_intact(layout)


@pytest.mark.parametrize(
    "args", [["eslint", "."], ["-y", "cowsay", "hi"], ["--package=typescript", "tsc", "--version"]], ids=" ".join
)
def test_npx_tools_that_are_not_package_managers_pass_through(layout, args):
    proc = _run(layout, "npx", args, layout["worktree"], {"FAKE_NPM_EXIT": "3"})
    assert proc.returncode == 3
    assert proc.stdout == f"fake-npx-stdout {' '.join(args)}\n"
    assert _fake_calls(layout) == [f"npx\t{layout['worktree']}\t{' '.join(args)}"]


@pytest.mark.parametrize("command", DENOMINATOR + EQUIVALENTS[:3], ids=" ".join)
@pytest.mark.parametrize("location", sorted(LOCATIONS))
def test_destructive_command_into_real_node_modules_installs(layout, command, location):
    _make_real(layout)
    relative_cwd, placement = LOCATIONS[location]
    cwd = layout["worktree"] / relative_cwd
    args = [*command, *placement]
    proc = _run(layout, "npm", args, cwd, {"FAKE_NPM_EXIT": "5"})
    assert proc.returncode == 5, proc.stderr
    assert proc.stdout == f"fake-npm-stdout {' '.join(args)}\n"
    assert proc.stderr == "fake-npm-stderr\n"
    assert _fake_calls(layout) == [f"npm\t{cwd}\t{' '.join(args)}"]
    assert _sentinels_intact(layout)


@pytest.mark.parametrize(
    "args,env",
    [
        (["install", "-g", "left-pad"], {}),
        (["i", "--global", "left-pad"], {}),
        (["uninstall", "--location=global", "left-pad"], {}),
        (["install", "-L", "global", "left-pad"], {}),
        (["install", "left-pad"], {"npm_config_global": "true"}),
    ],
    ids=["-g", "--global", "--location=global", "-L global", "env"],
)
def test_global_installs_are_not_project_installs_and_pass_through(layout, args, env):
    proc = _run(layout, "npm", args, layout["worktree"], env)
    assert proc.returncode == 0, proc.stderr
    assert len(_fake_calls(layout)) == 1


def test_stdin_reaches_the_real_tool(layout, tmp_path):
    reader = layout["fake_bin"] / "npm"
    reader.write_text("#!/usr/bin/env bash\ncat\n", encoding="utf-8")
    path_entries = [str(layout["shim_dir"]), str(layout["fake_bin"]), "/usr/bin", "/bin"]
    proc = subprocess.run(
        [str(layout["shim_dir"] / "npm"), "ls"],
        cwd=layout["worktree"],
        env={"PATH": os.pathsep.join(path_entries), "HOME": str(tmp_path)},
        input="piped\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert (proc.returncode, proc.stdout) == (0, "piped\n")


def test_run_script_calling_npm_ci_is_refused_through_path(layout):
    """A run-script's inner `npm ci` resolves through PATH, so the shim sees it."""
    proc = _run(layout, "npm", ["run", "reinstall"], layout["worktree"], {"FAKE_RUN_SCRIPT": "npm ci"})
    assert proc.returncode == 1
    assert "refused `npm ci`" in proc.stderr
    assert _fake_calls(layout) == [f"npm\t{layout['worktree']}\trun reinstall"]
    assert _sentinels_intact(layout)


def _real_npm() -> str | None:
    for entry in os.environ.get("AGENT_ORIGINAL_PATH", os.environ.get("PATH", "")).split(os.pathsep):
        if not entry or entry.endswith(os.path.join("agent_runtime", "shims")):
            continue
        candidate = Path(entry) / "npm"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


@pytest.mark.skipif(_real_npm() is None, reason="needs a real npm to execute a package.json run-script")
def test_real_npm_run_script_inner_npm_ci_hits_the_shim(layout):
    """Real npm builds the run-script PATH from the caller's PATH, keeping the shim first."""
    real_npm = Path(_real_npm())
    worktree = layout["worktree"]
    _write_json(worktree / "package.json", {"name": "worktree", "scripts": {"reinstall": "npm ci"}})
    path_entries = [str(layout["shim_dir"]), str(real_npm.parent), "/usr/bin", "/bin"]
    proc = subprocess.run(
        [str(layout["shim_dir"] / "npm"), "run", "reinstall"],
        cwd=worktree,
        env={"PATH": os.pathsep.join(path_entries), "HOME": str(layout["tmp"]), "npm_config_update_notifier": "false"},
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert proc.returncode != 0
    assert "refused `npm ci`" in proc.stderr
    assert _sentinels_intact(layout)


@pytest.mark.parametrize("args", [["ci"], ["install"], ["--prefix", "site", "ci"], ["prune"]], ids=" ".join)
def test_unguarded_fake_npm_destroys_the_sentinel(layout, args):
    """Control: without the shim the same call empties the primary's folder."""
    proc = _run(layout, "npm", args, layout["worktree"], shim=False)
    assert proc.returncode == 0
    assert not _sentinels_intact(layout)


def test_missing_project_interpreter_fails_closed(layout):
    (layout["shim_dir"].parents[2] / ".venv" / "bin" / "python").unlink()
    proc = _run(layout, "npm", ["ls"], layout["worktree"])
    assert proc.returncode == 127
    assert "cannot find the project interpreter" in proc.stderr
    assert _fake_calls(layout) == []


def test_shim_never_resolves_itself_as_the_real_tool(layout):
    env = {
        "PATH": os.pathsep.join([str(layout["shim_dir"]), "/usr/bin", "/bin"]),
        "AGENT_ORIGINAL_PATH": os.pathsep.join([str(layout["shim_dir"]), "/nonexistent"]),
        "HOME": str(layout["tmp"]),
        "AGENT_REAL_NPM": str(layout["shim_dir"] / "npm"),
    }
    proc = subprocess.run(
        [str(layout["shim_dir"] / "npm"), "ls"],
        cwd=layout["tmp"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 127
    assert "could not locate the real npm" in proc.stderr


def test_pinned_real_tool_is_used(layout):
    proc = _run(
        layout,
        "npm",
        ["ls"],
        layout["worktree"],
        {
            "PATH": f"{layout['shim_dir']}{os.pathsep}/usr/bin{os.pathsep}/bin",
            "AGENT_REAL_NPM": str(layout["fake_bin"] / "npm"),
        },
    )
    assert proc.returncode == 0
    assert len(_fake_calls(layout)) == 1


def test_symlink_inside_the_same_worktree_is_allowed(layout):
    worktree = layout["worktree"]
    (worktree / "site" / "node_modules").unlink()
    (worktree / "vendor-modules").mkdir()
    (worktree / "site" / "node_modules").symlink_to(worktree / "vendor-modules")
    proc = _run(layout, "npm", ["ci"], worktree / "site")
    assert proc.returncode == 0, proc.stderr


def test_refusal_names_the_symlink_to_remove(layout):
    proc = _run(layout, "npm", ["ci"], layout["worktree"] / "site")
    assert f"unlink {layout['worktree'] / 'site' / 'node_modules'}" in proc.stderr


# --- unit tests of the guard's npm ports -------------------------------------


@pytest.mark.parametrize(
    "token,expected",
    [
        ("i", "install"),
        ("ic", "ci"),
        ("cit", "install-ci-test"),
        ("clean-install-test", "install-ci-test"),
        ("dedu", "dedupe"),
        ("installTest", "install-test"),
        ("run", "run-script"),
        ("info", "view"),
        ("u", None),
        ("", None),
        ("help-search", "help-search"),
    ],
)
def test_deref_command_matches_npm(token, expected):
    assert npm_guard.deref_command(token) == expected


def test_parse_keeps_options_after_positionals_and_stops_at_double_dash():
    parsed = npm_guard.parse_npm_argv(["ci", "--prefix", "site", "--", "--prefix", "x"])
    assert parsed.remain == ["ci", "--prefix", "x"]
    assert parsed.last("prefix") == "site"


def test_parse_collects_repeated_workspaces():
    parsed = npm_guard.parse_npm_argv(["-w", "a", "--workspace=b", "install"])
    assert parsed.values("workspace") == ["a", "b"]
    assert parsed.remain == ["install"]


def test_npx_split_matches_npx_cli():
    assert npm_guard.split_npx_argv(["-y", "-p", "npm", "npm", "ci"]) == (["--yes", "--package", "npm"], ["npm", "ci"])
    assert npm_guard.split_npx_argv(["--node-arg", "x", "tool"]) == ([], ["tool"])
    assert npm_guard.split_npx_argv(["--yes"]) == (["--yes"], [])


def test_local_prefix_detects_workspace_root(layout):
    worktree = layout["worktree"]
    assert npm_guard.local_prefix(worktree / "packages" / "kit") == (worktree, worktree / "packages" / "kit")
    assert npm_guard.local_prefix(worktree / "site" / "src") == (worktree / "site", None)
    assert npm_guard.local_prefix(worktree / "packages" / "kit", detect_workspace=False) == (
        worktree / "packages" / "kit",
        None,
    )


def test_workspace_patterns_support_negation_braces_and_globstar(tmp_path):
    patterns = npm_guard._workspace_patterns(
        {"workspaces": {"packages": ["./{apps,libs}/*", "tools/**", "!libs/private"]}}
    )
    assert npm_guard._matches_workspaces(tmp_path, tmp_path / "apps" / "web", patterns)
    assert npm_guard._matches_workspaces(tmp_path, tmp_path / "tools" / "a" / "b", patterns)
    assert not npm_guard._matches_workspaces(tmp_path, tmp_path / "libs" / "private", patterns)
    assert not npm_guard._matches_workspaces(tmp_path, tmp_path / "site", patterns)


def test_main_rejects_unknown_tool(capsys):
    assert npm_guard.main(["yarn", "install"]) == 2
    assert "usage" in capsys.readouterr().err


# --- wiring: dispatched shells resolve npm/npx to the shim ---------------------


def test_shim_files_are_executable_and_npx_shares_the_npm_shim():
    assert os.access(SHIM_SOURCE, os.X_OK)
    npx = SHIM_SOURCE.parent / "npx"
    assert npx.is_symlink() and os.readlink(npx) == "npm"


def test_dispatch_worker_path_resolves_npm_and_npx_to_the_shim(monkeypatch):
    from scripts import delegate

    # delegate pins the primary checkout; point it at this checkout's shims.
    monkeypatch.setattr(delegate, "_REPO_ROOT", REPO_ROOT)
    env = delegate._pinned_worker_venv_env({"PATH": "/usr/bin:/bin"})
    shim_dir = delegate._REPO_ROOT / "scripts" / "agent_runtime" / "shims"
    assert shutil.which("npm", path=env["PATH"]) == str(shim_dir / "npm")
    assert shutil.which("npx", path=env["PATH"]) == str(shim_dir / "npx")


def test_runner_merge_guard_path_resolves_npm_to_the_shim():
    from scripts.agent_runtime import runner

    env = runner._apply_merge_guard(mode="danger", env={"PATH": "/usr/bin:/bin"})
    assert shutil.which("npm", path=env["PATH"]) == str(runner._SHIMS_DIR / "npm")
