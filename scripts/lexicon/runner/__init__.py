"""Chunked lexicon enrichment runner (#5230 PR1 — engine isolation).

PR1 ships the bounded lookup rewrite, sealed CEFR/relations phases, streaming
I/O, and hard-capped worker subprocesses. Ledger/leases (PR2), network
cache/packets (PR3), and sealing/assembly (PR4) are typed stubs only.
"""

from __future__ import annotations

from scripts.lexicon.runner.contracts import ENGINE_VERSION, SERIALIZATION_VERSION
from scripts.lexicon.runner.offline_engine import enrich_offline_slice

__all__ = [
    "ENGINE_VERSION",
    "SERIALIZATION_VERSION",
    "enrich_offline_slice",
]
