"""Applied #9609 register rows and RB-1 attribution contracts."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def rows():
    return {
        row["id"]: row
        for row in yaml.safe_load((ROOT / "docs/sources/permissions-register.yaml").read_text())["sources"]
    }


def test_all_pending_rows_are_applied():
    register = rows()
    assert {"zno_nmt", "pravopys_2019", "pohribnyi_1992", "textbooks_university"} <= register.keys()
    assert not (ROOT / "registry/projects/open_model_data/register_rows_pending.yaml").exists()


def test_phraseology_edition_is_applied_and_twin_is_current():
    row = rows()["frazeolohichnyi"]
    evidence = yaml.safe_load(
        (ROOT / "registry/projects/open_model_data/sources/frazeolohichnyi_edition.yaml").read_text()
    )
    assert evidence["verdict"] == "verified" and evidence["edition"]["volumes"] == 1
    assert evidence["edition"]["isbn"] in row["citation"]["form"]
    assert row["open_questions"] == []
