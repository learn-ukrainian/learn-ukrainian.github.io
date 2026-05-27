
from scripts.build.linear_pipeline import _textbook_quote_fidelity_gate


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
