"""Dependency-free validation for launcher epic selectors."""

import re


def validate_epic(epic: str) -> None:
    """Match handoff_identity.sh epic_name_valid: lowercase alnum, inner hyphens."""
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", epic):
        raise ValueError("epic must be a selector such as infra or 7919")
