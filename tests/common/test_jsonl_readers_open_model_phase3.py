"""Exercise all seven live Phase 3 boundaries with real JSON parsing (#9556)."""

import json
from types import SimpleNamespace

import pytest

from scripts.projects.open_model_data import phase3_disposition_audit as audit
from scripts.projects.open_model_data import phase3_heldout_partition as heldout
from scripts.projects.open_model_data import phase3_pravopys_delta as pravopys
from scripts.projects.open_model_data import phase3_source_dispositions as dispositions
from scripts.projects.open_model_data import phase3_source_production_transport as transport
from scripts.projects.open_model_data import phase3_source_unit_materialization as materializer

SITES = ["audit", "heldout_snapshot", "heldout_file", "pravopys", "dispositions", "transport", "materializer"]


@pytest.mark.parametrize("site", SITES)
@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"], ids=["NEL", "LS", "PS"])
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_live_phase3_reader_preserves_unicode_separator(site, separator, ending, tmp_path, monkeypatch):
    value = f"before{separator}after"
    rows = [
        {
            "family_id": "ua_gec",
            "ordinal": ordinal,
            "unit_id": f"unit.{ordinal}",
            "unit_sha256": "a" * 64,
            "locator": {"probe": value},
            "probe": value,
        }
        for ordinal in (1, 2)
    ]
    text = (ending or "\n").join(json.dumps(row, ensure_ascii=False) for row in rows) + ending
    path = tmp_path / "ua_gec.units.jsonl"
    path.write_bytes(text.encode("utf-8"))

    if site == "audit":
        receipt = {"families": [{"family_id": "ua_gec", "ledger_file": path.name, "unit_count": 2}]}
        (tmp_path / audit.source_freeze.RECEIPT_FILE).write_text(json.dumps(receipt))
        # Only the upstream freeze verifier is isolated; the reader, parser,
        # count checks, and locator hashing all run to completion.
        monkeypatch.setattr(audit.source_freeze, "validate", lambda *a, **kw: None)
        actual_receipt, _, records = audit._source_receipt(tmp_path)
        assert actual_receipt == receipt
        assert records["ua_gec"] == [
            {
                "unit_id": row["unit_id"],
                "unit_sha256": row["unit_sha256"],
                "unit_locator_sha256": audit.sha256_value(row["locator"]),
            }
            for row in rows
        ]
    elif site.startswith("heldout"):
        if site == "heldout_snapshot":
            member = "projects/open_model_data/evidence/source_universe_v1/ua_gec.units.jsonl"
            monkeypatch.setattr(heldout, "DEFAULT_SOURCE_UNIVERSE", tmp_path)
            monkeypatch.setattr(
                heldout, "artifact_set", lambda *a, **kw: SimpleNamespace(artifacts={member: text.encode("utf-8")})
            )
        assert heldout._load_freeze_ua_gec_units(tmp_path) == rows
    elif site == "pravopys":
        assert pravopys._read_jsonl(path) == rows
    elif site == "dispositions":
        assert dispositions._ledger_records(path, "ua_gec") == [
            {
                "unit_id": row["unit_id"],
                "unit_sha256": row["unit_sha256"],
                "locator_sha256": dispositions.sha256_bytes(
                    dispositions.canonical_json(row["locator"]).encode("utf-8")
                ),
            }
            for row in rows
        ]
    elif site == "transport":
        body = json.dumps({"probe": value}, ensure_ascii=False)
        newline = ending or "\n"
        raw = f"```json{newline}{body}{newline}```{ending}".encode()
        assert transport._strict_response(raw, "fixture") == {"probe": value}
    else:
        assert materializer._read_ledger(path, "ua_gec") == rows


@pytest.mark.parametrize("site", ["audit", "dispositions", "materializer"])
def test_strict_ledgers_still_reject_an_extra_blank_record(site, tmp_path, monkeypatch):
    path = tmp_path / "ua_gec.units.jsonl"
    path.write_text(json.dumps({"family_id": "ua_gec", "ordinal": 1}) + "\n\n")
    if site == "audit":
        receipt = {"families": [{"family_id": "ua_gec", "ledger_file": path.name, "unit_count": 1}]}
        (tmp_path / audit.source_freeze.RECEIPT_FILE).write_text(json.dumps(receipt))
        monkeypatch.setattr(audit.source_freeze, "validate", lambda *a, **kw: None)
        # Supply the binding fields so the second, blank record is the failure.
        path.write_text(json.dumps({"unit_id": "unit.1", "unit_sha256": "a" * 64, "locator": {}}) + "\n\n")
        with pytest.raises(json.JSONDecodeError):
            audit._source_receipt(tmp_path)
    elif site == "dispositions":
        path.write_text(
            json.dumps({"family_id": "ua_gec", "unit_id": "unit.1", "unit_sha256": "a" * 64, "locator": {}}) + "\n\n"
        )
        with pytest.raises(dispositions.DispositionError, match=":2"):
            dispositions._ledger_records(path, "ua_gec")
    else:
        with pytest.raises(materializer.MaterializationError, match="cannot read frozen"):
            materializer._read_ledger(path, "ua_gec")
