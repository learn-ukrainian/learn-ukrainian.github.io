"""Both CI TruffleHog steps pin the scanner image (#10056).

The action SHA pins the workflow script only. The action input ``version``
defaults to ``latest``, so an omitted or floating value scans whatever image
the registry serves that day.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
_EXACT_VERSION = re.compile(r"\d+\.\d+\.\d+\Z")


def _trufflehog_steps() -> list[dict]:
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    steps = []
    for job in workflow["jobs"].values():
        for step in job.get("steps") or []:
            if "trufflehog" in str(step.get("uses") or ""):
                steps.append(step)
    return steps


def test_both_trufflehog_steps_pin_an_exact_scanner_version() -> None:
    steps = _trufflehog_steps()
    assert len(steps) == 2
    versions = []
    for step in steps:
        version = (step.get("with") or {}).get("version")
        assert isinstance(version, str)
        assert "latest" not in version.lower()
        assert _EXACT_VERSION.fullmatch(version)
        versions.append(version)
    assert versions[0] == versions[1]
