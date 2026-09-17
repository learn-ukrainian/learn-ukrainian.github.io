"""Unit tests and invariant verifications for Track 6 Grammar, Valency & Syntactic Precision Engine.

Covers Issue #8143 / Epic #6321.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

from jsonschema import validate

from scripts.projects.open_model_data import v6_mine_grammar_valency as miner

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RELEASE_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v05_grammar_valency"
EVAL_SCHEMA_PATH = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "contracts" / "v1_grammar_valency_eval_record.schema.json"
RECEIPT_SCHEMA_PATH = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "contracts" / "v1_grammar_valency_release_receipt.schema.json"


def test_taxonomy_coverage_and_categories() -> None:
    """Ensure full 20-category UA-GEC taxonomy (14 Grammar + 6 Fluency) is covered."""
    assert len(miner.ALL_GRAMMAR_CATEGORIES) == 14
    assert len(miner.ALL_FLUENCY_CATEGORIES) == 6
    assert len(miner.FULL_TAXONOMY) == 20

    for cat in miner.FULL_TAXONOMY:
        assert cat in miner.CATEGORY_EXPLANATIONS
        assert "title" in miner.CATEGORY_EXPLANATIONS[cat]
        assert "rule" in miner.CATEGORY_EXPLANATIONS[cat]
        assert len(miner.CATEGORY_EXPLANATIONS[cat]["rule"]) > 20


def test_valency_frames_authenticity_and_coverage() -> None:
    """Verify linguistic coverage of case valency and prepositional government frames."""
    frames = miner.VALENCY_FRAMES
    assert len(frames) >= 12

    verbs = {f["verb"] for f in frames}
    assert "опанувати" in verbs  # опанувати що (знахідний)
    assert "докоряти" in verbs  # докоряти кому (давальний)
    assert "навчатися" in verbs  # навчатися чого (родовий)
    assert "властивий" in verbs  # властивий кому (давальний)
    assert "дякувати" in verbs  # дякувати кому (давальний)
    assert "вибачати" in verbs  # вибачати кому (давальний)
    assert "хворіти" in verbs  # хворіти на що (на + знахідний)
    assert "знущатися" in verbs  # знущатися з кого (з + родовий)
    assert "потребувати" in verbs  # потребувати чого (родовий)
    assert "завдати" in verbs  # завдати шкоди (родовий)
    assert "вжити" in verbs  # вжити заходів (родовий)
    assert "прийменник_по" in verbs  # у справах, за законом
    assert "прийменник_при" in verbs  # за участі, за умови

    for f in frames:
        assert len(f["examples"]) >= 3
        for correct, incorrect in f["examples"]:
            assert correct != incorrect
            assert len(correct) > 15
            assert len(incorrect) > 15


def test_vesum_database_resolution_and_attestation() -> None:
    """Verify that VESUM database resolves via git-common-dir and forms_all queries succeed."""
    vesum_db = miner.DEFAULT_VESUM_DB
    assert vesum_db.is_file(), f"VESUM database could not be resolved at {vesum_db}"

    import sqlite3
    conn = sqlite3.connect(f"file:{vesum_db}?mode=ro", uri=True)
    cur = conn.cursor()

    for verb, expected_min_forms in [
        ("опанувати", 10),
        ("докоряти", 15),
        ("навчатися", 25),
        ("завідувач", 10),
        ("властивий", 20),
    ]:
        lemma, count, attested = miner.query_vesum_lemma_and_count(cur, verb)
        assert lemma == verb
        assert attested is True
        assert count >= expected_min_forms, f"Expected >={expected_min_forms} forms for {verb}, got {count}"


def test_gate6_tone_calibration_respectful_pedagogy() -> None:
    """Verify Gate 6 tone check filters condescending terms and passes polite phrasing."""
    pejorative_words = miner.load_tone_dict(miner.DEFAULT_TONE_DICT_DIR)
    assert "тупий" in pejorative_words
    assert "недолугий" in pejorative_words
    assert "ідіотський" in pejorative_words
    assert "невігластво" in pejorative_words

    # Condescending phrase must fail
    condescending_phrase = "Це абсолютно тупий і недолугий варіант тексту."
    assert not miner.verify_respectful_tone(condescending_phrase, pejorative_words)

    # Respectful pedagogical phrase must pass
    respectful_phrase = (
        "У поданому реченні допущено помилку відмінкового керування. "
        "Нормативним варіантом в українській літературній мові є вживання прийменника «за»."
    )
    assert miner.verify_respectful_tone(respectful_phrase, pejorative_words)


def test_eval_benchmark_disk_invariants_and_schema() -> None:
    """Validate held-out negative control eval benchmark against schema contract."""
    eval_file = RELEASE_DIR / "brown_uk_negative_control_eval.jsonl"
    assert eval_file.is_file(), f"Missing eval file: {eval_file}"

    schema = json.loads(EVAL_SCHEMA_PATH.read_text(encoding="utf-8"))
    count = 0
    seen_ids = set()

    with eval_file.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            validate(instance=rec, schema=schema)
            assert rec["eval_id"] not in seen_ids
            seen_ids.add(rec["eval_id"])
            assert rec["target_action"] == "PRESERVE"
            assert rec["is_pristine_control"] is True
            assert rec["source_corpus"] == "brown_uk_good"
            count += 1

    assert count == 500
    assert len({rec["document_id"] for rec in (json.loads(line) for line in eval_file.open(encoding="utf-8"))}) >= 40


def test_zero_train_eval_leakage_firewall() -> None:
    """Enforce strict 0% train/eval leakage between held-out eval and SFT shards."""
    eval_file = RELEASE_DIR / "brown_uk_negative_control_eval.jsonl"
    eval_sentences = set()
    with eval_file.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            eval_sentences.add(rec["sentence_text"].strip())

    sft_files = sorted(glob.glob(str(RELEASE_DIR / "sft" / "sft_shard_*.jsonl")))
    assert len(sft_files) == 70

    leaks = 0
    for sf in sft_files:
        with open(sf, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                orig = rec.get("original_text", "").strip()
                corr = rec.get("corrected_text", "").strip()
                if orig in eval_sentences or corr in eval_sentences:
                    leaks += 1

    assert leaks == 0, f"Found {leaks} train/eval leakage instances!"


def test_sft_shards_disk_invariants_and_manifest() -> None:
    """Verify SFT manifest, shard sizes <= 2,000 KB, SHA-256 integrity, ID uniqueness, and zero markup."""
    manifest_path = RELEASE_DIR / "sft" / "manifest.json"
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["total_trajectories"] == 35000
    assert manifest["shards_count"] == 70
    assert len(manifest["shards"]) == 70

    total_read = 0
    seen_ids = set()
    for shard_info in manifest["shards"]:
        shard_file = RELEASE_DIR / "sft" / shard_info["shard_file"]
        assert shard_file.is_file()

        # Hard constraint: git-tracked file size <= 2,000 KB
        size_kb = shard_file.stat().st_size / 1024.0
        assert size_kb <= 2000.0, f"Shard {shard_file.name} exceeds 2,000 KB: {size_kb:.2f} KB"

        # Check sha256
        actual_sha = miner.sha256_file(shard_file)
        assert actual_sha == shard_info["sha256"], f"SHA mismatch on {shard_file.name}"

        # Check lines and trajectory invariants
        lines_count = 0
        with shard_file.open(encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                tid = rec["trajectory_id"]
                assert tid not in seen_ids, f"Duplicate trajectory_id found: {tid}"
                seen_ids.add(tid)

                orig = rec.get("original_text", "")
                corr = rec.get("corrected_text", "")
                assert "error_type=" not in orig and "error_type=" not in corr
                assert ":::" not in orig and ":::" not in corr
                assert "{" not in orig and "{" not in corr
                assert "}" not in orig and "}" not in corr

                lines_count += 1

        assert lines_count == shard_info["trajectories_count"]
        total_read += lines_count

    assert total_read == 35000
    assert len(seen_ids) == 35000


def test_abbreviation_protection_sentence_splitting() -> None:
    """Verify that sentence splitting does not fragment abbreviations or initials."""
    sample = (
        "Загальний прибуток підприємства склав понад 2 тис. грн за минулий квартал. "
        "Академік А. Кримський та проф. Шевченко високо оцінили результати роботи."
    )
    sents = miner.split_clean_ukrainian_sentences(sample)
    assert len(sents) == 2
    assert sents[0] == "Загальний прибуток підприємства склав понад 2 тис. грн за минулий квартал."
    assert sents[1] == "Академік А. Кримський та проф. Шевченко високо оцінили результати роботи."


def test_sentence_splitting_rejects_unbalanced_and_defective_punctuation() -> None:
    """Verify filtering of unbalanced parentheses, brackets, and unclosed relative clauses."""
    # Defect: unclosed parenthesis
    sample_paren = "Адже буддисти активно виступали за мир (наприклад, «Луганськ – це Україна»."
    assert len(miner.split_clean_ukrainian_sentences(sample_paren)) == 0

    # Defect: unclosed relative clause missing closing comma before main predicate
    sample_comma = "Посада, на яку приймаєте працівника обов'язково повинна бути в державному класифікаторі професій в Україні."
    assert len(miner.split_clean_ukrainian_sentences(sample_comma)) == 0

    # Valid sentence with balanced punctuation and subordinate clause must pass
    sample_valid = "Посада, на яку приймаєте працівника, обов'язково повинна бути в державному класифікаторі професій в Україні."
    assert len(miner.split_clean_ukrainian_sentences(sample_valid)) == 1


def test_valency_explanations_codification_nuance() -> None:
    """Verify valency explanations cite modern literary codification (СУМ, Правопис 2019)."""
    frames = {f["verb"]: f for f in miner.VALENCY_FRAMES}
    assert "докоряти" in frames
    assert "навчатися" in frames

    # dokoriati explanation must cite literary norm and avoid blanket Russian calque claim
    dok_expl = frames["докоряти"]["explanation"]
    assert "давальним відмінком" in dok_expl
    assert "невірно" not in dok_expl
    assert "російською синтаксичною калькою" not in dok_expl

    # navchatysia explanation must cite Pravopys 2019 / SUM and genitive government
    navch_expl = frames["навчатися"]["explanation"]
    assert "родово" in navch_expl
    assert "Правопис 2019" in navch_expl or "СУМ" in navch_expl
    assert "синтаксичною калькою з російської" not in navch_expl

    # All frames must have nuanced critique
    for frame in miner.VALENCY_FRAMES:
        assert "critique" in frame
        assert len(frame["critique"]) > 20


def test_valency_trajectories_critique_step() -> None:
    """Verify that valency trajectories use tailored critique instead of generic calque assertion."""
    trajectories = miner.build_valency_trajectories()
    for t in trajectories:
        step3 = t["reasoning_steps"][2]
        assert step3.startswith("3. Оцінка помилкової моделі: ")
        assert "Спростування помилкової моделі: конструкція" not in step3


def test_vesum_query_fail_closed_when_cursor_none() -> None:
    """Verify query_vesum_lemma_and_count returns attested=False when cursor is None."""
    lemma, count, attested = miner.query_vesum_lemma_and_count(None, "перевірка")
    assert lemma == "перевірка"
    assert count == 1
    assert attested is False


def test_negative_controls_filtering_rejects_defective_structures() -> None:
    """Verify that incomplete subordinate clauses, comma before predicate, and unclosed appositives are rejected."""
    import sqlite3

    conn = sqlite3.connect(f"file:{miner.DEFAULT_VESUM_DB}?mode=ro", uri=True)
    cur = conn.cursor()

    # Defect 1: Incomplete subordinate clause lacking predicate
    frag = "Зрозуміло, що після надання коментарів відповідними керівниками та службами обласного автодору."
    assert not miner.is_pristine_eval_sentence(frag, cur_ves=cur)

    # Defect 2: Comma separating coordinate subjects from predicate
    comma_pred = "Ні знімок обличчя вбивці, ні детальне відео злочину, ні свідчення десятків людей, не дозволили правоохоронцям зробити подвиг."
    assert len(miner.split_clean_ukrainian_sentences(comma_pred)) == 0

    # Defect 3: Unclosed тобто appositive before predicate
    unclosed_tobto = "Вважають, що ті вимоги, які практикують, тобто писання заяви про вступ, здавання фотографій на документи, навіть сплата членських внесків нагадує партійний стиль облікування своїх членів."
    assert len(miner.split_clean_ukrainian_sentences(unclosed_tobto)) == 0

    # Defect 4: Digit-starting sentence split cleanly
    two_sents = "Згідно з документом надходження складуть 890 мільйонів гривень. 90,5 відсотка грошового наповнення забезпечать субвенції."
    sents = miner.split_clean_ukrainian_sentences(two_sents)
    assert len(sents) == 2
    assert sents[0] == "Згідно з документом надходження складуть 890 мільйонів гривень."
    assert sents[1] == "90,5 відсотка грошового наповнення забезпечать субвенції."

    # Defect 5 (Round 4): Detached fragment with relative clause lacking matrix predicate
    frag_rel = "Насамперед, через деякі законодавчі прогалини, які даються взнаки на цьому етапі."
    assert not miner.is_pristine_eval_sentence(frag_rel, cur_ves=cur)

    # Defect 6 (Round 4): Dangling speech reporting verb without coordinated subject pronoun
    dangling_speech = "За словами мера, цей проект після доопрацювання погоджувальна рада розгляне знову, й додав, мовляв, таке зволікання зумовлене тим, що муніципалітет не хоче ускладнювати ситуацію в місті."
    assert not miner.is_pristine_eval_sentence(dangling_speech, cur_ves=cur)

    # Defect 7 (Round 4): Unclosed subordinate clause before coordinating conjunction joining matrix predicates (Pravopys §158)
    unclosed_coord = "Він наголосив, що «Fit for Partnership with Germany» суттєво допомагає при налагодженні контактів з потенційними партнерами і закликав усіх охочих приєднуватися."
    assert not miner.is_pristine_eval_sentence(unclosed_coord, cur_ves=cur)

    # Defect 8 (Round 4): Erroneous comma before single 'або' joining homogeneous complements (Pravopys §158)
    comma_abo = "Тоді водний транспорт у Києві, як каже Олександр Михайлик, був зручнішим за наземний, відтак на Русанівські сади до 1960-х їздили на міському катері, або на човні."
    assert not miner.is_pristine_eval_sentence(comma_abo, cur_ves=cur)


def test_release_receipt_schema_and_checksum() -> None:
    """Validate release receipt against JSON schema and sha256 checksum."""
    receipt_file = RELEASE_DIR / "release_receipt.json"
    assert receipt_file.is_file()

    schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    validate(instance=receipt, schema=schema)

    assert receipt["issue"] == 8143
    assert receipt["parent_epic"] == 6321
    assert receipt["evaluation_benchmark"]["total_cases"] == 500
    assert receipt["sft_training_dataset"]["total_trajectories"] == 35000
    assert receipt["sft_training_dataset"]["shards_count"] == 70
    assert receipt["invariants_verified"]["zero_train_eval_leakage"] is True
    assert receipt["invariants_verified"]["full_20_category_taxonomy_ingested"] is True
    assert receipt["invariants_verified"]["vesum_valency_verified"] is True
    assert receipt["invariants_verified"]["tone_calibration_gate6_verified"] is True
    assert receipt["invariants_verified"]["precommit_file_ceiling_satisfied"] is True

    # Check sha256 file
    sha_file = RELEASE_DIR / "release_receipt.json.sha256"
    assert sha_file.is_file()
    expected_sha = miner.sha256_file(receipt_file)
    assert expected_sha in sha_file.read_text(encoding="utf-8")


def test_hermetic_isolation_synthetic_run(tmp_path: Path) -> None:
    """Hermetic test: run extraction and sharding on isolated synthetic fixtures."""
    ua_gec_dir = tmp_path / "ua-gec"
    brown_uk_dir = tmp_path / "brown-uk"
    tone_dict_dir = tmp_path / "tone-dict"
    out_dir = tmp_path / "release"

    # Create synthetic UA-GEC annotated file
    ann_dir = ua_gec_dir / "data" / "gec-fluency" / "train" / "annotated"
    ann_dir.mkdir(parents=True)
    ann_content = (
        "Студенти {опанували мовою=>опанували мову:::error_type=G/Case} за один семестр. "
        "Керівництво {прийняло міри=>вжило заходів:::error_type=F/Calque} своєчасно."
    )
    (ann_dir / "0001.a1.ann").write_text(ann_content, encoding="utf-8")

    # Create synthetic Brown-UK good and so-so files
    good_dir = brown_uk_dir / "data" / "good"
    so_so_dir = brown_uk_dir / "data" / "so-so"
    good_dir.mkdir(parents=True)
    so_so_dir.mkdir(parents=True)

    for i in range(15):
        (good_dir / f"doc_{i:03d}.txt").write_text(
            f"Це бездоганне речення номер {i} для перевірки негативного контролю та відсутності помилок.",
            encoding="utf-8",
        )
    (so_so_dir / "doc_so_so.txt").write_text(
        "Це речення з живого мовлення для контрастивного стилістичного аналізу.",
        encoding="utf-8",
    )

    # Create synthetic tone-dict
    tone_dict_dir.mkdir(parents=True)
    (tone_dict_dir / "tone-dict-uk-manual.tsv").write_text(
        "тупий\t-1\t-1\nідіот\t-1\t-1\n",
        encoding="utf-8",
    )

    # Run extraction pipeline with small target count
    pej = miner.load_tone_dict(tone_dict_dir)
    assert "тупий" in pej

    eval_recs, brown_train = miner.load_brown_uk_sentences(brown_uk_dir, eval_count=10)
    assert len(eval_recs) == 10

    ua_items = miner.load_ua_gec_annotations(ua_gec_dir)
    assert len(ua_items) == 2

    val_items = miner.build_valency_trajectories()
    assert len(val_items) > 0

    sft_trajectories = miner.build_sft_dataset(
        ua_gec_items=ua_items,
        valency_items=val_items,
        brown_uk_train=brown_train,
        pejorative_words=pej,
        target_count=100,
    )
    assert len(sft_trajectories) == 100

    shard_files, manifest = miner.shard_dataset(sft_trajectories, out_dir, num_shards=5)
    assert len(shard_files) == 5
    assert manifest["total_trajectories"] == 100
