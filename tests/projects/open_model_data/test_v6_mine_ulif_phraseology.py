"""test_v6_mine_ulif_phraseology.py - Test suite for Phase 6.2 NASU ULIF Phraseology Engine.

Verifies:
1. 0% train/eval leakage firewall: strictly held-out classical authors and calques.
2. Canonical calque catalog: authentic Ukrainian mechanisms, non-empty replacements, and flaw classification.
3. Multi-turn instructional reasoning trajectory synthesis: <thought> trace formatting and pedagogical tone.
4. Contrastive DPO pair generation: valid schema, non-trivial prompt, chosen, and rejected texts.
5. Draft 2020-12 JSON Schema validation for held-out evaluation records and release receipts.
6. Shard formatting, manifest consistency, and size ceiling (< 2,000 KB per shard).
7. Live extraction from ULIF (data/ulif_dump_all.db) and sources (frazeolohichnyi) when present.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v6_mine_ulif_phraseology import (
    CANONICAL_CALQUE_PAIRS,
    DEFAULT_SOURCES_DB,
    DEFAULT_ULIF_DB,
    HELD_OUT_AUTHORS,
    SCHEMA_EVAL_PATH,
    SCHEMA_RECEIPT_PATH,
    CalquePair,
    PhraseologyUnit,
    SynonymGroup,
    clean_raw_html_and_tags,
    clean_stress_marks,
    extract_classical_author,
    generate_dpo_dataset,
    generate_evaluation_benchmark,
    generate_release_receipt,
    generate_sft_dataset,
    is_author_held_out,
    load_frazeolohichnyi_dictionary,
    load_ulif_phraseology_and_synonyms,
    synthesize_sft_trajectory,
)


def _has_ulif() -> bool:
    if not DEFAULT_ULIF_DB.is_file() or DEFAULT_ULIF_DB.stat().st_size < 1_000_000:
        return False
    try:
        with sqlite3.connect(f"file:{DEFAULT_ULIF_DB}?mode=ro", uri=True) as conn:
            r = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name='ulif_entries'").fetchone()
            return r is not None
    except Exception:
        return False


def _has_sources() -> bool:
    if not DEFAULT_SOURCES_DB.is_file() or DEFAULT_SOURCES_DB.stat().st_size < 1_000_000:
        return False
    try:
        with sqlite3.connect(f"file:{DEFAULT_SOURCES_DB}?mode=ro", uri=True) as conn:
            r = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name='frazeolohichnyi'").fetchone()
            return r is not None
    except Exception:
        return False


requires_ulif = pytest.mark.skipif(not _has_ulif(), reason="data/ulif_dump_all.db missing or empty")
requires_sources = pytest.mark.skipif(not _has_sources(), reason="data/sources.db missing or empty")


# =========================================================================
# 1. Linguistic Normalization & Text Cleaning Tests
# =========================================================================

def test_clean_stress_marks():
    raw = "б[']і[/']лий (Б[']о[/']жий) світ, нар.-поет."
    cleaned = clean_stress_marks(raw)
    assert "[']" not in cleaned
    assert "[/']" not in cleaned
    assert cleaned == "білий (Божий) світ, нар.-поет."


def test_clean_raw_html_and_tags():
    raw = "<ID>1</ID>|<fna>Робінзон</fna>|{{</fras>}} ≤щось≥ [інше]"
    cleaned = clean_raw_html_and_tags(raw)
    assert "<ID>" not in cleaned
    assert "</fras>" not in cleaned
    assert "≤" not in cleaned
    assert "≥" not in cleaned
    assert cleaned == "Робінзон| щось інше" or "Робінзон" in cleaned


def test_extract_classical_author():
    text = "Я ходив скаржитись на Лисицю (І. Нечуй-Левицький); — Сказали (З газети)."
    auth = extract_classical_author(text)
    assert auth == "І. Нечуй-Левицький"


def test_is_author_held_out():
    assert is_author_held_out("О. Гончар") is True
    assert is_author_held_out("М. Стельмах") is True
    assert is_author_held_out("Ю. Яновський") is True
    assert is_author_held_out("А. Дімаров") is True
    assert is_author_held_out("І. Франко") is False
    assert is_author_held_out("Леся Українка") is False


# =========================================================================
# 2. Canonical Anti-Calque Catalog Invariants
# =========================================================================

def test_canonical_calque_catalog_integrity():
    assert len(CANONICAL_CALQUE_PAIRS) >= 25
    calque_set = set()
    valid_flaws = {
        "soviet_lexicography_acceptance",
        "lack_of_morphemic_reasoning",
        "mechanical_wordnet_synset",
        "unvetted_purism_hallucination",
    }
    held_out_count = 0
    for cp in CANONICAL_CALQUE_PAIRS:
        assert len(cp.calque) > 2
        assert len(cp.authentic) > 2
        assert len(cp.mechanism) >= 15
        assert cp.rejected_flaw in valid_flaws
        assert cp.calque not in calque_set, f"Duplicate calque: {cp.calque}"
        calque_set.add(cp.calque)
        if cp.is_held_out:
            held_out_count += 1
    assert held_out_count >= 3, "Must have at least 3 dedicated held-out calque pairs"


# =========================================================================
# 3. Trajectory & SFT Synthesis Tests
# =========================================================================

def test_synthesize_sft_trajectory_anti_calque():
    cp = CalquePair(
        calque="приймати участь",
        authentic="брати участь",
        mechanism="Дієслово приймати позначає фізичний захват або зарахування; абстрактна співдія — брати участь.",
        author_or_source="Б. Антоненко-Давидович «Як ми говоримо»",
        rejected_flaw="lack_of_morphemic_reasoning",
    )
    traj = synthesize_sft_trajectory(None, cp, None, 1, "anti_calque_decolonization")
    assert traj["schema_version"] == "v1_ulif_phraseology_trajectory"
    assert traj["task_type"] == "anti_calque_decolonization"
    assert "приймати участь" in traj["query"]
    assert "<thought>" in traj["final_response"]
    assert "</thought>" in traj["final_response"]
    assert "брати участь" in traj["final_response"]


def test_synthesize_sft_trajectory_synonyms():
    sg = SynonymGroup(
        headword="балакати",
        synonyms=["говорити", "розмовляти", "бесідувати", "гуторити"],
        source_dict="ulif_nasu",
    )
    traj = synthesize_sft_trajectory(None, None, sg, 2, "synonymic_nuance_and_register")
    assert traj["task_type"] == "synonymic_nuance_and_register"
    assert "балакати" in traj["query"]
    assert "<thought>" in traj["final_response"]
    assert "говорити" in traj["final_response"]


def test_synthesize_sft_trajectory_idiom_interpretation():
    u = PhraseologyUnit(
        headword="рука",
        idiom="гріти руки",
        definition="Наживатися у нечесний спосіб.",
        citation_text="Він на цьому добре погрів руки (І. Франко).",
        author="І. Франко",
        source_dict="frazeolohichnyi_slovnyk",
        is_held_out=False,
    )
    traj = synthesize_sft_trajectory(u, None, None, 3, "idiom_interpretation_literary")
    assert traj["task_type"] == "idiom_interpretation_literary"
    assert "гріти руки" in traj["query"]
    assert "<thought>" in traj["final_response"]
    assert "Наживатися у нечесний спосіб" in traj["final_response"]


# =========================================================================
# 4. Evaluation Benchmark Schema & 0% Leakage Tests
# =========================================================================

def test_generate_evaluation_benchmark_and_schema_validation():
    schema = json.loads(SCHEMA_EVAL_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    eval_units = [
        PhraseologyUnit(
            headword="гору",
            idiom="брати гору",
            definition="Отримувати вирішальну перевагу чи перемогу.",
            citation_text="Наша правда брала гору у важких боях (О. Гончар).",
            author="О. Гончар",
            source_dict="ulif_nasu",
            is_held_out=True,
        )
    ]
    eval_calques = [cp for cp in CANONICAL_CALQUE_PAIRS if cp.is_held_out]

    with tempfile.TemporaryDirectory() as tmpdir:
        eval_dir = Path(tmpdir) / "eval"
        meta, _sha, _counts, _authors = generate_evaluation_benchmark(
            eval_units=eval_units,
            eval_calques=eval_calques,
            output_path=eval_dir,
            target_count=10,
        )
        assert (eval_dir / "manifest_eval.json").exists()
        assert meta["total_cases"] == 10

        shard_files = list(eval_dir.glob("eval_shard_*.jsonl"))
        assert len(shard_files) >= 1
        for sf in shard_files:
            with sf.open("r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    validator.validate(record)
                    assert record["source_metadata"]["partition"] == "held_out_eval"


def test_zero_train_eval_leakage_firewall():
    eval_calques = [cp for cp in CANONICAL_CALQUE_PAIRS if cp.is_held_out]
    train_calques = [cp for cp in CANONICAL_CALQUE_PAIRS if not cp.is_held_out]

    eval_calque_names = {cp.calque for cp in eval_calques}
    train_calque_names = {cp.calque for cp in train_calques}

    intersection = eval_calque_names.intersection(train_calque_names)
    assert not intersection, f"Train/Eval calque leakage detected: {intersection}"

    for hoa in HELD_OUT_AUTHORS:
        for tc in train_calques:
            assert hoa not in tc.author_or_source, f"Held-out author {hoa} leaked in train calque {tc.calque}"


# =========================================================================
# 5. Sharding and Ceiling Invariants Tests
# =========================================================================

def test_sft_sharding_ceiling():
    units = [
        PhraseologyUnit("гору", "брати гору", "перемагати", "І. Франко", "І. Франко", "ulif", False),
    ]
    calques = [cp for cp in CANONICAL_CALQUE_PAIRS if not cp.is_held_out]
    synonyms = [SynonymGroup("сміливий", ["відважний", "хоробрий", "мужній"], "ulif")]

    with tempfile.TemporaryDirectory() as tmpdir:
        sft_dir = Path(tmpdir) / "sft"
        manifest, _sha, _tasks = generate_sft_dataset(
            units=units,
            calques=calques,
            synonyms=synonyms,
            output_dir=sft_dir,
            target_count=20,
            shards_count=2,
            trajectories_per_shard=10,
        )
        assert sft_dir.exists()
        assert manifest["total_trajectories"] == 20
        assert manifest["shards_count"] == 2
        assert manifest["max_shard_size_kb"] < 2000.0


def test_dpo_sharding_ceiling():
    calques = [cp for cp in CANONICAL_CALQUE_PAIRS if not cp.is_held_out]
    units = [PhraseologyUnit("гору", "брати гору", "перемагати", "І. Франко", "І. Франко", "ulif", False)]

    with tempfile.TemporaryDirectory() as tmpdir:
        dpo_dir = Path(tmpdir) / "dpo"
        manifest, _sha, _flaws = generate_dpo_dataset(
            calques=calques,
            units=units,
            output_dir=dpo_dir,
            target_count=20,
            shards_count=2,
            pairs_per_shard=10,
        )
        assert dpo_dir.exists()
        assert manifest["total_pairs"] == 20
        assert manifest["shards_count"] == 2
        assert manifest["max_shard_size_kb"] < 2000.0


# =========================================================================
# 6. Release Receipt Schema Validation Test
# =========================================================================

def test_release_receipt_schema_validation():
    schema = json.loads(SCHEMA_RECEIPT_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        sft_man_path = td / "manifest_sft.json"
        sft_man_data = {
            "dataset_name": "uldr_v06_ulif_phraseology_sft",
            "total_trajectories": 45000,
            "shards_count": 90,
            "max_shard_size_kb": 1050.0,
            "shards": [],
        }
        sft_man_path.write_text(json.dumps(sft_man_data))

        dpo_man_path = td / "manifest_dpo.json"
        dpo_man_data = {
            "dataset_name": "uldr_v06_ulif_phraseology_dpo",
            "total_pairs": 20000,
            "shards_count": 40,
            "max_shard_size_kb": 950.0,
            "shards": [],
        }
        dpo_man_path.write_text(json.dumps(dpo_man_data))

        eval_meta = {
            "directory_path": str(td / "eval"),
            "manifest_file": str(td / "eval" / "manifest_eval.json"),
            "manifest_sha256": "0" * 64,
            "shards_count": 3,
            "total_cases": 1500,
            "max_shard_size_kb": 1100.0,
            "held_out_categories": {"anti_calque_decolonization": 3, "authentic_idiom_usage": 1497},
            "held_out_authors_count": 4,
            "held_out_authors": HELD_OUT_AUTHORS,
        }

        receipt = generate_release_receipt(
            eval_meta=eval_meta,
            sft_manifest_path=sft_man_path,
            sft_manifest_sha256="1" * 64,
            sft_task_dist={"anti_calque_decolonization": 15000, "idiom_interpretation_literary": 15000, "synonymic_nuance_and_register": 10000, "contextual_dialogue_usage": 5000},
            dpo_manifest_path=dpo_man_path,
            dpo_manifest_sha256="2" * 64,
            dpo_flaw_dist={"lack_of_morphemic_reasoning": 15000, "soviet_lexicography_acceptance": 5000},
            output_dir=td,
        )

        validator.validate(receipt)
        assert receipt["schema_version"] == "v1_ulif_phraseology_release_receipt"
        assert receipt["issue"] == 8140
        assert receipt["parent_epic"] == 6321
        assert receipt["invariants_verified"]["zero_train_eval_leakage"] is True


# =========================================================================
# 7. Live Database Integration Tests (Conditional)
# =========================================================================

@requires_ulif
def test_live_ulif_extraction():
    units, syns = load_ulif_phraseology_and_synonyms(DEFAULT_ULIF_DB)
    assert len(units) > 100
    assert len(syns) > 1000


@requires_sources
def test_live_frazeolohichnyi_extraction():
    units = load_frazeolohichnyi_dictionary(DEFAULT_SOURCES_DB)
    assert len(units) > 20000
