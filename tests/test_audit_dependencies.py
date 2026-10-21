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
    resolve_cve_to_ghsa,
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
    assert "http-cache-semantics" not in ignores
    assert "foo" not in ignores


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

    audit_json = json.dumps(
        {
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
        }
    )

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

    audit_json = json.dumps(
        {
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
        }
    )

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


@patch("subprocess.run")
def test_audit_node_suppressed_high_with_unrelated_moderate_passes(mock_run: MagicMock, tmp_path: Path):
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

    audit_json = json.dumps(
        {
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
                },
                "unrelated-moderate": {
                    "name": "unrelated-moderate",
                    "severity": "moderate",
                    "via": [
                        {
                            "name": "unrelated-moderate",
                            "url": "https://github.com/advisories/GHSA-moderate-advisory",
                            "severity": "moderate",
                        }
                    ],
                },
            }
        }
    )

    mock_run.return_value = MagicMock(returncode=1, stdout=audit_json, stderr="")

    res = audit_node(tmp_path, ignore_file)
    assert res == 0


@patch("subprocess.run")
def test_audit_node_cve_suppression_does_not_suppress_unrelated_critical(mock_run: MagicMock, tmp_path: Path):
    import json

    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "package.json").write_text("{}", encoding="utf-8")
    (site_dir / "package-lock.json").write_text("{}", encoding="utf-8")

    ignore_file = tmp_path / "npm-audit-ignore.yaml"
    ignore_file.write_text(
        "vulnerabilities:\n  - cve: CVE-2026-9999\n    package: foo-pkg\n",
        encoding="utf-8",
    )

    audit_json = json.dumps(
        {
            "vulnerabilities": {
                "foo-pkg": {
                    "name": "foo-pkg",
                    "severity": "critical",
                    "via": [
                        {
                            "name": "foo-pkg",
                            "url": "https://github.com/advisories/GHSA-unrelated-critical",
                            "severity": "critical",
                        }
                    ],
                }
            }
        }
    )

    mock_run.return_value = MagicMock(returncode=1, stdout=audit_json, stderr="")

    res = audit_node(tmp_path, ignore_file)
    assert res == 1


def test_resolve_cve_to_ghsa():
    # Known alias from static table
    assert resolve_cve_to_ghsa("CVE-2026-93748") == "GHSA-CH52-4W7C-C8XP"
    assert resolve_cve_to_ghsa("cve-2026-93748") == "GHSA-CH52-4W7C-C8XP"

    # Custom aliases dictionary
    custom = {"CVE-9999-1111": "GHSA-CUSTOM-ID"}
    assert resolve_cve_to_ghsa("CVE-9999-1111", custom) == "GHSA-CUSTOM-ID"

    # Unknown CVE returns None when network fails/is mocked
    with patch("urllib.request.urlopen", side_effect=Exception("network offline")):
        assert resolve_cve_to_ghsa("CVE-0000-0000") is None


def test_load_npm_audit_ignores_with_cve_aliases(tmp_path: Path):
    ignore_file = tmp_path / "npm-audit-ignore.yaml"
    data = {
        "aliases": {
            "CVE-1111-2222": "GHSA-custom-alias",
        },
        "vulnerabilities": [
            {"cve": "CVE-2026-93748", "package": "http-cache-semantics"},
            {"cve": "CVE-1111-2222", "package": "other-pkg"},
        ],
    }
    ignore_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    ignores = load_npm_audit_ignores(ignore_file)
    assert "CVE-2026-93748" in ignores
    assert "GHSA-CH52-4W7C-C8XP" in ignores
    assert "CVE-1111-2222" in ignores
    assert "GHSA-CUSTOM-ALIAS" in ignores
    assert "http-cache-semantics" not in ignores


@patch("subprocess.run")
def test_audit_node_cve_suppression_successfully_suppresses_intended_canonical_advisory(
    mock_run: MagicMock, tmp_path: Path
):
    import json

    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "package.json").write_text("{}", encoding="utf-8")
    (site_dir / "package-lock.json").write_text("{}", encoding="utf-8")

    ignore_file = tmp_path / "npm-audit-ignore.yaml"
    ignore_file.write_text(
        "vulnerabilities:\n  - cve: CVE-2026-93748\n    package: http-cache-semantics\n",
        encoding="utf-8",
    )

    audit_json = json.dumps(
        {
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
        }
    )

    mock_run.return_value = MagicMock(returncode=1, stdout=audit_json, stderr="")

    res = audit_node(tmp_path, ignore_file)
    assert res == 0
