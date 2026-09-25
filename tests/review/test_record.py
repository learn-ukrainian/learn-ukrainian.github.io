"""``scripts.review.record`` (#8430 R2b-A): validate, save, then write the verdict file, findings and budgets.

The lesson world is the three-lesson fixture module of tests/build/test_fresh_e3b2.py with real
manifests written by the engine; the plan world is tests/helpers/plan_review_world.py. The
validator is the real one: nothing of it is faked, a return is accepted or rejected by
``validate_review``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.build.fresh import manifest as fresh_manifest
from scripts.build.fresh import plan_manifest as pm
from scripts.build.fresh.plan_promote import promote_plan
from scripts.curriculum.evidence import lock
from scripts.review import findings_db, fixloop, record, second_seat
from scripts.review.receipts.ledger import create_empty_ledger
from scripts.review.validate import codes
from tests.build.test_fresh_e3b2 import _fake_state, _fixture, _write
from tests.review.test_r1_schema_ledger import LESSON_CHECKS, PLAN_CHECKS, _dump, _record, _review

pytestmark = pytest.mark.reads_content

LEVEL, SLUG = "a1", "fixture-module"
PROSE = "lesson prose alpha"
ITEM = "alpha-item-text"


class World:
    """A tmp repository with a three-lesson module, its manifests, dispatch records and a database."""

    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.root = root
        monkeypatch.setattr(fresh_manifest, "planned_state", lambda *a, **kw: _fake_state({"a": 1}))
        _, _, self.plan_dir, self.evidence_dir, self.state_dir, self.page_dir = _fixture(root)
        self.tasks_dir = root / "batch_state" / "tasks"
        self.tasks_dir.mkdir(parents=True)
        self.db = root / "batch_state" / "review-findings" / f"{LEVEL}.sqlite"
        self.ledgers = root / "batch_state" / "review-receipts"
        self.out = root / "out"
        self.out.mkdir()
        self.counter = 0
        self.write_manifests()
        for n in (1, 2, 3):
            self.writer(n)
        self.task("review-claude", "claude", "claude-sonnet-5")

    # --- inputs -------------------------------------------------------------------------
    def write_manifests(self, ns: tuple[int, ...] = (1, 2, 3)) -> None:
        for n in ns:
            _write(LEVEL, SLUG, n, self.state_dir, self.plan_dir, self.evidence_dir, self.page_dir, self.root)

    def manifest(self, n: int) -> Path:
        return self.state_dir / f"lesson-{n}.manifest.yaml"

    def digest(self, n: int) -> str:
        return (self.state_dir / f"lesson-{n}.manifest.sha256").read_text(encoding="ascii").strip()

    def expanded(self, n: int) -> Path:
        path = self.out / f"lesson-{n}.expanded.yaml"
        units = [
            {"tab": "urok", "activity": None, "item": None, "block": 0, "role": "narration", "text": PROSE},
            {"tab": "vpravy", "activity": "act-1", "item": 0, "block": 0, "role": "item_prompt", "text": ITEM},
        ]
        _dump(path, {"lesson": {"level": LEVEL, "slug": SLUG, "n": n}, "units": units})
        return path

    def task(self, task_id: str, agent: str, model: str | None, **extra: Any) -> str:
        (self.tasks_dir / f"{task_id}.json").write_text(
            json.dumps({"task_id": task_id, "agent": agent, "model": model, "status": "done", **extra}),
            encoding="utf-8",
        )
        return task_id

    def writer(self, n: int, model: str = "gpt-6-astra") -> None:
        lock.atomic_write(
            self.state_dir / f"lesson-{n}.writer.yaml",
            yaml.safe_dump({"writer": "codex-tools", "model": model}).encode(),
        )

    def provenance(self, n: int, spans: list[dict[str, Any]]) -> None:
        document = {"provenance_schema": 1, "lesson": {"level": LEVEL, "slug": SLUG, "n": n}, "spans": spans}
        lock.atomic_write(self.state_dir / f"lesson-{n}.provenance.yaml", lock.yaml_bytes(document))

    # --- a review -----------------------------------------------------------------------
    def next_ids(self) -> tuple[str, str]:
        self.counter += 1
        return f"review-{self.counter}", f"attempt-{self.counter}"

    def make_return(
        self,
        n: int,
        findings: list[dict[str, Any]] | None = None,
        *,
        ids: tuple[str, str] | None = None,
        manifest: str | None = None,
        previous: str | None = None,
    ) -> dict[str, Any]:
        """Write a review return, its ledger and (for the receipts a finding names) ledger records; returns the paths."""
        review_id, attempt_id = ids or self.next_ids()
        digest = manifest or self.digest(n)
        ledger = self.ledgers / review_id / f"{attempt_id}.jsonl"
        create_empty_ledger(ledger)
        checks = {name: "clean" for name in LESSON_CHECKS}
        if n == 3:
            checks["recap"] = "clean"
        built = []
        for finding in findings or []:
            finding = json.loads(json.dumps(finding))
            self._cite(finding, ledger, digest, review_id, attempt_id)
            built.append(finding)
            checks[finding["dimension"]] = [
                *(checks[finding["dimension"]] if isinstance(checks[finding["dimension"]], list) else []),
                finding["id"],
            ]
        path = self.out / f"{review_id}-{attempt_id}.return.yaml"
        _dump(
            path,
            _review(
                kind="lesson",
                manifest_hash=digest,
                checks=checks,
                findings=built,
                attempt_id=attempt_id,
                review_id=review_id,
                previous=previous,
            ),
        )
        return {
            "review": path,
            "ledger": ledger,
            "review_id": review_id,
            "attempt_id": attempt_id,
            "n": n,
            "findings": built,
        }

    @staticmethod
    def _cite(finding: dict[str, Any], ledger: Path, digest: str, review_id: str, attempt_id: str) -> None:
        def receipt(result: str = "attested result", tool: str = "verify_words") -> str:
            return _record(
                ledger, manifest=digest, result=result, attempt_id=attempt_id, review_id=review_id, tool=tool
            )

        if finding.get("evidence") == "auto":
            finding["evidence"] = {"receipt": receipt()}
        if finding.get("unsupported_by_source") == "auto":
            finding["unsupported_by_source"] = {
                "searches": [{"receipt": receipt("No results found.", "search_text"), "outcome": "no_hits"}]
            }
        if finding.get("source_conflict") == "auto":
            finding["source_conflict"] = {"a": {"receipt": receipt()}, "b": {"receipt": receipt("second authority")}}

    def record(self, made: dict[str, Any], *, task_id: str = "review-claude", **kwargs: Any) -> record.Outcome:
        return record.record_return(
            made["review"],
            manifest_path=self.manifest(made["n"]),
            document_path=self.expanded(made["n"]),
            ledger_path=made["ledger"],
            task_id=task_id,
            repo_root=self.root,
            db_path=self.db,
            tasks_dir=self.tasks_dir,
            **kwargs,
        )

    def db_rows(self, table: str, where: str = "1=1") -> list[sqlite3.Row]:
        conn = findings_db.connect(self.db)
        try:
            return conn.execute(f"SELECT * FROM {table} WHERE {where}").fetchall()
        finally:
            conn.close()

    def verdict_file(self, n: int) -> Path:
        return self.state_dir / f"lesson-{n}.verdict.yaml"

    def closure(self) -> dict[str, Any]:
        """The engine's closure file, recomputed from every manifest in the history (what the engine does after a build)."""
        from scripts.build.fresh.closure import compute_closure

        lessons = [{"n": n, "kind": "recap" if n == 3 else "teach"} for n in (1, 2, 3)]
        return compute_closure(
            LEVEL, SLUG, lessons, repo_root=self.root, state_dir=self.state_dir, site_dir=self.page_dir
        )


def finding(fid: str = "F-01", **overrides: Any) -> dict[str, Any]:
    base = {
        "id": fid,
        "status": "active",
        "locations": [{"tab": "urok", "quote": PROSE}],
        "dimension": "job",
        "severity": "MINOR",
        "claim": "A claim.",
        "evidence": "auto",
    }
    base.update(overrides)
    return base


def unsupported(fid: str = "F-01", **overrides: Any) -> dict[str, Any]:
    base = finding(fid, dimension="language", sub_dimension="calque", **overrides)
    base.pop("evidence")
    base["unsupported_by_source"] = "auto"
    return base


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    return World(tmp_path, monkeypatch)


# --- acceptance and the files it writes -----------------------------------------------------


def test_an_accepted_return_writes_the_saved_return_the_verdict_file_and_one_row_per_finding(world: World) -> None:
    made = world.make_return(
        2, [finding("F-01"), finding("F-02", severity="MAJOR", could_be_a_gate="yes - a script could count it")]
    )
    outcome = world.record(made)
    assert outcome.accepted and outcome.verdict == "REVISE" and outcome.findings == 2
    saved = world.state_dir / f"lesson-2.review.{made['attempt_id']}.yaml"
    assert saved.read_bytes() == made["review"].read_bytes()
    verdict = yaml.safe_load(world.verdict_file(2).read_bytes())
    assert verdict.keys() == {"verdict", "attempt_id", "manifest_sha256", "validated_at"}
    assert verdict["verdict"] == "REVISE" and verdict["attempt_id"] == made["attempt_id"]
    assert verdict["manifest_sha256"] == world.digest(2)
    [attempt] = world.db_rows("attempts")
    assert attempt["verdict"] == "APPROVE" or attempt["verdict"] == "REVISE"
    assert (attempt["level"], attempt["slug"], attempt["lesson_n"], attempt["kind"]) == (LEVEL, SLUG, 2, "lesson")
    assert attempt["manifest_sha256"] == world.digest(2) and attempt["task_id"] == "review-claude"
    assert len(world.db_rows("findings")) == 2


def test_identities_come_from_the_dispatch_record_not_from_the_return(world: World) -> None:
    made = world.make_return(1)
    world.record(made)
    [attempt] = world.db_rows("attempts")
    # the return claims fixture-model / fixture-harness / fixture-family; the dispatch record says otherwise
    assert (attempt["reviewer_model"], attempt["harness"], attempt["reviewer_family"]) == (
        "claude-sonnet-5",
        "claude",
        "anthropic",
    )
    assert attempt["writer_family"] == "openai"


def test_a_rejected_return_writes_the_saved_return_and_a_rejected_row_and_nothing_else(world: World) -> None:
    made = world.make_return(2, [finding("F-01", evidence={"receipt": "r-fabricated"})])
    outcome = world.record(made)
    assert not outcome.accepted and outcome.verdict == "REJECTED"
    assert codes.RECEIPT_NOT_IN_LEDGER in outcome.rejection_codes
    assert (world.state_dir / f"lesson-2.review.{made['attempt_id']}.yaml").read_bytes() == made["review"].read_bytes()
    [attempt] = world.db_rows("attempts")
    assert attempt["verdict"] == "REJECTED"
    assert codes.RECEIPT_NOT_IN_LEDGER in json.loads(attempt["rejection_codes_json"])
    assert world.db_rows("findings") == [] and world.db_rows("settle_items") == [] and world.db_rows("budgets") == []
    assert not world.verdict_file(2).exists()


def test_a_rejected_return_does_not_replace_the_verdict_of_record(world: World) -> None:
    world.record(world.make_return(2))
    before = world.verdict_file(2).read_bytes()
    world.record(world.make_return(2, [finding(evidence={"receipt": "r-fabricated"})]))
    assert world.verdict_file(2).read_bytes() == before


def test_a_lesson_review_needs_its_expanded_document(world: World) -> None:
    made = world.make_return(1)
    outcome = record.record_return(
        made["review"],
        manifest_path=world.manifest(1),
        ledger_path=made["ledger"],
        task_id="review-claude",
        repo_root=world.root,
        db_path=world.db,
        tasks_dir=world.tasks_dir,
    )
    assert not outcome.accepted and codes.LESSON_UNREADABLE in outcome.rejection_codes


def test_the_echoed_attempt_must_be_the_one_recorded(world: World) -> None:
    made = world.make_return(1)
    outcome = world.record(made, attempt_id="attempt-other")
    assert not outcome.accepted and record.ATTEMPT_IDENTITY_MISMATCH in outcome.rejection_codes


@pytest.mark.parametrize("bad", ["../escape", "a/b", ".hidden", "x" * 200])
def test_an_attempt_id_that_would_name_a_path_outside_the_state_directory_is_refused(world: World, bad: str) -> None:
    made = world.make_return(1)
    with pytest.raises(record.RecordError):
        world.record(made, attempt_id=bad)
    assert not list(world.state_dir.glob("*.review.*"))


# --- identities fail closed ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("agent", "model", "extra"),
    [
        ("claude", "zzz-model", {}),  # a model no family resolves
        ("claude", None, {}),  # no model at all
        ("claude", "unknown", {}),
        (
            "cursor",
            "auto",
            {"resolved_model": "unknown", "resolved_model_known": False},
        ),  # an unattested multi-model harness
        ("", "claude-sonnet-5", {}),  # no harness
    ],
)
def test_an_unknown_model_or_family_fails_closed(world: World, agent: str, model: str | None, extra: dict) -> None:
    world.task("review-bad", agent, model, **extra)
    made = world.make_return(1)
    with pytest.raises(record.RecordError):
        world.record(made, task_id="review-bad")
    assert world.db_rows("attempts") == [] and not world.verdict_file(1).exists()


def test_a_missing_dispatch_record_fails_closed(world: World) -> None:
    with pytest.raises(record.RecordError, match="unreadable"):
        world.record(world.make_return(1), task_id="never-dispatched")
    assert world.db_rows("attempts") == []


def test_a_cursor_seat_counts_when_its_concrete_model_is_attested(world: World) -> None:
    world.task("review-cursor", "cursor", "auto", resolved_model="claude-opus-5-5", resolved_model_known=True)
    world.record(world.make_return(1), task_id="review-cursor")
    [attempt] = world.db_rows("attempts")
    assert (attempt["harness"], attempt["reviewer_family"]) == ("cursor", "anthropic")


# --- staleness ------------------------------------------------------------------------------------


@pytest.mark.parametrize("target", ["pack", "words", "gates", "lesson", "upstream", "digest", "learner_state"])
def test_a_manifest_input_that_changed_since_the_manifest_rejects_the_attempt_as_stale(
    world: World, target: str
) -> None:
    paths = {
        "pack": world.evidence_dir / f"{SLUG}.yaml",
        "words": world.evidence_dir / "_words.yaml",
        "gates": world.state_dir / "lesson-2.gates.yaml",
        "lesson": world.page_dir / "2.mdx",
        "upstream": world.page_dir / "1.mdx",
        "learner_state": world.state_dir / "lesson-2.learner-state.yaml",
    }
    manifest = yaml.safe_load(world.manifest(2).read_bytes())
    paths["digest"] = world.root / manifest["module_digest"]["path"]
    made = world.make_return(2)
    paths[target].write_bytes(paths[target].read_bytes() + b"# changed after the manifest\n")
    outcome = world.record(made)
    assert not outcome.accepted and record.MANIFEST_INPUTS_STALE in outcome.rejection_codes
    assert not world.verdict_file(2).exists()
    [attempt] = world.db_rows("attempts")
    assert attempt["verdict"] == "REJECTED" and record.MANIFEST_INPUTS_STALE in json.loads(
        attempt["rejection_codes_json"]
    )


def test_a_deleted_manifest_input_is_stale_too(world: World) -> None:
    made = world.make_return(2)
    (world.state_dir / "lesson-2.gates.yaml").unlink()
    assert record.MANIFEST_INPUTS_STALE in world.record(made).rejection_codes


def test_an_unchanged_manifest_is_not_stale(world: World) -> None:
    assert world.record(world.make_return(2)).accepted


# --- findings: lossless, none dropped -----------------------------------------------------------------


def test_no_finding_is_dropped_between_the_validator_and_the_database(world: World) -> None:
    findings = [
        finding("F-01"),
        finding("F-02", dimension="learner_fit", severity="MAJOR", expected="attested"),
        finding("F-03", dimension="fact", evidence=None, source_conflict="auto"),
        unsupported("F-04"),
        finding("F-05", locations=[], scope={"tab": "urok"}, dimension="english", could_be_a_gate="no"),
        finding(
            "F-06", dimension="activity", locations=[{"tab": "vpravy", "activity": "act-1", "item": 0, "quote": ITEM}]
        ),
    ]
    for item in findings:
        if "evidence" in item and item["evidence"] is None:
            item.pop("evidence")
    made = world.make_return(2, findings)
    outcome = world.record(made)
    assert outcome.accepted and outcome.findings == len(findings)
    returned = yaml.safe_load(made["review"].read_bytes())["findings"]
    rows = world.db_rows("findings", "attempt_id = '" + made["attempt_id"] + "'")
    assert len(rows) == len(returned) == len(findings)
    assert [row["finding_id"] for row in rows] == [item["id"] for item in returned]
    for row, item in zip(rows, returned, strict=True):
        assert json.loads(row["finding_json"]) == item  # the whole finding, as returned
        assert json.loads(row["locations_json"]) == item.get("locations", [])
    by_id = {row["finding_id"]: row for row in rows}
    assert len(json.loads(by_id["F-03"]["receipts_json"])) == 2  # every receipt, not the first one
    assert json.loads(by_id["F-01"]["receipts_json"]) == [returned[0]["evidence"]["receipt"]]
    assert by_id["F-04"]["evidence_kind"] == "unsupported_by_source"
    assert by_id["F-02"]["sub_dimension"] is None and by_id["F-04"]["sub_dimension"] == "calque"


def test_a_database_row_missing_after_the_inserts_rolls_the_attempt_back(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = findings_db.insert_finding
    seen = []

    def lossy(conn, review_id, attempt_id, item, **kwargs):
        seen.append(item["id"])
        if len(seen) == 1:
            return  # a finding silently not stored
        real(conn, review_id, attempt_id, item, **kwargs)

    monkeypatch.setattr(findings_db, "insert_finding", lossy)
    made = world.make_return(2, [finding("F-01"), finding("F-02", dimension="fact")])
    with pytest.raises(record.RecordError, match="stored"):
        world.record(made)
    assert world.db_rows("attempts") == [] and world.db_rows("findings") == []
    assert not world.verdict_file(2).exists()


# --- settle items --------------------------------------------------------------------------------------


def test_an_unsupported_by_source_finding_opens_exactly_one_settle_item(world: World) -> None:
    made = world.make_return(2, [unsupported("F-01"), finding("F-02", dimension="fact")])
    outcome = world.record(made)
    [item] = world.db_rows("settle_items")
    assert outcome.settle_items == [item["item_id"]]
    assert item["finding_ref"] == f"{made['review_id']}/{made['attempt_id']}/F-01"
    assert item["outcome"] is None and item["kind"] == "unsupported_by_source"
    assert (item["level"], item["slug"], item["lesson_n"]) == (LEVEL, SLUG, 2)
    world.record(made)  # the same return recorded again opens nothing new
    assert len(world.db_rows("settle_items")) == 1


def test_a_resolved_unsupported_finding_opens_no_item(world: World) -> None:
    first = world.make_return(2, [unsupported("F-01")])
    world.record(first)
    made = world.make_return(
        2, [unsupported("F-01", status="resolved")], ids=(first["review_id"], "attempt-9"), previous=first["attempt_id"]
    )
    outcome = world.record(made)
    assert outcome.accepted, outcome.rejection_codes
    assert len(world.db_rows("settle_items")) == 1  # only the first attempt's active finding opened one


# --- budgets and the terminal transition --------------------------------------------------------------------


def test_each_revise_verdict_is_a_round_and_the_third_is_terminal(world: World) -> None:
    for round_ in (1, 2, 3):
        outcome = world.record(world.make_return(2, [finding("F-01", severity="MAJOR")]))
        assert outcome.verdict == "REVISE"
        [budget] = world.db_rows("budgets", "lesson_n = 2")
        assert budget["revise_rounds"] == round_
        assert bool(outcome.terminal) is (round_ == 3)
    assert (
        outcome.terminal[0]["transition"] == "operator" and outcome.terminal[0]["reason"] == "revise_budget_exhausted"
    )


def test_an_approve_is_not_a_round(world: World) -> None:
    world.record(world.make_return(2))
    assert world.db_rows("budgets") == []


def test_a_review_failure_is_recorded_and_counted(world: World) -> None:
    for count in (1, 2, 3):
        made = world.make_return(2)
        outcome = record.record_return(
            None,
            manifest_path=world.manifest(2),
            task_id="review-claude",
            repo_root=world.root,
            db_path=world.db,
            tasks_dir=world.tasks_dir,
            review_id=made["review_id"],
            attempt_id=made["attempt_id"],
            failure="timeout",
        )
        assert outcome.verdict == "FAILED" and not outcome.accepted
        [budget] = world.db_rows("budgets", "lesson_n = 2")
        assert budget["review_failures"] == count
        assert bool(outcome.terminal) is (count == 3)
    assert outcome.terminal[0]["reason"] == "review_failure_after_fallback"
    failed = world.db_rows("attempts", "verdict = 'FAILED'")
    assert len(failed) == 3 and {row["failure_reason"] for row in failed} == {"timeout"}
    assert not world.verdict_file(2).exists()


def test_recording_the_same_failure_twice_counts_it_once(world: World) -> None:
    kwargs = dict(
        manifest_path=world.manifest(2),
        task_id="review-claude",
        repo_root=world.root,
        db_path=world.db,
        tasks_dir=world.tasks_dir,
        review_id="r-1",
        attempt_id="a-1",
        failure="crash",
    )
    record.record_return(None, **kwargs)
    assert record.record_return(None, **kwargs).replay
    assert world.db_rows("budgets")[0]["review_failures"] == 1


def test_a_rejected_return_is_counted_as_a_failed_review_by_a_later_failure_record(world: World) -> None:
    made = world.make_return(2, [finding(evidence={"receipt": "r-fabricated"})])
    world.record(made)
    assert world.db_rows("budgets") == []
    args = dict(
        manifest_path=world.manifest(2),
        task_id="review-claude",
        repo_root=world.root,
        db_path=world.db,
        tasks_dir=world.tasks_dir,
        review_id=made["review_id"],
        attempt_id=made["attempt_id"],
        failure="rejected_return",
    )
    record.record_return(None, **args)
    record.record_return(None, **args)
    [budget] = world.db_rows("budgets")
    assert budget["review_failures"] == 1
    [attempt] = world.db_rows("attempts")
    assert attempt["verdict"] == "REJECTED" and attempt["failure_reason"] == "rejected_return"


def test_a_failure_needs_a_known_reviewer_too(world: World) -> None:
    with pytest.raises(record.RecordError):
        record.record_return(
            None,
            manifest_path=world.manifest(2),
            task_id="never-dispatched",
            repo_root=world.root,
            db_path=world.db,
            tasks_dir=world.tasks_dir,
            review_id="r-1",
            attempt_id="a-1",
            failure="timeout",
        )
    assert world.db_rows("budgets") == []


# --- replay ---------------------------------------------------------------------------------------------------


def test_recording_the_same_return_again_changes_nothing_but_repairs_a_missing_verdict_file(world: World) -> None:
    made = world.make_return(2, [finding("F-01", severity="MAJOR")])
    world.record(made)
    world.verdict_file(2).unlink()  # a crash between the database and the verdict file
    again = world.record(made)
    assert again.replay and again.accepted and world.verdict_file(2).is_file()
    assert len(world.db_rows("attempts")) == 1 and len(world.db_rows("findings")) == 1
    assert world.db_rows("budgets")[0]["revise_rounds"] == 1  # not counted twice


def test_a_different_return_for_a_recorded_attempt_is_refused(world: World) -> None:
    made = world.make_return(2)
    world.record(made)
    other = world.make_return(2, [finding("F-01")], ids=(made["review_id"], made["attempt_id"]))
    with pytest.raises(record.RecordError, match="different return"):
        world.record(other)


# --- a seeded lesson never enters the loop ----------------------------------------------------------------------------


def test_a_seeded_attempt_is_kept_apart_and_never_enters_the_fix_loop(world: World) -> None:
    made = world.make_return(2, [finding("F-01", severity="BLOCKER"), unsupported("F-02")])
    outcome = world.record(made, seed_id="seed-7")
    assert outcome.accepted and outcome.seed_id == "seed-7" and outcome.verdict_file is None and outcome.terminal == []
    [attempt] = world.db_rows("attempts")
    assert attempt["seed_id"] == "seed-7"
    assert {row["seed_id"] for row in world.db_rows("findings")} == {"seed-7"}
    assert world.db_rows("settle_items") == [] and world.db_rows("budgets") == []
    assert not world.verdict_file(2).exists()
    assert all(row["layer"] is None for row in world.db_rows("findings"))
    conn = findings_db.connect(world.db)
    try:
        assert (
            findings_db.module_attempts(conn, LEVEL, SLUG) == []
            and findings_db.module_findings(conn, LEVEL, SLUG) == []
        )
    finally:
        conn.close()


def test_a_seeded_failure_does_not_count_against_the_lesson(world: World) -> None:
    record.record_return(
        None,
        manifest_path=world.manifest(2),
        task_id="review-claude",
        repo_root=world.root,
        db_path=world.db,
        tasks_dir=world.tasks_dir,
        review_id="r-1",
        attempt_id="a-1",
        failure="timeout",
        seed_id="seed-7",
    )
    assert world.db_rows("budgets") == []


# --- the database refuses a foreign schema version ------------------------------------------------------------------------


def test_record_refuses_a_database_with_another_schema_version(world: World) -> None:
    findings_db.connect(world.db).close()
    conn = sqlite3.connect(world.db)
    conn.execute("UPDATE schema_version SET version = 99")
    conn.commit()
    conn.close()
    with pytest.raises(findings_db.VersionMismatch):
        world.record(world.make_return(1))
    assert not world.verdict_file(1).exists()


# --- layers at record time ------------------------------------------------------------------------------------------------


def test_the_layer_is_assigned_from_the_provenance_at_record_time(world: World) -> None:
    span = {
        "tab": "urok",
        "step": "s1",
        "activity": None,
        "item": None,
        "block": 0,
        "span": 0,
        "start": 0,
        "end": len(PROSE),
        "source": "record",
        "ref": "T-1",
        "role": "record_print",
        "text": PROSE,
        "record_kind": "quote",
        "record_side": None,
        "option_origin": None,
        "is_key": None,
    }
    world.provenance(2, [span])
    world.record(world.make_return(2, [finding("F-01")]))
    assert world.db_rows("findings")[0]["layer"] == "pack"


# --- second seat -------------------------------------------------------------------------------------------------------------


@pytest.fixture
def sampled(monkeypatch: pytest.MonkeyPatch) -> None:
    real = findings_db.load_parameters
    monkeypatch.setattr(findings_db, "load_parameters", lambda *a, **kw: {**real(), "second_seat_divisor": 1})


def test_a_second_seat_review_on_the_same_manifest_writes_an_agreement_row(world: World, sampled: None) -> None:
    world.task("review-google", "agy", "gemini-3.8-flash-high")
    first = world.record(world.make_return(2, [finding("F-01", severity="MAJOR")]))
    assert first.verdict == "REVISE"
    made = world.make_return(2, [finding("F-01", severity="MAJOR")])
    outcome = world.record(made, task_id="review-google", second=True)
    assert outcome.accepted and outcome.agreement["agreed"] is True and outcome.verdict_file is None
    [row] = world.db_rows("agreement")
    assert (row["level"], row["slug"], row["lesson_n"], bool(row["agreed"])) == (LEVEL, SLUG, 2, True)
    assert json.loads(row["disagreed_json"]) == []
    assert world.db_rows("budgets")[0]["revise_rounds"] == 1  # the second seat is not a round
    assert (
        yaml.safe_load(world.verdict_file(2).read_bytes())["attempt_id"] == "attempt-1"
    )  # the first seat's verdict stands
    [second_attempt] = world.db_rows("attempts", "role = 'second'")
    assert second_attempt["reviewer_family"] == "google"


def test_a_blocking_disagreement_opens_a_settle_item_that_holds_the_module(world: World, sampled: None) -> None:
    world.task("review-google", "agy", "gemini-3.8-flash-high")
    world.record(world.make_return(2, [finding("F-01", severity="MAJOR")]))
    outcome = world.record(world.make_return(2), task_id="review-google", second=True)
    assert outcome.agreement["agreed"] is False
    [item] = world.db_rows("settle_items")
    assert item["kind"] == "second_seat_disagreement" and item["outcome"] is None
    assert item["finding_ref"].endswith("/attempt-1/F-01") and outcome.settle_items == [item["item_id"]]


def test_a_second_seat_of_the_first_reviewers_family_is_refused(world: World, sampled: None) -> None:
    world.record(world.make_return(2))
    world.task("review-claude-2", "claude", "claude-opus-5-5")  # the first reviewer's family
    with pytest.raises(record.RecordError, match="third family"):
        world.record(world.make_return(2), task_id="review-claude-2", second=True)
    assert world.db_rows("agreement") == [] and len(world.db_rows("attempts")) == 1


def test_a_second_seat_of_the_writers_family_is_a_rejected_attempt(world: World, sampled: None) -> None:
    world.record(world.make_return(2))
    world.task("review-gpt", "codex", "gpt-6-astra")  # the writer's family
    outcome = world.record(world.make_return(2), task_id="review-gpt", second=True)
    assert not outcome.accepted and outcome.verdict == "REJECTED"
    assert record.SAME_FAMILY_REVIEW in outcome.rejection_codes
    [second] = world.db_rows("attempts", "role = 'second'")
    assert second["verdict"] == "REJECTED" and record.SAME_FAMILY_REVIEW in json.loads(second["rejection_codes_json"])
    assert world.db_rows("agreement") == []


def test_a_second_seat_needs_the_lesson_to_be_sampled_and_a_first_review_on_that_manifest(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    world.task("review-google", "agy", "gemini-3.8-flash-high")
    real = findings_db.load_parameters
    monkeypatch.setattr(findings_db, "load_parameters", lambda *a, **kw: {**real(), "second_seat_divisor": 10**9})
    n = next(n for n in (1, 2, 3) if not second_seat.selected(LEVEL, SLUG, n, 10**9))
    with pytest.raises(record.RecordError, match="not in the second-seat sample"):
        world.record(world.make_return(n), task_id="review-google", second=True)
    monkeypatch.setattr(findings_db, "load_parameters", lambda *a, **kw: {**real(), "second_seat_divisor": 1})
    with pytest.raises(record.RecordError, match="no first-seat review"):
        world.record(world.make_return(n), task_id="review-google", second=True)


# --- the CLI ---------------------------------------------------------------------------------------------------------------------------


def _argv(world: World, made: dict[str, Any], *extra: str) -> list[str]:
    return [
        str(made["review"]),
        "--manifest",
        str(world.manifest(made["n"])),
        "--lesson",
        str(world.expanded(made["n"])),
        "--ledger",
        str(made["ledger"]),
        "--task-id",
        "review-claude",
        "--repo-root",
        str(world.root),
        "--db",
        str(world.db),
        "--tasks-dir",
        str(world.tasks_dir),
        *extra,
    ]


def test_the_cli_prints_one_json_object_and_exits_by_outcome(world: World, capsys: pytest.CaptureFixture[str]) -> None:
    assert record.main(_argv(world, world.make_return(1))) == 0
    accepted = json.loads(capsys.readouterr().out)
    assert (
        accepted["accepted"] is True
        and accepted["verdict"] == "APPROVE"
        and accepted["verdict_file"].endswith("lesson-1.verdict.yaml")
    )
    assert record.main(_argv(world, world.make_return(2, [finding(evidence={"receipt": "nope"})]))) == 1
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["accepted"] is False and codes.RECEIPT_NOT_IN_LEDGER in rejected["rejection_codes"]
    assert "record --failure" in rejected["next"]
    for _ in range(2):
        assert record.main(_argv(world, world.make_return(2, [finding("F-01", severity="MAJOR")]))) == 0
    assert (
        record.main(_argv(world, world.make_return(2, [finding("F-01", severity="MAJOR")]))) == 3
    )  # the third REVISE is terminal
    assert json.loads(capsys.readouterr().out.split("\n}\n")[-2] + "\n}")["terminal"][0]["transition"] == "operator"
    assert record.main([*_argv(world, world.make_return(1)), "--task-id", "nope"]) == 2


def test_the_cli_help_lists_every_option_and_example() -> None:
    text = record.build_parser().format_help()
    for word in ("--failure", "--seed-id", "--second-seat", "--task-id", "Examples:", "Exit codes"):
        assert word in text


# --- a plan verdict written by record is accepted by plan-promote (the product path) -----------------------------------------------------------


def test_a_plan_verdict_written_by_record_is_accepted_by_plan_promote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    from tests.build.test_fresh_plan_review import fake_verify, make_manifest
    from tests.curriculum.test_plan_validate import LEVEL as PLAN_LEVEL
    from tests.curriculum.test_plan_validate import SLUG as PLAN_SLUG
    from tests.helpers.plan_review_world import build_env

    monkeypatch.setattr("scripts.build.fresh.plan_manifest.verify_pack_strict", fake_verify())
    env = build_env(tmp_path / "tree")
    digest = make_manifest(env, capsys)
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "plan-review-task.json").write_text(
        json.dumps({"agent": "claude", "model": "claude-sonnet-5"}), encoding="utf-8"
    )
    ledger = tmp_path / "ledgers" / "review-p" / "attempt-p.jsonl"
    create_empty_ledger(ledger)
    review = tmp_path / "plan.return.yaml"
    _dump(
        review,
        _review(
            kind="plan",
            manifest_hash=digest,
            checks={name: "clean" for name in PLAN_CHECKS},
            findings=[],
            attempt_id="attempt-p",
            review_id="review-p",
        ),
    )
    assert pm.plan_review_status(PLAN_LEVEL, PLAN_SLUG, repo_root=env.root)["state"] == "unreviewed"

    outcome = record.record_return(
        review,
        manifest_path=env.state_dir / "plan-review.manifest.yaml",
        ledger_path=ledger,
        task_id="plan-review-task",
        repo_root=env.root,
        db_path=tmp_path / "plan.sqlite",
        tasks_dir=tasks,
    )
    assert outcome.accepted and outcome.verdict == "APPROVE" and outcome.verdict_file.endswith("plan-review.yaml")
    written = yaml.safe_load((env.state_dir / "plan-review.yaml").read_bytes())
    assert (
        written["verdict"] == "APPROVE"
        and written["attempt_id"] == "attempt-p"
        and written["manifest_sha256"] == digest
    )
    assert (env.state_dir / "plan-review.attempt-p.yaml").read_bytes() == review.read_bytes()
    assert pm.plan_review_status(PLAN_LEVEL, PLAN_SLUG, repo_root=env.root)["state"] == "reviewed_pending_promotion"

    receipt = promote_plan(
        PLAN_LEVEL, PLAN_SLUG, repo_root=env.root
    )  # the transactional promotion reads what record wrote
    assert (
        receipt["already_promoted"] is False
        and receipt["attempt_id"] == "attempt-p"
        and receipt["manifest_sha256"] == digest
    )
    assert pm.plan_review_status(PLAN_LEVEL, PLAN_SLUG, repo_root=env.root)["state"] == "reviewed_promoted"
    [row] = [r for r in _rows(tmp_path / "plan.sqlite", "attempts")]
    assert row["kind"] == "plan" and row["lesson_n"] is None and row["verdict"] == "APPROVE"


def test_a_plan_revise_is_written_and_promote_refuses_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    from tests.build.test_fresh_plan_review import fake_verify, make_manifest
    from tests.curriculum.test_plan_validate import LEVEL as PLAN_LEVEL
    from tests.curriculum.test_plan_validate import SLUG as PLAN_SLUG
    from tests.helpers.plan_review_world import build_env

    monkeypatch.setattr("scripts.build.fresh.plan_manifest.verify_pack_strict", fake_verify())
    env = build_env(tmp_path / "tree")
    digest = make_manifest(env, capsys)
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "t.json").write_text(json.dumps({"agent": "claude", "model": "claude-sonnet-5"}), encoding="utf-8")
    ledger = tmp_path / "ledgers" / "review-p" / "attempt-p.jsonl"
    create_empty_ledger(ledger)
    receipt_id = _record(
        ledger, manifest=digest, result="attested result", attempt_id="attempt-p", review_id="review-p"
    )
    checks = {name: "clean" for name in PLAN_CHECKS}
    checks["sequencing"] = ["F-01"]
    plan_finding = {
        "id": "F-01",
        "status": "active",
        "locations": [{"lesson": 1, "step": "s1", "field": "teach", "quote": "first letter"}],
        "dimension": "plan_defect",
        "severity": "MAJOR",
        "claim": "A claim.",
        "evidence": {"receipt": receipt_id},
    }
    review = tmp_path / "plan.return.yaml"
    _dump(
        review,
        _review(
            kind="plan",
            manifest_hash=digest,
            checks=checks,
            findings=[plan_finding],
            attempt_id="attempt-p",
            review_id="review-p",
        ),
    )
    outcome = record.record_return(
        review,
        manifest_path=env.state_dir / "plan-review.manifest.yaml",
        ledger_path=ledger,
        task_id="t",
        repo_root=env.root,
        db_path=tmp_path / "plan.sqlite",
        tasks_dir=tasks,
    )
    assert outcome.accepted and outcome.verdict == "REVISE"
    assert yaml.safe_load((env.state_dir / "plan-review.yaml").read_bytes())["verdict"] == "REVISE"
    assert pm.plan_review_status(PLAN_LEVEL, PLAN_SLUG, repo_root=env.root)["state"] == "not_approved"
    with pytest.raises(pm.PlanReviewError):
        promote_plan(PLAN_LEVEL, PLAN_SLUG, repo_root=env.root)
    assert _rows(tmp_path / "plan.sqlite", "findings")[0]["layer"] == "plan"


def _rows(path: Path, table: str) -> list[sqlite3.Row]:
    conn = findings_db.connect(path)
    try:
        return conn.execute(f"SELECT * FROM {table}").fetchall()
    finally:
        conn.close()


# --- the cross-family gate --------------------------------------------------------------------------------


def test_a_first_seat_of_the_writers_own_family_is_a_rejected_attempt(world: World) -> None:
    world.task("review-gpt", "codex", "gpt-6-astra")  # the fixture's writer model is gpt-6-astra too
    made = world.make_return(2, [finding("F-01", severity="MAJOR")])
    outcome = world.record(made, task_id="review-gpt")
    assert not outcome.accepted and outcome.verdict == "REJECTED"
    assert record.SAME_FAMILY_REVIEW in outcome.rejection_codes
    [attempt] = world.db_rows("attempts")
    assert attempt["verdict"] == "REJECTED" and attempt["reviewer_family"] == attempt["writer_family"] == "openai"
    assert json.loads(attempt["rejection_codes_json"]) == [record.SAME_FAMILY_REVIEW]
    assert world.db_rows("findings") == [] and world.db_rows("budgets") == [] and world.db_rows("settle_items") == []
    assert not world.verdict_file(2).exists()


def test_a_reviewer_of_another_family_is_not_rejected_for_family(world: World) -> None:
    outcome = world.record(world.make_return(2))
    assert outcome.accepted and record.SAME_FAMILY_REVIEW not in outcome.rejection_codes


@pytest.mark.parametrize(
    "writer_record",
    [{"writer": "mystery-lane", "model": "mystery-model-9"}, {"writer": "auto", "model": "unknown"}, None],
)
def test_an_unresolvable_writer_identity_refuses_the_attempt_and_records_nothing(
    world: World, writer_record: dict[str, str] | None
) -> None:
    path = world.state_dir / "lesson-2.writer.yaml"
    if writer_record is None:
        path.unlink()
    else:
        path.write_bytes(yaml.safe_dump(writer_record).encode())
    made = world.make_return(2)
    with pytest.raises(record.RecordError, match=record.WRITER_IDENTITY_UNKNOWN) as raised:
        world.record(made)
    assert raised.value.code == record.WRITER_IDENTITY_UNKNOWN
    assert world.db_rows("attempts") == [] and not world.verdict_file(2).exists()
    assert not list(world.state_dir.glob("*.review.*"))


def test_an_unresolvable_writer_refuses_a_second_seat_too(world: World, sampled: None) -> None:
    world.record(world.make_return(2))
    world.task("review-google", "agy", "gemini-3.8-flash-high")
    (world.state_dir / "lesson-2.writer.yaml").write_bytes(yaml.safe_dump({"writer": "x", "model": "y"}).encode())
    with pytest.raises(record.RecordError, match=record.WRITER_IDENTITY_UNKNOWN):
        world.record(world.make_return(2), task_id="review-google", second=True)


# --- the verdict file is a projection of the database ------------------------------------------------------


def latest_row(world: World, n: int) -> sqlite3.Row:
    conn = findings_db.connect(world.db)
    try:
        return findings_db.latest_accepted(conn, LEVEL, SLUG, "lesson", n)
    finally:
        conn.close()


def assert_file_is_latest_row(world: World, n: int) -> None:
    latest = latest_row(world, n)
    on_disk = yaml.safe_load(world.verdict_file(n).read_bytes())
    assert on_disk == {name: latest[name] for name in ("verdict", "attempt_id", "manifest_sha256", "validated_at")}


def fail_verdict_writes(monkeypatch: pytest.MonkeyPatch) -> dict[str, bool]:
    """Make every verdict-file write fail while ``switch["on"]``; returns the switch."""
    real = lock.atomic_write
    switch = {"on": True}

    def failing(path: Path, content: bytes, **kwargs: Any) -> None:
        if switch["on"] and Path(path).name.endswith(".verdict.yaml"):
            raise OSError("no space left on device")
        real(path, content, **kwargs)

    monkeypatch.setattr(lock, "atomic_write", failing)
    return switch


def test_a_failed_verdict_write_after_the_commit_keeps_the_attempt_and_reports_the_stale_file(
    world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world.record(world.make_return(2))  # APPROVE, published
    switch = fail_verdict_writes(monkeypatch)
    made = world.make_return(2, [finding("F-01", severity="MAJOR")])
    assert record.main(_argv(world, made)) == 2  # recorded, but the file could not follow
    printed = json.loads(capsys.readouterr().out)
    assert printed["accepted"] and printed["verdict"] == "REVISE" and "no space left" in printed["projection_error"]
    assert "--repair-projections" in printed["next"]
    assert latest_row(world, 2)["verdict"] == "REVISE" and len(world.db_rows("attempts")) == 2
    assert yaml.safe_load(world.verdict_file(2).read_bytes())["verdict"] == "APPROVE"  # stale, and the row says so
    switch["on"] = False
    assert record.main(_argv(world, made)) == 0  # recording it again republishes from the database
    assert_file_is_latest_row(world, 2)
    assert yaml.safe_load(world.verdict_file(2).read_bytes())["verdict"] == "REVISE"


def test_replaying_an_older_attempt_never_republishes_it_over_a_newer_one(world: World) -> None:
    one = world.make_return(2)
    world.record(one)  # attempt 1: APPROVE
    two = world.make_return(2, [finding("F-01", severity="MAJOR")])
    world.record(two)  # attempt 2: REVISE
    again = world.record(one)
    assert again.replay and again.verdict == "APPROVE"
    assert_file_is_latest_row(world, 2)
    on_disk = yaml.safe_load(world.verdict_file(2).read_bytes())
    assert (on_disk["verdict"], on_disk["attempt_id"]) == ("REVISE", two["attempt_id"])


def test_latest_is_the_highest_sequence_not_the_latest_timestamp(world: World) -> None:
    world.record(world.make_return(2), now="2031-01-01T00:00:00+00:00")
    two = world.make_return(2, [finding("F-01", severity="MAJOR")])
    world.record(two, now="2020-01-01T00:00:00+00:00")  # a clock that went backwards
    assert latest_row(world, 2)["attempt_id"] == two["attempt_id"]
    assert_file_is_latest_row(world, 2)


def test_a_replay_publishes_the_projection_that_a_crash_left_out(world: World) -> None:
    made = world.make_return(2)
    world.record(made)
    world.verdict_file(2).unlink()
    assert world.record(made).replay
    assert_file_is_latest_row(world, 2)


# --- the raw return is reserved, validated and stored as one set of bytes ---------------------------------------


def two_returns_of_one_attempt(world: World) -> tuple[dict[str, Any], dict[str, Any]]:
    """Two different returns under one attempt id (kept apart on disk: make_return names files by attempt)."""
    ids = ("review-x", "attempt-x")
    first = world.make_return(2, ids=ids)
    kept_first = world.out / "first.return.yaml"
    kept_first.write_bytes(first["review"].read_bytes())
    second = world.make_return(2, [finding("F-01", severity="MAJOR")], ids=ids)
    kept_second = world.out / "second.return.yaml"
    kept_second.write_bytes(second["review"].read_bytes())
    return {**first, "review": kept_first}, {**second, "review": kept_second}


def saved_return(world: World, made: dict[str, Any]) -> Path:
    return world.state_dir / f"lesson-2.review.{made['attempt_id']}.yaml"


def test_two_recorders_of_one_attempt_id_with_different_bytes_cannot_validate_one_and_store_the_other(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    a, b = two_returns_of_one_attempt(world)
    real = record._rejection_codes
    seen: list[str] = []

    def racing(*args: Any, **kwargs: Any) -> list[str]:
        # recorder B runs to its own reservation while recorder A is still validating
        with pytest.raises(record.RecordError) as raised:
            world.record(b)
        seen.append(raised.value.code)
        return real(*args, **kwargs)

    monkeypatch.setattr(record, "_rejection_codes", racing)
    outcome = world.record(a)
    assert seen == [record.ATTEMPT_RETURN_CONFLICT]
    assert outcome.accepted and outcome.findings == 0
    assert saved_return(world, a).read_bytes() == a["review"].read_bytes()
    [attempt] = world.db_rows("attempts")
    assert attempt["return_sha256"] == hashlib.sha256(a["review"].read_bytes()).hexdigest()
    assert world.db_rows("findings") == []  # B's finding was never stored


def test_a_reserved_return_replaced_before_the_insert_is_refused(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    a, b = two_returns_of_one_attempt(world)
    real = record._rejection_codes

    def swapping(*args: Any, **kwargs: Any) -> list[str]:
        codes_ = real(*args, **kwargs)
        lock.atomic_write(saved_return(world, a), b["review"].read_bytes())  # replaced after the validation
        return codes_

    monkeypatch.setattr(record, "_rejection_codes", swapping)
    with pytest.raises(record.RecordError, match=record.ATTEMPT_RETURN_CONFLICT):
        world.record(a)
    assert world.db_rows("attempts") == [] and not world.verdict_file(2).exists()


def test_a_reserved_return_replaced_during_the_insert_rolls_the_transaction_back(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    a, b = two_returns_of_one_attempt(world)
    real = findings_db.insert_attempt

    def swapping(conn: Any, row: dict[str, Any]) -> None:
        real(conn, row)
        lock.atomic_write(saved_return(world, a), b["review"].read_bytes())  # replaced after the row is written

    monkeypatch.setattr(findings_db, "insert_attempt", swapping)
    with pytest.raises(record.RecordError, match=record.ATTEMPT_RETURN_CONFLICT):
        world.record(a)
    assert world.db_rows("attempts") == [] and world.db_rows("findings") == [] and not world.verdict_file(2).exists()


def test_a_reserved_return_swapped_during_validation_and_restored_is_not_what_is_validated(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = ("review-x", "attempt-x")
    bad = world.make_return(
        2, [finding("F-01", locations=[{"tab": "urok", "quote": "no such text in the unit"}])], ids=ids
    )
    bad_bytes = bad["review"].read_bytes()
    kept_bad = world.out / "bad.return.yaml"
    kept_bad.write_bytes(bad_bytes)
    good = world.make_return(2, [finding("F-01")], ids=ids)  # valid on its own, same attempt id
    good_bytes = good["review"].read_bytes()
    assert good_bytes != bad_bytes
    reserved = saved_return(world, bad)
    real = record.validate_review

    def swapping(path: Path, **kwargs: Any) -> Any:
        assert Path(path) != reserved  # the validator is never pointed at the reserved name
        lock.atomic_write(reserved, good_bytes)  # a valid return sits under the name while validating...
        try:
            return real(path, **kwargs)
        finally:
            lock.atomic_write(reserved, bad_bytes)  # ...and the recorded bytes are back before the hash check

    monkeypatch.setattr(record, "validate_review", swapping)
    outcome = world.record({**bad, "review": kept_bad})
    assert not outcome.accepted and outcome.verdict == "REJECTED"
    assert codes.QUOTE_NOT_IN_UNIT in outcome.rejection_codes
    assert world.db_rows("findings") == []
    [attempt] = world.db_rows("attempts")
    assert attempt["verdict"] == "REJECTED" and attempt["return_sha256"] == hashlib.sha256(bad_bytes).hexdigest()


def test_a_different_return_under_a_reserved_name_is_refused_even_with_no_row(world: World) -> None:
    a, b = two_returns_of_one_attempt(world)
    record._reserve_return(world.root, world.state_dir, saved_return(world, a).name, a["review"].read_bytes())
    with pytest.raises(record.RecordError, match=record.ATTEMPT_RETURN_CONFLICT):
        world.record(b)
    assert saved_return(world, a).read_bytes() == a["review"].read_bytes() and world.db_rows("attempts") == []
    assert world.record(a).accepted  # the same bytes under the reserved name are the same attempt: idempotent
    assert not list(world.state_dir.glob(".lesson-2.review.*"))  # no temporary file is left behind


def test_recording_a_recorded_attempt_with_different_bytes_is_an_attempt_return_conflict(world: World) -> None:
    a, b = two_returns_of_one_attempt(world)
    world.record(a)
    with pytest.raises(record.RecordError) as raised:
        world.record(b)
    assert raised.value.code == record.ATTEMPT_RETURN_CONFLICT
    assert saved_return(world, a).read_bytes() == a["review"].read_bytes()


# --- claims raised against an older manifest are moot once the lesson is reviewed on a newer one ------------------


def regenerate_lesson_two(world: World) -> None:
    (world.page_dir / "2.mdx").write_text("# Lesson 2 regenerated\n", encoding="utf-8")
    world.write_manifests((2, 3))


def test_a_newer_manifests_accepted_attempt_closes_the_older_open_items_as_moot(world: World) -> None:
    old = world.make_return(2, [unsupported("F-01")])
    world.record(old)
    [item] = world.db_rows("settle_items")
    old_manifest = world.digest(2)
    regenerate_lesson_two(world)
    assert world.digest(2) != old_manifest
    new = world.make_return(2)  # the regenerated lesson no longer makes the claim
    outcome = world.record(new)
    assert outcome.accepted and outcome.moot_items == [item["item_id"]]
    [closed] = world.db_rows("settle_items")
    assert closed["outcome"] == findings_db.MOOT_SUPERSEDED and closed["superseded_by"] == new["attempt_id"]
    assert not closed["needs_operator"] and closed["manifest_sha256"] == old_manifest


def test_a_claim_raised_again_on_the_new_manifest_opens_a_new_item(world: World) -> None:
    world.record(world.make_return(2, [unsupported("F-01")]))
    regenerate_lesson_two(world)
    again = world.make_return(2, [unsupported("F-01")])
    outcome = world.record(again)
    items = world.db_rows("settle_items", "1=1 ORDER BY item_id")
    assert [row["outcome"] for row in items] == [findings_db.MOOT_SUPERSEDED, None]
    assert items[1]["manifest_sha256"] == world.digest(2) and outcome.settle_items == [items[1]["item_id"]]


def test_an_attempt_on_the_same_manifest_closes_nothing_and_neither_does_another_lesson(world: World) -> None:
    world.record(world.make_return(2, [unsupported("F-01")]))
    world.record(world.make_return(2))  # a re-review of the same manifest
    world.record(world.make_return(1))  # another lesson
    assert [row["outcome"] for row in world.db_rows("settle_items")] == [None]


def test_nothing_is_closed_when_the_attempts_manifest_is_not_the_current_one(world: World) -> None:
    world.record(world.make_return(2, [unsupported("F-01")]))
    regenerate_lesson_two(world)
    newer = world.make_return(2)
    sidecar = world.state_dir / "lesson-2.manifest.sha256"
    kept = sidecar.read_bytes()
    sidecar.unlink()  # the engine's pointer is gone: current is unknown
    outcome = world.record(newer)
    assert outcome.accepted and outcome.moot_items == [] and "cannot be established" in outcome.moot_note
    assert [row["outcome"] for row in world.db_rows("settle_items")] == [None]
    sidecar.write_bytes(kept)  # the pointer is back; the attempt is replayed and now closes what it made moot
    replayed = world.record(newer)
    assert replayed.replay and len(replayed.moot_items) == 1 and replayed.moot_note is None
    [closed] = world.db_rows("settle_items")
    assert closed["outcome"] == findings_db.MOOT_SUPERSEDED and closed["superseded_by"] == newer["attempt_id"]
    assert world.record(newer).moot_items == []  # idempotent: nothing is left to close


def test_repair_projections_closes_the_items_record_could_not(world: World) -> None:
    world.record(world.make_return(2, [unsupported("F-01")]))
    regenerate_lesson_two(world)
    newer = world.make_return(2)
    sidecar = world.state_dir / "lesson-2.manifest.sha256"
    kept = sidecar.read_bytes()
    sidecar.unlink()
    world.record(newer)
    sidecar.write_bytes(kept)
    conn = findings_db.connect(world.db)
    try:
        repair = fixloop.repair_projections(conn, world.root, LEVEL, SLUG)
        again = fixloop.repair_projections(conn, world.root, LEVEL, SLUG)
    finally:
        conn.close()
    [item] = world.db_rows("settle_items")
    assert repair["moot_closed"] == [str(item["item_id"])] and again["moot_closed"] == []
    assert item["outcome"] == findings_db.MOOT_SUPERSEDED
