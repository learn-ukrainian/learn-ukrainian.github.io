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

    # Deep mock: Mock qdrant client directly to raise an error
    with patch("rag.query.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_collections.side_effect = Exception("Connection refused")
        mock_get_client.return_value = mock_client

        with pytest.raises(LinearPipelineError, match=r"Qdrant on 127\.0\.0\.1:6334 is not reachable"):
            build_knowledge_packet._verify_qdrant_liveness()

def test_build_knowledge_packet_raises_on_empty_collection():
    plan_path = Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml")

    # Deep mock: Mock collection_stats
    with patch("rag.query.get_client"):
        with patch("rag.query.collection_stats", return_value={"textbooks": {"points_count": 0}}):
            with pytest.raises(LinearPipelineError, match=r"Reindex with: \.venv/bin/python scripts/rag/ingest\.py --all"):
                build_knowledge_packet._verify_qdrant_liveness()

def test_build_knowledge_packet_raises_on_low_chunks():
    plan_path = Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml")

    with patch("build.research.build_knowledge_packet._verify_qdrant_liveness"):
        # Mock search_text from the actual Qdrant level instead of _search_rag
        with patch("rag.query.search_text", return_value=[]):
            with pytest.raises(LinearPipelineError, match="retrieved 0 chunks"):
                build_knowledge_packet.build_packet(plan_path)

        # Mock search_text to return only 2 chunks (below floor)
        hits = [{"id": 1, "text": "hit1"}, {"id": 2, "text": "hit2"}]
        with patch("rag.query.search_text", return_value=hits):
            with patch("build.research.build_knowledge_packet._format_hit", return_value="hit"):
                with pytest.raises(LinearPipelineError, match="Reduce floor or query more sections in plan"):
                    build_knowledge_packet.build_packet(plan_path)

def test_allow_degraded_rag_bypasses_errors(capsys):
    plan_path = Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml")

    with patch("rag.query.search_text", side_effect=Exception("Connection refused")):
        # Pass allow_degraded_rag=True
        packet = build_knowledge_packet.build_packet(plan_path, allow_degraded_rag=True)
        assert "*No relevant textbook excerpts found.*" in packet

        # Verify stderr warning is emitted
        stderr = capsys.readouterr().err
        assert "LOUD WARNING" in stderr
        assert "RAG search internal error" in stderr or "unreachable" in stderr

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

    with patch("rag.query.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_collections.side_effect = Exception("Connection refused")
        mock_get_client.return_value = mock_client

        # We need to mock other things to get to the _ensure_worktree call
        with patch("scripts.delegate._read_state", return_value=None):
            with patch("scripts.delegate.Path.read_text", return_value="prompt"):
                with patch("scripts.delegate._auto_worktree_path", return_value=Path("/tmp/wt")):
                    with patch("scripts.delegate._resolve_sha", return_value="sha"):
                        with patch("scripts.delegate._provision_data_symlinks"):
                            with patch("subprocess.run") as mock_run:
                                with patch("subprocess.Popen") as mock_popen:
                                    mock_run.return_value = MagicMock(returncode=0)

                                    result = delegate.cmd_dispatch(args)

                                    # Verify cmd_dispatch caught DispatchPreconditionError and returned 1
                                    assert result == 1
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

    # Mock get_client — it should NOT be called
    with patch("rag.query.get_client") as mock_get_client:
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

                                    mock_get_client.assert_not_called()
                                    mock_popen.assert_called()

