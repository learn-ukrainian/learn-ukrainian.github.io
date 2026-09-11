"""Unit tests for ULDR consumer formatting and evaluation harness (#7926)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.projects.open_model_data.v4_evaluate_decolonization import (
    evaluate_predictions,
    evaluate_single_response,
)
from scripts.projects.open_model_data.v4_format_decolonization import (
    dpo_pair_to_trl,
    format_consumer_datasets,
    trajectory_to_chatml,
    trajectory_to_sharegpt,
)


def test_trajectory_to_sharegpt() -> None:
    sample_traj = {
        "trajectory_id": "traj.decolonize.avtovyshka",
        "target_term": "автовишка",
        "query": "Як правильно сказати «автовишка»?",
        "reasoning_steps": [
            "Аналіз морфемної будови: -вишка є росіянізмом.",
            "Питомий відповідник: автовежа.",
        ],
        "final_response": "Правильно вживати «автовежа».",
    }

    sg = trajectory_to_sharegpt(sample_traj)
    assert sg["id"] == "traj.decolonize.avtovyshka"
    assert sg["target_term"] == "автовишка"
    assert len(sg["conversations"]) == 3
    assert "messages" not in sg

    sys_msg, human_msg, gpt_msg = sg["conversations"]
    assert sys_msg["from"] == "system"
    assert "деколонізації" in sys_msg["value"]
    assert human_msg["from"] == "human"
    assert human_msg["value"] == sample_traj["query"]
    assert gpt_msg["from"] == "gpt"
    assert "<thought>" in gpt_msg["value"]
    assert "Крок 1: Аналіз морфемної будови" in gpt_msg["value"]
    assert "Крок 2: Питомий відповідник" in gpt_msg["value"]
    assert "</thought>" in gpt_msg["value"]
    assert "Правильно вживати «автовежа»." in gpt_msg["value"]


def test_trajectory_to_chatml() -> None:
    sample_traj = {
        "trajectory_id": "traj.decolonize.avtovyshka",
        "target_term": "автовишка",
        "query": "Як правильно сказати «автовишка»?",
        "reasoning_steps": [
            "Аналіз морфемної будови: -вишка є росіянізмом.",
            "Питомий відповідник: автовежа.",
        ],
        "final_response": "Правильно вживати «автовежа».",
    }

    cml = trajectory_to_chatml(sample_traj)
    assert cml["id"] == "traj.decolonize.avtovyshka"
    assert cml["target_term"] == "автовишка"
    assert len(cml["messages"]) == 2
    assert "conversations" not in cml
    assert cml["messages"][0]["role"] == "user"
    assert "деколонізації" in cml["messages"][0]["content"]
    assert sample_traj["query"] in cml["messages"][0]["content"]
    assert cml["messages"][1]["role"] == "assistant"
    assert "<thought>" in cml["messages"][1]["content"]
    assert "</thought>" in cml["messages"][1]["content"]


def test_gemma3_and_gemma4_template_adaptation() -> None:
    sample_sg = {
        "id": "traj.decolonize.avtovyshka",
        "target_term": "автовишка",
        "conversations": [
            {"from": "system", "value": "Ти — помічник з мовної деколонізації."},
            {"from": "human", "value": "Як сказати «автовишка»?"},
            {"from": "gpt", "value": "<thought>\nКрок 1: Аналіз морфемної будови.\n</thought>\n\nВживайте «автовежа»."},
        ],
    }

    # 1. Verify TRL adaptation recipe maps to ChatML and eliminates collisions
    def convert_to_chatml(example: dict) -> dict:
        convs = example["conversations"]
        sys_val = next((c["value"] for c in convs if c["from"] == "system"), "")
        human_val = next((c["value"] for c in convs if c["from"] == "human"), "")
        gpt_val = next((c["value"] for c in convs if c["from"] == "gpt"), "")
        user_text = f"{sys_val}\n\n{human_val}" if sys_val else human_val
        return {
            "messages": [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": gpt_val},
            ]
        }

    cml_rec = convert_to_chatml(sample_sg)
    assert "messages" in cml_rec
    assert len(cml_rec["messages"]) == 2
    assert cml_rec["messages"][0]["role"] == "user"
    assert cml_rec["messages"][1]["role"] == "assistant"

    # 2. Verify Gemma 3 format structure (<start_of_turn> / <end_of_turn>)
    user_msg = cml_rec["messages"][0]["content"]
    asst_msg = cml_rec["messages"][1]["content"]
    gemma3_rendered = (
        f"<start_of_turn>user\n{user_msg}<end_of_turn>\n"
        f"<start_of_turn>model\n{asst_msg}<end_of_turn>"
    )
    assert "<start_of_turn>user" in gemma3_rendered
    assert "<end_of_turn>" in gemma3_rendered
    assert "<start_of_turn>model" in gemma3_rendered
    assert "<thought>" in gemma3_rendered

    # 3. Verify Gemma 4 native turn & channel structure (<|turn> / <turn|>, <|channel>thought)
    thought_match = re.search(r"<thought>(.*?)</thought>", asst_msg, re.DOTALL)
    assert thought_match is not None
    thought_body = thought_match.group(1).strip()
    final_reply = re.sub(r"<thought>.*?</thought>\s*", "", asst_msg, flags=re.DOTALL).strip()

    gemma4_rendered = (
        f"<|turn>user\n{user_msg}<turn|>\n"
        f"<|turn>model\n"
        f"<|channel>thought\n{thought_body}\n<channel|>\n"
        f"{final_reply}<turn|>"
    )
    assert "<|turn>user" in gemma4_rendered
    assert "<turn|>" in gemma4_rendered
    assert "<|turn>model" in gemma4_rendered
    assert "<|channel>thought" in gemma4_rendered
    assert "<channel|>" in gemma4_rendered
    assert "Вживайте «автовежа»." in gemma4_rendered


def test_dpo_pair_to_trl() -> None:
    # Real schema: metadata does NOT contain calque_category
    sample_dpo = {
        "pair_id": "dpo.decolonize.avtovyshka",
        "prompt": "Чи правильне слово «автовишка»?",
        "chosen": "Ні, правильний термін — «автовежа».",
        "rejected": "Так, «автовишка» цілком нормативне слово.",
        "metadata": {
            "target_term": "автовишка",
            "rejected_flaw": "affirmation_of_calque",
            "primary_alternative": "автовежа",
            "vesum_verified": True,
        },
    }

    trl = dpo_pair_to_trl(sample_dpo)
    assert trl["id"] == "dpo.decolonize.avtovyshka"
    assert trl["target_term"] == "автовишка"
    assert trl["calque_category"] == "lexical_calque"
    assert sample_dpo["prompt"] in trl["prompt"]
    assert "деколонізації" in trl["prompt"]
    assert trl["chosen"] == sample_dpo["chosen"]
    assert trl["rejected"] == sample_dpo["rejected"]
    assert "деколонізації" in trl["system"]

    # Test active participle dynamic classification
    participle_dpo = {
        "pair_id": "dpo.decolonize.bazhayuchyj",
        "prompt": "Чи можна казати бажаючий?",
        "chosen": "Вживайте охочий.",
        "rejected": "Бажаючий це норма.",
        "metadata": {"target_term": "бажаючий"},
    }
    trl_part = dpo_pair_to_trl(participle_dpo)
    assert trl_part["calque_category"] == "active_participle"


def test_evaluate_single_response() -> None:
    target = "пилосос"
    alts = ["пилосмок", "порохотяг"]

    # 1. Ideal decolonized response: eliminates calque, provides authentic alternative, gives reasoning
    good_resp = (
        "Слово «пилосос» є російською калькою. "
        "В українській мові пил не «смокчуть», а втягують. "
        "Тому нормативними відповідниками є пилосмок або класичний порохотяг, "
        "підтверджені словником ВЕСУМ та чинними підручниками МОН."
    )
    res_good = evaluate_single_response(target, alts, good_resp)
    assert res_good["calque_eliminated"] is True
    assert res_good["authentic_suggested"] is True
    assert res_good["reasoning_grounded"] is True
    assert res_good["composite_score"] >= 0.80
    assert res_good["is_pass"] is True

    # 2. Defending the calque: affirms the calque as correct
    bad_resp = "Правильно вживати «пилосос». Слово пилосос є нормативним в українській мові."
    res_bad = evaluate_single_response(target, alts, bad_resp)
    assert res_bad["calque_eliminated"] is False
    assert res_bad["authentic_suggested"] is False
    assert res_bad["is_pass"] is False
    assert res_bad["composite_score"] == 0.0

    # 3. Minimal fragment without reasoning (< 35 chars) does not pass
    minimal_resp = "Вживайте пилосмок."
    res_min = evaluate_single_response(target, alts, minimal_resp)
    assert res_min["calque_eliminated"] is True
    assert res_min["authentic_suggested"] is True
    assert res_min["reasoning_grounded"] is False
    assert res_min["composite_score"] <= 0.40
    assert res_min["is_pass"] is False


def test_adversarial_contradictory_response_rejected() -> None:
    """F3: verify contradictory responses that praise calque and reject alternative fail."""
    target = "badtoken"
    alts = ["goodtoken"]

    # Probe from audit F3
    contradictory_resp = "badtoken — це правильний вибір. Не вживайте goodtoken. Тут немає помилки. Суфікс. Словник."
    res = evaluate_single_response(target, alts, contradictory_resp)
    assert res["composite_score"] == 0.0
    assert res["is_pass"] is False
    assert res["calque_eliminated"] is False
    assert res["authentic_suggested"] is False
    assert res["reasoning_grounded"] is False

    # Empty string
    res_empty = evaluate_single_response(target, alts, "")
    assert res_empty["composite_score"] == 0.0
    assert res_empty["is_pass"] is False

    # Keyword spam only
    res_spam = evaluate_single_response(target, alts, "goodtoken суфікс словник")
    assert res_spam["is_pass"] is False
    assert res_spam["composite_score"] <= 0.40


def test_evaluator_denominator_and_reconciliation(tmp_path: Path) -> None:
    """F4: verify exact gold denominator reconciliation, duplicate rejection, and missing penalization."""
    gold_path = tmp_path / "gold.jsonl"
    preds_path = tmp_path / "preds.jsonl"

    g1 = {
        "trajectory_id": "traj.1",
        "target_term": "калька1",
        "register_spectrum": {"alternatives": [{"lemma": "норма1"}]},
        "final_response": "Калька1 є росіянізмом. Вживайте норма1 за словником ВЕСУМ.",
    }
    g2 = {
        "trajectory_id": "traj.2",
        "target_term": "калька2",
        "register_spectrum": {"alternatives": [{"lemma": "норма2"}]},
        "final_response": "Калька2 є росіянізмом. Вживайте норма2 за словником ВЕСУМ.",
    }
    gold_path.write_text(json.dumps(g1) + "\n" + json.dumps(g2) + "\n", encoding="utf-8")

    # Supply 1 valid prediction, 1 duplicate prediction of g1, and 1 unknown prediction (g2 missing)
    p1 = {
        "id": "traj.1",
        "target_term": "калька1",
        "response": "Слово калька1 — росіянізм. Правильно норма1 за підручником та ВЕСУМ.",
    }
    p1_dup = {
        "id": "traj.1",
        "target_term": "калька1",
        "response": "Дублікат",
    }
    p_unk = {
        "id": "traj.unknown",
        "target_term": "невідомий",
        "response": "Невідомо",
    }
    preds_path.write_text(
        json.dumps(p1) + "\n" + json.dumps(p1_dup) + "\n" + json.dumps(p_unk) + "\n",
        encoding="utf-8",
    )

    summary = evaluate_predictions(gold_path, preds_path)
    assert summary["expected_gold_records"] == 2
    assert summary["total_evaluated"] == 1
    assert summary["missing_records_count"] == 1
    assert summary["duplicate_predictions_count"] == 1
    assert summary["unknown_predictions_count"] == 1
    assert summary["pass_rate"] == 0.50  # 1 pass out of 2 expected gold items


def test_format_and_evaluate_end_to_end(tmp_path: Path) -> None:
    in_dir = tmp_path / "generated"
    in_dir.mkdir(parents=True)
    out_dir = tmp_path / "consumer"

    # Create mock manifest and shards with disjoint targets and IDs
    traj_held_out = in_dir / "mock_traj_held_out.jsonl"
    dpo_held_out = in_dir / "mock_dpo_held_out.jsonl"
    traj_train = in_dir / "mock_traj_train.jsonl"
    dpo_train = in_dir / "mock_dpo_train.jsonl"

    record_held_out = {
        "trajectory_id": "traj.decolonize.kholostyak",
        "target_term": "холостяк",
        "query": "Як правильно замінити слово «холостяк»?",
        "reasoning_steps": ["Слово «холостяк» є росіянізмом.", "Питоме слово — неодружений або парубок."],
        "final_response": "Слово «холостяк» є калькою. В українській мові вживають парубок або неодружений.",
        "register_spectrum": {"alternatives": [{"lemma": "парубок"}, {"lemma": "неодружений"}]},
    }
    traj_held_out.write_text(json.dumps(record_held_out, ensure_ascii=False) + "\n", encoding="utf-8")

    dpo_held_out_rec = {
        "pair_id": "dpo.decolonize.kholostyak",
        "prompt": "Як замінити слово холостяк?",
        "chosen": "Вживайте парубок.",
        "rejected": "Холостяк це норма.",
        "metadata": {
            "target_term": "холостяк",
            "rejected_flaw": "affirmation_of_calque",
            "primary_alternative": "парубок",
            "vesum_verified": True,
        },
    }
    dpo_held_out.write_text(json.dumps(dpo_held_out_rec, ensure_ascii=False) + "\n", encoding="utf-8")

    record_train = {
        "trajectory_id": "traj.decolonize.perekluchyty",
        "target_term": "переключити",
        "query": "Як сказати переключити?",
        "reasoning_steps": ["Калька від рос. переключить.", "Питоме: перемкнути."],
        "final_response": "Вживайте «перемкнути».",
        "register_spectrum": {"alternatives": [{"lemma": "перемкнути"}]},
    }
    traj_train.write_text(json.dumps(record_train, ensure_ascii=False) + "\n", encoding="utf-8")

    dpo_train_rec = {
        "pair_id": "dpo.decolonize.perekluchyty",
        "prompt": "Як сказати переключити?",
        "chosen": "Вживайте перемкнути.",
        "rejected": "Переключити це норма.",
        "metadata": {
            "target_term": "переключити",
            "rejected_flaw": "affirmation_of_calque",
            "primary_alternative": "перемкнути",
            "vesum_verified": True,
        },
    }
    dpo_train.write_text(json.dumps(dpo_train_rec, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "dataset_name": "ULDR Mock",
        "shards": [
            {
                "partition": "train",
                "trajectories_file": traj_train.name,
                "dpo_pairs_file": dpo_train.name,
            },
            {
                "partition": "held_out",
                "trajectories_file": traj_held_out.name,
                "dpo_pairs_file": dpo_held_out.name,
            },
        ],
    }
    (in_dir / "decolonization_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    # Run format_consumer_datasets
    stats = format_consumer_datasets(in_dir, out_dir, records_per_shard=10)
    assert stats["sharegpt_train_count"] == 1
    assert stats["sharegpt_held_out_count"] == 1
    assert stats["trl_dpo_train_count"] == 1
    assert stats["trl_dpo_held_out_count"] == 1
    assert stats["quality_metrics"]["zero_private_paths"] is True
    assert stats["quality_metrics"]["zero_restricted_sources"] is True
    assert stats["partition_firewall"]["verified_disjoint_ids"] is True
    assert stats["partition_firewall"]["verified_disjoint_targets"] is True

    # Verify consumer_formats_manifest.json on disk
    manifest_on_disk = json.loads((out_dir / "consumer_formats_manifest.json").read_text(encoding="utf-8"))
    assert manifest_on_disk["quality_metrics"]["zero_private_paths"] is True
    assert manifest_on_disk["quality_metrics"]["zero_restricted_sources"] is True

    # Verify shipped DPO records have populated calque_category and embedded system prompt
    dpo_shards = list(out_dir.glob("uldr_dpo_*.jsonl"))
    assert len(dpo_shards) >= 1
    for dpo_s in dpo_shards:
        for line in dpo_s.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                assert rec["calque_category"] == "lexical_calque"
                assert "деколонізації" in rec["prompt"]

    # Verify ShareGPT has pure ShareGPT structure (conversations only, no conflicting messages column)
    sg_shards = list(out_dir.glob("uldr_sharegpt_*.jsonl"))
    assert len(sg_shards) >= 1
    for sg_s in sg_shards:
        for line in sg_s.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                assert "conversations" in rec
                assert "messages" not in rec
                assert len(rec["conversations"]) == 3
                assert "деколонізації" in rec["conversations"][0]["value"]

    # Run evaluate_predictions with a passing prediction
    preds_file = tmp_path / "preds.jsonl"
    preds_file.write_text(
        json.dumps(
            {
                "id": "traj.decolonize.kholostyak",
                "target_term": "холостяк",
                "response": "Слово «холостяк» — це росіянізм і радянська калька. Правильно казати парубок за словником ВЕСУМ та підручником МОН.",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    eval_report = tmp_path / "report.json"
    eval_res = evaluate_predictions(traj_held_out, preds_file, eval_report)
    assert eval_res["expected_gold_records"] == 1
    assert eval_res["total_evaluated"] == 1
    assert eval_res["calque_elimination_rate"] == 1.0
    assert eval_res["authentic_suggestion_rate"] == 1.0
    assert eval_res["reasoning_grounding_rate"] == 1.0
    assert eval_res["pass_rate"] == 1.0
    assert eval_report.is_file()


def test_adversarial_non_answers_rejected() -> None:
    # R3: explicit refusal must score 0.0 and fail
    target = "badtoken"
    alts = ["goodtoken"]

    refusal = "Я відмовляюся оцінювати badtoken чи goodtoken. Слова «калька» та «суфікс» наведено лише для прикладу."
    res_refusal = evaluate_single_response(target, alts, refusal)
    assert res_refusal["is_pass"] is False
    assert res_refusal["composite_score"] == 0.0

    # R3: keyword spam with repeated tokens must fail (token repetition penalty)
    spam = "goodtoken суфікс словник суфікс словник суфікс словник"
    res_spam = evaluate_single_response(target, alts, spam)
    assert res_spam["is_pass"] is False
    assert res_spam["composite_score"] <= 0.40

    # R3: legitimate affirmation of alternative (not target) must pass
    legit = "Слово badtoken є калькою. Рекомендуємо goodtoken, оскільки це питоме слово за словником ВЕСУМ. Це не є помилкою в сучасній літературній нормі."
    res_legit = evaluate_single_response(target, alts, legit)
    assert res_legit["is_pass"] is True
    assert res_legit["composite_score"] >= 0.8


def test_partition_firewall_rejects_dpo_target_leakage(tmp_path: Path) -> None:
    # R4: train SFT target 'a', train DPO target 'b', held-out SFT 'b' must fail closed
    import pytest

    in_dir = tmp_path / "leak_gen"
    in_dir.mkdir()
    out_dir = tmp_path / "leak_consumer"

    train_sft = in_dir / "train_sft.jsonl"
    train_dpo = in_dir / "train_dpo.jsonl"
    held_sft = in_dir / "held_sft.jsonl"
    held_dpo = in_dir / "held_dpo.jsonl"

    train_sft.write_text(json.dumps({"trajectory_id": "t1", "target_term": "term_a", "query": "q", "final_response": "r"}) + "\n")
    train_dpo.write_text(json.dumps({"pair_id": "d1", "prompt": "p", "chosen": "c", "rejected": "rej", "metadata": {"target_term": "term_b"}}) + "\n")
    held_sft.write_text(json.dumps({"trajectory_id": "t2", "target_term": "term_b", "query": "q", "final_response": "r"}) + "\n")
    held_dpo.write_text(json.dumps({"pair_id": "d2", "prompt": "p", "chosen": "c", "rejected": "rej", "metadata": {"target_term": "term_c"}}) + "\n")

    manifest = {
        "shards": [
            {"partition": "train", "trajectories_file": train_sft.name, "dpo_pairs_file": train_dpo.name},
            {"partition": "held_out", "trajectories_file": held_sft.name, "dpo_pairs_file": held_dpo.name},
        ]
    }
    (in_dir / "decolonization_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match=r"Partition firewall violation.*overlapping target terms"):
        format_consumer_datasets(in_dir, out_dir)


def test_evaluate_predictions_resolves_exact_id_over_prompt_substring(tmp_path: Path) -> None:
    # R5: prediction ID synthetic.otherbadtoken with prompt 'Compare badtoken with otherbadtoken'
    # must score against otherbadtoken, NOT badtoken
    gold_path = tmp_path / "gold.jsonl"
    g1 = {"trajectory_id": "synthetic.badtoken", "target_term": "badtoken", "register_spectrum": {"alternatives": [{"lemma": "good1"}]}}
    g2 = {"trajectory_id": "synthetic.otherbadtoken", "target_term": "otherbadtoken", "register_spectrum": {"alternatives": [{"lemma": "good2"}]}}
    gold_path.write_text(json.dumps(g1) + "\n" + json.dumps(g2) + "\n", encoding="utf-8")

    preds_path = tmp_path / "preds.jsonl"
    p = {
        "id": "synthetic.otherbadtoken",
        "prompt": "Compare badtoken with otherbadtoken",
        "response": "Слово otherbadtoken — це росіянізм. Вживайте good2, оскільки це норма за словником ВЕСУМ.",
    }
    preds_path.write_text(json.dumps(p) + "\n", encoding="utf-8")

    summary = evaluate_predictions(gold_path, preds_path)
    assert summary["expected_gold_records"] == 2
    assert summary["total_evaluated"] == 1
    assert summary["missing_records_count"] == 1
    eval_row = next(r for r in summary["evaluations"] if r["status"] == "evaluated")
    assert eval_row["id"] == "synthetic.otherbadtoken"
    assert eval_row["target_term"] == "otherbadtoken"


def test_atomic_staging_protects_existing_consumer_dir(tmp_path: Path) -> None:
    # R6: staging directory protects existing files if validation fails
    import pytest

    in_dir = tmp_path / "atomic_gen"
    in_dir.mkdir()
    out_dir = tmp_path / "atomic_consumer"
    out_dir.mkdir()
    sentinel = out_dir / "important_existing.jsonl"
    sentinel.write_text("existing content\n", encoding="utf-8")

    # Incomplete manifest (violates validation)
    (in_dir / "decolonization_manifest.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError):
        format_consumer_datasets(in_dir, out_dir)

    # Sentinel file must still exist untouched
    assert sentinel.is_file()
    assert sentinel.read_text(encoding="utf-8") == "existing content\n"
