"""Unit tests for Phase 5.8: Middle Ukrainian & Cossack Baroque Literature Mining Engine.

Parent Epic: #6321 (Open Model Data)
Issue: #8105
"""

import ast
import json
from pathlib import Path

import jsonschema

from scripts.projects.open_model_data.v5_mine_middle_ukrainian import (
    DEFAULT_VESUM_DB,
    EVAL_SCHEMA_FILE,
    EXCLUDED_MODERN_WORKS,
    HELD_OUT_EVAL_WORKS,
    STRATA_EARLY_RUTHENIAN,
    STRATA_HIGH_COSSACK_BAROQUE,
    STRATA_RENAISSANCE_POLEMICAL,
    STRATA_TRANSITIONAL_PRE_MODERN,
    MiddleUkrainianChunk,
    build_eval_suite,
    build_sft_dataset,
    classify_stratum,
    clean_text_diplomatic,
    exact_clopper_pearson_lower,
    is_editorial_preface,
    normalize_historical_snippet,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_strata_classification_and_date_disambiguation() -> None:
    """Verify that works are accurately partitioned into 4 chronological strata with date disambiguation."""
    # 1. Early Ruthenian Chancery
    strat, comp, ms = classify_stratum("hramoty_xiv_st", 1350)
    assert strat == STRATA_EARLY_RUTHENIAN
    assert "1350" in comp
    assert "XIV" in ms

    # 2. Renaissance & Polemical
    strat, comp, ms = classify_stratum("druhyy_volynskyy_statut_vkl_1566_roku", 1566)
    assert strat == STRATA_RENAISSANCE_POLEMICAL
    assert "1566" in comp

    strat, comp, ms = classify_stratum("ukrayinska_poeziya_kinets_xvi_seredyna_xvii_st", 1600)
    assert strat == STRATA_RENAISSANCE_POLEMICAL

    # 3. High Cossack Baroque
    strat, comp, ms = classify_stratum("shchodennyk_mykoly_khanenka_1719_1754", 1754)
    assert strat == STRATA_HIGH_COSSACK_BAROQUE
    assert "1648" in comp

    strat, comp, ms = classify_stratum("feodosiy_sofonovych_khronika_z_litopystsiv_starodavnikh", 1673)
    assert strat == STRATA_HIGH_COSSACK_BAROQUE

    # 4. Transitional / Pre-Modern
    strat, comp, ms = classify_stratum("istoriya_rusiv", 1829)
    assert strat == STRATA_TRANSITIONAL_PRE_MODERN
    assert "1765" in comp or "1829" in comp

    strat, comp, ms = classify_stratum("rihelman_litopysna_opovid_pro_malu_rosiyu", 1785)
    assert strat == STRATA_TRANSITIONAL_PRE_MODERN


def test_translation_segregation_and_preface_filtering() -> None:
    """Verify that modern translations and academic prefaces are strictly segregated."""
    # Excluded modern translations
    assert "feofan_prokopovych_filosofski_tvory" in EXCLUDED_MODERN_WORKS
    assert "uzhevych_paryzkyy_rukopys_pereklad_1970" in EXCLUDED_MODERN_WORKS
    assert "samiylo_velychko_litopys_1648_1700" in EXCLUDED_MODERN_WORKS
    assert "synopsys_kyyiv_1674" in EXCLUDED_MODERN_WORKS

    # Modern editorial preface detection
    preface_sample = (
        "Упорядники висловлюють щиру подяку працівникам ЦДІА України у м. Києві. "
        "У радянський час дослідники неодноразово зверталися до цього рукопису."
    )
    assert is_editorial_preface(preface_sample) is True

    # Authentic historical text must NOT be detected as preface
    authentic_sample = (
        "Се я, князь великий, далъ есмо сесь нашъ листъ земяномъ киевскимъ и всЂмъ людемъ посполитымъ, "
        "абы мЂли вольности свои и права, яко первеи было."
    )
    assert is_editorial_preface(authentic_sample) is False


def test_document_partitioning_disjointness() -> None:
    """Verify that held-out evaluation works are strictly disjoint from training works."""
    assert "symonovskyy_korotkyy_opys_pro_kozatskyy_malorosiyskyy_narod" in HELD_OUT_EVAL_WORKS
    assert "ivan_velychkovskyy_tvory" in HELD_OUT_EVAL_WORKS
    assert "chernihivskyy_litopys" in HELD_OUT_EVAL_WORKS
    assert "zyzaniy_leksys_1596" in HELD_OUT_EVAL_WORKS

    for w in HELD_OUT_EVAL_WORKS:
        assert w not in EXCLUDED_MODERN_WORKS


def test_clean_text_diplomatic() -> None:
    """Verify diplomatic cleaning preserves historical Cyrillic characters and strips markup/page numbers."""
    raw = "<p>Се я, кн̃зь <b>Олександр</b>\\47\\ [12] далъ листъ&nbsp;свой.</p>"
    cleaned = clean_text_diplomatic(raw)
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "\\47\\" not in cleaned
    assert "[12]" not in cleaned
    assert "кн̃зь" in cleaned
    assert "листъ свой" in cleaned


def test_normalize_historical_snippet() -> None:
    """Verify normalization strips injected tags and punctuation for leak detection."""
    sample = "Се я, князь великий! [Вставка: приймати участь]"
    norm = normalize_historical_snippet(sample)
    assert "вставка" not in norm
    assert "приймати" not in norm
    assert norm == "сеякнязьвеликий"


def test_eval_suite_generation_and_schema() -> None:
    """Verify that evaluation suite generates valid records matching schema contract."""
    mock_chunks = [
        MiddleUkrainianChunk(
            id=1,
            chunk_id="test_c0001",
            work_id="symonovskyy_korotkyy_opys_pro_kozatskyy_malorosiyskyy_narod",
            work_title="Короткий опис про козацький народ",
            author="Симоновський П.",
            year=1765,
            genre="chronicle",
            text="Для лучшей от непріятельских нападеній безопасности собралось войска малороссійскаго пять тысячъ человЂкъ. А по сему случаю козаки стояли обозомъ у рЂки ДнЂпра въ готовности.",
            char_count=350,
            stratum=STRATA_TRANSITIONAL_PRE_MODERN,
            composition_date="1765",
            manuscript_or_print_date="1847",
            is_archaic=True,
        ),
        MiddleUkrainianChunk(
            id=2,
            chunk_id="test_c0002",
            work_id="ivan_velychkovskyy_tvory",
            work_title="Твори Івана Величковського",
            author="Величковський І.",
            year=1690,
            genre="poetry",
            text="Гавріил зачатіє дЂвЂ возвЂщаєт и спасеніє миру явлѧет во ВифлеємЂ от дЂвы пречистої. В день же осмый по закону Господню обрЂзаніє приѧти изволилъ Хрїстосъ Спаситель нашъ.",
            char_count=300,
            stratum=STRATA_HIGH_COSSACK_BAROQUE,
            composition_date="1690",
            manuscript_or_print_date="1972",
            is_archaic=True,
        ),
    ]

    eval_suite = build_eval_suite(mock_chunks, target_quota=4, seed=42)
    assert len(eval_suite) == 4

    eval_schema = json.loads(EVAL_SCHEMA_FILE.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(eval_schema)

    preserve_count = 0
    correct_count = 0
    for case in eval_suite:
        validator.validate(case)
        if case["case_type"] == "PRESERVE":
            preserve_count += 1
            assert case["expected_action"] == "PRESERVE"
            assert case["has_injected_error"] is False
        else:
            correct_count += 1
            assert case["expected_action"] == "CORRECT_INJECTED_ERROR"
            assert case["has_injected_error"] is True
            assert case["expected_replacement"] is not None

    assert preserve_count == 2
    assert correct_count == 2


def test_zero_train_eval_leakage_firewall(tmp_path: Path) -> None:
    """Verify that no held-out eval sentences leak into training trajectories."""
    mock_eval_chunk = MiddleUkrainianChunk(
        id=1,
        chunk_id="eval_c0001",
        work_id="symonovskyy_korotkyy_opys_pro_kozatskyy_malorosiyskyy_narod",
        work_title="Симоновський",
        author="Симоновський П.",
        year=1765,
        genre="prose",
        text="Секретне речення для перевірки нульового витоку інформації у тренувальний набір. Друге контрольне речення для перевірки збереження лінгвістичних ознак.",
        char_count=300,
        stratum=STRATA_TRANSITIONAL_PRE_MODERN,
        composition_date="1765",
        manuscript_or_print_date="1847",
        is_archaic=True,
    )
    mock_train_chunk = MiddleUkrainianChunk(
        id=2,
        chunk_id="train_c0001",
        work_id="shchodennyk_mykoly_khanenka_1719_1754",
        work_title="Щоденник Ханенка",
        author="Ханенко М.",
        year=1754,
        genre="diary",
        text="Абсолютно незалежний текст щоденника для тренування моделі без витоку даних. Друга частина щоденникових записів про перебіг козацьких справ.",
        char_count=300,
        stratum=STRATA_HIGH_COSSACK_BAROQUE,
        composition_date="1754",
        manuscript_or_print_date="1884",
        is_archaic=True,
    )

    eval_suite = build_eval_suite([mock_eval_chunk], target_quota=2, seed=42)
    sft_data = build_sft_dataset(
        [mock_train_chunk],
        eval_suite=eval_suite,
        vesum_db=DEFAULT_VESUM_DB,
        target_sft_quota=4,
        replay_quota=2,
        seed=42,
    )

    eval_norm = {normalize_historical_snippet(c["input_text"]) for c in eval_suite}
    for t in sft_data:
        q_norm = normalize_historical_snippet(t["query"])
        resp_norm = normalize_historical_snippet(t["final_response"])
        for en in eval_norm:
            assert en not in q_norm, f"Leakage detected in query: {en}"
            assert en not in resp_norm, f"Leakage detected in response: {en}"


def test_clopper_pearson_confidence_interval() -> None:
    """Verify that exact Clopper-Pearson computation produces statistically sound lower bound."""
    lower = exact_clopper_pearson_lower(500, 500, alpha=0.05)
    assert 0.99 <= lower <= 1.0

    lower_half = exact_clopper_pearson_lower(250, 500, alpha=0.05)
    assert 0.45 <= lower_half <= 0.55


def test_subprocess_timeout_guard_in_script() -> None:
    """Verify that all subprocess calls in v5_mine_middle_ukrainian.py pass explicit timeout=."""
    script_path = REPO_ROOT / "scripts" / "projects" / "open_model_data" / "v5_mine_middle_ukrainian.py"
    tree = ast.parse(script_path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name in ("check_output", "run", "Popen", "check_call"):
                has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
                assert has_timeout, f"Subprocess call {func_name} at line {node.lineno} missing timeout="
