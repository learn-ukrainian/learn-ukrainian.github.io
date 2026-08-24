"""Token-aware OPSEC scanning for Monitor API response values.

The scanner is intentionally a consumer-side utility.  It does not rewrite a
response or make decisions about which response fields are safe; callers pass
the body, header values, and optional ``_telemetry`` value that they want
checked.  Findings retain the operation and leaf field path so a route sweep
can identify the owning emitter without exposing a larger response in its
failure output.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

DEFAULT_OPERATION = "<unknown>"
BOUNDED_FILESYSTEM_ROOTS = (
    "/home",
    "/Users",
    "/Volumes",
    "/private",
    "/opt",
    "/srv",
    "/tmp",
    "/var",
)

_BODY_PATH = "body"
_HEADERS_PATH = "headers"
_TELEMETRY_PATH = "_telemetry"
_MISSING = object()

_SHA_RE = re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64})(?![0-9A-Fa-f])")
_RFC3339_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})"
    r"(?![A-Za-z0-9_])"
)
_EPIC_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])epic:[0-9]+(?![A-Za-z0-9_])")
_API_ROUTE_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])/api(?:/[^\s\"'<>]*)?")
_ISO_DURATION_RE = re.compile(
    r"(?<![A-Za-z0-9_])-?P"
    r"(?=(?:[0-9]+(?:\.[0-9]+)?[YMWD]|T[0-9]+(?:\.[0-9]+)?[HMS]))"
    r"(?:[0-9]+(?:\.[0-9]+)?Y)?"
    r"(?:[0-9]+(?:\.[0-9]+)?M)?"
    r"(?:[0-9]+(?:\.[0-9]+)?W)?"
    r"(?:[0-9]+(?:\.[0-9]+)?D)?"
    r"(?:T(?:[0-9]+(?:\.[0-9]+)?H)?(?:[0-9]+(?:\.[0-9]+)?M)?(?:[0-9]+(?:\.[0-9]+)?S)?)?"
    r"(?![A-Za-z0-9_])",
    re.IGNORECASE,
)

# This is only a candidate tokenizer.  Whether a candidate is an address is
# decided by ipaddress.ip_address below; the regex must not become a second,
# subtly different IP parser.  Bracketed addresses keep an optional port as a
# single candidate.  Unbracketed IPv4:port is handled by the same parser.
_IP_CANDIDATE_RE = re.compile(r"(?<![A-Za-z0-9])(?:\[[0-9A-Fa-f:.%]+\](?::[0-9]{1,5})?|[0-9A-Fa-f:.]+)(?![A-Za-z0-9])")
_FILESYSTEM_PATH_RE = re.compile(
    rf"(?<![A-Za-z0-9/])/(?P<root>{'|'.join(re.escape(root[1:]) for root in BOUNDED_FILESYSTEM_ROOTS)})"
    r"(?![A-Za-z0-9_-])"
    r"(?P<tail>/[^\s\"'<>]*)?"
)
_USER_AT_HOST_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"(?P<token>[A-Za-z0-9_.-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::[0-9]{1,5})?)"
    r"(?![A-Za-z0-9_.-])"
)
_SSH_ALIAS_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_.@-])ssh[ \t]+"
    r"(?P<alias>[A-Za-z0-9][A-Za-z0-9._-]*)(?![A-Za-z0-9_.:@-])"
)
_HOST_PORT_RE = re.compile(
    r"(?<![A-Za-z0-9_.@-])"
    r"(?P<host>[A-Za-z](?:[A-Za-z0-9.-]*[A-Za-z0-9])?):(?P<port>[0-9]{1,5})"
    r"(?![0-9A-Za-z_.%])"
)
_TRANSCRIPT_FILENAME_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_.-])"
    r"(?P<filename>[A-Za-z0-9][A-Za-z0-9_.-]*\.jsonl(?:\.gz)?)"
    r"(?![A-Za-z0-9_.-])"
)

_SAFE_FIELD_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_SSH_PROSE_WORDS = frozenset(
    {"a", "an", "and", "as", "by", "for", "from", "host", "in", "on", "or", "probes", "the", "to"}
)
_CSS_NUMERIC_PROPERTIES = frozenset(
    {
        "align-items",
        "border",
        "border-bottom",
        "border-bottom-left-radius",
        "border-bottom-right-radius",
        "border-left",
        "box-shadow",
        "border-radius",
        "bottom",
        "column-gap",
        "flex",
        "font-size",
        "font-weight",
        "gap",
        "grid-column",
        "grid-row",
        "height",
        "inset",
        "left",
        "line-height",
        "margin",
        "margin-bottom",
        "margin-left",
        "margin-right",
        "margin-top",
        "max-height",
        "max-width",
        "min-height",
        "min-width",
        "opacity",
        "padding",
        "padding-bottom",
        "padding-left",
        "padding-right",
        "padding-top",
        "right",
        "top",
        "width",
        "z-index",
    }
)


@dataclass(frozen=True, slots=True)
class Finding:
    """One OPSEC match in one string-valued response leaf.

    ``start`` and ``end`` are offsets in the leaf value, not in a serialized
    response.  The operation and field path are deliberately separate: a
    caller can scan the same value for more than one route operation while a
    nested body/header/telemetry path remains unambiguous.
    """

    operation: str
    field_path: str
    kind: str
    token: str
    start: int
    end: int

    @property
    def path(self) -> str:
        """Compatibility alias for callers that call the field path ``path``."""
        return self.field_path

    @property
    def field(self) -> str:
        """Compatibility alias for callers that call the field path ``field``."""
        return self.field_path

    @property
    def value(self) -> str:
        """Compatibility alias for the matched token."""
        return self.token

    @property
    def match(self) -> str:
        """Compatibility alias for the matched token."""
        return self.token

    @property
    def category(self) -> str:
        """Compatibility alias for the finding kind."""
        return self.kind

    @property
    def source(self) -> str:
        """Return the response section containing this finding."""
        return self.field_path.split(".", 1)[0].split("[", 1)[0]

    def as_dict(self) -> dict[str, Any]:
        """Return a small JSON-compatible representation for test reports."""
        return {
            "operation": self.operation,
            "field_path": self.field_path,
            "kind": self.kind,
            "token": self.token,
            "start": self.start,
            "end": self.end,
        }


# A descriptive name is useful to integrations while ``Finding`` remains a
# short import for tests and route-sweep failure reports.
OpsecFinding = Finding


@dataclass(frozen=True, slots=True)
class _Candidate:
    start: int
    end: int
    kind: str
    token: str
    priority: int


def _field_path(parent: str, key: object) -> str:
    key_text = str(key)
    if _SAFE_FIELD_KEY_RE.fullmatch(key_text):
        return f"{parent}.{key_text}"
    return f"{parent}[{key_text!r}]"


def _iter_string_leaves(
    value: Any,
    field_path: str,
    seen: set[int] | None = None,
) -> Iterable[tuple[str, str]]:
    """Yield string leaves with stable JSON-like paths.

    API bodies and telemetry are JSON-compatible, but accepting bytes makes
    the helper usable with header adapters without forcing a separate caller.
    Cycles are ignored rather than allowing a malformed test fixture to hang
    a route sweep.
    """
    active = set() if seen is None else seen
    if isinstance(value, str):
        yield field_path, value
        return
    if isinstance(value, (bytes, bytearray)):
        yield field_path, bytes(value).decode("utf-8", errors="replace")
        return
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in active:
            return
        next_active = active | {marker}
        for key, child in value.items():
            yield from _iter_string_leaves(child, _field_path(field_path, key), next_active)
        return
    if isinstance(value, (list, tuple)):
        marker = id(value)
        if marker in active:
            return
        next_active = active | {marker}
        for index, child in enumerate(value):
            yield from _iter_string_leaves(child, f"{field_path}[{index}]", next_active)


def _iter_canaries(canaries: object) -> Iterable[str]:
    if canaries is None:
        return
    if isinstance(canaries, str):
        if canaries:
            yield canaries
        return
    if isinstance(canaries, Mapping):
        for value in canaries.values():
            yield from _iter_canaries(value)
        return
    if isinstance(canaries, Iterable):
        for value in canaries:
            yield from _iter_canaries(value)


def _protected_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Return spans for identifiers and syntax that are intentionally safe."""
    spans = [
        (match.start(), match.end())
        for pattern in (_SHA_RE, _RFC3339_RE, _EPIC_RE, _API_ROUTE_RE, _ISO_DURATION_RE)
        for match in pattern.finditer(text)
    ]
    if not spans:
        return ()
    spans.sort()
    merged: list[tuple[int, int]] = [spans[0]]
    for start, end in spans[1:]:
        previous_start, previous_end = merged[-1]
        if start <= previous_end:
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return tuple(merged)


def _overlaps(start: int, end: int, spans: Iterable[tuple[int, int]]) -> bool:
    return any(start < span_end and span_start < end for span_start, span_end in spans)


def _ip_version(candidate: str) -> int | None:
    """Return the address version for a candidate, using ipaddress as parser."""
    value = candidate
    if value.startswith("["):
        closing = value.find("]")
        if closing < 0:
            return None
        value = value[1:closing]

    if "." not in value and ":" not in value:
        return None

    try:
        return ipaddress.ip_address(value).version
    except ValueError:
        pass

    # An IPv4 address with a port is not accepted as one ipaddress token.  Do
    # not parse a host by hand: only the address portion is split, then the
    # address itself is still validated by ipaddress.
    if ":" not in value:
        return None
    address, separator, port = value.rpartition(":")
    if not separator or not port.isdecimal() or not address or len(port) > 5:
        return None
    try:
        return ipaddress.ip_address(address).version
    except ValueError:
        return None


def _trim_path_token(match: re.Match[str]) -> tuple[int, int, str]:
    raw = match.group(0)
    token = raw.rstrip(".,;:!?)]}")
    end = match.start() + len(token)
    return match.start(), end, token


def _is_css_numeric_property(text: str, match: re.Match[str]) -> bool:
    """Avoid treating CSS declarations as hostname/port values."""
    if match.group("host").lower() not in _CSS_NUMERIC_PROPERTIES:
        return False
    prefix = text[max(0, match.start() - 256) : match.start()]
    if prefix.rfind("{") > prefix.rfind("}"):
        return True
    return re.search(r"\bstyle\s*=", prefix, re.IGNORECASE) is not None


def _select_candidates(candidates: Iterable[_Candidate]) -> list[_Candidate]:
    """Deduplicate overlapping descriptions while retaining the strongest one."""
    unique = {(item.start, item.end, item.kind, item.token): item for item in candidates}
    ordered = sorted(
        unique.values(),
        key=lambda item: (-item.priority, item.start, -(item.end - item.start), item.kind),
    )
    selected: list[_Candidate] = []
    for candidate in ordered:
        if any(candidate.start < item.end and item.start < candidate.end for item in selected):
            continue
        selected.append(candidate)
    return sorted(selected, key=lambda item: (item.start, item.end, item.kind))


def scan_text(
    text: str,
    *,
    operation: str = DEFAULT_OPERATION,
    field_path: str = "body",
    canaries: object = (),
) -> list[Finding]:
    """Scan one text value and preserve its operation/field provenance."""
    if not isinstance(text, str):
        return []

    protected = _protected_spans(text)
    candidates: list[_Candidate] = []

    for canary in dict.fromkeys(_iter_canaries(canaries)):
        for match in re.finditer(re.escape(canary), text):
            candidates.append(_Candidate(match.start(), match.end(), "canary", match.group(0), 100))

    for match in _FILESYSTEM_PATH_RE.finditer(text):
        start, end, token = _trim_path_token(match)
        if token and not _overlaps(start, end, protected):
            candidates.append(_Candidate(start, end, "filesystem-root", token, 80))

    for match in _USER_AT_HOST_RE.finditer(text):
        host = match.group("token").rsplit("@", 1)[-1].split(":", 1)[0]
        if not host.isdigit() and not _overlaps(match.start(), match.end(), protected):
            candidates.append(_Candidate(match.start(), match.end(), "user-at-host", match.group(0), 75))

    for match in _IP_CANDIDATE_RE.finditer(text):
        raw = match.group(0)
        candidate = raw if raw.startswith("[") else raw.rstrip(".")
        if not candidate or _overlaps(match.start(), match.start() + len(candidate), protected):
            continue
        version = _ip_version(candidate)
        if version is not None:
            candidates.append(
                _Candidate(
                    match.start(),
                    match.start() + len(candidate),
                    f"ipv{version}",
                    candidate,
                    70,
                )
            )

    for match in _HOST_PORT_RE.finditer(text):
        if (
            not _is_css_numeric_property(text, match)
            and 0 < int(match.group("port")) <= 65535
            and not _overlaps(match.start(), match.end(), protected)
        ):
            candidates.append(_Candidate(match.start(), match.end(), "host-port", match.group(0), 60))

    for match in _SSH_ALIAS_RE.finditer(text):
        alias = match.group("alias").rstrip(".")
        start = match.start("alias")
        end = match.end("alias")
        if alias.lower() not in _SSH_PROSE_WORDS and not _overlaps(start, end, protected):
            candidates.append(_Candidate(start, end, "ssh-alias", alias, 50))

    for match in _TRANSCRIPT_FILENAME_RE.finditer(text):
        if not _overlaps(match.start(), match.end(), protected):
            candidates.append(_Candidate(match.start(), match.end(), "transcript-filename", match.group(0), 40))

    return [
        Finding(
            operation=str(operation),
            field_path=field_path,
            kind=candidate.kind,
            token=candidate.token,
            start=candidate.start,
            end=candidate.end,
        )
        for candidate in _select_candidates(candidates)
    ]


def scan_value(
    value: Any,
    *,
    operation: str = DEFAULT_OPERATION,
    field_path: str = "body",
    canaries: object = (),
) -> list[Finding]:
    """Recursively scan JSON-compatible values, retaining each leaf path."""
    findings: list[Finding] = []
    for leaf_path, text in _iter_string_leaves(value, field_path):
        findings.extend(
            scan_text(
                text,
                operation=operation,
                field_path=leaf_path,
                canaries=canaries,
            )
        )
    return findings


def scan_body(
    body: Any,
    *,
    operation: str = DEFAULT_OPERATION,
    canaries: object = (),
) -> list[Finding]:
    """Scan an API response body under the ``body`` provenance root."""
    return scan_value(body, operation=operation, field_path=_BODY_PATH, canaries=canaries)


def scan_headers(
    headers: Any,
    *,
    operation: str = DEFAULT_OPERATION,
    canaries: object = (),
) -> list[Finding]:
    """Scan every response-header value under the ``headers`` root."""
    return scan_value(headers, operation=operation, field_path=_HEADERS_PATH, canaries=canaries)


def scan_telemetry(
    telemetry: Any,
    *,
    operation: str = DEFAULT_OPERATION,
    canaries: object = (),
) -> list[Finding]:
    """Scan the optional ``_telemetry`` section under its own root."""
    return scan_value(telemetry, operation=operation, field_path=_TELEMETRY_PATH, canaries=canaries)


def scan_response(
    operation: str = DEFAULT_OPERATION,
    body: Any = _MISSING,
    headers: Any = None,
    telemetry: Any = _MISSING,
    *,
    canaries: object = (),
) -> list[Finding]:
    """Scan body, headers, and telemetry as separate response sections.

    ``body`` may contain a top-level ``_telemetry`` mapping when the caller
    has not supplied ``telemetry`` separately.  It is moved to the dedicated
    provenance root rather than reported as an ordinary body field.
    """
    response_body = None if body is _MISSING else body
    response_telemetry = telemetry
    if isinstance(response_body, Mapping) and _TELEMETRY_PATH in response_body:
        embedded_telemetry = response_body[_TELEMETRY_PATH]
        response_body = {key: value for key, value in response_body.items() if key != _TELEMETRY_PATH}
        if response_telemetry is _MISSING:
            response_telemetry = embedded_telemetry

    findings = scan_body(response_body, operation=operation, canaries=canaries)
    findings.extend(scan_headers(headers, operation=operation, canaries=canaries))
    if response_telemetry is not _MISSING:
        findings.extend(scan_telemetry(response_telemetry, operation=operation, canaries=canaries))
    return findings


def scan_response_fields(
    body: Any = None,
    headers: Any = None,
    telemetry: Any = _MISSING,
    *,
    operation: str = DEFAULT_OPERATION,
    canaries: object = (),
) -> list[Finding]:
    """Body-first wrapper for callers that assemble response fields positionally."""
    return scan_response(operation, body, headers, telemetry, canaries=canaries)


scan_api_response = scan_response
scan = scan_response


__all__ = [
    "BOUNDED_FILESYSTEM_ROOTS",
    "DEFAULT_OPERATION",
    "Finding",
    "OpsecFinding",
    "scan",
    "scan_api_response",
    "scan_body",
    "scan_headers",
    "scan_response",
    "scan_response_fields",
    "scan_telemetry",
    "scan_text",
    "scan_value",
]
