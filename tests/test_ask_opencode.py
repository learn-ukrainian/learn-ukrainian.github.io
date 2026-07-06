"""Tests for ab ask-opencode bridge subcommand (PR-D1)."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_agent_bridge._opencode import OPENCODE_DEFAULT_MODEL, _invoke_opencode


def test_opencode_default_model_is_cheap_and_guard_allowed():
    from scripts.ai_agent_bridge.routing_guard import assert_model_routing_allowed

    assert OPENCODE_DEFAULT_MODEL == "openrouter/google/gemma-4-31b-it"
    assert_model_routing_allowed(OPENCODE_DEFAULT_MODEL, context="default-model test")


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
            assert "hello" in argv


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


def test_no_absolute_scripts_self_imports_in_bridge_package():
    """Script-path invocation (`python scripts/ai_agent_bridge/__main__.py`,
    the documented CLI form) puts scripts/ — not the repo root — on sys.path,
    so the package is importable only as `ai_agent_bridge`. An absolute
    `scripts.ai_agent_bridge` self-import inside the package therefore breaks
    every lane whose module does it (#4473's lazy routing_guard import in
    _opencode.py killed pool/glm/gemma for script-path callers)."""
    import re
    from pathlib import Path

    pkg = Path(__file__).resolve().parent.parent / "scripts" / "ai_agent_bridge"
    offenders = []
    for path in sorted(pkg.rglob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"\s*(from|import)\s+scripts\.ai_agent_bridge", line):
                offenders.append(f"{path.name}:{lineno}")
    assert offenders == [], (
        f"absolute scripts.* self-imports break script-path invocation: {offenders}"
    )


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
