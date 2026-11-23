"""Both CI TruffleHog steps pin the scanner image (#10056).

The pinned action passes ``image:version`` to Docker. Together those inputs
must name the same digest in both jobs.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
_IMAGE = "ghcr.io/trufflesecurity/trufflehog@sha256"
_DIGEST_HEX = re.compile(r"[0-9a-f]{64}")


def _trufflehog_steps() -> list[dict]:
    workflow = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    steps = []
    for job in workflow["jobs"].values():
        for step in job.get("steps") or []:
            if "trufflehog" in str(step.get("uses") or ""):
                steps.append(step)
    return steps


def test_both_trufflehog_steps_pin_the_same_scanner_digest() -> None:
    steps = _trufflehog_steps()
    assert len(steps) == 2
    digests = []
    for step in steps:
        inputs = step["with"]
        assert inputs["image"] == _IMAGE
        digest = inputs["version"]
        assert isinstance(digest, str)
        assert _DIGEST_HEX.fullmatch(digest)
        digests.append(digest)
    assert digests[0] == digests[1]
