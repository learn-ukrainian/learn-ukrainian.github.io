from pathlib import Path

import pytest

from scripts.build.fresh.path_guard import public_diagnostic


@pytest.mark.parametrize("root", [Path("/home/test/project"), Path("/tmp/project with spaces")])
def test_public_diagnostic_keeps_only_repository_relative_paths(root):
    message = f"failed: '{root}/curriculum/receipt.yaml', root={root}; external /home/other/receipt.yaml"
    result = public_diagnostic(message, root)
    assert result == "failed: './curriculum/receipt.yaml', root=.; external <external-path>"
    assert str(root) not in result and "/home/" not in result
    assert public_diagnostic(f"sibling {root}-other/file.yaml", root).startswith("sibling <external-path>")


def test_public_diagnostic_preserves_relative_paths_and_reason_codes():
    message = "receipt_span_alignment_failed: curriculum/receipt.yaml unit ('urok', 's1')"
    assert public_diagnostic(message, Path("/tmp/project")) == message
