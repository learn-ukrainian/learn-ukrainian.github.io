"""Host-path and host-fact guards for anti-leak tests.

Tests check for generic home-directory patterns plus the deployment's own
needles (``scripts/opsec/needles.py``), so no test has to name a real
account or home directory. Reject samples use the fictional values below.

Results and failures carry kinds and line numbers only, never matched text: with
a deployment needles file the match is a private value. Use the
``assert_no_*`` helpers instead of ``assert not ...`` so pytest's assertion
rewriting cannot print the scanned text either.
"""

from __future__ import annotations

import re
from functools import lru_cache
from ipaddress import AddressValueError, IPv4Address

from scripts.api.occupancy_sanitize import _CANONICAL_ALIASES
from scripts.opsec.needles import Needles, home_dir_pattern, load_needles

# Fictional values for reject samples; only their shape matters.
FIXTURE_USER = "fixture-user"
FIXTURE_HOME = "/".join(("", "home", FIXTURE_USER))
HOST_ALIASES = _CANONICAL_ALIASES
_ALIASES = "|".join(re.escape(alias) for alias in sorted(HOST_ALIASES))
_HOST_ALIAS = re.compile(rf"(?:{_ALIASES})")
_IPV4 = re.compile(r"(?<![\w.])\d{1,3}(?:\.\d{1,3}){3}(?!\w|\.\d)")
_SSH_HOSTNAME = re.compile(r"^[ \t]*HostName(?:[ \t]+|=)", re.MULTILINE | re.IGNORECASE)
_ADDON_TREE = re.compile(rf"/opt/(?:{_ALIASES})(?=$|[^\w.-])")


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


def host_fact_lines(text: str) -> dict[str, list[int]]:
    """Host facts by kind and 1-based line number, without matched values.

    Aliases come from the occupancy sanitizer. IPv4 literals are validated
    before rejecting addresses outside the loopback range. Add-on trees are
    known aliases installed under ``/opt``; SSH directives are line-anchored.
    Empty kinds are omitted and multiple matches on one line are deduplicated.
    """
    ipv4_lines = set()
    for match in _IPV4.finditer(text):
        try:
            address = IPv4Address(match.group(0))
        except AddressValueError:
            continue
        if not address.is_loopback:
            ipv4_lines.add(text.count("\n", 0, match.start()) + 1)
    findings = {
        "host alias": _lines(_HOST_ALIAS, text),
        "non-loopback IPv4": sorted(ipv4_lines),
        "SSH HostName": _lines(_SSH_HOSTNAME, text),
        "add-on install tree": _lines(_ADDON_TREE, text),
    }
    return {kind: lines for kind, lines in findings.items() if lines}


def assert_no_host_facts(text: str, where: str = "text") -> None:
    """Reject host facts with diagnostics containing only kinds and line numbers."""
    findings = host_fact_lines(text)
    if findings:
        details = "; ".join(f"{kind} at line(s) {', '.join(map(str, lines))}" for kind, lines in findings.items())
        raise AssertionError(f"{where}: {details}")
