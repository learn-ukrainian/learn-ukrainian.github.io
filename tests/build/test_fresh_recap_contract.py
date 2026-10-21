"""Public synthetic contract tests for #10105; independent held-out cases stay unseen."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.build.fresh.assemble import AssemblerError, _render_urok_markdown, assemble_expanded_document
from scripts.curriculum.arc.loader import ArcPosition, ArcStaleError
from scripts.curriculum.learner_state.immersion import ImmersionError, compute_lesson_immersion_band
from scripts.curriculum.validate import codes
from scripts.curriculum.validate.cross import LevelPlans
from scripts.curriculum.validate.pack import Pack, WordRecord, WordStore, load_pack
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.review_gates import ReviewGates

ROOT = Path(__file__).resolve().parents[2]


def registered_quote(quote="model"):
    """Existing publication fixture identity; synthetic print, no language assertion."""
    from tests.curriculum.evidence.test_publication import record

    return record(quote=quote)


def task(task_id: str = "practical-closure") -> dict:
    return {
        "id": task_id,
        "action": "select_for_context",
        "context_en": "A new familiar situation.",
        "instruction_en": "Select and use a taught model that fits the situation.",
        "response_mode": "selection",
        "success_criteria_en": ["Select a model suited to the context."],
        "learner_reads": [],
    }


def test_stale_arc_is_rejected(tmp_path):
    doc = ROOT / "docs/epics/fresh-build-a1-arc.md"
    changed = tmp_path / "changed.md"
    changed.write_bytes(doc.read_bytes() + b"\nChanged source.\n")
    with pytest.raises(ImmersionError) as exc:
        compute_lesson_immersion_band("a1", 1, 1, 0, doc_path=changed)
    assert exc.value.code == "arc_band_table_missing"
    assert isinstance(exc.value.__cause__, ArcStaleError)


def gate_world(*, embedded=False, early_count=0, orientation=False):
    intro = {
        "id": "s1",
        "kind": "teach",
        "introduces": {"letters": [], "vocabulary": ["W-001"], "grammar": ["G-a1-001"]},
    }
    closure = {
        "id": "s2",
        "kind": "recap",
        "task": task(),
        "uses": {"vocabulary": ["W-001"], "grammar": ["G-a1-001"]},
        "evidence": ["T-001"],
        "practice": [],
    }
    inv = {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}}
    lesson = {
        "n": 1,
        "kind": "teach" if embedded else "recap",
        "inventory": copy.deepcopy(inv),
        "steps": [intro, closure] if embedded else [closure],
        "activities": [],
    }
    if embedded:
        lesson["closes_with_recap"] = True
        lesson["inventory"]["vocabulary"]["core"] = [{"evidence": "W-001"}]
    plan = {"level": "a1", "slug": "unit", "arc_ref": {"position": 1}, "lessons": [lesson]}
    records = {"W-001": WordRecord("W-001", "model", frozenset())}
    prior = {
        "lessons": [
            {
                "inventory": {"vocabulary": {"core": [{"evidence": f"W-{i + 100:03d}"} for i in range(early_count)]}},
                "steps": [],
            }
        ]
    }
    gates = ReviewGates(
        Report("a1", "unit"),
        plan,
        "a1",
        WordStore(Path("words"), records),
        [],
        LevelPlans(),
        Path("words"),
        pack=Pack(Path("pack"), ids=frozenset({"T-001"})),
    )
    gates.__dict__["_base_layer"] = (frozenset(), "")
    gates.__dict__["_earlier_introduced"] = ({"W-001"} if not embedded else set(), "")
    if not embedded:
        # Genuine earlier teaching supplies the grammar; normal synthetic position is 2.
        plan["arc_ref"]["position"] = 2
        prior["lessons"][0]["steps"] = [{"introduces": {"grammar": ["G-a1-001"], "vocabulary": ["W-001"]}}]
        gates.level_plans.by_position[1] = ("prior", prior, Path("prior"))
    if orientation:
        gates.arc = [
            ArcPosition(
                plan["arc_ref"]["position"], "unit", 1, "job", None, "phase", "skill", [], [], band_key="a1-orientation"
            )
        ]
    return gates, closure


def assembly_world():
    g, _step = gate_world()
    plan = g.plan
    plan["lessons"][0]["steps"] = [_step]
    draft = {
        "status": "ok",
        "steps": [{"id": "s2", "blocks": [{"kind": "prose", "text": "Support first."}]}],
        "activities": [],
    }
    return draft, plan, {"texts": [{"id": "T-001", "quote": "model"}]}, {"words": []}


def test_assembler_prints_plan_without_draft_echo():
    draft, plan, pack, words = assembly_world()
    expanded, prov = assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)
    rendered, mapping = _render_urok_markdown(draft, expanded, pack, words)
    assert rendered.index("Support first.") < rendered.index(task()["instruction_en"])
    assert all(t in rendered for t in [task()["context_en"], *task()["success_criteria_en"], "Response: selection"])
    assert mapping.verify(rendered) == {
        i: unit["text"] for i, unit in enumerate(expanded["units"]) if unit["tab"] == "urok"
    }
    from scripts.build.fresh.assemble import get_provenance_validator

    get_provenance_validator().validate(prov)
    draft["steps"] = []
    with pytest.raises(AssemblerError, match="recap_task_order"):
        assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)


@pytest.mark.parametrize("section,record,selection,code", [
    ("texts", {**registered_quote("x" * 860), "source": {"kind": "textbook", "file": "unregistered", "page": 39}},
     "T-001", "publication_right"),
    ("texts", registered_quote("x" * 801), {"ref": "T-001", "words": ["x"]}, "publication_limit"),
    ("texts", {**registered_quote(), "source": {**registered_quote()["source"], "page": None}},
     "T-001", "publication_attribution"),
    ("texts", {"id": "T-001", "text": "model"}, "T-001", "learner_text_not_allowed"),
    ("texts", {**registered_quote(), "text": "sibling"}, "T-001", "learner_text_not_allowed"),
    ("examples", {"id": "EX-001", "text": "model", "items_sample": ["sibling"]},
     "EX-001", "learner_text_not_allowed"),
    ("exercises", {"id": "X-001", "items_sample": ["model"]}, "X-001", "learner_text_not_allowed"),
    ("examples", {"id": "T-001", "text": "model"}, "T-001", "learner_text_not_allowed"),
    ("texts", registered_quote(), {"ref": "T-001", "words": ["models"]}, "recap_task_print"),
    ("texts", registered_quote(), {"ref": "T-001", "words": ["Model"]}, "recap_task_print"),
    ("texts", registered_quote(), {"ref": "T-001", "words": []}, "recap_task_print"),
    ("examples", {"id": "EX-001", "text": ""}, "EX-001", "recap_task_print"),
    ("examples", {"id": "EX-001"}, "EX-001", "recap_task_print"),
    ("examples", {"id": "EX-001", "text": None}, "EX-001", "recap_task_print"),
    ("texts", registered_quote(), "T-999", "recap_task_print"),
])
def test_recap_source_refusals_agree_in_assembly_and_validation(tmp_path, section, record, selection, code):
    import yaml

    draft, plan, _pack, words = assembly_world()
    step = plan["lessons"][0]["steps"][0]
    ref = selection if isinstance(selection, str) else selection["ref"]
    step["evidence"] = [ref]
    step["task"]["learner_reads"] = [selection]
    pack = {section: [record]}
    with pytest.raises(AssemblerError) as exc:
        assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)
    assert exc.value.code == code
    path = tmp_path / "pack.yaml"
    path.write_text(yaml.safe_dump(pack))
    gates, closure = gate_world()
    gates.pack = load_pack(path)
    # Aggregate print is deliberately present even for absent refs: it cannot grant permission.
    gates.pack.record_texts[ref] = "model"
    closure["evidence"] = [ref]
    closure["task"]["learner_reads"] = [selection]
    gates.check_practical_recaps()
    assert codes.RECAP_TASK_PRINT in gates.report.codes()


def produced_recap_codes() -> set[str]:
    """Actual outcomes from public fixture mutations, for the validator registry check."""
    produced = set()
    for change in [
        lambda g, s: s.pop("task"),
        lambda g, s: s["task"].update(instruction_en=" "),
        lambda g, s: s["task"].update(instruction_en="Choose 'село'."),
        lambda g, s: s["uses"].update(vocabulary=["W-999"]),
        lambda g, s: g.plan["lessons"][0]["steps"].append({"id": "s3", "kind": "practice"}),
        lambda g, s: s["task"].update(learner_reads=["T-999"]),
    ]:
        g, s = gate_world()
        change(g, s)
        g.check_practical_recaps()
        produced |= g.report.codes()
    g, _ = gate_world(embedded=True, orientation=True)
    g.check_practical_recaps()
    return produced | g.report.codes()


def quoted_task_world(tmp_path, quote="село", *, slug="sample-slug"):
    """Controlled locked disk fixture from existing captured source facts."""
    import sqlite3

    from scripts.curriculum.evidence import lesson_lock, lock
    from tests.build.test_fresh_assemble import (
        make_draft,
        make_pack,
        make_plan,
        make_plan_lesson,
        make_text_record,
        make_word_record,
        make_words_store,
    )

    capture = json.loads((ROOT / "tests/fixtures/stress-ci.json").read_text())
    captured = next(row for row in capture["forms"] if row["form_unstressed"] == "село")
    analysis = capture["vesum"]["село"][0]
    word = make_word_record(1, "село", forms=[{
        "form": "село", "tags": analysis["tags"], "stress_source": "ulif", "markers": [],
        "learner": True, "stressed": captured["pedagogical_stressed_form"],
    }])
    base_analysis = capture["vesum"]["апостроф"][0]
    base_form = next(row for row in capture["forms"] if row["form_unstressed"] == "апостроф")
    base_word = make_word_record(2, "апостроф", forms=[{
        "form": "апостроф", "tags": base_analysis["tags"], "stress_source": "ulif", "markers": [],
        "learner": True, "stressed": base_form["pedagogical_stressed_form"],
    }])
    untaught_analysis = capture["vesum"]["замок"][0]
    untaught_form = next(row for row in capture["forms"] if row["form_unstressed"] == "замок")
    untaught_word = make_word_record(3, "замок", forms=[{
        "form": "замок", "tags": untaught_analysis["tags"], "stress_source": "ulif", "markers": [],
        "learner": True, "stressed": untaught_form["pedagogical_stressed_form"],
    }])
    words = make_words_store(words=[word, base_word, untaught_word])
    introduction = {
        "id": "s1", "kind": "teach", "teach": "Teach the recorded model.",
        "evidence": ["T-1"], "introduces": {"vocabulary": ["W-1"], "grammar": [], "letters": list("село")},
        "uses": {"vocabulary": [], "grammar": []}, "practice": [],
    }
    closing = {
        "id": "s2", "kind": "recap", "task": task(), "evidence": ["T-1"],
        "uses": {"vocabulary": ["W-1"], "grammar": []}, "practice": [],
    }
    closing["task"]["learner_reads"] = [{"ref": "T-1", "words": ["село"]}]
    closing["task"].update(
        context_en=f"The familiar label is '{quote}'.", instruction_en=f"Choose '{quote}' for this context.",
        success_criteria_en=[f"Say '{quote}' for the appropriate context."],
    )
    lesson = make_plan_lesson(1, [introduction, closing], core_words=[word])
    lesson["closes_with_recap"] = True
    lesson["inventory"]["phonetics"] = {"letters": list("село"), "sounds": []}
    plan = make_plan(lessons=[lesson], module=slug)
    pack = make_pack(texts=[make_text_record(1, "село")])
    plans_dir, evidence_dir = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1", tmp_path / "curriculum/l2-uk-en/evidence/a1"
    plans_dir.mkdir(parents=True)
    evidence_dir.mkdir(parents=True)
    for path, data in [
        (plans_dir / f"{slug}.yaml", plan), (evidence_dir / f"{slug}.yaml", pack),
        (evidence_dir / "_words.yaml", words),
        (evidence_dir / "_base.request.yaml", {"words": [{"lemma": "апостроф", "pos": "noun"}]}),
    ]:
        path.write_bytes(lock.yaml_bytes(data))
        lock.write(path)
    locked = lesson_lock.compute_lesson_lock(
        "a1", slug, plans_dir=plans_dir, evidence_dir=evidence_dir, repo_root=tmp_path,
    )
    lock_path = evidence_dir / f"_state/{slug}/lessons.lock.yaml"
    lock_path.parent.mkdir(parents=True)
    lock.write(lock_path, lock.yaml_bytes(locked))
    draft = make_draft(
        module=f"a1/{slug}",
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "Teach the familiar label.", "explains": ["T-1"]}]},
               {"id": "s2", "blocks": [{"kind": "prose", "text": "Use it in context.", "explains": ["T-1"]}]}],
        lesson_lock_entry_sha256=locked["lessons"][0]["entry_sha256"],
    )
    # A small database of captured VESUM analyses supports outside-state diagnostics.
    vesum_db = tmp_path / "captured-vesum.db"
    with sqlite3.connect(vesum_db) as conn:
        conn.executescript("""
            CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER,
                word_form TEXT, lemma TEXT, pos TEXT, tags TEXT, source_comment TEXT, source_location TEXT);
            CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT);
            CREATE TABLE vesum_build_metadata (key TEXT, value TEXT);
            CREATE VIEW forms AS SELECT word_form, lemma, pos, tags FROM forms_all;
        """)
        conn.execute("INSERT INTO vesum_build_metadata VALUES (?,?)", (
            "canonical_jsonl_sha256", hashlib.sha256(json.dumps(capture["vesum"]).encode()).hexdigest(),
        ))
        row_id = 0
        for spelling in ("село", "замок"):
            for row in capture["vesum"][spelling]:
                row_id += 1
                conn.execute("INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)", (
                    row_id, row_id, spelling, row["lemma"], row["pos"], row["tags"], "", f"capture:{row_id}",
                ))
    (lock_path.parent / "lesson-1.draft.yaml").write_bytes(lock.yaml_bytes(draft))
    return {
        "plan": plan, "pack": pack, "words": words, "draft": draft,
        "plans_dir": plans_dir, "evidence_dir": evidence_dir, "vesum_db": vesum_db,
        "captured": captured,
    }


@pytest.mark.parametrize("quote,taught", [
    pytest.param("село", True, marks=pytest.mark.site_toolchain),
    ("замок", False),
])
def test_quoted_tasks_real_resolution_stress_and_check9(tmp_path, monkeypatch, quote, taught):
    """Real assembly, allowlist, resolver, locks, stress, render and check11 on both cases."""
    import yaml

    from scripts.build.fresh.assemble import check_5_assembly, check_9_stress_and_render
    from scripts.curriculum.evidence.sources import Sources
    from scripts.curriculum.resolver import codes as resolver_codes
    from scripts.curriculum.resolver.inputs import ExpandedDocument
    from scripts.curriculum.resolver.stream import load_allowlist, resolve

    world = quoted_task_world(tmp_path, quote)
    plan, pack, words, draft = (world[key] for key in ("plan", "pack", "words", "draft"))
    plans_dir, evidence_dir, vesum_db, captured = (world[key] for key in (
        "plans_dir", "evidence_dir", "vesum_db", "captured",
    ))
    assembled = check_5_assembly(draft, plan, pack, words, "a1", "sample-slug", 1)
    assert assembled.passed, assembled.to_dict()
    expanded = assembled.artifacts["expanded_doc"]
    instructions = [u for u in expanded["units"] if str(u["block"]).startswith("recap_")
                    and not str(u["block"]).startswith(("recap_print", "recap_attribution"))]
    assert len([u for u in instructions if quote in u["text"]]) == 3
    assert all(u["role"] == "instruction" for u in instructions)
    printed = [u for u in expanded["units"] if str(u["block"]).startswith("recap_print")]
    assert len(printed) == 1 and printed[0]["text"] == "село"
    assert printed[0]["role"] == "record_print"

    with Sources(vesum_db=vesum_db, sources_db=tmp_path / "unused-sources.db") as sources:
        allowlist = load_allowlist(
            "a1", "sample-slug", 1, plans_dir=plans_dir, evidence_dir=evidence_dir,
        )
        assert set(allowlist.records) == {"W-1", "W-2"}
        stream = resolve(ExpandedDocument.from_data(expanded), allowlist, sources)
    quoted_tokens = [t for t in stream.tokens if t["token"] == quote and t["role"] == "instruction"]
    assert len(quoted_tokens) == 3
    from scripts.build.fresh.assemble import assemble_lesson

    closed_sources = []

    class CapturedSources(Sources):
        def close(self):
            super().close()
            closed_sources.append(self)

    monkeypatch.setattr("scripts.build.fresh.assemble.Sources", lambda: CapturedSources(
        vesum_db=vesum_db, sources_db=tmp_path / "unused-sources.db",
    ))
    full = assemble_lesson(
        "a1", "sample-slug", 1, repo_root=tmp_path, draft_dict=draft,
        plan_dict=plan, pack_dict=pack, words_dict=words, plans_dir=plans_dir,
        evidence_dir=evidence_dir, output_dir=tmp_path / "full-state", site_dir=tmp_path / "full-site",
    )
    assert len(closed_sources) == 1
    assert closed_sources[0]._conn is None and closed_sources[0]._receipt_words == {}
    if not taught:
        assert {t["class"] for t in quoted_tokens} == {resolver_codes.LEMMA_OUTSIDE_STATE}
        assert len(stream.failures) == 3
        assert not (tmp_path / "site/1.mdx").exists()
        print("quoted_tasks: assembly=PASS resolver=lemma_outside_state (3) render=not_attempted")
        print("production_assembly_untaught:", json.dumps(full, ensure_ascii=False, default=str))
        assert not full.get("check_9", {}).get("passed"), full
        assert full["failure"]["layer"] == "stream", full
        assert full["failure"]["check"] == 9
        assert full["blocking_tokens"] == [quote] * 3, full
        assert full["blocking_token_classes"] == [resolver_codes.LEMMA_OUTSIDE_STATE] * 3, full
        assert not (tmp_path / "full-site/1.mdx").exists()
        return
    assert full["ok"], full
    assert full["check_5"]["passed"] and full["check_9"]["passed"] and full["check_11"]["passed"], full
    print("production_check11_artifact:", json.dumps(full["check_11"], ensure_ascii=False, default=str))
    full_mdx = (tmp_path / "full-site/1.mdx").read_text()
    assert full_mdx.count(captured["pedagogical_stressed_form"]) >= 4
    assert "recap_print" in (tmp_path / "full-state/lesson-1.expanded.yaml").read_text()
    print("production_assembly_taught: check5=PASS resolver=resolved check9=PASS check11=PASS MDX=written")
    assert stream.failures == [] and stream.open_tokens() == []
    assert all(t["selected"]["stressed"] == captured["pedagogical_stressed_form"] for t in quoted_tokens)
    rendered = check_9_stress_and_render(
        expanded, draft, plan, pack, words, stream, "a1", "sample-slug", 1,
        provenance_doc=assembled.artifacts["provenance"], repo_root=tmp_path,
        plans_dir=plans_dir, evidence_dir=evidence_dir, output_dir=tmp_path / "state", site_dir=tmp_path / "site",
    )
    assert rendered.passed, rendered.to_dict()
    mdx = (tmp_path / "site/1.mdx").read_text()
    assert mdx.count(captured["pedagogical_stressed_form"]) >= 3
    stressed = yaml.safe_load((tmp_path / "state/lesson-1.stressed.yaml").read_text())
    assert all(captured["pedagogical_stressed_form"] in u["text"] for u in stressed["units"]
               if str(u["block"]).startswith("recap_") and quote in u["text"])
    print("quoted_tasks: assembly=PASS resolver=resolved (3) check9=PASS MDX=written")
