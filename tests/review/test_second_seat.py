"""The second-seat sample (#8430 R2b-A, operator decision 5): selection, families, comparison, agreement rows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.review import findings_db as db
from scripts.review import second_seat as ss

PARAMS = {"second_seat_divisor": 10}


def test_selection_is_the_sha256_rule_with_the_divisor_from_the_parameters() -> None:
    for n in range(1, 60):
        digest = hashlib.sha256(f"a1/some-module/{n}".encode()).hexdigest()
        assert ss.selected("a1", "some-module", n, 10) is (int(digest, 16) % 10 == 0)
    assert all(ss.selected("a1", "m", n, 1) for n in range(1, 20))  # divisor 1: everything
    assert db.load_parameters()["second_seat_divisor"] == 10


def test_selection_is_deterministic_and_about_one_in_ten() -> None:
    picked = [n for n in range(1, 2001) if ss.selected("b1", "a-module", n, 10)]
    assert picked == [n for n in range(1, 2001) if ss.selected("b1", "a-module", n, 10)]
    assert 140 <= len(picked) <= 260  # 200 expected; a 1-in-10 sample, not a rule of thumb
    assert ss.selected("a1", "m", 3, 10) == ss.selected("a1", "m", 3, 10)
    assert {ss.selected("a1", "m", 3, 10), ss.selected("a2", "m", 3, 10), ss.selected("a1", "n", 3, 10)} <= {
        True,
        False,
    }


def test_the_third_family_rule() -> None:
    assert ss.is_third_family("openai", "anthropic", "google")
    assert not ss.is_third_family("openai", "anthropic", "openai")
    assert not ss.is_third_family("openai", "anthropic", "anthropic")
    assert not ss.is_third_family("openai", "openai", "google")


@pytest.mark.parametrize(
    ("identifier", "family"),
    [
        ("claude-sonnet-5", "anthropic"),
        ("gpt-6-astra", "openai"),
        ("gemini-3.8-flash-high", "google"),
        ("agy", "google"),
        ("codex-tools", "openai"),
    ],
)
def test_families_come_from_the_closeout_resolver(identifier: str, family: str) -> None:
    assert ss.concrete_family(identifier, what="t") == family


@pytest.mark.parametrize("identifier", ["", "unknown", "auto", "unattested-harness", "cursor", "zzz-model", None])
def test_an_unknown_or_ambiguous_identity_fails_closed(identifier) -> None:
    with pytest.raises(ss.IdentityError):
        ss.concrete_family(identifier, what="t")


def write_writer(directory: Path, n: int, **meta) -> None:
    (directory / f"lesson-{n}.writer.yaml").write_text(yaml.safe_dump(meta), encoding="utf-8")


def test_the_writers_family_is_read_from_the_writer_record_through_the_resolver(tmp_path: Path) -> None:
    write_writer(tmp_path, 1, writer="codex-tools", model="gpt-6-astra")
    assert ss.writer_family(tmp_path, 1) == "openai"
    write_writer(
        tmp_path, 2, writer="claude-tools", model="unknown"
    )  # the seat model did not resolve: the seat name does
    assert ss.writer_family(tmp_path, 2) == "anthropic"
    write_writer(tmp_path, 3, writer="mystery", model="unknown")
    with pytest.raises(ss.IdentityError):
        ss.writer_family(tmp_path, 3)
    with pytest.raises(ss.IdentityError, match="unreadable"):
        ss.writer_family(tmp_path, 4)


def finding(
    fid: str,
    dimension: str = "job",
    severity: str = "MAJOR",
    *,
    tab: str = "urok",
    activity=None,
    item=None,
    status: str = "active",
) -> dict:
    location = {
        "tab": tab,
        "quote": "q",
        **({"activity": activity} if activity else {}),
        **({"item": item} if item is not None else {}),
    }
    return {
        "id": fid,
        "status": status,
        "locations": [location],
        "dimension": dimension,
        "severity": severity,
        "claim": "c",
        "evidence": {"receipt": "r"},
    }


def test_two_seats_that_find_the_same_thing_in_the_same_place_agree() -> None:
    result = ss.compare_findings([finding("F-01")], [finding("F-07", severity="BLOCKER")])
    assert result == {"agreed": True, "disagreed": []}
    assert ss.compare_findings([], []) == {"agreed": True, "disagreed": []}


def test_a_finding_the_other_seat_lacks_is_a_disagreement_on_its_side() -> None:
    result = ss.compare_findings([finding("F-01"), finding("F-02", "fact")], [finding("F-09")])
    assert not result["agreed"]
    [entry] = result["disagreed"]
    assert (
        entry["side"] == "a" and entry["finding_id"] == "F-02" and entry["reason"] == "no_match" and entry["blocking"]
    )
    other = ss.compare_findings([], [finding("F-01", severity="MINOR")])["disagreed"][0]
    assert other["side"] == "b" and other["blocking"] is False


def test_the_same_dimension_in_another_place_is_not_a_match() -> None:
    result = ss.compare_findings([finding("F-01", tab="urok")], [finding("F-01", tab="slovnyk")])
    assert {(entry["side"], entry["reason"]) for entry in result["disagreed"]} == {("a", "no_match"), ("b", "no_match")}
    inside = ss.compare_findings(
        [finding("F-01", tab="vpravy", activity="a1", item=2)], [finding("F-01", tab="vpravy", activity="a1", item=3)]
    )
    assert not inside["agreed"]
    scoped = ss.compare_findings(
        [finding("F-01", tab="vpravy", activity="a1", item=2)],
        [{**finding("F-01"), "locations": [], "scope": {"tab": "vpravy", "activity": "a1"}}],
    )
    assert scoped["agreed"]  # an activity-level absence finding covers the activity's items


def test_a_matched_pair_that_crosses_the_blocking_line_is_a_disagreement_against_the_blocking_side() -> None:
    result = ss.compare_findings([finding("F-01", severity="MINOR")], [finding("F-01", severity="MAJOR")])
    [entry] = result["disagreed"]
    assert entry["side"] == "b" and entry["reason"] == "severity_boundary" and entry["blocking"]
    same_side = ss.compare_findings([finding("F-01", severity="MAJOR")], [finding("F-01", severity="BLOCKER")])
    assert same_side["agreed"]


def test_resolved_findings_are_history_and_do_not_disagree() -> None:
    assert ss.compare_findings([finding("F-01", status="resolved")], [])["agreed"]
    assert not ss.compare_findings([finding("F-01", status="persisting")], [])["agreed"]


def test_each_finding_is_matched_at_most_once() -> None:
    result = ss.compare_findings([finding("F-01"), finding("F-02")], [finding("F-01")])
    assert [(e["side"], e["finding_id"]) for e in result["disagreed"]] == [("a", "F-02")]


# --- against the database ---------------------------------------------------------------------------


def attempt(
    role: str,
    attempt_id: str,
    family: str,
    *,
    manifest: str = "ab" * 32,
    verdict: str = "REVISE",
    seed: str | None = None,
) -> dict:
    return {
        "review_id": f"R-{attempt_id}",
        "attempt_id": attempt_id,
        "kind": "lesson",
        "level": "a1",
        "slug": "m",
        "lesson_n": 2,
        "manifest_sha256": manifest,
        "reviewer_model": "m",
        "reviewer_family": family,
        "harness": "h",
        "verdict": verdict,
        "validated_at": "t",
        "task_id": "t",
        "role": role,
        "seed_id": seed,
    }


@pytest.fixture
def conn(tmp_path: Path):
    connection = db.connect(tmp_path / "a1.sqlite")
    yield connection
    connection.close()


def store(conn, row: dict, findings: list[dict]) -> None:
    with db.transaction(conn):
        db.insert_attempt(conn, row)
        for item in findings:
            db.insert_finding(conn, row["review_id"], row["attempt_id"], item, layer=None, seed_id=row["seed_id"])


def test_eligibility_needs_the_sample_a_first_review_on_the_manifest_and_a_third_family(conn) -> None:
    all_lessons = {"second_seat_divisor": 1}
    kwargs = dict(
        level="a1",
        slug="m",
        lesson_n=2,
        manifest_sha256="ab" * 32,
        first_attempt=None,
        writer="openai",
        second_family="google",
    )
    with pytest.raises(ss.SecondSeatError, match="no first-seat review"):
        ss.check_eligible(conn, params=all_lessons, **kwargs)
    store(conn, attempt("first", "A1", "anthropic"), [])
    assert ss.check_eligible(conn, params=all_lessons, **kwargs)["attempt_id"] == "A1"
    with pytest.raises(ss.SecondSeatError, match="third family"):
        ss.check_eligible(conn, params=all_lessons, **{**kwargs, "second_family": "openai"})
    with pytest.raises(ss.SecondSeatError, match="third family"):
        ss.check_eligible(conn, params=all_lessons, **{**kwargs, "second_family": "anthropic"})
    with pytest.raises(ss.SecondSeatError, match="no first-seat review"):  # the first review is of another manifest
        ss.check_eligible(conn, params=all_lessons, **{**kwargs, "manifest_sha256": "cd" * 32})
    never = {"second_seat_divisor": 10**12}
    lesson = next(n for n in range(1, 50) if not ss.selected("a1", "m", n, 10**12))
    with pytest.raises(ss.SecondSeatError, match="not in the second-seat sample"):
        ss.check_eligible(conn, params=never, **{**kwargs, "lesson_n": lesson})


def test_a_seeded_first_attempt_is_not_a_first_review(conn) -> None:
    store(conn, attempt("first", "A1", "anthropic", seed="seed-1"), [])
    with pytest.raises(ss.SecondSeatError, match="no first-seat review"):
        ss.check_eligible(
            conn,
            params={"second_seat_divisor": 1},
            level="a1",
            slug="m",
            lesson_n=2,
            manifest_sha256="ab" * 32,
            first_attempt=None,
            writer="openai",
            second_family="google",
        )


def test_the_agreement_row_and_the_settle_items_of_a_disagreement(conn) -> None:
    store(conn, attempt("first", "A1", "anthropic"), [finding("F-01"), finding("F-02", "fact", "MINOR")])
    store(
        conn,
        attempt("second", "A2", "google"),
        [finding("F-01", severity="BLOCKER"), finding("F-05", "english", "MAJOR", tab="slovnyk")],
    )
    first, second = (db.get_attempt(conn, f"R-{a}", a) for a in ("A1", "A2"))
    with db.transaction(conn):
        result = ss.record_agreement(conn, first, second, opened_at="t2")
    assert result["agreed"] is False
    [row] = conn.execute("SELECT * FROM agreement").fetchall()
    assert (row["level"], row["slug"], row["lesson_n"], row["attempt_a"], row["attempt_b"], row["agreed"]) == (
        "a1",
        "m",
        2,
        "A1",
        "A2",
        0,
    )
    entries = json.loads(row["disagreed_json"])
    assert {(e["side"], e["finding_id"], e["reason"]) for e in entries} == {
        ("a", "F-02", "no_match"),
        ("b", "F-05", "no_match"),
    }
    # only the BLOCKER/MAJOR disagreement (the second seat's F-05) is a settle item; the first seat's MINOR F-02 is not
    [item] = conn.execute("SELECT * FROM settle_items").fetchall()
    assert (
        item["finding_ref"] == "R-A2/A2/F-05" and item["kind"] == "second_seat_disagreement" and item["outcome"] is None
    )
    assert result["settle_items"] == [item["item_id"]]


def test_an_agreement_row_says_agreed_and_opens_nothing(conn) -> None:
    store(conn, attempt("first", "A1", "anthropic"), [finding("F-01")])
    store(conn, attempt("second", "A2", "google"), [finding("F-03")])
    first, second = (db.get_attempt(conn, f"R-{a}", a) for a in ("A1", "A2"))
    with db.transaction(conn):
        ss.record_agreement(conn, first, second, opened_at="t2")
    [row] = conn.execute("SELECT * FROM agreement").fetchall()
    assert row["agreed"] == 1 and json.loads(row["disagreed_json"]) == []
    assert conn.execute("SELECT COUNT(*) FROM settle_items").fetchone()[0] == 0


def test_the_cli_reports_selection_without_writing(capsys: pytest.CaptureFixture[str]) -> None:
    assert ss.main(["select", "a1", "m", "3"]) == 0
    assert json.loads(capsys.readouterr().out) == {"divisor": 10, "selected": ss.selected("a1", "m", 3, 10)}
    assert ss.main(["plan", "a1", "m", "--lessons", "40"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["selected"] == [n for n in range(1, 41) if ss.selected("a1", "m", n, 10)]
    text = ss.build_parser().format_help()
    assert "Examples:" in text and "Outputs:" in text
