"""Pending permissions-register rows for #9609 are complete and apply cleanly.

The register file is pinned by the Atlas pilot freeze (#9643), so the rows wait in
registry/projects/open_model_data/register_rows_pending.yaml.  These tests keep them
ready to apply: each added row validates against the register schema, adds a new id,
and each amendment yields a valid row.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[3]
PENDING = REPO_ROOT / "registry" / "projects" / "open_model_data" / "register_rows_pending.yaml"
REGISTER = REPO_ROOT / "docs" / "sources" / "permissions-register.yaml"
SCHEMA = REPO_ROOT / "schemas" / "permissions-register.schema.json"

# The register rows the issue names as missing.
REQUIRED_NEW_IDS = {"zno_nmt", "pravopys_2019", "pohribnyi_1992"}


def _source_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return Draft202012Validator({"$defs": schema["$defs"], **schema["$defs"]["source"]})


def _pending() -> dict[str, Any]:
    return yaml.safe_load(PENDING.read_text(encoding="utf-8"))


def _register_rows() -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in yaml.safe_load(REGISTER.read_text(encoding="utf-8"))["sources"]}


def _apply_amendment(row: dict[str, Any], amendment: dict[str, Any]) -> dict[str, Any]:
    amended = copy.deepcopy(row)
    for operation in ("set", "append"):
        for dotted, value in amendment.get(operation, {}).items():
            *parents, leaf = dotted.split(".")
            target = amended
            for key in parents:
                target = target[key]
            assert leaf in target, f"{amendment['id']}: {dotted} is not an existing field"
            target[leaf] = value if operation == "set" else [*target[leaf], *value]
    return amended


def test_register_rows_cover_the_missing_sources():
    added = {row["id"] for row in _pending()["add"]}
    assert added >= REQUIRED_NEW_IDS


@pytest.mark.parametrize("row", _pending()["add"], ids=lambda row: row["id"])
def test_added_row_validates_and_is_new(row):
    errors = sorted(error.message for error in _source_validator().iter_errors(row))
    assert errors == []
    assert row["id"] not in _register_rows(), f"{row['id']} is already in the register"
    assert row["provenance"]["retrieved_evidence"].strip()


@pytest.mark.parametrize("amendment", _pending()["amend"], ids=lambda amendment: amendment["id"])
def test_amendment_targets_an_existing_row_and_stays_valid(amendment):
    rows = _register_rows()
    assert amendment["id"] in rows
    assert amendment["reason"].strip()
    amended = _apply_amendment(rows[amendment["id"]], amendment)
    assert sorted(error.message for error in _source_validator().iter_errors(amended)) == []


def test_frazeolohichnyi_amendment_carries_the_verified_edition():
    [amendment] = [item for item in _pending()["amend"] if item["id"] == "frazeolohichnyi"]
    assert "ISBN 966-00-0797-3" in amendment["set"]["citation.form"]
    evidence = yaml.safe_load((REPO_ROOT / _pending()["evidence"]["frazeolohichnyi_edition"]).read_text("utf-8"))
    assert evidence["verdict"] == "verified"
    assert evidence["edition"]["isbn"] == "966-00-0797-3"
