import json
from pathlib import Path

from scripts.audit.resolve_fixture_rights import load_replace_list


def test_all_fixture_evidence_has_rights_matrix_row():
    # Load the matrix
    matrix_path = Path("tests/fixtures/qg_bakeoff_rights/rights.json")
    assert matrix_path.exists(), "rights.json must exist"

    with open(matrix_path, encoding="utf-8") as f:
        rights_data = json.load(f)

    replace_list_path = Path("docs/projects/ua-eval-harness/fixture-rights-replace-list.md")
    replace_keys = set(load_replace_list(replace_list_path))

    valid_classifications = {"POINTER", "QUOTED_TEXT"}
    valid_verdicts = {"SHIP", "POINTER_ONLY", "REPLACE", "UNKNOWN"}

    matrix_keys = set()
    verdict_counts = {}
    for row in rights_data:
        matrix_keys.add((row["fixture"], row["claim_id"], row["quote_or_ref"]))
        verdict_counts[row["verdict"]] = verdict_counts.get(row["verdict"], 0) + 1
        assert row.get("classification") in valid_classifications, (
            f"Row missing or invalid classification: {row}"
        )
        assert row.get("verdict") in valid_verdicts, f"Row has invalid verdict: {row}"

        if row["classification"] == "QUOTED_TEXT":
            assert row["verdict"] in {"REPLACE", "UNKNOWN"} or (
                row.get("matched_table") and row.get("chunk_id")
            ), (
                f"QUOTED_TEXT rows require matched_table+chunk_id unless verdict is REPLACE/UNKNOWN: {row}"
            )
            if row["verdict"] == "UNKNOWN":
                assert row.get("license") == "UNKNOWN", f"UNKNOWN quoted rows must not claim a license: {row}"

        if row["classification"] == "POINTER":
            assert row.get("verdict") == "SHIP", f"Pointer rows should auto-ship: {row}"
            assert row.get("license") == "N/A", f"Pointer rows should not claim a source license: {row}"

        if row["verdict"] == "REPLACE":
            assert (row["fixture"], row["claim_id"]) in replace_keys, (
                f"REPLACE row must be listed in fixture-rights-replace-list.md: {row}"
            )

        if str(row.get("license", "")).startswith("CC-BY-SA"):
            evidence = row.get("evidence", {})
            assert row.get("source_file"), f"CC rows must preserve source attribution: {row}"
            assert evidence.get("license_basis_url"), f"CC rows must preserve license URL: {row}"

    assert verdict_counts.get("UNKNOWN", 0) == 0, "Committed rights matrix must not contain UNKNOWN rows"
    for fixture, claim_id in replace_keys:
        assert any(
            row["fixture"] == fixture and row["claim_id"] == claim_id and row["verdict"] == "REPLACE"
            for row in rights_data
        ), f"Replace-list row missing from rights.json: {(fixture, claim_id)}"

    # Extract dynamically from fixtures
    found_keys = set()
    fixture_dir = Path("tests/fixtures/qg_bakeoff")
    for fpath in fixture_dir.glob("*.json"):
        slug = fpath.stem
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

            vlog = data.get("verification_log", "")
            if vlog:
                found_keys.add((slug, "root_vlog", vlog))

            for claim in data.get("claims", []):
                cid = claim.get("claim_id")
                de = claim.get("distractor_evidence")
                vb = claim.get("verified_by")

                if de:
                    found_keys.add((slug, f"{cid}_distractor", de))
                if vb:
                    found_keys.add((slug, f"{cid}_verified", vb))

    # Assert
    missing_in_matrix = found_keys - matrix_keys
    assert not missing_in_matrix, (
        f"Found {len(missing_in_matrix)} evidence items in fixtures that are not in rights.json: {missing_in_matrix}"
    )

    extra_in_matrix = matrix_keys - found_keys
    assert not extra_in_matrix, (
        f"Found {len(extra_in_matrix)} evidence items in rights.json that are no longer in fixtures: {extra_in_matrix}"
    )
