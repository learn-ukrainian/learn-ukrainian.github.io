"""Machinery configuration for the Monitor API: roots, stores and the product entry.

Curriculum configuration (levels, seminar tracks, textbook roots) is product
code in ``scripts.project_api.config`` (Monitor split, C-4687).
"""

import os
from pathlib import Path

from scripts.common.bridge_paths import configured_bridge_db_path
from scripts.common.repo_root import product_root

# Project root is the immutable code snapshot when the API is release-served.
# Mutable data remains reachable through the release's explicit symlinks.
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _live_repo_root() -> Path:
    """Return the checkout Git operations and child tools must target."""
    configured = os.environ.get("LEARN_UK_REPO_ROOT")
    if not configured:
        return PROJECT_ROOT
    supplied = Path(configured).expanduser()
    if not supplied.is_absolute():
        raise RuntimeError("LEARN_UK_REPO_ROOT must be an absolute path")
    candidate = supplied.resolve()
    if not candidate.is_dir() or not (candidate / ".git").exists():
        raise RuntimeError(f"LEARN_UK_REPO_ROOT is not a Git checkout: {candidate}")
    return candidate


LIVE_REPO_ROOT = _live_repo_root()

# Curriculum paths
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# Message broker database
MESSAGE_DB = configured_bridge_db_path(PROJECT_ROOT)

# Dashboards directory (for static file serving)
DASHBOARDS_DIR = PROJECT_ROOT / "dashboards"


def __getattr__(name: str) -> Path:
    """``PRODUCT_ROOT``, selected once, when the application first asks for it (C-4746).

    Product root (C-4687): the checkout whose configured product entry supplies the
    product half of the API. It is ``repo_root.product_root()``'s choice, made at
    startup rather than at import, so importing this module never needs a product.
    Served from a release snapshot, that is the snapshot itself (its ``curriculum``
    live-data link carries the product marker); it is never the live checkout
    (``LIVE_REPO_ROOT``), which owns no snapshot code. Outside a product checkout the
    startup names the product with ``LU_PRODUCT_ROOT``, or the first use refuses.
    """
    if name != "PRODUCT_ROOT":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    selected = product_root()
    globals()["PRODUCT_ROOT"] = selected
    return selected


# Batch state directory
BATCH_STATE_DIR = Path(os.environ.get("LEARN_UKRAINIAN_BATCH_STATE_DIR", PROJECT_ROOT / "batch_state"))

# Server settings
API_HOST = "127.0.0.1"  # nosec B104 — bind to localhost only
API_PORT = 8765
