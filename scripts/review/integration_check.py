"""R2b integration check (#8430, "R2b integration check" of the R2b header): the review tooling, end to end.

Driver-run after R2b-A (records, fix loop, second seat), R2b-B (prompts) and R2b-C (settle) are on ``main``;
not the implementers' tests. It builds a module the way the engine does (the three-lesson fixture module of
``tests/build/test_fresh_e3b2.py`` with the plan-review world of ``tests/helpers/plan_review_world.py`` laid
over it: one plan, three built lessons, real manifests, real closure) in a directory of its own, never in the
repository's content trees, and drives the product paths through their own command-line entry points
(``record``, ``fixloop``, ``settle``, ``plan-promote``, ``plan-review-status``, the prompt renderer and checker).

``run-crafted``   cases (iii) layers, (v) second seat, (vi) staleness, (vii) budgets and signal, (viii) module
                  verdict, with crafted returns that pass the real validator (built from the fixture's own spans
                  and receipts of a fixture ledger; nothing of the validator is faked).
``prepare-real``  renders and checks the prompts of cases (i) plan review, (ii) lesson 2 review and (iv) the settle
                  item, and writes one dispatch card each. It dispatches nothing: the driver does.
``finish-real``   after the driver recorded the real returns: the remaining assertions of (i), (ii) and (iv).

This proves the tooling, not reviewer quality (admitting a reviewer is the seeded-defect measurement, R3).
Stand-ins, named: ``planned_state`` (lesson manifests) and ``pack-verify --strict`` (plan review) are replaced at
their one seam, as the repository's own tests do, because the real ones need the sources database.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import io
import json
import shlex
import shutil
import sqlite3
import sys
import traceback
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.agent_runtime import review_mcp
from scripts.build.fresh import plan_manifest
from scripts.build.fresh.cli import main as fresh_cli
from scripts.common.repo_root import resolve_repo_root
from scripts.curriculum.validate.validate import main as validate_main
from scripts.review import findings_db, fixloop, record, second_seat, settle
from scripts.review.prompts import check as prompt_check
from scripts.review.prompts import render as prompt_render
from scripts.review.receipts.ledger import create_empty_ledger
from tests.build.test_fresh_plan_review import fake_verify
from tests.curriculum import test_plan_validate as plan_fixture
from tests.helpers import plan_review_world
from tests.review.test_fixloop import span
from tests.review.test_r1_schema_ledger import PLAN_CHECKS, _dump, _review
from tests.review.test_record import LEVEL, PROSE, SLUG, World, finding, unsupported

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY = resolve_repo_root(Path(__file__), 2)  # batch_state lives here, never in a worktree copy
# where a receipt-recording seat writes its ledger: prepare_review_attempt anchors it to the primary checkout
RECEIPTS_ROOT = resolve_repo_root(Path(review_mcp.__file__), 2) / "batch_state" / "review-receipts"
TASKS_DIR = PRIMARY / "batch_state" / "tasks"  # where the dispatcher writes the task records identities come from
PYTHON = PRIMARY / ".venv" / "bin" / "python"
STATE_NAME = "integration-state.json"

# The fixture lesson's units: ASCII placeholders only, one per layer the fix loop tells apart.
RECORD_QUOTE = "pack-quote-alpha"
WORD_ENTRY = "word-entry-gamma"
ITEM = "alpha-item-text"  # the incorrect side of an error record
TYPED_OPTION = "typed-option-delta"  # a distractor the writer typed
UNITS: list[dict[str, Any]] = [
    {"tab": "urok", "activity": None, "item": None, "block": 0, "role": "narration", "text": PROSE},
    {"tab": "urok", "activity": None, "item": None, "block": 1, "role": "quoted_term", "text": RECORD_QUOTE},
    {"tab": "slovnyk", "activity": None, "item": None, "block": 0, "role": "gloss", "text": WORD_ENTRY},
    {"tab": "vpravy", "activity": "act-1", "item": 0, "block": 0, "role": "item_prompt", "text": ITEM},
    {"tab": "vpravy", "activity": "act-2", "item": 0, "block": 0, "role": "option", "text": TYPED_OPTION},
]
SECOND_SEAT_MODEL = ("agy", "gemini-3.8-flash-high")  # the third family: the writer is openai, the first seat anthropic


# --- running the product entry points -------------------------------------------------------------


@dataclass
class Run:
    code: int
    out: str
    err: str

    def json(self) -> dict[str, Any]:
        """The object the entry point printed: all of stdout (``record`` indents), else its last line."""
        text = self.out.strip()
        try:
            return json.loads(text) if text else {}
        except ValueError:
            return json.loads(text.splitlines()[-1])


def run_main(main: Callable[[list[str] | None], int], argv: list[str]) -> Run:
    """Call an entry point's ``main`` in process and keep what it printed and the exit code it returned."""
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = int(main(argv) or 0)
        except SystemExit as stop:
            code = int(stop.code) if isinstance(stop.code, int) else 1
    return Run(code, out.getvalue(), err.getvalue())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- the module world -----------------------------------------------------------------------------


class ModuleWorld(World):
    """The three-lesson fixture module built by the engine helpers, with a promotable plan.

    ``promote=True`` runs the plan through a crafted review and ``plan-promote`` before the lesson manifests are
    written (a lesson manifest pins the plan, so the engine builds lessons after the plan is promoted);
    ``promote=False`` leaves the plan review manifest ready and the plan unreviewed (cases (i) and (iii) of the
    real seats start there).
    """

    def __init__(self, root: Path, mp: pytest.MonkeyPatch, *, promote: bool) -> None:
        self._deferred = True  # World.__init__ writes manifests; here they wait for the plan
        super().__init__(root, mp)
        self._deferred = False
        self.mp = mp
        self.expanded_dir = root / "out" / "expanded"
        self.plan_review_digest = ""
        self._write_pages()
        self._overlay_plan_world()
        mp.setattr(plan_manifest, "verify_pack_strict", fake_verify())
        self.plan_review_digest = self._plan_manifest()
        if promote:
            self.promote_crafted()
        self.write_manifests()
        self.closure()

    @classmethod
    def attach(cls, root: Path, mp: pytest.MonkeyPatch) -> ModuleWorld:
        """A prepared world opened again (no build): what a later process needs to record or read against it."""
        self = cls.__new__(cls)
        self.root, self.mp, self._deferred = Path(root), mp, False
        self.plan_dir = self.root / "curriculum/l2-uk-en/lesson-plans" / LEVEL
        self.evidence_dir = self.root / "curriculum/l2-uk-en/evidence" / LEVEL
        self.state_dir = self.evidence_dir / "_state" / SLUG
        self.page_dir = self.root / "site/src/content/docs" / LEVEL / SLUG
        self.tasks_dir = self.root / "batch_state" / "tasks"
        self.db = self.root / "batch_state" / "review-findings" / f"{LEVEL}.sqlite"
        self.ledgers = self.root / "batch_state" / "review-receipts"
        self.out = self.root / "out"
        self.expanded_dir = self.out / "expanded"
        self.counter = 100  # crafted ids of a later process never collide with the ones already recorded
        return self

    # the engine's files -------------------------------------------------------------------------
    def write_manifests(self, ns: tuple[int, ...] = (1, 2, 3)) -> None:
        if not self._deferred:
            super().write_manifests(ns)

    def _write_pages(self, suffix: str = "") -> None:
        body = "\n\n".join(unit["text"] for unit in UNITS)
        for n in (1, 2, 3):
            (self.page_dir / f"{n}.mdx").write_text(f"# Lesson {n}\n\n{body}\n{suffix}", encoding="utf-8")

    def expanded(self, n: int) -> Path:
        path = self.out / f"lesson-{n}.expanded.yaml"
        _dump(path, {"lesson": {"level": LEVEL, "slug": SLUG, "n": n}, "units": copy.deepcopy(UNITS)})
        return path

    def regenerate_page(self, n: int, *, manifest: bool = True) -> None:
        """What the engine does when it rebuilds a lesson: a new page, a new manifest, the closure recomputed."""
        (self.page_dir / f"{n}.mdx").write_text(
            (self.page_dir / f"{n}.mdx").read_text(encoding="utf-8") + f"\nregenerated {n}\n", encoding="utf-8"
        )
        if manifest:
            self.write_manifests((n,))
        self.closure()

    def _overlay_plan_world(self) -> None:
        """Lay the plan-review world (a valid plan, provisional pack, word store, arc, registry) over the module."""
        plan, pack, words = plan_fixture.build_base()
        words["words"][7]["pos"] = "noun"  # W-008 is the base layer of the planned learner state
        recap = copy.deepcopy(plan["lessons"][1])
        recap["n"] = 3
        plan["lessons"] = [plan["lessons"][0], plan_fixture._plain_teach_lesson(2, "lesson-two"), recap]
        plan["module"] = plan["slug"] = SLUG
        plan["evidence_ref"]["path"] = f"curriculum/l2-uk-en/evidence/{LEVEL}/{SLUG}.yaml"
        scratch = self.root.parent / f"{self.root.name}.scratch"
        world = plan_fixture.write_world(scratch, plan, pack, words, slug=SLUG)
        promoted = yaml.safe_load(world.plan_path.read_bytes())
        promoted["evidence_ref"]["sha256"] = plan_review_world.STALE_SHA  # the provisional pack is not promoted yet
        world.plan_path.write_bytes(yaml.safe_dump(promoted, allow_unicode=True, sort_keys=False).encode("utf-8"))
        (world.plan_path.parent / "_decisions.yaml").write_text("decisions: []\n", encoding="utf-8")
        (scratch / "docs/epics").mkdir(parents=True, exist_ok=True)
        (scratch / "docs/epics/fresh-build-requirements.md").write_text("# fixture requirements\n", encoding="utf-8")
        (world.pack_path.parent / "_base.request.yaml").write_text(
            yaml.safe_dump({"words": [{"lemma": "lemma-eight", "pos": "noun"}]}), encoding="utf-8"
        )
        (scratch / "curriculum/l2-uk-en/curriculum.yaml").write_text(  # the module manifest the prompt checker reads
            yaml.safe_dump({"levels": {LEVEL: {"type": "core", "modules": [SLUG, "neighbour-unit"]}}}), encoding="utf-8"
        )
        for tree in ("curriculum", "docs"):
            shutil.copytree(scratch / tree, self.root / tree, dirs_exist_ok=True)
        shutil.rmtree(scratch)
        plan_review_world.git(self.root, "init", "-q", "-b", "main")
        plan_review_world.git(self.root, "add", "-A")
        plan_review_world.git(self.root, "commit", "-q", "-m", "baseline")
        plan_review_world.git(self.root, "update-ref", "refs/remotes/origin/main", "HEAD")

    def _plan_manifest(self) -> str:
        plan_path = self.plan_dir / f"{SLUG}.yaml"
        done = run_main(validate_main, [LEVEL, SLUG, "--plan", str(plan_path), "--provisional-pack", "--write-report"])
        if done.code != 0:
            raise RuntimeError(f"plan-validate --provisional-pack failed: {done.out.strip()[-400:]}")
        made = run_main(fresh_cli, ["plan-manifest", LEVEL, SLUG, "--repo-root", str(self.root)])
        if made.code != 0:
            raise RuntimeError(f"plan-manifest failed: {made.err.strip()[-400:]}")
        return made.json()["manifest_sha256"]

    # the plan review -----------------------------------------------------------------------------
    @property
    def plan_manifest_path(self) -> Path:
        return self.state_dir / "plan-review.manifest.yaml"

    def promote_crafted(self) -> dict[str, Any]:
        """A crafted plan review recorded through ``record`` and accepted by ``plan-promote``."""
        review_id, attempt_id = "review-plan", "attempt-plan"
        ledger = self.ledgers / review_id / f"{attempt_id}.jsonl"
        create_empty_ledger(ledger)
        review = self.out / "plan.return.yaml"
        _dump(
            review,
            _review(
                kind="plan",
                manifest_hash=self.plan_review_digest,
                checks={name: "clean" for name in PLAN_CHECKS},
                findings=[],
                attempt_id=attempt_id,
                review_id=review_id,
            ),
        )
        self.task("plan-review-claude", "claude", "claude-sonnet-5")
        recorded = run_main(
            record.main,
            [
                str(review),
                "--manifest",
                str(self.plan_manifest_path),
                "--ledger",
                str(ledger),
                "--task-id",
                "plan-review-claude",
                *self.location_args(),
            ],
        )
        if recorded.code != 0:
            raise RuntimeError(
                f"the crafted plan review was not recorded: {recorded.err.strip()} {recorded.out[-300:]}"
            )
        return self.promote()

    def promote(self) -> dict[str, Any]:
        promoted = run_main(fresh_cli, ["plan-promote", LEVEL, SLUG, "--repo-root", str(self.root)])
        if promoted.code != 0:
            raise RuntimeError(f"plan-promote refused: {promoted.err.strip()[-500:]}")
        return promoted.json()

    def plan_status(self) -> dict[str, Any]:
        return run_main(fresh_cli, ["plan-review-status", LEVEL, SLUG, "--repo-root", str(self.root)]).json()

    # entry points --------------------------------------------------------------------------------
    def location_args(self) -> list[str]:
        return ["--repo-root", str(self.root), "--db", str(self.db), "--tasks-dir", str(self.tasks_dir)]

    def record_cli(self, made: dict[str, Any], *, task_id: str = "review-claude", second: bool = False) -> Run:
        argv = [
            str(made["review"]),
            "--manifest",
            str(self.manifest(made["n"])),
            "--lesson",
            str(self.expanded(made["n"])),
            "--ledger",
            str(made["ledger"]),
            "--task-id",
            task_id,
            *self.location_args(),
        ]
        return run_main(record.main, [*argv, "--second-seat"] if second else argv)

    def fixloop_cli(self, *argv: str) -> Run:
        return run_main(fixloop.main, ["--repo-root", str(self.root), "--db", str(self.db), *argv])

    def verdict(self) -> dict[str, Any]:
        """``fixloop verdict``: computes and writes ``module-verdict.yaml``; returns the document read back."""
        done = self.fixloop_cli("verdict", LEVEL, SLUG)
        if done.code != 0:
            raise RuntimeError(f"fixloop verdict failed: {done.err.strip()}")
        return yaml.safe_load((self.state_dir / fixloop.MODULE_VERDICT_NAME).read_bytes())

    def dump_db(self) -> dict[str, list]:
        conn = sqlite3.connect(self.db)
        try:
            return {
                table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table}")]
                for table in ("attempts", "findings", "budgets", "settle_items", "agreement")
            }
        finally:
            conn.close()

    def second_seat_task(self) -> str:
        return self.task("review-google", *SECOND_SEAT_MODEL)

    def approve_all(self) -> None:
        for n in (1, 2, 3):
            done = self.record_cli(self.make_return(n))
            if done.code != 0 or done.json().get("verdict") != "APPROVE":
                raise RuntimeError(f"lesson {n} was not approved: {done.out[-300:]} {done.err.strip()}")


@contextlib.contextmanager
def module_world(root: Path, *, promote: bool) -> Iterator[ModuleWorld]:
    mp = pytest.MonkeyPatch()
    try:
        yield ModuleWorld(root, mp, promote=promote)
    finally:
        mp.undo()


def hold_codes(document: dict[str, Any]) -> list[str]:
    return [hold["code"] for hold in document["holds"]]


# --- cases ----------------------------------------------------------------------------------------


@dataclass
class Case:
    key: str
    title: str
    base: Path
    evidence: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def expect(self, ok: bool, message: str) -> bool:
        if not ok:
            self.failures.append(message)
        return ok

    def note(self, text: str) -> None:
        self.evidence.append(text)

    def rel(self, path: Path) -> str:
        path = Path(path)
        return path.relative_to(self.base).as_posix() if path.is_relative_to(self.base) else path.as_posix()

    @property
    def passed(self) -> bool:
        return not self.failures

    def line(self) -> str:
        text = f"{'PASS' if self.passed else 'FAIL'} ({self.key}) {self.title}: " + "; ".join(self.evidence)
        return text + ("" if self.passed else " || FAILED: " + " | ".join(self.failures))


def db_rows(world: ModuleWorld, table: str, where: str = "1=1") -> list[sqlite3.Row]:
    return world.db_rows(table, where)


def case_layers(c: Case) -> None:
    """(iii) a sourced finding on an engine-printed record span gets that record's layer; never-blamed spans are not."""
    with module_world(c.base / "iii-layers", promote=True) as w:
        w.provenance(
            2,
            [
                span(PROSE, source="writer_prose", block=0),
                span(RECORD_QUOTE, kind="quote", block=1),
                span(WORD_ENTRY, tab="slovnyk", kind="word"),
                span(ITEM, tab="vpravy", activity="act-1", item=0, kind="error", side="incorrect"),
                span(
                    TYPED_OPTION,
                    tab="vpravy",
                    activity="act-2",
                    item=0,
                    source="writer_prose",
                    origin="writer_typed",
                    key=False,
                ),
            ],
        )

        def at(quote: str, **place: Any) -> list[dict[str, Any]]:
            return [{"tab": place.pop("tab", "urok"), **place, "quote": quote}]

        findings = [
            finding("F-01", locations=at(RECORD_QUOTE)),
            finding("F-02", locations=at(WORD_ENTRY, tab="slovnyk")),
            finding("F-03", dimension="activity", locations=at(ITEM, tab="vpravy", activity="act-1", item=0)),
            finding("F-04", dimension="activity", locations=at(TYPED_OPTION, tab="vpravy", activity="act-2", item=0)),
            finding("F-05", locations=at(PROSE)),
        ]
        made = w.make_return(2, findings)
        done = w.record_cli(made)
        c.expect(done.code == 0 and done.json().get("accepted") is True, f"record refused: {done.out[-300:]}{done.err}")
        layers = {row["finding_id"]: row["layer"] for row in db_rows(w, "findings")}
        expected = {
            "F-01": "pack",
            "F-02": "word_store",
            "F-03": "not_blamed",
            "F-04": "not_blamed",
            "F-05": "regenerate_lesson",
        }
        c.expect(layers == expected, f"layers {layers} != {expected}")
        report = w.fixloop_cli("report", LEVEL, SLUG, "--json")
        report_layers = {
            layer: sorted(item["finding_ref"].split("/")[-1] for item in items)
            for layer, items in json.loads(report.out)["layers"].items()
        }
        c.expect(
            report_layers
            == {
                "pack": ["F-01"],
                "word_store": ["F-02"],
                "not_blamed": ["F-03", "F-04"],
                "regenerate_lesson": ["F-05"],
            },
            f"the fix-loop report groups the layers as {report_layers}",
        )
        c.expect(
            len(db_rows(w, "findings")) == len(findings), "a finding was dropped between the validator and the database"
        )
        saved = w.state_dir / f"lesson-2.review.{made['attempt_id']}.yaml"
        c.note(f"return {c.rel(saved)} sha256={sha256(saved)[:12]}")
        c.note(f"db {c.rel(w.db)} findings={len(db_rows(w, 'findings'))} layers={layers}")


def case_second_seat(c: Case) -> None:
    """(v) the sampled lesson is reviewed again on the same manifest by a third family; agreement, disagreement."""
    params = findings_db.load_parameters()
    sampled = [n for n in (1, 2, 3) if second_seat.selected(LEVEL, SLUG, n, params["second_seat_divisor"])]
    c.expect(sampled == [3], f"the sampling rule selects lessons {sampled}, expected [3] of the fixture")
    with module_world(c.base / "v-second-seat-agree", promote=True) as w:
        w.approve_all()
        held = w.verdict()
        c.expect(
            hold_codes(held) == [fixloop.HOLD_SECOND_SEAT_PENDING],
            f"a sampled lesson without a second review: holds {hold_codes(held)}",
        )
        seat = w.second_seat_task()
        refused = w.record_cli(w.make_return(1), task_id=seat, second=True)
        c.expect(
            refused.code == 2 and "not in the second-seat sample" in refused.err,
            f"a second seat on an unsampled lesson: exit {refused.code} {refused.err.strip()}",
        )
        same_family = w.record_cli(w.make_return(3), task_id="review-claude", second=True)
        c.expect(same_family.code == 2, f"a second seat of the first seat's family: exit {same_family.code}")
        made = w.make_return(3)
        done = w.record_cli(made, task_id=seat, second=True)
        c.expect(
            done.code == 0 and done.json().get("accepted") is True, f"second seat refused: {done.out[-300:]}{done.err}"
        )
        first = db_rows(w, "attempts", "role = 'first' AND lesson_n = 3")[-1]
        [second] = db_rows(w, "attempts", "role = 'second'")
        c.expect(
            first["manifest_sha256"] == second["manifest_sha256"] == w.digest(3),
            "the two seats did not review one manifest",
        )
        families = {first["writer_family"], first["reviewer_family"], second["reviewer_family"]}
        c.expect(len(families) == 3, f"families writer/first/second are not three: {families}")
        [agreement] = db_rows(w, "agreement")
        c.expect(agreement["agreed"] == 1 and agreement["lesson_n"] == 3, "no agreement row for the clean pair")
        approved = w.verdict()
        c.expect(
            approved["verdict"] == "APPROVE", f"agreement should let the module be approved: {hold_codes(approved)}"
        )
        c.note(
            f"agree: writer={first['writer_family']} first={first['reviewer_family']} second={second['reviewer_family']} "
            f"manifest={w.digest(3)[:12]} agreement rows={len(db_rows(w, 'agreement'))} verdict={approved['verdict']}"
        )
    with module_world(c.base / "v-second-seat-disagree", promote=True) as w:
        w.approve_all()
        seat = w.second_seat_task()
        made = w.make_return(3, [finding("F-01", severity="MAJOR")])
        done = w.record_cli(made, task_id=seat, second=True)
        payload = done.json()
        c.expect(
            done.code == 0 and payload.get("accepted") is True,
            f"disagreeing second seat refused: {done.out[-300:]}{done.err}",
        )
        [agreement] = db_rows(w, "agreement")
        c.expect(agreement["agreed"] == 0, "a MAJOR the first seat lacks was recorded as agreement")
        items = db_rows(w, "settle_items")
        c.expect(
            [(row["kind"], row["outcome"], row["lesson_n"]) for row in items]
            == [("second_seat_disagreement", None, 3)],
            f"settle items {[tuple(row) for row in items]}",
        )
        held = w.verdict()
        c.expect(
            held["verdict"] != "APPROVE" and "settle_open" in hold_codes(held),
            f"the open disagreement did not hold the module: {held['verdict']} {hold_codes(held)}",
        )
        c.note(
            f"disagree: agreement agreed=0, settle item {items[0]['item_id']} open, module-verdict "
            f"{held['verdict']} holds={hold_codes(held)} ({c.rel(w.state_dir / fixloop.MODULE_VERDICT_NAME)})"
        )


def case_staleness(c: Case) -> None:
    """(vi) regenerating lesson 1 makes the reviews of lessons 2-3 stale through the closure."""
    with module_world(c.base / "vi-staleness", promote=True) as w:
        w.approve_all()
        seat = w.second_seat_task()
        c.expect(
            w.record_cli(w.make_return(3), task_id=seat, second=True).code == 0, "second seat of lesson 3 not recorded"
        )
        before = w.verdict()
        c.expect(before["verdict"] == "APPROVE", f"the baseline is not APPROVE: {hold_codes(before)}")
        old = {n: w.digest(n) for n in (1, 2, 3)}
        spent = w.fixloop_cli("regenerate", LEVEL, SLUG, "1")
        c.expect(
            spent.code == 0 and spent.json().get("stale_until_re_reviewed") == [2, 3],
            f"regenerate names the stale lessons {spent.json().get('stale_until_re_reviewed')}",
        )
        w.regenerate_page(1, manifest=False)  # the page is rebuilt; its manifest is not yet
        rebuilt = w.verdict()
        c.expect(rebuilt["verdict"] != "APPROVE", "the module stayed APPROVE after lesson 1 was regenerated")
        states = {row["n"]: row["state"] for row in rebuilt["lessons"]}
        c.expect(states == {1: "stale", 2: "stale", 3: "stale"}, f"states after the regeneration: {states}")
        upstream = " ".join(rebuilt["lessons"][1]["stale"])
        c.expect("upstream_lessons" in upstream, f"lesson 2 does not name the lesson it read: {upstream}")
        closure = fixloop.read_closure(w.state_dir)
        c.expect(
            {row["n"] for row in closure["stale"] if row.get("upstream") == 1} == {2, 3},
            "module.closure.yaml does not list lessons 2 and 3 as stale on lesson 1",
        )
        w.write_manifests((1,))
        w.closure()
        w.write_manifests((2, 3))  # the engine then rebuilds the lessons after lesson 1 on their new inputs
        w.closure()
        steps = []
        for n in (1, 2, 3):
            steps.append(w.verdict()["verdict"])
            done = w.record_cli(w.make_return(n))
            c.expect(
                done.code == 0 and done.json().get("verdict") == "APPROVE",
                f"re-review of lesson {n}: {done.out[-200:]}",
            )
        pending = w.verdict()
        c.expect(steps == ["HOLD", "HOLD", "HOLD"], f"verdicts before each re-review: {steps}")
        c.expect(
            pending["verdict"] == "HOLD" and hold_codes(pending) == [fixloop.HOLD_SECOND_SEAT_PENDING],
            f"after the three re-reviews only the second seat of lesson 3 was left: {hold_codes(pending)}",
        )
        c.expect(
            w.record_cli(w.make_return(3), task_id=seat, second=True).code == 0,
            "second seat on the new manifest not recorded",
        )
        final = w.verdict()
        c.expect(final["verdict"] == "APPROVE", f"not APPROVE after everything was re-reviewed: {hold_codes(final)}")
        new = {n: w.digest(n) for n in (1, 2, 3)}
        c.expect(all(new[n] != old[n] for n in (1, 2, 3)), "a manifest did not change with the regeneration")
        c.note(
            "regenerate 1 -> stale [2, 3]; states "
            f"{states}; HOLD until re-reviewed on manifests { {n: new[n][:8] for n in new} } (were { {n: old[n][:8] for n in old} }); "
            f"closure {c.rel(w.state_dir / 'module.closure.yaml')}; final {final['verdict']}"
        )


def case_budgets_and_signal(c: Case) -> None:
    """(vii) the third REVISE round and the regeneration budget are terminal (operator); the signal is printed."""
    with module_world(c.base / "vii-budgets", promote=True) as w:
        calque = {"dimension": "language", "sub_dimension": "calque", "severity": "MAJOR"}
        first = w.record_cli(w.make_return(1, [finding("F-01", **calque)]))
        second = w.record_cli(w.make_return(2, [finding("F-01", **calque)]))
        c.expect(first.code == 0 and second.code == 0, "the two REVISE reviews were not recorded")
        before = w.dump_db()
        report = w.fixloop_cli("report", LEVEL, SLUG)
        printed = "SIGNAL (no automatic branch): language/calque in lessons [1, 2]"
        c.expect(printed in report.out, f"the signal is not printed: {report.out[-400:]}")
        c.expect(w.dump_db() == before, "reading the signal changed the database")
        c.expect(not (w.state_dir / fixloop.MODULE_VERDICT_NAME).exists(), "the signal wrote a module verdict")
        rounds = [
            w.record_cli(w.make_return(2, [finding("F-01", severity="MAJOR")])),
            w.record_cli(w.make_return(2, [finding("F-01", severity="MAJOR")])),
        ]
        c.expect(
            rounds[0].code == 0 and rounds[0].json().get("terminal") is None, "the second REVISE round was terminal"
        )
        terminal = rounds[1].json().get("terminal") or []
        c.expect(
            rounds[1].code == 3
            and [(t["transition"], t["reason"]) for t in terminal] == [("operator", fixloop.REASON_REVISE)],
            f"the third REVISE round: exit {rounds[1].code} terminal {terminal}",
        )
        refused = w.fixloop_cli("regenerate", LEVEL, SLUG, "2")
        c.expect(
            refused.code == 3 and refused.json().get("reason") == fixloop.REASON_REVISE,
            f"a regeneration after the third REVISE round: exit {refused.code} {refused.out.strip()}",
        )
        budgets = {row["lesson_n"]: (row["revise_rounds"], row["regenerations"]) for row in db_rows(w, "budgets")}
        c.expect(budgets.get(2) == (3, 0), f"lesson 2 budgets {budgets.get(2)}: the refused regeneration was spent")
        held = w.verdict()
        c.expect(
            "terminal_operator" in hold_codes(held),
            f"the module verdict does not carry the terminal: {hold_codes(held)}",
        )
        spent = [w.fixloop_cli("regenerate", LEVEL, SLUG, "1") for _ in range(6)]
        c.expect(all(run.code == 0 for run in spent), "the module regeneration budget refused before 2 x lessons")
        last = w.fixloop_cli("regenerate", LEVEL, SLUG, "3")
        c.expect(
            last.code == 3
            and last.json()
            == {
                "transition": "operator",
                "reason": fixloop.REASON_REGENERATIONS,
                "detail": "6 of 6 regenerations are spent",
            },
            f"the seventh regeneration: exit {last.code} {last.out.strip()}",
        )
        spent_now = {row["lesson_n"]: (row["revise_rounds"], row["regenerations"]) for row in db_rows(w, "budgets")}
        first_terminal = terminal[0] if terminal else {}
        c.note(
            f"signal printed; lesson 2 revise_rounds=3 -> {first_terminal.get('transition')}:{first_terminal.get('reason')} "
            f"(record exit {rounds[1].code}, regenerate exit {refused.code}); regenerations 6/6 then "
            f"{last.json().get('reason')} (exit {last.code}); db {c.rel(w.db)} budgets (revise, regenerations)={spent_now}"
        )


def case_module_verdict(c: Case) -> None:
    """(viii) the module verdict is written, schema-valid, APPROVE, and lists every lesson verdict."""
    with module_world(c.base / "viii-module-verdict", promote=True) as w:
        w.approve_all()
        c.expect(
            w.record_cli(w.make_return(3), task_id=w.second_seat_task(), second=True).code == 0,
            "second seat not recorded",
        )
        document = w.verdict()
        path = w.state_dir / fixloop.MODULE_VERDICT_NAME
        errors = list(Draft202012Validator(fixloop.MODULE_VERDICT_SCHEMA).iter_errors(document))
        c.expect(not errors, f"module-verdict.yaml is not schema-valid: {errors[:1]}")
        c.expect(
            document["verdict"] == "APPROVE" and document["holds"] == [],
            f"verdict {document['verdict']} {hold_codes(document)}",
        )
        c.expect(
            [(row["n"], row["state"], row["verdict"], row["manifest_sha256"]) for row in document["lessons"]]
            == [(n, "current", "APPROVE", w.digest(n)) for n in (1, 2, 3)],
            "the lesson verdicts are not the three current APPROVEs",
        )
        c.expect(
            document["settle_items"] == {"open": [], "waiting_for_operator": [], "supported_defect_pending": []},
            "a settle item is open",
        )
        c.expect(document["plan"]["state"] == "reviewed_promoted", f"plan {document['plan']}")
        c.expect(w.plan_status()["state"] == "reviewed_promoted", "plan-review-status is not reviewed_promoted")
        c.note(
            f"{c.rel(path)} sha256={sha256(path)[:12]} verdict={document['verdict']} lessons="
            f"{[(row['n'], row['verdict']) for row in document['lessons']]} plan={document['plan']['state']} "
            f"db attempts={len(db_rows(w, 'attempts'))} findings={len(db_rows(w, 'findings'))} agreement={len(db_rows(w, 'agreement'))}"
        )


CRAFTED_CASES: list[tuple[str, str, Callable[[Case], None]]] = [
    ("iii", "layers", case_layers),
    ("v", "second seat", case_second_seat),
    ("vi", "staleness", case_staleness),
    ("vii", "budgets and signal", case_budgets_and_signal),
    ("viii", "module verdict", case_module_verdict),
]


def run_case(key: str, title: str, function: Callable[[Case], None], base: Path) -> Case:
    case = Case(key, title, base)
    try:
        function(case)
    except Exception as error:  # a crash is a failure of the check, reported with where it happened
        location = traceback.extract_tb(error.__traceback__)[-1]
        case.failures.append(
            f"{type(error).__name__}: {error} (at {location.filename.rsplit('/', 1)[-1]}:{location.lineno})"
        )
    return case


def prepare_out(out: Path) -> Path:
    out = Path(out).resolve()
    if out == REPO_ROOT or out.is_relative_to(REPO_ROOT):
        raise SystemExit(f"error: --out {out} is inside the repository; the check never writes into its content trees")
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"error: --out {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    return out


def run_crafted(out: Path) -> int:
    base = prepare_out(out)
    cases = [run_case(key, title, function, base) for key, title, function in CRAFTED_CASES]
    for case in cases:
        print(case.line())
    failed = [case.key for case in cases if not case.passed]
    print(
        f"{len(cases) - len(failed)}/{len(cases)} crafted cases pass"
        + (f"; FAILED: {', '.join(failed)}" if failed else "")
    )
    return 1 if failed else 0


# --- the real seats: prepare and finish -----------------------------------------------------------


def token_of(out: Path) -> str:
    return hashlib.sha256(str(Path(out).resolve()).encode()).hexdigest()[:8]


def dispatch_argv(agent: str, task_id: str, prompt: Path, manifest: Path, review_id: str, attempt_id: str) -> list[str]:
    return [
        str(PYTHON),
        str(PRIMARY / "scripts" / "delegate.py"),
        "dispatch",
        "--agent",
        agent,
        "--mode",
        "read-only",
        "--task-id",
        task_id,
        "--prompt-file",
        str(prompt),
        "--review-attempt",
        str(manifest),
        "--review-id",
        review_id,
        "--attempt-id",
        attempt_id,
    ]


def render_and_check(root: Path, manifest: Path, prompt: Path) -> tuple[str, str]:
    """Render the prompt from the manifest and check it with the repository's own CLIs; returns its sha256 and the note."""
    rendered = run_main(prompt_render.main, [str(manifest), "--output", str(prompt), "--repo-root", str(root)])
    if rendered.code != 0:
        raise RuntimeError(f"render failed: {rendered.err.strip()[-400:]}")
    checked = run_main(prompt_check.main, [str(prompt), "--manifest", str(manifest), "--repo-root", str(root)])
    if checked.code != 0:
        raise RuntimeError(f"prompt check failed: {checked.out.strip()[-600:]}")
    digest = sha256(prompt)
    recorded = Path(f"{prompt}.sha256").read_text(encoding="ascii").strip()
    if recorded != digest:
        raise RuntimeError(f"the prompt's sha256 sidecar {recorded} is not the prompt's hash {digest}")
    return digest, checked.out.strip()


@dataclass
class Seat:
    """The identifiers of one receipt-recording seat: review and attempt ids, the task id, where its ledger lands."""

    review_id: str
    attempt_id: str
    task_id: str

    @classmethod
    def of(cls, token: str, kind: str) -> Seat:
        return cls(f"r2b-{token}-{kind}", "a1", f"r2b-{token}-{kind}-seat")

    @property
    def ledger(self) -> Path:
        return RECEIPTS_ROOT / self.review_id / f"{self.attempt_id}.jsonl"


def make_card(
    out: Path,
    key: str,
    title: str,
    *,
    root: Path,
    seat: Seat,
    agent: str,
    manifest: Path,
    prompt: Path,
    record_argv: list[str],
    return_path: Path,
    **extra: Any,
) -> dict[str, Any]:
    """Render and check the prompt, then describe everything the driver needs to run the seat and record its return."""
    digest, note = render_and_check(root, manifest, prompt)
    return {
        "case": key,
        "title": title,
        "world": str(root),
        "prompt": str(prompt),
        "prompt_sha256": digest,
        "prompt_check": note,
        "manifest": str(manifest),
        "manifest_sha256": sha256(manifest),
        "review_id": seat.review_id,
        "attempt_id": seat.attempt_id,
        "task_id": seat.task_id,
        "ledger": str(seat.ledger),
        "return_path": str(return_path),
        "record": record_argv,
        "dispatch": dispatch_argv(agent, seat.task_id, prompt, manifest, seat.review_id, seat.attempt_id),
        **extra,
    }


def record_argv_of(world: ModuleWorld, seat: Seat, manifest: Path, return_path: Path, *lesson: str) -> list[str]:
    """The exact ``scripts.review.record`` command; identities are read from the primary checkout's dispatch record."""
    return [
        str(PYTHON),
        "-m",
        "scripts.review.record",
        str(return_path),
        "--manifest",
        str(manifest),
        *lesson,
        "--ledger",
        str(seat.ledger),
        "--task-id",
        seat.task_id,
        "--repo-root",
        str(world.root),
        "--db",
        str(world.db),
        "--tasks-dir",
        str(TASKS_DIR),
    ]


def render_card(out: Path, card: dict[str, Any]) -> str:
    """Write the card as JSON beside the prompts and return its text form for the driver."""
    cards = out / "cards"
    cards.mkdir(exist_ok=True)
    card["dispatch_cmd"] = shlex.join(card["dispatch"])
    card["record_cmd"] = f"cd {shlex.quote(str(REPO_ROOT))} && {shlex.join(card['record'])}"
    (cards / f"{card['case']}.json").write_text(json.dumps(card, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    wait = shlex.join([str(PYTHON), str(PRIMARY / "scripts" / "delegate.py"), "wait", card["task_id"]])
    finish = shlex.join([str(PYTHON), "-m", "scripts.review.integration_check", "finish-real", "--out", str(out)])
    lines = [
        f"=== DISPATCH CARD ({card['case']}) {card['title']} ===",
        f"prompt:    {card['prompt']}",
        f"           sha256 {card['prompt_sha256']} ({card['prompt_check']})",
        f"manifest:  {card['manifest']}",
        f"           sha256 {card['manifest_sha256']}",
        f"ids:       review-id {card['review_id']}  attempt-id {card['attempt_id']}  task-id {card['task_id']}",
        f"ledger:    {card['ledger']}  (written by the receipt-recording seat)",
        "1. dispatch the seat, wait for it, and save its reply (it starts with the YAML return) to",
        f"   {card['return_path']}",
        f"   {card['dispatch_cmd']}",
        f"   {wait}",
        "2. record it:",
        f"   {card['record_cmd']}",
        "3. once (i), (ii) and (iv) are recorded:",
        f"   cd {shlex.quote(str(REPO_ROOT))} && {finish}",
    ]
    return "\n".join(lines)


def prepare_plan_card(out: Path, token: str, agent: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """(i) the plan-review world, plan not yet reviewed."""
    with module_world(out / "plan-world", promote=False) as plan:
        seat = Seat.of(token, "plan")
        return_path = out / "returns" / "i-plan.return.yaml"
        card = make_card(
            out,
            "i",
            "plan review (recorded, promoted, plan-review-status reviewed_promoted)",
            root=plan.root,
            seat=seat,
            agent=agent,
            manifest=plan.plan_manifest_path,
            prompt=out / "cards" / "i-plan.prompt.md",
            return_path=return_path,
            record_argv=record_argv_of(plan, seat, plan.plan_manifest_path, return_path),
        )
        if card["manifest_sha256"] != plan.plan_review_digest:
            raise RuntimeError("the plan-review manifest's sha256 is not its recorded digest")
        state = {
            "world": str(plan.root),
            "db": str(plan.db),
            "review_id": seat.review_id,
            "attempt_id": seat.attempt_id,
            "manifest_sha256": card["manifest_sha256"],
        }
        return card, state


def prepare_module_cards(
    out: Path, token: str, lesson_agent: str, settle_agent: str
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """(ii) lesson 2 and (iv) the settle item, in the module world (plan promoted, lessons built on it)."""
    with module_world(out / "module-world", promote=True) as w:
        seat = Seat.of(token, "lesson2")
        manifest = w.manifest(2)
        return_path = out / "returns" / "ii-lesson-2.return.yaml"
        lesson = make_card(
            out,
            "ii",
            "lesson 2 review by a receipt-recording seat",
            root=w.root,
            seat=seat,
            agent=lesson_agent,
            manifest=manifest,
            prompt=out / "cards" / "ii-lesson-2.prompt.md",
            return_path=return_path,
            record_argv=record_argv_of(w, seat, manifest, return_path, "--lesson", str(w.expanded(2))),
        )
        if lesson["manifest_sha256"] != w.digest(2):
            raise RuntimeError("the lesson manifest's sha256 is not its sidecar digest")
        lesson_state = {
            "world": str(w.root),
            "db": str(w.db),
            "review_id": seat.review_id,
            "attempt_id": seat.attempt_id,
            "manifest_sha256": lesson["manifest_sha256"],
            "task_id": seat.task_id,
        }
        # (iv) a crafted first review of lesson 1 that carries one unsupported_by_source finding opens the item
        crafted = w.make_return(1, [unsupported("F-01")])
        recorded = w.record_cli(crafted)
        items = recorded.json().get("settle_items") or []
        if recorded.code != 0 or len(items) != 1:
            raise RuntimeError(
                f"the crafted first review opened settle items {items}: {recorded.out[-300:]}{recorded.err}"
            )
        item_id = items[0]
        open_verdict = w.verdict()
        kept = out / "module-verdict.while-open.yaml"
        shutil.copyfile(w.state_dir / fixloop.MODULE_VERDICT_NAME, kept)
        if open_verdict["verdict"] == "APPROVE" or "settle_open" not in hold_codes(open_verdict):
            raise RuntimeError(
                f"the module verdict is {open_verdict['verdict']} {hold_codes(open_verdict)} with the item open"
            )
        seat = Seat.of(token, "settle")
        manifest = out / "cards" / "iv-settle.manifest.yaml"
        prompt = out / "cards" / "iv-settle.prompt.md"
        settle.prepare(
            item_id,
            db_path=w.db,
            document_path=w.page_dir / "1.mdx",
            prior_ledger=crafted["ledger"],
            review_id=seat.review_id,
            attempt_id=seat.attempt_id,
            manifest_path=manifest,
            prompt_path=prompt,
            repo_root=w.root,
        )
        return_path = out / "returns" / "iv-settle.return.yaml"
        record_argv = [
            str(PYTHON),
            "-m",
            "scripts.review.settle",
            "--repo-root",
            str(w.root),
            "record",
            str(return_path),
            "--db",
            str(w.db),
            "--manifest",
            str(manifest),
            "--ledger",
            str(seat.ledger),
            "--decided-by",
            seat.task_id,
        ]
        settled = make_card(
            out,
            "iv",
            f"settle item {item_id} (unsupported_by_source finding of lesson 1)",
            root=w.root,
            seat=seat,
            agent=settle_agent,
            manifest=manifest,
            prompt=prompt,
            return_path=return_path,
            record_argv=record_argv,
            item_id=item_id,
        )
        settle_state = {
            "world": str(w.root),
            "db": str(w.db),
            "item_id": item_id,
            "manifest_sha256": settled["manifest_sha256"],
            "while_open_verdict": str(kept),
            "open_verdict": open_verdict["verdict"],
            "open_holds": hold_codes(open_verdict),
        }
        return [lesson, settled], lesson_state, settle_state


def prepare_real(out: Path, *, plan_agent: str, lesson_agent: str, settle_agent: str) -> int:
    out = prepare_out(out)
    token = token_of(out)
    try:
        plan_card, plan_state = prepare_plan_card(out, token, plan_agent)
        module_cards, lesson_state, settle_state = prepare_module_cards(out, token, lesson_agent, settle_agent)
    except RuntimeError as error:
        print(f"PREPARE FAILED: {error}", file=sys.stderr)
        return 1
    state = {"schema": 1, "token": token, "cases": {"i": plan_state, "ii": lesson_state, "iv": settle_state}}
    (out / STATE_NAME).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("\n\n".join(render_card(out, card) for card in [plan_card, *module_cards]))
    print(
        f"\nprepared under {out} (state {STATE_NAME}); the driver dispatches the three seats; nothing was dispatched here"
    )
    return 0


def _read_state(out: Path) -> dict[str, Any]:
    path = Path(out).resolve() / STATE_NAME
    if not path.is_file():
        raise SystemExit(f"error: {path} does not exist; run prepare-real first")
    return json.loads(path.read_text(encoding="utf-8"))


def _attached(root: Path) -> tuple[Path, Path, Path]:
    """The state directory, database and page directory of a prepared world."""
    state = plan_manifest.state_dir(root.resolve(), LEVEL, SLUG)
    return (
        state,
        root / "batch_state" / "review-findings" / f"{LEVEL}.sqlite",
        root / "site/src/content/docs" / LEVEL / SLUG,
    )


def _rows(db: Path, sql: str, *args: Any) -> list[sqlite3.Row]:
    conn = findings_db.connect(db)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def finish_plan(c: Case, info: dict[str, Any]) -> None:
    root = Path(info["world"])
    state, db, _ = _attached(root)
    saved = state / f"plan-review.{info['attempt_id']}.yaml"
    verdict_file = state / "plan-review.yaml"
    if not c.expect(
        saved.is_file() and verdict_file.is_file(),
        "the plan review was not recorded: no saved return or plan-review.yaml",
    ):
        return
    written = yaml.safe_load(verdict_file.read_bytes())
    c.expect(
        written["manifest_sha256"] == info["manifest_sha256"], "plan-review.yaml names another manifest than the card's"
    )
    c.expect(written["attempt_id"] == info["attempt_id"], "plan-review.yaml names another attempt")
    [attempt] = _rows(db, "SELECT * FROM attempts WHERE kind = 'plan' AND attempt_id = ?", info["attempt_id"])
    findings = yaml.safe_load(saved.read_bytes()).get("findings") or []
    c.expect(
        len(_rows(db, "SELECT * FROM findings WHERE attempt_id = ?", info["attempt_id"])) == len(findings),
        "the database's findings are not the return's findings",
    )
    c.note(
        f"plan-review.yaml verdict={written['verdict']} attempt={written['attempt_id']} manifest={written['manifest_sha256'][:12]} findings={len(findings)} harness={attempt['harness']}"
    )
    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(plan_manifest, "verify_pack_strict", fake_verify())
        if written["verdict"] != "APPROVE":
            c.expect(
                False,
                f"the seat's verdict is {written['verdict']}: plan-promote refuses it (tooling worked; the driver decides whether to re-dispatch)",
            )
            return
        promoted = run_main(fresh_cli, ["plan-promote", LEVEL, SLUG, "--repo-root", str(root)])
        c.expect(promoted.code == 0, f"plan-promote refused the recorded review: {promoted.err.strip()[-400:]}")
        status = run_main(fresh_cli, ["plan-review-status", LEVEL, SLUG, "--repo-root", str(root)]).json()
    finally:
        mp.undo()
    c.expect(status.get("state") == "reviewed_promoted", f"plan-review-status is {status.get('state')}")
    receipt = state / plan_manifest.RECEIPT_NAME
    c.note(
        f"plan-promote ok, status {status.get('state')}" + (f", receipt {c.rel(receipt)}" if receipt.is_file() else "")
    )


def finish_lesson(c: Case, info: dict[str, Any]) -> None:
    root = Path(info["world"])
    state, db, _ = _attached(root)
    saved = state / f"lesson-2.review.{info['attempt_id']}.yaml"
    verdict_file = state / "lesson-2.verdict.yaml"
    if not c.expect(
        saved.is_file() and verdict_file.is_file(),
        "the lesson 2 review was not recorded (no saved return or verdict file)",
    ):
        return
    manifest = state / "lesson-2.manifest.yaml"
    written = yaml.safe_load(verdict_file.read_bytes())
    c.expect(sha256(manifest) == info["manifest_sha256"], "the lesson manifest changed after the card was written")
    c.expect(
        written["manifest_sha256"] == sha256(manifest), "the verdict file's manifest hash is not the manifest's sha256"
    )
    c.expect(written["attempt_id"] == info["attempt_id"], "the verdict file names another attempt")
    returned = yaml.safe_load(saved.read_bytes()).get("findings") or []
    stored = _rows(db, "SELECT * FROM findings WHERE attempt_id = ?", info["attempt_id"])
    c.expect(len(stored) == len(returned), f"database findings {len(stored)} != return findings {len(returned)}")
    c.expect(
        sorted(row["finding_id"] for row in stored) == sorted(item["id"] for item in returned),
        "the database's finding ids are not the return's",
    )
    [attempt] = _rows(db, "SELECT * FROM attempts WHERE attempt_id = ?", info["attempt_id"])
    c.note(
        f"{c.rel(verdict_file)} verdict={written['verdict']} manifest={written['manifest_sha256'][:12]}=sha256({c.rel(manifest)}); "
        f"findings db={len(stored)} return={len(returned)}; harness={attempt['harness']} model={attempt['reviewer_model']} family={attempt['reviewer_family']}"
    )


def finish_settle(c: Case, info: dict[str, Any]) -> None:
    root = Path(info["world"])
    state, db, _ = _attached(root)
    c.expect(
        info["open_verdict"] != "APPROVE" and "settle_open" in info["open_holds"],
        f"while open the module verdict was {info['open_verdict']} {info['open_holds']}",
    )
    [item] = _rows(db, "SELECT * FROM settle_items WHERE item_id = ?", info["item_id"])
    c.expect(
        item["outcome"] in findings_db.SEAT_OUTCOMES,
        f"the settle item has outcome {item['outcome']}: no validated outcome was recorded",
    )
    saved = state / f"settle-{info['item_id']}.reply.yaml"
    c.expect(saved.is_file(), "the settle reply was not saved")
    if item["outcome"] in findings_db.OPERATOR_OUTCOMES:
        c.expect(item["needs_operator"] == 1, "a source_conflict/unresolved outcome is not marked for the operator")
        c.note(f"item {item['item_id']} outcome={item['outcome']} marked for the operator")
    else:
        c.note(
            f"item {item['item_id']} outcome={item['outcome']} decided_by={item['decided_by']} receipts={item['receipts_json']}"
        )
    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(plan_manifest, "verify_pack_strict", fake_verify())
        conn = findings_db.connect(db)
        try:
            after = fixloop.compute_module_verdict(conn, LEVEL, SLUG, root=root, params=findings_db.load_parameters())
        finally:
            conn.close()
    finally:
        mp.undo()
    c.expect("settle_open" not in hold_codes(after), "the decided item still holds the module as open")
    c.note(
        f"while open: {info['open_verdict']} {info['open_holds']} ({c.rel(Path(info['while_open_verdict']))}); after: {after['verdict']} {hold_codes(after)}"
    )


def finish_real(out: Path) -> int:
    out = Path(out).resolve()
    state = _read_state(out)
    cases = [
        run_case("i", "plan review recorded, promoted", lambda c: finish_plan(c, state["cases"]["i"]), out),
        run_case("ii", "lesson 2 real seat", lambda c: finish_lesson(c, state["cases"]["ii"]), out),
        run_case("iv", "settle real seat", lambda c: finish_settle(c, state["cases"]["iv"]), out),
    ]
    for case in cases:
        print(case.line())
    failed = [case.key for case in cases if not case.passed]
    print(
        f"{len(cases) - len(failed)}/{len(cases)} real cases pass"
        + (f"; FAILED: {', '.join(failed)}" if failed else "")
    )
    return 1 if failed else 0


# --- command line ---------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.review.integration_check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "R2b integration check (#8430): drives the review tooling end to end on the three-lesson fixture module.\n"
            "Use after R2b-A, R2b-B and R2b-C are on main. run-crafted needs no seat; prepare-real writes the dispatch\n"
            "cards of the three real-seat cases and dispatches nothing; finish-real asserts them after the driver\n"
            "recorded the returns. Do NOT use it to measure reviewer quality (that is the seeded-defect measurement, R3)."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.integration_check run-crafted --out /tmp/r2b-crafted\n"
            "  .venv/bin/python -m scripts.review.integration_check prepare-real --out /tmp/r2b-real\n"
            "  .venv/bin/python -m scripts.review.integration_check finish-real --out /tmp/r2b-real\n"
            "\nOutputs: one PASS/FAIL line per case with its evidence (paths, hashes, database row counts); prepare-real\n"
            "also prints the cards and writes cards/*.json, prompts, returns/ and integration-state.json under --out.\n"
            "Exit codes: 0 every case passes; 1 a case fails or prepare-real found a problem; 2 usage or unusable --out.\n"
            "--out must be an empty directory outside the repository."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    crafted = sub.add_parser("run-crafted", help="cases (iii), (v), (vi), (vii), (viii) with crafted returns")
    crafted.add_argument("--out", type=Path, required=True)
    prepare = sub.add_parser(
        "prepare-real", help="render and check the prompts of (i), (ii), (iv); write dispatch cards"
    )
    prepare.add_argument("--out", type=Path, required=True)
    for name, default in (("plan", "claude"), ("lesson", "claude"), ("settle", "claude")):
        prepare.add_argument(f"--{name}-agent", default=default, help=f"harness of the {name} seat (default {default})")
    finish = sub.add_parser(
        "finish-real", help="assert the remaining parts of (i), (ii), (iv) after the returns were recorded"
    )
    finish.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run-crafted":
        return run_crafted(args.out)
    if args.command == "prepare-real":
        return prepare_real(
            args.out, plan_agent=args.plan_agent, lesson_agent=args.lesson_agent, settle_agent=args.settle_agent
        )
    return finish_real(args.out)


if __name__ == "__main__":
    sys.exit(main())
