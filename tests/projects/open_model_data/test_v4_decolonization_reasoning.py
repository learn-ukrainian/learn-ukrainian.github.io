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
    generate_pipeline,
    normalize_text,
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
        },
        "порохотяг": None,
    }

    result = synthesize_trajectory_and_dpo(candidate, vesum_counts, tb_attestations)
    assert result is not None
    trajectory, dpo_pair = result

    # Validate against schemas
    traj_validator = jsonschema.Draft202012Validator(trajectory_schema)
    dpo_validator = jsonschema.Draft202012Validator(dpo_pair_schema)

    errors = list(traj_validator.iter_errors(trajectory))
    assert not errors, f"Trajectory schema error: {[e.message for e in errors]}"

    errors = list(dpo_validator.iter_errors(dpo_pair))
    assert not errors, f"DPO schema error: {[e.message for e in errors]}"

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


def test_generate_pipeline_mock(
    tmp_path: Path,
    trajectory_schema: dict[str, Any],
    dpo_pair_schema: dict[str, Any],
) -> None:
    # Set up mock files
    mock_lt = tmp_path / "mock_lt.json"
    mock_lt.write_text(
        json.dumps({
            "автовишка": {"suggestions": ["автовежа"]},
            "бажаючий": {"suggestions": ["охочий"]},
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    mock_sources_db = tmp_path / "mock_sources.db"
    conn = sqlite3.connect(mock_sources_db)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE textbooks (title TEXT, grade INTEGER, subject TEXT, author TEXT, text TEXT)"
    )
    cur.execute(
        "INSERT INTO textbooks VALUES ('Українська мова', 7, 'Українська мова', 'О. Авраменко', 'Охочий до праці учень.')"
    )
    cur.execute(
        "CREATE TABLE ua_gec_errors (error TEXT, correct TEXT, error_type TEXT, is_native INTEGER)"
    )
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
    assert (out_dir / "decolonization_manifest.json").is_file()

    # Check that shards are created
    shards = manifest["shards"]
    assert len(shards) >= 1
    for sh in shards:
        t_file = out_dir / sh["trajectories_file"]
        d_file = out_dir / sh["dpo_pairs_file"]
        assert t_file.is_file()
        assert d_file.is_file()
        # Verify shard size well under 2,000 KB cap
        assert t_file.stat().st_size < 2_000_000
        assert d_file.stat().st_size < 2_000_000

        # Verify no private host paths
        t_content = t_file.read_text(encoding="utf-8")
        assert "/home/ops" not in t_content
        assert "/tmp/" not in t_content
