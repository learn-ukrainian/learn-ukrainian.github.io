from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from scripts.ci.audit_dependencies import (
    audit_node,
    audit_python,
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


def test_audit_python_no_lockfile(tmp_path: Path):
    res = audit_python(tmp_path, tmp_path / "ignore.yaml")
    assert res == 0


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
    assert "--ignore-vuln" in cmd
    assert "CVE-TEST" in cmd


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
    assert res == 0


@patch("subprocess.run")
def test_audit_node_success(mock_run: MagicMock, tmp_path: Path):
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "package.json").write_text("{}", encoding="utf-8")

    mock_run.return_value = MagicMock(returncode=0, stdout="found 0 vulnerabilities", stderr="")

    res = audit_node(tmp_path)
    assert res == 0
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd == ["npm", "audit", "--omit=dev", "--audit-level=high"]


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
