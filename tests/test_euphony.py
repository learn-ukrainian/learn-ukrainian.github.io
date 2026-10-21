"""
Tests for euphony (милозвучність) checker.

Covers all three Ukrainian phonetic alternation rules:
  Rule 1: і/й conjunction alternation (й only between vowels)
  Rule 2: у/в preposition alternation (phonetic position)
  Rule 3: з/із/зі preposition alternation (before sibilants/clusters)

Also tests auto-fix, track exemptions, and line-skipping logic.

Issue: #624, #593
"""

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.checks.euphony import (
    auto_fix_euphony,
    check_euphony_violations,
)

# =============================================================================
# Helper functions
# =============================================================================


# =============================================================================
# Rule 1: і/й alternation
# =============================================================================

class TestRule1IY:

    def test_detect_i_between_vowels(self):
        """і between two vowels should be flagged."""
        content = "вона і Олена пішли"
        violations = check_euphony_violations(content)
        assert any("і між голосними" in v["issue"] for v in violations)

    def test_detect_y_after_consonant(self):
        """й after a consonant should be flagged."""
        content = "він й Олена"
        violations = check_euphony_violations(content)
        assert any("й після приголосного" in v["issue"] for v in violations)

    def test_y_between_vowels_is_ok(self):
        """й between vowels is correct — no violation."""
        content = "вона й Олена"
        violations = check_euphony_violations(content)
        rule1 = [v for v in violations if "і між голосними" in v["issue"]
                 or "й після приголосного" in v["issue"]]
        assert len(rule1) == 0

    def test_fix_i_to_y(self):
        """Auto-fix: і between vowels → й."""
        content = "вона і Олена пішли"
        fixed, count = auto_fix_euphony(content)
        assert count == 1
        assert "й Олена" in fixed

    def test_fix_y_to_i(self):
        """Auto-fix: й after consonant → і."""
        content = "він й Олена"
        fixed, count = auto_fix_euphony(content)
        assert count == 1
        assert "він і" in fixed


# =============================================================================
# Rule 2: у/в alternation
# =============================================================================

class TestRule2UV:

    def test_detect_u_before_vowel(self):
        """у before a vowel should be flagged."""
        content = "Вони живуть у Одесі"
        violations = check_euphony_violations(content)
        assert any("у перед голосним" in v["issue"] for v in violations)

    def test_detect_v_before_v(self):
        """в before в/ф should be flagged."""
        content = "Вона працює в відділі"
        violations = check_euphony_violations(content)
        assert any("в перед в/ф" in v["issue"] for v in violations)

    def test_detect_v_before_consonant_cluster(self):
        """в before a consonant cluster should be flagged."""
        content = "Діти вчаться в школі"
        violations = check_euphony_violations(content)
        assert any("в перед збігом приголосних" in v["issue"] for v in violations)

    def test_v_before_vowel_is_ok(self):
        """в before a vowel is correct — no violation."""
        content = "Вони живуть в Одесі"
        violations = check_euphony_violations(content)
        uv = [v for v in violations if "у перед" in v["issue"] or "в перед" in v["issue"]]
        assert len(uv) == 0

    def test_fix_u_to_v_before_vowel(self):
        """Auto-fix: у before vowel → в."""
        content = "Живу у Одесі"
        fixed, count = auto_fix_euphony(content)
        assert count >= 1
        assert "в Одесі" in fixed

    def test_fix_v_to_u_before_cluster(self):
        """Auto-fix: в before consonant cluster → у."""
        content = "Вчиться в школі"
        fixed, count = auto_fix_euphony(content)
        assert count >= 1
        assert "у школі" in fixed

    def test_fix_preserves_case(self):
        """Auto-fix preserves uppercase at sentence start."""
        content = "У Одесі живуть люди"
        fixed, count = auto_fix_euphony(content)
        assert count >= 1
        assert fixed.startswith("В Одесі")


# =============================================================================
# Rule 3: з/із/зі alternation
# =============================================================================

class TestRule3ZIZ:

    def test_detect_z_before_sibilant(self):
        """з before з/с/ш/ч should be flagged."""
        content = "Зроблено з сиру та молока"
        violations = check_euphony_violations(content)
        assert any("з перед з/с/ш/ч" in v["issue"] for v in violations)

    def test_iz_before_sibilant_is_ok(self):
        """із before a sibilant is correct — no violation."""
        content = "Зроблено із сиру"
        violations = check_euphony_violations(content)
        rule3 = [v for v in violations if "з перед" in v.get("issue", "")]
        assert len(rule3) == 0

    def test_fix_z_to_iz(self):
        """Auto-fix: з before sibilant → із."""
        content = "Зроблено з сиру"
        fixed, count = auto_fix_euphony(content)
        assert count >= 1
        assert "із сиру" in fixed


# =============================================================================
# Track exemptions & edge cases
# =============================================================================

class TestExemptions:

    def test_oes_track_exempt(self):
        """OES track (Old East Slavic) should be exempt from euphony."""
        content = "вона і Олена"
        violations = check_euphony_violations(content, file_path="/curriculum/l2-uk-en/oes/module.md")
        assert len(violations) == 0


class TestEdgeCases:

    def test_multiple_violations_single_line(self):
        """A line can have multiple violations."""
        content = "вона і Олена жила у Одесі"
        violations = check_euphony_violations(content)
        assert len(violations) >= 2  # і→й + у→в

    def test_autofix_idempotent(self):
        """Running auto-fix twice should produce no additional changes."""
        content = "вона і Олена жила у Одесі з сиру"
        fixed1, count1 = auto_fix_euphony(content)
        assert count1 > 0
        fixed2, count2 = auto_fix_euphony(fixed1)
        assert count2 == 0
        assert fixed1 == fixed2
