from __future__ import annotations

import json
from copy import deepcopy

import pytest

from scripts.orchestration import task_identity


def _identity(*, issue: int | None = 5295) -> dict:
    return task_identity.build_identity(
        repository=task_identity.DEFAULT_REPOSITORY,
        stream_epic=4707,
        stream_epic_url=None,
        github_issue_number=issue,
        github_issue_url=None,
        semantic_title="Repair fleet rollover task identity",
        task_family="infra-harness",
        role="orchestrator",
        predecessor_task_id="predecessor-1",
        replacement_task_id=None,
        lineage_id="lineage-task-identity",
        generation=2,
        terminal_goal="merge",
    )


def _fresh_identity(**overrides) -> dict:
    return task_identity.build_identity(**{
        "repository": task_identity.DEFAULT_REPOSITORY,
        "stream_epic": 4707,
        "stream_epic_url": None,
        "github_issue_number": 10143,
        "github_issue_url": None,
        "semantic_title": "Initialize fresh task lifecycle",
        "task_family": "infra-harness",
        "role": "driver",
        "fresh_task_id": "native-thread-10143",
        "terminal_goal": "merge",
        "lifecycle_state": "active",
        **overrides,
    })


def test_fresh_identity_validates_without_rollover_ancestry() -> None:
    identity = _crash_roundtrip(_fresh_identity())
    assert task_identity.validate_identity(identity) == identity
    assert list(task_identity._IDENTITY_VALIDATOR.iter_errors(identity)) == []
    assert identity["origin"] == "fresh"
    assert identity["task_id"] == "native-thread-10143"
    assert identity["lifecycle_state"] == "active"
    assert set(identity).isdisjoint({"lineage_id", "generation", "predecessor_task_id", "replacement_task_id"})
    assert set(identity["carriers"].values()) == {identity["visible_title"]}


@pytest.mark.parametrize("task_id", ["", " ", " native-thread", "native thread", "native\nthread", "native\x00thread", "native\x7fthread", 7])
def test_fresh_builder_rejects_malformed_native_task_ids(task_id) -> None:
    with pytest.raises(ValueError):
        _fresh_identity(fresh_task_id=task_id)


@pytest.mark.parametrize("field,value", [
    ("lineage_id", "lineage-real"), ("lineage_id", ""),
    ("predecessor_task_id", "thread-old"), ("replacement_task_id", "thread-new"),
    ("generation", 1), ("generation", 0),
    ("lifecycle_state", "confirmed"), ("lifecycle_state", ""), ("lifecycle_state", None),
    ("lifecycle_state", "prepared"),
    ("legacy_fallback", True), ("terminal_goal", "unknown"),
])
def test_fresh_builder_rejects_rollover_and_legacy_fields(field, value) -> None:
    with pytest.raises(ValueError):
        _fresh_identity(**{field: value})


@pytest.mark.parametrize("field,value", [
    ("origin", None), ("origin", "rollover"), ("task_id", None), ("task_id", ""),
    ("task_id", "native thread"), ("task_id", "native\x00thread"), ("task_id", "native-thread\n"),
    ("lineage_id", None), ("lineage_id", ""), ("lineage_id", "lineage-real"),
    ("predecessor_task_id", None), ("replacement_task_id", None),
    ("generation", 0), ("generation", 1), ("lifecycle_state", "resumed"),
])
def test_fresh_schema_rejects_malformed_and_mixed_envelopes(field, value) -> None:
    identity = _fresh_identity()
    identity[field] = value
    assert list(task_identity._IDENTITY_VALIDATOR.iter_errors(identity))
    with pytest.raises(ValueError, match="schema violation"):
        task_identity.validate_identity(identity)


@pytest.mark.parametrize("field", ["origin", "task_id"])
def test_fresh_schema_requires_explicit_origin_and_native_task_id(field) -> None:
    identity = _fresh_identity()
    del identity[field]
    with pytest.raises(ValueError, match="schema violation"):
        task_identity.validate_identity(identity)


@pytest.mark.parametrize("field,value", [
    ("lineage_id", None), ("lineage_id", ""), ("lineage_id", "Bad-Lineage"),
    ("predecessor_task_id", None), ("predecessor_task_id", ""),
    ("generation", None), ("generation", 0), ("generation", True),
    ("origin", "fresh"), ("task_id", "native-thread"), ("lifecycle_state", "active"),
])
def test_rollover_schema_still_rejects_invalid_identity(field, value) -> None:
    identity = _identity()
    identity[field] = value
    with pytest.raises(ValueError, match="schema violation"):
        task_identity.validate_identity(identity)


@pytest.mark.parametrize("field", ["lineage_id", "generation", "predecessor_task_id", "replacement_task_id"])
def test_rollover_schema_still_requires_ancestry(field) -> None:
    identity = _identity()
    del identity[field]
    with pytest.raises(ValueError, match="schema violation"):
        task_identity.validate_identity(identity)


def test_rollover_builder_still_rejects_null_lifecycle_state() -> None:
    identity = _identity()
    with pytest.raises(ValueError, match="schema violation"):
        task_identity.build_identity(**{
            key: value for key, value in identity.items()
            if key not in {"schema_version", "visible_title", "carriers", "migration", "lifecycle_state"}
        }, lifecycle_state=None)


def test_fresh_identity_cannot_resume_an_unrelated_rollover() -> None:
    identity = _fresh_identity()
    with pytest.raises(ValueError, match="no rollover title transition"):
        task_identity.mark_resumed(identity, _transition(identity), replacement_task_id=identity["task_id"])


def _transition(identity: dict, harness: str = "codex-app") -> dict:
    return task_identity.new_title_transition(
        harness=harness,
        visible_title_value=identity["visible_title"],
        prepared_at="2026-07-16T08:00:00Z",
    )


def _crash_roundtrip(value: dict) -> dict:
    return json.loads(json.dumps(value))


def test_semantic_title_survives_every_native_title_boundary_and_crash() -> None:
    identity = _crash_roundtrip(_identity())
    transition = _crash_roundtrip(_transition(identity))
    title = "#5295 — Repair fleet rollover task identity"
    assert identity["visible_title"] == title

    identity, transition = task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        evidence="exact native create receipt",
        now="2026-07-16T08:01:00Z",
    )
    identity, transition = _crash_roundtrip(identity), _crash_roundtrip(transition)
    identity, transition = task_identity.record_title_acknowledgement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        succeeded=True,
        evidence="set_thread_title acknowledged",
        error="",
        now="2026-07-16T08:02:00Z",
    )
    identity, transition = _crash_roundtrip(identity), _crash_roundtrip(transition)
    identity, transition = task_identity.record_title_readback(
        identity,
        transition,
        replacement_task_id="replacement-2",
        observed_title=title,
        succeeded=True,
        evidence="exact native readback",
        error="",
        now="2026-07-16T08:03:00Z",
    )
    identity, transition = _crash_roundtrip(identity), _crash_roundtrip(transition)
    identity = task_identity.mark_resumed(
        identity,
        transition,
        replacement_task_id="replacement-2",
    )
    identity = _crash_roundtrip(identity)
    identity = task_identity.mark_confirmed(
        identity,
        transition,
        replacement_task_id="replacement-2",
    )

    assert identity["semantic_title"] == "Repair fleet rollover task identity"
    assert identity["visible_title"] == title
    assert identity["lifecycle_state"] == "confirmed"
    assert set(identity["carriers"].values()) == {title}


def test_title_acknowledgement_without_readback_is_not_reconciled() -> None:
    identity = _identity()
    transition = _transition(identity)
    identity, transition = task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        evidence="exact binding",
        now="2026-07-16T08:01:00Z",
    )
    identity, transition = task_identity.record_title_acknowledgement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        succeeded=True,
        evidence="adapter acknowledgement",
        error="",
        now="2026-07-16T08:02:00Z",
    )

    with pytest.raises(ValueError, match="acknowledgement without exact readback"):
        task_identity.assert_title_ready(
            identity,
            transition,
            replacement_task_id="replacement-2",
        )


def test_incorrect_native_title_readback_fails_closed() -> None:
    identity = _identity()
    transition = _transition(identity)
    identity, transition = task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        evidence="exact binding",
        now="2026-07-16T08:01:00Z",
    )
    identity, transition = task_identity.record_title_readback(
        identity,
        transition,
        replacement_task_id="replacement-2",
        observed_title="Replacement task",
        succeeded=True,
        evidence="native readback",
        error="wrong visible title",
        now="2026-07-16T08:02:00Z",
    )

    assert identity["lifecycle_state"] == "title_failed"
    assert transition["readback_receipt"]["exact_match"] is False
    with pytest.raises(ValueError, match="without exact readback"):
        task_identity.assert_title_ready(
            identity,
            transition,
            replacement_task_id="replacement-2",
        )


def test_exact_title_readback_does_not_normalize_whitespace() -> None:
    identity = _identity()
    transition = _transition(identity)
    identity, transition = task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        evidence="exact binding",
        now="2026-07-16T08:01:00Z",
    )
    identity, transition = task_identity.record_title_readback(
        identity,
        transition,
        replacement_task_id="replacement-2",
        observed_title=identity["visible_title"].replace(" — ", "  — "),
        succeeded=True,
        evidence="native readback",
        error="whitespace differs",
        now="2026-07-16T08:02:00Z",
    )

    assert identity["lifecycle_state"] == "title_failed"
    assert transition["readback_receipt"]["exact_match"] is False


def test_incorrect_replacement_id_fails_closed_at_every_title_gate() -> None:
    identity = _identity()
    transition = _transition(identity)
    identity, transition = task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        evidence="exact binding",
        now="2026-07-16T08:01:00Z",
    )

    with pytest.raises(ValueError, match="exact persisted binding"):
        task_identity.bind_replacement(
            identity,
            transition,
            replacement_task_id="wrong-replacement",
            evidence="wrong binding",
            now="2026-07-16T08:02:00Z",
        )
    with pytest.raises(ValueError, match="exact binding"):
        task_identity.record_title_acknowledgement(
            identity,
            transition,
            replacement_task_id="wrong-replacement",
            succeeded=True,
            evidence="wrong acknowledgement",
            error="",
            now="2026-07-16T08:02:00Z",
        )


@pytest.mark.parametrize(
    "title",
    [
        "",
        "   ",
        "Replacement task",
        "Resume rollover",
        "Codex continuation",
        "Generation 2",
        "lineage-abc123",
        "rollover-abc123",
        "019f6a34-df56-4951-9384-c160b627789b",
    ],
)
def test_blank_generic_and_runtime_identifier_titles_are_rejected(title: str) -> None:
    with pytest.raises(ValueError):
        task_identity.validate_semantic_title(title)


def test_terminal_goal_is_typed_and_issue_requires_stream_epic() -> None:
    arguments = {
        "repository": task_identity.DEFAULT_REPOSITORY,
        "stream_epic": 4707,
        "stream_epic_url": None,
        "github_issue_number": 5295,
        "github_issue_url": None,
        "semantic_title": "Repair fleet rollover task identity",
        "task_family": "infra-harness",
        "role": "orchestrator",
        "predecessor_task_id": "predecessor-1",
        "replacement_task_id": None,
        "lineage_id": "lineage-task-identity",
        "generation": 2,
    }
    with pytest.raises(ValueError, match="terminal goal must be one of"):
        task_identity.build_identity(**arguments, terminal_goal="finish everything")
    with pytest.raises(ValueError, match="exactly one stream epic"):
        task_identity.build_identity(
            **{**arguments, "stream_epic": None},
            terminal_goal="merge",
        )
    with pytest.raises(ValueError, match="lineage ID must start with a lowercase letter"):
        task_identity.build_identity(
            **{**arguments, "lineage_id": "123-invalid-lineage"},
            terminal_goal="merge",
        )


def test_unsupported_adapter_records_honest_carrier_fallback() -> None:
    identity = _identity(issue=None)
    transition = _transition(identity, harness="claude")
    identity, transition = task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="claude-task-2",
        evidence="dispatch runtime task binding",
        now="2026-07-16T08:01:00Z",
    )

    receipt = transition["fallback_receipt"]
    assert identity["visible_title"] == "infra-harness — Repair fleet rollover task identity"
    assert receipt["native_mutation_supported"] is False
    assert receipt["attempted"] is False
    assert receipt["carriers"] == list(task_identity.FALLBACK_CARRIERS)
    task_identity.assert_title_ready(
        identity,
        transition,
        replacement_task_id="claude-task-2",
    )


@pytest.mark.parametrize(
    ("harness", "native_supported"),
    [
        ("codex-app", True),
        ("claude", False),
        ("gemini", False),
        ("agy", False),
        ("cursor", False),
        ("hermes", False),
        ("opencode", False),
    ],
)
def test_every_harness_uses_the_shared_identity_contract(harness: str, native_supported: bool) -> None:
    identity = _identity()
    transition = _transition(identity, harness=harness)

    assert task_identity.validate_identity(identity) == identity
    assert task_identity.validate_title_transition(transition, identity) == transition
    assert transition["native_title_supported"] is native_supported
    assert transition["visible_title"] == identity["visible_title"]


def test_title_transition_rejects_non_object_events() -> None:
    identity = _identity()
    transition = _transition(identity)
    transition["events"].append("corrupted-event")

    with pytest.raises(ValueError, match="events must be a list of objects"):
        task_identity.validate_title_transition(transition, identity)


@pytest.mark.parametrize(
    ("state", "expected_prefix"),
    [
        ("awaiting_replacement_binding", "Bind the exact replacement"),
        ("awaiting_native_title", "Request the exact native title action"),
        ("title_acknowledged", "Read back only"),
        ("title_mutation_failed", "Repair the exact title boundary"),
        ("title_readback_failed", "Repair the exact title boundary"),
        ("title_reconciled", "Resume only"),
        ("fallback_recorded", "Resume only"),
        ("unknown-state", "Inspect the exact receipt"),
    ],
)
def test_safe_recommended_resolution_covers_every_operator_state(
    state: str,
    expected_prefix: str,
) -> None:
    resolution = task_identity.safe_recommended_resolution(
        {"state": state, "replacement_task_id": "replacement-2"},
        rollover_id="rollover-2",
    )

    assert resolution.startswith(expected_prefix)
    assert "rollover-2" in resolution or "replacement-2" in resolution


def test_legacy_packet_receives_deterministic_identity_backfill() -> None:
    legacy = {
        "schema_version": 2,
        "agent": "claude",
        "lineage_id": "lineage-legacy-packet",
        "active": {"thread_id": "legacy-predecessor"},
        "replacement": {
            "rollover_id": "rollover-legacy",
            "lineage_id": "lineage-legacy-packet",
            "generation": 3,
            "status": "pending_start",
            "prepared_at": "2026-07-15T08:00:00Z",
            "display": {"title": "Generation 3"},
        },
    }

    first, migrated = task_identity.backfill_legacy_identity(
        legacy,
        agent="claude",
        repository=task_identity.DEFAULT_REPOSITORY,
        now="2026-07-16T08:00:00Z",
    )
    second, migrated_again = task_identity.backfill_legacy_identity(
        deepcopy(first),
        agent="claude",
        repository=task_identity.DEFAULT_REPOSITORY,
        now="2026-07-17T08:00:00Z",
    )

    assert migrated is True
    assert migrated_again is False
    assert second["replacement"]["identity"] == first["replacement"]["identity"]
    assert first["replacement"]["identity"]["visible_title"] == (
        "thread-rollover — Recover predecessor task context"
    )
    assert first["replacement"]["identity"]["migration"] == {
        "source": "legacy-v2-deterministic-fallback",
        "legacy_fallback": True,
    }
    assert first["replacement"]["identity"]["terminal_goal"] == "unknown"
    assert first["replacement"]["title_transition"]["harness"] == "claude-legacy"
    assert first["replacement"]["title_transition"]["state"] == "awaiting_replacement_binding"


def test_title_boundary_retries_are_idempotent() -> None:
    identity = _identity()
    transition = _transition(identity)
    identity, transition = task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        evidence="binding",
        now="2026-07-16T08:01:00Z",
    )
    bound = (deepcopy(identity), deepcopy(transition))
    assert task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        evidence="retry",
        now="2026-07-16T09:01:00Z",
    ) == bound

    identity, transition = task_identity.record_title_acknowledgement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        succeeded=True,
        evidence="acknowledgement",
        error="",
        now="2026-07-16T08:02:00Z",
    )
    acknowledged = (deepcopy(identity), deepcopy(transition))
    assert task_identity.record_title_acknowledgement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        succeeded=True,
        evidence="retry",
        error="",
        now="2026-07-16T09:02:00Z",
    ) == acknowledged

    identity, transition = task_identity.record_title_readback(
        identity,
        transition,
        replacement_task_id="replacement-2",
        observed_title=identity["visible_title"],
        succeeded=True,
        evidence="readback",
        error="",
        now="2026-07-16T08:03:00Z",
    )
    reconciled = (deepcopy(identity), deepcopy(transition))
    assert task_identity.record_title_readback(
        identity,
        transition,
        replacement_task_id="replacement-2",
        observed_title=identity["visible_title"],
        succeeded=True,
        evidence="retry",
        error="",
        now="2026-07-16T09:03:00Z",
    ) == reconciled


def test_native_title_failure_can_retry_to_durable_success() -> None:
    identity = _identity()
    transition = _transition(identity)
    identity, transition = task_identity.bind_replacement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        evidence="binding",
        now="2026-07-16T08:01:00Z",
    )
    identity, transition = task_identity.record_title_acknowledgement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        succeeded=False,
        evidence="first adapter attempt",
        error="transient failure",
        now="2026-07-16T08:02:00Z",
    )
    assert identity["lifecycle_state"] == "title_failed"
    assert transition["state"] == "title_mutation_failed"

    identity, transition = task_identity.record_title_acknowledgement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        succeeded=True,
        evidence="retry acknowledged",
        error="",
        now="2026-07-16T08:03:00Z",
    )
    identity, transition = task_identity.record_title_readback(
        identity,
        transition,
        replacement_task_id="replacement-2",
        observed_title=identity["visible_title"],
        succeeded=True,
        evidence="exact retry readback",
        error="",
        now="2026-07-16T08:04:00Z",
    )
    reconciled = (deepcopy(identity), deepcopy(transition))

    assert identity["lifecycle_state"] == "title_ready"
    assert transition["state"] == "title_reconciled"
    assert transition["mutation_receipt"]["succeeded"] is True
    assert transition["readback_receipt"]["exact_match"] is True

    assert task_identity.record_title_acknowledgement(
        identity,
        transition,
        replacement_task_id="replacement-2",
        succeeded=False,
        evidence="late duplicate failure",
        error="transient adapter response",
        now="2026-07-16T10:02:00Z",
    ) == reconciled
    assert task_identity.record_title_readback(
        identity,
        transition,
        replacement_task_id="replacement-2",
        observed_title="late stale value",
        succeeded=False,
        evidence="late duplicate failure",
        error="transient adapter response",
        now="2026-07-16T10:03:00Z",
    ) == reconciled
