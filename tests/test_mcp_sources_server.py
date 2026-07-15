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
import inspect
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the server directory to path so we can import it
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources"))


@pytest.fixture
def server_module():
    """Import the server module fresh."""
    if "server" in sys.modules:
        del sys.modules["server"]
    import server as srv
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
            "verify_word", "verify_source_attribution", "verify_words", "verify_lemma", "verify_quote", "check_modern_form",
            "query_wikipedia", "query_grac", "query_ulif",
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
            assert tool.inputSchema is not None, f"{tool.name} missing inputSchema"
            assert tool.inputSchema.get("type") == "object", f"{tool.name} schema not object type"

    def test_verify_word_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vw = next(t for t in tools if t.name == "verify_word")
        assert "word" in vw.inputSchema["required"]
        assert "word" in vw.inputSchema["properties"]

    def test_search_text_subject_schema(self, server_module):
        tools = _run(server_module.list_tools())
        search_text = next(t for t in tools if t.name == "search_text")
        subject = search_text.inputSchema["properties"]["subject"]
        assert subject["enum"] == list(server_module.CANONICAL_TEXTBOOK_SUBJECTS)
        assert "ukrmova" in subject["description"]

    def test_search_images_subject_schema(self, server_module):
        tools = _run(server_module.list_tools())
        search_images = next(t for t in tools if t.name == "search_images")
        subject = search_images.inputSchema["properties"]["subject"]
        assert subject["enum"] == list(server_module.CANONICAL_TEXTBOOK_SUBJECTS)
        assert "ukrmova" in subject["description"]

    def test_verify_words_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vw = next(t for t in tools if t.name == "verify_words")
        assert "words" in vw.inputSchema["required"]
        props = vw.inputSchema["properties"]["words"]
        assert props["type"] == "array"
        assert props["items"]["type"] == "string"

    def test_verify_quote_schema(self, server_module):
        tools = _run(server_module.list_tools())
        vq = next(t for t in tools if t.name == "verify_quote")
        assert vq.inputSchema["required"] == ["author", "text"]
        assert vq.inputSchema["properties"]["min_confidence"]["default"] == 0.80

    def test_verify_source_attribution_schema(self, server_module):
        tools = _run(server_module.list_tools())
        tool = next(t for t in tools if t.name == "verify_source_attribution")
        assert tool.inputSchema["required"] == ["source", "claim"]
        assert set(tool.inputSchema["properties"]["source"]["enum"]) == {
            "grinchenko_1907",
            "esum",
            "sum11",
            "antonenko_davydovych",
            "literary",
            "heritage",
            "wikipedia",
            "style_guide",
        }


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


class TestSSEStateless:
    """Test that SSE mode uses stateless=True to avoid initialization handshake issues."""

    def test_main_sse_passes_stateless(self, server_module):
        """Verify the SSE handler calls server.run with stateless=True.

        This is critical: without stateless=True, Claude Code's SSE client
        fails with 'Received request before initialization was complete'
        because it doesn't send the MCP initialize handshake.
        """
        source = inspect.getsource(server_module.main_sse)
        assert "stateless=True" in source, (
            "main_sse must pass stateless=True to server.run() — "
            "without it, SSE clients that skip the initialize handshake "
            "get -32602 errors on every tool call"
        )

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
