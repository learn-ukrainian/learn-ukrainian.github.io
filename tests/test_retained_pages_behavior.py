"""Direct retained-page behavior and bookmark compatibility proofs for #10667."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.test_work_dashboard_private_integration import _private_ok, _public_min

ROOT = Path(__file__).resolve().parents[1]


def test_retained_pages_browser_and_clock_behavior() -> None:
    env = {
        **os.environ,
        "RETAINED_WORK_FIXTURE": json.dumps(_public_min()),
        "RETAINED_PRIVATE_FIXTURE": json.dumps(_private_ok()),
    }
    result = subprocess.run(
        ["node", "--test", "tests/retained_pages_behavior.test.cjs"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("page", "target"),
    [
        ("audit-dashboard.html", "quality.html"),
        ("channels.html", "fleet.html"),
        ("comms.html", "fleet.html"),
        ("images.html", "image-explorer.html"),
        ("track-health.html", "progress.html"),
    ],
)
def test_all_five_compatibility_redirects_remain_intact(page: str, target: str) -> None:
    html = (ROOT / "dashboards" / page).read_text(encoding="utf-8")
    assert 'http-equiv="refresh"' in html
    assert f"url=/{target}" in html
    assert f'href="/{target}"' in html
    assert "/api/" not in html
