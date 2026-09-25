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
import math
from datetime import date
from pathlib import Path

import pytest

from scripts.review import findings_db
from scripts.review.seeds import manifest as sm
from scripts.review.seeds import score
from tests.review.seeds.fixtures import Env, clean_lesson, finding, linguistic_seed, mechanical_seed

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


@pytest.mark.parametrize(
    ("k", "n", "low", "high"),
    [
        (2, 4, 0.1500, 0.8500),
        (1, 4, 0.0456, 0.6994),
        (3, 6, 0.1876, 0.8124),
        (7, 10, 0.3968, 0.8922),
        (8, 10, 0.4902, 0.9433),
        (5, 10, 0.2366, 0.7634),
        (0, 22, 0.0, 3.8415 / (22 + 3.8415)),  # closed form: z^2 / (n + z^2)
        (22, 22, 22 / (22 + 3.8415), 1.0),
    ],
)
def test_the_wilson_interval_matches_the_hand_computed_values(k: int, n: int, low: float, high: float) -> None:
    got_low, got_high = score.wilson_interval(k, n, 0.95)
    assert near(got_low, low) and near(got_high, high), (got_low, got_high)


def test_the_wilson_interval_of_no_trials_is_undefined_and_bad_counts_are_refused() -> None:
    assert score.wilson_interval(0, 0, 0.95) is None
    with pytest.raises(ValueError):
        score.wilson_interval(5, 4, 0.95)


def test_the_normal_quantile_follows_the_confidence() -> None:
    assert near(score.z_value(0.95), 1.95996) and near(score.z_value(0.90), 1.64485)
    assert score.wilson_interval(5, 10, 0.90)[0] > score.wilson_interval(5, 10, 0.95)[0]


@pytest.mark.parametrize(
    ("events", "low", "high"),
    [  # the exact (Garwood) 95 % limits of a Poisson mean given the count
        (0, 0.0, 3.6889),
        (1, 0.0253, 5.5716),
        (2, 0.2422, 7.2247),
        (5, 1.6235, 11.6683),
        (10, 4.7954, 18.3904),
    ],
)
def test_the_poisson_exact_interval_matches_the_tabulated_limits(events: int, low: float, high: float) -> None:
    got_low, got_high = score.poisson_exact_interval(events, 1, 0.95)
    assert near(got_low, low) and near(got_high, high), (got_low, got_high)


def test_the_poisson_interval_scales_with_the_number_of_lessons() -> None:
    low, high = score.poisson_exact_interval(2, 4, 0.95)
    assert near(low, 0.2422 / 4) and near(high, 7.2247 / 4)
    assert score.poisson_exact_interval(0, 0, 0.95) is None
    with pytest.raises(ValueError):
        score.poisson_exact_interval(-1, 4, 0.95)


@pytest.mark.parametrize(
    ("only_a", "only_b", "p"),
    [
        (1, 6, 0.125),  # 2 * (1 + 7) / 2^7
        (0, 8, 2 / 256),
        (6, 1, 0.125),
        (3, 3, 1.0),  # a tie is capped at 1
        (1, 2, 1.0),  # 2 * (1 + 3) / 8
        (2, 10, 2 * (1 + 12 + 66) / 4096),
        (0, 1, 1.0),
    ],
)
def test_exact_mcnemar_matches_the_binomial_tail(only_a: int, only_b: int, p: float) -> None:
    assert score.mcnemar_exact(only_a, only_b) == NEAR(p)


def test_mcnemar_without_discordant_pairs_has_no_p_value() -> None:
    assert score.mcnemar_exact(0, 0) is None


def test_the_intervals_agree_with_scipy_on_a_grid() -> None:
    stats = pytest.importorskip("scipy.stats", reason="scipy is only a cross-check")

    for n in (1, 2, 5, 22, 30, 100):
        for k in range(0, n + 1, max(1, n // 7)):
            ref = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson")
            low, high = score.wilson_interval(k, n, 0.95)
            assert math.isclose(low, ref.low, abs_tol=1e-9) and math.isclose(high, ref.high, abs_tol=1e-9), (k, n)
    for k in (0, 1, 2, 7, 20, 60):
        low, high = score.poisson_exact_interval(k, 1, 0.95)
        ref_low = 0.0 if k == 0 else stats.chi2.ppf(0.025, 2 * k) / 2
        ref_high = stats.chi2.ppf(0.975, 2 * k + 2) / 2
        assert math.isclose(low, ref_low, abs_tol=1e-8) and math.isclose(high, ref_high, abs_tol=1e-8), k
    for a, b in ((1, 6), (2, 10), (0, 9), (4, 4)):
        assert math.isclose(score.mcnemar_exact(a, b), stats.binomtest(min(a, b), a + b, 0.5).pvalue, abs_tol=1e-12)


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


def test_dimensions_with_no_seeds_are_listed_with_no_units(fixture_score) -> None:
    _, _, result = fixture_score
    empty = result.report["recall_by_dimension"]["fact"]
    assert (empty["k"], empty["n"], empty["point"], empty["low"], empty["high"]) == (0, 0, None, None, None)
    assert set(result.report["recall_by_dimension"]) >= {
        "job",
        "language",
        "learner_fit",
        "activity",
        "evidence_use",
        "english",
        "fact",
        "recap",
    }


def test_blocking_recall_is_a_planted_finding_that_holds_the_lesson(fixture_score) -> None:
    _, _, result = fixture_score
    job = result.report["blocking_recall_by_dimension"]["job"]
    # seed-job-2 was found but only as MINOR: detected, not blocking -> 1 of 4
    assert (job["k"], job["n"]) == (1, 4) and near(job["low"], 0.0456) and near(job["high"], 0.6994)
    assert result.report["blocking_recall_by_dimension"]["activity"]["k"] == 1
    assert (result.report["blocking_recall_pooled"]["k"], result.report["blocking_recall_pooled"]["n"]) == (2, 6)


def test_the_valid_attempt_recall_is_secondary_and_excludes_failed_and_rejected_attempts(fixture_score) -> None:
    _, _, result = fixture_score
    valid = result.report["recall_valid_first_attempts_by_dimension"]
    assert (valid["job"]["k"], valid["job"]["n"]) == (2, 3) and (valid["activity"]["k"], valid["activity"]["n"]) == (
        1,
        1,
    )
    assert (
        result.report["recall_valid_first_attempts_pooled"]["k"],
        result.report["recall_valid_first_attempts_pooled"]["n"],
    ) == (3, 4)
    text = score.render_report(result)
    assert "secondary" in text and "recall on valid first attempts" in text


def test_false_findings_per_clean_lesson_uses_poisson_exact_and_never_counts_a_genuine_additional_finding(
    fixture_score,
) -> None:
    _, _, result = fixture_score
    rate = result.report["false_findings_per_clean_lesson"]
    # clean-1: two false findings; clean-2's blocker is a genuine_additional finding -> not false; 2 over 4 lessons
    assert (rate["events"], rate["lessons"], rate["method"]) == (2, 4, "poisson_exact") and rate["point"] == 0.5
    assert near(rate["low"], 0.2422 / 4) and near(rate["high"], 7.2247 / 4)
    assert result.report["adjudicated_classes"]["clean"] == {"false": 2, "genuine_additional": 1}


def test_the_share_of_clean_lessons_falsely_blocked_is_wilson_and_leaves_a_genuine_blocker_out(fixture_score) -> None:
    _, _, result = fixture_score
    blocked = result.report["clean_lessons_falsely_blocked"]
    assert (blocked["k"], blocked["n"], blocked["method"]) == (1, 4, "wilson")
    assert near(blocked["low"], 0.0456) and near(blocked["high"], 0.6994)


def test_the_evidence_validation_rate_has_rejected_and_failed_attempts_in_the_denominator(fixture_score) -> None:
    _, _, result = fixture_score
    validation = result.report["evidence_validation"]
    # ten first attempts; seed-job-4 and clean-4 failed, seed-act-1 was rejected -> 7 accepted
    assert (
        (validation["k"], validation["n"]) == (7, 10)
        and near(validation["low"], 0.3968)
        and near(validation["high"], 0.8922)
    )
    assert result.report["first_attempt_outcomes"] == {"accepted": 7, "failed": 2, "rejected": 1}


def test_a_retry_is_reported_and_never_scored_as_a_second_observation(fixture_score) -> None:
    _, ids, result = fixture_score
    retries = result.report["retries"]
    assert retries["units"] == 1 and retries["attempts"] == 1 and retries["outcomes"] == {"accepted": 1}
    assert [outcome for _, outcome in retries["by_unit"]["seed-job-4"]] == ["accepted"]
    observation = result.observations["seed-job-4"]
    assert (observation.outcome, observation.detected, observation.blocking) == ("failed", False, False)
    assert observation.attempt_id == ids["seed-job-4"][1]
    assert len(result.observations) == 10, "one observation per unit"
    assert result.report["units"] == {"seeds": 6, "clean": 4}


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


def test_the_fixture_report_is_exploratory_and_says_why_in_its_title_and_first_line(fixture_score) -> None:
    _, _, result = fixture_score
    report = result.report
    assert report["threshold_eligible"] is False
    text = score.render_report(result)
    lines = text.splitlines()
    assert lines[0].startswith("# EXPLORATORY — not for choosing a threshold")
    assert lines[2].startswith("**EXPLORATORY — not for choosing a threshold.**")
    assert "job: 4 scored planted defects on real built lessons, 22 needed" in text
    assert "4 scored clean lessons on real built lessons, 30 needed" in text
    assert "Known limits" in text and "Recall is measured against the defects we thought of" in text
    assert "about 21 planted defects per dimension" in text


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


def test_only_real_built_lessons_count_toward_the_size(env: Env) -> None:
    _big_set(env, per_dimension=22, cleans=30, source="fixture")
    result = run(env)
    assert result.report["threshold_eligible"] is False
    assert set(result.report["eligibility"]["real_built_seeds_by_dimension"].values()) == {0}


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
        "seed-l2", planter_model="gpt-6-astra", planter_family="openai", writer_family="anthropic"
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
    conn.execute("UPDATE attempts SET reviewer_model = 'gpt-6-sol' WHERE attempt_id = ?", (ids[1],))
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
    assert run(env, model="gpt-6-astra", allow_partial=True).report["models"] == ["gpt-6-astra"]


def test_a_seat_with_no_attempts_has_nothing_to_score(env: Env) -> None:
    env.add(mechanical_seed("seed-a1"), "first")
    env.add(mechanical_seed("seed-held-out"))
    sm.freeze_confirmation(["seed-held-out"], env.root)
    with pytest.raises(score.ScoreError) as caught:
        run(env, seat="agy")
    assert caught.value.code == score.NO_ATTEMPTS


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


def test_the_threshold_is_shown_only_when_the_operator_has_written_it(env: Env) -> None:
    confirmation_world(env)
    text = score.render_report(
        run(env, set_name="confirmation", params={**findings_db.load_parameters(), "admission_threshold": 0.8})
    )
    assert "Admission threshold: 0.8." in text


# --- the paired comparison ------------------------------------------------------------------------------------------------


def _seat_score(seat: str, detections: dict[str, bool]) -> score.SeatScore:
    observations = {
        unit: score.Observation(unit, "seed", "job", "real_built", "r", f"a-{unit}", "accepted", detected=found)
        for unit, found in detections.items()
    }
    return score.SeatScore(seat, "first", observations, {})


def test_the_paired_comparison_is_exact_mcnemar_on_the_discordant_seeds() -> None:
    # 12 shared seeds: both found 4; only b found 6; only a found 1; neither found 1
    a = {f"s{i}": True for i in range(4)} | {"s4": True} | {f"s{i}": False for i in range(5, 12)}
    b = {f"s{i}": True for i in range(4)} | {"s4": False} | {f"s{i}": (i < 11) for i in range(5, 12)}
    a["only-a-only"], b["only-b-only"] = True, True  # a seed only one seat was scored on is not a pair
    paired = score.paired_comparison(_seat_score("codex", a), _seat_score("agy", b))
    assert paired["paired_seeds"] == 12 and paired["both_detected"] == 4
    assert (paired["only_a_detected"], paired["only_b_detected"], paired["neither_detected"]) == (1, 6, 1)
    assert paired["p_value"] == NEAR(0.125) and paired["test"] == "mcnemar_exact"
    assert paired["discordant_seeds"]["only_a"] == ["s4"]
    assert "Exact McNemar on the discordant pairs: p = 0.1250" in score.render_report(
        score.SeatScore("codex", "first", {}, {**_stub_report()}), paired
    )


def test_a_paired_comparison_with_no_shared_or_no_discordant_seeds_has_no_p_value() -> None:
    same = {"s1": True, "s2": False}
    assert score.paired_comparison(_seat_score("a", same), _seat_score("b", same))["p_value"] is None
    none = score.paired_comparison(_seat_score("a", {"s1": True}), _seat_score("b", {"s2": True}))
    assert none["paired_seeds"] == 0 and none["p_value"] is None


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


def _stub_report() -> dict:
    observations = {"s1": score.Observation("s1", "seed", "job", "fixture", "r", "a", "accepted", detected=True)}
    return score.compute_report(
        "codex",
        "first",
        observations,
        {"models": ["m"], "family": "openai", "not_applicable": {}, "not_attempted": [], "pending": []},
        None,
        findings_db.load_parameters(),
        today=TODAY,
    )


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


def test_the_report_directory_is_dated_and_named_for_the_seat() -> None:
    path = score.report_path("codex", date(2026, 9, 25), Path("/repo"))
    assert path == Path("/repo/audit/reviewer-measurement/2026-09-25-codex/REPORT.md")
