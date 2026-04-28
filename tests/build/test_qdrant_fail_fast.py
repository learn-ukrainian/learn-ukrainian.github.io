
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build.linear_pipeline import LinearPipelineError
from build.research import build_knowledge_packet


def test_build_knowledge_packet_raises_on_qdrant_fail():
    plan_path = Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml")

    # Mock _verify_qdrant_liveness to raise LinearPipelineError
    with patch("build.research.build_knowledge_packet._verify_qdrant_liveness") as mock_verify:
        mock_verify.side_effect = LinearPipelineError("Qdrant unreachable")

        with pytest.raises(LinearPipelineError, match="Qdrant unreachable"):
            build_knowledge_packet.build_packet(plan_path)

def test_build_knowledge_packet_raises_on_low_chunks():
    plan_path = Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml")

    # Mock _verify_qdrant_liveness to pass
    # Mock _search_rag to return empty list
    with patch("build.research.build_knowledge_packet._verify_qdrant_liveness"):
        with patch("build.research.build_knowledge_packet._search_rag", return_value=[]):
            with pytest.raises(LinearPipelineError, match="retrieved 0 chunks"):
                build_knowledge_packet.build_packet(plan_path)

def test_allow_degraded_rag_bypasses_errors():
    plan_path = Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml")

    # Mock _search_rag to return empty list, but pass allow_degraded_rag=True
    with patch("build.research.build_knowledge_packet._search_rag", return_value=[]):
        packet = build_knowledge_packet.build_packet(plan_path, allow_degraded_rag=True)
        assert "*No relevant textbook excerpts found.*" in packet

def test_delegate_liveness_probe_fails_dispatch():
    from scripts import delegate

    args = MagicMock()
    args.agent = "gemini"
    args.task_id = "test-123"
    args.allow_degraded_rag = False
    args.worktree = "auto"
    args.cwd = None
    args.prompt = "prompt"
    args.prompt_file = None
    args.mode = "read-only"
    args.model = None

    # Mock _provision_qdrant_alive to exit(1)
    with patch("scripts.delegate._provision_qdrant_alive") as mock_alive:
        mock_alive.side_effect = SystemExit(1)

        # We need to mock other things to get to the _ensure_worktree call
        with patch("scripts.delegate._read_state", return_value=None):
            with patch("scripts.delegate.Path.read_text", return_value="prompt"):
                with patch("scripts.delegate._auto_worktree_path", return_value=Path("/tmp/wt")):
                    with patch("scripts.delegate._resolve_sha", return_value="sha"):
                        with patch("scripts.delegate._provision_data_symlinks"):
                            with patch("subprocess.run") as mock_run:
                                with patch("subprocess.Popen") as mock_popen:
                                    mock_run.return_value = MagicMock(returncode=0)

                                    with pytest.raises(SystemExit):
                                        delegate.cmd_dispatch(args)

                                    # Verify subprocess.Popen (the worker) was NOT called
                                    mock_popen.assert_not_called()

def test_delegate_allow_degraded_rag_bypasses_liveness():
    from scripts import delegate

    args = MagicMock()
    args.agent = "gemini"
    args.task_id = "test-124"
    args.allow_degraded_rag = True
    args.worktree = "auto"
    args.cwd = None
    args.prompt = "prompt"
    args.prompt_file = None
    args.mode = "read-only"
    args.model = None

    # Mock _provision_qdrant_alive — it should NOT be called
    with patch("scripts.delegate._provision_qdrant_alive") as mock_alive:
        # We need to mock other things to get to the _ensure_worktree call
        with patch("scripts.delegate._read_state", return_value=None):
            with patch("scripts.delegate.Path.read_text", return_value="prompt"):
                with patch("scripts.delegate._auto_worktree_path", return_value=Path("/tmp/wt")):
                    with patch("scripts.delegate._resolve_sha", return_value="sha"):
                        with patch("scripts.delegate._provision_data_symlinks"):
                            with patch("subprocess.run") as mock_run:
                                with patch("subprocess.Popen") as mock_popen:
                                    mock_run.return_value = MagicMock(returncode=0)
                                    mock_popen.return_value = MagicMock(pid=12345, stdin=MagicMock())

                                    delegate.cmd_dispatch(args)

                                    # Verify _provision_qdrant_alive was NOT called
                                    mock_alive.assert_not_called()
                                    # Verify worker WAS called
                                    mock_popen.assert_called()
