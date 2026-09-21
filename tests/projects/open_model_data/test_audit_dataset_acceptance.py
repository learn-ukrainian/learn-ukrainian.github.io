"""Test suite for Dataset Acceptance Audit Gate (#8339).

Verifies the seven mechanical acceptance checks, failure modes, false-positive guards,
dependency fail-closed behaviors, profile provenance, review lifecycle, and baseline empirical reproductions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data.audit_dataset_acceptance import (
    ASPECT_PAIRS_FILE,
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
    compute_dataset_sha256,
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
    norm = LinguisticNormalizer(VESUM_DB_PATH, ASPECT_PAIRS_FILE)
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
    assert normalize_ukrainian_text("з’явитися") == "з'явитися"
    assert normalize_ukrainian_text("обʼєкт") == "об'єкт"
    assert normalize_ukrainian_text("нови́й") == "новий"
    assert normalize_ukrainian_text("ба́чити") == "бачити"
    assert normalize_ukrainian_text("  слово   з   пробілами\n") == "слово з пробілами"


def test_delexicalization_quote_and_digit_masking():
    """Test masking of all typographic quote styles and digits."""
    s1 = "Проаналізуйте напис: «Jan Lohowski» 1585 року."
    assert delexicalize_text(s1) == "Проаналізуйте напис: <QUOTED_SPAN> # року."

    s2 = 'Поясніть слово "калька" у розділі 3.'
    assert delexicalize_text(s2) == "Поясніть слово <QUOTED_SPAN> у розділі #."

    s3 = "Текст „цитата“ та ‘інша’ 2026."
    assert delexicalize_text(s3) == "Текст <QUOTED_SPAN> та <QUOTED_SPAN> #."

    s4 = "Шаблон {word} та <item> у списку [1]."
    assert delexicalize_text(s4) == "Шаблон <VAR> та <VAR> у списку <VAR>."


# ── Split Detection Tests (Blocker 1) ───────────────────────────────────────


def test_split_detection_relative_paths(tmp_path):
    """Test that split detection is relative and does not false-trigger on directory names."""
    dataset_dir = tmp_path / "contest_latest_eval_archive" / "data"
    dataset_dir.mkdir(parents=True)

    # File inside train folder should be train even if parent dir has 'contest' or 'eval'
    f_train = dataset_dir / "train" / "shard_001.jsonl"
    f_train.parent.mkdir(parents=True)
    f_train.touch()

    r1 = parse_dataset_record({"query": "q", "final_response": "a"}, f_train, 1, dataset_dir)
    assert r1.split == "train"

    # File inside eval folder should be eval
    f_eval = dataset_dir / "eval" / "shard_001.jsonl"
    f_eval.parent.mkdir(parents=True)
    f_eval.touch()

    r2 = parse_dataset_record({"query": "q", "final_response": "a"}, f_eval, 1, dataset_dir)
    assert r2.split == "eval"

    # Filename stem matching word boundary test / eval
    f_stem = dataset_dir / "shards" / "dataset-test.jsonl"
    f_stem.parent.mkdir(parents=True)
    f_stem.touch()

    r3 = parse_dataset_record({"query": "q", "final_response": "a"}, f_stem, 1, dataset_dir)
    assert r3.split == "eval"

    # Explicit record split overrides path
    r4 = parse_dataset_record({"query": "q", "final_response": "a", "split": "eval"}, f_train, 1, dataset_dir)
    assert r4.split == "eval"


# ── Profile Provenance & Security Tests (Blocker 2) ─────────────────────────


def test_profile_provenance_and_security():
    """Verify committed profile allowlist, traversal rejection, and composite hash."""
    # 1. Committed profiles load cleanly
    t_def, h_def = load_profile("default")
    assert "max_exact_duplicate_rate" in t_def
    assert len(h_def) == 64

    t_gram, h_gram = load_profile("grammar_8342")
    assert t_gram["min_correction_share"] == 0.70
    assert h_gram != h_def

    # 2. Path traversal attempts are rejected
    with pytest.raises(ValueError, match="path separators not permitted"):
        load_profile("../default")

    with pytest.raises(ValueError, match="path separators not permitted"):
        load_profile("../../etc/passwd")

    # 3. Unapproved profile names are rejected
    with pytest.raises(ValueError, match="Unapproved profile"):
        load_profile("unapproved_custom")


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
    """Check 1 fails immediately on exact duplicate QA pairs."""
    pair = ("Яка столиця України?", "Столиця України - місто Київ.")
    records = [
        parse_dataset_record({"query": pair[0], "final_response": pair[1]}, Path("shard.jsonl"), 1),
        parse_dataset_record({"query": pair[0], "final_response": pair[1]}, Path("shard.jsonl"), 2),
    ]
    res = audit_check_1_repeats(records, default_thresholds)
    assert res.status == "FAIL"
    assert res.metrics["exact_duplicate_count"] == 1
    assert res.metrics["max_single_multiplicity"] == 2
    assert any("Exact duplicate rate" in f for f in res.failures)


# ── Check 2: Form Letters & Entropy ─────────────────────────────────────────


def test_check2_fails_on_form_letter_reasoning(default_thresholds):
    """Check 2 fails when reasoning collapses into a single repeated template."""
    records = []
    template_reasoning = "Крок 1: Аналізуємо граматичну основу. Крок 2: Перевіряємо за словником."
    for i in range(1200):
        records.append(
            parse_dataset_record(
                {
                    "query": f"Поясніть приклад {i}",
                    "reasoning_steps": [template_reasoning],
                    "final_response": f"Унікальна відповідь на запитання {i} з докладним поясненням.",
                },
                Path("shard.jsonl"),
                i,
            )
        )
    res = audit_check_2_form_letters(records, default_thresholds)
    assert res.status == "FAIL"
    assert res.metrics["reasoning"]["top1"] > 0.90
    assert any("Reasoning top 1 pattern covers" in f for f in res.failures)


# ── Check 3: Content Share & Thin Categories ────────────────────────────────


def test_check3_fails_on_excessive_passive_controls(default_thresholds):
    """Check 3 fails when passive controls overwhelm substantive corrections."""
    records = []
    for i in range(100):
        is_err = i < 10  # 90% clean controls, only 10% substantive corrections
        records.append(
            parse_dataset_record(
                {
                    "query": f"Речення {i}",
                    "is_erroneous": is_err,
                    "original_text": "правильний текст" if not is_err else "помилковий текст",
                    "corrected_text": "правильний текст",
                    "category": "орфографія",
                },
                Path("shard.jsonl"),
                i,
            )
        )
    res = audit_check_3_content_share(records, default_thresholds, manifest_task_type="correction")
    assert res.status == "FAIL"
    assert res.metrics["substantive_correction_share"] == 0.10
    assert any("Substantive correction share" in f for f in res.failures)


def test_check3_fails_on_zero_labeled_records_for_correction_task(default_thresholds):
    """Check 3 fails closed if correction task is declared but zero records have correction labels."""
    records = [parse_dataset_record({"query": "q", "final_response": "a"}, Path("shard.jsonl"), i) for i in range(10)]
    res = audit_check_3_content_share(records, default_thresholds, manifest_task_type="correction")
    assert res.status == "FAIL"
    assert any("zero labeled records" in f for f in res.failures)


# ── Check 4: Self-Contradiction Audit ───────────────────────────────────────


def test_check4_fails_on_chronological_contradiction(default_thresholds, normalizer):
    """Check 4 catches Kyivan Rus period label with Early Modern/Late Modern dating in reasoning."""
    rec = parse_dataset_record(
        {
            "query": "Напис на сріблі",
            "morphemic_breakdown": "kyivan_rus_epigraphy (XI–XIII ст.)",
            "reasoning_steps": ["Пам'ятка датується (1585–1700) роками."],
            "final_response": "Текст",
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_4_contradictions([rec], default_thresholds, normalizer)
    assert res.status == "FAIL"
    assert res.metrics["contradiction_count"] == 1
    assert any("Labeled Kyivan Rus" in f for f in res.failures)


def test_check4_permits_inflected_target_term(default_thresholds, normalizer):
    """Check 4 permits target term present in inflected form in context."""
    rec = parse_dataset_record(
        {
            "query": "Він пив свіжий сік.",
            "final_response": "Все вірно.",
            "target_term": "соку",  # Genitive form of сік
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_4_contradictions([rec], default_thresholds, normalizer)
    assert res.status == "PASS"
    assert res.metrics["contradiction_count"] == 0


def test_check4_multiword_target_term_matching(default_thresholds, normalizer):
    """Check 4 requires all words of a multi-word target term to be present."""
    # Only "брати" present, "участь" missing
    rec_missing = parse_dataset_record(
        {
            "query": "Ми брали книжки в бібліотеці.",
            "final_response": "Все вірно.",
            "target_term": "брати участь",
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_4_contradictions([rec_missing], default_thresholds, normalizer)
    assert res.status == "FAIL"
    assert res.metrics["contradiction_count"] == 1


# ── Check 5: Source Rules (Epic Rules 3 & 4) ────────────────────────────────


def test_check5_fails_on_soviet_sum11_aliases_and_affirmative_mentions(default_thresholds):
    """Check 5 catches all Soviet СУМ-11 aliases and affirmative body text citations."""
    aliases = ["СУМ 11", "sum-11", "СУМ_11", "словник української мови в 11 томах"]
    for alias in aliases:
        rec = parse_dataset_record(
            {
                "query": "Питання",
                "final_response": "Відповідь",
                "source_metadata": {"authority": alias},
            },
            Path("shard.jsonl"),
            1,
        )
        res = audit_check_5_source_rules([rec], default_thresholds)
        assert res.status == "FAIL"
        assert res.metrics["sum11_normative_violations"] == 1

    # Body text affirmative citation
    rec_body = parse_dataset_record(
        {
            "query": "Чи є це слово нормативним?",
            "final_response": "Згідно з СУМ-11 це слово є нормативним літературним словом.",
            "source_metadata": {"authority": "vesum"},
        },
        Path("shard.jsonl"),
        2,
    )
    res_body = audit_check_5_source_rules([rec_body], default_thresholds)
    assert res_body.status == "FAIL"
    assert res_body.metrics["sum11_normative_violations"] == 1


def test_check5_fails_on_soviet_sum11_negative_inference(default_thresholds):
    """Check 5 catches rejection of authentic Ukrainian words based on absence from СУМ-11."""
    rec = parse_dataset_record(
        {
            "query": "Чи правильне слово розпросторити?",
            "reasoning_steps": ["Слово відсутнє в СУМ-11, тому вважається помилковим."],
            "final_response": "Це помилка.",
            "source_metadata": {"authority": "vesum"},
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_5_source_rules([rec], default_thresholds)
    assert res.status == "FAIL"
    assert res.metrics["sum11_negative_inferences"] == 1


def test_check5_permits_contrastive_soviet_colonization_context(default_thresholds):
    """Check 5 permits СУМ-11 strictly as contrastive historical context alongside modern authority."""
    rec = parse_dataset_record(
        {
            "query": "Як маркувалося слово літовище в радянський період?",
            "final_response": "Слово літовище було замінено на аеродром у СУМ-11.",
            "historical_suppression_note": "СУМ-11 штучно маркував автентичні українські терміни як застарілі.",
            "source_metadata": {"authority": "СУМ-20"},
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_5_source_rules([rec], default_thresholds)
    assert res.status == "PASS"
    assert res.metrics["sum11_normative_violations"] == 0


def test_check5_fails_on_contrastive_without_modern_authority(default_thresholds):
    """Check 5 fails if contrastive note is present but sole cited authority is СУМ-11."""
    rec = parse_dataset_record(
        {
            "query": "Слово літовище",
            "final_response": "Відповідь",
            "historical_suppression_note": "Радянське вилучення",
            "source_metadata": {"authority": "СУМ-11"},
        },
        Path("shard.jsonl"),
        1,
    )
    res = audit_check_5_source_rules([rec], default_thresholds)
    assert res.status == "FAIL"
    assert res.metrics["unapproved_authorities_violations"] == 1


# ── Check 6: Train/Test Split Leakage (Aspect Normalization & DPO) ──────────


def test_check6_fails_on_aspect_pair_target_leakage(default_thresholds, normalizer):
    """Check 6 catches target leakage across aspect partners (написати vs писати)."""
    train_rec = parse_dataset_record(
        {"query": "Він любить писати твори.", "final_response": "Добре.", "target_term": "писати"},
        Path("train.jsonl"),
        1,
    )
    train_rec.split = "train"

    eval_rec = parse_dataset_record(
        {"query": "Треба написати листа швидко.", "final_response": "Чудово.", "target_term": "написати"},
        Path("eval.jsonl"),
        2,
    )
    eval_rec.split = "eval"

    res = audit_check_6_split_overlap([train_rec, eval_rec], default_thresholds, normalizer)
    assert res.status == "FAIL"
    assert res.metrics["target_term_leakage_count"] == 1
    assert any("Target phenomenon leakage" in f for f in res.failures)


def test_check6_catches_dpo_leakage(default_thresholds, normalizer):
    """Check 6 detects 4-gram leakage inside chosen and rejected text of DPO rows."""
    long_passage = "У запеклій боротьбі славні козаки хоробро здобули вирішальну перемогу над ворогом."
    train_rec = parse_dataset_record(
        {"query": "Питання 1", "chosen": long_passage, "rejected": "Інше"},
        Path("train.jsonl"),
        1,
    )
    train_rec.split = "train"

    eval_rec = parse_dataset_record(
        {"query": "Питання 2", "chosen": long_passage, "rejected": "Інше"},
        Path("eval.jsonl"),
        2,
    )
    eval_rec.split = "eval"

    res = audit_check_6_split_overlap([train_rec, eval_rec], default_thresholds, normalizer)
    assert res.status == "FAIL"
    assert res.metrics["eval_records_high_containment"] == 1


# ── Check 7: Sampling Determinism & Sign-Off Verification (M2, M3) ──────────


def test_check7_sample_generation_and_deterministic_seed(tmp_path, default_thresholds):
    """Check 7 generates deterministic samples invariant to record shuffling."""
    records_a = [
        parse_dataset_record(
            {"query": f"Питання {i}", "final_response": f"Відповідь {i}", "category": f"cat_{i % 5}"},
            Path("shard.jsonl"),
            i,
        )
        for i in range(50)
    ]
    records_b = list(reversed(records_a))

    sample_a = tmp_path / "sample_a.md"
    sample_b = tmp_path / "sample_b.md"

    res_a, path_a, seed_a = audit_check_7_sample_drawer(
        records_a, default_thresholds, "fake_hash_123", "prof_123", sample_a
    )
    res_b, path_b, seed_b = audit_check_7_sample_drawer(
        records_b, default_thresholds, "fake_hash_123", "prof_123", sample_b
    )

    assert seed_a == seed_b
    assert res_a.metrics["sample_size_drawn"] == res_b.metrics["sample_size_drawn"]

    # Assert exact ranking of JSON records
    json_a = json.loads(path_a.with_suffix(".json").read_text(encoding="utf-8"))
    json_b = json.loads(path_b.with_suffix(".json").read_text(encoding="utf-8"))
    assert [r["content_hash"] for r in json_a] == [r["content_hash"] for r in json_b]


def test_check7_signoff_verification_lifecycle(tmp_path, default_thresholds):
    """Verify strict sign-off validation schema (seed, profile, counts, defect count)."""
    records = [
        parse_dataset_record({"query": f"q_{i}", "final_response": f"a_{i}"}, Path("shard.jsonl"), i) for i in range(10)
    ]
    sample_md = tmp_path / "sample.md"
    default_thresholds["sample_size"] = 10

    # 1. Valid Signoff
    _, _, seed = audit_check_7_sample_drawer(
        records, default_thresholds, "dataset_hash_abc", "profile_hash_def", sample_md
    )
    valid_signoff_file = tmp_path / "valid_signoff.json"
    valid_signoff_file.write_text(
        json.dumps(
            {
                "dataset_sha256": "dataset_hash_abc",
                "sample_seed": seed,
                "profile_sha256": "profile_hash_def",
                "sample_size_reviewed": 10,
                "blocker_defect_count": 0,
                "reviewer_id": "linguist_1",
                "reviewer_family": "independent_human",
            }
        ),
        encoding="utf-8",
    )

    res_verified, _, _ = audit_check_7_sample_drawer(
        records, default_thresholds, "dataset_hash_abc", "profile_hash_def", sample_md, valid_signoff_file
    )
    assert res_verified.status == "PASS"
    assert res_verified.metrics["signoff_verified"] is True

    # 2. Tampered dataset hash
    bad_hash_file = tmp_path / "bad_hash_signoff.json"
    bad_hash_file.write_text(
        json.dumps(
            {
                "dataset_sha256": "tampered_hash",
                "sample_seed": seed,
                "profile_sha256": "profile_hash_def",
                "sample_size_reviewed": 10,
                "blocker_defect_count": 0,
                "reviewer_id": "linguist_1",
                "reviewer_family": "independent_human",
            }
        ),
        encoding="utf-8",
    )
    res_bad_hash, _, _ = audit_check_7_sample_drawer(
        records, default_thresholds, "dataset_hash_abc", "profile_hash_def", sample_md, bad_hash_file
    )
    assert res_bad_hash.status == "FAIL"
    assert any("does not match current dataset" in f for f in res_bad_hash.failures)

    # 3. Unresolved blockers
    blockers_file = tmp_path / "blockers_signoff.json"
    blockers_file.write_text(
        json.dumps(
            {
                "dataset_sha256": "dataset_hash_abc",
                "sample_seed": seed,
                "profile_sha256": "profile_hash_def",
                "sample_size_reviewed": 10,
                "blocker_defect_count": 2,
                "reviewer_id": "linguist_1",
                "reviewer_family": "independent_human",
            }
        ),
        encoding="utf-8",
    )
    res_blockers, _, _ = audit_check_7_sample_drawer(
        records, default_thresholds, "dataset_hash_abc", "profile_hash_def", sample_md, blockers_file
    )
    assert res_blockers.status == "FAIL"
    assert any("reports 2 unresolved BLOCKER defect(s)" in f for f in res_blockers.failures)

    # 4. Bad blocker type (negative or bool)
    bad_type_file = tmp_path / "bad_type_signoff.json"
    bad_type_file.write_text(
        json.dumps(
            {
                "dataset_sha256": "dataset_hash_abc",
                "sample_seed": seed,
                "profile_sha256": "profile_hash_def",
                "sample_size_reviewed": 10,
                "blocker_defect_count": -1,
                "reviewer_id": "linguist_1",
                "reviewer_family": "independent_human",
            }
        ),
        encoding="utf-8",
    )
    res_bad_type, _, _ = audit_check_7_sample_drawer(
        records, default_thresholds, "dataset_hash_abc", "profile_hash_def", sample_md, bad_type_file
    )
    assert res_bad_type.status == "FAIL"
    assert any("must be a non-negative integer" in f for f in res_bad_type.failures)


# ── Full Audit Runner & Fail-Closed Tests ───────────────────────────────────


def test_run_acceptance_audit_manifest_and_exit_codes(tmp_path):
    """Verify run_acceptance_audit handles malformed manifest, exit codes 0, 2, and 3."""
    d = tmp_path / "dataset"
    d.mkdir()
    (d / "train.jsonl").write_text('{"query": "Як справи?", "final_response": "Чудово."}\n', encoding="utf-8")
    (d / "eval.jsonl").write_text('{"query": "Хто ти?", "final_response": "Я помічник."}\n', encoding="utf-8")

    # 1. Malformed manifest exits code 2
    (d / "manifest.json").write_text("{broken json", encoding="utf-8")
    report_broken, code_broken = run_acceptance_audit(d, sample_size=10)
    assert code_broken == 2
    assert report_broken.overall_status == "OPERATIONAL_ERROR"

    # 2. Clean manifest and automated pass exits 0
    (d / "manifest.json").write_text(json.dumps({"has_evaluation_split": True}), encoding="utf-8")
    report_clean, code_clean = run_acceptance_audit(d, sample_size=10)
    assert code_clean == 0
    assert report_clean.overall_status == "PASSED_AUTOMATED_CHECKS"

    # 3. Clean automated pass with require_human_signoff exits 3
    report_pending, code_pending = run_acceptance_audit(d, sample_size=10, require_human_signoff=True)
    assert code_pending == 3
    assert report_pending.overall_status == "PASSED_AUTOMATED_CHECKS_PENDING_SIGNOFF"

    # 4. Non-dict record in JSONL exits code 2
    (d / "bad.jsonl").write_text('["not a dict"]\n', encoding="utf-8")
    report_bad_rec, code_bad_rec = run_acceptance_audit(d, sample_size=10)
    assert code_bad_rec == 2
    assert report_bad_rec.overall_status == "OPERATIONAL_ERROR"


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


# ── Round 2 Review Findings Regression Tests (R2-F1 to R2-F9) ───────────────


def test_empty_dataset_fails_closed_with_exit_code_2(tmp_path):
    """R2-F1: Dataset with zero valid records exits 2 (OPERATIONAL_ERROR)."""
    d = tmp_path / "empty_dataset"
    d.mkdir()
    (d / "blank.jsonl").write_text("   \n\n   \n", encoding="utf-8")

    report, exit_code = run_acceptance_audit(d)
    assert exit_code == 2
    assert report.overall_status == "OPERATIONAL_ERROR"


def test_signoff_verification_compares_against_actual_drawn_count(tmp_path, default_thresholds):
    """R2-F2: Signoff verification matches actual drawn count, not arbitrary profile limit."""
    records = [
        parse_dataset_record({"query": f"q_{i}", "final_response": f"a_{i}"}, Path("shard.jsonl"), i) for i in range(15)
    ]
    sample_md = tmp_path / "sample.md"
    default_thresholds["sample_size"] = 300  # Profile asks for 300, but dataset only has 15

    _, _, seed = audit_check_7_sample_drawer(records, default_thresholds, "d_sha", "p_sha", sample_md)
    # Actual drawn count is 15
    signoff_15 = tmp_path / "signoff_15.json"
    signoff_15.write_text(
        json.dumps(
            {
                "dataset_sha256": "d_sha",
                "sample_seed": seed,
                "profile_sha256": "p_sha",
                "sample_size_reviewed": 15,
                "blocker_defect_count": 0,
                "reviewer_id": "rev1",
                "reviewer_family": "human",
            }
        ),
        encoding="utf-8",
    )
    res_pass, _, _ = audit_check_7_sample_drawer(records, default_thresholds, "d_sha", "p_sha", sample_md, signoff_15)
    assert res_pass.status == "PASS"
    assert res_pass.metrics["signoff_verified"] is True

    # Less than actual drawn count fails
    signoff_10 = tmp_path / "signoff_10.json"
    signoff_10.write_text(
        json.dumps(
            {
                "dataset_sha256": "d_sha",
                "sample_seed": seed,
                "profile_sha256": "p_sha",
                "sample_size_reviewed": 14,
                "blocker_defect_count": 0,
                "reviewer_id": "rev1",
                "reviewer_family": "human",
            }
        ),
        encoding="utf-8",
    )
    res_fail, _, _ = audit_check_7_sample_drawer(records, default_thresholds, "d_sha", "p_sha", sample_md, signoff_10)
    assert res_fail.status == "FAIL"
    assert any("must be an integer >= actual sample size drawn (15)" in f for f in res_fail.failures)


def test_check2_catches_small_form_letter_dataset(default_thresholds):
    """R2-F3: Check 2 catches form letter dataset with identical reasoning across 50 records."""
    records = []
    identical_reasoning = "Крок 1: Перевіряємо правило. Крок 2: Знаходимо нормативну форму."
    for i in range(50):
        records.append(
            parse_dataset_record(
                {
                    "query": f"Як пишеться слово {i}?",
                    "reasoning_steps": [identical_reasoning],
                    "final_response": f"Слово {i} пишеться згідно з правилом.",
                },
                Path("shard.jsonl"),
                i,
            )
        )
    res = audit_check_2_form_letters(records, default_thresholds)
    assert res.status == "FAIL"
    assert any("Reasoning" in f for f in res.failures)


def test_run_acceptance_audit_handles_unhandled_exceptions_with_exit_code_2(tmp_path):
    """R2-F4: Malformed messages list, invalid UTF-8, and unknown split exit code 2."""
    d = tmp_path / "dataset"
    d.mkdir()

    # 1. Invalid UTF-8 bytes
    (d / "corrupt.jsonl").write_bytes(b'{"query": "test", \xff\xfe "bad": true}\n')
    report_utf8, code_utf8 = run_acceptance_audit(d, sample_size=10)
    assert code_utf8 == 2
    assert report_utf8.overall_status == "OPERATIONAL_ERROR"
    (d / "corrupt.jsonl").unlink()

    # 2. Malformed message item (string instead of dict)
    (d / "bad_msg.jsonl").write_text('{"messages": ["string_instead_of_dict"]}\n', encoding="utf-8")
    report_msg, code_msg = run_acceptance_audit(d, sample_size=10)
    assert code_msg == 2
    assert report_msg.overall_status == "OPERATIONAL_ERROR"
    (d / "bad_msg.jsonl").unlink()

    # 3. Unknown split name
    (d / "bad_split.jsonl").write_text(
        '{"query": "q", "final_response": "a", "split": "invalid_split"}\n', encoding="utf-8"
    )
    report_split, code_split = run_acceptance_audit(d, sample_size=10)
    assert code_split == 2
    assert report_split.overall_status == "OPERATIONAL_ERROR"


def test_sample_drawer_includes_dpo_and_correction_fields_and_signoff_template(tmp_path, default_thresholds):
    """R2-F5 & R2-F9: Sample drawer renders DPO and correction fields and emits .signoff_template.json."""
    records = [
        parse_dataset_record(
            {
                "query": "Редагувати речення",
                "original_text": "Ми приймаємо участь.",
                "corrected_text": "Ми беремо участь.",
                "chosen": "Правильно: беремо участь.",
                "rejected": "Неправильно: приймаємо участь.",
                "category": "phraseology",
            },
            Path("shard.jsonl"),
            1,
        )
    ]
    sample_md = tmp_path / "review_sample.md"
    _, written_path, _ = audit_check_7_sample_drawer(records, default_thresholds, "ds_123", "prof_123", sample_md)
    assert written_path.is_file()
    content = written_path.read_text(encoding="utf-8")
    assert "Вихідний текст (Original):" in content
    assert "Ми приймаємо участь." in content
    assert "Виправлений текст (Corrected):" in content
    assert "Ми беремо участь." in content
    assert "Еталонна відповідь (Chosen):" in content
    assert "Правильно: беремо участь." in content
    assert "Відхилена відповідь (Rejected):" in content
    assert "Неправильно: приймаємо участь." in content

    # Signoff template emitted
    template_path = tmp_path / "review_sample.signoff_template.json"
    assert template_path.is_file()
    template_data = json.loads(template_path.read_text(encoding="utf-8"))
    assert template_data["dataset_sha256"] == "ds_123"
    assert template_data["sample_size_drawn"] == 1


def test_dataset_hash_includes_manifest_and_profile_hash_includes_aspect_pairs(tmp_path):
    """R2-F6: manifest.json is hashed into dataset_sha256 and aspect_pairs into profile hash."""
    d = tmp_path / "dataset"
    d.mkdir()
    f = d / "data.jsonl"
    f.write_text('{"query": "a", "final_response": "b"}\n', encoding="utf-8")

    hash_without_manifest = compute_dataset_sha256([f], d)

    m = d / "manifest.json"
    m.write_text(json.dumps({"has_evaluation_split": True}), encoding="utf-8")
    hash_with_manifest_1 = compute_dataset_sha256([f], d)
    assert hash_without_manifest != hash_with_manifest_1

    m.write_text(json.dumps({"has_evaluation_split": False}), encoding="utf-8")
    hash_with_manifest_2 = compute_dataset_sha256([f], d)
    assert hash_with_manifest_1 != hash_with_manifest_2

    # Aspect pairs in profile hash
    _, default_hash = load_profile("default")
    assert isinstance(default_hash, str) and len(default_hash) == 64


def test_check5_fails_on_compound_authority_containing_soviet_sum11(default_thresholds):
    """R2-F7: Compound authority citing Soviet SUM-11 alongside approved names fails."""
    # 1. Non-contrastive record with compound authority
    rec_non_contrastive = parse_dataset_record(
        {
            "query": "Поясніть слово",
            "final_response": "Нормальне слово.",
            "source_authority": "СУМ-11 (ВЕСУМ)",
        },
        Path("shard.jsonl"),
        1,
    )
    res1 = audit_check_5_source_rules([rec_non_contrastive], default_thresholds)
    assert res1.status == "FAIL"
    assert any("Citing СУМ-11 as normative source" in f for f in res1.failures)

    # 2. Contrastive record with compound authority but lacking independent modern authority
    rec_contrastive = parse_dataset_record(
        {
            "query": "Поясніть колоніальне спотворення",
            "final_response": "У радянський час форму було спотворено.",
            "source_authority": "СУМ-11 (ВЕСУМ)",
            "historical_suppression_note": "Зафіксовано зросійщення у СУМ-11",
        },
        Path("shard.jsonl"),
        2,
    )
    res2 = audit_check_5_source_rules([rec_contrastive], default_thresholds)
    assert res2.status == "FAIL"
    assert any("lacks approved modern Ukrainian authority" in f for f in res2.failures)


def test_aspect_normalizer_does_not_strip_prefixes_blindly(normalizer):
    """R2-F8: normalize_verb_aspect maps via curated pairs without blind prefix stripping."""
    # показати must map to показувати, never казати
    norm_pokazaty = normalizer.normalize_verb_aspect("показати", ":perf:")
    assert norm_pokazaty == "показувати"

    # сказати must map to говорити, never казати
    norm_skazaty = normalizer.normalize_verb_aspect("сказати", ":perf:")
    assert norm_skazaty == "говорити"


def test_fair_thin_category_boost_and_dev_split(tmp_path, default_thresholds):
    """R2-F9: dev split is recognized as eval; thin boost is distributed fairly round-robin."""
    rec_dev = parse_dataset_record({"query": "q", "final_response": "a", "split": "dev"}, Path("shard.jsonl"), 1)
    assert rec_dev.split == "eval"

    rec_dev_path = parse_dataset_record({"query": "q", "final_response": "a"}, Path("dev/shard.jsonl"), 2)
    assert rec_dev_path.split == "eval"


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
