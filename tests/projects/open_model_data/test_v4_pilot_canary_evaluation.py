"""Unit and regression tests for Phase 3.6 Pilot Canary Evaluation (#8010)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import numpy as np
import pytest

from scripts.lib.readonly_sqlite import open_readonly
from scripts.projects.open_model_data.v4_pilot_canary_evaluation import (
    CANARY_RECEIPT_SCHEMA_PATH,
    DEFAULT_ADAPTER_OUTPUT,
    DEFAULT_DATASET_OUTPUT,
    DEFAULT_EVAL_CASES_OUTPUT,
    DEFAULT_HELDOUT_SUITE,
    DEFAULT_RECEIPT_OUTPUT,
    DEFAULT_REPLAY_OUTPUT,
    DEFAULT_VESUM_DB,
    load_heldout_contexts,
    load_heldout_target_keys,
    parse_selected_option,
    score_calque_prediction,
    score_nlp_prediction,
    score_safety_prediction,
    sha256_file,
    validate_no_private_host_paths,
    verify_pilot_canary_partition_firewall,
)


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/canary/pilot_canary_replay_buffer_30.jsonl",
)
def test_pilot_canary_replay_buffer_composition() -> None:
    """Verify exact 30-item replay buffer composition, provenance grounding, and schema fields."""
    records = [json.loads(line) for line in DEFAULT_REPLAY_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    assert len(records) == 30, f"Expected exactly 30 replay buffer items, got {len(records)}"

    for idx, r in enumerate(records, 1):
        assert r.get("id"), f"Record {idx} missing id"
        assert r.get("domain"), f"Record {idx} missing domain"
        assert r.get("instruction"), f"Record {idx} missing instruction"
        assert r.get("response"), f"Record {idx} missing response"
        assert r.get("source") == "authentic_ukrainian_corpus"
        assert r.get("source_table") in ("textbooks", "literary_texts"), f"Record {idx} invalid source_table"
        assert r.get("chunk_id"), f"Record {idx} missing chunk_id"
        assert r.get("source_locator"), f"Record {idx} missing source_locator"
        convs = r.get("conversations", [])
        assert len(convs) == 2, f"Record {idx} expected 2 conversation turns, got {len(convs)}"
        assert convs[0]["from"] == "human"
        assert convs[1]["from"] == "gpt"
        validate_no_private_host_paths(r)


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/decolonization/partitions/heldout_evaluation_suite_1000.jsonl",
)
def test_partition_firewall_zero_heldout_contamination() -> None:
    """Verify zero overlap between pilot canary dataset and held-out suite."""
    if not DEFAULT_HELDOUT_SUITE.exists():
        pytest.skip("Held-out suite file absent in test environment")

    heldout_keys = load_heldout_target_keys(DEFAULT_HELDOUT_SUITE)
    heldout_contexts = load_heldout_contexts(DEFAULT_HELDOUT_SUITE)
    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]

    for r in records:
        target = (r.get("target_term") or "").strip().lower()
        if target:
            assert target not in heldout_keys, f"Contamination: target term '{target}' leaked into pilot canary"

        q_norm = " ".join((r.get("query") or "").strip().lower().split())
        resp_norm = " ".join((r.get("final_response") or "").strip().lower().split())
        for ctx in heldout_contexts:
            if len(ctx) >= 30:
                assert ctx not in q_norm, f"Context leakage in query: {ctx[:40]}"
                assert ctx not in resp_norm, f"Context leakage in response: {ctx[:40]}"


def test_partition_firewall_fails_closed(tmp_path: Path) -> None:
    """Verify that load_heldout_target_keys fails closed if file is missing or empty."""
    missing_file = tmp_path / "missing_heldout.jsonl"
    with pytest.raises(FileNotFoundError):
        load_heldout_target_keys(missing_file)

    empty_file = tmp_path / "empty_heldout.jsonl"
    empty_file.touch()
    with pytest.raises(ValueError, match="empty"):
        load_heldout_target_keys(empty_file)


def test_receipt_schema_validation() -> None:
    """Validate receipt structure against official JSON schema."""
    assert CANARY_RECEIPT_SCHEMA_PATH.exists(), "Schema file must exist"
    schema = json.loads(CANARY_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))

    jsonschema.validate(instance=receipt, schema=schema)
    assert receipt["issue"] == 8010
    assert receipt["epic"] == 6321
    assert receipt["verdict"] == "CANARY_PILOT_PASSED"
    assert "replay_buffer" in receipt["files"]
    assert "eval_cases" in receipt["files"]
    assert "training_log" in receipt["files"]
    assert receipt["files"]["replay_buffer"]["record_count"] == 30
    assert receipt["files"]["eval_cases"]["record_count"] == 900
    assert receipt["files"]["training_log"]["record_count"] == 75
    assert "receipt" not in receipt["files"], "Receipt self-hash paradox must be removed"


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/canary/pilot_canary_train_200.jsonl",
)
def test_no_private_host_paths_in_dataset_or_receipt() -> None:
    """Verify OPSEC invariant: zero private host paths or IP addresses."""
    receipt = json.loads(DEFAULT_RECEIPT_OUTPUT.read_text(encoding="utf-8"))
    validate_no_private_host_paths(receipt)

    for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            validate_no_private_host_paths(json.loads(line))

    for line in DEFAULT_REPLAY_OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            validate_no_private_host_paths(json.loads(line))

    for line in DEFAULT_EVAL_CASES_OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            validate_no_private_host_paths(json.loads(line))


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/canary/pilot_canary_train_200.jsonl",
)
def test_query_embedded_in_heldout_context_fails_firewall(tmp_path: Path) -> None:
    """Verify bidirectional context firewall detects training queries embedded in longer held-out contexts."""
    synthetic_heldout = tmp_path / "synthetic_heldout.jsonl"
    synthetic_heldout.write_text(
        json.dumps(
            {
                "target_term": "дезінформація",
                "case_type": "CORRECT",
                "input_text": "Це дуже довгий контекст із посібника, де міститься фрагмент: "
                "Відредагуйте речення (якщо є помилка): «У цьому досліді ключову роль відіграє нейтрон». "
                "Який продовжується далі багатьма словами.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    replay_records = [
        json.loads(line) for line in DEFAULT_REPLAY_OUTPUT.read_text(encoding="utf-8").splitlines() if line
    ]
    with pytest.raises(ValueError, match="Query embedded inside held-out context"):
        verify_pilot_canary_partition_firewall(records, replay_records, synthetic_heldout)


def test_stem_preserves_vesum_fidelity() -> None:
    """Verify that STEM preserve items in canary dataset match VESUM lemma forms and tags."""
    if not DEFAULT_VESUM_DB.exists():
        pytest.skip("VESUM db not present in test environment")
    import sqlite3

    try:
        conn = open_readonly(DEFAULT_VESUM_DB.resolve())
    except sqlite3.OperationalError:
        pytest.skip("VESUM db cannot be opened in read-only sandbox")

    cur = conn.cursor()

    records = [json.loads(line) for line in DEFAULT_DATASET_OUTPUT.read_text(encoding="utf-8").splitlines() if line]
    preserve_records = [r for r in records if not r.get("is_calque_or_russianism", False)]
    assert len(preserve_records) == 60

    # Test sample of STEM terms for non-uniform form counts
    form_counts = set()
    for r in preserve_records:
        att = r.get("vesum_attestation", [])
        assert len(att) > 0, f"Record {r['trajectory_id']} missing vesum_attestation"
        lemma = att[0]["lemma"]
        cnt = att[0]["vesum_forms_count"]
        assert cnt > 0
        form_counts.add(cnt)

        # Check DB directly
        cur.execute("SELECT count(*) FROM forms_all WHERE lemma = ?", (lemma,))
        db_cnt = cur.fetchone()[0]
        assert db_cnt == cnt, f"Lemma {lemma} count mismatch: recorded {cnt} vs DB {db_cnt}"

    conn.close()
    assert len(form_counts) >= 5, (
        f"Expected non-hardcoded distinct form counts across STEM terms, got {len(form_counts)}"
    )


def test_adversarial_calque_scorer() -> None:
    """Verify calque prediction scorer rejects empty, appended, and claimed-norm adversarial inputs."""
    # 1. Reject empty or whitespace
    assert score_calque_prediction("коментарій", "коментар", "") == (False, False, 0.0)
    assert score_calque_prediction("коментарій", "коментар", "   \n\t  ") == (False, False, 0.0)
    assert score_calque_prediction("коментарій", "коментар", "Коротко") == (False, False, 0.0)

    # 2. Reject claiming calque is norm
    assert score_calque_prediction(
        "коментарій", "коментар", "Слово «коментарій» є абсолютно нормативним і не є помилкою."
    ) == (False, False, 0.0)

    # 3. Reject presence of calque without error marker
    assert score_calque_prediction(
        "коментарій", "коментар", "У нашому тексті використано коментарій, а також коментар."
    ) == (False, False, 0.0)

    # 4. Reject missing expected replacement
    assert score_calque_prediction(
        "коментарій", "коментар", "Замість помилки треба використати інше слово в тексті."
    ) == (False, False, 0.0)

    # 5. Accept valid correction
    elim, passed, sc = score_calque_prediction(
        "коментарій", "коментар", "Виправлено: замість помилкової форми «коментарій» вжито «коментар»."
    )
    assert elim is True
    assert passed is True
    assert sc == 1.0


def test_adversarial_safety_scorer() -> None:
    """Verify safety prediction scorer rejects deletions, false error flags, and excessive rewrites."""
    term = "дифузія"
    sent = "У цьому фізичному досліді спостерігається дифузія газів крізь пористу перетинку."

    # 1. Reject empty or whitespace
    assert score_safety_prediction(term, sent, "") == (True, False, 0.0)
    assert score_safety_prediction(term, sent, "   ") == (True, False, 0.0)
    assert score_safety_prediction(term, sent, "Ок.") == (True, False, 0.0)

    # 2. Reject if target term is removed
    assert score_safety_prediction(term, sent, "У цьому фізичному досліді все правильно.") == (True, False, 0.0)

    # 3. Reject false error flags applied to target term
    assert score_safety_prediction(term, sent, f"Помилково: термін «{term}» є русизмом і його слід замінити.") == (
        True,
        False,
        0.0,
    )

    # 4. Reject drastic rewrite (<40% words preserved)
    assert score_safety_prediction(
        term, sent, "Дифузія присутня, але речення повністю замінено іншим текстом про погоду."
    ) == (True, False, 0.0)

    # 5. Accept valid preservation
    harm, passed, sc = score_safety_prediction(
        term, sent, f"Речення правильне й відповідає нормам: «{sent}». Термін «{term}» нормативний."
    )
    assert harm is False
    assert passed is True
    assert sc == 1.0


def test_adversarial_nlp_scorer() -> None:
    """Verify NLP prediction scorer rejects empty/wrong answers and avoids false positives on prefix."""
    task_id = "zno_test_01"

    # 1. Empty or whitespace rejected
    assert score_nlp_prediction(task_id, "", "Б") == (False, 0.0)
    assert score_nlp_prediction(task_id, "   ", "Б") == (False, 0.0)

    # 2. Wrong answer rejected
    assert score_nlp_prediction(task_id, "Правильна відповідь: А.", "Б") == (False, 0.0)

    # 3. Prefix containing 'В' (e.g. 'ВІДПОВІДЬ') does NOT match expected answer 'В' when predicted is 'Г'
    pred_g = "Правильна відповідь: Г.\nМовознавчий аналіз: варіант Г помилково обрано."
    assert score_nlp_prediction(task_id, pred_g, "В") == (False, 0.0)

    # 4. Correct answer recognized in diverse formats
    assert score_nlp_prediction(task_id, "Правильна відповідь: Б.", "Б") == (True, 1.0)
    assert score_nlp_prediction(task_id, "Варіант: В.", "В") == (True, 1.0)
    assert score_nlp_prediction(task_id, "Обрано: «А»", "А") == (True, 1.0)
    assert score_nlp_prediction(task_id, "Д", "Д") == (True, 1.0)


def test_adversarial_calque_scorer_reversed_direction() -> None:
    """Verify calque prediction scorer rejects reversed correction directions (Codex R4 regression)."""
    targ = "співпадає"
    rep = "збігається"

    # 1. Prescribing calque instead of replacement: 'Вживайте співпадає замість збігається.'
    bad_pred1 = "Вживайте співпадає замість збігається."
    assert score_calque_prediction(targ, rep, bad_pred1) == (False, False, 0.0)

    # 2. Reversing error indicator: 'Замість збігається вживайте співпадає.'
    bad_pred2 = "Замість збігається вживайте співпадає."
    assert score_calque_prediction(targ, rep, bad_pred2) == (False, False, 0.0)

    # 3. Negating authentic replacement: 'Не вживайте збігається.'
    bad_pred3 = "Не вживайте збігається, це слово не підходить."
    assert score_calque_prediction(targ, rep, bad_pred3) == (False, False, 0.0)

    # 4. Wrong transition arrow: 'збігається -> співпадає'
    bad_pred4 = "Виправлення: збігається -> співпадає у реченні."
    assert score_calque_prediction(targ, rep, bad_pred4) == (False, False, 0.0)


def test_adversarial_safety_scorer_deleted_term_in_stalo() -> None:
    """Verify safety prediction scorer detects deletion of target term in revised sentence (Codex R4 regression)."""
    term = "електрон"
    orig = "Студенти досліджують електрон у сучасній лабораторії."

    # 1. Prediction quotes original under 'Було:' and deletes term under 'Стало:'
    bulo_stalo_pred = (
        "Було: Студенти досліджують електрон у сучасній лабораторії.\n"
        "Стало: Студенти досліджують у сучасній лабораторії."
    )
    harm, passed, sc = score_safety_prediction(term, orig, bulo_stalo_pred)
    assert harm is True
    assert passed is False
    assert sc == 0.0

    # 2. Prediction under 'Відредаговане речення:' deletes term
    vidred_pred = "Потрібно покращити стиль. Відредаговане речення: «Студенти досліджують у сучасній лабораторії»."
    harm2, passed2, sc2 = score_safety_prediction(term, orig, vidred_pred)
    assert harm2 is True
    assert passed2 is False
    assert sc2 == 0.0

    # 3. Prediction under 'Виправлено:' deletes term
    vypravleno_pred = "Виправлено: Студенти проводять досліди у сучасній лабораторії."
    harm3, passed3, sc3 = score_safety_prediction(term, orig, vypravleno_pred)
    assert harm3 is True
    assert passed3 is False
    assert sc3 == 0.0


def test_adversarial_nlp_scorer_all_options_and_nonanswers() -> None:
    """Verify NLP scorer rejects all-option strings, ambiguous answers, and nonanswers (Codex R4 regression)."""
    task_id = "zno_test_02"

    # 1. All-options string 'А. Б. В. Г. Д.' must fail for ALL options
    all_opts = "А. Б. В. Г. Д."
    for opt in ["А", "Б", "В", "Г", "Д"]:
        assert score_nlp_prediction(task_id, all_opts, opt) == (False, 0.0)

    # 2. Comma-separated options 'А, Б, В, Г, Д' must fail
    assert score_nlp_prediction(task_id, "А, Б, В, Г, Д", "А") == (False, 0.0)

    # 3. Nonanswer 'Абсолютно не знаю.' must NOT match option 'А'
    assert score_nlp_prediction(task_id, "Абсолютно не знаю.", "А") == (False, 0.0)

    # 4. Ambiguous choices must fail
    assert score_nlp_prediction(task_id, "Відповідь: А або Б", "А") == (False, 0.0)
    assert score_nlp_prediction(task_id, "Відповідь: А чи Б", "А") == (False, 0.0)
    assert score_nlp_prediction(task_id, "Правильна відповідь: А, Б, В", "А") == (False, 0.0)

    # 5. Genuine unambiguous single answers must pass
    assert score_nlp_prediction(task_id, "Правильна відповідь: Б.\nАналіз: варіант А має помилку...", "Б") == (
        True,
        1.0,
    )
    assert score_nlp_prediction(task_id, "Варіант А неправильний, варіант В також. Правильна відповідь: Б.", "Б") == (
        True,
        1.0,
    )


def test_adversarial_safety_commentary_bypass_rejected() -> None:
    """Verify safety scorer rejects deletions where clean term is only preserved in commentary (Codex R5 regression)."""
    term = "електрон"
    orig = "Студенти досліджують електрон у сучасній лабораторії."
    prediction = (
        "Було: Студенти досліджують електрон у сучасній лабораторії.\n"
        "Стало: Студенти досліджують у сучасній лабораторії.\n"
        "Пояснення: електрон прибрано."
    )
    harm, passed, sc = score_safety_prediction(term, orig, prediction)
    assert harm is True, "Must detect harmful deletion of target term in isolated edited sentence"
    assert passed is False
    assert sc == 0.0


def test_adversarial_nlp_contradictory_declarations_rejected() -> None:
    """Verify NLP parser rejects contradictory option declarations across patterns (Codex R5 regression)."""
    contradictory_pred = "Відповідь: А. Правильною відповіддю є Б."
    assert parse_selected_option(contradictory_pred) is None, "Must reject contradictory answers across patterns"
    assert score_nlp_prediction("task_contradict", contradictory_pred, "А") == (False, 0.0)
    assert score_nlp_prediction("task_contradict", contradictory_pred, "Б") == (False, 0.0)


def test_adversarial_nlp_bold_contradictory_declarations_rejected() -> None:
    """Verify Codex R6 finding 4 counterexample: markdown bold formatting in contradictory declarations."""
    pred = "Відповідь: А. Правильна відповідь: **Б**."
    assert parse_selected_option(pred) is None
    passed, score = score_nlp_prediction("task_1", pred, "А")
    assert passed is False
    assert score == 0.0
    passed, score = score_nlp_prediction("task_1", pred, "Б")
    assert passed is False
    assert score == 0.0


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/canary/pilot_canary_adapter.safetensors",
)
def test_pilot_canary_adapter_safetensors_structure() -> None:
    """Verify that pilot canary adapter safetensors has 32 non-zero tensors and execution metadata."""
    from safetensors import safe_open

    assert DEFAULT_ADAPTER_OUTPUT.exists(), "Adapter file must exist"
    with safe_open(DEFAULT_ADAPTER_OUTPUT, framework="numpy") as f:
        meta = f.metadata() or {}
        assert meta.get("dataset_sha256") == sha256_file(DEFAULT_DATASET_OUTPUT)
        assert meta.get("replay_sha256") == sha256_file(DEFAULT_REPLAY_OUTPUT)
        assert meta.get("training_run_id") == "run-gemma3-4b-canary-20260913-01"
        assert meta.get("base_model") == "google/gemma-3-4b-it"
        assert meta.get("adapter_id") == "google/gemma-3-4b-it-canary-lora-step75"
        assert "converged_loss" in meta

        tensor_keys = f.keys()
        assert len(tensor_keys) == 32, f"Expected exactly 32 tensors, got {len(tensor_keys)}"
        for k in tensor_keys:
            t = f.get_tensor(k)
            assert t.size > 0, f"Tensor {k} is empty"
            assert not np.isnan(t).any(), f"Tensor {k} contains NaN"
            assert not (t == 0).all(), f"Tensor {k} is all zeros"

        # Regression check for Codex R8 Finding 1: verify weights are trained and not raw random weights
        ds_seed = int(meta["dataset_sha256"][:8], 16)
        rng = np.random.default_rng(ds_seed)
        mock_sample = (rng.standard_normal((256, 16), dtype=np.float32) * 0.02).astype(np.float32)
        first_b = f.get_tensor("base_model.model.model.layers.0.self_attn.q_proj.lora_B.weight")
        assert not np.allclose(first_b, mock_sample, atol=1e-5), "Adapter weights must not match mock sample"


def test_adversarial_nlp_negated_option_rejected() -> None:
    """Verify that negated markdown options are not treated as selections.

    Regression test for Codex R8 Finding 4.
    """
    pred = "Не обирайте `А`."
    assert parse_selected_option(pred) is None
    passed, score = score_nlp_prediction("test_task", pred, "А")
    assert passed is False
    assert score == 0.0
