"""Chunked lexicon enrichment runner (#5230).

PR1: bounded lookup rewrite, sealed CEFR/relations, streaming I/O, hard caps.
PR2: real-unit ledger, fencing/CAS, resume, attempt caps, operator retry.
PR3 network cache/packets and PR4 streaming assembly remain stubs.
"""

from __future__ import annotations

from scripts.lexicon.runner.contracts import ENGINE_VERSION, SERIALIZATION_VERSION
from scripts.lexicon.runner.ledger import Ledger, compute_run_fingerprint
from scripts.lexicon.runner.offline_engine import enrich_offline_slice

__all__ = [
    "ENGINE_VERSION",
    "SERIALIZATION_VERSION",
    "Ledger",
    "compute_run_fingerprint",
    "enrich_offline_slice",
]
