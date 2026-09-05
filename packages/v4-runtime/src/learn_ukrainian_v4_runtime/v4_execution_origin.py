"""V4 native-runner execution origin (PR #7662 repair 8).

``RequestExecutor.execute_capture`` ingests caller captures and is not a V4
execution authority. The only production origin is
``scripts.agent_runtime.runner._execute_invocation_plan`` after the runner
has resolved an opaque authorization, atomically claimed the exact binding,
spawned the authorized plan, and derived facts from that process.

This module owns the source-blind prompt profiles, the serializable
authorize/claim protocol, and runner-owned observation derivation. Persistence
stays on the Fleet Comms PostgreSQL plane via
``v4_canonical_authority_store``.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from pathlib import Path
from typing import Any

from learn_ukrainian_v4_runtime import v4_a3_builder_packet as packet
from learn_ukrainian_v4_runtime import v4_a7_original_row_factory as a7
from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.contracts import new_id
from learn_ukrainian_v4_runtime.identity import KNOWN_HARNESS_EXECUTABLES

AUTHOR_PROMPT_PROFILE = "v4-author-source-blind-v1"
REVIEWER_PROMPT_PROFILE = "v4-reviewer-source-blind-v1"
V4_SOURCES_CAPABILITY_ENV = "V4_SOURCES_ATTEMPT_CAPABILITY"
V4_REVIEW_VERDICT_RE = re.compile(r"^[ \t]*V4-REVIEW-VERDICT:[ \t]*(PASS|FAIL)[ \t]*$", re.MULTILINE)
V4_AUTHOR_ROW_RE = re.compile(r"V4-AUTHOR-ROW:\s*(\{.*\})\s*$", re.DOTALL)
DEFAULT_REVIEW_RUBRIC_RELATIVE = "data/projects/open_model_data/trust/v4_review_rubric_v1.txt"
HEX64_RE = re.compile(r"^[a-f0-9]{64}$")


class V4ExecutionOriginError(RuntimeError):
    """Native V4 authorize/claim/observation origin refused an operation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise V4ExecutionOriginError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _repo_root():
    from learn_ukrainian_v4_runtime.resources import resource_root

    return resource_root()


def packet_receipt_path() -> Path:
    """Lowest-IO seam: tests may monkeypatch this to a fixture receipt."""
    return packet.DEFAULT_PACKET_RECEIPT


def slot_manifest_path() -> Path:
    """Lowest-IO seam: tests may monkeypatch this to a fixture manifest."""
    return a7.SLOT_MANIFEST_PATH


def review_rubric_path() -> Path:
    """Lowest-IO seam: tests may monkeypatch this to a fixture rubric."""
    return _repo_root() / DEFAULT_REVIEW_RUBRIC_RELATIVE


def load_frozen_slot(slot_id: str) -> dict[str, Any]:
    from learn_ukrainian_v4_runtime import v4_stage_evidence as ev

    _require(isinstance(slot_id, str) and bool(slot_id), "slot_id must be a nonempty string -- refusing")
    manifest = json.loads(slot_manifest_path().read_text(encoding="utf-8"))
    for stratum in ev.frozen_slot_strata(manifest):
        if slot_id in stratum["slot_ids"]:
            return {
                "slot_id": slot_id,
                "stratum": stratum["stratum"],
                "id_prefix": stratum["id_prefix"],
            }
    raise V4ExecutionOriginError(f"slot_id {slot_id!r} is not a frozen public V4 slot -- refusing")


def load_a3_packet_commitment() -> str:
    receipt = json.loads(packet_receipt_path().read_text(encoding="utf-8"))
    packet.validate_receipt_schema(receipt)
    digest = receipt.get("packet", {}).get("packet_commitment_sha256")
    _require(
        isinstance(digest, str) and bool(HEX64_RE.match(digest)),
        "A3 packet receipt carries no packet_commitment_sha256 -- refusing",
    )
    return digest


def load_review_rubric_sha256() -> str:
    path = review_rubric_path()
    _require(path.is_file(), f"V4 review rubric is missing: {path} -- refusing")
    return _sha256_bytes(path.read_bytes())


def build_author_prompt(*, slot_id: str, packet_sha256: str, expected_seat: str) -> str:
    """Fixed source-blind author profile: slot/packet/seat hashes only."""
    return (
        f"V4_PROMPT_PROFILE={AUTHOR_PROMPT_PROFILE}\n"
        f"role=author\n"
        f"slot_id={slot_id}\n"
        f"packet_sha256={packet_sha256}\n"
        f"expected_seat={expected_seat}\n"
        "Emit one independently authored row as a single JSON object after the\n"
        "marker V4-AUTHOR-ROW. Do not include source text, held-out membership,\n"
        "eligible unit ids, or any corpus excerpt. Call sanctioned Sources\n"
        "verifier tools when evidence is required.\n"
    )


def build_reviewer_prompt(
    *,
    authorship_receipt_sha256: str,
    rubric_sha256: str,
    packet_sha256: str,
    expected_seat: str,
) -> str:
    """Fixed source-blind reviewer profile: receipt/rubric/packet hashes only."""
    return (
        f"V4_PROMPT_PROFILE={REVIEWER_PROMPT_PROFILE}\n"
        f"role=reviewer\n"
        f"authorship_receipt_sha256={authorship_receipt_sha256}\n"
        f"rubric_sha256={rubric_sha256}\n"
        f"packet_sha256={packet_sha256}\n"
        f"expected_seat={expected_seat}\n"
        "Emit exactly one machine-readable verdict line:\n"
        "V4-REVIEW-VERDICT: PASS\n"
        "or\n"
        "V4-REVIEW-VERDICT: FAIL\n"
        "Do not include source text, held-out membership, or eligible unit ids.\n"
    )


def prompt_digest(prompt: str) -> str:
    return _sha256_text(prompt)


def derive_harness(resolved_recipient: str) -> str:
    candidate = (resolved_recipient or "").strip().lower()
    _require(
        candidate in KNOWN_HARNESS_EXECUTABLES,
        f"recipient {resolved_recipient!r} is not a canonical V4 harness -- refusing",
    )
    return candidate


def mint_capability_token() -> tuple[str, str]:
    """Return ``(plaintext_token, sha256_digest)``. Only the digest is stored."""
    token = secrets.token_urlsafe(32)
    return token, _sha256_text(token)


def capability_digest(token: str) -> str:
    return _sha256_text(token)


def transported_prompt_bytes(*, plan: Any, review_cmd: list[str]) -> bytes:
    """Bytes actually transported to the child: stdin payload, else argv after ``--``."""
    stdin_payload = getattr(plan, "stdin_payload", "") or ""
    if stdin_payload:
        return str(stdin_payload).encode("utf-8")
    if "--" in review_cmd:
        index = review_cmd.index("--")
        return " ".join(review_cmd[index + 1 :]).encode("utf-8")
    return b""


def argv_digest(review_cmd: list[str]) -> str:
    return _sha256_text(_canonical_json(list(review_cmd)))


def executable_name(review_cmd: list[str]) -> str:
    _require(
        bool(review_cmd) and isinstance(review_cmd[0], str) and review_cmd[0],
        "post-isolation argv has no executable -- refusing",
    )
    return Path(review_cmd[0]).name.lower()


def domain_separated_aggregate_digest(*, stdout: bytes, stderr: bytes, output: bytes) -> str:
    return _sha256_text(
        _canonical_json(
            {
                "stdout_sha256": _sha256_bytes(stdout),
                "stderr_sha256": _sha256_bytes(stderr),
                "output_sha256": _sha256_bytes(output),
            }
        )
    )


def derive_observed_model(events: tuple[dict[str, Any], ...]) -> str | None:
    seen: set[str] = set()
    for event in events or ():
        if not isinstance(event, dict):
            continue
        candidates = [event.get("model")]
        message = event.get("message")
        if isinstance(message, dict):
            candidates.append(message.get("model"))
        for value in candidates:
            if isinstance(value, str) and value.strip():
                seen.add(value.strip())
    return seen.pop() if len(seen) == 1 else None


def derive_session_id(events: tuple[dict[str, Any], ...], parse_session_id: str | None) -> str | None:
    seen: set[str] = set()
    for event in events or ():
        if not isinstance(event, dict):
            continue
        value = event.get("session_id")
        if isinstance(value, str) and value.strip():
            seen.add(value.strip())
    if parse_session_id:
        if seen and parse_session_id not in seen:
            return None
        seen.add(parse_session_id)
    return seen.pop() if len(seen) == 1 else None


def parse_capture_events(stdout: str) -> tuple[dict[str, Any], ...]:
    events: list[dict[str, Any]] = []
    for line in (stdout or "").splitlines():
        text = line.strip()
        if not text.startswith("{"):
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
    return tuple(events)


def parse_author_row_text(response_text: str) -> str | None:
    match = V4_AUTHOR_ROW_RE.search(response_text or "")
    if match is None:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    row_text = payload.get("row_text")
    if not isinstance(row_text, str) or not row_text.strip():
        return None
    return row_text


def parse_review_verdict(response_text: str) -> str | None:
    found = {match.group(1) for match in V4_REVIEW_VERDICT_RE.finditer(response_text or "")}
    return found.pop() if len(found) == 1 else None


def blindness_from_prompt_profile(
    *, prompt_profile: str, transported_digest: str, authorized_digest: str
) -> tuple[bool, bool, bool]:
    """Blindness is derived from the validated source-blind profile + exact digest.

    A mismatch refuses at the caller; this function never hard-codes False
    independently of those two facts.
    """
    _require(
        transported_digest == authorized_digest,
        "transported prompt digest does not match the authorized source-blind prompt -- refusing",
    )
    _require(
        prompt_profile in {AUTHOR_PROMPT_PROFILE, REVIEWER_PROMPT_PROFILE},
        f"prompt profile {prompt_profile!r} is not a source-blind V4 profile -- refusing",
    )
    return False, False, False


def inject_sources_capability(*, env: dict[str, str], token: str) -> dict[str, str]:
    """Place the one-attempt capability in the child environment.

    Codex MCP configs already honor ``bearer_token_env_var``; Claude streamable
    HTTP configs honor ``headers.Authorization``. The runner also copies the
    token into a per-invocation MCP JSON when it writes one. The plaintext
    token is never stored in PostgreSQL.
    """
    updated = dict(env)
    updated[V4_SOURCES_CAPABILITY_ENV] = token
    return updated


def mcp_sources_auth_config(*, url: str, token: str) -> dict[str, Any]:
    """Existing native MCP HTTP auth shapes: Claude headers + Codex bearer env."""
    return {
        "type": "streamable-http",
        "url": url,
        "headers": {"Authorization": f"Bearer {token}"},
        "bearer_token_env_var": V4_SOURCES_CAPABILITY_ENV,
    }


def apply_mcp_capability_to_tool_config(tool_config: dict[str, Any] | None, *, token: str) -> dict[str, Any]:
    """Stamp the capability onto whatever MCP HTTP config the adapter already has."""
    config = dict(tool_config or {})
    servers = config.get("mcp_servers")
    if isinstance(servers, dict):
        updated_servers = {}
        for name, server in servers.items():
            if not isinstance(server, dict):
                updated_servers[name] = server
                continue
            stamped = dict(server)
            stamped["bearer_token_env_var"] = V4_SOURCES_CAPABILITY_ENV
            headers = dict(stamped.get("headers") or {})
            headers["Authorization"] = f"Bearer {token}"
            stamped["headers"] = headers
            updated_servers[name] = stamped
        config["mcp_servers"] = updated_servers
    mcp_config_path = config.get("mcp_config_path")
    if isinstance(mcp_config_path, str) and mcp_config_path:
        path = Path(mcp_config_path)
        if path.is_file():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                servers = payload.get("mcpServers")
                if isinstance(servers, dict):
                    for server in servers.values():
                        if not isinstance(server, dict):
                            continue
                        headers = dict(server.get("headers") or {})
                        headers["Authorization"] = f"Bearer {token}"
                        server["headers"] = headers
                    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return config


def new_attempt_id() -> str:
    return new_id("v4attempt")


def new_task_run_ids(*, slot_id: str, role: str) -> tuple[str, str]:
    """Service-allocated opaque task/run ids; never caller-supplied."""
    return f"v4-{role}-{slot_id}", new_id("v4run")


def load_active_trust_policy() -> tuple[dict[str, Any], str]:
    return trust.load_production_trust_policy()
