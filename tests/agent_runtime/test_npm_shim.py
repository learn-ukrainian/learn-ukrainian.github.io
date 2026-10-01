"""The agent npm/npx shim refuses non-read-only calls in a worktree whose node_modules links outward (#9460).

Each scratch layout mirrors a dispatch worktree: a real git primary checkout with
real ``node_modules`` and ``site/node_modules`` holding a sentinel file, and a
``git worktree`` under ``.worktrees/dispatch/`` whose folders are symlinks to
them. A fake ``npm``/``npx`` behind the shim records each call, exits early on
``--version``/``--help`` like npm, and for tree-writing commands empties the
target ``node_modules`` the way ``npm ci`` does; no network and no real install
is involved. The real ``npm`` only runs harmless commands against scratch
directories.

Failing-before proof: every refusal test asserts the fake was never invoked and
the sentinel survived. Without the shim (``test_unguarded_fake_npm_destroys_the_sentinel``)
the same calls reach the fake and the sentinel is deleted.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from scripts.agent_runtime import npm_guard

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIM_SOURCE = REPO_ROOT / "scripts" / "agent_runtime" / "shims" / "npm"
GUARD_SOURCE = REPO_ROOT / "scripts" / "agent_runtime" / "npm_guard.py"
SENTINEL = "sentinel.txt"

FAKE_TOOL = r"""#!/usr/bin/env bash
# Fake npm/npx: log the call, exit early on version/help, emulate `npm ci` emptying its target.
tool="$(basename "$0")"
printf '%s\t%s\t%s\n' "$tool" "$PWD" "$*" >> "$FAKE_NPM_LOG"
target="$PWD"
command=""
args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
  case "${args[$i]}" in
    --version | -v | --help | -h) echo "fake-$tool-stdout $*"; exit 0 ;;
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
    ["isntall"],
    ["dedu"],
    ["installTest"],
    ["rebuild"],
    ["link"],
    ["audit", "fix"],
    ["--loglevel", "info", "install"],
    ["--logl", "info", "ci"],
    ["--no-audit", "ci"],
    ["--", "ci"],
    ["--cache", "x", "inst"],
]

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

# Held-out shapes from the independent review: each made real npm delete the
# sentinel past the previous, argument-parsing guard. (args, env, cwd, package.json override)
REVIEW_BYPASSES = {
    "env-location-GLOBAL": (["ci"], {"NPM_CONFIG_LOCATION": "GLOBAL"}, "."),
    "prefix-whitespace": (["ci", "--prefix= site "], {}, "."),
    "prefix-env-substitution": (["ci", "--prefix=${TARGET}"], {"TARGET": "site"}, "."),
    "extglob-workspace-member": (["ci"], {}, "packages/kit"),
    "git-dir-redirect": (["ci"], {"GIT_DIR": "/nonexistent"}, "site"),
    "version-switched-off": (["--version", "false", "ci"], {}, "."),
    "usage-switched-off": (["--help", "--no-usage", "ci"], {}, "."),
    "version-as-option-value": (["--cache", "--version", "ci"], {}, "."),
    "value-option-as-option-value": (["--cache", "--prefix", "inst", "run", "build"], {}, "."),
}

# Legitimate global installs: npm would not touch the worktree, but the guard no
# longer predicts that, so they are refused while the link exists.
GLOBAL_SHAPES = {
    "-g": (["install", "-g", "left-pad"], {}),
    "global-false-location-global": (["install", "--global=false", "--location=global", "left-pad"], {}),
    "env-global-location-project": (["install", "--location=project", "left-pad"], {"npm_config_global": "true"}),
    "npmrc-global": (["install", "left-pad"], {}),
}

# Clearly read-only calls that run in a protected worktree.
READ_ONLY = [
    [],
    ["ls"],
    ["ls", "--all"],
    ["run", "build"],
    ["run", "build", "--", "--watch"],
    ["test"],
    ["start"],
    ["view", "left-pad"],
    ["info", "left-pad", "version"],
    ["outdated"],
    ["explain", "left-pad"],
    ["audit"],
    ["audit", "--json"],
    ["config", "get", "registry"],
    ["config", "list"],
    ["cache", "verify"],
    ["version"],
    ["help", "ls"],
    ["root"],
    ["doctor"],
    ["--prefix", "site", "run", "build"],
    ["-C", "site", "run", "build"],
    ["-w", "site", "run", "build"],
    ["--prefix=site", "run", "build"],
    ["--loglevel=warn", "test"],
    ["--version"],
    ["-v"],
    ["--help"],
    ["ci", "--version"],
    ["--version", "ci"],
    ["install", "--help"],
    ["ci", "-h"],
    ["exec", "eslint", "--version"],
]

# Read-only in npm but not provably so without npm's tables: refused, with a reason.
FALSE_REFUSALS = {
    "view-ci": (["view", "ci"], "`ci` is an npm command that rewrites node_modules"),
    "help-install": (["help", "install"], "`install` is an npm command"),
    "run-ci": (["run", "ci"], "`ci` is an npm command"),
    "bare-option-before-command": (["--json", "run", "build"], "could not tell whether `build`"),
    "unknown-command": (["pkg", "get", "name"], "`pkg` is not on the guard's read-only allowlist"),
    "version-bump": (["version", "patch"], "`version patch` is not on the guard's read-only allowlist"),
    "config-set": (["config", "set", "x=y"], "`config set` is not on the guard's read-only allowlist"),
    "exec-after-bare-option": (["--json", "exec", "vitest"], "could not tell whether `vitest`"),
}

# The Claude adapter's npx fallback: its prompt and settings arguments mention
# npm, paths and install words in free text, which must not trip the guard.
CLAUDE_FALLBACK = [
    "@anthropic-ai/claude-code@latest",
    "-p",
    "--settings",
    '{"hooks":{"PreToolUse":[{"command":"/opt/tools/npm guard"}]}}',
    "--output-format",
    "stream-json",
    "--verbose",
    "--",
    "Fix the build: run npm ci, then /usr/bin/npm install and yarn add x.",
]

# npx and npm exec launching a tool that is not a package manager: they run an
# existing binary or fetch one into npm's own cache, never rewriting node_modules.
LAUNCHES = [
    ("npm", ["--prefix", "site", "exec", "--", "vitest", "run"]),
    ("npm", ["--prefix", "site", "exec", "--", "vitest", "run", "-t", "adds it"]),
    ("npm", ["--prefix", "site", "exec", "--", "tsc", "--noEmit"]),
    ("npm", ["--prefix", "site", "exec", "--", "playwright", "test", "e2e/atlas-practice.spec.ts"]),
    ("npm", ["x", "eslint", "."]),
    ("npx", ["playwright", "--version"]),
    ("npx", ["vitest", "-c", "vitest.config.ts"]),
    ("npx", ["@anthropic-ai/claude-code", "--version"]),
    ("npx", CLAUDE_FALLBACK),
]

# npx and npm exec naming a package manager (as a name, spec, scope or path, in
# a --key=value or in a -c/--call shell command) or an install word.
LAUNCH_REFUSALS = {
    "npx-npm-ci": ("npx", ["npm", "ci"], "`npm` names a package manager"),
    "npx-npx": ("npx", ["npx", "pnpm"], "`npx` names a package manager"),
    "npx-npm-install": ("npx", ["npm", "install"], "`npm` names a package manager"),
    "npx-npm-version-spec": ("npx", ["npm@10", "install"], "`npm@10` names a package manager"),
    "npx-yes-npm-ci": ("npx", ["--yes", "npm", "ci", "--ignore-scripts"], "`npm` names a package manager"),
    "npx-absolute-npm": ("npx", ["/usr/bin/npm", "ci"], "`/usr/bin/npm` names a package manager"),
    "npx-node-npm-cli": (
        "npx",
        ["node", "/usr/lib/node_modules/npm/bin/npm-cli.js", "ci"],
        "names a package manager",
    ),
    "npx-pnpm-cjs": ("npx", ["./tools/pnpm.cjs", "store", "path"], "`./tools/pnpm.cjs` names a package manager"),
    "npx-scoped-pnpm": ("npx", ["@pnpm/exe", "list"], "`@pnpm/exe` names a package manager"),
    "npx-corepack": ("npx", ["corepack", "pnpm", "i"], "`corepack` names a package manager"),
    "npx-yarn": ("npx", ["yarn"], "`yarn` names a package manager"),
    "npx-yarnpkg": ("npx", ["yarnpkg", "--frozen-lockfile"], "`yarnpkg` names a package manager"),
    "npx-bun": ("npx", ["bun", "x", "vite"], "`bun` names a package manager"),
    "npx-package-option": ("npx", ["-p", "npm", "-c", "npm ci"], "`npm` names a package manager"),
    "npx-call-shell": ("npx", ["-c", "echo start && npm ci"], "`npm` names a package manager"),
    "npx-call-shell-pnpm": ("npx", ["--call=cd site; pnpm i"], "`pnpm` names a package manager"),
    "npx-call-subshell": ("npx", ["-c", "node $(which npm) ci"], "`npm` names a package manager"),
    "npx-version-then-pnpm": ("npx", ["--version", "pnpm", "install"], "`pnpm` names a package manager"),
    "npx-install-word": ("npx", ["some-tool", "install"], "`install` is an install word"),
    "npx-call-install-word": ("npx", ["-c", "some-tool add left-pad"], "`add` is an install word"),
    "exec-pnpm-install": ("npm", ["exec", "--", "pnpm", "install"], "`pnpm` names a package manager"),
    "exec-yarn-add": ("npm", ["exec", "--", "yarn", "add", "x"], "`yarn` names a package manager"),
    "exec-package-npm": ("npm", ["exec", "--package=npm", "--", "npm", "ci"], "`npm` names a package manager"),
    "x-npm-ci": ("npm", ["x", "npm", "ci"], "`npm` names a package manager"),
    "exec-call-install": ("npm", ["exec", "-c", "npm install"], "`npm` names a package manager"),
    "exec-yarn": ("npm", ["exec", "yarn"], "`yarn` names a package manager"),
    "exec-yarn-version": ("npm", ["exec", "--", "yarn", "--version"], "`yarn` names a package manager"),
    "exec-prefix-install-word": (
        "npm",
        ["--prefix", "site", "exec", "--", "some-tool", "ci"],
        "`ci` is an install word",
    ),
}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _git(cwd: Path, *args: str) -> None:
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(cwd),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, timeout=60)


def _scratch_checkouts(tmp_path: Path) -> tuple[Path, Path]:
    """A real primary checkout with real node_modules and a dispatch git worktree."""
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    _git(primary, "commit", "-q", "--allow-empty", "-m", "init")
    _write_json(primary / "package.json", {"name": "primary", "workspaces": ["packages/*"]})
    for folder in (primary / "node_modules", primary / "site" / "node_modules"):
        folder.mkdir(parents=True)
        (folder / SENTINEL).write_text("keep\n", encoding="utf-8")
        (folder / "dep").mkdir()

    worktree = primary / ".worktrees" / "dispatch" / "agent" / "task"
    _git(primary, "worktree", "add", "-q", "--detach", str(worktree))
    _write_json(worktree / "package.json", {"name": "worktree", "workspaces": ["packages/*"]})
    _write_json(worktree / "packages" / "kit" / "package.json", {"name": "@lu/kit"})
    _write_json(worktree / "site" / "package.json", {"name": "site"})
    (worktree / "site" / "src").mkdir()
    return primary, worktree


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

    primary, worktree = _scratch_checkouts(tmp_path)
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


def _assert_passed_through(layout, proc, tool: str, args: list[str], cwd: Path, exit_code: int) -> None:
    assert proc.returncode == exit_code, proc.stderr
    assert proc.stdout == f"fake-{tool}-stdout {' '.join(args)}\n"
    assert _fake_calls(layout) == [f"{tool}\t{cwd}\t{' '.join(args)}"]


# --- refusals in a worktree whose node_modules links outward -----------------


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


@pytest.mark.parametrize("case", sorted(REVIEW_BYPASSES))
def test_review_bypass_shapes_are_refused(layout, case):
    args, env, relative_cwd = REVIEW_BYPASSES[case]
    if case == "extglob-workspace-member":
        _write_json(layout["worktree"] / "package.json", {"name": "worktree", "workspaces": ["packages/@(kit|app)"]})
    _assert_refused(layout, _run(layout, "npm", args, layout["worktree"] / relative_cwd, env))


@pytest.mark.parametrize("case", sorted(GLOBAL_SHAPES))
def test_global_installs_are_refused_while_the_link_exists(layout, case):
    args, env = GLOBAL_SHAPES[case]
    if case == "npmrc-global":
        (layout["worktree"] / ".npmrc").write_text("global=true\n", encoding="utf-8")
    proc = _run(layout, "npm", args, layout["worktree"], env)
    _assert_refused(layout, proc)
    assert "global installs (-g)" in proc.stderr
    assert "run the command outside this worktree" in proc.stderr


@pytest.mark.parametrize("case", sorted(LAUNCH_REFUSALS))
def test_npx_and_npm_exec_launching_a_package_manager_are_refused(layout, case):
    tool, args, reason = LAUNCH_REFUSALS[case]
    proc = _run(layout, tool, args, layout["worktree"])
    _assert_refused(layout, proc)
    assert reason in proc.stderr


@pytest.mark.parametrize("case", sorted(FALSE_REFUSALS))
def test_unclassifiable_read_only_calls_are_refused_with_the_reason(layout, case):
    args, reason = FALSE_REFUSALS[case]
    proc = _run(layout, "npm", args, layout["worktree"])
    _assert_refused(layout, proc)
    assert reason in proc.stderr


def test_refusal_names_every_link_to_remove(layout):
    worktree = layout["worktree"]
    proc = _run(layout, "npm", ["ci"], worktree / "site")
    assert f"unlink {worktree / 'node_modules'} && unlink {worktree / 'site' / 'node_modules'}" in proc.stderr
    assert f"resolves to {layout['primary'] / 'site' / 'node_modules'}" in proc.stderr


def test_one_outward_link_is_enough(layout):
    worktree = layout["worktree"]
    (worktree / "node_modules").unlink()
    (worktree / "node_modules").mkdir()
    proc = _run(layout, "npm", ["ci"], worktree)
    _assert_refused(layout, proc)
    assert f"unlink {worktree / 'site' / 'node_modules'}`" in proc.stderr


def test_dangling_outward_link_is_refused(layout):
    worktree = layout["worktree"]
    (worktree / "node_modules").unlink()
    (worktree / "node_modules").symlink_to(layout["tmp"] / "missing")
    (worktree / "site" / "node_modules").unlink()
    _assert_refused(layout, _run(layout, "npm", ["ci"], worktree))
    assert not (layout["tmp"] / "missing").exists()


def test_run_script_calling_npm_ci_is_refused_through_path(layout):
    """A run-script's inner `npm ci` resolves through PATH, so the shim sees it."""
    proc = _run(layout, "npm", ["run", "reinstall"], layout["worktree"], {"FAKE_RUN_SCRIPT": "npm ci"})
    assert proc.returncode == 1
    assert "refused `npm ci`" in proc.stderr
    assert _fake_calls(layout) == [f"npm\t{layout['worktree']}\trun reinstall"]
    assert _sentinels_intact(layout)


# --- calls that run ------------------------------------------------------------


@pytest.mark.parametrize("args", READ_ONLY, ids=lambda value: " ".join(value) or "bare")
@pytest.mark.parametrize("relative_cwd", [".", "site"])
def test_read_only_calls_pass_through_in_a_protected_worktree(layout, args, relative_cwd):
    cwd = layout["worktree"] / relative_cwd
    early = any(flag in args for flag in ("--version", "-v", "--help", "-h"))
    proc = _run(layout, "npm", args, cwd, {"FAKE_NPM_EXIT": "7"})
    _assert_passed_through(layout, proc, "npm", args, cwd, 0 if early else 7)
    if not early:
        assert proc.stderr == "fake-npm-stderr\n"
    assert _sentinels_intact(layout)


@pytest.mark.parametrize("args", [["--version"], ["-v"], ["--help"], ["-h"]], ids=" ".join)
def test_npx_version_and_help_pass_through(layout, args):
    proc = _run(layout, "npx", args, layout["worktree"])
    _assert_passed_through(layout, proc, "npx", args, layout["worktree"], 0)


def _launch_id(value):
    return value if isinstance(value, str) else " ".join(value)[:60]


@pytest.mark.parametrize("tool,args", LAUNCHES, ids=_launch_id)
@pytest.mark.parametrize("relative_cwd", [".", "site"])
def test_npx_and_npm_exec_launching_a_tool_pass_through(layout, tool, args, relative_cwd):
    """Arguments, stdin, stdout, stderr and the exit code reach the real tool unchanged."""
    for name in ("npm", "npx"):
        (layout["fake_bin"] / name).write_text(
            '#!/usr/bin/env bash\nprintf "%s\\0" "$@" > "$FAKE_NPM_LOG"\ncat\necho "fake-stderr" >&2\nexit 9\n',
            encoding="utf-8",
        )
    cwd = layout["worktree"] / relative_cwd
    proc = subprocess.run(
        [str(layout["shim_dir"] / tool), *args],
        cwd=cwd,
        env={
            "PATH": f"{layout['shim_dir']}:{layout['fake_bin']}:/usr/bin:/bin",
            "HOME": str(layout["tmp"]),
            "FAKE_NPM_LOG": str(layout["log"]),
        },
        input="piped\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert (proc.returncode, proc.stdout, proc.stderr) == (9, "piped\n", "fake-stderr\n")
    assert layout["log"].read_text(encoding="utf-8").split("\0")[:-1] == args
    assert _sentinels_intact(layout)


ANYTHING = [
    list(args)
    for args in dict.fromkeys(
        tuple(args)
        for args in DENOMINATOR
        + EQUIVALENTS
        + [args for args, _, _ in REVIEW_BYPASSES.values()]
        + [args for args, _ in GLOBAL_SHAPES.values()]
        + [args for args, _ in FALSE_REFUSALS.values()]
    )
]


@pytest.mark.parametrize("args", ANYTHING, ids=" ".join)
def test_any_call_passes_through_with_real_node_modules(layout, args):
    _make_real(layout)
    cwd = layout["worktree"]
    proc = _run(layout, "npm", args, cwd, {"FAKE_NPM_EXIT": "5"})
    early = any(flag in args for flag in ("--version", "-v", "--help", "-h"))
    _assert_passed_through(layout, proc, "npm", args, cwd, 0 if early else 5)
    if not early:
        assert proc.stderr == "fake-npm-stderr\n"
    assert _sentinels_intact(layout)


@pytest.mark.parametrize("command", DENOMINATOR, ids=" ".join)
@pytest.mark.parametrize("location", sorted(LOCATIONS))
def test_destructive_command_into_real_node_modules_installs(layout, command, location):
    _make_real(layout)
    relative_cwd, placement = LOCATIONS[location]
    cwd = layout["worktree"] / relative_cwd
    args = [*command, *placement]
    proc = _run(layout, "npm", args, cwd, {"FAKE_NPM_EXIT": "5"})
    _assert_passed_through(layout, proc, "npm", args, cwd, 5)
    assert proc.stderr == "fake-npm-stderr\n"
    assert _sentinels_intact(layout)


@pytest.mark.parametrize("tool,args", [("npx", ["pnpm", "install"]), ("npm", ["exec", "yarn"])], ids=str)
def test_npx_passes_through_with_real_node_modules(layout, tool, args):
    _make_real(layout)
    proc = _run(layout, tool, args, layout["worktree"], {"FAKE_NPM_EXIT": "3"})
    _assert_passed_through(layout, proc, tool, args, layout["worktree"], 3)


def test_symlinks_inside_the_same_worktree_pass(layout):
    worktree = layout["worktree"]
    for relative in ("node_modules", "site/node_modules"):
        (worktree / relative).unlink()
        (worktree / "vendor" / relative).mkdir(parents=True)
        (worktree / relative).symlink_to(worktree / "vendor" / relative)
    proc = _run(layout, "npm", ["ci"], worktree / "site", {"FAKE_NPM_EXIT": "4"})
    _assert_passed_through(layout, proc, "npm", ["ci"], worktree / "site", 4)
    assert _sentinels_intact(layout)


def test_outside_any_worktree_passes_through(layout):
    """Residual: with no git worktree there is nothing to inspect, so the call runs."""
    elsewhere = layout["tmp"] / "elsewhere"
    elsewhere.mkdir()
    proc = _run(layout, "npm", ["ci"], elsewhere, {"FAKE_NPM_EXIT": "6"})
    _assert_passed_through(layout, proc, "npm", ["ci"], elsewhere, 6)


def test_primary_checkout_with_real_node_modules_passes_through(layout):
    proc = _run(layout, "npm", ["ls"], layout["primary"])
    _assert_passed_through(layout, proc, "npm", ["ls"], layout["primary"], 0)


def test_stdin_reaches_the_real_tool(layout):
    reader = layout["fake_bin"] / "npm"
    reader.write_text("#!/usr/bin/env bash\ncat\n", encoding="utf-8")
    for cwd in (layout["worktree"], layout["primary"]):
        proc = subprocess.run(
            [str(layout["shim_dir"] / "npm"), "ls"],
            cwd=cwd,
            env={"PATH": f"{layout['shim_dir']}:{layout['fake_bin']}:/usr/bin:/bin", "HOME": str(layout["tmp"])},
            input="piped\n",
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert (proc.returncode, proc.stdout) == (0, "piped\n")


@pytest.mark.parametrize("args", [["ci"], ["install"], ["--prefix", "site", "ci"], ["prune"]], ids=" ".join)
def test_unguarded_fake_npm_destroys_the_sentinel(layout, args):
    """Control: without the shim the same call empties the primary's folder."""
    proc = _run(layout, "npm", args, layout["worktree"], shim=False)
    assert proc.returncode == 0
    assert not _sentinels_intact(layout)


# --- the real npm, harmless calls against scratch directories only -----------


def _real_npm() -> str | None:
    for entry in os.environ.get("AGENT_ORIGINAL_PATH", os.environ.get("PATH", "")).split(os.pathsep):
        if not entry or entry.endswith(os.path.join("agent_runtime", "shims")):
            continue
        candidate = Path(entry) / "npm"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _run_real(layout: dict[str, Path], args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    real_npm = Path(_real_npm())
    path_entries = [str(layout["shim_dir"]), str(real_npm.parent), "/usr/bin", "/bin"]
    env = {
        "PATH": os.pathsep.join(path_entries),
        "HOME": str(layout["tmp"]),
        "npm_config_update_notifier": "false",
        "npm_config_offline": "true",
    }
    return subprocess.run(
        [str(layout["shim_dir"] / "npm"), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


@pytest.mark.skipif(_real_npm() is None, reason="needs a real npm to execute a package.json run-script")
def test_real_npm_run_script_inner_npm_ci_hits_the_shim(layout):
    """Real npm builds the run-script PATH from the caller's PATH, keeping the shim first."""
    worktree = layout["worktree"]
    _write_json(worktree / "package.json", {"name": "worktree", "scripts": {"reinstall": "npm ci"}})
    proc = _run_real(layout, ["run", "reinstall"], worktree)
    assert proc.returncode != 0
    assert "refused `npm ci`" in proc.stderr
    assert _sentinels_intact(layout)


@pytest.mark.skipif(_real_npm() is None, reason="needs a real npm")
@pytest.mark.parametrize("args", [["ci", "--version"], ["--version", "ci"], ["install", "--help"]], ids=" ".join)
def test_real_npm_early_exits_run_and_leave_the_link_target_intact(layout, args):
    proc = _run_real(layout, args, layout["worktree"])
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip()
    assert "refused" not in proc.stderr
    assert _sentinels_intact(layout)


# --- shim plumbing --------------------------------------------------------------


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


# --- unit tests of the guard ---------------------------------------------------


@pytest.mark.parametrize(
    "tool,args,allowed",
    [
        ("npm", [], True),
        ("npm", ["--prefix", "site"], True),
        ("npm", ["-g"], True),
        ("npm", ["--", "ls"], True),
        ("npm", ["--json", "ls"], True),
        ("npm", ["ci", "--version"], True),
        ("npm", ["ci", "--", "--version"], False),
        ("npm", ["--version", "true", "ci"], False),
        ("npm", ["-v=false", "ci"], False),
        ("npm", ["--prefix", "-v", "ci"], False),
        ("npm", ["--json", "true", "inst"], False),
        ("npm", ["--json", "ls", "left-pad"], False),
        ("npm", ["--json", "config", "get"], False),
        ("npm", ["version", "--json"], True),
        ("npm", ["cache", "clean"], False),
        ("npm", ["LS"], False),
        ("npx", ["--version"], True),
        ("npx", ["-y", "--version"], True),
        ("npx", [], True),
        ("npx", ["vitest", "--reporter=verbose"], True),
        ("npx", ["--package=@scope/tool@1.2.3", "tool"], True),
        ("npx", ["--package=npm@10", "tool"], False),
        ("npx", ["-c=npm ci"], False),
        ("npx", ["NPM"], False),
        ("npx", ["pnpm.exe"], False),
        ("npx", ["npm:pnpm@9"], False),
        ("npx", ["npm-check-updates"], True),
        ("npx", ["tool", "--save=install"], False),
        ("npx", ["-c", "tool run build"], True),
        ("npm", ["exec"], True),
        ("npm", ["--json", "exec", "ls"], True),
        ("npm", ["exec", "--", "tool", "audit", "fix"], False),
        ("npm", ["run", "x", "ci"], False),
    ],
    ids=lambda value: value if isinstance(value, str) else (" ".join(value) if isinstance(value, list) else str(value)),
)
def test_refusal_reason(tool, args, allowed):
    assert (npm_guard.refusal_reason(tool, args) is None) is allowed


def test_outward_links_reports_the_symlink_and_its_target(layout):
    worktree, primary = layout["worktree"], layout["primary"]
    assert npm_guard.outward_links(worktree) == [
        (worktree / "node_modules", primary / "node_modules"),
        (worktree / "site" / "node_modules", primary / "site" / "node_modules"),
    ]
    assert npm_guard.outward_links(primary) == []


def test_outward_link_through_a_symlinked_parent_names_the_parent(layout):
    worktree, primary = layout["worktree"], layout["primary"]
    shutil.rmtree(worktree / "site")
    (worktree / "site").symlink_to(primary / "site")
    (worktree / "node_modules").unlink()
    assert npm_guard.outward_links(worktree) == [(worktree / "site", primary / "site" / "node_modules")]


def test_worktree_root_ignores_git_environment(layout, monkeypatch):
    monkeypatch.setenv("GIT_DIR", str(layout["primary"] / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(layout["tmp"]))
    assert npm_guard.worktree_root(layout["worktree"] / "site" / "src") == layout["worktree"]
    assert npm_guard.worktree_root(layout["tmp"]) is None


def test_main_rejects_unknown_tool(capsys):
    assert npm_guard.main(["yarn", "install"]) == 2
    assert "usage" in capsys.readouterr().err


def test_protected_paths_match_delegate_provisioning():
    """The guard's list mirrors the node_modules links delegate creates; fail when they diverge."""
    from scripts import delegate

    tree = ast.parse(textwrap.dedent(inspect.getsource(delegate._provision_data_symlinks)))
    loops = [node for node in ast.walk(tree) if isinstance(node, ast.For) and isinstance(node.iter, ast.Tuple)]
    linked = [element.value for loop in loops for element in loop.iter.elts if isinstance(element, ast.Constant)]
    assert linked, "could not find the provisioned path tuple in _provision_data_symlinks"
    assert tuple(path for path in linked if Path(path).name == "node_modules") == npm_guard.PROTECTED_PATHS


def test_delegate_provisioned_worktree_is_protected(tmp_path):
    from scripts import delegate

    primary, worktree = _scratch_checkouts(tmp_path)
    assert npm_guard.outward_links(worktree) == []
    delegate._provision_data_symlinks(worktree, primary)
    assert [link for link, _ in npm_guard.outward_links(worktree)] == [
        worktree / relative for relative in npm_guard.PROTECTED_PATHS
    ]
    assert npm_guard.main(["npm", "ci"], cwd=worktree) == 1


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
