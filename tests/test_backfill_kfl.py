"""
Tests for KFL (Key Facts Ledger) backfill script.

Covers all deterministic extraction functions:
  - Subject extraction from H1
  - Chronology parsing (date extraction, year normalization, BCE, Roman numerals)
  - Quote parsing (guillemets, attribution, source)
  - Decolonization context parsing (imperial myths)
  - Vital status detection (deceased/unknown)
  - Birth/death date detection (biographical tracks)
  - KFL YAML generation and insertion
  - Idempotency (has_kfl check)
  - YAML escaping

Issue: #626
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from backfill_kfl import (
    extract_subject,
    extract_section,
    parse_chronology,
    _extract_year,
    _roman_to_int,
    parse_quotes,
    parse_decolonization,
    detect_vital_status,
    detect_birth_death,
    build_kfl_yaml,
    _yaml_escape,
    _fallback_claims,
    has_kfl,
    insert_kfl,
)


# =============================================================================
# extract_subject
# =============================================================================

class TestExtractSubject:

    def test_standard_heading(self):
        content = "# Дослідження: Трипільська цивілізація\n\nBody text."
        assert extract_subject(content) == "Трипільська цивілізація"

    def test_heading_with_extra_spaces(self):
        content = "# Дослідження:   Князь Святослав  \n\nBody."
        assert extract_subject(content) == "Князь Святослав"

    def test_no_heading(self):
        content = "Some random content without a proper heading."
        assert extract_subject(content) == ""

    def test_heading_among_other_content(self):
        content = "Intro paragraph.\n\n# Дослідження: Княгиня Ольга\n\n## Section\n"
        assert extract_subject(content) == "Княгиня Ольга"

    def test_wrong_heading_level(self):
        """## is not H1 — should not match."""
        content = "## Дослідження: Щось\n"
        assert extract_subject(content) == ""


# =============================================================================
# extract_section
# =============================================================================

class TestExtractSection:

    def test_extract_existing_section(self):
        content = (
            "# Title\n\n"
            "## Хронологія\n"
            "- event 1\n"
            "- event 2\n\n"
            "## Наступний розділ\n"
            "Other content.\n"
        )
        section = extract_section(content, "Хронологія")
        assert "event 1" in section
        assert "event 2" in section
        assert "Other content" not in section

    def test_last_section_before_eof(self):
        content = (
            "# Title\n\n"
            "## Деколонізаційний контекст\n"
            "Myth content here.\n"
        )
        section = extract_section(content, "Деколонізаційний контекст")
        assert "Myth content" in section

    def test_nonexistent_section(self):
        content = "# Title\n\n## Other\nContent.\n"
        assert extract_section(content, "Хронологія") == ""


# =============================================================================
# _extract_year
# =============================================================================

class TestExtractYear:

    def test_simple_four_digit_year(self):
        assert _extract_year("1896 р.") == 1896

    def test_approximate_year(self):
        assert _extract_year("~890 р.") == 890

    def test_year_range_takes_first(self):
        assert _extract_year("5500–5400 рр. до н.е.") == -5500

    def test_bce_marker(self):
        assert _extract_year("3500 р. до н.е.") == -3500

    def test_bce_marker_spacing(self):
        assert _extract_year("3500 р. до н. е.") == -3500

    def test_three_digit_year(self):
        assert _extract_year("882 рік") == 882

    def test_date_with_month(self):
        """'11 липня 969 р.' should extract 969."""
        assert _extract_year("11 липня 969 р.") == 969

    def test_dual_date(self):
        """'9 вересня / 18 жовтня 957 р.' → 957."""
        assert _extract_year("9 вересня / 18 жовтня 957 р.") == 957

    def test_roman_century(self):
        assert _extract_year("VII ст.") == 650  # midpoint of 7th century

    def test_roman_century_bce(self):
        assert _extract_year("IV ст. до н.е.") == -350  # midpoint of 4th century BCE

    def test_unparseable(self):
        assert _extract_year("давно") is None

    def test_empty_string(self):
        assert _extract_year("") is None


# =============================================================================
# _roman_to_int
# =============================================================================

class TestRomanToInt:

    def test_simple_numerals(self):
        assert _roman_to_int("I") == 1
        assert _roman_to_int("V") == 5
        assert _roman_to_int("X") == 10

    def test_subtractive_notation(self):
        assert _roman_to_int("IV") == 4
        assert _roman_to_int("IX") == 9
        assert _roman_to_int("XL") == 40

    def test_complex_numeral(self):
        assert _roman_to_int("XIV") == 14
        assert _roman_to_int("MCMXCIX") == 1999

    def test_lowercase_accepted(self):
        assert _roman_to_int("vii") == 7

    def test_invalid_character(self):
        assert _roman_to_int("ABC") is None

    def test_empty_string(self):
        assert _roman_to_int("") is None


# =============================================================================
# parse_chronology
# =============================================================================

class TestParseChronology:

    def test_standard_bullets(self):
        section = (
            "- **1896 р.** — Вікентій Хвойка відкрив першу стоянку\n"
            "- **~5500 рр. до н.е.** — Початок трипільської культури\n"
        )
        events = parse_chronology(section)
        assert len(events) == 2
        assert events[0]["raw_date"] == "1896 р."
        assert events[0]["year"] == 1896
        assert "Хвойка" in events[0]["event"]
        assert events[1]["year"] == -5500

    def test_dash_variants(self):
        """Should handle em-dash (—), en-dash (–), and hyphen (-)."""
        for dash in ["—", "–", "-"]:
            section = f"- **1000 р.** {dash} Подія відбулась\n"
            events = parse_chronology(section)
            assert len(events) == 1
            assert events[0]["year"] == 1000

    def test_no_bullets(self):
        section = "Just some free text without bullets."
        assert parse_chronology(section) == []

    def test_malformed_bullet(self):
        """Missing bold markers should not match."""
        section = "- 1896 — Some event\n"
        assert parse_chronology(section) == []

    def test_empty_section(self):
        assert parse_chronology("") == []


# =============================================================================
# parse_quotes
# =============================================================================

class TestParseQuotes:

    def test_guillemet_quote(self):
        section = (
            '- **Цитата Хвойки (1896):** «Ця культура має місцеве походження»\n'
        )
        quotes = parse_quotes(section)
        assert len(quotes) == 1
        assert "місцеве походження" in quotes[0]["text"]
        assert quotes[0]["attribution"] == "Хвойки"
        assert quotes[0]["source"] == "1896"

    def test_source_in_parentheses(self):
        section = '- **Цитата (ПМЛ про 3-тю помсту):** «Взяла данину»\n'
        quotes = parse_quotes(section)
        assert len(quotes) == 1
        assert "ПМЛ про 3-тю помсту" in quotes[0]["source"]

    def test_multiple_quotes_same_line(self):
        section = '- **Цитата:** «Перша» і «Друга»\n'
        quotes = parse_quotes(section)
        assert len(quotes) == 2
        assert quotes[0]["text"] == "Перша"
        assert quotes[1]["text"] == "Друга"

    def test_no_quotes(self):
        section = "- Просто факт без цитати\n"
        assert parse_quotes(section) == []

    def test_non_bullet_lines_skipped(self):
        section = "Some intro text with «quotes» here.\n- **Цитата:** «Реальна»\n"
        quotes = parse_quotes(section)
        assert len(quotes) == 1
        assert quotes[0]["text"] == "Реальна"

    def test_empty_section(self):
        assert parse_quotes("") == []

    def test_unicode_quotes(self):
        """Should also match \u201c...\u201d (left/right double quotation marks)."""
        section = '- **Цитата:** \u201cТекст цитати\u201d\n'
        quotes = parse_quotes(section)
        assert len(quotes) == 1
        assert quotes[0]["text"] == "Текст цитати"


# =============================================================================
# parse_decolonization
# =============================================================================

class TestParseDecolonization:

    def test_single_myth(self):
        section = (
            "- **Imperial/Soviet myth:** Tripillia culture was primitive.\n"
        )
        myths = parse_decolonization(section)
        assert len(myths) == 1
        assert "primitive" in myths[0]

    def test_multiple_myths(self):
        section = (
            "- **Imperial/Soviet myth:** Myth one.\n"
            "- **Ukrainian reality:** Reality one.\n"
            "- **Imperial/Soviet myth:** Myth two.\n"
            "- **Ukrainian reality:** Reality two.\n"
        )
        myths = parse_decolonization(section)
        assert len(myths) == 2
        assert "Myth one" in myths[0]
        assert "Myth two" in myths[1]

    def test_no_myths(self):
        section = "Just some context without the expected format.\n"
        assert parse_decolonization(section) == []

    def test_empty_section(self):
        assert parse_decolonization("") == []

    def test_multiline_myth_collapsed(self):
        """Multi-line myth text should be collapsed to single line."""
        section = (
            "- **Imperial/Soviet myth:** This is a long myth\n"
            "  that spans   multiple lines.\n"
        )
        myths = parse_decolonization(section)
        assert len(myths) == 1
        assert "  " not in myths[0]  # multiple spaces collapsed

    def test_ukrainian_label(self):
        """Ukrainian myth labels should also be parsed."""
        section = "- **Імперський міф:** Трипілля було примітивним.\n"
        myths = parse_decolonization(section)
        assert len(myths) == 1
        assert "примітивним" in myths[0]

    def test_imperial_myth_label(self):
        """'Imperial Myth' (without /Soviet) should match."""
        section = "- **Imperial Myth:** Kyiv was founded by Russians.\n"
        myths = parse_decolonization(section)
        assert len(myths) == 1

    def test_soviet_myth_label(self):
        section = "- **Радянський міф:** Ukraine was always part of Russia.\n"
        myths = parse_decolonization(section)
        assert len(myths) == 1

    def test_label_without_colon(self):
        """Bold label without colon after ** should still match."""
        section = "- **Imperial/Soviet myth** Tripillia was primitive.\n"
        myths = parse_decolonization(section)
        assert len(myths) == 1


# =============================================================================
# detect_vital_status
# =============================================================================

class TestDetectVitalStatus:

    def test_death_in_last_events(self):
        events = [
            {"event": "Народився у 945 р.", "year": 945},
            {"event": "Здійснив похід на Болгарію", "year": 968},
            {"event": "Загинув у бою з печенігами", "year": 972},
        ]
        assert detect_vital_status(events, "") == "deceased"

    def test_death_in_content(self):
        events = [{"event": "Правив Києвом", "year": 1000}]
        content = "Він помер у 1054 році."
        assert detect_vital_status(events, content) == "deceased"

    def test_no_death_indicators(self):
        events = [{"event": "Почав будівництво", "year": 1000}]
        assert detect_vital_status(events, "Будівельний проект.") == "unknown"

    def test_empty_events(self):
        assert detect_vital_status([], "") == "unknown"

    def test_various_death_keywords(self):
        """All death keywords should trigger 'deceased'."""
        keywords = [
            "помер", "загинув", "вбит", "смерть",
            "†", "похован", "розстрілян", "страчен"
        ]
        for kw in keywords:
            events = [{"event": f"Він {kw} у бою", "year": 1000}]
            assert detect_vital_status(events, "") == "deceased", f"Failed for: {kw}"


# =============================================================================
# detect_birth_death
# =============================================================================

class TestDetectBirthDeath:

    def test_birth_and_death(self):
        events = [
            {"event": "Народився в Києві", "year": 942, "raw_date": "942 р."},
            {"event": "Почав правити", "year": 962, "raw_date": "962 р."},
            {"event": "Загинув у бою", "year": 972, "raw_date": "972 р."},
        ]
        birth, death = detect_birth_death(events)
        assert birth == "942"
        assert death == "972"

    def test_approximate_birth(self):
        events = [
            {"event": "Народився приблизно", "year": 890, "raw_date": "~890 р."},
            {"event": "Помер", "year": 945, "raw_date": "945 р."},
        ]
        birth, death = detect_birth_death(events)
        assert birth == "~890"
        assert death == "945"

    def test_no_birth_keyword(self):
        """First event without birth keyword → no birth extracted."""
        events = [
            {"event": "Почав правити", "year": 960, "raw_date": "960 р."},
            {"event": "Загинув", "year": 972, "raw_date": "972 р."},
        ]
        birth, death = detect_birth_death(events)
        assert birth == ""
        assert death == "972"

    def test_no_death(self):
        events = [
            {"event": "Народився", "year": 1000, "raw_date": "1000 р."},
            {"event": "Правив", "year": 1020, "raw_date": "1020 р."},
        ]
        birth, death = detect_birth_death(events)
        assert birth == "1000"
        assert death == ""

    def test_empty_events(self):
        assert detect_birth_death([]) == ("", "")


# =============================================================================
# _yaml_escape
# =============================================================================

class TestYamlEscape:

    def test_no_escaping_needed(self):
        assert _yaml_escape("Simple text") == "Simple text"

    def test_escape_double_quotes(self):
        assert _yaml_escape('He said "hello"') == 'He said \\"hello\\"'

    def test_escape_backslash(self):
        assert _yaml_escape("path\\to\\file") == "path\\\\to\\\\file"

    def test_escape_newline(self):
        assert _yaml_escape("line1\nline2") == "line1 line2"

    def test_combined_escaping(self):
        assert _yaml_escape('"quote"\nnewline') == '\\"quote\\" newline'


# =============================================================================
# _fallback_claims
# =============================================================================

class TestFallbackClaims:

    def test_returns_up_to_three(self):
        myths = ["Myth 1", "Myth 2", "Myth 3", "Myth 4"]
        claims = _fallback_claims(myths)
        assert len(claims) == 3

    def test_truncates_long_claims(self):
        long_myth = "x" * 500
        claims = _fallback_claims([long_myth])
        assert len(claims[0]) == 300

    def test_empty_myths(self):
        assert _fallback_claims([]) == []


# =============================================================================
# build_kfl_yaml
# =============================================================================

class TestBuildKflYaml:

    def test_basic_structure(self):
        kfl = build_kfl_yaml(
            subject="Трипілля",
            events=[{"raw_date": "5500 р. до н.е.", "event": "Початок", "year": -5500}],
            quotes=[],
            forbidden_claims=[],
            track="hist",
        )
        assert "## Key Facts Ledger" in kfl
        assert "```yaml" in kfl
        assert "```" in kfl
        assert 'subject: "Трипілля"' in kfl
        assert "key_events:" in kfl
        assert "year: -5500" in kfl

    def test_biographical_track(self):
        """bio should include vital_status and birth/death dates."""
        events = [
            {"raw_date": "942 р.", "event": "Народився", "year": 942},
            {"raw_date": "972 р.", "event": "Загинув у бою", "year": 972},
        ]
        kfl = build_kfl_yaml(
            subject="Святослав",
            events=events,
            quotes=[],
            forbidden_claims=[],
            track="bio",
        )
        assert "vital_status:" in kfl
        assert "birth:" in kfl
        assert "death:" in kfl

    def test_non_bio_track_no_vitals(self):
        kfl = build_kfl_yaml(
            subject="Topic",
            events=[],
            quotes=[],
            forbidden_claims=[],
            track="hist",
        )
        assert "vital_status:" not in kfl

    def test_includes_quotes(self):
        kfl = build_kfl_yaml(
            subject="Topic",
            events=[],
            quotes=[{"text": "Цитата тут", "source": "ПМЛ", "attribution": "Нестор"}],
            forbidden_claims=[],
            track="hist",
        )
        assert "primary_quotes:" in kfl
        assert "Цитата тут" in kfl
        assert "ПМЛ" in kfl

    def test_includes_forbidden_claims(self):
        kfl = build_kfl_yaml(
            subject="Topic",
            events=[],
            quotes=[],
            forbidden_claims=["Claim A", "Claim B"],
            track="hist",
        )
        assert "forbidden_claims:" in kfl
        assert "Claim A" in kfl
        assert "Claim B" in kfl

    def test_caps_quotes_at_five(self):
        quotes = [{"text": f"Q{i}", "source": "", "attribution": ""} for i in range(8)]
        kfl = build_kfl_yaml("Topic", [], quotes, [], "hist")
        assert kfl.count("text:") == 5

    def test_skips_events_without_year(self):
        events = [
            {"raw_date": "невідомо", "event": "Something", "year": None},
            {"raw_date": "1000 р.", "event": "Real event", "year": 1000},
        ]
        kfl = build_kfl_yaml("Topic", events, [], [], "hist")
        assert "year: 1000" in kfl
        assert "Something" not in kfl

    def test_truncates_long_events(self):
        long_event = "x" * 300
        events = [{"raw_date": "1000 р.", "event": long_event, "year": 1000}]
        kfl = build_kfl_yaml("Topic", events, [], [], "hist")
        # Event text should be truncated to 200 chars
        assert "x" * 200 in kfl
        assert "x" * 201 not in kfl


# =============================================================================
# has_kfl
# =============================================================================

class TestHasKfl:

    def test_has_kfl_present(self):
        content = "# Title\n\n## Key Facts Ledger\n```yaml\n...\n```\n"
        assert has_kfl(content) is True

    def test_has_kfl_absent(self):
        content = "# Title\n\n## Хронологія\n- event\n"
        assert has_kfl(content) is False

    def test_empty_content(self):
        assert has_kfl("") is False


# =============================================================================
# insert_kfl
# =============================================================================

class TestInsertKfl:

    def test_insert_after_h1(self):
        content = (
            "# Дослідження: Трипілля\n\n"
            "## Хронологія\n"
            "- event 1\n"
        )
        kfl = "## Key Facts Ledger\n```yaml\nsubject: test\n```\n"
        result = insert_kfl(content, kfl)
        # KFL should appear between H1 and first ## section
        h1_pos = result.index("# Дослідження: Трипілля")
        kfl_pos = result.index("## Key Facts Ledger")
        chrono_pos = result.index("## Хронологія")
        assert h1_pos < kfl_pos < chrono_pos

    def test_no_h1_returns_unchanged(self):
        content = "## Section\nContent.\n"
        kfl = "## Key Facts Ledger\n```yaml\nsubject: test\n```\n"
        result = insert_kfl(content, kfl)
        assert result == content

    def test_insert_preserves_content(self):
        content = (
            "# Дослідження: Test\n\n"
            "## Хронологія\n"
            "- **1000 р.** — Event\n"
        )
        kfl = "## Key Facts Ledger\n```yaml\nsubject: test\n```\n"
        result = insert_kfl(content, kfl)
        assert "## Хронологія" in result
        assert "Event" in result
        assert "## Key Facts Ledger" in result

    def test_blank_line_before_kfl(self):
        """Should always have a blank line between H1 and KFL."""
        content = "# Дослідження: Test\n## Section\n"
        kfl = "## Key Facts Ledger\n```yaml\n```\n"
        result = insert_kfl(content, kfl)
        # After H1, there should be \n\n before KFL
        assert "Test\n\n## Key Facts Ledger" in result


# =============================================================================
# Integration: round-trip
# =============================================================================

class TestIntegration:

    SAMPLE_RESEARCH = (
        "# Дослідження: Трипільська цивілізація\n\n"
        "## Хронологія\n"
        "- **5500 рр. до н.е.** — Початок трипільської культури\n"
        "- **1896 р.** — Вікентій Хвойка відкрив першу стоянку\n\n"
        "## Ключові факти та цитати\n"
        "- **Цитата Хвойки (1896):** «Ця культура має місцеве походження»\n\n"
        "## Деколонізаційний контекст\n"
        "- **Imperial/Soviet myth:** Tripillia was primitive and irrelevant.\n"
        "- **Ukrainian reality:** One of the largest Copper Age civilizations.\n"
    )

    def test_full_extraction_pipeline(self):
        """End-to-end: extract all fields from a realistic research file."""
        content = self.SAMPLE_RESEARCH

        subject = extract_subject(content)
        assert subject == "Трипільська цивілізація"

        chrono = extract_section(content, "Хронологія")
        events = parse_chronology(chrono)
        assert len(events) == 2
        assert events[0]["year"] == -5500
        assert events[1]["year"] == 1896

        facts = extract_section(content, "Ключові факти та цитати")
        quotes = parse_quotes(facts)
        assert len(quotes) == 1
        assert "місцеве походження" in quotes[0]["text"]

        decol = extract_section(content, "Деколонізаційний контекст")
        myths = parse_decolonization(decol)
        assert len(myths) == 1
        assert "primitive" in myths[0]

    def test_build_and_insert(self):
        """Build KFL YAML and insert it into the research file."""
        content = self.SAMPLE_RESEARCH

        subject = extract_subject(content)
        events = parse_chronology(extract_section(content, "Хронологія"))
        quotes = parse_quotes(extract_section(content, "Ключові факти та цитати"))
        myths = parse_decolonization(extract_section(content, "Деколонізаційний контекст"))
        claims = _fallback_claims(myths)

        kfl = build_kfl_yaml(subject, events, quotes, claims, "hist")
        result = insert_kfl(content, kfl)

        # KFL should be present
        assert has_kfl(result)
        # Original content should be preserved
        assert "## Хронологія" in result
        assert "## Ключові факти та цитати" in result

    def test_idempotency(self):
        """Inserting KFL twice should not duplicate it (has_kfl guard)."""
        content = self.SAMPLE_RESEARCH
        kfl = build_kfl_yaml("Test", [], [], [], "hist")
        once = insert_kfl(content, kfl)
        assert has_kfl(once)
        # has_kfl would prevent a second insertion in process_file(),
        # but insert_kfl itself doesn't check — verify KFL is in output
        assert once.count("## Key Facts Ledger") == 1

    def test_biographical_round_trip(self):
        """Biographical track includes birth/death dates."""
        content = (
            "# Дослідження: Князь Святослав\n\n"
            "## Хронологія\n"
            "- **~942 р.** — Народився у Києві\n"
            "- **968 р.** — Похід на Болгарію\n"
            "- **972 р.** — Загинув у бою з печенігами\n\n"
            "## Ключові факти та цитати\n"
            "- **Цитата (ПМЛ):** «Іду на ви»\n"
        )

        subject = extract_subject(content)
        events = parse_chronology(extract_section(content, "Хронологія"))
        quotes = parse_quotes(extract_section(content, "Ключові факти та цитати"))

        kfl = build_kfl_yaml(subject, events, quotes, [], "bio")
        assert 'vital_status: "deceased"' in kfl
        assert 'birth: "~942"' in kfl
        assert 'death: "972"' in kfl
        assert "«Іду на ви»" in kfl or "Іду на ви" in kfl
