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
    # Deep mock: Mock qdrant client directly to raise an error
    with patch("rag.query.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_collections.side_effect = Exception("Connection refused")
        mock_get_client.return_value = mock_client

        with pytest.raises(LinearPipelineError, match=r"Qdrant on 127\.0\.0\.1:6334 is not reachable"):
            build_knowledge_packet._verify_qdrant_liveness()

def test_build_knowledge_packet_raises_on_empty_collection():
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
        hits = [
            {"chunk_id": "c1", "text": "hit1", "author": "a", "grade": 1, "page": 1, "score": 0.9},
            {"chunk_id": "c2", "text": "hit2", "author": "a", "grade": 1, "page": 2, "score": 0.8}
        ]
        with patch("rag.query.search_text", return_value=hits):
            with pytest.raises(LinearPipelineError, match="Reduce floor or query more sections in plan"):
                build_knowledge_packet.build_packet(plan_path)

def test_build_knowledge_packet_cumulative_floor():
    """Test that hits from multiple queries in a section combine to meet the floor."""
    plan_path = Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml")

    # Mock _verify_qdrant_liveness to pass
    with patch("build.research.build_knowledge_packet._verify_qdrant_liveness"):
        # Each hit MUST be > 50 chars to pass _format_hit
        long_text = "This is a sufficiently long text to pass the 50 character limit check in format_hit. " * 2

        def mock_search_fn(query, **kwargs):
            # Return 5 hits for any query to ensure floor is met
            return [
                {"chunk_id": f"h_{query}_{i}", "text": long_text + str(i), "author": "a", "grade": 1, "page": i, "score": 0.9}
                for i in range(5)
            ]

        with patch("rag.query.search_text", side_effect=mock_search_fn):
            # Should NOT raise LinearPipelineError because total hits >= 5 per section
            packet = build_knowledge_packet.build_packet(plan_path)
            # The plan has 5 sections, each should have 5 hits = 25 hits total
            assert packet.count("> **Source:**") >= 25

def test_search_rag_exception_boundaries(capsys):
    """Finding 2: Qdrant errors fail-fast, others are graceful."""
    import httpx
    from build.research.build_knowledge_packet import _search_rag

    # 1. Qdrant-related error (fatal -> LinearPipelineError)
    with patch("rag.query.search_text", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(LinearPipelineError, match="RAG Qdrant search unreachable"):
            _search_rag("test", allow_degraded=False)

    # 2. Unrelated error (graceful)
    with patch("rag.query.search_text", side_effect=RuntimeError("totally unrelated")):
        results = _search_rag("test", allow_degraded=False)
        assert results == []
        stderr = capsys.readouterr().err
        assert "RAG search internal error" in stderr

def test_allow_degraded_rag_bypasses_errors(capsys):
    plan_path = Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml")

    with patch("rag.query.search_text", side_effect=Exception("Qdrant connection refused")):
        # Pass allow_degraded_rag=True
        packet = build_knowledge_packet.build_packet(plan_path, allow_degraded_rag=True)
        assert "*No relevant textbook excerpts found.*" in packet

        # Verify stderr warning is emitted
        stderr = capsys.readouterr().err
        assert "⚠️  RAG Qdrant search unreachable" in stderr

def test_delegate_liveness_probe_blocks_worker_spawn_no_worktree():
    """Finding 1: Liveness probe blocks worker spawn even without --worktree."""
    from scripts import delegate

    args = MagicMock()
    args.agent = "gemini"
    args.task_id = "test-125"
    args.allow_degraded_rag = False
    args.worktree = None # NO WORKTREE
    args.cwd = "."
    args.prompt = "prompt"
    args.prompt_file = None
    args.mode = "read-only"
    args.model = None

    with patch("rag.query.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_collections.side_effect = Exception("Connection refused")
        mock_get_client.return_value = mock_client

        with patch("scripts.delegate._read_state", return_value=None):
            with patch("scripts.delegate._write_state_atomic"):
                with patch("subprocess.Popen") as mock_popen:
                    result = delegate.cmd_dispatch(args)

                    # Verify cmd_dispatch failed
                    assert result == 1
                    # Verify Popen was never called
                    mock_popen.assert_not_called()

def test_delegate_liveness_probe_blocks_worker_spawn_worktree():
    """Finding 1: Liveness probe blocks worker spawn with --worktree."""
    from scripts import delegate

    args = MagicMock()
    args.agent = "gemini"
    args.task_id = "test-126"
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

        with patch("scripts.delegate._read_state", return_value=None):
            with patch("scripts.delegate._auto_worktree_path", return_value=Path("/tmp/wt")):
                with patch("scripts.delegate._ensure_worktree") as mock_ensure:
                    # ensure_worktree should be called
                    mock_ensure.return_value = (Path("/tmp/wt"), "branch", {})

                    with patch("scripts.delegate._write_state_atomic"):
                        with patch("subprocess.Popen") as mock_popen:
                            result = delegate.cmd_dispatch(args)

                            # Verify cmd_dispatch failed
                            assert result == 1
                            # Verify Popen was never called
                            mock_popen.assert_not_called()
