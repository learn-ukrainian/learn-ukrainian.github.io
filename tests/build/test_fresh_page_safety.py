"""Held-out regressions for the five assembled-page defects in #9544."""

from __future__ import annotations

import copy
import html
import json
import os
import re
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


@pytest.mark.parametrize("page", ["Text {kind: dialogue}", "<Bad>", "<A p={JSON.parse(`[1,2]"])
@pytest.mark.site_toolchain
def test_whole_page_compile_rejects_syntax_without_valid_islands(page):
    report = gate.check_mdx_render(page)
    assert report["passed"] is False and report["compiled"] is False


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
@pytest.mark.site_toolchain
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


# Author-only prose from fresh-build-plan-schema.md §§2, 2a and 4. Titles,
# subtitles, learner outcome (job) and speaker names are learner-facing metadata.
PLAN_GUIDANCE_FIELDS = (
    "focus",
    "rationale",
    "use",
    "objectives",
    "connects_to",
    "prerequisites",
    "changelog",
    "register",
    "teach",
    "point",
    "situation",
    "setting",
    "target_grammar",
    "role",
)


@pytest.mark.parametrize("field", PLAN_GUIDANCE_FIELDS)
def test_no_plan_authoring_field_reaches_a_page(field):
    data = json.loads((FIXTURE / "inputs.json").read_text())
    marker = f"AUTHOR_ONLY_{field} {{kind: dialogue}} <b>"

    def replace_leaves(value):
        if isinstance(value, dict):
            return {key: replace_leaves(child) for key, child in value.items()}
        if isinstance(value, list):
            return [replace_leaves(child) for child in value]
        return marker if isinstance(value, str) else value

    def inject(value):
        if isinstance(value, dict):
            return {key: replace_leaves(child) if key == field else inject(child) for key, child in value.items()}
        if isinstance(value, list):
            return [inject(child) for child in value]
        return value

    data["plan"] = inject(data["plan"])
    # Exercise top-level guidance even where the archived plan omits the field.
    data["plan"][field] = marker
    before = copy.deepcopy(data)
    page, _ = reassemble_attempt5(data)
    assert f"AUTHOR_ONLY_{field}" not in html.unescape(page)
    assert data == before


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


@pytest.mark.site_toolchain
def test_hostile_pack_resource_metadata_compiles(monkeypatch):
    data = json.loads((FIXTURE / "inputs.json").read_text())
    hostile = ' {kind: dialogue} <b> ` $ & " \\'
    for video in data["pack"]["videos"]:
        video["title"] = "Video title" + hostile
        video["channel"] += hostile
        video["use"] = "PACK_AUTHOR_ONLY" + hostile
    original = assemble.publication.resource_citation

    def citation(record):
        entry = original(record)
        return {**entry, "title": entry["title"] + hostile, "description": "Credit" + hostile} if entry else entry

    monkeypatch.setattr(assemble.publication, "resource_citation", citation)
    page, _ = reassemble_attempt5(data)
    resources = page.split('label="Ресурси', 1)[1]
    assert mdx_safe_text("Video title" + hostile) in resources
    assert mdx_safe_text("Credit" + hostile) in resources
    assert "PACK_AUTHOR_ONLY" not in page
    assert gate.check_mdx_render(page)["passed"] is True


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


@pytest.mark.repo_wide
def test_ci_runs_site_toolchain_tests_in_required_frontend_job():
    import yaml

    root = Path(__file__).resolve().parents[2]
    jobs = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())["jobs"]
    steps = {step.get("name"): step for step in jobs["frontend"]["steps"]}
    compiler = steps["Real MDX compiler regressions"]
    assert "if" not in compiler
    assert "-m site_toolchain --strict-markers" in compiler["run"]
    assert "not site_toolchain" in next(s["run"] for s in jobs["pytest"]["steps"] if s.get("name") == "Run pytest")
    assert "if" not in steps["Install site toolchain"]
    assert "if" not in steps["Python CI environment"]
    assert "frontend" in jobs["ci-gate"]["needs"]
    # Every test file that declares this marker is in the Frontend command.
    marked_files = [
        path.relative_to(root).as_posix()
        for path in (root / "tests").rglob("test_*.py")
        if "@pytest.mark.site_toolchain" in path.read_text()
    ]
    assert marked_files
    assert all(path in compiler["run"] for path in marked_files)


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
