"""The scorer, against hand-computed fixtures (#8430 R3-A).

Every expected number below was worked out by hand from the formulas in the scorer's docstring, not read back from
the code; the interval end points are the standard tabulated values (Wilson score, Garwood exact Poisson) to four
places. The fixture is one seat, ``codex`` (family openai), on a first set of six seeds and four clean lessons:

===============  ==============================================  ========================================
unit             first attempt by the seat                       counts as
===============  ==============================================  ========================================
seed-job-1       accepted, planted found, blocking               detected, blocking
seed-job-2       accepted, planted found, MINOR (not blocking)   detected, not blocking
seed-job-3       accepted, planted not found                     not detected
seed-job-4       FAILED; a retry is accepted and finds it        not detected (the retry is only reported)
seed-act-1       REJECTED by the validator                       not detected
seed-act-2       accepted, planted found, blocking               detected, blocking
clean-1          accepted; F-01 BLOCKER false, F-02 false        2 false findings, falsely blocked
clean-2          accepted; F-01 BLOCKER genuine_additional       0 false findings, not falsely blocked
clean-3          accepted, no findings                           0, not blocked
clean-4          FAILED                                          0, not blocked (stays in the denominator)
===============  ==============================================  ========================================
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from scripts.review import findings_db
from scripts.review.seeds import manifest as sm
from scripts.review.seeds import score
from tests.review.seeds.fixtures import SEATS, Env, clean_lesson, finding, linguistic_seed, mechanical_seed

TODAY = date(2026, 9, 25)
NEAR = pytest.approx


def near(value: float, expected: float) -> bool:
    return abs(value - expected) < 5e-4


@pytest.fixture
def env(tmp_path: Path) -> Env:
    return Env(tmp_path)


def run(env: Env, seat: str = "codex", set_name: str = "first", **kwargs):
    return score.score_seat(seat, set_name, repo_root=env.root, db_path_for=env.path_for, today=TODAY, **kwargs)


def build_first_set(env: Env, *, source: str = "real_built") -> dict[str, tuple[str, str]]:
    """The table above; returns the first-attempt ids by unit."""
    ids: dict[str, tuple[str, str]] = {}

    def seed(name: str, dimension: str) -> tuple:
        unit = mechanical_seed(f"seed-{name}", dimension, source=source)
        env.add(unit, "first")
        return unit, name

    def detected(name: str, dimension: str, severity: str, found: bool = True):
        unit, _ = seed(name, dimension)
        ids[unit.seed_id] = env.attempt(unit, "codex", "REVISE", [finding("F-01", severity), finding("F-02", "MINOR")])
        env.seed_result(
            unit.seed_id,
            ids[unit.seed_id],
            found,
            found and severity in ("BLOCKER", "MAJOR"),
            {"F-01": "planted" if found else "false", "F-02": "false"},
        )

    detected("job-1", "job", "BLOCKER")
    unit, _ = seed("job-2", "job")
    ids["seed-job-2"] = env.attempt(unit, "codex", "REVISE", [finding("F-01", "MAJOR"), finding("F-02", "MINOR")])
    env.seed_result("seed-job-2", ids["seed-job-2"], True, False, {"F-01": "false", "F-02": "planted"})
    detected("job-3", "job", "BLOCKER", found=False)
    unit, _ = seed("job-4", "job")
    ids["seed-job-4"] = env.attempt(unit, "codex", "FAILED")
    retry = env.attempt(unit, "codex", "REVISE", [finding("F-01", "BLOCKER")])
    env.seed_result("seed-job-4", retry, True, True, {"F-01": "planted"})  # the retry found it; it does not count
    unit, _ = seed("act-1", "activity")
    ids["seed-act-1"] = env.attempt(unit, "codex", "REJECTED")
    detected("act-2", "activity", "BLOCKER")

    clean_units = {}
    for name in ("1", "2", "3", "4"):
        clean_units[name] = clean_lesson(f"clean-{name}", source=source)
        env.add(clean_units[name], "first")
    ids["clean-1"] = env.attempt(
        clean_units["1"], "codex", "REVISE", [finding("F-01", "BLOCKER"), finding("F-02", "MINOR")]
    )
    env.clean_result("clean-1", ids["clean-1"], {"F-01": "false", "F-02": "false"}, True)
    ids["clean-2"] = env.attempt(clean_units["2"], "codex", "REVISE", [finding("F-01", "BLOCKER")])
    env.clean_result("clean-2", ids["clean-2"], {"F-01": "genuine_additional"}, False)
    ids["clean-3"] = env.attempt(clean_units["3"], "codex", "APPROVE")
    env.clean_result("clean-3", ids["clean-3"], {}, False)
    ids["clean-4"] = env.attempt(clean_units["4"], "codex", "FAILED")
    return ids


@pytest.fixture
def fixture_score(env: Env):
    """Scores the table. Two more units are frozen as the confirmation set, so the freeze assigns the table to ``first``."""
    for name in ("conf-1", "conf-2"):
        env.add(mechanical_seed(f"seed-{name}"))
    ids = build_first_set(env)
    sm.freeze_confirmation(["seed-conf-1", "seed-conf-2"], env.root)
    return env, ids, run(env)


# --- the interval arithmetic ---------------------------------------------------------------------------------------------


# --- the hand-computed fixture ------------------------------------------------------------------------------------------


def test_recall_per_dimension_counts_failed_and_rejected_first_attempts_as_not_detected(fixture_score) -> None:
    _, _, result = fixture_score
    report = result.report
    job, activity = report["recall_by_dimension"]["job"], report["recall_by_dimension"]["activity"]
    # job: seed-job-1 and -2 found; -3 missed; -4's FIRST attempt failed (its retry does not count) -> 2 of 4
    assert (job["k"], job["n"], job["method"]) == (2, 4, "wilson") and job["point"] == 0.5
    assert near(job["low"], 0.1500) and near(job["high"], 0.8500)
    # activity: seed-act-1 was rejected by the validator (not detected), seed-act-2 found -> 1 of 2, Wilson(1, 2)
    assert (activity["k"], activity["n"]) == (1, 2)
    assert near(activity["low"], 0.0945) and near(activity["high"], 0.9055)
    pooled = report["recall_pooled"]
    assert (pooled["k"], pooled["n"]) == (3, 6) and near(pooled["low"], 0.1876) and near(pooled["high"], 0.8124)


def test_the_report_is_computed_only_from_the_first_attempt_by_the_seat(env: Env) -> None:
    unit = mechanical_seed("seed-x1")
    env.add(unit, "first")
    other = env.attempt(unit, "agy", "REVISE", [finding("F-01")])  # another seat's attempt is not this seat's
    env.seed_result("seed-x1", other, True, True, {"F-01": "planted"})
    mine = env.attempt(unit, "codex", "REVISE", [finding("F-01")])
    env.seed_result("seed-x1", mine, False, False, {"F-01": "false"})
    env.add(mechanical_seed("seed-x2"))
    sm.freeze_confirmation(["seed-x2"], env.root)
    report = run(env).report
    assert report["recall_by_dimension"]["job"]["k"] == 0
    assert report["recall_by_dimension"]["job"]["n"] == 1


# --- exploratory vs threshold-eligible ------------------------------------------------------------------------------


def _big_set(
    env: Env, *, per_dimension: int, cleans: int, source: str = "real_built", extra_fixture: bool = False
) -> None:
    _, required = sm.lesson_dimensions()
    for dimension in required:
        for index in range(per_dimension):
            unit = (linguistic_seed if dimension == "language" else mechanical_seed)(
                f"seed-{dimension}-{index}", dimension, source=source
            )
            env.add(unit, "first")
            ids = env.attempt(unit, "codex", "REVISE", [finding("F-01", dimension=dimension)])
            env.seed_result(
                unit.seed_id, ids, index % 2 == 0, index % 2 == 0, {"F-01": "planted" if index % 2 == 0 else "false"}
            )
    for index in range(cleans):
        unit = clean_lesson(f"clean-{index}", source=source)
        env.add(unit, "first")
        env.clean_result(unit.clean_id, env.attempt(unit, "codex", "APPROVE"), {}, False)
    if extra_fixture:
        unit = mechanical_seed("seed-canary", "job", source="canary")
        env.add(unit, "first")
        env.seed_result("seed-canary", env.attempt(unit, "codex", "APPROVE"), False, False, {})
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)


def test_a_set_that_reaches_the_size_on_real_built_lessons_is_threshold_eligible(env: Env) -> None:
    _big_set(env, per_dimension=22, cleans=30)
    result = run(env)
    assert result.report["threshold_eligible"] is True and result.report["exploratory_reasons"] == []
    assert result.report["eligibility"]["real_built_clean_lessons"] == 30
    assert set(result.report["eligibility"]["real_built_seeds_by_dimension"].values()) == {22}
    text = score.render_report(result)
    assert text.splitlines()[0].startswith("# Reviewer measurement") and "EXPLORATORY" not in text
    job = result.report["recall_by_dimension"]["job"]
    assert (job["k"], job["n"]) == (11, 22)


@pytest.mark.parametrize(("per_dimension", "cleans"), [(21, 30), (22, 29)])
def test_one_short_of_the_size_is_exploratory(env: Env, per_dimension: int, cleans: int) -> None:
    _big_set(env, per_dimension=per_dimension, cleans=cleans)
    result = run(env)  # the real parameters: 22 per dimension, 30 clean
    assert result.report["threshold_eligible"] is False
    assert len(result.report["exploratory_reasons"]) == (8 if per_dimension == 21 else 1)
    assert score.render_report(result).splitlines()[0].startswith("# EXPLORATORY")


def test_the_sizes_are_parameters_not_constants(env: Env) -> None:
    _big_set(env, per_dimension=2, cleans=3)
    assert run(env).report["threshold_eligible"] is False
    small = {**findings_db.load_parameters(), "min_planted_per_dimension": 2, "min_clean_lessons": 3}
    assert run(env, params=small).report["threshold_eligible"] is True
    assert run(env, params={**small, "min_clean_lessons": 4}).report["threshold_eligible"] is False


def test_a_canary_or_fixture_unit_keeps_the_report_exploratory_even_at_full_size(env: Env) -> None:
    _big_set(env, per_dimension=22, cleans=30, extra_fixture=True)
    result = run(env)
    assert result.report["threshold_eligible"] is False
    assert (
        "1 units are not real built lessons (canary or fixture): ['seed-canary']"
        in result.report["exploratory_reasons"][0]
    )


# --- a partial run --------------------------------------------------------------------------------------------------------


def test_a_unit_the_seat_never_attempted_refuses_the_run_unless_a_partial_report_is_allowed(env: Env) -> None:
    done = mechanical_seed("seed-done")
    env.add(done, "first")
    env.seed_result("seed-done", env.attempt(done, "codex", "APPROVE"), False, False, {})
    env.add(mechanical_seed("seed-todo"), "first")
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    with pytest.raises(score.ScoreError) as caught:
        run(env)
    assert caught.value.code == score.UNIT_NOT_ATTEMPTED and "seed-todo" in str(caught.value)
    partial = run(env, allow_partial=True)
    assert (
        partial.report["excluded"]["not_attempted"] == ["seed-todo"] and partial.report["threshold_eligible"] is False
    )
    assert "the run is partial" in " ".join(partial.report["exploratory_reasons"])
    assert "Not attempted: seed-todo" in score.render_report(partial)


def test_an_accepted_attempt_that_is_not_adjudicated_yet_is_pending_never_dropped_silently(env: Env) -> None:
    unit = mechanical_seed("seed-a1")
    env.add(unit, "first")
    env.attempt(unit, "codex", "REVISE", [finding("F-01")])  # no seed_results row
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    with pytest.raises(score.ScoreError) as caught:
        run(env)
    assert caught.value.code == score.ADJUDICATION_PENDING
    with pytest.raises(score.ScoreError) as caught:
        run(env, allow_partial=True)  # nothing left to score
    assert caught.value.code == score.NO_ATTEMPTS


def test_the_rolling_set_may_be_partial_and_needs_no_lock(env: Env) -> None:
    unit = mechanical_seed("seed-r1")
    env.add(unit, "rolling")
    env.seed_result("seed-r1", env.attempt(unit, "codex", "REVISE", [finding("F-01")]), True, True, {"F-01": "planted"})
    env.add(mechanical_seed("seed-r2"), "rolling")
    result = run(env, set_name="rolling")
    assert result.report["set"] == "rolling" and result.report["confirmation_lock_sha256"] is None
    assert result.report["excluded"]["not_attempted"] == ["seed-r2"]


# --- a seat is scored only on what it may review ----------------------------------------------------------------------


def test_a_seed_planted_by_the_seats_own_family_is_not_in_its_pool_and_is_not_counted_as_missed(env: Env) -> None:
    fine = linguistic_seed("seed-l1", planter_model="gemini-3.1-pro-preview", planter_family="google")
    own = linguistic_seed(
        "seed-l2", planter_model="gpt-6.1-sol", planter_family="openai", writer_family="anthropic"
    )  # planted by openai
    for unit in (fine, own):
        env.add(unit, "first")
    env.seed_result(
        "seed-l1",
        env.attempt(fine, "codex", "REVISE", [finding("F-01", dimension="language")]),
        True,
        True,
        {"F-01": "planted"},
    )
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    result = run(env)
    assert result.report["excluded"]["not_applicable"] == {"seed-l2": [sm.PLANTER_IS_REVIEWER]}
    assert result.report["recall_by_dimension"]["language"]["n"] == 1
    assert "Not applicable to this seat" in score.render_report(result)


def test_an_attempt_by_a_family_that_may_not_review_the_unit_refuses_the_run(env: Env) -> None:
    unit = mechanical_seed("seed-a1", writer_family="openai")
    env.add(unit, "first")
    env.attempt(
        unit, "codex", "APPROVE"
    )  # openai reviewing an openai-written lesson (only possible if recording was bypassed)
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    with pytest.raises(score.ScoreError) as caught:
        run(env)
    assert caught.value.code == sm.REVIEWER_IS_WRITER


def test_a_seat_with_attempts_under_two_models_must_name_one(env: Env) -> None:
    unit = mechanical_seed("seed-a1")
    env.add(unit, "first")
    ids = env.attempt(unit, "codex", "REVISE", [finding("F-01")])
    env.seed_result("seed-a1", ids, True, True, {"F-01": "planted"})
    conn = env.connect()
    conn.execute("UPDATE attempts SET reviewer_model = 'gpt-6-luna' WHERE attempt_id = ?", (ids[1],))
    other = mechanical_seed("seed-a2")
    conn.close()
    env.add(other, "first")
    ids2 = env.attempt(other, "codex", "REVISE", [finding("F-01")])
    env.seed_result("seed-a2", ids2, True, True, {"F-01": "planted"})
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    with pytest.raises(score.ScoreError) as caught:
        run(env)
    assert caught.value.code == score.MIXED_SEAT
    assert run(env, model="gpt-6.1-sol", allow_partial=True).report["models"] == ["gpt-6.1-sol"]


def test_a_seat_with_no_attempts_has_nothing_to_score(env: Env) -> None:
    env.add(mechanical_seed("seed-a1"), "first")
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    with pytest.raises(score.ScoreError) as caught:
        run(env, seat="agy")
    assert caught.value.code == score.NO_ATTEMPTS
    assert not env.path_for("a1").exists()


def test_a_seed_whose_recorded_identity_drifted_from_its_manifest_is_not_scored(env: Env) -> None:
    unit = mechanical_seed("seed-a1")
    env.add(unit, "first")
    ids = env.attempt(unit, "codex", "REVISE", [finding("F-01")])
    env.seed_result("seed-a1", ids, True, True, {"F-01": "planted"})
    conn = env.connect()
    with findings_db.transaction(conn):
        findings_db.record_seed_identity(conn, {**unit.identity_row(), "writer_family": "google"})
    conn.close()
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    with pytest.raises(score.ScoreError) as caught:
        run(env)
    assert caught.value.code == score.IDENTITY_MISMATCH


# --- the confirmation lock is verified before scoring -------------------------------------------------------------------


def confirmation_world(env: Env):
    units = []
    for name in ("c1", "c2"):
        unit = mechanical_seed(f"seed-{name}")
        env.add(unit)
        units.append(unit)
    env.add(mechanical_seed("seed-f1"), "first")
    sm.freeze_confirmation(["seed-c1", "seed-c2"], env.root)
    for unit in units:
        env.seed_result(
            unit.seed_id, env.attempt(unit, "codex", "REVISE", [finding("F-01")]), True, True, {"F-01": "planted"}
        )
    return units


def test_a_confirmation_run_scores_exactly_the_frozen_list_and_prints_the_lock_hash(env: Env) -> None:
    confirmation_world(env)
    result = run(env, set_name="confirmation")
    lock = sm.verify_confirmation_lock(env.root)
    assert result.report["set"] == "confirmation" and result.report["units"] == {"seeds": 2, "clean": 0}
    assert result.report["confirmation_lock_sha256"] == lock.sha256
    assert lock.sha256 in score.render_report(result)
    assert "Admission threshold: not set" in score.render_report(result)


def test_the_hash_is_verified_before_a_confirmation_run_reads_the_database(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    confirmation_world(env)
    path = env.root / "batch_state" / "review-measurement" / "confirmation.lock"
    path.write_text(
        path.read_text().replace("seed-c2", "seed-f1"), encoding="utf-8"
    )  # a unit swapped out of the frozen list
    opened: list[Path] = []
    real = findings_db.connect
    monkeypatch.setattr(findings_db, "connect", lambda p: opened.append(p) or real(p))
    for set_name in ("confirmation", "first"):
        with pytest.raises(sm.MeasurementError) as caught:
            run(env, set_name=set_name)
        assert caught.value.code == sm.CONFIRMATION_LOCK_INVALID
    assert opened == [], "nothing was read from the findings database"


def test_a_first_or_confirmation_run_needs_the_lock_but_a_rolling_one_does_not(env: Env) -> None:
    env.add(mechanical_seed("seed-a1"), "first")
    for set_name in ("first", "confirmation"):
        with pytest.raises(sm.MeasurementError) as caught:
            run(env, set_name=set_name)
        assert caught.value.code == sm.CONFIRMATION_LOCK_MISSING


def test_a_first_report_never_contains_a_confirmation_unit(env: Env) -> None:
    units = confirmation_world(env)
    assignments = sm.load_assignments(env.root)
    assert {assignments[unit.seed_id] for unit in units} == {"confirmation"}
    first = env.attempt(mechanical_seed("seed-f1"), "codex", "REVISE", [finding("F-01")])
    env.seed_result("seed-f1", first, True, True, {"F-01": "planted"})
    assert set(run(env, set_name="first").observations) == {"seed-f1"}
    # a hand-edited assignment file cannot smuggle a locked unit into the first set: the lock check refuses first
    sets = env.root / "batch_state" / "review-measurement" / "sets.yaml"
    sets.write_text(sets.read_text().replace("seed-c1: confirmation", "seed-c1: first"), encoding="utf-8")
    with pytest.raises(sm.MeasurementError) as caught:
        run(env, set_name="first")
    assert caught.value.code == sm.CONFIRMATION_LOCK_INVALID


# --- the paired comparison ------------------------------------------------------------------------------------------------


def test_two_seats_are_paired_on_the_seeds_both_may_review(env: Env) -> None:
    units = [mechanical_seed(f"seed-p{i}") for i in range(3)]
    for unit in units:
        env.add(unit, "first")
    for seat, found in (("codex", (True, True, False)), ("agy", (False, True, True))):
        for unit, hit in zip(units, found, strict=True):
            ids = env.attempt(unit, seat, "REVISE", [finding("F-01")])
            env.seed_result(unit.seed_id, ids, hit, hit, {"F-01": "planted" if hit else "false"})
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    paired = score.paired_comparison(run(env, "codex"), run(env, "agy"))
    assert (paired["paired_seeds"], paired["both_detected"], paired["only_a_detected"], paired["only_b_detected"]) == (
        3,
        1,
        1,
        1,
    )
    assert paired["p_value"] == NEAR(1.0)


# --- agreement per seat pair -------------------------------------------------------------------------------------------


def _first_world(env: Env) -> None:
    for name in ("conf-1", "conf-2"):
        env.add(mechanical_seed(f"seed-{name}"))
    build_first_set(env)
    sm.freeze_confirmation(["seed-conf-1", "seed-conf-2"], env.root)


def _lesson_pair(env: Env, n: int, first: str, second: str, disagreed: list[dict] | None = None) -> None:
    """Two seats' accepted attempts on real lesson ``n`` of a1/agreement-course and their ``agreement`` row."""
    conn = env.connect()
    try:
        with findings_db.transaction(conn):
            for role, seat, attempt_id in (("first", first, f"g{n}-first"), ("second", second, f"g{n}-second")):
                model, family = SEATS[seat]
                findings_db.insert_attempt(
                    conn,
                    {
                        "review_id": f"rev-g{n}-{role}",
                        "attempt_id": attempt_id,
                        "kind": "lesson",
                        "level": "a1",
                        "slug": "agreement-course",
                        "lesson_n": n,
                        "manifest_sha256": f"{n:064x}",
                        "reviewer_model": model,
                        "reviewer_family": family,
                        "harness": seat,
                        "verdict": "REVISE",
                        "validated_at": "2026-09-25T00:00:00+00:00",
                        "task_id": f"task-g{n}-{role}",
                        "role": role,
                    },
                )
            findings_db.insert_agreement(
                conn,
                level="a1",
                slug="agreement-course",
                lesson_n=n,
                attempt_a=f"g{n}-first",
                attempt_b=f"g{n}-second",
                agreed=not disagreed,
                disagreed=disagreed or [],
            )
    finally:
        conn.close()


def _shadow_attempt(env: Env, review_id: str, attempt_id: str, seat: str, lesson_n: int) -> None:
    """An attempt that reuses ``attempt_id`` under another review id (the table keeps (review_id, attempt_id) unique)."""
    model, family = SEATS[seat]
    conn = env.connect()
    try:
        with findings_db.transaction(conn):
            findings_db.insert_attempt(
                conn,
                {
                    "review_id": review_id,
                    "attempt_id": attempt_id,
                    "kind": "lesson",
                    "level": "a1",
                    "slug": "agreement-course",
                    "lesson_n": lesson_n,
                    "manifest_sha256": f"{lesson_n:064x}",
                    "reviewer_model": model,
                    "reviewer_family": family,
                    "harness": seat,
                    "verdict": "REVISE",
                    "validated_at": "2026-09-24T00:00:00+00:00",
                    "task_id": f"task-{review_id}",
                    "role": "first",
                },
            )
    finally:
        conn.close()


def test_an_attempt_id_shared_by_two_reviews_of_a_lesson_refuses_the_agreement_report(env: Env) -> None:
    _first_world(env)
    # an older attempt of another seat with the same attempt id on the same lesson, under another review id
    _shadow_attempt(env, "rev-old", "g1-first", "grok", 1)
    _lesson_pair(env, 1, "codex", "agy")
    with pytest.raises(score.ScoreError) as raised:
        score.agreement_by_seat_pair(["a1"], db_path_for=env.path_for, confidence=0.95)
    assert raised.value.code == score.AGREEMENT_AMBIGUOUS and "rev-old" in str(raised.value)
    with pytest.raises(score.ScoreError) as raised:
        run(env)
    assert raised.value.code == score.AGREEMENT_AMBIGUOUS


def test_an_attempt_id_reused_on_another_lesson_does_not_confuse_the_seat_pair(env: Env) -> None:
    _first_world(env)
    _shadow_attempt(env, "rev-old", "g1-first", "grok", 2)  # the same id, but a different lesson
    _lesson_pair(env, 1, "codex", "agy")
    [entry] = score.agreement_by_seat_pair(["a1"], db_path_for=env.path_for, confidence=0.95)
    assert [side["harness"] for side in entry["seats"]] == ["agy", "codex"]


# --- the CLI ---------------------------------------------------------------------------------------------------------------


def test_the_cli_prints_the_report_or_refuses_with_a_code(
    env: Env, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    confirmation_world(env)
    monkeypatch.setattr(findings_db, "db_path", lambda level, repo_root=None: env.db)
    assert score.main(["--seat", "codex", "--set", "confirmation", "--repo-root", str(env.root)]) == 0
    assert "EXPLORATORY" in capsys.readouterr().out
    assert score.main(["--seat", "codex", "--set", "confirmation", "--json", "--repo-root", str(env.root)]) == 0
    assert json.loads(capsys.readouterr().out)["set"] == "confirmation"
    assert score.main(["--seat", "agy", "--set", "confirmation", "--repo-root", str(env.root)]) == 2
    assert "no_attempts" in capsys.readouterr().err


def test_agreement_with_missing_database_does_not_create_it(env: Env) -> None:
    assert score.agreement_by_seat_pair(["a1"], db_path_for=env.path_for, confidence=0.95) == []
    assert not env.path_for("a1").exists()


@pytest.mark.parametrize("reader", ["collect", "agreement"])
@pytest.mark.parametrize("versions", [None, [], [-1], [findings_db.SCHEMA_VERSION + 1], [5, 5]])
def test_readers_refuse_unrecognized_schema_without_mutation(env: Env, reader: str, versions) -> None:
    env.add(mechanical_seed("seed-schema"), "rolling")
    conn = env.connect()
    try:
        with conn:
            if versions is None:
                conn.execute("DROP TABLE schema_version")
            else:
                conn.execute("DELETE FROM schema_version")
                conn.executemany("INSERT INTO schema_version VALUES (?)", [(version,) for version in versions])
    finally:
        conn.close()
    before = env.db.read_bytes()
    with pytest.raises(findings_db.VersionMismatch, match="refusing to open"):
        if reader == "collect":
            score.collect("codex", "rolling", repo_root=env.root, db_path_for=env.path_for)
        else:
            score.agreement_by_seat_pair(["a1"], db_path_for=env.path_for, confidence=0.95)
    assert env.db.read_bytes() == before


@pytest.mark.parametrize("version", [*findings_db.MIGRATIONS, findings_db.SCHEMA_VERSION])
def test_readonly_findings_open_preserves_timeout_and_does_not_migrate(env: Env, version: int) -> None:
    conn = env.connect()
    try:
        with conn:
            conn.execute("UPDATE schema_version SET version = ?", (version,))
    finally:
        conn.close()
    before = env.db.read_bytes()
    conn = score._open_findings_readonly(env.db)
    try:
        assert conn.execute("SELECT version FROM schema_version").fetchone()[0] == version
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 30000
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("UPDATE schema_version SET version = 99")
    finally:
        conn.close()
    assert env.db.read_bytes() == before
