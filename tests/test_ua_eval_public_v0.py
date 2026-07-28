from __future__ import annotations

from scripts.projects.ua_eval_harness.smoke_public_v0 import run_smoke


def test_public_v0_reproduces_all_saved_baselines() -> None:
    summaries = run_smoke()

    assert [summary["name"] for summary in summaries] == [
        "identity",
        "deterministic fixture rules",
        "gpt-5.6-terra saved run",
    ]
    assert all(summary["responses"] == 677 for summary in summaries)
    assert summaries[0]["edit_f0_5"] == 0.0
    assert summaries[1]["edit_f0_5"] == 0.0
    assert summaries[2]["edit_f0_5"] == 0.24390243902439027
    assert summaries[0]["headline_calque_recall"] == 0.0
    assert summaries[1]["headline_calque_recall"] == 0.0
    assert summaries[2]["headline_calque_recall"] == 0.14102564102564102
    assert summaries[2]["exact_sentence_accuracy"] == 0.16100443131462333
