"""Argv and environment rules for an observed process start (#9807).

Reviewed git and gh templates are validators. A start outside those templates,
a shell syntax check, a launch replacement, or a hook-controlled configuration
override is a violation. Launch explanations are not exemptions. A typed
operand matches one reviewed shape: it is never an open argv tail, and an
option-shaped token (``-…``) never fills an operand slot.

Executable resolution and on-disk git/gh configuration are trust assumptions.
A hook-controlled ``executable=``, ``-c``, ``GIT_CONFIG*``, pager, editor,
askpass, or browser variable does not inherit that trust. ``NO_COLOR`` and
``CLICOLOR`` are not command variables. No value of a command variable is an
inert exception: ``PAGER=cat`` is still rejected.
"""

from __future__ import annotations

import json
import os
import re
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

_FIELD_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
_PR_NUMBER = re.compile(r"[1-9][0-9]*\Z")
_PR_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)\Z")
_OWNER_REPO = re.compile(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\Z")
_REF_FORBIDDEN = frozenset(" ~^:?*[\\")
# The corpus docstring contains a backtick example `gh pr merge ... --admin`.
# The parser forwards that ellipsis as the PR selector. It is not a branch
# name (`..` is forbidden) and it is not option-shaped.
_PROSE_ELLIPSIS = "..."
_OPERAND_KEYS = {
    "pr-selector": frozenset({"type"}),
    "owner-repo": frozenset({"type"}),
    "absolute-path": frozenset({"type"}),
    "json-fields": frozenset({"type", "fields"}),
}
_TEMPLATE_KEYS = frozenset({"program", "argv", "serves", "note"})


@dataclass(frozen=True)
class TypedOperand:
    """One reviewed operand slot. ``fields`` is the json allowlist, when used."""

    kind: str
    fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class TemplateCitation:
    """Source line that builds the argv this template validates."""

    file: str
    line: int
    text: str


@dataclass(frozen=True)
class Template:
    program: str
    argv: tuple[str | None | TypedOperand, ...]
    serves: tuple[TemplateCitation, ...]
    note: str = ""


def _operand(value: object) -> str | None | TypedOperand:
    if value is None:
        return None
    if isinstance(value, str):
        if not value:
            raise AssertionError("template literal is empty")
        return value
    if not isinstance(value, dict):
        raise AssertionError(f"template operand has unsupported shape: {value!r}")
    kind = value.get("type")
    expected = _OPERAND_KEYS.get(kind) if isinstance(kind, str) else None
    if expected is None or set(value) != expected:
        raise AssertionError(f"template operand type is not reviewed: {value!r}")
    if kind != "json-fields":
        return TypedOperand(kind)
    fields = value["fields"]
    if (
        not isinstance(fields, list)
        or not fields
        or len(fields) != len(set(fields))
        or not all(isinstance(field, str) and _FIELD_NAME.fullmatch(field) for field in fields)
    ):
        raise AssertionError(f"json field allowlist is not an explicit set: {fields!r}")
    return TypedOperand("json-fields", tuple(fields))


def _citation(value: object) -> TemplateCitation:
    if not isinstance(value, dict) or set(value) != {"file", "line", "text"}:
        raise AssertionError(f"template citation is incomplete: {value!r}")
    path = value["file"]
    line = value["line"]
    text = value["text"]
    if (
        not isinstance(path, str)
        or not path
        or path.startswith("/")
        or "\\" in path
        or ".." in Path(path).parts
        or isinstance(line, bool)
        or not isinstance(line, int)
        or line < 1
        or not isinstance(text, str)
        or not text
    ):
        raise AssertionError(f"template citation is not a repo line: {value!r}")
    return TemplateCitation(path, line, text)


def load_template_records() -> tuple[Template, ...]:
    """Reviewed argv templates. Each one cites the hook line it validates."""
    payload = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    if payload.get("role") != "runtime argv validators, not exemptions":
        raise AssertionError("command template fixture lost its validator role")
    raw_templates = payload.get("templates")
    if not isinstance(raw_templates, list) or not raw_templates:
        raise AssertionError("command template fixture has no templates")
    records: list[Template] = []
    for item in raw_templates:
        if not isinstance(item, dict) or not {"program", "argv", "serves"} <= set(item) <= _TEMPLATE_KEYS:
            raise AssertionError(f"template record is not reviewed: {item!r}")
        program = item["program"]
        raw_argv = item["argv"]
        raw_serves = item["serves"]
        note = item.get("note", "")
        if program not in GIT_GH or not isinstance(raw_argv, list) or not raw_argv:
            raise AssertionError(f"template program or argv is not reviewed: {item!r}")
        if not isinstance(raw_serves, list) or not raw_serves or not isinstance(note, str):
            raise AssertionError(f"template citation is missing: {item!r}")
        argv = tuple(_operand(part) for part in raw_argv)
        literals = [part for part in argv if isinstance(part, str)]
        if config_injection_tokens(literals):
            raise AssertionError(f"template contains a config-injection token: {literals!r}")
        records.append(
            Template(
                program,
                argv,
                tuple(_citation(cite) for cite in raw_serves),
                note,
            )
        )
    return tuple(records)


def load_templates() -> tuple[tuple[str, tuple[str | None | TypedOperand, ...]], ...]:
    return tuple((record.program, record.argv) for record in load_template_records())


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


def _ref_piece(piece: str) -> bool:
    """Owner or repo piece: the reviewed character class, and not option-shaped."""
    return bool(piece) and not piece.startswith("-") and piece not in {".", ".."}


def _branch_name(token: str) -> bool:
    """Git ``check-ref-format --branch`` name. Option-shaped tokens are refused."""
    if not token or token.startswith("-") or token in {"@", "HEAD"}:
        return False
    if token.startswith("/") or token.endswith("/") or token.endswith("."):
        return False
    if ".." in token or "@{" in token or "//" in token:
        return False
    if any(ord(char) < 32 or ord(char) == 127 or char in _REF_FORBIDDEN for char in token):
        return False
    return all(part and not part.startswith(".") and not part.endswith(".lock") for part in token.split("/"))


def _pr_selector(token: str) -> bool:
    """PR number, branch name, GitHub pull URL, or the one prose ellipsis."""
    if token == _PROSE_ELLIPSIS:
        return True
    if _PR_NUMBER.fullmatch(token):
        return True
    url = _PR_URL.fullmatch(token)
    if url is not None:
        owner, repo, _number = url.groups()
        return _ref_piece(owner) and _ref_piece(repo)
    return _branch_name(token)


def _owner_repo(token: str) -> bool:
    """``--repo`` value ``<owner>/<repo>`` matching the reviewed character class."""
    if not token or token.startswith("-"):
        return False
    match = _OWNER_REPO.fullmatch(token)
    if match is None:
        return False
    owner, repo = match.groups()
    return _ref_piece(owner) and _ref_piece(repo)


def _json_fields(token: str, fields: tuple[str, ...]) -> bool:
    """Comma list whose names are exactly the template's field allowlist."""
    if not token or token.startswith("-"):
        return False
    parts = token.split(",")
    if len(parts) != len(fields) or len(set(parts)) != len(parts):
        return False
    return set(parts) == set(fields)


def _absolute_path(token: str) -> bool:
    """``git -C`` operand: an absolute path, never an option.

    An existing directory is the reviewed case. Production also passes a
    not-yet-created absolute path (the write target's parent is missing, so
    ``git -C`` receives that missing path). An existing file is not a directory
    operand. A relative path is refused so this check does not use the
    auditor's cwd.
    """
    if not token or token.startswith("-") or "\x00" in token or "\n" in token or "\r" in token:
        return False
    path = Path(token)
    if not path.is_absolute():
        return False
    if path.exists():
        return path.is_dir()
    return True


def _match_part(token: str, part: str | None | TypedOperand) -> bool:
    if part is None:
        return bool(token) and not token.startswith("-")
    if isinstance(part, str):
        return token == part
    if part.kind == "pr-selector":
        return _pr_selector(token)
    if part.kind == "owner-repo":
        return _owner_repo(token)
    if part.kind == "json-fields":
        return _json_fields(token, part.fields)
    if part.kind == "absolute-path":
        return _absolute_path(token)
    return False


def matches_template(argv: Sequence[str]) -> bool:
    """True when ``argv`` is one reviewed template and carries no config injection."""
    if len(argv) < 2 or config_injection_tokens(argv):
        return False
    name = executable_name(argv[0])
    rest = list(argv[1:])
    for template_name, parts in load_templates():
        if name != template_name or len(rest) != len(parts):
            continue
        if all(_match_part(token, part) for token, part in zip(rest, parts, strict=True)):
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
