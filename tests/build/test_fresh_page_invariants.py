"""Learner-surface invariants across the live schemas and archived attempt-5 inputs.

English sentinels are synthetic transport probes, not curriculum content.
"""

from __future__ import annotations

import copy
import html
import json
import re

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


def test_unknown_publication_field_fails_closed():
    with pytest.raises(assemble.AssemblerError, match="learner_text_not_allowed"):
        assemble.learner_text_permission("pack.texts.*.future_url", {})
