"""Small shared helpers for Git subprocesses running under the API service."""

from __future__ import annotations

import os

GIT_REDIRECT_ENV_KEYS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_PREFIX",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
)


def sanitized_git_env() -> dict[str, str]:
    """Return an environment that lets ``git -C`` select only its explicit root."""
    return {key: value for key, value in os.environ.items() if key not in GIT_REDIRECT_ENV_KEYS}
