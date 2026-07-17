"""Network fetch/parse worker (#5230 PR3).

Operates only against the durable network cache. Never opens ``sources.db``.
Uses request-level fenced claims; 429 releases to ``retry_scheduled`` and sets a
host-wide cooldown without touching packet transport state.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import (
    ADAPTER_VERSION,
    NORMALIZER_VERSION,
    PARSED_SCHEMA_VERSION,
    PARSER_VERSION,
    REQUEST_POLICY_VERSION,
)
from scripts.lexicon.runner.network_cache import (
    CacheCasStatus,
    NetworkCache,
    compute_request_key,
)
from scripts.lexicon.runner.sources_guard import (
    SourcesDbForbiddenError,
    guard_network_worker,
    open_sources_db_refused,
)
from scripts.lexicon.runner.transport import (
    BundleItem,
    PacketItem,
    build_bundle,
    item_content_hash,
    read_packet,
)

FetchFn = Callable[[str, str, bytes | None, dict[str, str]], tuple[int, dict[str, str], bytes]]
ParseFn = Callable[[bytes, Mapping[str, Any]], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class NetworkWorkItem:
    lemma_id: str
    method: str
    url: str
    request_body: bytes | None = None
    response_affecting_headers: dict[str, str] | None = None
    request_meta: dict[str, Any] | None = None

    @property
    def request_key(self) -> str:
        return compute_request_key(
            method=self.method,
            url=self.url,
            request_body=self.request_body,
            response_affecting_headers=self.response_affecting_headers,
        )

    def as_packet_item(self) -> PacketItem:
        request = {
            "adapter_version": ADAPTER_VERSION,
            "method": self.method.upper(),
            "request_body_b64": None
            if self.request_body is None
            else base64.b64encode(self.request_body).decode("ascii"),
            "request_policy_version": REQUEST_POLICY_VERSION,
            "response_affecting_headers": dict(self.response_affecting_headers or {}),
            "url": self.url,
            **dict(self.request_meta or {}),
        }
        return PacketItem.from_request(self.lemma_id, self.request_key, request)


@dataclass(slots=True)
class FetchOutcome:
    lemma_id: str
    request_key: str
    status: str  # done | retry_scheduled | failed_terminal | cache_hit_parsed
    result: dict[str, Any] | None = None
    result_hash: str | None = None
    error_code: str | None = None
    fetched: bool = False
    status_code: int | None = None


def refuse_sources_db(path: Path | str) -> None:
    """Public hard guard used by network worker entry points and tests."""
    open_sources_db_refused(path)


def default_parse(body: bytes, request: Mapping[str, Any]) -> dict[str, Any]:
    """Minimal deterministic parser: JSON if possible, else text envelope."""
    text = body.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"text": text}
    return {
        "lemma_id": request.get("lemma_id"),
        "parser_version": PARSER_VERSION,
        "payload": parsed,
        "request_key": request.get("request_key"),
        "url": request.get("url"),
    }


def process_request(
    cache: NetworkCache,
    item: NetworkWorkItem,
    *,
    owner: str,
    fetch: FetchFn,
    parse: ParseFn = default_parse,
    host: str = "default",
    now: float | None = None,
    cooldown_seconds: float = 60.0,
) -> FetchOutcome:
    """Claim → (cache hit | fetch+atomic cache) → parse. Never opens sources.db."""
    with guard_network_worker():
        request_key = item.request_key
        claim = cache.claim_request(request_key, owner, now=now, host=host)
        if claim.status is CacheCasStatus.HOST_COOLDOWN:
            return FetchOutcome(
                lemma_id=item.lemma_id,
                request_key=request_key,
                status="retry_scheduled",
                error_code="host_cooldown",
            )
        if claim.status is CacheCasStatus.ATTEMPT_CAP_EXHAUSTED:
            return FetchOutcome(
                lemma_id=item.lemma_id,
                request_key=request_key,
                status="failed_terminal",
                error_code="attempt_cap_exhausted",
            )
        if not claim.ok:
            return FetchOutcome(
                lemma_id=item.lemma_id,
                request_key=request_key,
                status="failed_terminal",
                error_code=claim.status.value,
            )

        body: bytes
        body_sha: str
        status_code: int
        fetched = False

        if claim.is_cache_hit:
            assert claim.cached_body is not None and claim.body_sha256 is not None
            body = claim.cached_body
            body_sha = claim.body_sha256
            status_code = int(claim.status_code or 200)
        else:
            assert claim.lease_generation is not None
            cache.record_fetch_attempt()
            status_code, resp_headers, body = fetch(
                item.method,
                item.url,
                item.request_body,
                dict(item.response_affecting_headers or {}),
            )
            fetched = True
            if status_code == 429:
                ts = time.time() if now is None else float(now)
                cache.commit_retry_scheduled(
                    request_key,
                    owner,
                    claim.lease_generation,
                    host=host,
                    next_allowed_at=ts + float(cooldown_seconds),
                    error_code="http_429",
                    now=ts,
                )
                return FetchOutcome(
                    lemma_id=item.lemma_id,
                    request_key=request_key,
                    status="retry_scheduled",
                    error_code="http_429",
                    fetched=True,
                    status_code=429,
                )
            raw = cache.commit_raw(
                request_key,
                owner,
                claim.lease_generation,
                method=item.method,
                url=item.url,
                request_body=item.request_body,
                response_affecting_headers=item.response_affecting_headers,
                status_code=status_code,
                response_headers=resp_headers,
                body=body,
                now=now,
            )
            if not raw.ok:
                return FetchOutcome(
                    lemma_id=item.lemma_id,
                    request_key=request_key,
                    status="failed_terminal",
                    error_code=raw.status.value,
                    fetched=True,
                    status_code=status_code,
                )
            body_sha = hashlib.sha256(body).hexdigest()

        request_ctx = {
            "lemma_id": item.lemma_id,
            "request_key": request_key,
            "url": item.url,
            "method": item.method.upper(),
        }
        parsed = parse(body, request_ctx)
        cache.put_parsed(
            request_key=request_key,
            body_sha256=body_sha,
            parser_version=PARSER_VERSION,
            normalizer_version=NORMALIZER_VERSION,
            schema_version=PARSED_SCHEMA_VERSION,
            parsed_payload=json.dumps(parsed, ensure_ascii=False, sort_keys=True),
            now=now,
        )
        result_body = {
            "lemma_id": item.lemma_id,
            "request_key": request_key,
            "result": parsed,
        }
        return FetchOutcome(
            lemma_id=item.lemma_id,
            request_key=request_key,
            status="done" if not claim.is_cache_hit else "cache_hit_parsed",
            result=parsed,
            result_hash=item_content_hash(result_body),
            fetched=fetched,
            status_code=status_code,
        )


def process_packet_to_bundle(
    cache: NetworkCache,
    packet_path: Path,
    *,
    owner: str,
    fetch: FetchFn,
    output_dir: Path,
    host: str = "default",
    parse: ParseFn = default_parse,
    now: float | None = None,
    cooldown_seconds: float = 60.0,
) -> tuple[Path | None, list[FetchOutcome]]:
    """Fetch/parse every packet item via the cache; emit one result bundle when all done.

    Items that land in ``retry_scheduled`` do not enter the bundle. Returns
    ``(bundle_path_or_None, outcomes)``.
    """
    with guard_network_worker():
        packet = read_packet(packet_path)
        outcomes: list[FetchOutcome] = []
        bundle_items: list[BundleItem] = []
        for entry in packet.items:
            body_b64 = entry["request"].get("request_body_b64")
            req_body = None
            if body_b64:
                req_body = base64.b64decode(body_b64)
            work = NetworkWorkItem(
                lemma_id=entry["lemma_id"],
                method=str(entry["request"].get("method") or "GET"),
                url=str(entry["request"]["url"]),
                request_body=req_body,
                response_affecting_headers=dict(
                    entry["request"].get("response_affecting_headers") or {}
                ),
            )
            # Prefer packet's request_key identity; recompute must match.
            if work.request_key != entry["request_key"]:
                outcomes.append(
                    FetchOutcome(
                        lemma_id=entry["lemma_id"],
                        request_key=entry["request_key"],
                        status="failed_terminal",
                        error_code="request_key_mismatch",
                    )
                )
                continue
            out = process_request(
                cache,
                work,
                owner=owner,
                fetch=fetch,
                parse=parse,
                host=host,
                now=now,
                cooldown_seconds=cooldown_seconds,
            )
            outcomes.append(out)
            if out.result is not None and out.status in {
                "done",
                "cache_hit_parsed",
            }:
                bundle_items.append(
                    BundleItem.from_result(
                        out.lemma_id,
                        out.request_key,
                        out.result,
                    )
                )
        if not bundle_items:
            return None, outcomes
        ref = build_bundle(
            run_id=str(packet.manifest["run_id"]),
            fingerprint=str(packet.manifest["fingerprint"]),
            packet_id=packet.artifact_id,
            packet_generation=int(packet.manifest["generation"]),
            items=bundle_items,
            output_dir=output_dir,
        )
        return ref.path, outcomes


def assert_network_worker_cannot_open_sources(path: Path | str = "sources.db") -> None:
    """Test helper / startup check: always raises for sources.db."""
    try:
        with guard_network_worker():
            refuse_sources_db(path)
    except SourcesDbForbiddenError:
        raise
    raise AssertionError("sources.db guard did not fire")
