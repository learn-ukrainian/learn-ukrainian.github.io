"""Unit tests for Phase 5.8: Middle Ukrainian & Cossack Baroque Literature Mining Engine.

Parent Epic: #6321 (Open Model Data)
Issue: #8105
"""

import ast
import json
import re
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v5_mine_middle_ukrainian import (
    DEFAULT_SOURCES_DB,
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
    evaluate_middle_ukrainian_suite,
    exact_clopper_pearson_lower,
    is_editorial_preface,
    load_middle_ukrainian_chunks,
    load_replay_buffer,
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
    assert "zyzaniy_leksys_1596" in EXCLUDED_MODERN_WORKS
    assert "smotrytskyy_hramatiky_slovenskiya_1619" in EXCLUDED_MODERN_WORKS

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
        text="Секретне речення для перевірки нульового витоку інформації у тренувальний набір панованє. Друге контрольне речення для перевірки збереження лінгвістичних ознак вольности.",
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
        text="Абсолютно незалежний текст щоденника для тренування моделі без витоку даних албо листъ. Друга частина щоденникових записів про перебіг справ гетман.",
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


def test_evaluator_strictness_and_rejection() -> None:
    """Verify that evaluate_middle_ukrainian_suite rejects dummy/uncorrected/incomplete predictions."""
    eval_suite = [
        {
            "eval_id": "eval_001",
            "case_type": "PRESERVE",
            "input_text": "Се я, князь великий, далъ есмо сесь нашъ листъ земяномъ киевскимъ.",
            "expected_output": "Се я, князь великий, далъ есмо сесь нашъ листъ земяномъ киевскимъ.",
            "has_injected_error": False,
        },
        {
            "eval_id": "eval_002",
            "case_type": "CORRECT",
            "input_text": "Се я, князь великий. [Вставка: приймати участь]",
            "expected_output": "Се я, князь великий. брати участь",
            "target_term": "приймати участь",
            "injected_error": "приймати участь",
            "expected_replacement": "брати участь",
            "has_injected_error": True,
        },
    ]

    # 1. Reject predictions=None
    with pytest.raises(ValueError, match="predictions must be provided"):
        evaluate_middle_ukrainian_suite(eval_suite, None)

    # 2. Reject dummy [PRESERVE] prediction
    res = evaluate_middle_ukrainian_suite(
        eval_suite,
        [
            {"eval_id": "eval_001", "predicted_output": "[PRESERVE]"},
            {"eval_id": "eval_002", "predicted_output": "Се я, князь великий. брати участь"},
        ],
    )
    assert res["preservation_rate"] == 0.0
    assert res["mixed_error_correction_rate"] == 1.0
    assert res["accuracy"] == 0.5

    # 3. Reject uncorrected error in mixed case
    res = evaluate_middle_ukrainian_suite(
        eval_suite,
        [
            {
                "eval_id": "eval_001",
                "predicted_output": "Се я, князь великий, далъ есмо сесь нашъ листъ земяномъ киевскимъ.",
            },
            {"eval_id": "eval_002", "predicted_output": "Се я, князь великий. приймати участь"},
        ],
    )
    assert res["preservation_rate"] == 1.0
    assert res["mixed_error_correction_rate"] == 0.0
    assert res["accuracy"] == 0.5

    # 4. Reject missing replacement in mixed case
    res = evaluate_middle_ukrainian_suite(
        eval_suite,
        [
            {
                "eval_id": "eval_001",
                "predicted_output": "Се я, князь великий, далъ есмо сесь нашъ листъ земяномъ киевскимъ.",
            },
            {"eval_id": "eval_002", "predicted_output": "Се я, князь великий."},
        ],
    )
    assert res["mixed_error_correction_rate"] == 0.0

    # 5. Reject dropped historical text in mixed case
    res = evaluate_middle_ukrainian_suite(
        eval_suite,
        [
            {
                "eval_id": "eval_001",
                "predicted_output": "Се я, князь великий, далъ есмо сесь нашъ листъ земяномъ киевскимъ.",
            },
            {"eval_id": "eval_002", "predicted_output": "брати участь"},
        ],
    )
    assert res["mixed_error_correction_rate"] == 0.0

    # 5b. Adversarial: reject truncated historical text with inserted error correction (Finding 1)
    res = evaluate_middle_ukrainian_suite(
        eval_suite,
        [
            {
                "eval_id": "eval_001",
                "predicted_output": "Се я, князь великий, далъ есмо сесь нашъ листъ земяномъ киевскимъ.",
            },
            {
                "eval_id": "eval_002",
                "predicted_output": eval_suite[1]["input_text"][0]
                + " [Вставка: "
                + eval_suite[1]["expected_replacement"]
                + "]",
            },
        ],
    )
    assert res["mixed_error_correction_rate"] == 0.0
    assert res["accuracy"] == 0.5

    # 6. Valid predictions score 100%
    res = evaluate_middle_ukrainian_suite(
        eval_suite,
        [
            {
                "eval_id": "eval_001",
                "predicted_output": "Се я, князь великий, далъ есмо сесь нашъ листъ земяномъ киевскимъ.",
            },
            {"eval_id": "eval_002", "predicted_output": "Се я, князь великий. брати участь"},
        ],
    )
    assert res["accuracy"] == 1.0
    assert res["preservation_rate"] == 1.0
    assert res["mixed_error_correction_rate"] == 1.0


def test_sft_dataset_balance_and_interleaving() -> None:
    """Verify that build_sft_dataset generates a strict 50/50 balance of PRESERVE/CORRECT rows."""
    mock_chunks = [
        MiddleUkrainianChunk(
            id=i + 1,
            chunk_id=f"train_chunk_{i:04d}",
            work_id="shchodennyk_mykoly_khanenka_1719_1754",
            work_title="Щоденник Ханенка",
            author="Ханенко М.",
            year=1754,
            genre="diary",
            text=f"Абсолютно автентичний текст розділу {i} про панованє та звичаї полку албо листъ. "
            f"Друге вагоме речення з історичними деталями про вольности номер {i} гетман.",
            char_count=350,
            stratum=STRATA_HIGH_COSSACK_BAROQUE,
            composition_date="1754",
            manuscript_or_print_date="1884",
            is_archaic=True,
        )
        for i in range(10)
    ]

    sft_data = build_sft_dataset(
        mock_chunks,
        eval_suite=[],
        vesum_db=DEFAULT_VESUM_DB,
        target_sft_quota=20,
        replay_quota=4,
        seed=42,
    )

    assert len(sft_data) == 20
    preserve_count = sum(1 for t in sft_data if not t["is_calque_or_russianism"])
    correct_count = sum(1 for t in sft_data if t["is_calque_or_russianism"])
    assert preserve_count == 10
    assert correct_count == 10

    # Verify interleaving (adjacent items alternate)
    for i in range(len(sft_data) - 1):
        assert sft_data[i]["is_calque_or_russianism"] != sft_data[i + 1]["is_calque_or_russianism"]

    # Verify schema compliance for correction rows
    valid_registers = {"living_standard", "classical_regional", "technical_compound", "purist_neologism"}
    for t in sft_data:
        if t["is_calque_or_russianism"]:
            ctx = t.get("lexicographical_context")
            assert ctx is not None
            assert "historical_suppression_note" in ctx
            alts = t.get("register_spectrum", {}).get("alternatives", [])
            assert len(alts) > 0
            for alt in alts:
                assert alt["register_tier"] in valid_registers


def test_replay_buffer_sources_and_attestations() -> None:
    """Verify that replay buffer loads dialect preservation and modern literary anti-calque rows without medieval v0.4a."""
    trajectories = load_replay_buffer(DEFAULT_VESUM_DB, quota=20)
    assert len(trajectories) == 20

    preserve_count = sum(1 for t in trajectories if not t.get("is_calque_or_russianism", False))
    correct_count = sum(1 for t in trajectories if t.get("is_calque_or_russianism", False))
    assert preserve_count == 10
    assert correct_count == 10

    for t in trajectories:
        # Must not contain medieval Kyivan Rus v0.4a identifiers
        tid = t.get("trajectory_id", "")
        assert "kyivan_rus" not in tid
        assert "v04a" not in tid
        assert "epigraphy" not in tid

        # VESUM attestations must contain modern_literary_replay tag
        attestations = t.get("vesum_attestation", [])
        assert len(attestations) > 0
        for att in attestations:
            assert "modern_literary_replay" in att.get("tags", [])


def test_release_dataset_disk_invariants() -> None:
    """Verify on-disk release artifacts strictly meet all quota, balance, and file-size invariants."""
    release_dir = REPO_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v04b_middle_ukrainian"
    eval_file = release_dir / "middle_ukrainian_eval.jsonl"
    manifest_file = release_dir / "sft" / "manifest.json"

    if not eval_file.is_file() or not manifest_file.is_file():
        pytest.skip("Release artifacts not yet generated on disk")

    # Eval invariants
    eval_rows = [json.loads(line) for line in eval_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(eval_rows) == 500
    eval_preserve = sum(1 for r in eval_rows if r["case_type"] == "PRESERVE")
    eval_correct = sum(1 for r in eval_rows if r["case_type"] == "CORRECT")
    assert eval_preserve == 250
    assert eval_correct == 250

    # SFT invariants
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["total_trajectories"] == 10000
    assert manifest["total_shards"] == 30

    sft_rows_count = 0
    sft_preserve = 0
    sft_correct = 0

    for shard_info in manifest["shards"]:
        shard_path = release_dir / "sft" / shard_info["file_name"]
        assert shard_path.is_file()
        assert shard_path.stat().st_size < 2000 * 1024, f"File {shard_path.name} exceeds 2,000 KB"
        with shard_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    sft_rows_count += 1
                    if row.get("is_calque_or_russianism", False):
                        sft_correct += 1
                    else:
                        sft_preserve += 1

    assert sft_rows_count == 10000
    assert sft_preserve == 5000
    assert sft_correct == 5000


def test_no_editorial_apparatus_in_released_artifacts() -> None:
    """Verify no editorial commentaries, modern studies, or academic prefaces exist in released files."""
    release_dir = REPO_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v04b_middle_ukrainian"
    eval_file = release_dir / "middle_ukrainian_eval.jsonl"
    sft_dir = release_dir / "sft"

    if not eval_file.is_file():
        pytest.skip("Release artifacts not yet generated on disk")

    forbidden_snippets = [
        "упорядник",
        "радянськ",
        "дослідник",
        "дисертаці",
        "монографі",
        "ЦДІА",
        "німчук",
        "пещак",
        "боплан",
        "срезневськ",
    ]

    with eval_file.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            inp = row.get("input_text", "")
            exp = row.get("expected_output", "")
            for snip in forbidden_snippets:
                assert snip not in inp.casefold(), f"Editorial snippet '{snip}' found in eval row {i}: {inp}"
                assert snip not in exp.casefold(), f"Editorial snippet '{snip}' found in eval row {i}: {exp}"

    for shard in sft_dir.glob("sft_shard_*.jsonl"):
        with shard.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                row = json.loads(line)
                q = row.get("query", "")
                m = re.search(r"«(.*?)»", q)
                hist = m.group(1) if m else q
                for snip in forbidden_snippets:
                    assert snip not in hist.casefold(), (
                        f"Editorial snippet '{snip}' found in {shard.name} row {i}: {hist}"
                    )


def test_vesum_attestation_consistency_in_released_artifacts() -> None:
    """Verify that is_standard_attested strictly equals (vesum_forms_count > 0) across all SFT rows."""
    release_dir = REPO_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v04b_middle_ukrainian"
    sft_dir = release_dir / "sft"

    if not sft_dir.is_dir():
        pytest.skip("Release artifacts not yet generated on disk")

    for shard in sft_dir.glob("sft_shard_*.jsonl"):
        with shard.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                row = json.loads(line)
                attestations = row.get("vesum_attestation", [])
                assert len(attestations) > 0, f"Missing attestations in {shard.name} row {i}"
                for att in attestations:
                    count = att.get("vesum_forms_count", 0)
                    is_attested = att.get("is_standard_attested")
                    assert is_attested == (count > 0), (
                        f"Inconsistent attestation in {shard.name} row {i}: is_standard_attested={is_attested}, count={count}"
                    )


def test_release_receipt_schema_validation() -> None:
    """Verify that release_receipt.json strictly validates against the receipt schema contract."""
    receipt_file = (
        REPO_ROOT
        / "data"
        / "projects"
        / "open_model_data"
        / "release"
        / "uldr_v04b_middle_ukrainian"
        / "release_receipt.json"
    )
    schema_file = (
        REPO_ROOT
        / "data"
        / "projects"
        / "open_model_data"
        / "contracts"
        / "v1_middle_ukrainian_release_receipt.schema.json"
    )

    if not receipt_file.is_file():
        pytest.skip("Release receipt not yet generated on disk")

    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))

    validator = jsonschema.Draft202012Validator(schema)
    validator.validate(receipt)

    assert receipt["evaluation_metrics"]["status"] in ("measured", "unmeasured")
    if receipt["evaluation_metrics"]["status"] == "unmeasured":
        assert receipt["evaluation_metrics"]["v04b_eval_accuracy"] is None
        assert receipt["evaluation_metrics"]["confidence_interval_95"] is None
        assert receipt["evaluation_metrics"]["regression_against_v02_pct"] is None


def test_regression_velychkovsky_and_mytsyk_commentary_excluded() -> None:
    """Verify that specific Round 3 and Round 4 commentary leaks (Velychkovsky, Mytsyk, Khanenko) are excluded."""
    release_dir = REPO_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v04b_middle_ukrainian"
    eval_file = release_dir / "middle_ukrainian_eval.jsonl"
    sft_dir = release_dir / "sft"

    if not eval_file.is_file():
        pytest.skip("Release artifacts not yet generated on disk")

    leaked_strings = [
        "поет славить «добра воина»",
        "поет славить",
        "несообразностями, они дают ряд интересных фактов",
        "несообразностями",
        "они дают ряд интересных фактов",
        "авторъ „дневника“ — генеральный хоружій николай",
        "авторъ „дневника“",
        "генеральный хоружій николай",
        "въ первой половинЂ xvii село волосковичи",
        "село волосковичи",
        "считается стефанъ ханенко, запорожецъ",
        "стефанъ ханенко",
    ]

    eval_rows = []
    with eval_file.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            eval_rows.append(row)
            inp = row.get("input_text", "").casefold()
            exp = row.get("expected_output", "").casefold()
            for s in leaked_strings:
                assert s not in inp, f"Leaked string '{s}' found in eval row {i}: {inp}"
                assert s not in exp, f"Leaked string '{s}' found in eval row {i}: {exp}"
            assert row.get("source_metadata", {}).get("chunk_id") != "1b7685d5_c0057"
            assert row.get("source_metadata", {}).get("chunk_id") != "5f2476e8_c0004"

    # Verify Ivan Velychkovsky is actively represented in the held-out evaluation benchmark
    v_eval_rows = [r for r in eval_rows if r.get("work_id") == "ivan_velychkovskyy_tvory"]
    assert len(v_eval_rows) > 0, "Evaluation suite must contain records from Ivan Velychkovsky"

    for shard in sft_dir.glob("sft_shard_*.jsonl"):
        with shard.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                row = json.loads(line)
                q = row.get("query", "").casefold()
                resp = row.get("final_response", "").casefold()
                for s in leaked_strings:
                    assert s not in q, f"Leaked string '{s}' found in {shard.name} row {i}: {q}"
                    assert s not in resp, f"Leaked string '{s}' found in {shard.name} row {i}: {resp}"


def test_source_boundaries_and_work_exclusions() -> None:
    """Verify that source boundaries are strictly enforced and excluded works are never admitted."""
    assert "litopystsi_krokovskoho_ta_yasynskoho" in EXCLUDED_MODERN_WORKS
    assert "suspilno_politychna_dumka_xvi_xvii_st" in EXCLUDED_MODERN_WORKS
    assert "sherer_litopys_malorosiyi_1788" in EXCLUDED_MODERN_WORKS
    assert "shevalye_istoriya_viyny_kozakiv_proty_polshchi_1663" in EXCLUDED_MODERN_WORKS
    assert "pivdennoruski_litopysy_bilozerskyy" in EXCLUDED_MODERN_WORKS
    assert "feodosiy_sofonovych_khronika_z_litopystsiv_starodavnikh" in EXCLUDED_MODERN_WORKS
    assert "rihelman_litopysna_opovid_pro_malu_rosiyu" in EXCLUDED_MODERN_WORKS

    if DEFAULT_SOURCES_DB.is_file():
        chunks = load_middle_ukrainian_chunks(DEFAULT_SOURCES_DB)

        v_chunks = [c for c in chunks if c.work_id == "ivan_velychkovskyy_tvory"]
        assert len(v_chunks) == 76, f"Expected 76 Velychkovsky chunks (70-145), got {len(v_chunks)}"
        for c in v_chunks:
            num = int(c.chunk_id.split("_c")[-1])
            assert 70 <= num <= 145, f"Invalid Velychkovsky chunk admitted: {c.chunk_id}"

        k_chunks = [c for c in chunks if c.work_id == "shchodennyk_mykoly_khanenka_1719_1754"]
        assert len(k_chunks) > 0, "Expected Khanenko diary chunks to be loaded"
        for c in k_chunks:
            num = int(c.chunk_id.split("_c")[-1])
            assert num > 16, f"Lazarevsky intro chunk admitted: {c.chunk_id}"
            assert not (635 <= num <= 647), f"Bodyansky preface chunk admitted: {c.chunk_id}"
            assert not re.match(r"^\s*\d+\)\s+", c.text), f"Footnote chunk admitted: {c.chunk_id}"

        for c in chunks:
            assert c.work_id not in EXCLUDED_MODERN_WORKS
            if c.work_id == "hramoty_xiv_st":
                num = int(c.chunk_id.split("_c")[-1])
                assert 40 <= num <= 90, f"Invalid hramoty_xiv_st chunk admitted: {c.chunk_id}"
            elif c.work_id == "ukrayinski_intermediyi_xvii_xviii_st":
                num = int(c.chunk_id.split("_c")[-1])
                assert num >= 171, f"Invalid intermediyi chunk admitted: {c.chunk_id}"
            elif "bayky_" in c.work_id:
                num = int(c.chunk_id.split("_c")[-1])
                assert 80 <= num <= 240, f"Invalid bayky chunk admitted: {c.chunk_id}"
