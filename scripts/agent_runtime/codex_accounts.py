"""Labelled Codex homes. Bindings contain locations and budget, never credentials."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
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
# Routes are account {a, b} x kind {sub, api}. Account a keeps its original labels, "sub"
# (the default home) and "api"; every other route is bound by its own entry, under its
# recorded label, in the private codex_accounts.json.
CODEX_BOUND_ACCOUNTS = ("api", "b-sub", "b-api")
CODEX_ACCOUNT_LABELS = (DEFAULT_CODEX_ACCOUNT, *CODEX_BOUND_ACCOUNTS)
# Routes logged in with a ChatGPT subscription, so each has its own plan usage window.
# The "api" routes are billed per token and have none.
CODEX_SUBSCRIPTION_ACCOUNTS = (DEFAULT_CODEX_ACCOUNT, "b-sub")
# Accepted spellings, resolved to the recorded label before anything else reads them.
CODEX_ACCOUNT_ALIASES = {"a-sub": "sub", "a-api": "api", "b": "b-sub"}
# Account a's routes keep their original behaviour; account b's must show a login at admission.
_LOGIN_PROBED_ACCOUNTS = ("b-sub", "b-api")
_LOGIN_STATUS_TIMEOUT_S = 30
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
    if isinstance(raw, str) and raw in CODEX_ACCOUNT_LABELS:
        return raw
    if isinstance(raw, str) and raw in CODEX_ACCOUNT_ALIASES:
        return CODEX_ACCOUNT_ALIASES[raw]
    raise CodexAccountRefused("codex_account_unknown")


def _load_bindings(environ: Mapping[str, str] | None) -> dict[str, CodexAccountBinding]:
    """Read private codex_accounts.json, with the same file protections as Claude bindings.

    Format: {"schema_version": 1, "accounts": {"<label>":
    {"codex_home": "<absolute private directory>", "budget_usd": 200}, ...}}, with one entry
    per bound route label (CODEX_BOUND_ACCOUNTS); a route without one refuses as unbound.
    budget_usd is the meter's reference budget.
    LU_CODEX_ACCOUNTS_FILE overrides the XDG learn-ukrainian config location.
    """
    path = _user_config_file(environ, "LU_CODEX_ACCOUNTS_FILE", "codex_accounts.json")
    try:
        data = None if path is None else _read_private_json(path, limit=16384, code="claude_account_binding")
    except ClaudeAccountRefused as exc:
        raise CodexAccountRefused(exc.code.replace("claude_account", "codex_account")) from None
    if data is None:
        raise CodexAccountRefused("codex_account_binding_missing")
    bindings = {}
    try:
        if (not isinstance(data, dict) or set(data) != {"schema_version", "accounts"}
                or type(data["schema_version"]) is not int or data["schema_version"] != 1
                or not isinstance(data["accounts"], dict) or not data["accounts"]
                or not set(data["accounts"]) <= set(CODEX_BOUND_ACCOUNTS)):
            raise ValueError
        for label, entry in data["accounts"].items():
            if not isinstance(entry, dict) or set(entry) != {"codex_home", "budget_usd"}:
                raise ValueError
            home = entry["codex_home"]
            if (not isinstance(home, str) or not Path(home).is_absolute()
                    or any(ord(c) < 32 or ord(c) == 127 for c in home)):
                raise ValueError
            budget = Decimal(str(entry["budget_usd"]))
            if not budget.is_finite() or budget <= 0:
                raise ValueError
            bindings[label] = CodexAccountBinding(Path(home), budget)
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise CodexAccountRefused("codex_account_binding_invalid") from None
    return bindings


def load_codex_account_binding(environ: Mapping[str, str] | None = None, label: str = "api") -> CodexAccountBinding:
    """The binding of one route; a route the file does not bind refuses, never substitutes."""
    binding = _load_bindings(environ).get(resolve_codex_account_label(label))
    if binding is None:
        raise CodexAccountRefused("codex_account_unbound")
    return binding


def _require_login(env: Mapping[str, str], directory: Path) -> None:
    """Ask Codex whether the bound home holds a login; only the exit status is read."""
    codex = shutil.which("codex", path=env.get("PATH"))
    if codex is None:
        raise CodexAccountRefused("codex_account_login_unverified")
    try:
        result = subprocess.run(
            [codex, "login", "status"], env=dict(env), cwd=directory, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=_LOGIN_STATUS_TIMEOUT_S, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise CodexAccountRefused("codex_account_login_unverified") from None
    if result.returncode != 0:
        raise CodexAccountRefused("codex_account_not_logged_in")


def default_codex_home(environ: Mapping[str, str] | None = None) -> Path:
    """Account a's home (label ``sub``): ``$HOME/.codex``, whatever ``CODEX_HOME`` says."""
    env = os.environ if environ is None else environ
    return Path(env.get("HOME") or Path.home()) / ".codex"


def _validated_bound_home(label: str, bindings: Mapping[str, CodexAccountBinding],
                          environ: Mapping[str, str]) -> Path:
    """The bound home of ``label``: a private directory of this user, not account a's, not shared."""
    if label not in bindings:
        raise CodexAccountRefused("codex_account_unbound")
    try:
        directory = bindings[label].codex_home
        info = directory.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) & 0o077):
            raise CodexAccountRefused("codex_account_home_not_private")
        if directory.resolve() == default_codex_home(environ).resolve():
            raise CodexAccountRefused("codex_account_binding_is_default")
        if any(other != label and os.path.realpath(binding.codex_home) == os.path.realpath(directory)
               for other, binding in bindings.items()):
            raise CodexAccountRefused("codex_account_binding_shared")
    except OSError:
        raise CodexAccountRefused("codex_account_home_unavailable") from None
    return directory


def codex_account_home(label: object, environ: Mapping[str, str] | None = None) -> Path:
    """The home a reader of ``label``'s own state (usage window, login) must use; refuses, never substitutes.

    ``sub`` is ``$HOME/.codex``; ambient ``CODEX_HOME`` is ignored, so a process
    started on another account's home cannot report that account as ``sub``.
    Every other label is its validated binding. Runs no subprocess.
    """
    env = os.environ if environ is None else environ
    label = resolve_codex_account_label(label)
    if label == DEFAULT_CODEX_ACCOUNT:
        return default_codex_home(env)
    return _validated_bound_home(label, _load_bindings(env), env)


def codex_account_of_environment(environ: Mapping[str, str] | None = None) -> str | None:
    """The label whose home ``CODEX_HOME`` selects, or ``None`` when it cannot be attributed.

    Unset, or account a's home, is ``sub``; a bound home is its label. A scoped
    or unknown home, or an unreadable binding file, is ``None``: callers must
    treat it as unattributed, never as a guessed account.
    """
    env = os.environ if environ is None else environ
    home = env.get("CODEX_HOME")
    if not home:
        return DEFAULT_CODEX_ACCOUNT
    try:
        target = os.path.realpath(home)
        if target == os.path.realpath(default_codex_home(env)):
            return DEFAULT_CODEX_ACCOUNT
        bindings = _load_bindings(env)
    except (CodexAccountRefused, OSError, ValueError):
        return None
    matches = [label for label, binding in bindings.items() if os.path.realpath(binding.codex_home) == target]
    return matches[0] if len(matches) == 1 else None


def codex_account_env(label: object, environ: Mapping[str, str]) -> dict[str, str]:
    """Preserve the default route; bind a labelled run to its own home or refuse.

    Called at admission with the ambient environment and again at launch. No auth
    file is opened: Codex itself uses the login already stored in the selected home.
    An account-b route must also report a login there (`codex login status`).
    """
    label = resolve_codex_account_label(label)
    if label == DEFAULT_CODEX_ACCOUNT:
        return dict(environ)
    if any(environ.get(name) for name in _AUTH_ENV):
        raise CodexAccountRefused("codex_account_ambient_conflict")
    directory = _validated_bound_home(label, _load_bindings(environ), environ)
    try:
        if environ.get("CODEX_HOME") and not directory.samefile(Path(environ["CODEX_HOME"])):
            raise CodexAccountRefused("codex_account_ambient_conflict")
    except OSError:
        raise CodexAccountRefused("codex_account_home_unavailable") from None
    env = {name: value for name, value in environ.items() if name not in _AUTH_ENV}
    env["CODEX_HOME"] = str(directory)
    if label in _LOGIN_PROBED_ACCOUNTS:
        _require_login(env, directory)
    return env
