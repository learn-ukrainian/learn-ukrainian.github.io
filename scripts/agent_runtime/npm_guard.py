"""Refuse npm/npx calls that could rewrite a node_modules shared through a symlink (#9460).

Dispatch worktrees receive the primary checkout's ``node_modules`` and
``site/node_modules`` as symlinks (``delegate._provision_data_symlinks``).
``npm ci`` deletes its target folder first, so running it in a worktree empties
the primary's real folder through the link. The ``npm`` shim (``npx`` links to
it) runs this module before handing over to the real binary:

    python -I -S npm_guard.py {npm|npx} ARGS...

Exit 0 lets the shim ``exec`` the real tool unchanged; exit 1 (message on
stderr) refuses.

The decision is a fact about the worktree, not a prediction of where npm will
write. npm's options, config files, environment, prefix and workspace
resolution are deliberately not modelled, so none of them can steer the guard:

* No protected path of the current git worktree resolves outside it: every call
  passes through untouched, without looking at the arguments.
* At least one does: only clearly read-only calls pass, namely a version/help
  early exit, an allowlisted read-only subcommand with no destructive command
  word anywhere in the arguments, or ``npx``/``npm exec`` whose arguments name
  no package manager and no install word. Everything else is refused, including
  global installs.

``npx`` and ``npm exec`` run an existing binary or fetch a package into npm's
own cache; they do not rewrite the project's node_modules. The hazard is the
tool they launch: a package manager (or an install through some other tool)
writes through the link, and pnpm, yarn or an npm reached by path bypass this
shim. So any argument naming a package manager, as a name, spec, scope or path,
in a ``--key=value`` or in the shell command of ``-c``/``--call``, refuses the
call, and so does any argument that is an install word.

Standard library only: the shim runs it with ``-I -S``.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

# The node_modules entries ``scripts/delegate.py::_provision_data_symlinks``
# links into every dispatch worktree. Duplicated because the guard cannot import
# delegate; test_npm_shim fails when the two lists diverge.
PROTECTED_PATHS = ("node_modules", "site/node_modules")

# npm prints its version or the command usage and exits before running anything.
EARLY_EXIT_FLAGS = frozenset({"--version", "-v", "--help", "-h"})

# The only options the guard knows for certain to consume the next argument
# (npm's ``prefix`` and ``workspace``, long and short). Any other bare option
# might take a value, so the word after it is treated as ambiguous.
VALUE_OPTIONS = frozenset({"--prefix", "-C", "--workspace", "-w"})

# npm commands and aliases (including npm's own typo aliases) that rewrite
# node_modules. Present anywhere in the arguments, they refuse the call.
DESTRUCTIVE_WORDS = frozenset(
    {
        "ci", "clean-install", "ic", "install-clean", "isntall-clean",
        "install", "i", "in", "ins", "inst", "insta", "instal", "add",
        "isnt", "isnta", "isntal", "isntall",
        "update", "up", "upgrade", "udpate",
        "prune", "dedupe", "ddp",
        "uninstall", "un", "unlink", "remove", "rm", "r",
        "rebuild", "rb", "link", "ln", "edit",
        "install-test", "it", "install-ci-test", "cit", "clean-install-test", "sit",
    }
)  # fmt: skip

# Subcommands that do not write node_modules, mapped to the words allowed as
# their next positional (None: any; an empty set: none). Scripts started by the
# run-script family call npm through PATH and so re-enter this guard.
READ_ONLY_COMMANDS: dict[str, frozenset[str] | None] = {
    "run": None, "run-script": None, "test": None, "t": None, "tst": None,
    "start": None, "stop": None, "restart": None,
    "ls": None, "list": None, "ll": None, "la": None,
    "view": None, "v": None, "info": None, "show": None,
    "search": None, "s": None, "find": None,
    "outdated": None, "explain": None, "why": None, "fund": None, "query": None,
    "audit": None,  # ``audit fix`` is refused separately
    "doctor": None, "help": None, "help-search": None,
    "root": None, "prefix": None, "whoami": None, "ping": None,
    "config": frozenset({"get", "list", "ls"}),
    "cache": frozenset({"ls", "verify"}),
    "version": frozenset(),  # bare ``npm version`` only prints versions
}  # fmt: skip

EXEC_COMMANDS = frozenset({"exec", "x"})

# Package managers and their entry scripts (compared without a script extension).
PACKAGE_MANAGERS = frozenset(
    {"npm", "npx", "npm-cli", "npx-cli", "pnpm", "pnpx", "yarn", "yarnpkg", "corepack", "bun", "bunx"}
)
SCRIPT_EXTENSIONS = frozenset({"js", "cjs", "mjs", "cmd", "exe", "ps1"})

# npx/npm exec options whose value is a shell command line.
SHELL_OPTIONS = frozenset({"-c", "--call"})


def worktree_root(cwd: Path) -> Path | None:
    """The git worktree containing ``cwd``, or None outside any (or without git)."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    top = proc.stdout.strip()
    return Path(top) if proc.returncode == 0 and top else None


def outward_links(root: Path) -> list[tuple[Path, Path]]:
    """``(link, target)`` for each protected path resolving outside ``root``."""
    real_root = Path(os.path.realpath(root))
    found = []
    for relative in PROTECTED_PATHS:
        path = root / relative
        if not os.path.lexists(path):
            continue
        resolved = Path(os.path.realpath(path))
        if resolved != real_root and real_root not in resolved.parents:
            found.append((_first_symlink(root, path), resolved))
    return found


def _first_symlink(root: Path, path: Path) -> Path:
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            return current
    return path


def _kinds(args: Sequence[str]) -> list[str]:
    """Classify each argument without knowing npm's option table.

    ``flag``: a version/help flag that cannot be another option's value;
    ``option``/``value-option``/``bare-option``: an option token (a bare one may
    take the next word as its value, unless it may itself be a value);
    ``value``: certainly a value; ``maybe-value``: follows a bare option;
    ``positional``: certainly not a value; ``end``: npm's ``--`` terminator.
    """
    kinds: list[str] = []
    previous = ""
    ended = False
    for token in args:
        if ended:
            kind = "positional"
        elif len(token) >= 2 and set(token) == {"-"}:
            kind, ended = "end", True
        elif previous == "value-option":
            kind = "value"
        elif token.startswith("-") and token != "-":
            certain = previous not in ("bare-option", "value-option")
            if "=" in token:
                kind = "option"
            elif certain and token in VALUE_OPTIONS:
                kind = "value-option"
            elif certain and token in EARLY_EXIT_FLAGS:
                kind = "flag"
            else:
                kind = "bare-option"
        elif previous == "bare-option":
            kind = "maybe-value"
        else:
            kind = "positional"
        kinds.append(kind)
        previous = kind
    return kinds


def _early_exit(tool: str, args: Sequence[str], kinds: Sequence[str]) -> bool:
    """True when npm/npx certainly prints its version or usage and stops."""
    if tool == "npx":
        return len(args) == 1 and kinds[0] == "flag"
    head = [(token, kind) for token, kind in zip(args, kinds, strict=True)]
    if "end" in kinds:
        head = head[: kinds.index("end")]
    if not any(kind == "flag" for _, kind in head):
        return False
    # ``--version false``, ``--no-usage`` or ``-v=false`` can switch the flag back off.
    return not any(
        token in ("true", "false") or token.startswith("--no-") or (token.startswith("-") and "=" in token)
        for token, _ in head
    )


def _names_package_manager(word: str) -> bool:
    """True for a package-manager name, spec, scope or path (``npm@10``, ``@pnpm/exe``, ``/usr/bin/npm``).

    Text with whitespace (a prompt passed to the launched tool) names nothing.
    """
    if not word or any(char.isspace() for char in word):
        return False
    for part in re.split(r"[/\\:]", word.lower()):
        name = part.lstrip("@").split("@", 1)[0]
        stem, dot, extension = name.rpartition(".")
        if (stem if dot and extension in SCRIPT_EXTENSIONS else name) in PACKAGE_MANAGERS:
            return True
    return False


def _launch_words(args: Sequence[str]) -> list[str]:
    """The arguments, ``--key=value`` values and the words of ``-c``/``--call`` shell commands."""
    words: list[str] = []
    shell_next = False
    for token in args:
        key, equals, value = token.partition("=")
        if shell_next:
            words += re.split(r"[\s;&|()<>`'\"$]+", token)
        elif token.startswith("-") and equals:
            words += re.split(r"[\s;&|()<>`'\"$]+", value) if key in SHELL_OPTIONS else [value]
        else:
            words.append(token)
        shell_next = not shell_next and token in SHELL_OPTIONS
    return words


def _launch_refusal(launcher: str, args: Sequence[str]) -> str | None:
    """Why ``npx``/``npm exec`` with ``args`` could reach a package manager, or None."""
    for word in _launch_words(args):
        if _names_package_manager(word):
            return (
                f"`{word}` names a package manager; {launcher} may launch other tools here, but a "
                "package manager would write through the link."
            )
        if word in DESTRUCTIVE_WORDS:
            return (
                f"`{word}` is an install word; {launcher} is refused when any argument is one rather "
                "than guess whether the launched tool installs."
            )
    return None


def refusal_reason(tool: str, args: Sequence[str]) -> str | None:
    """Why ``tool ARGS`` is not clearly read-only, or None when it is."""
    kinds = _kinds(args)
    if _early_exit(tool, args, kinds):
        return None
    if tool == "npx":
        return _launch_refusal("npx", args)
    words = [index for index, kind in enumerate(kinds) if kind in ("positional", "maybe-value")]
    if any(args[index] in EXEC_COMMANDS for index in words):
        reason = _launch_refusal("npm exec", args)
        if reason:
            return reason
    destructive = [token for token in args if token in DESTRUCTIVE_WORDS]
    if destructive:
        return (
            f"`{destructive[0]}` is an npm command that rewrites node_modules; the guard refuses it "
            "wherever it appears in the arguments rather than guess which word is the subcommand."
        )
    if "audit" in args and "fix" in args:
        return "`audit fix` rewrites node_modules."
    for position, index in enumerate(words):
        word = args[index]
        if word in EXEC_COMMANDS and position == 0:
            # Its arguments passed the launch check; as a maybe-value the next word decides.
            if kinds[index] == "positional":
                return None
            continue
        if word not in READ_ONLY_COMMANDS:
            if kinds[index] == "maybe-value" or position > 0:
                return (
                    f"could not tell whether `{word}` is the subcommand or an option's value; put "
                    "options after the subcommand or write them as --key=value."
                )
            return f"`{word}` is not on the guard's read-only allowlist."
        allowed = READ_ONLY_COMMANDS[word]
        following = args[words[position + 1]] if position + 1 < len(words) else None
        if allowed is not None and following is not None and following not in allowed:
            return f"`{word} {following}` is not on the guard's read-only allowlist."
        if kinds[index] == "positional":
            return None
    return None


def refusal_message(tool: str, args: Sequence[str], root: Path, links: Sequence[tuple[Path, Path]], reason: str) -> str:
    shown = " ".join([tool, *args])
    lines = [f"error: agent {tool} shim refused `{shown}` (#9460).", f"       Reason: {reason}"]
    for link, target in links:
        lines.append(f"       {link} resolves to {target}, outside this worktree ({root}).")
    unlinks = " && ".join(f"unlink {link}" for link, _ in links)
    lines += [
        "       While such a link exists only clearly read-only npm commands run here; installs,",
        "       global installs (-g), and npx or npm exec naming a package manager or an install",
        "       word are refused because they could empty the shared folder through the link.",
        f"       Safe alternative: remove the link inside this worktree first (`{unlinks}`",
        "       deletes only the link, never its target), then install here so npm creates a",
        "       worktree-local node_modules; or run the command outside this worktree.",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None, *, cwd: Path | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("npm", "npx"):
        print("usage: npm_guard.py {npm|npx} ARGS...", file=sys.stderr)
        return 2
    tool, rest = args[0], args[1:]
    root = worktree_root(Path(os.getcwd()) if cwd is None else cwd)
    if root is None:
        return 0
    links = outward_links(root)
    if not links:
        return 0
    reason = refusal_reason(tool, rest)
    if reason is None:
        return 0
    print(refusal_message(tool, rest, root, links, reason), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
