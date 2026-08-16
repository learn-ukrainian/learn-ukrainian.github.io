"""Tests for the seat-viability decision metric (#4797 decision metric v2).

Every floor is mutation-checked: a just-below input must fail with exactly
the expected machine reason and the adjacent just-above input must pass, so
deleting or inverting a floor comparison flips at least one assertion.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit import qg_seat_decision as qsd

REPO_ROOT = Path(__file__).resolve().parents[2]
SEAT = "pin-a [opencode/qg_bakeoff_opencode]"


def _obs(
    *,
    is_true: bool,
    fabrication_class: str | None = None,
    verdict: str = "CONFIRMED",
    slug: str = "fix-a",
    domain: str = "folk",
    run: int = 1,
    claim_id: str = "c1",
    seat: str = SEAT,
    arm: str = "tooled",
) -> qsd.ClaimObservation:
    return qsd.ClaimObservation(
        seat=seat,
        arm=arm,
        slug=slug,
        domain=domain,
        run=run,
        claim_id=claim_id,
        is_true=is_true,
        fabrication_class=fabrication_class,
        effective_verdict=verdict,
    )


def _healthy_observations(
    *,
    u_caught: int = 4,
    u_total: int = 4,
    m_caught: int = 4,
    m_total: int = 4,
    true_confirmed: int = 8,
    true_refuted: int = 0,
    true_total: int = 8,
    domain: str = "folk",
) -> list[qsd.ClaimObservation]:
    """A seat that passes every floor by default; knobs push one metric at a time."""
    observations: list[qsd.ClaimObservation] = []
    for index in range(u_total):
        observations.append(
            _obs(
                is_true=False,
                fabrication_class="U",
                verdict="REFUTED_BY_CONTRADICTION" if index < u_caught else "UNVERIFIED_INSUFFICIENT_SEARCH",
                claim_id=f"u{index}",
                domain=domain,
            )
        )
    for index in range(m_total):
        observations.append(
            _obs(
                is_true=False,
                fabrication_class="M",
                verdict="UNATTESTED_AFTER_SEARCH" if index < m_caught else "UNVERIFIED_INSUFFICIENT_SEARCH",
                claim_id=f"m{index}",
                domain=domain,
            )
        )
    for index in range(true_total):
        if index < true_confirmed:
            verdict = "CONFIRMED"
        elif index < true_confirmed + true_refuted:
            verdict = "REFUTED_BY_CONTRADICTION"
        else:
            verdict = "UNATTESTED_AFTER_SEARCH"
        observations.append(_obs(is_true=True, verdict=verdict, claim_id=f"t{index}", domain=domain))
    return observations


class TestWilsonInterval:
    def test_zero_total_is_none(self) -> None:
        assert qsd.wilson_interval(0, 0) is None

    def test_invalid_fraction_raises(self) -> None:
        with pytest.raises(qsd.SeatDecisionError):
            qsd.wilson_interval(5, 4)

    def test_degenerate_endpoints_are_exact(self) -> None:
        lo_all, hi_all = qsd.wilson_interval(10, 10)
        assert hi_all == pytest.approx(1.0)
        assert 0 < lo_all < 1
        lo_none, hi_none = qsd.wilson_interval(0, 10)
        assert lo_none == pytest.approx(0.0)
        assert 0 < hi_none < 1

    def test_complement_symmetry(self) -> None:
        lo, hi = qsd.wilson_interval(8, 10)
        clo, chi = qsd.wilson_interval(2, 10)
        assert lo == pytest.approx(1 - chi)
        assert hi == pytest.approx(1 - clo)

    def test_contains_point_estimate_and_narrows_with_n(self) -> None:
        lo, hi = qsd.wilson_interval(8, 10)
        assert lo < 0.8 < hi
        lo_big, hi_big = qsd.wilson_interval(80, 100)
        assert hi_big - lo_big < hi - lo

    def test_known_value_regression_pin(self) -> None:
        # Wilson 95% for 8/10 — pinned so a formula mutation cannot pass silently.
        lo, hi = qsd.wilson_interval(8, 10)
        assert lo == pytest.approx(0.4901625, abs=1e-6)
        assert hi == pytest.approx(0.9433178, abs=1e-6)


class TestEffectiveVerdict:
    def test_missing_claim(self) -> None:
        assert qsd.effective_verdict({"matched": False, "verdict": "CONFIRMED"}) == "MISSING"

    def test_gate_neutralized_positive_is_downgraded(self) -> None:
        row = {"matched": True, "verdict": "CONFIRMED", "live_admissible_neutralized": True}
        assert qsd.effective_verdict(row) == "UNVERIFIED_INSUFFICIENT_SEARCH"

    def test_plain_verdict_uppercased(self) -> None:
        assert qsd.effective_verdict({"matched": True, "verdict": "confirmed"}) == "CONFIRMED"


class TestDecideSeat:
    def test_healthy_seat_is_viable_with_no_reasons(self) -> None:
        report = qsd.decide_seat(SEAT, _healthy_observations())
        assert report.decision == qsd.DECISION_VIABLE
        assert report.reasons == []
        assert report.audit_notes == []

    def test_bare_arm_observations_are_ignored(self) -> None:
        observations = _healthy_observations()
        observations.append(_obs(is_true=False, fabrication_class="U", verdict="CONFIRMED", arm="bare"))
        report = qsd.decide_seat(SEAT, observations)
        assert report.decision == qsd.DECISION_VIABLE
        assert report.unsafe_accepts is not None and report.unsafe_accepts.numerator == 0

    def test_unsafe_accept_is_not_viable(self) -> None:
        observations = _healthy_observations()
        observations.append(
            _obs(is_true=False, fabrication_class="U", verdict="CONFIRMED", slug="fix-b", claim_id="planted")
        )
        report = qsd.decide_seat(SEAT, observations)
        assert report.decision == qsd.DECISION_NOT_VIABLE
        assert "UNSAFE_ACCEPT" in report.reasons
        assert {"fixture": "fix-b", "claim_id": "planted", "run": 1} in report.unsafe_accept_claims

    def test_unsafe_accept_allowlist_clears_reason(self) -> None:
        observations = _healthy_observations()
        observations.append(
            _obs(is_true=False, fabrication_class="U", verdict="CONFIRMED", slug="fix-b", claim_id="planted")
        )
        report = qsd.decide_seat(
            SEAT,
            observations,
            unsafe_accept_allowlist=[{"fixture": "fix-b", "claim_id": "planted"}],
        )
        assert "UNSAFE_ACCEPT" not in report.reasons

    def test_gate_neutralized_confirm_on_false_is_not_unsafe(self) -> None:
        # Admissibility is a HARD precondition: an inadmissible CONFIRMED was
        # neutralized upstream, so it reaches us as UNVERIFIED — no unsafe
        # accept, but also no fabrication catch.
        observations = _healthy_observations()
        observations.append(
            _obs(
                is_true=False,
                fabrication_class="U",
                verdict="UNVERIFIED_INSUFFICIENT_SEARCH",
                claim_id="neutralized",
            )
        )
        report = qsd.decide_seat(SEAT, observations)
        assert "UNSAFE_ACCEPT" not in report.reasons
        assert report.u_recall.numerator == 4
        assert report.u_recall.denominator == 5

    def test_u_recall_floor_boundary(self) -> None:
        # 3/4 = 0.75 meets the floor; 2/3 ≈ 0.667 fails it.
        passing = qsd.decide_seat(SEAT, _healthy_observations(u_caught=3, u_total=4))
        assert "U_RECALL_FLOOR" not in passing.reasons
        failing = qsd.decide_seat(SEAT, _healthy_observations(u_caught=2, u_total=3))
        assert failing.decision == qsd.DECISION_NOT_VIABLE
        assert "U_RECALL_FLOOR" in failing.reasons

    def test_m_recall_floor_boundary(self) -> None:
        # 4/7 meets the floor exactly; 3/7 fails it.
        passing = qsd.decide_seat(SEAT, _healthy_observations(m_caught=4, m_total=7))
        assert "M_RECALL_FLOOR" not in passing.reasons
        failing = qsd.decide_seat(SEAT, _healthy_observations(m_caught=3, m_total=7))
        assert failing.decision == qsd.DECISION_NOT_VIABLE
        assert "M_RECALL_FLOOR" in failing.reasons

    def test_true_retention_floor_boundary(self) -> None:
        passing = qsd.decide_seat(SEAT, _healthy_observations(true_confirmed=4, true_total=8))
        assert "TRUE_RETENTION_FLOOR" not in passing.reasons
        failing = qsd.decide_seat(SEAT, _healthy_observations(true_confirmed=3, true_total=8))
        assert failing.decision == qsd.DECISION_NOT_VIABLE
        assert "TRUE_RETENTION_FLOOR" in failing.reasons

    def test_true_refuted_guardrail_boundary(self) -> None:
        # 1/10 = 0.1 is allowed (ceiling is ≤); 2/10 breaches it.
        passing = qsd.decide_seat(SEAT, _healthy_observations(true_confirmed=9, true_refuted=1, true_total=10))
        assert "TRUE_REFUTED_GUARDRAIL" not in passing.reasons
        failing = qsd.decide_seat(SEAT, _healthy_observations(true_confirmed=8, true_refuted=2, true_total=10))
        assert failing.decision == qsd.DECISION_NOT_VIABLE
        assert "TRUE_REFUTED_GUARDRAIL" in failing.reasons

    def test_missing_claims_count_against_recall_and_coverage(self) -> None:
        # 20 claims per arm keeps one MISSING under the 0.9 coverage floor,
        # so the anti-gaming rule (missing U counts as not caught) is isolated.
        observations = _healthy_observations(u_caught=4, u_total=4, m_caught=8, m_total=8, true_total=8)
        observations.append(_obs(is_true=False, fabrication_class="U", verdict="MISSING", claim_id="omitted"))
        report = qsd.decide_seat(SEAT, observations)
        assert report.u_recall.denominator == 5
        assert report.u_recall.numerator == 4
        assert report.coverage is not None
        assert report.coverage.numerator == 20
        assert report.coverage.denominator == 21
        assert "COVERAGE_FLOOR" not in report.reasons

    def test_coverage_floor_boundary(self) -> None:
        # 18/20 = 0.9 exactly meets the floor; 18/21 ≈ 0.857 fails it.
        base = _healthy_observations(u_caught=4, u_total=4, m_caught=8, m_total=8, true_total=6)
        passing_observations = base + [
            _obs(is_true=True, verdict="MISSING", claim_id=f"miss{index}") for index in range(2)
        ]
        passing = qsd.decide_seat(SEAT, passing_observations)
        assert "COVERAGE_FLOOR" not in passing.reasons
        failing_observations = base + [
            _obs(is_true=True, verdict="MISSING", claim_id=f"miss{index}") for index in range(3)
        ]
        failing = qsd.decide_seat(SEAT, failing_observations)
        assert "COVERAGE_FLOOR" in failing.reasons

    def test_domain_floor_named_reason(self) -> None:
        observations = _healthy_observations(domain="folk")
        # A second domain with enough denominator (4) and 0 catches.
        observations += [
            _obs(
                is_true=False,
                fabrication_class="U",
                verdict="UNVERIFIED_INSUFFICIENT_SEARCH",
                slug="hist-fix",
                domain="history",
                claim_id=f"h{index}",
            )
            for index in range(4)
        ]
        # Keep the seat-level U recall above its floor: 16 more catches.
        observations += [
            _obs(
                is_true=False,
                fabrication_class="U",
                verdict="REFUTED_BY_CONTRADICTION",
                claim_id=f"extra{index}",
            )
            for index in range(16)
        ]
        report = qsd.decide_seat(SEAT, observations)
        assert "U_RECALL_FLOOR" not in report.reasons
        assert "DOMAIN_FLOOR_history_u_recall" in report.reasons
        assert report.decision == qsd.DECISION_NOT_VIABLE

    def test_small_domain_is_low_n_note_not_reason(self) -> None:
        observations = _healthy_observations(domain="folk")
        observations.append(
            _obs(
                is_true=False,
                fabrication_class="U",
                verdict="UNVERIFIED_INSUFFICIENT_SEARCH",
                slug="hist-fix",
                domain="history",
                claim_id="h0",
            )
        )
        report = qsd.decide_seat(SEAT, observations)
        assert not any(reason.startswith("DOMAIN_FLOOR_history") for reason in report.reasons)
        assert "DOMAIN_LOW_N_history" in report.audit_notes
        assert report.decision == qsd.DECISION_VIABLE_WITH_AUDIT

    def test_no_class_denominator_is_insufficient_data(self) -> None:
        observations = [_obs(is_true=True, verdict="CONFIRMED", claim_id=f"t{index}") for index in range(6)]
        report = qsd.decide_seat(SEAT, observations)
        assert report.decision == qsd.DECISION_INSUFFICIENT_DATA
        assert report.reasons == ["INSUFFICIENT_DATA"]

    def test_unsafe_accept_dominates_empty_class_short_circuit(self) -> None:
        # CF finding on #6883: zero tolerance must dominate — a counted unsafe
        # accept is NOT_VIABLE even when an empty U/M class would otherwise
        # short-circuit the decision to INSUFFICIENT_DATA.
        # Both classes empty: the only false claim is unclassified and CONFIRMED.
        observations = [_obs(is_true=False, fabrication_class=None, verdict="CONFIRMED", claim_id="planted")]
        report = qsd.decide_seat(SEAT, observations)
        assert report.unsafe_accepts is not None and report.unsafe_accepts.numerator == 1
        assert report.decision == qsd.DECISION_NOT_VIABLE
        assert "UNSAFE_ACCEPT" in report.reasons
        assert "INSUFFICIENT_DATA" not in report.reasons
        # One class empty (no M rows): still NOT_VIABLE, never INSUFFICIENT_DATA.
        observations = [_obs(is_true=False, fabrication_class="U", verdict="CONFIRMED", claim_id="planted")]
        report = qsd.decide_seat(SEAT, observations)
        assert report.decision == qsd.DECISION_NOT_VIABLE
        assert "UNSAFE_ACCEPT" in report.reasons
        # Allowlisted, the unsafe accept no longer counts, so the empty-class
        # short-circuit applies again.
        report = qsd.decide_seat(
            SEAT,
            observations,
            unsafe_accept_allowlist=[{"fixture": "fix-a", "claim_id": "planted"}],
        )
        assert report.decision == qsd.DECISION_INSUFFICIENT_DATA
        assert report.reasons == ["INSUFFICIENT_DATA"]


def _artifact(
    *,
    pin: str = "pin-a",
    slug: str = "fix-a",
    arm: str = "tooled",
    run_index: int = 1,
    claims: list[dict[str, object]],
    failure_class: str | None = None,
) -> dict[str, object]:
    artifact: dict[str, object] = {
        "model": {"pin": pin, "transport": "opencode", "entrypoint": "qg_bakeoff_opencode"},
        "fixture": {"slug": slug},
        "arm": arm,
        "run_index": run_index,
        "status": "ran",
        "score": {"claims": claims},
    }
    if failure_class:
        artifact["failure_class"] = failure_class
    return artifact


class TestObservationsFromArtifacts:
    def test_extracts_effective_outcomes(self) -> None:
        claims = [
            {"claim_id": "c1", "matched": True, "is_true": True, "fabrication_class": None, "verdict": "CONFIRMED"},
            {
                "claim_id": "c2",
                "matched": True,
                "is_true": False,
                "fabrication_class": "U",
                "verdict": "CONFIRMED",
                "live_admissible_neutralized": True,
            },
            {"claim_id": "c3", "matched": False, "is_true": False, "fabrication_class": "M"},
        ]
        observations = qsd.observations_from_artifacts([_artifact(claims=claims)], {"fix-a": "folk"})
        assert [o.effective_verdict for o in observations] == [
            "CONFIRMED",
            "UNVERIFIED_INSUFFICIENT_SEARCH",
            "MISSING",
        ]
        assert observations[0].domain == "folk"
        assert observations[0].seat == SEAT

    def test_ops_quota_cells_excluded(self) -> None:
        claims = [{"claim_id": "c1", "matched": True, "is_true": True, "verdict": "CONFIRMED"}]
        observations = qsd.observations_from_artifacts([_artifact(claims=claims, failure_class="ops_quota")], {})
        assert observations == []


class TestScorecardRoundTrip:
    """The degraded-mode parser must track qg_bakeoff's scorecard emitter."""

    @pytest.fixture()
    def scorecard(self, tmp_path: Path) -> Path:
        from scripts.audit import qg_bakeoff

        fixture = qg_bakeoff.BakeoffFixture(
            slug="fix-a",
            title="Fixture A",
            passage_md="passage",
            claims=(
                qg_bakeoff.FixtureClaim("t1", "True claim one", True),
                qg_bakeoff.FixtureClaim("u1", "Planted U claim", False, fabrication_class="U"),
                qg_bakeoff.FixtureClaim("m1", "Planted M claim", False, fabrication_class="M"),
            ),
        )
        payload = {
            "fact_checks": [
                {"claim": "True claim one", "verdict": "CONFIRMED"},
                {"claim": "Planted U claim", "verdict": "REFUTED_BY_CONTRADICTION"},
                {"claim": "Planted M claim", "verdict": "UNATTESTED_AFTER_SEARCH"},
            ]
        }
        score = qg_bakeoff.score_payload(payload, fixture)
        artifacts = [
            _artifact(claims=[], slug="fix-a") | {"score": score},
            _artifact(claims=[], slug="fix-a", arm="bare") | {"score": score},
        ]
        path = tmp_path / "SCORECARD.md"
        qg_bakeoff.write_scorecard(path, artifacts)
        return path

    def test_round_trip_matches_emitter(self, scorecard: Path) -> None:
        rows = qsd.parse_scorecard_runs_table(scorecard.read_text(encoding="utf-8"))
        tooled = [row for row in rows if row["arm"] == "tooled"]
        assert len(tooled) == 1
        assert tooled[0]["passage"] == "fix-a"
        assert tooled[0]["u honesty"].startswith("1/1")
        assert tooled[0]["m alignment"].startswith("1/1")

    def test_degraded_reports_capped_at_audit(self, scorecard: Path) -> None:
        reports = qsd.seat_reports_from_scorecard(
            scorecard.read_text(encoding="utf-8"),
            {"fix-a": "folk"},
            {"fix-a": 3},
        )
        assert len(reports) == 1
        report = reports[0]
        assert report.decision == qsd.DECISION_VIABLE_WITH_AUDIT
        assert "UNSAFE_ACCEPTS_UNKNOWN" in report.audit_notes
        assert "TRUE_RETENTION_UNKNOWN" in report.audit_notes
        assert report.unsafe_accepts is None
        assert report.u_recall.numerator == 1
        assert report.u_recall.denominator == 1
        assert report.coverage is not None and report.coverage.rate == 1.0

    def test_missing_fixture_count_is_an_error(self, scorecard: Path) -> None:
        with pytest.raises(qsd.SeatDecisionError):
            qsd.seat_reports_from_scorecard(scorecard.read_text(encoding="utf-8"), {}, {})


class TestCommittedMultirunScorecard:
    """Integration against the committed 17-fixture multirun scorecard."""

    SCORECARD = REPO_ROOT / "audit" / "2026-07-06-qg-bakeoff-multirun" / "SCORECARD.md"

    def test_parses_all_seats_and_fixtures(self) -> None:
        from scripts.audit.qg_bakeoff import DOMAIN_BY_SLUG

        markdown = self.SCORECARD.read_text(encoding="utf-8")
        rows = qsd.parse_scorecard_runs_table(markdown)
        tooled_rows = [row for row in rows if row["arm"] == "tooled"]
        assert len({row["passage"] for row in tooled_rows}) == 17
        reports = qsd.seat_reports_from_scorecard(
            markdown,
            DOMAIN_BY_SLUG,
            {slug: 9 for slug in DOMAIN_BY_SLUG},
        )
        assert len(reports) == 3
        for report in reports:
            # 17 fixtures × 3 runs × 1 U claim each.
            assert report.u_recall.denominator == 51
            assert report.decision in {
                qsd.DECISION_VIABLE_WITH_AUDIT,
                qsd.DECISION_NOT_VIABLE,
            }


class TestCli:
    def test_artifact_dir_mode_writes_outputs(self, tmp_path: Path) -> None:
        claims = [
            {"claim_id": "t1", "matched": True, "is_true": True, "fabrication_class": None, "verdict": "CONFIRMED"},
            {
                "claim_id": "u1",
                "matched": True,
                "is_true": False,
                "fabrication_class": "U",
                "verdict": "REFUTED_BY_CONTRADICTION",
            },
            {
                "claim_id": "m1",
                "matched": True,
                "is_true": False,
                "fabrication_class": "M",
                "verdict": "UNATTESTED_AFTER_SEARCH",
            },
        ]
        out_dir = tmp_path / "bakeoff"
        out_dir.mkdir()
        (out_dir / "cell.json").write_text(json.dumps(_artifact(claims=claims)), encoding="utf-8")
        json_out = tmp_path / "decision.json"
        md_out = tmp_path / "DECISION.md"
        exit_code = qsd.main([str(out_dir), "--json-out", str(json_out), "--md-out", str(md_out)])
        assert exit_code == 0
        payload = json.loads(json_out.read_text(encoding="utf-8"))
        assert payload["degraded_input"] is False
        assert payload["thresholds"]["u_recall_floor"] == qsd.U_RECALL_FLOOR
        assert payload["seats"][0]["seat"] == SEAT
        assert "QG Seat Decision" in md_out.read_text(encoding="utf-8")

    def test_empty_dir_is_an_error(self, tmp_path: Path) -> None:
        assert qsd.main([str(tmp_path)]) == 2
