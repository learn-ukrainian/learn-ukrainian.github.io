"""Deployment-specific needles for the repository's leak scanners.

Public code carries only generic patterns. A deployment may install a JSON
file naming its own run users and home directories; scanners add those exact
values to their generic patterns. Without the file (CI, a fresh clone) the
generic patterns still apply, so no scanner ever gets weaker than the
fallback.

The file is a JSON object with ``schema_version`` 1, a ``run_users`` list of
account names and a ``home_dirs`` list of absolute directories.

Location: ``LU_OPSEC_NEEDLES_FILE`` if set (empty means no file), otherwise
``$XDG_CONFIG_HOME/learn-ukrainian/opsec-needles.json`` (the home config
directory when ``XDG_CONFIG_HOME`` is unset). A file that exists but is
malformed raises :class:`NeedlesError` rather than silently scanning with
fewer needles.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

ENV_NEEDLES_FILE = "LU_OPSEC_NEEDLES_FILE"
NEEDLES_FILE_NAME = "opsec-needles.json"
SCHEMA_VERSION = 1

# Any home directory under the usual roots. The look-behind keeps URL paths
# such as ``example.org/home/page`` out while still matching quoted, spaced
# or ``file://`` forms.
GENERIC_HOME_DIR_PATTERN = r"(?<![\w.-])(?:/home|/Users)/[A-Za-z0-9_.-]+"

_RUN_USER_RE = re.compile(r"^[a-z_][a-z0-9_-]*$")


class NeedlesError(ValueError):
    """The needles file exists but does not match the schema."""


@dataclass(frozen=True)
class Needles:
    run_users: tuple[str, ...] = ()
    home_dirs: tuple[str, ...] = ()


def needles_file(environ: Mapping[str, str] | None = None) -> Path | None:
    """Return the needles file path for ``environ`` (``os.environ`` by default)."""
    env = os.environ if environ is None else environ
    if ENV_NEEDLES_FILE in env:
        value = env[ENV_NEEDLES_FILE]
        return Path(value) if value else None
    base = env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "learn-ukrainian" / NEEDLES_FILE_NAME


def _string_list(data: Mapping[str, object], key: str, path: Path) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise NeedlesError(f"{path}: {key!r} must be a list of non-empty strings")
    return tuple(value)


def load_needles(path: Path | None = None, *, environ: Mapping[str, str] | None = None) -> Needles:
    """Load needles from ``path`` (or the configured file); empty when absent."""
    target = needles_file(environ) if path is None else path
    if target is None or not target.is_file():
        return Needles()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NeedlesError(f"{target}: unreadable needles file ({type(exc).__name__})") from None
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise NeedlesError(f"{target}: expected an object with schema_version {SCHEMA_VERSION}")
    run_users = _string_list(data, "run_users", target)
    home_dirs = _string_list(data, "home_dirs", target)
    bad_users = [user for user in run_users if not _RUN_USER_RE.match(user)]
    if bad_users:
        raise NeedlesError(f"{target}: run_users must be account names")
    if any(not home.startswith("/") or home.endswith("/") or any(c.isspace() for c in home) for home in home_dirs):
        raise NeedlesError(f"{target}: home_dirs must be absolute paths without a trailing slash")
    return Needles(run_users=run_users, home_dirs=home_dirs)


def home_dir_pattern(needles: Needles) -> str:
    """Regex alternation matching any home directory plus the deployment's own."""
    exact = [re.escape(home) + r"(?![A-Za-z0-9_.-])" for home in needles.home_dirs]
    return "(?:" + "|".join([GENERIC_HOME_DIR_PATTERN, *exact]) + ")"


def run_user_alias_pattern(needles: Needles) -> str | None:
    """Regex alternation for ``Host <user>`` / ``<user>@`` aliases, if any users are configured."""
    if not needles.run_users:
        return None
    users = "|".join(re.escape(user) for user in needles.run_users)
    return rf"(?:\bHost\s+(?:{users})\b|(?:{users})@)"
