"""Held-out regressions for the five assembled-page defects in #9544."""

from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts.build import mdx_render_gate as gate
from scripts.build import verify_shippable as shippable
from scripts.build.fresh import assemble
from scripts.generate_mdx.converters import mdx_safe_text

FIXTURE = Path(__file__).parent / "fixtures/attempt5"


def reassemble_attempt5(data=None):
    """Use archived draft/record inputs, never a live archive path."""
    data = data if data is not None else json.loads((FIXTURE / "inputs.json").read_text())
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


@pytest.mark.site_toolchain
def test_attempt5_parse_failure_is_caught_despite_valid_islands():
    broken = (FIXTURE / "broken-1.mdx").read_text()
    assert gate.iter_template_literals(broken)
    # The previous gate's entire validation still passes this broken page.
    assert all(gate._node_eval_one(inner) is None for inner in gate.iter_template_literals(broken))
    result = gate.check_mdx_render(broken)
    assert result["passed"] is False and result["compiled"] is False
    assert any("Could not parse expression" in item["error"] for item in result["failures"])


@pytest.mark.site_toolchain
def test_attempt5_reassembled_page_has_learner_headings_and_no_placeholders():
    page, data = reassemble_attempt5()
    for activity in data["plan"]["lessons"][0]["activities"]:
        assert activity["focus"] not in html.unescape(page)
    assert data["plan"]["lessons"][0]["rationale"] not in page
    for activity in data["draft"]["activities"]:
        # These fixture components display the instruction prop, once.
        assert page.count(activity["instruction"]) == 1
    assert "{{gloss:" not in page and "{{uk:" not in page
    assert gate.check_mdx_render(page)["passed"] is True


@pytest.mark.site_toolchain
def test_text_encoding_preserves_learner_characters():
    text = '{ } < > ` $ ${x} & " \\ &#123; ' + "don't"
    encoded = mdx_safe_text(text)
    assert html.unescape(encoded) == text
    assert gate.check_mdx_render(encoded)["passed"] is True


@pytest.mark.parametrize("text", ["import this example", "export the words", "### Story\nRead | this."])
@pytest.mark.site_toolchain
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
            "src/content/docs/a1/fixture/1.mdx:123:51 Could not parse expression with acorn"
            if failure == "mdx"
            else "ModuleNotFoundError: dependency unavailable",
        )

    if failure == "missing_python":
        monkeypatch.setattr(shippable, "project_interpreter", lambda root: tmp_path / "absent")
    monkeypatch.setattr(shippable.subprocess, "run", run)
    report = shippable._astro_build_step(
        tmp_path / "build.log", fresh_pages=[shippable.PROJECT_ROOT / "site/src/content/docs/a1/fixture/1.mdx"]
    )
    assert report["passed"] is False
    assert report["layer"] == ("engine" if failure == "mdx" else "harness")


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


@pytest.mark.parametrize("source,exit_code", [("Learner text", 0), ("Text {kind: dialogue}", 1)])
@pytest.mark.site_toolchain
def test_gate_cli_reports_real_compilation(tmp_path, capsys, source, exit_code):
    page = tmp_path / "lesson.mdx"
    page.write_text(source)
    assert gate.main([str(page), "--json"]) == exit_code
    report = json.loads(capsys.readouterr().out)
    assert report["compiled"] is (exit_code == 0)


def test_attempt5_instructions_print_once_and_ids_stay_in_provenance():
    page, data = reassemble_attempt5()
    for activity in data["draft"]["activities"]:
        assert page.count(activity["instruction"]) == 1, activity["id"]
    assert not re.search(r"T-0\d+", page.split('label="Ресурси', 1)[1])
    # Quote-host ids in JSON props are metadata, not displayed learner text.
    # Resource ids still identify the evidence in the provenance document.
    _, provenance = assemble.assemble_expanded_document(
        *(data[k] for k in ("draft", "plan", "pack", "words")), "a1", "sounds-letters-and-hello", 1
    )
    assert {u["ref"] for u in provenance["spans"] if u.get("tab") == "resursy"} >= {"T-041", "T-040", "T-035"}


@pytest.mark.parametrize(
    "filename,layer",
    [
        ("src/content/docs/a1/fixture/1.mdx", "engine"),
        ("src/content/docs/a1/fixture/index.mdx", "engine"),
        ("src/content/docs/a1/other/1.mdx", "harness"),
        ("1.mdx", "harness"),
        (None, "harness"),
    ],
)
def test_site_compiler_errors_only_charge_owned_fresh_pages(tmp_path, monkeypatch, filename, layer):
    log = tmp_path / "build.log"
    log.write_text((f"{filename}:123:51 " if filename else "") + "MDXError: Could not parse expression with acorn")
    monkeypatch.setattr(shippable, "_astro_build", lambda _: False)
    report = shippable._astro_build_step(
        log,
        fresh_pages=[
            shippable.PROJECT_ROOT / f"site/src/content/docs/a1/fixture/{name}.mdx" for name in ("1", "index")
        ],
    )
    assert report["passed"] is False and report["layer"] == layer
    if filename and layer == "harness":
        assert filename in report["detail"]


@pytest.mark.parametrize("duplicate_title", [False, True])
def test_attempt5_duplicate_titles_do_not_repeat_instructions(duplicate_title):
    data = json.loads((FIXTURE / "inputs.json").read_text())
    for activity in data["draft"]["activities"]:
        activity["title"] = activity["instruction"] if duplicate_title else "Separate title"
    page, _ = reassemble_attempt5(data)
    for activity in data["draft"]["activities"]:
        assert page.count(activity["instruction"]) == 1
    if not duplicate_title:
        assert "Separate title" in page


@pytest.mark.site_toolchain
def test_all_resource_text_fields_use_the_same_mdx_encoder():
    from scripts.generate_mdx.resources import format_resources_for_mdx

    hostile = '{kind: dialogue} <b> ` $ & " \\'
    resources = [
        {
            "role": "textbook",
            "title": "Title " + hostile,
            "author": "Author " + hostile,
            "pages": "Page " + hostile,
            "description": "Description " + hostile,
        },
        {"role": "book", "source_ref": "Citation " + hostile},
        {
            "role": "video",
            "title": "Video " + hostile,
            "channel": "Channel " + hostile,
            "url": "https://example.com/video",
        },
    ]
    page = format_resources_for_mdx(resources)
    assert page.count(mdx_safe_text(hostile)) == 7
    assert gate.check_mdx_render(page)["passed"] is True


@pytest.mark.parametrize("role", ["book", "video"])
@pytest.mark.parametrize("url", ["javascript:probe", "data:text/plain,probe", "wiki/private.md", "https://", "https://example.com/a b", "https://[invalid", "//example.com/probe", "https://user:pass@example.com/probe"])
def test_rejected_resource_url_cannot_be_a_fallback_label(role, url):
    from scripts.generate_mdx.resources import format_resources_for_mdx

    page = format_resources_for_mdx([{"role": role, "url": url}], is_ukrainian_forced=True)
    assert url not in page
    assert "**—**" in page
