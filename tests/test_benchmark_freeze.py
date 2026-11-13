from __future__ import annotations

from pathlib import Path

from scripts.audit import freeze_benchmark


def test_heldout_hashes_include_only_non_hidden_json_files(tmp_path: Path) -> None:
    public_hash_input = tmp_path / "heldout-a.json"
    public_hash_input.write_text('{"slug": "private-a"}\n', encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not a fixture\n", encoding="utf-8")
    (tmp_path / ".DS_Store").write_text("mac metadata\n", encoding="utf-8")
    (tmp_path / ".hidden.json").write_text('{"slug": "hidden"}\n', encoding="utf-8")

    heldout = freeze_benchmark._heldout_fixtures(tmp_path)

    assert heldout == {
        "count": 1,
        "sha256": [freeze_benchmark._sha256_file(public_hash_input)],
    }
