"""Default-deny rules for an observed hook process start (#9807).

A start is allowed only when it matches one typed template. Shell-mediated
events (``os.system``, ``shell=True``, ``sh -c``) are violations even when the
command string would have matched a template. Unknown programs and wrappers
are violations. Basename equality does not authorize an executable path.

Executable resolution and on-disk git/gh configuration are trust assumptions
of the harness baseline. A hook-controlled ``executable=``, ``PATH``, ``HOME``,
``XDG_CONFIG_HOME``, ``GH_CONFIG_DIR``, ``GIT_EXEC_PATH``, ``GIT_REDIRECT_ENV_KEYS``
value, ``-c``, pager, editor, askpass, or browser variable does not inherit
that trust. ``NO_COLOR`` and ``CLICOLOR`` are not command variables. No value
of a command variable is an inert exception: ``PAGER=cat`` is still rejected.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from scripts.common.git_context import GIT_REDIRECT_ENV_KEYS
from scripts.common.repo_root import project_interpreter

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
TEMPLATE_PATH = FIXTURE_DIR / "command_templates.json"
EXPLANATION_PATH = FIXTURE_DIR / "launch_explanations.json"

# Dropping inherited-environment checks is a held-out mutation, not a mode.
DROP_INHERITED_ENV = "HOOK_RUNTIME_DROP_INHERITED_ENV"

SYNTAX_SHELLS = frozenset({"bash", "sh", "dash", "zsh"})
GIT_GH = frozenset({"git", "gh"})
PROGRAMS = frozenset({"git", "gh", "python"})
_TEMPLATE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

# Command variables named by the runtime decision. GIT_CONFIG and GIT_CONFIG_*
# are configuration injection, including GIT_CONFIG_PARAMETERS.
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

# Harness-controlled locations. A launch may keep the baseline value. A hook
# change, including a newly set or dropped key, is a violation. GIT_COMMON_DIR
# and the rest of GIT_REDIRECT_ENV_KEYS are repository redirection.
REDIRECT_KEYS = frozenset(GIT_REDIRECT_ENV_KEYS) | {
    "GH_CONFIG_DIR",
    "GIT_EXEC_PATH",
    "HOME",
    "PATH",
    "XDG_CONFIG_HOME",
}

# Python-loading overrides matter when a Python image would run. The healer's
# child is not executed; a launch that still names Python is held to these keys.
PYTHON_LOADER_KEYS = frozenset(
    {
        "PYTHONEXECUTABLE",
        "PYTHONHOME",
        "PYTHONINSPECT",
        "PYTHONPATH",
        "PYTHONSAFEPATH",
        "PYTHONSTARTUP",
    }
)

# Color switches the guards set so gh does not emit ANSI JSON. They are not
# command variables and are not on the injection list.
INERT_COLOR_VARIABLES = frozenset({"CLICOLOR", "NO_COLOR"})

_FIELD_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
_PR_NUMBER = re.compile(r"[1-9][0-9]*\Z")
_PR_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)\Z")
_OWNER_REPO = re.compile(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\Z")
_API_ENDPOINT = re.compile(r"repos/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/branches/(.+)/protection\Z")
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
    "api-endpoint": frozenset({"type"}),
    "project-interpreter": frozenset({"type"}),
    "repo-script": frozenset({"type", "path"}),
    "repository-root": frozenset({"type"}),
}
_TEMPLATE_KEYS = frozenset({"id", "program", "argv", "serves", "note"})
PYTHON_TEMPLATE_ID = "python-check-core-bare"


@dataclass(frozen=True)
class TypedOperand:
    """One reviewed operand slot. ``fields`` is the json allowlist, when used."""

    kind: str
    fields: tuple[str, ...] = ()
    script: str = ""


@dataclass(frozen=True)
class TemplateCitation:
    """Source line that builds the argv this template validates."""

    file: str
    line: int
    text: str


@dataclass(frozen=True)
class Template:
    id: str
    program: str
    argv: tuple[str | TypedOperand, ...]
    serves: tuple[TemplateCitation, ...]
    note: str = ""


def _operand(value: object) -> str | TypedOperand:
    if value is None or value == "":
        raise AssertionError("template operand is untyped")
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        raise AssertionError(f"template operand has unsupported shape: {value!r}")
    kind = value.get("type")
    expected = _OPERAND_KEYS.get(kind) if isinstance(kind, str) else None
    if expected is None or set(value) != expected:
        raise AssertionError(f"template operand type is not reviewed: {value!r}")
    if kind == "json-fields":
        fields = value["fields"]
        if (
            not isinstance(fields, list)
            or not fields
            or len(fields) != len(set(fields))
            or not all(isinstance(field, str) and _FIELD_NAME.fullmatch(field) for field in fields)
        ):
            raise AssertionError(f"json field allowlist is not an explicit set: {fields!r}")
        return TypedOperand("json-fields", tuple(fields))
    if kind == "repo-script":
        relative = value["path"]
        if (
            not isinstance(relative, str)
            or not relative
            or relative.startswith("/")
            or "\\" in relative
            or ".." in Path(relative).parts
        ):
            raise AssertionError(f"repo script is not a relative path: {relative!r}")
        return TypedOperand("repo-script", script=relative)
    return TypedOperand(kind)


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


@lru_cache(maxsize=1)
def load_template_records() -> tuple[Template, ...]:
    """Reviewed argv templates. Each one cites the hook line it validates."""
    payload = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    if payload.get("role") != "runtime argv validators, not exemptions":
        raise AssertionError("command template fixture lost its validator role")
    raw_templates = payload.get("templates")
    if not isinstance(raw_templates, list) or not raw_templates:
        raise AssertionError("command template fixture has no templates")
    records: list[Template] = []
    seen: set[str] = set()
    for item in raw_templates:
        if not isinstance(item, dict) or not {"id", "program", "argv", "serves"} <= set(item) <= _TEMPLATE_KEYS:
            raise AssertionError(f"template record is not reviewed: {item!r}")
        template_id = item["id"]
        program = item["program"]
        raw_argv = item["argv"]
        raw_serves = item["serves"]
        note = item.get("note", "")
        if not isinstance(template_id, str) or _TEMPLATE_ID.fullmatch(template_id) is None or template_id in seen:
            raise AssertionError(f"template id is not a unique slug: {template_id!r}")
        seen.add(template_id)
        if program not in PROGRAMS or not isinstance(raw_argv, list) or not raw_argv:
            raise AssertionError(f"template program or argv is not reviewed: {item!r}")
        if not isinstance(raw_serves, list) or not raw_serves or not isinstance(note, str):
            raise AssertionError(f"template citation is missing: {item!r}")
        argv = tuple(_operand(part) for part in raw_argv)
        if any(part is None for part in argv):
            raise AssertionError(f"template has an untyped operand: {template_id}")
        literals = [part for part in argv if isinstance(part, str)]
        if config_injection_tokens(literals):
            raise AssertionError(f"template contains a config-injection token: {literals!r}")
        if program == "python" and any(part in {"-c", "-m"} for part in literals):
            raise AssertionError("python template allows code execution")
        records.append(
            Template(
                template_id,
                program,
                argv,
                tuple(_citation(cite) for cite in raw_serves),
                note,
            )
        )
    return tuple(records)


def load_templates() -> tuple[tuple[str, tuple[str | TypedOperand, ...]], ...]:
    return tuple((record.program, record.argv) for record in load_template_records())


def template_ids() -> tuple[str, ...]:
    """Frozen launch-inventory ids, in fixture order."""
    return tuple(record.id for record in load_template_records())


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


def is_redirect_key(name: str) -> bool:
    return name in REDIRECT_KEYS


def looks_like_python(argv: Sequence[str]) -> bool:
    return bool(argv) and executable_name(argv[0]).startswith("python")


def drop_inherited_env() -> bool:
    return os.environ.get(DROP_INHERITED_ENV) == "1"


def injection_names(
    *,
    explicit: Mapping[str, str] | None,
    inherited: Mapping[str, str],
    baseline: Mapping[str, str],
    python_launch: bool,
) -> tuple[str, ...]:
    """Key names whose presence or baseline difference is a hook-controlled redirect.

    Values stay in the caller. The returned names are safe to log.
    """
    if explicit is None and drop_inherited_env():
        return ()
    source = explicit if explicit is not None else inherited
    names: set[str] = set()
    for key, value in source.items():
        if is_command_variable(key):
            names.add(key)
            continue
        if is_redirect_key(key) and baseline.get(key) != value:
            names.add(key)
            continue
        if python_launch and key in PYTHON_LOADER_KEYS and baseline.get(key) != value:
            names.add(key)
    for key, value in baseline.items():
        if not value or key in source:
            continue
        if is_redirect_key(key) or (python_launch and key in PYTHON_LOADER_KEYS):
            names.add(key)
    return tuple(sorted(names))


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


def _repository_root(token: str) -> bool:
    """Directory the healer discovered by walking to ``scripts/common/repo_root.py``."""
    if not _absolute_path(token):
        return False
    path = Path(token)
    return path.is_dir() and (path / "scripts" / "common" / "repo_root.py").is_file()


def _api_endpoint(token: str) -> bool:
    """``repos/<owner>/<repo>/branches/<branch>/protection`` and nothing else."""
    if not token or token.startswith("-") or token.startswith("/") or "?" in token or "\\" in token:
        return False
    match = _API_ENDPOINT.fullmatch(token)
    if match is None:
        return False
    owner, repo, branch = match.groups()
    if not (_ref_piece(owner) and _ref_piece(repo)):
        return False
    if not branch or branch.startswith("-") or branch.startswith("/") or branch.endswith("/"):
        return False
    if ".." in branch or "//" in branch or "@{" in branch:
        return False
    return all(part and not part.startswith("-") and part not in {".", ".."} for part in branch.split("/"))


def _match_part(token: str, part: str | TypedOperand) -> bool:
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
    if part.kind == "api-endpoint":
        return _api_endpoint(token)
    return False


def _match_python(argv: Sequence[str], record: Template) -> bool:
    """Exact interpreter, script, ``--repo`` root, ``--fix``, and ``-q``."""
    parts = record.argv
    if len(argv) != len(parts) or any(token in {"-c", "-m"} for token in argv):
        return False
    root: str | None = None
    script_token = ""
    script_rel = ""
    interpreter = ""
    for token, part in zip(argv, parts, strict=True):
        if isinstance(part, str):
            if token != part:
                return False
            continue
        if part.kind == "repository-root":
            if not _repository_root(token):
                return False
            root = token
            continue
        if part.kind == "repo-script":
            script_token = token
            script_rel = part.script
            continue
        if part.kind == "project-interpreter":
            interpreter = token
            continue
        return False
    if root is None or not script_rel or not interpreter:
        return False
    if script_token != str(Path(root) / script_rel):
        return False
    try:
        expected = str(project_interpreter(Path(root)))
    except (OSError, FileNotFoundError):
        return False
    return interpreter == expected


def _match_record(argv: Sequence[str], record: Template) -> bool:
    if record.program in GIT_GH:
        if not argv or argv[0] != record.program:
            return False
        rest = list(argv[1:])
        if len(rest) != len(record.argv):
            return False
        return all(_match_part(token, part) for token, part in zip(rest, record.argv, strict=True))
    if record.program == "python":
        return _match_python(argv, record)
    return False


def identify_template(argv: Sequence[str]) -> str | None:
    """Template id when ``argv`` is one reviewed shape and carries no config injection."""
    if len(argv) < 2 or config_injection_tokens(argv):
        return None
    for record in load_template_records():
        if _match_record(argv, record):
            return record.id
    return None


def matches_template(argv: Sequence[str]) -> bool:
    """True when ``argv`` is one reviewed template and carries no config injection."""
    return identify_template(argv) is not None


@dataclass(frozen=True)
class ObservedStart:
    """One process-start audit record. ``explicit_env`` None means the process inherits.

    ``env_injection`` is key names only. When it is set, those names are the
    injection finding and the env mappings are not read again.
    """

    event: str
    pid: int
    parent_pid: int
    pair_index: int
    executable: str
    argv: tuple[str, ...]
    explicit_env: dict[str, str] | None
    inherited_dangerous: dict[str, str]
    shell_mediated: str = ""
    env_injection: tuple[str, ...] | None = None
    explicit: bool = False

    @property
    def child_of_fork(self) -> bool:
        return self.pid != self.parent_pid


def shell_kind_of(start: ObservedStart) -> str:
    """Shell event kind. ``os.system`` stays a shell event after the command is split."""
    if start.shell_mediated:
        return start.shell_mediated
    return _argv_shell_kind(start.argv)


def _argv_shell_kind(argv: Sequence[str]) -> str:
    if len(argv) < 2:
        return ""
    exe = executable_name(argv[0])
    if exe in SYNTAX_SHELLS and "-c" in argv[1:]:
        return f"{exe} -c"
    return ""


def _shell_words(start: ObservedStart) -> tuple[str, ...] | None:
    """Words inside a shell event. The shell's own ``-c`` is not one of them."""
    kind = shell_kind_of(start)
    if not kind:
        return None
    if kind == "os.system":
        return start.argv
    for index, token in enumerate(start.argv):
        if token == "-c" and index + 1 < len(start.argv):
            payload = start.argv[index + 1]
            try:
                return tuple(shlex.split(payload, posix=True))
            except ValueError:
                return (payload,)
    return None


def _embedded_syntax(argv: Sequence[str]) -> str | None:
    """Syntax check behind a wrapper such as ``timeout`` or ``env``."""
    for index, token in enumerate(argv):
        if executable_name(token) in SYNTAX_SHELLS:
            detail = syntax_check_detail(tuple(argv[index:]))
            if detail:
                return detail
    return None


def _syntax_reasons(start: ObservedStart) -> tuple[str, ...]:
    found: list[str] = []
    words = _shell_words(start)
    if words is None:
        detail = syntax_check_detail(start.argv)
        if detail:
            found.append(detail)
        embedded = _embedded_syntax(start.argv)
        if embedded and embedded not in found:
            found.append(embedded)
    else:
        detail = syntax_check_detail(words)
        if detail:
            found.append(detail)
    return tuple(f"syntax-check:{item}" for item in found)


def _config_reason(start: ObservedStart) -> str | None:
    words = _shell_words(start)
    if words is None:
        if not start.argv or start.argv[0] not in GIT_GH:
            return None
        tokens: Sequence[str] = start.argv
    else:
        tokens = words
    injected = config_injection_tokens(tokens)
    if not injected:
        return None
    return "config-injection:" + ",".join(injected)


def _launch_replacement(start: ObservedStart) -> bool:
    if not start.argv or not start.executable:
        return False
    return executable_name(start.executable) != executable_name(start.argv[0])


def _executable_override(start: ObservedStart) -> bool:
    """Full executable path, independent of argv. Same basename is not permission."""
    exe = start.executable
    if not exe or not start.argv:
        return False
    argv0 = start.argv[0]
    if executable_name(exe) == executable_name(argv0) and exe != argv0:
        return True
    if exe == argv0 and ("/" in exe or exe.startswith(".")):
        return identify_template(start.argv) != PYTHON_TEMPLATE_ID
    return False


def _resolved_injection(start: ObservedStart) -> tuple[str, ...]:
    if start.env_injection is not None:
        return tuple(sorted(set(start.env_injection)))
    source: dict[str, str] = {}
    if start.explicit_env is not None:
        source.update(start.explicit_env)
    elif not drop_inherited_env():
        source.update(start.inherited_dangerous)
    names = [key for key in source if is_command_variable(key) or is_redirect_key(key)]
    return tuple(sorted(names))


def _miss_reason(argv: Sequence[str]) -> str:
    token = argv[0] if argv else ""
    base = executable_name(token)
    if base in GIT_GH:
        return "unclassified-argv"
    return f"unknown-program:{base or 'empty'}"


def classify_start(start: ObservedStart) -> tuple[str, ...]:
    """Violation reasons for one start. Empty means the start matches one template."""
    reasons: list[str] = []
    kind = shell_kind_of(start)
    if kind:
        reasons.append(f"shell-mediated:{kind}")
    reasons.extend(_syntax_reasons(start))
    replaced = _launch_replacement(start)
    overridden = _executable_override(start)
    if replaced:
        reasons.append("launch-replacement")
    if overridden:
        reasons.append("executable-override")
    config = _config_reason(start)
    if config:
        reasons.append(config)
    injected = _resolved_injection(start)
    if injected:
        reasons.append("env-injection:" + ",".join(injected))
    # A shell event is never a direct template, even when its words match one.
    matched = (not kind) and identify_template(start.argv) is not None
    blocked = bool(kind) or replaced or overridden or bool(config) or bool(injected)
    if blocked:
        if not matched and not kind:
            reasons.append(_miss_reason(start.argv))
        return tuple(reasons)
    if not matched:
        reasons.append(_miss_reason(start.argv))
    return tuple(reasons)


def allowed_template(start: ObservedStart) -> str | None:
    """Template id when the start is allowed. Shell events never return an id."""
    if classify_start(start):
        return None
    return identify_template(start.argv)


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


def attempted_start(event: ObservedStart) -> bool:
    """True for a hook process start. The driver's canary and forks are not starts."""
    if event.event in {"os.fork", "os.forkpty"}:
        return False
    return event.argv != ("__audit_canary__", "intercept")
