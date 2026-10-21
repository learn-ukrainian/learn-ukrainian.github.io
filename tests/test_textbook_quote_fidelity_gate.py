from scripts.build.linear_pipeline import _textbook_quote_fidelity_gate
from scripts.build.seminar_quote_exemptions import seminar_quote_exemption_key


def test_match(monkeypatch):
    """Test 1 — match (happy path)"""

    def mock_search(keywords, limit=20):
        return [{"text": "Це тестова цитата, яка збігається ідеально."}]

    monkeypatch.setattr("scripts.wiki.sources_db.search_textbooks", mock_search)

    module_text = """
> Це тестова цитата, яка збігається ідеально.

*— Захарійчук, Grade 1, p.24*
"""
    result = _textbook_quote_fidelity_gate(module_text)
    assert result["passed"] is True
    assert result["violations"] == []


def test_mismatch(monkeypatch):
    """Test 2 — mismatch (m20 Кнак regression)"""

    source_chunk = '''Мій день
— Сьогодні в мене багато справ, — мови-
ло жабеня Квак. — Занотую.
«Поснідати. Одягнутися. Піти до Квака.
Прогулятися з Кваком. Пообідати. Подрімати.
Погратися з Кваком. Повечеряти. Лягти спати».
— Ну от і все. Тут за-пи-са-ний  у-весь
мій  день (за Арнольдом  Лобелом).'''

    def mock_search(keywords, limit=20):
        return [{"text": source_chunk}]

    monkeypatch.setattr("scripts.wiki.sources_db.search_textbooks", mock_search)

    module_text = """
> Мій день
> — Сьогодні в мене багато справ, — мови-
> ло жабеня Кнак. — Запишу.
> «Поснідати. Одягнутися. Піти до Квака.
> Прогулятися з Кваком. Пообідати. Подрімати.
> Погратися з Кваком. Повечеряти. Лягти спати».
> — Ну от і все. Тут за-пи-са-ний  у-весь
> мій  день (за Арнольдом  Лобелом).

*— Захарійчук, Grade 1, p.24*
"""
    result = _textbook_quote_fidelity_gate(module_text)
    assert result["passed"] is False
    assert len(result["violations"]) > 0
    violation = result["violations"][0]
    assert "differs" in violation["reason"] or ">=3" in violation["reason"]
    assert "Квак" in violation["nearest_source"]


def test_partial_mismatch(monkeypatch):
    """Test 3 — partial-mismatch below threshold"""

    def mock_search(keywords, limit=20):
        # 1-char difference (ы vs и), plus missing punctuation. Less than 3 chars different after normalization.
        return [{"text": "Це тестова цитата."}]

    monkeypatch.setattr("scripts.wiki.sources_db.search_textbooks", mock_search)

    module_text = """
> Це тестова цытата.

*— Підручник, p.1*
"""
    result = _textbook_quote_fidelity_gate(module_text)
    assert result["passed"] is True
    assert result["violations"] == []


def test_no_attribution():
    """Test 4a — no-attribution"""
    module_text = """
> Це цитата без джерела.
"""
    result = _textbook_quote_fidelity_gate(module_text)
    assert result["passed"] is False
    assert len(result["violations"]) > 0
    assert "Missing attribution without NO_VERIFY" in result["violations"][0]["reason"]


def test_no_attribution_with_opt_out():
    """Test 4b — NO_VERIFY opt-out"""
    module_text = """
<!-- NO_VERIFY: orchestrator review pending -->
> Це цитата без джерела.
"""
    result = _textbook_quote_fidelity_gate(module_text)
    assert result["passed"] is True
    assert result["violations"] == []


def test_seminar_literary_source_marker_uses_literary_corpus(monkeypatch):
    calls = {"literary": 0, "textbooks": 0}

    def mock_search_literary(keywords, limit=20):
        calls["literary"] += 1
        return [
            {
                "text": "Вже весна воскресла, / Що ж сь нам принесла? / Дівоцькую красу",
            }
        ]

    def mock_search_textbooks(keywords, limit=20):
        calls["textbooks"] += 1
        return []

    monkeypatch.setattr("scripts.wiki.sources_db.search_literary", mock_search_literary)
    monkeypatch.setattr("scripts.wiki.sources_db.search_textbooks", mock_search_textbooks)

    module_text = """
> Вже весна воскресла,
> Що ж сь нам принесла?
> Дівоцькую красу.
>
> *— Грушевський [S1]*
"""
    result = _textbook_quote_fidelity_gate(module_text, level="folk")

    assert result["passed"] is True
    assert result["violations"] == []
    assert calls == {"literary": 1, "textbooks": 0}


def test_seminar_textbook_attributed_fabrication_still_fails(monkeypatch):
    calls = {"literary": 0, "textbooks": 0}

    def mock_search_literary(keywords, limit=20):
        calls["literary"] += 1
        return [{"text": "Цей літературний корпус не має рятувати підручникову цитату."}]

    def mock_search_textbooks(keywords, limit=20):
        calls["textbooks"] += 1
        return []

    monkeypatch.setattr("scripts.wiki.sources_db.search_literary", mock_search_literary)
    monkeypatch.setattr("scripts.wiki.sources_db.search_textbooks", mock_search_textbooks)

    module_text = """
> Вигаданий уривок, якого немає в підручнику, але він має підручникову атрибуцію.

*— Заболотний, Grade 6, p.11*
"""
    result = _textbook_quote_fidelity_gate(module_text, level="folk")

    assert result["passed"] is False
    assert result["violations"] == [
        {
            "quote": "Вигаданий уривок, якого немає в підручнику, але він має підручникову атрибуцію.",
            "attribution": "Заболотний, Grade 6, p.11",
            "reason": "No match in textbook corpus",
        }
    ]
    assert calls == {"literary": 0, "textbooks": 1}


def test_core_level_matches_default_textbook_behavior(monkeypatch):
    calls = {"literary": 0, "textbooks": 0}

    def mock_search_literary(keywords, limit=20):
        calls["literary"] += 1
        return []

    def mock_search_textbooks(keywords, limit=20):
        calls["textbooks"] += 1
        return [{"text": "Це справжня підручникова цитата."}]

    monkeypatch.setattr("scripts.wiki.sources_db.search_literary", mock_search_literary)
    monkeypatch.setattr("scripts.wiki.sources_db.search_textbooks", mock_search_textbooks)

    module_text = """
> Це справжня підручникова цитата.

*— Захарійчук, Grade 1, p.24*
"""
    default_result = _textbook_quote_fidelity_gate(module_text)
    core_result = _textbook_quote_fidelity_gate(module_text, level="a1")

    assert core_result == default_result
    assert core_result["passed"] is True
    assert core_result["violations"] == []
    assert calls == {"literary": 0, "textbooks": 2}


def test_core_level_does_not_accept_seminar_embedded_attribution(monkeypatch):
    calls = {"textbooks": 0}

    def mock_search_textbooks(keywords, limit=20):
        calls["textbooks"] += 1
        return [{"text": "Це справжня підручникова цитата."}]

    monkeypatch.setattr("scripts.wiki.sources_db.search_textbooks", mock_search_textbooks)

    module_text = """
> Це справжня підручникова цитата.
>
> *— Захарійчук, Grade 1, p.24*
"""
    default_result = _textbook_quote_fidelity_gate(module_text)
    core_result = _textbook_quote_fidelity_gate(module_text, level="a1")

    assert core_result == default_result
    assert core_result["passed"] is False
    assert core_result["violations"][0]["reason"] == "Missing attribution without NO_VERIFY"
    assert calls == {"textbooks": 0}


def test_seminar_no_verify_attested_fragment_passes(monkeypatch):
    calls = {"literary": 0}

    def mock_search_literary(keywords, limit=20):
        calls["literary"] += 1
        return [{"text": "Ой на горі вогонь горить, а в долині вода."}]

    monkeypatch.setattr("scripts.wiki.sources_db.search_literary", mock_search_literary)

    module_text = """
<!-- NO_VERIFY: корпусно звірений фрагмент -->
> Ой на горі вогонь горить, а в долині вода.

*— народна дума [S1]*
"""
    result = _textbook_quote_fidelity_gate(
        module_text,
        level="folk",
        module_slug="narodni-balady",
    )

    assert result["passed"] is True
    assert result["violations"] == []
    assert result["warnings"] == []
    assert calls["literary"] == 1


def test_seminar_no_verify_fabricated_fragment_fails_without_exemption(monkeypatch):
    monkeypatch.setattr("scripts.wiki.sources_db.search_literary", lambda keywords, limit=20: [])

    module_text = """
<!-- NO_VERIFY: корпусно звірений фрагмент -->
> Цей уривок вигаданий і не має бути в корпусі.

*— Kupala [S1]*
"""
    result = _textbook_quote_fidelity_gate(
        module_text,
        level="folk",
        module_slug="narodni-balady",
    )

    assert result["passed"] is False
    assert result["violations"] == [
        {
            "quote": "Цей уривок вигаданий і не має бути в корпусі.",
            "attribution": "Kupala [S1]",
            "reason": (
                "NO_VERIFY on seminar level but fragment not corpus-attested "
                "and not exempted"
            ),
        }
    ]


def test_seminar_no_verify_fabricated_fragment_with_exemption_warns(monkeypatch):
    quote = "Цей уривок вигаданий і не має бути в корпусі."
    exemption_key = seminar_quote_exemption_key("narodni-balady", quote)
    exemption = {
        "module_slug": "narodni-balady",
        "reason": "manual reviewer attestation pending corpus ingest",
        "reviewer": "folk-track-driver",
        "date": "2026-07-05",
    }

    monkeypatch.setattr("scripts.wiki.sources_db.search_literary", lambda keywords, limit=20: [])
    monkeypatch.setattr(
        "scripts.build.seminar_quote_exemptions.load_seminar_quote_exemptions",
        lambda: {exemption_key: exemption},
    )

    module_text = f"""
<!-- NO_VERIFY: корпусно звірений фрагмент -->
> {quote}

*— Kupala [S1]*
"""
    result = _textbook_quote_fidelity_gate(
        module_text,
        level="folk",
        module_slug="narodni-balady",
    )

    assert result["passed"] is True
    assert result["violations"] == []
    assert len(result["warnings"]) == 1
    assert result["warnings"][0]["reason"] == (
        "NO_VERIFY seminar quote exempted from corpus match"
    )
    assert result["warnings"][0]["exemption"] == exemption
    assert result["verdict"] == "WARN"
    assert result["severity"] == "WARN"


def test_core_no_verify_fragment_still_skipped(monkeypatch):
    calls = {"textbooks": 0}

    def mock_search_textbooks(keywords, limit=20):
        calls["textbooks"] += 1
        return []

    monkeypatch.setattr("scripts.wiki.sources_db.search_textbooks", mock_search_textbooks)

    module_text = """
<!-- NO_VERIFY: orchestrator review pending -->
> Це цитата без джерела.

*— Захарійчук, Grade 1, p.24*
"""
    result = _textbook_quote_fidelity_gate(module_text, level="a1")

    assert result["passed"] is True
    assert result["violations"] == []
    assert calls["textbooks"] == 0
