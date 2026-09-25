"""The R2b integration check harness (#8430): its own behaviour, with negative controls.

``run-crafted`` must pass on the code as it is and must FAIL when the product path it proves is broken (each
control below breaks one seam and expects exactly that case to fail). ``prepare-real`` + ``finish-real`` are
exercised with crafted returns standing in for the real seats: the ledgers and dispatch records are redirected
to a temporary tree, so nothing of ``batch_state`` is touched.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

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


def only(case_key: str, tmp_path: Path) -> ic.Case:
    key, title, function = next(item for item in ic.CRAFTED_CASES if item[0] == case_key)
    return ic.run_case(key, title, function, tmp_path)


@pytest.mark.parametrize(
    ("case_key", "target", "attribute", "replacement"),
    [
        ("iii", fixloop, "span_layer", lambda span: fixloop.REGENERATE),  # blame every span on the writer
        ("v", second_seat, "selected", lambda *a, **kw: False),  # the sampling rule selects nothing
        ("vi", fixloop, "dependents", lambda closure, n: []),  # regeneration stales nobody
        ("vii", fixloop, "terminal_transitions", lambda *a, **kw: []),  # no budget is ever terminal
        ("viii", pm, "plan_review_status", lambda *a, **kw: {"state": "unreviewed", "stale": {}}),
    ],
)
def test_breaking_the_product_path_fails_exactly_its_case(
    case_key: str, target: Any, attribute: str, replacement: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert only(case_key, tmp_path / "control").passed is True  # the control: it passes before the break
    monkeypatch.setattr(target, attribute, replacement)
    broken = only(case_key, tmp_path / "broken")
    assert not broken.passed, broken.line()
    assert broken.line().startswith(f"FAIL ({case_key})")


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


@pytest.fixture(scope="module")
def prepared(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, Path]:
    """prepare-real with the ledgers and dispatch records redirected to a temporary tree."""
    root = tmp_path_factory.mktemp("real")
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


def card(out: Path, key: str) -> dict[str, Any]:
    return json.loads((out / "cards" / f"{key}.json").read_text(encoding="utf-8"))


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
    text = (out / STATE).read_text(encoding="utf-8")
    assert json.loads(text)["cases"]["iv"]["open_verdict"] != "APPROVE"


def test_the_settle_item_is_open_and_holds_the_module_while_the_seat_has_not_answered(
    prepared: tuple[Path, Path, Path],
) -> None:
    out, _, _ = prepared
    info = json.loads((out / STATE).read_text(encoding="utf-8"))["cases"]["iv"]
    held = yaml.safe_load(Path(info["while_open_verdict"]).read_bytes())
    assert held["verdict"] != "APPROVE" and [item["item_id"] for item in held["settle_items"]["open"]] == [
        info["item_id"]
    ]
    rows = ic._rows(Path(info["db"]), "SELECT kind, outcome, lesson_n FROM settle_items")
    assert [tuple(row) for row in rows] == [("unsupported_by_source", None, 1)]


def test_finish_fails_every_real_case_before_any_return_is_recorded(
    prepared: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    out, _, _ = prepared
    assert ic.main(["finish-real", "--out", str(out)]) == 1
    lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith(("PASS", "FAIL"))]
    assert [line.split()[:2] for line in lines] == [["FAIL", "(i)"], ["FAIL", "(ii)"], ["FAIL", "(iv)"]]


def simulate_seats(out: Path, receipts: Path, tasks: Path, *, settle_outcome: str = "refuted") -> None:
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
        (tasks / f"{plan['task_id']}.json").write_text(
            json.dumps({"agent": "claude", "model": "claude-sonnet-5"}), encoding="utf-8"
        )
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
        (tasks / f"{lesson['task_id']}.json").write_text(
            json.dumps({"agent": "claude", "model": "claude-sonnet-5"}), encoding="utf-8"
        )
        assert record.main(lesson["record"][3:]) == 0
        # (iv) the settle seat: two hit receipts of two sources for a source_conflict, one hit for a refutation
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
        assert settle.main(item["record"][3:]) == 0
    finally:
        mp.undo()


def test_finish_passes_when_the_seats_returns_were_recorded(
    prepared: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    out, receipts, tasks = prepared
    simulate_seats(out, receipts, tasks)
    capsys.readouterr()
    assert ic.main(["finish-real", "--out", str(out)]) == 0
    text = capsys.readouterr().out
    assert [line.split()[:2] for line in text.splitlines() if line.startswith(("PASS", "FAIL"))] == [
        ["PASS", "(i)"],
        ["PASS", "(ii)"],
        ["PASS", "(iv)"],
    ]
    plan = card(out, "i")
    assert "reviewed_promoted" in text and "plan-review.yaml verdict=APPROVE" in text
    lesson = card(out, "ii")
    state = Path(lesson["world"]) / "curriculum/l2-uk-en/evidence/a1/_state" / SLUG
    written = yaml.safe_load((state / "lesson-2.verdict.yaml").read_bytes())
    assert written["manifest_sha256"] == lesson["manifest_sha256"] and plan["attempt_id"] == "a1"
    assert "outcome=refuted" in text and "findings db=1 return=1" in text


def test_finish_rejects_a_verdict_file_naming_another_manifest(
    prepared: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    out, _, _ = prepared
    lesson = card(out, "ii")
    state = Path(lesson["world"]) / "curriculum/l2-uk-en/evidence/a1/_state" / SLUG
    path = state / "lesson-2.verdict.yaml"
    original = path.read_bytes()
    try:
        document = yaml.safe_load(original)
        document["manifest_sha256"] = "0" * 64
        path.write_text(yaml.safe_dump(document), encoding="utf-8")
        assert ic.main(["finish-real", "--out", str(out)]) == 1
        assert "not the manifest's sha256" in capsys.readouterr().out
    finally:
        path.write_bytes(original)


def test_a_source_conflict_is_marked_for_the_operator(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    receipts, tasks = tmp_path / "receipts", tmp_path / "tasks"
    receipts.mkdir()
    tasks.mkdir()
    patch = pytest.MonkeyPatch()
    patch.setattr(ic, "RECEIPTS_ROOT", receipts)
    patch.setattr(ic, "TASKS_DIR", tasks)
    try:
        assert ic.main(["prepare-real", "--out", str(tmp_path / "out")]) == 0
        simulate_seats(tmp_path / "out", receipts, tasks, settle_outcome="source_conflict")
        capsys.readouterr()
        assert ic.main(["finish-real", "--out", str(tmp_path / "out")]) == 0
        assert "marked for the operator" in capsys.readouterr().out
        [item] = ic._rows(
            Path(card(tmp_path / "out", "iv")["world"]) / "batch_state/review-findings/a1.sqlite",
            "SELECT * FROM settle_items",
        )
        assert item["outcome"] == "source_conflict" and item["needs_operator"] == 1
        assert item["outcome"] in findings_db.OPERATOR_OUTCOMES and LEVEL == "a1"
    finally:
        patch.undo()


# --- no Ukrainian typed --------------------------------------------------------------------------------


@pytest.mark.repo_wide
def test_no_cyrillic_in_the_check_or_its_tests() -> None:
    cyrillic = re.compile(f"[{chr(0x400)}-{chr(0x4FF)}]")  # the Cyrillic block, without typing it
    for path in (Path(ic.__file__), Path(__file__)):
        assert cyrillic.findall(path.read_text(encoding="utf-8")) == [], path.name
