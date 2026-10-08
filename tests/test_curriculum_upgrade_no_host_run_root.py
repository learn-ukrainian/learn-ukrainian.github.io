"""Anti-leak guard for curriculum-upgrade public files from #7999.

Needles come from tests/_host_path_guard.py (generic home-directory patterns
plus the deployment's own). Production curriculum, audit, and spec files must
not bake a host checkout or interpreter path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._host_path_guard import host_path_hits

pytestmark = [pytest.mark.reads_content, pytest.mark.repo_wide]

ROOT = Path(__file__).resolve().parents[1]

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
        for hit in host_path_hits(text):
            leaked.append(f"{path.relative_to(ROOT)} contains {hit}")
    assert not leaked, "baked host run-root still present:\n" + "\n".join(leaked)
