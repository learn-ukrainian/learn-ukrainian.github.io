"""Per-attempt receipt ledger for sources calls made during a review.

The sources MCP server imports this package only while review recording is
on. Nothing here opens a network connection.
"""

from .ledger import (
    ENV_KEYS,
    REVIEW_TOOLS,
    LedgerError,
    LedgerHashStaleLastLine,
    ReceiptNotFound,
    ReviewSession,
    append,
    collect_snapshots,
    create_empty_ledger,
    lookup,
    records,
    session_from_environ,
)
from .outcomes import classify_outcome

__all__ = [
    "ENV_KEYS",
    "REVIEW_TOOLS",
    "LedgerError",
    "LedgerHashStaleLastLine",
    "ReceiptNotFound",
    "ReviewSession",
    "append",
    "classify_outcome",
    "collect_snapshots",
    "create_empty_ledger",
    "lookup",
    "records",
    "session_from_environ",
]
