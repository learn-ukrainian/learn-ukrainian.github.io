"""Stdlib-only client for the remote Monitor epic lifecycle API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlencode, urlparse

from agents_extensions.shared.session_streams.model import (
    Entry,
    EntryRef,
    EntryType,
    HolderKind,
    Lease,
    LeaseHolder,
    StreamDigest,
)

DEFAULT_MONITOR = "http://127.0.0.1:8765"
REMOTE_TIMEOUT_SECONDS = 10


class RemoteSupervisorError(RuntimeError):
    """Base error for a refused or unavailable Monitor API operation."""


class RemoteUnreachableError(RemoteSupervisorError):
    """The Monitor API could not be reached; no claim is inferred."""


class RemoteLeaseLostError(RemoteSupervisorError):
    """The server fenced this client; renewal must stop."""


def monitor_url(raw: str | None = None) -> str:
    """Validate the configured Monitor URL without exposing it in responses."""
    value = (raw if raw is not None else os.environ.get("LU_MONITOR_LOOPBACK", DEFAULT_MONITOR)).strip()
    try:
        parsed = urlparse(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise RemoteSupervisorError("monitor URL must be an HTTP loopback URL") from exc
    if parsed.scheme != "http" or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise RemoteSupervisorError("monitor URL must be an HTTP loopback URL")
    if host not in {"localhost", "127.0.0.1"}:
        raise RemoteSupervisorError("monitor URL must be an HTTP loopback URL")
    return f"http://127.0.0.1:{port or 8765}"


def _entry_from_payload(payload: Mapping[str, Any]) -> Entry:
    refs = tuple(
        EntryRef(
            kind=str(ref["kind"]),
            uri=str(ref["uri"]) if ref.get("uri") is not None else None,
            target_entry_id=int(ref["target_entry_id"]) if ref.get("target_entry_id") is not None else None,
        )
        for ref in payload.get("refs", ())
    )
    return Entry(
        entry_id=int(payload["entry_id"]),
        stream_id=str(payload.get("stream", payload.get("stream_id"))),
        session_id=str(payload["session_id"]),
        agent=str(payload["agent"]),
        harness=str(payload["harness"]),
        ts=str(payload["ts"]),
        type=EntryType(str(payload["type"])),
        body=str(payload["body"]),
        body_sha256=str(payload["body_sha256"]),
        idempotency_key=str(payload["idempotency_key"]),
        refs=refs,
    )


def _digest_from_payload(payload: Mapping[str, Any]) -> StreamDigest:
    return StreamDigest(
        stream_id=str(payload["stream_id"]),
        limit=int(payload["limit"]),
        pinned=tuple(_entry_from_payload(entry) for entry in payload.get("pinned", ())),
        recent=tuple(_entry_from_payload(entry) for entry in payload.get("recent", ())),
        high_water_entry_id=int(payload.get("high_water_entry_id", 0)),
    )


class RemoteEpicClient:
    """One narrow, retry-free HTTP client; callers own lifecycle retry policy."""

    def __init__(self, *, base: str | None = None, opener: Callable[..., Any] | None = None) -> None:
        self.base = monitor_url(base)
        self.opener = urllib.request.urlopen if opener is None else opener

    def _request(self, method: str, path: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        body = (
            None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        request = urllib.request.Request(
            f"{self.base}{path}",
            data=body,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method=method,
        )
        try:
            with self.opener(request, timeout=REMOTE_TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8")
                status = int(getattr(response, "status", 200))
        except urllib.error.HTTPError as exc:
            try:
                raw = exc.read().decode("utf-8")
                detail = json.loads(raw).get("detail", "request refused")
            except (ValueError, json.JSONDecodeError, OSError):
                detail = "request refused"
            if exc.code == 409:
                raise RemoteLeaseLostError("LEASE LOST: Monitor fenced the exact lease") from None
            raise RemoteSupervisorError(f"Monitor API refused request ({exc.code}): {detail}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RemoteUnreachableError("Monitor API unreachable; no remote claim was made") from exc
        if status >= 400:
            if status == 409:
                raise RemoteLeaseLostError("LEASE LOST: Monitor fenced the exact lease")
            raise RemoteSupervisorError("Monitor API returned an error")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RemoteSupervisorError("Monitor API returned non-JSON data") from exc
        if not isinstance(data, dict):
            raise RemoteSupervisorError("Monitor API returned a non-object JSON document")
        return data

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/epics/v1/health")

    @staticmethod
    def _lease_payload(lease: Lease) -> dict[str, Any]:
        return {
            "stream_id": lease.stream_id,
            "session_id": lease.session_id,
            "lease_id": lease.lease_id,
            "generation": lease.generation,
            "fencing_token": lease.fencing_token,
            "holder": {
                "agent": lease.holder.agent,
                "harness": lease.holder.harness,
                "instance_id": lease.holder.instance_id,
                "task_id": lease.holder.task_id,
                "process_id": lease.holder.process_id,
                "holder_kind": lease.holder.holder_kind.value,
                "host_id": lease.holder.host_id,
            },
        }

    @staticmethod
    def _lease_from_response(payload: Mapping[str, Any], fallback: LeaseHolder) -> Lease:
        holder_payload = payload.get("holder") or {}
        holder = LeaseHolder(
            agent=str(holder_payload.get("agent", fallback.agent)),
            harness=str(holder_payload.get("harness", fallback.harness)),
            instance_id=str(holder_payload.get("instance_id", fallback.instance_id)),
            process_id=(
                int(holder_payload["process_id"])
                if holder_payload.get("process_id") is not None
                else fallback.process_id
            ),
            task_id=holder_payload.get("task_id", fallback.task_id),
            holder_kind=HolderKind(holder_payload.get("holder_kind", fallback.holder_kind.value)),
            host_id=holder_payload.get("host_id", fallback.host_id),
        )
        holder.validate()
        return Lease(
            stream_id=str(payload["stream_id"]),
            session_id=str(payload["session_id"]),
            lease_id=str(payload["lease_id"]),
            generation=int(payload["generation"]),
            fencing_token=int(payload["fencing_token"]),
            holder=holder,
            heartbeat_at=str(payload["heartbeat_at"]),
            expires_at=str(payload["expires_at"]),
            ttl_seconds=int(payload["ttl_seconds"]),
            version=int(payload["version"]),
        )

    def claim(
        self,
        *,
        stream_id: str,
        holder: LeaseHolder,
        lineage_id: str,
        ttl_seconds: int = 900,
        session_id: str | None = None,
        lease_id: str | None = None,
        digest_limit: int = 20,
    ) -> tuple[Lease, dict[str, Any]]:
        # A health read is deliberate: a failed preflight cannot have mutated a lease.
        health = self.health()
        if health.get("ok") is not True:
            raise RemoteSupervisorError("Monitor API health check failed; no remote claim was made")
        session_id = session_id or f"session-{uuid.uuid4().hex}"
        lease_id = lease_id or f"lease-{uuid.uuid4().hex}"
        holder_payload = {
            "agent": holder.agent,
            "harness": holder.harness,
            "instance_id": holder.instance_id,
            "task_id": holder.task_id,
            "process_id": holder.process_id,
            "holder_kind": holder.holder_kind.value,
            "host_id": holder.host_id,
        }
        response = self._request(
            "POST",
            f"/api/epics/v1/{stream_id}/claim",
            {
                "session_id": session_id,
                "lease_id": lease_id,
                "lineage_id": lineage_id,
                "ttl_seconds": ttl_seconds,
                "digest_limit": digest_limit,
                **holder_payload,
            },
        )
        lease_payload = response.get("lease")
        if not isinstance(lease_payload, dict):
            raise RemoteSupervisorError("Monitor claim response omitted its lease")
        return self._lease_from_response(lease_payload, holder), response

    def heartbeat(self, lease: Lease) -> Lease:
        response = self._request(
            "POST",
            f"/api/epics/v1/{lease.stream_id}/heartbeat",
            self._lease_payload(lease),
        )
        payload = response.get("lease")
        if not isinstance(payload, dict):
            raise RemoteSupervisorError("Monitor heartbeat response omitted its lease")
        return self._lease_from_response(payload, lease.holder)

    def handoff(
        self,
        lease: Lease,
        *,
        entry_type: EntryType | str,
        body: str,
        idempotency_key: str,
        refs: list[dict[str, Any]] | None = None,
        digest_limit: int = 20,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/epics/v1/{lease.stream_id}/handoff",
            {
                **self._lease_payload(lease),
                "type": EntryType(entry_type).value,
                "body": body,
                "idempotency_key": idempotency_key,
                "refs": refs or [],
                "digest_limit": digest_limit,
            },
        )

    def release(
        self,
        lease: Lease | None = None,
        *,
        stream_id: str | None = None,
        force: bool = False,
        actor_agent: str | None = None,
        actor_host_id: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if force:
            if not stream_id:
                raise RemoteSupervisorError("--force requires --stream")
            payload: dict[str, Any] = {
                "force": True,
                "actor_agent": actor_agent,
                "actor_host_id": actor_host_id,
                "reason": reason,
            }
        else:
            if lease is None:
                raise RemoteSupervisorError("release requires the exact lease envelope")
            stream_id = lease.stream_id
            payload = self._lease_payload(lease)
        return self._request("POST", f"/api/epics/v1/{stream_id}/release", payload)

    def stream(self, stream_id: str, *, digest_limit: int = 20) -> dict[str, Any]:
        query = urlencode({"limit": digest_limit})
        return self._request("GET", f"/api/epics/v1/{stream_id}?{query}")

    @staticmethod
    def digest_from_response(response: Mapping[str, Any]) -> StreamDigest:
        digest = response.get("digest")
        if not isinstance(digest, dict):
            raise RemoteSupervisorError("Monitor response omitted its digest")
        return _digest_from_payload(digest)
