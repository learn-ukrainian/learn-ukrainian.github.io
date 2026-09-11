"""Unit tests for ULDR consumer formatting and evaluation harness (#7926)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.projects.open_model_data.v4_evaluate_decolonization import (
    evaluate_predictions,
    evaluate_single_response,
)
from scripts.projects.open_model_data.v4_format_decolonization import (
    dpo_pair_to_trl,
    format_consumer_datasets,
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
    assert trl["prompt"] == sample_dpo["prompt"]
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
    assert res_bad["composite_score"] < 0.50

    # 3. Merely mentioning authentic word without reasoning
    minimal_resp = "Вживайте пилосмок."
    res_min = evaluate_single_response(target, alts, minimal_resp)
    assert res_min["calque_eliminated"] is True
    assert res_min["authentic_suggested"] is True
    assert res_min["reasoning_grounded"] is False
    assert res_min["composite_score"] == 0.80
    assert res_min["is_pass"] is True


def test_format_and_evaluate_end_to_end(tmp_path: Path) -> None:
    in_dir = tmp_path / "generated"
    in_dir.mkdir(parents=True)
    out_dir = tmp_path / "consumer"

    # Create mock manifest and shards
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

    dpo_rec = {
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
    dpo_held_out.write_text(json.dumps(dpo_rec, ensure_ascii=False) + "\n", encoding="utf-8")

    record_train = {
        "trajectory_id": "traj.decolonize.perekluchyty",
        "target_term": "переключити",
        "query": "Як сказати переключити?",
        "reasoning_steps": ["Калька від рос. переключить.", "Питоме: перемкнути."],
        "final_response": "Вживайте «перемкнути».",
        "register_spectrum": {"alternatives": [{"lemma": "перемкнути"}]},
    }
    traj_train.write_text(json.dumps(record_train, ensure_ascii=False) + "\n", encoding="utf-8")
    dpo_train.write_text(json.dumps(dpo_rec, ensure_ascii=False) + "\n", encoding="utf-8")

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

    # Verify consumer_formats_manifest.json on disk
    manifest_on_disk = json.loads((out_dir / "consumer_formats_manifest.json").read_text(encoding="utf-8"))
    assert manifest_on_disk["quality_metrics"]["zero_private_paths"] is True
    assert manifest_on_disk["quality_metrics"]["zero_restricted_sources"] is True

    # Verify shipped DPO records have populated calque_category
    dpo_shards = list(out_dir.glob("uldr_dpo_*.jsonl"))
    assert len(dpo_shards) >= 1
    for dpo_s in dpo_shards:
        for line in dpo_s.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                assert rec["calque_category"] == "lexical_calque"

    # Run evaluate_predictions with a passing prediction
    preds_file = tmp_path / "preds.jsonl"
    preds_file.write_text(
        json.dumps(
            {
                "id": "traj.decolonize.kholostyak",
                "target_term": "холостяк",
                "response": "Слово «холостяк» — це росіянізм і радянська калька. Правильно казати парубок за словником ВЕСУМ.",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    eval_report = tmp_path / "report.json"
    eval_res = evaluate_predictions(traj_held_out, preds_file, eval_report)
    assert eval_res["total_evaluated"] == 1
    assert eval_res["calque_elimination_rate"] == 1.0
    assert eval_res["authentic_suggestion_rate"] == 1.0
    assert eval_res["reasoning_grounding_rate"] == 1.0
    assert eval_res["pass_rate"] == 1.0
    assert eval_report.is_file()
