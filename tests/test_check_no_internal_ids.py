from pathlib import Path

import pytest

from scripts.audit import check_no_internal_ids

pytestmark = pytest.mark.reads_content


def test_chunk_id_inside_html_comment_is_not_flagged(tmp_path: Path) -> None:
    """B1 regression: <!-- VERIFY … chunk_id="…" --> authoring markers never render,
    so build-provenance inside an HTML comment is not a learner-surface leak; the same
    term in rendered prose still is."""
    doc = tmp_path / "m.md"
    doc.write_text(
        'Rendered chunk mention 5794da94_c0817.\n'
        '<!-- VERIFY: source="MCP" chunk_id="7-klas-ukrmova-avramenko-2024_s0078" -->\n'
        'Another visible id 40beaaff_c0000 here.\n',
        encoding="utf-8",
    )
    lines = [f.line_no for f in check_no_internal_ids.scan_files([doc])]
    assert 2 not in lines  # the comment line is blanked
    assert 1 in lines and 3 in lines  # rendered corpus ids still flagged
