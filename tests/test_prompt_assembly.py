"""
Tests for prompt template assembly (fill_template.py).

Covers:
- fill_template() — placeholder substitution
- find_unresolved() — unresolved placeholder detection
- main() CLI — end-to-end with YAML files, --set overrides, strict mode

Issue: #520
"""

import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fill_template import main

# =============================================================================
# fill_template() UNIT TESTS
# =============================================================================


# =============================================================================
# find_unresolved() UNIT TESTS
# =============================================================================


# =============================================================================
# PLACEHOLDER_RE REGEX TESTS
# =============================================================================


# =============================================================================
# main() CLI INTEGRATION TESTS
# =============================================================================

class TestMainCLI:

    def test_strict_mode_fails_on_unresolved(self, tmp_path, monkeypatch):
        """Strict mode returns 1 when placeholders remain."""
        template = tmp_path / "template.md"
        template.write_text("{RESOLVED} and {MISSING}")

        placeholders = tmp_path / "placeholders.yaml"
        placeholders.write_text(yaml.dump({"RESOLVED": "ok"}))

        output = tmp_path / "output.md"

        monkeypatch.setattr("sys.argv", [
            "fill_template.py",
            "--template", str(template),
            "--placeholders", str(placeholders),
            "--output", str(output),
            "--strict",
        ])
        result = main()
        assert result == 1
