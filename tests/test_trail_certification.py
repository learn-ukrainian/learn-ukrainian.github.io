"""Tests for the hermetic P14 TrailSpec certification harness."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.orchestration.trails import trail_certification as certification_module
from scripts.orchestration.trails.models import CommandExecution, ExitClass
from scripts.orchestration.trails.trail_certification import (
    BINARY_DAMAGE_EVENT_CODES,
    FAULT_CLASSES,
    CaseExpectation,
    CertificationCase,
    CertificationSubject,
    CoverageRequirements,
    HermeticCertificationError,
    HermeticFixture,
    P3Action,
    TrailCertificationError,
    TrailCertificationHarness,
    UnsupportedTrailSpecError,
    case_matrix_coverage_gaps,
    load_case_matrix,
    one_sided_95_upper_bound,
    validate_certification_attestation_data,
)

FIXTURES = Path(__file__).parent / "trails" / "fixtures" / "certification"
RUNNER_COMMIT = "a" * 40
RUNNER_DIGEST = "b" * 64


def _fixed_clock() -> datetime:
    return datetime(2026, 7, 29, 9, 0, 0, tzinfo=UTC)


def _harness(tmp_path: Path) -> TrailCertificationHarness:
    return TrailCertificationHarness(
        output_root=tmp_path / "batch_state" / "trail-certification",
        runner_commit=RUNNER_COMMIT,
        runner_digest=RUNNER_DIGEST,
        clock=_fixed_clock,
    )


def _subject(
    *,
    trail_path: Path | None = None,
    seat: str = "certification-seat",
    decision_table_paths: dict[str, Path] | None = None,
) -> CertificationSubject:
    return CertificationSubject(
        trail_path=trail_path or FIXTURES / "executable.trail.yaml",
        seat=seat,
        model="synthetic-model",
        harness="synthetic-harness",
        cli_version="0.0-test",
        tool_isolation_profile="exact-three-tool-test",
        decision_table_paths=decision_table_paths,
    )


def _fixture() -> HermeticFixture:
    return HermeticFixture(
        project_root=FIXTURES,
        seat_registry_path=FIXTURES / "seats.yaml",
    )


def _case(
    *,
    case_id: str,
    transition: str,
    outcome: str,
    exit_class: ExitClass,
    state: str,
    stop_code: str | None = None,
    fault: str = "unknown-ci",
    plant: str = "synthetic-plant",
    damage_event_codes: tuple[str, ...] = (),
    fault_stage: str | None = None,
) -> CertificationCase:
    token = "accepted" if transition == "accepted" else "refused"
    return CertificationCase(
        case_id=case_id,
        fault=fault,
        plant=plant,
        expected=CaseExpectation(
            transition=transition,
            stop_code=stop_code,
            outcome=outcome,
            exit_class=int(exit_class),
            state=state,
        ),
        actions=(P3Action(verb="step", expected_step="start"),),
        command_execution=CommandExecution(exit_code=0, stdout=token, stderr=""),
        fault_stage=fault_stage,
        damage_event_codes=damage_event_codes,
    )


def test_harness_executes_p3_cases_from_sqlite_and_writes_bound_attestation(tmp_path: Path) -> None:
    accepted = _case(
        case_id="current-head-approval",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
        fault="interruption-resume",
        plant="current-head-approval",
    )
    refused = _case(
        case_id="draft-ci-refused",
        transition="refused",
        outcome="stop_parked",
        exit_class=ExitClass.STOP_PARKED,
        state="parked",
        stop_code="STOP-unknown",
        fault="unknown-ci",
        plant="draft-ci",
    )
    tables = tmp_path / "decision-table.yaml"
    tables.write_text("schema_version: synthetic\n", encoding="utf-8")

    result = _harness(tmp_path).run(
        certification_id="certification-001",
        subject=_subject(decision_table_paths={"synthetic-table": tables}),
        fixture=_fixture(),
        cases=(accepted, refused),
        coverage=CoverageRequirements(
            transitions=("accepted", "refused"),
            stop_codes=("STOP-unknown",),
            fault_classes=("interruption-resume", "unknown-ci"),
        ),
    )

    persisted = json.loads(result.attestation_path.read_text(encoding="utf-8"))
    assert persisted == result.attestation
    assert result.attestation_path == (
        tmp_path / "batch_state" / "trail-certification" / "certification-001" / "attestation.json"
    )
    assert result.attestation["trail"]["trail_id"] == "rb3-certification-fixture"
    assert result.attestation["runner"] == {"commit": RUNNER_COMMIT, "digest": RUNNER_DIGEST}
    assert result.attestation["environment"]["tool_isolation_profile"] == "exact-three-tool-test"
    assert result.attestation["coverage"]["missing_transitions"] == []
    assert result.attestation["coverage"]["missing_stop_codes"] == []
    assert result.attestation["coverage"]["missing_fault_classes"] == []
    assert result.attestation["cases"][1]["observed"]["stop_code"] == "STOP-unknown"
    assert result.attestation["cases"][0]["step_chain_digest"] != result.attestation["cases"][1]["step_chain_digest"]
    assert result.attestation["status"] == {
        "harness_passed": True,
        "trial_eligible": False,
        "production_certified": False,
        "demote": False,
    }
    assert result.attestation["live_canary_receipts"] == [
        {"slot": "live-canary-1", "status": "pending", "receipt": None},
        {"slot": "live-canary-2", "status": "pending", "receipt": None},
    ]
    state_db = result.attestation_path.parent / "cases" / "current-head-approval" / "state.sqlite3"
    assert state_db.is_file()


def test_harness_refuses_v1_before_constructing_the_p3_runner(tmp_path: Path, monkeypatch) -> None:
    case = _case(
        case_id="legacy-refusal",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
    )

    def assert_v1_refused(subject: CertificationSubject) -> None:
        try:
            _harness(tmp_path).run(
                certification_id="legacy",
                subject=subject,
                fixture=_fixture(),
                cases=(case,),
            )
        except UnsupportedTrailSpecError:
            return
        raise AssertionError("the certification harness accepted an execution-ineligible trail")

    assert_v1_refused(_subject(trail_path=FIXTURES / "legacy.trail.yaml", seat="grok-daily"))
    valid_spec = certification_module._read_trail(
        FIXTURES / "executable.trail.yaml", seat_registry_path=FIXTURES / "seats.yaml"
    )
    monkeypatch.setattr(certification_module, "_read_trail", lambda *args, **kwargs: valid_spec)
    with pytest.raises(AssertionError):
        assert_v1_refused(_subject())


def test_harness_records_an_injected_crash_without_spawning_a_live_command(tmp_path: Path) -> None:
    case = CertificationCase(
        case_id="crash-before-spawn",
        fault="crash-before-spawn",
        plant="retry-failure-preserved",
        expected=CaseExpectation(
            transition=None,
            stop_code=None,
            outcome="injected-crash",
            exit_class=None,
            state="active",
        ),
        actions=(P3Action(verb="step", expected_step="start"),),
        command_execution=CommandExecution(exit_code=0, stdout="accepted", stderr=""),
        fault_stage="after_prepared_before_spawn",
    )

    attestation = _harness(tmp_path).run(
        certification_id="crash-before-spawn",
        subject=_subject(),
        fixture=_fixture(),
        cases=(case,),
    ).attestation

    assert attestation["cases"][0]["observed"] == {
        "transition": None,
        "stop_code": None,
        "outcome": "injected-crash",
        "exit_class": None,
        "state": "active",
    }


def test_any_damage_event_demotes_even_when_the_case_transition_matches(tmp_path: Path) -> None:
    case = _case(
        case_id="self-review-accepted",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
        fault="conflicting-reviews",
        plant="self-review",
        damage_event_codes=("self-review-accepted",),
    )

    attestation = _harness(tmp_path).run(
        certification_id="damage-event",
        subject=_subject(),
        fixture=_fixture(),
        cases=(case,),
    ).attestation

    assert attestation["cases"][0]["passed"] is True
    assert attestation["damage_event_codes"] == ["self-review-accepted"]
    assert attestation["event_count"] == 1
    assert attestation["status"] == {
        "harness_passed": False,
        "trial_eligible": False,
        "production_certified": False,
        "demote": True,
    }


def test_hermetic_receipt_slots_are_pending_and_non_fabricable(tmp_path: Path) -> None:
    case = _case(
        case_id="pending-slots",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
    )
    attestation = _harness(tmp_path).run(
        certification_id="pending-slots",
        subject=_subject(),
        fixture=_fixture(),
        cases=(case,),
    ).attestation
    forged = copy.deepcopy(attestation)
    forged["live_canary_receipts"][0] = {
        "slot": "live-canary-1",
        "status": "clean",
        "receipt": {"fabricated": True},
    }

    with pytest.raises(TrailCertificationError, match="cannot fabricate a live canary"):
        validate_certification_attestation_data(forged)


def test_exact_operability_upper_bound_has_the_memo_corrected_threshold() -> None:
    assert one_sided_95_upper_bound(0, 59) < 0.05
    assert one_sided_95_upper_bound(0, 58) >= 0.05
    assert 0.05 < one_sided_95_upper_bound(1, 59) < 0.1


def test_case_matrix_covers_all_trail_plants_and_fault_classes() -> None:
    matrix = load_case_matrix(FIXTURES / "case-matrix.v1.yaml")

    assert case_matrix_coverage_gaps(matrix) == {}
    assert {case["fault"] for case in matrix} >= FAULT_CLASSES


def test_attestation_schema_rejects_unknown_damage_event_codes(tmp_path: Path) -> None:
    case = _case(
        case_id="schema-damage",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
    )
    attestation = _harness(tmp_path).run(
        certification_id="schema-damage",
        subject=_subject(),
        fixture=_fixture(),
        cases=(case,),
    ).attestation
    malformed = copy.deepcopy(attestation)
    malformed["damage_event_codes"] = ["invented-damage-code"]

    with pytest.raises(TrailCertificationError, match="schema violation"):
        validate_certification_attestation_data(malformed)


def _probe_executor(adapter: str, escape: bool):
    """Executor subclass that fires one synthetic command probe at the hermetic guard."""

    class _ProbeExecutor(certification_module.TrailExecutor):
        def begin(self, **kwargs):
            cwd = self.project_root / "outside-the-fixture" if escape else self.project_root
            self.command_runner({"adapter": adapter}, cwd)
            raise AssertionError("the hermetic guard did not refuse the probe")

    return _ProbeExecutor


def test_hermetic_guard_refuses_command_cwd_escape(tmp_path: Path, monkeypatch) -> None:
    case = _case(
        case_id="hermetic-escape",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
    )
    monkeypatch.setattr(certification_module, "TrailExecutor", _probe_executor("shell", escape=True))

    with pytest.raises(HermeticCertificationError, match="escaped its fixture root"):
        _harness(tmp_path).run(
            certification_id="hermetic-escape",
            subject=_subject(),
            fixture=_fixture(),
            cases=(case,),
        )


def test_hermetic_guard_refuses_unknown_command_adapter(tmp_path: Path, monkeypatch) -> None:
    case = _case(
        case_id="hermetic-adapter",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
    )
    monkeypatch.setattr(
        certification_module, "TrailExecutor", _probe_executor("live-network", escape=False)
    )

    with pytest.raises(HermeticCertificationError, match="unknown adapter"):
        _harness(tmp_path).run(
            certification_id="hermetic-adapter",
            subject=_subject(),
            fixture=_fixture(),
            cases=(case,),
        )


def test_missed_stop_mismatch_derives_the_missed_stop_damage_event(tmp_path: Path) -> None:
    case = _case(
        case_id="missed-stop-derived",
        transition="refused",
        outcome="stop_parked",
        exit_class=ExitClass.STOP_PARKED,
        state="parked",
        stop_code="STOP-other",
    )

    attestation = _harness(tmp_path).run(
        certification_id="missed-stop-derived",
        subject=_subject(),
        fixture=_fixture(),
        cases=(case,),
    ).attestation

    assert attestation["cases"][0]["passed"] is False
    assert attestation["cases"][0]["observed"]["stop_code"] == "STOP-unknown"
    assert attestation["damage_event_codes"] == ["missed-stop"]
    assert attestation["status"]["demote"] is True
    assert attestation["status"]["harness_passed"] is False


def test_attestation_output_is_immutable_across_reruns(tmp_path: Path) -> None:
    case = _case(
        case_id="immutable",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
    )
    harness = _harness(tmp_path)
    harness.run(
        certification_id="immutable", subject=_subject(), fixture=_fixture(), cases=(case,)
    )

    with pytest.raises(TrailCertificationError, match="already exists"):
        harness.run(
            certification_id="immutable", subject=_subject(), fixture=_fixture(), cases=(case,)
        )


def test_trail_hash_drift_between_p3_and_submitted_spec_is_refused(tmp_path: Path, monkeypatch) -> None:
    case = _case(
        case_id="hash-drift",
        transition="accepted",
        outcome="terminal",
        exit_class=ExitClass.OK,
        state="terminal",
    )
    monkeypatch.setattr(certification_module, "compute_trail_hash", lambda spec: "0" * 64)

    with pytest.raises(TrailCertificationError, match="differs from the submitted TrailSpec"):
        _harness(tmp_path).run(
            certification_id="hash-drift",
            subject=_subject(),
            fixture=_fixture(),
            cases=(case,),
        )


def test_binary_damage_event_codes_are_complete() -> None:
    assert {
        "merged-regression",
        "unauthorized-rail-file-edit",
        "self-review-accepted",
        "false-closure",
        "missed-stop",
        "stale-generation-action",
        "review-merge-bypass",
        "replayed-side-effect",
        "wrong-head-rerun",
    } == BINARY_DAMAGE_EVENT_CODES
