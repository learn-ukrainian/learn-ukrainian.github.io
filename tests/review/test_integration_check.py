"""The R2b integration check harness (#8430): its own behaviour, with negative controls.

``run-crafted`` must pass on the code as it is and must FAIL when the product path it proves is broken: each
negative control breaks one seam, runs the WHOLE crafted suite and expects exactly the cases that depend on
that seam to fail (and every other case to pass). ``prepare-real`` + ``finish-real`` are exercised with crafted
returns standing in for the real seats: the ledgers and dispatch records are redirected to a temporary tree, so
nothing of ``batch_state`` is touched.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.build.fresh import assemble
from scripts.build.fresh import plan_manifest as pm
from scripts.review import findings_db, fixloop, record, second_seat, settle
from scripts.review import integration_check as ic
from scripts.review.receipts import ledger
from tests.build.test_fresh_plan_review import fake_verify
from tests.review.test_r1_schema_ledger import PLAN_CHECKS, _dump, _review
from tests.review.test_record import LEVEL, SLUG, finding

pytestmark = pytest.mark.reads_content

STATE = ic.STATE_NAME


# --- run-crafted ------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def crafted(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str, Path]:
    import contextlib
    import io

    out = tmp_path_factory.mktemp("crafted") / "out"
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        code = ic.main(["run-crafted", "--out", str(out)])
    return code, printed.getvalue(), out


def test_every_crafted_case_passes_and_prints_its_evidence(crafted: tuple[int, str, Path]) -> None:
    code, printed, out = crafted
    lines = [line for line in printed.splitlines() if line.startswith(("PASS", "FAIL"))]
    assert code == 0, printed
    assert [line.split()[0:2] for line in lines] == [["PASS", f"({key})"] for key in ("iii", "v", "vi", "vii", "viii")]
    assert "5/5 crafted cases pass" in printed
    # the evidence is concrete: paths under --out, hashes, database counts
    joined = "\n".join(lines)
    assert "sha256=" in joined and "findings=5" in joined and "agreement rows=1" in joined
    assert (
        out / "viii-module-verdict/curriculum/l2-uk-en/evidence/a1/_state/fixture-module/module-verdict.yaml"
    ).is_file()


def test_the_module_verdict_the_check_reports_is_the_engines_own_file(crafted: tuple[int, str, Path]) -> None:
    _, _, out = crafted
    state = out / "viii-module-verdict/curriculum/l2-uk-en/evidence/a1/_state/fixture-module"
    document = yaml.safe_load((state / "module-verdict.yaml").read_bytes())
    assert document["verdict"] == "APPROVE" and [row["n"] for row in document["lessons"]] == [1, 2, 3]
    assert (state / "module.closure.yaml").is_file() and (state / pm.RECEIPT_NAME).is_file()
    assert not (Path(ic.REPO_ROOT) / "curriculum" / "l2-uk-en" / "evidence" / "a1" / "_state" / SLUG).exists()


REAL_KIND = assemble.derive_record_kind

# each control: (what is broken, module, attribute, replacement, the cases that must then FAIL)
CONTROLS = [
    ("every span is blamed on the writer", fixloop, "span_layer", lambda span: fixloop.REGENERATE, {"iii"}),
    (
        "the engine prints no word record kind",
        assemble,
        "derive_record_kind",
        lambda ref, tab=None: "note" if ref.startswith("W-") else REAL_KIND(ref, tab),
        {"iii"},
    ),
    # the sampling rule also decides whether (vi) and (viii) need a second seat before APPROVE
    ("nothing is sampled for a second seat", second_seat, "selected", lambda *a, **kw: False, {"v", "vi", "viii"}),
    ("a regeneration stales nobody", fixloop, "dependents", lambda closure, n: [], {"vi"}),
    ("no budget is terminal for the module verdict", fixloop, "terminal_transitions", lambda *a, **kw: [], {"vii"}),
    # #8774: without the refusal a review past the terminal budget is accepted and counted as one more round
    ("a review past a terminal budget is accepted", record, "_terminal_budget", lambda *a, **kw: None, {"vii"}),
    # the plan gate is part of every APPROVE of the module verdict
    (
        "the plan is never reviewed",
        pm,
        "plan_review_status",
        lambda *a, **kw: {"state": "unreviewed", "stale": {}},
        {"v", "vi", "viii"},
    ),
]


def test_the_whole_crafted_suite_passes_before_any_break(tmp_path: Path) -> None:
    assert [(case.key, case.passed) for case in ic.run_all(tmp_path)] == [(key, True) for key, _, _ in ic.CRAFTED_CASES]


@pytest.mark.parametrize(
    ("broken", "target", "attribute", "replacement", "failing"), CONTROLS, ids=[c[0] for c in CONTROLS]
)
def test_breaking_a_product_path_fails_exactly_the_cases_that_prove_it(
    broken: str,
    target: Any,
    attribute: str,
    replacement: Any,
    failing: set[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(target, attribute, replacement)
    cases = ic.run_all(tmp_path)
    assert {case.key for case in cases if not case.passed} == failing, "\n".join(case.line() for case in cases)
    assert all(case.line().startswith("FAIL") for case in cases if case.key in failing)


def test_a_crash_inside_a_case_is_a_failure_with_its_location(tmp_path: Path) -> None:
    def crash(case: ic.Case) -> None:
        raise ValueError("boom")

    case = ic.run_case("x", "crash", crash, tmp_path)
    assert not case.passed and "ValueError: boom" in case.line() and "test_integration_check.py" in case.line()


def test_the_output_directory_must_be_empty_and_outside_the_repository(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="inside the repository"):
        ic.prepare_out(ic.REPO_ROOT / "scratch-out")
    (tmp_path / "used").mkdir()
    (tmp_path / "used" / "file").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit, match="not empty"):
        ic.prepare_out(tmp_path / "used")
    assert ic.prepare_out(tmp_path / "fresh").is_dir()


def test_the_help_states_use_and_exit_codes(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        ic.main(["--help"])
    text = capsys.readouterr().out
    for word in ("run-crafted", "prepare-real", "finish-real", "Examples:", "Exit codes", "Do NOT"):
        assert word in text


# --- prepare-real / finish-real ----------------------------------------------------------------------


def prepare(root: Path) -> tuple[Path, Path, Path]:
    """prepare-real with the ledgers and dispatch records redirected to a temporary tree."""
    receipts, tasks = root / "receipts", root / "tasks"
    receipts.mkdir()
    tasks.mkdir()
    patch = pytest.MonkeyPatch()
    patch.setattr(ic, "RECEIPTS_ROOT", receipts)
    patch.setattr(ic, "TASKS_DIR", tasks)
    try:
        assert ic.main(["prepare-real", "--out", str(root / "out")]) == 0
    finally:
        patch.undo()
    return root / "out", receipts, tasks


@pytest.fixture(scope="module")
def prepared(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, Path]:
    """A prepared check whose seats never answered (nothing here is ever recorded)."""
    return prepare(tmp_path_factory.mktemp("real"))


def card(out: Path, key: str) -> dict[str, Any]:
    return json.loads((out / "cards" / f"{key}.json").read_text(encoding="utf-8"))


def state_of(out: Path, key: str) -> dict[str, Any]:
    return json.loads((out / STATE).read_text(encoding="utf-8"))["cases"][key]


def test_prepare_writes_three_cards_with_exact_hashes_and_commands(prepared: tuple[Path, Path, Path]) -> None:
    out, receipts, tasks = prepared
    assert list(tasks.iterdir()) == [] and list(receipts.iterdir()) == []  # nothing was dispatched or recorded
    for key, kind in (("i", "plan"), ("ii", "lesson"), ("iv", "settle")):
        one = card(out, key)
        prompt = Path(one["prompt"])
        assert hashlib.sha256(prompt.read_bytes()).hexdigest() == one["prompt_sha256"]
        assert Path(f"{prompt}.sha256").read_text(encoding="ascii").strip() == one["prompt_sha256"]
        assert hashlib.sha256(Path(one["manifest"]).read_bytes()).hexdigest() == one["manifest_sha256"]
        assert one["prompt_check"].startswith("PASS")
        manifest = yaml.safe_load(Path(one["manifest"]).read_bytes())
        assert manifest["kind"] == kind
        argv = one["dispatch"]
        assert argv[argv.index("--review-attempt") + 1] == one["manifest"]
        assert argv[argv.index("--review-id") + 1] == one["review_id"]
        assert argv[argv.index("--attempt-id") + 1] == one["attempt_id"]
        assert (
            argv[argv.index("--task-id") + 1] == one["task_id"]
            and argv[argv.index("--prompt-file") + 1] == one["prompt"]
        )
        assert argv[argv.index("--mode") + 1] == "read-only" and "--worktree" not in argv
        assert (
            Path(one["ledger"]).parent.name == one["review_id"]
            and Path(one["ledger"]).name == f"{one['attempt_id']}.jsonl"
        )
        assert one["record"][2] == ("scripts.review.settle" if kind == "settle" else "scripts.review.record")
        assert one["return_path"] in one["record"] and one["record_cmd"].startswith("cd ")
    assert card(out, "ii")["record"][card(out, "ii")["record"].index("--lesson") + 1].endswith("lesson-2.expanded.yaml")
    iv = card(out, "iv")
    assert iv["record"][iv["record"].index("--decided-by") + 1] == iv["task_id"]  # the decision is made under the task
    assert state_of(out, "iv")["ledger"] == iv["ledger"] and state_of(out, "iv")["tasks_dir"] == str(tasks)


def test_the_settle_item_alone_holds_the_module_while_the_seat_has_not_answered(
    prepared: tuple[Path, Path, Path],
) -> None:
    out, _, _ = prepared
    info = state_of(out, "iv")
    held = yaml.safe_load(Path(info["while_open_verdict"]).read_bytes())
    assert held["verdict"] == "HOLD" and [item["item_id"] for item in held["settle_items"]["open"]] == [info["item_id"]]
    assert [hold["code"] for hold in held["holds"]] == [
        "settle_open"
    ]  # nothing else holds it: lessons, plan, second seat
    assert [(row["n"], row["state"], row["verdict"]) for row in held["lessons"]] == [
        (n, "current", "APPROVE") for n in (1, 2, 3)
    ]
    assert held["plan"]["state"] == "reviewed_promoted"
    assert info["open_verdict"] == "HOLD" and info["open_holds"] == ["settle_open"]
    rows = ic._rows(Path(info["db"]), "SELECT kind, outcome, lesson_n FROM settle_items")
    assert [tuple(row) for row in rows] == [("unsupported_by_source", None, 1)]
    assert [row["role"] for row in ic._rows(Path(info["db"]), "SELECT role FROM attempts WHERE role = 'second'")] == [
        "second"
    ]


def test_finish_fails_every_real_case_before_any_return_is_recorded(
    prepared: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    out, _, _ = prepared
    assert ic.main(["finish-real", "--out", str(out)]) == 1
    lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith(("PASS", "FAIL"))]
    assert [line.split()[:2] for line in lines] == [["FAIL", "(i)"], ["FAIL", "(ii)"], ["FAIL", "(iv)"]]


def seat_record(tasks: Path, task_id: str, model: str = "claude-sonnet-5") -> None:
    """The dispatch record ``delegate.py dispatch`` writes for a seat: what its identity is resolved from."""
    (tasks / f"{task_id}.json").write_text(json.dumps({"agent": "claude", "model": model}), encoding="utf-8")


def simulate_seats(out: Path, tasks: Path, *, settle_outcome: str = "refuted", settle_dispatched: bool = True) -> None:
    """What the driver does after the seats answered: the returns saved where the cards say, then the record commands."""
    mp = pytest.MonkeyPatch()
    try:
        # (i) the plan
        plan = card(out, "i")
        ledger.create_empty_ledger(Path(plan["ledger"]))
        Path(plan["return_path"]).parent.mkdir(exist_ok=True)
        _dump(
            Path(plan["return_path"]),
            _review(
                kind="plan",
                manifest_hash=plan["manifest_sha256"],
                checks={name: "clean" for name in PLAN_CHECKS},
                findings=[],
                attempt_id=plan["attempt_id"],
                review_id=plan["review_id"],
            ),
        )
        seat_record(tasks, plan["task_id"])
        mp.setattr(pm, "verify_pack_strict", fake_verify())
        assert record.main(plan["record"][3:]) == 0
        # (ii) lesson 2
        lesson = card(out, "ii")
        world = ic.ModuleWorld.attach(Path(lesson["world"]), mp)
        made = world.make_return(2, [finding("F-01")], ids=(lesson["review_id"], lesson["attempt_id"]))
        Path(lesson["ledger"]).parent.mkdir(parents=True, exist_ok=True)
        for suffix in ("", ".sha256"):
            shutil.copyfile(f"{made['ledger']}{suffix}", f"{lesson['ledger']}{suffix}")
        shutil.copyfile(made["review"], lesson["return_path"])
        seat_record(tasks, lesson["task_id"])
        assert record.main(lesson["record"][3:]) == 0
        # (iv) the settle seat: two hit receipts of two sources for a source_conflict, one hit otherwise
        item = card(out, "iv")
        ledger.create_empty_ledger(Path(item["ledger"]))
        manifest_sha = item["manifest_sha256"]
        calls = [("query_sum20", "entry text"), ("search_style_guide", "guide text")]
        receipts_made = [
            ledger.append(
                Path(item["ledger"]), review_id=item["review_id"], attempt_id=item["attempt_id"], manifest_sha256=manifest_sha,
                tool=tool, server_version="fixture", arguments={}, snapshots={}, status="ok", result=text,
                outcome_facts={"call_status": "ok", "hits": 1, "status": "hits_found", "unavailable": False},
            )
            for tool, text in calls
        ]  # fmt: skip
        used = receipts_made if settle_outcome == "source_conflict" else receipts_made[:1]
        reply = {
            "settle_schema": 1, "item_id": item["item_id"], "review_id": item["review_id"], "attempt_id": item["attempt_id"],
            "manifest_sha256": manifest_sha, "outcome": settle_outcome, "reason": "The cited result addresses the sense.",
            "evidence": [{"receipt": rid, "quote": text} for rid, (_, text) in zip(used, calls, strict=False)],
            "broadened_searches": [],
        }  # fmt: skip
        Path(item["return_path"]).write_text(yaml.safe_dump(reply, sort_keys=False), encoding="utf-8")
        if settle_dispatched:
            seat_record(tasks, item["task_id"])
        assert settle.main(item["record"][3:]) == 0
    finally:
        mp.undo()


@pytest.fixture(scope="module")
def finished(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """A prepared check whose three seats answered and were recorded (tests that break it restore it)."""
    out, _, tasks = prepare(tmp_path_factory.mktemp("finished"))
    simulate_seats(out, tasks)
    return out, tasks


def finish(out: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    capsys.readouterr()
    code = ic.main(["finish-real", "--out", str(out)])
    return code, capsys.readouterr().out


def verdicts(text: str) -> dict[str, str]:
    return {
        line.split()[1].strip("()"): line.split()[0] for line in text.splitlines() if line.startswith(("PASS", "FAIL"))
    }


def test_finish_passes_when_the_seats_returns_were_recorded(
    finished: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    out, _ = finished
    code, text = finish(out, capsys)
    assert code == 0 and verdicts(text) == {"i": "PASS", "ii": "PASS", "iv": "PASS"}, text
    plan, lesson, item = card(out, "i"), card(out, "ii"), card(out, "iv")
    assert "reviewed_promoted" in text and "plan-review.yaml verdict=APPROVE" in text
    state = Path(lesson["world"]) / "curriculum/l2-uk-en/evidence/a1/_state" / SLUG
    written = yaml.safe_load((state / "lesson-2.verdict.yaml").read_bytes())
    assert written["manifest_sha256"] == lesson["manifest_sha256"] and plan["attempt_id"] == "a1"
    assert "findings db=1 return=1" in text
    # the settle seat: outcome, the decision made under the card's task, its receipts, the verdict after (APPROVE)
    assert (
        "outcome=refuted" in text and f"decided_by={item['task_id']}" in text and "seat=claude/claude-sonnet-5" in text
    )
    assert "while open: HOLD ['settle_open']" in text and "after: APPROVE []" in text


def test_finish_rejects_a_verdict_file_naming_another_manifest(
    finished: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    out, _ = finished
    lesson = card(out, "ii")
    path = Path(lesson["world"]) / "curriculum/l2-uk-en/evidence/a1/_state" / SLUG / "lesson-2.verdict.yaml"
    original = path.read_bytes()
    try:
        document = yaml.safe_load(original)
        document["manifest_sha256"] = "0" * 64
        path.write_text(yaml.safe_dump(document), encoding="utf-8")
        code, text = finish(out, capsys)
        assert code == 1 and "not the manifest's sha256" in text and verdicts(text)["ii"] == "FAIL"
    finally:
        path.write_bytes(original)


def altered(db: Path, sql: str, *args: Any) -> None:
    conn = sqlite3.connect(db)
    try:
        conn.execute(sql, args)
        conn.commit()
    finally:
        conn.close()


@pytest.mark.parametrize("what", ["finding_json", "claim column", "another id"])
def test_a_stored_finding_that_differs_from_the_returned_one_fails_case_ii(
    what: str, finished: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """(ii) "database findings = return findings" is full equality of each finding, not ids or counts."""
    out, _ = finished
    db = Path(card(out, "ii")["world"]) / "batch_state/review-findings/a1.sqlite"
    attempt = card(out, "ii")["attempt_id"]
    [row] = ic._rows(db, "SELECT * FROM findings WHERE attempt_id = ?", attempt)
    stored = json.loads(row["finding_json"])
    stored["claim"] = "A different claim."
    updates = {
        "finding_json": ("UPDATE findings SET finding_json = ? WHERE attempt_id = ?", json.dumps(stored)),
        "claim column": ("UPDATE findings SET claim = ? WHERE attempt_id = ?", "A different claim."),
        "another id": ("UPDATE findings SET finding_id = ? WHERE attempt_id = ?", "F-99"),
    }
    sql, value = updates[what]
    try:
        altered(db, sql, value, attempt)
        code, text = finish(out, capsys)
        assert code == 1 and verdicts(text) == {"i": "PASS", "ii": "FAIL", "iv": "PASS"}, text
        assert "database findings are not the return's findings" in text
    finally:
        altered(
            db,
            "UPDATE findings SET finding_json = ?, claim = ?, finding_id = ? WHERE attempt_id = ?",
            row["finding_json"],
            row["claim"],
            row["finding_id"],
            attempt,
        )
    assert finish(out, capsys)[0] == 0


def test_finish_needs_the_settle_seats_dispatch_record(
    finished: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    out, tasks = finished
    path = tasks / f"{card(out, 'iv')['task_id']}.json"
    kept = path.read_bytes()
    try:
        path.unlink()  # a settle outcome recorded by hand, with no dispatch behind it
        code, text = finish(out, capsys)
        assert code == 1 and verdicts(text) == {"i": "PASS", "ii": "PASS", "iv": "FAIL"}, text
        assert "no settle dispatch task record" in text
        path.write_text(json.dumps({"agent": "claude", "model": "zzz-model"}), encoding="utf-8")  # no resolvable model
        assert verdicts(finish(out, capsys)[1])["iv"] == "FAIL"
    finally:
        path.write_bytes(kept)
    assert finish(out, capsys)[0] == 0


@pytest.mark.parametrize("what", ["decided_by", "receipt not in the ledger", "receipt of another attempt"])
def test_the_settle_decision_must_belong_to_the_cards_task_and_its_ledger(
    what: str, finished: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    out, _ = finished
    info = state_of(out, "iv")
    db = Path(info["db"])
    [row] = ic._rows(db, "SELECT * FROM settle_items WHERE item_id = ?", info["item_id"])
    changes = {
        "decided_by": ("decided_by", "some-other-task"),
        "receipt not in the ledger": ("receipts_json", '["r-not-in-the-ledger"]'),
        "receipt of another attempt": ("receipts_json", "[]"),
    }
    column, value = changes[what]
    ledger_path = Path(info["ledger"])
    prior_ledger = ledger_path.read_bytes(), Path(f"{ledger_path}.sha256").read_bytes()
    try:
        if what == "receipt of another attempt":  # a real receipt, but of a ledger record naming another attempt
            first = json.loads(prior_ledger[0].splitlines()[0])["receipt_id"]
            other = tmp_ledger_with_other_attempt(ledger_path, first)
            value = json.dumps([other])
        altered(db, f"UPDATE settle_items SET {column} = ? WHERE item_id = ?", value, info["item_id"])
        code, text = finish(out, capsys)
        assert code == 1 and verdicts(text) == {"i": "PASS", "ii": "PASS", "iv": "FAIL"}, text
    finally:
        altered(db, f"UPDATE settle_items SET {column} = ? WHERE item_id = ?", row[column], info["item_id"])
        ledger_path.write_bytes(prior_ledger[0])
        Path(f"{ledger_path}.sha256").write_bytes(prior_ledger[1])
    assert finish(out, capsys)[0] == 0


def tmp_ledger_with_other_attempt(ledger_path: Path, receipt_id: str) -> str:
    """Append a receipt to the seat's ledger that names another attempt; returns its id."""
    return ledger.append(
        ledger_path, review_id="r-other", attempt_id="a-other", manifest_sha256="0" * 64,
        tool="query_sum20", server_version="fixture", arguments={}, snapshots={}, status="ok", result="x",
        outcome_facts={"call_status": "ok", "hits": 1, "status": "hits_found", "unavailable": False},
    )  # fmt: skip


@pytest.mark.parametrize(
    ("outcome", "holds", "operator"),
    [
        ("source_conflict", ["settle_operator_pending", "terminal_operator"], True),
        ("supported_defect", ["settle_supported_defect"], False),
    ],
)
def test_what_the_module_verdict_keeps_after_a_settle_outcome(
    outcome: str, holds: list[str], operator: bool, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The item was the only hold; after the seat decided it, exactly the outcome's own consequence remains."""
    out, _, tasks = prepare(tmp_path)
    simulate_seats(out, tasks, settle_outcome=outcome)
    code, text = finish(out, capsys)
    assert code == 0 and verdicts(text)["iv"] == "PASS", text
    assert f"after: {'HOLD' if operator else 'REVISE'} {holds}" in text
    [item] = ic._rows(
        Path(card(out, "iv")["world"]) / "batch_state/review-findings/a1.sqlite", "SELECT * FROM settle_items"
    )
    assert item["outcome"] == outcome and item["needs_operator"] == int(operator)
    assert ("marked for the operator" in text) is operator
    assert (item["outcome"] in findings_db.OPERATOR_OUTCOMES) is operator and LEVEL == "a1"


# --- no Ukrainian typed --------------------------------------------------------------------------------


@pytest.mark.repo_wide
def test_no_cyrillic_in_the_check_or_its_tests() -> None:
    cyrillic = re.compile(f"[{chr(0x400)}-{chr(0x4FF)}]")  # the Cyrillic block, without typing it
    for path in (Path(ic.__file__), Path(__file__)):
        assert cyrillic.findall(path.read_text(encoding="utf-8")) == [], path.name
