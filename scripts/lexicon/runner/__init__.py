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

from types import ModuleType
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


def _submodule(name: str) -> ModuleType:
    # Static imports only: the SQLite boundary lint refuses an import whose
    # module name is computed (scripts/hygiene/lint_source_db_writable_connects.py).
    match name:
        case "contracts":
            from scripts.lexicon.runner import contracts

            return contracts
        case "finalize":
            from scripts.lexicon.runner import finalize

            return finalize
        case "ledger":
            from scripts.lexicon.runner import ledger

            return ledger
        case "network_cache":
            from scripts.lexicon.runner import network_cache

            return network_cache
        case "offline_engine":
            from scripts.lexicon.runner import offline_engine

            return offline_engine
        case "offline_reduce":
            from scripts.lexicon.runner import offline_reduce

            return offline_reduce
        case "ulif_dictua_parse":
            from scripts.lexicon.runner import ulif_dictua_parse

            return ulif_dictua_parse
    raise AssertionError(name)


def __getattr__(name: str) -> Any:
    submodule = _EXPORTS.get(name)
    if submodule is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(_submodule(submodule), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
