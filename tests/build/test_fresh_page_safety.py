"""Held-out regressions for the five assembled-page defects in #9544."""

from __future__ import annotations

import html
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts.build import mdx_render_gate as gate
from scripts.build import verify_shippable as shippable
from scripts.build.fresh import assemble
from scripts.build.fresh.regeneration import load_ledger, record_failure
from scripts.generate_mdx.converters import mdx_safe_text

FIXTURE = Path(__file__).parent / "fixtures/attempt5"


def reassemble_attempt5():
    """Use archived draft/record inputs, never a live archive path."""
    data = json.loads((FIXTURE / "inputs.json").read_text())
    draft, plan, pack, words = (data[k] for k in ("draft", "plan", "pack", "words"))
    expanded, provenance = assemble.assemble_expanded_document(
        draft, plan, pack, words, "a1", "sounds-letters-and-hello", 1
    )
    with (
        patch.object(assemble.lesson_lock, "check_lesson_lock", return_value=(True, "")),
        patch.object(
            assemble.lesson_lock,
            "compute_lesson_lock",
            return_value={"lessons": [{"n": 1, "entry_sha256": draft["inputs"]["lesson_lock_entry_sha256"]}]},
        ),
        patch.object(assemble, "planned_state", return_value=SimpleNamespace(waiver=None, cumulative_core_count=0)),
    ):
        result = assemble.check_9_stress_and_render(
            expanded,
            draft,
            plan,
            pack,
            words,
            data["stream"],
            "a1",
            "sounds-letters-and-hello",
            1,
            provenance_doc=provenance,
        )
    assert result.passed, result.to_dict()
    return result.artifacts["mdx"], data


def test_attempt5_parse_failure_is_caught_despite_valid_islands():
    broken = (FIXTURE / "broken-1.mdx").read_text()
    assert gate.iter_template_literals(broken)
    # The previous gate's entire validation still passes this broken page.
    assert all(gate._node_eval_one(inner) is None for inner in gate.iter_template_literals(broken))
    result = gate.check_mdx_render(broken)
    assert result["passed"] is False and result["compiled"] is False
    assert any("Could not parse expression" in item["error"] for item in result["failures"])


def test_attempt5_reassembled_page_has_learner_headings_and_no_placeholders():
    page, data = reassemble_attempt5()
    for activity in data["plan"]["lessons"][0]["activities"]:
        assert activity["focus"] not in html.unescape(page)
    assert data["plan"]["lessons"][0]["rationale"] not in page
    for activity in data["draft"]["activities"]:
        assert "### " + mdx_safe_text(activity["instruction"]) in page
    assert "{{gloss:" not in page and "{{uk:" not in page
    assert gate.check_mdx_render(page)["passed"] is True


@pytest.mark.parametrize("page", ["Text {kind: dialogue}", "<Bad>", "<A p={JSON.parse(`[1,2]"])
def test_whole_page_compile_rejects_syntax_without_valid_islands(page):
    report = gate.check_mdx_render(page)
    assert report["passed"] is False and report["compiled"] is False


def test_text_encoding_preserves_learner_characters():
    text = '{ } < > ` $ ${x} & " \\ &#123; ' + "don't"
    encoded = mdx_safe_text(text)
    assert html.unescape(encoded) == text
    assert gate.check_mdx_render(encoded)["passed"] is True


@pytest.mark.parametrize("text", ["import this example", "export the words", "### Story\nRead | this."])
def test_text_cannot_become_esm_or_a_story_heading(text):
    encoded = mdx_safe_text(text)
    assert html.unescape(encoded) == text
    assert not encoded.startswith(("import ", "export ", "###"))
    assert gate.check_mdx_render(encoded)["passed"] is True


def test_compile_toolchain_failure_cannot_pass(monkeypatch):
    monkeypatch.setattr(gate.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 1, "", ""))
    report = gate.check_mdx_render("Plain text")
    assert report["passed"] is False and report["layer"] == "harness"


def test_node_unavailable_is_skipped_not_compiled(monkeypatch):
    monkeypatch.setattr(gate.shutil, "which", lambda *a: None)
    report = gate.check_mdx_render("Plain text")
    assert report["passed"] is None and report["skipped"] is True
    assert report.get("compiled") is not True


def test_payload_expansion_visits_every_nested_string():
    payload = {
        "title": "{{uk:Title}}",
        "items": [{"word": "{{gloss:W-1}}", "note": "{{uk:Note}}", "options": ["{{gloss:W-1}}"]}],
    }
    result = assemble.expand_payload_text(
        payload, assemble.gloss_replacer({"words": [{"id": "W-1", "lemma": "word", "gloss_en": "gloss"}]})
    )
    assert result == {
        "title": "Title",
        "items": [{"word": "word (gloss)", "note": "Note", "options": ["word (gloss)"]}],
    }
    assert "{{" in json.dumps(payload)  # input remains immutable


def test_check9_rejects_missed_payload_placeholder(monkeypatch):
    original = assemble.expand_payload_text

    def leave_one(value, replace_gloss):
        result = original(value, replace_gloss)
        if isinstance(result, list) and result and isinstance(result[0], dict) and "instruction" in result[0]:
            result[0]["items"][0]["word"] = "{{gloss:W-074}}"
        return result

    monkeypatch.setattr(assemble, "expand_payload_text", leave_one)
    with pytest.raises(AssertionError, match="unexpanded_print_placeholder"):
        reassemble_attempt5()


def test_astro_build_passes_absolute_project_interpreter(tmp_path, monkeypatch):
    interpreter = tmp_path / "python"
    interpreter.write_text("#!/bin/sh\n")
    interpreter.chmod(0o755)
    monkeypatch.setattr(shippable, "project_interpreter", lambda root: interpreter)
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "build complete\n", "")

    monkeypatch.setattr(shippable.subprocess, "run", run)
    assert shippable._astro_build(tmp_path / "build.log") is True
    assert calls[0][1]["env"]["PYTHON"] == str(interpreter.absolute())
    assert calls[0][1]["env"].get("PATH") == os.environ.get("PATH")
    assert calls[0][1]["cwd"] == shippable.PROJECT_ROOT / "site"


@pytest.mark.parametrize("failure", ["missing_python", "missing_npm", "timeout", "hydration", "mdx"])
def test_build_failure_attribution(tmp_path, monkeypatch, failure):
    interpreter = tmp_path / "python"
    interpreter.write_text("#!/bin/sh\n")
    interpreter.chmod(0o755)
    monkeypatch.setattr(shippable, "project_interpreter", lambda root: interpreter)

    def run(argv, **kwargs):
        if failure == "missing_npm":
            raise FileNotFoundError("npm")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, 900)
        return subprocess.CompletedProcess(
            argv,
            1,
            "",
            "1.mdx:123:51 Could not parse expression with acorn"
            if failure == "mdx"
            else "ModuleNotFoundError: dependency unavailable",
        )

    if failure == "missing_python":
        monkeypatch.setattr(shippable, "project_interpreter", lambda root: tmp_path / "absent")
    monkeypatch.setattr(shippable.subprocess, "run", run)
    report = shippable._astro_build_step(tmp_path / "build.log")
    assert report["passed"] is False
    assert report["layer"] == ("engine" if failure == "mdx" else "harness")


def test_harness_failures_do_not_spend_a_regeneration(tmp_path):
    ledger = tmp_path / "lesson-1.regeneration.yaml"
    before = load_ledger(ledger, "sample", 1)
    for _ in range(3):
        record_failure(
            ledger, "sample", 1, {"check": 11, "layer": "harness", "reason": "build environment unavailable"}, {}
        )
    assert load_ledger(ledger, "sample", 1) == before
    assert not ledger.exists()
    assert (tmp_path / "lesson-1.writer-harness.yaml").is_file()


@pytest.mark.parametrize("passed,layer", [(False, "harness"), (None, "harness"), (False, "engine")])
def test_check11_propagates_the_environment_layer(monkeypatch, passed, layer):
    monkeypatch.setattr(
        shippable,
        "verify",
        lambda *a, **kw: {
            "shippable": False,
            "steps": [{"step": "mdx_render", "passed": passed, "layer": layer}],
        },
    )
    report = assemble.check_11_render("a1", "fixture")
    assert report.passed is False and report.layer == layer


def test_missing_page_fails_closed(tmp_path):
    report = gate.check_mdx_render_path(tmp_path / "absent.mdx")
    assert report["passed"] is False and "not found" in report["message"]


@pytest.mark.parametrize("source,exit_code", [("Learner text", 0), ("Text {kind: dialogue}", 1)])
def test_gate_cli_reports_real_compilation(tmp_path, capsys, source, exit_code):
    page = tmp_path / "lesson.mdx"
    page.write_text(source)
    assert gate.main([str(page), "--json"]) == exit_code
    report = json.loads(capsys.readouterr().out)
    assert report["compiled"] is (exit_code == 0)


def test_shippable_report_distinguishes_compilation_from_full_render(capsys):
    shippable._print_human(
        {"level": "a1", "slug": "fixture", "shippable": True, "render_fully_validated": False, "steps": []}
    )
    assert "page compilation and island checks only" in capsys.readouterr().out
