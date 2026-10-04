"""Unicode boundary regressions through real lexicon readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.lexicon.curated_seed_atlas_admission", "_read_jsonl", 64),
        ("scripts.lexicon.ohoiko_paired_headword_split", "append_space_collapse_audit", 850),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
