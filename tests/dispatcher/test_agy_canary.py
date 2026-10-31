"""The fixed store-read canary returns typed, path-free results and rejects unknown operations."""

from dataclasses import asdict

from scripts.dispatcher.agy_canary import StoreReadResult, _attempt, _read_store
from scripts.dispatcher.agy_sandbox import _probe_passed
from scripts.storage import topology


def test_store_read_refusal_never_echoes_input_path(tmp_path, monkeypatch):
    monkeypatch.setattr(topology, "resolve_store", lambda *args, **kwargs: topology.StoreRefusal("sources", "locality_network"))
    result = _read_store("sources", str(tmp_path / "private"))
    assert result == StoreReadResult("refused", "sources", "locality_network")
    assert str(tmp_path) not in repr(result)
    assert _attempt("execute", "private code", None) == "UNKNOWN_OP"


def test_typed_read_refusal_is_accepted_only_when_explicitly_planned():
    refusal = asdict(StoreReadResult("refused", "sources", "wal_sidecars_unavailable"))
    read = asdict(StoreReadResult("read", "sources"))
    assert not _probe_passed({"op": "store_read", "expect": [read], "outcome": refusal})
    assert _probe_passed({"op": "store_read", "expect": [read, refusal], "outcome": refusal})
    assert not _probe_passed({"op": "store_read", "expect": [read, refusal],
                              "outcome": asdict(StoreReadResult("refused", "sources", "store_unavailable"))})
