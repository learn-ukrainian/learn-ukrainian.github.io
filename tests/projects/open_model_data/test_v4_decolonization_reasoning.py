"""Unit tests for the ULDR automated decolonization generator pipeline (#7922)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_decolonization_reasoning import (
    CalqueCandidate,
    classify_calque_type,
    compute_id,
    find_dictionary_attestation,
    find_textbook_attestation,
    generate_pipeline,
    normalize_text,
    scan_generated_files,
    strip_accents,
    synthesize_trajectory_and_dpo,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"


@pytest.fixture(scope="module")
def trajectory_schema() -> dict[str, Any]:
    schema_path = CONTRACTS_DIR / "v1_decolonization_trajectory.schema.json"
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def dpo_pair_schema() -> dict[str, Any]:
    schema_path = CONTRACTS_DIR / "v1_decolonization_dpo_pair.schema.json"
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


def test_classify_calque_type() -> None:
    cat, src, _ = classify_calque_type("бажаючий")
    assert cat == "active_participle"
    assert "активного дієприкметника" in src

    cat, src, _ = classify_calque_type("обезболюючий")
    assert cat in ("active_participle", "prefixal_calque")

    cat, src, _ = classify_calque_type("обеззброїти")
    assert cat == "prefixal_calque"
    assert "обез-" in src

    cat, src, _ = classify_calque_type("сопоставити")
    assert cat == "prefixal_calque"
    assert "со-" in src

    cat, src, _ = classify_calque_type("в першу чергу")
    assert cat == "phrasal_calque"
    assert "послівного перекладу" in src

    cat, src, _ = classify_calque_type("холостяк")
    assert cat == "lexical_calque"
    assert "росіянізмом" in src


def test_normalize_and_accents() -> None:
    raw = " «пилотя́г»! "
    assert normalize_text(raw) == "пилотяг"
    assert strip_accents("приймати́ у́часть") == "приймати участь"


def test_compute_id_deterministic() -> None:
    id1 = compute_id("traj", "Пилосос")
    id2 = compute_id("traj", "пилосос ")
    assert id1 == id2
    assert id1.startswith("traj.decolonize.")


def test_find_textbook_attestation_denies_restricted_sources(tmp_path: Path) -> None:
    db_path = tmp_path / "test_sources.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE textbooks (title TEXT, grade TEXT, subject TEXT, author TEXT, text TEXT, source_file TEXT)"
    )
    # Restricted source 1: ULP podcast (grade blank)
    cur.execute(
        "INSERT INTO textbooks VALUES ('ULP Ep 1', '', 'lexicon', 'Ukrainian Lessons Podcast', 'Цікаве завдання на уроці.', 'ulp-1-01-lesson-notes')"
    )
    # Restricted source 2: Ohoiko vocabulary (grade blank)
    cur.execute(
        "INSERT INTO textbooks VALUES ('500 Verbs', '', 'lexicon', 'Anna Ohoiko', 'Виконувати завдання щодня.', 'anna-ohoiko-500-verbs')"
    )
    # Restricted source 3: University chunk (non-school grade)
    cur.execute(
        "INSERT INTO textbooks VALUES ('Університет', 'university', 'ling', 'ДонНУ', 'Практичне завдання курсу.', 'donnu-ling-2023')"
    )
    # Genuine school textbook: Grade 7
    cur.execute(
        "INSERT INTO textbooks VALUES ('Українська мова', '7', 'ukrmova', 'avramenko', 'Виконуємо тренувальне завдання.', '7-klas-ukrmova-avramenko-2024')"
    )
    conn.commit()
    conn.close()

    res = find_textbook_attestation("завдання", db_path)
    assert res is not None
    # Must match the genuine school textbook, NOT ULP, Ohoiko, or University
    assert res["grade"] == 7
    assert res["subject"] == "Українська мова"
    assert res["author"] == "О. Авраменко"
    assert "ulp-" not in res["source_file"]
    assert "ohoiko" not in res["source_file"]


def test_find_dictionary_attestation(tmp_path: Path) -> None:
    db_path = tmp_path / "test_dict.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE grinchenko (word TEXT)")
    cur.execute("CREATE TABLE sum11 (word TEXT)")
    cur.execute("INSERT INTO grinchenko VALUES ('охочий')")
    cur.execute("INSERT INTO sum11 VALUES ('холостяк')")
    conn.commit()
    conn.close()

    res_g = find_dictionary_attestation("охочий", db_path)
    assert res_g is not None
    assert "Грінченка" in res_g

    res_s = find_dictionary_attestation("холостяк", db_path)
    assert res_s is not None
    assert "СУМ-11" in res_s

    res_none = find_dictionary_attestation("вигаданеслово", db_path)
    assert res_none is None


def test_synthesize_trajectory_and_dpo(
    trajectory_schema: dict[str, Any],
    dpo_pair_schema: dict[str, Any],
) -> None:
    candidate = CalqueCandidate(
        target_term="пилосос",
        suggestions=["пилосмок", "порохотяг", "вакуум"],
        source_tag="curated_calques",
        curated_evidence=["Пометун 9 клас Всесвітня історія с. 166"],
    )
    vesum_counts = {"пилосмок": 12, "порохотяг": 8, "вакуум": 0}
    tb_attestations = {
        "пилосмок": {
            "title": "Всесвітня історія 9 клас",
            "grade": 9,
            "subject": "Всесвітня історія",
            "author": "О. Пометун",
            "snippet": "Перша модель пилосмока, запатентована в 1908 р.",
            "source_file": "9-klas-vsesvitnia-istoriia-pometun-2026",
        },
        "порохотяг": None,
    }
    dict_attestations = {
        "пилосмок": None,
        "порохотяг": None,
    }

    result = synthesize_trajectory_and_dpo(candidate, vesum_counts, tb_attestations, dict_attestations)
    assert result is not None
    trajectory, dpo_pair = result

    # Validate against schemas
    traj_validator = jsonschema.Draft202012Validator(trajectory_schema)
    dpo_validator = jsonschema.Draft202012Validator(dpo_pair_schema)

    errors = list(traj_validator.iter_errors(trajectory))
    assert not errors, f"Trajectory schema error: {[e.message for e in errors]}"

    errors = list(dpo_validator.iter_errors(dpo_pair))
    assert not errors, f"DPO schema error: {[e.message for e in errors]}"

    # Verify no fabricated dictionary claims (e.g. SUM-20 / VTS)
    traj_str = json.dumps(trajectory, ensure_ascii=False)
    assert "СУМ-20" not in traj_str
    assert "ВТС" not in traj_str

    # Verify register_spectrum alternatives are a subset of vesum_attestation
    vesum_lemmas = {v["lemma"] for v in trajectory["vesum_attestation"]}
    for alt in trajectory["register_spectrum"]["alternatives"]:
        assert alt["lemma"] in vesum_lemmas

    # Verify purist neologism tier for 0-form entry
    purist_alts = [
        alt for alt in trajectory["register_spectrum"]["alternatives"] if alt["register_tier"] == "purist_neologism"
    ]
    assert len(purist_alts) == 1
    assert purist_alts[0]["lemma"] == "вакуум"


def test_scan_generated_files_detects_violations(tmp_path: Path) -> None:
    clean_file = tmp_path / "clean.jsonl"
    clean_file.write_text('{"query": "Як правильно?", "text": "Добрий день."}\n', encoding="utf-8")

    zero_p, zero_r, viols = scan_generated_files([clean_file])
    assert zero_p is True
    assert zero_r is True
    assert len(viols) == 0

    # Leak test 1: Private host path
    leak_path_file = tmp_path / "leak_path.jsonl"
    leak_path_file.write_text('{"path": "/home/ops/secret/data.txt"}\n', encoding="utf-8")

    zero_p, zero_r, viols = scan_generated_files([leak_path_file])
    assert zero_p is False
    assert len(viols) > 0

    # Leak test 2: Restricted source leak
    leak_source_file = tmp_path / "leak_source.jsonl"
    leak_source_file.write_text('{"source": "ulp-1-01-lesson-notes"}\n', encoding="utf-8")

    zero_p, zero_r, viols = scan_generated_files([leak_source_file])
    assert zero_r is False
    assert len(viols) > 0


def test_generate_pipeline_mock(
    tmp_path: Path,
    trajectory_schema: dict[str, Any],
    dpo_pair_schema: dict[str, Any],
) -> None:
    mock_lt = tmp_path / "mock_lt.json"
    mock_lt.write_text(
        json.dumps(
            {
                "автовишка": {"suggestions": ["автовежа"]},
                "бажаючий": {"suggestions": ["охочий"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    mock_sources_db = tmp_path / "mock_sources.db"
    conn = sqlite3.connect(mock_sources_db)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE textbooks (title TEXT, grade TEXT, subject TEXT, author TEXT, text TEXT, source_file TEXT)"
    )
    cur.execute(
        "INSERT INTO textbooks VALUES ('Українська мова', '7', 'ukrmova', 'avramenko', 'Охочий до праці учень.', '7-klas-ukrmova-avramenko-2024')"
    )
    cur.execute("CREATE TABLE ua_gec_errors (error TEXT, correct TEXT, error_type TEXT, is_native INTEGER)")
    cur.execute("CREATE TABLE grinchenko (word TEXT)")
    cur.execute("CREATE TABLE sum11 (word TEXT)")
    conn.commit()
    conn.close()

    mock_vesum_db = tmp_path / "mock_vesum.db"
    conn = sqlite3.connect(mock_vesum_db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE forms (lemma TEXT, form TEXT)")
    cur.execute("INSERT INTO forms VALUES ('автовежа', 'автовежі')")
    cur.execute("INSERT INTO forms VALUES ('охочий', 'охочого')")
    conn.commit()
    conn.close()

    out_dir = tmp_path / "generated"

    manifest = generate_pipeline(
        lt_replacements_path=mock_lt,
        sources_db_path=mock_sources_db,
        vesum_db_path=mock_vesum_db,
        out_dir=out_dir,
        limit=5,
        records_per_shard=2,
        verify_schema=True,
    )

    assert manifest["total_trajectories"] >= 2
    assert manifest["total_dpo_pairs"] >= 2
    assert manifest["quality_metrics"]["vesum_verification_rate"] == 1.0
    assert manifest["quality_metrics"]["zero_private_paths"] is True
    assert manifest["quality_metrics"]["zero_restricted_sources"] is True
    assert (out_dir / "decolonization_manifest.json").is_file()

    shards = manifest["shards"]
    assert len(shards) >= 1
    for sh in shards:
        t_file = out_dir / sh["trajectories_file"]
        d_file = out_dir / sh["dpo_pairs_file"]
        assert t_file.is_file()
        assert d_file.is_file()
        assert t_file.stat().st_size < 2_000_000
        assert d_file.stat().st_size < 2_000_000

        t_content = t_file.read_text(encoding="utf-8")
        assert "/home/ops" not in t_content
        assert "/tmp/" not in t_content
        assert "ulp-" not in t_content
        assert "ohoiko" not in t_content
        assert "СУМ-20" not in t_content
        assert "ВТС" not in t_content
