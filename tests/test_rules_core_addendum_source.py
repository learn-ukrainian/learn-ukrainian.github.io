"""Rules loaders keep fleet policy and product curriculum in their own trees (#12819)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.common import repo_root
from scripts.lib import rules_core

CORE = "## P0 — FLEET CORE\n"
ADDENDUM = "# PRODUCT CURRICULUM\n"
DECOY = "# MACHINERY DECOY\n"


def _product(root: Path, addendum: str | None = ADDENDUM) -> Path:
    marker = root / repo_root.PRODUCT_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("product: fixture\n", encoding="utf-8")
    target = root / rules_core.CONTENT_ADDENDUM_REL
    target.parent.mkdir(parents=True)
    if addendum is not None:
        target.write_text(addendum, encoding="utf-8")
    return root


@pytest.fixture
def split(tmp_path: Path, monkeypatch):
    machinery = tmp_path / "machinery"
    rules = machinery / rules_core.RULES_DIR_REL
    rules.mkdir(parents=True)
    (rules / "core.md").write_text(CORE, encoding="utf-8")
    (rules / "core-curriculum.md").write_text(DECOY, encoding="utf-8")
    product = _product(tmp_path / "product")
    monkeypatch.setenv(repo_root.RULES_DIR_ENV, str(rules))
    monkeypatch.setenv(repo_root.PRODUCT_ROOT_ENV, str(product))
    monkeypatch.setenv("AGENT_NO_TELEMETRY_FOOTER", "1")
    monkeypatch.setenv("LU_RULES_SEAT", "content")
    return machinery, product


def _cli(*args: str):
    return subprocess.run(
        [sys.executable, str(repo_root.machinery_path("lib/rules_core.py")), *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _shell(machinery: Path, form: str):
    script = """source "$1/lib/rules_core.sh"
    rules_core_load "$2" "$3" '' codex || exit 1
    case "$4" in
      block) printf '%s' "$LC_RULES_CORE" ;;
      toml) rules_core_toml "$2" "$3" ;;
      kimi) path="$(rules_core_kimi_agent_file "$2" "$3")" && cat "$path" ;;
    esac"""
    return subprocess.run(
        ["bash", "-c", script, "bash", str(repo_root.machinery_root()), sys.executable, str(machinery), form],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _client(machinery: Path):
    from scripts.api import rules_router
    from scripts.api.monitor_context import get_ctx

    app = FastAPI()
    app.include_router(rules_router.router, prefix="/api/rules")
    app.dependency_overrides[get_ctx] = lambda: SimpleNamespace(roots=SimpleNamespace(project_root=machinery))
    return TestClient(app)


def test_python_uses_product_not_machinery(split):
    """Wrong-source defect: a decoy machinery addendum must never enter a content seat."""
    assert rules_core.core_text("content") == CORE + rules_core.FILE_SEP + ADDENDUM
    assert rules_core.source_path(rules_core.CONTENT_ADDENDUM_REL) == split[1] / rules_core.CONTENT_ADDENDUM_REL


def test_explicit_product_wins(split, tmp_path):
    """Precedence defect: a caller's explicit product overrides LU_PRODUCT_ROOT."""
    explicit = _product(tmp_path / "explicit", "# EXPLICIT PRODUCT\n")
    expected = CORE + rules_core.FILE_SEP + "# EXPLICIT PRODUCT\n"
    assert rules_core.core_text("content", explicit) == expected
    result = _cli("--root", str(explicit), "--seat", "content", "--format", "text")
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.mark.parametrize("form", ["text", "block", "toml", "kimi-agent-file", "json"])
def test_cli_default_keeps_configured_product(split, form):
    """Default-shadowing defect: CLI machinery defaults must not override LU_PRODUCT_ROOT."""
    result = _cli("--seat", "content", "--format", form)
    assert result.returncode == 0, result.stderr
    if form == "json":
        assert (
            json.loads(result.stdout)["sha256"]
            == hashlib.sha256((CORE + rules_core.FILE_SEP + ADDENDUM).encode()).hexdigest()
        )
    else:
        assert "PRODUCT CURRICULUM" in result.stdout
        assert "MACHINERY DECOY" not in result.stdout


@pytest.mark.parametrize("form", ["block", "toml", "kimi"])
def test_shell_default_keeps_configured_product(split, form):
    """Default-shadowing defect: all shell renders preserve the configured product."""
    result = _shell(split[0], form)
    assert result.returncode == 0, result.stderr
    assert "PRODUCT CURRICULUM" in result.stdout
    assert "MACHINERY DECOY" not in result.stdout


@pytest.mark.parametrize("form", ["markdown", "json"])
def test_http_default_keeps_configured_product(split, form):
    """Default-shadowing defect: the API context's machinery root is not product selection."""
    response = _client(split[0]).get(f"/api/rules?scope=content&format={form}")
    assert response.status_code == 200, response.text
    body = response.text if form == "markdown" else response.json()["markdown"]
    assert body == CORE + rules_core.FILE_SEP + ADDENDUM


@pytest.mark.parametrize("damage", ["missing", "empty", "blank", "directory", "encoding"])
def test_product_addendum_refuses_despite_decoy(split, damage):
    """Fallback defect: missing or unreadable product content refuses despite a readable decoy."""
    target = split[1] / rules_core.CONTENT_ADDENDUM_REL
    target.unlink()
    if damage == "directory":
        target.mkdir()
    elif damage != "missing":
        target.write_bytes({"empty": b"", "blank": b" \n\t", "encoding": b"\xff"}[damage])
    with pytest.raises(rules_core.RulesCoreMissing, match=rules_core.CONTENT_ADDENDUM_REL):
        rules_core.require_core("content")
    assert rules_core.core_text("core") == CORE
    output = split[1] / "side-effect" / "rules.txt"
    result = _cli("--seat", "content", "--format", "block", "--output", str(output))
    assert result.returncode == 3, result.stderr
    assert rules_core.CONTENT_ADDENDUM_REL in result.stderr
    assert not output.parent.exists()
    for form in ("block", "toml", "kimi"):
        result = _shell(split[0], form)
        assert result.returncode == 1, result.stderr
        assert rules_core.CONTENT_ADDENDUM_REL in result.stderr
        assert not result.stdout
    for form in ("markdown", "json"):
        response = _client(split[0]).get(f"/api/rules?scope=content&format={form}")
        assert response.status_code == 503, response.text
        assert rules_core.CONTENT_ADDENDUM_REL in response.json()["detail"]


def test_core_never_resolves_product(split, monkeypatch):
    """Machinery-only regression: core seats must succeed even when product resolution raises."""

    def unavailable(*args, **kwargs):
        raise repo_root.ProductRootError("no product")

    monkeypatch.setattr(repo_root, "product_root", unavailable)
    if hasattr(rules_core, "product_root"):
        monkeypatch.setattr(rules_core, "product_root", unavailable)
    assert rules_core.core_text("core") == CORE
    assert rules_core.require_core("core") == "core"
    assert _client(split[0]).get("/api/rules?scope=core").text == CORE
    monkeypatch.setenv(repo_root.PRODUCT_ROOT_ENV, str(split[0] / "missing-product"))
    assert _cli("--seat", "core", "--format", "text").stdout == CORE
    monkeypatch.setenv("LU_RULES_SEAT", "core")
    assert _shell(split[0], "block").returncode == 0


def test_invalid_product_is_named_refusal(split, monkeypatch):
    """Resolver-refusal defect: invalid product selection must refuse through RulesCoreMissing."""
    monkeypatch.setenv(repo_root.PRODUCT_ROOT_ENV, str(split[0]))
    with pytest.raises(rules_core.RulesCoreMissing, match=rules_core.CONTENT_ADDENDUM_REL):
        rules_core.core_text("content")
    result = _cli("--seat", "content", "--format", "text")
    assert result.returncode == 3
    assert rules_core.CONTENT_ADDENDUM_REL in result.stderr
    assert _client(split[0]).get("/api/rules?scope=content").status_code == 503
