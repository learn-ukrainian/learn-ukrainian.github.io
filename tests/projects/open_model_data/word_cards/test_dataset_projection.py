"""Version and certification labels over synthetic cards, never language proof."""

import copy
import json

import pytest

from scripts.atlas import word_card_certification as certification
from scripts.projects.open_model_data.word_cards import dataset_projection as projection
from tests.projects.open_model_data import test_word_card_dataset_release as release_fixtures
from tests.word_card_certification_fixtures import certification_fixture  # noqa: F401

release_input = release_fixtures.release_input
synthetic_mount = release_fixtures.synthetic_mount


@pytest.mark.parametrize("format", ["json", "jsonl"])
@pytest.mark.parametrize("certified", [False, True])
def test_row_contract_and_counts(release_input, format, certified):
    card = release_input.card
    if not certified:
        card["card_version"] = "0.1.0"
        card["known_gaps"] = ["Independent linguistic review pending"]
    original = copy.deepcopy(card)
    result = projection.create_release(
        [card], release_version="v0.1.0", format=format, allow_candidates=True,
    )
    rows = json.loads(result.dataset) if format == "json" else [json.loads(result.dataset)]
    assert len(rows) == 1
    row = rows[0]
    assert {key: value for key, value in row.items() if key != "fields"} == {
        "card_id": "wc_0123456789ab", "card_kind": "lexeme",
        "card_version": card["build"]["card_version"] if certified else "0.1.0",
        "status": "CERTIFIED" if certified else "CANDIDATE",
        "known_gaps": [] if certified else ["Independent linguistic review pending"],
    }
    assert [(f["field"], f["value"], f["citation"]["source_id"]) for f in row["fields"]] == [
        ("spelling", "fixture-head", "vesum"),
        ("definition_uk", "permitted-definition", "ulif"),
    ]
    assert (result.manifest["card_count"], result.manifest["certified_count"],
            result.manifest["candidate_count"]) == ((1, 1, 0) if certified else (1, 0, 1))
    assert card == original
    assert result == projection.create_release(
        [card], release_version="v0.1.0", format=format, allow_candidates=True,
    )


@pytest.mark.parametrize("fault", ["missing", "withdrawn", "modified", "site_only"])
def test_failed_certification_never_becomes_certified(release_input, fault):
    if fault == "missing":
        release_input.ledger["approved_reviews"] = []
    elif fault == "withdrawn":
        release_input.ledger["approved_reviews"][0]["status"] = "withdrawn"
    elif fault == "site_only":
        release_input.ledger["approved_reviews"][0]["approved_for"] = ["site"]
    else:
        release_input.card["assertions"][0]["value"] = "Changed synthetic value"
    release_input.ledger_path.write_text(json.dumps(release_input.ledger))
    result = projection.create_release(
        [release_input.card], release_version="v0.1.0", allow_candidates=True,
    )
    row = json.loads(result.dataset)
    assert (row["status"], row["known_gaps"], row["card_version"]) == (
        "CANDIDATE", [], release_input.card["build"]["card_version"],
    )
    with pytest.raises(certification.UncertifiedCardRefusal):
        projection.create_release([release_input.card], release_version="v0.1.0")


@pytest.mark.parametrize("fault", ["assertion", "extra", "gaps", "version", "state"])
def test_candidate_schema_validation(release_input, fault):
    card = release_input.card
    if fault == "assertion":
        del card["assertions"][0]["producer"]
    elif fault == "extra":
        card["uncited_definition"] = "Unvalidated payload"
    elif fault == "gaps":
        card["known_gaps"] = "Not an array"
    elif fault == "version":
        card["card_version"] = 1
    else:
        card["state"] = "suppressed"
    with pytest.raises(projection.ProjectionRefusal):
        projection.create_release([card], release_version="v0.1.0", allow_candidates=True)


@pytest.mark.parametrize("fault", ["citation", "register"])
def test_candidate_permission_bindings(release_input, fault, tmp_path):
    card = release_input.card
    card["known_gaps"] = ["Pending review"]
    register = release_input.register
    if fault == "citation":
        card["assertions"][0]["licence_ref"]["register_source_id"] = "wrong"
    else:
        register = tmp_path / "other-register.yaml"
        register.write_bytes(release_input.register.read_bytes() + b"\n")
    with pytest.raises(projection.ProjectionRefusal, match=r"citation|register differs"):
        projection.create_release([card], release_version="v0.1.0", register_path=register,
                                  allow_candidates=True)


def test_mixed_release_counts_only_emitted_cards(release_input):
    candidate = copy.deepcopy(release_input.card)
    candidate["card_id"] = "wc_0123456789ac"
    for index, assertion in enumerate(candidate["assertions"]):
        assertion["assertion_id"] = "wa_" + f"{100 + index:024x}"
        assertion["subject"]["id"] = candidate["card_id"]
    result = projection.create_release(
        [candidate, release_input.card], release_version="v0.1.0", allow_candidates=True,
    )
    rows = [json.loads(line) for line in result.dataset.splitlines()]
    assert [row["status"] for row in rows] == ["CERTIFIED", "CANDIDATE"]
    assert (result.manifest["card_count"], result.manifest["certified_count"],
            result.manifest["candidate_count"]) == (2, 1, 1)
    # A candidate with no surviving assertion contributes only to the input count.
    candidate["assertions"] = []
    filtered = projection.create_release(
        [candidate, release_input.card], release_version="v0.1.0", allow_candidates=True,
    )
    assert (filtered.manifest["input_card_count"], filtered.manifest["card_count"],
            filtered.manifest["certified_count"], filtered.manifest["candidate_count"]) == (2, 1, 1, 0)


def test_candidate_cli_and_cumulative_withdrawal(release_input, tmp_path, capsys):
    card = release_input.card
    card["known_gaps"] = ["Pending review"]
    source = tmp_path / "cards.json"
    source.write_text(json.dumps([card]))
    common = ["--cards", str(source), "--version", "v0.1.0"]
    assert projection.main([*common, "--output", str(tmp_path / "strict")]) == 1
    assert not (tmp_path / "strict").exists()
    assert projection.main([*common, "--allow-candidates", "--output", str(tmp_path / "candidate")]) == 0
    manifest = json.loads(capsys.readouterr().out)
    assert (manifest["certified_count"], manifest["candidate_count"]) == (0, 1)
    assert json.loads((tmp_path / "candidate/word-cards.jsonl").read_bytes())["known_gaps"] == ["Pending review"]
    replacement = projection.withdraw_release(
        [card], previous_version="v0.1.0", release_version="v0.1.1", allow_candidates=True,
        selector={"source_id": "vesum"}, justification="Synthetic withdrawal",
        withdrawals=[{"selector": {"source_id": "ulif"}, "justification": "Prior withdrawal"}],
    )
    assert replacement.dataset == b""
    assert (replacement.manifest["card_count"], replacement.manifest["certified_count"],
            replacement.manifest["candidate_count"]) == (0, 0, 0)
    assert replacement.withdrawal_notice["removed_field_citations"] == 1
