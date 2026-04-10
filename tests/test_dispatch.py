"""Tests for scripts/build/dispatch.py — unified V6 dispatch + logging."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.dispatch import (
    CLAUDE_REVIEWER_TOOLS,
    CLAUDE_WRITER_TOOLS,
    _save_dispatch_log,
    dispatch_agent,
)


@pytest.fixture(autouse=True)
def _isolate_usage_log(tmp_path):
    """Ensure no test writes to the real batch_state/api_usage/ log."""
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield

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
            model="gemini-3.1-pro-preview",
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
            model="claude-opus-4-6",
            prompt_chars=2000, response_chars=3000,
            returncode=0, duration_s=120.5, ok=True,
        )
        meta_file = next((orch_dir / "dispatch").glob("*-meta.json"))
        data = json.loads(meta_file.read_text())

        assert data["phase"] == "review"
        assert data["agent"] == "claude-tools (claude-opus-4-6)"
        assert data["model"] == "claude-opus-4-6"
        assert data["ok"] is True
        assert data["returncode"] == 0
        assert data["prompt_chars"] == 2000
        assert data["response_chars"] == 3000
        assert data["prompt_tokens_est"] == 526
        assert data["response_tokens_est"] == 789
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

    def test_session_analysis_emitted_for_successful_gemini_call(
        self, tmp_path
    ):
        """When prompt+response are provided for a successful Gemini dispatch,
        the post-dispatch hook should emit a session-analysis YAML next to
        the meta.json. Covers the #1174 wiring end-to-end without touching
        the Gemini CLI itself.
        """
        orch_dir = tmp_path / "orch" / "test-slug"
        prompt = (
            "# Section-by-Section Generation — Section 1/4\n"
            "## Section Skeleton\n"
            "- P1 (~100 words): [Nominative case review with examples]\n"
            "<!-- INJECT_ACTIVITY: quiz, Case Drill, 8 items -->\n"
            "## Full Plan\n"
            + "plan content\n" * 20
            + "## Knowledge Packet\n"
            + "wiki\n" * 200
            + "## Output\nWrite the section."
        )
        response = (
            "## Cases\nThe Nominative case marks the subject of a sentence. "
            "Here are examples with the Nominative.\n"
            "<!-- INJECT_ACTIVITY: quiz, Case Drill, 8 items -->"
        )
        _save_dispatch_log(
            orch_dir, "write", "gemini-tools (gemini-3.1-pro-preview)",
            model="gemini-3.1-pro-preview",
            prompt_chars=len(prompt),
            response_chars=len(response),
            ok=True,
            prompt=prompt,
            response=response,
        )
        analysis_files = list(
            (orch_dir / "dispatch").glob("*-session-analysis.yaml")
        )
        assert len(analysis_files) == 1
        import yaml
        data = yaml.safe_load(analysis_files[0].read_text())
        assert data["phase"] == "write"
        assert data["prompt_chars"] == len(prompt)
        assert data["response_chars"] == len(response)
        # Wiki should dominate this synthetic prompt
        assert "wiki" in data["large_sections"]
        # At least one directive was extracted (skeleton para + activity)
        assert data["directives_total"] >= 2

    def test_session_analysis_skipped_for_failed_call(self, tmp_path):
        """A failed call must NOT emit a session-analysis file — the
        response is unreliable and analysis would produce noise."""
        orch_dir = tmp_path / "orch" / "test-slug"
        _save_dispatch_log(
            orch_dir, "write", "gemini-tools",
            model="gemini-3.1-pro-preview",
            prompt_chars=100, response_chars=0, ok=False,
            prompt="prompt text", response="",
        )
        analysis_files = list(
            (orch_dir / "dispatch").glob("*-session-analysis.yaml")
        )
        assert analysis_files == []

    def test_session_analysis_skipped_for_non_gemini_agent(self, tmp_path):
        """Session analysis currently targets Gemini only — Codex/Claude
        session formats are handled by separate adapters."""
        orch_dir = tmp_path / "orch" / "test-slug"
        _save_dispatch_log(
            orch_dir, "write", "codex (gpt-5.4)",
            model="gpt-5.4",
            prompt_chars=100, response_chars=100, ok=True,
            prompt="## Plan\nsome plan content", response="some response",
        )
        analysis_files = list(
            (orch_dir / "dispatch").glob("*-session-analysis.yaml")
        )
        assert analysis_files == []


# ---------------------------------------------------------------------------
# dispatch_agent integration (mocked subprocess)
# ---------------------------------------------------------------------------

class TestDispatchAgent:
    """Test dispatch_agent with mocked subprocess."""

    @patch("agent_runtime.runner.invoke")
    def test_gemini_dispatch(self, mock_invoke, tmp_path):
        # Post Phase 3: dispatch routes Gemini through agent_runtime.
        # We mock runtime_invoke and assert the glue translates dispatch
        # args into the right runtime call.
        from agent_runtime.result import Result
        mock_invoke.return_value = Result(
            ok=True, agent="gemini", model="gemini-test", mode="workspace-write",
            response="## Section 1\nContent...", stderr_excerpt=None,
            duration_s=1.5, session_id=None, rate_limited=False, stalled=False,
            returncode=0, usage_record={},
        )
        ok, raw = dispatch_agent(
            "test prompt", agent="gemini", phase="write",
            orch_dir=tmp_path, timeout=300, model="gemini-test",
        )
        assert ok is True
        assert "Section 1" in raw
        assert (tmp_path / "dispatch").exists()
        # Assert runtime was called with the right shape
        call_kwargs = mock_invoke.call_args.kwargs
        assert call_kwargs["mode"] == "workspace-write"
        assert call_kwargs["model"] == "gemini-test"
        assert call_kwargs["entrypoint"] == "dispatch"
        assert call_kwargs["tool_config"] is None  # mcp_tools=False by default

    @patch("agent_runtime.runner.invoke")
    def test_claude_tools_dispatch(self, mock_invoke, tmp_path):
        """Post Phase 5: Claude routes through runtime. MCP tool config
        travels via tool_config dict, not argv assertions."""
        from agent_runtime.result import Result
        mock_invoke.return_value = Result(
            ok=True, agent="claude", model="claude-opus-4-6", mode="read-only",
            response="content here", stderr_excerpt=None, duration_s=1.0,
            session_id=None, rate_limited=False, stalled=False,
            returncode=0, usage_record={},
        )
        ok, _raw = dispatch_agent(
            "test prompt", agent="claude-tools", phase="review",
            orch_dir=tmp_path, timeout=600,
            mcp_tools=True, allowed_tools=CLAUDE_REVIEWER_TOOLS,
            model="claude-opus-4-6",
        )
        assert ok is True
        # MCP tool config must have been passed through tool_config
        kwargs = mock_invoke.call_args.kwargs
        assert kwargs["tool_config"] is not None
        assert "mcp_config_path" in kwargs["tool_config"]
        assert kwargs["tool_config"]["allowed_tools"] == CLAUDE_REVIEWER_TOOLS
        assert kwargs["entrypoint"] == "dispatch"

    @patch.dict("os.environ", {}, clear=True)
    @patch("agent_runtime.runner.invoke")
    def test_codex_dispatch_read_only_mode(self, mock_invoke, tmp_path):
        """Post Phase 3: agent='codex' → mode='read-only' in runtime."""
        from agent_runtime.result import Result
        mock_invoke.return_value = Result(
            ok=True, agent="codex", model="gpt-5.4", mode="read-only",
            response="Codex final answer", stderr_excerpt=None,
            duration_s=2.0, session_id="test-session",
            rate_limited=False, stalled=False, returncode=0, usage_record={},
        )
        ok, raw = dispatch_agent(
            "test prompt", agent="codex", phase="review",
            orch_dir=tmp_path, timeout=600, model="gpt-5.4",
        )
        assert ok is True
        assert raw == "Codex final answer"
        kwargs = mock_invoke.call_args.kwargs
        assert kwargs["mode"] == "read-only"
        assert kwargs["entrypoint"] == "dispatch"
        assert kwargs["session_id"] is None

    @patch.dict("os.environ", {}, clear=True)
    @patch("agent_runtime.runner.invoke")
    def test_codex_tools_dispatch_workspace_write_mode(self, mock_invoke, tmp_path):
        """Post Phase 3: agent='codex-tools' → mode='workspace-write'."""
        from agent_runtime.result import Result
        mock_invoke.return_value = Result(
            ok=True, agent="codex", model="gpt-5.4", mode="workspace-write",
            response="OK", stderr_excerpt=None, duration_s=1.0,
            session_id=None, rate_limited=False, stalled=False,
            returncode=0, usage_record={},
        )
        ok, raw = dispatch_agent(
            "test prompt", agent="codex-tools", phase="write",
            orch_dir=tmp_path, timeout=600, model="gpt-5.4",
        )
        assert ok is True
        assert raw == "OK"
        kwargs = mock_invoke.call_args.kwargs
        assert kwargs["mode"] == "workspace-write"

    @patch.dict("os.environ", {"CODEX_DISPATCH_MODE": "danger"}, clear=False)
    @patch("agent_runtime.runner.invoke")
    def test_codex_dispatch_honors_danger_override(self, mock_invoke, tmp_path):
        """Post Phase 3: CODEX_DISPATCH_MODE=danger → mode='danger'."""
        from agent_runtime.result import Result
        mock_invoke.return_value = Result(
            ok=True, agent="codex", model="gpt-5.4", mode="danger",
            response="OK", stderr_excerpt=None, duration_s=1.0,
            session_id=None, rate_limited=False, stalled=False,
            returncode=0, usage_record={},
        )
        ok, raw = dispatch_agent(
            "test prompt", agent="codex", phase="review",
            orch_dir=tmp_path, timeout=600, model="gpt-5.4",
        )
        assert ok is True
        assert raw == "OK"
        kwargs = mock_invoke.call_args.kwargs
        assert kwargs["mode"] == "danger"

    @patch("agent_runtime.runner.invoke")
    def test_timeout_logged(self, mock_invoke, tmp_path):
        """Post Phase 3: runtime raises AgentTimeoutError → dispatch logs failure."""
        from agent_runtime.errors import AgentTimeoutError
        mock_invoke.side_effect = AgentTimeoutError("gemini", 300)

        ok, raw = dispatch_agent(
            "test", agent="gemini", phase="skeleton",
            orch_dir=tmp_path, timeout=300, model="test",
        )
        assert ok is False
        assert raw == ""
        meta_files = sorted((tmp_path / "dispatch").glob("*-meta.json"))
        assert len(meta_files) >= 1
        for mf in meta_files:
            data = json.loads(mf.read_text())
            assert data["ok"] is False

    @patch("agent_runtime.runner.invoke")
    def test_failure_logged(self, mock_invoke, tmp_path):
        """Post Phase 5: Claude routes through runtime. Runtime returns
        Result(ok=False) with stderr_excerpt; dispatch writes it to log."""
        from agent_runtime.result import Result
        mock_invoke.return_value = Result(
            ok=False, agent="claude", model="test", mode="read-only",
            response="", stderr_excerpt="Error: model overloaded",
            duration_s=0.5, session_id=None, rate_limited=False,
            stalled=False, returncode=1, usage_record={},
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
