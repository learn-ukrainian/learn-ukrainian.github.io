"""Regression test for #2050.

The russian_shadow channel inside ``_judge_eval_lib._russian_shadow_check``
silently went dead in both the H1 (PR #2046) and H2 (PR #2049) calibration
runs because `from scripts.verification.check_ru_morph import is_russian_pattern`
raises ``ModuleNotFoundError`` when the entry-point script
``scripts/audit/judge_calibration_matrix.py`` is invoked with
``python scripts/audit/judge_calibration_matrix.py`` (Python sets
``sys.path[0]`` to ``scripts/audit/``, not the repo root). The bare
``except ImportError`` swallowed the failure and the prompt rendered
``(pymorphy3 unavailable in this environment)``.

The fix is a module-level ``sys.path`` shim in ``_judge_eval_lib.py`` that
inserts ``PROJECT_ROOT`` so absolute imports resolve regardless of how the
module is loaded. This test reproduces the exact bug scenario: it spawns a
subprocess whose ``cwd`` is ``scripts/audit/`` and verifies the channel
imports + fires on a token that is unambiguously Russian.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _has_pymorphy3() -> bool:
    import importlib.util

    return importlib.util.find_spec("pymorphy3") is not None


@pytest.mark.skipif(
    not _has_pymorphy3(),
    reason="pymorphy3 not installed; russian_shadow channel cannot be tested at all",
)
def test_russian_shadow_channel_alive_in_process() -> None:
    """In-process import — the module-level sys.path shim makes the absolute
    `scripts.verification.check_ru_morph` import resolve."""
    from scripts.audit._judge_eval_lib import _russian_shadow_check

    result = _russian_shadow_check("спасибо")
    assert result["available"] is True, (
        "russian_shadow channel reported unavailable; sys.path shim did not "
        "make `scripts.verification.check_ru_morph` importable. See #2050."
    )
    # `спасибо` is a Russian-only common word; pymorphy3 RU should match it.
    triggered = result["triggered_tokens"]
    assert triggered, (
        "russian_shadow channel imported but did not fire on `спасибо`; "
        "expected at least one triggered token. Got: " + repr(result)
    )


@pytest.mark.skipif(
    not _has_pymorphy3(),
    reason="pymorphy3 not installed; russian_shadow channel cannot be tested at all",
)
def test_russian_shadow_channel_alive_from_audit_cwd() -> None:
    """Reproduce the exact #2050 bug scenario: subprocess launched with
    cwd=`scripts/audit/`, simulating `python scripts/audit/<runner>.py`
    where `sys.path[0]` becomes `scripts/audit/`."""
    audit_dir = PROJECT_ROOT / "scripts" / "audit"
    assert audit_dir.is_dir(), f"scripts/audit not found at {audit_dir}"

    # Strip PYTHONPATH so the subprocess doesn't inherit repo-root from the
    # pytest invocation; otherwise the shim wouldn't be exercised.
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}

    script = (
        "import sys, json;"
        "from _judge_eval_lib import _russian_shadow_check;"
        "result = _russian_shadow_check('спасибо');"
        "print(json.dumps(result))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(audit_dir),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0, (
        f"subprocess failed (rc={proc.returncode}). "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    import json as _json
    result = _json.loads(proc.stdout.splitlines()[-1])
    assert result["available"] is True, (
        "russian_shadow channel reported unavailable when run from "
        "scripts/audit/ — the #2050 sys.path bug is back. "
        f"subprocess stderr={proc.stderr!r}"
    )
    assert result["triggered_tokens"], (
        "russian_shadow channel imported but did not fire on `спасибо` "
        f"from audit cwd. Got: {result!r}"
    )
