from pathlib import Path

import pytest

from scripts.audit import check_adrs


def test_rebuild_index_missing_sentinels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    adr_dir = tmp_path / "docs" / "architecture" / "adr"
    adr_dir.mkdir(parents=True)
    readme = adr_dir / "README.md"
    readme.write_text("## Index\n\nNo sentinels here.", "utf-8")

    monkeypatch.setattr(check_adrs, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(check_adrs, "ADR_DIR", adr_dir)
    monkeypatch.setattr(check_adrs, "README_PATH", readme)

    exit_code = check_adrs.main(["--rebuild-index"])

    assert exit_code == 1

    captured = capsys.readouterr()
    assert "ADR-INDEX sentinels are missing" in captured.err
