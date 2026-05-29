from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit import lint_bio_dossier_xref


def _write_dossier(tmp_path: Path, body: str) -> Path:
    dossier = tmp_path / "example-bio.md"
    dossier.write_text(
        f"""# Example Bio

## 6. Contested points

- placeholder

## 7. Cross-track links

{body}

## 8. Naming-canonical

- **Slug:** `example-bio`
""",
        encoding="utf-8",
    )
    return dossier


def test_existing_fabricated_path_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    plans_dir = tmp_path / "curriculum" / "l2-uk-en" / "plans" / "lit"
    plans_dir.mkdir(parents=True)
    (plans_dir / "real-module.yaml").write_text("title: real\n", encoding="utf-8")

    dossier = _write_dossier(
        tmp_path,
        """- **Existing LIT modules (VERIFIED present via `test -e`):**
  - `plans/lit/missing-module.yaml`
  - `curriculum/l2-uk-en/plans/lit/real-module.yaml`""",
    )

    monkeypatch.setattr(lint_bio_dossier_xref, "PROJECT_ROOT", tmp_path)

    assert lint_bio_dossier_xref.main(["--paths", str(dossier)]) == 1
    output = capsys.readouterr().out
    assert "plans/lit/missing-module.yaml" in output
    assert "Existing LIT modules" in output
    assert "plans/lit/real-module.yaml" not in output


def test_potential_and_real_existing_paths_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    for track, slug in (("lit", "verified-module"), ("hist", "future-module")):
        plan_dir = tmp_path / "curriculum" / "l2-uk-en" / "plans" / track
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / f"{slug}.yaml").write_text("title: ok\n", encoding="utf-8")

    dossier = _write_dossier(
        tmp_path,
        """- **Existing LIT modules (VERIFIED present via `test -e`):**
  - `curriculum/l2-uk-en/plans/lit/verified-module.yaml`
- **Candidate cross-track connections (Phase 2+ — NOT existing files):**
  - `plans/hist/future-module.yaml`
  - A `plans/bio/example-bio.yaml` does **not** yet exist — to be created in Phase 2.""",
    )

    monkeypatch.setattr(lint_bio_dossier_xref, "PROJECT_ROOT", tmp_path)

    assert lint_bio_dossier_xref.main(["--paths", str(dossier)]) == 0
    output = capsys.readouterr().out
    assert "No fabricated Existing cross-track plan paths found." in output


def test_real_repo_existing_path_passes(capsys) -> None:
    dossier = Path("docs/research/bio/volodymyr-vynnychenko.md")
    if not dossier.exists():
        pytest.skip("volodymyr-vynnychenko dossier not present in checkout")

    assert lint_bio_dossier_xref.main(["--paths", str(dossier)]) == 0
    output = capsys.readouterr().out
    assert "No fabricated Existing cross-track plan paths found." in output
