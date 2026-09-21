"""Test suite for Dataset Acceptance Audit Gate (#8339).

Verifies the seven mechanical acceptance checks, failure modes, false-positive guards,
dependency fail-closed behaviors, and baseline empirical reproductions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data.audit_dataset_acceptance import (
    DEFAULT_SOURCES_DB,
    VESUM_DB_PATH,
    LinguisticNormalizer,
    audit_check_1_repeats,
    audit_check_2_form_letters,
    audit_check_3_content_share,
    audit_check_4_contradictions,
    audit_check_5_source_rules,
    audit_check_6_split_overlap,
    audit_check_7_sample_drawer,
    delexicalize_text,
    load_profile,
    normalize_ukrainian_text,
    parse_dataset_record,
    run_acceptance_audit,
)


@pytest.fixture(scope="module")
def normalizer():
    """Shared linguistic normalizer for unit tests."""
    if not VESUM_DB_PATH.is_file():
        pytest.skip(f"VESUM DB {VESUM_DB_PATH} not found")
    norm = LinguisticNormalizer(VESUM_DB_PATH)
    yield norm
    norm.close()


@pytest.fixture(scope="module")
def default_thresholds():
    """Load default acceptance profile thresholds."""
    thresholds, _ = load_profile("default")
    return thresholds


# ── Text Normalization & Delexicalization Tests ─────────────────────────────


def test_ukrainian_text_normalization():
    """Test NFKC, apostrophe unification, stress stripping, and whitespace collapse."""
    # Apostrophes: ’ (U+2019), ʼ (U+02BC), ` -> '
    assert normalize_ukrainian_text("з’явитися") == "з'явитися"
    assert normalize_ukrainian_text("обʼєкт") == "об'єкт"
    # Combining acute accent U+0301 (stress mark)
    assert normalize_ukrainian_text("нови́й") == "новий"
    assert normalize_ukrainian_text("ба́чити") == "бачити"
    # Whitespace
    assert normalize_ukrainian_text("  слово   з   пробілами\n") == "слово з пробілами"


def test_delexicalization_quote_and_digit_masking():
    """Test masking of all typographic quote styles and digits."""
    s1 = "Проаналізуйте напис: «Jan Lohowski» 1585 року."
    assert delexicalize_text(s1) == "Проаналізуйте напис: <QUOTED_SPAN> # року."

    s2 = 'Поясніть слово "калька" у розділі 3.'
    assert delexicalize_text(s2) == "Поясніть слово <QUOTED_SPAN> у розділі #."

    s3 = "Текст „цитата“ та ‘інша’ 2026."
    assert delexicalize_text(s3) == "Текст <QUOTED_SPAN> та <QUOTED_SPAN> #."


# ── Check 1: Repeats & Duplicates ───────────────────────────────────────────


def test_check1_passes_on_unique_records(default_thresholds):
    """Check 1 passes when all QA pairs are distinct and not template clones."""
    sentences = [
        ("Як правильно вживати слово обрій?", "Слово обрій є синонімом до горизонт."),
        ("Поясніть значення фразеологізму бити байдики.", "Бити байдики означає ледарювати."),
        ("Чому форма сідий є калькою?", "В українській мові вживається слово сивий."),
        ("У чому полягає відмінність між військовим і воєнним?", "Військовий стосується війська, воєнний - війни."),
        ("Який відмінок вимагає прийменник завдяки?", "Прийменник завдяки вимагає давального відмінка."),
    ]
    records = [
        parse_dataset_record({"query": q, "final_response": a}, Path("shard.jsonl"), i)
        for i, (q, a) in enumerate(sentences)
    ]
    res = audit_check_1_repeats(records, default_thresholds)
    assert res.status == "PASS"
    assert res.metrics["exact_duplicate_count"] == 0
    assert res.metrics["exact_duplicate_rate"] == 0.0
    assert res.metrics["near_duplicate_template_rate"] == 0.0


def test_check1_fails_on_duplicate_qa_pair(default_thresholds):
    """Check 1 deliberately fails when identical QA pairs are repeated (M1 failure mode)."""
    records = [
        parse_dataset_record({"query": "Одне й те саме", "final_response": "Та сама відповідь"}, Path("shard.jsonl"), i)
        for i in range(10)
    ]
    res = audit_check_1_repeats(records, default_thresholds)
    assert res.status == "FAIL"
    assert res.metrics["exact_duplicate_count"] == 9
    assert res.metrics["exact_duplicate_rate"] == 0.90
    assert res.metrics["max_single_multiplicity"] == 10
    assert any("Exact duplicate rate" in f for f in res.failures)


# ── Check 2: Form Letters & Pattern Concentration ───────────────────────────


def test_check2_fails_on_form_letter_reasoning(default_thresholds):
    """Check 2 deliberately fails when reasoning templates collapse into form letters."""
    # 100 records sharing the identical 1 reasoning template with only quoted span varying
    records = [
        parse_dataset_record(
            {
                "query": f"Проаналізуйте слово «слово_{i}» у реченні.",
                "reasoning_steps": [
                    f"1. Палеографічна локалізація: Софія, пам'ятка «слово_{i}».",
                    "2. Соціолінгвістичний регістр: жива розмовна мова.",
                    "3. Висновок: пам'ятка давньоруської доби.",
                ],
                "final_response": f"Слово «слово_{i}» є давньоруським.",
            },
            Path("shard.jsonl"),
            i,
        )
        for i in range(100)
    ]
    res = audit_check_2_form_letters(records, default_thresholds)
    assert res.status == "FAIL"
    assert res.metrics["reasoning"]["top1"] == 1.0  # 100% covered by 1 template
    assert any("Reasoning top 20 patterns" in f or "Reasoning top 5" in f for f in res.failures)


# ── Check 3: Real Content Share ─────────────────────────────────────────────


def test_check3_fails_on_excessive_passive_controls(default_thresholds):
    """Check 3 deliberately fails when passive controls vastly outweigh corrections (93% passive v05 bug)."""
    records = []
    # 95 controls ("nothing wrong")
    for i in range(95):
        records.append(
            parse_dataset_record(
                {
                    "is_erroneous": False,
                    "original_text": f"Правильне речення номер {i}.",
                    "corrected_text": f"Правильне речення номер {i}.",
                    "category": "syntax",
                },
                Path("shard.jsonl"),
                i,
            )
        )
    # 5 corrections
    for i in range(5):
        records.append(
            parse_dataset_record(
                {
                    "is_erroneous": True,
                    "original_text": f"Помилкове речення {i}.",
                    "corrected_text": f"Виправлене речення {i}.",
                    "category": "syntax",
                },
                Path("shard.jsonl"),
                100 + i,
            )
        )

    res = audit_check_3_content_share(records, default_thresholds, manifest_task_type="correction")
    assert res.status == "FAIL"
    assert res.metrics["clean_control_share"] == 0.95
    assert res.metrics["substantive_correction_share"] == 0.05
    assert any("correction share 5.0% is below floor" in f for f in res.failures)


# ── Check 4: Self-Contradiction Audit ───────────────────────────────────────


def test_check4_fails_on_chronological_contradiction(default_thresholds, normalizer):
    """Check 4 deliberately fails on in-record date contradiction (XI-XIII label vs 1585 in Step 1)."""
    record = parse_dataset_record(
        {
            "query": "Проаналізуйте напис: «Jan Lohowski».",
            "morphemic_breakdown": "Києво-руська епіграфічна пам'ятка XI–XIII ст. (Софія Київська).",
            "reasoning_steps": [
                "1. Палеографічна локалізація: Софійський собор у Києві, приміщення 208 (1585–1700 рр.). Текст: «Jan Lohowski»."
            ],
            "final_response": "Уривок «Jan Lohowski» є автентичним графіті (1585–1700 рр.).",
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_4_contradictions([record], default_thresholds, normalizer)
    assert res.status == "FAIL"
    assert res.metrics["contradiction_count"] == 1
    assert any("Labeled XI–XIII century but Step 1 dating" in f for f in res.failures)


def test_check4_permits_incidental_date_mention(default_thresholds, normalizer):
    """Check 4 does not false-fail on legitimate incidental historical date mentions in body."""
    record = parse_dataset_record(
        {
            "query": "Проаналізуйте напис доби Козацького бароко.",
            "morphemic_breakdown": "Староукраїнська пам'ятка доби Бароко (XVII-XVIII ст.).",
            "reasoning_steps": [
                "1. Історична локалізація: Гетьманщина (1650-1700 рр.).",
                "2. Зауважимо, що текст було переписано у XVIII ст. зі старішого списку.",
            ],
            "final_response": "Текст доби Бароко.",
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_4_contradictions([record], default_thresholds, normalizer)
    assert res.status == "PASS"
    assert res.metrics["contradiction_count"] == 0


def test_check4_permits_inflected_target_term(default_thresholds, normalizer):
    """Check 4 does not false-fail when target_term is inflected in text (VESUM lemma match)."""
    record = parse_dataset_record(
        {
            "query": "Поясніть вживання форми у реченні.",
            "target_term": "вигляд",
            "original_text": "Він не подавав вигляду, що щось сталося.",
            "final_response": "У реченні вжито форму родового відмінка.",
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_4_contradictions([record], default_thresholds, normalizer)
    assert res.status == "PASS"
    assert res.metrics["contradiction_count"] == 0


# ── Check 5: Source Rules (Epic Rules 3 & 4) ────────────────────────────────


def test_check5_fails_on_soviet_sum11_normative_use(default_thresholds):
    """Check 5 deliberately fails if СУМ-11 is cited as normative source of truth."""
    record = parse_dataset_record(
        {
            "query": "Поясніть слово «визволення».",
            "final_response": "Тлумачення слова згідно з радянським тлумачним словником.",
            "source_metadata": {"authority": "СУМ-11", "page": 123},
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_5_source_rules([record], default_thresholds)
    assert res.status == "FAIL"
    assert res.metrics["sum11_normative_violations"] == 1


def test_check5_fails_on_soviet_sum11_negative_inference(default_thresholds):
    """Check 5 deliberately fails if a word is condemned because it is absent from СУМ-11."""
    record = parse_dataset_record(
        {
            "query": "Чи є нормативним слово «часопис»?",
            "final_response": "Це слово відсутнє в СУМ-11, тому воно рідковживане та застаріле.",
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_5_source_rules([record], default_thresholds)
    assert res.status == "FAIL"
    assert res.metrics["sum11_negative_inferences"] == 1


def test_check5_permits_contrastive_soviet_colonization_context(default_thresholds):
    """Check 5 permits СУМ-11 strictly when cited under historical_suppression_note."""
    record = parse_dataset_record(
        {
            "query": "Порівняйте значення слів «сідий» та «сивий».",
            "final_response": "«Сідий» є калькою з російської.",
            "source_metadata": {
                "historical_suppression_note": "СУМ-11 допустив вживання форми «сідий» унаслідок зближення мов.",
                "authority": "СУМ-20",
            },
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_5_source_rules([record], default_thresholds)
    assert res.status == "PASS"
    assert res.metrics["sum11_normative_violations"] == 0


# ── Check 6: Train/Test Overlap & Aspect Normalization ───────────────────────


def test_check6_fails_on_aspect_pair_leakage(default_thresholds, normalizer):
    """Check 6 catches train/test leakage even when verbs differ by aspectual prefixes (робити vs зробити)."""
    train_record = parse_dataset_record(
        {
            "query": "Він любив робити вигляд, що слухає уважно лекцію в університеті.",
            "final_response": "У реченні вжито фразеологізм.",
        },
        Path("sft_shard.jsonl"),
        1,
    )
    eval_record = parse_dataset_record(
        {
            "query": "Вона спромоглася зробити вигляд, що слухає уважно лекцію в університеті.",
            "final_response": "У реченні вжито фразеологізм.",
        },
        Path("eval_shard.jsonl"),
        1,
    )
    res = audit_check_6_split_overlap([train_record, eval_record], default_thresholds, normalizer)
    assert res.status == "FAIL"
    # Overlap detected via aspect-normalized 4-grams
    assert res.metrics["eval_records_high_containment"] == 1
    assert res.metrics["high_containment_share"] == 1.0


# ── Check 7: Sampling & Review Lifecycle ────────────────────────────────────


def test_check7_sample_generation_and_deterministic_seed(tmp_path, default_thresholds):
    """Check 7 draws deterministic sample and writes valid MD and JSON sidecars."""
    records = [
        parse_dataset_record(
            {
                "query": f"Запитання {i}",
                "final_response": f"Відповідь {i}",
                "category": f"cat_{i % 5}",
            },
            Path(f"shard_{i % 3}.jsonl"),
            i,
        )
        for i in range(50)
    ]
    sample_out = tmp_path / "test_sample.md"
    dataset_hash = "abc1234567890abcdef"

    res, path = audit_check_7_sample_drawer(records, default_thresholds, dataset_hash, sample_out)
    assert res.status == "PASS"
    assert path.is_file()
    assert path.with_suffix(".json").is_file()

    content_md = path.read_text(encoding="utf-8")
    assert "Independent Language Review Sample Package" in content_md
    assert "Мовна якість" in content_md
    assert "радянських/колоніальних спотворень" in content_md


# ── Dependency Fail-Closed Tests ────────────────────────────────────────────


def test_run_acceptance_audit_fails_on_missing_vesum_db(tmp_path):
    """Acceptance audit exits 2 if vesum.db is missing (fail-closed)."""
    dummy_dir = tmp_path / "data"
    dummy_dir.mkdir()
    (dummy_dir / "sample.jsonl").write_text('{"query": "a", "final_response": "b"}\n', encoding="utf-8")

    report, exit_code = run_acceptance_audit(
        dataset_dir=dummy_dir,
        vesum_db=Path("/nonexistent/vesum.db"),
        sources_db=DEFAULT_SOURCES_DB,
    )
    assert exit_code == 2
    assert report.overall_status == "OPERATIONAL_ERROR"


# ── Empirical Baseline Reproduction Tests (#6321, Roadmap §2) ───────────────

BASELINES_DIR = Path(__file__).resolve().parents[3] / "data" / "projects" / "open_model_data"
V04A_DIR = BASELINES_DIR / "archive" / "quarantined_historical" / "uldr_v04a_kyivan_rus"
V04B_DIR = BASELINES_DIR / "archive" / "quarantined_historical" / "uldr_v04b_middle_ukrainian"
V05_DIR = BASELINES_DIR / "release" / "uldr_v05_grammar_valency"


@pytest.mark.skipif(not V04A_DIR.is_dir(), reason="uldr_v04a not on local disk")
def test_reproduces_v04a_kyivan_rus_findings(default_thresholds, normalizer):
    """Verify reproduction of findings on uldr_v04a (#8103): 467 date contradictions, top-5 query 94.1%."""
    shards = sorted(V04A_DIR.glob("sft/*.jsonl"))
    records = []
    for s in shards:
        for idx, line in enumerate(s.open(encoding="utf-8"), 1):
            records.append(parse_dataset_record(json.loads(line), s, idx))

    q_res = audit_check_2_form_letters(records, default_thresholds)
    assert q_res.metrics["query"]["top5"] == pytest.approx(0.941, abs=0.01)

    c_res = audit_check_4_contradictions(records, default_thresholds, normalizer)
    assert c_res.metrics["contradiction_count"] >= 467


@pytest.mark.skipif(not V04B_DIR.is_dir(), reason="uldr_v04b not on local disk")
def test_reproduces_v04b_middle_ukrainian_findings(default_thresholds):
    """Verify reproduction of findings on uldr_v04b (#8105): 142 reasoning patterns, 20 cover 98.8%."""
    shards = sorted(V04B_DIR.glob("sft/*.jsonl"))
    records = []
    for s in shards:
        for idx, line in enumerate(s.open(encoding="utf-8"), 1):
            records.append(parse_dataset_record(json.loads(line), s, idx))

    f_res = audit_check_2_form_letters(records, default_thresholds)
    assert f_res.metrics["reasoning"]["K"] == 142
    assert f_res.metrics["reasoning"]["top20"] == pytest.approx(0.988, abs=0.005)
    assert f_res.metrics["query"]["top5"] == pytest.approx(0.902, abs=0.005)


@pytest.mark.skipif(not V05_DIR.is_dir(), reason="uldr_v05 not on local disk")
def test_reproduces_v05_grammar_valency_findings(default_thresholds):
    """Verify reproduction of findings on uldr_v05 (#8143): 32,629 controls, 2,371 corrections, 13 queries."""
    shards = sorted(V05_DIR.glob("sft/*.jsonl"))
    records = []
    for s in shards:
        for idx, line in enumerate(s.open(encoding="utf-8"), 1):
            records.append(parse_dataset_record(json.loads(line), s, idx))

    c_res = audit_check_3_content_share(records, default_thresholds, manifest_task_type="correction")
    assert c_res.metrics["controls_count"] == 32629
    assert c_res.metrics["corrections_count"] == 2371
    assert c_res.metrics["thin_categories_count"] == 8

    q_res = audit_check_2_form_letters(records, default_thresholds)
    assert q_res.metrics["query"]["K"] == 13
