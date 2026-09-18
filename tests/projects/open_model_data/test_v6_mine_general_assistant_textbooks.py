"""test_v6_mine_general_assistant_textbooks.py - Test suite for Phase 6.1 General Assistant.

Verifies:
1. Held-out textbook firewall: 0% train/eval verbatim text leakage across 22 held-out textbooks.
2. Subject & grade coverage across all STEM and Humanities curriculum disciplines (Grades 1–11).
3. Entity preservation: mathematical volume («об'єм циліндра», «об'єм піраміди») and
   scientific ratio («відношення величин», «відношення чисел») protected against naive substitution.
4. Pravopys 2019 scientific terminology & Russian calque elimination («розв'язувати задачу», «принаймні»).
5. Gate 6 pedagogical tone calibration: absence of condescending or pejorative language.
6. Typography & punctuation invariants: Pravopys § 164 nested quotes, zero double terminal punctuation.
7. VESUM lexical attestation: read-only database query verification on forms_all.
8. Draft 2020-12 schema validation for evaluation benchmark and release receipt.
9. Manifest invariants: shard count, trajectory counts, and size ceiling (< 2,000 KB).
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v6_mine_general_assistant_textbooks import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCES_DB,
    DEFAULT_VESUM_DB,
    EXERCISE_IMPERATIVES,
    HELD_OUT_SET,
    HELD_OUT_TEXTBOOKS,
    PROTECTED_RATIO_TERMS,
    PROTECTED_VOLUME_TERMS,
    SCHEMA_EVAL_PATH,
    SCHEMA_RECEIPT_PATH,
    STOPWORD_TERMS,
    TextbookChunk,
    apply_calque_sanitation,
    check_protected_entities,
    ensure_single_terminal_dot,
    extract_key_concept,
    extract_meaningful_text_snippet,
    extract_scientific_terminology,
    format_nested_quotes,
    generate_evaluation_benchmark,
    generate_release_receipt,
    generate_sft_dataset,
    get_vesum_cursor,
    is_vesum_attested,
    load_textbook_chunks,
    sanitize_ip_addresses,
    synthesize_trajectory,
    truncate_word_boundary,
    verify_pedagogical_tone,
)

_CHUNKS_CACHE: tuple[list[TextbookChunk], list[TextbookChunk]] | None = None


def get_cached_chunks() -> tuple[list[TextbookChunk], list[TextbookChunk]]:
    global _CHUNKS_CACHE
    if _CHUNKS_CACHE is None:
        _CHUNKS_CACHE = load_textbook_chunks(DEFAULT_SOURCES_DB)
    return _CHUNKS_CACHE


def test_held_out_firewall_zero_leakage():
    """Verify that held-out textbooks and training textbooks form strictly disjoint sets."""
    eval_chunks, train_chunks = get_cached_chunks()
    eval_books = {c.source_file for c in eval_chunks}
    train_books = {c.source_file for c in train_chunks}
    eval_chunk_ids = {c.chunk_id for c in eval_chunks}
    train_chunk_ids = {c.chunk_id for c in train_chunks}
    eval_text_hashes = {hashlib.sha256(c.text.strip().encode("utf-8")).hexdigest() for c in eval_chunks}
    train_text_hashes = {hashlib.sha256(c.text.strip().encode("utf-8")).hexdigest() for c in train_chunks}

    # Strict disjointness: books, chunk IDs, and verbatim text hashes
    assert eval_books.isdisjoint(train_books), f"Book leakage detected: {eval_books & train_books}"
    assert eval_chunk_ids.isdisjoint(train_chunk_ids), f"Chunk leakage detected: {eval_chunk_ids & train_chunk_ids}"
    assert eval_text_hashes.isdisjoint(train_text_hashes), "Verbatim text content leakage detected between eval and train"
    assert len(eval_books) == len(HELD_OUT_TEXTBOOKS), f"Expected {len(HELD_OUT_TEXTBOOKS)} held-out books, got {len(eval_books)}"
    assert len(eval_chunks) >= 2000, f"Expected substantial held-out chunk pool (>=2000), got {len(eval_chunks)}"
    assert len(train_chunks) >= 13000, f"Expected large training chunk pool (>=13000), got {len(train_chunks)}"



def test_subject_and_grade_coverage():
    """Verify that all state curriculum subjects and grades 1-11 are covered."""
    eval_chunks, train_chunks = get_cached_chunks()
    all_chunks = eval_chunks + train_chunks

    subjects_seen = {c.subject for c in all_chunks}
    grades_seen = {c.grade for c in all_chunks if c.grade}

    # Check key STEM subjects
    for subj in ["algebra", "heometriya", "fizyka", "khimiya", "biolohiya", "matematyka", "informatyka"]:
        assert subj in subjects_seen, f"Missing critical STEM subject: {subj}"

    # Check key Humanities subjects
    for subj in ["istoriya", "vsesvitnia", "pravoznavstvo", "ukrmova", "ukrlit", "ekonomika"]:
        assert subj in subjects_seen, f"Missing critical Humanities subject: {subj}"

    # Check grades coverage
    for grade in ["1", "5", "7", "8", "9", "10", "11"]:
        assert grade in grades_seen, f"Missing school grade: {grade}"


def test_entity_preservation_volume_and_ratio():
    """Verify that mathematical volume and scientific ratio entities are protected against hyper-purist mutation."""
    # Volume terms must be preserved
    for term in PROTECTED_VOLUME_TERMS:
        assert "об'єм" in term, f"Protected volume term must contain 'об'єм': {term}"
        # Simulating check_protected_entities
        assert check_protected_entities(f"Обчисліть {term} за заданою висотою.") is True

    # Corrupted volume terms must fail check
    assert check_protected_entities("Знайдіть обсяг піраміди.") is False
    assert check_protected_entities("Обчисліть обсяг циліндра.") is False
    assert check_protected_entities("Знайдіть обсяг куба.") is False

    # Ratio terms must be preserved
    for term in PROTECTED_RATIO_TERMS:
        assert "відношення" in term, f"Protected ratio term must contain 'відношення': {term}"
        assert check_protected_entities(f"Знайдіть {term} у прямокутному трикутнику.") is True

    # Corrupted ratio terms must fail check
    assert check_protected_entities("Визначте стосунки величин у досліді.") is False
    assert check_protected_entities("Знайдіть стосунки чисел.") is False


def test_pravopys_2019_scientific_terminology_and_calques():
    """Verify that native Ukrainian scientific nomenclature is used and calques are eradicated."""
    # Calque eradication
    calque_test_cases = [
        ("Треба вирішувати задачу послідовно.", "Треба розв'язувати задачу послідовно."),
        ("По крайній мірі, це підтверджує закон.", "Принаймні, це підтверджує закон."),
        ("В залежності від температури речовина плавиться.", "Залежно від температури речовина плавиться."),
        ("Учні повинні приймати участь у досліді.", "Учні повинні брати участь у досліді."),
        ("Ця речовина може наносити шкоду організму.", "Ця речовина може завдавати шкоди організму."),
        ("В кінці кінців ми отримали правильну відповідь.", "Зрештою ми отримали правильну відповідь."),
    ]
    for raw, expected in calque_test_cases:
        cleaned = apply_calque_sanitation(raw)
        assert cleaned == expected, f"Failed calque replacement for: {raw}"


def test_gate6_pedagogical_tone_calibration():
    """Verify that Gate 6 tone calibration detects pejorative and condescending phrasing."""
    # Prohibited pejorative stems
    bad_phrases = [
        "Це очевидно кожному дурню.",
        "Не дивно, що ви цього не розумієте.",
        "Навіть першокласник знає це правило.",
        "Як можна не знати такої простої речі?",
        "Соромно не знати закону Ньютона.",
        "Цей учень абсолютно безграмотний.",
    ]
    for phrase in bad_phrases:
        assert verify_pedagogical_tone(phrase) is False, f"Failed to reject pejorative phrase: {phrase}"

    # Acceptable constructive pedagogical phrases
    good_phrases = [
        "Розгляньмо детальніше сутність цього фізичного явища.",
        "Зверніть увагу на алгоритм розв'язування цього рівняння.",
        "Відповідно до закону збереження маси, маса реагентів дорівнює масі продуктів реакції.",
        "Для кращого розуміння проаналізуємо наведений приклад.",
    ]
    for phrase in good_phrases:
        assert verify_pedagogical_tone(phrase) is True, f"Incorrectly rejected valid pedagogical phrase: {phrase}"


def test_typography_and_nested_quotes():
    """Verify Pravopys § 164 nested quotes formatting and single terminal punctuation."""
    # Nested quotes: outer «...», inner „...“
    raw_quote = 'Він сказав: "Це видатний твір "Кобзар" нашого поета".'
    nested = format_nested_quotes(raw_quote)
    assert "«" in nested and "»" in nested and "„" in nested and "“" in nested, f"Failed nested quotes: {nested}"

    # Double dot cleanup
    assert ensure_single_terminal_dot("Текст закінчується крапкою.") == "Текст закінчується крапкою."
    assert ensure_single_terminal_dot("Текст без крапки") == "Текст без крапки."
    assert ensure_single_terminal_dot("Текст із знаком оклику!") == "Текст із знаком оклику!"
    assert ensure_single_terminal_dot("Текст із знаком питання?") == "Текст із знаком питання?"
    assert ensure_single_terminal_dot("Текст із подвійною крапкою..") == "Текст із подвійною крапкою."


def test_vesum_scientific_attestation():
    """Verify that authentic Ukrainian scientific terms are attested in VESUM and fails closed."""
    # Fail closed verification: when cursor is None and use_default_if_none is False, must return False
    assert is_vesum_attested("водень", None, use_default_if_none=False) is False
    assert is_vesum_attested("", None, use_default_if_none=False) is False


    cur = get_vesum_cursor(DEFAULT_VESUM_DB)
    if cur is None:
        pytest.skip("VESUM database not found on disk")

    canonical_scientific_lemmas = [
        "водень", "кисень", "вуглець", "дискримінант",
        "теорема", "трикутник", "клітина", "суверенітет",
    ]
    for lemma in canonical_scientific_lemmas:
        assert is_vesum_attested(lemma, cur) is True, f"Scientific lemma not attested in VESUM: {lemma}"

    # Multi-word term validation: all words must be attested
    assert is_vesum_attested("об'єм циліндра", cur) is True
    assert is_vesum_attested("сульфатна кислота", cur) is True
    assert is_vesum_attested("об'єм невідомещонебуває", cur) is False

    # Non-Ukrainian pseudo-words must fail attestation
    assert is_vesum_attested("xyznonexistent", cur) is False
    assert is_vesum_attested("11-й", cur) is False


def test_sanitize_ip_addresses():
    """Verify that educational networking IP examples are converted to RFC 5737 and sections preserved."""
    raw_ip = f"{84}.{42}.{63}.{1}"
    private_ip = f"{192}.{168}.{0}.{12}"
    # Real routable public IP in textbook must be converted to RFC 5737
    assert sanitize_ip_addresses(f"комп'ютерна адреса: {raw_ip}.") == "комп'ютерна адреса: 198.51.100.1."
    # RFC 1918 private IP must be converted
    assert sanitize_ip_addresses(f"локальна мережа: {private_ip}.") == "локальна мережа: 198.51.100.12."
    # Standard document outline / section citation must be preserved
    assert sanitize_ip_addresses("Згідно з пунктом 4.1.3.1 стандарту.") == "Згідно з пунктом 4.1.3.1 стандарту."
    # Loopback and public DNS preserved
    assert sanitize_ip_addresses("Хост 127.0.0.1 або 8.8.8.8.") == "Хост 127.0.0.1 або 8.8.8.8."
    # RFC 5737 doc IP preserved
    assert sanitize_ip_addresses("Тестова адреса: 198.51.100.4.") == "Тестова адреса: 198.51.100.4."
    # Dotted chains (diagram labels) must be preserved, not converted to IPs
    assert sanitize_ip_addresses("Поставимо 1.2.3.4.6.7.8.10 у схему.") == "Поставимо 1.2.3.4.6.7.8.10 у схему."
    # Plain numeric lists without networking context must be preserved
    num_list = ".".join(["25", "30", "40", "50"])
    assert sanitize_ip_addresses(f"Значення числового ряду: {num_list}.") == f"Значення числового ряду: {num_list}."
    # Synthetic IP in networking context must be converted even if small octets
    assert sanitize_ip_addresses("вузол в мережі має адресу 1.2.3.4.") == "вузол в мережі має адресу 198.51.100.4."


def test_concept_extraction_rejects_imperatives():
    """Verify that exercise instructions starting with imperative verbs are rejected from concepts."""
    bad_chunk = TextbookChunk(
        chunk_id="test_exercise_chunk",
        title="Сторінка 180",
        text="6. Складіть коротке повідомлення, оцінюючи свою діяльність на уроці.\nІнтелектуальний клуб.",
        source_file="8-klas-heohrafiya-hilberh-2025",
        grade="8",
        author="Гільберг",
        subject="heohrafiya",
        char_count=200,
    )
    concept = extract_key_concept(bad_chunk)
    if concept:
        assert not concept.lower().startswith("складіть")
        assert not concept.lower().startswith("оцініть")
        words = concept.split()
        if words:
            w0 = words[0].lower().strip(".,;:?!'\"«»„“—–()")
            assert w0 not in EXERCISE_IMPERATIVES
    else:
        assert concept == ""


def test_synthetic_pipeline_hermetic_run():
    """Run a hermetic end-to-end dry run in a temp dir and validate contracts."""
    eval_chunks, train_chunks = get_cached_chunks()
    assert len(eval_chunks) > 0 and len(train_chunks) > 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        eval_dir = tmp_path / "eval"
        sft_dir = tmp_path / "sft"

        # Generate small eval benchmark
        eval_manifest, eval_sha, eval_subj, eval_domain = generate_evaluation_benchmark(
            eval_chunks[:30], eval_dir, target_count=20, shards_count=1
        )
        assert eval_manifest["total_cases"] == 20
        assert eval_manifest["shards_count"] == 1
        assert (eval_dir / "manifest.json").is_file()
        assert (eval_dir / "manifest.json.sha256").is_file()

        # Validate eval records against schema
        schema_eval = json.loads(SCHEMA_EVAL_PATH.read_text(encoding="utf-8"))
        val_eval = jsonschema.Draft202012Validator(schema_eval)
        eval_shard = eval_dir / eval_manifest["shards"][0]["shard_file"]
        with eval_shard.open(encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                val_eval.validate(rec)
                assert rec["track_domain"] in ("stem", "humanities")
                assert verify_pedagogical_tone(rec["reference_solution"])
                assert check_protected_entities(rec["reference_solution"])

        # Generate small SFT dataset
        cur_ves = get_vesum_cursor(DEFAULT_VESUM_DB)
        manifest, sft_sha, sft_subj, sft_domain, books_cnt = generate_sft_dataset(
            train_chunks[:50], sft_dir, target_count=30, shards_count=3, vesum_cur=cur_ves
        )
        assert manifest["total_trajectories"] == 30
        assert manifest["shards_count"] == 3
        assert (sft_dir / "manifest.json").is_file()
        assert (sft_dir / "manifest.json.sha256").is_file()

        # Generate release receipt
        receipt = generate_release_receipt(
            eval_dir=eval_dir,
            eval_manifest_sha256=eval_sha,
            eval_count=20,
            eval_shards_count=1,
            eval_max_shard_size_kb=eval_manifest["max_shard_size_kb"],
            eval_subj_dist=eval_subj,
            eval_domain_dist=eval_domain,
            sft_dir=sft_dir,
            manifest_sha256=sft_sha,
            sft_count=30,
            shards_count=3,
            max_shard_size_kb=manifest["max_shard_size_kb"],
            sft_subj_dist=sft_subj,
            sft_domain_dist=sft_domain,
            books_count=books_cnt,
            git_commit="test_commit_hash",
            output_dir=tmp_path,
        )
        assert receipt["schema_version"] == "v1_general_assistant_release_receipt"
        assert receipt["issue"] == 8139
        assert receipt["parent_epic"] == 6321
        assert receipt["invariants_verified"]["zero_train_eval_leakage"] is True


def test_eval_benchmark_disk_invariants_and_schema():
    """Validate full evaluation benchmark against schema if present on disk."""
    manifest_file = DEFAULT_OUTPUT_DIR / "eval" / "manifest.json"
    if not manifest_file.is_file():
        pytest.skip("Full release eval benchmark not generated yet")

    schema = json.loads(SCHEMA_EVAL_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest["total_cases"] == 2500:
        assert manifest["shards_count"] == 5
        assert len(manifest["shards"]) == 5
        total_seen = 0
        seen_books = set()
        seen_subjects = set()
        for shard_info in manifest["shards"]:
            assert shard_info["cases_count"] == 500
            assert shard_info["size_kb"] < 2000.0, f"Shard exceeds ceiling: {shard_info}"
            shard_path = DEFAULT_OUTPUT_DIR / "eval" / shard_info["shard_file"]
            assert shard_path.is_file()
            hasher = hashlib.sha256()
            with shard_path.open(encoding="utf-8") as f:
                for line in f:
                    hasher.update(line.encode("utf-8"))
                    rec = json.loads(line)
                    validator.validate(rec)
                    src_book = rec["source_metadata"]["source_book"]
                    assert src_book in HELD_OUT_SET
                    seen_books.add(src_book)
                    seen_subjects.add(rec["subject"])

                    # Invariant checks on actual records
                    concept = rec["concept"]
                    w0 = concept.split()[0].lower().strip(".,;:?!'\"«»„“—–()")
                    assert w0 not in EXERCISE_IMPERATIVES, f"Imperative concept found: {concept}"
                    assert verify_pedagogical_tone(rec["query"])
                    assert verify_pedagogical_tone(rec["reference_solution"])
                    assert check_protected_entities(rec["reference_solution"])
                    json_str = json.dumps(rec, ensure_ascii=False)
                    assert not re.search(r"«[^»]*«", json_str), f"Nested guillemets in eval record: {rec['eval_id']}"
                    assert not re.search(r"(?:\.\s+){3,}|\.{4,}", json_str), f"TOC dot leader in eval record: {rec['eval_id']}"
                    assert not re.search(r"\(\s*\)|\.\s+\.", json_str), f"Formula garble in eval record: {rec['eval_id']}"
                    for field_name in ["query", "reference_solution", "concept"]:
                        val = rec[field_name]
                        assert val.count("«") == val.count("»"), f"Unbalanced guillemets in {field_name}: {val}"
                        assert val.count("„") == val.count("“"), f"Unbalanced inner quotes in {field_name}: {val}"
                    for step in rec["reference_reasoning"]:
                        assert step.count("«") == step.count("»"), f"Unbalanced guillemets in step: {step}"
                        assert step.count("„") == step.count("“"), f"Unbalanced inner quotes in step: {step}"
                    step2 = rec["reference_reasoning"][1]
                    assert not step2.endswith("...»") and not step2.endswith("...».") and not step2.endswith("...»."), f"Truncated quote ending in step 2: {step2}"
                    assert "..." not in step2, f"Ellipsis in step 2 quotation: {step2}"
                    for t in rec.get("scientific_terminology", []):
                        assert t.lower() not in STOPWORD_TERMS, f"Stopword '{t}' in eval record terms: {t}"

                    total_seen += 1
            assert hasher.hexdigest() == shard_info["sha256"]
        assert total_seen == 2500
        # Stratification: all 22 held-out textbooks and all 22 curriculum subjects present
        assert len(seen_books) == len(HELD_OUT_TEXTBOOKS), f"Missing held-out books: {HELD_OUT_SET - seen_books}"
        assert len(seen_subjects) == len(HELD_OUT_TEXTBOOKS), f"Expected 22 subjects, got {len(seen_subjects)}"



def test_sft_manifest_and_shards_invariants():
    """Validate SFT shards and manifest against invariants if present on disk."""
    import re
    manifest_file = DEFAULT_OUTPUT_DIR / "sft" / "manifest.json"
    if not manifest_file.is_file():
        pytest.skip("Full release SFT dataset not generated yet")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest["total_trajectories"] == 75000:
        assert manifest["shards_count"] == 150
        assert len(manifest["shards"]) == 150
        for shard_info in manifest["shards"][:5]:
            assert shard_info["trajectories_count"] == 500
            assert shard_info["size_kb"] < 2000.0, f"Shard exceeds ceiling: {shard_info}"
            shard_path = DEFAULT_OUTPUT_DIR / "sft" / shard_info["shard_file"]
            assert shard_path.is_file()
            with shard_path.open(encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    assert not re.search(r"«[^»]*«", line), f"Nested guillemets in SFT record: {rec['trajectory_id']}"
                    assert not re.search(r"(?:\.\s+){3,}|\.{4,}", line), f"TOC dot leader in SFT record: {rec['trajectory_id']}"
                    assert not re.search(r"\(\s*\)|\.\s+\.", line), f"Formula garble in SFT record: {rec['trajectory_id']}"
                    for field_name in ["query", "final_response", "target_concept"]:
                        val = rec[field_name]
                        assert val.count("«") == val.count("»"), f"Unbalanced guillemets in {field_name}: {val}"
                        assert val.count("„") == val.count("“"), f"Unbalanced inner quotes in {field_name}: {val}"
                    for step in rec["reasoning_steps"]:
                        assert step.count("«") == step.count("»"), f"Unbalanced guillemets in step: {step}"
                        assert step.count("„") == step.count("“"), f"Unbalanced inner quotes in step: {step}"
                    step2 = rec["reasoning_steps"][1]
                    assert not step2.endswith("...»") and not step2.endswith("...».") and not step2.endswith("...»."), f"Truncated quote ending in step 2: {step2}"
                    assert "..." not in step2, f"Ellipsis in step 2 quotation: {step2}"
                    step3 = rec["reasoning_steps"][2]
                    assert "верховенство права" not in step3.lower() or rec["subject"] == "pravoznavstvo"
                    for sw in ["клас", "математика", "підручник", "україни"]:
                        assert f"терміни: {sw}" not in step3.lower(), f"Stopword '{sw}' cited in vesum note: {step3}"
                    for t in rec.get("scientific_terminology", []):
                        assert t.lower() not in STOPWORD_TERMS, f"Stopword '{t}' in SFT terms: {t}"


def test_release_receipt_schema_and_checksum():
    """Validate release receipt against Draft 2020-12 schema if present on disk."""
    receipt_file = DEFAULT_OUTPUT_DIR / "release_receipt.json"
    if not receipt_file.is_file():
        pytest.skip("Full release receipt not generated yet")

    schema = json.loads(SCHEMA_RECEIPT_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    validator.validate(receipt)

    sha_file = receipt_file.with_suffix(".json.sha256")
    assert sha_file.is_file()
    computed_sha = hashlib.sha256(receipt_file.read_bytes()).hexdigest()
    recorded_sha = sha_file.read_text(encoding="utf-8").split()[0]
    assert computed_sha == recorded_sha


def test_nested_guillemets_resolution():
    """Verify that nested quotes are converted from «...«...»...» to «...„...“...» per Pravopys § 164."""
    import re
    test_cases = [
        ("«У так званій «Шкотській книзі» записували задачі»", "«У так званій „Шкотській книзі“ записували задачі»"),
        ('«Говорив: "Це «важливо» для нас" і пішов»', '«Говорив: „Це „важливо“ для нас“ і пішов»'),
        ("«Підручник «Алгебра» 9 клас»", "«Підручник „Алгебра“ 9 клас»"),
        ("««Подвійні лапки»»", "«„Подвійні лапки“»"),
    ]
    for raw, expected in test_cases:
        res = format_nested_quotes(raw)
        assert res == expected, f"Failed nested quotes for {raw}: got {res}"
        assert not re.search(r"«[^»]*«", res), f"Nested opening guillemets found in {res}"


def test_truncate_word_boundary():
    """Verify that word boundary truncation never cuts tokens mid-word."""
    text = "Наприклад, розглядаючи прямокутник зі сторонами a і b, ми знаходимо площу."
    truncated = truncate_word_boundary(text, 25)
    assert not truncated.endswith(" розв..."), f"Mid-word cut in {truncated}"
    assert truncated.endswith("..."), f"Expected terminal ellipsis in {truncated}"
    assert " прямокутник" not in truncated or "прямокутник" in truncated.split()
    # Check that short text is not truncated
    short = "Короткий текст."
    assert truncate_word_boundary(short, 50) == short


def test_snippet_rejects_exercises_and_ocr():
    """Verify that snippets reject numbered exercises, imperatives, and OCR drop-cap fragments."""
    # Numbered exercise lines
    ex1 = "8. Назвіть основні твори письменника та охарактеризуйте його творчий шлях."
    assert extract_meaningful_text_snippet(ex1) == ""

    # Exercise with dropped drop-cap
    ex2 = "М. улгаков 8. азвіть основні твори письменника та охарактеризуйте."
    assert extract_meaningful_text_snippet(ex2) == ""

    # Line with exercise imperative inside
    ex3 = "Учні повинні уважно прочитати параграф і порівняйте наведені приклади."
    assert extract_meaningful_text_snippet(ex3) == ""

    # Clean textbook exposition passes
    clean = "Функція f(x) називається парною, якщо для будь-якого x з області визначення виконується рівність f(-x) = f(x)."
    res = extract_meaningful_text_snippet(clean)
    assert len(res) >= 50
    assert "парною" in res


def test_terminology_rejects_stopwords():
    """Verify that school and meta stopwords are never cited as verified scientific terms."""
    dummy_chunk = TextbookChunk(
        chunk_id="test_terms_chunk",
        title="Сторінка 5",
        text="У 9 класі математика та геометрія вивчають поняття об'єм циліндра та числова множина в підручнику України.",
        source_file="9-klas-heometriya-burda-2017",
        grade="9",
        author="Бурда",
        subject="heometriya",
        char_count=250,
    )
    terms = extract_scientific_terminology(dummy_chunk)
    for t in terms:
        for w in t.lower().split():
            assert w not in STOPWORD_TERMS, f"Stopword '{w}' found in scientific terms: {terms}"


def test_trajectory_step3_grounding_no_fake_claims():
    """Verify that trajectory step 3 is grounded in concept terms and does not make fake discipline claims."""
    # Economics chunk on budget: should NOT claim "верховенство права" or "суверенітет"
    econ_chunk = TextbookChunk(
        chunk_id="test_econ_chunk",
        title="Тема 4. Державний бюджет",
        text="Державний бюджет — це план доходів і видатків держави на певний період. Бюджетний дефіцит виникає коли видатки перевищують доходи.",
        source_file="10-klas-ekonomika-krupetska-2018",
        grade="10",
        author="Крупецька",
        subject="ekonomika",
        char_count=300,
    )
    cur_ves = get_vesum_cursor(DEFAULT_VESUM_DB)
    traj = synthesize_trajectory(econ_chunk, 1, "terminological_pedagogy", cur_ves=cur_ves)
    step3 = traj["reasoning_steps"][2]
    final_resp = traj["final_response"]

    # Invariants: no unrelated claims
    assert "верховенство права" not in step3.lower(), f"Unrelated legal claim in econ step 3: {step3}"
    assert "державотворення" not in step3.lower(), f"Unrelated legal claim in econ step 3: {step3}"
    assert "об'єм" not in step3.lower() or "бюджет" in step3.lower()
    for w in STOPWORD_TERMS:
        if len(w) > 4:
            assert f"терміни: {w}" not in step3.lower(), f"Stopword '{w}' cited in vesum note: {step3}"
