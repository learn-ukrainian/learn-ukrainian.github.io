"""Decide whether an ``npm``/``npx`` call may run in an agent worktree (#9460).

Dispatch worktrees receive ``node_modules`` and ``site/node_modules`` as
symlinks into the primary checkout (``delegate._provision_data_symlinks``).
``npm ci`` deletes its target folder first, so running it in a worktree empties
the primary's real folder through the link. The ``npm`` shim next to the
``gh``/``git`` shims runs this module before handing over to the real binary:

    python -I -S npm_guard.py {npm|npx} ARGS...

Exit 0 lets the shim ``exec`` the real tool unchanged; exit 1 (with a message on
stderr) refuses. Only commands that rewrite the installed tree are examined —
``ci``, ``install``, ``update``, ``prune``, ``dedupe``, ``uninstall``,
``rebuild``, ``link``, ``edit``, ``install-test``, ``install-ci-test``,
``audit fix`` and package managers launched through ``npx``/``npm exec``. Such a
command is refused when a ``node_modules`` it would write resolves (realpath)
outside the worktree that contains its starting directory. Global installs
write to the global prefix, not a project folder, and pass through.

The argv handling is a port of npm 9/10's own resolution so the guard targets
exactly the folder npm would: nopt option parsing (value-taking keys, boolean
lookahead, shorthands, long-option abbreviations), command dereferencing
(aliases and unique abbreviations), ``npx`` argument splitting, and the local
prefix walk with workspace-root detection. Standard library only: the shim runs
it with ``-I -S`` before any project import is possible.
"""

from __future__ import annotations

import fnmatch
import json
import os
import shlex
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# --- npm command list (npm 9/10 ``lib/utils/cmd-list.js``) -------------------

COMMANDS = frozenset(
    {
        "access", "adduser", "audit", "bugs", "cache", "ci", "completion", "config", "dedupe",
        "deprecate", "diff", "dist-tag", "docs", "doctor", "edit", "exec", "explain", "explore",
        "find-dupes", "fund", "get", "help", "help-search", "hook", "init", "install",
        "install-ci-test", "install-test", "link", "ll", "login", "logout", "ls", "org",
        "outdated", "owner", "pack", "ping", "pkg", "prefix", "profile", "prune", "publish",
        "query", "rebuild", "repo", "restart", "root", "run-script", "sbom", "search", "set",
        "shrinkwrap", "star", "stars", "start", "stop", "team", "test", "token", "uninstall",
        "unpublish", "unstar", "update", "version", "view", "whoami",
    }
)  # fmt: skip

ALIASES = {
    "author": "owner", "home": "docs", "issues": "bugs", "info": "view", "show": "view",
    "find": "search", "add": "install", "unlink": "uninstall", "remove": "uninstall",
    "rm": "uninstall", "r": "uninstall", "un": "uninstall", "rb": "rebuild", "list": "ls",
    "ln": "link", "create": "init", "i": "install", "it": "install-test",
    "cit": "install-ci-test", "up": "update", "c": "config", "s": "search", "se": "search",
    "tst": "test", "t": "test", "ddp": "dedupe", "v": "view", "run": "run-script",
    "clean-install": "ci", "clean-install-test": "install-ci-test", "x": "exec",
    "why": "explain", "la": "ll", "verison": "version", "ic": "ci", "innit": "init",
    "in": "install", "ins": "install", "inst": "install", "insta": "install",
    "instal": "install", "isnt": "install", "isnta": "install", "isntal": "install",
    "isntall": "install", "install-clean": "ci", "isntall-clean": "ci", "hlep": "help",
    "dist-tags": "dist-tag", "upgrade": "update", "udpate": "update", "rum": "run-script",
    "sit": "install-ci-test", "urn": "run-script", "ogr": "org", "add-user": "adduser",
}  # fmt: skip

# Commands that reify or rewrite the installed tree. ``audit`` only with ``fix``.
TREE_WRITERS = frozenset(
    {
        "ci",
        "install",
        "install-test",
        "install-ci-test",
        "update",
        "prune",
        "dedupe",
        "uninstall",
        "rebuild",
        "link",
        "edit",
    }
)

# Package managers whose launch through ``npx``/``npm exec`` can rewrite node_modules.
PACKAGE_MANAGERS = frozenset({"npm", "npx", "pnpm", "yarn", "corepack"})

# --- npm config option types (npm 9/10 ``lib/utils/config/definitions.js``) --

# Keys whose type is not Boolean: nopt consumes the next argument as the value.
VALUE_KEYS = frozenset(
    {
        "_auth", "access", "also", "audit-level", "auth-type", "before", "ca", "cache",
        "cache-max", "cache-min", "cafile", "call", "cert", "ci-name", "cidr", "cpu", "depth",
        "diff", "diff-dst-prefix", "diff-src-prefix", "diff-unified", "editor",
        "expect-result-count", "fetch-retries", "fetch-retry-factor", "fetch-retry-maxtimeout",
        "fetch-retry-mintimeout", "fetch-timeout", "git", "globalconfig", "heading",
        "https-proxy", "include", "init-author-email", "init-author-name", "init-author-url",
        "init-license", "init-module", "init-version", "init.author.email", "init.author.name",
        "init.author.url", "init.license", "init.module", "init.version", "install-strategy",
        "key", "libc", "local-address", "location", "lockfile-version", "loglevel", "logs-dir",
        "logs-max", "maxsockets", "message", "node-options", "noproxy", "omit", "only", "os",
        "otp", "package", "pack-destination", "prefix", "preid", "provenance-file", "proxy",
        "registry", "replace-registry-host", "save-prefix", "sbom-format", "sbom-type", "scope",
        "script-shell", "searchexclude", "searchlimit", "searchopts", "searchstaleness", "shell",
        "tag", "tag-version-prefix", "tmp", "umask", "user-agent", "userconfig", "viewer",
        "which", "workspace",
    }
)  # fmt: skip

# Keys typed ``[null, Boolean, ...]``: boolean, but accept an explicit literal next.
MIXED_KEYS = {
    "browser": frozenset({"null", "true", "false"}),  # also a String: see _STRING_MIXED
    "color": frozenset({"always", "true", "false"}),
    "optional": frozenset({"null", "true", "false"}),
    "production": frozenset({"null", "true", "false"}),
    "workspaces": frozenset({"null", "true", "false"}),
    "yes": frozenset({"null", "true", "false"}),
}
_STRING_MIXED = frozenset({"browser"})

BOOLEAN_KEYS = frozenset(
    {
        "all", "allow-same-version", "audit", "bin-links", "commit-hooks", "description", "dev",
        "diff-ignore-all-space", "diff-name-only", "diff-no-prefix", "diff-text", "dry-run",
        "engine-strict", "expect-results", "force", "foreground-scripts", "format-package-lock",
        "fund", "git-tag-version", "global", "global-style", "if-present", "ignore-scripts",
        "include-attestations", "include-staged", "include-workspace-root", "install-links",
        "json", "legacy-bundling", "legacy-peer-deps", "link", "long", "offline",
        "omit-lockfile-registry-resolved", "package-lock", "package-lock-only", "parseable",
        "prefer-dedupe", "prefer-offline", "prefer-online", "progress", "provenance",
        "read-only", "rebuild-bundle", "save", "save-bundle", "save-dev", "save-exact",
        "save-optional", "save-peer", "save-prod", "shrinkwrap", "sign-git-commit",
        "sign-git-tag", "strict-peer-deps", "strict-ssl", "timing", "unicode", "update-notifier",
        "usage", "version", "versions", "workspaces-update",
    }
)  # fmt: skip

ALL_KEYS = VALUE_KEYS | BOOLEAN_KEYS | frozenset(MIXED_KEYS)
ARRAY_KEYS = frozenset({"workspace", "package", "include", "omit"})

SHORTHANDS = {
    "enjoy-by": ["--before"], "d": ["--loglevel", "info"], "dd": ["--loglevel", "verbose"],
    "ddd": ["--loglevel", "silly"], "quiet": ["--loglevel", "warn"], "q": ["--loglevel", "warn"],
    "s": ["--loglevel", "silent"], "silent": ["--loglevel", "silent"],
    "verbose": ["--loglevel", "verbose"], "desc": ["--description"], "help": ["--usage"],
    "local": ["--no-global"], "n": ["--no-yes"], "no": ["--no-yes"],
    "porcelain": ["--parseable"], "readonly": ["--read-only"], "reg": ["--registry"],
    "iwr": ["--include-workspace-root"], "a": ["--all"], "c": ["--call"], "f": ["--force"],
    "g": ["--global"], "L": ["--location"], "l": ["--long"], "m": ["--message"],
    "p": ["--parseable"], "C": ["--prefix"], "S": ["--save"], "B": ["--save-bundle"],
    "D": ["--save-dev"], "E": ["--save-exact"], "O": ["--save-optional"], "P": ["--save-prod"],
    "?": ["--usage"], "H": ["--usage"], "h": ["--usage"], "v": ["--version"],
    "w": ["--workspace"], "ws": ["--workspaces"], "y": ["--yes"],
}  # fmt: skip

# ``npx`` argument splitting (npm 9/10 ``bin/npx-cli.js``).
_NPX_REMOVED = frozenset({"always-spawn", "ignore-existing", "shell-auto-fallback", "npm", "node-arg", "n"})
_NPX_SWITCHES = (
    BOOLEAN_KEYS
    | frozenset(MIXED_KEYS)
    | {
        "always-spawn",
        "ignore-existing",
        "shell-auto-fallback",
        "no-install",
        "quiet",
        "q",
        "version",
        "v",
        "help",
        "h",
    }
)
_NPX_OPTS = frozenset({"npm", "node-arg", "n", "package", "p", "cache", "userconfig", "call", "c", "shell"})

_SHELL_SEPARATORS = frozenset({"&&", "||", ";", "|", "&"})


def _unique_prefix(token: str, words: Sequence[str] | frozenset[str]) -> str | None:
    """Resolve ``token`` the way the ``abbrev`` package does: exact word or unique prefix."""
    if token in words:
        return token
    matches = [word for word in words if word.startswith(token)]
    return matches[0] if len(matches) == 1 else None


_ABBREV_WORDS = COMMANDS | frozenset(ALIASES)


def deref_command(token: str) -> str | None:
    """Return the npm command ``token`` runs, or None when npm would not run one."""
    if not token:
        return None
    if any(ch.isupper() for ch in token):
        token = "".join(f"-{ch.lower()}" if ch.isupper() else ch for ch in token)
    if token == "help-search":
        return token
    resolved = _unique_prefix(token, _ABBREV_WORDS)
    while resolved in ALIASES:
        resolved = ALIASES[resolved]
    return resolved


def _resolve_short(arg: str) -> list[str] | None:
    """Port of nopt ``resolveShort``: expand a shorthand, or None for a real option."""
    key = arg.lstrip("-")
    if _unique_prefix(key, ALL_KEYS) == key:
        return None
    if key in SHORTHANDS:
        return list(SHORTHANDS[key])
    singles = {name for name in SHORTHANDS if len(name) == 1}
    if key and all(ch in singles for ch in key):
        return [part for ch in key for part in SHORTHANDS[ch]]
    if _unique_prefix(key, ALL_KEYS) is not None:
        return None
    short = _unique_prefix(key, frozenset(SHORTHANDS))
    return list(SHORTHANDS[short]) if short else None


@dataclass
class ParsedArgs:
    """The parts of an npm argv that decide what gets written where."""

    remain: list[str] = field(default_factory=list)
    options: dict[str, object] = field(default_factory=dict)

    def last(self, key: str) -> object:
        value = self.options.get(key)
        return value[-1] if isinstance(value, list) and value else value

    def values(self, key: str) -> list[object]:
        value = self.options.get(key)
        if value is None:
            return []
        return list(value) if isinstance(value, list) else [value]


def parse_npm_argv(argv: Sequence[str]) -> ParsedArgs:
    """Port of nopt ``parse`` with npm's types and shorthands."""
    args = list(argv)
    parsed = ParsedArgs()
    i = 0
    while i < len(args):
        arg = args[i]
        if len(arg) >= 2 and set(arg) == {"-"}:
            parsed.remain.extend(args[i + 1 :])
            break
        if not (arg.startswith("-") and len(arg) > 1):
            parsed.remain.append(arg)
            i += 1
            continue
        had_eq = "=" in arg
        if had_eq:
            arg, value = arg.split("=", 1)
            args[i : i + 1] = [arg, value]
        expansion = _resolve_short(arg)
        if expansion:
            args[i : i + 1] = expansion
            if arg != expansion[0]:
                continue
        key = arg.lstrip("-")
        negated: bool | None = None
        while key.lower().startswith("no-"):
            negated = not negated
            key = key[3:]
        key = _unique_prefix(key, ALL_KEYS) or key
        lookahead = args[i + 1] if i + 1 < len(args) else None

        known = key in ALL_KEYS
        is_bool = negated is not None or key in BOOLEAN_KEYS or key in MIXED_KEYS or (not known and not had_eq)
        if is_bool:
            value: object = not negated
            if lookahead in ("true", "false"):
                value = lookahead == "true"
                if negated:
                    value = not value
                lookahead = None
                i += 1
            if key in MIXED_KEYS and lookahead is not None:
                literal = lookahead in MIXED_KEYS[key]
                string = key in _STRING_MIXED and not (
                    lookahead.startswith("-") and len(lookahead) > 1 and lookahead[1] != "-"
                )
                if literal or string:
                    value = lookahead
                    i += 1
            _store(parsed, key, value)
            i += 1
            continue
        if lookahead is not None and len(lookahead) >= 2 and set(lookahead) == {"-"}:
            lookahead = None
            i -= 1
        _store(parsed, key, True if lookahead is None else lookahead)
        i += 2
    return parsed


def _store(parsed: ParsedArgs, key: str, value: object) -> None:
    if key in ARRAY_KEYS:
        parsed.options.setdefault(key, [])
        parsed.options[key].append(value)  # type: ignore[union-attr]
    else:
        parsed.options[key] = value


def split_npx_argv(argv: Sequence[str]) -> tuple[list[str], list[str]]:
    """Port of ``npx-cli.js``: npm options, then the command and its arguments."""
    args = list(argv)
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            return args[:i], args[i + 1 :]
        if not arg.startswith("-"):
            return args[:i], args[i:]
        key, _, value = arg.lstrip("-").partition("=")
        has_value = "=" in arg
        if key == "p":
            args[i] = "--package" + (f"={value}" if has_value else "")
        elif key == "shell":
            args[i] = "--script-shell" + (f"={value}" if has_value else "")
        elif key == "no-install":
            args[i] = "--yes=false"
        elif key in SHORTHANDS and key not in _NPX_REMOVED:
            expansion = list(SHORTHANDS[key])
            if has_value:
                expansion.append(value)
            args[i : i + 1] = expansion
            continue
        if key in _NPX_REMOVED:
            del args[i]
            if (
                not has_value
                and key not in _NPX_SWITCHES
                and i < len(args)
                and (key in _NPX_OPTS or not args[i].startswith("-"))
            ):
                del args[i]
            continue
        if (
            not has_value
            and key not in _NPX_SWITCHES
            and i + 1 < len(args)
            and (key in _NPX_OPTS or not args[i + 1].startswith("-"))
        ):
            i += 1
        i += 1
    return args, []


# --- project resolution -------------------------------------------------------


def _is_global(parsed: ParsedArgs, env: Mapping[str, str]) -> bool:
    location = parsed.last("location")
    if "global" in parsed.options:
        return parsed.last("global") is True
    if location is not None:
        return location == "global"
    lowered = {key.lower(): value for key, value in env.items()}
    if "npm_config_global" in lowered:
        return lowered["npm_config_global"].strip().lower() in ("true", "1")
    return lowered.get("npm_config_location", "").strip().lower() == "global"


def _read_package(directory: Path) -> dict | None:
    try:
        data = json.loads((directory / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _workspace_patterns(package: Mapping) -> list[str]:
    workspaces = package.get("workspaces")
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages")
    if not isinstance(workspaces, list):
        return []
    patterns = []
    for item in workspaces:
        if isinstance(item, str):
            negated = item.startswith("!")
            body = item[1:] if negated else item
            body = body.removeprefix("./").strip("/")
            patterns.extend(("!" if negated else "") + expanded for expanded in _expand_braces(body))
    return patterns


def _expand_braces(pattern: str) -> list[str]:
    start = pattern.find("{")
    end = pattern.find("}", start + 1)
    if start < 0 or end < 0:
        return [pattern]
    head, body, tail = pattern[:start], pattern[start + 1 : end], pattern[end + 1 :]
    return [expanded for option in body.split(",") for expanded in _expand_braces(head + option + tail)]


def _glob_match(parts: Sequence[str], patterns: Sequence[str]) -> bool:
    if not patterns:
        return not parts
    if patterns[0] == "**":
        return any(_glob_match(parts[index:], patterns[1:]) for index in range(len(parts) + 1))
    return bool(parts) and fnmatch.fnmatchcase(parts[0], patterns[0]) and _glob_match(parts[1:], patterns[1:])


def _matches_workspaces(root: Path, member: Path, patterns: Sequence[str]) -> bool:
    try:
        parts = member.relative_to(root).parts
    except ValueError:
        return False
    if not parts:
        return False
    matched = False
    for pattern in patterns:
        negated = pattern.startswith("!")
        if _glob_match(parts, Path(pattern.lstrip("!")).parts):
            matched = not negated
    return matched


def _workspace_members(root: Path, patterns: Sequence[str]) -> Iterator[Path]:
    split = [Path(pattern.lstrip("!")).parts for pattern in patterns]
    depth = None if any("**" in parts for parts in split) else max((len(parts) for parts in split), default=0)
    for current, dirnames, filenames in os.walk(root):
        directory = Path(current)
        level = len(directory.relative_to(root).parts)
        keep = depth is None or level < depth
        dirnames[:] = [name for name in dirnames if keep and name not in ("node_modules", ".git")]
        if "package.json" in filenames and _matches_workspaces(root, directory, patterns):
            yield directory


def local_prefix(cwd: Path, *, detect_workspace: bool = True) -> tuple[Path, Path | None]:
    """Port of ``@npmcli/config`` ``loadLocalPrefix``: (prefix, auto-detected workspace)."""
    prefix: Path | None = None
    for directory in (cwd, *cwd.parents):
        has_package = (directory / "package.json").is_file()
        if prefix is None:
            if has_package or (directory / "node_modules").is_dir():
                prefix = directory
                if not detect_workspace:
                    break
            continue
        if not has_package:
            continue
        package = _read_package(directory)
        if package is None:
            continue
        patterns = _workspace_patterns(package)
        if (prefix / "package.json").is_file() and _matches_workspaces(directory, prefix, patterns):
            return directory, prefix
    return (prefix or cwd), None


@dataclass
class Target:
    """One command that will rewrite ``node_modules`` folders."""

    label: str
    start: Path
    node_modules: list[Path]


def _project_target(label: str, parsed: ParsedArgs, cwd: Path) -> Target:
    prefix_value = parsed.last("prefix")
    workspaces: list[Path] = []
    if isinstance(prefix_value, str) and prefix_value:
        start = Path(os.path.abspath(cwd / os.path.expanduser(prefix_value)))
        root = start
    else:
        start = cwd
        root, detected = local_prefix(cwd, detect_workspace=parsed.last("workspaces") is not False)
        if detected is not None:
            workspaces.append(detected)
    patterns = _workspace_patterns(_read_package(root) or {})
    names = [str(value) for value in parsed.values("workspace") if isinstance(value, str)]
    if names or parsed.last("workspaces") is True:
        members = list(_workspace_members(root, patterns)) if patterns else []
        for member in members:
            package = _read_package(member) or {}
            relative = member.relative_to(root).as_posix()
            if parsed.last("workspaces") is True or any(
                name in (package.get("name"), relative) or Path(os.path.abspath(root / name)) == member
                for name in names
            ):
                workspaces.append(member)
        for name in names:
            candidate = Path(os.path.abspath(root / name))
            if candidate.is_dir():
                workspaces.append(candidate)
    folders = [root / "node_modules", *(member / "node_modules" for member in workspaces)]
    unique = list(dict.fromkeys(folders))
    return Target(label=label, start=start, node_modules=unique)


def npm_targets(argv: Sequence[str], cwd: Path, env: Mapping[str, str]) -> list[Target]:
    """Return what an ``npm ARGV`` call run from ``cwd`` would rewrite."""
    parsed = parse_npm_argv(argv)
    if not parsed.remain:
        return []
    command = deref_command(parsed.remain[0])
    if command == "exec":
        return _exec_targets(parsed, parsed.remain[1:], cwd, env)
    if _is_global(parsed, env):
        return []
    writes = command in TREE_WRITERS or (command == "audit" and parsed.remain[1:2] == ["fix"])
    if not writes:
        return []
    return [_project_target(f"npm {' '.join(argv)}".strip(), parsed, cwd)]


def npx_targets(argv: Sequence[str], cwd: Path, env: Mapping[str, str]) -> list[Target]:
    """Return what an ``npx ARGV`` call run from ``cwd`` would rewrite."""
    options, command = split_npx_argv(argv)
    parsed = parse_npm_argv(options)
    return _exec_targets(parsed, command, cwd, env)


def _package_name(spec: str) -> str:
    name = spec.rsplit("/", 1)[-1] if spec.startswith(("/", ".", "~")) else spec
    if name.startswith("@"):
        scope, _, rest = name[1:].partition("/")
        return "@" + scope + "/" + rest.split("@", 1)[0]
    return name.split("@", 1)[0]


def _exec_targets(parsed: ParsedArgs, command: Sequence[str], cwd: Path, env: Mapping[str, str]) -> list[Target]:
    """Targets of ``npm exec``: package managers it launches, by name or call string."""
    launches: list[list[str]] = []
    if command:
        launches.append(list(command))
    call = parsed.last("call")
    if isinstance(call, str) and call:
        try:
            words = shlex.split(call)
        except ValueError:
            words = call.split()
        segment: list[str] = []
        for word in [*words, "&&"]:
            if word in _SHELL_SEPARATORS:
                if segment:
                    launches.append(segment)
                segment = []
            else:
                segment.append(word)
    targets: list[Target] = []
    outer = parsed if isinstance(parsed.last("prefix"), str) else None
    for launch in launches:
        for index, word in enumerate(launch):
            manager = _package_name(word)
            if manager not in PACKAGE_MANAGERS:
                continue
            rest = launch[index + 1 :]
            if manager == "npm":
                inner = npm_targets(rest, cwd, env)
            elif manager == "npx":
                inner = npx_targets(rest, cwd, env)
            else:
                inner = [_project_target(f"{manager} {' '.join(rest)}".strip(), parse_npm_argv([]), cwd)]
            if inner and outer is not None:
                inner.append(_project_target(inner[0].label, outer, cwd))
            targets.extend(inner)
            break
    return targets


# --- decision -----------------------------------------------------------------


def worktree_root(start: Path) -> Path:
    """Nearest ancestor holding ``.git`` (a worktree's file or a checkout's dir)."""
    for directory in (start, *start.parents):
        if os.path.lexists(directory / ".git"):
            return directory
    return start


def _first_symlink(root: Path, folder: Path) -> Path:
    try:
        parts = folder.relative_to(root).parts
    except ValueError:
        return folder
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            return current
    return folder


def violations(targets: Sequence[Target]) -> list[tuple[Target, Path, Path, Path]]:
    """``(target, folder, resolved, worktree)`` for each folder resolving outside its worktree."""
    found = []
    for target in targets:
        root = worktree_root(target.start)
        real_root = Path(os.path.realpath(root))
        for folder in target.node_modules:
            if not os.path.lexists(folder):
                continue
            resolved = Path(os.path.realpath(folder))
            if resolved != real_root and real_root not in resolved.parents:
                found.append((target, folder, resolved, root))
    return found


def refusal_message(tool: str, target: Target, folder: Path, resolved: Path, root: Path) -> str:
    link = _first_symlink(root, folder)
    return (
        f"error: agent {tool} shim refused `{target.label}` (#9460).\n"
        f"       {folder} resolves to {resolved}, outside this worktree ({root}).\n"
        "       The command would rewrite or empty that shared folder through the symlink.\n"
        f"       Safe alternative: remove the symlink inside this worktree first (`unlink {link}`\n"
        "       deletes only the link, never its target), then run the install there so it\n"
        "       creates a worktree-local node_modules."
    )


def main(argv: Sequence[str] | None = None, *, cwd: Path | None = None, env: Mapping[str, str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("npm", "npx"):
        print("usage: npm_guard.py {npm|npx} ARGS...", file=sys.stderr)
        return 2
    tool, rest = args[0], args[1:]
    here = Path(os.getcwd()) if cwd is None else cwd
    environment = os.environ if env is None else env
    targets = npm_targets(rest, here, environment) if tool == "npm" else npx_targets(rest, here, environment)
    found = violations(targets)
    if not found:
        return 0
    print(refusal_message(tool, *found[0]), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
