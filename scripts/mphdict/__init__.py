"""Read-only queries for the local mphdict ODbL dictionary databases.

The databases are deliberately not vendored: local development and production
hydrate them under ``data/mphdict/``.  The public functions resolve a worktree
to its main checkout's shared data directory when necessary and never modify a
source database.
"""

from .query import (
    decode_stress,
    mphdict_etymology,
    mphdict_headword,
    mphdict_synonyms,
    mphdict_synonyms_available,
    normalize_gloss,
    normalize_lookup,
)

__all__ = [
    "decode_stress",
    "mphdict_etymology",
    "mphdict_headword",
    "mphdict_synonyms",
    "mphdict_synonyms_available",
    "normalize_gloss",
    "normalize_lookup",
]
