"""E3b1 ordered runner and contract edge cases."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import assemble, runner
from scripts.build.fresh.regeneration import invalidate_lesson_resolution, load_ledger, record_failure, record_success
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state.inventory_gate import GateFailure, GateReport
from scripts.curriculum.resolver.inputs import Allowlist
from tests.build.test_fresh_assemble import (
    make_draft,
    make_pack,
    make_plan,
    make_plan_lesson,
    make_word_record,
    make_words_store,
    validate_fixture_draft,
    validate_fixture_pack,
    validate_fixture_plan,
    validate_fixture_words,
)

pytestmark = pytest.mark.reads_content
ROOT = Path(__file__).resolve().parents[2]


def _fixture(*, text: str = "слово " * 11, two_senses: bool = False):
    w1 = make_word_record(1, "слово", gloss_en="word", sense_gloss="term")
    w1["forms"][0]["stressed"] = "сло\u0301во"
    records = [w1]
    if two_senses:
        w2 = make_word_record(2, "слово", gloss_en="word", sense_gloss="other sense")
        w2["forms"][0]["stressed"] = "сло\u0301во"
        records.append(w2)
    words = make_words_store(words=records)
    pack = make_pack()
    step = {"id": "s1", "kind": "teach", "teach": "Teach",
            "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
            "uses": {"grammar": [], "vocabulary": []}, "evidence": ["W-1"], "practice": []}
    lesson = make_plan_lesson(1, [step], core_words=[w1], incidental_words=records[1:])
    plan = make_plan(lessons=[lesson])
    draft = make_draft(steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": text, "explains": ["W-1"]}]}])
    for validate, obj in ((validate_fixture_pack, pack), (validate_fixture_words, words),
                          (validate_fixture_plan, plan), (validate_fixture_draft, draft)):
        validate(obj)
    return draft, plan, pack, words


def test_true_false_before_text_and_schema_valid_fixture():
    draft, plan, _pack, _words = _fixture()
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "true-false", "placement": "inline", "focus": "Read"}]
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    draft["steps"][0]["blocks"].insert(0, {"kind": "activity", "ref": "a1"})
    draft["activities"] = [{"id": "a1", "instruction": "Choose", "items": [{"statement": "слово", "is_true": True,
                                                                 "explanation": "Read"}]}]
    row = runner.check_3_structure(draft, plan["lessons"][0])
    assert row["reason"] == "true_false_before_text" and row["layer"] == "writer"


def test_structure_uses_plan_consolidation_list():
    draft, plan, _pack, _words = _fixture()
    plan["lessons"][0]["consolidation"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "true-false", "placement": "workbook", "focus": "Read"}]
    draft["activities"] = [{"id": "a1", "instruction": "Read", "items": [
        {"statement": "слово", "correct": True, "explanation": "Read"}]}]
    draft["consolidation"]["activities"] = ["a1"]
    assert runner.check_3_structure(draft, plan["lessons"][0])["status"] == "passed"


def test_form_choice_store_options_valid_invented_duplicate_and_tags():
    draft, plan, pack, words = _fixture()
    record = words["words"][0]
    record["forms"].append({**record["forms"][0], "form": "слова", "stressed": "слова\u0301", "tags": "noun:inanim:n:v_rod"})
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    item = {"sentence": "____", "answer": "слово", "options": ["слово", "слова"],
            "explanation": "Choose", "mode": "form-choice", "record": "W-1", "answer_tags": record["forms"][0]["tags"]}
    draft["activities"] = [{"id": "a1", "instruction": "Choose", "items": [item]}]
    row, found = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert row["status"] == "passed" and [f["stressed"] for f in found[("a1", 0)]] == ["сло\u0301во", "слова\u0301"]
    for changed in ({"options": ["слово", "invented"]}, {"options": ["слово", "слово"]},
                    {"answer_tags": "noun:missing"}):
        bad = copy.deepcopy(draft)
        bad["activities"][0]["items"][0].update(changed)
        row, _ = runner.check_4_activities(bad, plan["lessons"][0], words, pack)
        assert (row["check"], row["reason"], row["layer"]) == (4, "form_choice_options_invalid", "writer")


def test_counting_contract_urok_only_with_quoted_term_and_english():
    units = [{"tab": "urok", "role": "quoted_term", "text": "слово"},
             {"tab": "urok", "role": "vesum_exempt", "text": "English line"},
             {"tab": "urok", "role": "narration", "text": "слово"},
             {"tab": "slovnyk", "role": "record_print", "text": "слово слово"}]
    row = runner.check_6_count({"units": units}, 4)
    assert row["status"] == "passed"
    assert row["details"]["urok_tokens"] == 4
    assert row["details"]["ukrainian_tokens"] == 2
    assert row["details"]["ukrainian_share"] == 0.5
    assert "word_target_not_calibrated" in row["details"]["not_checked"]


def test_counting_contract_inline_gloss_uses_record_lemma_and_english_gloss():
    word = make_word_record(1, "слово", gloss_en="word in English")
    row = runner.check_6_count({"units": [
        {"tab": "urok", "role": "gloss_ref", "text": "{{gloss:W-1}}"},
        {"tab": "slovnyk", "role": "record_print", "text": "слово"},
    ]}, 4, make_words_store(words=[word]))
    assert row["details"]["urok_tokens"] == 4
    assert row["details"]["ukrainian_tokens"] == 1


def test_regeneration_repeated_check_uses_second_layer_and_invalidates_only_lesson(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")}
    first = {"check": 4, "code": "4", "reason": "bad", "layer": "writer"}
    one = record_failure(path, "sample-slug", 1, first, inputs, at="2026-01-01T00:00:00Z")
    assert one["regenerations"] == 0 and one["terminal_layer"] is None
    inputs["plan_sha256"] = "b" * 64
    two = record_failure(path, "sample-slug", 1, first, inputs, at="2026-01-02T00:00:00Z")
    assert two["regenerations"] == 1 and two["terminal_layer"] == "plan"
    assert load_ledger(path, "sample-slug", 1) == two
    for n in (1, 2):
        for suffix in ("questions.yaml", "resolutions.yaml"):
            target = tmp_path / f"lesson-{n}.{suffix}"
            lock.write(target, b"data")
    invalidate_lesson_resolution(tmp_path, 1)
    assert not (tmp_path / "lesson-1.resolutions.yaml").exists()
    assert (tmp_path / "lesson-2.resolutions.yaml").exists()


def test_two_regenerations_route_third_failure_to_driver(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")}
    for number in (1, 2, 3):
        result = record_failure(path, "sample-slug", 1,
                                {"check": number, "code": str(number), "reason": "failure", "layer": "writer"},
                                inputs, at=f"2026-01-0{number}T00:00:00Z")
    assert result["regenerations"] == 2
    assert result["terminal_layer"] == "driver"


def test_successful_regeneration_counts_even_without_a_second_failure(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")}
    record_failure(path, "sample-slug", 1,
                   {"check": 4, "code": "4", "reason": "failure", "layer": "writer"}, inputs,
                   at="2026-01-01T00:00:00Z")
    result = record_success(path, "sample-slug", 1)
    assert result["regenerations"] == 1 and result["terminal_layer"] is None


def test_each_check_failure_carries_layer():
    for number in range(1, 10):
        row = runner.failure(number, "fixture_failure", "writer")
        assert row == {"check": number, "status": "failed", "code": str(number),
                       "reason": "fixture_failure", "layer": "writer"}


def test_clean_environment_build_cli_fails_closed_before_dispatch(tmp_path):
    env = {"PATH": os.environ.get("PATH", ""), "LEARN_UKRAINIAN_REPO_ROOT": str(tmp_path)}
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.build.fresh", "build", "a1", "sample-slug", "--lesson", "1"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30, check=False,
    )
    assert completed.returncode == 1
    assert '"layer": "driver"' in completed.stderr


def test_production_question_callable_awaits_task_and_reads_answers(tmp_path, monkeypatch):
    answer_file = tmp_path / "answers.yaml"
    answer_file.write_text("```yaml\nanswers:\n- id: Q-001\n  record: W-1\n```\n", encoding="utf-8")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        output = "" if len(calls) == 1 else json.dumps({"status": "done", "result_file": str(answer_file)})
        return subprocess.CompletedProcess(cmd, 0, stdout=output, stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    batch = {"lesson": {"level": "a1", "slug": "sample-slug", "n": 1}, "questions": []}
    answers = runner.dispatch_questions(batch, "agy:fixture", repo_root=tmp_path)
    assert answers == {"answers": [{"id": "Q-001", "record": "W-1"}]}
    assert len(calls) == 2
    assert calls[0][0][0] == calls[1][0][0] == sys.executable
    assert "--model" in calls[0][0] and "fixture" in calls[0][0]
    assert "wait" in calls[1][0]
    assert all(call[1]["timeout"] for call in calls)


class _FixtureSources:
    def _vesum_identity(self):
        return "f" * 64, {}

    def verify_words(self, words):
        return type("Result", (), {"raw": {word: [] for word in words}})()


def _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, *, seat="agy:fixture", expected_inputs=None,
                  inventory_gate=None, render_check=None, manifest_writer=None):
    allowlist = Allowlist.from_records(words["words"], words_lock="f" * 64)
    monkeypatch.setattr(assemble, "planned_state", lambda *a, **kw: type("State", (), {"cumulative_core_count": 10, "waiver": None})())
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **kw: (True, ""))
    monkeypatch.setattr(assemble.lesson_lock, "compute_lesson_lock", lambda *a, **kw: {"lessons": [{"n": 1, "entry_sha256": "0" * 64}]})
    monkeypatch.setattr(assemble, "compute_lesson_immersion_band", lambda **kw: type("Band", (), {"band_key": "a1"})())
    questions_seen = []

    def answer(batch, seat):
        questions_seen.extend(q["id"] for q in batch["questions"])
        return {"answers": [{"id": q["id"], "record": "W-2" if q["unit"]["block"] == "inc_W-2" else q["candidates"][0]["record"]}
                            for q in batch["questions"]]}

    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    (state / "lesson-1.draft.yaml").write_bytes(lock.yaml_bytes(draft))
    monkeypatch.setattr(runner, "write_manifest", manifest_writer or
                        (lambda *a, **kw: ({"recap": False}, "a" * 64)))
    report = runner.run_lesson(
        "a1", "sample-slug", 1, draft=draft, plan=plan, pack=pack, words=words,
        state_dir=state, repo_root=tmp_path, plans_dir=tmp_path, evidence_dir=tmp_path,
        question_seat=seat, question_dispatch=answer, sources=_FixtureSources(),
        allowlist=allowlist, site_dir=tmp_path / "site",
        inventory_gate=inventory_gate or (lambda *a, **kw: GateReport("a1", "sample-slug", 1, ())),
        observed_writer=lambda *a, **kw: None, expected_inputs=expected_inputs,
        render_check=render_check or (lambda *a, **kw: assemble.CheckResult(
            check=11, passed=True, artifacts={"verify_shippable": {"shippable": True}})),
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return report, state, questions_seen


def test_contract_fixture_same_stress_sense_through_checks_1_to_9(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture(two_senses=True)
    report, state, seen = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    assert [r["status"] for r in report["checks"][:9]] == ["passed"] * 9
    assert seen
    assert lock.check(state / "lesson-1.gates.yaml")
    assert lock.check(state / "lesson-1.resolutions.yaml")
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    assert "сло\u0301во" in mdx
    assert "other sense" in mdx


def test_check_11_failure_is_engine_layer_and_ledger_check_11(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words,
                                     render_check=lambda *a, **kw: assemble.CheckResult(
                                         check=11, passed=False, reason="render failed", layer="render",
                                         artifacts={"verify_shippable": {"shippable": False}}))
    failed = next(row for row in report["checks"] if row["status"] == "failed")
    assert (failed["check"], failed["layer"], failed["reason"]) == (11, "engine", "render failed")
    assert failed["details"]["verify_shippable"]["shippable"] is False
    assert load_ledger(state / "lesson-1.regeneration.yaml", "sample-slug", 1)["attempts"][0]["failed_check"] == 11
    assert not (state / "lesson-1.manifest.yaml").exists()


def test_check_12_failure_has_error_file_and_no_current_manifest(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()

    def mismatch(*a, **kw):
        raise ValueError("style card sidecar mismatch: docs/style-cards/a1.sha256")

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words,
                                     manifest_writer=mismatch)
    assert report["passed"] is False and report["passed_through"] == 12
    assert yaml.safe_load((state / "lesson-1.gates.yaml").read_text(encoding="utf-8"))["passed"] is True
    error = yaml.safe_load((state / "lesson-1.manifest-error.yaml").read_text(encoding="utf-8"))
    assert error["check"] == 12 and error["layer"] == "engine" and "a1.sha256" in error["path"]
    assert not (state / "lesson-1.manifest.yaml").exists()


def test_contract_fixture_marked_form_stops_at_check_7(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    words["words"][0]["forms"][0]["markers"] = ["arch"]
    words["words"][0]["forms"][0]["learner"] = False
    validate_fixture_words(words)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert bad["check"] == 7 and bad["layer"] == "pack" and bad["token"] == "слово"


def test_contract_fixture_hyphenated_compound_through_check_9(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture(text="слово-слово " * 11)
    rec = words["words"][0]
    rec["lemma"] = "слово-слово"
    rec["forms"][0]["form"] = "слово-слово"
    rec["forms"][0]["stressed"] = "сло\u0301во-сло\u0301во"
    plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["lemma"] = "слово-слово"
    validate_fixture_words(words)
    validate_fixture_plan(plan)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    assert "сло\u0301во-сло\u0301во" in (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")


def test_contract_fixture_intentional_error_item_through_check_9(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    pack["errors"] = [{"id": "E-001", "source": {"table": "ua_gec_errors", "id": 1},
                       "incorrect": "слове", "correct": "слово", "error_type": "form", "pattern": "fixture"}]
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "error-correction", "placement": "inline",
                                           "focus": "Correct", "error_refs": ["E-001"]}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [{"id": "a1", "instruction": "Correct", "items": [
        {"sentence": "слове", "error": "слове", "correction": "слово", "explanation": "Correct",
         "error_ref": "E-001"}]}]
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    assert "слове" in (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")


def test_contract_fixture_regeneration_invalidates_receipts(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    draft["steps"][0]["id"] = "s2"
    validate_fixture_draft(draft)
    first, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    receipt = state / "lesson-1.resolutions.yaml"
    lock.write(receipt, b"old")
    plan["title"] = "Changed plan input"
    validate_fixture_plan(plan)
    second, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    ledger = load_ledger(state / "lesson-1.regeneration.yaml", "sample-slug", 1)
    assert first["checks"][2]["status"] == second["checks"][2]["status"] == "failed"
    assert ledger["regenerations"] == 1 and ledger["terminal_layer"] == "plan"
    assert not receipt.exists()


def test_runner_form_choice_options_invalid_reports_check_4(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [{"id": "a1", "instruction": "Choose", "items": [
        {"sentence": "____", "answer": "слово", "options": ["слово", "invented"],
         "explanation": "Choose", "mode": "form-choice", "record": "W-1",
         "answer_tags": words["words"][0]["forms"][0]["tags"]}]}]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["reason"], bad["layer"]) == (4, "form_choice_options_invalid", "writer")


def test_runner_true_false_before_text_reports_check_3(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "true-false", "placement": "inline", "focus": "Read"}]
    draft["steps"][0]["blocks"].insert(0, {"kind": "activity", "ref": "a1"})
    draft["activities"] = [{"id": "a1", "instruction": "Read", "items": [
        {"statement": "слово", "correct": True, "explanation": "Read"}]}]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["reason"], bad["layer"]) == (3, "true_false_before_text", "writer")


def test_runner_check_1_echo_hash_failure(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words,
                                 expected_inputs={"plan_sha256": "f" * 64})
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (1, "writer")


def test_runner_check_2_declared_gap(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    draft["status"] = "evidence_gap"
    draft["gaps"] = [{"step": "s1", "need": "example", "detail": "Missing evidence"}]
    draft["steps"][0]["blocks"] = []
    validate_fixture_draft(draft)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (2, "pack")


def test_runner_check_5_missing_record(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    draft["steps"][0]["blocks"].append({"kind": "example", "ref": "EX-1"})
    plan["lessons"][0]["steps"][0]["evidence"].append("EX-1")
    validate_fixture_draft(draft)
    validate_fixture_plan(plan)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (5, "pack")


def test_runner_check_6_target_is_lesson_minimum(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture(text="слово")
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"], bad["details"]["urok_tokens"]) == (6, "writer", 1)


def test_runner_check_7_source_unavailable_has_gate_report(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()

    def unavailable(*args, **kwargs):
        raise OSError("fixture source missing")

    monkeypatch.setattr(runner, "resolve", unavailable)
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (7, "pack")
    assert lock.check(state / "lesson-1.gates.yaml")


def test_runner_check_8_requires_explicit_seat(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture(two_senses=True)
    report, state, seen = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, seat=None)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["reason"], bad["layer"]) == (8, "question_seat_required", "driver")
    assert seen == []
    assert lock.check(state / "lesson-1.questions.yaml")


def test_runner_check_9_engine_failure_layer(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    monkeypatch.setattr(runner, "check_9_stress_and_render", lambda *a, **kw:
                        assemble.CheckResult(check=9, passed=False, reason="fixture_render_error", layer="engine"))
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["reason"], bad["layer"]) == (9, "fixture_render_error", "engine")


def test_inventory_failure_is_reported_as_check_7_after_answers(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture(two_senses=True)

    def gate(level, slug, n, stream, **kwargs):
        assert all(token["selected"] is not None for token in stream.open_tokens())
        assert any(token["unit"].get("step") == "s1" for token in stream.tokens)
        return GateReport(level, slug, n, (GateFailure(
            "core_not_introduced", level, slug, n, "urok", "слово", "слово", "W-1", "fixture gate failure"),))

    report, _, seen = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, inventory_gate=gate)
    assert seen
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["code"], bad["layer"]) == (7, "core_not_introduced", "writer")
    assert report["checks"][7]["status"] == "passed"


def test_form_choice_prints_store_spelling_and_state_is_byte_stable(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    form = {**words["words"][0]["forms"][0], "form": "слова", "stressed": "слова\u0301",
            "tags": "noun:inanim:n:v_rod"}
    words["words"][0]["forms"].append(form)
    plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["forms"].append(form["tags"])
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [{"id": "a1", "instruction": "Choose", "items": [
        {"sentence": "____", "answer": "слово", "options": ["слово", "слова"],
         "explanation": "Choose", "mode": "form-choice", "record": "W-1",
         "answer_tags": words["words"][0]["forms"][0]["tags"]}]}]
    validate_fixture_words(words)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    first, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert first["passed"] is True, first
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    assert "сло\u0301во" in mdx and "слова\u0301" in mdx
    before = {name: (state / name).read_bytes() for name in (
        "lesson-1.expanded.yaml", "lesson-1.questions.yaml", "lesson-1.resolutions.yaml",
        "lesson-1.stressed.yaml", "lesson-1.gates.yaml")}
    second, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert second == first
    assert {name: (state / name).read_bytes() for name in before} == before
