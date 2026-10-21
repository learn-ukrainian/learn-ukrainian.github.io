"""Importing the lexicon admit scripts must not change the process environment (#9473).

A module-level ``os.environ[...] = ...`` leaks into every later test in the same
xdist worker. The offline switch belongs in each script's entry point, scoped.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lexicon import admit_fmu_boosters, admit_stem_slice_2a, enrich_manifest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_KEY = "LEXICON_SLOVNYK_OFFLINE"
ADMIT_MODULES = ["scripts.lexicon.admit_fmu_boosters", "scripts.lexicon.admit_stem_slice_2a"]


@pytest.mark.parametrize("module", ADMIT_MODULES)
def test_import_leaves_environment_unchanged(module: str) -> None:
    code = (
        "import os\n"
        "before = dict(os.environ)\n"
        f"import {module}\n"
        "assert dict(os.environ) == before, sorted(set(os.environ) ^ set(before))\n"
    )
    env = {k: v for k, v in os.environ.items() if k != ENV_KEY}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("module", "entry_name", "runner_name"),
    [
        (admit_fmu_boosters, "main", "admit_fmu_boosters"),
        (admit_stem_slice_2a, "main", "admit_slice_2a"),
    ],
)
@pytest.mark.parametrize("prior", [None, "0"])
def test_main_scopes_offline_switch_and_restores_prior(
    monkeypatch: pytest.MonkeyPatch, module, entry_name: str, runner_name: str, prior: str | None
) -> None:
    if prior is None:
        monkeypatch.delenv(ENV_KEY, raising=False)
    else:
        monkeypatch.setenv(ENV_KEY, prior)
    seen: list[bool] = []

    def fake_runner(**_kwargs):
        seen.append(enrich_manifest._phase1_offline_mode())
        return {}

    monkeypatch.setattr(module, runner_name, fake_runner)
    monkeypatch.setattr(sys, "argv", [module.__name__, "--dry-run"])

    assert getattr(module, entry_name)() == 0

    assert seen == [True]
    assert os.environ.get(ENV_KEY) == prior


def test_slovnyk_offline_env_restores_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_KEY, "0")
    with pytest.raises(RuntimeError), enrich_manifest.slovnyk_offline_env():
        assert os.environ[ENV_KEY] == "1"
        raise RuntimeError("boom")
    assert os.environ[ENV_KEY] == "0"
