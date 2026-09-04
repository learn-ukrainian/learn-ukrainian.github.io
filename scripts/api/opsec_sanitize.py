"""Route-wide OPSEC sanitizer for leaked absolute filesystem paths.

The scanner in ``opsec_scan`` is the detector of record.  This module is the
rewriter: it replaces filesystem-root tokens the scanner would report with an
opaque placeholder so Monitor JSON responses cannot echo host paths.

It is intentionally narrower than the scanner.  Host ids, loopback dashboard
URLs, and other non-path findings stay the emitters' responsibility.  The
rewriter exists so a pass-through or a still-open field-shape burn-down cannot
re-emit an absolute path that the scanner already knows how to name.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from scripts.api.opsec_scan import scan_text

REDACTED_ABSOLUTE_PATH = "[redacted-path]"
_UNCHANGED = object()


def sanitize_text(text: str) -> str:
    """Replace leaked absolute filesystem-root tokens in one string."""
    if not text:
        return text
    findings = [finding for finding in scan_text(text) if finding.kind == "filesystem-root"]
    if not findings:
        return text
    rewritten = text
    for finding in sorted(findings, key=lambda item: item.start, reverse=True):
        rewritten = rewritten[: finding.start] + REDACTED_ABSOLUTE_PATH + rewritten[finding.end :]
    return rewritten


def sanitize_document(value: Any) -> Any:
    """Redact paths, scanning each distinct string once per response.

    Projection items and attention rows repeat the same metadata thousands of
    times. Keep this memo local: no public/private data or scanner result can
    survive into another request.
    """
    return _sanitize_document(value, {})


def _sanitize_document(value: Any, scanned: dict[str, str]) -> Any:
    if isinstance(value, str):
        if value not in scanned:
            scanned[value] = sanitize_text(value)
        sanitized = scanned[value]
        # Preserve unchanged object identity, including equal distinct strings.
        return value if sanitized == value else sanitized
    if isinstance(value, Mapping):
        changed = False
        rewritten: dict[Any, Any] = {}
        for key, child in value.items():
            sanitized = _sanitize_document(child, scanned)
            rewritten[key] = sanitized
            if sanitized is not child:
                changed = True
        return rewritten if changed else value
    if isinstance(value, list):
        rewritten_list = [_sanitize_document(child, scanned) for child in value]
        if any(left is not right for left, right in zip(rewritten_list, value, strict=True)):
            return rewritten_list
        return value
    if isinstance(value, tuple):
        rewritten_tuple = tuple(_sanitize_document(child, scanned) for child in value)
        if any(left is not right for left, right in zip(rewritten_tuple, value, strict=True)):
            return rewritten_tuple
        return value
    return value


def _is_json_content(response: Response) -> bool:
    if isinstance(response, JSONResponse):
        return True
    content_type = response.headers.get("content-type", "")
    return "application/json" in content_type


def _response_body_bytes(response: Response) -> bytes:
    raw = getattr(response, "body", None)
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    return b""


async def _read_response_body(response: Response) -> bytes:
    raw = _response_body_bytes(response)
    if raw:
        return raw
    iterator = getattr(response, "body_iterator", None)
    if iterator is None:
        return b""
    chunks: list[bytes] = []
    async for chunk in iterator:
        if isinstance(chunk, bytes):
            chunks.append(chunk)
        else:
            chunks.append(str(chunk).encode("utf-8"))
    return b"".join(chunks)


def _rebuild_json_response(response: Response, content: Any, raw: bytes) -> Response:
    headers = {key: value for key, value in response.headers.items() if key.lower() != "content-length"}
    if content is _UNCHANGED:
        return Response(
            content=raw,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
            background=response.background,
        )
    return JSONResponse(
        content=content,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type,
        background=response.background,
    )


def sanitize_json_bytes(raw: bytes) -> tuple[Any, bytes]:
    """Return ``(sanitized_payload_or_sentinel, original_bytes)``."""
    if not raw:
        return _UNCHANGED, raw
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return _UNCHANGED, raw
    sanitized = sanitize_document(payload)
    if sanitized == payload:
        return _UNCHANGED, raw
    return sanitized, raw


async def sanitize_json_response(response: Response) -> Response:
    """Return a JSON response whose body has leaked absolute paths stripped."""
    if not _is_json_content(response):
        return response
    raw = await _read_response_body(response)
    sanitized, original = sanitize_json_bytes(raw)
    if sanitized is _UNCHANGED:
        if _response_body_bytes(response):
            return response
        return _rebuild_json_response(response, _UNCHANGED, original)
    return _rebuild_json_response(response, sanitized, original)


async def opsec_path_sanitizer_middleware(
    request: Request,
    call_next: Callable[[Request], Any],
) -> Response:
    """Strip leaked absolute paths from JSON Monitor responses."""
    response = await call_next(request)
    return await sanitize_json_response(response)
