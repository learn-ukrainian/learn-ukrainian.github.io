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

from scripts.opsec.needles import Needles, home_dir_pattern, load_needles

# Fictional values for reject samples; only their shape matters.
FIXTURE_USER = "fixture-user"
FIXTURE_HOME = "/".join(("", "home", FIXTURE_USER))


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
