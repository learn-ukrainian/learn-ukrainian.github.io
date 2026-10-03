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

from scripts import config
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


def assert_unique_workbook_pointers(page):
    """Check complete visible pointers, including any learner heading, on tab 3."""
    tabs = re.findall(r'<TabItem label="[^"]+">(.*?)</TabItem>', page, re.DOTALL)
    assert len(tabs) == 4
    pointers = re.findall(
        r"(?:^### [^\n]+\n\n)?^\*\((?:див\. |see lesson).*\)\*$",
        html.unescape(tabs[2]), re.MULTILINE,
    )
    assert len(pointers) == len(set(pointers)), f"Repeated workbook pointers: {pointers}"
    return pointers


def visible_type_ids(lines, types):
    """Match complete engine ids even inside a longer visible line."""
    return {typ for typ in types if any(re.search(r"\b" + re.escape(typ) + r"\b", line) for line in lines)}


@pytest.mark.parametrize("line", ["quiz", "§quiz", "Here is quiz:", "A fill-in exercise"])
def test_type_id_invariant_catches_ids_inside_longer_lines(line):
    assert visible_type_ids([line], {"quiz", "fill-in"})


def test_type_id_invariant_keeps_word_boundaries():
    assert not visible_type_ids(["quizzes filling-in"], {"quiz", "fill-in"})


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("module_num", [1, 4, 21, 51])
def test_assembler_added_english_obeys_the_page_immersion_band(level, module_num, render_environment):
    inputs = maximal_draft(level)
    draft, plan, pack, words = inputs
    plan["arc_ref"]["position"] = module_num
    example = "ExampleEnglishProbe"
    dialogue = ["DialogueEnglishProbeOne", "DialogueEnglishProbeTwo"]
    gloss = "InlineEnglishProbe"
    pack["examples"][0]["translation_en"] = example
    draft["dialogue"]["translation_en"] = dialogue
    words["words"][0]["gloss_en"] = gloss
    result, expanded = check_render(inputs, level)
    assert result.passed, result.to_dict()
    tabs = re.findall(r'<TabItem label="[^"]+">(.*?)</TabItem>', html.unescape(result.artifacts["mdx"]), re.DOTALL)
    assert len(tabs) == 4
    body = "\n".join(tabs[i] for i in (0, 2, 3))
    counts = {probe: body.count(probe) for probe in [example, *dialogue, gloss]}
    # Independent expectation from the config's level policies: A1's designed
    # scaffold survives; A2 examples/dialogues stay Ukrainian; B1+ English is
    # confined to Tab 2. This measures additions, not synthetic fixture prose.
    policy = config.compute_immersion_band(level, module_num)
    if level == "a1":
        assert policy["advisory_pct_max"] < 75
        assert all(count > 0 for count in counts.values()), counts
    else:
        assert policy["advisory_pct_min"] >= 75
        assert counts == dict.fromkeys(counts, 0), counts
        assert "isUkrainian={false}" not in body, "A2+ widgets must use Ukrainian UI"
        assert re.findall(r'<TabItem label="([^"]+)">', result.artifacts["mdx"]) == ["Урок", "Словник", "Вправи", "Ресурси"]
    assert gloss in tabs[1], "Vocabulary support must survive at every level"
    translations = [u for u in expanded["units"] if str(u["block"]).startswith("dialogue_translation_")]
    assert len(translations) == (len(dialogue) if level == "a1" else 0)


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("placement", ["inline", "workbook"])
@pytest.mark.site_toolchain
def test_no_activity_type_id_is_visible_on_any_page(level, placement, render_environment, tmp_path, monkeypatch):
    inputs = maximal_draft(level)
    draft, plan, _, _ = inputs
    schema = json.loads((ROOT / f"schemas/activities-{level}.schema.json").read_text())
    types = {name.removesuffix("-" + level) for name in schema["definitions"]}
    types_by_id = {a["id"]: a["type"] for a in plan["lessons"][0]["activities"]}
    assert set(types_by_id.values()) == types
    for activity in draft["activities"]:
        activity.pop("title", None)
        # Payload prefixes name engine types only to distinguish transport
        # fixtures. Replace that synthetic prose so longer-line matching can
        # detect actual engine leaks without exempting any visible fields.
        typ = types_by_id[activity["id"]]

        def replace_prefix(value, typ=typ):
            if isinstance(value, str):
                return re.sub(r"\b" + re.escape(typ) + r"\b", "Probe", value)
            if isinstance(value, list):
                return [replace_prefix(child) for child in value]
            if isinstance(value, dict):
                return {key: replace_prefix(child) for key, child in value.items()}
            return value

        activity.update(replace_prefix(activity))
        # The maximal transport fixture prefixes every payload with its type.
        # Anagram splits "anagram items ..." into visible tiles; independent
        # letter data ensures a tile cannot masquerade as an engine leak.
        if types_by_id[activity["id"]] == "anagram":
            for item in activity["items"]:
                item.update(letters=["x", "y"], answer="xy")
    for activity in plan["lessons"][0]["activities"]:
        activity["placement"] = "practice" if placement == "inline" else "workbook"
    # Exercise every type in the Lesson tab or exclusively in the workbook,
    # rather than only the maximal fixture's first inline type.
    draft["steps"][0]["blocks"] = [b for b in draft["steps"][0]["blocks"] if b["kind"] != "activity"]
    draft["consolidation"]["activities"] = []
    plan["lessons"][0]["steps"][0]["practice"] = []
    if placement == "inline":
        ids = [a["id"] for a in draft["activities"]]
        draft["steps"][0]["blocks"].extend({"kind": "activity", "ref": aid} for aid in ids)
        plan["lessons"][0]["steps"][0]["practice"] = ids

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
    assert len(blocks) == len(types)
    page = html.unescape(result.artifacts["mdx"])
    pointers = assert_unique_workbook_pointers(page)
    assert bool(pointers) == (placement == "inline")
    lesson_end = page.index("</TabItem>")
    assert all((page.index(html.unescape(block)) < lesson_end) == (placement == "inline") for block in blocks)
    rendered = render_activity_blocks(blocks, tmp_path)
    # Check surrounding Markdown across all tabs and actual component text;
    # engine ids inside JSX/JSON props are bindings, not visible prose.
    markdown = re.sub(r"<[A-Z]\w*\b[^>]*?/>", "", page).split("---", 2)[-1]
    markdown_lines = {re.sub(r"^#{1,6}\s+", "", line.strip()) for line in markdown.splitlines()}
    visible_lines = {
        line.strip()
        for line in html.unescape(re.sub(r"<[^>]+>", "\n", "\n".join(rendered))).splitlines()
    }
    leaks = visible_type_ids(markdown_lines | visible_lines, types)
    assert not leaks, f"Visible activity type ids: {leaks}; lines: {[line for line in markdown_lines | visible_lines if visible_type_ids([line], leaks)]}"


def test_attempt5_has_no_activity_type_heading(render_environment):
    page, _ = reassemble_attempt5()
    assert assert_unique_workbook_pointers(page) == ['*(див. вкладку «Урок»)*']
    types = set().union(*(
        {name.removesuffix("-" + level) for name in json.loads((ROOT / f"schemas/activities-{level}.schema.json").read_text())["definitions"]}
        for level in LEVELS
    ))
    lines = {re.sub(r"^#{1,6}\s+", "", line.strip()) for line in html.unescape(page).splitlines()}
    # Preserve the whole-line guard everywhere. Broaden label surfaces with
    # word boundaries: ordinary A1 prose can legitimately say "reading" or
    # "order", while labels such as §quiz must never expose an engine id.
    labels = [line for line in html.unescape(page).splitlines() if re.match(r"^(?:#{1,6}\s|\*\()", line)]
    leaks = (types & lines) | visible_type_ids(labels, types)
    assert not leaks, f"Visible activity type ids: {leaks}"


@pytest.mark.parametrize("as_dict", [False, True])
@pytest.mark.parametrize("title", ["", "   ", "Learner title"])
@pytest.mark.parametrize("ukrainian", [False, True])
def test_inline_pointer_uses_only_an_explicit_learner_title(as_dict, title, ukrainian):
    from types import SimpleNamespace

    from scripts.generate_mdx.converters import _inline_activity_cross_ref_to_mdx

    fields = {"type": "quiz", "title": title}
    activity = fields if as_dict else SimpleNamespace(**fields)
    pointer = _inline_activity_cross_ref_to_mdx(activity, "", ukrainian)
    heading = f"### {title.strip()}\n\n" if title.strip() else ""
    reference = "див. вкладку «Урок»" if ukrainian else "see lesson tab"
    assert pointer == f"{heading}*({reference})*"


@pytest.mark.parametrize("as_dict", [False, True])
@pytest.mark.parametrize("ukrainian", [False, True])
@pytest.mark.parametrize("selector", ["ids", "positions"])
def test_headingless_pointers_are_unique_and_distinct_targets_stay(as_dict, ukrainian, selector):
    from types import SimpleNamespace

    from scripts.generate_mdx.converters import yaml_activity_mdx_parts

    fields = [
        {"id": str(i), "type": "quiz", "title": "Learner title" if i >= 6 else ""}
        for i in range(8)
    ]
    activities = fields if as_dict else [SimpleNamespace(**item) for item in fields]
    selectors = (
        {"inline_cross_ref_ids": {str(i) for i in range(8)}}
        if selector == "ids" else {"inline_cross_ref_positions": set(range(8))}
    )
    parts = yaml_activity_mdx_parts(
        activities, is_ukrainian_forced=ukrainian,
        inline_cross_ref_section_titles={"2": "One", "3": "One", "4": "Two", "5": "Two"},
        **selectors,
    )
    tab = "див. вкладку «Урок»" if ukrainian else "see lesson tab"
    section = "див. розділ, §" if ukrainian else "see lesson, §"
    assert parts == [
        (None, f"*({tab})*"),
        (None, f"*({section}One)*"),
        (None, f"*({section}Two)*"),
        (None, f"### Learner title\n\n*({tab})*"),
    ]


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
