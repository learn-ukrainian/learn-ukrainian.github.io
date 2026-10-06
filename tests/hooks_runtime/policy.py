"""Argv and environment rules for an observed process start (#9807).

Reviewed git and gh templates are validators. A start outside those templates,
a shell syntax check, a launch replacement, or a hook-controlled configuration
override is a violation. Launch explanations are not exemptions.

Executable resolution and on-disk git/gh configuration are trust assumptions.
A hook-controlled ``executable=``, ``-c``, ``GIT_CONFIG*``, pager, editor,
askpass, or browser variable does not inherit that trust. ``NO_COLOR`` and
``CLICOLOR`` are not command variables. No value of a command variable is an
inert exception: ``PAGER=cat`` is still rejected.
"""

from __future__ import annotations

import json
import os
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
TEMPLATE_PATH = FIXTURE_DIR / "command_templates.json"
EXPLANATION_PATH = FIXTURE_DIR / "launch_explanations.json"

# Dropping inherited-environment checks is a held-out mutation, not a mode.
DROP_INHERITED_ENV = "HOOK_RUNTIME_DROP_INHERITED_ENV"

SYNTAX_SHELLS = frozenset({"bash", "sh", "dash", "zsh"})
GIT_GH = frozenset({"git", "gh"})

# Command variables named by the runtime decision, plus GIT_EDITOR from the
# proposal and GIT_EXTERNAL_DIFF (git executes it the same way it executes
# GIT_SSH_COMMAND). GIT_CONFIG and GIT_CONFIG_* are configuration injection.
EXACT_COMMAND_VARIABLES = frozenset(
    {
        "BROWSER",
        "EDITOR",
        "GH_BROWSER",
        "GH_EDITOR",
        "GH_PAGER",
        "GIT_ASKPASS",
        "GIT_EDITOR",
        "GIT_EXTERNAL_DIFF",
        "GIT_PAGER",
        "GIT_SEQUENCE_EDITOR",
        "GIT_SSH",
        "GIT_SSH_COMMAND",
        "PAGER",
        "SSH_ASKPASS",
        "SSH_ASKPASS_REQUIRE",
        "VISUAL",
    }
)

# Color switches the guards set so gh does not emit ANSI JSON. They are not
# command variables and are not on the injection list.
INERT_COLOR_VARIABLES = frozenset({"CLICOLOR", "NO_COLOR"})


def load_templates() -> tuple[tuple[str, tuple[str | None, ...]], ...]:
    payload = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    if payload.get("role") != "runtime argv validators, not exemptions":
        raise AssertionError("command template fixture lost its validator role")
    templates: list[tuple[str, tuple[str | None, ...]]] = []
    for name, parts in payload["templates"]:
        templates.append((name, tuple(parts)))
    return tuple(templates)


def load_explanations() -> tuple[dict[str, str], ...]:
    payload = json.loads(EXPLANATION_PATH.read_text(encoding="utf-8"))
    if payload.get("role") != "runtime fixtures, not exemptions":
        raise AssertionError("launch explanations were reclassified as exemptions")
    return tuple(payload["entries"])


def executable_name(token: str) -> str:
    return token.replace("\\", "/").rsplit("/", 1)[-1]


def _decode(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "surrogateescape")
    return None


def argv_requests_syntax_check(argv: Sequence[str]) -> bool:
    """True when literal words ask a shell not to execute.

    A short-option cluster containing ``n`` (``-n``, ``-nc``, ``-xn``),
    ``--noexec``, or ``-o noexec`` is a syntax check.
    """
    for index, token in enumerate(argv):
        if token == "--noexec":
            return True
        if token == "-o" and index + 1 < len(argv) and argv[index + 1] == "noexec":
            return True
        if token.startswith("-") and not token.startswith("--") and "n" in token[1:]:
            return True
    return False


def syntax_check_detail(argv: Sequence[str]) -> str | None:
    """Return ``bash -n`` style detail when ``argv`` is a literal syntax check."""
    if not argv:
        return None
    words = list(argv)
    exe = executable_name(words[0])
    rest = words[1:]
    if exe == "env":
        index = 0
        while index < len(rest):
            token = rest[index]
            name = executable_name(token)
            if name in SYNTAX_SHELLS:
                exe = name
                rest = rest[index + 1 :]
                break
            if token in {"-i", "-"} or token.startswith("-u") or "=" in token or token.startswith("-"):
                index += 2 if token in {"-u", "-S"} else 1
                continue
            return None
        else:
            return None
    if exe not in SYNTAX_SHELLS or not argv_requests_syntax_check(rest):
        return None
    for index, token in enumerate(rest):
        if token == "--noexec":
            return f"{exe} --noexec"
        if token == "-o" and index + 1 < len(rest) and rest[index + 1] == "noexec":
            return f"{exe} -o noexec"
        if token.startswith("-") and not token.startswith("--") and "n" in token[1:]:
            return f"{exe} {token}"
    return None


def is_command_variable(name: str) -> bool:
    if name in INERT_COLOR_VARIABLES:
        return False
    return name in EXACT_COMMAND_VARIABLES or name == "GIT_CONFIG" or name.startswith("GIT_CONFIG_")


def dangerous_snapshot(mapping: Mapping[str, str] | None) -> dict[str, str]:
    if not mapping:
        return {}
    return {key: value for key, value in mapping.items() if is_command_variable(key)}


def drop_inherited_env() -> bool:
    return os.environ.get(DROP_INHERITED_ENV) == "1"


def config_injection_tokens(argv: Sequence[str]) -> tuple[str, ...]:
    """Option and alias forms that make git or gh run hook-controlled config."""
    found: list[str] = []
    for token in argv:
        if token == "-c" or (token.startswith("-c") and not token.startswith("--")):
            found.append(token)
            continue
        if token == "--config" or token.startswith("--config=") or token == "--config-env" or token.startswith(
            "--config-env="
        ):
            found.append(token)
            continue
        if token.startswith("!"):
            found.append(token)
            continue
        if "alias." in token and "!" in token:
            found.append(token)
    return tuple(found)


def matches_template(argv: Sequence[str]) -> bool:
    """True when ``argv`` is one reviewed template and carries no config injection."""
    if len(argv) < 2 or config_injection_tokens(argv):
        return False
    name = executable_name(argv[0])
    rest = list(argv[1:])
    for template_name, parts in load_templates():
        if name != template_name or len(rest) != len(parts):
            continue
        matched = True
        for token, part in zip(rest, parts, strict=True):
            if part is None:
                if not token or token.startswith("-"):
                    matched = False
                    break
                continue
            if token != part:
                matched = False
                break
        if matched:
            return True
    return False


@dataclass(frozen=True)
class ObservedStart:
    """One process-start audit record. ``explicit_env`` None means the process inherits."""

    event: str
    pid: int
    parent_pid: int
    pair_index: int
    executable: str
    argv: tuple[str, ...]
    explicit_env: dict[str, str] | None
    inherited_dangerous: dict[str, str]

    @property
    def child_of_fork(self) -> bool:
        return self.pid != self.parent_pid


def effective_argv(start: ObservedStart) -> tuple[str, ...]:
    """Argv the kernel would see, including an ``executable=`` replacement."""
    argv = start.argv
    executable = start.executable
    if not executable:
        return argv
    if not argv:
        return (executable,)
    if executable_name(executable) != executable_name(argv[0]):
        return (executable, *argv)
    return argv


def classify_start(start: ObservedStart) -> tuple[str, ...]:
    """Violation reasons for one start. Empty means the start is inside the rules."""
    reasons: list[str] = []
    argv = effective_argv(start)
    detail = syntax_check_detail(argv) or syntax_check_detail(start.argv)
    if detail is not None:
        reasons.append(f"syntax-check:{detail}")
    if start.argv and start.executable and executable_name(start.executable) != executable_name(start.argv[0]):
        reasons.append("launch-replacement")
    program = executable_name(start.argv[0]) if start.argv else executable_name(start.executable)
    if program in GIT_GH or executable_name(start.executable) in GIT_GH:
        if not matches_template(start.argv):
            reasons.append("unclassified-argv")
        injected = config_injection_tokens(start.argv)
        if injected:
            reasons.append("config-injection:" + ",".join(injected))
    dangerous = dict(start.explicit_env or {})
    if start.explicit_env is None and not drop_inherited_env():
        dangerous.update(start.inherited_dangerous)
    dangerous = {key: value for key, value in dangerous.items() if is_command_variable(key)}
    if dangerous:
        names = ",".join(sorted(dangerous))
        reasons.append(f"env-injection:{names}")
    return tuple(reasons)


def text_argv(value: object) -> tuple[str, ...] | None:
    """Decode an audit argv that may contain str and bytes."""
    if isinstance(value, (str, bytes)):
        text = _decode(value)
        if text is None:
            return None
        try:
            return tuple(shlex.split(text, posix=True))
        except ValueError:
            return (text,)
    if isinstance(value, (list, tuple)):
        words: list[str] = []
        for item in value:
            text = _decode(item)
            if text is None:
                return None
            words.append(text)
        return tuple(words)
    return None
