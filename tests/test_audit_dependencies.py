from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from scripts.ci.audit_dependencies import (
    audit_node,
    audit_python,
    filter_npm_audit_vulnerabilities,
    load_npm_audit_ignores,
    load_pip_audit_ignores,
    main,
)


def test_load_pip_audit_ignores(tmp_path: Path):
    ignore_file = tmp_path / ".pip-audit-ignore.yaml"
    data = {
        "vulnerabilities": [
            {"id": "CVE-2026-0001", "package": "foo", "reason": "test"},
            {"id": "PYSEC-2026-0002", "package": "bar", "reason": "test2"},
            "CVE-2026-0003",
        ]
    }
    ignore_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    ignores = load_pip_audit_ignores(ignore_file)
    assert ignores == ["CVE-2026-0001", "PYSEC-2026-0002", "CVE-2026-0003"]


def test_load_pip_audit_ignores_missing_file(tmp_path: Path):
    non_existent = tmp_path / "does-not-exist.yaml"
    assert load_pip_audit_ignores(non_existent) == []


def test_load_pip_audit_ignores_empty_file(tmp_path: Path):
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("", encoding="utf-8")
    assert load_pip_audit_ignores(empty_file) == []


def test_load_npm_audit_ignores(tmp_path: Path):
    ignore_file = tmp_path / "npm-audit-ignore.yaml"
    data = {
        "vulnerabilities": [
            {"id": "GHSA-ch52-4w7c-c8xp", "package": "http-cache-semantics", "reason": "test"},
            {"cve": "CVE-2026-9999", "package": "foo", "reason": "test2"},
            {"package": "bar", "reason": "test3"},
            "GHSA-1111-2222-3333",
        ]
    }
    ignore_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    ignores = load_npm_audit_ignores(ignore_file)
    assert "GHSA-CH52-4W7C-C8XP" in ignores
    assert "CVE-2026-9999" in ignores
    assert "bar" in ignores
    assert "GHSA-1111-2222-3333" in ignores


def test_load_npm_audit_ignores_missing_and_empty(tmp_path: Path):
    assert load_npm_audit_ignores(None) == []
    assert load_npm_audit_ignores(tmp_path / "does-not-exist.yaml") == []
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("", encoding="utf-8")
    assert load_npm_audit_ignores(empty_file) == []


def test_filter_npm_audit_vulnerabilities_all_suppressed():
    vulns = {
        "@astrojs/mdx": {
            "name": "@astrojs/mdx",
            "severity": "high",
            "via": ["astro"],
        },
        "astro": {
            "name": "astro",
            "severity": "high",
            "via": ["http-cache-semantics"],
        },
        "http-cache-semantics": {
            "name": "http-cache-semantics",
            "severity": "high",
            "via": [
                {
                    "name": "http-cache-semantics",
                    "dependency": "http-cache-semantics",
                    "url": "https://github.com/advisories/GHSA-ch52-4w7c-c8xp",
                    "severity": "high",
                }
            ],
        },
    }
    suppressed, unsuppressed = filter_npm_audit_vulnerabilities(vulns, ["GHSA-CH52-4W7C-C8XP"])
    assert suppressed == {"@astrojs/mdx", "astro", "http-cache-semantics"}
    assert unsuppressed == {}


def test_filter_npm_audit_vulnerabilities_unsuppressed():
    vulns = {
        "astro": {
            "name": "astro",
            "severity": "high",
            "via": [
                "http-cache-semantics",
                {
                    "name": "astro",
                    "dependency": "astro",
                    "url": "https://github.com/advisories/GHSA-unsuppressed",
                    "severity": "high",
                },
            ],
        },
        "http-cache-semantics": {
            "name": "http-cache-semantics",
            "severity": "high",
            "via": [
                {
                    "name": "http-cache-semantics",
                    "dependency": "http-cache-semantics",
                    "url": "https://github.com/advisories/GHSA-ch52-4w7c-c8xp",
                    "severity": "high",
                }
            ],
        },
    }
    suppressed, unsuppressed = filter_npm_audit_vulnerabilities(vulns, ["GHSA-CH52-4W7C-C8XP"])
    assert suppressed == {"http-cache-semantics"}
    assert "astro" in unsuppressed


def test_audit_python_no_lockfile(tmp_path: Path):
    res = audit_python(tmp_path, tmp_path / "ignore.yaml")
    assert res == 1


@patch("subprocess.run")
def test_audit_python_success(mock_run: MagicMock, tmp_path: Path):
    req_file = tmp_path / "requirements-lock.txt"
    req_file.write_text("package==1.0.0\n", encoding="utf-8")
    ignore_file = tmp_path / "ignore.yaml"
    ignore_file.write_text("vulnerabilities:\n  - id: CVE-TEST\n", encoding="utf-8")

    mock_run.return_value = MagicMock(returncode=0, stdout="No known vulnerabilities found", stderr="")

    res = audit_python(tmp_path, ignore_file)
    assert res == 0
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    kwargs = mock_run.call_args[1]
    assert "--ignore-vuln" in cmd
    assert "CVE-TEST" in cmd
    assert kwargs.get("timeout") == 300


@patch("subprocess.run")
def test_audit_python_failure(mock_run: MagicMock, tmp_path: Path):
    req_file = tmp_path / "requirements-lock.txt"
    req_file.write_text("package==1.0.0\n", encoding="utf-8")
    ignore_file = tmp_path / "ignore.yaml"

    mock_run.return_value = MagicMock(returncode=1, stdout="Found 1 known vulnerability", stderr="")

    res = audit_python(tmp_path, ignore_file)
    assert res == 1


def test_audit_node_no_package_json(tmp_path: Path):
    res = audit_node(tmp_path)
    assert res == 1


@patch("subprocess.run")
def test_audit_node_success(mock_run: MagicMock, tmp_path: Path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "package.json").write_text("{}", encoding="utf-8")
    (site_dir / "package-lock.json").write_text("{}", encoding="utf-8")

    mock_run.return_value = MagicMock(returncode=0, stdout="found 0 vulnerabilities", stderr="")

    res = audit_node(tmp_path)
    assert res == 0
    assert mock_run.call_count == 2
    for call_item in mock_run.call_args_list:
        cmd = call_item[0][0]
        kwargs = call_item[1]
        assert cmd == ["npm", "audit", "--omit=dev", "--audit-level=high", "--json"]
        assert kwargs.get("timeout") == 120


@patch("subprocess.run")
def test_audit_node_suppressed(mock_run: MagicMock, tmp_path: Path):
    import json

    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "package.json").write_text("{}", encoding="utf-8")
    (site_dir / "package-lock.json").write_text("{}", encoding="utf-8")

    ignore_file = tmp_path / "npm-audit-ignore.yaml"
    ignore_file.write_text(
        "vulnerabilities:\n  - id: GHSA-ch52-4w7c-c8xp\n    package: http-cache-semantics\n",
        encoding="utf-8",
    )

    audit_json = json.dumps({
        "vulnerabilities": {
            "http-cache-semantics": {
                "name": "http-cache-semantics",
                "severity": "high",
                "via": [
                    {
                        "name": "http-cache-semantics",
                        "url": "https://github.com/advisories/GHSA-ch52-4w7c-c8xp",
                        "severity": "high",
                    }
                ],
            }
        }
    })

    mock_run.return_value = MagicMock(returncode=1, stdout=audit_json, stderr="")

    res = audit_node(tmp_path, ignore_file)
    assert res == 0


@patch("subprocess.run")
def test_audit_node_unsuppressed_fails(mock_run: MagicMock, tmp_path: Path):
    import json

    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "package.json").write_text("{}", encoding="utf-8")
    (site_dir / "package-lock.json").write_text("{}", encoding="utf-8")

    audit_json = json.dumps({
        "vulnerabilities": {
            "unsuppressed-pkg": {
                "name": "unsuppressed-pkg",
                "severity": "high",
                "via": [
                    {
                        "name": "unsuppressed-pkg",
                        "url": "https://github.com/advisories/GHSA-xxxx-yyyy-zzzz",
                        "severity": "high",
                    }
                ],
            }
        }
    })

    mock_run.return_value = MagicMock(returncode=1, stdout=audit_json, stderr="")

    res = audit_node(tmp_path)
    assert res == 1


@patch("subprocess.run")
def test_audit_node_unparseable_json_fails(mock_run: MagicMock, tmp_path: Path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "package.json").write_text("{}", encoding="utf-8")
    (site_dir / "package-lock.json").write_text("{}", encoding="utf-8")

    mock_run.return_value = MagicMock(returncode=1, stdout="not json", stderr="fatal error")

    res = audit_node(tmp_path)
    assert res == 1


@patch("scripts.ci.audit_dependencies.audit_python")
@patch("scripts.ci.audit_dependencies.audit_node")
def test_main_cli(mock_node: MagicMock, mock_py: MagicMock, tmp_path: Path):
    mock_py.return_value = 0
    mock_node.return_value = 0

    code = main(["--repo-root", str(tmp_path)])
    assert code == 0
    mock_py.assert_called_once()
    mock_node.assert_called_once()

    mock_py.reset_mock()
    mock_node.reset_mock()
    code_skip_node = main(["--repo-root", str(tmp_path), "--skip-node"])
    assert code_skip_node == 0
    mock_py.assert_called_once()
    mock_node.assert_not_called()
