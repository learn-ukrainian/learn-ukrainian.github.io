"""Labelled Codex homes. Bindings contain locations and budget, never credentials."""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from scripts.agent_runtime.attempt_boundary import (
    ClaudeAccountRefused,
    _read_private_json,
    _user_config_file,
)

DEFAULT_CODEX_ACCOUNT = "sub"
_AUTH_ENV = ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN")


class CodexAccountRefused(ValueError):
    """Value-free refusal safe for task records and diagnostics."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"CODEX_ACCOUNT_REFUSED: {code}")


@dataclass(frozen=True)
class CodexAccountBinding:
    codex_home: Path = field(repr=False)
    budget_usd: Decimal


def resolve_codex_account_label(raw: object) -> str:
    if raw is None:
        return DEFAULT_CODEX_ACCOUNT
    if isinstance(raw, str) and raw in ("sub", "api"):
        return raw
    raise CodexAccountRefused("codex_account_unknown")


def load_codex_account_binding(environ: Mapping[str, str] | None = None) -> CodexAccountBinding:
    """Read private codex_accounts.json, with the same file protections as Claude bindings.

    Format: {"schema_version": 1, "accounts": {"api":
    {"codex_home": "<absolute private directory>", "budget_usd": 200}}}.
    LU_CODEX_ACCOUNTS_FILE overrides the XDG learn-ukrainian config location.
    """
    path = _user_config_file(environ, "LU_CODEX_ACCOUNTS_FILE", "codex_accounts.json")
    try:
        data = None if path is None else _read_private_json(path, limit=16384, code="claude_account_binding")
    except ClaudeAccountRefused as exc:
        raise CodexAccountRefused(exc.code.replace("claude_account", "codex_account")) from None
    if data is None:
        raise CodexAccountRefused("codex_account_binding_missing")
    try:
        if (not isinstance(data, dict) or set(data) != {"schema_version", "accounts"}
                or type(data["schema_version"]) is not int or data["schema_version"] != 1
                or not isinstance(data["accounts"], dict) or set(data["accounts"]) != {"api"}):
            raise ValueError
        entry = data["accounts"]["api"]
        if not isinstance(entry, dict) or set(entry) != {"codex_home", "budget_usd"}:
            raise ValueError
        home = entry["codex_home"]
        if (not isinstance(home, str) or not Path(home).is_absolute()
                or any(ord(c) < 32 or ord(c) == 127 for c in home)):
            raise ValueError
        budget = Decimal(str(entry["budget_usd"]))
        if not budget.is_finite() or budget <= 0:
            raise ValueError
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise CodexAccountRefused("codex_account_binding_invalid") from None
    return CodexAccountBinding(Path(home), budget)


def codex_account_env(label: object, environ: Mapping[str, str]) -> dict[str, str]:
    """Preserve the default route; refuse conflicting sources for an API-labelled run.

    Called at admission with the ambient environment and again at launch. No auth
    file is opened: Codex itself uses the login already stored in the selected home.
    """
    if resolve_codex_account_label(label) == DEFAULT_CODEX_ACCOUNT:
        return dict(environ)
    if any(environ.get(name) for name in _AUTH_ENV):
        raise CodexAccountRefused("codex_account_ambient_conflict")
    binding = load_codex_account_binding(environ)
    try:
        directory = binding.codex_home
        info = directory.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) & 0o077):
            raise CodexAccountRefused("codex_account_home_not_private")
        if directory.resolve() == (Path(environ.get("HOME") or Path.home()) / ".codex").resolve():
            raise CodexAccountRefused("codex_account_binding_is_default")
        if environ.get("CODEX_HOME") and not directory.samefile(Path(environ["CODEX_HOME"])):
            raise CodexAccountRefused("codex_account_ambient_conflict")
    except OSError:
        raise CodexAccountRefused("codex_account_home_unavailable") from None
    env = {name: value for name, value in environ.items() if name not in _AUTH_ENV}
    env["CODEX_HOME"] = str(directory)
    return env
