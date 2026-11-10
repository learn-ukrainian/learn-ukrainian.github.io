"""Chunked lexicon enrichment runner (#5230).

PR1: bounded lookup rewrite, sealed CEFR/relations, streaming I/O, hard caps.
PR2: real-unit ledger, fencing/CAS, resume, attempt caps, operator retry.
PR3: disconnected network cache, packets/bundles, fenced import.
PR4: leaf sealing handoff, streaming finalization, publication gate.
Offline reduce: consume ULIF network-cache raw envelopes → structured candidate.

The package-level names below load their submodule on first use (PEP 562), so
importing one submodule, such as ``atlas_job`` for the Monitor, does not import
the corpus writers.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scripts.lexicon.runner.contracts import ENGINE_VERSION, SERIALIZATION_VERSION
    from scripts.lexicon.runner.finalize import finalize_run
    from scripts.lexicon.runner.ledger import Ledger, compute_run_fingerprint
    from scripts.lexicon.runner.network_cache import NetworkCache, compute_request_key
    from scripts.lexicon.runner.offline_engine import enrich_offline_slice
    from scripts.lexicon.runner.offline_reduce import reduce_offline_slice
    from scripts.lexicon.runner.ulif_dictua_parse import parse_dictua_envelope

_EXPORTS = {
    "ENGINE_VERSION": "contracts",
    "SERIALIZATION_VERSION": "contracts",
    "Ledger": "ledger",
    "NetworkCache": "network_cache",
    "compute_request_key": "network_cache",
    "compute_run_fingerprint": "ledger",
    "enrich_offline_slice": "offline_engine",
    "finalize_run": "finalize",
    "parse_dictua_envelope": "ulif_dictua_parse",
    "reduce_offline_slice": "offline_reduce",
}

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


def __getattr__(name: str) -> Any:
    submodule = _EXPORTS.get(name)
    if submodule is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(f"{__name__}.{submodule}"), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
