"""E3b1 ordered runner and contract edge cases."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import assemble, runner
from scripts.build.fresh.regeneration import invalidate_lesson_resolution, load_ledger, record_failure, record_success
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state.inventory_gate import GateFailure, GateReport
from scripts.curriculum.resolver import receipts
from scripts.curriculum.resolver.inputs import Allowlist
from tests.build.test_fresh_assemble import (
    make_draft,
    make_pack,
    make_plan,
    make_plan_lesson,
    make_text_record,
    make_word_record,
    make_words_store,
    validate_fixture_draft,
    validate_fixture_pack,
    validate_fixture_plan,
    validate_fixture_words,
)
from tests.curriculum.resolver.evidence_helpers import receipt_sources  # noqa: F401

pytestmark = pytest.mark.reads_content
ROOT = Path(__file__).resolve().parents[2]


def _confirm_fixture_form(state: Path, item: dict) -> None:
    resolution = receipts.check_receipts(state / "lesson-1.resolutions.yaml")
    demand = item["requires"]
    options = item["options"]
    authored = yaml.safe_load((state / "lesson-1.draft.yaml").read_text(encoding="utf-8"))
    doc = {
        "requirements_schema": 2,
        "lesson": resolution["lesson"],
        "inputs": receipts.requirement_inputs(resolution["inputs"], authored),
        "items": [
            {
                "activity": "a1",
                "item": 0,
                "requires": demand,
                "payload_sha256": receipts.requirement_payload_sha256(
                    receipts.requirement_sentence(item), options, 0, demand
                ),
                "decision": "confirm",
                "reason": "fixture checks receipt plumbing",
                "requires_forced": True,
                "options": [
                    {"text": text, "judgement": "valid" if i == 0 else "invalid", "evidence": ["vesum:5682038-5682052"]}
                    for i, text in enumerate(options)
                ],
                "writer": {"seat": "codex@sol", "family": "openai"},
                "reviewer": {"seat": "claude@sonnet", "family": "anthropic", "lane": "language"},
            }
        ],
    }
    receipts.write_requirement_receipts(receipts.requirement_receipt_path(state, 1), doc)


def _fixture(*, text: str = "слово " * 11, two_senses: bool = False):
    w1 = make_word_record(1, "слово", gloss_en="word", sense_gloss="term")
    w1["forms"][0]["stressed"] = "сло\u0301во"
    records = [w1]
    if two_senses:
        w2 = make_word_record(2, "слово", gloss_en="other sense", sense_gloss="unchecked")
        w2["forms"][0]["stressed"] = "сло\u0301во"
        records.append(w2)
    words = make_words_store(words=records)
    pack = make_pack()
    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": ["W-1"],
        "practice": [],
    }
    lesson = make_plan_lesson(1, [step], core_words=[w1], incidental_words=records[1:])
    plan = make_plan(lessons=[lesson])
    draft = make_draft(steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": text, "explains": ["W-1"]}]}])
    for validate, obj in (
        (validate_fixture_pack, pack),
        (validate_fixture_words, words),
        (validate_fixture_plan, plan),
        (validate_fixture_draft, draft),
    ):
        validate(obj)
    return draft, plan, pack, words


@pytest.mark.parametrize("surface", ["И", "А", "О", "У", "И, и", "Ии", "[и]"])
def test_literacy_inline_letters_bypass_word_lookup(surface):
    from scripts.curriculum.resolver.inputs import ExpandedDocument
    from scripts.curriculum.resolver.stream import resolve

    draft, plan, pack, words = _fixture(text="Meet {{uk:" + surface + "}} and {{uk:слово}}.")
    lesson = plan["lessons"][0]
    lesson["inventory"]["phonetics"] = {"letters": ["А", "О", "У", "И"], "sounds": []}
    # Word records for а/о/у must never win over the phonetics classification.
    letters_as_words = [make_word_record(i, ch, pos="intj", gloss_en="synthetic")
                        for i, ch in enumerate(["а", "о", "у"], 2)]
    allowlist = Allowlist.from_records(words["words"] + letters_as_words, letters={"А", "О", "У", "И"})
    expanded, provenance = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    stream = resolve(ExpandedDocument.from_data(expanded), allowlist, _FixtureSources())
    letter_rows = [t for t in stream.tokens if t["role"] == "phonetics"]
    assert letter_rows
    assert all(t["class"] == "letter_or_syllable" and t["candidates"] == [] for t in letter_rows)
    assert all(t["selected"] is None for t in letter_rows)
    assert any(s["role"] == "phonetics" for s in provenance["spans"])
    assert any(t["token"] == "слово" and t["class"] == "resolved" for t in stream.tokens)
    assert runner.check_7_deterministic(stream, lesson)["status"] == "passed"


def test_literacy_unlisted_letter_has_typed_engine_failure():
    from scripts.curriculum.resolver.inputs import ExpandedDocument
    from scripts.curriculum.resolver.stream import resolve

    draft, plan, pack, words = _fixture(text="Meet {{uk:Н}} and {{uk:слово}}.")
    lesson = plan["lessons"][0]
    lesson["inventory"]["phonetics"] = {"letters": ["И"], "sounds": []}
    expanded, _ = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    stream = resolve(ExpandedDocument.from_data(expanded), Allowlist.from_records(words["words"], letters={"И"}), _FixtureSources())
    row = runner.check_7_deterministic(stream, lesson)
    assert (row["status"], row["code"], row["layer"], row["token"]) == (
        "failed", "letter_outside_state", "engine", "Н")


def test_internal_term_triggers_writer_regeneration_feedback(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture(text="Learn it by ear as one chunk. " + "слово " * 11)
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    row = next(r for r in report["checks"] if r["status"] == "failed")
    assert (row["check"], row["layer"], row["token"]) == (5, "writer", "chunk")
    assert row["reason"] == "internal_learner_term: build/process term: chunk"
    ledger = load_ledger(state / "lesson-1.regeneration.yaml", "sample-slug", 1)
    assert ledger["terminal_layer"] is None
    assert ledger["attempts"][0]["reason"] == row["reason"]


def test_runner_calls_frozen_draft_report_interface(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    called = []

    def controlled_report(received_plan, received_drafts):
        called.append((received_plan, received_drafts))
        return {"lessons": {"1": {"workbook": 0}}}

    # Control only the return value here to verify the runner's exact call contract.
    monkeypatch.setattr(runner, "draft_report", controlled_report)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True
    assert called == [(plan, [draft])]
    assert report["checks"][3]["details"]["draft_report"] == {"lessons": {"1": {"workbook": 0}}}


def test_runner_real_draft_report_has_numeric_single_lesson_totals(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    pack["errors"] = [
        {
            "id": "E-001",
            "source": {"table": "ua_gec_errors", "id": 1},
            "incorrect": "слове",
            "correct": "слово",
            "error_type": "form",
            "pattern": "fixture",
        }
    ]
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [
        {"id": "a1", "type": "error-correction", "placement": "inline", "focus": "Correct", "error_refs": ["E-001"]}
    ]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Correct",
            "items": [
                {
                    "sentence": "слове",
                    "error": "слове",
                    "correction": "слово",
                    "explanation": "Correct",
                    "error_ref": "E-001",
                }
            ],
        }
    ]
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)

    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    activity = report["checks"][3]["details"]["draft_report"]
    assert activity["stage"] == "draft"
    assert activity["lessons"] == [
        {
            "n": 1,
            "response_opportunities": {"total": 1, "by_type": {"error-correction": 1}},
            "explanation_coverage": {"explained": 1, "total": 1},
            "planned_workbook": 0,
            "rendered_and_playable": "not_available_at_this_stage",
        }
    ]
    assert activity["module"]["response_opportunities_total"] == 1
    assert activity["module"]["inline_response_opportunities_total"] == 1


def test_runner_missing_vesum_orthography_fails_closed(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    # VESUM слово/слова: source location 5682038-5682052.
    words["words"][0]["forms"].append(
        {
            **words["words"][0]["forms"][0],
            "form": "слова",
            "stressed": "слова\u0301",
            "tags": "noun:inanim:n:v_rod",
        }
    )
    words["words"].extend(
        [
            make_word_record(2, "а", pos="conj", gloss_en="and"),
            make_word_record(3, "я", pos="pron", gloss_en="I"),
        ]
    )
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Spelling"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Choose",
            "items": [
                {
                    "sentence": "слов___",
                    "options": ["а", "я"],
                    "answer": "а",
                    "mode": "orthography",
                    "target_record": "W-1",
                    "kind": "orthography",
                    "option_why": ["This spelling fits.", "This spelling does not fit."],
                    "explanation": "Choose the spelling.",
                }
            ],
        }
    ]
    monkeypatch.setenv("VESUM_DB_PATH", str(tmp_path / "missing-vesum.db"))
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["code"], bad["layer"]) == (7, "a1_choice_source_unavailable", "pack")


def test_true_false_before_text_and_schema_valid_fixture():
    draft, plan, _pack, _words = _fixture()
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "true-false", "placement": "inline", "focus": "Read"}]
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    draft["steps"][0]["blocks"].insert(0, {"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {"id": "a1", "instruction": "Choose", "items": [{"statement": "слово", "is_true": True, "explanation": "Read"}]}
    ]
    row = runner.check_3_structure(draft, plan["lessons"][0])
    assert row["reason"] == "true_false_before_text" and row["layer"] == "writer"


def test_structure_uses_plan_consolidation_list():
    draft, plan, _pack, _words = _fixture()
    plan["lessons"][0]["consolidation"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "true-false", "placement": "workbook", "focus": "Read"}]
    draft["activities"] = [
        {"id": "a1", "instruction": "Read", "items": [{"statement": "слово", "correct": True, "explanation": "Read"}]}
    ]
    draft["consolidation"]["activities"] = ["a1"]
    assert runner.check_3_structure(draft, plan["lessons"][0])["status"] == "passed"


def test_form_choice_store_options_valid_invented_duplicate_and_tags():
    draft, plan, pack, words = _fixture()
    record = words["words"][0]
    record["forms"].append(
        {**record["forms"][0], "form": "слова", "stressed": "слова\u0301", "tags": "noun:inanim:n:v_rod"}
    )
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    item = {
        "sentence": "____",
        "answer": "слово",
        "options": ["слово", "слова"],
        "explanation": "Choose",
        "mode": "form-choice",
        "record": "W-1",
        "answer_tags": record["forms"][0]["tags"],
        "kind": "form",
        "tests_feature": "Case",
        "requires": {"Case": "Nom", "Number": "Sing"},
        "option_why": ["This is the nominative form.", "This is the genitive form."],
    }
    draft["activities"] = [{"id": "a1", "instruction": "Choose", "items": [item]}]
    row, found = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert row["status"] == "passed" and [f["stressed"] for f in found[("a1", 0)]] == ["сло\u0301во", "слова\u0301"]
    for changed in (
        {"options": ["слово", "invented"]},
        {"options": ["слово", "слово"]},
        {"answer_tags": "noun:missing"},
    ):
        bad = copy.deepcopy(draft)
        bad["activities"][0]["items"][0].update(changed)
        row, _ = runner.check_4_activities(bad, plan["lessons"][0], words, pack)
        assert (row["check"], row["reason"], row["layer"]) == (4, "form_choice_options_invalid", "writer")


def test_counting_contract_urok_only_with_quoted_term_and_english():
    units = [
        {"tab": "urok", "role": "quoted_term", "text": "слово"},
        {"tab": "urok", "role": "vesum_exempt", "text": "English line"},
        {"tab": "urok", "role": "narration", "text": "слово"},
        {"tab": "slovnyk", "role": "record_print", "text": "слово слово"},
    ]
    row = runner.check_6_count({"units": units}, 4)
    assert row["status"] == "passed"
    assert row["details"]["urok_tokens"] == 4
    assert row["details"]["ukrainian_tokens"] == 2
    assert row["details"]["ukrainian_share"] == 0.5
    assert "word_target_not_calibrated" in row["details"]["not_checked"]


def test_counting_contract_inline_gloss_uses_record_lemma_and_english_gloss():
    word = make_word_record(1, "слово", gloss_en="word in English")
    row = runner.check_6_count(
        {
            "units": [
                {"tab": "urok", "role": "gloss_ref", "text": "{{gloss:W-1}}"},
                {"tab": "slovnyk", "role": "record_print", "text": "слово"},
            ]
        },
        4,
        make_words_store(words=[word]),
    )
    assert row["details"]["urok_tokens"] == 4
    assert row["details"]["ukrainian_tokens"] == 1


def test_regeneration_repeated_check_uses_second_layer_and_invalidates_only_lesson(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")}
    first = {"check": 4, "code": "4", "reason": "bad", "layer": "writer"}
    one = record_failure(path, "sample-slug", 1, first, inputs, at="2026-01-01T00:00:00Z")
    assert one["regenerations"] == 0 and one["terminal_layer"] is None
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
        result = record_failure(
            path,
            "sample-slug",
            1,
            {"check": number, "code": str(number), "reason": "failure", "layer": "writer"},
            inputs,
            at=f"2026-01-0{number}T00:00:00Z",
        )
    assert result["regenerations"] == 2
    assert result["terminal_layer"] == "driver"


def test_successful_regeneration_counts_even_without_a_second_failure(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")}
    record_failure(
        path,
        "sample-slug",
        1,
        {"check": 4, "code": "4", "reason": "failure", "layer": "writer"},
        inputs,
        at="2026-01-01T00:00:00Z",
    )
    result = record_success(path, "sample-slug", 1)
    assert result["regenerations"] == 1 and result["terminal_layer"] is None


def test_each_check_failure_carries_layer():
    for number in range(1, 10):
        row = runner.failure(number, "fixture_failure", "writer")
        assert row == {
            "check": number,
            "status": "failed",
            "code": str(number),
            "reason": "fixture_failure",
            "layer": "writer",
        }


def test_clean_environment_build_cli_fails_closed_before_dispatch(tmp_path):
    env = {"PATH": os.environ.get("PATH", ""), "LEARN_UKRAINIAN_REPO_ROOT": str(tmp_path)}
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.build.fresh", "build", "a1", "sample-slug", "--lesson", "1"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
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
    def __init__(self, *, evidence_sources=None):
        self.evidence_sources = evidence_sources

    def resolve_evidence_ids(self, evidence_ids):
        from scripts.curriculum.evidence.sources import Sources

        if self.evidence_sources is not None:
            return self.evidence_sources.resolve_evidence_ids(evidence_ids)
        with Sources() as sources:
            return sources.resolve_evidence_ids(evidence_ids)

    def bind_evidence_forms(self, resolved, citations):
        from scripts.curriculum.evidence.sources import Sources

        if self.evidence_sources is not None:
            return self.evidence_sources.bind_evidence_forms(resolved, citations)
        with Sources() as sources:
            return sources.bind_evidence_forms(resolved, citations)

    def _vesum_identity(self):
        return "f" * 64, {}

    def verify_words(self, words):
        return type("Result", (), {"raw": {word: [] for word in words}})()


def _complete_a1_choice_fixture(draft, plan, pack, words):
    """Give older integration fixtures the A1 metadata required by fresh drafts."""
    lesson = plan["lessons"][0]
    types = {activity["id"]: activity["type"] for activity in lesson.get("activities") or []}
    needs_host = False
    for activity in draft.get("activities") or []:
        typ = types.get(activity["id"])
        if typ == "match-up":
            activity.setdefault("left_role", "question")
            activity.setdefault("right_role", "answer")
            for pair in activity.get("pairs") or []:
                pair.setdefault("why", "These sides correspond.")
        for item in activity.get("items") or []:
            options = [True, False] if typ == "true-false" else item.get("words" if typ == "odd-one-out" else "options")
            option_texts = [option.get("text") if isinstance(option, dict) else option for option in options or []]
            if typ == "fill-in" and item.get("mode") == "form-choice":
                item.setdefault("kind", "form")
                item.setdefault("tests_feature", "Case")
                item.setdefault("requires", {"Case": "Nom", "Number": "Sing"})
            elif typ == "fill-in" and item.get("mode") == "orthography":
                item.setdefault("kind", "orthography")
                item.setdefault("target_record", "W-1")
            elif (
                len(option_texts) == 2
                and set(option_texts) == {"слово", "слова"}
                and words["words"][0]["lemma"] == "слово"
            ):
                record = words["words"][0]
                if not any(form["form"] == "слова" for form in record["forms"]):
                    record["forms"].append(
                        {
                            **record["forms"][0],
                            "form": "слова",
                            "stressed": "слова\u0301",
                            "tags": "noun:inanim:n:v_rod",
                        }
                    )
                key_text = item.get("answer") or item.get("correction") or item.get("letter")
                if key_text is None and type(item.get("correct")) is int:
                    key_text = option_texts[item["correct"]]
                if key_text is None:
                    key_text = next(
                        (
                            option["text"]
                            for option in options
                            if isinstance(option, dict) and option.get("correct") is True
                        ),
                        None,
                    )
                item.setdefault("kind", "form")
                item.setdefault("tests_feature", "Case")
                item.setdefault("requires", {"Case": "Gen" if key_text == "слова" else "Nom", "Number": "Sing"})
                item.setdefault("option_records", ["W-1", "W-1"])
            elif typ in {
                "quiz",
                "multiple-choice",
                "odd-one-out",
                "error-correction",
                "translate",
                "image-to-letter",
                "true-false",
            } and (typ != "error-correction" or item.get("options")):
                item.setdefault("kind", "comprehension")
                item.setdefault("host", {"kind": "quote", "ref": "T-1"})
                needs_host = True
            if isinstance(options, list) and options:
                item.setdefault("option_why", ["This choice is checked against the prompt."] * len(options))
    if needs_host:
        if not any(text.get("id") == "T-1" for text in pack.get("texts") or []):
            pack.setdefault("texts", []).append(make_text_record(1, "слово"))
        for step in draft.get("steps") or []:
            if any(block.get("kind") == "activity" for block in step.get("blocks") or []):
                blocks = step["blocks"]
                first_activity = next(i for i, block in enumerate(blocks) if block.get("kind") == "activity")
                if first_activity == 0:
                    continue
                if not any(block.get("kind") == "quote" and block.get("ref") == "T-1" for block in blocks):
                    blocks.insert(first_activity, {"kind": "quote", "ref": "T-1"})
                planned_step = next(candidate for candidate in lesson["steps"] if candidate["id"] == step["id"])
                if "T-1" not in planned_step.get("evidence", []):
                    planned_step.setdefault("evidence", []).append("T-1")


def _run_contract(
    tmp_path,
    monkeypatch,
    draft,
    plan,
    pack,
    words,
    *,
    seat="agy:fixture",
    expected_inputs=None,
    inventory_gate=None,
    render_check=None,
    manifest_writer=None,
    level=None,
    observed_writer=None,
    gloss_ids=frozenset(),
    question_dispatch=None,
    n=1,
    sources_receipt=True,
):
    lvl = level or plan.get("level") or "a1"
    if lvl == "a1":
        _complete_a1_choice_fixture(draft, plan, pack, words)
    allowlist = Allowlist.from_records(words["words"], gloss_ids=gloss_ids, words_lock="f" * 64)
    monkeypatch.setattr(
        assemble, "planned_state", lambda *a, **kw: type("State", (), {"cumulative_core_count": 10, "waiver": None})()
    )
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **kw: (True, ""))
    monkeypatch.setattr(
        assemble.lesson_lock,
        "compute_lesson_lock",
        lambda *a, **kw: {"lessons": [{"n": lesson["n"], "entry_sha256": "0" * 64} for lesson in plan["lessons"]]},
    )
    monkeypatch.setattr(assemble, "compute_lesson_immersion_band", lambda **kw: type("Band", (), {"band_key": lvl})())
    questions_seen = []

    def answer(batch, seat):
        questions_seen.extend(q["id"] for q in batch["questions"])
        return {
            "answers": [
                {"id": q["id"], "record": "W-2" if q["unit"]["block"] == "inc_W-2" else q["candidates"][0]["record"]}
                for q in batch["questions"]
            ]
        }

    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    (state / f"lesson-{n}.writer.yaml").write_text("model: gpt-6.1-sol\n", encoding="utf-8")
    (state / f"lesson-{n}.draft.yaml").write_bytes(lock.yaml_bytes(draft))
    if sources_receipt:
        from tests.build.test_fresh_source_coverage import seal_writer
        # An invalid draft remains an invalid assembly fixture.
        with suppress(assemble.AssemblerError):
            seal_writer(state, monkeypatch, draft, plan, pack, words, n=n, expected_inputs=expected_inputs)
    monkeypatch.setattr(runner, "write_manifest", manifest_writer or (lambda *a, **kw: ({"recap": False}, "a" * 64)))
    report = runner.run_lesson(
        lvl,
        "sample-slug",
        n,
        draft=draft,
        plan=plan,
        pack=pack,
        words=words,
        state_dir=state,
        repo_root=tmp_path,
        plans_dir=tmp_path,
        evidence_dir=tmp_path,
        question_seat=seat,
        question_dispatch=question_dispatch or answer,
        sources=_FixtureSources(),
        allowlist=allowlist,
        site_dir=tmp_path / "site",
        inventory_gate=inventory_gate or (lambda *a, **kw: GateReport(lvl, "sample-slug", 1, ())),
        observed_writer=observed_writer or (lambda *a, **kw: None),
        expected_inputs=expected_inputs,
        render_check=render_check
        or (
            lambda *a, **kw: assemble.CheckResult(
                check=11, passed=True, artifacts={"verify_shippable": {"shippable": True}}
            )
        ),
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
    report, state, _ = _run_contract(
        tmp_path,
        monkeypatch,
        draft,
        plan,
        pack,
        words,
        render_check=lambda *a, **kw: assemble.CheckResult(
            check=11,
            passed=False,
            reason="render failed",
            layer="render",
            artifacts={"verify_shippable": {"shippable": False}},
        ),
    )
    failed = next(row for row in report["checks"] if row["status"] == "failed")
    assert (failed["check"], failed["layer"], failed["reason"]) == (11, "engine", "render failed")
    assert failed["details"]["verify_shippable"]["shippable"] is False
    assert load_ledger(state / "lesson-1.regeneration.yaml", "sample-slug", 1)["attempts"][0]["failed_check"] == 11
    assert not (state / "lesson-1.manifest.yaml").exists()


def test_check11_harness_failure_preserves_layer_without_regeneration(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    report, state, _ = _run_contract(
        tmp_path,
        monkeypatch,
        draft,
        plan,
        pack,
        words,
        render_check=lambda *a, **kw: assemble.CheckResult(
            check=11,
            passed=False,
            reason="interpreter unavailable",
            layer="harness",
            artifacts={"verify_shippable": {"shippable": False}},
        ),
    )
    failed = next(row for row in report["checks"] if row["status"] == "failed")
    assert (failed["check"], failed["layer"]) == (11, "harness")
    ledger = load_ledger(state / "lesson-1.regeneration.yaml", "sample-slug", 1)
    assert ledger["attempts"] == [] and ledger["regenerations"] == 0
    assert (state / "lesson-1.writer-harness.yaml").is_file()


def test_check_12_failure_has_error_file_and_no_current_manifest(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()

    def mismatch(*a, **kw):
        raise ValueError("style card sidecar mismatch: docs/style-cards/a1.sha256")

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, manifest_writer=mismatch)
    assert report["passed"] is False and report["passed_through"] == 12
    assert yaml.safe_load((state / "lesson-1.gates.yaml").read_text(encoding="utf-8"))["passed"] is True
    error = yaml.safe_load((state / "lesson-1.manifest-error.yaml").read_text(encoding="utf-8"))
    assert error["check"] == 12 and error["layer"] == "engine" and "a1.sha256" in error["path"]
    assert not (state / "lesson-1.manifest.yaml").exists()


@pytest.mark.parametrize("stage", [7, 12])
@pytest.mark.parametrize("external", [False, True])
def test_failure_state_withholds_absolute_paths(tmp_path, monkeypatch, stage, external):
    from scripts.review.digest.error import DigestError

    draft, plan, pack, words = _fixture()
    path = Path("/home/private-user/project/receipts.yaml") if external else tmp_path / "state/receipts.yaml"

    def fail(*a, **kw):
        raise DigestError("receipt_span_alignment_failed", f"receipts {path}: token mismatch")

    kwargs = {"manifest_writer": fail} if stage == 12 else {"inventory_gate": fail}
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, **kwargs)
    assert report["passed"] is False and report["passed_through"] == stage
    files = [state / "lesson-1.regeneration.yaml", state / "lesson-1.gates.yaml"]
    if stage == 12:
        files.append(state / "lesson-1.manifest-error.yaml")
    serialized = "\n".join(p.read_text() for p in files) + str(report)
    assert str(tmp_path) not in serialized and "/home/" not in serialized
    assert "receipt_span_alignment_failed" in serialized
    assert ("<external-path>" if external else "./state/receipts.yaml") in serialized


def test_stress_surface_mismatch_is_an_engine_failure(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()

    def mismatch(*args):
        raise assemble.AssemblerError("stress_surface_mismatch", "different surface", "engine")

    monkeypatch.setattr(assemble, "apply_stress", mismatch)
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed_through"] == 9 and not report["passed"]
    failed = next(row for row in report["checks"] if row["status"] == "failed")
    assert failed["layer"] == "engine" and "stress_surface_mismatch" in failed["reason"]
    assert load_ledger(state / "lesson-1.regeneration.yaml", "sample-slug", 1)["terminal_layer"] == "engine"


def test_contract_fixture_marked_form_stops_at_check_7(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    words["words"][0]["forms"][0]["markers"] = ["arch"]
    words["words"][0]["forms"][0]["learner"] = False
    validate_fixture_words(words)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert bad["check"] == 7 and bad["layer"] == "writer" and bad["token"] == "слово"


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
    pack["errors"] = [
        {
            "id": "E-001",
            "source": {"table": "ua_gec_errors", "id": 1},
            "incorrect": "слове",
            "correct": "слово",
            "error_type": "form",
            "pattern": "fixture",
        }
    ]
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [
        {"id": "a1", "type": "error-correction", "placement": "inline", "focus": "Correct", "error_refs": ["E-001"]}
    ]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Correct",
            "items": [
                {
                    "sentence": "слове",
                    "error": "слове",
                    "correction": "слово",
                    "explanation": "Correct",
                    "error_ref": "E-001",
                }
            ],
        }
    ]
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
    assert ledger["regenerations"] == 0 and ledger["terminal_layer"] is None
    assert not receipt.exists()
    lock.write(receipt, b"old")
    third, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    ledger = load_ledger(state / "lesson-1.regeneration.yaml", "sample-slug", 1)
    assert third["checks"][2]["status"] == "failed"
    assert ledger["regenerations"] == 1 and ledger["terminal_layer"] == "plan"
    assert not receipt.exists()


def test_runner_form_choice_options_invalid_reports_check_4(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Choose",
            "items": [
                {
                    "sentence": "____",
                    "answer": "слово",
                    "options": ["слово", "invented"],
                    "explanation": "Choose",
                    "mode": "form-choice",
                    "record": "W-1",
                    "answer_tags": words["words"][0]["forms"][0]["tags"],
                }
            ],
        }
    ]
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
    draft["activities"] = [
        {"id": "a1", "instruction": "Read", "items": [{"statement": "слово", "correct": True, "explanation": "Read"}]}
    ]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["reason"], bad["layer"]) == (3, "true_false_before_text", "writer")


def test_runner_check_1_echo_hash_failure(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    report, _, _ = _run_contract(
        tmp_path, monkeypatch, draft, plan, pack, words, expected_inputs={"plan_sha256": "f" * 64}
    )
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
    monkeypatch.setattr(
        runner,
        "check_9_stress_and_render",
        lambda *a, **kw: assemble.CheckResult(check=9, passed=False, reason="fixture_render_error", layer="engine"),
    )
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["reason"], bad["layer"]) == (9, "fixture_render_error", "engine")


def test_inventory_failure_is_reported_as_check_7_after_answers(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture(two_senses=True)

    def gate(level, slug, n, stream, **kwargs):
        assert all(token["selected"] is not None for token in stream.open_tokens())
        assert any(token["unit"].get("step") == "s1" for token in stream.tokens)
        return GateReport(
            level,
            slug,
            n,
            (
                GateFailure(
                    "core_not_introduced", level, slug, n, "urok", "слово", "слово", "W-1", "fixture gate failure"
                ),
            ),
        )

    report, _, seen = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, inventory_gate=gate)
    assert seen
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["code"], bad["layer"]) == (7, "core_not_introduced", "writer")
    assert report["checks"][7]["status"] == "passed"


def test_form_choice_prints_store_spelling_and_state_is_byte_stable(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    form = {**words["words"][0]["forms"][0], "form": "слова", "stressed": "слова\u0301", "tags": "noun:inanim:n:v_rod"}
    words["words"][0]["forms"].append(form)
    plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["forms"].append(form["tags"])
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Choose",
            "items": [
                {
                    "sentence": "____",
                    "answer": "слово",
                    "options": ["слово", "слова"],
                    "explanation": "Choose",
                    "mode": "form-choice",
                    "record": "W-1",
                    "answer_tags": words["words"][0]["forms"][0]["tags"],
                }
            ],
        }
    ]
    validate_fixture_words(words)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    first, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert first["checks"][6]["code"] == "requires_receipt_missing"
    _confirm_fixture_form(state, draft["activities"][0]["items"][0])
    first, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert first["passed"] is True, first
    assert first["checks"][6]["details"]["requirement_receipts"] == [
        {"activity": "a1", "item": 0, "requirement": "confirmed"}
    ]
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    assert "сло\u0301во" in mdx and "слова\u0301" in mdx
    before = {
        name: (state / name).read_bytes()
        for name in (
            "lesson-1.expanded.yaml",
            "lesson-1.questions.yaml",
            "lesson-1.resolutions.yaml",
            "lesson-1.stressed.yaml",
            "lesson-1.gates.yaml",
        )
    }
    second, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert second == first
    assert {name: (state / name).read_bytes() for name in before} == before


def test_runner_keeps_owned_source_snapshot_through_choice_gate(tmp_path, monkeypatch):
    from scripts.curriculum.evidence.sources import SourceResult, Sources

    draft, plan, pack, words = _fixture()
    # Exercise the owned-session path rather than the injected source double.
    monkeypatch.setattr(sys.modules[__name__], "_FixtureSources", lambda: None)
    monkeypatch.setattr(
        Sources, "verify_words", lambda self, words: SourceResult({word: [] for word in words}, "f" * 64)
    )
    resolve = runner.resolve
    choices = runner.check_7_a1_choices
    captured = []

    def scoped_resolve(expanded, allowlist, sources, **kwargs):
        sources._db()
        captured.append(sources)
        return resolve(expanded, allowlist, sources, **kwargs)

    def scoped_choices(*args, **kwargs):
        assert kwargs["sources"] is captured[0]
        assert captured[0]._conn is not None
        return choices(*args, **kwargs)

    monkeypatch.setattr(runner, "resolve", scoped_resolve)
    monkeypatch.setattr(runner, "check_7_a1_choices", scoped_choices)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    assert len(captured) == 1 and captured[0]._conn is None


def test_runner_releases_owned_snapshot_on_resolver_failure(tmp_path, monkeypatch):
    from scripts.curriculum.evidence.sources import Sources

    draft, plan, pack, words = _fixture()
    monkeypatch.setattr(sys.modules[__name__], "_FixtureSources", lambda: None)
    captured = []

    def unavailable(expanded, allowlist, sources, **kwargs):
        sources._db()
        captured.append(sources)
        raise OSError("fixture source failure")

    monkeypatch.setattr(runner, "resolve", unavailable)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is False and report["passed_through"] == 7
    assert len(captured) == 1 and isinstance(captured[0], Sources) and captured[0]._conn is None


@pytest.mark.parametrize("dispatch_fails", [False, True])
def test_runner_releases_snapshot_before_dispatch_and_reopens_at_gate(tmp_path, monkeypatch, dispatch_fails):
    import sqlite3

    from scripts.curriculum.evidence.sources import SourceResult, Sources

    draft, plan, pack, words = _fixture(two_senses=True)
    monkeypatch.setattr(sys.modules[__name__], "_FixtureSources", lambda: None)
    monkeypatch.setattr(
        Sources, "verify_words", lambda self, words: SourceResult({word: [] for word in words}, "f" * 64)
    )
    captured = []
    original_resolve = runner.resolve
    original_choices = runner.check_7_a1_choices

    def resolve(expanded, allowlist, sources, **kwargs):
        old = sources._db()
        captured.append((sources, old))
        return original_resolve(expanded, allowlist, sources, **kwargs)

    def dispatch(batch, seat):
        sources, old = captured[0]
        assert sources._conn is None
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            old.execute("SELECT 1")
        if dispatch_fails:
            raise RuntimeError("fixture provider failure")
        with sqlite3.connect(sources.sources_db) as writer:
            writer.execute("INSERT INTO grinchenko (id, definition) VALUES (99, 'post-dispatch row')")
        return {"answers": [{"id": q["id"], "record": q["candidates"][0]["record"]} for q in batch["questions"]]}

    def choices(*args, **kwargs):
        sources, old = captured[0]
        assert kwargs["sources"] is sources and sources._conn is None
        assert sources._db() is not old
        assert (
            sources._db().execute("SELECT definition FROM grinchenko WHERE id=99").fetchone()[0] == "post-dispatch row"
        )
        return original_choices(*args, **kwargs)

    monkeypatch.setattr(runner, "resolve", resolve)
    monkeypatch.setattr(runner, "check_7_a1_choices", choices)
    report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, question_dispatch=dispatch)
    assert report["passed"] is not dispatch_fails, report
    assert captured[0][0]._conn is None


@pytest.mark.parametrize("kind", ["prose", "table"])
def test_standard_citation_is_required_and_plan_bound(kind):
    draft, plan, _, _ = _fixture()
    lesson = plan["lessons"][0]
    lesson["steps"][0]["evidence"].append("S-001")
    block = draft["steps"][0]["blocks"][0]
    block["explains"].append("S-001")
    if kind == "table":
        block.update(kind="table", rows=[[block.pop("text")]])
    assert runner.check_3_structure(draft, lesson)["status"] == "passed"
    block["explains"].remove("S-001")
    assert runner.check_3_structure(draft, lesson)["status"] == "failed"
    block["explains"].append("S-999")
    assert runner.check_3_structure(draft, lesson)["status"] == "failed"


def test_check_11_two_lesson_build_scopes_each_number_and_keeps_module_gate_strict(tmp_path, monkeypatch):
    from scripts.build import linear_pipeline, verify_shippable

    draft, plan, pack, words = _fixture()
    # A gap ensures the runner forwards the actual n, rather than a position.
    second = copy.deepcopy(plan["lessons"][0])
    second.update(n=3, slug="second-lesson", title="Second lesson")
    plan["lessons"].append(second)
    (tmp_path / "sample-slug.yaml").write_bytes(lock.yaml_bytes(plan))
    monkeypatch.setattr(verify_shippable, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(verify_shippable, "_astro_build", lambda p: True)
    monkeypatch.setattr(linear_pipeline, "run_mdx_render_gate", lambda t: {"passed": True})
    scopes = []

    def check(*args, **kwargs):
        scopes.append(kwargs["through_lesson"])
        return assemble.check_11_render(*args, **kwargs)

    first, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, render_check=check)
    assert first["passed"] is True, first
    assert next(row for row in first["checks"] if row["check"] == 11)["status"] == "passed"
    assert (tmp_path / "site/1.mdx").is_file()
    assert not (tmp_path / "site/3.mdx").exists()
    full = assemble.check_11_render(
        "a1", "sample-slug", module_dir=tmp_path / "site", plan_path=tmp_path / "sample-slug.yaml"
    )
    assert full.passed is False
    assert full.artifacts["verify_shippable"]["steps"][0]["missing_lesson_ids"] == [3]
    draft = copy.deepcopy(draft)
    draft["lesson"]["n"] = 3
    second_report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, n=3, render_check=check)
    assert second_report["passed"] is True, second_report
    assert scopes == [1, 3]
    assert (
        assemble.check_11_render(
            "a1", "sample-slug", module_dir=tmp_path / "site", plan_path=tmp_path / "sample-slug.yaml"
        ).passed
        is True
    )


def test_runner_missing_writer_sources_stops_at_shared_check_5(tmp_path, monkeypatch):
    fixture = _fixture()
    report, state, _ = _run_contract(tmp_path, monkeypatch, *fixture, sources_receipt=False)
    failed = next(row for row in report["checks"] if row["status"] == "failed")
    assert (failed["check"], failed["code"], failed["layer"]) == (5, "writer_sources_missing", "engine")
    assert failed["details"]["writer_sources"]["forms"]["missing"] > 0
    assert not (state / "lesson-1.expanded.yaml").exists()
