"""
Tests for Russicism detection audit check.

Covers:
- Pattern matching for 13 Russicism patterns
- Quote context awareness (guillemets, blockquotes)
- Track exemptions (OES/RUTH)
- Severity escalation (1-2 = warning, 3+ = critical)

Issue: #520, #596
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.checks.russicism_detection import (
    check_russicisms,
    _is_in_quote_context,
)


# =============================================================================
# HELPERS
# =============================================================================

def _wrap(text: str) -> str:
    """Wrap text in minimal module structure so narrative zone parsing works."""
    return f"---\nlevel: B1\n---\n\n# Title\n\n## Пояснення\n\n{text}\n"


# =============================================================================
# BASIC DETECTION
# =============================================================================

class TestBasicDetection:

    def test_clean_content_no_violations(self):
        """Standard Ukrainian content produces no violations."""
        content = _wrap(
            "Студент бере участь у конференції. "
            "Він отримує нові знання. "
            "Наступний крок — практика."
        )
        violations = check_russicisms(content)
        assert violations == []

    def test_detects_приймати_участь(self):
        """Detects 'приймати участь' (should be 'брати участь')."""
        content = _wrap("Він вирішив приймати участь у конкурсі.")
        violations = check_russicisms(content)
        assert len(violations) == 1
        assert "приймати участь" in violations[0]['issue']

    def test_detects_получати(self):
        """Detects 'получати' (should be 'отримувати')."""
        content = _wrap("Вони будуть получати зарплату вчасно.")
        violations = check_russicisms(content)
        assert len(violations) == 1
        assert "получати" in violations[0]['issue']

    def test_detects_відноситися(self):
        """Detects 'відноситися' (should be 'стосуватися')."""
        content = _wrap("Це відноситися до граматики.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_detects_слідуючий(self):
        """Detects 'слідуючий' (should be 'наступний')."""
        content = _wrap("Слідуючий урок буде складнішим.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_detects_кушати(self):
        """Detects 'кушати' (should be 'їсти')."""
        content = _wrap("Давайте кушати разом.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_detects_вообще(self):
        """Detects 'вообще' (should be 'взагалі')."""
        content = _wrap("Він вообще не розуміє правил.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_detects_нравитися(self):
        """Detects 'нравитися' (should be 'подобатися')."""
        content = _wrap("Мені нравитися ця книга.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_detects_скучати(self):
        """Detects 'скучати' (should be 'сумувати')."""
        content = _wrap("Я скучати за тобою.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_detects_самий_кращий(self):
        """Detects 'самий кращий' (should be 'найкращий')."""
        content = _wrap("Це самий кращий варіант.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_detects_любий_as_any(self):
        """Detects 'любий момент' meaning 'any moment' (should be 'будь-який')."""
        content = _wrap("Це може статися в любий момент.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_любий_as_dear_not_flagged(self):
        """'Любий' meaning 'dear/beloved' should NOT be flagged."""
        content = _wrap("Любий друже, як справи?")
        violations = check_russicisms(content)
        assert violations == []


# =============================================================================
# SEVERITY ESCALATION
# =============================================================================

class TestSeverity:

    def test_single_russicism_warning(self):
        """1 Russicism = warning severity."""
        content = _wrap("Він получати листа.")
        violations = check_russicisms(content)
        assert len(violations) == 1
        assert violations[0]['severity'] == 'warning'

    def test_three_russicisms_critical(self):
        """3+ Russicisms = critical severity."""
        content = _wrap(
            "Він получати листа. "
            "Вона кушати суп. "
            "Вообще це неправильно."
        )
        violations = check_russicisms(content)
        assert len(violations) == 1  # One aggregated violation
        assert violations[0]['severity'] == 'critical'
        assert "3" in violations[0]['issue']


# =============================================================================
# QUOTE CONTEXT AWARENESS
# =============================================================================

class TestQuoteContext:

    def test_guillemets_not_flagged(self):
        """Russicisms inside «guillemets» are skipped (quoted speech)."""
        content = _wrap('Він сказав: «Треба кушати більше овочів».')
        violations = check_russicisms(content)
        assert violations == []

    def test_blockquote_not_flagged(self):
        """Russicisms in blockquotes are skipped."""
        content = _wrap(
            "> Давня приказка: получати мало, а працювати багато."
        )
        violations = check_russicisms(content)
        assert violations == []

    def test_outside_quotes_still_flagged(self):
        """Russicism outside quotes is still flagged even with quoted ones."""
        content = _wrap(
            '«Він получати листа» — це неправильно. '
            'Але він знову получати помилки.'
        )
        violations = check_russicisms(content)
        assert len(violations) == 1  # Only the non-quoted one

    def test_is_in_quote_context_guillemets(self):
        """Helper correctly identifies guillemet context."""
        text = "Він сказав: «кушати треба» і пішов."
        # Position of "кушати" is after «
        pos = text.index("кушати")
        assert _is_in_quote_context(text, pos) is True

    def test_is_in_quote_context_not_in_quote(self):
        """Helper correctly identifies non-quote context."""
        text = "Він любить кушати суп."
        pos = text.index("кушати")
        assert _is_in_quote_context(text, pos) is False


# =============================================================================
# TRACK EXEMPTIONS
# =============================================================================

class TestTrackExemptions:

    def test_oes_track_exempt(self):
        """OES track content is exempt (historical texts)."""
        content = _wrap("Він получати грамоту від князя.")
        violations = check_russicisms(content, file_path="/curriculum/l2-uk-en/oes/module.md")
        assert violations == []

    def test_ruth_track_exempt(self):
        """RUTH track content is exempt (historical texts)."""
        content = _wrap("Слідуючий документ важливий.")
        violations = check_russicisms(content, file_path="/curriculum/l2-uk-en/ruth/module.md")
        assert violations == []

    def test_b1_track_not_exempt(self):
        """B1 track content is NOT exempt."""
        content = _wrap("Він получати грамоту.")
        violations = check_russicisms(content, file_path="/curriculum/l2-uk-en/b1/module.md")
        assert len(violations) == 1


# =============================================================================
# CASE INSENSITIVITY
# =============================================================================

class TestCaseInsensitivity:

    def test_uppercase_detected(self):
        """Russicisms at sentence start (capitalized) are detected."""
        content = _wrap("Получати знання — це важливо.")
        violations = check_russicisms(content)
        assert len(violations) == 1

    def test_mixed_case_detected(self):
        """Mixed case variants are detected."""
        content = _wrap("ВООБЩЕ це дивно.")
        violations = check_russicisms(content)
        assert len(violations) == 1
