"""Coverage tests for miscellaneous scripts.

Targets:
  1. scripts/pipeline/screen.py
  2. scripts/ai_agent_bridge/_gemini.py
  3. scripts/vocab_extract_proper.py
  4. scripts/generate_ipa.py
  5. scripts/migrate_audit_review_paths.py
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "pipeline"))


# ============================================================================
# 1. pipeline/screen.py
# ============================================================================


# ============================================================================
# 2. ai_agent_bridge/_gemini.py
# ============================================================================


class TestHandleGeminiError:
    """Test _handle_gemini_error."""

    def _import(self):
        from scripts.ai_agent_bridge._gemini import _handle_gemini_error

        return _handle_gemini_error

    @patch("time.sleep")
    def test_rate_limit_returns_retry(self, mock_sleep):
        f = self._import()
        with patch("scripts.ai_agent_bridge._gemini._detect_model_error", return_value=None):
            result = f("exhausted your capacity", "test-model", 0, 5, 30)
            assert result == "retry"

    def test_rate_limit_last_attempt_returns_stop(self):
        f = self._import()
        with patch("scripts.ai_agent_bridge._gemini._detect_model_error", return_value=None):
            result = f("429 error", "test-model", 4, 5, 30)
            assert result == "stop"

    def test_unknown_error_returns_continue(self):
        f = self._import()
        with patch("scripts.ai_agent_bridge._gemini._detect_model_error", return_value=None):
            result = f("some random error", "test-model", 0, 5, 30)
            assert result == "continue"


class TestSendGeminiError:
    """Test _send_gemini_error."""

    def _import(self):
        from scripts.ai_agent_bridge._gemini import _send_gemini_error

        return _send_gemini_error

    def test_sends_error_message(self):
        f = self._import()
        msg = {"task_id": "test-task"}
        with (
            patch("scripts.ai_agent_bridge._gemini.send_message", return_value=99) as sm,
            patch("scripts.ai_agent_bridge._gemini.acknowledge") as ack,
            patch("scripts.ai_agent_bridge._gemini.record_ask_failure"),
        ):
            f(msg, 42)
            sm.assert_called_once()
            # #6915: a failed processing must NOT consume the inbound message.
            ack.assert_not_called()

    def test_exception_suppressed(self):
        f = self._import()
        msg = {"task_id": "test-task"}
        with patch("scripts.ai_agent_bridge._gemini.send_message", side_effect=Exception("boom")):
            f(msg, 42)  # Should not raise


class TestSendGeminiMessage:
    """Test _send_gemini_message."""

    def _import(self):
        from scripts.ai_agent_bridge._gemini import _send_gemini_message

        return _send_gemini_message

    def test_output_path_mode(self):
        f = self._import()
        with (
            patch("scripts.ai_agent_bridge._gemini.send_to_gemini", return_value=10) as st,
            patch("scripts.ai_agent_bridge._gemini.acknowledge") as ack,
        ):
            result = f("content", "task-1", "query", None, None, None, "model", False, "/out")
            assert result == 10
            ack.assert_called_once()

    def test_normal_mode(self):
        f = self._import()
        with (
            patch("scripts.ai_agent_bridge._gemini.send_to_gemini", return_value=12),
            patch("scripts.ai_agent_bridge._gemini.acknowledge") as ack,
        ):
            result = f("content", "task-1", "query", None, None, None, "model", False, None)
            assert result == 12
            ack.assert_not_called()


class TestDetectModelError:
    """Test _detect_model_error from _model.py."""

    def _import(self):
        from scripts.ai_agent_bridge._model import _detect_model_error

        return _detect_model_error

    def test_not_found(self):
        f = self._import()
        result = f("model not found error", "test-model")
        assert result is not None
        assert "not available" in result

    def test_no_model_error(self):
        f = self._import()
        result = f("some other error", "test-model")
        assert result is None


# ============================================================================
# 4. vocab_extract_proper.py
# ============================================================================


class TestStressedToIpa:
    def _import(self):
        from vocab.vocab_extract_proper import stressed_to_ipa

        return stressed_to_ipa

    def test_stressed_word(self):
        f = self._import()
        result = f("мі\u0301сто")
        assert "ˈ" in result  # Stress mark in IPA


class TestGetKnownLemmas:
    def _import(self):
        from vocab.vocab_extract_proper import get_known_lemmas

        return get_known_lemmas

    def test_existing_db(self, tmp_path):
        f = self._import()
        import sqlite3

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE lemmas (uk TEXT)")
        conn.execute("INSERT INTO lemmas VALUES ('слово')")
        conn.execute("INSERT INTO lemmas VALUES ('текст')")
        conn.commit()
        conn.close()
        result = f(db_path)
        assert result == {"слово", "текст"}

    def test_corrupted_db(self, tmp_path):
        f = self._import()
        db_path = tmp_path / "bad.db"
        db_path.write_text("not a database")
        result = f(db_path)
        assert result == set()


class TestCreateVocabularyEntries:
    def _import(self):
        from vocab.vocab_extract_proper import create_vocabulary_entries

        return create_vocabulary_entries

    def test_stressifier_error(self):
        f = self._import()
        mock_stressifier = MagicMock(side_effect=Exception("stress error"))
        with patch("vocab.vocab_extract_proper.get_stressifier", return_value=mock_stressifier):
            entries = f({"слово": {"pos": "noun", "gender": "n", "count": 1}})
        assert len(entries) == 1
        assert entries[0]["ipa"] == ""
        # Can't easily check level from stats, but it shouldn't crash


# ============================================================================
# 5. generate_ipa.py
# ============================================================================


class TestPostprocess:
    def _import(self):
        from generate_ipa import _postprocess

        return _postprocess

    def test_rule1_a_to_open_back(self):
        f = self._import()
        assert f("ɐ") == "ɑ"

    def test_rule2_nonsyllabic_i_to_j(self):
        f = self._import()
        assert f("i\u032f") == "j"

    def test_rule3_lax_u(self):
        f = self._import()
        assert f("ʊ") == "u"

    def test_rule3b_o_to_open_mid(self):
        f = self._import()
        assert f("o") == "ɔ"

    def test_rule3c_e_to_open_mid(self):
        f = self._import()
        assert f("e") == "ɛ"

    def test_rule4_w_to_labiodental(self):
        f = self._import()
        assert f("w") == "ʋ"

    def test_rule5_u_nonsyl_palatalized(self):
        f = self._import()
        assert f("u\u032fʲ") == "ʋʲ"

    def test_rule6_u_nonsyl_before_stress(self):
        f = self._import()
        assert f("u\u032fˈ") == "ˈʋ"

    def test_rule7_u_nonsyl_before_secondary_stress(self):
        f = self._import()
        assert f("u\u032fˌ") == "ˌʋ"

    def test_rule8_u_nonsyl_before_vowel(self):
        f = self._import()
        assert f("u\u032fa") == "ʋa"


class TestGenerateIpa:
    def _import(self):
        from generate_ipa import generate_ipa

        return generate_ipa

    def test_stress_override(self):
        f = self._import()
        match = {"stressed_form": "те́ст", "source": "override"}
        mock_ipa_uk = MagicMock()
        mock_ipa_uk.ipa.return_value = "tɛst"
        with (
            patch("generate_ipa._get_ipa_overrides", return_value={}),
            patch(
                "scripts.verification.stress.verify_stress", return_value={"status": "ok", "matches": [match]}
            ) as oracle,
            patch("scripts.verification.stress.spoken_stressed_form", return_value="те́ст") as spoken,
            patch.dict("sys.modules", {"ipa_uk": mock_ipa_uk}),
        ):
            assert f("тест") == "[tɛst]"
        oracle.assert_called_once_with("тест")
        spoken.assert_called_once_with(match)
        mock_ipa_uk.ipa.assert_called_once_with("те́ст")

    def test_stress_oracle_failure(self):
        f = self._import()
        with (
            patch("generate_ipa._get_ipa_overrides", return_value={}),
            patch("scripts.verification.stress.verify_stress", side_effect=RuntimeError("source failure")),
        ):
            assert f("тест") is None

    @pytest.mark.parametrize("status", ["pending", "ambiguous", "not_found"])
    def test_unresolved_stress_withholds_ipa(self, status):
        f = self._import()
        with (
            patch("generate_ipa._get_ipa_overrides", return_value={}),
            patch("scripts.verification.stress.verify_stress", return_value={"status": status, "matches": []}),
            patch.dict("sys.modules", {"ipa_uk": MagicMock()}) as modules,
        ):
            assert f("тест") is None
            modules["ipa_uk"].ipa.assert_not_called()

    @pytest.mark.parametrize("raw", ["", "   "])
    def test_ipa_uk_empty_result(self, raw):
        self._assert_ipa_result(raw=raw)

    def test_ipa_uk_failure(self):
        self._assert_ipa_result(error=RuntimeError("IPA failure"))

    def _assert_ipa_result(self, *, raw=None, error=None):
        f = self._import()
        mock_ipa_uk = MagicMock()
        mock_ipa_uk.ipa.return_value = raw
        mock_ipa_uk.ipa.side_effect = error
        with (
            patch("generate_ipa._get_ipa_overrides", return_value={}),
            patch("scripts.verification.stress.verify_stress", return_value={"status": "ok", "matches": [{}]}),
            patch("scripts.verification.stress.spoken_stressed_form", return_value="те́ст"),
            patch.dict("sys.modules", {"ipa_uk": mock_ipa_uk}),
        ):
            assert f("тест") is None
        mock_ipa_uk.ipa.assert_called_once_with("те́ст")

    def test_single_letter(self):
        f = self._import()
        mock_ipa_uk = MagicMock()
        mock_ipa_uk.ipa.return_value = "ɑ"
        with (
            patch("generate_ipa._get_ipa_overrides", return_value={}),
            patch("scripts.verification.stress.verify_stress", return_value={"status": "invalid_input", "matches": []}),
            patch.dict("sys.modules", {"ipa_uk": mock_ipa_uk}),
        ):
            assert f("а") == "[ɑ]"
        mock_ipa_uk.ipa.assert_called_once_with("а")


class TestLoadOverrides:
    def _import(self):
        from generate_ipa import _load_overrides

        return _load_overrides

    def test_file_with_dict(self, tmp_path):
        f = self._import()
        import yaml

        data = {"word": "value"}
        (tmp_path / "test.yaml").write_text(yaml.dump(data))
        with patch("generate_ipa.DATA_DIR", tmp_path):
            result = f("test.yaml")
        assert result == {"word": "value"}

    def test_file_with_non_dict(self, tmp_path):
        f = self._import()
        (tmp_path / "test.yaml").write_text("- item1\n- item2\n")
        with patch("generate_ipa.DATA_DIR", tmp_path):
            with pytest.raises(ValueError, match="Expected a YAML mapping"):
                f("test.yaml")


class TestStressifyWord:
    def _import(self):
        from generate_ipa import _stressify_word

        return _stressify_word

    def test_stressifier_error(self):
        f = self._import()
        mock_stress = MagicMock(side_effect=Exception("fail"))
        with patch("scripts.pipeline.stress_annotator._oracle_choice", side_effect=mock_stress):
            assert f("сло́во") == "слово"


class TestCheckEntryLine:
    def _import(self):
        from generate_ipa import _check_entry_line

        return _check_entry_line

    def test_lemma_first_line(self):
        f = self._import()
        entry = {"lemma": None, "ipa_line": None, "ipa_old": None}
        f("- lemma: слово", entry, 0, is_first=True)
        assert entry["lemma"] == "слово"

    def test_ipa_continuation_line(self):
        f = self._import()
        entry = {"lemma": None, "ipa_line": None, "ipa_old": None}
        f("  ipa: '[tɛst]'", entry, 5, is_first=False)
        assert entry["ipa_line"] == 5
        assert entry["ipa_old"] == "[tɛst]"


class TestRegenerateVocabIpa:
    def _import(self):
        from generate_ipa import regenerate_vocab_ipa

        return regenerate_vocab_ipa

    def test_ipa_updated(self, tmp_path):
        f = self._import()
        yaml_file = tmp_path / "vocab.yaml"
        yaml_file.write_text("- lemma: слово\n  ipa: '[old]'\n")
        with patch("generate_ipa.generate_ipa", return_value="[new]"):
            result = f(yaml_file)
        assert result == 1
        content = yaml_file.read_text()
        assert "[new]" in content

    def test_ipa_inserted(self, tmp_path):
        f = self._import()
        yaml_file = tmp_path / "vocab.yaml"
        yaml_file.write_text("- lemma: слово\n  pos: noun\n")
        with patch("generate_ipa.generate_ipa", return_value="[tɛst]"):
            result = f(yaml_file)
        assert result == 1
        content = yaml_file.read_text()
        assert "[tɛst]" in content

    def test_same_ipa_no_change(self, tmp_path):
        f = self._import()
        yaml_file = tmp_path / "vocab.yaml"
        yaml_file.write_text("- lemma: слово\n  ipa: '[same]'\n")
        with patch("generate_ipa.generate_ipa", return_value="[same]"):
            result = f(yaml_file)
        assert result == 0


class TestReplaceProseIpa:
    def _import(self):
        from generate_ipa import replace_prose_ipa

        return replace_prose_ipa

    def test_bold_ipa_replaced(self, tmp_path):
        f = self._import()
        md = tmp_path / "test.md"
        md.write_text("**місто** [ˈmʲistɔ]\n")
        mock_stress = MagicMock(return_value="мі\u0301сто")
        with patch("scripts.pipeline.stress_annotator._oracle_choice", side_effect=mock_stress):
            result = f(md)
        assert result == 1
        content = md.read_text()
        assert content == "**мі́сто**\n"


# ============================================================================
# 5. migrate_audit_review_paths.py
# ============================================================================


class TestMoveReviews:
    def _import(self):
        from migrate.migrate_audit_review_paths import move_reviews

        return move_reviews

    def test_apply_actually_moves(self, tmp_path):
        f = self._import()
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        review_file = audit_dir / "my-module-review.md"
        review_file.write_text("content")

        actions = f(tmp_path, dry_run=False)
        assert len(actions) == 1
        assert not review_file.exists()
        assert (tmp_path / "review" / "my-module-review.md").exists()


class TestRenameAuditReports:
    def _import(self):
        from migrate.migrate_audit_review_paths import rename_audit_reports

        return rename_audit_reports

    def test_apply_renames(self, tmp_path):
        f = self._import()
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        report = audit_dir / "01-my-module-audit-report.md"
        report.write_text("content")

        actions = f(tmp_path, dry_run=False)
        assert not report.exists()
        assert (audit_dir / "my-module-audit.md").exists()


class TestRenameStatusFiles:
    def _import(self):
        from migrate.migrate_audit_review_paths import rename_status_files

        return rename_status_files

    def test_apply_updates_module_field(self, tmp_path):
        f = self._import()
        status_dir = tmp_path / "status"
        status_dir.mkdir()
        (status_dir / "01-my-module.json").write_text('{"module": "01-my-module"}')

        f(tmp_path, dry_run=False)
        dest = status_dir / "my-module.json"
        assert dest.exists()
        data = json.loads(dest.read_text())
        assert data["module"] == "my-module"


class TestUpdateStatusModuleField:
    def _import(self):
        from migrate.migrate_audit_review_paths import _update_status_module_field

        return _update_status_module_field

    def test_updates_field(self, tmp_path):
        f = self._import()
        path = tmp_path / "status.json"
        path.write_text('{"module": "old-name", "score": 5}')
        f(path, "new-name")
        data = json.loads(path.read_text())
        assert data["module"] == "new-name"
        assert data["score"] == 5
        # No write should happen (module already matches)


# ============================================================================
# Additional edge case tests to boost coverage
# ============================================================================
