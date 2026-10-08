"""Host-path guard for anti-leak tests.

Tests check for generic home-directory patterns plus the deployment's own
needles (``scripts/opsec/needles.py``), so no test has to name a real
account or home directory. Reject samples use the fictional values below.

Results and failures carry line numbers only, never the matched text: with
a deployment needles file the match is a private value. Use the
``assert_no_*`` helpers instead of ``assert not ...`` so pytest's assertion
rewriting cannot print the scanned text either.
"""

from __future__ import annotations

import re
from functools import lru_cache

from scripts.api.occupancy_sanitize import _CANONICAL_ALIASES
from scripts.opsec.needles import Needles, home_dir_pattern, load_needles

# Fictional values for reject samples; only their shape matters.
FIXTURE_USER = "fixture-user"
FIXTURE_HOME = "/".join(("", "home", FIXTURE_USER))

# Host aliases the public occupancy sanitizer already knows; tests reuse that
# list instead of spelling the names again.
HOST_ALIASES: tuple[str, ...] = tuple(sorted(_CANONICAL_ALIASES))

# A token boundary that also accepts a preceding backslash escape (``\n``,
# ``\x1b``, ``\u001b``), so escaped text (JSON dumps, source literals) cannot
# hide a value that starts a new line or field.
_ESCAPED_BOUNDARY = r"(?<=\\[A-Za-z])|(?<=\\x[0-9A-Fa-f]{2})|(?<=\\u[0-9A-Fa-f]{4})"

# Generic host facts: non-loopback dotted IPv4 literals, SSH ``HostName``
# lines and install trees under the conventional add-on prefix.
IPV4_LITERAL_RE = re.compile(rf"(?:(?<![\w.])|{_ESCAPED_BOUNDARY})(?:\d{{1,3}}\.){{3}}\d{{1,3}}(?![\w.])")
INSTALL_ROOT_RE = re.compile(rf"(?:(?<![\w.-])|{_ESCAPED_BOUNDARY})(?:/opt)/[A-Za-z0-9_][A-Za-z0-9_.-]*")
HOSTNAME_LINE_RE = re.compile(r"\bHostName\b")

HOST_ALIAS = "host alias"
IPV4_LITERAL = "IPv4 literal"
INSTALL_TREE = "install tree"
HOSTNAME_LINE = "HostName line"
HOST_FACT_KINDS = (HOST_ALIAS, IPV4_LITERAL, INSTALL_TREE, HOSTNAME_LINE)


@lru_cache(maxsize=1)
def _deployment_needles() -> Needles:
    return load_needles()


@lru_cache(maxsize=8)
def host_path_re(needles: Needles | None = None) -> re.Pattern[str]:
    """Any home directory, plus the deployment's own home directories."""
    return re.compile(home_dir_pattern(_deployment_needles() if needles is None else needles))


@lru_cache(maxsize=8)
def checkout_path_re(needles: Needles | None = None) -> re.Pattern[str]:
    """A checkout baked under a home directory (``<home>[/projects]/learn-ukrainian``)."""
    pattern = home_dir_pattern(_deployment_needles() if needles is None else needles)
    return re.compile(pattern + r"(?:/projects)?/learn-ukrainian")


@lru_cache(maxsize=8)
def host_template_re(needles: Needles | None = None) -> re.Pattern[str]:
    """A home-directory path template: ``/home/<user>`` or ``<any home>/<placeholder>``."""
    pattern = home_dir_pattern(_deployment_needles() if needles is None else needles)
    return re.compile(rf"(?:{pattern}|(?<![\w.-])(?:/home|/Users))/<")


def _lines(pattern: re.Pattern[str], text: str, home_root: str | None = None) -> list[int]:
    lines = {
        text.count("\n", 0, match.start()) + 1
        for match in pattern.finditer(text)
        if home_root is None or match.group(0).startswith(home_root + "/")
    }
    return sorted(lines)


def host_path_lines(text: str, *, needles: Needles | None = None) -> list[int]:
    """1-based line numbers of home directories in ``text``."""
    return _lines(host_path_re(needles), text)


def checkout_path_lines(text: str, *, home_root: str | None = None, needles: Needles | None = None) -> list[int]:
    """1-based line numbers of baked checkouts, optionally only under ``home_root``."""
    return _lines(checkout_path_re(needles), text, home_root)


def _fail(where: str, kind: str, lines: list[int]) -> None:
    if lines:
        # Raised directly (not via ``assert``) so no rewritten explanation
        # repeats the scanned text or the matches.
        raise AssertionError(f"{where}: {kind} at line(s) {', '.join(map(str, lines))}")


def assert_no_host_paths(text: str, where: str = "text", *, needles: Needles | None = None) -> None:
    _fail(where, "home directory", host_path_lines(text, needles=needles))


def assert_no_checkout_paths(text: str, where: str = "text", *, needles: Needles | None = None) -> None:
    _fail(where, "checkout under a home directory", checkout_path_lines(text, needles=needles))


def host_template_lines(text: str, *, needles: Needles | None = None) -> list[int]:
    """1-based line numbers of home-directory path templates in ``text``."""
    return _lines(host_template_re(needles), text)


def assert_no_host_templates(text: str, where: str = "text", *, needles: Needles | None = None) -> None:
    _fail(where, "home-directory path template", host_template_lines(text, needles=needles))


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def host_fact_lines(text: str, *, kinds: tuple[str, ...] = HOST_FACT_KINDS) -> dict[str, list[int]]:
    """1-based line numbers of host facts in ``text``, per kind; empty kinds are omitted."""
    found: dict[str, set[int]] = {}
    if HOST_ALIAS in kinds:
        for alias in HOST_ALIASES:
            for match in re.finditer(re.escape(alias), text):
                found.setdefault(HOST_ALIAS, set()).add(_line_of(text, match.start()))
    if IPV4_LITERAL in kinds:
        for match in IPV4_LITERAL_RE.finditer(text):
            if not match.group(0).startswith(("127.", "0.")):
                found.setdefault(IPV4_LITERAL, set()).add(_line_of(text, match.start()))
    if INSTALL_TREE in kinds:
        for match in INSTALL_ROOT_RE.finditer(text):
            found.setdefault(INSTALL_TREE, set()).add(_line_of(text, match.start()))
    if HOSTNAME_LINE in kinds:
        for match in HOSTNAME_LINE_RE.finditer(text):
            found.setdefault(HOSTNAME_LINE, set()).add(_line_of(text, match.start()))
    return {kind: sorted(found[kind]) for kind in HOST_FACT_KINDS if kind in found}


def assert_no_host_facts(text: str, where: str = "text", *, kinds: tuple[str, ...] = HOST_FACT_KINDS) -> None:
    found = host_fact_lines(text, kinds=kinds)
    if found:
        detail = "; ".join(f"{kind} at line(s) {', '.join(map(str, lines))}" for kind, lines in found.items())
        # Raised directly so no rewritten explanation repeats the text.
        raise AssertionError(f"{where}: {detail}")
