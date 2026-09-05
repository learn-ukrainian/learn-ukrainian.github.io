"""Strict wire contract for the existing private API's V4 Actions adapter.

The private adapter verifies OIDC cryptography and authoritative GitHub resources.
This package never accepts principal facts from an HTTP body. A verifier is a
trusted service dependency installed at API startup, distinct from review auth.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Protocol

AUTHZ_POLICY = "hramatka-v4-actions-authz.v1"
AUTHORIZE_SCHEMA = "hramatka-v4-operation-authorize.v1"
EXECUTE_SCHEMA = "hramatka-v4-operation-execute.v1"
OPAQUE_ID = re.compile(r"[A-Za-z0-9_-]{43}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")


class OperationRefused(ValueError):
    """A V4 operation failed closed before producing authority."""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_request(raw: bytes, *, execution: bool) -> dict[str, str]:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= 1024:
        raise OperationRefused("request_size")

    def pairs(items: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in items:
            if key in result:
                raise OperationRefused("duplicate_key")
            result[key] = value
        return result

    try:
        body = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
        expected = {"schema", "authorization_id"} if execution else {"schema"}
        if not isinstance(body, dict) or set(body) != expected:
            raise OperationRefused("request_keys")
        if body["schema"] != (EXECUTE_SCHEMA if execution else AUTHORIZE_SCHEMA):
            raise OperationRefused("request_schema")
        if execution and (
            not isinstance(body["authorization_id"], str) or not OPAQUE_ID.fullmatch(body["authorization_id"])
        ):
            raise OperationRefused("authorization_id")
        if canonical_bytes(body) != raw:
            raise OperationRefused("noncanonical_request")
    except (UnicodeError, json.JSONDecodeError, TypeError) as exc:
        raise OperationRefused("invalid_request") from exc
    return body


@dataclass(frozen=True)
class ActionsPrincipal:
    """Authenticated private adapter output, never deserialized from caller JSON."""

    repository_id: int
    workflow_ref: str
    ref: str
    subject: str
    workflow_sha256: str
    run_id: int
    run_attempt: int
    check_run_id: int
    runner_id: int
    runner_group_id: int
    runner_label: str
    authz_policy_sha256: str
    jti: str

    def ownership(self) -> dict:
        result = asdict(self)
        result.pop("jti")
        for key in ("repository_id", "run_id", "run_attempt", "check_run_id", "runner_id", "runner_group_id"):
            if type(result[key]) is not int or result[key] <= 0:
                raise OperationRefused("invalid_authenticated_principal")
        for key in ("workflow_sha256", "authz_policy_sha256"):
            if not isinstance(result[key], str) or not HEX64.fullmatch(result[key]):
                raise OperationRefused("invalid_authenticated_policy")
        if not self.jti or not self.workflow_ref or not self.ref or not self.subject or not self.runner_label:
            raise OperationRefused("invalid_authenticated_principal")
        return result


class ActionsVerifier(Protocol):
    def authenticate(self, *, oidc_token: str, github_bearer: str) -> ActionsPrincipal:
        """Require fresh operation-specific OIDC + authoritative Actions lookups.

        Recheck repository, audience, issuer, event, ref, exact workflow bytes,
        execute-v4-real-slot job, run/attempt/check and configured runner identity.
        Reject teacher cookies, review tokens and ordinary bearer tokens.
        """
        ...
