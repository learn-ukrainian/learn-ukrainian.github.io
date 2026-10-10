"""Learner-surface invariants across the live schemas and archived attempt-5 inputs.

English sentinels are synthetic transport probes, not curriculum content.
"""

from __future__ import annotations

import ast
import copy
import html
import inspect
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from scripts import config
from scripts.build.fresh import assemble
from tests.build.test_fresh_page_safety import FIXTURE, reassemble_attempt5
from tests.build.test_fresh_render_coverage import LEVELS, ROOT, check_render, maximal_draft
from tests.build.test_fresh_render_coverage import render_environment as render_environment

# Explicit paths, rather than an author-field denylist. Every other string is tainted.
# Binding fields preserve typed selectors/references so the real renderer can run;
# they grant no right to publish prose from sibling fields.
LEARNER_TEXT_ALLOWLIST = assemble.LEARNER_TEXT_ALLOWLIST
BINDING_ALLOWLIST = {
    "plan.arc_ref.level",
    "plan.lessons.*.slug",
    "plan.lessons.*.kind",
    "plan.lessons.*.activities.*.id",
    "plan.lessons.*.activities.*.type",
    "plan.lessons.*.activities.*.placement",
    "plan.lessons.*.steps.*.id",
    "plan.lessons.*.steps.*.kind",
    "plan.lessons.*.steps.*.practice.*",
    "plan.lessons.*.steps.*.evidence.*",
    "plan.lessons.*.steps.*.explains.*",
    "plan.lessons.*.steps.*.ref",
    "plan.lessons.*.steps.*.needs.*",
    "plan.lessons.*.steps.*.paradigm.id",
    "plan.lessons.*.steps.*.paradigm.word",
    "plan.lessons.*.steps.*.paradigm.forms.*",
    "plan.lessons.*.inventory.vocabulary.core.*.evidence",
    "plan.lessons.*.inventory.vocabulary.core.*.forms.*",
    "plan.lessons.*.inventory.vocabulary.incidental.*.evidence",
    "plan.lessons.*.inventory.vocabulary.incidental.*.forms.*",
    "plan.lessons.*.videos.*.evidence",
    "plan.lessons.*.reading_passages.*.reading_slug",
    "pack.texts.*.id",
    "pack.texts.*.source.file",
    "pack.texts.*.source.kind",
    "pack.examples.*.id",
    "pack.videos.*.id",
    "pack.errors.*.id",
    "pack.standard.*.id",
}


def taint_author_strings(plan, pack, draft):
    """Visit every string leaf; new/unknown paths default to a unique sentinel."""
    selected_quotes = {block["ref"] for step in draft["steps"] for block in step["blocks"] if block["kind"] == "quote"}
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
        if pattern.startswith("pack.texts.") and pattern in LEARNER_TEXT_ALLOWLIST:
            record = pack["texts"][int(path[2])]
            allowed = pattern != "pack.texts.*.quote" or record["id"] in selected_quotes
            if allowed:
                allowed = assemble.learner_text_allowed(pattern, record)
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
        payloads.append(
            {key: kwargs[key] for key in ("meta_data", "vocab_items", "external_resources", "yaml_activities")}
        )
        return original(**kwargs)

    monkeypatch.setattr(assemble, "generate_mdx", capture)
    lesson = plan["lessons"][0]
    lesson["reading_passages"] = [
        {
            "title": "Learner reading title",
            "genre": "Learner genre",
            "reading_slug": "fixture-reading",
            "supports": "author reading support",
            "notes": "author reading notes",
        }
    ]
    lesson.update(
        {
            "rationale": "author rationale",
            "objectives": ["objective"],
            "connects_to": "connection",
            "prerequisites": ["prerequisite"],
            "register": "register",
            "situation": "situation",
            "setting": "setting",
            "target_grammar": "grammar",
            "role": "role",
            "point": "point",
            "subtitle": "author subtitle",
        }
    )
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
    jsx = [
        re.sub(r"client:only=['\"]react['\"]", "", re.sub(r"^### [^\n]*\n\n", "", block, flags=re.MULTILINE))
        for block in blocks
    ]
    names = set(re.findall(r"<([A-Z]\w*)", "\n".join(jsx)))
    imports = []
    for name in sorted(names):
        named = name in {"MarkTheWordsActivity", "ObserveActivity", "HighlightMorphemesActivity"}
        filename = name.removesuffix("Activity") if named else name
        target = ROOT / f"site/src/components/{filename}.tsx"
        imports.append(f"import {'{' + name + '}' if named else name} from {json.dumps(str(target))};")
    source = "\n".join(imports) + '\nimport {renderToStaticMarkup} from "react-dom/server";\n'
    source += "console.log(JSON.stringify([" + ",".join(f"renderToStaticMarkup({s})" for s in jsx) + "]));"
    script = tmp_path / "render.tsx"
    output = tmp_path / "render.cjs"
    script.write_text(source)
    build = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            "import {build} from 'esbuild'; await build({entryPoints:[process.argv[1]],"
            "outfile:process.argv[2],bundle:true,platform:'node',format:'cjs',jsx:'automatic',"
            "alias:{react:process.cwd()+'/node_modules/react'},loader:{'.css':'empty'},nodePaths:[process.cwd()+'/node_modules'],logLevel:'error'});",
            str(script),
            str(output),
        ],
        cwd=ROOT / "site",
        capture_output=True,
        text=True,
        timeout=60,
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
        html.unescape(tabs[2]),
        re.MULTILINE,
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


def english_input_fields(source):
    """Discover explicit English reads independently of the channel registry."""
    fields = set()
    for node in ast.walk(ast.parse(source)):
        key = None
        if isinstance(node, ast.Subscript):
            key = node.slice
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
        ):
            key = node.args[0]
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            name = key.value
            if name == "en" or name.endswith("_en") or name.startswith("english_") or name == "sense_gloss":
                fields.add(name)
    return fields


def assert_english_channels_classified(source):
    registered = {path.removesuffix(".*").rsplit(".", 1)[-1] for path in assemble.ENGLISH_CHANNELS}
    missing = english_input_fields(source) - registered
    assert not missing, f"Unclassified English fields: {sorted(missing)}"


def test_every_english_field_read_has_a_production_classification():
    assert_english_channels_classified(inspect.getsource(assemble))
    assert set(assemble.ENGLISH_CHANNELS.values()) == {
        "body_support",
        "vocabulary_and_inline_support",
        "writer_bilingual",
        "plan_task_scaffolding",
    }


def test_new_english_producer_fails_until_classified(monkeypatch):
    source = inspect.getsource(assemble) + '\ndef future_english(record):\n    return record.get("note_en")\n'
    with pytest.raises(AssertionError, match="note_en"):
        assert_english_channels_classified(source)
    monkeypatch.setitem(assemble.ENGLISH_CHANNELS, "pack.examples.*.note_en", "body_support")
    assert_english_channels_classified(source)


def plant_english_probe(inputs, path, probe):
    """Follow a registered path, including arrays; optional leaf fields are planted."""

    def visit(value, parts):
        head, *tail = parts
        if head == "*":
            assert isinstance(value, list), path
            if not tail:
                for index in range(len(value)):
                    value[index] = probe
                return len(value)
            return sum(visit(child, tail) for child in value)
        if not tail:
            value[head] = probe
            return 1
        if head not in value:
            return 0
        return visit(value[head], tail)

    return visit(inputs, path.split("."))


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("module_num", [1, 4, 21, 51])
@pytest.mark.parametrize("channel", assemble.ENGLISH_CHANNELS)
def test_assembler_added_english_obeys_the_page_immersion_band(level, module_num, channel, render_environment):
    inputs = maximal_draft(level)
    draft, plan, pack, words = inputs
    plan["arc_ref"]["position"] = module_num
    if channel.startswith("plan."):
        from tests.build.test_fresh_recap_contract import task

        plan["lessons"][0]["steps"][-1]["task"] = task()
    probe = "EnglishChannelProbe"
    assert plant_english_probe({"plan": plan, "draft": draft, "pack": pack, "words": words}, channel, probe), channel
    result, expanded = check_render(inputs, level)
    assert result.passed, result.to_dict()
    tabs = re.findall(r'<TabItem label="[^"]+">(.*?)</TabItem>', html.unescape(result.artifacts["mdx"]), re.DOTALL)
    assert len(tabs) == 4
    counts = {tab: text.count(probe) for tab, text in zip(("urok", "slovnyk", "vpravy", "resursy"), tabs, strict=True)}
    # Independent config expectations for assembler additions. Writer-supplied
    # bilingual prose is classified separately and remains upstream-gated.
    policy = config.compute_immersion_band(level, module_num)
    if level == "a1":
        assert policy["advisory_pct_max"] < 75
    else:
        assert policy["advisory_pct_min"] >= 75
        body = "\n".join(tabs[i] for i in (0, 2, 3))
        assert "isUkrainian={false}" not in body, "A2+ widgets must use Ukrainian UI"
        assert re.findall(r'<TabItem label="([^"]+)">', result.artifacts["mdx"]) == [
            "Урок",
            "Словник",
            "Вправи",
            "Ресурси",
        ]
    classification = assemble.ENGLISH_CHANNELS[channel]
    if classification == "writer_bilingual":
        assert counts["urok"] > 0
        assert not any(counts[tab] for tab in ("slovnyk", "vpravy", "resursy"))
    elif classification in {"body_support", "plan_task_scaffolding"}:
        assert (counts["urok"] > 0) == (level == "a1"), counts
        assert not any(counts[tab] for tab in ("slovnyk", "vpravy", "resursy"))
    else:
        assert classification == "vocabulary_and_inline_support"
        assert counts["slovnyk"] > 0, "Vocabulary support must survive at every level"
        assert (counts["urok"] > 0) == (level == "a1"), counts
        if level != "a1":
            assert not any(counts[tab] for tab in ("urok", "vpravy", "resursy")), counts
    translations = [u for u in expanded["units"] if str(u["block"]).startswith("dialogue_translation_")]
    assert len(translations) == (len(draft["dialogue"]["translation_en"]) if level == "a1" else 0)


def test_recap_english_channels_are_plan_fields_not_draft_echoes():
    expected = {
        "plan.lessons.*.steps.*.task.context_en",
        "plan.lessons.*.steps.*.task.instruction_en",
        "plan.lessons.*.steps.*.task.success_criteria_en.*",
    }
    assert {p for p, c in assemble.ENGLISH_CHANNELS.items() if c == "plan_task_scaffolding"} == expected


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
    visible_lines = {line.strip() for line in html.unescape(re.sub(r"<[^>]+>", "\n", "\n".join(rendered))).splitlines()}
    leaks = visible_type_ids(markdown_lines | visible_lines, types)
    assert not leaks, (
        f"Visible activity type ids: {leaks}; lines: {[line for line in markdown_lines | visible_lines if visible_type_ids([line], leaks)]}"
    )


def test_attempt5_has_no_activity_type_heading(render_environment):
    page, _ = reassemble_attempt5()
    assert assert_unique_workbook_pointers(page) == ["*(див. вкладку «Урок»)*"]
    types = set().union(
        *(
            {
                name.removesuffix("-" + level)
                for name in json.loads((ROOT / f"schemas/activities-{level}.schema.json").read_text())["definitions"]
            }
            for level in LEVELS
        )
    )
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

    fields = [{"id": str(i), "type": "quiz", "title": "Learner title" if i >= 6 else ""} for i in range(8)]
    activities = fields if as_dict else [SimpleNamespace(**item) for item in fields]
    selectors = (
        {"inline_cross_ref_ids": {str(i) for i in range(8)}}
        if selector == "ids"
        else {"inline_cross_ref_positions": set(range(8))}
    )
    parts = yaml_activity_mdx_parts(
        activities,
        is_ukrainian_forced=ukrainian,
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
def test_every_activity_instruction_is_visible_exactly_once(
    level, title_mode, render_environment, tmp_path, monkeypatch
):
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
        fresh_activity_mdx(SimpleNamespace(title="Title", instruction="Read"), "### Read\n\n<Unknown />")


@pytest.mark.parametrize(
    "arc_ref",
    [
        None,
        [],
        "arc",
        {},
        {"position": None},
        {"position": True},
        {"position": 0},
        {"position": -1},
        {"position": "1"},
        {"position": "invalid"},
        {"position": 1.5},
    ],
)
def test_malformed_arc_ref_fails_with_named_plan_error_before_use(arc_ref, monkeypatch):
    draft, plan, pack, words = maximal_draft("a1")
    plan["arc_ref"] = arc_ref
    monkeypatch.setattr(
        assemble, "body_english_support_allowed", lambda *a, **k: pytest.fail("band read before validation")
    )
    with pytest.raises(assemble.AssemblerError) as caught:
        assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "fixture", 1)
    assert (caught.value.code, caught.value.layer) == (assemble.PLAN_ARC_REF_INVALID, "plan")
    result = assemble.check_9_stress_and_render({}, draft, plan, pack, words, {}, "a1", "fixture", 1)
    assert not result.passed and result.layer == "plan"
    assert result.reason.startswith(assemble.PLAN_ARC_REF_INVALID + ":")


def test_missing_arc_ref_fails_with_named_error():
    with pytest.raises(assemble.AssemblerError, match="plan_arc_ref_invalid"):
        assemble.plan_arc_position({})
    assert assemble.plan_arc_position({"arc_ref": {"position": 51}}) == 51


@pytest.mark.parametrize("level", LEVELS)
def test_every_assembler_english_decision_uses_the_shared_helper(level, render_environment, monkeypatch):
    calls = []
    original = assemble.body_english_support_allowed

    def capture(level, module_num=1):
        calls.append((level, module_num))
        return original(level, module_num)

    monkeypatch.setattr(assemble, "body_english_support_allowed", capture)
    inputs = maximal_draft(level)
    result, expanded = check_render(inputs, level)
    assert result.passed, result.to_dict()
    # Expansion, check 9, and final provenance must agree. Direct renderer use
    # also goes through the helper when no precomputed support flag is passed.
    assert len(calls) >= 3 and set(calls) == {(level, 1)}
    before = len(calls)
    assemble._render_urok_markdown(inputs[0], expanded, inputs[2], inputs[3])
    assert len(calls) == before + 1
    assert calls[-1] == (level, 1)
    assert original(level.upper(), 51) == (level == "a1")


def test_sentinel_uses_the_production_learner_text_allowlist():
    assert LEARNER_TEXT_ALLOWLIST is assemble.LEARNER_TEXT_ALLOWLIST
    assert not assemble.learner_text_allowed("pack.texts.*.supports", {})
    assert assemble.learner_text_allowed("plan.lessons.*.title")
    assert not assemble.learner_text_allowed("pack.texts.*.url")


@pytest.mark.parametrize("field", ["url", "episode_url"])
@pytest.mark.parametrize(
    "source_file,permitted",
    [("ulp-1-00-lesson-notes", True), ("not-registered", False), ("1-klas-bukvar-zaharijchuk-2025-1", False)],
)
def test_url_allowlist_uses_registry_permission_not_pack_claim(field, source_file, permitted):
    url = "https://www.ukrainianlessons.com/episode1/"
    record = {
        "id": "T-1",
        field: url,
        "quote": "Synthetic excerpt",
        "source": {"file": source_file, "kind": "textbook", "page": 12},
        "publish": {"allowed": True},
        "resource_credit": {"episode_links": True},
    }
    path = f"pack.texts.*.{field}"
    assert assemble.learner_text_allowed(path, record) == permitted
    resources = assemble.build_resursy_tab({"steps": [{"explains": ["T-1"]}]}, {"texts": [record]})
    assert (url in json.dumps(resources)) == permitted
    if permitted:
        with pytest.raises(assemble.AssemblerError, match="owned_quote_refused"):
            assemble.learner_text_allowed("pack.texts.*.quote", record)


@pytest.mark.parametrize("field", ["url", "episode_url"])
def test_url_sentinel_preserves_only_registry_permitted_leaf(field):
    draft, plan, pack, _ = maximal_draft("a1")
    pack["texts"][0].update(
        source={"file": "ulp-1-00-lesson-notes", "kind": "textbook", "page": 12},
        **{field: "https://www.ukrainianlessons.com/episode1/"},
    )
    # The no-copy source is grounding only. Only its registry-permitted link
    # survives; quote prose is tainted even if the pack claims publication.
    draft["steps"][0]["blocks"] = [b for b in draft["steps"][0]["blocks"] if b["kind"] != "quote"]
    _, tainted, sentinels = taint_author_strings(plan, pack, draft)
    assert tainted["texts"][0][field] == pack["texts"][0][field]
    assert "pack.texts.0.quote" in sentinels.values()
    pack["texts"][0]["source"]["file"] = "not-registered"
    _, tainted, sentinels = taint_author_strings(plan, pack, draft)
    assert f"pack.texts.0.{field}" in sentinels.values()
    assert tainted["texts"][0][field].startswith("ZZ")


def test_unknown_publication_field_fails_closed():
    with pytest.raises(assemble.AssemblerError, match="learner_text_not_allowed"):
        assemble.learner_text_permission("pack.texts.*.future_url", {})


def english_schema_paths(node, document, path=(), *, schema_path=None, schemas_dir=ROOT / "schemas"):
    """Walk file-local schema refs, pruning cycles only on the current branch."""
    schemas_dir = schemas_dir.resolve()
    schema_path = (schema_path or schemas_dir / "inline.schema.json").resolve()
    documents = {schema_path: document}

    def walk(node, document, schema_path, path, ancestors):
        if not isinstance(node, dict) or id(node) in ancestors:
            return set()
        ancestors = ancestors | {id(node)}
        found = set()
        if "$ref" in node:
            ref = urlsplit(node["$ref"])
            assert not (ref.scheme or ref.netloc or ref.query), f"Non-local schema ref: {node['$ref']}"
            target_path = (schema_path.parent / unquote(ref.path)).resolve() if ref.path else schema_path
            assert target_path.is_relative_to(schemas_dir), f"Schema ref outside schemas/: {node['$ref']}"
            if target_path not in documents:
                documents[target_path] = json.loads(target_path.read_text(encoding="utf-8"))
            target_document = documents[target_path]
            target = target_document
            pointer = unquote(ref.fragment)
            assert not pointer or pointer.startswith("/"), f"Unsupported schema anchor: {node['$ref']}"
            if pointer:
                for part in pointer[1:].split("/"):
                    part = part.replace("~1", "/").replace("~0", "~")
                    target = target[int(part)] if isinstance(target, list) else target[part]
            found.update(walk(target, target_document, target_path, path, ancestors))
        for key, child in node.get("properties", {}).items():
            if key == "en" or key.endswith("_en") or key.startswith("english_") or key == "sense_gloss":
                suffix = ("*",) if child.get("type") == "array" else ()
                found.add(".".join((*path, key, *suffix)))
            else:
                found.update(walk(child, document, schema_path, (*path, key), ancestors))
        if node.get("type") == "array":
            found.update(walk(node.get("items"), document, schema_path, (*path, "*"), ancestors))
        for keyword in ("oneOf", "anyOf", "allOf"):
            for child in node.get(keyword, []):
                found.update(walk(child, document, schema_path, path, ancestors))
        return found

    return walk(node, document, schema_path, path, frozenset())


@pytest.mark.parametrize("level", LEVELS)
def test_every_english_schema_path_is_classified_in_production(level):
    paths = set()
    for root, filename in (
        ("plan", "module-plan-v2.schema.json"),
        ("draft", f"lesson-draft-{level}-v1.schema.json"),
        ("pack", "evidence-pack-v1.schema.json"),
        ("words", "evidence-words-v1.schema.json"),
    ):
        schema_path = ROOT / "schemas" / filename
        schema = json.loads(schema_path.read_text())
        paths.update(english_schema_paths(schema, schema, (root,), schema_path=schema_path))
        if root == "draft":
            # The validator binds these definitions by plan type, outside the
            # root schema's payload-key union. They share the activity path.
            for definition in schema["$defs"]["activity_types"].values():
                paths.update(
                    english_schema_paths(
                        definition,
                        schema,
                        ("draft", "activities", "*"),
                        schema_path=schema_path,
                    )
                )
    classified = set(assemble.ENGLISH_CHANNELS) | assemble.ENGLISH_METADATA_FIELDS
    assert paths == classified, f"Unclassified English schema paths: {sorted(paths - classified)}"


@pytest.mark.parametrize("level", LEVELS)
def test_new_activity_english_field_fails_production_classification(level, monkeypatch):
    schema_path = ROOT / "schemas" / f"activities-{level}.schema.json"
    schema = json.loads(schema_path.read_text())
    schema["definitions"][f"quiz-{level}"]["properties"]["hint_en"] = {"type": "string"}
    original = Path.read_text

    def read_text(path, *args, **kwargs):
        if path == schema_path:
            return json.dumps(schema)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    with pytest.raises(AssertionError, match=r"draft\.activities\.\*\.hint_en"):
        test_every_english_schema_path_is_classified_in_production(level)


def test_schema_ref_cycles_preserve_each_sibling_path_and_target_document(tmp_path):
    schema_path = tmp_path / "first.schema.json"
    schema = {
        "properties": {key: {"$ref": "nested/second.schema.json"} for key in ("first", "second")},
        "allOf": [{"$ref": "#"}],
    }
    other = {
        "properties": {
            "hint_en": {"type": "string"},
            "again": {"$ref": "../first.schema.json"},
            "detail": {"$ref": "#/$defs/a~1b~0c"},
        },
        "$defs": {"a/b~c": {"properties": {"english_note": {"type": "array"}}}},
    }
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/second.schema.json").write_text(json.dumps(other))
    schema_path.write_text(json.dumps(schema))
    assert english_schema_paths(schema, schema, ("draft",), schema_path=schema_path, schemas_dir=tmp_path) == {
        "draft.first.hint_en",
        "draft.second.hint_en",
        "draft.first.detail.english_note.*",
        "draft.second.detail.english_note.*",
    }


@pytest.mark.parametrize(
    "ref,error",
    [
        ("../outside.schema.json", "outside schemas/"),
        ("https://example.com/schema.json", "Non-local schema ref"),
        ("missing.schema.json", None),
    ],
)
def test_schema_refs_cannot_silently_skip_unresolvable_targets(ref, error, tmp_path):
    schema = {"$ref": ref}
    with pytest.raises(AssertionError if error else FileNotFoundError, match=error):
        english_schema_paths(schema, schema, schemas_dir=tmp_path)


def test_new_english_path_with_an_existing_field_name_requires_classification():
    schema = {
        "properties": {
            "videos": {
                "type": "array",
                "items": {
                    "properties": {"translation_en": {"type": "string"}},
                },
            }
        }
    }
    paths = english_schema_paths(schema, schema, ("pack",))
    assert paths == {"pack.videos.*.translation_en"}
    assert paths - (set(assemble.ENGLISH_CHANNELS) | assemble.ENGLISH_METADATA_FIELDS) == paths
    assert assemble.learner_text_permission("plan.lessons.*.title", {}) is None
