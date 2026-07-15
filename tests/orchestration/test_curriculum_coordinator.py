"""Contract and failure-mode tests for the curriculum track coordinator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration import curriculum_coordinator as coordinator

BUNDLE_FILES = ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    manifest = {
        "levels": {
            "folk": {"type": "track", "modules": ["alpha", "bravo", "charlie", "delta"]},
            "bio": {
                "type": "track",
                "modules": ["echo", "foxtrot", "andrii-malyshko"],
            },
        }
    }
    path = root / "curriculum/l2-uk-en/curriculum.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    for track in manifest["levels"]:
        (root / "curriculum/l2-uk-en" / track).mkdir(parents=True)
    return root


def _build(repo: Path, track: str, slug: str, count: int = 4) -> None:
    directory = repo / "curriculum/l2-uk-en" / track / slug
    directory.mkdir(parents=True, exist_ok=True)
    for filename in BUNDLE_FILES[:count]:
        (directory / filename).write_text("fixture\n", encoding="utf-8")


def _evaluator(states: dict[str, str] | None = None):
    configured = states or {}

    def evaluate(_track: str, slug: str) -> dict[str, Any]:
        state = configured.get(slug, "current")
        return {
            "module_state": "built" if state in {"stale", "current"} else state,
            "preparation_state": state if state in {"stale", "current"} else "missing",
            "state": "built-current" if state == "current" else "preparation-required",
            "next_action": "certify" if state == "current" else "prepare",
            "preparation_identity": (slug[0] * 64) if state in {"stale", "current"} else None,
        }

    return evaluate


def _health(*, codex: str = "cool", claude: str = "cool", stale: bool = False):
    def probe() -> dict[str, Any]:
        def lane(status: str) -> dict[str, Any]:
            return {
                "status": status,
                "health": {"healthy": True},
                "codexbar": {"stale": stale},
            }

        return {
            "generated_at": "2026-07-14T12:00:00Z",
            "diagnostics": {"stale": stale},
            "agents": {
                "codex": lane(codex),
                "claude": lane(claude),
                "gemini": lane("cool"),
            },
        }

    return probe


def _start(
    repo: Path,
    runtime: Path,
    *,
    track: str = "folk",
    owner: str = "sol",
    scope: str = "all",
    **kwargs: Any,
) -> tuple[Path, dict[str, Any]]:
    return coordinator.start_run(
        track,
        owner=owner,
        scope=scope,
        repo_root=repo,
        runtime_root=runtime,
        readiness_evaluator=_evaluator(kwargs.pop("states", None)),
        **kwargs,
    )


def _acquire(
    repo: Path,
    runtime: Path,
    run_id: str,
    *,
    health_probe=None,
    states: dict[str, str] | None = None,
):
    return coordinator.acquire_next(
        run_id,
        owner="sol",
        repo_root=repo,
        runtime_root=runtime,
        health_probe=health_probe or _health(),
        readiness_evaluator=_evaluator(states),
    )


def _no_change(repo: Path, runtime: Path, run_id: str, evidence: str = "pbr:v1"):
    ledger = json.loads((runtime / "runs" / f"{run_id}.json").read_text(encoding="utf-8"))
    slug = coordinator.derive_state(ledger)["current_module"]
    if slug is None:
        slug = next(
            event["details"]["slug"]
            for event in reversed(ledger["history"])
            if event["event"] == "MODULE_FINISHED"
        )
    return coordinator.record_module(
        run_id,
        owner="sol",
        slug=slug,
        disposition="no-change",
        integration={"evidence": evidence},
        repo_root=repo,
        runtime_root=runtime,
    )


def test_versioned_config_and_schemas_are_strict() -> None:
    config = coordinator.load_config()
    assert config["config_version"] == "curriculum-coordinator.v1"
    assert [group["id"] for group in config["health"]["capability_groups"]] == [
        "curriculum-build",
        "independent-review",
    ]
    invalid = dict(config)
    invalid["unexpected"] = True
    with pytest.raises(coordinator.CoordinatorError, match="Additional properties"):
        coordinator._validate(invalid, coordinator.CONFIG_SCHEMA_PATH, "fixture")


def test_manifest_selectors_ranges_and_prerequisites(repo: Path, tmp_path: Path) -> None:
    _build(repo, "folk", "alpha")
    _build(repo, "folk", "bravo", count=2)
    _build(repo, "folk", "charlie")

    _path, ranged = _start(
        repo,
        tmp_path / "range",
        start="2",
        end="delta",
        wave_size=2,
    )
    assert [item["slug"] for item in ranged["queue"]] == ["bravo", "charlie", "delta"]
    assert [item["manifest_index"] for item in ranged["queue"]] == [1, 2, 3]
    assert [item["wave"] for item in ranged["queue"]] == [1, 1, 2]
    assert [item["prerequisites"] for item in ranged["queue"]] == [[], ["bravo"], ["charlie"]]
    assert [item["initial_module_state"] for item in ranged["queue"]] == [
        "partial",
        "built",
        "unbuilt",
    ]

    _path, built = _start(repo, tmp_path / "built", scope="built")
    assert [item["slug"] for item in built["queue"]] == ["alpha", "charlie"]
    _path, unbuilt = _start(repo, tmp_path / "unbuilt", scope="unbuilt")
    assert [item["slug"] for item in unbuilt["queue"]] == ["delta"]
    _path, stale = _start(
        repo,
        tmp_path / "stale",
        scope="stale",
        states={"alpha": "stale", "bravo": "current", "charlie": "stale", "delta": "current"},
    )
    assert [item["slug"] for item in stale["queue"]] == ["alpha", "charlie"]
    _path, one = _start(repo, tmp_path / "one", scope="one", module="bravo")
    assert [item["slug"] for item in one["queue"]] == ["bravo"]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"scope": "one", "module": "ghost"}, "active --module"),
        ({"start": "delta", "end": "alpha"}, "start occurs after"),
        ({"start": "0"}, "outside"),
        ({"scope": "all", "module": "alpha"}, "only valid"),
        ({"wave_size": 0}, "wave size"),
    ],
)
def test_invalid_selectors_fail_closed(
    repo: Path,
    tmp_path: Path,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(coordinator.CoordinatorError, match=message):
        _start(repo, tmp_path / message.replace(" ", "-"), **kwargs)


def test_duplicate_start_is_idempotent_and_foreign_owner_is_blocked(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    path, first = _start(repo, runtime, scope="one", module="alpha")
    same_path, second = _start(repo, runtime, scope="one", module="alpha")
    assert same_path == path
    assert second == first
    assert [event["event"] for event in second["history"]] == ["RUN_STARTED"]

    with pytest.raises(coordinator.CoordinatorError, match="lease belongs"):
        _start(repo, runtime, owner="terra", scope="one", module="bravo")


def test_health_pause_resume_serial_waves_and_no_change(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, wave_size=3)
    run_id = ledger["run_id"]

    polls = 0

    def changing_unhealthy_probe() -> dict[str, Any]:
        nonlocal polls
        polls += 1
        snapshot = _health(codex="near_cap")()
        snapshot["generated_at"] = f"2026-07-14T12:00:0{polls}Z"
        return snapshot

    _path, paused, item = _acquire(
        repo, runtime, run_id, health_probe=changing_unhealthy_probe
    )
    assert item is None
    assert coordinator.compact_status(paused)["status"] == "paused"
    pause_count = len(paused["history"])
    _path, retried, item = _acquire(
        repo, runtime, run_id, health_probe=changing_unhealthy_probe
    )
    assert item is None
    assert len(retried["history"]) == pause_count

    for expected in ("alpha", "bravo", "charlie"):
        _path, active, item = _acquire(repo, runtime, run_id)
        assert item and item["slug"] == expected
        _path, duplicate, same_item = _acquire(repo, runtime, run_id)
        assert same_item == item
        assert len(duplicate["history"]) == len(active["history"])
        _no_change(repo, runtime, run_id, evidence=f"pbr:{expected}")

    after_wave = json.loads((_path).read_text(encoding="utf-8"))
    assert after_wave["history"][-1]["event"] == "WAVE_COMPLETED"
    assert after_wave["history"][-1]["details"] == {"wave": 1}

    _path, second_pause, item = _acquire(repo, runtime, run_id, health_probe=_health(stale=True))
    assert item is None
    assert coordinator.compact_status(second_pause)["next_module"] == "delta"
    _path, _active, item = _acquire(repo, runtime, run_id)
    assert item and item["slug"] == "delta"
    current = json.loads(_path.read_text(encoding="utf-8"))
    assert any(
        event["event"] == "RUN_RESUMED"
        and event["details"]["reason"] == "wave-health-restored"
        for event in current["history"]
    )
    _no_change(repo, runtime, run_id, evidence="pbr:delta")
    final = json.loads(_path.read_text(encoding="utf-8"))
    assert [event["event"] for event in final["history"]][-3:] == [
        "MODULE_FINISHED",
        "WAVE_COMPLETED",
        "RUN_COMPLETED",
    ]
    assert coordinator.compact_status(final)["status"] == "complete"
    assert not (runtime / "leases/tracks/folk.json").exists()


def test_global_mutation_lease_blocks_cross_track_work(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, folk = _start(repo, runtime, scope="one", module="alpha")
    _path, bio = _start(repo, runtime, track="bio", scope="one", module="echo")
    _acquire(repo, runtime, folk["run_id"])
    with pytest.raises(coordinator.CoordinatorError, match="lease belongs"):
        _acquire(repo, runtime, bio["run_id"])

    coordinator.record_module(
        folk["run_id"],
        owner="sol",
        slug="alpha",
        disposition="blocked",
        integration={"evidence": "blocker:source-rights"},
        repo_root=repo,
        runtime_root=runtime,
    )
    _path, retried, item = _acquire(repo, runtime, folk["run_id"])
    assert item and item["slug"] == "alpha"
    assert coordinator.derive_state(retried)["modules"]["alpha"] == "active"
    coordinator.record_module(
        folk["run_id"],
        owner="sol",
        slug="alpha",
        disposition="blocked",
        integration={"evidence": "blocker:source-rights"},
        repo_root=repo,
        runtime_root=runtime,
    )
    _path, _ledger, item = _acquire(repo, runtime, bio["run_id"])
    assert item and item["slug"] == "echo"


def test_expired_lease_requires_exact_resume_and_is_never_stolen(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    lease_path = runtime / "leases/tracks/folk.json"
    lease = json.loads(lease_path.read_text(encoding="utf-8"))
    lease["expires_at"] = "2000-01-01T00:00:00+00:00"
    lease_path.write_text(json.dumps(lease), encoding="utf-8")

    with pytest.raises(coordinator.CoordinatorError, match="expired"):
        _acquire(repo, runtime, ledger["run_id"])
    with pytest.raises(coordinator.CoordinatorError, match="stale lease belongs"):
        _start(repo, runtime, owner="terra", scope="one", module="bravo")

    coordinator.resume_run(
        ledger["run_id"], owner="sol", repo_root=repo, runtime_root=runtime
    )
    _path, _ledger, item = _acquire(repo, runtime, ledger["run_id"])
    assert item and item["slug"] == "alpha"


def test_acquired_module_with_expired_lease_requires_resume(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    run_id = ledger["run_id"]
    _acquire(repo, runtime, run_id)
    global_path = runtime / "leases/global/mutation.json"
    lease = json.loads(global_path.read_text(encoding="utf-8"))
    lease["expires_at"] = "2000-01-01T00:00:00+00:00"
    global_path.write_text(json.dumps(lease), encoding="utf-8")

    with pytest.raises(coordinator.CoordinatorError, match="expired"):
        _acquire(repo, runtime, run_id)
    coordinator.resume_run(run_id, owner="sol", repo_root=repo, runtime_root=runtime)
    _path, _ledger, item = _acquire(repo, runtime, run_id)
    assert item and item["slug"] == "alpha"


def test_finish_retry_heals_cleanup_after_crash(repo: Path, tmp_path: Path, monkeypatch) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    run_id = ledger["run_id"]
    _acquire(repo, runtime, run_id)
    real_release = coordinator._release_owned_lease
    calls = 0

    def crash_once(path: Path, owned_run_id: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("simulated crash after ledger commit")
        real_release(path, owned_run_id)

    monkeypatch.setattr(coordinator, "_release_owned_lease", crash_once)
    with pytest.raises(OSError, match="simulated crash"):
        _no_change(repo, runtime, run_id)
    monkeypatch.setattr(coordinator, "_release_owned_lease", real_release)
    path, healed = _no_change(repo, runtime, run_id)
    assert sum(event["event"] == "MODULE_FINISHED" for event in healed["history"]) == 1
    assert coordinator.compact_status(healed)["status"] == "complete"
    assert not (runtime / "leases/global/mutation.json").exists()
    assert not (runtime / "leases/modules/folk--alpha.json").exists()
    same_path, duplicate = _start(repo, runtime, scope="one", module="alpha")
    assert same_path == path
    assert duplicate == healed


def test_conflicting_replay_and_incomplete_repair_identity_fail(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    run_id = ledger["run_id"]
    _acquire(repo, runtime, run_id)
    with pytest.raises(coordinator.CoordinatorError, match="PR number"):
        coordinator.record_module(
            run_id,
            owner="sol",
            slug="alpha",
            disposition="complete",
            integration={"issue": 5158, "evidence": "repair:test"},
            repo_root=repo,
            runtime_root=runtime,
        )
    _no_change(repo, runtime, run_id, evidence="pbr:pass")
    with pytest.raises(coordinator.CoordinatorError, match="conflicting replay"):
        _no_change(repo, runtime, run_id, evidence="pbr:different")


def test_completed_repair_requires_full_merge_and_cleanup_identity(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    run_id = ledger["run_id"]
    _acquire(repo, runtime, run_id)
    _path, complete = coordinator.record_module(
        run_id,
        owner="sol",
        slug="alpha",
        disposition="complete",
        integration={
            "issue": 6001,
            "worktree": ".worktrees/dispatch/codex/6001-alpha",
            "branch": "codex/6001-alpha",
            "pr": 6002,
            "merge_sha": "a" * 40,
            "cleanup": "complete",
            "evidence": "review:claude-opus",
        },
        repo_root=repo,
        runtime_root=runtime,
    )
    assert coordinator.compact_status(complete)["counts"]["complete"] == 1


def test_completed_repair_rejects_misaligned_branch_identity(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    _acquire(repo, runtime, ledger["run_id"])
    with pytest.raises(coordinator.CoordinatorError, match="align"):
        coordinator.record_module(
            ledger["run_id"],
            owner="sol",
            slug="alpha",
            disposition="complete",
            integration={
                "issue": 6001,
                "worktree": ".worktrees/dispatch/codex/6001-alpha",
                "branch": "codex/different",
                "pr": 6002,
                "merge_sha": "a" * 40,
                "cleanup": "complete",
                "evidence": "review:claude-opus",
            },
            repo_root=repo,
            runtime_root=runtime,
        )


def test_ledger_tampering_is_detected_by_replay_validation(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    path, ledger = _start(repo, runtime, scope="one", module="alpha")
    ledger["history"][0]["details"]["request_sha256"] = "0" * 64
    path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(coordinator.CoordinatorError, match="identity does not match"):
        coordinator.status_run(
            ledger["run_id"], owner="sol", repo_root=repo, runtime_root=runtime
        )


def test_manifest_drift_invalidates_the_durable_queue(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    manifest_path = repo / "curriculum/l2-uk-en/curriculum.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["levels"]["folk"]["modules"].append("golf")
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    status = coordinator.status_run(
        ledger["run_id"], owner="sol", repo_root=repo, runtime_root=runtime
    )
    assert status["manifest_current"] is False
    with pytest.raises(coordinator.CoordinatorError, match="manifest changed"):
        coordinator.resume_run(
            ledger["run_id"], owner="sol", repo_root=repo, runtime_root=runtime
        )
    with pytest.raises(coordinator.CoordinatorError, match="lease belongs"):
        _start(repo, runtime, scope="one", module="bravo")
    _path, abandoned = coordinator.adjudicate_run(
        ledger["run_id"],
        owner="sol",
        reason="manifest authority changed while the run was inactive",
        repo_root=repo,
        runtime_root=runtime,
    )
    assert coordinator.compact_status(abandoned)["status"] == "abandoned"
    assert abandoned["history"][-1]["event"] == "RUN_ABANDONED"
    _path, replacement = _start(repo, runtime, scope="one", module="bravo")
    assert replacement["run_id"] != ledger["run_id"]


def test_current_manifest_run_cannot_be_abandoned(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    with pytest.raises(coordinator.CoordinatorError, match="exact-run resume"):
        coordinator.adjudicate_run(
            ledger["run_id"],
            owner="sol",
            reason="unsafe cancellation attempt",
            repo_root=repo,
            runtime_root=runtime,
        )


def test_adjudication_retry_heals_leases_after_crash(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    _acquire(repo, runtime, ledger["run_id"])
    manifest_path = repo / "curriculum/l2-uk-en/curriculum.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["levels"]["folk"]["modules"].append("golf")
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    real_release = coordinator._release_owned_lease
    calls = 0

    def crash_once(path: Path, owned_run_id: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("simulated crash after abandonment commit")
        real_release(path, owned_run_id)

    monkeypatch.setattr(coordinator, "_release_owned_lease", crash_once)
    with pytest.raises(OSError, match="simulated crash"):
        coordinator.adjudicate_run(
            ledger["run_id"],
            owner="sol",
            reason="manifest changed during an active module",
            repo_root=repo,
            runtime_root=runtime,
        )
    monkeypatch.setattr(coordinator, "_release_owned_lease", real_release)
    _path, healed = coordinator.adjudicate_run(
        ledger["run_id"],
        owner="sol",
        reason="exact retry after crash",
        repo_root=repo,
        runtime_root=runtime,
    )
    assert coordinator.compact_status(healed)["status"] == "abandoned"
    assert not (runtime / "leases/tracks/folk.json").exists()
    assert not (runtime / "leases/global/mutation.json").exists()
    assert not (runtime / "leases/modules/folk--alpha.json").exists()
    _path, replacement = _start(repo, runtime, scope="one", module="bravo")
    assert replacement["run_id"] != ledger["run_id"]


def test_blocked_integration_identity_is_consistent(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    _acquire(repo, runtime, ledger["run_id"])
    with pytest.raises(coordinator.CoordinatorError, match="must not claim"):
        coordinator.record_module(
            ledger["run_id"],
            owner="sol",
            slug="alpha",
            disposition="blocked",
            integration={"issue": 5158, "evidence": "blocker:test"},
            repo_root=repo,
            runtime_root=runtime,
        )
    _path, blocked = coordinator.record_module(
        ledger["run_id"],
        owner="sol",
        slug="alpha",
        disposition="blocked",
        integration={
            "issue": 5158,
            "worktree": ".worktrees/dispatch/codex/5158-track-coordinator",
            "branch": "codex/5158-track-coordinator",
            "cleanup": "pending",
            "evidence": "blocker:test",
        },
        repo_root=repo,
        runtime_root=runtime,
    )
    assert coordinator.compact_status(blocked)["status"] == "blocked"


def test_partial_module_lease_claim_rolls_back_global_lease(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    module_lease = runtime / "leases/modules/folk--alpha.json"
    coordinator._atomic_write_json(
        module_lease,
        coordinator._lease_document(
            run_id="clc-" + "f" * 24,
            owner="foreign",
            lease_seconds=1800,
            track="folk",
            slug="alpha",
        ),
    )
    with pytest.raises(coordinator.CoordinatorError, match="lease belongs"):
        _acquire(repo, runtime, ledger["run_id"])
    assert not (runtime / "leases/global/mutation.json").exists()


def test_recomputed_but_impossible_event_is_rejected(repo: Path, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    path, ledger = _start(repo, runtime, scope="one", module="alpha")
    details = {"module_count": 1}
    ledger["history"].append(
        {
            "sequence": 2,
            "event_id": coordinator._event_id("RUN_COMPLETED", details),
            "event": "RUN_COMPLETED",
            "at": "2026-07-14T12:00:00+00:00",
            "details": details,
        }
    )
    path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(coordinator.CoordinatorError, match="completion is premature"):
        coordinator.status_run(
            ledger["run_id"], owner="sol", repo_root=repo, runtime_root=runtime
        )


def test_one_line_cli_start_and_status_use_compact_contract(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runtime = repo / "batch_state/curriculum-lifecycle"
    assert (
        coordinator.main(
            [
                "--repo-root",
                str(repo),
                "start",
                "--track",
                "folk",
                "--owner",
                "sol",
                "--scope",
                "one",
                "--module",
                "alpha",
                "--terminal-goal",
                "merge",
            ]
        )
        == 0
    )
    started = json.loads(capsys.readouterr().out)
    run_id = started["status"]["run_id"]
    assert started["status"]["next_module"] == "alpha"
    assert Path(started["ledger"]).parent == runtime / "runs"
    assert (
        coordinator.main(
            [
                "--repo-root",
                str(repo),
                "status",
                "--run-id",
                run_id,
                "--owner",
                "sol",
            ]
        )
        == 0
    )
    status = json.loads(capsys.readouterr().out)
    assert status["event_count"] == 1


def test_bio_371_deploy_goal_rejects_pending_and_certification_only_track_ledger(
    repo: Path, tmp_path: Path
) -> None:
    incident = {
        "track_run_id": "0b4b92fcc5ca4653a33fb89b68c7cfc8",
        "coordinator_run_id": "clc-d571995205b4c2773fc9c2a1",
        "pr": 5255,
        "merge_sha": "ba5e43d42922d6c08ec3f4b5e0f558e18ac74041",
    }
    runtime = tmp_path / "runtime"
    _path, ledger = _start(
        repo,
        runtime,
        track="bio",
        scope="one",
        module="andrii-malyshko",
        terminal_goal="deploy",
    )
    run_id = ledger["run_id"]
    _acquire(repo, runtime, run_id)
    track_run_id = incident["track_run_id"]
    track_path = tmp_path / "track-completion.json"
    track_ledger = {
        "target": {"selector": "bio/andrii-malyshko"},
        "run": {"run_id": track_run_id, "status": "active"},
        "terminal_goal": "deploy",
        "state": "PBR_PASS_QG_PENDING",
        "publication": {
            "pr": incident["pr"],
            "merge_sha": incident["merge_sha"],
        },
        "certification_evidence": [],
    }
    track_path.write_text(json.dumps(track_ledger), encoding="utf-8")
    integration = {
        "evidence": f"BIO-371 coordinator:{incident['coordinator_run_id']}",
        "track_ledger": str(track_path),
        "track_run_id": track_run_id,
    }
    with pytest.raises(coordinator.CoordinatorError, match="not satisfied"):
        coordinator.record_module(
            run_id,
            owner="sol",
            slug="andrii-malyshko",
            disposition="no-change",
            integration=integration,
            repo_root=repo,
            runtime_root=runtime,
        )
    track_ledger["run"]["status"] = "completed"
    track_ledger["state"] = "COMPLETE"
    track_path.write_text(json.dumps(track_ledger), encoding="utf-8")
    with pytest.raises(coordinator.CoordinatorError, match="deployment receipt"):
        coordinator.record_module(
            run_id,
            owner="sol",
            slug="andrii-malyshko",
            disposition="no-change",
            integration=integration,
            repo_root=repo,
            runtime_root=runtime,
        )
    track_ledger["certification_evidence"] = [
        {"value": {"kind": "deployment"}}
    ]
    track_path.write_text(json.dumps(track_ledger), encoding="utf-8")
    _path, complete = coordinator.record_module(
        run_id,
        owner="sol",
        slug="andrii-malyshko",
        disposition="no-change",
        integration=integration,
        repo_root=repo,
        runtime_root=runtime,
    )
    _path, replayed = coordinator.record_module(
        run_id,
        owner="sol",
        slug="andrii-malyshko",
        disposition="no-change",
        integration=integration,
        repo_root=repo,
        runtime_root=runtime,
    )
    assert coordinator.compact_status(complete)["terminal_satisfied"] is True
    assert replayed == complete


def test_pages_deploy_installs_audit_import_dependencies() -> None:
    workflow = (coordinator.PROJECT_ROOT / ".github/workflows/deploy-pages.yml").read_text(
        encoding="utf-8"
    )
    assert "PyYAML==6.0.3 jsonschema==4.26.0" in workflow


def test_legacy_completed_run_migration_reopens_unproven_module(
    repo: Path, tmp_path: Path
) -> None:
    runtime = tmp_path / "runtime"
    _path, ledger = _start(repo, runtime, scope="one", module="alpha")
    run_id = ledger["run_id"]
    _acquire(repo, runtime, run_id)
    _path, legacy_complete = _no_change(repo, runtime, run_id)
    assert coordinator.compact_status(legacy_complete)["status"] == "complete"

    _path, migrated = coordinator.migrate_terminal_goal(
        run_id,
        owner="sol",
        terminal_goal="deploy",
        repo_root=repo,
        runtime_root=runtime,
    )
    status = coordinator.compact_status(migrated)
    assert status["status"] == "blocked"
    assert status["terminal_goal"] == "deploy"
    assert status["terminal_satisfied"] is False
    _path, resumed = coordinator.resume_run(
        run_id,
        owner="sol",
        repo_root=repo,
        runtime_root=runtime,
    )
    assert coordinator.compact_status(resumed)["status"] == "blocked"
    _path, _ledger, acquired = _acquire(repo, runtime, run_id)
    assert acquired is not None and acquired["slug"] == "alpha"
    assert "queue" not in status
