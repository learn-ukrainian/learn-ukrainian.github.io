"""Digest exception definition (#8430 WP 15 Part R2a)."""

from __future__ import annotations


class DigestError(Exception):
    """Failure outcome in module digest computation or verification."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
