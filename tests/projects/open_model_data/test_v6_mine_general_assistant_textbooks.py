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
    DANGLING_STARTER_RE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCES_DB,
    DEFAULT_VESUM_DB,
    DEFINITIONAL_MARKER_RE,
    EXERCISE_IMPERATIVES,
    FORWARD_BACKWARD_REF_RE,
    HELD_OUT_SET,
    HELD_OUT_TEXTBOOKS,
    PROTECTED_RATIO_TERMS,
    PROTECTED_VOLUME_TERMS,
    SCHEMA_EVAL_PATH,
    SCHEMA_RECEIPT_PATH,
    STOPWORD_TERMS,
    TextbookChunk,
    apply_calque_sanitation,
    check_concept_contradiction,
    check_protected_entities,
    clean_and_validate_candidate,
    ensure_single_terminal_dot,
    extract_key_concept,
    extract_meaningful_text_snippet,
    extract_scientific_terminology,
    extract_scientific_terminology_for_snippet,
    format_nested_quotes,
    generate_evaluation_benchmark,
    generate_release_receipt,
    generate_sft_dataset,
    get_vesum_cursor,
    get_vesum_lemmas,
    has_unresolved_anaphora,
    is_concept_in_citation_form,
    is_definitional_for_concept,
    is_snippet_grounded_in_concept,
    is_vesum_attested,
    is_vesum_pronoun,
    lemmatize_noun_phrase,
    load_textbook_chunks,
    sanitize_ip_addresses,
    synthesize_eval_task,
    synthesize_trajectory,
    truncate_word_boundary,
    verify_dataset_pedagogy_tone,
    verify_entity_preservation_volume_ratio,
    verify_eval_no_fake_algorithm_claims,
    verify_pedagogical_tone,
    verify_pravopys_2019,
    verify_snippet_concept_grounding,
    verify_terms_present_in_snippet,
    verify_zero_dangling_starters,
    verify_zero_inflected_concepts,
    verify_zero_train_eval_leakage,
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
    assert len(eval_chunks) >= 180, f"Expected substantial held-out chunk pool (>=180), got {len(eval_chunks)}"
    assert len(train_chunks) >= 1500, f"Expected large training chunk pool (>=1500), got {len(train_chunks)}"



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
    """Verify that snippets reject numbered exercises, imperatives, lab lists, and OCR drop-cap fragments."""
    # Numbered exercise lines
    ex1 = "8. Назвіть основні твори письменника та охарактеризуйте його творчий шлях."
    assert extract_meaningful_text_snippet(ex1) == ""

    # Exercise with dropped drop-cap
    ex2 = "М. улгаков 8. азвіть основні твори письменника та охарактеризуйте."
    assert extract_meaningful_text_snippet(ex2) == ""

    # Line with exercise imperative inside
    ex3 = "Учні повинні уважно прочитати параграф і порівняйте наведені приклади."
    assert extract_meaningful_text_snippet(ex3) == ""

    # Lab equipment list
    ex4 = "Що знадобиться: графітовий стрижень від олівця; компас; два проводи завдовжки 30 см; паперова серветка."
    assert extract_meaningful_text_snippet(ex4) == ""

    # Exercise question with figure ref and math comparison
    ex5 = "Які з фігур, зображених на рисунку 20.23, збігаються зі своїми образами при гомотетії із центром O та коефіцієнтом k < 0?"
    assert extract_meaningful_text_snippet(ex5) == ""

    # Clean textbook exposition passes when grounded
    clean = "Функція називається парною, якщо для будь-якого значення аргументу з області визначення значення функції залишаються однаковими."
    res = extract_meaningful_text_snippet(clean, concept="парна функція", terms=["функція"])
    assert len(res) >= 50
    assert "парною" in res
    assert not res.endswith("?.")


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

    # Invariants: no unrelated claims
    assert "верховенство права" not in step3.lower(), f"Unrelated legal claim in econ step 3: {step3}"
    assert "державотворення" not in step3.lower(), f"Unrelated legal claim in econ step 3: {step3}"
    assert "об'єм" not in step3.lower() or "бюджет" in step3.lower()
    for w in STOPWORD_TERMS:
        if len(w) > 4:
            assert f"терміни: {w}" not in step3.lower(), f"Stopword '{w}' cited in vesum note: {step3}"


def test_terminology_no_bare_adjectives_or_subsets():
    """Verify that terminology extraction never produces bare adjectives or redundant subset terms."""
    dummy_chunk = TextbookChunk(
        chunk_id="test_subset_chunk",
        title="Квадратична функція та електричний струм",
        text="У цьому розділі розглядається квадратична функція, її графік, а також електричний струм і напруга.",
        source_file="9-klas-algebra-merzliak-2017",
        grade="9",
        author="Мерзляк",
        subject="algebra",
        char_count=300,
    )
    cur_ves = get_vesum_cursor(DEFAULT_VESUM_DB)
    terms = extract_scientific_terminology(dummy_chunk, cur_ves=cur_ves)

    # Bare adjective 'квадратична' must NOT be in terms
    assert "квадратична" not in terms, f"Bare adjective found in terms: {terms}"

    # Subset terms: if compound term is present, single-word subset must be dropped
    for t1 in terms:
        t1_words = set(t1.lower().split())
        for t2 in terms:
            if t1 != t2 and t1_words.issubset(set(t2.lower().split())):
                pytest.fail(f"Term '{t1}' is a subset of '{t2}' in terms: {terms}")


def test_concept_contradiction_rejection():
    """Verify that contradictory concepts and modifiers are strictly rejected."""
    # Arithmetic vs geometric
    snip_geom = "Записану рівність називають формулою n-го члена геометричної прогресії."
    assert check_concept_contradiction(snip_geom, "Арифметична прогресія") is True
    assert is_snippet_grounded_in_concept(snip_geom, "Арифметична прогресія") is False

    snip_arith = "Послідовність є арифметичною прогресією, якщо кожний наступний член більший за попередній."
    assert check_concept_contradiction(snip_arith, "Арифметична прогресія") is False
    assert is_snippet_grounded_in_concept(snip_arith, "Арифметична прогресія") is True
    assert is_snippet_grounded_in_concept(snip_arith, "Геометрична прогресія") is False

    # Even vs odd
    snip_even = "Графік парної функції є симетричним відносно осі ординат."
    assert check_concept_contradiction(snip_even, "Непарна функція") is True
    assert is_snippet_grounded_in_concept(snip_even, "Непарна функція") is False
    assert is_snippet_grounded_in_concept(snip_even, "Парна функція") is True


def test_dangling_starters_rejection():
    """Verify that anaphoric dangling starters are detected and rejected from snippets."""
    bad_starters = [
        "Записану рівність називають формулою n-го члена геометричної прогресії.",
        "Цю рівність називають формулою коренів квадратного рівняння.",
        "Цю формулу застосовують для обчислення тиску.",
        "Цей вираз є тотожністю.",
        "Цей малюнок ілюструє перебіг реакції.",
        "Звідси маємо шуканий результат для функції.",
        "Аналогічно доводиться теорема для довільного трикутника.",
        "Тому для обчислення площі використовуємо формулу.",
        "Отже, пряма є дотичною до кола.",
        "Тоді маємо рівність векторів на площині.",
        "Наприклад, число 12 є складеним.",
        "Позначимо через x шукану швидкість автомобіля.",
        "Нехай дано трикутник зі сторонами a, b і c.",
        "Підставивши значення у формулу, отримуємо розв'язок.",
        "Доведемо правильність цієї рівності методом індукції.",
        "Розглянемо приклад розв'язування лінійного рівняння.",
        "Таку рівність називають пропорцією двох величин.",
    ]
    for s in bad_starters:
        assert DANGLING_STARTER_RE.search(s), f"Failed to detect dangling starter in: {s}"
        assert is_snippet_grounded_in_concept(s, "поняття") is False

    good_sentence = "Квадрат будь-якого члена геометричної прогресії дорівнює добутку двох сусідніх із ним членів."
    assert not DANGLING_STARTER_RE.search(good_sentence)


def test_terminology_containment_in_snippet_or_concept():
    """Verify that scientific terms are strictly present in the snippet or concept (no hallucinated chunk terms)."""
    # Vectors snippet with no triangles mentioned
    snip_vec = "Вектором називають напрямлений відрізок, тобто відрізок, для якого вказано, яка з його границь є початком, а яка — кінцем."
    conc_vec = "Вектори"
    cur_ves = get_vesum_cursor(DEFAULT_VESUM_DB)
    terms = extract_scientific_terminology_for_snippet(snip_vec, conc_vec, "heometriya", cur_ves=cur_ves)

    # Invariants: no triangles, 100% containment
    assert "трикутник" not in terms, f"Irrelevant term 'трикутник' found in vector terms: {terms}"
    assert len(terms) >= 1
    snip_lemmas = get_vesum_lemmas(snip_vec, cur_ves)
    conc_lemmas = get_vesum_lemmas(conc_vec, cur_ves)
    for t in terms:
        t_lemmas = get_vesum_lemmas(t, cur_ves) or {t.lower()}
        assert (
            t.lower() in snip_vec.lower()
            or t.lower() in conc_vec.lower()
            or bool(t_lemmas & snip_lemmas)
            or bool(t_lemmas & conc_lemmas)
        ), f"Term '{t}' not in snippet or concept"


def test_eval_query_solution_factual_alignment():
    """Verify that eval tasks have honest attribution, zero fake algorithm claims, and no ungrounded curriculum claims."""
    dummy_chunk = TextbookChunk(
        chunk_id="test_eval_chunk",
        title="18. Геометрична прогресія",
        text=(
            "18. Геометрична прогресія 175\n"
            "Квадрат будь-якого члена геометричної прогресії, крім першого (і останнього, якщо прогресія є скінченною), "
            "дорівнює добутку двох сусідніх із ним членів.\n"
        ),
        source_file="9-klas-algebra-merzliak-2017",
        grade="9",
        author="Мерзляк",
        subject="algebra",
        char_count=260,
    )
    rec = synthesize_eval_task(dummy_chunk, 1)

    # Invariants
    assert rec["concept"] == "Геометрична прогресія"
    assert "Мерзляк" in rec["query"] or "Мерзляк" in rec["reference_solution"]
    assert "згідно з навчальною програмою" not in rec["reference_solution"].lower()
    for step in rec["reference_reasoning"]:
        assert "згідно з навчальною програмою" not in step.lower()
        if "алгоритм" in step.lower():
            assert "алгоритм" in rec["query"].lower()
    for t in rec["scientific_terminology"]:
        text_corpus = (rec["reference_solution"] + " " + rec["concept"]).lower()
        assert t.lower() in text_corpus, f"Term '{t}' not contained in solution or concept"


@pytest.mark.timeout(300)
def test_dynamic_verification_functions_pass():
    """Verify that dynamic verification functions execute without error."""
    eval_dir = DEFAULT_OUTPUT_DIR / "eval"
    sft_dir = DEFAULT_OUTPUT_DIR / "sft"
    if eval_dir.exists() and sft_dir.exists():
        assert verify_zero_train_eval_leakage(eval_dir, sft_dir) is True
        assert verify_entity_preservation_volume_ratio(eval_dir, sft_dir) is True
        assert verify_pravopys_2019(eval_dir, sft_dir) is True
        assert verify_dataset_pedagogy_tone(eval_dir, sft_dir) is True
        assert verify_snippet_concept_grounding(eval_dir, sft_dir) is True
        assert verify_terms_present_in_snippet(eval_dir, sft_dir) is True
        assert verify_zero_dangling_starters(eval_dir, sft_dir) is True
        assert verify_zero_inflected_concepts(eval_dir, sft_dir) is True
        assert verify_eval_no_fake_algorithm_claims(eval_dir) is True


def test_r6_fable_findings_rejection():
    """Verify rejection of all 5 defects identified in Claude Fable Round 6 review."""
    # 1. 00000001: Exercise imperative concept & mid-word truncation rejection
    cand_01 = "Виконай ділення та відгадай ім"
    assert clean_and_validate_candidate(cand_01) is None
    assert "виконай" in EXERCISE_IMPERATIVES
    assert "відгадай" in EXERCISE_IMPERATIVES
    assert "знайди" in EXERCISE_IMPERATIVES
    assert "обчисли" in EXERCISE_IMPERATIVES
    assert clean_and_validate_candidate("Виконай ділення") is None

    # 2. 3e9: Dangling starter 'Аналогічні правила' and backward pointer 'рівносильну даній'
    snip_3e9 = (
        "Аналогічні правила застосовують і під час розв'язування нерівностей. "
        "Якщо який-небудь доданок перенести з однієї частини нерівності в другу, змінивши при цьому його знак на протилежний, "
        "то отримаємо нерівність, рівносильну даній."
    )
    assert DANGLING_STARTER_RE.search(snip_3e9) is not None
    assert FORWARD_BACKWARD_REF_RE.search(snip_3e9) is not None
    assert is_snippet_grounded_in_concept(snip_3e9, "Нерівності") is False

    # 3. 3ed: Forward pointer 'про які йтиметься в наступній темі' and missing primary entity 'сон'
    snip_3ed = "Є й триваліші біоритми, наприклад менструальний цикл у жіночому організмі, про які йтиметься в наступній темі."
    assert FORWARD_BACKWARD_REF_RE.search(snip_3ed) is not None
    assert is_snippet_grounded_in_concept(snip_3ed, "Сон як прояв біоритмів організму") is False

    # 4. 3ec: Isolated remark 'Найвигіднішій відстані відповідає найменша енергія' & non-circular terminology
    snip_3ec = "Найвигіднішій відстані відповідає найменша енергія."
    terms_3ec = extract_scientific_terminology_for_snippet(snip_3ec, "Енергія", "khimiya")
    # Terminology must NOT contain the concept itself
    assert "енергія" not in [t.lower() for t in terms_3ec]
    assert DEFINITIONAL_MARKER_RE.search("Функція називається парною, якщо...") is not None

    # 5. 3ee: No fake 'нормативне визначення' claims and zero ungrounded 'програмою курсу' query claims
    dummy_chunk = TextbookChunk(
        chunk_id="chunk_test_3ee",
        title="Сторінка 34",
        text="На відміну від вкладеного файлу такі зображення не треба відкривати, отримувач одразу бачить текст листа із малюнком.",
        source_file="7-klas-informatyka-bondarenko-2024",
        grade="7",
        author="Бондаренко",
        subject="informatyka",
        char_count=150,
    )
    rec = synthesize_eval_task(dummy_chunk, 1)
    all_text = (rec["query"] + " " + rec["reference_solution"] + " " + " ".join(rec["reference_reasoning"])).lower()
    assert "нормативне визначення" not in all_text
    assert "програмою курсу" not in all_text
    assert "за програмою" not in all_text


def test_r7_fable_findings_rejection():
    """Verify rejection of all defects identified in Claude Fable Round 7 review."""
    cur = get_vesum_cursor()

    # 1. Pronoun and function word rejection in terminology
    # Inflected pronouns and function words must be strictly recognized as pronouns/stopwords
    assert is_vesum_pronoun("нього", cur) is True
    assert is_vesum_pronoun("її", cur) is True
    assert is_vesum_pronoun("вони", cur) is True
    assert is_vesum_pronoun("який", cur) is True
    assert "треба" in STOPWORD_TERMS
    assert "відміну" in STOPWORD_TERMS

    snip_dummy = "Для цього треба підключити реостат до електричного кола."
    terms = extract_scientific_terminology_for_snippet(snip_dummy, "Реостат", "fizyka", cur_ves=cur)
    terms_lower = [t.lower() for t in terms]
    assert "нього" not in terms_lower
    assert "треба" not in terms_lower
    assert "цього" not in terms_lower
    for t in terms_lower:
        assert not is_vesum_pronoun(t, cur), f"Pronoun leaked into terms: {t}"

    # 2. Authentic domain lemma equality vs substring prefix matching
    assert "орган" in get_vesum_lemmas("органів", cur)
    assert "організм" not in get_vesum_lemmas("органів", cur)
    assert "організм" in get_vesum_lemmas("організмом", cur)
    assert "орган" not in get_vesum_lemmas("організмом", cur)

    # «Орган» vs «організмом» must fail (lemma 'орган' != 'організм')
    snip_organizm = "Будова організму тварин залежить від середовища існування."
    assert is_snippet_grounded_in_concept(snip_organizm, "Орган", cur_ves=cur) is False

    # «Орган» vs «орган — це...» must pass (exact lemma match)
    snip_organ = "Орган — це частина організму, яка виконує специфічну функцію."
    assert is_snippet_grounded_in_concept(snip_organ, "Орган", cur_ves=cur) is True

    # 3. Definitional pattern enforcement: concept and snippet mismatch rejection
    # «Реостат — це...» defines «Реостат», NOT «Електричні явища»
    snip_rheostat = "Реостат — це прилад для регулювання сили струму в колі."
    assert is_definitional_for_concept(snip_rheostat, "Реостат", cur_ves=cur) is True
    assert is_definitional_for_concept(snip_rheostat, "Електричні явища", cur_ves=cur) is False
    assert is_snippet_grounded_in_concept(snip_rheostat, "Електричні явища", cur_ves=cur) is False

    # 4. Dangling starters and anaphora rejection
    assert DANGLING_STARTER_RE.search("Її також використовують для вимірювання струму.") is not None
    assert DANGLING_STARTER_RE.search("Натомість такі речовини мають високу температуру кипіння.") is not None
    assert DANGLING_STARTER_RE.search("На відміну від металів діелектрики не проводять струм.") is not None
    assert DANGLING_STARTER_RE.search("Вони складаються з однакових молекул.") is not None


def test_r8_chapter_prefix_stripping_and_book_structure_rejection():
    """Verify stripping of chapter/unit prefixes and rejection of bare structural labels."""
    # 1. Chapter prefix stripping
    assert clean_and_validate_candidate("Розділ 2. Франція в XVI столітті") == "Франція в xvi столітті"
    assert clean_and_validate_candidate("Тема 3. Електричний струм") == "Електричний струм"
    assert clean_and_validate_candidate("Частина 1. Фонетика") == "Фонетика"
    assert clean_and_validate_candidate("Тема: Моделювання") == "Моделювання"
    assert clean_and_validate_candidate("Розділ I. Стародавній Рим") == "Стародавній рим"
    assert clean_and_validate_candidate("Параграф 14. Складне речення") == "Складне речення"

    # 2. Legitimate concepts with 'частина' or 'тема' preserved
    assert clean_and_validate_candidate("Частина мови") == "Частина мови"
    assert clean_and_validate_candidate("Тема і рема") == "Тема і рема"

    # 3. Bare structural labels rejected
    assert clean_and_validate_candidate("Розділ") is None
    assert clean_and_validate_candidate("Розділ 2") is None
    assert clean_and_validate_candidate("Розділ IV") is None
    assert clean_and_validate_candidate("Тема 5") is None
    assert clean_and_validate_candidate("Зміст") is None
    assert clean_and_validate_candidate("Вступ") is None
    assert clean_and_validate_candidate("Передмова") is None
    assert clean_and_validate_candidate("Післямова") is None


def test_r8_mojibake_rejection_and_strict_concept_grounding():
    """Verify rejection of font-corrupted mojibake and strict concept grounding."""
    cur = get_vesum_cursor()

    # 1. Mojibake rejection in clean_and_validate_candidate
    assert clean_and_validate_candidate("Ðîс²я") is None
    assert clean_and_validate_candidate("12345") is None

    # 2. Strict concept grounding: concept words in STOPWORD_TERMS (like Школа) must not bypass grounding
    s_active = "Активність у шкільному житті — це реальна можливість впливати на свій освітній простір."
    assert is_snippet_grounded_in_concept(s_active, "Школа", cur_ves=cur) is False

    s_shkola = "Школа — це не лише будівля для навчання, а спільнота, у якій щодня народжуються ідеї."
    assert is_snippet_grounded_in_concept(s_shkola, "Школа", cur_ves=cur) is True


def test_r9_fable_findings_elimination():
    """Verify systematic elimination of all 4 defect classes identified in Round 8 CF review."""
    cur = get_vesum_cursor()

    # 1. Defect 1: Inflected Instrumental Concepts vs Citation Form
    assert is_concept_in_citation_form("Сонячною радіацією", cur) is False
    assert is_concept_in_citation_form("Механічним рухом", cur) is False
    assert is_concept_in_citation_form("Силою тяжіння", cur) is False
    assert is_concept_in_citation_form("Клітиною", cur) is False
    assert is_concept_in_citation_form("Сонячна радіація", cur) is True
    assert is_concept_in_citation_form("Механічний рух", cur) is True
    assert is_concept_in_citation_form("Сила тяжіння", cur) is True
    assert is_concept_in_citation_form("Клітина", cur) is True

    assert lemmatize_noun_phrase("сонячною радіацією", cur) == "Сонячна радіація"
    assert lemmatize_noun_phrase("механічним рухом", cur) == "Механічний рух"
    assert lemmatize_noun_phrase("питомою теплотою плавлення", cur) == "Питома теплота плавлення"
    assert lemmatize_noun_phrase("силою тяжіння", cur) == "Сила тяжіння"
    assert clean_and_validate_candidate("Сонячною радіацією", cur) == "Сонячна радіація"
    assert clean_and_validate_candidate("Механічним рухом", cur) == "Механічний рух"

    # 2. Defect 2: Dangling Mid-Sentence Anaphora and Deictic Openers
    assert has_unresolved_anaphora("Нині в цій непростій справі допомагає комп'ютер.") is True
    assert has_unresolved_anaphora("Сукупність цієї енергії називають сонячною радіацією.") is True
    assert has_unresolved_anaphora("Таку зміну називають механічним рухом.") is True
    assert has_unresolved_anaphora("Цей процес називають дифузією.") is True
    assert has_unresolved_anaphora("Сьогодні у школі ми вивчаємо фізику.") is True

    s_clean_anim = "Покадрова анімація — спосіб створення анімації, за якого художник малює кожен кадр майбутнього фільму."
    assert has_unresolved_anaphora(s_clean_anim) is False
    s_clean_teplo = "Питома теплота плавлення — фізична величина, що характеризує кристалічну речовину."
    assert has_unresolved_anaphora(s_clean_teplo) is False

    # 3. Defect 3: Definitional Alignment & Defined Subject
    assert is_definitional_for_concept(s_clean_teplo, "Теплота", cur) is False
    assert is_definitional_for_concept(s_clean_teplo, "Питома теплота плавлення", cur) is True

    s_nerve = "Нервова тканина. Основні клітини нервової тканини — нейрони — мають численні відростки."
    assert is_definitional_for_concept(s_nerve, "Клітина", cur) is False

    # 4. Defect 4: Scientific Terminology Quality
    terms_anim = extract_scientific_terminology_for_snippet(s_clean_anim, "Покадрова анімація", "informatyka", cur)
    assert "анімація" in terms_anim
    assert "кадр" in terms_anim
    assert "фільм" in terms_anim
    assert "непростий" not in terms_anim
    assert "справа" not in terms_anim
    assert "створення" not in terms_anim
    assert "художник" not in terms_anim
    assert len(terms_anim) >= 3

    terms_teplo = extract_scientific_terminology_for_snippet(s_clean_teplo, "Питома теплота плавлення", "fizyka", cur)
    assert "речовина" in terms_teplo or "кристалічний" in terms_teplo
    assert "фізичний" not in terms_teplo
    assert "величина" not in terms_teplo
    assert "питомий" not in terms_teplo
    assert len(terms_teplo) >= 3
