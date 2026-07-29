"""Tests for RB-1 / RB-6 v1.1 trail specs and the v1 estate registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration.validate_trailspec import (
    DEFAULT_ESTATE_REGISTRY_PATH,
    PROJECT_ROOT,
    TrailSpecValidationError,
    validate_estate_registry,
    validate_estate_registry_data,
    validate_trailspec,
    validate_trailspec_data,
)

RB1_TRAIL_PATH = PROJECT_ROOT / "scripts/config/trails/rb1-cold-start.trail.yaml"
RB6_TRAIL_PATH = PROJECT_ROOT / "scripts/config/trails/rb6-estate-probes.trail.yaml"
ESTATE_PATH = DEFAULT_ESTATE_REGISTRY_PATH


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_rb1_trail_validates_v11() -> None:
    """RB-1 v1.1 passes validator, has non-empty hash, and is execution eligible."""
    res = validate_trailspec(spec_path=RB1_TRAIL_PATH)
    assert res["ok"] is True
    spec = res["spec"]
    assert spec["trail_id"] == "rb1-cold-start"
    assert spec["version"] == "1.0.0"
    assert spec["steps_count"] == 10
    assert spec["execution_eligible"] is True
    assert len(spec["trail_hash"]) == 64


def test_rb6_trail_validates_v11() -> None:
    """RB-6 v1.1 passes validator, has non-empty hash, and is execution eligible."""
    res = validate_trailspec(spec_path=RB6_TRAIL_PATH)
    assert res["ok"] is True
    spec = res["spec"]
    assert spec["trail_id"] == "rb6-estate-probes"
    assert spec["version"] == "1.0.0"
    assert spec["steps_count"] == 7
    assert spec["execution_eligible"] is True
    assert len(spec["trail_hash"]) == 64


def test_estate_registry_seed_validates() -> None:
    """Estate registry seed estate.v1.yaml validates against estate-registry.v1 schema."""
    res = validate_estate_registry(registry_path=ESTATE_PATH)
    assert res["ok"] is True
    assert res["schema_version"] == "estate-registry.v1"
    assert res["refused_surfaces_count"] == 4


def test_rb6_references_estate_registry_entries() -> None:
    """RB-6 probes explicitly reference estate surfaces defined in estate.v1.yaml."""
    estate_data = _load_yaml(ESTATE_PATH)
    rb6_data = _load_yaml(RB6_TRAIL_PATH)

    surfaces = estate_data["surfaces"]
    refused = set(estate_data["refused_mutation_surfaces"])

    # Extract declared estate surface identities
    vps_aliases = {v["ssh_alias"] for v in surfaces["vps_hosts"]}
    services = {s["systemd_unit"] for s in surfaces["services"]}
    repos = {Path(r["local_path"]).name for r in surfaces["repositories"]}
    sites = {s["url"] for s in surfaces["public_sites"]}

    assert "vps" in vps_aliases
    assert "hramatka-api" in services
    assert "learn-ukrainian-infra-private" in repos
    # Exact-set equality (not substring membership): stricter, and it avoids the
    # URL-substring pattern CodeQL flags (py/incomplete-url-substring-sanitization).
    assert sites == {"https://learn-ukrainian.github.io/"}

    # Refused surfaces check
    assert "pilot-vps" in refused
    assert "hramatka-api" in refused
    assert "learn-ukrainian-infra-private" in refused
    assert "public-site" in refused

    # Consistency pin: the registry values must appear in the probe COMMANDS
    # (not just intent prose). RB-6 probes deliberately hardcode these values
    # for runtime robustness; this assertion is what makes the registry the
    # source of truth — drifting a command away from the registry fails here.
    _assert_registry_consumed_by_commands(estate_data, rb6_data)


def _assert_registry_consumed_by_commands(estate_data: dict, rb6_data: dict) -> None:
    surfaces = estate_data["surfaces"]
    step_commands = " ".join(
        s["command"]["argv"][-1] for s in rb6_data["steps"] if s["command"]["argv"]
    )
    for vps in surfaces["vps_hosts"]:
        alias = vps["ssh_alias"]
        assert f"ssh -o BatchMode=yes -o ConnectTimeout=5 {alias} " in step_commands, (
            f"registry ssh alias '{alias}' is not consumed by any RB-6 probe command"
        )
    for service in surfaces["services"]:
        assert service["systemd_unit"] in step_commands, (
            f"registry systemd unit '{service['systemd_unit']}' is not consumed "
            "by any RB-6 probe command"
        )
    for repo in surfaces["repositories"]:
        assert repo["local_path"] in step_commands, (
            f"registry repo path '{repo['local_path']}' is not consumed by any RB-6 probe command"
        )
    # Token equality (not substring): the URL must appear as a standalone shell
    # token of a probe command — stricter, and clear of the CodeQL URL-substring rule.
    command_tokens = step_commands.split()
    for site in surfaces["public_sites"]:
        assert any(token == site["url"] for token in command_tokens), (
            f"registry site url '{site['url']}' is not consumed by any RB-6 probe command"
        )


def test_negative_rb6_registry_drift_fails_consistency() -> None:
    """Mutation negative: a registry value drifting away from the commands FAILS the pin."""
    estate_data = _load_yaml(ESTATE_PATH)
    rb6_data = _load_yaml(RB6_TRAIL_PATH)
    estate_data["surfaces"]["vps_hosts"][0]["ssh_alias"] = "vps-renamed"
    with pytest.raises(AssertionError, match="vps-renamed"):
        _assert_registry_consumed_by_commands(estate_data, rb6_data)


def test_negative_rb1_dropped_predicate_clause_fails() -> None:
    """Mutation negative test: dropping a clause from a transition evidence fails validation."""
    data = _load_yaml(RB1_TRAIL_PATH)
    # Remove all clauses from the first transition evidence
    data["steps"][0]["transitions"]["none"]["evidence"]["clauses"] = []

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)
    assert "schema violation" in str(exc_info.value) or "clauses" in str(exc_info.value)


def test_negative_rb1_unpublished_stop_code_fails() -> None:
    """Mutation negative test: using an unpublished STOP code fails validation."""
    data = _load_yaml(RB1_TRAIL_PATH)
    data["stop_codes"].append("STOP-invented-code")

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)
    assert "Unknown stop_code" in str(exc_info.value)


def test_negative_rb1_duplicate_predicate_id_fails() -> None:
    """Mutation negative test: reusing a predicate_id within a step fails validation."""
    data = _load_yaml(RB1_TRAIL_PATH)
    step = data["steps"][0]
    # Reuse detect-rollover-none in pending_start transition
    step["transitions"]["pending_start"]["evidence"]["predicate_id"] = "detect-rollover-none"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)
    assert "Exactly-one-predicate rule violated" in str(exc_info.value)


def test_negative_rb6_unquoted_parameter_in_shell_fails() -> None:
    """Mutation negative test: unquoted parameter interpolation in a shell program string fails."""
    data = _load_yaml(RB6_TRAIL_PATH)
    # Reintroduce {handoff_agent} in argv[2]
    data["steps"][0]["command"]["argv"][2] = "echo {handoff_agent}"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)
    assert "Unquoted parameter interpolation prohibited" in str(exc_info.value)


def test_negative_estate_registry_extra_properties_fails() -> None:
    """Mutation negative test: adding illegal top-level property to estate registry fails strict schema."""
    data = _load_yaml(ESTATE_PATH)
    data["illegal_extra_property"] = True

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_estate_registry_data(data)
    assert "EstateRegistry schema violation" in str(exc_info.value)


def test_negative_estate_registry_missing_refused_surface_fails() -> None:
    """Mutation negative test: removing a required surface section from estate registry fails schema."""
    data = _load_yaml(ESTATE_PATH)
    del data["surfaces"]["vps_hosts"]

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_estate_registry_data(data)
    assert "EstateRegistry schema violation" in str(exc_info.value)


KNOWN_PASSTHROUGH_VOCABULARY = {
    # detect_rollover and claim_rollover pass through thread_handoff.py detect JSON 'status' values
    ("rb1-cold-start", "detect_rollover"): {"none", "pending_start", "resumed", "ambiguous", "unparseable"},
    ("rb1-cold-start", "claim_rollover"): {"none", "pending_start", "resumed", "ambiguous", "unparseable"},
}


def _verify_step_reachability(spec: dict[str, Any]) -> None:
    trail_id = spec["trail_id"]
    for step in spec["steps"]:
        step_id = step["step_id"]
        cmd_argv = step["command"]["argv"]
        sh_prog = cmd_argv[2] if len(cmd_argv) > 2 else " ".join(cmd_argv)
        passthrough = KNOWN_PASSTHROUGH_VOCABULARY.get((trail_id, step_id), set())

        for trans_key in step["transitions"].keys():
            is_literal = trans_key in sh_prog
            is_passthrough = trans_key in passthrough
            assert is_literal or is_passthrough, (
                f"Dead transition key '{trans_key}' in step '{step_id}' of trail '{trail_id}'. "
                f"Transition key does not appear in sh -c program nor in documented pass-through vocabulary."
            )


def test_rb1_rb6_transition_reachability() -> None:
    """Every transition key in RB-1 and RB-6 specs is reachable by an emittable stdout token."""
    _verify_step_reachability(_load_yaml(RB1_TRAIL_PATH))
    _verify_step_reachability(_load_yaml(RB6_TRAIL_PATH))


def test_negative_dead_transition_key_fails_reachability() -> None:
    """Mutation negative test: re-adding a dead transition key to any step fails reachability check."""
    spec = _load_yaml(RB1_TRAIL_PATH)
    spec["steps"][0]["transitions"]["dead_unreachable_key"] = {
        "target": "STOP-concurrency-conflict",
        "evidence": {
            "predicate_id": "detect-rollover-dead",
            "clauses": [
                {
                    "source": "command_receipt",
                    "field": "actor_outcome",
                    "op": "eq",
                    "value": "dead_unreachable_key",
                }
            ],
        },
    }
    with pytest.raises(AssertionError) as exc_info:
        _verify_step_reachability(spec)
    assert "Dead transition key 'dead_unreachable_key'" in str(exc_info.value)


def test_rb1_action_honesty_pin() -> None:
    """Action-honesty pin: judgment-tier steps in RB-1 must use observation vocabulary and never fake action tokens."""
    data = _load_yaml(RB1_TRAIL_PATH)
    steps_by_id = {s["step_id"]: s for s in data["steps"]}

    FORBIDDEN_DISHONEST_TOKENS = {
        "confirmed",
        "applied_and_drained",
        "reaped_with_receipts",
    }

    # 1. claim_rollover
    claim_step = steps_by_id["claim_rollover"]
    assert claim_step["command"]["mutation_class"] == "observe"
    claim_tokens = set(claim_step["transitions"].keys())
    assert claim_tokens == {
        "none",
        "pending_start",
        "resumed",
        "ambiguous",
        "unparseable",
        "detect_failed",
    }
    assert FORBIDDEN_DISHONEST_TOKENS.isdisjoint(claim_tokens)

    # 2. apply_inbox
    apply_step = steps_by_id["apply_inbox"]
    assert apply_step["command"]["mutation_class"] == "observe"
    apply_tokens = set(apply_step["transitions"].keys())
    assert apply_tokens == {"inbox_zero", "pending_requires_application"}
    assert FORBIDDEN_DISHONEST_TOKENS.isdisjoint(apply_tokens)

    # 3. reap_stale_refs
    reap_step = steps_by_id["reap_stale_refs"]
    assert reap_step["command"]["mutation_class"] == "observe"
    reap_tokens = set(reap_step["transitions"].keys())
    assert reap_tokens == {"no_stale_refs", "stale_refs_require_judgment", "reap_probe_failed"}
    assert FORBIDDEN_DISHONEST_TOKENS.isdisjoint(reap_tokens)


@pytest.mark.parametrize("dishonest_token", ["confirmed", "applied_and_drained", "reaped_with_receipts"])
def test_negative_rb1_action_honesty_dishonest_token_fails(dishonest_token: str) -> None:
    """Mutation negative test: re-introducing any dishonest success token fails the action-honesty check."""
    data = _load_yaml(RB1_TRAIL_PATH)
    steps_by_id = {s["step_id"]: s for s in data["steps"]}

    FORBIDDEN_DISHONEST_TOKENS = {
        "confirmed",
        "applied_and_drained",
        "reaped_with_receipts",
    }

    for step_id in ("claim_rollover", "apply_inbox", "reap_stale_refs"):
        tokens = set(steps_by_id[step_id]["transitions"].keys())
        tokens.add(dishonest_token)
        assert not FORBIDDEN_DISHONEST_TOKENS.isdisjoint(tokens)


def test_negative_estate_refused_surfaces_drift_fails_validation() -> None:
    """Mutation negative: refused list drifting from per-surface policy fails validation."""
    from scripts.orchestration.validate_trailspec import (
        TrailSpecValidationError,
        validate_estate_registry_data,
    )

    estate_data = _load_yaml(ESTATE_PATH)
    assert validate_estate_registry_data(estate_data)["ok"] is True
    estate_data["refused_mutation_surfaces"].remove("pilot-vps")
    with pytest.raises(TrailSpecValidationError, match="pilot-vps"):
        validate_estate_registry_data(estate_data)


def test_negative_estate_surface_id_keyed_refusal_is_not_skipped() -> None:
    """Mutation negative: a surface_id-keyed group declaring refused is cross-checked too."""
    from scripts.orchestration.validate_trailspec import (
        TrailSpecValidationError,
        validate_estate_registry_data,
    )

    estate_data = _load_yaml(ESTATE_PATH)
    estate_data["surfaces"]["worktrees"][0]["mutation_policy"] = "refused"
    # refused_mutation_surfaces not updated -> cross-check must catch the drift
    with pytest.raises(TrailSpecValidationError, match="worktree-list"):
        validate_estate_registry_data(estate_data)
