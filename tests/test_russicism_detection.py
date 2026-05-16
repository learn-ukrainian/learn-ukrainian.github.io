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

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.checks.russicism_detection import (
    _is_in_quote_context,
    check_russicisms,
    check_ua_gec_calques,
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


# =============================================================================
# UA-GEC CALQUE PATTERNS — added 2026-05-14 from UA-GEC v2 F/Calque mining
# (CC-BY-4.0, github.com/grammarly/ua-gec)
# =============================================================================

class TestUaGecCalquePatterns:
    """Each new pattern: positive case + negative (legitimate use) where applicable."""

    # --- Discourse-marker calques ---

    def test_таким_чином_caught(self):
        violations = check_russicisms(_wrap("Таким чином, ми розглянули проблему."))
        assert violations and "таким чином" in violations[0]["issue"]

    def test_так_як_caught(self):
        violations = check_russicisms(_wrap("Це питання так як і інші не вирішено."))
        assert violations and "так як" in violations[0]["issue"]

    def test_в_цілому_caught(self):
        violations = check_russicisms(_wrap("В цілому ситуація стабільна."))
        assert violations and "в цілому" in violations[0]["issue"]

    def test_в_першу_чергу_caught(self):
        violations = check_russicisms(_wrap("В першу чергу слід згадати про це."))
        assert violations and "в першу чергу" in violations[0]["issue"]

    def test_з_іншої_сторони_caught(self):
        violations = check_russicisms(_wrap("З іншої сторони, це не зовсім так."))
        assert violations and "сторони" in violations[0]["issue"]

    def test_з_однієї_сторони_caught(self):
        violations = check_russicisms(_wrap("З однієї сторони, це добре."))
        assert violations and "сторони" in violations[0]["issue"]

    def test_значить_discourse_marker_caught(self):
        """`Значить,` as parenthetical — calque."""
        violations = check_russicisms(_wrap("Значить, ми маємо рацію."))
        assert violations and "значить" in violations[0]["issue"]

    def test_значить_verbal_use_clean(self):
        """`значить` as verb (= 'means') — correct UK, must NOT flag."""
        violations = check_russicisms(_wrap("Це слово багато значить для мене."))
        assert violations == []

    # --- Lexical Russianisms ---

    def test_співпадають_caught(self):
        violations = check_russicisms(_wrap("Числа співпадають точно."))
        assert violations and "співпада" in violations[0]["issue"]

    def test_бормотати_caught(self):
        violations = check_russicisms(_wrap("Він почав бормотати щось незрозуміле."))
        assert violations and "бормот" in violations[0]["issue"]

    def test_буфетчик_caught(self):
        violations = check_russicisms(_wrap("Буфетчик подав каву."))
        assert violations and "буфетчик" in violations[0]["issue"]

    def test_прийшлось_caught(self):
        violations = check_russicisms(_wrap("Прийшлось довго чекати."))
        assert violations and "прийшлось" in violations[0]["issue"]

    def test_повезе_caught(self):
        violations = check_russicisms(_wrap("Може повезе наступного разу."))
        assert violations and "повезе" in violations[0]["issue"]

    def test_відправився_reflexive_caught(self):
        """Reflexive `відправився` (= departed) is RU calque."""
        violations = check_russicisms(_wrap("Він відправився у дорогу рано-вранці."))
        assert violations and "відправ" in violations[0]["issue"]

    def test_відправляється_transitive_clean(self):
        """Transitive `відправляється` (= is sent) is correct UK."""
        violations = check_russicisms(_wrap("Поїзд відправляється о шостій."))
        assert violations == []

    def test_відношення_caught(self):
        violations = check_russicisms(_wrap("Це важливе відношення між нами."))
        assert violations and "відношення" in violations[0]["issue"]

    # --- Fixed-expression calques ---

    def test_робив_вигляд_caught(self):
        violations = check_russicisms(_wrap("Він робив вигляд, що читає."))
        assert violations and "робив вигляд" in violations[0]["issue"]

    def test_на_фоні_caught(self):
        violations = check_russicisms(_wrap("На фоні цих подій настав спокій."))
        assert violations and "на фоні" in violations[0]["issue"]

    def test_справа_в_тому_caught(self):
        violations = check_russicisms(_wrap("Справа в тому, що ми не готові."))
        assert violations and "справа в тому" in violations[0]["issue"]

    def test_справа_у_тому_caught(self):
        """`Справа у тому` — variant spelling of same calque."""
        violations = check_russicisms(_wrap("Справа у тому, що часу немає."))
        assert violations and "справа в тому" in violations[0]["issue"]

    def test_справа_other_sense_clean(self):
        """`справа` in 'matter / case' sense — correct UK, must NOT flag."""
        violations = check_russicisms(_wrap("Кожна справа важлива для людей."))
        assert violations == []

    # --- Numerical-sense calque ---

    def test_пару_numerical_caught(self):
        """`пару` as numeral ('a couple of days') — RU calque."""
        violations = check_russicisms(_wrap("Зустрінемось через пару днів."))
        assert violations and "пару" in violations[0]["issue"]

    def test_пару_numerical_hours_caught(self):
        violations = check_russicisms(_wrap("Чекай пару годин."))
        assert violations and "пару" in violations[0]["issue"]

    def test_пару_noun_clean(self):
        """`пара / пару` as noun ('a pair of shoes') — correct UK."""
        violations = check_russicisms(_wrap("Купив нову пару взуття."))
        assert violations == []


# =============================================================================
# UA-GEC BULK LOOKUP TABLE — info-only F/Calque suggestions
# =============================================================================

class TestUaGecBulkLookup:
    """Bulk CSV lookup catches high-frequency UA-GEC calques as non-blocking info."""

    def test_detects_коментарій(self):
        violations = check_ua_gec_calques(_wrap("Автор залишив коментарій до тексту."))
        assert violations and violations[0]["matched"].casefold() == "коментарій"

    def test_detects_підписників(self):
        violations = check_ua_gec_calques(_wrap("У блогу вже багато підписників."))
        assert violations and violations[0]["matched"].casefold() == "підписників"

    def test_detects_посту(self):
        violations = check_ua_gec_calques(_wrap("Після посту автор відповів на питання."))
        assert violations and violations[0]["matched"].casefold() == "посту"

    def test_detects_лайки(self):
        violations = check_ua_gec_calques(_wrap("Цей текст швидко зібрав лайки."))
        assert violations and violations[0]["matched"].casefold() == "лайки"

    def test_detects_вірно(self):
        violations = check_ua_gec_calques(_wrap("Вірно пояснити правило важливо."))
        assert violations and violations[0]["matched"].casefold() == "вірно"

    def test_detects_дозволяє(self):
        violations = check_ua_gec_calques(_wrap("Цей підхід дозволяє краще бачити структуру."))
        assert violations and violations[0]["matched"].casefold() == "дозволяє"

    def test_detects_як_тільки(self):
        violations = check_ua_gec_calques(_wrap("Як тільки учень читає, він бачить приклад."))
        assert violations and violations[0]["matched"].casefold() == "як тільки"

    def test_detects_у_якості(self):
        violations = check_ua_gec_calques(_wrap("Це слово використано у якості прикладу."))
        assert violations and violations[0]["matched"].casefold() == "у якості"

    def test_пара_взуття_not_flagged(self):
        violations = check_ua_gec_calques(_wrap("На полиці стоїть пара взуття."))
        assert violations == []

    def test_справа_generic_not_flagged(self):
        violations = check_ua_gec_calques(_wrap("Кожна справа важлива для громади."))
        assert violations == []

    def test_наступний_krok_not_flagged(self):
        violations = check_ua_gec_calques(_wrap("Будь-який наступний крок потребує уваги."))
        assert violations == []

    def test_даний_math_context_not_flagged(self):
        violations = check_ua_gec_calques(_wrap("Даний метод у геометрії допомагає довести теорему."))
        assert violations == []

    def test_all_matches_are_info(self):
        violations = check_ua_gec_calques(_wrap("Коментарій до посту отримав лайки."))
        assert violations
        assert {violation["severity"] for violation in violations} == {"info"}

    def test_quotes_and_blockquotes_skipped(self):
        quoted = check_ua_gec_calques(_wrap("Він написав: «Коментарій до посту отримав лайки»."))
        blockquoted = check_ua_gec_calques(_wrap("> Коментарій до посту отримав лайки."))
        assert quoted == []
        assert blockquoted == []
