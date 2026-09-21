"""Anti-leak guard for curriculum-upgrade public files from #7999.

Detector needles stay in this test. Production curriculum, audit, and spec
files must not bake a host checkout or interpreter path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

ROOT = Path(__file__).resolve().parents[1]

# Reject-sample needles for the anti-leak detector. Do not copy these into
# public curriculum, audit, or operator-spec files.
_HOST_RUN_ROOT_NEEDLES = (
    "/home/ops",
    "/home/ubuntu",
    "/Users/krisztiankoos",
)

_PUBLIC_TREES = (
    Path("docs/epics/curriculum-upgrade-phase1-spec.md"),
    Path("audit/curriculum-upgrade/pilot-things-have-gender/verify_pilot.py"),
    Path("curriculum/l2-uk-en/a1/things-have-gender"),
    Path("curriculum/l2-uk-en/a1/what-is-it-like"),
)


def _iter_public_files() -> list[Path]:
    files: list[Path] = []
    for rel in _PUBLIC_TREES:
        path = ROOT / rel
        if path.is_file():
            files.append(path)
            continue
        files.extend(p for p in path.rglob("*") if p.is_file())
    return files


def test_curriculum_upgrade_public_files_have_no_baked_host_run_root() -> None:
    files = _iter_public_files()
    assert files, "expected curriculum-upgrade public files to scan"
    leaked: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for needle in _HOST_RUN_ROOT_NEEDLES:
            if needle in text:
                leaked.append(f"{path.relative_to(ROOT)} contains {needle}")
    assert not leaked, "baked host run-root still present:\n" + "\n".join(leaked)
