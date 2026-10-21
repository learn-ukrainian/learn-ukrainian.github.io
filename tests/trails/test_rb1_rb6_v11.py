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
    validate_trailspec_data,
)

RB1_TRAIL_PATH = PROJECT_ROOT / "scripts/config/trails/rb1-cold-start.trail.yaml"
RB6_TRAIL_PATH = PROJECT_ROOT / "scripts/config/trails/rb6-estate-probes.trail.yaml"
ESTATE_PATH = DEFAULT_ESTATE_REGISTRY_PATH


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_estate_registry_seed_validates() -> None:
    """Estate registry seed estate.v1.yaml validates against estate-registry.v1 schema."""
    res = validate_estate_registry(registry_path=ESTATE_PATH)
    assert res["ok"] is True
    assert res["schema_version"] == "estate-registry.v1"
    assert res["refused_surfaces_count"] == 4


def test_rb6_references_estate_registry_entries() -> None:
    """RB-6 probes must not reconstruct estate topology from the public registry seed."""
    estate_data = _load_yaml(ESTATE_PATH)
    rb6_data = _load_yaml(RB6_TRAIL_PATH)

    surfaces = estate_data["surfaces"]
    refused = set(estate_data["refused_mutation_surfaces"])

    # Declared estate surface identities (opaque tokens — not probe command literals).
    vps_names = {v["name"] for v in surfaces["vps_hosts"]}
    service_names = {s["name"] for s in surfaces["services"]}
    repo_names = {r["name"] for r in surfaces["repositories"]}
    sites = {s["url"] for s in surfaces["public_sites"]}

    assert "estate-probe-vps" in vps_names
    assert "estate-probe-service" in service_names
    assert "estate-probe-private-repo" in repo_names
    # Exact-set equality (not substring membership): stricter, and it avoids the
    # URL-substring pattern CodeQL flags (py/incomplete-url-substring-sanitization).
    assert sites == {"https://learn-ukrainian.github.io/"}

    # Refused surfaces check
    assert "estate-probe-vps" in refused
    assert "estate-probe-service" in refused
    assert "estate-probe-private-repo" in refused
    assert "public-site" in refused

    # Decoupling pin: registry fields must not jointly appear in probe commands.
    _assert_registry_decoupled_from_commands(estate_data, rb6_data)


def _assert_registry_decoupled_from_commands(estate_data: dict, rb6_data: dict) -> None:
    surfaces = estate_data["surfaces"]
    step_commands = " ".join(
        s["command"]["argv"][-1] for s in rb6_data["steps"] if s["command"]["argv"]
    )
    ssh_aliases = {v["ssh_alias"] for v in surfaces["vps_hosts"]}
    for vps in surfaces["vps_hosts"]:
        assert vps["ssh_alias"] not in step_commands, (
            f"registry ssh alias '{vps['ssh_alias']}' must not appear in RB-6 probe commands"
        )
        assert vps["role"] not in step_commands, (
            f"registry role '{vps['role']}' must not appear in RB-6 probe commands"
        )
    for service in surfaces["services"]:
        assert service["host_alias"] not in step_commands, (
            f"registry host alias '{service['host_alias']}' must not appear in RB-6 probe commands"
        )
        assert service["systemd_unit"] not in step_commands, (
            f"registry systemd unit '{service['systemd_unit']}' must not appear in RB-6 probe commands"
        )
        assert service["host_alias"] not in ssh_aliases, (
            "registry must not cross-link service host_alias to vps ssh_alias"
        )
    for repo in surfaces["repositories"]:
        assert repo["local_path"] not in step_commands, (
            f"registry repo path '{repo['local_path']}' must not appear in RB-6 probe commands"
        )
    command_tokens = step_commands.split()
    for site in surfaces["public_sites"]:
        assert site["url"] not in command_tokens, (
            f"registry site url '{site['url']}' must not appear in RB-6 probe commands"
        )

    for env_key in ("RB6_PROBE_SSH", "RB6_PROBE_UNIT", "RB6_PROBE_REPO", "RB6_PROBE_SITE"):
        assert env_key in step_commands, (
            f"RB-6 probe commands must use runtime env placeholder {env_key}"
        )


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

        for trans_key in step["transitions"]:
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


def test_negative_estate_refused_surfaces_drift_fails_validation() -> None:
    """Mutation negative: refused list drifting from per-surface policy fails validation."""
    from scripts.orchestration.validate_trailspec import (
        TrailSpecValidationError,
    )

    estate_data = _load_yaml(ESTATE_PATH)
    assert validate_estate_registry_data(estate_data)["ok"] is True
    estate_data["refused_mutation_surfaces"].remove("estate-probe-vps")
    with pytest.raises(TrailSpecValidationError, match="estate-probe-vps"):
        validate_estate_registry_data(estate_data)


def test_negative_estate_surface_id_keyed_refusal_is_not_skipped() -> None:
    """Mutation negative: a surface_id-keyed group declaring refused is cross-checked too."""
    from scripts.orchestration.validate_trailspec import (
        TrailSpecValidationError,
    )

    estate_data = _load_yaml(ESTATE_PATH)
    estate_data["surfaces"]["worktrees"][0]["mutation_policy"] = "refused"
    # refused_mutation_surfaces not updated -> cross-check must catch the drift
    with pytest.raises(TrailSpecValidationError, match="worktree-list"):
        validate_estate_registry_data(estate_data)
