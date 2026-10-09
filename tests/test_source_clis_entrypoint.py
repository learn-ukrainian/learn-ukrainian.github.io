"""Real source-tool startup probes without pytest's import paths (#9991)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = (
    "scripts/ingest/grac_frequency_ingest.py",
    "scripts/ingest/slovnyk_me_ingest.py",
    "scripts/curriculum/evidence/sources.py",
    "scripts/lexicon/enrich_manifest.py",
)


@pytest.fixture
def clean_env(tmp_path: Path) -> dict[str, str]:
    # An allowlist excludes PYTHONPATH, user site packages, live session identity,
    # source-store overrides and credentials inherited by the pytest process.
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(tmp_path),
        "TMPDIR": str(tmp_path),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LEXICON_SLOVNYK_OFFLINE": "1",
    }


@pytest.mark.parametrize("path", ENTRYPOINTS)
@pytest.mark.parametrize("style", ("file", "module"))
def test_source_cli_help(path: str, style: str, clean_env: dict[str, str]) -> None:
    args = [path] if style == "file" else ["-m", path.removesuffix(".py").replace("/", ".")]
    command = [sys.executable, *args, "--help"]
    result = subprocess.run(
        command, cwd=ROOT, env=clean_env, capture_output=True, text=True, timeout=30, check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"{command!r}: exit {result.returncode}\n{output}"
    assert "Traceback" not in output, output
    # sources.py exposes library primitives, so its startup probe has no parser.
    if path != "scripts/curriculum/evidence/sources.py":
        assert "usage:" in result.stdout.lower(), output
        assert "--help" in result.stdout, output


@pytest.mark.parametrize("module", ("scripts.wiki.slovnyk_me", "scripts.rag.source_query"))
def test_source_helpers_do_not_load_curriculum_audit(module: str, clean_env: dict[str, str]) -> None:
    code = f"""
import importlib
import sys

importlib.import_module({module!r})
heavy = [name for name in sys.modules if name in ('audit.core', 'scripts.audit.core')
         or name.startswith(('audit.checks', 'scripts.audit.checks'))]
assert not heavy, heavy
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=clean_env,
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
