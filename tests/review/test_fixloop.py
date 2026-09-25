"""The fix loop (#8430 R2b-A): layers, signal, budgets, closure, the module verdict, terminal transitions."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import ValidationError

from scripts.review import findings_db as db
from scripts.review import fixloop
from tests.review.test_record import ITEM, LEVEL, PROSE, SLUG, World, finding, unsupported

pytestmark = pytest.mark.reads_content

PARAMS = db.load_parameters()


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    return World(tmp_path, monkeypatch)


# --- layer assignment from provenance ---------------------------------------------------------


def span(
    text: str,
    *,
    tab: str = "urok",
    activity: str | None = None,
    item: int | None = None,
    block: int = 0,
    index: int = 0,
    source: str = "record",
    kind: str | None = "quote",
    side: str | None = None,
    origin: str | None = None,
    key: bool | None = None,
    start: int = 0,
) -> dict[str, Any]:
    return {
        "tab": tab,
        "step": None,
        "activity": activity,
        "item": item,
        "block": block,
        "span": index,
        "start": start,
        "end": start + len(text),
        "source": source,
        "ref": "T-1" if source == "record" else None,
        "role": "record_print" if source == "record" else "narration",
        "text": text,
        "record_kind": kind if source == "record" else None,
        "record_side": side,
        "option_origin": origin,
        "is_key": key,
    }


def provenance(*spans: dict[str, Any]) -> dict[str, Any]:
    return {"provenance_schema": 1, "lesson": {"level": LEVEL, "slug": SLUG, "n": 1}, "spans": list(spans)}


def located(quote: str, **location: Any) -> dict[str, Any]:
    return finding("F-01", locations=[{"tab": location.pop("tab", "urok"), "quote": quote, **location}])


@pytest.mark.parametrize(
    ("kind", "layer"),
    [
        ("word", "word_store"),
        ("quote", "pack"),
        ("example", "pack"),
        ("exercise_text", "pack"),
        ("error", "pack"),
        ("note", "pack"),
        ("video", "pack"),
        ("resource", "pack"),
    ],
)
def test_a_defective_span_the_engine_printed_from_a_record_is_that_records_layer(kind: str, layer: str) -> None:
    assert fixloop.layer_for_finding(located("alpha"), provenance(span("alpha", kind=kind)), kind="lesson") == layer


def test_writer_prose_is_regenerated() -> None:
    assert (
        fixloop.layer_for_finding(located("alpha"), provenance(span("alpha", source="writer_prose")), kind="lesson")
        == "regenerate_lesson"
    )


def test_the_incorrect_side_of_an_error_record_is_never_blamed() -> None:
    data = provenance(
        span("wrong", tab="vpravy", activity="a1", item=0, kind="error", side="incorrect"),
        span("right", tab="vpravy", activity="a1", item=0, index=1, start=5, kind="error", side="correct"),
    )
    at = {"tab": "vpravy", "activity": "a1", "item": 0}
    assert fixloop.layer_for_finding(located("wrong", **at), data, kind="lesson") == "not_blamed"
    assert (
        fixloop.layer_for_finding(located("right", **at), data, kind="lesson") == "pack"
    )  # the correct side is the pack's


def test_a_typed_distractor_is_never_blamed_but_a_typed_key_is_the_writers() -> None:
    at = {"tab": "vpravy", "activity": "a1", "item": 0}
    distractor = span(
        "opt-a", tab="vpravy", activity="a1", item=0, source="writer_prose", origin="writer_typed", key=False
    )
    typed_key = span(
        "opt-b",
        tab="vpravy",
        activity="a1",
        item=0,
        index=1,
        start=5,
        source="writer_prose",
        origin="writer_typed",
        key=True,
    )
    store_distractor = span(
        "opt-c", tab="vpravy", activity="a1", item=0, index=2, start=10, kind="word", origin="store", key=False
    )
    data = provenance(distractor, typed_key, store_distractor)
    assert fixloop.layer_for_finding(located("opt-a", **at), data, kind="lesson") == "not_blamed"
    assert fixloop.layer_for_finding(located("opt-b", **at), data, kind="lesson") == "regenerate_lesson"
    assert (
        fixloop.layer_for_finding(located("opt-c", **at), data, kind="lesson") == "word_store"
    )  # an engine-made option is the store's


def test_a_span_that_is_not_blamed_never_takes_the_blame_from_one_that_is() -> None:
    data = provenance(
        span("wrong ", kind="error", side="incorrect"), span("prose", index=1, start=6, source="writer_prose")
    )
    both = finding("F-01", locations=[{"tab": "urok", "quote": "wrong"}, {"tab": "urok", "quote": "prose"}])
    assert fixloop.layer_for_finding(both, data, kind="lesson") == "regenerate_lesson"


def test_several_layers_are_mixed_and_a_quote_across_two_spans_implicates_both() -> None:
    data = provenance(span("left ", kind="word"), span("right", index=1, start=5, kind="quote"))
    assert fixloop.layer_for_finding(located("left right"), data, kind="lesson") == "mixed"
    assert fixloop.layer_for_finding(located("left"), data, kind="lesson") == "word_store"


def test_the_quote_is_matched_the_way_the_validator_folds_it() -> None:
    data = provenance(span("сло́во", kind="word"))
    assert fixloop.layer_for_finding(located("слово"), data, kind="lesson") == "word_store"


def test_a_location_names_its_own_unit() -> None:
    data = provenance(
        span("same", tab="vpravy", activity="a1", item=0, kind="error", side="incorrect"),
        span("same", tab="vpravy", activity="a1", item=1, source="writer_prose"),
    )
    assert (
        fixloop.layer_for_finding(located("same", tab="vpravy", activity="a1", item=1), data, kind="lesson")
        == "regenerate_lesson"
    )
    assert (
        fixloop.layer_for_finding(located("same", tab="vpravy", activity="a1", item=0), data, kind="lesson")
        == "not_blamed"
    )
    assert fixloop.layer_for_finding(located("same", tab="urok"), data, kind="lesson") == "unlocated"


def test_findings_that_provenance_cannot_place_are_unlocated_not_guessed() -> None:
    assert fixloop.layer_for_finding(located("nowhere"), provenance(span("alpha")), kind="lesson") == "unlocated"
    assert fixloop.layer_for_finding(located("alpha"), None, kind="lesson") == "unlocated"


@pytest.mark.parametrize(
    ("dimension", "layer"),
    [("plan_defect", "plan"), ("evidence_gap", "pack_builder"), ("engine_or_gate", "engine")],
)
def test_the_dimensions_that_name_their_own_layer(dimension: str, layer: str) -> None:
    assert (
        fixloop.layer_for_finding(
            located(
                "alpha",
            ),
            None,
            kind="lesson",
        )
        == "unlocated"
    )
    assert fixloop.layer_for_finding({**located("alpha"), "dimension": dimension}, None, kind="lesson") == layer


def test_an_absence_finding_is_the_writers_and_a_plan_review_finding_is_the_plans() -> None:
    absence = finding("F-01", locations=[], scope={"tab": "urok"})
    assert fixloop.layer_for_finding(absence, None, kind="lesson") == "regenerate_lesson"
    assert fixloop.layer_for_finding(located("alpha"), None, kind="plan") == "plan"
    assert (
        fixloop.layer_for_finding({**located("alpha"), "dimension": "evidence_gap"}, None, kind="plan")
        == "pack_builder"
    )


def test_a_resolved_finding_has_no_layer() -> None:
    assert (
        fixloop.layer_for_finding({**located("alpha"), "status": "resolved"}, provenance(span("alpha")), kind="lesson")
        is None
    )


def test_provenance_is_validated_against_its_schema(tmp_path: Path) -> None:
    good = provenance(span("alpha"))
    (tmp_path / "lesson-1.provenance.yaml").write_text(yaml.safe_dump(good), encoding="utf-8")
    assert fixloop.load_provenance(tmp_path, 1)["spans"][0]["text"] == "alpha"
    bad = provenance({**span("alpha"), "record_kind": "mystery"})
    (tmp_path / "lesson-2.provenance.yaml").write_text(yaml.safe_dump(bad), encoding="utf-8")
    for n in (2, 3):
        with pytest.raises(fixloop.ProvenanceError):
            fixloop.load_provenance(tmp_path, n)


def test_layers_are_recorded_from_the_real_provenance_and_never_blame_by_design_spans(world: World) -> None:
    world.provenance(
        2,
        [
            span(PROSE, kind="quote"),
            span(ITEM, tab="vpravy", activity="act-1", item=0, kind="error", side="incorrect"),
        ],
    )
    findings = [
        finding("F-01"),
        finding(
            "F-02", dimension="activity", locations=[{"tab": "vpravy", "activity": "act-1", "item": 0, "quote": ITEM}]
        ),
    ]
    world.record(world.make_return(2, findings))
    layers = {row["finding_id"]: row["layer"] for row in world.db_rows("findings")}
    assert layers == {"F-01": "pack", "F-02": "not_blamed"}


# --- the signal, the gate list, the level-wide count ----------------------------------------------------


def test_the_same_dimension_and_sub_dimension_in_two_lessons_is_printed_and_nothing_is_done(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    for n in (1, 2):
        world.record(
            world.make_return(n, [finding("F-01", dimension="language", sub_dimension="calque", severity="MAJOR")])
        )
    world.record(world.make_return(3, [finding("F-01", dimension="language", sub_dimension="stress")]))
    world.record(world.make_return(3, [finding("F-02", dimension="job")]))
    before = _dump_db(world.db)
    conn = db.connect(world.db)
    try:
        report = fixloop.build_report(conn, LEVEL, SLUG, root=world.root, params=PARAMS)
        text = fixloop.render_report(report)
    finally:
        conn.close()
    assert report["signal"] == [{"dimension": "language", "sub_dimension": "calque", "lessons": [1, 2]}]
    assert "SIGNAL (no automatic branch): language/calque in lessons [1, 2]" in text
    assert _dump_db(world.db) == before  # no automatic branch: reading the signal changes nothing
    assert not (world.state_dir / fixloop.MODULE_VERDICT_NAME).exists()


def _dump_db(path: Path) -> dict[str, list]:
    conn = sqlite3.connect(path)
    try:
        return {
            table: conn.execute(f"SELECT * FROM {table}").fetchall()
            for table in ("attempts", "findings", "budgets", "settle_items", "agreement")
        }
    finally:
        conn.close()


def test_a_seeded_lesson_adds_nothing_to_the_signal(world: World) -> None:
    world.record(world.make_return(1, [finding("F-01", dimension="language", sub_dimension="calque")]))
    world.record(
        world.make_return(2, [finding("F-01", dimension="language", sub_dimension="calque")]), seed_id="seed-1"
    )
    conn = db.connect(world.db)
    try:
        assert fixloop.same_dimension_signal(db.module_findings(conn, LEVEL, SLUG)) == []
    finally:
        conn.close()


def test_findings_that_could_be_a_gate_are_listed_when_they_match_the_schemas_pattern() -> None:
    rows = [
        {
            "review_id": "R",
            "attempt_id": "A",
            "finding_id": "F-01",
            "lesson_n": 1,
            "dimension": "job",
            "status": "active",
            "could_be_a_gate": "yes - count the words",
        },
        {
            "review_id": "R",
            "attempt_id": "A",
            "finding_id": "F-02",
            "lesson_n": 1,
            "dimension": "job",
            "status": "active",
            "could_be_a_gate": "no",
        },
        {
            "review_id": "R",
            "attempt_id": "A",
            "finding_id": "F-03",
            "lesson_n": 1,
            "dimension": "job",
            "status": "active",
            "could_be_a_gate": None,
        },
        {
            "review_id": "R",
            "attempt_id": "A",
            "finding_id": "F-04",
            "lesson_n": 2,
            "dimension": "fact",
            "status": "resolved",
            "could_be_a_gate": "yes - old",
        },
        {
            "review_id": "R",
            "attempt_id": "A",
            "finding_id": "F-05",
            "lesson_n": 2,
            "dimension": "fact",
            "status": "persisting",
            "could_be_a_gate": "yes - persists",
        },
        {
            "review_id": "R",
            "attempt_id": "A",
            "finding_id": "F-06",
            "lesson_n": 2,
            "dimension": "fact",
            "status": "active",
            "could_be_a_gate": "yes",
        },
    ]
    listed = fixloop.gate_candidates(rows, PARAMS["gate_candidate_pattern"])
    assert [(item["finding_ref"], item["could_be_a_gate"]) for item in listed] == [
        ("R/A/F-01", "yes - count the words"),
        ("R/A/F-05", "yes - persists"),
    ]


def test_the_report_lists_the_gate_candidates_for_the_driver(world: World) -> None:
    world.record(
        world.make_return(
            1,
            [
                finding("F-01", could_be_a_gate="yes - a script could count them"),
                finding("F-02", dimension="fact", could_be_a_gate="no"),
            ],
        )
    )
    conn = db.connect(world.db)
    try:
        report = fixloop.build_report(conn, LEVEL, SLUG, root=world.root, params=PARAMS)
    finally:
        conn.close()
    assert [item["could_be_a_gate"] for item in report["gate_candidates"]] == ["yes - a script could count them"]
    assert "GATE CANDIDATE" in fixloop.render_report(report)


def test_the_same_unsupported_claim_in_three_lessons_goes_to_the_operator(world: World) -> None:
    for n in (1, 2):
        world.record(world.make_return(n, [unsupported("F-01")]))
    conn = db.connect(world.db)
    try:
        [two] = fixloop.unsupported_claim_counts(conn, 3)
        assert two["to_operator"] is False and len(two["lessons"]) == 2
        world.record(world.make_return(3, [unsupported("F-01")]))
        [three] = fixloop.unsupported_claim_counts(conn, 3)
        assert three["to_operator"] is True and len(three["lessons"]) == 3
        report = fixloop.build_report(conn, LEVEL, SLUG, root=world.root, params=PARAMS)
    finally:
        conn.close()
    assert fixloop.REASON_UNSUPPORTED_LESSONS in {item["reason"] for item in report["terminal"]}


# --- budgets survive changes upstream ---------------------------------------------------------------


def test_the_budget_is_keyed_by_module_and_lesson_and_survives_a_plan_pack_or_card_change(world: World) -> None:
    world.record(world.make_return(2, [finding("F-01", severity="MAJOR")]))
    first = world.digest(2)
    plan = world.plan_dir / f"{SLUG}.yaml"
    plan.write_bytes(plan.read_bytes() + b"# the plan was edited\n")
    pack = world.evidence_dir / f"{SLUG}.yaml"
    from scripts.curriculum.evidence import lock

    lock.write(pack, pack.read_bytes() + b"# the pack was rebuilt\n")
    card = world.root / "docs/style-cards/a1.md"
    card.write_text("A1 style, revised\n", encoding="utf-8")
    import hashlib

    (world.root / "docs/style-cards/a1.sha256").write_text(
        hashlib.sha256(card.read_bytes()).hexdigest() + "\n", encoding="ascii"
    )
    world.write_manifests()
    assert world.digest(2) != first  # every input the count could have hung on has changed
    world.record(world.make_return(2, [finding("F-01", severity="MAJOR")]))
    rows = world.db_rows("budgets")
    assert [(row["level"], row["slug"], row["lesson_n"], row["revise_rounds"]) for row in rows] == [(LEVEL, SLUG, 2, 2)]


def test_the_regeneration_budget_is_twice_the_lesson_count_then_terminal(world: World) -> None:
    world.closure()
    conn = db.connect(world.db)
    closure = fixloop.read_closure(world.state_dir)
    lessons = [1, 2, 3]
    try:
        spent = [fixloop.regenerate(conn, LEVEL, SLUG, n, lessons, PARAMS, closure) for n in (1, 2, 3, 1, 2, 3)]
        assert [row["regenerations"] for row in spent] == [1, 2, 3, 4, 5, 6] and spent[0]["limit"] == 6
        assert (
            spent[0]["stale_until_re_reviewed"] == [2, 3]
            and spent[1]["stale_until_re_reviewed"] == [3]
            and spent[2]["stale_until_re_reviewed"] == []
        )
        with pytest.raises(fixloop.TerminalTransition) as terminal:
            fixloop.regenerate(conn, LEVEL, SLUG, 2, lessons, PARAMS, closure)
        assert terminal.value.reason == fixloop.REASON_REGENERATIONS
        assert (
            sum(row["regenerations"] for row in db.module_budgets(conn, LEVEL, SLUG).values()) == 6
        )  # nothing was spent
        with pytest.raises(fixloop.FixLoopError, match="not a lesson"):
            fixloop.regenerate(conn, LEVEL, SLUG, 9, lessons, PARAMS, closure)
    finally:
        conn.close()


def test_no_regeneration_after_the_third_revise_round(world: World) -> None:
    for _ in range(3):
        world.record(world.make_return(2, [finding("F-01", severity="MAJOR")]))
    conn = db.connect(world.db)
    try:
        with pytest.raises(fixloop.TerminalTransition) as terminal:
            fixloop.regenerate(conn, LEVEL, SLUG, 2, [1, 2, 3], PARAMS, None)
        assert terminal.value.reason == fixloop.REASON_REVISE
        assert (
            fixloop.regenerate(conn, LEVEL, SLUG, 1, [1, 2, 3], PARAMS, None)["regenerations"] == 1
        )  # other lessons still may
    finally:
        conn.close()


def test_every_terminal_path_is_named_operator(world: World) -> None:
    import scripts.review.record as record_module

    for _ in range(3):
        world.record(world.make_return(1, [finding("F-01", severity="MAJOR")]))  # revise budget
    for i in range(3):  # review failures
        record_module.record_return(
            None,
            manifest_path=world.manifest(2),
            task_id="review-claude",
            repo_root=world.root,
            db_path=world.db,
            tasks_dir=world.tasks_dir,
            review_id=f"rf-{i}",
            attempt_id=f"af-{i}",
            failure="timeout",
        )
    conn = db.connect(world.db)
    try:
        with db.transaction(conn):
            db.mark_disputed(conn, LEVEL, SLUG, 3, "the writer's lane disputes the verdict")
            item = db.open_settle_item(
                conn,
                ref="R/A/F-9",
                kind="unsupported_by_source",
                level=LEVEL,
                slug=SLUG,
                lesson_n=3,
                manifest_sha256=None,
                opened_at="t",
            )
        db.record_settle_outcome(conn, item, "unresolved", [], "settle-seat")
        found = fixloop.terminal_transitions(conn, LEVEL, SLUG, [1, 2, 3], PARAMS, needs_regeneration=False)
    finally:
        conn.close()
    assert {entry["reason"] for entry in found} == {
        fixloop.REASON_REVISE,
        fixloop.REASON_REVIEW_FAILURE,
        fixloop.REASON_DISPUTED,
        fixloop.REASON_SETTLE,
    }
    assert {entry["transition"] for entry in found} == {"operator"}


def test_the_regeneration_terminal_needs_a_lesson_that_still_wants_one(world: World) -> None:
    conn = db.connect(world.db)
    try:
        with db.transaction(conn):
            for n in (1, 2, 3):
                db.bump_budget(conn, LEVEL, SLUG, n, "regenerations")
                db.bump_budget(conn, LEVEL, SLUG, n, "regenerations")
        assert fixloop.terminal_transitions(conn, LEVEL, SLUG, [1, 2, 3], PARAMS, needs_regeneration=False) == []
        [entry] = fixloop.terminal_transitions(conn, LEVEL, SLUG, [1, 2, 3], PARAMS, needs_regeneration=True)
        assert entry["reason"] == fixloop.REASON_REGENERATIONS and entry["transition"] == "operator"
    finally:
        conn.close()


# --- the dependency closure ---------------------------------------------------------------------------------


def test_the_closure_is_read_from_the_engines_file_and_names_the_lessons_after_k(world: World) -> None:
    assert fixloop.read_closure(world.state_dir) is None
    world.closure()
    closure = fixloop.read_closure(world.state_dir)
    assert (
        fixloop.dependents(closure, 1) == [2, 3]
        and fixloop.dependents(closure, 2) == [3]
        and fixloop.dependents(closure, 3) == []
    )
    (world.page_dir / "1.mdx").write_text("# Lesson 1 regenerated\n", encoding="utf-8")
    world.closure()
    closure = fixloop.read_closure(world.state_dir)
    assert {row["n"] for row in closure["stale"] if row.get("upstream") == 1} == {2, 3}
    assert fixloop.dependents(closure, 1) == [2, 3]


# --- the module verdict ---------------------------------------------------------------------------------------------


@pytest.fixture
def promoted(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.build.fresh import plan_manifest as pm

    monkeypatch.setattr(
        pm,
        "plan_review_status",
        lambda *a, **kw: {
            "state": "reviewed_promoted",
            "manifest_sha256": "0" * 64,
            "attempt_id": "plan-1",
            "stale": {},
        },
    )


def verdict(world: World, **kwargs: Any) -> dict[str, Any]:
    conn = db.connect(world.db)
    try:
        return fixloop.compute_module_verdict(conn, LEVEL, SLUG, root=world.root, params=PARAMS, **kwargs)
    finally:
        conn.close()


def approve_all(world: World) -> None:
    for n in (1, 2, 3):
        assert world.record(world.make_return(n)).verdict == "APPROVE"
    world.closure()


def codes_of(document: dict[str, Any]) -> list[str]:
    return [hold["code"] for hold in document["holds"]]


def test_a_module_whose_lessons_are_approved_on_current_manifests_and_whose_plan_is_promoted_is_approved(
    world: World, promoted: None
) -> None:
    approve_all(world)
    document = verdict(world)
    assert document["verdict"] == "APPROVE" and document["holds"] == [] and document["terminal"] == []
    assert [(row["n"], row["kind"], row["state"], row["verdict"]) for row in document["lessons"]] == [
        (1, "lesson", "current", "APPROVE"),
        (2, "lesson", "current", "APPROVE"),
        (3, "recap", "current", "APPROVE"),
    ]
    assert [row["manifest_sha256"] for row in document["lessons"]] == [world.digest(n) for n in (1, 2, 3)]
    assert document["settle_items"] == {"open": [], "waiting_for_operator": [], "supported_defect_pending": []}
    assert document["plan"]["state"] == "reviewed_promoted"
    path = fixloop.write_module_verdict(world.root, document)
    assert path == world.state_dir / "module-verdict.yaml"
    on_disk = yaml.safe_load(path.read_bytes())
    assert on_disk == document and on_disk["verdict"] == "APPROVE"


def test_the_module_verdict_document_is_schema_checked() -> None:
    from jsonschema import Draft202012Validator

    with pytest.raises(ValidationError):
        Draft202012Validator(fixloop.MODULE_VERDICT_SCHEMA).validate({"module_verdict_schema": 1, "verdict": "MAYBE"})


def test_a_module_with_an_open_settle_item_is_not_approved(world: World, promoted: None) -> None:
    world.record(
        world.make_return(1, [unsupported("F-01")])
    )  # an unsupported claim is MINOR: the lesson itself is APPROVE
    world.record(world.make_return(2))
    world.record(world.make_return(3))
    world.closure()
    document = verdict(world)
    assert document["lessons"][0]["verdict"] == "APPROVE"
    assert document["verdict"] != "APPROVE" and "settle_open" in codes_of(document)
    [item] = document["settle_items"]["open"]
    assert item["kind"] == "unsupported_by_source" and item["lesson_n"] == 1
    conn = db.connect(world.db)
    try:
        db.record_settle_outcome(conn, item["item_id"], "refuted", ["r-1"], "settle-seat")
    finally:
        conn.close()
    assert verdict(world)["verdict"] == "APPROVE"  # refuted: the finding closes, no regeneration


def test_a_source_conflict_or_unresolved_item_holds_the_module_until_the_operator_decides(
    world: World, promoted: None
) -> None:
    world.record(world.make_return(1, [unsupported("F-01")]))
    world.record(world.make_return(2))
    world.record(world.make_return(3))
    world.closure()
    conn = db.connect(world.db)
    try:
        [item] = db.module_settle_items(conn, LEVEL, SLUG)
        db.record_settle_outcome(conn, item["item_id"], "source_conflict", ["r-1", "r-2"], "settle-seat")
        held = verdict(world)
        assert held["verdict"] == "HOLD" and codes_of(held).count("settle_operator_pending") == 1
        assert {entry["reason"] for entry in held["terminal"]} == {fixloop.REASON_SETTLE}
        db.record_operator_decision(conn, item["item_id"], "keep")
    finally:
        conn.close()
    assert verdict(world)["verdict"] == "APPROVE"


def test_a_confirmed_defect_holds_the_module_until_the_lesson_is_rebuilt_and_reviewed_again(
    world: World, promoted: None
) -> None:
    world.record(world.make_return(1))
    world.record(world.make_return(2, [unsupported("F-01")]))
    world.record(world.make_return(3))
    world.closure()
    conn = db.connect(world.db)
    try:
        [item] = db.module_settle_items(conn, LEVEL, SLUG)
        db.record_settle_outcome(conn, item["item_id"], "supported_defect", ["r-1"], "settle-seat")
    finally:
        conn.close()
    held = verdict(world)
    assert held["verdict"] == "REVISE" and "settle_supported_defect" in codes_of(held)
    (world.page_dir / "2.mdx").write_text("# Lesson 2 rebuilt\n", encoding="utf-8")
    world.write_manifests((2, 3))
    world.closure()
    assert verdict(world)["verdict"] != "APPROVE"  # the reviews of 2 and 3 are of superseded manifests
    world.record(world.make_return(2))
    world.record(world.make_return(3))
    world.closure()
    assert verdict(world)["verdict"] == "APPROVE"  # the defect item was of the earlier manifest


def test_a_lesson_that_is_not_reviewed_holds_the_module(world: World, promoted: None) -> None:
    world.record(world.make_return(1))
    world.record(world.make_return(2))
    world.closure()
    document = verdict(world)
    assert document["verdict"] == "HOLD" and codes_of(document) == ["lesson_unreviewed"]
    assert document["lessons"][2]["state"] == "unreviewed"


def test_a_lesson_with_a_current_revise_makes_the_module_revise(world: World, promoted: None) -> None:
    world.record(world.make_return(1))
    world.record(world.make_return(2, [finding("F-01", severity="MAJOR")]))
    world.record(world.make_return(3))
    world.closure()
    document = verdict(world)
    assert document["verdict"] == "REVISE" and codes_of(document) == ["lesson_revise"]


def test_the_third_revise_round_makes_the_verdict_a_hold_with_the_terminal_transition(
    world: World, promoted: None
) -> None:
    for n in (1, 3):
        world.record(world.make_return(n))
    for _ in range(3):
        world.record(world.make_return(2, [finding("F-01", severity="MAJOR")]))
    world.closure()
    document = verdict(world)
    assert document["verdict"] == "HOLD" and "terminal_operator" in codes_of(document)
    assert (
        document["terminal"][0]["transition"] == "operator"
        and document["terminal"][0]["reason"] == fixloop.REASON_REVISE
    )


def test_a_plan_that_is_not_promoted_holds_the_module(world: World) -> None:
    approve_all(world)
    document = verdict(world)
    assert document["verdict"] == "HOLD" and codes_of(document) == ["plan_not_promoted"]


def test_a_module_without_the_engines_closure_file_is_held(world: World, promoted: None) -> None:
    for n in (1, 2, 3):
        world.record(world.make_return(n))
    assert codes_of(verdict(world)) == ["closure_missing"]


def test_regenerating_lesson_one_makes_the_reviews_of_two_and_three_stale_until_they_are_reviewed_again(
    world: World, promoted: None
) -> None:
    approve_all(world)
    assert verdict(world)["verdict"] == "APPROVE"
    (world.page_dir / "1.mdx").write_text("# Lesson 1 regenerated\n", encoding="utf-8")
    world.closure()
    document = verdict(world)
    assert document["verdict"] == "HOLD"
    assert [(row["n"], row["state"]) for row in document["lessons"]] == [(1, "stale"), (2, "stale"), (3, "stale")]
    assert "upstream_lessons[0]" in " ".join(document["lessons"][1]["stale"])  # lesson 2 names the lesson it read
    world.write_manifests()  # the engine writes new manifests for the regenerated module
    world.closure()
    document = verdict(world)
    assert document["verdict"] == "HOLD" and all(row["state"] == "stale" for row in document["lessons"])
    assert any("newer manifest" in reason for reason in document["lessons"][1]["stale"])
    world.record(world.make_return(1))
    assert verdict(world)["verdict"] == "HOLD"  # lessons 2 and 3 are still of the superseded manifests
    world.record(world.make_return(2))
    assert verdict(world)["verdict"] == "HOLD"
    world.record(world.make_return(3))
    assert verdict(world)["verdict"] == "APPROVE"


def test_a_verdict_whose_manifest_of_record_is_gone_or_altered_is_stale(world: World, promoted: None) -> None:
    approve_all(world)
    history = world.state_dir / "manifests" / "lesson-2" / f"{world.digest(2)}.yaml"
    history.write_bytes(history.read_bytes() + b"# altered\n")
    assert "does not hash to its name" in verdict(world)["lessons"][1]["stale"][0]
    history.unlink()
    assert "missing" in verdict(world)["lessons"][1]["stale"][0]


def test_a_verdict_file_that_is_not_a_verdict_is_stale_not_trusted(world: World, promoted: None) -> None:
    approve_all(world)
    world.verdict_file(2).write_text("verdict: APPROVE\n", encoding="utf-8")
    row = verdict(world)["lessons"][1]
    assert row["state"] == "stale" and row["verdict"] is None


def test_a_seeded_review_never_reaches_the_module_verdict(world: World, promoted: None) -> None:
    approve_all(world)
    world.record(
        world.make_return(2, [unsupported("F-01"), finding("F-02", severity="BLOCKER", dimension="fact")]),
        seed_id="seed-3",
    )
    document = verdict(world)
    assert document["verdict"] == "APPROVE" and document["settle_items"]["open"] == []


# --- the CLI -------------------------------------------------------------------------------------------------------------


def run(world: World, *argv: str) -> int:
    return fixloop.main(["--repo-root", str(world.root), "--db", str(world.db), *argv])


def test_the_cli_writes_the_module_verdict_and_prints_the_report(
    world: World, promoted: None, capsys: pytest.CaptureFixture[str]
) -> None:
    approve_all(world)
    assert run(world, "verdict", LEVEL, SLUG) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["verdict"] == "APPROVE" and printed["path"].endswith("_state/fixture-module/module-verdict.yaml")
    assert yaml.safe_load((world.state_dir / "module-verdict.yaml").read_bytes())["verdict"] == "APPROVE"
    assert run(world, "report", LEVEL, SLUG, "--json") == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "APPROVE" and report["terminal"] == [] and report["layers"] == {}
    assert run(world, "report", LEVEL, SLUG) == 0
    assert "module a1/fixture-module: APPROVE" in capsys.readouterr().out


def test_the_cli_refuses_a_regeneration_past_the_budget_with_the_operator_transition(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.closure()
    for _ in range(6):
        assert run(world, "regenerate", LEVEL, SLUG, "2") == 0
    capsys.readouterr()
    assert run(world, "regenerate", LEVEL, SLUG, "2") == 3
    assert json.loads(capsys.readouterr().out) == {
        "transition": "operator",
        "reason": fixloop.REASON_REGENERATIONS,
        "detail": "6 of 6 regenerations are spent",
    }


def test_the_cli_records_a_dispute_and_an_operator_decision(world: World, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(world, "dispute", LEVEL, SLUG, "2", "--reason", "the writer lane disputes it") == 3
    assert json.loads(capsys.readouterr().out)["reason"] == fixloop.REASON_DISPUTED
    conn = db.connect(world.db)
    try:
        with db.transaction(conn):
            item = db.open_settle_item(
                conn,
                ref="R/A/F-1",
                kind="unsupported_by_source",
                level=LEVEL,
                slug=SLUG,
                lesson_n=2,
                manifest_sha256=None,
                opened_at="t",
            )
        db.record_settle_outcome(conn, item, "unresolved", [], "settle-seat")
    finally:
        conn.close()
    assert run(world, "operator-decision", LEVEL, str(item), "--decision", "keep") == 0
    assert run(world, "operator-decision", LEVEL, str(item), "--decision", "again") == 2  # not waiting any more
    assert "not waiting for the operator" in capsys.readouterr().err


def test_the_help_states_use_and_exit_codes() -> None:
    text = fixloop.build_parser().format_help()
    for word in ("Use after", "Do NOT use", "Examples:", "Exit codes", "regenerate", "operator-decision"):
        assert word in text
