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
import re
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
    HELD_OUT_CURATED_CALQUE_PAIRS,
    SCHEMA_EVAL_PATH,
    SCHEMA_RECEIPT_PATH,
    SPEECH_VERB_RE,
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
    get_phrase_lemmas,
    get_word_lemma_or_stem,
    is_record_held_out,
    load_frazeolohichnyi_dictionary,
    load_ua_gec_calques,
    load_ulif_phraseology_and_synonyms,
    parse_frazeolohichnyi_entry,
    sanitize_calque_string,
    synthesize_sft_trajectory,
    ukrainian_stem,
    verify_phrase_in_vesum,
    verify_receipt_invariants,
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
    raw_def = "блук[']а[/']ти манівц[']я[/']ми, розм. Робити щось не так, як треба. — Довго я блудив манівцями (О. Гончар)."
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
            "thought_tag_semantic_reasoning": True,
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
    assert len(units) >= 15000


@requires_sources
def test_live_ua_gec_extraction():
    calques = load_ua_gec_calques(DEFAULT_SOURCES_DB)
    assert len(calques) >= 400
    for c in calques:
        assert len(c.calque.split()) >= 2
        assert len(c.calque) >= 5
        assert len(c.authentic) >= 5
        assert '"' not in c.calque and '"' not in c.authentic
        # Quotation marks stripped, only intra-word Ukrainian apostrophes allowed
        assert not re.search(r"(?<![а-яіїєґА-ЯІЇЄҐ'])'|'(?![а-яіїєґА-ЯІЇЄҐ'])", c.calque)
        assert not re.search(r"(?<![а-яіїєґА-ЯІЇЄҐ'])'|'(?![а-яіїєґА-ЯІЇЄҐ'])", c.authentic)


def test_verify_receipt_invariants_real_checks():
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        sft_dir = td / "sft"
        dpo_dir = td / "dpo"
        sft_dir.mkdir()
        dpo_dir.mkdir()

        # Valid SFT shard
        sft_shard = sft_dir / "sft_shard_001_of_001.jsonl"
        valid_row = {
            "task_type": "idiom_interpretation_literary",
            "target_phrase": "брати гору",
            "final_response": "<thought>Аналізую фразеологізм «брати гору» за академічним фразеологічним словником.</thought>\n\nНормативний вираз: **«брати гору»**.",
        }
        sft_shard.write_text(json.dumps(valid_row, ensure_ascii=False) + "\n", encoding="utf-8")

        # Valid DPO shard
        dpo_shard = dpo_dir / "dpo_shard_001_of_001.jsonl"
        dpo_row = {
            "chosen": "<thought>Обґрунтування правильної норми слововживання.</thought>\n\nПравильно казати: **«брати участь»**.",
            "rejected": "<thought>Помилкова думка.</thought>\n\nМожна казати інакше.",
        }
        dpo_shard.write_text(json.dumps(dpo_row, ensure_ascii=False) + "\n", encoding="utf-8")

        eval_records = [{"target_idiom": "брати гору"}]
        res = verify_receipt_invariants(
            eval_records=eval_records,
            sft_dir=sft_dir,
            dpo_dir=dpo_dir,
            cur_ves=None,
            sources_db=DEFAULT_SOURCES_DB,
        )
        assert res["thought_tags_verified_count"] == 1
        assert res["zero_russian_syntactic_calques"] is True


@requires_vesum
def test_live_vesum_attestation():
    with sqlite3.connect(f"file:{DEFAULT_VESUM_DB}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        assert verify_phrase_in_vesum("брати участь", cur) is True
        assert verify_phrase_in_vesum("впадати в око", cur) is True


# =========================================================================
# 8. Regression Tests for Claude Sonnet Review Findings 1–8
# =========================================================================

def test_canonical_calque_no_fake_volumes():
    """Finding 5: Ensure no fabricated SUM-20 volumes in canonical or curated calques."""
    vol_re = re.compile(r"т\.\s*\d+", re.IGNORECASE)
    sum_vol_re = re.compile(r"СУМ-20,?\s*т\.", re.IGNORECASE)
    for cp in CANONICAL_CALQUE_PAIRS:
        assert not vol_re.search(cp.mechanism), f"Found volume citation in {cp.calque}: {cp.mechanism}"
        assert not vol_re.search(cp.author_or_source), f"Found volume citation in {cp.calque}: {cp.author_or_source}"
        assert not sum_vol_re.search(cp.mechanism), f"Found SUM volume in {cp.calque}: {cp.mechanism}"
        assert not sum_vol_re.search(cp.author_or_source), f"Found SUM volume in {cp.calque}: {cp.author_or_source}"

    for cp in HELD_OUT_CURATED_CALQUE_PAIRS:
        assert not vol_re.search(cp.mechanism), f"Found volume citation in {cp.calque}: {cp.mechanism}"
        assert not vol_re.search(cp.author_or_source), f"Found volume citation in {cp.calque}: {cp.author_or_source}"
        assert not sum_vol_re.search(cp.mechanism), f"Found SUM volume in {cp.calque}: {cp.mechanism}"
        assert not sum_vol_re.search(cp.author_or_source), f"Found SUM volume in {cp.calque}: {cp.author_or_source}"


def test_curated_held_out_calques_integrity():
    """Finding 4: Validate curated held-out calque catalog completeness and disjointness."""
    assert len(HELD_OUT_CURATED_CALQUE_PAIRS) >= 100
    canonical_set = {cp.calque.strip().lower() for cp in CANONICAL_CALQUE_PAIRS}
    held_out_set = {cp.calque.strip().lower() for cp in HELD_OUT_CURATED_CALQUE_PAIRS}

    # Zero overlap between canonical training calques and held-out evaluation calques
    overlap = canonical_set.intersection(held_out_set)
    assert not overlap, f"Found overlap between canonical and held-out calques: {overlap}"

    for cp in HELD_OUT_CURATED_CALQUE_PAIRS:
        assert cp.is_held_out is True
        assert len(cp.calque.strip()) >= 3
        assert len(cp.authentic.strip()) >= 3
        assert len(cp.mechanism.strip()) >= 20
        assert len(cp.author_or_source.strip()) >= 5


def test_anti_calque_10_modalities():
    """Finding 6: Test that anti-calque SFT trajectory synthesis generates 10 distinct queries."""
    cp = CANONICAL_CALQUE_PAIRS[0]
    queries = set()
    for idx in range(10):
        traj = synthesize_sft_trajectory(None, cp, None, idx, "anti_calque_decolonization", scenario_idx=idx)
        assert traj["task_type"] == "anti_calque_decolonization"
        assert cp.authentic in traj["final_response"]
        assert "<thought>" in traj["final_response"]
        assert "</thought>" in traj["final_response"]
        queries.add(traj["query"])

    assert len(queries) == 10, f"Expected 10 unique communicative query templates, got {len(queries)}"


def test_rebalanced_sft_distribution():
    """Finding 6: Verify SFT generation produces balanced task proportions."""
    units = [PhraseologyUnit(f"гору_{i}", f"брати гору {i}", "перемагати", "Франко", "Франко", "dict", "регістр", False) for i in range(25)]
    diag_units = [PhraseologyUnit(f"діалог_{i}", f"вести діалог {i}", "спілкуватися", "Франко", "Франко", "dict", "регістр", False) for i in range(10)]
    calques = CANONICAL_CALQUE_PAIRS[:5]
    synonyms = [SynonymGroup(f"слово_{i}", [f"синонім_{i}_a", f"синонім_{i}_b"], "dict") for i in range(15)]

    with tempfile.TemporaryDirectory() as tmpdir:
        sft_dir = Path(tmpdir) / "sft"
        manifest, _sha, task_counts = generate_sft_dataset(
            units=units,
            dialogue_units=diag_units,
            calques=calques,
            synonyms=synonyms,
            output_dir=sft_dir,
            target_count=45,
            shards_count=1,
            trajectories_per_shard=45,
        )
        assert manifest["total_trajectories"] == 45
        assert task_counts["idiom_interpretation_literary"] == 20
        assert task_counts["synonymic_nuance_and_register"] == 15
        assert task_counts["contextual_dialogue_usage"] == 5
        assert task_counts["anti_calque_decolonization"] == 5


def test_verify_receipt_invariants_fails_on_unattested_literary():
    """Finding 1 & 2: Invariants fail when literary idiom is not attested in frazeolohichnyi."""
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        sft_dir = td / "sft"
        dpo_dir = td / "dpo"
        sft_dir.mkdir()
        dpo_dir.mkdir()

        # Unattested literary idiom
        sft_shard = sft_dir / "sft_shard_001_of_001.jsonl"
        fake_row = {
            "task_type": "idiom_interpretation_literary",
            "target_phrase": "вигаданий псевдофразеологізм абсолютно невідомий",
            "final_response": "<thought>Аналізую семантичне значення та образну основу фразеологізму.</thought>\n\nТлумачення.",
        }
        sft_shard.write_text(json.dumps(fake_row, ensure_ascii=False) + "\n", encoding="utf-8")

        dpo_shard = dpo_dir / "dpo_shard_001_of_001.jsonl"
        dpo_shard.write_text(json.dumps({
            "chosen": "<thought>Коректне обґрунтування норми української мови.</thought>\n\nПравильно казати: **«брати участь»**.",
            "rejected": "<thought>Помилкова думка.</thought>\n\nНеправильно.",
        }, ensure_ascii=False) + "\n", encoding="utf-8")

        with pytest.raises(AssertionError, match="Classical literary citations grounding invariant failed"):
            verify_receipt_invariants(
                eval_records=[{"target_idiom": "брати гору"}],
                sft_dir=sft_dir,
                dpo_dir=dpo_dir,
                cur_ves=None,
                sources_db=DEFAULT_SOURCES_DB,
            )


def test_verify_receipt_invariants_fails_on_affirmed_calque():
    """Finding 3: Calque firewall catches affirmed calque recommendation in SFT and DPO chosen."""
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        sft_dir = td / "sft"
        dpo_dir = td / "dpo"
        sft_dir.mkdir()
        dpo_dir.mkdir()

        # Affirmed calque in SFT response
        sft_shard = sft_dir / "sft_shard_001_of_001.jsonl"
        bad_sft = {
            "task_type": "anti_calque_decolonization",
            "target_phrase": "приймати участь",
            "final_response": "<thought>Аналізую морфемні корені та семантичне слововживання виразу.</thought>\n\nНормативний відповідник:** **«приймати участь»**.",
        }
        sft_shard.write_text(json.dumps(bad_sft, ensure_ascii=False) + "\n", encoding="utf-8")

        dpo_shard = dpo_dir / "dpo_shard_001_of_001.jsonl"
        dpo_shard.write_text(json.dumps({
            "chosen": "<thought>Коректне обґрунтування норми української мови.</thought>\n\nПравильно казати: **«брати участь»**.",
            "rejected": "<thought>Помилкова думка.</thought>\n\nНеправильно.",
        }, ensure_ascii=False) + "\n", encoding="utf-8")

        with pytest.raises(AssertionError, match="Russian calque 'приймати участь' affirmed/recommended"):
            verify_receipt_invariants(
                eval_records=[{"target_idiom": "брати гору"}],
                sft_dir=sft_dir,
                dpo_dir=dpo_dir,
                cur_ves=None,
                sources_db=DEFAULT_SOURCES_DB,
            )


def test_inflected_variant_leakage_detection():
    """Finding 7: Stemming and morphological audit detects inflected forms of eval items."""
    assert ukrainian_stem("брали") == "бра"
    assert ukrainian_stem("участю") == "участ"
    cache: dict[str, str] = {}
    assert get_word_lemma_or_stem("брали", None, cache) == "бра"
    lemmas = get_phrase_lemmas("брати участь у змаганнях", None, cache)
    assert "бра" in lemmas or "участ" in lemmas

    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        sft_dir = td / "sft"
        dpo_dir = td / "dpo"
        sft_dir.mkdir()
        dpo_dir.mkdir()

        # SFT shard has inflected multi-word eval phrase in one sentence: "вчора брали гору"
        sft_shard = sft_dir / "sft_shard_001_of_001.jsonl"
        sft_shard.write_text(json.dumps({
            "target_phrase": "інший вираз",
            "query": "Питання",
            "final_response": "У запеклій боротьбі козаки впевнено брали гору над ворогом.",
        }, ensure_ascii=False) + "\n", encoding="utf-8")

        dpo_shard = dpo_dir / "dpo_shard_001_of_001.jsonl"
        dpo_shard.write_text(json.dumps({"chosen": "Чистий текст", "rejected": "Помилка"}, ensure_ascii=False) + "\n", encoding="utf-8")

        eval_records = [{"target_idiom": "брати гору", "calqued_counterpart": None}]
        with pytest.raises(AssertionError, match="inflected variant leak"):
            audit_zero_train_eval_leakage(sft_dir, dpo_dir, eval_records=eval_records)


def test_release_receipt_git_commit_custom():
    """Finding 8: Ensure git_commit can be explicitly passed to receipt generator."""
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        sft_man = td / "manifest_sft.json"
        sft_man.write_text("{}")
        dpo_man = td / "manifest_dpo.json"
        dpo_man.write_text("{}")

        eval_meta = {
            "directory_path": "eval",
            "manifest_file": "eval/manifest_eval.json",
            "manifest_sha256": "0" * 64,
            "shards_count": 3,
            "total_cases": 1500,
            "max_shard_size_kb": 1000.0,
            "held_out_categories": {},
            "held_out_authors_count": 4,
            "held_out_authors": ["Франко"],
        }
        verification_info = {
            "zero_russian_syntactic_calques": True,
            "classical_literary_citations_grounded": True,
            "thought_tag_semantic_reasoning": True,
            "vesum_and_ulif_morphology_verified": True,
            "zero_train_eval_leakage": True,
            "vesum_attested_tokens_count": 100,
            "literary_citations_grounded_count": 100,
            "thought_tags_verified_count": 100,
        }

        receipt = generate_release_receipt(
            eval_meta=eval_meta,
            sft_manifest_path=sft_man,
            sft_manifest_sha256="1" * 64,
            sft_task_dist={},
            dpo_manifest_path=dpo_man,
            dpo_manifest_sha256="2" * 64,
            dpo_flaw_dist={},
            verification_info=verification_info,
            unique_calques=10,
            unique_idioms=10,
            unique_synonyms=10,
            output_path=td / "receipt.json",
            git_commit="deadbeefcafe1234567890",
        )
        assert receipt["git_commit"] == "deadbeefcafe1234567890"


def test_sanitize_calque_string_preserves_apostrophe():
    """Ensure intra-word apostrophes in words like розв'язати are preserved, not split into spaces."""
    assert sanitize_calque_string("розв'язати") == "розв'язати"
    assert sanitize_calque_string("«розв’язати»") == "розв'язати"
    assert sanitize_calque_string("  'вирішити'  ") == "вирішити"
    assert sanitize_calque_string("«в см'ятку»") == "в см'ятку"


def test_idiom_response_diversity():
    """Finding 1 & 5: Ensure SFT idiom responses do not use a single repeated opening prefix."""
    unit = PhraseologyUnit(
        headword="рука",
        idiom="гріти руки",
        definition="Наживатися у нечесний спосіб.",
        citation_text="Він на цьому добре погрів руки.",
        author="І. Франко",
        source_dict="frazeolohichnyi",
        register="розмовний",
    )
    openings = set()
    for i in range(12):
        traj = synthesize_sft_trajectory(unit, None, None, i, "idiom_interpretation_literary")
        # Extract first sentence after </thought>
        body = traj["final_response"].split("</thought>\n\n")[1]
        first_line = body.split("\n")[0]
        openings.add(first_line)

    assert len(openings) >= 5, f"Expected at least 5 varied response openings, got {len(openings)}"


def test_clean_definition_no_embedded_quotes_or_numbers():
    """Finding 3: Ensure parse_frazeolohichnyi_entry produces clean semantic definition without embedded quotes/valency numbers."""
    raw_word = "набити руку {{</fras>}}"
    raw_def = "наб[']и[/']ти / набив[']а[/']ти ≤соб[']і[/']≥ р[']у[/']ку на (в) чому і без додатка. Набути досвіду, уміння, вправності, майстерності в чому-небудь. Кріпкі дід були, руку на житті набили (Остап Вишня); Є загроза... (О. Довженко)"
    unit = parse_frazeolohichnyi_entry(raw_word, raw_def)
    assert unit.idiom == "набити руку"
    assert "Остап Вишня" not in unit.definition
    assert "набивати" not in unit.definition
    assert "1." not in unit.definition
    assert "Набути досвіду" in unit.definition
    assert unit.author == "Остап Вишня"
    assert "Кріпкі дід були" in unit.citation_text

    raw_word2 = "розбити горщик {{</fras>}}"
    raw_def2 = "розб[']и[/']ти (поб[']и[/']ти) глек (гл[']е[/']ка, г[']о[/']рщик, г[']о[/']рщика, макітру і т.ін.) з ким, рідше між ким і без додатка. 1. Розірвати, порушити дружні стосунки; посваритися. Дівер з невісткою Розбив горщик з лемішкою (П. Чубинський); Чи вона сміється? (П. Загребельний)"
    unit2 = parse_frazeolohichnyi_entry(raw_word2, raw_def2)
    assert unit2.idiom == "розбити горщик"
    assert "Розірвати, порушити дружні стосунки" in unit2.definition
    assert "1." not in unit2.definition
    assert "макітру" not in unit2.definition
    assert "П. Чубинський" not in unit2.definition
    assert unit2.author == "П. Чубинський"
    assert "Розбив горщик" in unit2.citation_text


def test_dpo_rejected_diversity():
    """Finding 2 & 5: Ensure DPO rejected pairs are not byte-identical across records."""
    calques = CANONICAL_CALQUE_PAIRS[:14]
    with tempfile.TemporaryDirectory() as tmpdir:
        dpo_dir = Path(tmpdir) / "dpo"
        _manifest, _sha, _flaws = generate_dpo_dataset(
            calques=calques,
            output_dir=dpo_dir,
            target_count=None,
            pairs_per_shard=20,
        )
        rejected_texts = set()
        for f in dpo_dir.glob("dpo_shard_*.jsonl"):
            with f.open("r", encoding="utf-8") as fh:
                for line in fh:
                    row = json.loads(line)
                    rejected_texts.add(row["rejected"])

        # Across 14 DPO pairs, there must not be constant strawmen
        assert len(rejected_texts) == 14, f"Expected 14 unique rejected texts across pairs, got {len(rejected_texts)}"


def test_quote_boundary_no_embedded_author_or_joins():
    """CF R8 Finding 1: Ensure quotes never have embedded author tags or multi-quote joins."""
    raw_word = "пристати до лиця {{</fras>}}"
    raw_def = "приставати / пристати до лиця кому. Личити, пасувати комусь. Ясно-синій колір дуже приставав їй до лиця (І. Нечуй-Левицький); Чорний здоровий платок, котрим була її голова і плечі аж до пояса прикриті, так пристав їй до лиця (Панас Мирний)."
    unit = parse_frazeolohichnyi_entry(raw_word, raw_def)
    assert unit is not None
    assert "(" not in unit.citation_text
    assert ")" not in unit.citation_text
    assert ";" not in unit.citation_text
    assert "І. Нечуй-Левицький" not in unit.citation_text
    assert unit.author == "І. Нечуй-Левицький"
    assert unit.citation_text == "Ясно-синій колір дуже приставав їй до лиця"


def test_parser_leakage_remnants_and_dummy_starts():
    """CF R8 Finding 2: Ensure dummy pronoun starts are rejected and headword remnants stripped."""
    # Definition starting with dummy pronoun must be dropped
    raw_word_dummy = "мати рацію {{</fras>}}"
    raw_def_dummy = "Хто-небудь має рацію. Бути правим у суперечці. Я сказав правду (О. Гончар)."
    assert parse_frazeolohichnyi_entry(raw_word_dummy, raw_def_dummy) is None

    # Valency remnants like 'матері кого. Копистка:' must be stripped or rejected
    raw_word_leak = "ну к лихій матері {{</fras>}}"
    raw_def_leak = "ну к лихій (нечистій) матері кого. Уживається як лайка або прокльон. ≤Копистка:≥ Випий, зіронько!.. Та випий, ну тебе к лихій матері! ≤Параска:≥ От сатана, таки спокусив (М. Куліш)."
    unit_leak = parse_frazeolohichnyi_entry(raw_word_leak, raw_def_leak)
    assert unit_leak is not None
    assert "матері кого" not in unit_leak.citation_text
    assert "Копистка:" not in unit_leak.citation_text
    assert "(" not in unit_leak.citation_text
    assert unit_leak.citation_text == "Випий, зіронько!.. Та випий, ну тебе к лихій матері! От сатана, таки спокусив"


def test_idiom_thought_register_conditional():
    """CF R8 Finding 3: Ensure thoughts only assert register when present and match answers."""
    unit_no_reg = PhraseologyUnit(
        headword="рука",
        idiom="набити руку",
        definition="Набути практичного досвіду.",
        citation_text="Кріпкі дід були, руку на житті набили",
        author="Остап Вишня",
        source_dict="frazeolohichnyi_slovnyk",
        register=None,
        is_held_out=False,
    )
    sft_no_reg = synthesize_sft_trajectory(unit_no_reg, None, None, 0, "idiom_interpretation_literary")
    # No fake register claim when register is None
    assert "загальновживаний літературний" not in sft_no_reg["final_response"]
    assert "стилістичний регістр" not in sft_no_reg["final_response"].lower()

    unit_reg = PhraseologyUnit(
        headword="горщик",
        idiom="розбити горщик",
        definition="Розірвати дружні стосунки.",
        citation_text="Дівер з невісткою розбив горщик",
        author="П. Чубинський",
        source_dict="frazeolohichnyi_slovnyk",
        register="розмовний",
        is_held_out=False,
    )
    sft_reg = synthesize_sft_trajectory(unit_reg, None, None, 0, "idiom_interpretation_literary")
    # Register present in thought and answer
    assert "розмовний" in sft_reg["final_response"]


def test_vetted_calque_catalog_no_disputed_pairs():
    """CF R8 & R9: Ensure disputed calques are excluded and vetted pairs included."""
    calques = [cp.calque for cp in CANONICAL_CALQUE_PAIRS]
    assert "кидатися в очі" not in calques
    assert "грати роль" not in calques
    assert "брати верх" not in calques
    assert "приходити в голову" not in calques
    assert "потерпіти крах" in calques
    assert "взяти себе в руки" in calques
    assert "нанести шкоду" in calques
    assert "слідуюча зупинка" in calques


def test_clean_raw_html_preserves_speaker_names_in_dialogue():
    """CF R9 Finding 1: Ensure character names in ≤word≥ are preserved in dialogue, not stripped into stray punctuation."""
    raw_quote = "— Чого це ти, Чіпко, як мила з'їв? — питає ≤Лушня≥. — Чого ти журишся? (Панас Мирний)."
    cleaned = clean_raw_html_and_tags(raw_quote)
    assert "питає Лушня" in cleaned
    assert "питає ." not in cleaned
    assert " . —" not in cleaned

    # Drama speaker prefix with colon should still be stripped
    drama_line = "≤Савка:≥ Я вам, куме, признаюсь, що сам ходив... (І. Карпенко-Карий)."
    cleaned_drama = clean_raw_html_and_tags(drama_line)
    assert "Савка:" not in cleaned_drama
    assert "Я вам, куме" in cleaned_drama


def test_parse_frazeolohichnyi_rejects_spliced_quotes_and_selects_clean_attestation():
    """CF R9 Finding 2: Ensure spliced quotes with '.. .' are rejected in favor of clean citations."""
    raw_word = "хоч крізь землю провалися {{</fras>}}"
    raw_def = (
        "хоч крізь з[']е[/']млю пров[']а[/']люйся (провал[']и[/']ся і т.ін.). Дуже неприємно, незручно, соромно і т.ін. комусь. "
        "Йому так неприємна була вся ця історія.. .складається таке неприємне враження, що прямо хоч крізь землю провалюйсь (М. Хвильовий); "
        "А як щось поламається? Та ще й на Віриній ділянці! Тоді хоч крізь землю провалися (А. Хорунжий); "
        "≤Любов:≥ Коли б ви знали, як мені часом буває сором (Леся Українка)."
    )
    unit = parse_frazeolohichnyi_entry(raw_word, raw_def)
    assert unit is not None
    # Spliced quote by Хвильовий with '.. .' must be skipped in favor of clean quote by Хорунжий
    assert unit.author == "А. Хорунжий"
    assert unit.citation_text == "А як щось поламається? Та ще й на Віриній ділянці! Тоді хоч крізь землю провалися"
    assert ".. ." not in unit.citation_text


def test_parse_frazeolohichnyi_rejects_mismatched_pronoun_quote():
    """CF R9 Finding 2: Ensure quote must attest specific required pronoun variant."""
    raw_word = "хай би тобі трясця {{</fras>}}"
    raw_def = (
        "хай ≤би≥ йому (їй, тобі, їм, вам) трясця, лайл. Уживається як недобре побажання. "
        "— Хай йому трясця, ще вскочимо в пащу Гітлера (П. Панч); "
        "— Хай йому трясця, цьому улемові! (З. Тулуб); "
        "— Та в трест викликали, хай би йому трясця,— зі словом сказала вона (Є. Гуцало); "
        "— А хай вам трясця! — тріснув голос тітки Марії (Я. Баш)."
    )
    # None of the citations in raw_def attests 'тобі', so this variant must not be matched to a mismatched quote with 'йому'
    unit = parse_frazeolohichnyi_entry(raw_word, raw_def)
    assert unit is None

    # If the entry variant is 'хай би йому трясця', it should match Є. Гуцало
    raw_word_yomu = "хай би йому трясця {{</fras>}}"
    unit_yomu = parse_frazeolohichnyi_entry(raw_word_yomu, raw_def)
    assert unit_yomu is not None
    assert unit_yomu.author in ("П. Панч", "З. Тулуб", "Є. Гуцало")


def test_dpo_chosen_thought_diversity_and_no_tautology():
    """CF R9 Finding 3: Ensure chosen thoughts are varied across linguistic angles and avoid tautology."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dpo_dir = Path(tmpdir) / "dpo"
        _manifest, _sha, _flaws = generate_dpo_dataset(
            calques=CANONICAL_CALQUE_PAIRS[:8],
            output_dir=dpo_dir,
            target_count=None,
            pairs_per_shard=20,
        )
        thoughts = set()
        for f in dpo_dir.glob("dpo_shard_*.jsonl"):
            with f.open("r", encoding="utf-8") as fh:
                for line in fh:
                    row = json.loads(line)
                    chosen = row["chosen"]
                    # No tautological phrases
                    assert "думка спадає на думку" not in chosen.lower()
                    m_th = re.search(r"<thought>(.*?)</thought>", chosen, re.DOTALL)
                    assert m_th is not None
                    thoughts.add(m_th.group(1).strip())

        # Must have diverse reasoning angles, not a single static template
        assert len(thoughts) >= 4, f"Expected at least 4 distinct chosen thoughts, got {len(thoughts)}"


def test_speech_verb_before_punctuation_re():
    """CF R9 Finding 1 & 5: Ensure speech verb regex detects orphaned verbs before punctuation."""
    assert SPEECH_VERB_RE.search("— питає . — Чого ти") is not None
    assert SPEECH_VERB_RE.search("— каже . — Ходімо") is not None
    assert SPEECH_VERB_RE.search("— мовив — і пішов") is not None
    assert SPEECH_VERB_RE.search("— сказав .. Безпачпортною") is not None
    # Legitimate non-orphaned text
    assert SPEECH_VERB_RE.search("— питає Лушня. — Чого ти") is None
    assert SPEECH_VERB_RE.search("він каже правду") is None
