"""Dependency-light bridge database path resolution."""

import os
from pathlib import Path


def default_bridge_db_path(primary_repo_root: Path) -> Path:
    """Return the bridge DB owned by the primary checkout."""
    return primary_repo_root / ".mcp" / "servers" / "message-broker" / "messages.db"


def configured_bridge_db_path(primary_repo_root: Path) -> Path:
    """Apply the bridge's optional database override to its default path."""
    return Path(os.environ.get("AB_DB_PATH", str(default_bridge_db_path(primary_repo_root))))
