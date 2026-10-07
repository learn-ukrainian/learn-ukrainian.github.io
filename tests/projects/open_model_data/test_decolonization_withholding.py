"""Unsupported held evidence is withheld; review/integrity errors still fail (#9858)."""

from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from scripts.lib.readonly_sqlite import open_readonly
from scripts.projects.open_model_data import build_decolonization_cases as builder
from scripts.projects.open_model_data import sum20_codification_records as records
from tests.projects.open_model_data.test_sum20_codification_records import (
    FORMERLY_KEPT_RECORDS,
    _healthy_dictionary_schema,
)

# Full held-source regression denominator, including failures hidden by the old first exception.
EXPECTED_WITHHELD = {
    "decol_lex_001": "held_source_missing",
    "decol_lex_002": "held_source_unproven",
    "decol_lex_003": "held_source_missing",
    "decol_lex_005": "held_source_missing",
    "decol_lex_006": "held_source_missing",
    "decol_lex_007": "held_source_missing",
    "decol_lex_008": "held_source_missing",
    "decol_lex_009": "held_source_unproven",
    "decol_lex_012": "held_source_unproven",
    "decol_lex_014": "held_source_unproven",
    "decol_lex_016": "held_source_missing",
    "decol_lex_017": "held_source_unproven",
    "decol_lex_019": "held_source_missing",
    "decol_lex_020": "held_source_missing",
    "decol_lex_021": "held_source_missing",
    "decol_lex_022": "held_source_missing",
    "decol_lex_023": "held_source_unproven",
    "decol_lex_024": "held_source_missing",
    "decol_lex_025": "held_source_unproven",
    "decol_lex_026": "held_source_unproven",
    "decol_lex_027": "held_source_unproven",
    "decol_lex_028": "held_source_unproven",
    "decol_lex_029": "held_source_unproven",
    "decol_lex_030": "held_source_unproven",
    "decol_lex_031": "held_source_unproven",
    "decol_lex_032": "held_source_unproven",
    "decol_lex_034": "held_source_unproven",
    "decol_lex_035": "held_source_unproven",
    "decol_lex_036": "held_source_unproven",
    "decol_lex_037": "held_source_unproven",
    "decol_lex_038": "held_source_unproven",
    "decol_lex_039": "held_source_unproven",
    "decol_lex_040": "held_source_unproven",
    "decol_lex_041": "held_source_missing",
    "decol_lex_042": "held_source_unproven",
    "decol_lex_043": "held_source_unproven",
    "decol_lex_044": "held_source_missing",
    "decol_lex_045": "held_source_unproven",
    "decol_lex_046": "held_source_unproven",
    "decol_lex_047": "held_source_unproven",
    "decol_lex_048": "held_source_unproven",
    "decol_lex_049": "held_source_unproven",
    "decol_lex_050": "held_source_unproven",
    "decol_lex_051": "held_source_unproven",
    "decol_lex_052": "held_source_unproven",
    "decol_lex_053": "held_source_unproven",
    "decol_lex_054": "held_source_unproven",
    "decol_lex_055": "held_source_unproven",
    "decol_lex_056": "held_source_unproven",
    "decol_lex_057": "held_source_unproven",
    "decol_lex_058": "held_source_unproven",
    "decol_lex_059": "held_source_unproven",
    "decol_lex_060": "held_source_unproven",
    "decol_prep_001": "held_source_missing",
    "decol_prep_002": "held_source_missing",
    "decol_prep_004": "held_source_missing",
    "decol_prep_005": "held_source_missing",
    "decol_prep_006": "held_source_missing",
    "decol_prep_007": "held_source_missing",
    "decol_prep_008": "held_source_missing",
    "decol_prep_009": "held_source_missing",
    "decol_prep_010": "held_source_missing",
    "decol_prep_011": "held_source_missing",
    "decol_prep_012": "held_source_missing",
    "decol_prep_013": "held_source_missing",
    "decol_prep_014": "held_source_missing",
    "decol_prep_015": "held_source_missing",
    "decol_prep_016": "held_source_missing",
    "decol_prep_017": "held_source_missing",
    "decol_prep_018": "held_source_missing",
    "decol_prep_019": "held_source_missing",
    "decol_prep_020": "held_source_missing",
    "decol_prep_021": "held_source_missing",
    "decol_prep_022": "held_source_missing",
    "decol_prep_023": "held_source_missing",
    "decol_prep_024": "held_source_missing",
    "decol_prep_025": "held_source_missing",
    "decol_prep_026": "held_source_missing",
    "decol_prep_028": "held_source_missing",
    "decol_prep_031": "held_source_missing",
    "decol_prep_032": "held_source_missing",
    "decol_prep_033": "held_source_missing",
    "decol_prep_037": "held_source_missing",
    "decol_prep_038": "held_source_missing",
    "decol_prep_039": "held_source_missing",
    "decol_prep_040": "held_source_missing",
    "decol_prep_042": "held_source_missing",
    "decol_prep_044": "held_source_unproven",
    "decol_prep_045": "held_source_missing",
    "decol_prep_046": "held_source_missing",
    "decol_prep_047": "held_source_missing",
    "decol_prep_048": "held_source_missing",
    "decol_prot_001": "held_source_unproven",
    "decol_prot_002": "held_source_unproven",
    "decol_prot_003": "held_source_unproven",
    "decol_prot_004": "held_source_unproven",
    "decol_prot_005": "held_source_missing",
    "decol_prot_006": "held_source_unproven",
    "decol_prot_007": "held_source_unproven",
    "decol_prot_010": "held_source_unproven",
    "decol_prot_011": "held_source_missing",
    "decol_prot_012": "held_source_unproven",
    "decol_prot_013": "held_source_unproven",
    "decol_prot_015": "held_source_unproven",
    "decol_prot_016": "held_source_unproven",
    "decol_prot_017": "held_source_unproven",
    "decol_prot_018": "held_source_unproven",
    "decol_prot_019": "held_source_unproven",
    "decol_prot_020": "held_source_missing",
    "decol_prot_021": "held_source_unproven",
    "decol_prot_022": "held_source_unproven",
    "decol_prot_023": "held_source_unproven",
    "decol_prot_024": "held_source_unproven",
    "decol_prot_025": "held_source_unproven",
    "decol_prot_026": "held_source_unproven",
    "decol_prot_027": "held_source_unproven",
    "decol_prot_028": "held_source_unproven",
    "decol_prot_029": "held_source_unproven",
    "decol_prot_030": "held_source_unproven",
    "decol_prot_031": "held_source_unproven",
    "decol_prot_033": "held_source_unproven",
    "decol_prot_034": "held_source_unproven",
    "decol_prot_035": "held_source_unproven",
    "decol_prot_036": "held_source_unproven",
    "decol_prot_037": "held_source_unproven",
    "decol_prot_038": "held_source_unproven",
    "decol_prot_039": "held_source_unproven",
    "decol_prot_040": "held_source_unproven",
    "decol_prot_041": "held_source_unproven",
    "decol_prot_042": "held_source_unproven",
    "decol_prot_043": "held_source_unproven",
    "decol_prot_044": "held_source_unproven",
    "decol_prot_045": "held_source_unproven",
    "decol_prot_046": "quarantined_headword",
    "decol_prot_047": "held_source_unproven",
    "decol_prot_048": "held_source_unproven",
    "decol_prot_049": "held_source_unproven",
    "decol_prot_050": "held_source_missing",
    "decol_prot_051": "held_source_unproven",
    "decol_prot_052": "held_source_unproven",
    "decol_prot_053": "held_source_unproven",
    "decol_prot_054": "held_source_unproven",
    "decol_prot_055": "held_source_missing",
    "decol_prot_056": "held_source_unproven",
    "decol_prot_057": "held_source_unproven",
    "decol_prot_058": "quarantined_headword",
    "decol_prot_059": "quarantined_headword",
    "decol_prot_060": "held_source_missing",
    "decol_prot_061": "quarantined_headword",
    "decol_prot_062": "held_source_missing",
    "decol_prot_063": "quarantined_headword",
    "decol_prot_064": "quarantined_headword",
    "decol_prot_065": "held_source_unproven",
    "decol_prot_066": "held_source_unproven",
    "decol_prot_067": "held_source_unproven",
    "decol_prot_068": "held_source_missing",
    "decol_prot_069": "quarantined_headword",
    "decol_prot_070": "held_source_missing",
    "decol_prot_071": "quarantined_headword",
    "decol_prot_072": "quarantined_headword",
    "decol_prot_073": "held_source_unproven",
    "decol_prot_074": "held_source_unproven",
    "decol_prot_075": "held_source_unproven",
    "decol_syn_001": "held_source_unproven",
    "decol_syn_003": "held_source_unproven",
    "decol_syn_005": "held_source_unproven",
    "decol_syn_006": "held_source_unproven",
    "decol_syn_010": "held_source_unproven",
    "decol_syn_011": "held_source_unproven",
    "decol_syn_012": "held_source_unproven",
    "decol_syn_014": "held_source_unproven",
    "decol_syn_015": "held_source_unproven",
    "decol_syn_016": "held_source_unproven",
    "decol_syn_017": "held_source_unproven",
    "decol_syn_018": "held_source_unproven",
    "decol_syn_019": "held_source_missing",
    "decol_syn_020": "held_source_unproven",
    "decol_syn_021": "held_source_missing",
    "decol_syn_022": "held_source_missing",
    "decol_syn_023": "held_source_unproven",
    "decol_syn_024": "quarantined_headword",
    "decol_syn_025": "held_source_missing",
    "decol_syn_029": "held_source_unproven",
    "decol_syn_030": "held_source_unproven",
    "decol_syn_031": "held_source_unproven",
    "decol_syn_032": "held_source_missing",
    "decol_syn_033": "held_source_unproven",
    "decol_syn_034": "held_source_unproven",
    "decol_syn_035": "held_source_missing",
    "decol_syn_036": "held_source_unproven",
    "decol_syn_037": "held_source_unproven",
    "decol_syn_038": "held_source_unproven",
    "decol_syn_039": "held_source_missing",
    "decol_syn_040": "held_source_unproven",
    "decol_syn_041": "held_source_unproven",
    "decol_syn_042": "held_source_missing",
    "decol_syn_043": "held_source_unproven",
    "decol_syn_044": "held_source_missing",
    "decol_syn_045": "held_source_unproven",
    "decol_syn_046": "held_source_unproven",
    "decol_syn_047": "held_source_unproven",
    "decol_syn_048": "held_source_unproven",
    "decol_syn_049": "held_source_unproven",
    "decol_syn_050": "held_source_unproven",
    "decol_syn_051": "held_source_unproven",
    "decol_syn_052": "held_source_unproven",
    "decol_syn_053": "held_source_unproven",
    "decol_syn_054": "held_source_unproven",
    "decol_syn_055": "held_source_unproven",
    "decol_syn_056": "held_source_unproven",
    "decol_syn_057": "held_source_unproven",
    "decol_syn_058": "held_source_unproven",
    "decol_syn_059": "held_source_missing",
    "decol_syn_060": "held_source_missing",
    "decol_syn_061": "held_source_unproven",
    "decol_syn_062": "held_source_missing",
    "decol_syn_063": "held_source_missing",
    "decol_syn_064": "held_source_unproven",
    "decol_syn_065": "held_source_unproven",
}

EXPECTED_RETAINED_BINDINGS = {
    "decol_lex_004": ("style_guide", 187, "text", "0bb89c81df10abb6318e8f79e6e2e462b6054ff3cb9f434d7d3f5937122c8281"),
    "decol_lex_010": ("style_guide", 81, "text", "7aa77d2f4a231fc0626e1a2ae8e1fad0b8b89e84315db3fbf7933763f7d11458"),
    "decol_lex_011": ("style_guide", 14, "text", "052d222f2bbf4f969884e31698eaf153646e1efc4b6f6cbc2072697a48208754"),
    "decol_lex_013": ("style_guide", 55, "text", "238a3975a169669983560bf5d2c65c06cf5daf910dff79041288f467203e1a9b"),
    "decol_lex_015": ("style_guide", 44, "text", "8bedc7d9f03fd2b679a87966ce62d19e46776d1091790215e22202c71a8cb613"),
    "decol_lex_018": ("style_guide", 53, "text", "300948a5e6e96788a10737ab673578dca294b303d738d946b58d7fa73b4f3f29"),
    "decol_lex_033": ("style_guide", 39, "text", "4c68c2591f1597a5fd3ea2151f05d7856108534ecfb587bb97a9f704fd3565a7"),
    "decol_prep_003": ("style_guide", 248, "text", "31b5604aa86091fad867d521c4f8c845e436891b86bda0ea2eeb82f8c5430a97"),
    "decol_prep_027": ("style_guide", 247, "text", "ad2d94d1b8c52be75a9b8b6d45ccf200ddfd888dab184e4ffba54d4dd268163f"),
    "decol_prep_029": ("style_guide", 227, "text", "da4373206f7b7b6cf87d340e2ec6db5dfc01c00a13a9c560e9699eb09d76f2ba"),
    "decol_prep_030": ("style_guide", 24, "text", "6d700ec76a822c5840015bc86dbbdf35a8567eceecb0caf98777a93f10f96693"),
    "decol_prep_034": ("style_guide", 156, "text", "a0885dd80c9f1fe2ce4337ece97e1a806256478fef3cef4869724884c5846fd4"),
    "decol_prep_035": ("style_guide", 247, "text", "ad2d94d1b8c52be75a9b8b6d45ccf200ddfd888dab184e4ffba54d4dd268163f"),
    "decol_prep_036": ("style_guide", 33, "text", "97f483649ad7f17b919a472f35b0300703285f89bb213d4cdc2da919d2e6d453"),
    "decol_prep_041": ("style_guide", 247, "text", "ad2d94d1b8c52be75a9b8b6d45ccf200ddfd888dab184e4ffba54d4dd268163f"),
    "decol_prep_043": ("style_guide", 143, "text", "3f8d4fab15851cf7b49012ffaf07b2f834f6633dc34942577e027cade93b9f3b"),
    "decol_prep_049": ("style_guide", 75, "text", "05d444ef78dd45dc45cb7ea5ffde3dfb03ec4aeee0c3b87f6968e2b638a9c203"),
    "decol_prep_050": ("style_guide", 193, "text", "1e51c229e97f484e6ce0f3109b94223a21359fc2b0d7799265080c2588280154"),
    "decol_prot_008": ("style_guide", 12, "text", "5e4ce53c351bb08b22d4c08a7694bb54e122d58cf16e6770c7f921d7888c0d63"),
    "decol_prot_009": ("style_guide", 80, "text", "3d228c9c09037d3ae31cf67d1a59492106c5ddc5df11612d1997d5ecc3b5a887"),
    "decol_prot_014": ("style_guide", 222, "text", "d15ad371a69c495a42691b0302e86b6385f2f1a48e0d55d4beb312c3a7f421ba"),
    "decol_prot_032": ("style_guide", 2, "text", "bf32f4df4fa83292791f41f0e6f0e3df94b7dffd1effac50a6033bc1821186bc"),
    "decol_syn_002": ("style_guide", 175, "text", "bd65e6b64de1e0cd71732dba525a0bf9eebfa26e9fd17a3d7950b137dbc6f680"),
    "decol_syn_004": ("style_guide", 177, "text", "a166f9f9bd46f4e753f880cf48da7d2fdccc83760b61cefd98cfae3acf060f05"),
    "decol_syn_007": ("style_guide", 35, "text", "736f95a491641a858ad810785b97dd9be8ffd45a8dda14fb1884d57231e689c3"),
    "decol_syn_008": ("style_guide", 125, "text", "7c839aab2674a45397bd2db9d9c67a9fc749d5f7bc932e3905cf9306e8aa0bd0"),
    "decol_syn_009": ("style_guide", 247, "text", "ad2d94d1b8c52be75a9b8b6d45ccf200ddfd888dab184e4ffba54d4dd268163f"),
    "decol_syn_013": ("style_guide", 45, "text", "f74757ce119fd16e33368e10f228cbdeb0dee0641a4bd6c1f65d607b5ec1ba8f"),
    "decol_syn_026": ("style_guide", 130, "text", "3c76979385a294bc32c0e24a2d945d931d01bc60acb4007176e9ffbb996bf6e0"),
    "decol_syn_027": ("style_guide", 130, "text", "3c76979385a294bc32c0e24a2d945d931d01bc60acb4007176e9ffbb996bf6e0"),
    "decol_syn_028": ("style_guide", 127, "text", "d57379ea79df998ad8b2a19aedb48797d08802866b26a18c3fe37fe60b3798e2"),
}


def _healthy_source_schema(conn):
    _healthy_dictionary_schema(conn)
    for column in ("speaker", "source_file", "channel_id", "domain", "decolonization_tag"):
        conn.execute(f"ALTER TABLE external_articles ADD COLUMN {column} TEXT")
    conn.executescript(
        "CREATE TABLE style_guide (id INTEGER PRIMARY KEY, word TEXT, section TEXT, source TEXT, text TEXT, excerpt_full TEXT, page INTEGER);"
        "CREATE TABLE ua_gec_errors (id INTEGER PRIMARY KEY, error TEXT, correct TEXT, error_type TEXT, doc_id TEXT);"
        "CREATE TABLE textbooks (id INTEGER PRIMARY KEY, title TEXT, text TEXT, author TEXT, author_uk TEXT, source_file TEXT);"
        "CREATE VIRTUAL TABLE textbooks_fts USING fts5(title,text);"
        "CREATE TABLE pravopys_paragraphs (source_id TEXT, number INTEGER, text TEXT, text_sha256 TEXT, locator TEXT);"
    )


def _one_case(monkeypatch, confirmation):
    sources = sqlite3.connect(":memory:")
    vesum = sqlite3.connect(":memory:")
    _healthy_source_schema(sources)
    connections = iter((vesum, sources))
    monkeypatch.setattr(builder.sqlite3, "connect", lambda *a, **kw: next(connections))
    monkeypatch.setattr(builder, "LEXICAL_CALQUES", [builder.LEXICAL_CALQUES[2]])
    for name in ("SYNTACTIC_CALQUES", "PREPOSITIONAL_CALQUES", "PROTECTIVE_CONTROLS"):
        monkeypatch.setattr(builder, name, [])
    monkeypatch.setattr(builder, "make_reviewer_confirmation", confirmation)
    return sources, vesum


def test_decolonization_source_failure_is_recorded_and_build_completes(monkeypatch):
    def unavailable(*args):
        raise builder.SourceEvidenceUnavailable("no held row", "held_source_missing")

    sources, vesum = _one_case(monkeypatch, unavailable)
    try:
        withheld = []
        assert builder.build_all_cases(withheld=withheld) == []
        assert withheld == [
            {
                "case_id": "decol_lex_003",
                "reason_code": "held_source_missing",
                "record_keys": [],
                "owner": "claude-open-model-data",
                "issue": 6321,
            }
        ]
    finally:
        sources.close()
        vesum.close()


def test_decolonization_integrity_failure_is_never_withholding(monkeypatch):
    def invalid_review(*args):
        raise ValueError("review content digest mismatch")

    sources, vesum = _one_case(monkeypatch, invalid_review)
    try:
        with pytest.raises(ValueError, match="review content digest mismatch"):
            builder.build_all_cases(withheld=[])
    finally:
        sources.close()
        vesum.close()


@pytest.mark.parametrize(
    "case_id",
    [
        "decol_prot_058",
        "decol_prot_061",
        "decol_prot_063",
        "decol_prot_064",
        "decol_prot_071",
    ],
)
def test_decolonization_queries_cannot_fallback_for_withheld_passages(case_id):
    evidence = builder.EXPLICIT_SOURCE_EVIDENCE[case_id]
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        _healthy_dictionary_schema(sources)
        with pytest.raises(builder.SourceEvidenceUnavailable, match="Committed source record"):
            builder.query_source_evidence(
                case_id,
                evidence["target_term"],
                "",
                evidence["authority"],
                "protective_authentic",
                sources.cursor(),
                vesum.cursor(),
                [],
            )


def test_decolonization_check_and_export_account_for_withholding(monkeypatch, tmp_path, capsys):
    withheld = [{"case_id": "decol_lex_003", "reason_code": "held_source_missing", "owner": "claude-open-model-data"}]

    def build(**kwargs):
        kwargs["withheld"].extend(withheld)
        return []

    monkeypatch.setattr(builder, "build_all_cases", build)
    assert builder.main(["--check"]) == 0
    output = capsys.readouterr().out
    assert "withheld 1 of 1 candidates" in output
    assert "Withheld decol_lex_003: held_source_missing" in output
    assert "all 250" not in output
    assert builder.main(["--output-dir", str(tmp_path)]) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["withheld_cases"] == withheld
    assert manifest["candidate_cases"] == 1
    assert json.loads((tmp_path / "cases.json").read_text()) == []
    assert (tmp_path / "decolonization_train.jsonl").read_text() == ""
    assert (tmp_path / "decolonization_eval.jsonl").read_text() == ""


def test_decolonization_held_sources_pin_withheld_set():
    sources = builder._resolve_db_path("sources.db", builder.PROJECT_ROOT)
    vesum = builder._resolve_db_path("vesum.db", builder.PROJECT_ROOT)
    if not sources.is_file() or not vesum.is_file():
        pytest.skip("requires held sources.db and vesum.db")
    if not (builder.REGISTRY_DECOLONIZATION_DIR / "reviews/decol_lex_001.review.json").is_file():
        pytest.skip("requires committed review dossiers in sparse checkout")
    with open_readonly(sources) as conn:
        dispositions = records.committed_record_dispositions(conn)
        assert {
            key for key, d in dispositions.items() if d["reason_code"] == "held_source_unproven"
        } == FORMERLY_KEPT_RECORDS
        assert {d["status"] for d in dispositions.values()} == {"withheld"}
    withheld = []
    accepted = builder.build_all_cases(withheld=withheld)
    assert {d["case_id"]: d["reason_code"] for d in withheld} == EXPECTED_WITHHELD
    assert {
        c.case_id: (
            c.reviewer_confirmation["source_evidence"]["binding"]["table"],
            c.reviewer_confirmation["source_evidence"]["binding"]["row_id"],
            c.reviewer_confirmation["source_evidence"]["binding"]["text_field"],
            c.reviewer_confirmation["source_evidence"]["binding"]["text_sha256"],
        )
        for c in accepted
    } == EXPECTED_RETAINED_BINDINGS
    assert len(accepted) + len(withheld) == 250
    assert len(withheld) == len(EXPECTED_WITHHELD)
    assert not ({c.case_id for c in accepted} & set(EXPECTED_WITHHELD))
    assert all(d["owner"] == "claude-open-model-data" and d["issue"] == 6321 for d in withheld)
    train, evaluation = builder.generate_dataset_records(accepted)
    assert len(train) + len(evaluation) == len(accepted) * 2
    assert not ({r["case_id"] for r in train + evaluation} & set(EXPECTED_WITHHELD))


@pytest.fixture
def dictionary_probe(monkeypatch):
    """Independent synthetic rows; no copied catalog/committed quotations."""
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        _healthy_dictionary_schema(sources)
        vesum.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, pos TEXT, tags TEXT, source_location TEXT)")
        vesum.execute("INSERT INTO forms_all VALUES ('fixture', 'fixture', 'noun', '', 'synthetic')")
        evidence = {
            "authority": "СУМ-20",
            "source": "СУМ-20",
            "target_term": "fixture",
            "article": "FIXTURE",
            "supporting_passage": "literal synthetic passage",
            "locus": "synthetic locus",
        }
        monkeypatch.setattr(builder, "EXPLICIT_SOURCE_EVIDENCE", {"synthetic": evidence})
        yield sources, vesum, evidence


def _query_dictionary(probe):
    sources, vesum, evidence = probe
    return builder.query_source_evidence(
        "synthetic",
        evidence["target_term"],
        "",
        evidence["authority"],
        "synthetic",
        sources.cursor(),
        vesum.cursor(),
        [],
    )


@pytest.mark.parametrize("row_text", ["fixture", "fixture literal synthetic passage altered"])
def test_headword_and_changed_passage_cannot_authenticate_dictionary(dictionary_probe, row_text):
    sources, _, evidence = dictionary_probe
    # Even a tiny catalog quotation edit must not bypass the generic binding check.
    if "altered" in row_text:
        evidence["supporting_passage"] += " changed"
    sources.execute("INSERT INTO ulif_dictua_entries VALUES (1, 'fixture', 'fixture', ?)", (row_text,))
    with pytest.raises(builder.SourceEvidenceUnavailable, match="literal passage") as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "held_source_unproven"


def test_literal_passage_with_wrong_credited_source_withholds(dictionary_probe):
    sources, _, evidence = dictionary_probe
    sources.execute(
        "INSERT INTO ulif_dictua_entries VALUES (1, 'fixture', 'fixture', ?)",
        (evidence["supporting_passage"],),
    )
    with pytest.raises(builder.SourceEvidenceUnavailable, match="passage/source binding") as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "held_source_unproven"


@pytest.mark.parametrize("lookup", ["headword", "phrase"])
def test_literal_same_source_dictionary_positive_control(dictionary_probe, lookup):
    sources, vesum, evidence = dictionary_probe
    if lookup == "phrase":
        evidence["target_term"] = "fixture phrase"
        evidence["article"] = "ABSENT"
        evidence["supporting_passage"] = "fixture phrase literal synthetic passage"
        vesum.execute("INSERT INTO forms_all VALUES ('phrase', 'phrase', 'noun', '', 'synthetic')")
    sources.execute(
        "INSERT INTO sum20_articles VALUES (42, 'FIXTURE', 'fixture', ?, '', 'https://sum20ua.com/?wordid=42', '')",
        (evidence["supporting_passage"],),
    )
    result = builder.query_source_evidence(
        "synthetic", evidence["target_term"], "", "СУМ-20", "synthetic", sources.cursor(), vesum.cursor(), []
    )
    assert result["supporting_passage"] == evidence["supporting_passage"]
    assert result["source"] == "СУМ-20"


@pytest.mark.parametrize("table", ["sum20_articles", "ulif_dictua_entries", "external_articles"])
@pytest.mark.parametrize("defect", ["missing_table", "missing_column"])
def test_required_dictionary_schema_errors_abort(dictionary_probe, table, defect):
    sources, _, _ = dictionary_probe
    # Synthetic store damage, never a real source mutation.
    sources.execute(f"DROP TABLE {table}")
    if defect == "missing_column":
        sources.execute(f"CREATE TABLE {table} (id INTEGER)")
    with pytest.raises(sqlite3.OperationalError, match=r"no such (table|column)"):
        _query_dictionary(dictionary_probe)


def test_review_missing_tables_reproduction_cannot_pass_check(monkeypatch, tmp_path):
    sources_path = tmp_path / "sources.db"
    vesum_path = tmp_path / "vesum.db"
    with sqlite3.connect(sources_path), sqlite3.connect(vesum_path):
        pass
    monkeypatch.setattr(builder, "_resolve_db_path", lambda name, root: tmp_path / name)
    # F2: no sum20_articles, ulif_dictua_entries or external_articles.
    with pytest.raises(sqlite3.OperationalError, match="no such table: sum20_articles"):
        builder.main(["--check"])


def test_healthy_dictionary_with_no_row_withholds(dictionary_probe):
    with pytest.raises(builder.SourceEvidenceUnavailable, match="Held source") as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "held_source_missing"


def test_healthy_dictionary_with_missing_literal_passage_withholds(dictionary_probe):
    sources, _, _ = dictionary_probe
    sources.execute(
        "INSERT INTO sum20_articles VALUES (42, 'FIXTURE', 'fixture', 'fixture unrelated text', '', "
        "'https://sum20ua.com/?wordid=42', '')"
    )
    with pytest.raises(builder.SourceEvidenceUnavailable, match="literal passage") as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "held_source_unproven"


def test_edited_passage_cannot_bypass_quarantined_headword(dictionary_probe):
    sources, _, evidence = dictionary_probe
    evidence["supporting_passage"] += " changed"
    sources.execute(
        "INSERT INTO sum20_articles VALUES (42, 'FIXTURE', 'fixture', ?, '', "
        "'https://sum20ua.com/?wordid=42', 'synthetic quarantine')",
        (evidence["supporting_passage"],),
    )
    with pytest.raises(builder.SourceEvidenceUnavailable, match="quarantined headword") as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "quarantined_headword"


@pytest.mark.parametrize("title", ["ВТС fixture", "Review of ВТС fixture", "тлумачний fixture"])
def test_external_dictionary_title_never_authenticates_identity(dictionary_probe, title):
    sources, _, evidence = dictionary_probe
    evidence["authority"] = evidence["source"] = "ВТС"
    sources.execute("INSERT INTO external_articles VALUES (9, ?, ?)", (title, evidence["supporting_passage"]))
    with pytest.raises(builder.SourceEvidenceUnavailable) as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "held_source_unproven"


def test_trusted_vts_cache_positive_control(dictionary_probe):
    sources, _, evidence = dictionary_probe
    evidence["authority"] = evidence["source"] = "ВТС"
    sources.execute("CREATE TABLE slovnyk_me_entries (id INTEGER, source_url TEXT, dictionary_slug TEXT, text TEXT)")
    sources.execute(
        "INSERT INTO slovnyk_me_entries VALUES (13, 'https://slovnyk.me/dict/vts/fixture', 'vts', 'literal synthetic passage')"
    )
    assert _query_dictionary(dictionary_probe)["binding"]["locator"] == "slovnyk_me_entries:13"


def test_missing_source_provenance_column_is_integrity_failure(dictionary_probe):
    sources, _, _ = dictionary_probe
    sources.execute("ALTER TABLE sum20_articles DROP COLUMN official_url")
    with pytest.raises(sqlite3.OperationalError, match="no such column: official_url"):
        _query_dictionary(dictionary_probe)


def test_dictionary_query_error_is_never_ordinary_absence(dictionary_probe):
    sources, vesum, evidence = dictionary_probe

    class FailedQuery:
        connection = sources

        def execute(self, query, args=()):
            if "ORDER BY id" in query and "sum20_articles" in query:
                raise sqlite3.OperationalError("synthetic query failure")
            return sources.execute(query, args)

    with pytest.raises(sqlite3.OperationalError, match="synthetic query failure"):
        builder.query_source_evidence(
            "synthetic", "fixture", "", evidence["authority"], "synthetic", FailedQuery(), vesum.cursor(), []
        )


PASSAGE = "literal synthetic passage"
ANTONENKO = "Борис Антоненко-Давидович «Як ми говоримо»"
PONOMARIV = "Олександр Пономарів «Культура слова»"
HORODENSKA = "Катерина Городенська «Чи правильне слововживання?»"


@pytest.fixture(params=["style", "book", "external", "horodenska", "pravopys", "gec"])
def admitted_source_probe(request, monkeypatch):
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        _healthy_source_schema(sources)
        vesum.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, pos TEXT, tags TEXT, source_location TEXT)")
        vesum.execute("INSERT INTO forms_all VALUES ('fixture','fixture','noun','','synthetic')")
        auth = {
            "style": ANTONENKO,
            "book": ANTONENKO,
            "external": PONOMARIV,
            "horodenska": HORODENSKA,
            "pravopys": "Український правопис (2019)",
            "gec": "UA-GEC (Syvokon et al., 2023)",
        }[request.param]
        ev = {
            "authority": auth,
            "source": "UA-GEC v2.0" if request.param == "gec" else auth,
            "target_term": "fixture",
            "supporting_passage": PASSAGE,
            "locus": "synthetic locus",
        }
        monkeypatch.setattr(builder, "EXPLICIT_SOURCE_EVIDENCE", {"synthetic": ev})
        monkeypatch.setattr(
            builder,
            "UA_GEC_RECORD_MAP",
            {
                "synthetic": {
                    "id": 12,
                    "correct": "fixture",
                    "error": "wrong",
                    "error_type": "F/Calque",
                    "doc_id": "fixture-doc",
                }
            },
        )
        yield sources, vesum, ev, request.param


def _insert_witness(probe, text=PASSAGE, row_id=12):
    sources, _, ev, family = probe
    if family == "style":
        sources.execute(
            "INSERT INTO style_guide VALUES (?, 'fixture', 'synthetic', 'Антоненко-Давидович', ?, '', 1)",
            (row_id, text),
        )
    elif family == "book":
        sources.execute(
            "INSERT INTO textbooks VALUES (?, 'arbitrary chunk title', ?, 'Borys Antonenko-Davydovych', 'Борис Антоненко-Давидович', 'antonenko-davydovych-yak-my-hovorymo')",
            (row_id, text),
        )
    elif family in ("external", "horodenska"):
        sources.execute(
            "INSERT INTO external_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (row_id, "synthetic witness", text, ev["authority"], "synthetic-held-book", "witness", "book", None),
        )
    elif family == "pravopys":
        sources.execute(
            "INSERT INTO pravopys_paragraphs VALUES ('pravopys_2019_official', ?, ?, ?, 'synthetic §12')",
            (row_id, text, hashlib.sha256(text.encode()).hexdigest()),
        )
    elif family == "gec":
        # A correction containing the exact passage still has to align to independently mapped metadata.
        # Use the error field for the quotation; correction identity remains 'fixture'.
        sources.execute("INSERT INTO ua_gec_errors VALUES (?, ?, 'fixture', 'F/Calque', 'fixture-doc')", (row_id, text))
        builder.UA_GEC_RECORD_MAP["synthetic"]["error"] = text


def _query_source(probe):
    sources, vesum, ev, _ = probe
    return builder.query_source_evidence(
        "synthetic", "fixture", "", ev["authority"], "synthetic", sources.cursor(), vesum.cursor(), []
    )


def test_each_admitted_family_literal_positive(admitted_source_probe):
    _insert_witness(admitted_source_probe)
    result = _query_source(admitted_source_probe)
    binding = result["binding"]
    assert result["supporting_passage"] == PASSAGE
    assert binding["row_id"] == ("pravopys_2019_official:12" if admitted_source_probe[3] == "pravopys" else 12)
    assert binding["text_sha256"] == hashlib.sha256(PASSAGE.encode()).hexdigest()
    assert binding["locator"]


@pytest.mark.parametrize(
    "text",
    [
        "fixture",
        "LITERAL synthetic passage",
        "literal synthetic\npassage",
        "líteral synthetic passage",
        "literal\u00a0synthetic passage",
    ],
)
def test_each_family_headword_or_normalized_only_is_withheld(admitted_source_probe, text):
    _insert_witness(admitted_source_probe, text)
    with pytest.raises(builder.SourceEvidenceUnavailable) as error:
        _query_source(admitted_source_probe)
    assert error.value.reason_code == "held_source_unproven"


def test_each_family_placeholder_never_survives(admitted_source_probe):
    _insert_witness(admitted_source_probe)
    admitted_source_probe[2]["supporting_passage"] = "arbitrary placeholder not in witness"
    with pytest.raises(builder.SourceEvidenceUnavailable) as error:
        _query_source(admitted_source_probe)
    assert error.value.reason_code == "held_source_unproven"


def test_each_family_miscredited_source_withholds(admitted_source_probe):
    _insert_witness(admitted_source_probe)
    admitted_source_probe[2]["source"] = "unknown source"
    with pytest.raises(builder.SourceEvidenceUnavailable) as error:
        _query_source(admitted_source_probe)
    assert error.value.reason_code == "held_source_unproven"


def test_each_family_healthy_absence_withholds(admitted_source_probe):
    with pytest.raises(builder.SourceEvidenceUnavailable) as error:
        _query_source(admitted_source_probe)
    assert error.value.reason_code == "held_source_missing"


@pytest.mark.parametrize("marker", ["channel_id", "domain", "source_file", "decolonization_tag", "other_case_tag"])
def test_project_authored_literal_is_not_a_witness(monkeypatch, marker):
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        _healthy_source_schema(sources)
        vesum.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, pos TEXT, tags TEXT, source_location TEXT)")
        vesum.execute("INSERT INTO forms_all VALUES ('fixture','fixture','noun','','synthetic')")
        ev = {
            "authority": PONOMARIV,
            "source": PONOMARIV,
            "target_term": "fixture",
            "supporting_passage": PASSAGE,
            "locus": "synthetic",
        }
        monkeypatch.setattr(builder, "EXPLICIT_SOURCE_EVIDENCE", {"synthetic": ev})
        probe = (sources, vesum, ev, "external")
        _insert_witness(probe)
        value = {
            "channel_id": "omd",
            "domain": "codification",
            "source_file": "codification-synthetic",
            "decolonization_tag": "synthetic",
            "other_case_tag": "decol_syn_001",
        }[marker]
        sources.execute(
            f"UPDATE external_articles SET {'decolonization_tag' if marker == 'other_case_tag' else marker} = ?",
            (value,),
        )
        with pytest.raises(builder.SourceEvidenceUnavailable) as error:
            _query_source(probe)
        assert error.value.reason_code == "held_source_unproven"
        # Same literal in a separately admitted non-project witness must still succeed.
        _insert_witness(probe, row_id=13)
        assert _query_source(probe)["binding"]["row_id"] == 13
        assert sources.execute("SELECT count(*) FROM external_articles").fetchone()[0] == 2


def test_later_literal_witness_not_first_anchor_or_limited_hit(admitted_source_probe):
    if admitted_source_probe[3] == "gec":
        # UA-GEC binds its mapped record, rather than arbitrarily changing record identity.
        _insert_witness(admitted_source_probe)
        assert _query_source(admitted_source_probe)["binding"]["row_id"] == 12
        return
    for row_id in range(1, 151):
        _insert_witness(admitted_source_probe, "fixture unrelated body", row_id=row_id)
    _insert_witness(admitted_source_probe, row_id=151)
    assert str(_query_source(admitted_source_probe)["binding"]["row_id"]).endswith("151")


def test_dictionary_later_homonym_and_definition_field_positive(dictionary_probe):
    sources, _, _ = dictionary_probe
    sources.execute(
        "INSERT INTO sum20_articles VALUES (1, 'FIXTURE', 'fixture', 'fixture unrelated body', '', 'https://sum20ua.com/?wordid=1', '')"
    )
    sources.execute(
        "INSERT INTO sum20_articles VALUES (2, 'FIXTURE', 'fixture', 'fixture other body', 'literal synthetic passage', 'https://sum20ua.com/?wordid=2', '')"
    )
    binding = _query_dictionary(dictionary_probe)["binding"]
    assert binding["row_id"] == 2 and binding["text_field"] == "definition_text"


@pytest.mark.parametrize(
    "table,column",
    [
        ("textbooks", "author_uk"),
        ("external_articles", "channel_id"),
        ("style_guide", "source"),
        ("pravopys_paragraphs", "locator"),
        ("ua_gec_errors", "doc_id"),
    ],
)
@pytest.mark.parametrize("defect", ["table", "column"])
def test_all_required_source_contract_faults_abort_check(monkeypatch, tmp_path, table, column, defect):
    with sqlite3.connect(tmp_path / "sources.db") as conn:
        _healthy_source_schema(conn)
        if defect == "table":
            conn.execute(f"DROP TABLE {table}")
        else:
            conn.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
    sqlite3.connect(tmp_path / "vesum.db").close()
    monkeypatch.setattr(builder, "_resolve_db_path", lambda name, root: tmp_path / name)
    with pytest.raises(sqlite3.OperationalError, match=r"no such (table|column)"):
        builder.main(["--check"])


@pytest.mark.parametrize("missing", ["textbooks", "textbooks_fts"])
def test_n2_cli_independent_missing_textbook_or_fts_contract(monkeypatch, tmp_path, missing):
    # Independently constructed CLI store, without the shared schema fixture.
    with sqlite3.connect(tmp_path / "sources.db") as conn:
        conn.executescript("""
            CREATE TABLE sum20_articles (id, headword, normalized_lookup_key, article_text, definition_text, official_url);
            CREATE TABLE ulif_dictua_entries (id, canonical_headword, normalized_query, sense_gloss);
            CREATE TABLE external_articles (id, title, text, speaker, source_file, channel_id, domain, decolonization_tag);
            CREATE TABLE ua_gec_errors (id, error, correct, error_type, doc_id);
            CREATE TABLE style_guide (id, word, section, source, text, excerpt_full, page);
            CREATE TABLE pravopys_paragraphs (source_id, number, text, text_sha256, locator);
        """)
        if missing != "textbooks":
            conn.execute("CREATE TABLE textbooks (id, title, text, author, author_uk, source_file)")
        if missing != "textbooks_fts":
            conn.execute("CREATE VIRTUAL TABLE textbooks_fts USING fts5(title,text)")
    sqlite3.connect(tmp_path / "vesum.db").close()
    monkeypatch.setattr(builder, "_resolve_db_path", lambda name, root: tmp_path / name)
    with pytest.raises(sqlite3.OperationalError, match=f"no such table: {missing}"):
        builder.main(["--check"])


def test_pravopys_text_digest_fault_aborts(monkeypatch):
    with sqlite3.connect(":memory:") as conn:
        _healthy_source_schema(conn)
        conn.execute(
            "INSERT INTO pravopys_paragraphs VALUES ('pravopys_2019_official',12,'literal synthetic passage','wrong','§12')"
        )
        with pytest.raises(ValueError, match="Source text digest mismatch"):
            builder._bind_admitted_passage(
                "synthetic",
                {
                    "authority": "Український правопис (2019)",
                    "source": "Український правопис (2019)",
                    "supporting_passage": PASSAGE,
                },
                conn.cursor(),
            )


def test_existing_malformed_optional_cache_aborts_even_with_live_dictionary_hit(dictionary_probe):
    sources, _, _ = dictionary_probe
    sources.execute(
        "INSERT INTO sum20_articles VALUES (12,'FIXTURE','fixture','literal synthetic passage','','https://sum20ua.com/?wordid=12','')"
    )
    sources.execute("CREATE TABLE slovnyk_me_entries (id INTEGER, text TEXT)")
    with pytest.raises(sqlite3.OperationalError, match="no such column: source_url"):
        _query_dictionary(dictionary_probe)


@pytest.mark.parametrize("fault", ["missing_locator", "wrong_source_id"])
def test_pravopys_locator_or_identity_cannot_be_promoted(monkeypatch, fault):
    with sqlite3.connect(":memory:") as conn:
        _healthy_source_schema(conn)
        source_id = "unknown-edition" if fault == "wrong_source_id" else "pravopys_2019_official"
        locator = "" if fault == "missing_locator" else "§12"
        conn.execute(
            "INSERT INTO pravopys_paragraphs VALUES (?,12,?,?,?)",
            (source_id, PASSAGE, hashlib.sha256(PASSAGE.encode()).hexdigest(), locator),
        )
        evidence = {
            "authority": "Український правопис (2019)",
            "source": "Український правопис (2019)",
            "supporting_passage": PASSAGE,
        }
        if fault == "missing_locator":
            with pytest.raises(ValueError, match="Missing admitted Pravopys locator"):
                builder._bind_admitted_passage("synthetic", evidence, conn.cursor())
        else:
            with pytest.raises(builder.SourceEvidenceUnavailable) as error:
                builder._bind_admitted_passage("synthetic", evidence, conn.cursor())
            assert error.value.reason_code == "held_source_missing"


@pytest.mark.parametrize("family", ["external", "style", "textbook", "gec", "pravopys"])
def test_required_query_failure_cannot_become_healthy_absence(monkeypatch, family):
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        _healthy_source_schema(sources)
        builder.validate_source_schema(sources.cursor())
        tables = {
            "external": "external_articles",
            "style": "style_guide",
            "textbook": "textbooks",
            "gec": "ua_gec_errors",
            "pravopys": "pravopys_paragraphs",
        }
        auth = {
            "external": PONOMARIV,
            "style": ANTONENKO,
            "textbook": PONOMARIV,
            "gec": "UA-GEC (Syvokon et al., 2023)",
            "pravopys": "Український правопис (2019)",
        }[family]
        ev = {
            "authority": auth,
            "source": auth,
            "target_term": "fixture",
            "supporting_passage": PASSAGE,
            "locus": "synthetic",
        }
        monkeypatch.setattr(builder, "EXPLICIT_SOURCE_EVIDENCE", {"synthetic": ev})
        monkeypatch.setattr(builder, "UA_GEC_RECORD_MAP", {"synthetic": 12})
        vesum.execute("CREATE TABLE forms_all (lemma,word_form,pos,tags,source_location)")
        vesum.execute("INSERT INTO forms_all VALUES ('fixture','fixture','noun','','synthetic')")

        def deny(action, arg1, arg2, database, trigger):
            return (
                sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and arg1 == tables[family] else sqlite3.SQLITE_OK
            )

        sources.set_authorizer(deny)
        with pytest.raises(sqlite3.DatabaseError, match="prohibited"):
            builder.query_source_evidence(
                "synthetic", "fixture", "", auth, "synthetic", sources.cursor(), vesum.cursor(), []
            )


@pytest.fixture
def reviewed_synthetic_case(monkeypatch, tmp_path):
    item = {
        "case_id": "synthetic",
        "target_term": "fixture",
        "russian_copy": "",
        "ukrainian_proper": ["fixture"],
        "authority": PONOMARIV,
        "is_erroneous": False,
        "contexts": ["fixture context"],
        "split": "train",
    }
    evidence = {
        "source": PONOMARIV,
        "authority": PONOMARIV,
        "target_term": "fixture",
        "supporting_passage": PASSAGE,
        "locus": "synthetic locus",
    }
    # Independent expected payload, not compute_case_content_sha256 or builder output.
    payload = {
        "case_id": "synthetic",
        "category": "synthetic",
        "is_erroneous": False,
        "target_term": "fixture",
        "russian_copy": "",
        "ukrainian_proper": ["fixture"],
        "authority": PONOMARIV,
        "contexts": ["fixture context"],
        "source_evidence": {
            "source": PONOMARIV,
            "locus": "synthetic locus",
            "supporting_passage": PASSAGE,
            "page": None,
            "article": None,
            "section": None,
        },
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    review = {
        "review_receipt_id": "REV-synthetic",
        "review_dossier_locator": "data/projects/open_model_data/components/decolonization/reviews/synthetic.review.json",
        "reviewer_id": "claude_blue_team_ling_review",
        "reviewer_family": "claude",
        "status": "confirmed",
        "verdict": "APPROVED",
        "category": "synthetic",
        "is_erroneous": False,
        "target_term": "fixture",
        "russian_copy": "",
        "authority": PONOMARIV,
        "supporting_passage": PASSAGE,
        "authority_locus": "synthetic locus",
        "content_sha256": digest,
    }
    dossier = dict(review)
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews/synthetic.review.json").write_text(json.dumps(dossier))
    signoff = {
        "reviewer_id": "claude_blue_team_ling_review",
        "reviewer_family": "claude",
        "sample_size_drawn": 1,
        "sample_size_reviewed": 1,
        "blocker_defect_count": 0,
        "minor_defect_count": 0,
        "dataset_sha256": "1" * 64,
        "profile_sha256": "2" * 64,
        "signoff_date": "2026-09-22",
    }
    (tmp_path / "acceptance_review_sample.signoff.json").write_text(json.dumps(signoff))
    monkeypatch.setattr(builder, "REGISTRY_DECOLONIZATION_DIR", tmp_path)
    monkeypatch.setattr(builder, "EXPLICIT_SOURCE_EVIDENCE", {"synthetic": evidence})
    monkeypatch.setattr(builder, "INDEPENDENT_LANGUAGE_REVIEWS", {"synthetic": review})
    with sqlite3.connect(":memory:") as sources, sqlite3.connect(":memory:") as vesum:
        _healthy_source_schema(sources)
        vesum.execute("CREATE TABLE forms_all (lemma,word_form,pos,tags,source_location)")
        vesum.execute("INSERT INTO forms_all VALUES ('fixture','fixture','noun','','synthetic')")
        yield item, evidence, review, dossier, tmp_path, sources.cursor(), vesum.cursor()


@pytest.mark.parametrize(
    "fault",
    [
        "valid_unavailable",
        "review_rejected",
        "dossier_rejected",
        "changed_receipt",
        "changed_passage",
        "changed_locus",
        "changed_source",
        "changed_context",
        "review_digest",
        "dossier_digest",
    ],
)
def test_unavailable_source_never_hides_review_or_dossier_integrity(reviewed_synthetic_case, fault):
    item, evidence, review, dossier, path, sources, vesum = reviewed_synthetic_case
    if fault == "review_rejected":
        review["verdict"] = "REJECTED"
    if fault == "dossier_rejected":
        dossier["verdict"] = "REJECTED"
    if fault == "changed_receipt":
        dossier["review_receipt_id"] = "changed"
    if fault == "changed_passage":
        evidence["supporting_passage"] = "changed"
    if fault == "changed_locus":
        evidence["locus"] = "changed"
    if fault == "changed_source":
        evidence["source"] = "changed"
    if fault == "changed_context":
        item["contexts"] = ["changed"]
    if fault == "review_digest":
        review["content_sha256"] = "0" * 64
    if fault == "dossier_digest":
        dossier["content_sha256"] = "0" * 64
    (path / "reviews/synthetic.review.json").write_text(json.dumps(dossier))
    if fault == "valid_unavailable":
        with pytest.raises(builder.SourceEvidenceUnavailable) as error:
            builder.make_reviewer_confirmation(item, "synthetic", vesum, sources, [])
        assert error.value.reason_code == "held_source_missing"
    else:
        with pytest.raises(ValueError) as error:
            builder.make_reviewer_confirmation(item, "synthetic", vesum, sources, [])
        assert not isinstance(error.value, builder.SourceEvidenceUnavailable)


def test_pinned_book_source_with_contradictory_author_withholds(monkeypatch):
    with sqlite3.connect(":memory:") as conn:
        _healthy_source_schema(conn)
        conn.execute(
            "INSERT INTO textbooks VALUES (12,'arbitrary title','literal synthetic passage','other author','other author','antonenko-davydovych-yak-my-hovorymo')"
        )
        with pytest.raises(builder.SourceEvidenceUnavailable):
            builder._bind_admitted_passage(
                "synthetic", {"authority": ANTONENKO, "source": ANTONENKO, "supporting_passage": PASSAGE}, conn.cursor()
            )


def test_exact_cited_book_metadata_binds_without_body_author_guess(monkeypatch):
    with sqlite3.connect(":memory:") as conn:
        _healthy_source_schema(conn)
        conn.execute(
            "INSERT INTO textbooks VALUES (12,'Культура слова','literal synthetic passage','Олександр Пономарів','Олександр Пономарів','synthetic-admitted-book')"
        )
        binding = builder._bind_admitted_passage(
            "synthetic", {"authority": PONOMARIV, "source": PONOMARIV, "supporting_passage": PASSAGE}, conn.cursor()
        )
        assert binding["locator"] == "textbooks:12"
        assert binding["source_provenance"]["source"] == PONOMARIV


def test_literal_without_resolving_row_identity_is_integrity_failure():
    with pytest.raises(ValueError, match="Missing resolving source row identity"):
        builder._literal_binding(PASSAGE, "style_guide", None, "text", PASSAGE, {"source": ANTONENKO})


def test_malformed_official_url_cannot_authenticate_literal_dictionary(dictionary_probe):
    sources, _, _ = dictionary_probe
    sources.execute(
        "INSERT INTO sum20_articles VALUES (12,'FIXTURE','fixture','literal synthetic passage','','https://[invalid','')"
    )
    with pytest.raises(builder.SourceEvidenceUnavailable) as error:
        _query_dictionary(dictionary_probe)
    assert error.value.reason_code == "held_source_unproven"
