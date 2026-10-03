"""Learner-surface invariants across the live schemas and archived attempt-5 inputs.

English sentinels are synthetic transport probes, not curriculum content.
"""

from __future__ import annotations

import copy
import html
import json
import re
import subprocess

import pytest

from scripts.build.fresh import assemble
from tests.build.test_fresh_page_safety import FIXTURE, reassemble_attempt5
from tests.build.test_fresh_render_coverage import LEVELS, ROOT, check_render, maximal_draft
from tests.build.test_fresh_render_coverage import render_environment as render_environment

# Explicit paths, rather than an author-field denylist. Every other string is tainted.
# Binding fields preserve typed selectors/references so the real renderer can run;
# they grant no right to publish prose from sibling fields.
LEARNER_TEXT_ALLOWLIST = {
    "plan.lessons.*.title": "Learner lesson title.",
    "plan.lessons.*.job": "Learner outcome in lesson frontmatter.",
    "plan.lessons.*.reading_passages.*.title": "Hosted reading title.",
    "plan.lessons.*.reading_passages.*.genre": "Hosted reading genre label.",
    "pack.examples.*.text": "Example bytes explicitly selected by the draft.",
    "pack.examples.*.translation_en": "Example translation with A1 scaffolding.",
    "pack.videos.*.title": "Public video title.",
    "pack.videos.*.channel": "Public media attribution.",
    "pack.videos.*.url": "Public media link.",
    "pack.texts.*.episode_url": "Registry-permitted public episode link.",
    "pack.texts.*.url": "Registry-permitted public episode link.",
    "pack.texts.*.quote": "Only selected quotes with publication-registry permission.",
}
BINDING_ALLOWLIST = {
    "plan.arc_ref.level", "plan.lessons.*.slug", "plan.lessons.*.kind",
    "plan.lessons.*.activities.*.id", "plan.lessons.*.activities.*.type",
    "plan.lessons.*.activities.*.placement", "plan.lessons.*.steps.*.id",
    "plan.lessons.*.steps.*.kind", "plan.lessons.*.steps.*.practice.*",
    "plan.lessons.*.steps.*.evidence.*", "plan.lessons.*.steps.*.explains.*",
    "plan.lessons.*.steps.*.ref", "plan.lessons.*.steps.*.needs.*",
    "plan.lessons.*.steps.*.paradigm.id", "plan.lessons.*.steps.*.paradigm.word",
    "plan.lessons.*.steps.*.paradigm.forms.*",
    "plan.lessons.*.inventory.vocabulary.core.*.evidence",
    "plan.lessons.*.inventory.vocabulary.core.*.forms.*",
    "plan.lessons.*.inventory.vocabulary.incidental.*.evidence",
    "plan.lessons.*.inventory.vocabulary.incidental.*.forms.*",
    "plan.lessons.*.videos.*.evidence", "plan.lessons.*.reading_passages.*.reading_slug",
    "pack.texts.*.id", "pack.texts.*.source.file", "pack.texts.*.source.kind",
    "pack.examples.*.id", "pack.videos.*.id", "pack.errors.*.id",
    "pack.standard.*.id",
}


def taint_author_strings(plan, pack, draft):
    """Visit every string leaf; new/unknown paths default to a unique sentinel."""
    selected_quotes = {
        block["ref"] for step in draft["steps"] for block in step["blocks"] if block["kind"] == "quote"
    }
    sentinels = {}

    def visit(value, path):
        if isinstance(value, dict):
            return {k: visit(v, (*path, k)) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v, (*path, str(i))) for i, v in enumerate(value)]
        if not isinstance(value, str):
            return value
        pattern = ".".join("*" if p.isdigit() else p for p in path)
        allowed = pattern in LEARNER_TEXT_ALLOWLIST or pattern in BINDING_ALLOWLIST
        if pattern == "pack.texts.*.quote":
            record = pack["texts"][int(path[2])]
            allowed = record["id"] in selected_quotes
            if allowed:
                assemble.publication.quote_attribution(record)  # actual registry, never pack permission
        if allowed:
            return value
        sentinel = "ZZ" + "_".join(path) + "ZZ"
        sentinels[sentinel] = ".".join(path)
        return sentinel

    return visit(plan, ("plan",)), visit(pack, ("pack",)), sentinels


@pytest.mark.parametrize("case", ["a1", "b1", "attempt5"])
def test_no_nonlearner_string_reaches_any_page_or_payload(case, render_environment, monkeypatch):
    if case == "attempt5":
        data = json.loads((FIXTURE / "inputs.json").read_text())
        inputs = tuple(data[k] for k in ("draft", "plan", "pack", "words"))
    else:
        inputs = maximal_draft(case)
    draft, plan, pack, words = copy.deepcopy(inputs)
    # Maximal draft has every activity/block. Add optional author metadata to the
    # accompanying plan/pack as well; real attempt-5 leaves are visited unchanged.
    payloads = []
    original = assemble.generate_mdx

    def capture(**kwargs):
        payloads.append({key: kwargs[key] for key in ("meta_data", "vocab_items", "external_resources", "yaml_activities")})
        return original(**kwargs)

    monkeypatch.setattr(assemble, "generate_mdx", capture)
    lesson = plan["lessons"][0]
    lesson["reading_passages"] = [{
        "title": "Learner reading title", "genre": "Learner genre", "reading_slug": "fixture-reading",
        "supports": "author reading support", "notes": "author reading notes",
    }]
    lesson.update({
        "rationale": "author rationale", "objectives": ["objective"],
        "connects_to": "connection", "prerequisites": ["prerequisite"],
        "register": "register", "situation": "situation", "setting": "setting",
        "target_grammar": "grammar", "role": "role", "point": "point",
        "subtitle": "author subtitle",
    })
    plan["changelog"] = ["change"]
    for step in lesson["steps"]:
        step["teach"] = "teaching directive"
    for rec in pack.get("texts", []):
        rec.update({"supports": "author support", "notes": "author note"})
    for rec in pack.get("videos", []):
        rec["use"] = "author use"
    plan, pack, sentinels = taint_author_strings(plan, pack, draft)
    assert sentinels and any("supports" in path for path in sentinels.values())
    if case == "attempt5":
        page, _ = reassemble_attempt5({**data, "draft": draft, "plan": plan, "pack": pack, "words": words})
    else:
        result, _ = check_render((draft, plan, pack, words), case)
        assert result.passed, result.to_dict()
        page = result.artifacts["mdx"]
    decoded = html.unescape(page) + json.dumps(payloads, ensure_ascii=False, default=vars)
    leaks = [path for sentinel, path in sentinels.items() if sentinel in decoded]
    assert not leaks, "Non-learner text leaked: " + ", ".join(leaks)


def render_activity_blocks(blocks, tmp_path):
    """Execute the page's actual JSX/JSON with the actual React components."""
    jsx = [re.sub(r"client:only=['\"]react['\"]", "", re.sub(r"^### [^\n]*\n\n", "", block, flags=re.MULTILINE)) for block in blocks]
    names = set(re.findall(r"<([A-Z]\w*)", "\n".join(jsx)))
    imports = []
    for name in sorted(names):
        named = name in {"MarkTheWordsActivity", "ObserveActivity", "HighlightMorphemesActivity"}
        filename = name.removesuffix("Activity") if named else name
        target = ROOT / f"site/src/components/{filename}.tsx"
        imports.append(f"import {'{'+name+'}' if named else name} from {json.dumps(str(target))};")
    source = "\n".join(imports) + '\nimport {renderToStaticMarkup} from "react-dom/server";\n'
    source += "console.log(JSON.stringify([" + ",".join(f"renderToStaticMarkup({s})" for s in jsx) + "]));"
    script = tmp_path / "render.tsx"
    output = tmp_path / "render.cjs"
    script.write_text(source)
    build = subprocess.run(
        ["node", "--input-type=module", "-e",
         "import {build} from 'esbuild'; await build({entryPoints:[process.argv[1]],"
         "outfile:process.argv[2],bundle:true,platform:'node',format:'cjs',jsx:'automatic',"
         "alias:{react:process.cwd()+'/node_modules/react'},loader:{'.css':'empty'},nodePaths:[process.cwd()+'/node_modules'],logLevel:'error'});",
         str(script), str(output)], cwd=ROOT / "site", capture_output=True, text=True, timeout=60,
    )
    assert build.returncode == 0, build.stderr
    rendered = subprocess.run(["node", str(output)], capture_output=True, text=True, timeout=60)
    assert rendered.returncode == 0, rendered.stderr
    return json.loads(rendered.stdout)


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("title_mode", ["absent", "same", "distinct"])
@pytest.mark.site_toolchain
def test_every_activity_instruction_is_visible_exactly_once(level, title_mode, render_environment, tmp_path, monkeypatch):
    inputs = maximal_draft(level)
    for i, activity in enumerate(inputs[0]["activities"]):
        activity["instruction"] = f"InstructionSentinel{level}{i}End"
        if title_mode == "same":
            activity["title"] = activity["instruction"]
        elif title_mode == "distinct":
            activity["title"] = f"Separate learner title {i}"
        else:
            activity.pop("title", None)
    from scripts.generate_mdx.unit_map import LessonUnitMap

    blocks = []
    original = LessonUnitMap.verify

    def capture(mapping, page):
        pieces = original(mapping, page)
        blocks.extend(value for key, value in pieces.items() if isinstance(key, tuple) and key[0] == "activity")
        return pieces

    monkeypatch.setattr(LessonUnitMap, "verify", capture)
    result, _ = check_render(inputs, level)
    assert result.passed, result.to_dict()
    page = result.artifacts["mdx"]
    assert len(blocks) == len(inputs[0]["activities"])
    # A direct source count also covers surrounding headings and title props.
    counts = {a["id"]: html.unescape(page).count(a["instruction"]) for a in inputs[0]["activities"]}
    assert set(counts.values()) == {1}, counts
    rendered = render_activity_blocks(blocks, tmp_path)
    # Surrounding MDX headings are learner text too (Cloze prints its instruction there).
    visible = html.unescape(re.sub(r"<[^>]+>", "", "\n".join(rendered)))
    visible += "\n" + "\n".join(re.findall(r"^### (.*)$", html.unescape(page), re.MULTILINE))
    counts = {a["id"]: visible.count(a["instruction"]) for a in inputs[0]["activities"]}
    assert set(counts.values()) == {1}, counts


def test_cloze_heading_cannot_be_removed_by_prop_like_learner_text():
    from types import SimpleNamespace

    from scripts.generate_mdx.converters import fresh_activity_mdx

    activity = SimpleNamespace(title="Unique instruction", instruction="Unique instruction")
    mdx = '### Unique instruction\n\n<Cloze passage={"Read title= and instruction= as text"} />'
    assert fresh_activity_mdx(activity, mdx) == mdx


def test_fresh_unknown_component_display_contract_fails_closed():
    from types import SimpleNamespace

    from scripts.generate_mdx.converters import fresh_activity_mdx

    with pytest.raises(ValueError, match="no component display contract"):
        fresh_activity_mdx(SimpleNamespace(title="Title", instruction="Read"), '### Read\n\n<Unknown />')
