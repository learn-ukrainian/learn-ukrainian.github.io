"""Scoring manifests, independence, the seeded-attempt identity check in record.py, sets and the confirmation lock (#8430 R3-A)."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest
import yaml

from scripts.review import record, second_seat
from scripts.review.prompts.eligibility import pin_refusals
from scripts.review.prompts.render import PinIneligibleError, render_prompt
from scripts.review.seeds import manifest as sm
from tests.review.seeds.fixtures import (
    GOLD_FAMILY,
    GOLD_MODEL,
    PLANTER_FAMILY,
    PLANTER_MODEL,
    Env,
    clean_lesson,
    linguistic_seed,
    mechanical_seed,
)
from tests.review.test_prompts import _repoint, _setup_lesson_fixture
from tests.review.test_record import LEVEL as RECORD_LEVEL
from tests.review.test_record import SLUG as RECORD_SLUG
from tests.review.test_record import World

pytestmark = pytest.mark.reads_content


@pytest.fixture
def env(tmp_path: Path) -> Env:
    return Env(tmp_path)


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    return World(tmp_path, monkeypatch)


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


# --- the resolver facts the fixtures rely on ----------------------------------------------------------------------------


def test_the_fixture_models_resolve_to_the_families_the_fixtures_record() -> None:
    assert second_seat.concrete_family(PLANTER_MODEL, what="planter") == PLANTER_FAMILY
    assert second_seat.concrete_family(GOLD_MODEL, what="gold") == GOLD_FAMILY


# --- scoring manifests and clean records ------------------------------------------------------------------------------


def test_a_scoring_manifest_round_trips_and_is_private(env: Env) -> None:
    seed = linguistic_seed("seed-a1")
    path = sm.write_scoring_manifest(seed, env.root)
    assert path == env.root / "batch_state" / "review-measurement" / "seeds" / "seed-a1.yaml"
    assert mode(path) == 0o600 and mode(path.parent) == 0o700
    assert sm.load_seed("seed-a1", env.root) == seed
    document = yaml.safe_load(path.read_bytes())
    assert document["scoring_manifest"] == 1 and document["identities"]["gold_verdict"] == "pass"
    assert not list(path.parent.glob(".*")), "no temporary file is left behind"


def test_a_clean_record_round_trips_and_is_private(env: Env) -> None:
    clean = clean_lesson("clean-a1")
    path = sm.write_clean_record(clean, env.root)
    assert mode(path) == 0o600 and sm.load_clean("clean-a1", env.root) == clean


def test_a_record_is_immutable_once_written(env: Env) -> None:
    seed = mechanical_seed("seed-a1")
    sm.write_scoring_manifest(seed, env.root)
    sm.write_scoring_manifest(seed, env.root)  # the same content again is a no-op
    with pytest.raises(sm.MeasurementError) as caught:
        sm.write_scoring_manifest(mechanical_seed("seed-a1", semantic_defect="another defect"), env.root)
    assert caught.value.code == sm.MANIFEST_EXISTS


@pytest.mark.parametrize(
    "seed",
    [
        mechanical_seed("not-a-seed-id"),
        mechanical_seed("seed-a1", dimension="not_a_dimension"),
        mechanical_seed("seed-a1", dimension="language", sub_dimension=None),
        mechanical_seed("seed-a1", dimension="language", sub_dimension="no_such_sub"),
        mechanical_seed("seed-a1", sub_dimension="calque"),  # only a language seed has one
        mechanical_seed("seed-a1", source="invented"),
        mechanical_seed("seed-a1", n=0),
        mechanical_seed("seed-a1", target_spans=[]),
        mechanical_seed("seed-a1", semantic_defect=" "),
        mechanical_seed("seed-a1", planter_model="script"),  # a mechanical seed has no planter
        mechanical_seed("seed-a1", gold_verdict="pass"),
        linguistic_seed("seed-a1", gold_checker_family=None),
        linguistic_seed("seed-a1", planter_family=None),
        linguistic_seed("seed-a1", gold_verdict="not_applicable"),
        linguistic_seed("seed-a1", gold_verdict="maybe"),
    ],
)
def test_an_unusable_scoring_manifest_is_refused_when_written(env: Env, seed: sm.Seed) -> None:
    with pytest.raises(sm.MeasurementError):
        sm.write_scoring_manifest(seed, env.root)
    assert not (env.root / "batch_state" / "review-measurement" / "seeds").exists()


def test_a_missing_or_wrong_record_is_refused_when_read(env: Env) -> None:
    with pytest.raises(sm.MeasurementError) as caught:
        sm.load_seed("seed-none", env.root)
    assert caught.value.code == sm.MANIFEST_MISSING
    sm.write_scoring_manifest(mechanical_seed("seed-a1"), env.root)
    directory = env.root / "batch_state" / "review-measurement" / "seeds"
    (directory / "seed-b1.yaml").write_bytes((directory / "seed-a1.yaml").read_bytes())
    with pytest.raises(sm.MeasurementError, match="holds the manifest of seed-a1"):
        sm.load_seed("seed-b1", env.root)
    with pytest.raises(sm.MeasurementError):
        sm.load_seed("../etc/passwd", env.root)


def test_the_required_dimensions_are_the_taxonomys_non_optional_lesson_checks() -> None:
    every, required = sm.lesson_dimensions()
    assert required == ["job", "language", "learner_fit", "activity", "evidence_use", "english", "fact", "recap"]
    assert {"evidence_gap", "plan_defect", "engine_or_gate"} <= set(every) - set(required)


# --- independence -------------------------------------------------------------------------------------------------------


def violations(seed: sm.Seed, *, writer: str = "anthropic", reviewer: str = "openai") -> list[str]:
    return sm.independence_violations(seed, writer_family=writer, reviewer_family=reviewer)


def test_an_independent_linguistic_pair_breaks_no_rule() -> None:
    assert violations(linguistic_seed("seed-a1")) == []  # writer anthropic, planter google, gold xai, reviewer openai


@pytest.mark.parametrize(
    ("seed", "writer", "reviewer", "expected"),
    [
        (linguistic_seed("seed-a1"), "openai", "openai", [sm.REVIEWER_IS_WRITER]),
        (linguistic_seed("seed-a1"), "google", "openai", [sm.PLANTER_IS_WRITER]),
        (linguistic_seed("seed-a1"), "anthropic", "google", [sm.PLANTER_IS_REVIEWER]),
        (
            linguistic_seed("seed-a1", gold_checker_family="google"),
            "anthropic",
            "openai",
            [sm.GOLD_CHECKER_IS_PLANTER],
        ),
        (linguistic_seed("seed-a1"), "anthropic", "xai", [sm.GOLD_CHECKER_IS_REVIEWER]),
        (linguistic_seed("seed-a1", gold_verdict="fail"), "anthropic", "openai", [sm.GOLD_CHECK_NOT_PASSED]),
        # a mechanical seed is made by a script: only the writer/reviewer rule applies
        (mechanical_seed("seed-a1"), "anthropic", "anthropic", [sm.REVIEWER_IS_WRITER]),
        (mechanical_seed("seed-a1"), "anthropic", "google", []),
    ],
)
def test_each_independence_rule_has_its_named_code(seed, writer, reviewer, expected) -> None:
    assert violations(seed, writer=writer, reviewer=reviewer) == expected


def test_the_adjudicator_is_neither_the_writers_nor_the_reviewers_family() -> None:
    kwargs = {"writer_family": "anthropic", "reviewer_family": "openai"}
    assert sm.adjudicator_violations(adjudicator_family="google", **kwargs) == []
    assert sm.adjudicator_violations(adjudicator_family="anthropic", **kwargs) == [sm.ADJUDICATOR_IS_WRITER]
    assert sm.adjudicator_violations(adjudicator_family="openai", **kwargs) == [sm.ADJUDICATOR_IS_REVIEWER]


@pytest.mark.parametrize("writer", ["", "  ", None])
def test_an_unknown_writer_or_reviewer_is_refused_not_defaulted(env: Env, writer) -> None:
    unit = env.add(mechanical_seed("seed-a1"))
    with pytest.raises(sm.MeasurementError) as caught:
        sm.check_attempt_identity(
            unit, target=("a1", "seed-a1-module", 1), writer_family=writer, reviewer_family="openai", repo_root=env.root
        )
    assert caught.value.code == sm.SEED_IDENTITY_UNKNOWN
    with pytest.raises(sm.MeasurementError) as caught:
        sm.check_attempt_identity(
            unit,
            target=("a1", "seed-a1-module", 1),
            writer_family="anthropic",
            reviewer_family=writer,
            repo_root=env.root,
        )
    assert caught.value.code == sm.SEED_IDENTITY_UNKNOWN


def test_a_unit_with_no_record_is_an_unknown_identity(env: Env) -> None:
    for unit in ("seed-ghost", "clean-ghost"):
        with pytest.raises(sm.MeasurementError) as caught:
            sm.check_attempt_identity(
                unit, target=("a1", "m", 1), writer_family="anthropic", reviewer_family="openai", repo_root=env.root
            )
        assert caught.value.code == sm.SEED_IDENTITY_UNKNOWN


def test_a_recorded_family_the_resolver_does_not_confirm_is_a_mismatch(env: Env) -> None:
    unit = env.add(linguistic_seed("seed-a1", planter_family="openai"))  # gemini resolves to google
    with pytest.raises(sm.MeasurementError) as caught:
        sm.check_attempt_identity(
            unit,
            target=("a1", "seed-a1-module", 1),
            writer_family="anthropic",
            reviewer_family="xai",
            repo_root=env.root,
        )
    assert caught.value.code == sm.SEED_IDENTITY_MISMATCH
    unit = env.add(linguistic_seed("seed-b1", planter_model="a-model-nobody-resolves", planter_family="x"))
    with pytest.raises(sm.MeasurementError) as caught:
        sm.check_attempt_identity(
            unit,
            target=("a1", "seed-b1-module", 1),
            writer_family="anthropic",
            reviewer_family="openai",
            repo_root=env.root,
        )
    assert caught.value.code == sm.SEED_IDENTITY_UNKNOWN


def test_the_recorded_writer_and_target_must_be_the_live_ones(env: Env) -> None:
    unit = env.add(mechanical_seed("seed-a1"))
    args = {"reviewer_family": "openai", "repo_root": env.root}
    with pytest.raises(sm.MeasurementError) as caught:
        sm.check_attempt_identity(unit, target=("a1", "seed-a1-module", 1), writer_family="google", **args)
    assert caught.value.code == sm.SEED_IDENTITY_MISMATCH
    with pytest.raises(sm.MeasurementError) as caught:
        sm.check_attempt_identity(unit, target=("a1", "another-module", 1), writer_family="anthropic", **args)
    assert caught.value.code == sm.SEED_IDENTITY_MISMATCH
    record_ = sm.check_attempt_identity(unit, target=("a1", "seed-a1-module", 1), writer_family="anthropic", **args)
    assert record_.seed_id == "seed-a1"


# --- the seeded-attempt identity check in record.py -----------------------------------------------------------------------
# World: lessons written by gpt-6-astra (family openai); the default review seat is claude-sonnet-5 (anthropic).


def register(world: World, seed: sm.Seed) -> str:
    sm.write_scoring_manifest(seed, world.root)
    return seed.seed_id


def ling(seed_id: str, n: int = 2, **over) -> sm.Seed:
    fields = {"level": RECORD_LEVEL, "slug": RECORD_SLUG, "lesson_n": n, "writer_family": "openai"}
    fields.update(over)
    return linguistic_seed(seed_id, **fields)


def refused(world: World, seed_id: str, *, n: int = 2, task_id: str = "review-claude", **kwargs) -> record.RecordError:
    with pytest.raises(record.RecordError) as caught:
        world.record(world.make_return(n), task_id=task_id, seed_id=seed_id, register=False, **kwargs)
    # nothing is recorded for a refused pair: no attempt, no finding, no seed identity, no budget, no verdict file
    for table in ("attempts", "findings", "seed_identities", "budgets", "settle_items"):
        assert world.db_rows(table) == [], table
    assert not world.verdict_file(n).exists()
    return caught.value


def test_an_independent_seeded_attempt_is_recorded_with_its_identities(world: World) -> None:
    seed = ling("seed-7")  # writer openai, planter google, gold xai, reviewer anthropic
    outcome = world.record(world.make_return(2), seed_id=register(world, seed))
    assert outcome.accepted and outcome.seed_id == "seed-7"
    [attempt] = world.db_rows("attempts")
    assert attempt["seed_id"] == "seed-7" and attempt["writer_family"] == "openai"
    [identity] = world.db_rows("seed_identities")
    assert dict(identity) == seed.identity_row()
    # a second review of the same seed leaves one identity row
    world.record(world.make_return(2), seed_id="seed-7")
    assert len(world.db_rows("attempts")) == 2 and len(world.db_rows("seed_identities")) == 1


@pytest.mark.parametrize(
    ("over", "task", "code"),
    [
        ({"planter_model": "gpt-6-astra", "planter_family": "openai"}, "review-claude", sm.PLANTER_IS_WRITER),
        (
            {"planter_model": "claude-sonnet-5", "planter_family": "anthropic"},
            "review-claude",
            sm.PLANTER_IS_REVIEWER,
        ),
        (
            {"gold_checker_model": PLANTER_MODEL, "gold_checker_family": PLANTER_FAMILY},
            "review-claude",
            sm.GOLD_CHECKER_IS_PLANTER,
        ),
        (
            {"gold_checker_model": "claude-sonnet-5", "gold_checker_family": "anthropic"},
            "review-claude",
            sm.GOLD_CHECKER_IS_REVIEWER,
        ),
        ({"gold_verdict": "fail"}, "review-claude", sm.GOLD_CHECK_NOT_PASSED),
        ({}, "review-writer-seat", sm.REVIEWER_IS_WRITER),
    ],
)
def test_each_violated_independence_rule_is_refused_with_its_named_code(world: World, over, task, code) -> None:
    world.task("review-writer-seat", "codex", "gpt-6-astra")  # a reviewer of the writer's own family
    register(world, ling("seed-7", **over))
    error = refused(world, "seed-7", task_id=task)
    assert error.code == code and code in str(error)


def test_an_unknown_identity_is_refused_and_nothing_is_recorded(world: World) -> None:
    assert refused(world, "seed-nobody-registered").code == sm.SEED_IDENTITY_UNKNOWN
    assert refused(world, "clean-nobody-registered").code == sm.SEED_IDENTITY_UNKNOWN
    register(world, ling("seed-7", planter_family="anthropic"))  # the resolver says google
    assert refused(world, "seed-7").code == sm.SEED_IDENTITY_MISMATCH
    register(world, ling("seed-8", planter_model="a-model-nobody-resolves", planter_family="x"))
    assert refused(world, "seed-8").code == sm.SEED_IDENTITY_UNKNOWN


def test_an_unknown_writer_or_reviewer_is_refused_before_any_seed_rule(world: World) -> None:
    register(world, ling("seed-7"))
    (world.state_dir / "lesson-2.writer.yaml").write_text(yaml.safe_dump({"writer": "mystery", "model": "mystery"}))
    assert refused(world, "seed-7").code == record.WRITER_IDENTITY_UNKNOWN
    world.writer(2)
    world.task("review-unknown", "codex", None)
    with pytest.raises(record.RecordError, match="attested model"):
        world.record(world.make_return(2), task_id="review-unknown", seed_id="seed-7", register=False)
    assert world.db_rows("attempts") == []


def test_a_seed_is_recorded_for_one_lesson_only(world: World) -> None:
    register(world, ling("seed-7", n=3))
    assert refused(world, "seed-7", n=2).code == sm.SEED_IDENTITY_MISMATCH  # registered for lesson 3, reviewed as 2
    register(world, ling("seed-8", writer_family="google"))
    assert refused(world, "seed-8").code == sm.SEED_IDENTITY_MISMATCH  # the record says the writer is not openai


def test_a_clean_measurement_lesson_is_checked_and_has_no_seed_identity_row(world: World) -> None:
    sm.write_clean_record(
        clean_lesson("clean-7", level=RECORD_LEVEL, slug=RECORD_SLUG, n=2, writer_family="openai"), world.root
    )
    outcome = world.record(world.make_return(2), seed_id="clean-7")
    assert outcome.accepted and outcome.seed_id == "clean-7" and outcome.verdict_file is None
    [attempt] = world.db_rows("attempts")
    assert attempt["seed_id"] == "clean-7" and attempt["writer_family"] == "openai"
    assert world.db_rows("seed_identities") == [] and world.db_rows("budgets") == []
    world.task("review-writer-seat", "codex", "gpt-6-astra")
    world.db.unlink()
    assert refused(world, "clean-7", task_id="review-writer-seat").code == sm.REVIEWER_IS_WRITER


def test_a_failed_seeded_attempt_is_checked_too_and_a_good_one_is_recorded_as_failed(world: World) -> None:
    register(world, ling("seed-7", gold_verdict="fail"))
    with pytest.raises(record.RecordError) as caught:
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
    assert caught.value.code == sm.GOLD_CHECK_NOT_PASSED and world.db_rows("attempts") == []
    register(world, ling("seed-8"))
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
        seed_id="seed-8",
    )
    [attempt] = world.db_rows("attempts")
    assert attempt["verdict"] == "FAILED" and attempt["seed_id"] == "seed-8" and attempt["writer_family"] is None
    assert len(world.db_rows("seed_identities")) == 1 and world.db_rows("budgets") == []


def test_a_replay_of_a_recorded_seeded_attempt_is_not_checked_again(world: World) -> None:
    register(world, ling("seed-7"))
    made = world.make_return(2)
    world.record(made, seed_id="seed-7")
    (world.root / "batch_state" / "review-measurement" / "seeds" / "seed-7.yaml").unlink()
    assert world.record(made, seed_id="seed-7").replay


@pytest.mark.parametrize(
    ("seed_id", "code"),
    [
        ("plain-id", record.SEED_ID_UNRECOGNISED),
        ("seed-", record.SEED_ID_UNRECOGNISED),
        ("seed-a b", record.SEED_ID_UNRECOGNISED),
    ],
)
def test_a_seed_id_must_be_a_seed_or_a_clean_id(world: World, seed_id: str, code: str) -> None:
    with pytest.raises(record.RecordError) as caught:
        world.record(world.make_return(2), seed_id=seed_id, register=False)
    assert caught.value.code == code and world.db_rows("attempts") == []


def test_a_measurement_attempt_is_a_first_seat_lesson_attempt(world: World) -> None:
    register(world, ling("seed-7"))
    with pytest.raises(record.RecordError) as caught:
        world.record(world.make_return(2), seed_id="seed-7", second=True)
    assert caught.value.code == record.SEED_UNSUPPORTED
    assert world.db_rows("attempts") == []


# --- sets and the confirmation lock -----------------------------------------------------------------------------------


def inventory(env: Env) -> None:
    for name in ("a", "b", "c", "d"):
        env.add(mechanical_seed(f"seed-{name}"))
    for name in ("a", "b"):
        env.add(clean_lesson(f"clean-{name}"))


def test_freezing_partitions_the_inventory_into_first_and_confirmation_and_writes_the_hash(env: Env) -> None:
    inventory(env)
    lock = sm.freeze_confirmation(["seed-c", "seed-d", "clean-b"], env.root, now="2026-09-25T10:00:00+00:00")
    assert lock.seeds == ("seed-c", "seed-d") and lock.clean == ("clean-b",)
    assert lock.sha256 == sm.lock_digest(["seed-d", "seed-c"], ["clean-b"])
    assert sm.load_assignments(env.root) == {
        "seed-a": "first",
        "seed-b": "first",
        "seed-c": "confirmation",
        "seed-d": "confirmation",
        "clean-a": "first",
        "clean-b": "confirmation",
    }
    path = env.root / "batch_state" / "review-measurement" / "confirmation.lock"
    assert mode(path) == 0o600 and mode(path.parent / "sets.yaml") == 0o600
    document = yaml.safe_load(path.read_bytes())
    assert (
        document["sha256"]
        == hashlib.sha256(
            json.dumps(
                {"clean": ["clean-b"], "seeds": ["seed-c", "seed-d"]}, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
    )
    assert sm.verify_confirmation_lock(env.root) == lock


def test_the_lock_is_written_once(env: Env) -> None:
    inventory(env)
    sm.freeze_confirmation(["seed-c"], env.root)
    with pytest.raises(sm.MeasurementError) as caught:
        sm.freeze_confirmation(["seed-d"], env.root)
    assert caught.value.code == sm.CONFIRMATION_FROZEN


def test_a_freeze_refuses_an_unknown_an_empty_or_an_already_assigned_unit(env: Env) -> None:
    inventory(env)
    for ids, code in (([], sm.CONFIRMATION_LOCK_INVALID), (["seed-ghost"], sm.MANIFEST_MISSING)):
        with pytest.raises(sm.MeasurementError) as caught:
            sm.freeze_confirmation(ids, env.root)
        assert caught.value.code == code
    sm.assign_set("seed-a", "first", env.root)
    with pytest.raises(sm.MeasurementError) as caught:
        sm.freeze_confirmation(["seed-a"], env.root)
    assert (
        caught.value.code == sm.SET_CONFLICT
        and not (env.root / "batch_state/review-measurement/confirmation.lock").exists()
    )


def test_a_freeze_interrupted_before_the_lock_is_completed_by_running_it_again(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory(env)
    real = sm.write_private
    monkeypatch.setattr(
        sm,
        "write_private",
        lambda path, data, **kw: (
            (_ for _ in ()).throw(OSError("disk")) if kw.get("exclusive") else real(path, data, **kw)
        ),
    )
    with pytest.raises(OSError, match="disk"):
        sm.freeze_confirmation(["seed-c"], env.root)
    monkeypatch.undo()
    with pytest.raises(sm.MeasurementError) as caught:
        sm.verify_confirmation_lock(env.root)
    assert caught.value.code == sm.CONFIRMATION_LOCK_MISSING
    assert sm.freeze_confirmation(["seed-c"], env.root).seeds == ("seed-c",)


def test_units_made_after_the_freeze_can_only_be_rolling(env: Env) -> None:
    inventory(env)
    sm.freeze_confirmation(["seed-c"], env.root)
    late = env.add(mechanical_seed("seed-late"))
    assert late not in sm.load_assignments(env.root)
    for name in ("first", "confirmation"):
        with pytest.raises(sm.MeasurementError) as caught:
            sm.assign_set(late, name, env.root)
        assert caught.value.code == sm.CONFIRMATION_FROZEN
    sm.assign_set(late, "rolling", env.root)
    sm.assign_set(late, "rolling", env.root)  # the same assignment again is a no-op
    with pytest.raises(sm.MeasurementError) as caught:
        sm.assign_set("seed-a", "rolling", env.root)  # a unit never moves out of first
    assert caught.value.code == sm.SET_CONFLICT
    assert sm.verify_confirmation_lock(env.root).seeds == ("seed-c",)


def test_assigning_needs_a_record_and_a_known_set(env: Env) -> None:
    with pytest.raises(sm.MeasurementError) as caught:
        sm.assign_set("seed-ghost", "first", env.root)
    assert caught.value.code == sm.MANIFEST_MISSING
    env.add(mechanical_seed("seed-a"))
    with pytest.raises(sm.MeasurementError):
        sm.assign_set("seed-a", "everything", env.root)


def rewrite_lock(env: Env, **changes) -> None:
    path = env.root / "batch_state" / "review-measurement" / "confirmation.lock"
    document = yaml.safe_load(path.read_bytes())
    document.update(changes)
    path.write_bytes(yaml.safe_dump(document).encode())


def test_the_hash_is_recomputed_and_every_tampering_is_detected(env: Env) -> None:
    inventory(env)
    sm.freeze_confirmation(["seed-c", "seed-d"], env.root)
    rewrite_lock(env, seeds=["seed-c"])  # a unit dropped from the list, the hash left alone
    with pytest.raises(sm.MeasurementError, match="hashes to") as caught:
        sm.verify_confirmation_lock(env.root)
    assert caught.value.code == sm.CONFIRMATION_LOCK_INVALID
    rewrite_lock(env, seeds=["seed-c"], sha256=sm.lock_digest(["seed-c"], []))  # list and hash both rewritten
    with pytest.raises(sm.MeasurementError, match="one side of the frozen list") as caught:
        sm.verify_confirmation_lock(env.root)
    assert caught.value.code == sm.CONFIRMATION_LOCK_INVALID
    rewrite_lock(env, seeds=["seed-c", "seed-d"], sha256="0" * 64)
    with pytest.raises(sm.MeasurementError):
        sm.verify_confirmation_lock(env.root)


def test_a_malformed_lock_is_invalid(env: Env) -> None:
    inventory(env)
    sm.freeze_confirmation(["seed-c"], env.root)
    rewrite_lock(env, seeds="seed-c")
    with pytest.raises(sm.MeasurementError) as caught:
        sm.verify_confirmation_lock(env.root)
    assert caught.value.code == sm.CONFIRMATION_LOCK_INVALID


def test_a_lock_naming_a_unit_with_no_record_is_invalid(env: Env) -> None:
    inventory(env)
    sm.freeze_confirmation(["seed-c"], env.root)
    (env.root / "batch_state/review-measurement/seeds/seed-c.yaml").unlink()
    with pytest.raises(sm.MeasurementError, match="no record"):
        sm.verify_confirmation_lock(env.root)


def test_no_lock_is_reported_as_such(env: Env) -> None:
    with pytest.raises(sm.MeasurementError) as caught:
        sm.verify_confirmation_lock(env.root)
    assert caught.value.code == sm.CONFIRMATION_LOCK_MISSING


# --- the measurement tree is outside every prompt path ------------------------------------------------------------------


def test_eligibility_refuses_a_pin_in_the_measurement_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "repo"
    _, doc, _ = _setup_lesson_fixture(root, monkeypatch, lesson_n=2)
    assert pin_refusals(doc, root) == []
    env = Env(root)
    env.add(mechanical_seed("seed-a"), "first")
    env.add(mechanical_seed("seed-b"))
    env.add(clean_lesson("clean-a"), "first")
    sm.freeze_confirmation(["seed-b"], root)
    measurement = root / "batch_state" / "review-measurement"
    assert (measurement / "confirmation.lock").exists()
    for target in (
        measurement / "seeds" / "seed-a.yaml",
        measurement / "clean" / "clean-a.yaml",
        measurement / "sets.yaml",
        measurement / "confirmation.lock",
    ):
        rel = target.relative_to(root).as_posix()
        pinned = json.loads(json.dumps(doc))
        _repoint(root, pinned, "inputs.plan", rel, target.read_bytes())
        codes = [refusal.code for refusal in pin_refusals(pinned, root)]
        assert codes and set(codes) <= {
            "pin_outside_module_paths",
            "pin_writer_material",
            "pin_foreign_module",
            "pin_path_not_repo_relative",
            "pin_v1_or_archive_tree",
        }, rel
        with pytest.raises(PinIneligibleError):
            render_prompt(pinned, repo_root=root)
        _repoint(root, pinned, "inputs.plan", rel, target.read_bytes())
    assert os.path.isdir(measurement)
