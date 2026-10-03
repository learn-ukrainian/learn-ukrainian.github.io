"""Unicode boundary regressions through real atlas readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.atlas.curated_seed_to_lexical_jsonl", "convert_seed_file", 178),
        ("scripts.atlas.lexical_projection", "_read_jsonl", 286),
        ("scripts.atlas.rebuild_teacher_curated_seed", "_read_jsonl", 44),
        ("scripts.atlas.residual_teacher_lists", "_read_jsonl", 51),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
