"""Tests for scripts/build/dispatch.py — unified V6 dispatch + logging."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.dispatch import (
    CLAUDE_REVIEWER_TOOLS,
    CLAUDE_WRITER_TOOLS,
    _save_dispatch_log,
    dispatch_agent,
)

# ---------------------------------------------------------------------------
# Tool constants
# ---------------------------------------------------------------------------

class TestToolConstants:
    """Verify the tool allow-lists are sane."""

    def test_writer_tools_has_all_core(self):
        for tool in ("verify_word", "verify_words", "verify_lemma",
                      "search_text", "query_pravopys"):
            assert f"mcp__rag__{tool}" in CLAUDE_WRITER_TOOLS

    def test_writer_tools_has_new_dictionary_tools(self):
        for tool in ("search_style_guide", "query_cefr_level",
                      "search_definitions", "search_etymology",
                      "search_idioms", "search_synonyms", "translate_en_uk",
                      "query_grac", "query_ulif", "query_r2u"):
            assert f"mcp__rag__{tool}" in CLAUDE_WRITER_TOOLS

    def test_reviewer_tools_has_verification_core(self):
        for tool in ("verify_words", "verify_lemma", "search_style_guide",
                      "query_r2u", "query_pravopys"):
            assert f"mcp__rag__{tool}" in CLAUDE_REVIEWER_TOOLS

    def test_reviewer_tools_has_quality_tools(self):
        for tool in ("query_cefr_level", "search_definitions",
                      "search_etymology", "search_idioms",
                      "search_synonyms", "query_grac"):
            assert f"mcp__rag__{tool}" in CLAUDE_REVIEWER_TOOLS

    def test_reviewer_tools_has_reference_tools(self):
        for tool in ("search_text", "search_literary", "query_wikipedia"):
            assert f"mcp__rag__{tool}" in CLAUDE_REVIEWER_TOOLS

    def test_tools_end_with_read(self):
        """Both allow-lists should end with Read (file system access)."""
        assert CLAUDE_WRITER_TOOLS.endswith("Read")
        assert CLAUDE_REVIEWER_TOOLS.endswith("Read")

    def test_no_edit_write_bash_in_tools(self):
        """Writers/reviewers should NOT have Edit, Write, or Bash."""
        for tools in (CLAUDE_WRITER_TOOLS, CLAUDE_REVIEWER_TOOLS):
            assert "Edit" not in tools
            assert "Write" not in tools.replace("CLAUDE_WRITER", "")  # avoid matching the var name
            assert "Bash" not in tools


# ---------------------------------------------------------------------------
# Dispatch log saving
# ---------------------------------------------------------------------------

class TestSaveDispatchLog:
    """Verify dispatch logs are written with correct structure."""

    def test_creates_dispatch_dir(self, tmp_path):
        orch_dir = tmp_path / "orchestration" / "test-slug"
        _save_dispatch_log(
            orch_dir, "write", "gemini-tools (gemini-3.1-pro-preview)",
            prompt_chars=1000, response_chars=5000,
            stderr="tool call: verify_words", duration_s=45.3, ok=True,
        )
        dispatch_dir = orch_dir / "dispatch"
        assert dispatch_dir.exists()

        # Should have meta.json and stderr.log
        meta_files = list(dispatch_dir.glob("*-meta.json"))
        stderr_files = list(dispatch_dir.glob("*.stderr.log"))
        assert len(meta_files) == 1
        assert len(stderr_files) == 1

    def test_meta_json_structure(self, tmp_path):
        orch_dir = tmp_path / "orch"
        _save_dispatch_log(
            orch_dir, "review", "claude-tools (claude-opus-4-6)",
            prompt_chars=2000, response_chars=3000,
            returncode=0, duration_s=120.5, ok=True,
        )
        meta_file = next((orch_dir / "dispatch").glob("*-meta.json"))
        data = json.loads(meta_file.read_text())

        assert data["phase"] == "review"
        assert data["agent"] == "claude-tools (claude-opus-4-6)"
        assert data["ok"] is True
        assert data["returncode"] == 0
        assert data["prompt_chars"] == 2000
        assert data["response_chars"] == 3000
        assert data["duration_s"] == 120.5
        assert "timestamp" in data

    def test_sequence_prefix(self, tmp_path):
        orch_dir = tmp_path / "orch"
        _save_dispatch_log(orch_dir, "skeleton", "gemini", ok=True)
        _save_dispatch_log(orch_dir, "write", "gemini", ok=True)

        files = sorted((orch_dir / "dispatch").glob("*-meta.json"))
        assert "01-skeleton" in files[0].name
        assert "02-write" in files[1].name

    def test_stderr_always_saved(self, tmp_path):
        """Even empty stderr creates a file (removes ambiguity)."""
        orch_dir = tmp_path / "orch"
        _save_dispatch_log(orch_dir, "write", "gemini", stderr="", ok=True)
        stderr_files = list((orch_dir / "dispatch").glob("*.stderr.log"))
        assert len(stderr_files) == 1
        assert stderr_files[0].read_text() == ""


# ---------------------------------------------------------------------------
# dispatch_agent integration (mocked subprocess)
# ---------------------------------------------------------------------------

class TestDispatchAgent:
    """Test dispatch_agent with mocked subprocess."""

    @patch("build.dispatch.subprocess.run")
    def test_gemini_dispatch(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="## Section 1\nContent...", stderr=""
        )
        ok, raw = dispatch_agent(
            "test prompt", agent="gemini", phase="write",
            orch_dir=tmp_path, timeout=300, model="gemini-test",
        )
        assert ok is True
        assert "Section 1" in raw
        # Should have created dispatch log
        assert (tmp_path / "dispatch").exists()

    @patch("build.dispatch.subprocess.run")
    def test_claude_tools_dispatch(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="content here", stderr="tool: verify_words"
        )
        ok, _raw = dispatch_agent(
            "test prompt", agent="claude-tools", phase="review",
            orch_dir=tmp_path, timeout=600,
            mcp_tools=True, allowed_tools=CLAUDE_REVIEWER_TOOLS,
            model="claude-opus-4-6",
        )
        assert ok is True
        # Check MCP config was passed
        cmd = mock_run.call_args[0][0]
        assert "--mcp-config" in cmd
        assert "--allowedTools" in cmd

    @patch.dict("os.environ", {}, clear=True)
    @patch("build.dispatch.subprocess.run")
    def test_codex_dispatch_uses_output_file(self, mock_run, tmp_path):
        def _fake_run(cmd, **kwargs):
            output_path = cmd[cmd.index("-o") + 1]
            Path(output_path).write_text("Codex final answer", encoding="utf-8")
            return MagicMock(returncode=0, stdout="session id: test-session", stderr="")

        mock_run.side_effect = _fake_run
        ok, raw = dispatch_agent(
            "test prompt", agent="codex", phase="review",
            orch_dir=tmp_path, timeout=600, model="gpt-5.4",
        )
        assert ok is True
        assert raw == "Codex final answer"
        cmd = mock_run.call_args[0][0]
        assert cmd[:2] == ["codex", "exec"]
        assert "-o" in cmd
        assert "-s" in cmd
        assert "read-only" in cmd
        assert cmd[-1] == "-"

    @patch.dict("os.environ", {}, clear=True)
    @patch("build.dispatch.subprocess.run")
    def test_codex_tools_dispatch_uses_full_auto(self, mock_run, tmp_path):
        def _fake_run(cmd, **kwargs):
            output_path = cmd[cmd.index("-o") + 1]
            Path(output_path).write_text("OK", encoding="utf-8")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = _fake_run
        ok, raw = dispatch_agent(
            "test prompt", agent="codex-tools", phase="write",
            orch_dir=tmp_path, timeout=600, model="gpt-5.4",
        )
        assert ok is True
        assert raw == "OK"
        cmd = mock_run.call_args[0][0]
        assert "--full-auto" in cmd
        assert cmd[-1] == "-"

    @patch.dict("os.environ", {"CODEX_DISPATCH_MODE": "danger"}, clear=True)
    @patch("build.dispatch.subprocess.run")
    def test_codex_dispatch_honors_danger_override(self, mock_run, tmp_path):
        def _fake_run(cmd, **kwargs):
            output_path = cmd[cmd.index("-o") + 1]
            Path(output_path).write_text("OK", encoding="utf-8")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = _fake_run
        ok, raw = dispatch_agent(
            "test prompt", agent="codex", phase="review",
            orch_dir=tmp_path, timeout=600, model="gpt-5.4",
        )
        assert ok is True
        assert raw == "OK"
        cmd = mock_run.call_args[0][0]
        assert "--dangerously-bypass-approvals-and-sandbox" in cmd
        assert "-s" not in cmd
        assert cmd[-1] == "-"

    @patch("build.dispatch.subprocess.run")
    def test_timeout_logged(self, mock_run, tmp_path):
        import subprocess as sp
        mock_run.side_effect = sp.TimeoutExpired(cmd=["gemini"], timeout=300)

        ok, raw = dispatch_agent(
            "test", agent="gemini", phase="skeleton",
            orch_dir=tmp_path, timeout=300, model="test",
        )
        assert ok is False
        assert raw == ""
        # Dispatch log should record the timeout (primary + fallback model)
        meta_files = sorted((tmp_path / "dispatch").glob("*-meta.json"))
        assert len(meta_files) == 2  # primary timeout + fallback timeout
        for mf in meta_files:
            data = json.loads(mf.read_text())
            assert data["ok"] is False

    @patch("build.dispatch.subprocess.run")
    def test_failure_logged(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error: model overloaded"
        )
        ok, _raw = dispatch_agent(
            "test", agent="claude", phase="write",
            orch_dir=tmp_path, model="test",
        )
        assert ok is False
        # stderr should be saved
        stderr_files = list((tmp_path / "dispatch").glob("*.stderr.log"))
        assert len(stderr_files) == 1
        assert "overloaded" in stderr_files[0].read_text()

    def test_unknown_agent_rejected(self, tmp_path):
        ok, _raw = dispatch_agent(
            "test", agent="llama", phase="write", orch_dir=tmp_path,
        )
        assert ok is False
