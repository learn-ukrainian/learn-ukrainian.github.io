"""Host-path guard for anti-leak tests.

Tests check for generic home-directory patterns plus the deployment's own
needles (``scripts/opsec/needles.py``), so no test has to name a real
account or home directory. Reject samples use the fictional values below.
"""

from __future__ import annotations

import re
from functools import lru_cache

from scripts.api.occupancy_sanitize import _CANONICAL_ALIASES
from scripts.opsec.needles import home_dir_pattern, load_needles

# Fictional values for reject samples; only their shape matters.
FIXTURE_USER = "fixture-user"
FIXTURE_HOME = "/".join(("", "home", FIXTURE_USER))

# Host aliases the public occupancy sanitizer already knows; tests reuse that
# list instead of spelling the names again.
HOST_ALIASES: tuple[str, ...] = tuple(sorted(_CANONICAL_ALIASES))

# Generic host facts: non-loopback dotted IPv4 literals, SSH ``HostName``
# lines and install trees under the conventional add-on prefix.
IPV4_LITERAL_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
INSTALL_ROOT_RE = re.compile(r"(?<![\w.-])(?:/opt)/[A-Za-z0-9_][A-Za-z0-9_.-]*")


def host_fact_hits(text: str) -> list[str]:
    """Host aliases, IPv4 literals, ``HostName`` lines and install trees in ``text``."""
    hits = [alias for alias in HOST_ALIASES if alias in text]
    hits += [ip for ip in IPV4_LITERAL_RE.findall(text) if not ip.startswith(("127.", "0."))]
    hits += INSTALL_ROOT_RE.findall(text)
    if re.search(r"\bHostName\b", text):
        hits.append("HostName")
    return hits


def install_root_hits(text: str) -> list[str]:
    """Install trees under the conventional add-on prefix in ``text``."""
    return INSTALL_ROOT_RE.findall(text)


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
