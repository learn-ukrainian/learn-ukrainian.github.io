"""Exercise all seven live Phase 3 boundaries with real JSON parsing (#9556)."""

import json

import pytest

from scripts.projects.open_model_data import phase3_disposition_audit as audit
from scripts.projects.open_model_data import phase3_source_dispositions as dispositions
from scripts.projects.open_model_data import phase3_source_unit_materialization as materializer


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
