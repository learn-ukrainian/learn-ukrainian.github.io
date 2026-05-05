"""Tests for the citation-provenance check (#1683).

Coverage:
  1. Detection — every source in the registry is recognized.
  2. Verification — flag fires for fabricated AD citation about
     `собака`. Verification passes when the source actually covers the
     headword.
  3. Annotation placement — markers go BEFORE any trailing
     `[AGREE]`/`[DISAGREE]` token so the deliberation tail check
     (`_channels_cli.py`) keeps matching.
  4. Graceful degradation — missing sources DB → soft-skip, not flag.
  5. De-duplication — multi-pattern same-source mentions in close
     proximity collapse to one citation.
  6. Regression — the canonical Gemini fabrication body from threads
     `482884ca054e` and `7c6e401053bb` flags exactly once on АД.

The verification tests use ``monkeypatch`` to swap out the actual
``wiki.sources_db`` lookup functions, so the suite runs without
needing ``data/sources.db`` to exist on the test machine.
"""

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on sys.path so ai_agent_bridge imports cleanly.
_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from ai_agent_bridge import _citation_check as cc

# ─────────────────────────────────────────────────────────────────────
# Detection
# ─────────────────────────────────────────────────────────────────────


def test_detect_antonenko_basic():
    body = "Антоненко-Давидович flags it as a Russianism."
    citations = cc.detect_citations(body)
    assert len(citations) == 1
    assert citations[0].source == "antonenko_davydovych"
    assert citations[0].source_label == "Антоненко-Давидович"


def test_detect_yak_my_hovorymo_alias_is_collapsed():
    """«Як ми говоримо» (the AD publication) is the same source —
    when both names appear close together, dedup collapses to one
    citation rather than emitting two parallel flags for one claim.
    """
    body = (
        "Антоненко-Давидович у книжці «Як ми говоримо» каже, "
        "що *собака* — чоловічого роду."
    )
    citations = cc.detect_citations(body)
    sources = [c.source for c in citations]
    assert sources.count("antonenko_davydovych") == 1, (
        f"Expected dedup to collapse to 1, got {sources}"
    )


def test_detect_all_known_sources_separately():
    body = (
        "VESUM lists *голос*. СУМ-11 has the entry. ЕСУМ traces the etymology. "
        "Грінченко 1907 attests it. Шевельов notes a phonological shift. "
        "Вихованець discusses syntax. Пономарів in his stylistic guide. "
        "Antonenko-Davydovych «Як ми говоримо». Український правопис 2019."
    )
    citations = cc.detect_citations(body)
    sources = {c.source for c in citations}
    expected = {
        "vesum",
        "sum_11",
        "esum",
        "hrinchenko_1907",
        "shevelov",
        "vykhovanets",
        "ponomariv",
        "antonenko_davydovych",
        "pravopys_2019",
    }
    assert expected.issubset(sources), (
        f"Missing sources: {expected - sources}"
    )


def test_detect_extracts_italicized_headword():
    body = "Антоненко-Давидович пише про *собака* в орудному."
    citations = cc.detect_citations(body)
    assert len(citations) == 1
    assert citations[0].headword == "собака"


def test_detect_extracts_imennyk_noun_pattern():
    body = "За Антоненком-Давидовичем, іменник собака — чоловічого роду."
    citations = cc.detect_citations(body)
    assert len(citations) == 1
    assert citations[0].headword == "собака"


def test_detect_no_citations_in_plain_message():
    assert cc.detect_citations("Hello, plain message.") == []
    assert cc.detect_citations("") == []


def test_detect_strips_stress_marks_in_normalize():
    # _normalize_word handles combining stress (U+0301) + curly apostrophes.
    # "со́бака" = с + о + U+0301 + б + а + к + а — the canonical Ukrainian
    # stress representation. Latin precomposed "á" is NOT normalized
    # because it's not a valid Ukrainian character.
    assert cc._normalize_word("Со́бака") == "собака"
    assert cc._normalize_word("дідусь’ого") == "дідусь'ого"


# ─────────────────────────────────────────────────────────────────────
# Verification — mocked lookups
# ─────────────────────────────────────────────────────────────────────


class _FakeSourcesDB:
    """Stand-in for wiki.sources_db with controllable lookup results."""

    SOURCES_DB_PATH = Path("/tmp/fake-sources-db-path-that-must-exist")

    def __init__(self, *, style_guide=None, sum11=None, hrinchenko=None, esum=None):
        self._style = style_guide or {}  # word -> [hits]
        self._sum11 = sum11 or {}
        self._hrin = hrinchenko or {}
        self._esum = esum or {}

    # The verifier only calls these via _try_load_sources_db().
    def search_style_guide(self, word, limit=5):
        return self._style.get(word, [])

    def search_definitions(self, word, limit=10):
        return self._sum11.get(word, [])

    def search_grinchenko_1907(self, word, limit=10):
        return self._hrin.get(word, [])

    def search_esum(self, query, limit=5, **kw):
        return self._esum.get(query, [])


def _make_fake_db_present(monkeypatch, **lookups):
    """Install a fake sources_db whose path is reported as existing."""
    fake = _FakeSourcesDB(**lookups)
    # Replace the lazy-load helper with one that returns our fake.
    monkeypatch.setattr(cc, "_try_load_sources_db", lambda: fake)

    # _verify_antonenko also calls _body_text_has(SOURCES_DB_PATH, ...).
    # Default it to return False so the body-text fallback doesn't
    # accidentally find hits. Tests can override.
    monkeypatch.setattr(cc, "_body_text_has", lambda *a, **kw: False)


def test_verify_antonenko_fabrication_about_sobaka_flags(monkeypatch):
    _make_fake_db_present(monkeypatch, style_guide={})
    body = (
        "Антоненко-Давидович пише, що feminine agreement with *собака* "
        "is a calque/Russianism."
    )
    result = cc.check_and_annotate(body)
    assert len(result.unverified) == 1
    assert result.unverified[0].citation.source == "antonenko_davydovych"
    assert "собака" in result.unverified[0].detail


def test_verify_antonenko_real_entry_does_not_flag(monkeypatch):
    """If AD's word column or body contains the headword, no flag."""
    _make_fake_db_present(monkeypatch, style_guide={"учень": [{"id": 1}]})
    body = "Антоненко-Давидович обговорює *учень* в орудному."
    result = cc.check_and_annotate(body)
    assert result.unverified == []


def test_verify_antonenko_body_fallback_passes(monkeypatch):
    """word-column miss but body-text hit → verified."""
    _make_fake_db_present(monkeypatch, style_guide={})
    monkeypatch.setattr(cc, "_body_text_has", lambda *a, **kw: True)
    body = "Антоненко-Давидович обговорює *учень*."
    result = cc.check_and_annotate(body)
    assert result.unverified == []


def test_verify_sum11_real_entry_does_not_flag(monkeypatch):
    _make_fake_db_present(monkeypatch, sum11={"собака": [{"word": "собака"}]})
    body = "СУМ-11 has *собака* as masculine."
    result = cc.check_and_annotate(body)
    flagged_sources = [v.citation.source for v in result.unverified]
    assert "sum_11" not in flagged_sources


def test_verify_sum11_missing_entry_flags(monkeypatch):
    _make_fake_db_present(monkeypatch, sum11={})
    body = "СУМ-11 lists *вигадка* with definition X."
    result = cc.check_and_annotate(body)
    flagged_sources = [v.citation.source for v in result.unverified]
    assert "sum_11" in flagged_sources


def test_vesum_and_shevelov_soft_skip(monkeypatch):
    _make_fake_db_present(monkeypatch)
    body = "VESUM lists *голос*. Шевельов notes a shift in *хата*."
    result = cc.check_and_annotate(body)
    # VESUM and Шевельов both have _verify_unknown — never flag.
    assert result.unverified == []
    # Both citations were detected, just not verified.
    sources = {c.source for c in result.citations}
    assert {"vesum", "shevelov"} <= sources


# ─────────────────────────────────────────────────────────────────────
# Annotation
# ─────────────────────────────────────────────────────────────────────


def test_annotation_preserves_agree_tail(monkeypatch):
    _make_fake_db_present(monkeypatch, style_guide={})
    body = "Антоненко-Давидович каже про *собака* (Russianism).\n\n[AGREE]"
    result = cc.check_and_annotate(body)
    assert result.annotated_body.rstrip().endswith("[AGREE]")
    assert "<!-- CITATION-UNVERIFIED" in result.annotated_body


def test_annotation_preserves_disagree_tail(monkeypatch):
    _make_fake_db_present(monkeypatch, style_guide={})
    body = "Антоненко-Давидович каже про *собака*.\n\n[DISAGREE]"
    result = cc.check_and_annotate(body)
    assert result.annotated_body.rstrip().endswith("[DISAGREE]")


def test_no_annotation_when_all_verified(monkeypatch):
    _make_fake_db_present(monkeypatch, style_guide={"учень": [{"id": 1}]})
    body = "Антоненко-Давидович обговорює *учень*.\n\n[AGREE]"
    result = cc.check_and_annotate(body)
    assert "<!-- CITATION-UNVERIFIED" not in result.annotated_body
    assert result.annotated_body == body  # untouched


def test_no_annotation_when_no_citations():
    result = cc.check_and_annotate("Plain message with no citations.\n\n[AGREE]")
    assert "<!-- CITATION-UNVERIFIED" not in result.annotated_body


# ─────────────────────────────────────────────────────────────────────
# Graceful degradation
# ─────────────────────────────────────────────────────────────────────


def test_missing_sources_db_soft_skips(monkeypatch):
    """When sources DB is unavailable, never flag — only soft-skip."""
    monkeypatch.setattr(cc, "_try_load_sources_db", lambda: None)
    body = "Антоненко-Давидович пише про *собака*."
    result = cc.check_and_annotate(body)
    assert result.unverified == []  # no flags
    # But citations are still detected.
    assert len(result.citations) == 1
    assert result.citations[0].source == "antonenko_davydovych"


def test_missing_pravopys_soft_skips(monkeypatch):
    monkeypatch.setattr(cc, "_try_load_pravopys", lambda: None)
    body = "Український правопис 2019 рекомендує *кав'ярня*."
    result = cc.check_and_annotate(body)
    assert result.unverified == []


# ─────────────────────────────────────────────────────────────────────
# Regression — canonical fabrication
# ─────────────────────────────────────────────────────────────────────


# Verbatim from thread `482884ca054e467a8fc7f596fb66ae96`, Gemini's r1
# reply to the собака-gender deliberation question (2026-05-05 ~00:30Z).
# Trimmed to the part that triggers the fabrication; the rest of the
# reply is grammar paradigms + adjectival-agreement which don't cite
# any source. The canonical fabrication is the explicit АД attribution.
_GEMINI_FABRICATION_482884 = """In modern literary Ukrainian, **собака** is strictly a **masculine** noun (чоловічий рід).

**Source Authority:**
This assignment is codified in VESUM and the academic dictionaries (СУМ-11, СУМ-20). It is also explicitly emphasized by Антоненко-Давидович у посібнику «Як ми говоримо», who categorizes the use of feminine agreement with *собака* as a morphological calque/Russianism.

**Declension Paradigm:**
Despite its masculine gender, *собака* belongs to the **First Declension, hard group**.

[AGREE]"""


def test_canonical_fabrication_regression_482884(monkeypatch):
    """Regression: the verbatim Gemini fake reply must flag exactly once on АД.

    The body mentions VESUM (soft-skip — no automated verifier), СУМ-11 +
    СУМ-20 (real entries — should not flag), and АД (fabricated — must
    flag). Tail is `[AGREE]` and must remain at the end of the output
    so the deliberation tail-check still recognizes the message.
    """
    # Real-world DB state for собака:
    #   - sum11.word=собака exists       (1 hit)
    #   - grinchenko.word=собака exists  (1 hit)
    #   - style_guide: NO entry, NO body mention
    _make_fake_db_present(
        monkeypatch,
        style_guide={},  # AD has no собака
        sum11={"собака": [{"word": "собака"}]},
        hrinchenko={"собака": [{"word": "собака"}]},
    )

    result = cc.check_and_annotate(_GEMINI_FABRICATION_482884)

    # Exactly one flag, on AD.
    flagged_sources = [v.citation.source for v in result.unverified]
    assert flagged_sources == ["antonenko_davydovych"], flagged_sources

    # AGREE tail is preserved at end.
    assert result.annotated_body.rstrip().endswith("[AGREE]")

    # Annotation appears before the [AGREE] tail.
    body_no_tail = result.annotated_body.rsplit("[AGREE]", 1)[0]
    assert "CITATION-UNVERIFIED" in body_no_tail
    assert "antonenko_davydovych" in body_no_tail
    assert 'headword="собака"' in body_no_tail


@pytest.mark.parametrize(
    "tail",
    ["", "\n[AGREE]", "\n\n[AGREE]", "\n[DISAGREE]", "\n\n  [AGREE]  "],
)
def test_tail_preservation_variants(monkeypatch, tail):
    _make_fake_db_present(monkeypatch, style_guide={})
    body = f"Антоненко-Давидович пише про *собака*.{tail}"
    result = cc.check_and_annotate(body)
    if tail.strip():
        assert result.annotated_body.rstrip().endswith(tail.strip())
    if "собака" in body:
        assert any(
            v.citation.source == "antonenko_davydovych"
            for v in result.unverified
        )


# ─────────────────────────────────────────────────────────────────────
# Headword extraction edge cases
# ─────────────────────────────────────────────────────────────────────


def test_headword_extraction_picks_closest_to_citation():
    """If multiple Cyrillic-headword candidates exist, prefer the one
    nearest the source-name span. Avoids picking unrelated words from
    the same paragraph.
    """
    body = (
        "Earlier we mentioned *вертеп* in passing. "
        "Now: Антоненко-Давидович пише про *собака*. "
        "And later we'll discuss *кав'ярня*."
    )
    citations = cc.detect_citations(body)
    assert len(citations) == 1
    assert citations[0].headword == "собака"


def test_headword_extraction_handles_missing():
    body = "Антоненко-Давидович is a good source."
    citations = cc.detect_citations(body)
    assert len(citations) == 1
    # No Cyrillic headword in the sentence — gracefully None.
    assert citations[0].headword is None


# ─────────────────────────────────────────────────────────────────────
# Integration with _channels.post()
# ─────────────────────────────────────────────────────────────────────


def _isolated_db(tmp_path, monkeypatch):
    """Spin up a fresh broker DB rooted in ``tmp_path`` and seed the
    test channel + agents. Returns the connection.

    Repoints ``_config.DB_PATH`` to a tmp file so each test gets its
    own DB without touching the real broker. Cleared automatically
    when ``tmp_path`` is removed at end of the test.
    """
    from ai_agent_bridge import _config, _db
    db_path = tmp_path / "messages.db"
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_db, "DB_PATH", db_path)
    conn = _db.init_db()
    conn.execute(
        "INSERT INTO channels(name, description, subscribers, created_at) "
        "VALUES (?, ?, ?, ?)",
        ("reviews", "test", "claude,gemini,codex", "2026-05-05T00:00:00Z"),
    )
    conn.commit()
    monkeypatch.setattr(_db, "get_db", lambda: conn)
    return conn


def test_channels_post_annotates_unverified_citation(monkeypatch, tmp_path):
    """End-to-end: posting a message with a fabricated citation results
    in the body (as persisted) carrying the CITATION-UNVERIFIED marker.
    """
    from ai_agent_bridge import _channels, _citation_check

    fake = _FakeSourcesDB(style_guide={})  # no AD entries
    monkeypatch.setattr(_citation_check, "_try_load_sources_db", lambda: fake)
    monkeypatch.setattr(_citation_check, "_body_text_has", lambda *a, **kw: False)

    conn = _isolated_db(tmp_path, monkeypatch)

    body = (
        "Антоненко-Давидович categorizes feminine *собака* as a Russianism."
    )
    result = _channels.post(
        "reviews",
        "gemini",
        body,
        to_agents=["claude"],
        kind="post",
        auto_snapshot=False,
    )

    row = conn.execute(
        "SELECT body FROM channel_messages WHERE message_id = ?",
        (result["message_id"],),
    ).fetchone()
    assert row is not None
    persisted = row["body"]
    assert "CITATION-UNVERIFIED" in persisted
    assert "antonenko_davydovych" in persisted
    assert 'headword="собака"' in persisted
    assert "feminine *собака*" in persisted


def test_channels_post_skips_verification_when_disabled(monkeypatch, tmp_path):
    from ai_agent_bridge import _channels, _citation_check

    fake = _FakeSourcesDB(style_guide={})
    monkeypatch.setattr(_citation_check, "_try_load_sources_db", lambda: fake)
    monkeypatch.setattr(_citation_check, "_body_text_has", lambda *a, **kw: False)

    conn = _isolated_db(tmp_path, monkeypatch)
    body = "Антоненко-Давидович пише про *собака*."
    result = _channels.post(
        "reviews",
        "gemini",
        body,
        to_agents=["claude"],
        kind="post",
        auto_snapshot=False,
        verify_citations=False,
    )
    row = conn.execute(
        "SELECT body FROM channel_messages WHERE message_id = ?",
        (result["message_id"],),
    ).fetchone()
    assert row is not None
    assert "CITATION-UNVERIFIED" not in row["body"]


def test_channels_post_skips_verification_for_system_kinds(monkeypatch, tmp_path):
    from ai_agent_bridge import _channels, _citation_check

    fake = _FakeSourcesDB(style_guide={})
    monkeypatch.setattr(_citation_check, "_try_load_sources_db", lambda: fake)
    monkeypatch.setattr(_citation_check, "_body_text_has", lambda *a, **kw: False)

    conn = _isolated_db(tmp_path, monkeypatch)
    body = "Антоненко-Давидович пише про *собака*."
    # `from_agent` must be a recognised agent; the verification skip
    # is gated on `kind`, not on the sender. Use `kind="system"` to
    # exercise the system-kind branch.
    result = _channels.post(
        "reviews",
        "user",
        body,
        to_agents=["claude"],
        kind="system",
        auto_snapshot=False,
    )
    row = conn.execute(
        "SELECT body FROM channel_messages WHERE message_id = ?",
        (result["message_id"],),
    ).fetchone()
    assert row is not None
    assert "CITATION-UNVERIFIED" not in row["body"]
