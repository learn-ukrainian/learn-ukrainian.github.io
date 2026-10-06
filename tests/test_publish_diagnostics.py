"""Read-only diagnostic projections for scripts.publish (#9792), with no gh calls."""

import json
import subprocess

import pytest

from scripts.opsec.prepublish import PublishBlocked
from scripts.publish import github as pub


def alert(path="scripts/example.py", number=7, security_severity="high"):
    return {
        "number": number,
        "state": "fixed",
        "html_url": f"https://github.com/unit/public/security/code-scanning/{number}",
        "rule": {"id": "py/fixture", "severity": "error", "security_severity_level": security_severity},
        "most_recent_instance": {
            "state": "open",
            "location": {"path": path, "start_line": 42},
            "message": {"text": "Fixture finding."},
        },
        "dismissed_by": {"login": "private-account"},
    }


def transport(pages, calls):
    def run(argv, **kwargs):
        calls.append(argv)
        # Exercise the fixed jq projection independently against real API-shaped
        # fixtures, including multiple pages and metadata that must be omitted.
        assert kwargs["capture_output"] and kwargs["text"]
        assert "--slurp" not in argv  # gh refuses --slurp together with --jq
        output = ""
        for page in pages:
            result = subprocess.run(
                ["jq", "-c", argv[argv.index("--jq") + 1]],
                input=json.dumps(page),
                text=True,
                capture_output=True,
                timeout=5,
            )
            if result.returncode:
                return result
            output += result.stdout
        return subprocess.CompletedProcess(argv, 0, output, "")

    return run


@pytest.mark.parametrize(
    "fields,query",
    [
        ({"number": 9781}, "state=open&pr=9781"),
        ({"ref": "refs/heads/feature.test"}, "state=open&ref=refs%2Fheads%2Ffeature.test"),
    ],
)
def test_alerts_get_selector_and_complete_projection(fields, query):
    calls = []
    result = pub.read(
        "code-scanning-alerts",
        repo="unit/public",
        runner=transport([[alert()], [alert(number=8, security_severity=None)]], calls),
        capture_output=True,
        text=True,
        **fields,
    )
    assert result.returncode == 0, result.stderr
    assert calls[0][:5] == [
        "gh",
        "api",
        "--method",
        "GET",
        "repos/unit/public/code-scanning/alerts?" + query + "&per_page=100",
    ]
    assert calls[0][5:7] == ["--paginate", "--jq"]
    rows = [row for page in result.stdout.splitlines() for row in json.loads(page)]
    assert rows == [
        {
            "rule_id": "py/fixture",
            "severity": "high",
            "state": "open",
            "file": "scripts/example.py",
            "start_line": 42,
            "message": "Fixture finding.",
            "html_path": "security/code-scanning/7",
        },
        {
            "rule_id": "py/fixture",
            "severity": "error",
            "state": "open",
            "file": "scripts/example.py",
            "start_line": 42,
            "message": "Fixture finding.",
            "html_path": "security/code-scanning/8",
        },
    ]


def test_annotations_get_and_complete_projection():
    calls = []
    pages = [
        [
            {
                "path": "scripts/example.py",
                "start_line": 4,
                "end_line": 8,
                "annotation_level": "failure",
                "message": "Fixture.",
                "blob_href": "https://api.github.com/private",
            }
        ],
        [
            {
                "path": ".github/workflows/codeql.yml",
                "start_line": 2,
                "annotation_level": "warning",
                "message": "Another.",
            }
        ],
    ]
    result = pub.read(
        "check-annotations",
        repo="unit/public",
        number=123,
        runner=transport(pages, calls),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert calls[0][:5] == ["gh", "api", "--method", "GET", "repos/unit/public/check-runs/123/annotations?per_page=100"]
    assert [row for page in result.stdout.splitlines() for row in json.loads(page)] == [
        {"path": "scripts/example.py", "line": 4, "level": "failure", "message": "Fixture."},
        {"path": ".github/workflows/codeql.yml", "line": 2, "level": "warning", "message": "Another."},
    ]


def test_legacy_alert_html_path():
    row = alert()
    row["html_url"] = "https://github.com/unit/public/code-scanning/7"
    result = pub.read(
        "code-scanning-alerts",
        repo="unit/public",
        number=1,
        runner=transport([[row]], []),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["html_path"] == "code-scanning/7"


@pytest.mark.parametrize(
    "html_url",
    [
        "https://other.invalid/unit/public/code-scanning/7",
        "https://github.com/unit/public/security/code-scanning/../7",
        "https://github.com/unit/public/security/code-scanning/7/extra",
        "https://github.com/unit/public/security/code-scanning/7?token=fixture",
        "",
        None,
    ],
)
def test_unsafe_alert_html_paths_refused(html_url):
    row = alert()
    row["html_url"] = html_url
    result = pub.read(
        "code-scanning-alerts",
        repo="unit/public",
        number=1,
        runner=transport([[row]], []),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not result.stdout
    assert not html_url or html_url not in result.stderr


@pytest.mark.parametrize("operation", ["code-scanning-alerts", "check-annotations"])
def test_empty_diagnostics(operation):
    result = pub.read(
        operation,
        repo="unit/public",
        number=1,
        runner=transport([[]], []),
        capture_output=True,
        text=True,
        paginate=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == []


@pytest.mark.parametrize("operation", ["code-scanning-alerts", "check-annotations"])
@pytest.mark.parametrize(
    "path",
    [
        "/private/file.py",
        "../file.py",
        "a/../file.py",
        "./file.py",
        "C:/file.py",
        "a\\file.py",
        "https://other.invalid/file.py",
        "a//file.py",
        "a\nfile.py",
        "",
        None,
    ],
)
def test_non_relative_diagnostic_paths_fail_closed(operation, path):
    row = (
        alert(path)
        if operation == "code-scanning-alerts"
        else {"path": path, "start_line": 1, "annotation_level": "failure", "message": "Fixture."}
    )
    result = pub.read(
        operation, repo="unit/public", number=1, runner=transport([[row]], []), capture_output=True, text=True
    )
    assert result.returncode != 0
    assert not result.stdout
    assert path is None or path == "" or path not in result.stderr


@pytest.mark.parametrize(
    "operation,fields",
    [
        ("code-scanning-alerts", {}),
        ("code-scanning-alerts", {"number": 1, "ref": "main"}),
        ("code-scanning-alerts", {"number": 0}),
        ("code-scanning-alerts", {"number": True}),
        ("code-scanning-alerts", {"ref": "main&state=all"}),
        ("code-scanning-alerts", {"ref": "refs/../main"}),
        ("code-scanning-alerts", {"ref": "refs//main"}),
        ("code-scanning-alerts", {"ref": "main", "method": "POST"}),
        ("check-annotations", {"number": "1/annotations"}),
        ("check-annotations", {"ref": "main"}),
        ("check-annotations", {"number": -1}),
        ("check-annotations", {"number": 1, "path": "extra"}),
    ],
)
def test_diagnostic_invalid_fields_never_send(operation, fields):
    with pytest.raises(PublishBlocked):
        pub.read(operation, repo="unit/public", runner=lambda *a, **k: pytest.fail("transport called"), **fields)


@pytest.mark.parametrize("operation", ["code-scanning-alerts", "check-annotations"])
def test_diagnostic_slurp_refused_before_transport(operation):
    with pytest.raises(PublishBlocked, match="slurp is unsupported"):
        pub.read(
            operation, repo="unit/public", number=1, slurp=True, runner=lambda *a, **k: pytest.fail("transport called")
        )


@pytest.mark.parametrize(
    "operation,selector",
    [
        ("code-scanning-alerts", ["--number", "9781"]),
        ("code-scanning-alerts", ["--ref", "refs/heads/main"]),
        ("check-annotations", ["--number", "123"]),
    ],
)
def test_diagnostic_cli(operation, selector):
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0)

    assert pub.main(["read", operation, "--repo", "unit/public", *selector], runner=run) == 0
    assert calls[0][2:4] == ["--method", "GET"]


def test_diagnostic_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        pub.main(["read", "--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "code-scanning-alerts" in help_text and "check-annotations" in help_text
    assert "either --ref or --number" in help_text
