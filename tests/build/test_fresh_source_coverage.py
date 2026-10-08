"""#10107 deterministic transport/binding adversaries, with synthetic evidence.

The frozen AGY fixture is the held-out transport witness. Other payloads test
admission mechanics only; their synthetic analyses make no Ukrainian claim.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import assemble, runner, writer
from scripts.build.fresh import source_coverage as coverage
from scripts.curriculum.evidence import lock
from tests.build.test_fresh_runner import _fixture


def quiz_fixture(encoding):
    """Reuse the established source-backed form fixture, with each supported key spelling."""
    from tests.build.test_fresh_runner import _complete_a1_choice_fixture

    draft, plan, pack, words = _fixture()
    lesson = plan["lessons"][0]
    lesson["steps"][0]["practice"] = ["a1"]
    lesson["activities"] = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Choose"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    item = {"question": "слово", "options": ["слово", "слова"], "explanation": "Choose the form."}
    if encoding == "int":
        item["correct"] = 0
    elif encoding == "answer":
        item["answer"] = "слово"
    else:
        item["options"] = [{"text": "слово", "correct": True}, {"text": "слова", "correct": False}]
    draft["activities"] = [{"id": "a1", "instruction": "Choose", "items": [item]}]
    _complete_a1_choice_fixture(draft, plan, pack, words)
    return draft, plan, pack, words


@pytest.mark.parametrize("encoding", ["int", "answer", "dict"])
def test_cached_quiz_keeps_writer_bytes_bound_and_live_annotation_for_later_checks(tmp_path, monkeypatch, encoding):
    from tests.build.test_fresh_runner import _run_contract

    fixture = quiz_fixture(encoding)
    original = runner.run_lesson
    observed = {}

    def cached_run(*args, **kwargs):
        state = kwargs["state_dir"]
        # The production module caller also loads the persisted draft before running checks.
        path = state / "lesson-1.draft.yaml"
        observed["bytes"] = path.read_bytes()
        observed["receipt"] = (state / "lesson-1.writer_tool_calls.json").read_bytes()
        kwargs["draft"] = observed["live"] = yaml.safe_load(observed["bytes"])
        return original(*args, **kwargs)

    monkeypatch.setattr(runner, "run_lesson", cached_run)
    report, state, _ = _run_contract(tmp_path, monkeypatch, *fixture)
    row = next(row for row in report["checks"] if row["check"] == 5)
    assert row["status"] == "passed" and row["details"]["writer_sources"]["code"] is None
    # No requirement receipt was supplied: the live key still reaches the later form gate.
    failed = next(row for row in report["checks"] if row["status"] == "failed")
    assert (failed["check"], failed["code"]) == (7, "requires_receipt_missing")
    assert observed["live"]["activities"][0]["items"][0]["_resolved_key_index"] == 0
    assert (state / "lesson-1.draft.yaml").read_bytes() == observed["bytes"]
    assert (state / "lesson-1.writer_tool_calls.json").read_bytes() == observed["receipt"]
    assert json.loads(observed["receipt"])["draft_sha256"] == hashlib.sha256(observed["bytes"]).hexdigest()


@pytest.mark.parametrize("encoding", ["int", "answer", "dict"])
def test_writer_and_annotated_quiz_expansion_and_provenance_are_byte_identical(encoding):
    fixture = quiz_fixture(encoding)
    draft, plan, pack, words = fixture
    annotated = copy.deepcopy(draft)
    row, _ = runner.check_4_activities(annotated, plan["lessons"][0], words, pack, level="a1")
    assert row["status"] == "passed"
    assert annotated["activities"][0]["items"][0]["_resolved_key_index"] == 0
    before = assemble.assemble_expanded_document(*fixture, "a1", "sample-slug", 1)
    after = assemble.assemble_expanded_document(annotated, plan, pack, words, "a1", "sample-slug", 1)
    assert tuple(map(lock.yaml_bytes, before)) == tuple(map(lock.yaml_bytes, after))
    assert "_resolved_key_index" not in draft["activities"][0]["items"][0]


@pytest.mark.parametrize("entry", ["check5", "standalone"])
def test_internal_quiz_annotation_cannot_enter_exact_writer_binding(tmp_path, monkeypatch, entry):
    draft, plan, pack, words = quiz_fixture("int")
    state = tmp_path / "state"
    seal_writer(state, monkeypatch, draft, plan, pack, words)
    persisted = (state / "lesson-1.draft.yaml").read_bytes()
    if entry == "check5":
        row, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack, level="a1")
        assert row["status"] == "passed"
        result = assemble.check_5_assembly(draft, plan, pack, words, "a1", "sample-slug", 1, output_dir=state)
        assert not result.passed and result.reason == "writer_sources_binding_mismatch"
    else:
        # A forged key at a distractor must not steer standalone provenance.
        draft["activities"][0]["items"][0]["_resolved_key_index"] = 1
        result = assemble.assemble_lesson(
            "a1", "sample-slug", 1, draft_dict=draft, plan_dict=plan, pack_dict=pack,
            words_dict=words, output_dir=state, repo_root=tmp_path,
        )
        assert result["failure"]["reason"] == "writer_sources_binding_mismatch"
    assert (state / "lesson-1.draft.yaml").read_bytes() == persisted
    assert not (state / "lesson-1.expanded.yaml").exists()
    assert not (state / "lesson-1.provenance.yaml").exists()


def test_writer_reply_and_runner_schema_refuse_internal_quiz_annotation(tmp_path, monkeypatch):
    from tests.build.test_fresh_runner import _run_contract

    fixture = quiz_fixture("int")
    draft, plan, _pack, _words = fixture
    types = {activity["id"]: activity["type"] for activity in plan["lessons"][0]["activities"]}
    assert writer.parse_and_validate_reply(yaml.safe_dump(draft), "a1", plan_activity_types=types) == draft
    draft["activities"][0]["items"][0]["_resolved_key_index"] = 1
    with pytest.raises(writer.DraftValidationError, match="_resolved_key_index"):
        writer.parse_and_validate_reply(yaml.safe_dump(draft), "a1", plan_activity_types=types)
    report, state, _ = _run_contract(tmp_path, monkeypatch, *fixture)
    assert report["passed_through"] == 1 and "_resolved_key_index" in report["checks"][0]["reason"]
    assert not (state / "lesson-1.expanded.yaml").exists()


def call(tool, arguments, result, **flags):
    return {
        "name": coverage.PREFIX + tool,
        "arguments": arguments,
        "result": result,
        "paired": True,
        "is_error": False,
        **flags,
    }


def verification(forms, *, missing=()):
    """Server-shaped synthetic analyses, never a linguistic oracle."""
    forms = list(forms)
    matches = {form: ([] if form in missing else [{"lemma": form, "pos": "synthetic"}]) for form in forms}
    found = sum(bool(rows) for rows in matches.values())
    return call(
        "verify_words",
        {"words": forms},
        {
            "schema": "sources.tool-result.v1",
            "tool": "verify_words",
            "status": "ok" if found else "empty",
            "disposition": "supported" if found == len(forms) else "partial",
            "success": found == len(forms),
            "query": {"words": forms},
            "result": {"words": forms, "matches": matches},
        },
    )


def search(tool, key, value, *, query="synthetic query"):
    return call(
        tool,
        {"query": query},
        {
            "schema": "sources.tool-result.v1",
            "tool": tool,
            "status": "ok",
            "query": {"query": query},
            "hits": [{key: value}],
        },
    )


def seal_writer(state, monkeypatch, draft, plan, pack, words, *, calls=None, expected_inputs=None, n=1):
    """Explicit fake-seat receipt through the production harvester; no gate bypass."""
    state.mkdir(parents=True, exist_ok=True)
    tasks = state / "tasks"
    tasks.mkdir(exist_ok=True)
    monkeypatch.setattr(coverage, "tasks_dir", lambda: tasks)
    level, slug = draft["lesson"]["module"].split("/")
    prompt = b"Synthetic writer prompt for admission mechanics.\n"
    prompt_hash = hashlib.sha256(prompt).hexdigest()
    inputs = {
        "plan_sha256": hashlib.sha256(lock.yaml_bytes(plan)).hexdigest(),
        "pack_lock": hashlib.sha256(lock.yaml_bytes(pack)).hexdigest(),
        "words_lock": hashlib.sha256(lock.yaml_bytes(words)).hexdigest(),
        "card_sha256": draft["inputs"]["style_card_sha256"],
        "prompt_sha256": prompt_hash,
    }
    if expected_inputs:
        for key in inputs:
            expected_key = "style_card_sha256" if key == "card_sha256" else key
            if expected_key in expected_inputs:
                inputs[key] = expected_inputs[expected_key]
    if not expected_inputs:
        for key in ("plan_sha256", "pack_lock", "words_lock"):
            draft["inputs"][key] = inputs[key]
    if calls is None:
        forms, evidence, _, _ = coverage.obligations(draft, plan, pack, words, level, slug, n)
        evidence_keys = {
            key for identity in evidence.values() for key in ([identity] if isinstance(identity, str) else identity)
        }
        verified = sorted(forms | {key[5:] for key in evidence_keys if key.startswith("form:")})
        calls = [verification(verified[offset : offset + 50]) for offset in range(0, len(verified), 50)]
        for key in sorted(evidence_keys):
            kind, value = key.split(":", 1)
            if kind == "chunk":
                calls.append(search("search_text", "chunk_id", value))
            elif kind == "error":
                calls.append(search("search_ua_gec_errors", "id", value))
            elif kind == "style":
                calls.append(search("search_style_guide", "id", value))
            elif kind == "url":
                calls.append(search("search_resources", "url", value))
    task_id = "synthetic-writer-1"
    sidecar = tasks / f"{task_id}.tool_calls.json"
    sidecar.write_text(json.dumps({"tool_calls": calls}, ensure_ascii=False))
    task = {
        "task_id": task_id,
        "status": "done",
        "agent": "codex",
        "model": "synthetic-model",
        "effort": "high",
        "prompt_sha256": inputs["prompt_sha256"],
        "tool_calls_file": str(sidecar),
        "tool_calls_sha256": hashlib.sha256(sidecar.read_bytes()).hexdigest(),
    }
    (tasks / f"{task_id}.json").write_text(json.dumps(task))
    meta = {
        "task_id": task_id,
        "attempt": 1,
        "writer": "codex",
        "model": task["model"],
        "effort": "high",
        "prompt_sha256": task["prompt_sha256"],
    }
    (state / f"lesson-{n}.prompt.md").write_bytes(prompt)
    (state / f"lesson-{n}.writer.yaml").write_text(yaml.safe_dump(meta))
    draft_file = state / f"lesson-{n}.draft.yaml"
    draft_file.write_bytes(lock.yaml_bytes(draft))
    coverage.harvest_receipt(
        state, n, level=level, slug=slug, inputs=inputs, meta=meta, task=task, draft_file=draft_file
    )
    return task, inputs


def check(state, fixture, **kwargs):
    return coverage.check_coverage(*fixture, "a1", "sample-slug", 1, state_dir=state, **kwargs)


@pytest.mark.parametrize(
    "change", ["unpaired", "error", "no_error_flag", "empty", "wrong_tool", "wrong_query", "truncated", "invalid_input"]
)
def test_noncreditable_results(change):
    sample = verification(["synthetic-form"])
    if change == "unpaired":
        sample["paired"] = False
    elif change == "error":
        sample["is_error"] = True
    elif change == "no_error_flag":
        sample.pop("is_error")
    elif change == "empty":
        sample["result"]["status"] = "empty"
    elif change == "wrong_tool":
        sample["result"]["tool"] = "search_text"
    elif change == "wrong_query":
        sample["result"]["query"]["words"] = ["unrelated"]
    elif change == "truncated":
        sample["arguments"]["words"].append({"_truncated_items": 1})
    else:
        sample["result"]["disposition"] = "invalid_input"
    assert coverage.credited_keys(sample) == set()


def test_partial_batch_credits_only_analysed_items():
    sample = verification(["one", "two", "three", "missing"], missing={"missing"})
    assert coverage.credited_keys(sample) == {"form:one", "form:two", "form:three"}
    assert coverage.credited_keys(verification([])) == set()


@pytest.mark.parametrize(
    "tool,key,prefix",
    [
        ("search_text", "chunk_id", "chunk:"),
        ("search_literary", "chunk_id", "chunk:"),
        ("search_style_guide", "id", "style:"),
        ("search_ua_gec_errors", "id", "error:"),
        ("search_resources", "url", "url:"),
    ],
)
def test_exact_structured_identities(tool, key, prefix):
    value = "https://example.org/resource" if tool == "search_resources" else "123"
    sample = search(tool, key, value)
    assert coverage.credited_keys(sample) == {prefix + value}
    sample["result"]["hits"] = [{"text": "123", "match_count": 99}]
    assert coverage.credited_keys(sample) == set()


def test_frozen_agy_held_out_is_unchanged_and_credit_is_result_derived():
    from scripts.agent_runtime.adapters.agy import _pair_transcript_generic_results

    fixture = Path("tests/fixtures/agy/generic_results_transcript.jsonl")
    raw = fixture.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    calls = _pair_transcript_generic_results(events, transcript_path=fixture)
    assert len(calls) == 4
    assert coverage.credited_keys(calls[1]) == {"form:" + form for form in calls[1]["arguments"]["words"]}
    assert len(coverage.credited_keys(calls[1])) == 3
    assert calls[2]["is_error"] is True
    assert all(not coverage.credited_keys(calls[i]) for i in (0, 2, 3))
    assert not any("BUILTIN" in json.dumps(item) for item in calls)
    assert fixture.read_bytes() == raw


def test_full_coverage_passes_and_metadata_has_no_raw_bodies(tmp_path, monkeypatch):
    fixture = _fixture()
    state = tmp_path / "state"
    task, _ = seal_writer(state, monkeypatch, *fixture)
    result = check(state, fixture)
    assert result["code"] is None
    assert result["forms"]["missing"] == result["evidence"]["missing"] == 0
    raw = (state / "lesson-1.writer_tool_calls.json").read_text()
    assert "synthetic query" not in raw and "synthetic-form" not in raw
    assert "matches" not in raw and "arguments" not in raw and "hits" not in raw
    assert task["tool_calls_file"] not in raw
    assembled = assemble.check_5_assembly(*fixture, "a1", "sample-slug", 1, output_dir=state)
    assert assembled.passed and (state / "lesson-1.expanded.yaml").is_file()


@pytest.mark.parametrize(
    "change",
    [
        "prompt",
        "draft",
        "injected",
        "input",
        "attempt",
        "model",
        "sidecar",
        "receipt_digest",
        "forged_credits",
        "lesson",
    ],
)
def test_stale_cache_and_binding_forgery_block_assembly(tmp_path, monkeypatch, change):
    fixture = _fixture()
    state = tmp_path / "state"
    task, _ = seal_writer(state, monkeypatch, *fixture)
    receipt_path = state / "lesson-1.writer_tool_calls.json"
    receipt = json.loads(receipt_path.read_text())
    expected = None
    if change == "prompt":
        (state / "lesson-1.prompt.md").write_text("changed prompt")
    elif change == "draft":
        (state / "lesson-1.draft.yaml").write_bytes(lock.yaml_bytes(fixture[0]) + b"\n")
    elif change == "injected":
        fixture[0]["steps"][0]["lead_in"] = "Injected learner text"
    elif change == "input":
        expected = {"pack_lock": "f" * 64}
    elif change == "attempt":
        receipt["attempt"] += 1
    elif change == "model":
        receipt["model"] = "unrelated-model"
    elif change == "sidecar":
        Path(task["tool_calls_file"]).write_text("[]")
    elif change == "receipt_digest":
        receipt["sidecar_sha256"] = "f" * 64
    elif change == "forged_credits":
        receipt["credited_calls"] = []
    else:
        receipt["lesson"]["n"] = 2
    receipt_path.write_text(json.dumps(receipt))
    result = assemble.check_5_assembly(*fixture, "a1", "sample-slug", 1, output_dir=state, expected_inputs=expected)
    assert not result.passed and result.reason == "writer_sources_binding_mismatch"
    assert not (state / "lesson-1.expanded.yaml").exists()


def test_missing_and_partial_coverage_and_standalone_cannot_bypass(tmp_path, monkeypatch):
    fixture = _fixture()
    state = tmp_path / "state"
    assert check(state, fixture)["code"] == "writer_sources_missing"
    seal_writer(state, monkeypatch, *fixture, calls=[])
    assert check(state, fixture)["code"] == "writer_sources_capture_incomplete"
    forms, _, _, _ = coverage.obligations(*fixture, "a1", "sample-slug", 1)
    seal_writer(state, monkeypatch, *fixture, calls=[verification(sorted(forms), missing=forms)])
    assert check(state, fixture)["code"] == "writer_sources_forms_uncovered"
    from tests.build.test_fresh_assemble import make_text_record

    fixture[2]["texts"] = [make_text_record(1, "synthetic witness")]
    fixture[1]["lessons"][0]["steps"][0]["evidence"].append("T-1")
    seal_writer(state, monkeypatch, *fixture, calls=[verification(sorted(forms))])
    assert check(state, fixture)["code"] == "writer_sources_evidence_uncovered"
    result = assemble.assemble_lesson(
        "a1",
        "sample-slug",
        1,
        draft_dict=fixture[0],
        plan_dict=fixture[1],
        pack_dict=fixture[2],
        words_dict=fixture[3],
        output_dir=tmp_path / "standalone",
        repo_root=tmp_path,
    )
    assert result["failure"]["reason"] == "writer_sources_missing"


def test_malformed_receipt_and_error_channel_never_credit(tmp_path, monkeypatch):
    fixture = _fixture()
    state = tmp_path / "state"
    seal_writer(state, monkeypatch, *fixture)
    receipt = state / "lesson-1.writer_tool_calls.json"
    receipt.write_text("{}")
    assert check(state, fixture)["code"] == "writer_sources_binding_mismatch"
    sample = verification(["synthetic-form"])
    sample["result"] = {"isError": True, "structured_content": sample["result"]}
    assert coverage.credited_keys(sample) == set()


def test_zero_obligations_still_require_an_actual_successful_sources_result(tmp_path, monkeypatch):
    fixture = _fixture()
    fixture[1]["lessons"] = [{"n": 1}]
    sample = search("search_text", "chunk_id", "chunk-1")
    sample["is_error"] = True
    state = tmp_path / "state"
    seal_writer(state, monkeypatch, *fixture, calls=[sample])
    summary = check(state, fixture, provenance={"spans": []})
    assert summary["forms"]["required"] == summary["evidence"]["required"] == 0
    assert summary["noncredited_calls"] == 1 and summary["code"] == "writer_sources_capture_incomplete"
    sample["is_error"] = False
    seal_writer(state, monkeypatch, *fixture, calls=[sample])
    assert check(state, fixture, provenance={"spans": []})["code"] is None


@pytest.mark.parametrize(
    "tool,text,arguments,expected",
    [
        (
            "verify_words",
            "3 analyses (3 distinct lemmas)\n\nBatch verification: 3 words\n\nFound: 2/3\n\n"
            "- **one** — FOUND (1 analysis (1 distinct lemma)): one(synthetic)\n"
            "- **two** — FOUND (1 analysis (1 distinct lemma)): two(synthetic)\n- **missing** — NOT FOUND",
            {"words": ["one", "two", "missing"]},
            {"form:one", "form:two"},
        ),
        (
            "verify_word",
            "1 analysis (1 distinct lemma)\n\n'synthetic' — matches in VESUM:\n\n"
            "- **lemma**: synthetic  |  **pos**: synthetic  |  **tags**: `synthetic`  |  **is_archaic**: False",
            {"word": "synthetic"},
            {"form:synthetic"},
        ),
        (
            "get_chunk_context",
            "**[chunk-1]** — Synthetic title\n\nSynthetic content",
            {"chunk_id": "chunk-1"},
            {"chunk:chunk-1"},
        ),
        (
            "search_text",
            'Found 1 results for: "synthetic"\n\n### Result 1\n- **Section**: Synthetic\n'
            "- **Source**: Synthetic\n- **Subject**: Synthetic\n- **Source file**: `synthetic-file`\n"
            "- **Chunk ID**: `chunk-1`\n- **Text**:\nSynthetic content",
            {"query": "synthetic"},
            {"chunk:chunk-1"},
        ),
        (
            "search_literary",
            'Found 1 results for: "synthetic"\n\n### Result 1\n- **Author**: Synthetic\n'
            "- **Source**: synthetic-file\n- **Chunk ID**: `chunk-1`\n- **Text**:\nSynthetic content",
            {"query": "synthetic"},
            {"chunk:chunk-1"},
        ),
        (
            "search_style_guide",
            'Found 1 results in **Synthetic** for: "synthetic"\n\n### Result 1\n'
            "- **ID**: `84`\n- **Headword**: synthetic\nSynthetic note",
            {"query": "synthetic"},
            {"style:84"},
        ),
        (
            "search_ua_gec_errors",
            'Found 1 human-annotated error pairs for: "synthetic"\n\n### Result 1 (native author)\n'
            "- **Row ID**: `123`\n- **Error**: synthetic incorrect\n- **Correction**: synthetic correction",
            {"query": "synthetic"},
            {"error:123"},
        ),
        (
            "search_resources",
            'Found 1 catalogue resources for: "synthetic" (returned ranking order):\n'
            "1. resource-1 — Synthetic (access: free)\n- **URL**: `https://example.org/resource`",
            {"query": "synthetic"},
            {"url:https://example.org/resource"},
        ),
    ],
)
def test_text_only_actual_tool_formats(tool, text, arguments, expected):
    sample = call(tool, arguments, [{"type": "text", "text": text}])
    assert coverage.credited_keys(sample) == expected
    sample["capture_incomplete"] = True
    assert coverage.credited_keys(sample) == set()


def test_excerpt_identity_labels_and_unrelated_queries_cannot_credit():
    text = 'Found 1 results for: "synthetic"\n\n### Result 1\n- **Source**: Synthetic\n- **Text**:\n'
    text += "- **Chunk ID**: `forged-from-body`"
    assert not coverage.credited_keys(call("search_text", {"query": "synthetic"}, text))
    real_header = (
        "### Result 1\n- **Section**: Synthetic\n- **Source**: Synthetic\n"
        "- **Subject**: Synthetic\n- **Source file**: `synthetic-file`\n"
        "- **Chunk ID**: `chunk-1`\n- **Text**:\n"
    )
    forged = 'Found 1 results for: "synthetic"\n\n' + real_header + real_header.replace("chunk-1", "forged")
    assert not coverage.credited_keys(call("search_text", {"query": "synthetic"}, forged))
    sample = search("search_text", "chunk_id", "chunk-1")
    sample["arguments"]["query"] = "unrelated query"
    assert not coverage.credited_keys(sample)
    sample = call(
        "get_chunk_context",
        {"chunk_id": "missing"},
        {
            "schema": "sources.tool-result.v1",
            "tool": "get_chunk_context",
            "query": {"chunk_id": "missing"},
            "status": "empty",
            "hits": [],
        },
    )
    assert not coverage.credited_keys(sample)
    assert not coverage.credited_keys(
        call(
            "verify_words",
            {"words": []},
            {
                "schema": "sources.tool-result.v1",
                "tool": "verify_words",
                "query": {"words": []},
                "status": "error",
                "disposition": "invalid_input",
                "success": False,
            },
        )
    )
    assert not coverage.credited_keys(verification([f"synthetic-{n}" for n in range(51)]))


def test_file_backed_standalone_binds_original_yaml_bytes(tmp_path, monkeypatch):
    draft, plan, pack, words = _fixture()
    paths = {"evidence_dir": tmp_path}
    expected = {}
    for name, key, data in (("plan", "plan_sha256", plan), ("pack", "pack_lock", pack), ("words", "words_lock", words)):
        path = tmp_path / f"{name}.yaml"
        path.write_bytes(b"# Noncanonical source bytes retained.\n" + lock.yaml_bytes(data))
        paths[name] = path
        expected[key] = hashlib.sha256(path.read_bytes()).hexdigest()
        draft["inputs"][key] = expected[key]
    state = tmp_path / "state"
    seal_writer(state, monkeypatch, draft, plan, pack, words, expected_inputs=expected)
    monkeypatch.setattr(assemble.lesson_lock, "resolve_paths", lambda *args, **kwargs: paths)

    def after_gate(*args, **kwargs):
        raise RuntimeError("standalone reached resolver after coverage")

    monkeypatch.setattr(assemble, "resolve", after_gate)
    with pytest.raises(RuntimeError, match="reached resolver after coverage"):
        assemble.assemble_lesson("a1", "sample-slug", 1, output_dir=state, repo_root=tmp_path)
    assert (state / "lesson-1.expanded.yaml").is_file()


def test_structured_single_form_and_context_identity():
    sample = call(
        "verify_word",
        {"word": "synthetic"},
        {
            "schema": "sources.tool-result.v1",
            "tool": "verify_word",
            "query": {"word": "synthetic"},
            "status": "ok",
            "disposition": "supported",
            "success": True,
            "result": {"word": "synthetic", "matches": [{"lemma": "synthetic", "pos": "synthetic"}]},
        },
    )
    assert coverage.credited_keys(sample) == {"form:synthetic"}
    sample["result"] = {"isError": False, "structured_content": sample["result"]}
    assert coverage.credited_keys(sample) == {"form:synthetic"}
    sample["result"] = [{"type": "text", "text": json.dumps(sample["result"]["structured_content"])}]
    assert coverage.credited_keys(sample) == {"form:synthetic"}
    sample = call(
        "get_chunk_context",
        {"chunk_id": "chunk-1"},
        {
            "schema": "sources.tool-result.v1",
            "tool": "get_chunk_context",
            "status": "ok",
            "query": {"chunk_id": "chunk-1"},
            "hits": [{"chunk_id": "chunk-1"}],
        },
    )
    assert coverage.credited_keys(sample) == {"chunk:chunk-1"}
    sample["result"]["hits"][0]["chunk_id"] = "unrelated"
    assert not coverage.credited_keys(sample)


def test_pinned_standard_report_only_and_engine_expansions(tmp_path, monkeypatch):
    from scripts.curriculum.evidence.sources import Sources

    fixture = _fixture()
    _draft, plan, pack, _words = fixture
    pack["standard"] = [{"id": "S-1", "lines": "1-2", "text": "synthetic standard", "file_sha256": "a" * 64}]
    pack["unsupported"] = [{"id": "U-1"}]
    plan["lessons"][0]["steps"][0]["evidence"].extend(["S-1", "U-1"])
    monkeypatch.setattr(Sources, "get_standard_lines", lambda self, start, end: ("synthetic standard", "a" * 64))
    forms, _, pinned, report_only = coverage.obligations(*fixture, "a1", "sample-slug", 1)
    assert report_only == {"U-1"}
    assert pinned["S-1"]["file_sha256"] == "a" * 64 and pinned["S-1"]["lines"] == "1-2"
    assert len(forms) == 1
    monkeypatch.setattr(Sources, "get_standard_lines", lambda self, start, end: ("changed standard", "b" * 64))
    _, evidence, pinned, _ = coverage.obligations(*fixture, "a1", "sample-slug", 1)
    assert "S-1" in evidence and not pinned


def test_runner_and_module_summary_schema_carry_counts_and_pins():
    from jsonschema import Draft202012Validator

    summary = coverage.coverage_summary(
        {"one", "missing"}, {"T-1": "chunk:1"}, {"form:one"}, code="writer_sources_evidence_uncovered", noncredited=2
    )
    schema = json.loads(Path("schemas/module-build-report-v1.schema.json").read_text())
    row = {
        "n": 1,
        "passed": False,
        "passed_through": 5,
        "manifest_sha256": None,
        "stopping_check": 5,
        "reason": "writer_sources_evidence_uncovered",
        "regenerations": 0,
        "terminal_layer": "engine",
        "layer": "engine",
        "writer_sources": summary,
    }
    Draft202012Validator(schema).validate({"level": "a1", "slug": "synthetic", "complete": False, "lessons": [row]})
    assert summary["forms"]["required"] == 2 and summary["forms"]["covered"] == 1
    assert summary["evidence"]["missing"] == 1 and summary["noncredited_calls"] == 2


@pytest.mark.parametrize("draft_exists", [False, True])
def test_stopped_module_reports_cited_obligations_without_a_valid_draft(tmp_path, monkeypatch, draft_exists):
    from scripts.build.fresh import cli, module
    from tests.build.test_fresh_assemble import make_text_record

    _, plan, pack, words = _fixture()
    pack["texts"] = [make_text_record(1, "synthetic witness")]
    plan["lessons"][0]["steps"][0]["evidence"].append("T-1")
    state_parent = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state"
    state = state_parent / "sample-slug"
    state.mkdir(parents=True)
    if draft_exists:
        (state / "lesson-1.draft.yaml").write_text("{}")
    monkeypatch.setattr(
        cli,
        "_load_lesson_data",
        lambda *args, **kwargs: (
            plan,
            plan["lessons"][0],
            pack,
            words,
            {"state_dir": state_parent, "plan": tmp_path / "plan.yaml"},
        ),
    )

    def stop(*args, **kwargs):
        raise ValueError("synthetic pre-writer stop")

    monkeypatch.setattr(module, "planned_state", stop)
    report = module.build_module("a1", "sample-slug", repo_root=tmp_path)
    row = report["lessons"][0]
    summary = row["writer_sources"]
    assert not report["complete"] and row["stopping_check"] == 0
    assert summary["code"] == "writer_sources_missing"
    assert summary["evidence"]["required"] >= 2
    assert summary["evidence"]["missing"] == summary["evidence"]["required"]
    assert summary["forms"]["required"] == summary["forms"]["covered"] == 0
    assert (state / "module.build.yaml").is_file()


def test_resource_aliases_use_existing_catalogue_canonicalization():
    sample = search("search_resources", "url", "https://youtu.be/synthetic-video?utm_source=fixture")
    assert coverage.credited_keys(sample) == {"url:https://www.youtube.com/watch?v=synthetic-video"}
    sample["result"]["hits"][0]["url"] = "https://user:credential@example.org/"
    assert not coverage.credited_keys(sample)


def test_formula_w_record_requires_all_component_form_results():
    draft, plan, pack, words = _fixture()
    words["words"][0] = {
        "id": "W-1",
        "kind": "formula",
        "text": "synthetic-first synthetic-second",
        "parts": [{"word": "W-2", "form": "synthetic-first"}, {"word": "W-3", "form": "synthetic-second"}],
    }
    _, evidence, _, _ = coverage.obligations(draft, plan, pack, words, "a1", "sample-slug", 1, provenance={"spans": []})
    partial = coverage.credited_keys(verification(["synthetic-first"]))
    assert not coverage._evidence_covered(evidence["W-1"], partial)
    assert not coverage._evidence_covered(frozenset(), partial)
    summary = coverage.coverage_summary(set(), evidence, partial, code="writer_sources_evidence_uncovered")
    assert summary["evidence"]["missing"] == 1
    complete = partial | coverage.credited_keys(verification(["synthetic-second"]))
    assert coverage.coverage_summary(set(), evidence, complete, code=None)["evidence"]["covered"] == 1
