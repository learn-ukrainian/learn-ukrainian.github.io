"""Tests for ab ask-opencode bridge subcommand (PR-D1)."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_agent_bridge._opencode import _invoke_opencode
from scripts.lib import rules_core

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]


def test_invoke_opencode_constructs_correct_argv():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="response", stderr="")
            _invoke_opencode("hello", "openrouter/google/gemma-4-31b-it")
            argv = run_mock.call_args[0][0]
            assert argv[0] == "/fake/opencode"
            assert argv[1] == "run"
            assert "--model" in argv
            assert "openrouter/google/gemma-4-31b-it" in argv
            assert argv[-1] == rules_core.with_core("hello")


def test_invoke_opencode_attaches_file(tmp_path):
    data_file = tmp_path / "report.html"
    data_file.write_text("<html><body>data</body></html>")
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_opencode("review", "openrouter/google/gemma-4-31b-it", data=str(data_file))
            argv = run_mock.call_args[0][0]
            assert "--file" in argv
            # file path is in argv right after --file
            file_idx = argv.index("--file")
            assert str(data_file.resolve()) == argv[file_idx + 1]
            assert argv[file_idx + 2] == "--"


def test_invoke_opencode_raises_when_binary_missing():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value=None):
        with pytest.raises(SystemExit, match="opencode CLI not found"):
            _invoke_opencode("hello", "openrouter/google/gemma-4-31b-it")


def test_run_opencode_lazy_import_resolves_under_script_path_invocation():
    """End-to-end repro of the #4473 regression: load the package exactly the
    way the documented CLI form does (ONLY scripts/ on sys.path, repo root
    absent) and drive _run_opencode far enough to execute its lazy
    routing_guard import. Pre-fix: ModuleNotFoundError. Post-fix: the import
    resolves and the stubbed missing-binary SystemExit fires."""
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    probe = (
        "import sys\n"
        "sys.path[:] = [p for p in sys.path if p not in ('', '.')]\n"
        f"sys.path.insert(0, {str(repo_root / 'scripts')!r})\n"
        "from ai_agent_bridge import _opencode\n"
        "import shutil\n"
        "shutil.which = lambda _n: None\n"
        "try:\n"
        "    _opencode._run_opencode('hi', 'openrouter/google/gemma-4-31b-it')\n"
        "except SystemExit:\n"
        "    print('LAZY-IMPORT-OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=str(repo_root / "tests"),  # anywhere that is NOT the repo root
        timeout=60,
    )
    assert "LAZY-IMPORT-OK" in result.stdout, (
        f"stdout={result.stdout!r} stderr={result.stderr[-800:]!r}"
    )


def test_strip_gemma_thought_keeps_answer_after_block():
    from scripts.ai_agent_bridge._opencode import _strip_gemma_thought

    raw = "<thought>reasoning here</thought>- приймають участь → беруть участь"
    assert _strip_gemma_thought(raw) == "- приймають участь → беруть участь"


def test_strip_gemma_thought_never_returns_empty():
    """Live burn 2026-07-07: a run that closed inside <thought> arrived blank."""
    from scripts.ai_agent_bridge._opencode import _strip_gemma_thought

    raw = "<thought>the whole answer lives in here: беруть участь</thought>"
    assert _strip_gemma_thought(raw) == raw
    assert _strip_gemma_thought("  plain answer, no thought block") .strip() == "plain answer, no thought block"
