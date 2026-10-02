"""The agent npm/npx shim refuses non-read-only calls in a worktree whose node_modules links outward (#9460).

Each scratch layout mirrors a dispatch worktree: a real git primary checkout with
real ``node_modules`` and ``site/node_modules`` holding a sentinel file, and a
``git worktree`` under ``.worktrees/dispatch/`` whose folders are symlinks to
them. A fake ``npm``/``npx`` behind the shim records each call, exits early on
``--version``/``--help`` like npm, and for tree-writing commands empties the
target ``node_modules`` the way ``npm ci`` does; no network and no real install
is involved. The real ``npm`` runs offline and only against scratch
directories: harmless commands, and in the unguarded controls a real
``npm ci`` that empties the scratch sentinel folder.

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
NPX_SOURCE = SHIM_SOURCE.parent / "npx"
GUARD_SOURCE = REPO_ROOT / "scripts" / "agent_runtime" / "npm_guard.py"
SENTINEL = "sentinel.txt"

FAKE_TOOL = r"""#!/usr/bin/env bash
# Fake npm/npx: log the call, exit early on version/help, emulate `npm ci` emptying its target.
tool="$(basename "$0")"
printf '%s\t%s\t%s\n' "$tool" "$PWD" "$*" >> "$FAKE_NPM_LOG"
# Like npm, the default prefix is the nearest directory holding package.json or node_modules.
target="$PWD"
while [[ "$target" != / && ! -e "$target/package.json" && ! -e "$target/node_modules" ]]; do
  target="$(dirname "$target")"
done
[[ "$target" == / ]] && target="$PWD"
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
    # Adapted for the closed exec rule: the unknown option itself now refuses.
    "exec-after-bare-option": (["--json", "exec", "vitest"], "`--json` is refused"),
}

# npx/npm exec calls that are harmless but refused by the closed rule (documented false positives).
EXEC_FALSE_REFUSALS = {
    "program-off-the-allowlist": ("npx", ["eslint", "."], "`eslint` is not on the allowlist"),
    "npm-x-off-the-allowlist": ("npm", ["x", "eslint", "."], "`eslint` is not on the allowlist"),
    "playwright-install": ("npx", ["playwright", "install", "chromium"], "`install` is an install word"),
    "no-before-the-program": ("npx", ["--no", "vitest"], "could not tell whether `vitest` is the program"),
    "workspace-option": ("npm", ["-w", "site", "exec", "--", "vitest"], "`-w` is refused"),
    "program-option-before-dashdash": ("npm", ["exec", "vitest", "--run"], "`--run` is refused"),
    "range-version": ("npx", ["vitest@>=3"], "`vitest@>=3` is not on the allowlist"),
    "no-program": ("npx", [], "npx names no program"),
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

# npx and npm exec running an allowlisted program: they run an existing binary
# or fetch one into npm's own cache, never rewriting node_modules.
LAUNCHES = [
    ("npm", ["--prefix", "site", "exec", "--", "vitest", "run"]),
    ("npm", ["--prefix", "site", "exec", "--", "vitest", "run", "-t", "adds it"]),
    ("npm", ["--prefix", "site", "exec", "--", "tsc", "--noEmit"]),
    ("npm", ["--prefix", "site", "exec", "--", "playwright", "test", "e2e/atlas-practice.spec.ts"]),
    ("npm", ["--prefix=site", "exec", "--yes", "--no-fund", "--", "tsc", "--noEmit"]),
    ("npm", ["-C", "site", "x", "vitest", "run"]),
    ("npx", ["playwright", "--version"]),
    ("npx", ["playwright", "test", "ui-policy"]),
    ("npx", ["vitest"]),
    ("npx", ["vitest", "-c", "vitest.config.ts"]),
    ("npx", ["vitest@3", "run", "--reporter=verbose"]),
    ("npx", ["./node_modules/.bin/vitest", "run"]),
    ("npx", ["-y", "--no-fund", "--", "vitest", "run"]),
    ("npx", ["--no", "--", "tsc", "--noEmit"]),
    ("npx", ["--yes", "markdownlint-cli2", "docs/README.md"]),
    ("npx", ["@anthropic-ai/claude-code", "--version"]),
    ("npx", ["@anthropic-ai/claude-code@latest", "--version"]),
    ("npx", CLAUDE_FALLBACK),
]

# The independent review's reproductions: real npm resolved the escaped shell
# text to `npm ci` and emptied the shared folder past the text-classifying guard.
ESCAPED_NPM_CI = "/usr/bin/n\\pm c\\i --ignore-scripts --no-audit --no-fund"
REVIEW_SHELL_CALLS = {
    "npm-exec-c": ("npm", ["exec", "-c", ESCAPED_NPM_CI]),
    "npm-exec-call-eq": ("npm", ["exec", f"--call={ESCAPED_NPM_CI}"]),
    "npx-c": ("npx", ["-c", ESCAPED_NPM_CI]),
    "npx-call-eq": ("npx", [f"--call={ESCAPED_NPM_CI}"]),
}

# npx and npm exec reaching a package manager through a shell, an interpreter,
# a package option or shell text: refused without reading any of the text.
LAUNCH_REFUSALS = {
    **{
        f"review-{case}": (tool, args, "is refused: as its own options")
        for case, (tool, args) in REVIEW_SHELL_CALLS.items()
    },
    "npx-sh-c": ("npx", ["sh", "-c", "npm ci"], "`sh` is not on the allowlist"),
    "npx-bash-c": ("npx", ["bash", "-c", "npm ci"], "`bash` is not on the allowlist"),
    "exec-bash-c": ("npm", ["exec", "--", "bash", "-c", "n\\pm c\\i"], "`bash` is not on the allowlist"),
    "npx-dash-c": ("npx", ["dash", "-c", "npm ci"], "`dash` is not on the allowlist"),
    "npx-node-e": ("npx", ["node", "-e", "require('child_process').execSync('npm ci')"], "`node` is not on"),
    "npx-env-npm-ci": ("npx", ["env", "npm", "ci"], "`env` is not on the allowlist"),
    "exec-env-npm-ci": ("npm", ["exec", "--", "env", "npm", "ci"], "`env` is not on the allowlist"),
    "npx-python": ("npx", ["python3", "-c", "import os; os.system('npm ci')"], "`python3` is not on"),
    "npx-p-npm": ("npx", ["-p", "npm", "npm", "ci"], "`-p` is refused"),
    "npx-package-eq": ("npx", ["--package=npm@10", "npm", "ci"], "`--package` is refused"),
    "npx-yes-npm-ci": ("npx", ["--yes", "npm", "ci"], "`npm` is not on the allowlist"),
    "npx-npm-ci": ("npx", ["npm", "ci"], "`npm` is not on the allowlist"),
    "npx-npx": ("npx", ["npx", "pnpm"], "`npx` is not on the allowlist"),
    "npx-npm-version-spec": ("npx", ["npm@10", "install"], "`npm@10` is not on the allowlist"),
    "npx-absolute-npm": ("npx", ["/usr/bin/npm", "ci"], "`/usr/bin/npm` is not on the allowlist"),
    "npx-escaped-npm": ("npx", ["/usr/bin/n\\pm", "c\\i"], "`/usr/bin/n\\pm` is not on the allowlist"),
    "npx-quoted-npm": ("npx", ["'npm'", "ci"], "`'npm'` is not on the allowlist"),
    "npx-ansi-c-quoted": ("npx", ["-c", "$'\\x6epm' ci"], "`-c` is refused"),
    "npx-parameter-expansion": ("npx", ["-c", "x=npm; ${x} ci"], "`-c` is refused"),
    "npx-command-substitution": ("npx", ["--call", "$(printf npm) ci"], "`--call` is refused"),
    "npx-eval": ("npx", ["-c", "eval 'n''pm ci'"], "`-c` is refused"),
    "npx-shell-option": ("npx", ["--shell=/bin/sh", "vitest"], "`--shell` is refused"),
    "npx-script-shell": ("npx", ["--script-shell", "/usr/bin/npm", "vitest"], "`--script-shell` is refused"),
    "npx-node-options": ("npx", ["--node-options=--require=./x.js", "vitest"], "`--node-options` is refused"),
    "npx-unknown-option": ("npx", ["--loglevel", "silent", "vitest"], "`--loglevel` is refused"),
    "npx-terminator-then-shell": ("npx", ["--", "sh", "-c", "npm ci"], "`sh` is not on the allowlist"),
    "npx-alias-spec": ("npx", ["vitest@npm:pnpm"], "`vitest@npm:pnpm` is not on the allowlist"),
    "npx-git-spec": ("npx", ["github:someone/vitest"], "`github:someone/vitest` is not on the allowlist"),
    "npx-foreign-scope": ("npx", ["@someone/vitest"], "`@someone/vitest` is not on the allowlist"),
    "npx-script-extension": ("npx", ["./tools/pnpm.cjs", "store", "path"], "`./tools/pnpm.cjs` is not on"),
    "npx-corepack": ("npx", ["corepack", "pnpm", "i"], "`corepack` is not on the allowlist"),
    "npx-yarn": ("npx", ["yarn"], "`yarn` is not on the allowlist"),
    "npx-bun": ("npx", ["bun", "x", "vite"], "`bun` is not on the allowlist"),
    "npx-deno": ("npx", ["deno", "run", "npm:npm", "ci"], "`deno` is not on the allowlist"),
    "npx-version-then-pnpm": ("npx", ["--version", "pnpm", "install"], "`--version` is refused"),
    "npx-allowed-program-install-word": ("npx", ["vitest", "install"], "`install` is an install word"),
    "npx-allowed-program-names-npm": ("npx", ["vitest", "--config=/usr/bin/npm"], "`--config=/usr/bin/npm` names a"),
    "npx-prefix-swallows-option": ("npx", ["--prefix", "-c", "npm ci"], "`--prefix` must be followed"),
    "exec-pnpm-install": ("npm", ["exec", "--", "pnpm", "install"], "`pnpm` is not on the allowlist"),
    "exec-package-npm": ("npm", ["exec", "--package=npm", "--", "npm", "ci"], "`--package` is refused"),
    "x-npm-ci": ("npm", ["x", "npm", "ci"], "`npm` is not on the allowlist"),
    "exec-call-after-program": ("npm", ["exec", "vitest", "-c", "npm ci"], "`-c` is refused"),
    "exec-call-before-subcommand": ("npm", ["-c", "npm ci", "exec", "vitest"], "`-c` is refused"),
    "exec-without-program": ("npm", ["exec"], "npm exec names no program"),
    "exec-after-read-only-word": ("npm", ["--json", "exec", "run", "-c", "npm ci"], "`--json` is refused"),
    "exec-prefix-install-word": (
        "npm",
        ["--prefix", "site", "exec", "--", "vitest", "ci"],
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


def _scratch_checkouts(tmp_path: Path, name: str = "task") -> tuple[Path, Path]:
    """A real primary checkout with real node_modules and a dispatch git worktree named ``name``."""
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    _git(primary, "commit", "-q", "--allow-empty", "-m", "init")
    _write_json(primary / "package.json", {"name": "primary", "workspaces": ["packages/*"]})
    for folder in (primary / "node_modules", primary / "site" / "node_modules"):
        folder.mkdir(parents=True)
        (folder / SENTINEL).write_text("keep\n", encoding="utf-8")
        (folder / "dep").mkdir()

    worktree = primary / ".worktrees" / "dispatch" / "agent" / name
    _git(primary, "worktree", "add", "-q", "--detach", str(worktree))
    _write_json(worktree / "package.json", {"name": "worktree", "workspaces": ["packages/*"]})
    _write_json(worktree / "packages" / "kit" / "package.json", {"name": "@lu/kit"})
    _write_json(worktree / "site" / "package.json", {"name": "site"})
    (worktree / "site" / "src").mkdir()
    return primary, worktree


def _build_layout(tmp_path: Path, worktree_name: str = "task") -> dict[str, Path]:
    """Scratch primary + dispatch worktree with symlinked node_modules folders."""
    tooling = tmp_path / "tooling"
    shim_dir = tooling / "scripts" / "agent_runtime" / "shims"
    shim_dir.mkdir(parents=True)
    shutil.copy2(SHIM_SOURCE, shim_dir / "npm")
    shutil.copy2(NPX_SOURCE, shim_dir / "npx")
    shutil.copy2(GUARD_SOURCE, tooling / "scripts" / "agent_runtime" / "npm_guard.py")
    (tooling / ".venv" / "bin").mkdir(parents=True)
    (tooling / ".venv" / "bin" / "python").symlink_to(sys.executable)

    fake_bin = tmp_path / "fakebin"
    fake_bin.mkdir()
    for name in ("npm", "npx"):
        fake = fake_bin / name
        fake.write_text(FAKE_TOOL, encoding="utf-8")
        fake.chmod(0o755)

    primary, worktree = _scratch_checkouts(tmp_path, worktree_name)
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


@pytest.fixture()
def layout(tmp_path: Path) -> dict[str, Path]:
    return _build_layout(tmp_path)


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
@pytest.mark.parametrize("relative_cwd", [".", "site"])
def test_npx_and_npm_exec_outside_the_closed_rule_are_refused(layout, case, relative_cwd):
    tool, args, reason = LAUNCH_REFUSALS[case]
    proc = _run(layout, tool, args, layout["worktree"] / relative_cwd)
    _assert_refused(layout, proc)
    assert reason in proc.stderr
    assert "only run allowlisted programs" in proc.stderr


@pytest.mark.parametrize("case", sorted(EXEC_FALSE_REFUSALS))
def test_harmless_exec_calls_outside_the_closed_rule_are_refused_with_the_reason(layout, case):
    tool, args, reason = EXEC_FALSE_REFUSALS[case]
    proc = _run(layout, tool, args, layout["worktree"])
    _assert_refused(layout, proc)
    assert reason in proc.stderr


@pytest.mark.parametrize("case", sorted(FALSE_REFUSALS))
def test_unclassifiable_read_only_calls_are_refused_with_the_reason(layout, case):
    args, reason = FALSE_REFUSALS[case]
    proc = _run(layout, "npm", args, layout["worktree"])
    _assert_refused(layout, proc)
    assert reason in proc.stderr


def test_link_beside_its_own_directory_is_refused(layout):
    """Inward to the worktree but outside ``site``: from the ``site`` ancestor it points outward."""
    worktree = layout["worktree"]
    (worktree / "node_modules").unlink()
    (worktree / "node_modules").mkdir()
    (worktree / "site" / "node_modules").unlink()
    (worktree / "vendor" / "node_modules").mkdir(parents=True)
    (worktree / "site" / "node_modules").symlink_to(worktree / "vendor" / "node_modules")
    proc = _run(layout, "npm", ["ci"], worktree / "site")
    assert proc.returncode == 1 and _fake_calls(layout) == []
    assert f"outside {worktree / 'site'}." in proc.stderr


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
    _assert_forwarded_unchanged(layout, tool, args, layout["worktree"] / relative_cwd)


def test_claude_adapter_npx_fallback_passes_through(layout, monkeypatch):
    """The adapter's own npx command line (no native claude), as build_invocation assembles it."""
    from scripts.agent_runtime.adapters import claude as claude_adapter

    monkeypatch.setattr(claude_adapter, "_default_claude_bin", lambda: None)
    monkeypatch.setattr(claude_adapter.shutil, "which", lambda name, *a, **k: "/usr/bin/npx" if name == "npx" else None)
    monkeypatch.setattr(claude_adapter, "_ensure_supported_claude_cli_version", lambda prefix: (2, 1, 200))
    plan = claude_adapter.ClaudeAdapter().build_invocation(
        prompt="Fix the build: run npm ci, then /usr/bin/npm install and yarn add x.",
        mode="workspace-write",
        cwd=layout["worktree"],
        model="claude-sonnet-5-5",
        task_id="task-9460",
        session_id=None,
        tool_config={},
    )
    assert plan.cmd[:2] == ["npx", "@anthropic-ai/claude-code@latest"]
    assert npm_guard.refusal_reason("npx", plan.cmd[1:]) is None
    for relative_cwd in (".", "site"):
        layout["log"].unlink(missing_ok=True)
        _assert_forwarded_unchanged(layout, "npx", plan.cmd[1:], layout["worktree"] / relative_cwd)


def _assert_forwarded_unchanged(layout, tool: str, args: list[str], cwd: Path) -> None:
    for name in ("npm", "npx"):
        (layout["fake_bin"] / name).write_text(
            '#!/usr/bin/env bash\nprintf "%s\\0" "$@" > "$FAKE_NPM_LOG"\ncat\necho "fake-stderr" >&2\nexit 9\n',
            encoding="utf-8",
        )
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
    """Each link stays inside the directory holding it (``site/node_modules`` inside ``site``).

    Changed with the filesystem walk: without a git root there is no worktree
    boundary, so a link is inward only relative to every ancestor that holds it;
    ``site/node_modules`` pointing to ``vendor/`` beside ``site`` is now refused.
    """
    worktree = layout["worktree"]
    for relative in ("node_modules", "site/node_modules"):
        link = worktree / relative
        link.unlink()
        (link.parent / "vendor" / "node_modules").mkdir(parents=True)
        link.symlink_to(link.parent / "vendor" / "node_modules")
    proc = _run(layout, "npm", ["ci"], worktree / "site", {"FAKE_NPM_EXIT": "4"})
    _assert_passed_through(layout, proc, "npm", ["ci"], worktree / "site", 4)
    assert _sentinels_intact(layout)


def test_outside_any_worktree_passes_through(layout):
    """No ancestor has an outward link, so there is nothing to protect and the call runs."""
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


def _run_real(
    layout: dict[str, Path], args: list[str], cwd: Path, tool: str = "npm", *, shim: bool = True
) -> subprocess.CompletedProcess[str]:
    real_npm = Path(_real_npm())
    path_entries = [str(layout["shim_dir"]), str(real_npm.parent), "/usr/bin", "/bin"]
    env = {
        "PATH": os.pathsep.join(path_entries if shim else path_entries[1:]),
        "HOME": str(layout["tmp"]),
        "npm_config_update_notifier": "false",
        "npm_config_offline": "true",
    }
    return subprocess.run(
        [str(layout["shim_dir"] / tool) if shim else str(real_npm.parent / tool), *args],
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


def _lockable(layout: dict[str, Path]) -> None:
    """Give the worktree and site/ a package.json and an empty lockfile, so real `npm ci` runs offline."""
    for folder, name in ((layout["worktree"], "worktree"), (layout["worktree"] / "site", "site")):
        _write_json(folder / "package.json", {"name": name, "version": "1.0.0"})
        _write_json(
            folder / "package-lock.json",
            {"name": name, "version": "1.0.0", "lockfileVersion": 3, "requires": True, "packages": {"": {}}},
        )


def _escaped_npm_ci(args: list[str], real_npm: Path) -> list[str]:
    """The review's shell text with the real npm's directory: the shell turns `n\\pm c\\i` into `npm ci`."""
    return [arg.replace("/usr/bin/", f"{real_npm.parent}/") for arg in args]


@pytest.mark.skipif(_real_npm() is None, reason="needs a real npm")
@pytest.mark.parametrize("case", sorted(REVIEW_SHELL_CALLS))
@pytest.mark.parametrize("relative_cwd", [".", "site"])
def test_real_npm_escaped_shell_call_is_refused(layout, case, relative_cwd):
    """The review's eight reproductions: through the shim real npm never runs and the sentinel survives."""
    _lockable(layout)
    tool, args = REVIEW_SHELL_CALLS[case]
    args = _escaped_npm_ci(args, Path(_real_npm()))
    proc = _run_real(layout, args, layout["worktree"] / relative_cwd, tool)
    assert proc.returncode == 1, proc.stderr
    assert "is refused: as its own options" in proc.stderr
    assert _sentinels_intact(layout)


@pytest.mark.skipif(_real_npm() is None, reason="needs a real npm")
@pytest.mark.parametrize("case", ["npm-exec-c", "npx-call-eq"])
@pytest.mark.parametrize("relative_cwd", [".", "site"])
def test_real_npm_escaped_shell_call_unguarded_destroys_the_sentinel(layout, case, relative_cwd):
    """Control: without the shim the same escaped text reaches `npm ci`, which empties the shared folder."""
    _lockable(layout)
    tool, args = REVIEW_SHELL_CALLS[case]
    proc = _run_real(
        layout, _escaped_npm_ci(args, Path(_real_npm())), layout["worktree"] / relative_cwd, tool, shim=False
    )
    assert proc.returncode == 0, proc.stderr
    assert not _sentinels_intact(layout)


REAL_SHELL_REFUSALS = [
    ("npx", ["sh", "-c", "npm ci"]),
    ("npm", ["exec", "--", "bash", "-c", "n\\pm c\\i"]),
    ("npx", ["node", "-e", "require('child_process').execSync('npm ci')"]),
    ("npx", ["env", "npm", "ci"]),
    ("npx", ["-p", "npm", "npm", "ci"]),
    ("npx", ["--package=npm@10", "npm", "ci"]),
    ("npx", ["--yes", "npm", "ci"]),
    ("npx", ["-c", "$'\\x6epm' ci"]),
    ("npx", ["-c", "x=npm; ${x} ci"]),
]


@pytest.mark.skipif(_real_npm() is None, reason="needs a real npm")
@pytest.mark.parametrize("tool,args", REAL_SHELL_REFUSALS, ids=_launch_id)
def test_real_npm_shell_and_interpreter_launches_are_refused(layout, tool, args):
    _lockable(layout)
    proc = _run_real(layout, args, layout["worktree"] / "site", tool)
    assert proc.returncode == 1, proc.stderr
    assert "refused" in proc.stderr and "#9460" in proc.stderr
    assert _sentinels_intact(layout)


@pytest.mark.skipif(_real_npm() is None, reason="needs a real npm")
@pytest.mark.parametrize(
    "tool,args,relative_cwd",
    [("npm", ["--prefix", "site", "exec", "--", "vitest", "run"], "."), ("npx", ["vitest", "run"], "site")],
    ids=["npm-prefix-exec", "npx-in-site"],
)
def test_real_npm_allowlisted_program_runs_with_the_sentinel_intact(layout, tool, args, relative_cwd):
    """A local vitest bin behind the link runs through real npm; its output and exit code come back unchanged."""
    bin_dir = layout["primary"] / "site" / "node_modules" / ".bin"
    bin_dir.mkdir()
    (bin_dir / "vitest").write_text('#!/bin/sh\necho "vitest ran: $*"\necho vitest-err >&2\nexit 3\n', encoding="utf-8")
    (bin_dir / "vitest").chmod(0o755)
    proc = _run_real(layout, args, layout["worktree"] / relative_cwd, tool)
    assert proc.returncode == 3, proc.stderr
    assert proc.stdout == "vitest ran: run\n"
    assert "vitest-err" in proc.stderr and "refused" not in proc.stderr
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
        # Adapted for the closed exec rule (each was allowed by the text-classifying rule):
        # no program, a --package or -c option, or a program off the allowlist now refuses.
        ("npx", ["-y", "--version"], False),
        ("npx", [], False),
        ("npx", ["--package=@scope/tool@1.2.3", "tool"], False),
        ("npx", ["npm-check-updates"], False),
        ("npx", ["-c", "tool run build"], False),
        ("npm", ["exec"], False),
        ("npm", ["--json", "exec", "ls"], False),
        ("npx", ["vitest", "--reporter=verbose"], True),
        ("npx", ["--package=npm@10", "tool"], False),
        ("npx", ["-c=npm ci"], False),
        ("npx", ["NPM"], False),
        ("npx", ["Vitest"], False),
        ("npx", ["vitest.cmd"], False),
        ("npx", ["pnpm.exe"], False),
        ("npx", ["npm:pnpm@9"], False),
        ("npx", ["vitest", "--save=install"], False),
        ("npx", ["---", "vitest", "-c", "x"], True),
        ("npx", ["--prefix", "site", "vitest"], True),
        ("npx", ["-C=site", "vitest"], True),
        ("npx", ["--prefix"], False),
        ("npx", ["--no-install", "vitest"], True),
        ("npx", ["--no-fund", "vitest"], False),
        ("npx", ["--no-fund", "--yes", "vitest"], True),
        ("npx", ["@anthropic-ai/claude-code@latest"], True),
        ("npx", ["@anthropic-ai/claude-code/../npm"], False),
        ("npx", ["@anthropic-ai/claude-code@npm:npm"], False),
        ("npx", ["vitest@"], False),
        ("npm", ["--no-fund", "exec", "--", "vitest"], True),
        ("npm", ["--no", "exec", "--", "vitest"], False),
        ("npm", ["exec", "--", "vitest", "-c", "npm ci"], True),
        ("npm", ["exec", "vitest", "--", "-c", "npm ci"], True),
        ("npm", ["exec", "--", "tool", "audit", "fix"], False),
        ("npm", ["run", "x", "ci"], False),
        ("npm", ["run", "x"], True),
        ("npm", ["--json", "true", "exec", "vitest"], False),
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


def test_walk_ignores_git_environment(layout, monkeypatch):
    """Adapted from the git-root test: the walk reads only the filesystem, so GIT_* cannot steer it."""
    worktree, primary = layout["worktree"], layout["primary"]
    monkeypatch.setenv("GIT_DIR", str(primary / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(layout["tmp"]))
    assert [link for _, link, _ in npm_guard.protected_links([worktree / "site" / "src"])] == [
        worktree / "node_modules",
        worktree / "site" / "node_modules",
    ]
    assert npm_guard.protected_links([layout["tmp"]]) == []
    assert npm_guard.protected_links([primary / "site"]) == []


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


# --- the protected worktree is found by walking the filesystem ----------------
# Each shape below made the a36195414c guard (git's reported root) let `npm ci`
# through to the fake, which then emptied the shared folder.


def test_nested_repository_does_not_hide_the_worktree_link(layout):
    """A repository at site/src made git report it as the root, hiding site/node_modules."""
    nested = layout["worktree"] / "site" / "src"
    _git(nested, "init", "-q", "-b", "main")
    proc = _run(layout, "npm", ["ci", "--ignore-scripts", "--no-audit", "--no-fund"], nested)
    _assert_refused(layout, proc)
    assert f"unlink {layout['worktree'] / 'site' / 'node_modules'}" in proc.stderr


def test_core_worktree_redirect_does_not_hide_the_worktree_link(layout):
    worktree = layout["worktree"]
    elsewhere = layout["tmp"] / "elsewhere"
    elsewhere.mkdir()
    _git(worktree, "config", "extensions.worktreeConfig", "true")
    _git(worktree, "config", "--worktree", "core.worktree", str(elsewhere))
    _assert_refused(layout, _run(layout, "npm", ["ci"], worktree / "site"))


@pytest.mark.parametrize("relative_cwd", [".", "site"])
def test_worktree_root_ending_in_a_space_is_protected(tmp_path, relative_cwd):
    space_layout = _build_layout(tmp_path, "task ")
    worktree = space_layout["worktree"]
    assert str(worktree).endswith(" ")
    proc = _run(space_layout, "npm", ["ci"], worktree / relative_cwd)
    _assert_refused(space_layout, proc)
    assert f"outside {worktree}." in proc.stderr
    assert npm_guard.main(["npm", "ci"], cwd=worktree / relative_cwd) == 1


def test_logical_working_directory_through_the_link_is_protected(layout):
    """Physically inside the primary's node_modules, logically inside the worktree: $PWD reveals the link."""
    logical = layout["worktree"] / "node_modules" / "dep"
    _assert_refused(layout, _run(layout, "npm", ["ci"], logical, {"PWD": str(logical)}))


@pytest.mark.parametrize("spelling", ["{}/", "{}/.", "{}//"])
def test_working_directory_spellings_are_protected(layout, spelling):
    site = layout["worktree"] / "site"
    _assert_refused(layout, _run(layout, "npm", ["ci"], site, {"PWD": spelling.format(site)}))
    assert npm_guard.main(["npm", "ci"], cwd=Path(spelling.format(site))) == 1


def test_symlinked_working_directory_is_protected(layout):
    alias = layout["tmp"] / "alias"
    alias.symlink_to(layout["worktree"])
    _assert_refused(layout, _run(layout, "npm", ["ci"], alias / "site", {"PWD": str(alias / "site")}))


def test_unreadable_working_directory_allows_only_read_only_calls(layout):
    """A deleted cwd might lie in a protected worktree; npm cannot run there either, so refuse writes."""
    gone = layout["worktree"] / "site" / "gone"
    script = 'cd "$1" && rmdir "$1" && "$2" "${@:3}"'
    base = [str(layout["shim_dir"] / "npm")]
    env = {
        "PATH": f"{layout['shim_dir']}:{layout['fake_bin']}:/usr/bin:/bin",
        "HOME": str(layout["tmp"]),
        "FAKE_NPM_LOG": str(layout["log"]),
    }
    for args, refused in ((["ci"], True), (["--version"], False)):
        gone.mkdir()
        proc = subprocess.run(
            ["bash", "-c", script, "bash", str(gone), *base, *args],
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if refused:
            assert proc.returncode == 1, proc.stderr
            assert "working directory cannot be read" in proc.stderr
            assert _fake_calls(layout) == []
        else:
            assert (proc.returncode, proc.stdout) == (0, "fake-npm-stdout --version\n"), proc.stderr
    assert _sentinels_intact(layout)


def test_main_treats_an_unreadable_working_directory_as_protected(monkeypatch, capsys):
    def deleted() -> str:
        raise FileNotFoundError("cwd deleted")

    monkeypatch.setattr(npm_guard.os, "getcwd", deleted)
    assert npm_guard.main(["npm", "ci"]) == 1
    assert "working directory cannot be read" in capsys.readouterr().err
    assert npm_guard.main(["npm", "--version"]) == 0


def test_outward_symlink_loop_is_refused(layout):
    worktree, tmp = layout["worktree"], layout["tmp"]
    (tmp / "loop-a").symlink_to(tmp / "loop-b")
    (tmp / "loop-b").symlink_to(tmp / "loop-a")
    (worktree / "node_modules").unlink()
    (worktree / "node_modules").symlink_to(tmp / "loop-a")
    (worktree / "site" / "node_modules").unlink()
    (worktree / "site" / "node_modules").symlink_to(worktree / "site" / "node_modules")
    proc = _run(layout, "npm", ["ci"], worktree / "site")
    _assert_refused(layout, proc)
    assert f"unlink {worktree / 'node_modules'}`" in proc.stderr


def test_walk_survives_deep_paths_and_unreadable_ancestors(layout):
    worktree = layout["worktree"]
    expected = [worktree / "node_modules", worktree / "site" / "node_modules"]
    deep = worktree / "site" / Path(*["d"] * 3000)
    assert len(str(deep)) > 4096
    assert [link for _, link, _ in npm_guard.protected_links([deep])] == expected
    if os.geteuid() == 0:
        pytest.skip("root ignores directory permissions")
    locked = worktree / "site" / "locked"
    locked.mkdir()
    locked.chmod(0)
    try:
        assert npm_guard.outward_links(locked / "inner") == []
        assert [link for _, link, _ in npm_guard.protected_links([locked / "inner"])] == expected
    finally:
        locked.chmod(0o755)


# --- the shim's interpreter and real-tool lookup --------------------------------


def _linked_shim_checkout(tmp_path: Path) -> tuple[Path, Path]:
    """A primary checkout holding the shim and a .venv, plus a linked worktree without a .venv."""
    main_root = tmp_path / "shim-primary"
    shim_dir = main_root / "scripts" / "agent_runtime" / "shims"
    shim_dir.mkdir(parents=True)
    shutil.copy2(SHIM_SOURCE, shim_dir / "npm")
    shutil.copy2(NPX_SOURCE, shim_dir / "npx")
    shutil.copy2(GUARD_SOURCE, main_root / "scripts" / "agent_runtime" / "npm_guard.py")
    (main_root / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    _git(main_root, "init", "-q", "-b", "main")
    _git(main_root, "add", ".")
    _git(main_root, "commit", "-q", "-m", "shim")
    (main_root / ".venv" / "bin").mkdir(parents=True)
    (main_root / ".venv" / "bin" / "python").symlink_to(sys.executable)
    linked = main_root / ".worktrees" / "dispatch" / "agent" / "task"
    _git(main_root, "worktree", "add", "-q", "--detach", str(linked))
    assert not (linked / ".venv").exists()
    return main_root, linked / "scripts" / "agent_runtime" / "shims"


@pytest.mark.parametrize("git_env", [{}, {"GIT_DIR": "/nonexistent", "GIT_WORK_TREE": "/nonexistent"}], ids=str)
def test_linked_worktree_shim_uses_the_main_checkout_interpreter(layout, git_env):
    _, linked_shims = _linked_shim_checkout(layout["tmp"])
    env = {
        "PATH": f"{linked_shims}:{layout['fake_bin']}:/usr/bin:/bin",
        "HOME": str(layout["tmp"]),
        "FAKE_NPM_LOG": str(layout["log"]),
        **git_env,
    }
    proc = subprocess.run(
        [str(linked_shims / "npm"), "--version"],
        cwd=layout["tmp"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert (proc.returncode, proc.stdout) == (0, "fake-npm-stdout --version\n"), proc.stderr


@pytest.mark.parametrize("stamped", [True, False], ids=["stamped-interpreter", "common-dir-lookup"])
def test_runner_merge_guard_npm_version_runs_from_a_linked_worktree(layout, stamped):
    from scripts.agent_runtime import runner

    _, linked_shims = _linked_shim_checkout(layout["tmp"])
    env = runner._apply_merge_guard(
        mode="danger",
        env={
            "PATH": f"{layout['fake_bin']}:/usr/bin:/bin",
            "HOME": str(layout["tmp"]),
            "FAKE_NPM_LOG": str(layout["log"]),
        },
    )
    assert env["AGENT_GIT_SHIM_PYTHON"] == sys.executable
    if not stamped:
        env.pop("AGENT_GIT_SHIM_PYTHON")
    env["PATH"] = env["PATH"].replace(str(runner._SHIMS_DIR), str(linked_shims), 1)
    npm = shutil.which("npm", path=env["PATH"])
    assert npm == str(linked_shims / "npm")
    proc = subprocess.run(
        [npm, "--version"], cwd=layout["tmp"], env=env, capture_output=True, text=True, check=False, timeout=60
    )
    assert (proc.returncode, proc.stdout) == (0, "fake-npm-stdout --version\n"), proc.stderr


def test_runner_merge_guard_npm_version_runs_through_this_checkout(layout):
    """The review's probe as written: the runner's own shim directory, whatever checkout this is."""
    from scripts.agent_runtime import runner

    env = runner._apply_merge_guard(
        mode="danger",
        env={
            "PATH": f"{layout['fake_bin']}:/usr/bin:/bin",
            "HOME": str(layout["tmp"]),
            "FAKE_NPM_LOG": str(layout["log"]),
        },
    )
    npm = shutil.which("npm", path=env["PATH"])
    assert npm == str(runner._SHIMS_DIR / "npm")
    proc = subprocess.run(
        [npm, "--version"], cwd=layout["tmp"], env=env, capture_output=True, text=True, check=False, timeout=60
    )
    assert (proc.returncode, proc.stdout) == (0, "fake-npm-stdout --version\n"), proc.stderr


def _shim_spellings(layout: dict[str, Path]) -> dict[str, str]:
    alias = layout["tmp"] / "shim-alias"
    alias.symlink_to(layout["shim_dir"])
    return {"dot": f"{layout['shim_dir']}/.", "slash": f"{layout['shim_dir']}//", "symlink": str(alias)}


@pytest.mark.parametrize("spelling", ["dot", "slash", "symlink"])
def test_shim_directory_spelled_differently_on_path_does_not_recurse(layout, spelling):
    entry = _shim_spellings(layout)[spelling]
    env = {
        "PATH": f"{entry}:{layout['fake_bin']}:/usr/bin:/bin",
        "AGENT_ORIGINAL_PATH": f"{entry}:{layout['fake_bin']}",
    }
    proc = _run(layout, "npm", ["--version"], layout["tmp"], env)
    assert (proc.returncode, proc.stdout) == (0, "fake-npm-stdout --version\n"), proc.stderr
    assert len(_fake_calls(layout)) == 1


@pytest.mark.parametrize("spelling", ["dot", "slash", "symlink"])
def test_pinned_shim_spelled_differently_is_not_used(layout, spelling):
    pinned = _shim_spellings(layout)[spelling] + ("npm" if spelling == "slash" else "/npm")
    proc = _run(layout, "npm", ["--version"], layout["tmp"], {"AGENT_REAL_NPM": pinned})
    assert (proc.returncode, proc.stdout) == (0, "fake-npm-stdout --version\n"), proc.stderr
    assert len(_fake_calls(layout)) == 1


def test_pinned_real_tool_does_not_bypass_the_guard(layout):
    proc = _run(layout, "npm", ["ci"], layout["worktree"], {"AGENT_REAL_NPM": str(layout["fake_bin"] / "npm")})
    _assert_refused(layout, proc)


# --- the npx wrapper and AGENT_SHIM_TOOL ----------------------------------------


def _argv0_npx(layout: dict[str, Path]) -> Path:
    """The former mechanism: a shim checkout whose `npx` is a symlink to the npm shim."""
    tooling = layout["tmp"] / "argv0-tooling"
    shim_dir = tooling / "scripts" / "agent_runtime" / "shims"
    shim_dir.mkdir(parents=True)
    shutil.copy2(SHIM_SOURCE, shim_dir / "npm")
    (shim_dir / "npx").symlink_to("npm")
    shutil.copy2(GUARD_SOURCE, tooling / "scripts" / "agent_runtime" / "npm_guard.py")
    (tooling / ".venv" / "bin").mkdir(parents=True)
    (tooling / ".venv" / "bin" / "python").symlink_to(sys.executable)
    return shim_dir / "npx"


def _run_path(layout: dict[str, Path], tool_path: Path, args: list[str], cwd: Path, extra_env=None):
    env = {
        "PATH": f"{layout['shim_dir']}:{layout['fake_bin']}:/usr/bin:/bin",
        "HOME": str(layout["tmp"]),
        "FAKE_NPM_LOG": str(layout["log"]),
        **(extra_env or {}),
    }
    return subprocess.run(
        [str(tool_path), *args], cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=60
    )


NPX_CASES = [
    ["--version"],
    ["--help"],
    *(args for tool, args, _ in [*LAUNCH_REFUSALS.values(), *EXEC_FALSE_REFUSALS.values()] if tool == "npx"),
    *(args for tool, args in [*REVIEW_SHELL_CALLS.values(), *LAUNCHES] if tool == "npx"),
]
NPX_REFUSALS = {case: value[1:] for case, value in LAUNCH_REFUSALS.items() if value[0] == "npx"}


@pytest.mark.parametrize("args", NPX_CASES, ids=_launch_id)
def test_npx_wrapper_behaves_exactly_like_the_former_argv0_npx(layout, args):
    """Same exit code, output, refusal and real-tool call as the npm shim reached as `npx` by argv0."""
    cwd = layout["worktree"]
    legacy = _argv0_npx(layout)
    outcomes = []
    for tool_path in (layout["shim_dir"] / "npx", legacy):
        layout["log"].unlink(missing_ok=True)
        proc = _run_path(layout, tool_path, args, cwd)
        outcomes.append((proc.returncode, proc.stdout, proc.stderr, _fake_calls(layout)))
        assert _sentinels_intact(layout)
    assert outcomes[0] == outcomes[1]


def test_npx_wrapper_runs_its_sibling_shim_whatever_path_says(layout):
    """The sibling npm shim is found by physical path, so a real npm first on PATH is never reached unguarded."""
    proc = _run_path(
        layout,
        layout["shim_dir"] / "npx",
        ["sh", "-c", "npm ci"],
        layout["worktree"],
        {"PATH": f"{layout['fake_bin']}:{layout['shim_dir']}:/usr/bin:/bin"},
    )
    _assert_refused(layout, proc)
    assert "agent npx shim refused" in proc.stderr


def _copied_npx(layout: dict[str, Path], sibling: str, *, guard: bool = True) -> Path:
    """The npx wrapper copied into another shim directory whose sibling `npm` is ``sibling``."""
    tooling = layout["tmp"] / "copied-tooling"
    shim_dir = tooling / "scripts" / "agent_runtime" / "shims"
    shim_dir.mkdir(parents=True)
    shutil.copy2(NPX_SOURCE, shim_dir / "npx")
    if guard:
        shutil.copy2(GUARD_SOURCE, tooling / "scripts" / "agent_runtime" / "npm_guard.py")
    (tooling / ".venv" / "bin").mkdir(parents=True)
    (tooling / ".venv" / "bin" / "python").symlink_to(sys.executable)
    npm = shim_dir / "npm"
    if sibling == "symlink-to-real-npm":
        npm.symlink_to(layout["fake_bin"] / "npm")
    elif sibling == "regular-file-without-marker":
        shutil.copy2(layout["fake_bin"] / "npm", npm)
    elif sibling == "symlink-to-the-shim":
        npm.symlink_to(SHIM_SOURCE)
    else:
        assert sibling == "shim"
        shutil.copy2(SHIM_SOURCE, npm)
    return shim_dir / "npx"


def _assert_npx_unguarded_refused(layout: dict[str, Path], proc: subprocess.CompletedProcess[str]) -> None:
    assert proc.returncode == 127, proc.stderr
    assert "is not the guarded npm shim" in proc.stderr and "refusing to run npx unguarded" in proc.stderr
    assert proc.stdout == ""
    assert _fake_calls(layout) == []
    assert _sentinels_intact(layout)


NPX_DESTROYER = ["ci", "--ignore-scripts", "--no-audit", "--no-fund", "--offline"]


@pytest.mark.parametrize(
    "sibling,guard",
    [
        ("symlink-to-real-npm", True),
        ("symlink-to-real-npm", False),
        ("regular-file-without-marker", True),
        ("symlink-to-the-shim", True),
        ("shim", False),
    ],
    ids=str,
)
@pytest.mark.parametrize("args", [NPX_DESTROYER, ["--version"]], ids=" ".join)
def test_copied_npx_beside_anything_but_the_guarded_shim_fails_closed(layout, sibling, guard, args):
    """Review reproduction: a copied wrapper must never run a sibling that is not the guarded npm shim."""
    proc = _run_path(layout, _copied_npx(layout, sibling, guard=guard), args, layout["worktree"])
    _assert_npx_unguarded_refused(layout, proc)


def test_copied_npx_beside_the_guarded_shim_works_as_before(layout):
    npx = _copied_npx(layout, "shim")
    proc = _run_path(layout, npx, NPX_DESTROYER, layout["worktree"])
    _assert_refused(layout, proc)
    assert "agent npx shim refused" in proc.stderr
    proc = _run_path(layout, npx, ["--version"], layout["worktree"])
    _assert_passed_through(layout, proc, "npx", ["--version"], layout["worktree"], 0)


def test_npm_shim_carries_the_marker_the_npx_wrapper_requires():
    marker_lines = [line for line in NPX_SOURCE.read_text(encoding="utf-8").splitlines() if line.startswith("marker=")]
    assert len(marker_lines) == 1
    marker = marker_lines[0].removeprefix("marker=").strip('"')
    assert SHIM_SOURCE.read_text(encoding="utf-8").splitlines().count(marker) == 1


HOSTILE_TOOL_VALUES = ["", "rm", "../npm", "npx; true", "NPX", "npx\n", "/usr/bin/npx"]


@pytest.mark.parametrize("value", HOSTILE_TOOL_VALUES, ids=repr)
def test_hostile_shim_tool_value_leaves_the_npm_shim_as_npm(layout, value):
    env = {"AGENT_SHIM_TOOL": value}
    proc = _run(layout, "npm", ["--version"], layout["worktree"], env)
    _assert_passed_through(layout, proc, "npm", ["--version"], layout["worktree"], 0)
    layout["log"].unlink()
    proc = _run(layout, "npm", ["ci"], layout["worktree"], env)
    _assert_refused(layout, proc)
    assert "agent npm shim refused `npm ci`" in proc.stderr


@pytest.mark.parametrize("value", [*HOSTILE_TOOL_VALUES, "npm"], ids=repr)
def test_caller_shim_tool_value_cannot_change_the_npx_wrapper(layout, value):
    env = {"AGENT_SHIM_TOOL": value}
    proc = _run(layout, "npx", ["--version"], layout["worktree"], env)
    _assert_passed_through(layout, proc, "npx", ["--version"], layout["worktree"], 0)
    layout["log"].unlink()
    proc = _run(layout, "npx", ["sh", "-c", "npm ci"], layout["worktree"], env)
    _assert_refused(layout, proc)
    assert "agent npx shim refused" in proc.stderr


@pytest.mark.parametrize("case", sorted(NPX_REFUSALS))
def test_shim_tool_npx_on_the_npm_shim_is_still_guarded_as_npx(layout, case):
    """Choosing npx through the variable only selects npx, which the guard checks as npx."""
    args, reason = NPX_REFUSALS[case]
    proc = _run(layout, "npm", args, layout["worktree"], {"AGENT_SHIM_TOOL": "npx"})
    _assert_refused(layout, proc)
    assert reason in proc.stderr and "agent npx shim refused" in proc.stderr


@pytest.mark.parametrize("tool,extra_env", [("npx", {}), ("npm", {"AGENT_SHIM_TOOL": "npx"})], ids=str)
def test_real_tool_never_inherits_the_shim_tool_variable(layout, tool, extra_env):
    """An inner `npm` run by the real npx must see itself as npm, so the variable is dropped."""
    (layout["fake_bin"] / "npx").write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "${AGENT_SHIM_TOOL-unset}"\n', encoding="utf-8"
    )
    proc = _run(layout, tool, ["vitest"], layout["worktree"], extra_env)
    assert (proc.returncode, proc.stdout) == (0, "unset\n"), proc.stderr


# --- wiring: dispatched shells resolve npm/npx to the shim ---------------------


def test_shim_files_are_regular_executables():
    """Both shims are regular files (the docs catalogue refuses tracked symlinks)."""
    for shim in (SHIM_SOURCE, NPX_SOURCE):
        assert shim.is_file() and not shim.is_symlink() and os.access(shim, os.X_OK)
    listed = subprocess.run(
        ["git", "ls-files", "-s", "--", "scripts/agent_runtime/shims"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout
    modes = {line.split("\t")[1].rsplit("/", 1)[1]: line.split()[0] for line in listed.splitlines()}
    assert modes["npm"] == modes["npx"] == "100755"


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
