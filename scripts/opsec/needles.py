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
directory when ``XDG_CONFIG_HOME`` is unset, empty or relative). An absent
default location falls back to the generic patterns; a missing non-empty
override fails closed. Anything else that cannot be read
as a valid file (a directory, a dangling link, a malformed payload) raises
:class:`NeedlesError` rather than silently scanning with fewer needles.
Error messages never repeat the configured location or its contents.
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
# or ``file://`` forms. A name must start with a letter, digit or underscore,
# so elided examples (three dots) and dot-directories do not count.
# JSON serialization turns control-character separators into escapes. Match
# those separators too, without treating arbitrary escaped letters as boundaries.
_HOME_DIR_BOUNDARY = r"(?:(?<![\w.-])|(?<=\\[bfnrt])|(?<=\\x[0-9A-Fa-f]{2})|(?<=\\u[0-9A-Fa-f]{4}))"
GENERIC_HOME_DIR_PATTERN = _HOME_DIR_BOUNDARY + r"(?:/home|/Users)/[A-Za-z0-9_][A-Za-z0-9_.-]*"

_RUN_USER_RE = re.compile(r"^[a-z_][a-z0-9_-]*$")


_LABEL = "needles file"


class NeedlesError(ValueError):
    """The needles location holds something that is not a valid needles file."""


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
    base = env.get("XDG_CONFIG_HOME")
    if not base or not Path(base).is_absolute():
        base = str(Path.home() / ".config")
    return Path(base) / "learn-ukrainian" / NEEDLES_FILE_NAME


def _string_list(data: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise NeedlesError(f"{_LABEL}: {key!r} must be a list of non-empty strings")
    return tuple(value)


def _is_absent(target: Path) -> bool:
    """True only when nothing (not even a dangling link) is at ``target``."""
    try:
        target.lstat()
    except FileNotFoundError:
        return True
    except OSError as exc:
        raise NeedlesError(f"{_LABEL}: location cannot be inspected ({type(exc).__name__})") from None
    return False


def _is_schema_version(value: object) -> bool:
    # ``bool`` is an ``int`` subclass and ``True == 1``; require a real integer.
    return type(value) is int and value == SCHEMA_VERSION


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate JSON keys without disclosing the offending key."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise NeedlesError(f"{_LABEL}: duplicate object key")
        result[key] = value
    return result


def load_needles(path: Path | None = None, *, environ: Mapping[str, str] | None = None) -> Needles:
    """Load needles from ``path`` (or the configured file); empty only when absent."""
    target = needles_file(environ) if path is None else path
    if target is None:
        return Needles()
    if _is_absent(target):
        env = os.environ if environ is None else environ
        if path is None and env.get(ENV_NEEDLES_FILE):
            raise NeedlesError(f"{_LABEL}: configured override is absent")
        return Needles()
    if not target.is_file():
        raise NeedlesError(f"{_LABEL}: location exists but is not a readable regular file")
    try:
        data = json.loads(target.read_text(encoding="utf-8"), object_pairs_hook=_unique_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NeedlesError(f"{_LABEL}: unreadable ({type(exc).__name__})") from None
    if not isinstance(data, dict) or not _is_schema_version(data.get("schema_version")):
        raise NeedlesError(f"{_LABEL}: expected an object with integer schema_version {SCHEMA_VERSION}")
    if data.keys() - {"schema_version", "run_users", "home_dirs"}:
        raise NeedlesError(f"{_LABEL}: unknown object key")
    run_users = _string_list(data, "run_users")
    home_dirs = _string_list(data, "home_dirs")
    bad_users = [user for user in run_users if not _RUN_USER_RE.fullmatch(user)]
    if bad_users:
        raise NeedlesError(f"{_LABEL}: run_users must be account names")
    if any(not home.startswith("/") or home.endswith("/") or any(c.isspace() for c in home) for home in home_dirs):
        raise NeedlesError(f"{_LABEL}: home_dirs must be absolute paths without a trailing slash")
    return Needles(run_users=run_users, home_dirs=home_dirs)


def home_dir_pattern(needles: Needles) -> str:
    """Regex alternation matching any home directory plus the deployment's own."""
    exact = []
    for home in needles.home_dirs:
        # Some validators scan raw strings; others scan json.dumps output.
        for form in dict.fromkeys((home, json.dumps(home, ensure_ascii=False)[1:-1])):
            # A sentence-final period is a separator; .bak and -other name
            # different directories and must not match an exact home needle.
            exact.append(_HOME_DIR_BOUNDARY + re.escape(form) + r"(?![A-Za-z0-9_-]|\.[A-Za-z0-9_-])")
    return "(?:" + "|".join([GENERIC_HOME_DIR_PATTERN, *exact]) + ")"


def run_user_alias_pattern(needles: Needles) -> str | None:
    """Regex alternation for ``Host <user>`` / ``<user>@`` aliases, if any users are configured."""
    if not needles.run_users:
        return None
    users = "|".join(re.escape(user) for user in needles.run_users)
    return rf"(?:\bHost\s+(?:{users})\b|(?:{users})@)"
