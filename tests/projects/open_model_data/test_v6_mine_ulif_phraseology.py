"""test_v6_mine_ulif_phraseology.py - Test suite for Phase 6.2 NASU ULIF Phraseology Engine.

Verifies:
1. 0% train/eval leakage firewall: strictly held-out classical authors and calques with case-sensitive word boundary matching.
2. Canonical calque catalog: authentic Ukrainian mechanisms, non-empty replacements, and flaw classification.
3. Multi-turn instructional reasoning trajectory synthesis: <thought> trace formatting and pedagogical tone.
4. Contrastive DPO pair generation: valid schema, non-trivial prompt, chosen, and rejected texts tailored to flaw.
5. Draft 2020-12 JSON Schema validation for held-out evaluation records and release receipts.
6. Shard formatting, manifest consistency, and size ceiling (< 2,000 KB per shard).
7. Zero leakage audit scanning actual generated shards on disk (author leakage & target phrase overlap).
8. Live extraction from ULIF (data/ulif_dump_all.db), sources (frazeolohichnyi, ua_gec_errors), and VESUM.
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
    DEFAULT_VESUM_DB,
    HELD_OUT_AUTHORS_DISPLAY,
    SCHEMA_EVAL_PATH,
    SCHEMA_RECEIPT_PATH,
    CalquePair,
    PhraseologyUnit,
    SynonymGroup,
    audit_zero_train_eval_leakage,
    clean_raw_html_and_tags,
    clean_stress_marks,
    extract_quote_for_author,
    generate_dpo_dataset,
    generate_evaluation_benchmark,
    generate_release_receipt,
    generate_sft_dataset,
    is_record_held_out,
    load_frazeolohichnyi_dictionary,
    load_ua_gec_calques,
    load_ulif_phraseology_and_synonyms,
    parse_frazeolohichnyi_entry,
    synthesize_sft_trajectory,
    verify_phrase_in_vesum,
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


def _has_vesum() -> bool:
    if not DEFAULT_VESUM_DB.is_file() or DEFAULT_VESUM_DB.stat().st_size < 1_000_000:
        return False
    try:
        with sqlite3.connect(f"file:{DEFAULT_VESUM_DB}?mode=ro", uri=True) as conn:
            r = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name='forms_all'").fetchone()
            return r is not None
    except Exception:
        return False


requires_ulif = pytest.mark.skipif(not _has_ulif(), reason="data/ulif_dump_all.db missing or empty")
requires_sources = pytest.mark.skipif(not _has_sources(), reason="data/sources.db missing or empty")
requires_vesum = pytest.mark.skipif(not _has_vesum(), reason="data/vesum.db missing or empty")


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
    assert "Робінзон" in cleaned


def test_extract_quote_for_author():
    text = "— Я ходив скаржитись на Лисицю (І. Нечуй-Левицький); Він засів у бліндажі і не виходив (О. Гончар); Інший приклад."
    quote = extract_quote_for_author(text, "О. Гончар")
    assert quote is not None
    assert "Він засів у бліндажі і не виходив" in quote


def test_parse_frazeolohichnyi_entry():
    raw_word = "блудити манівцями {{</fras>}}"
    raw_def = "блук[']а[/']ти манівц[']я[/']ми, розм. Робити щось не так, як треба. — Я вирішив так (О. Гончар)."
    unit = parse_frazeolohichnyi_entry(raw_word, raw_def)
    assert unit.idiom == "блудити манівцями"
    assert unit.register == "розмовний"
    assert "Робити щось не так, як треба" in unit.definition
    assert unit.is_held_out is True
    assert unit.author == "О. Гончар"


def test_is_record_held_out_word_boundaries():
    # Capitalized author names match
    assert is_record_held_out("Текст із твору (О. Гончар).") is True
    assert is_record_held_out("Тут згадується Гончар та його твори.") is True
    assert is_record_held_out("Повість (М. Стельмах).") is True
    assert is_record_held_out("Цитата (Ю. Яновський).") is True
    assert is_record_held_out("Оповідання (А. Дімаров).") is True

    # Common nouns (lowercase) and different surnames DO NOT match
    assert is_record_held_out("Згадується І. Гончаренко.") is False
    assert is_record_held_out("гончар випалює новий глиняний глечик.") is False
    assert is_record_held_out("старий стельмах ремонтує воза.") is False
    assert is_record_held_out("Твори І. Франка та Лесі Українки.") is False


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
    for cp in CANONICAL_CALQUE_PAIRS:
        assert len(cp.calque) > 2
        assert len(cp.authentic) > 2
        assert len(cp.mechanism) >= 15
        assert cp.rejected_flaw in valid_flaws
        assert cp.calque not in calque_set, f"Duplicate calque: {cp.calque}"
        calque_set.add(cp.calque)
        # Ensure zero Latin characters in author/source
        assert not any(ord(c) < 128 and c.isalpha() for c in cp.author_or_source)


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
        register="розмовний",
        is_held_out=False,
    )
    traj = synthesize_sft_trajectory(u, None, None, 3, "idiom_interpretation_literary")
    assert traj["task_type"] == "idiom_interpretation_literary"
    assert "гріти руки" in traj["query"]
    assert "<thought>" in traj["final_response"]
    assert "Наживатися у нечесний спосіб" in traj["final_response"]


def test_synthesize_sft_trajectory_dialogue():
    u = PhraseologyUnit(
        headword="гору",
        idiom="брати гору",
        definition="Перемагати у змаганні чи боротьбі.",
        citation_text="Наша правда брала гору (І. Франко).",
        author="І. Франко",
        source_dict="frazeolohichnyi_slovnyk",
        register="загальновживаний літературний",
        is_held_out=False,
    )
    traj = synthesize_sft_trajectory(u, None, None, 4, "contextual_dialogue_usage", scenario_idx=0)
    assert traj["task_type"] == "contextual_dialogue_usage"
    assert "брати гору" in traj["query"]
    assert "брати гору" in traj["final_response"]
    assert "—" in traj["final_response"]


# =========================================================================
# 4. Evaluation Benchmark Schema & 0% Leakage Tests
# =========================================================================

def test_generate_evaluation_benchmark_and_schema_validation():
    schema = json.loads(SCHEMA_EVAL_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    eval_units = [
        PhraseologyUnit(
            headword=f"гору_{i}",
            idiom=f"брати гору {i}",
            definition=f"Отримувати вирішальну перевагу чи перемогу {i}.",
            citation_text=f"Наша правда брала гору у важких боях {i} (О. Гончар)",
            author="О. Гончар",
            source_dict="ulif_nasu",
            register="загальновживаний літературний",
            is_held_out=True,
        )
        for i in range(1, 8)
    ]
    eval_calques = [
        CalquePair(
            calque=f"помилка {i}",
            authentic=f"правильно {i}",
            mechanism=f"Слововживання помилка {i} є калькою.",
            author_or_source="Корпус UA-GEC",
            rejected_flaw="lack_of_morphemic_reasoning",
            is_held_out=True,
            error_type="F/Calque",
        )
        for i in range(1, 4)
    ]
    synonyms = [SynonymGroup("добрий", ["гарний", "чудовий"], "ulif_nasu")]

    with tempfile.TemporaryDirectory() as tmpdir:
        eval_dir = Path(tmpdir) / "eval"
        meta, _sha, _counts, _authors = generate_evaluation_benchmark(
            eval_units=eval_units,
            eval_calques=eval_calques,
            synonym_pool=synonyms,
            output_dir=eval_dir,
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


# =========================================================================
# 5. Sharding and Ceiling Invariants Tests
# =========================================================================

def test_sft_sharding_ceiling():
    units = [
        PhraseologyUnit("гору", "брати гору", "перемагати", "І. Франко", "І. Франко", "ulif", "загальновживаний", False),
    ]
    dialogue_units = [
        PhraseologyUnit("думка", "мати думку", "міркувати", "І. Франко", "І. Франко", "ulif", "загальновживаний", False),
    ]
    calques = [CANONICAL_CALQUE_PAIRS[0]]
    synonyms = [SynonymGroup("сміливий", ["відважний", "хоробрий", "мужній"], "ulif")]

    with tempfile.TemporaryDirectory() as tmpdir:
        sft_dir = Path(tmpdir) / "sft"
        manifest, _sha, _tasks = generate_sft_dataset(
            units=units,
            dialogue_units=dialogue_units,
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
    calques = [CANONICAL_CALQUE_PAIRS[0]]
    units = [PhraseologyUnit("гору", "брати гору", "перемагати", "І. Франко", "І. Франко", "ulif", "загальновживаний", False)]
    synonyms = [SynonymGroup("сміливий", ["відважний", "хоробрий", "мужній"], "ulif")]

    with tempfile.TemporaryDirectory() as tmpdir:
        dpo_dir = Path(tmpdir) / "dpo"
        manifest, _sha, _flaws = generate_dpo_dataset(
            calques=calques,
            units=units,
            synonyms=synonyms,
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
# 6. Release Receipt Schema Validation & Disk Leakage Audit Test
# =========================================================================

def test_release_receipt_schema_validation():
    schema = json.loads(SCHEMA_RECEIPT_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        sft_man_path = td / "manifest_sft.json"
        sft_man_path.write_text("{}")

        dpo_man_path = td / "manifest_dpo.json"
        dpo_man_path.write_text("{}")

        eval_meta = {
            "directory_path": "data/projects/open_model_data/release/uldr_v06_ulif_phraseology/eval",
            "manifest_file": "data/projects/open_model_data/release/uldr_v06_ulif_phraseology/eval/manifest_eval.json",
            "manifest_sha256": "0" * 64,
            "shards_count": 3,
            "total_cases": 1500,
            "max_shard_size_kb": 1100.0,
            "held_out_categories": {"anti_calque_decolonization": 370, "authentic_idiom_usage": 1130},
            "held_out_authors_count": 4,
            "held_out_authors": HELD_OUT_AUTHORS_DISPLAY,
        }

        verification_info = {
            "zero_russian_syntactic_calques": True,
            "classical_literary_citations_grounded": True,
            "thought_tag_etymological_reasoning": True,
            "vesum_and_ulif_morphology_verified": True,
            "zero_train_eval_leakage": True,
            "vesum_attested_tokens_count": 1500,
            "literary_citations_grounded_count": 15000,
            "thought_tags_verified_count": 45000,
        }

        receipt = generate_release_receipt(
            eval_meta=eval_meta,
            sft_manifest_path=sft_man_path,
            sft_manifest_sha256="1" * 64,
            sft_task_dist={"anti_calque_decolonization": 15000, "idiom_interpretation_literary": 15000, "synonymic_nuance_and_register": 10000, "contextual_dialogue_usage": 5000},
            dpo_manifest_path=dpo_man_path,
            dpo_manifest_sha256="2" * 64,
            dpo_flaw_dist={"lack_of_morphemic_reasoning": 15000, "soviet_lexicography_acceptance": 5000},
            verification_info=verification_info,
            unique_calques=2500,
            unique_idioms=20000,
            unique_synonyms=10000,
            output_path=td / "receipt.json",
        )

        validator.validate(receipt)
        assert receipt["schema_version"] == "v1_ulif_phraseology_release_receipt"
        assert receipt["issue"] == 8140
        assert receipt["parent_epic"] == 6321
        assert receipt["invariants_verified"]["zero_train_eval_leakage"] is True
        assert receipt["verification_metrics"]["eval_target_overlap_count"] == 0


def test_audit_zero_train_eval_leakage_on_disk():
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        sft_dir = td / "sft"
        dpo_dir = td / "dpo"
        sft_dir.mkdir()
        dpo_dir.mkdir()

        # Clean shards
        sft_shard = sft_dir / "sft_shard_001_of_001.jsonl"
        sft_shard.write_text(json.dumps({"target_phrase": "чистий текст", "query": "Чистий текст Івана Франка"}, ensure_ascii=False) + "\n", encoding="utf-8")

        dpo_shard = dpo_dir / "dpo_shard_001_of_001.jsonl"
        dpo_shard.write_text(json.dumps({"target_phrase": "гарний вираз", "chosen": "Леся Українка чудово писала"}, ensure_ascii=False) + "\n", encoding="utf-8")

        # 1. Clean audit should pass
        eval_records = [{"target_idiom": "невідомий вираз", "calqued_counterpart": None}]
        res = audit_zero_train_eval_leakage(sft_dir, dpo_dir, eval_records=eval_records)
        assert res["zero_leakage_verified"] is True

        # 2. Author leakage introduces error
        sft_shard.write_text(json.dumps({"target_phrase": "новий вираз", "query": "Згадується О. Гончар"}, ensure_ascii=False) + "\n", encoding="utf-8")
        with pytest.raises(AssertionError, match="author leak"):
            audit_zero_train_eval_leakage(sft_dir, dpo_dir, eval_records=eval_records)

        # 3. Target phrase overlap introduces error
        sft_shard.write_text(json.dumps({"target_phrase": "невідомий вираз", "query": "Чистий текст"}, ensure_ascii=False) + "\n", encoding="utf-8")
        with pytest.raises(AssertionError, match="target overlap"):
            audit_zero_train_eval_leakage(sft_dir, dpo_dir, eval_records=eval_records)


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


@requires_sources
def test_live_ua_gec_extraction():
    calques = load_ua_gec_calques(DEFAULT_SOURCES_DB)
    assert len(calques) > 1000


@requires_vesum
def test_live_vesum_attestation():
    with sqlite3.connect(f"file:{DEFAULT_VESUM_DB}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        assert verify_phrase_in_vesum("брати участь", cur) is True
        assert verify_phrase_in_vesum("впадати в око", cur) is True
