"""Unit tests for ULDR consumer formatting and evaluation harness (#7926)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest

from scripts.projects.open_model_data.v4_evaluate_decolonization import (
    evaluate_predictions,
    evaluate_single_response,
)
from scripts.projects.open_model_data.v4_format_decolonization import (
    dpo_pair_to_trl,
    extract_target_term,
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
    gemma3_rendered = f"<start_of_turn>user\n{user_msg}<end_of_turn>\n<start_of_turn>model\n{asst_msg}<end_of_turn>"
    assert "<start_of_turn>user" in gemma3_rendered
    assert "<end_of_turn>" in gemma3_rendered
    assert "<start_of_turn>model" in gemma3_rendered
    assert "<thought>" in gemma3_rendered

    # 3. Verify Gemma 4 native turn & channel structure (<|turn> / <turn|>, <|channel>thought)
    import jinja2

    def convert_to_gemma4_native(example: dict) -> dict:
        convs = example["conversations"]
        sys_val = next((c["value"] for c in convs if c["from"] == "system"), "")
        human_val = next((c["value"] for c in convs if c["from"] == "human"), "")
        gpt_val = next((c["value"] for c in convs if c["from"] == "gpt"), "")

        thought_m = re.search(r"<thought>(.*?)</thought>", gpt_val, re.DOTALL)
        if thought_m:
            reasoning = thought_m.group(1).strip()
            final_text = re.sub(r"<thought>.*?</thought>\s*", "", gpt_val, flags=re.DOTALL).strip()
        else:
            reasoning = None
            final_text = gpt_val

        user_text = f"{sys_val}\n\n{human_val}" if sys_val else human_val
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": final_text}
        if reasoning:
            assistant_msg["reasoning"] = reasoning

        return {
            "messages": [
                {"role": "user", "content": user_text},
                assistant_msg,
            ]
        }

    gemma4_rec = convert_to_gemma4_native(sample_sg)
    assert "reasoning" in gemma4_rec["messages"][1]
    assert gemma4_rec["messages"][1]["reasoning"] == "Крок 1: Аналіз морфемної будови."
    assert "<thought>" not in gemma4_rec["messages"][1]["content"]

    # Official Gemma 4 Jinja template logic: thought channel emitted only when reasoning is populated
    # CodeQL-compliant Jinja instantiation with explicit autoescape=True and template-level raw control tags
    gemma4_jinja_template = (
        "{% autoescape false %}"
        "{% for message in messages %}"
        "{{ '<|turn>' + message['role'] + '\n' }}"
        "{% if message['reasoning'] is defined and message['reasoning'] is not none %}"
        "{{ '<|channel>thought\n' + message['reasoning'] + '\n<channel|>\n' }}"
        "{% endif %}"
        "{{ message['content'] + '<turn|>\n' }}"
        "{% endfor %}"
        "{% endautoescape %}"
    )
    template = jinja2.Template(gemma4_jinja_template, autoescape=True)
    jinja_rendered = template.render(messages=gemma4_rec["messages"])

    assert "<|turn>user\n" in jinja_rendered
    assert "<turn|>" in jinja_rendered
    assert "<|turn>assistant\n" in jinja_rendered
    assert "<|channel>thought\nКрок 1: Аналіз морфемної будови.\n<channel|>\n" in jinja_rendered
    assert "Вживайте «автовежа»." in jinja_rendered


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

    # G2: semantic non-answers with evasions or unrelated sentences mentioning token
    semantic_evasion = "Оцінки не буде. На дошці написано goodtoken. Учень читає словник, бо його цікавить суфікс."
    res_evasion = evaluate_single_response(target, alts, semantic_evasion)
    assert res_evasion["is_pass"] is False
    assert res_evasion["composite_score"] == 0.0

    semantic_non_answer = "На дошці написано goodtoken. Учень читає словник, бо його цікавить суфікс."
    res_non_answer = evaluate_single_response(target, alts, semantic_non_answer)
    assert res_non_answer["is_pass"] is False
    assert res_non_answer["composite_score"] == 0.0

    # G4: tokenless or punctuation-only input must not crash with ZeroDivisionError
    for tokenless in ("...", "!!! ???", "😊", "   ", "\n\t"):
        res_tokenless = evaluate_single_response(target, alts, tokenless)
        assert res_tokenless["is_pass"] is False
        assert res_tokenless["composite_score"] == 0.0


def test_partition_firewall_rejects_dpo_target_leakage(tmp_path: Path) -> None:
    # R4: train SFT target 'a', train DPO target 'b', held-out SFT 'b' must fail closed
    in_dir = tmp_path / "leak_gen"
    in_dir.mkdir()
    out_dir = tmp_path / "leak_consumer"

    train_sft = in_dir / "train_sft.jsonl"
    train_dpo = in_dir / "train_dpo.jsonl"
    held_sft = in_dir / "held_sft.jsonl"
    held_dpo = in_dir / "held_dpo.jsonl"

    train_sft.write_text(
        json.dumps({"trajectory_id": "t1", "target_term": "term_a", "query": "q", "final_response": "r"}) + "\n"
    )
    train_dpo.write_text(
        json.dumps(
            {"pair_id": "d1", "prompt": "p", "chosen": "c", "rejected": "rej", "metadata": {"target_term": "term_b"}}
        )
        + "\n"
    )
    held_sft.write_text(
        json.dumps({"trajectory_id": "t2", "target_term": "term_b", "query": "q", "final_response": "r"}) + "\n"
    )
    held_dpo.write_text(
        json.dumps(
            {"pair_id": "d2", "prompt": "p", "chosen": "c", "rejected": "rej", "metadata": {"target_term": "term_c"}}
        )
        + "\n"
    )

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
    g1 = {
        "trajectory_id": "synthetic.badtoken",
        "target_term": "badtoken",
        "register_spectrum": {"alternatives": [{"lemma": "good1"}]},
    }
    g2 = {
        "trajectory_id": "synthetic.otherbadtoken",
        "target_term": "otherbadtoken",
        "register_spectrum": {"alternatives": [{"lemma": "good2"}]},
    }
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


def test_extract_target_term_conflict_rejection() -> None:
    """G3: verify extract_target_term rejects conflicting top-level vs metadata representations."""
    # Consistent representations
    assert extract_target_term({"target_term": "Термін1"}) == "термін1"
    assert extract_target_term({"metadata": {"target_term": "Термін2"}}) == "термін2"
    assert extract_target_term({"target_term": "Термін3", "metadata": {"target_term": "термін3"}}) == "термін3"

    # Disagreeing representations
    conflict_rec = {
        "pair_id": "dpo.conflict.1",
        "target_term": "термін_а",
        "metadata": {"target_term": "термін_б"},
    }
    with pytest.raises(ValueError, match=r"Conflicting target term representations"):
        extract_target_term(conflict_rec)

    with pytest.raises(ValueError, match=r"Conflicting target term representations"):
        dpo_pair_to_trl(
            {
                "pair_id": "dpo.conflict.1",
                "prompt": "Питання",
                "chosen": "Правильно",
                "rejected": "Неправильно",
                "target_term": "термін_а",
                "metadata": {"target_term": "термін_б"},
            }
        )


def test_atomic_rollback_on_publication_failure(tmp_path: Path, monkeypatch: Any) -> None:
    """G5: publication failure must rollback and preserve existing files untouched."""
    in_dir = tmp_path / "gen"
    in_dir.mkdir()
    out_dir = tmp_path / "consumer"
    out_dir.mkdir()

    # Pre-existing published file
    existing_file = out_dir / "uldr_sharegpt_train_part001.jsonl"
    existing_file.write_text("old canonical content\n", encoding="utf-8")
    existing_manifest = out_dir / "consumer_formats_manifest.json"
    existing_manifest.write_text('{"old": true}\n', encoding="utf-8")

    # Valid input mock
    t_file = in_dir / "traj.jsonl"
    d_file = in_dir / "dpo.jsonl"
    t_file.write_text(
        json.dumps(
            {
                "trajectory_id": "t1",
                "target_term": "калька",
                "query": "q",
                "final_response": "r",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    d_file.write_text(
        json.dumps(
            {
                "pair_id": "d1",
                "prompt": "p",
                "chosen": "c",
                "rejected": "rej",
                "target_term": "калька",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = {
        "dataset_name": "ULDR",
        "total_trajectories": 1,
        "total_dpo_pairs": 1,
        "partition_counts": {"train": 1, "held_out": 0},
        "shards": [
            {
                "shard_index": 1,
                "partition": "train",
                "trajectories_file": t_file.name,
                "dpo_pairs_file": d_file.name,
                "records_count": 1,
            }
        ],
    }
    (in_dir / "decolonization_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    # Inject failure during moving files from staging into out_dir
    original_move = shutil.move

    def faulty_move(src: str, dst: str, *args: Any, **kwargs: Any) -> Any:
        # Allow moving old files to backup, fail on the first staged file move to out_dir
        if "staging" in str(src) and str(dst).startswith(str(out_dir)):
            raise OSError("Injected disk failure during publication move")
        return original_move(src, dst, *args, **kwargs)

    monkeypatch.setattr(shutil, "move", faulty_move)

    with pytest.raises(OSError, match=r"Injected disk failure"):
        format_consumer_datasets(in_dir, out_dir)

    # Verify existing files are preserved completely intact
    assert existing_file.is_file()
    assert existing_file.read_text(encoding="utf-8") == "old canonical content\n"
    assert existing_manifest.is_file()
    assert existing_manifest.read_text(encoding="utf-8") == '{"old": true}\n'

    # Verify no backup or staging directory leaks
    assert len(list(out_dir.glob(".backup_*"))) == 0
    assert len(list(out_dir.glob(".staging_*"))) == 0


def test_manifest_reconciliation_fail_closed(tmp_path: Path) -> None:
    """G6: manifest reconciliation must fail closed on unknown partitions, count mismatches, and asymmetries."""
    in_dir = tmp_path / "recon_gen"
    in_dir.mkdir()
    out_dir = tmp_path / "recon_consumer"

    t_file = in_dir / "traj.jsonl"
    d_file = in_dir / "dpo.jsonl"
    t_file.write_text(
        json.dumps({"trajectory_id": "t1", "target_term": "калька", "query": "q", "final_response": "r"}) + "\n",
        encoding="utf-8",
    )
    d_file.write_text(
        json.dumps({"pair_id": "d1", "prompt": "p", "chosen": "c", "rejected": "rej", "target_term": "калька"}) + "\n",
        encoding="utf-8",
    )

    # 1. Unknown partition
    manifest_unknown = {
        "dataset_name": "ULDR",
        "shards": [{"partition": "eval_unknown", "trajectories_file": t_file.name, "dpo_pairs_file": d_file.name}],
    }
    (in_dir / "decolonization_manifest.json").write_text(json.dumps(manifest_unknown), encoding="utf-8")
    with pytest.raises(ValueError, match=r"Unknown or unsupported partition 'eval_unknown'"):
        format_consumer_datasets(in_dir, out_dir)

    # 2. records_count mismatch
    manifest_records_count = {
        "dataset_name": "ULDR",
        "shards": [
            {
                "partition": "train",
                "trajectories_file": t_file.name,
                "dpo_pairs_file": d_file.name,
                "records_count": 99,
            }
        ],
    }
    (in_dir / "decolonization_manifest.json").write_text(json.dumps(manifest_records_count), encoding="utf-8")
    with pytest.raises(ValueError, match=r"Record count mismatch.*expected 99, got 1"):
        format_consumer_datasets(in_dir, out_dir)

    # 3. Partition count mismatch
    manifest_part_mismatch = {
        "dataset_name": "ULDR",
        "partition_counts": {"train": 50, "held_out": 0},
        "shards": [
            {
                "partition": "train",
                "trajectories_file": t_file.name,
                "dpo_pairs_file": d_file.name,
                "records_count": 1,
            }
        ],
    }
    (in_dir / "decolonization_manifest.json").write_text(json.dumps(manifest_part_mismatch), encoding="utf-8")
    with pytest.raises(ValueError, match=r"Partition 'train' count mismatch: declared 50, parsed 1"):
        format_consumer_datasets(in_dir, out_dir)

    # 4. Total count mismatch
    manifest_total_mismatch = {
        "dataset_name": "ULDR",
        "total_trajectories": 50,
        "shards": [
            {
                "partition": "train",
                "trajectories_file": t_file.name,
                "dpo_pairs_file": d_file.name,
                "records_count": 1,
            }
        ],
    }
    (in_dir / "decolonization_manifest.json").write_text(json.dumps(manifest_total_mismatch), encoding="utf-8")
    with pytest.raises(ValueError, match=r"Aggregate total_trajectories mismatch: manifest 50 != parsed 1"):
        format_consumer_datasets(in_dir, out_dir)


def test_descriptive_non_answer_scores_zero() -> None:
    """H1: A descriptive non-answer containing valid tokens but no prescription or grounded reasoning must score 0."""
    eval_res = evaluate_single_response(
        target_term="badtoken",
        valid_alternatives=["goodtoken"],
        response_text="Слово goodtoken записане на дошці. Учень читає словник, бо його цікавить суфікс.",
    )
    assert not eval_res["authentic_suggested"]
    assert not eval_res["reasoning_grounded"]
    assert eval_res["composite_score"] == 0.0


def test_backup_failure_preserves_original_dataset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """H2: Fault injection during backup creation must not delete original un-backed-up files."""
    in_dir = tmp_path / "inputs"
    out_dir = tmp_path / "outputs"
    in_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)

    orig_jsonl = out_dir / "uldr_sharegpt_train_part000.jsonl"
    orig_jsonl.write_text('{"id": "orig"}\n', encoding="utf-8")
    orig_manifest = out_dir / "consumer_formats_manifest.json"
    orig_manifest.write_text('{"status": "orig"}\n', encoding="utf-8")

    # Set up valid input manifest and shards
    t_shard = in_dir / "trajectories.jsonl"
    d_shard = in_dir / "dpos.jsonl"
    traj_data = {
        "trajectory_id": "traj.t1",
        "query": "Q",
        "reasoning_steps": ["S1"],
        "final_response": "R",
        "register_spectrum": {"primary_living_standard": "A"},
    }
    dpo_data = {"pair_id": "dpo.t1", "prompt": "P", "chosen": "C", "rejected": "R"}
    t_shard.write_text(json.dumps(traj_data) + "\n", encoding="utf-8")
    d_shard.write_text(json.dumps(dpo_data) + "\n", encoding="utf-8")

    manifest = {
        "dataset_name": "ULDR",
        "total_trajectories": 1,
        "total_dpo_pairs": 1,
        "shards": [
            {
                "partition": "train",
                "trajectories_file": t_shard.name,
                "dpo_pairs_file": d_shard.name,
                "records_count": 1,
            }
        ],
    }
    (in_dir / "decolonization_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    # Inject failure on first shutil.move during backup
    real_move = shutil.move

    def failing_move(src: Any, dst: Any, *args: Any, **kwargs: Any) -> Any:
        if ".backup_" in str(dst):
            raise OSError("Synthetic disk full or permission denied during backup creation")
        return real_move(src, dst, *args, **kwargs)

    monkeypatch.setattr(shutil, "move", failing_move)

    with pytest.raises(OSError, match="during backup creation"):
        format_consumer_datasets(in_dir, out_dir)

    # Originals must be preserved!
    assert orig_jsonl.is_file(), "Original jsonl was deleted during failed backup!"
    assert orig_jsonl.read_text(encoding="utf-8") == '{"id": "orig"}\n'
    assert orig_manifest.is_file(), "Original manifest was deleted during failed backup!"
    assert orig_manifest.read_text(encoding="utf-8") == '{"status": "orig"}\n'


def test_quoted_instruction_and_unrelated_reasoning_rejected() -> None:
    """I1: Quoted instructions and unrelated student reasoning must score 0.0 / FAIL."""
    target = "badtoken"
    alts = ["goodtoken"]

    # 1. Quoted instruction with citation disclaimer
    r1 = "На дошці написано «Вживайте goodtoken», бо учень переписав словник про суфікс. Це лише цитата з вправи."
    eval1 = evaluate_single_response(target, alts, r1)
    assert not eval1["is_pass"]
    assert eval1["composite_score"] == 0.0

    # 2. Recommendation coupled with unrelated narrative reasoning
    r2 = "Правильно вживати goodtoken. Учень читає словник, бо його цікавить суфікс."
    eval2 = evaluate_single_response(target, alts, r2)
    assert not eval2["is_pass"]
    assert not eval2["reasoning_grounded"]
    assert eval2["composite_score"] <= 0.40


def test_same_sentence_unrelated_reasoning_rejected() -> None:
    """J1: A recommendation with an unrelated reason in the same sentence must not score 100% / PASS."""
    target = "badtoken"
    alts = ["goodtoken"]

    # Probe from audit J1: speaker action narrative in the same sentence
    r = "Вживайте goodtoken, бо я прочитав словник і вивчив суфікс."
    eval_res = evaluate_single_response(target, alts, r)
    assert not eval_res["is_pass"]
    assert not eval_res["reasoning_grounded"]
    assert eval_res["composite_score"] <= 0.40


def test_explanation_concerning_other_word_rejected() -> None:
    """K2: An explanation concerning another word must fail grounding and not pass."""
    target = "badtoken"
    alts = ["goodtoken"]

    # Probe from audit K2: explanation explicitly concerns another word
    r = "Вживайте goodtoken, бо у словнику подано пояснення суфікса іншого слова."
    eval_res = evaluate_single_response(target, alts, r)
    assert not eval_res["is_pass"]
    assert not eval_res["reasoning_grounded"]
    assert eval_res["composite_score"] <= 0.40


def test_explanation_concerning_named_unrelated_word_rejected() -> None:
    """L2: An explanation concerning an explicitly named unrelated word must fail grounding and not pass."""
    target = "badtoken"
    alts = ["goodtoken"]

    # Probe from audit L2: explanation concerns explicitly named word «будинок»
    r1 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «будинок»."
    eval1 = evaluate_single_response(target, alts, r1)
    assert not eval1["is_pass"]
    assert not eval1["reasoning_grounded"]
    assert eval1["composite_score"] <= 0.40

    # Probe unquoted variant
    r2 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова будинок."
    eval2 = evaluate_single_response(target, alts, r2)
    assert not eval2["is_pass"]
    assert not eval2["reasoning_grounded"]
    assert eval2["composite_score"] <= 0.40


def test_explanation_concerning_grammatical_label_named_word_rejected() -> None:
    """M1: An explanation concerning an unrelated word preceded by a grammatical label must fail grounding."""
    target = "badtoken"
    alts = ["goodtoken"]

    # Probe from audit M1: grammatical label «іменника «будинок»»
    r1 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса іменника «будинок»."
    eval1 = evaluate_single_response(target, alts, r1)
    assert not eval1["is_pass"]
    assert not eval1["reasoning_grounded"]
    assert eval1["composite_score"] <= 0.40

    # Probe unquoted variant
    r2 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса іменника будинок."
    eval2 = evaluate_single_response(target, alts, r2)
    assert not eval2["is_pass"]
    assert not eval2["reasoning_grounded"]
    assert eval2["composite_score"] <= 0.40


def test_explanation_concerning_word_mova_rejected() -> None:
    """M1: An explanation concerning the word «мова» must not be exempted when «мова» is not the target."""
    target = "badtoken"
    alts = ["goodtoken"]

    # Probe from audit M1: generic word «мова»
    r1 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «мова»."
    eval1 = evaluate_single_response(target, alts, r1)
    assert not eval1["is_pass"]
    assert not eval1["reasoning_grounded"]
    assert eval1["composite_score"] <= 0.40

    # Probe unquoted variant
    r2 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова мова."
    eval2 = evaluate_single_response(target, alts, r2)
    assert not eval2["is_pass"]
    assert not eval2["reasoning_grounded"]
    assert eval2["composite_score"] <= 0.40


def test_explanation_concerning_word_spiv_rejected() -> None:
    """M1 Review: A named word matching an affix spelling (e.g. «спів») must not be exempted."""
    target = "badtoken"
    alts = ["goodtoken"]

    r1 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «спів»."
    eval1 = evaluate_single_response(target, alts, r1)
    assert not eval1["is_pass"]
    assert not eval1["reasoning_grounded"]
    assert eval1["composite_score"] <= 0.40

    r2 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова спів."
    eval2 = evaluate_single_response(target, alts, r2)
    assert not eval2["is_pass"]
    assert not eval2["reasoning_grounded"]
    assert eval2["composite_score"] <= 0.40


def test_explanation_concerning_word_forma_rejected() -> None:
    """M1 Review: A named word matching a grammatical descriptor (e.g. «форма») must not be exempted."""
    target = "badtoken"
    alts = ["goodtoken"]

    r1 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «форма»."
    eval1 = evaluate_single_response(target, alts, r1)
    assert not eval1["is_pass"]
    assert not eval1["reasoning_grounded"]
    assert eval1["composite_score"] <= 0.40

    r2 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова форма."
    eval2 = evaluate_single_response(target, alts, r2)
    assert not eval2["is_pass"]
    assert not eval2["reasoning_grounded"]
    assert eval2["composite_score"] <= 0.40


def test_explanation_concerning_authority_word_rejected() -> None:
    """M1 Review: A named word matching an authority name (e.g. «правопис») must not be exempted as a subject."""
    target = "badtoken"
    alts = ["goodtoken"]

    r1 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «правопис»."
    eval1 = evaluate_single_response(target, alts, r1)
    assert not eval1["is_pass"]
    assert not eval1["reasoning_grounded"]
    assert eval1["composite_score"] <= 0.40

    r2 = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова правопис."
    eval2 = evaluate_single_response(target, alts, r2)
    assert not eval2["is_pass"]
    assert not eval2["reasoning_grounded"]
    assert eval2["composite_score"] <= 0.40


def test_grammatical_qualifiers_not_treated_as_unrelated_subjects() -> None:
    """M1 Review P2: Grammatical qualifiers (e.g. «чоловічого роду») describe the subject and must not fail grounding."""
    target = "badtoken"
    alts = ["goodtoken"]

    r = "Вживайте goodtoken, бо за словником ВЕСУМ це іменник чоловічого роду з питомим суфіксом -ник."
    eval_res = evaluate_single_response(target, alts, r)
    assert eval_res["is_pass"]
    assert eval_res["reasoning_grounded"]
    assert eval_res["composite_score"] == 1.0


def test_explanation_concerning_words_with_modifier_prefixes_rejected() -> None:
    """M1 Review: Lexical subjects starting with rod-, vyd-, chas- (e.g. «родина», «видання», «часопис») must fail."""
    target = "badtoken"
    alts = ["goodtoken"]

    for word in ("родина", "видання", "часопис"):
        r_quoted = f"Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «{word}»."
        eval_q = evaluate_single_response(target, alts, r_quoted)
        assert not eval_q["is_pass"], f"Expected {word} (quoted) to fail"
        assert not eval_q["reasoning_grounded"], f"Expected {word} (quoted) grounding to fail"
        assert eval_q["composite_score"] <= 0.40

        r_unquoted = f"Вживайте goodtoken, бо у словнику подано пояснення суфікса слова {word}."
        eval_u = evaluate_single_response(target, alts, r_unquoted)
        assert not eval_u["is_pass"], f"Expected {word} (unquoted) to fail"
        assert not eval_u["reasoning_grounded"], f"Expected {word} (unquoted) grounding to fail"
        assert eval_u["composite_score"] <= 0.40


def test_explanation_concerning_words_odnyny_mnozhyny_rejected() -> None:
    """M1 Review P2: Explicit subjects 'однини', 'множини', or quoted modifier phrases must fail."""
    target = "badtoken"
    alts = ["goodtoken"]

    for word in ("однини", "множини"):
        r_quoted = f"Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «{word}»."
        eval_q = evaluate_single_response(target, alts, r_quoted)
        assert not eval_q["is_pass"], f"Expected {word} (quoted) to fail"
        assert not eval_q["reasoning_grounded"], f"Expected {word} (quoted) grounding to fail"
        assert eval_q["composite_score"] <= 0.40

        r_unquoted = f"Вживайте goodtoken, бо у словнику подано пояснення суфікса слова {word}."
        eval_u = evaluate_single_response(target, alts, r_unquoted)
        assert not eval_u["is_pass"], f"Expected {word} (unquoted) to fail"
        assert not eval_u["reasoning_grounded"], f"Expected {word} (unquoted) grounding to fail"
        assert eval_u["composite_score"] <= 0.40

    # Quoted modifier phrase must also be treated as a named entity
    r_phrase = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «чоловічого роду»."
    eval_phrase = evaluate_single_response(target, alts, r_phrase)
    assert not eval_phrase["is_pass"]
    assert not eval_phrase["reasoning_grounded"]
    assert eval_phrase["composite_score"] <= 0.40


def test_grammatical_number_modifiers_admitted() -> None:
    """M1 Review P2: Genuine grammatical number modifier phrases (e.g. 'у формі однини') must pass."""
    target = "badtoken"
    alts = ["goodtoken"]

    cases = [
        "Вживайте goodtoken, бо за словником ВЕСУМ це іменник у формі однини з питомим суфіксом -ник.",
        "Вживайте goodtoken, бо за словником ВЕСУМ це іменник числа однини з питомим суфіксом -ник.",
        "Вживайте goodtoken, бо за словником ВЕСУМ це іменник, що вживається в однині з питомим суфіксом -ник.",
    ]
    for r in cases:
        eval_res = evaluate_single_response(target, alts, r)
        assert eval_res["is_pass"], f"Expected {r} to pass"
        assert eval_res["reasoning_grounded"], f"Expected {r} grounding to pass"
        assert eval_res["composite_score"] == 1.0


def test_word_internal_apostrophes_not_treated_as_quotes() -> None:
    """M1 Review P2: Word-internal apostrophes (e.g. «Об'єкт», «пов'язано») must not suppress modifier stripping."""
    target = "badtoken"
    alts = ["goodtoken"]

    r = (
        "Об'єкт аналізу: Вживайте goodtoken, бо за словником ВЕСУМ це іменник чоловічого роду з питомим суфіксом -ник. "
        "Це пов'язано зі словотвором."
    )
    eval_res = evaluate_single_response(target, alts, r)
    assert eval_res["is_pass"]
    assert eval_res["reasoning_grounded"]
    assert eval_res["composite_score"] == 1.0


def test_unquoted_modifier_phrases_as_named_subjects_rejected() -> None:
    """M1 Review P2: Unquoted modifier phrases introduced by 'слова' (e.g. 'слова чоловічого роду') must fail."""
    target = "badtoken"
    alts = ["goodtoken"]

    r = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова чоловічого роду."
    eval_res = evaluate_single_response(target, alts, r)
    assert not eval_res["is_pass"]
    assert not eval_res["reasoning_grounded"]
    assert eval_res["composite_score"] <= 0.40


def test_unquoted_forma_odnyny_as_named_subject_rejected() -> None:
    """M1 Review P2: Unquoted 'слова форма однини' must not have its subject stripped and must fail."""
    target = "badtoken"
    alts = ["goodtoken"]

    r = "Вживайте goodtoken, бо у словнику подано пояснення суфікса слова форма однини."
    eval_res = evaluate_single_response(target, alts, r)
    assert not eval_res["is_pass"]
    assert not eval_res["reasoning_grounded"]
    assert eval_res["composite_score"] <= 0.40


def test_modifier_sequence_ordering_independent() -> None:
    """M1 Review P2: Chained modifiers (e.g. 'другої відміни чоловічого роду') must be order-independent."""
    target = "badtoken"
    alts = ["goodtoken"]

    cases = [
        "Вживайте goodtoken, бо за словником ВЕСУМ це іменник другої відміни чоловічого роду з питомим суфіксом -ник.",
        "Вживайте goodtoken, бо за словником ВЕСУМ це іменник чоловічого роду другої відміни з питомим суфіксом -ник.",
    ]
    for r in cases:
        eval_res = evaluate_single_response(target, alts, r)
        assert eval_res["is_pass"], f"Expected {r} to pass"
        assert eval_res["reasoning_grounded"], f"Expected {r} grounding to pass"
        assert eval_res["composite_score"] == 1.0


def test_unquoted_goodtoken_subject_explanation_admitted() -> None:
    """M1 Review P2: Unquoted target subject 'слово goodtoken є іменником чоловічого роду' must pass."""
    target = "badtoken"
    alts = ["goodtoken"]

    r_unquoted = (
        "Вживайте goodtoken, бо за словником ВЕСУМ слово goodtoken є іменником чоловічого роду з питомим суфіксом -ник."
    )
    eval_u = evaluate_single_response(target, alts, r_unquoted)
    assert eval_u["is_pass"]
    assert eval_u["reasoning_grounded"]
    assert eval_u["composite_score"] == 1.0

    r_quoted = "Вживайте goodtoken, бо за словником ВЕСУМ слово «goodtoken» є іменником чоловічого роду з питомим суфіксом -ник."
    eval_q = evaluate_single_response(target, alts, r_quoted)
    assert eval_q["is_pass"]
    assert eval_q["reasoning_grounded"]
    assert eval_q["composite_score"] == 1.0


def test_nested_grammatical_descriptors_target_and_unrelated_subjects() -> None:
    """M1 Review P2: Descriptor chains (e.g. 'варіант форми слова', 'форма іменника') must resolve through to their lexical subject."""
    target = "badtoken"
    alts = ["goodtoken"]

    # Target subject through descriptor chain -> PASS (1.0)
    for phrase in (
        "форма слова goodtoken",
        "форма іменника goodtoken",
        "форма слова «goodtoken»",
        "форма іменника «goodtoken»",
        "варіант форми слова goodtoken",
        "варіант форми слова «goodtoken»",
        "варіант форми іменника goodtoken",
        "варіант форми іменника «goodtoken»",
        "пояснення варіанта форми слова goodtoken",
        "пояснення варіанта форми слова «goodtoken»",
        "пояснення значення варіанта форми слова goodtoken",
        "пояснення суфікса варіанта форми іменника goodtoken",
    ):
        r_target = f"Вживайте goodtoken, бо за словником ВЕСУМ це {phrase} з питомим суфіксом -ник."
        eval_t = evaluate_single_response(target, alts, r_target)
        assert eval_t["is_pass"], f"Expected {phrase} to pass"
        assert eval_t["reasoning_grounded"], f"Expected {phrase} grounding to pass"
        assert eval_t["composite_score"] == 1.0

    # Unrelated subject through descriptor chain -> FAIL (<= 0.40)
    for phrase in (
        "форма слова будинок",
        "форма іменника будинок",
        "форма слова «будинок»",
        "форма іменника «будинок»",
        "форма слова форма",
        "форма слова іменник",
        "форма слова «форма»",
        "форма слова «іменник»",
        "форма іменника форма",
        "форма іменника іменник",
        "варіант форми слова будинок",
        "варіант форми слова «будинок»",
        "варіант форми слова форма",
        "варіант форми слова «форма»",
        "варіант форми слова іменник",
        "варіант форми слова «іменник»",
        "варіант форми іменника будинок",
        "варіант форми іменника «будинок»",
        "варіант форми іменника форма",
        "варіант форми іменника «форма»",
        "варіант форми іменника іменник",
        "варіант форми іменника «іменник»",
        "пояснення варіанта форми слова будинок",
        "пояснення варіанта форми слова «будинок»",
        "пояснення варіанта форми слова форма",
        "пояснення варіанта форми слова «форма»",
        "пояснення значення варіанта форми слова будинок",
        "варіант форми форма",
        "варіант форми «форма»",
        "варіант форми будинок",
        "варіант форми «будинок»",
    ):
        r_unrelated = f"Вживайте goodtoken, бо за словником ВЕСУМ це {phrase} з питомим суфіксом -ник."
        eval_u = evaluate_single_response(target, alts, r_unrelated)
        assert not eval_u["is_pass"], f"Expected {phrase} to fail"
        assert not eval_u["reasoning_grounded"], f"Expected {phrase} grounding to fail"
        assert eval_u["composite_score"] <= 0.40
