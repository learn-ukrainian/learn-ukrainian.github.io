"""Shared filesystem layout for immutable API release snapshots."""

from __future__ import annotations

import re
from pathlib import Path

RELEASE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RELEASES_RELATIVE_PATH = Path(".runtime") / "api" / "releases"
MANIFEST_NAME = ".release-manifest.json"

# ``scripts/`` and ``schemas/`` are immutable code inputs. Everything here is
# intentionally a live-data symlink; add entries only after auditing an API
# path access. ``tests/fixtures`` is nested because tests exercise a release
# directory without making the complete test suite part of each snapshot.
LIVE_DATA_PATHS: tuple[str, ...] = (
    "curriculum",
    "data",
    "audit",
    "batch_state",
    "docs",
    "wiki",
    "logs",
    "site",
    "tests/fixtures",
    "dashboards",
    ".mcp",
    "agents_extensions",
    "plans",
    ".pids",
)


def is_release_root(path: Path) -> bool:
    """Return whether ``path`` has the fixed release-snapshot layout."""
    return (
        RELEASE_SHA_RE.fullmatch(path.name) is not None
        and path.parent.name == "releases"
        and path.parent.parent.name == "api"
        and path.parent.parent.parent.name == ".runtime"
        and not path.is_symlink()
    )
