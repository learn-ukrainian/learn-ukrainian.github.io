"""Tests for the MCP Sources server (.mcp/servers/sources/server.py).

Historically called the "MCP RAG server" — the current implementation
is SQLite FTS5, not vector RAG, so the server was renamed to `sources`
in the April 2026 rename pass. Tool prefix is mcp__sources__*.

Covers:
- Tool listing returns all expected tools with correct schemas
- Tool dispatch routes to correct handlers
- SSE mode uses stateless=True (fix for initialization handshake issue)
- verify_word / verify_words handlers return correct format
- Error handling for unknown tools
"""

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"


@pytest.fixture
def server_module():
    """Import the server module fresh."""
    spec = importlib.util.spec_from_file_location("sources_server", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server"] = srv
    spec.loader.exec_module(srv)
    return srv


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


class TestListTools:
    """Test that list_tools returns all expected tools with valid schemas."""

    def test_returns_all_tools(self, server_module):
        tools = _run(server_module.list_tools())
        tool_names = {t.name for t in tools}

        expected = {
            "search_sources", "search_text", "search_images", "search_literary", "search_external",
            "get_full_text", "get_chunk_context", "collection_stats",
            "verify_word", "verify_source_attribution", "verify_words", "vet_vocabulary", "verify_lemma", "verify_quote", "check_modern_form",
            "verify_stress",
            "query_wikipedia", "query_grac", "query_ulif", "query_ulif_synonyms",
            "query_ulif_antonyms", "query_ulif_phraseology",
            "query_r2u", "query_e2u", "query_sum20", "query_slovnyk_me",
            "query_pravopys", "query_cefr_level",
            "search_style_guide", "search_definitions", "search_grinchenko_1907",
            "search_idioms", "search_synonyms", "translate_en_uk",
            "search_esum", "search_slovnyk_me", "search_heritage", "check_russian_shadow",
            "search_ua_gec_errors",
        }
        missing = expected - tool_names
        extra = tool_names - expected
        assert not missing, f"missing tools: {missing}"
        assert not extra, (
            f"unexpected tools: {extra}. Update the test expected set — "
            f"adding a tool to the server always requires a test update."
        )

    def test_all_tools_have_input_schema(self, server_module):
        tools = _run(server_module.list_tools())
        for tool in tools:
            assert tool.input_schema is not None, f"{tool.name} missing input_schema"
            assert tool.input_schema.get("type") == "object", f"{tool.name} schema not object type"

    def test_verify_word_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vw = next(t for t in tools if t.name == "verify_word")
        assert "word" in vw.input_schema["required"]
        assert "word" in vw.input_schema["properties"]

    def test_query_ulif_schema_accepts_structured_sections(self, server_module):
        tools = _run(server_module.list_tools())
        ulif = next(tool for tool in tools if tool.name == "query_ulif")
        sections = ulif.input_schema["properties"]["sections"]
        assert "default" not in sections
        assert sections["items"]["enum"] == [
            "paradigm", "synonyms", "antonyms", "phraseology",
        ]
        assert "When supplied" in sections["description"]


class TestUlifHandlers:
    def test_query_ulif_without_sections_renders_legacy_paradigm(self, server_module):
        paradigm = {"word": "великий", "rows": [["Називний", "великий"]]}
        with patch("rag.source_query.ulif_paradigm", return_value=paradigm) as query:
            result = _run(server_module.handle_query_ulif({"word": "великий"}))

        query.assert_called_once_with("великий")
        assert result[0].text == "Paradigm for 'великий':\n\nНазивний | великий"

    def test_query_ulif_without_sections_renders_legacy_no_result(self, server_module):
        with patch("rag.source_query.ulif_paradigm", return_value=None) as query:
            result = _run(server_module.handle_query_ulif({"word": "відсутнє"}))

        query.assert_called_once_with("відсутнє")
        assert result[0].text == "No ULIF paradigm found for: 'відсутнє'"

    def test_query_ulif_renders_structured_source_metadata(self, server_module):
        expected = {
            "source_id": "ulif_dictua",
            "official_url": "https://lcorp.ulif.org.ua/dictua",
            "attribution_label": "«Словники України» (Український мовно-інформаційний фонд НАН України)",
            "retrieved_at": "2026-07-15T00:00:00+00:00",
            "content_sha256": "a" * 64,
            "parser_version": "ulif-dictua-v1",
            "status": "ok",
            "sections": {"paradigm": {"rows": [["Називний", "великий"]]}},
        }
        with patch("rag.source_query.query_ulif", return_value=expected) as query:
            result = _run(server_module.handle_query_ulif({
                "word": "великий", "sections": ["paradigm"],
            }))

        query.assert_called_once_with("великий", ["paradigm"])
        assert json.loads(result[0].text) == expected

    def test_search_text_subject_schema(self, server_module):
        tools = _run(server_module.list_tools())
        search_text = next(t for t in tools if t.name == "search_text")
        subject = search_text.input_schema["properties"]["subject"]
        assert subject["enum"] == list(server_module.CANONICAL_TEXTBOOK_SUBJECTS)
        assert "ukrmova" in subject["description"]
        assert "grade" not in search_text.input_schema["properties"]
        assert "trust_tier" not in search_text.input_schema["properties"]
        assert "BGE-M3" not in search_text.description

    def test_search_images_stub_schema(self, server_module):
        tools = _run(server_module.list_tools())
        search_images = next(t for t in tools if t.name == "search_images")
        assert "stub" in search_images.description.lower()
        assert "SigLIP" not in search_images.description
        assert "grade" not in search_images.input_schema["properties"]
        assert "subject" not in search_images.input_schema["properties"]
        assert search_images.input_schema["required"] == ["query"]

    def test_search_literary_schema(self, server_module):
        tools = _run(server_module.list_tools())
        search_literary = next(t for t in tools if t.name == "search_literary")
        assert "work" not in search_literary.input_schema["properties"]
        assert "genre" not in search_literary.input_schema["properties"]
        assert "period" not in search_literary.input_schema["properties"]
        assert search_literary.input_schema["required"] == ["query"]

    def test_get_chunk_context_schema(self, server_module):
        tools = _run(server_module.list_tools())
        chunk_context = next(t for t in tools if t.name == "get_chunk_context")
        assert "window" not in chunk_context.input_schema["properties"]
        assert chunk_context.input_schema["required"] == ["chunk_id"]

    def test_get_full_text_schema(self, server_module):
        tools = _run(server_module.list_tools())
        full_text = next(t for t in tools if t.name == "get_full_text")
        assert "RAG" not in full_text.description
        assert full_text.input_schema["required"] == ["work"]

    def test_collection_stats_schema(self, server_module):
        tools = _run(server_module.list_tools())
        stats = next(t for t in tools if t.name == "collection_stats")
        assert "RAG" not in stats.description

    def test_verify_words_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vw = next(t for t in tools if t.name == "verify_words")
        assert "words" in vw.input_schema["required"]
        props = vw.input_schema["properties"]["words"]
        assert props["type"] == "array"
        assert props["items"]["type"] == "string"

    def test_vet_vocabulary_schema(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(tool for tool in tools if tool.name == "vet_vocabulary")
        assert tool.input_schema["required"] == ["words"]
        assert tool.input_schema["properties"]["words"]["type"] == "array"
        assert tool.input_schema["properties"]["include_definitions"]["default"] is False

    def test_verify_quote_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vq = next(t for t in tools if t.name == "verify_quote")
        assert vq.input_schema["required"] == ["author", "text"]
        assert vq.input_schema["properties"]["min_confidence"]["default"] == 0.80

    def test_verify_source_attribution_schema(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(t for t in tools if t.name == "verify_source_attribution")
        assert tool.input_schema["required"] == ["source", "claim"]
        assert set(tool.input_schema["properties"]["source"]["enum"]) == {
            "grinchenko_1907",
            "esum",
            "sum11",
            "antonenko_davydovych",
            "literary",
            "heritage",
            "wikipedia",
            "style_guide",
        }

    def test_verify_stress_schema(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(t for t in tools if t.name == "verify_stress")
        assert tool.input_schema["required"] == ["word"]
        assert "pos" in tool.input_schema["properties"]
        assert "tags" in tool.input_schema["properties"]


class TestCallToolDispatch:
    """Test that call_tool routes to correct handlers."""

    def test_unknown_tool_returns_error(self, server_module):
        result = _run(server_module.call_tool("nonexistent_tool", {}))
        assert len(result) == 1
        assert "Unknown tool" in result[0].text

    def test_verify_word_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_word", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_word", {"word": "тест"}))
            mock.assert_called_once_with({"word": "тест"})

    def test_verify_source_attribution_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_source_attribution", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            args = {"source": "grinchenko_1907", "claim": "коза"}
            _run(server_module.call_tool("verify_source_attribution", args))
            mock.assert_called_once_with(args)

    def test_verify_words_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_words", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_words", {"words": ["тест"]}))
            mock.assert_called_once_with({"words": ["тест"]})

    def test_vet_vocabulary_dispatches(self, server_module):
        with patch.object(server_module, "handle_vet_vocabulary", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            args = {"words": ["тест"], "include_definitions": True}
            _run(server_module.call_tool("vet_vocabulary", args))
            mock.assert_called_once_with(args)

    def test_verify_quote_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_quote", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_quote", {"author": "Шевченко", "text": "Та в Сибір загнали"}))
            mock.assert_called_once_with({"author": "Шевченко", "text": "Та в Сибір загнали"})

    def test_search_sources_dispatches(self, server_module):
        with patch.object(server_module, "handle_search_sources", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("search_sources", {"query": "голосні звуки"}))
            mock.assert_called_once_with({"query": "голосні звуки"})

    def test_search_text_handler_passes_subject_filter(self, server_module):
        hit = {
            "chunk_id": "chunk-1",
            "title": "Родовий відмінок",
            "section_title": "Родовий відмінок",
            "grade": "5",
            "author": "Авраменко",
            "subject": "ukrmova",
            "text": "Родовий відмінок у шкільному підручнику.",
        }
        with patch("wiki.sources_db.search_textbooks", return_value=[hit]) as mock:
            result = _run(
                server_module.handle_search_text(
                    {"query": "родовий відмінок", "subject": "ukrmova", "limit": 3}
                )
            )

        assert "Subject**: ukrmova" in result[0].text
        mock.assert_called_once()
        args, kwargs = mock.call_args
        assert "родовий" in args[0]
        assert args[1] == 3
        assert kwargs["subject"] == "ukrmova"

    def test_search_grinchenko_1907_dispatches(self, server_module):
        with patch.object(server_module, "handle_dict_search", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("search_grinchenko_1907", {"query": "тест"}))
            mock.assert_called_once_with({"query": "тест"}, "grinchenko_dict", "Грінченко")

    def test_search_slovnyk_me_dispatches(self, server_module):
        with patch.object(server_module, "handle_search_slovnyk_me", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("search_slovnyk_me", {"query": "тест"}))
            mock.assert_called_once_with({"query": "тест"})

    def test_search_heritage_dispatches(self, server_module):
        with patch.object(server_module, "handle_search_heritage", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("search_heritage", {"query": "тест"}))
            mock.assert_called_once_with({"query": "тест"})

    def test_check_modern_form_dispatches(self, server_module):
        with patch.object(server_module, "handle_check_modern_form", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("check_modern_form", {"word": "звір"}))
            mock.assert_called_once_with({"word": "звір"})


    def test_verify_stress_dispatches(self, server_module):
        with patch.object(server_module, "handle_verify_stress", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text="ok")]
            _run(server_module.call_tool("verify_stress", {"word": "замок", "pos": "VERB"}))
            mock.assert_called_once_with({"word": "замок", "pos": "VERB"})

    def test_handler_exception_returns_error_text(self, server_module):
        with patch.object(server_module, "handle_verify_word", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("test error")
            result = _run(server_module.call_tool("verify_word", {"word": "тест"}))
            assert len(result) == 1
            assert "RuntimeError" in result[0].text
            assert "test error" in result[0].text

    def test_search_esum_placeholder_hint(self, server_module):
        with patch("wiki.sources_db.search_esum", return_value=[]):
            result = _run(server_module.handle_search_esum({"query": "тест"}))
            assert len(result) == 1
            assert '"status": "not_implemented"' in result[0].text
            assert "goroh.pp.ua/Етимологія/тест" in result[0].text

    def test_query_sum20_formats_offline_official_records(self, server_module):
        record = {
            "source_id": "sum20_official",
            "source_record_id": "5",
            "stressed_headword": "АБАЖУ́Р",
            "pos": "ч.",
            "grammar": "а, ч.",
            "attribution_label": (
                "Словник української мови у 20 томах (УМІФ НАН України; "
                "Інститут мовознавства ім. О. О. Потебні НАН України)"
            ),
            "official_url": "https://sum20ua.com/?wordid=5",
            "retrieved_at": "2026-07-15T10:00:00+00:00",
            "content_sha256": "abc123",
            "parser_version": "sum20_official_v1",
            "status": "ok",
            "senses": [{"sense_order": 1, "definition": "Частина світильника", "register_labels": []}],
            "citations": [
                {
                    "citation_text": "На столику стояла свічка під абажуром",
                    "parsed_bib_fields": {"author": "Леся Українка"},
                }
            ],
        }
        with patch("wiki.sources_db.query_sum20", return_value=[record]) as mock:
            result = _run(server_module.handle_query_sum20({"word": "абажур"}))

        mock.assert_called_once_with("абажур")
        text = result[0].text
        assert "https://sum20ua.com/?wordid=5" in text
        assert "Леся Українка" in text
        assert "slovnyk.me" not in text


class TestVerifyWordHandler:
    """Test verify_word handler formatting."""

    def test_not_found(self, server_module):
        with patch("scripts.verification.vesum.verify_word", return_value=[]):
            result = _run(server_module.handle_verify_word({"word": "взяйте"}))
            assert "NOT FOUND" in result[0].text

    def test_found(self, server_module):
        mock_matches = [{"lemma": "читати", "pos": "verb", "tags": "verb:imperf:impr:s:2"}]
        with patch("scripts.verification.vesum.verify_word", return_value=mock_matches):
            result = _run(server_module.handle_verify_word({"word": "читай"}))
            assert "читати" in result[0].text
            assert "verb" in result[0].text
            assert "1 match" in result[0].text

    def test_passes_pos_filter(self, server_module):
        with patch("scripts.verification.vesum.verify_word", return_value=[]) as mock:
            _run(server_module.handle_verify_word({"word": "тест", "pos_filter": "noun"}))
            mock.assert_called_once_with("тест", "noun")


class TestVerifyWordsHandler:
    """Test verify_words handler formatting."""

    def test_batch_results(self, server_module):
        mock_results = {
            "стій": [{"lemma": "стояти", "pos": "verb", "tags": "verb:imperf:impr:s:2"}],
            "взяйте": [],
        }
        with patch("scripts.verification.vesum.verify_words", return_value=mock_results):
            result = _run(server_module.handle_verify_words({"words": ["стій", "взяйте"]}))
            text = result[0].text
            assert "Found: 1/2" in text
            assert "**стій** — FOUND" in text
            assert "**взяйте** — NOT FOUND" in text


class TestVerifyStressHandler:
    """Test the verify_stress handler wires args through and emits JSON (#6515)."""

    def test_returns_json_envelope(self, server_module):
        payload = {
            "input": "замок",
            "lookup_key": "замок",
            "status": "ambiguous",
            "matches": [],
            "unresolvable_by_tags": True,
            "source": {"dictionary": "ukrainian-word-stress (ULIF-derived)"},
        }
        with patch("scripts.verification.stress.verify_stress", return_value=payload) as mock:
            result = _run(server_module.handle_verify_stress({"word": "замок"}))
            mock.assert_called_once_with("замок", None, None)
            assert json.loads(result[0].text) == payload

    def test_passes_pos_and_tags(self, server_module):
        with patch("scripts.verification.stress.verify_stress", return_value={}) as mock:
            _run(server_module.handle_verify_stress({"word": "замок", "pos": "VERB", "tags": "Number=Sing"}))
            mock.assert_called_once_with("замок", "VERB", "Number=Sing")


@pytest.fixture
def vocabulary_vet_fixtures():
    """One fixture payload for each source that composite vocabulary vetting uses."""
    return {
        "vesum": {
            "кіт": [{"lemma": "кіт", "pos": "noun", "tags": "noun:anim:m:v_naz"}],
            "вигадане": [],
        },
        "cefr": {"кіт": [{"level": "A1"}], "вигадане": []},
        "shadow": {
            "кіт": {
                "matches_russian": False,
                "russian_lemma": None,
                "confidence": 0.0,
            },
            "вигадане": {
                "matches_russian": True,
                "russian_lemma": "выдуманный",
                "confidence": 0.91,
            },
        },
        "definitions": {
            "кіт": [{"definition": "КІТ, кота, ч. Свійська тварина родини котячих."}],
            "вигадане": [],
        },
    }


class TestVetVocabularyHandler:
    def test_reports_all_sources_and_missing_word(self, server_module, vocabulary_vet_fixtures):
        fixtures = vocabulary_vet_fixtures
        with (
            patch("scripts.verification.vesum.verify_words", return_value=fixtures["vesum"]) as verify_words,
            patch("wiki.sources_db.query_cefr_levels", return_value=fixtures["cefr"]) as query_cefr,
            patch(
                "scripts.verification.check_ru_morph.check_russian_patterns_batch",
                return_value=fixtures["shadow"],
            ) as check_shadow,
            patch(
                "wiki.sources_db.search_definitions_batch",
                return_value=fixtures["definitions"],
            ) as search_definitions,
        ):
            result = _run(
                server_module.handle_vet_vocabulary(
                    {"words": ["кіт", "вигадане"], "include_definitions": True}
                )
            )

        text = result[0].text
        assert text.splitlines()[0] == (
            "- **кіт** | VESUM: valid (lemma=кіт, pos=noun, tags=noun:anim:m:v_naz) "
            "| CEFR: A1 | Russian-shadow: not flagged (suspicion only, not a verdict) "
            "| Gloss: КІТ, кота, ч. Свійська тварина родини котячих."
        )
        assert "**вигадане** | VESUM: not found" in text
        assert "Russian-shadow: suspected (suspicion only, not a verdict; russian_lemma=выдуманный" in text
        assert "Gloss: КІТ, кота, ч. Свійська тварина родини котячих." in text
        assert "Gloss: not found" in text
        verify_words.assert_called_once_with(["кіт", "вигадане"])
        query_cefr.assert_called_once_with(["кіт", "вигадане"])
        search_definitions.assert_called_once_with(["кіт", "вигадане"])
        check_shadow.assert_called_once_with(
            ["кіт", "вигадане"], verified_words={"кіт"}
        )

    def test_omits_gloss_without_definitions_toggle(self, server_module, vocabulary_vet_fixtures):
        fixtures = vocabulary_vet_fixtures
        with (
            patch("scripts.verification.vesum.verify_words", return_value=fixtures["vesum"]),
            patch("wiki.sources_db.query_cefr_levels", return_value=fixtures["cefr"]),
            patch(
                "scripts.verification.check_ru_morph.check_russian_patterns_batch",
                return_value=fixtures["shadow"],
            ),
            patch("wiki.sources_db.search_definitions_batch") as search_definitions,
        ):
            result = _run(server_module.handle_vet_vocabulary({"words": ["кіт"]}))

        assert "Gloss:" not in result[0].text
        assert "Russian-shadow: not flagged (suspicion only, not a verdict)" in result[0].text
        search_definitions.assert_not_called()

    def test_honestly_truncates_after_500_words(self, server_module):
        words = [f"слово-{index}" for index in range(501)]
        first_500 = words[:500]
        with (
            patch("scripts.verification.vesum.verify_words", return_value={word: [] for word in first_500}) as verify_words,
            patch("wiki.sources_db.query_cefr_levels", return_value={}),
            patch(
                "scripts.verification.check_ru_morph.check_russian_patterns_batch",
                return_value={word: {"matches_russian": False} for word in first_500},
            ),
        ):
            result = _run(server_module.handle_vet_vocabulary({"words": words}))

        text = result[0].text
        assert text.startswith("Note: received 501 words; processed the first 500 (hard cap).")
        assert "**слово-499**" in text
        assert "**слово-500**" not in text
        verify_words.assert_called_once_with(first_500)


def _shevchenko_quote_hits():
    # Known-good source confirmed with mcp__sources__search_literary:
    # query="загнали в Сибір", chunk_id=d1b5c8a6_c0084, author="Шевченко Т."
    return [
        {
            "chunk_id": "d1b5c8a6_c0084",
            "title": "",
            "author": "Шевченко Т.",
            "year": 1814,
            "source_file": "ukrlib-shevchenko",
            "text": (
                "Що розлили з річку крові\n\n"
                "Та в Сибір загнали\n\n"
                "Свою шляхту, то вже й годі,\n\n"
                "Уже й запишались."
            ),
        },
        {
            "chunk_id": "9976239a_c0473",
            "title": "",
            "author": "Шевченко Т.",
            "year": 1961,
            "source_file": "wave10-shevchenko-tvory-t1",
            "text": "Сибір неісходима,\n\nА тюрм, а люду! що й казать!",
        },
        {
            "chunk_id": "other_shevchenko",
            "title": "Садок вишневий коло хати",
            "author": "Т. Г. Шевченко",
            "year": 1847,
            "source_file": "fixture",
            "text": "Садок вишневий коло хати,\n\nХрущі над вишнями гудуть.",
        },
    ]


class TestVerifyQuoteHandler:
    """Test verify_quote fuzzy attribution checks."""

    def test_known_good_shevchenko_line_matches(self, server_module):
        with patch("wiki.sources_db.search_literary", return_value=_shevchenko_quote_hits()):
            result = _run(
                server_module.handle_verify_quote(
                    {"author": "Шевченко", "text": "Та в Сибір загнали Свою шляхту"}
                )
            )
        data = json.loads(result[0].text)
        assert data["matched"] is True
        assert data["best_confidence"] >= 0.90
        assert data["matched_lines"][0]["context_chunk_id"] == "d1b5c8a6_c0084"

    def test_fabricated_fused_quote_returns_near_misses(self, server_module):
        with patch("wiki.sources_db.search_literary", return_value=_shevchenko_quote_hits()):
            result = _run(
                server_module.handle_verify_quote(
                    {"author": "Шевченко", "text": "Загнали в Сибір неісходиму"}
                )
            )
        data = json.loads(result[0].text)
        assert data["matched"] is False
        assert len(data["matched_lines"]) == 3
        assert data["matched_lines"][0]["confidence"] < 0.80

    def test_author_variants_find_same_line(self, server_module):
        matched_ids = []
        for author in ["Шевченко", "Т. Г. Шевченко", "Тарас Шевченко"]:
            with patch("wiki.sources_db.search_literary", return_value=_shevchenko_quote_hits()):
                result = _run(
                    server_module.handle_verify_quote(
                        {"author": author, "text": "Та в Сибір загнали Свою шляхту"}
                    )
                )
            data = json.loads(result[0].text)
            assert data["matched"] is True
            matched_ids.append(data["matched_lines"][0]["context_chunk_id"])
        assert matched_ids == ["d1b5c8a6_c0084"] * 3

    def test_empty_text_returns_clean_error(self, server_module):
        result = _run(server_module.call_tool("verify_quote", {"author": "Шевченко", "text": ""}))
        assert "ValueError: text is required" in result[0].text
        assert "Traceback" not in result[0].text


class TestVerifySourceAttributionHandler:
    """Test verify_source_attribution handler routing and verdicts."""

    def test_grinchenko_1907_discusses_koza(self, server_module):
        with patch(
            "wiki.sources_db.search_grinchenko_1907",
            return_value=[{"headword": "коза", "definition": "коза — свійська тварина"}],
        ) as mock:
            result = _run(
                server_module.handle_verify_source_attribution(
                    {"source": "grinchenko_1907", "claim": "коза"}
                )
            )

        mock.assert_called_once_with("коза", 5)
        data = json.loads(result[0].text)
        assert data["discusses"] is True
        assert data["evidence_count"] >= 1

    def test_antonenko_fake_claim_returns_completeness_note(self, server_module):
        with patch("wiki.sources_db.search_style_guide", return_value=[]) as mock:
            result = _run(
                server_module.handle_verify_source_attribution(
                    {"source": "antonenko_davydovych", "claim": "thisisdefinitelyfake999"}
                )
            )

        mock.assert_called_once_with("thisisdefinitelyfake999", 5)
        data = json.loads(result[0].text)
        assert data["discusses"] is False
        assert "completeness_note" in data

    def test_sum11_leninizm_discusses_with_sovietization_note(self, server_module):
        with patch(
            "wiki.sources_db.search_definitions",
            return_value=[{"headword": "ленінізм", "definition": "ленінізм — політичне вчення"}],
        ) as mock:
            result = _run(
                server_module.handle_verify_source_attribution(
                    {"source": "sum11", "claim": "ленінізм"}
                )
            )

        mock.assert_called_once_with("ленінізм", 5)
        data = json.loads(result[0].text)
        assert data["discusses"] is True
        assert "sovietization_risk" in data["completeness_note"]

    def test_invalid_source_returns_clean_error(self, server_module):
        result = _run(
            server_module.call_tool(
                "verify_source_attribution",
                {"source": "not_a_source", "claim": "коза"},
            )
        )

        assert len(result) == 1
        assert "Invalid source" in result[0].text
        assert "Traceback" not in result[0].text

    def test_empty_claim_returns_clean_error(self, server_module):
        result = _run(
            server_module.call_tool(
                "verify_source_attribution",
                {"source": "grinchenko_1907", "claim": " "},
            )
        )

        assert len(result) == 1
        assert "claim must be a non-empty string" in result[0].text
        assert "Traceback" not in result[0].text

    def test_wikipedia_route_uses_query_wikipedia_handler(self, server_module):
        text = "Wikipedia search: 'тест' — 1 results\n\n1. **Тест** — тестова сторінка"
        with patch.object(server_module, "handle_query_wikipedia", new_callable=AsyncMock) as mock:
            mock.return_value = [MagicMock(text=text)]
            result = _run(
                server_module.handle_verify_source_attribution(
                    {"source": "wikipedia", "claim": "тест", "limit": 2}
                )
            )

        mock.assert_called_once_with({"query": "тест", "mode": "search", "limit": 2})
        assert json.loads(result[0].text)["discusses"] is True

    def test_wikipedia_route_failure_returns_completeness_note(self, server_module):
        with patch.object(server_module, "handle_query_wikipedia", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("network down")
            result = _run(
                server_module.handle_verify_source_attribution(
                    {"source": "wikipedia", "claim": "тест", "limit": 2}
                )
            )

        data = json.loads(result[0].text)
        assert data["discusses"] is False
        assert data["evidence_count"] == 0
        assert data["completeness_note"] == "Wikipedia query failed: network down"


class TestSearchSourcesHandler:
    """Test search_sources handler formatting."""

    def test_empty_results(self, server_module):
        with patch("wiki.sources_db.search_sources", return_value=[]):
            result = _run(server_module.handle_search_sources({"query": "голосні звуки"}))
            assert result[0].text == "[]"

    def test_defaults_track_to_empty_string(self, server_module):
        with patch("wiki.sources_db.search_sources", return_value=[]) as mock:
            _run(server_module.handle_search_sources({"query": "голосні звуки"}))
            mock.assert_called_once_with("голосні звуки", track="", limit=10)

    def test_returns_json_payload(self, server_module):
        mock_hits = [
            {
                "chunk_id": "ukwiki:test-1",
                "corpus": "ukrainian_wiki",
                "title": "Голосні звуки",
                "text": "Голосні звуки творяться без перешкод.",
                "final_score": 0.91,
            }
        ]
        with patch("wiki.sources_db.search_sources", return_value=mock_hits) as mock:
            result = _run(
                server_module.handle_search_sources(
                    {"query": "голосні звуки", "track": "a1", "limit": 5}
                )
            )
            mock.assert_called_once_with("голосні звуки", track="a1", limit=5)
            assert '"corpus": "ukrainian_wiki"' in result[0].text
            assert '"chunk_id": "ukwiki:test-1"' in result[0].text


class TestCheckRussianShadowHandler:
    def test_handle_check_russian_shadow(self, server_module):
        with patch("scripts.verification.vesum.verify_word") as mock_verify_word:
            def mock_vesum(w):
                if w in ["получити", "здача"]:
                    return []
                return [{"lemma": w, "pos": "noun", "tags": ""}]
            mock_verify_word.side_effect = mock_vesum

            args = {"word": "получити", "threshold": 0.7}
            res = _run(server_module.handle_check_russian_shadow(args))

            assert len(res) == 1
            data = json.loads(res[0].text)
            assert data["matches_russian"] is True

            args = {"word": "привіт", "threshold": 0.7}
            res = _run(server_module.handle_check_russian_shadow(args))

            data = json.loads(res[0].text)
            assert data["matches_russian"] is False


_VESUM_DB = Path(__file__).resolve().parents[1] / "data" / "vesum.db"


@pytest.mark.skipif(
    not _VESUM_DB.exists(),
    reason="VESUM DB not present in CI sandbox — run locally for smoke coverage",
)
class TestIntegrationSmoke:
    """Smoke tests using real database (no mocks). Skipped when data/vesum.db absent."""

    def test_smoke_verify_word_archaic(self, server_module):
        """Test verify_word with a word that has an archaic tag."""
        result = _run(server_module.handle_verify_word({"word": "звір"}))
        assert "**is_archaic**: True" in result[0].text
        assert "**is_archaic**: False" in result[0].text  # Because it has modern forms too

    def test_smoke_verify_lemma_archaic(self, server_module):
        """Test verify_lemma with a lemma that has archaic forms."""
        result = _run(server_module.handle_verify_lemma({"lemma": "звір"}))
        assert "has_archaic_forms: True" in result[0].text
        assert "**is_archaic**: True" in result[0].text

    def test_smoke_check_modern_form_mixed(self, server_module):
        """Test check_modern_form with a word that has both modern and archaic tags."""
        result = _run(server_module.handle_check_modern_form({"word": "звір"}))
        data = json.loads(result[0].text)
        assert data["is_modern_codified"] is True
        assert data["has_archaic_form"] is True
        assert data["has_only_archaic_form"] is False

    def test_smoke_check_modern_form_modern_only(self, server_module):
        """Test check_modern_form with a modern-only word."""
        result = _run(server_module.handle_check_modern_form({"word": "Сибір"}))
        data = json.loads(result[0].text)
        assert data["is_modern_codified"] is True
        assert data["has_archaic_form"] is False
        assert data["has_only_archaic_form"] is False

    def test_smoke_check_modern_form_archaic_only(self, server_module):
        """Test check_modern_form with an archaic-only word."""
        result = _run(server_module.handle_check_modern_form({"word": "аби-де"}))
        data = json.loads(result[0].text)
        assert data["is_modern_codified"] is False
        assert data["has_archaic_form"] is True
        assert data["has_only_archaic_form"] is True


class TestDictSearchQuoteBalance:
    """Test _quote_balanced_clip and handle_dict_search quote balancing (#7026)."""

    def test_clip_short_text_unchanged(self, server_module):
        short = "Короткий текст"
        assert server_module._quote_balanced_clip(short, 500) == short

    def test_clip_without_quotes_adds_ellipsis(self, server_module):
        long_text = "а" * 600
        clipped = server_module._quote_balanced_clip(long_text, 500)
        assert len(clipped) == 501  # 500 + '…'
        assert clipped.endswith("…")

    def test_clip_preserves_guillemets_lookahead(self, server_module):
        # Open quote inside first 500 chars, closing quote within lookahead (at 520)
        base = "Початок " + "а" * 470 + " «цитата на двадцять слів» продовження"
        clipped = server_module._quote_balanced_clip(base, 500)
        assert "«цитата на двадцять слів»" in clipped
        assert clipped.count("«") == clipped.count("»")

    def test_clip_trims_before_unclosed_quote_when_closing_too_far(self, server_module):
        # Open quote at char 480, but closing quote is 300 chars away
        base = "Початок " + "а" * 470 + " «дуже довга цитата " + "б" * 300 + "»"
        clipped = server_module._quote_balanced_clip(base, 500)
        assert "«" not in clipped
        assert clipped.count("«") == clipped.count("»")

    def test_handle_dict_search_clips_long_definitions(self, server_module):
        hit = {
            "word": "тест",
            "definition": "Початок " + "а" * 600,
        }
        with patch("wiki.sources_db.search_definitions", return_value=[hit]):
            result = _run(server_module.handle_dict_search({"query": "тест"}, "sum11", "СУМ-11"))
            text = result[0].text
            assert "Found 1 results" in text
            assert "…" in text
            assert len(text) < 700


class TestHealthEndpoint:
    """Test health endpoint contract (#7026)."""

    def test_handle_health_response(self, server_module):
        app = server_module.create_http_app()
        routes = [r for r in app.routes if getattr(r, "path", None) == "/health"]
        assert len(routes) == 1
        health_endpoint = routes[0].endpoint

        response = _run(health_endpoint(None))
        data = json.loads(response.body.decode("utf-8"))
        assert data["status"] == "ok"
        assert "commit_sha" in data
        assert "db_path" in data
        assert "sources.db" in data["db_path"]


class TestCollectionStatsHandler:
    """Test collection_stats handler (#7026)."""

    def test_handle_collection_stats_dispatches(self, server_module):
        mock_stats = {
            "textbooks": 10,
            "esum_etymology": 20,
            "ua_gec_errors": 30,
            "sum20_articles": 40,
            "slovnyk_me_entries": 50,
            "wikipedia": 60,
        }
        with patch("wiki.sources_db.list_tables", return_value=mock_stats):
            result = _run(server_module.handle_collection_stats({}))
            data = json.loads(result[0].text)
            assert data["esum_etymology"] == 20
            assert data["ua_gec_errors"] == 30
            assert data["sum20_articles"] == 40
            assert data["slovnyk_me_entries"] == 50
            assert data["wikipedia"] == 60
