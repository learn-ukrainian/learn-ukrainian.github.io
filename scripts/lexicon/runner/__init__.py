"""Chunked lexicon enrichment runner (#5230).

PR1: bounded lookup rewrite, sealed CEFR/relations, streaming I/O, hard caps.
PR2: real-unit ledger, fencing/CAS, resume, attempt caps, operator retry.
PR3: disconnected network cache, packets/bundles, fenced import.
PR4: leaf sealing handoff, streaming finalization, publication gate.
Offline reduce: consume ULIF network-cache raw envelopes → structured candidate.
"""

from __future__ import annotations

from scripts.lexicon.runner.contracts import ENGINE_VERSION, SERIALIZATION_VERSION
from scripts.lexicon.runner.finalize import finalize_run
from scripts.lexicon.runner.ledger import Ledger, compute_run_fingerprint
from scripts.lexicon.runner.network_cache import NetworkCache, compute_request_key
from scripts.lexicon.runner.offline_engine import enrich_offline_slice
from scripts.lexicon.runner.offline_reduce import reduce_offline_slice
from scripts.lexicon.runner.ulif_dictua_parse import parse_dictua_envelope

__all__ = [
    "ENGINE_VERSION",
    "SERIALIZATION_VERSION",
    "Ledger",
    "NetworkCache",
    "compute_request_key",
    "compute_run_fingerprint",
    "enrich_offline_slice",
    "finalize_run",
    "parse_dictua_envelope",
    "reduce_offline_slice",
]
