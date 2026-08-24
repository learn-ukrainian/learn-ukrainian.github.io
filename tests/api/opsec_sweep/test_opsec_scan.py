"""Positive and negative corpus for the shared Monitor OPSEC scanner."""

from __future__ import annotations

import pytest

from scripts.api.opsec_scan import scan_response, scan_text

pytestmark = pytest.mark.repo_invariant


def _ipv4(*octets: int) -> str:
    return ".".join(str(octet) for octet in octets)


def _ipv6() -> str:
    return ":".join(("2001", "db8", "0", "0", "0", "0", "0", "17"))


def test_positive_corpus_catches_each_r3_shape() -> None:
    canary = "fixture-opsec-host-synthetic"
    ipv4 = _ipv4(10, 42, 0, 7)
    ipv6 = _ipv6()
    positive = (
        (ipv4, "ipv4"),
        (f"{ipv4}:8443", "ipv4"),
        (f"[{ipv6}]:9443", "ipv6"),
        ("/home/fixture/repository", "filesystem-root"),
        ("/Users/fixture/.claude/projects/session.jsonl", "filesystem-root"),
        ("/Volumes/fixture/store.sqlite", "filesystem-root"),
        ("/private/var/folders/fixture", "filesystem-root"),
        ("/opt/monitor/config", "filesystem-root"),
        ("/srv/monitor/data", "filesystem-root"),
        ("/tmp/fixture", "filesystem-root"),
        ("/var/lib/monitor", "filesystem-root"),
        ("runner@monitor-alias", "user-at-host"),
        ("ssh monitor-alias", "ssh-alias"),
        ("monitor-alias:8765", "host-port"),
        ("session-synthetic.jsonl", "transcript-filename"),
        (canary, "canary"),
    )

    for text, kind in positive:
        findings = scan_text(text, operation="GET /api/opsec", field_path="body.value", canaries=(canary,))
        assert any(finding.kind == kind and finding.token in text for finding in findings), (text, findings)


def test_negative_corpus_exempts_identifiers_timestamps_routes_and_durations() -> None:
    sha1 = "0123456789abcdef" * 2 + "01234567"
    sha256 = "abcdef0123456789" * 4
    negative = (
        sha1,
        f"sha256:{sha256}",
        "2026-08-24T19:12:43Z",
        "2026-08-24T19:12:43.123+02:00",
        "epic:9999",
        "/api/session-streams/v1/health",
        "timeout=PT1H30M",
        "retry-after=P2DT4H",
        "version 1.2.3",
    )

    for text in negative:
        assert scan_text(text, operation="GET /api/opsec", field_path="body.value") == [], text


def test_response_scan_keeps_body_header_and_telemetry_provenance() -> None:
    canary = "planted-route-sweep-canary"
    findings = scan_response(
        "GET /api/health",
        body={"nested": {"repo_root": "/tmp/fixture-root"}, "canary": canary},
        headers={"X-Forwarded-Host": "monitor-alias:8765"},
        telemetry={"transcript": "session-synthetic.jsonl"},
        canaries=(canary,),
    )

    assert [(finding.operation, finding.field_path) for finding in findings] == [
        ("GET /api/health", "body.nested.repo_root"),
        ("GET /api/health", "body.canary"),
        ("GET /api/health", "headers.X-Forwarded-Host"),
        ("GET /api/health", "_telemetry.transcript"),
    ]
    assert {finding.kind for finding in findings} == {"canary", "filesystem-root", "host-port", "transcript-filename"}


def test_response_scan_extracts_embedded_telemetry_as_a_separate_section() -> None:
    findings = scan_response(
        "GET /api/state",
        body={"ok": True, "_telemetry": {"newest_transcript": "current.jsonl"}},
    )

    assert [(finding.field_path, finding.token) for finding in findings] == [
        ("_telemetry.newest_transcript", "current.jsonl")
    ]


def test_ip_parser_does_not_treat_colons_in_timestamps_or_durations_as_addresses() -> None:
    text = "created=2026-08-24T19:12:43Z; timeout=PT30S; route=/api/health"
    assert scan_text(text, operation="GET /api/health", field_path="body") == []


def test_host_port_scanner_ignores_css_but_keeps_bare_hostnames() -> None:
    assert scan_text(
        '<style>.card { font-size:13; }</style>',
        operation="dashboard:synthetic.html",
    ) == []
    findings = scan_text("width:8765", operation="GET /api/health", field_path="body")
    assert [(finding.kind, finding.token) for finding in findings] == [("host-port", "width:8765")]
