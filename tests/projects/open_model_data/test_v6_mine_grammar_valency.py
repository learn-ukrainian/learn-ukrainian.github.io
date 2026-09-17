"""Unit tests and invariant verifications for Track 6 Grammar, Valency & Syntactic Precision Engine.

Covers Issue #8143 / Epic #6321.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

import pytest
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

    # Defect: compound abbreviation preceding sentence boundary must split and not merge
    sample_abbr = "В селі Лисець Тисменицького району травмовано чоловіка, 1972 р. н. З діагнозом «відкритий перелом лівої гомілки» потерпілого госпіталізовано до обласної клінічної лікарні."
    sents_abbr = miner.split_clean_ukrainian_sentences(sample_abbr)
    # The first sentence ends in 'р. н.' and is filtered out by the abbreviation ending guard; second sentence is pristine
    assert len(sents_abbr) == 1
    assert sents_abbr[0] == "З діагнозом «відкритий перелом лівої гомілки» потерпілого госпіталізовано до обласної клінічної лікарні."


@pytest.mark.parametrize(
    ("probe", "expected_suffix"),
    [
        ("1972 р. н. З діагнозом", "н. З діагнозом"),
        ("і т. д. З діагнозом", "д. З діагнозом"),
        ("і т. п. З діагнозом", "п. З діагнозом"),
        ("т. ін. З діагнозом", "ін. З діагнозом"),
        ("м. п. З діагнозом", "п. З діагнозом"),
    ],
)
def test_compound_abbreviations_preserve_terminal_dot_boundary(probe: str, expected_suffix: str) -> None:
    """Ensure compound abbreviations preserve terminal dot before uppercase letters for sentence splitting."""
    protected = miner.protect_abbreviations(probe)
    assert protected.endswith(expected_suffix)


def test_valency_explanations_codification_nuance() -> None:
    """Verify valency explanations cite modern literary codification (СУМ, Правопис 2019, Чак)."""
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

    # znushchatysia explanation must cite Chak, classical literary allowance, and F/Style category
    assert "знущатися" in frames
    znushch_frame = frames["знущатися"]
    assert "Чак" in znushch_frame["explanation"]
    assert "Шевченко" in znushch_frame["explanation"] or "Леся Українка" in znushch_frame["explanation"]
    assert znushch_frame["category"] == "F/Style"

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

    # Defect 9 (Round 5): Sentence-initial conjunction with erroneous comma (Pravopys §158)
    odnak_comma = "Однак, у селі теж можна було отримати ділянку під забудову."
    assert not miner.is_pristine_eval_sentence(odnak_comma, cur_ves=cur)

    # Defect 10 (Round 5): Subordinate conditional clause lacking matrix predicate
    frag_cond = "Звісно, за умови, якщо вони визначилися з ім'ям немовляти."
    assert not miner.is_pristine_eval_sentence(frag_cond, cur_ves=cur)

    # Defect 11 (Round 5): Trailing unicode ellipsis
    ellipsis_sent = "І така картина спостерігається не лише у відділі продажів…"
    assert not miner.is_pristine_eval_sentence(ellipsis_sent, cur_ves=cur)

    # Defect 12 (Round 6): Non-parenthetical adverb erroneously isolated by commas (Horodenska, p. 71)
    frag_adverb = "Створена в XIII столітті інквізиція розглядала, насамперед, справи про єресь, але якщо все-таки вдавалося вижити."
    assert not miner.is_pristine_eval_sentence(frag_adverb, cur_ves=cur)

    # Defect 13 (Round 6): Broken paired conjunction 'як ..., так ...' omitting 'і/й' (Pravopys 2019, §158.I.5)
    frag_paired = "На мою думку, в цьому полягає ще одна її цінність, адже вона доступна як для українського, так для німецького читача."
    assert not miner.is_pristine_eval_sentence(frag_paired, cur_ves=cur)

    # Defect 14 (Round 6): Multi-sentence fragment across compound abbreviation
    frag_multisents = "В селі Лисець Тисменицького району травмовано чоловіка, 1972 р. н. З діагнозом «відкритий перелом лівої гомілки» потерпілого госпіталізовано до обласної клінічної лікарні."
    assert not miner.is_pristine_eval_sentence(frag_multisents, cur_ves=cur)

    # Defect 15 (Round 7): Non-parenthetical adverbial time phrase isolated with comma (Yermolenko, p. 39)
    frag_time_adv = "Тим часом, перед стійкою реєстрації утворилася черга."
    assert not miner.is_pristine_eval_sentence(frag_time_adv, cur_ves=cur)

    # Defect 16 (Round 7): Non-parenthetical adverb isolated with comma (Horodenska, p. 58)
    frag_naspravdi = "Насправді, для частини учасників цей переплив став лише розминкою."
    assert not miner.is_pristine_eval_sentence(frag_naspravdi, cur_ves=cur)

    # Defect 17 (Round 7): Sentence-initial conjunction 'Втім' / 'Утім' with erroneous comma
    frag_vtim = "Втім, такі проблеми актуальні й сьогодні: у Конча-Заспі намивається пісок."
    assert not miner.is_pristine_eval_sentence(frag_vtim, cur_ves=cur)
    frag_utim = "Утім, далеко не лише ці двоє політиків почали активно рекламувати себе."
    assert not miner.is_pristine_eval_sentence(frag_utim, cur_ves=cur)

    # Defect 18 (Round 7): Compound abbreviation m. p. preceding sentence boundary
    frag_mp = "Документ було скріплено печаткою організації м. п. За цим розпорядженням створено комісію."
    assert not miner.is_pristine_eval_sentence(frag_mp, cur_ves=cur)

    # Defect 19 (Round 8): Pleonastic double future construction (Правопис 2019; IMZO Gr 7)
    frag_double_future = "Першими на дистанцію запрошують досвідчених плавців, що будуть змагатимуться за призові місця."
    assert not miner.is_pristine_eval_sentence(frag_double_future, cur_ves=cur)

    # Defect 20 (Round 8): Unpunctuated explanatory construction with demonstrative (Правопис 2019 §158.3.г)
    frag_unpunctuated_yak = "Структуру закону було вибудовано так, щоб за допомогою такого інструменту як референдум проводити провладні рішення."
    assert not miner.is_pristine_eval_sentence(frag_unpunctuated_yak, cur_ves=cur)

    # Defect 21 (Round 8): Preposed participial modifier erroneously isolated by commas (Правопис 2019 §158.3.а)
    frag_preposed_mod = "Розрахунок невикористаної субсидії визначається наступним чином: від суми, нарахованої за опалювальний сезон субсидії, віднімається вартість уже спожитого газу та вартість 100 кубів – 687,90 гривень."
    assert not miner.is_pristine_eval_sentence(frag_preposed_mod, cur_ves=cur)

    # Defect 22 (Round 9): Ungoverned numeral nominative/accusative case following 'близько' / 'до' (СУМ)
    frag_numeral = "Загалом представлено близько п'ятсот творів."
    assert not miner.is_pristine_eval_sentence(frag_numeral, cur_ves=cur)
    assert len(miner.split_clean_ukrainian_sentences(frag_numeral)) == 0

    # Defect 23 (Round 9): Comma separating homogeneous predicates, calque 'в свою чергу', isolated 'все ж' (Правопис §158)
    frag_homogeneous_comma = "В свою чергу, батьки переїхали на дачу, і почали вмовляти синів частіше займатися городом, але кількість грядок, все ж, вирішили зменшити."
    assert not miner.is_pristine_eval_sentence(frag_homogeneous_comma, cur_ves=cur)
    assert len(miner.split_clean_ukrainian_sentences(frag_homogeneous_comma)) == 0

    # Defect 24 (Round 9): Sentence-initial explanatory conjunction 'Тобто' with erroneous comma (Правопис §158)
    frag_tobto_comma = "Тобто, ця сума залишається на рахунку одержувача, а решта невикористаної субсидії повертається державі."
    assert not miner.is_pristine_eval_sentence(frag_tobto_comma, cur_ves=cur)
    assert len(miner.split_clean_ukrainian_sentences(frag_tobto_comma)) == 0

    # Defect 25 (Round 10): Comma separating homogeneous predicates with intervening adverb (Правопис §158)
    frag_adv_homogeneous = "Інформаційний запит ми надіслали 15 лютого, і щотижня зверталися за телефоном з приводу реагування на редакційне звернення."
    assert not miner.is_pristine_eval_sentence(frag_adv_homogeneous, cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_adv_homogeneous, cur_ves=cur)

    # Defect 26 (Round 10): Comma separating present-tense homogeneous predicates (VESUM pres:s:3) (Правопис §158)
    frag_pres_repro = "Він щодня читає книжки, і пише листи до друзів."
    assert not miner.is_pristine_eval_sentence(frag_pres_repro, cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_pres_repro, cur_ves=cur)

    # Defect 27 (Round 11): Clause-initial conjunction comma after clause boundary (Правопис §158)
    frag_otogh_comma = "Мовляв, начальство їхнє в Івано-Франківську, отож, звертайтеся туди."
    assert not miner.is_pristine_eval_sentence(frag_otogh_comma, cur_ves=cur)
    assert len(miner.split_clean_ukrainian_sentences(frag_otogh_comma)) == 0

    # Defect 28 (Round 11): Unpunctuated compound sentence lacking comma before 'і' (Правопис §158.2)
    frag_unpunctuated_compound = "Підростав Олексій і вже Миколка народився, тож вирішив пан Роман сам зробити свою першу скрипку синові."
    assert not miner.is_pristine_eval_sentence(frag_unpunctuated_compound, cur_ves=cur)
    assert miner.check_unpunctuated_compound_sentence(frag_unpunctuated_compound, cur_ves=cur)

    # Defect 29 (Round 11): Homogeneous predicate comma inside relative clause (Правопис §158.1)
    frag_relative_homogeneous = "Діяльністю станції поліція зацікавилась ще в 2015-му, коли почала перевірку фірм, які виграли на тендерах ЧАЕС, і повинні були займатися демонтажем і дезактивацією обладнання машинних залів енергоблоків."
    assert not miner.is_pristine_eval_sentence(frag_relative_homogeneous, cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_relative_homogeneous, cur_ves=cur)

    # Defect 30 (Round 11): Future-tense homogeneous predicate reproduction with VESUM ':futr:' (Правопис §158)
    frag_futr_repro = "Він щодня читатиме книжки, і писатиме листи до друзів."
    assert not miner.is_pristine_eval_sentence(frag_futr_repro, cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_futr_repro, cur_ves=cur)

    # Defect 31 (Round 12): Expanded unpunctuated compound sentence (Правопис §158 II.2)
    frag_expanded_compound = (
        "Концепція «бачу печатку – вірю» глибоко засіла у свідомості сучасних підприємців "
        "і найімовірніше останні й надалі використовуватимуть кліше на своїх документах."
    )
    assert not miner.is_pristine_eval_sentence(frag_expanded_compound, cur_ves=cur)
    assert miner.check_unpunctuated_compound_sentence(frag_expanded_compound, cur_ves=cur)

    # Defect 32 (Round 12): Homogeneous predicate comma with intervening elliptical clause (Правопис §158 I.1)
    frag_elliptical_homogeneous = (
        "Звісно, є і бенефіціар цього протистояння: Росія постачає наступальну зброю Азербайджану, "
        "оборонну – Вірменії, і готується в разі загострення ситуації в епіцентрі конфлікту зіграти роль провідного миротворця."
    )
    assert not miner.is_pristine_eval_sentence(frag_elliptical_homogeneous, cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_elliptical_homogeneous, cur_ves=cur)

    # Positive control (Round 12 P2): Accusative object before verb in homogeneous predicate sentence
    frag_valid_acc_object = "Він читатиме і листи писатиме до друзів."
    assert not miner.check_unpunctuated_compound_sentence(frag_valid_acc_object, cur_ves=cur)
    assert not miner.has_homogeneous_verb_comma(frag_valid_acc_object, cur_ves=cur)

    # Defect 33 (Round 13 P1): Detached apposition lacking closing comma before matrix verb (Правопис 2019 §158 I.14)
    frag_unclosed_appos = (
        "Тому на всі свята сім'я іванофранківчанки, прес-секретаря апеляційного суду "
        "Івано-Франківської області Людмили Безусової-Попович їде до Брошнева, до мами та бабусі Олени."
    )
    assert not miner.is_pristine_eval_sentence(frag_unclosed_appos, cur_ves=cur)
    assert miner.has_unclosed_appositive_comma(frag_unclosed_appos, cur_ves=cur)

    # Positive control 1 (Round 13 P2): Coordinated subordinate clauses sharing main clause predicate (Правопис 2019 §158 II.3 примітка 2)
    frag_subordinate_coord = "Я знаю, що він читає книжку і вона пише листа."
    assert not miner.check_unpunctuated_compound_sentence(frag_subordinate_coord, cur_ves=cur)
    assert miner.is_pristine_eval_sentence(frag_subordinate_coord, cur_ves=cur)

    # Positive control 2 (Round 13 P2): Closing parenthetical comma before coordinating conjunction (Правопис 2019 §158 I.11)
    frag_parenthetical_closing = "Він читає цікаву книжку, наприклад, і пише довгого листа."
    assert not miner.has_homogeneous_verb_comma(frag_parenthetical_closing, cur_ves=cur)
    assert miner.is_pristine_eval_sentence(frag_parenthetical_closing, cur_ves=cur)

    # Defect 34 (Round 14 P1): Unclosed clarifying adverbial modifier lacking closing comma before subject/predicate (Правопис 2019 §158 I.15(3))
    frag_unclosed_clarification = (
        "Українські буддисти спершу зводили свій храм на Луганщині, та звідти їх вигнала війна, "
        "і тепер під селом Паньківка, біля залитого фундаменту споруди сепаратисти облаштували свою базу."
    )
    assert not miner.is_pristine_eval_sentence(frag_unclosed_clarification, cur_ves=cur)
    assert miner.has_unclosed_clarification(frag_unclosed_clarification, cur_ves=cur)

    # Defect 35 (Round 14 P2): Comma separating homogeneous predicates with parenthetical word inside clause (Правопис 2019 §158 I.1)
    frag_clause_with_spravdi = "Він справді читає книжку, і пише довгого листа."
    assert not miner.is_pristine_eval_sentence(frag_clause_with_spravdi, cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_clause_with_spravdi, cur_ves=cur)

    # Defect 36 (Round 15 P1): Unpunctuated parenthetical following adversative conjunction (Правопис 2019 §158 I.11)
    frag_unpunctuated_navpaky = (
        "За словами голови Малолюбашанської ОТГ, сьогодні надходження від останнього скоротилися вдвічі, "
        "тоді як вартість пального не зменшується, а навпаки зростає."
    )
    assert not miner.is_pristine_eval_sentence(frag_unpunctuated_navpaky, cur_ves=cur)
    assert miner.UNPUNCTUATED_ADVERSATIVE_PARENTHETICAL_RE.search(frag_unpunctuated_navpaky)

    # Positive control (Round 15 P2): Multi-word parenthetical phrase 'власне кажучи' before coordinating conjunction (Правопис 2019 §158 I.11)
    frag_vlasne_kazhuchy = "Він читає цікаву книжку, власне кажучи, і пише довгого листа."
    assert not miner.has_homogeneous_verb_comma(frag_vlasne_kazhuchy, cur_ves=cur)
    assert miner.is_pristine_eval_sentence(frag_vlasne_kazhuchy, cur_ves=cur)

    # Defect 37 (Round 16 P1): Partially punctuated adversative parenthetical lacking opening comma after 'а' (Правопис 2019 §158 I.11, примітка 2)
    frag_partially_punctuated_navpaky = (
        "І так склалося, що поділ на «наші» і «ваші» свята, як пригадує пані Люда, "
        "їх зовсім не роз'єднував, а навпаки, зближував."
    )
    assert not miner.is_pristine_eval_sentence(frag_partially_punctuated_navpaky, cur_ves=cur)
    assert miner.UNPUNCTUATED_ADVERSATIVE_PARENTHETICAL_RE.search(frag_partially_punctuated_navpaky)
    assert len(miner.split_clean_ukrainian_sentences(frag_partially_punctuated_navpaky)) == 0

    # Positive control 1 (Round 16 P1): Fully punctuated adversative parenthetical (Правопис 2019 §158 I.11, примітка 2)
    frag_correct_navpaky = "Це їх зовсім не роз'єднувало, а, навпаки, зближувало."
    assert not miner.UNPUNCTUATED_ADVERSATIVE_PARENTHETICAL_RE.search(frag_correct_navpaky)
    assert miner.is_pristine_eval_sentence(frag_correct_navpaky, cur_ves=cur)

    # Defect 38 / Negative regression (Round 16 P2): Non-parenthetical accusative phrase ending in 'думку' not exempted from homogeneous predicate comma check (Правопис 2019 §158 I.1)
    frag_accusative_dumku = "Він записує речення, чужу думку, і читає довгого листа."
    assert not miner.is_parenthetical_segment("чужу думку", cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_accusative_dumku, cur_ves=cur)
    assert not miner.is_pristine_eval_sentence(frag_accusative_dumku, cur_ves=cur)

    # Positive control 2 (Round 16 P2): Legitimate parenthetical phrase with 'думку' (Правопис 2019 §158 I.11)
    frag_valid_dumku = "Він записує речення, на нашу думку, і читає довгого листа."
    assert miner.is_parenthetical_segment("на нашу думку", cur_ves=cur)
    assert not miner.has_homogeneous_verb_comma(frag_valid_dumku, cur_ves=cur)
    assert miner.is_pristine_eval_sentence(frag_valid_dumku, cur_ves=cur)

    # Defect 39 / Negative regression (Round 17 P2): Ordinary prepositional complement 'на думку про відпустку' not exempted from homogeneous predicate comma check (Правопис 2019 §158 I.2, примітка 1; I.11)
    frag_complement_dumku = "Він реагує на слова, на думку про відпустку, і пише довгого листа."
    assert not miner.is_parenthetical_segment("на думку про відпустку", cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_complement_dumku, cur_ves=cur)
    assert not miner.is_pristine_eval_sentence(frag_complement_dumku, cur_ves=cur)

    # Positive control 1 (Round 17 P2): Legitimate source attribution parenthetical 'на думку експертів' (Правопис 2019 §158 I.11)
    frag_valid_attribution = "Він реагує на слова, на думку експертів, і пише довгого листа."
    assert miner.is_parenthetical_segment("на думку експертів", cur_ves=cur)
    assert not miner.has_homogeneous_verb_comma(frag_valid_attribution, cur_ves=cur)
    assert miner.is_pristine_eval_sentence(frag_valid_attribution, cur_ves=cur)

    # Positive control 2 (Round 17 P2): Legitimate attribution parenthetical with 'словами' (Правопис 2019 §158 I.11)
    frag_valid_slovamy = "Він реагує на слова, словами автора, і пише довгого листа."
    assert miner.is_parenthetical_segment("словами автора", cur_ves=cur)
    assert not miner.has_homogeneous_verb_comma(frag_valid_slovamy, cur_ves=cur)
    assert miner.is_pristine_eval_sentence(frag_valid_slovamy, cur_ves=cur)

    # Positive control 3 (Round 17 P2): Removing erroneous comma before 'і' restores pristine status for ordinary complements
    frag_no_erroneous_comma = "Він реагує на слова, на думку про відпустку і пише довгого листа."
    assert not miner.has_homogeneous_verb_comma(frag_no_erroneous_comma, cur_ves=cur)

    # Defect 40 / Negative regression (Round 18 P2): Malformed parenthetical with incompatible modifier agreement 'на моїй думку' (Правопис 2019 §158 I.11)
    frag_incompatible_modifier = "Він реагує на слова, на моїй думку, і пише довгого листа."
    assert not miner.is_parenthetical_segment("на моїй думку", cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_incompatible_modifier, cur_ves=cur)
    assert not miner.is_pristine_eval_sentence(frag_incompatible_modifier, cur_ves=cur)

    # Positive control 1 (Round 18 P2): Valid pre-nominal modifier agreement with 'думку' (Правопис 2019 §158 I.11)
    frag_valid_f_zna = "Він реагує на слова, на мою думку, і пише довгого листа."
    assert miner.is_parenthetical_segment("на мою думку", cur_ves=cur)
    assert not miner.has_homogeneous_verb_comma(frag_valid_f_zna, cur_ves=cur)
    assert miner.is_pristine_eval_sentence(frag_valid_f_zna, cur_ves=cur)

    # Positive control 2 (Round 18 P2): Valid pre-nominal modifier agreement with 'погляд' (Правопис 2019 §158 I.11)
    frag_valid_m_zna = "Він реагує на слова, на мій погляд, і пише довгого листа."
    assert miner.is_parenthetical_segment("на мій погляд", cur_ves=cur)
    assert not miner.has_homogeneous_verb_comma(frag_valid_m_zna, cur_ves=cur)
    assert miner.is_pristine_eval_sentence(frag_valid_m_zna, cur_ves=cur)

    # Defect 41 / Negative regression (Round 19 P2): Invariable noun 'метро' modifying 'думку' rejected (Правопис 2019 §158 I.11)
    frag_metro_dumku = "Він реагує на слова, на метро думку, і пише довгого листа."
    assert not miner.is_parenthetical_segment("на метро думку", cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_metro_dumku, cur_ves=cur)
    assert not miner.is_pristine_eval_sentence(frag_metro_dumku, cur_ves=cur)

    # Defect 42 / Negative regression (Round 19 P2): Invariable noun 'таксі' modifying 'погляд' rejected (Правопис 2019 §158 I.11)
    frag_taksi_pohlyad = "Він реагує на слова, на таксі погляд, і пише довгого листа."
    assert not miner.is_parenthetical_segment("на таксі погляд", cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_taksi_pohlyad, cur_ves=cur)
    assert not miner.is_pristine_eval_sentence(frag_taksi_pohlyad, cur_ves=cur)

    # Defect 43 / Negative regression (Round 20 P2): Animate accusative modifier 'першого' with inanimate head 'погляд' rejected (Правопис 2019 §158 I.11)
    frag_pershoho_pohlyad = "Він реагує на слова, на першого погляд, і пише довгого листа."
    assert not miner.is_parenthetical_segment("на першого погляд", cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_pershoho_pohlyad, cur_ves=cur)
    assert not miner.is_pristine_eval_sentence(frag_pershoho_pohlyad, cur_ves=cur)

    # Defect 44 / Negative regression (Round 20 P2): Animate accusative modifier 'мого' with inanimate head 'погляд' rejected (Правопис 2019 §158 I.11)
    frag_moho_pohlyad = "Він реагує на слова, на мого погляд, і пише довгого листа."
    assert not miner.is_parenthetical_segment("на мого погляд", cur_ves=cur)
    assert miner.has_homogeneous_verb_comma(frag_moho_pohlyad, cur_ves=cur)
    assert not miner.is_pristine_eval_sentence(frag_moho_pohlyad, cur_ves=cur)

    # Defect 45 / Negative regression (Round 21 P2): Unpunctuated source-attribution parenthetical following coordinating conjunction lacking opening comma (Правопис 2019 §158 I.11)
    frag_ta_yak_perekonyuyut = "Та як переконують обізнані з методикою фінансування галузі, можливості влади обласного рівня тут обмежені."
    assert miner.UNPUNCTUATED_CONJUNCTION_PARENTHETICAL_RE.search(frag_ta_yak_perekonyuyut)
    assert not miner.is_pristine_eval_sentence(frag_ta_yak_perekonyuyut, cur_ves=cur)

    # Defect 46 / Positive control (Round 21 P2): Properly punctuated source-attribution parenthetical with opening comma (Правопис 2019 §158 I.11)
    frag_ta_yak_valid = "Та, як переконують обізнані з методикою фінансування галузі, можливості влади обласного рівня тут обмежені."
    assert not miner.UNPUNCTUATED_CONJUNCTION_PARENTHETICAL_RE.search(frag_ta_yak_valid)
    assert miner.is_pristine_eval_sentence(frag_ta_yak_valid, cur_ves=cur)

    # Defect 47 / Negative regression (Round 21 P2): Discordant personal name case agreement 'Олега Токарчуку' (genitive + dative)
    frag_oleha_tokarchuku = "Редакція «Дзеркала Коломиї» зателефонувала головлікареві Коломийської дитячої лікарні Олега Токарчуку з проханням розповісти про останні новини."
    assert miner.DISCORDANT_PERSONAL_NAME_CASE_RE.search(frag_oleha_tokarchuku)
    assert not miner.is_pristine_eval_sentence(frag_oleha_tokarchuku, cur_ves=cur)

    # Defect 48 / Positive control (Round 21 P2): Clean replacement literary sentence
    frag_shcho_stosuetsya = "А що стосується лікарів, то їм доведеться поки що обійтися 30 відсотками платні."
    assert not miner.DISCORDANT_PERSONAL_NAME_CASE_RE.search(frag_shcho_stosuetsya)
    assert miner.is_pristine_eval_sentence(frag_shcho_stosuetsya, cur_ves=cur)

    # Defect 49 / Negative regression (Round 23 P2): Unpunctuated asyndetic condition clause lacking dash (Правопис 2019 §161 II.1)
    frag_ne_vystachae_comma = "Не вистачає, скажімо, у якомусь селі коштів на ремонт доріг, школи, фельдшерсько-акушерського пункту, допоможе об'єднана громада."
    assert miner.UNPUNCTUATED_ASYNDETIC_CONDITION_RE.search(frag_ne_vystachae_comma)
    assert not miner.is_pristine_eval_sentence(frag_ne_vystachae_comma, cur_ves=cur)

    # Defect 50 / Positive control (Round 23 P2): Properly punctuated asyndetic condition with dash (Правопис 2019 §161 II.1)
    frag_ne_vystachae_dash = "Не вистачає, скажімо, у якомусь селі коштів на ремонт доріг, школи, фельдшерсько-акушерського пункту — допоможе об'єднана громада."
    assert not miner.UNPUNCTUATED_ASYNDETIC_CONDITION_RE.search(frag_ne_vystachae_dash)
    assert miner.is_pristine_eval_sentence(frag_ne_vystachae_dash, cur_ves=cur)

    # Defect 51 / Positive control (Round 23 P2): Clean replacement literary sentence
    frag_yikh_same_dlya_tsyoho = "Їх саме для цього обирали, і у своїх передвиборних програмах вони на цьому акцентували."
    assert not miner.UNPUNCTUATED_ASYNDETIC_CONDITION_RE.search(frag_yikh_same_dlya_tsyoho)
    assert miner.is_pristine_eval_sentence(frag_yikh_same_dlya_tsyoho, cur_ves=cur)

    # Defect 52 / Negative regression (Round 24 P2): Pleonastic numeral affix '26-ого' (Городенська 2017, p. 163)
    frag_26_oho = "Що буде після 26-ого, прогнозувати важко."
    assert miner.INVALID_NUMERAL_AFFIX_RE.search(frag_26_oho)
    assert not miner.is_pristine_eval_sentence(frag_26_oho, cur_ves=cur)

    # Defect 53 / Negative regression (Round 24 P2): Pleonastic numeral affix '80-их' (Городенська 2017, p. 163)
    frag_80_ykh = "Чимало поколінь дітей гралися такими іграшками, проте у 80-их роках XX століття традиція їхнього створення почала занепадати."
    assert miner.INVALID_NUMERAL_AFFIX_RE.search(frag_80_ykh)
    assert not miner.is_pristine_eval_sentence(frag_80_ykh, cur_ves=cur)

    # Defect 54 / Positive control (Round 24 P2): Properly affixed numeral '26-го' (Городенська 2017, p. 163)
    frag_26_ho = "Що буде після 26-го, прогнозувати важко."
    assert not miner.INVALID_NUMERAL_AFFIX_RE.search(frag_26_ho)
    assert miner.is_pristine_eval_sentence(frag_26_ho, cur_ves=cur)

    # Defect 55 / Positive control (Round 24 P2): Properly affixed numeral '80-х' (Городенська 2017, p. 163)
    frag_80_kh = "Чимало поколінь дітей гралися такими іграшками, проте у 80-х роках XX століття традиція їхнього створення почала занепадати."
    assert not miner.INVALID_NUMERAL_AFFIX_RE.search(frag_80_kh)
    assert miner.is_pristine_eval_sentence(frag_80_kh, cur_ves=cur)



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
