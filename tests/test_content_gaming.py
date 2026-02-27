"""
Tests for content gaming detection checks.

Covers:
- check_section_balance() — section proportion limits (#610)
- check_ipa_density() — IPA transcription word count cap (#610)
- check_filler_phrases() — LLM hedging/padding phrase detection
- check_section_depth() — shallow H2 section detection
- check_example_diversity() — template-identical example runs

Issue: #520, #610
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.checks.content_gaming import (
    check_section_balance,
    check_ipa_density,
    check_filler_phrases,
    check_section_depth,
    check_example_diversity,
)


# =============================================================================
# HELPERS
# =============================================================================

def _make_module(sections: dict[str, str], level: str = "B1") -> str:
    """Build a minimal module with given H2 sections and word counts."""
    parts = [f"---\nlevel: {level}\n---\n\n# Title\n"]
    for header, body in sections.items():
        parts.append(f"\n## {header}\n\n{body}\n")
    return '\n'.join(parts)


def _words(n: int, base: str = "слово") -> str:
    """Generate n Ukrainian-ish words."""
    return ' '.join(f"{base}{i}" for i in range(n))


# =============================================================================
# SECTION BALANCE TESTS
# =============================================================================

class TestSectionBalance:

    def test_balanced_sections_no_violation(self):
        """3 sections of roughly equal size pass."""
        content = _make_module({
            "Вступ": _words(100),
            "Пояснення": _words(100),
            "Практика": _words(100),
        })
        violations = check_section_balance(content)
        assert violations == []

    def test_single_bloated_section_warning(self):
        """One section at ~45% triggers warning."""
        content = _make_module({
            "Вступ": _words(50),
            "Пояснення": _words(180),  # ~45% of 400
            "Практика": _words(100),
            "Підсумок": _words(70),
        })
        violations = check_section_balance(content)
        assert len(violations) == 1
        assert violations[0]['severity'] == 'warning'
        assert violations[0]['type'] == 'SECTION_BALANCE_BLOATED'

    def test_single_bloated_section_critical(self):
        """One section at ~70% triggers critical."""
        content = _make_module({
            "Вступ": _words(30),
            "Пояснення": _words(350),  # ~70% of 500
            "Практика": _words(50),
            "Діалоги": _words(70),
        })
        violations = check_section_balance(content)
        assert len(violations) == 1
        assert violations[0]['severity'] == 'critical'

    def test_fewer_than_3_sections_skipped(self):
        """Modules with <3 H2 sections are skipped."""
        content = _make_module({
            "Вступ": _words(300),
            "Пояснення": _words(100),
        })
        violations = check_section_balance(content)
        assert violations == []

    def test_all_empty_sections_no_crash(self):
        """All empty sections don't cause division by zero."""
        content = _make_module({
            "A": "",
            "B": "",
            "C": "",
        })
        violations = check_section_balance(content)
        assert violations == []  # total_words=0, returns early


# =============================================================================
# IPA DENSITY TESTS
# =============================================================================

class TestIpaDensity:

    def test_no_ipa_no_violation(self):
        """Content without IPA passes."""
        content = _make_module({"Пояснення": _words(200)})
        violations = check_ipa_density(content)
        assert violations == []

    def test_normal_ipa_usage_passes(self):
        """A few IPA transcriptions in prose are fine."""
        body = _words(200) + " /prɪˈvit/ слово /ˈmɑːtʲi/ ще"
        content = _make_module({"Пояснення": body})
        violations = check_ipa_density(content)
        assert violations == []

    def test_excessive_ipa_noop(self):
        """IPA check is now a no-op (IPA removed from curriculum)."""
        ipa_blocks = " ".join([f"/prɪˈvit{i}/" for i in range(15)])
        body = _words(100) + " " + ipa_blocks
        content = _make_module({"Пояснення": body})
        violations = check_ipa_density(content)
        assert violations == []

    def test_slash_alternatives_not_ipa(self):
        """Plain slashes like він/вона should NOT be detected as IPA."""
        body = (
            _words(100) + " він/вона/воно "
            "та/або/чи " + _words(50)
        )
        content = _make_module({"Пояснення": body})
        violations = check_ipa_density(content)
        assert violations == []

    def test_bracket_ipa_noop(self):
        """IPA check is now a no-op (IPA removed from curriculum)."""
        ipa_blocks = " ".join([f"[ˈslovo{i}]" for i in range(20)])
        body = _words(80) + " " + ipa_blocks
        content = _make_module({"Пояснення": body})
        violations = check_ipa_density(content)
        assert violations == []


# =============================================================================
# FILLER PHRASE TESTS
# =============================================================================

class TestFillerPhrases:

    def test_clean_content_no_violation(self):
        """Content without filler phrases passes."""
        content = _make_module({"Пояснення": _words(200)})
        violations = check_filler_phrases(content)
        assert violations == []

    def test_moderate_fillers_warning(self):
        """6 filler phrases triggers warning for non-academic level."""
        fillers = '\n'.join([
            "Варто зазначити, що це важливо.",
            "Як ми бачимо, граматика потрібна.",
            "Цікаво, що це працює.",
            "Важливо зрозуміти цю тему.",
            "Слід зауважити, що правило просте.",
            "Необхідно підкреслити значення.",
        ])
        content = _make_module({"Пояснення": fillers + "\n" + _words(100)})
        violations = check_filler_phrases(content)
        assert len(violations) == 1
        assert violations[0]['severity'] == 'warning'

    def test_academic_level_higher_threshold(self):
        """C1 content gets higher filler threshold."""
        fillers = '\n'.join([
            "Варто зазначити, що це важливо.",
            "Як ми бачимо, граматика потрібна.",
            "Цікаво, що це працює.",
            "Важливо зрозуміти цю тему.",
            "Слід зауважити, що правило просте.",
            "Необхідно підкреслити значення.",
        ])
        content = _make_module(
            {"Пояснення": fillers + "\n" + _words(100)},
            level="C1",
        )
        violations = check_filler_phrases(content)
        # 6 fillers is below C1 threshold (8), so no violation
        assert violations == []


# =============================================================================
# SECTION DEPTH TESTS
# =============================================================================

class TestSectionDepth:

    def test_adequate_sections_pass(self):
        """Sections with enough words pass."""
        content = _make_module({
            "Вступ": _words(120),
            "Пояснення": _words(150),
            "Практика": _words(120),
        })
        violations = check_section_depth(content)
        assert violations == []

    def test_shallow_sections_warning(self):
        """A few shallow sections trigger warning."""
        content = _make_module({
            "Вступ": _words(20),
            "Пояснення": _words(150),
            "Практика": _words(30),
        })
        violations = check_section_depth(content)
        assert len(violations) == 1
        assert violations[0]['severity'] == 'warning'

    def test_a1_lower_threshold(self):
        """A1 uses 50-word threshold instead of 100."""
        content = _make_module({
            "Вступ": _words(60),
            "Пояснення": _words(80),
            "Практика": _words(55),
        }, level="A1")
        violations = check_section_depth(content)
        assert violations == []


# =============================================================================
# EXAMPLE DIVERSITY TESTS
# =============================================================================

class TestExampleDiversity:

    def test_diverse_examples_pass(self):
        """Examples with varied vocabulary pass."""
        body = "\n".join([
            "- Хлопець читає цікаву книгу в бібліотеці.",
            "- Мама готує смачний обід на кухні.",
            "- Студент пише складний іспит у залі.",
        ])
        content = _make_module({"Пояснення": body})
        violations = check_example_diversity(content)
        assert violations == []

    def test_a1_skipped(self):
        """A1 modules skip example diversity check."""
        body = "\n".join([
            "- Я бачу книгу.",
            "- Я бачу стіл.",
            "- Я бачу кота.",
            "- Я бачу собаку.",
        ])
        content = _make_module({"Пояснення": body}, level="A1")
        violations = check_example_diversity(content)
        assert violations == []

    def test_template_identical_run_warning(self):
        """3+ examples with >70% word overlap triggers warning at B1+."""
        # These share "Учень вивчає ... у школі" template
        body = "\n".join([
            "- Учень вивчає математику у школі щодня після обіду.",
            "- Учень вивчає фізику у школі щодня після обіду.",
            "- Учень вивчає хімію у школі щодня після обіду.",
            "- Учень вивчає біологію у школі щодня після обіду.",
        ])
        content = _make_module({"Пояснення": body})
        violations = check_example_diversity(content)
        assert len(violations) == 1
        assert violations[0]['type'] == 'TEMPLATE_EXAMPLE_RUN'
