#!/usr/bin/env python3
"""Public synthetic proofs for Cycle 007's fail-closed selector transport."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ADJ_PATH = HERE / "phase3-run-cycle007-dual-label-adjudication-v1.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adj_mod = _load_module(ADJ_PATH, "cycle007_adjudication_target")


FAKE_SELECTOR = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

counter_name = os.environ.get("CYCLE007_CALLS")
if counter_name:
    counter = Path(counter_name)
    calls = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(calls + 1), encoding="utf-8")
mode = os.environ.get("CYCLE007_MODE", "gemini")
if mode == "transport":
    raise SystemExit(17)
if mode == "structural":
    print("not valid stream json")
    raise SystemExit(0)
envelope = json.loads(sys.stdin.buffer.read())
text = envelope["message"]["content"][0]["text"]
records = json.loads(text.split("--- BEGIN IMMUTABLE DISAGREEMENT RECORDS JSON ---\n", 1)[1].split("--- END IMMUTABLE", 1)[0])["records"]
selection = "third" if mode == "third" else ("unresolved" if mode == "unresolved" else ("grok" if mode == "grok" else "gemini"))
selections = [{"unit_id": record["source_row"]["unit_id"], "unit_sha256": record["source_row"]["unit_sha256"], "selection": selection} for record in records]
if mode == "reordered":
    selections.reverse()
print(json.dumps({"event": "init", "init": {"model": "Claude Sonnet 4.6 (Thinking)"}}))
print(json.dumps({"event": "result", "result": {"status": "SUCCESS", "structured_output": {"selections": selections}}}))
'''


def _write(path: Path, value: object, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(mode)


def _setup_package(tmp_path: Path) -> tuple[Path, list[dict[str, object]]]:
    package = tmp_path / "package"
    package.mkdir(parents=True, mode=0o700)
    _write(package / "custody-receipt.json", {"synthetic": "custody"})
    _write(package / "manifest.json", {"synthetic": "manifest"})
    records: list[dict[str, object]] = []
    for number, choice in (("u-1", "first"), ("u-2", "second")):
        identity = str(len(records) + 1) * 64
        records.append(
            {
                "source_row": {"unit_id": number, "unit_sha256": identity, "synthetic_evidence": "PRIVATE_TEXT_DO_NOT_RECEIPT"},
                "grok_label": {"unit_id": number, "unit_sha256": identity, "decision_code": f"grok-{choice}", "private": "PRIVATE_TEXT_DO_NOT_RECEIPT"},
                "gemini_label": {"unit_id": number, "unit_sha256": identity, "decision_code": f"gemini-{choice}", "private": "PRIVATE_TEXT_DO_NOT_RECEIPT"},
            }
        )
    _write(package / adj_mod.COMPARE_OUTPUT / "clean_label" / "disagreements-0001.json", {"records": records})
    return package, records


def _fake_selector(tmp_path: Path) -> Path:
    selector = tmp_path / "synthetic-selector.py"
    selector.write_text(FAKE_SELECTOR, encoding="utf-8")
    selector.chmod(0o700)
    return selector


def _run_synthetic(package: Path, selector: Path) -> dict[str, object]:
    return adj_mod.adjudicate_packet(package, "clean_label", 1, provider=selector, synthetic_provider=True)


def test_real_default_has_no_candidate_fallback(tmp_path: Path) -> None:
    package, _ = _setup_package(tmp_path)

    with pytest.raises(adj_mod.Error) as exc:
        adj_mod.adjudicate_packet(package, "clean_label", 1)

    assert exc.value.failure_code == "binding_failure"
    assert not (package / adj_mod.OUTPUT / "final").exists()


def test_transport_selects_only_returned_candidate_and_receipt_is_text_free(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package, records = _setup_package(tmp_path)
    selector = _fake_selector(tmp_path)
    monkeypatch.setenv("CYCLE007_MODE", "gemini")

    receipt = _run_synthetic(package, selector)

    assert receipt["adjudicated_count"] == 2
    labels = json.loads((package / adj_mod.OUTPUT / "final/clean_label/labels-0001.json").read_text())
    assert labels["labels"] == [record["gemini_label"] for record in records]
    assert receipt["adjudicator"] == {"exact_model": adj_mod.MODEL, "model_family": "anthropic", "harness": "agy"}
    serialized_receipt = (package / adj_mod.OUTPUT / "final/clean_label/receipt-0001.json").read_text()
    assert "PRIVATE_TEXT_DO_NOT_RECEIPT" not in serialized_receipt
    assert adj_mod.verify_packet(package, "clean_label", 1)["ok"] is True


def test_rejects_third_label_and_order_drift_without_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selector = _fake_selector(tmp_path)
    for mode, expected in (("third", "third_label_invented_drift"), ("reordered", "ordinal_identity_binding_drift")):
        package, _ = _setup_package(tmp_path / mode)
        monkeypatch.setenv("CYCLE007_MODE", mode)
        with pytest.raises(adj_mod.Error) as exc:
            _run_synthetic(package, selector)
        assert exc.value.failure_code == expected
        assert not (package / adj_mod.OUTPUT / "final").exists()


def test_structural_retry_is_bounded_at_two_attempts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package, _ = _setup_package(tmp_path)
    selector = _fake_selector(tmp_path)
    calls = tmp_path / "calls"
    monkeypatch.setenv("CYCLE007_MODE", "structural")
    monkeypatch.setenv("CYCLE007_CALLS", str(calls))

    with pytest.raises(adj_mod.Error) as exc:
        _run_synthetic(package, selector)

    assert exc.value.failure_code == "stream_json_invalid"
    assert calls.read_text() == "2"
    stop = json.loads((package / adj_mod.OUTPUT / "provider-stop.json").read_text())
    assert stop["new_provider_calls_allowed"] is False and stop["text_free"] is True


def test_transport_failure_is_terminal_and_not_retried(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package, _ = _setup_package(tmp_path)
    selector = _fake_selector(tmp_path)
    calls = tmp_path / "calls"
    monkeypatch.setenv("CYCLE007_MODE", "transport")
    monkeypatch.setenv("CYCLE007_CALLS", str(calls))

    with pytest.raises(adj_mod.Error) as exc:
        _run_synthetic(package, selector)

    assert exc.value.failure_code == "provider_transport_failure"
    assert calls.read_text() == "1"
    with pytest.raises(adj_mod.Error):
        _run_synthetic(package, selector)
    assert calls.read_text() == "1"


def test_synthetic_override_requires_explicit_fixture_mode(tmp_path: Path) -> None:
    package, records = _setup_package(tmp_path)
    override = {"selections": [{"unit_id": record["source_row"]["unit_id"], "unit_sha256": record["source_row"]["unit_sha256"], "selection": "grok"} for record in records]}

    with pytest.raises(adj_mod.Error) as exc:
        adj_mod.adjudicate_packet(package, "clean_label", 1, selections_override=override)
    assert exc.value.failure_code == "mode_drift"

    receipt = adj_mod.adjudicate_packet(package, "clean_label", 1, selections_override=override, synthetic_provider=True)
    assert receipt["attempt_count"] == 0


def test_all_resume_preserves_private_unresolved_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package, _ = _setup_package(tmp_path)
    selector = _fake_selector(tmp_path)
    monkeypatch.setattr(adj_mod, "LANES", {"clean_label": 1})
    monkeypatch.setenv("CYCLE007_MODE", "unresolved")

    _run_synthetic(package, selector)
    batch = adj_mod.adjudicate_all(package, provider=selector, synthetic_provider=True)

    assert batch["packet_count"] == 1 and batch["total_unresolved"] == 2 and batch["text_free"] is True
    request = json.loads((package / adj_mod.OUTPUT / "operator-resolution-request.json").read_text())
    assert request["text_free"] is False and request["unresolved_count"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
