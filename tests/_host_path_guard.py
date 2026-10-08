"""Host-path guard for anti-leak tests.

Tests check for generic home-directory patterns plus the deployment's own
needles (``scripts/opsec/needles.py``), so no test has to name a real
account or home directory. Reject samples use the fictional values below.
"""

from __future__ import annotations

import re
from functools import lru_cache

from scripts.opsec.needles import home_dir_pattern, load_needles

# Fictional values for reject samples; only their shape matters.
FIXTURE_USER = "fixture-user"
FIXTURE_HOME = "/".join(("", "home", FIXTURE_USER))


@lru_cache(maxsize=1)
def host_path_re() -> re.Pattern[str]:
    """Any home directory, plus the deployment's own home directories."""
    return re.compile(home_dir_pattern(load_needles()))


@lru_cache(maxsize=1)
def checkout_path_re() -> re.Pattern[str]:
    """A checkout baked under a home directory (``<home>[/projects]/learn-ukrainian``)."""
    return re.compile(home_dir_pattern(load_needles()) + r"(?:/projects)?/learn-ukrainian")


def host_path_hits(text: str) -> list[str]:
    return [match.group(0) for match in host_path_re().finditer(text)]


def checkout_path_hits(text: str) -> list[str]:
    return [match.group(0) for match in checkout_path_re().finditer(text)]
