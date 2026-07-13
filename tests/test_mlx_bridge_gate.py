from __future__ import annotations

import builtins
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts/ directory to path to import wiki modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from wiki import dense_rerank, mlx_bridge


def test_get_physical_ram_darwin(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")

    def mock_check_output(args: list[str], **kwargs: Any) -> str:
        if args == ["sysctl", "-n", "hw.memsize"]:
            return "17179869184\n"
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)
    assert mlx_bridge.get_physical_ram() == 17179869184


def test_get_physical_ram_linux(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")

    mock_meminfo = "MemTotal:       16345678 kB\n"
    original_open = builtins.open

    def mock_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        if str(file) == "/proc/meminfo":
            from io import StringIO
            return StringIO(mock_meminfo)
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)
    assert mlx_bridge.get_physical_ram() == 16345678 * 1024


def test_no_mlx_kill_switch(monkeypatch) -> None:
    monkeypatch.setenv("SOURCES_MCP_NO_MLX", "1")
    monkeypatch.setattr(mlx_bridge, "get_physical_ram", lambda: 64 * 1024 * 1024 * 1024)

    with pytest.raises(mlx_bridge.MLXDisabledError) as exc_info:
        mlx_bridge.MLXEncoderBridge()
    assert "SOURCES_MCP_NO_MLX=1" in str(exc_info.value)


def test_force_mlx_override(monkeypatch) -> None:
    monkeypatch.setenv("SOURCES_MCP_FORCE_MLX", "1")
    monkeypatch.setattr(mlx_bridge, "get_physical_ram", lambda: 16 * 1024 * 1024 * 1024)

    # Instantiation should succeed
    bridge = mlx_bridge.MLXEncoderBridge()
    assert bridge is not None


def test_precedence_no_mlx_overrides_force_mlx(monkeypatch) -> None:
    monkeypatch.setenv("SOURCES_MCP_NO_MLX", "1")
    monkeypatch.setenv("SOURCES_MCP_FORCE_MLX", "1")
    monkeypatch.setattr(mlx_bridge, "get_physical_ram", lambda: 64 * 1024 * 1024 * 1024)

    with pytest.raises(mlx_bridge.MLXDisabledError) as exc_info:
        mlx_bridge.MLXEncoderBridge()
    assert "SOURCES_MCP_NO_MLX=1" in str(exc_info.value)


def test_floor_refusal_and_acceptance(monkeypatch) -> None:
    monkeypatch.delenv("SOURCES_MCP_NO_MLX", raising=False)
    monkeypatch.delenv("SOURCES_MCP_FORCE_MLX", raising=False)

    # Case A: Low RAM (16GB) -> refuse
    monkeypatch.setattr(mlx_bridge, "get_physical_ram", lambda: 16 * 1024 * 1024 * 1024)
    mlx_bridge._LOGGED_DISABLE = False

    with pytest.raises(mlx_bridge.MLXDisabledError) as exc_info:
        mlx_bridge.MLXEncoderBridge()
    assert "16GB RAM < 32GB floor" in str(exc_info.value)

    # Case B: High RAM (32GB) -> accept
    monkeypatch.setattr(mlx_bridge, "get_physical_ram", lambda: 32 * 1024 * 1024 * 1024)
    bridge = mlx_bridge.MLXEncoderBridge()
    assert bridge is not None


def test_consumer_degrades_not_raises(monkeypatch) -> None:
    # Force disabled state
    monkeypatch.setenv("SOURCES_MCP_NO_MLX", "1")

    # Mock load_corpus_index
    import numpy as np

    class MockIndex:
        def __init__(self) -> None:
            self.corpus = "test_corpus"
            self.shards = {0: np.zeros((2, 1024), dtype=np.float16)}
            self.unit_rows = {"1": (0, 0), "2": (0, 1)}

    monkeypatch.setattr(dense_rerank, "load_corpus_index", lambda *a, **kw: MockIndex())

    candidates = [
        {"unit_key": "1", "fts_score": -5.0},
        {"unit_key": "2", "fts_score": -10.0},
    ]

    # Reranking should degrade gracefully and not raise
    results = dense_rerank.rerank_candidates(
        "query",
        candidates,
        corpus="test_corpus",
        limit=10,
    )

    # Results should be returned, scored with 0.0, and sorted by fts_score (more negative is better)
    assert len(results) == 2
    assert results[0]["unit_key"] == "2"
    assert results[1]["unit_key"] == "1"
    assert results[0]["dense_score"] == 0.0
    assert results[0]["cosine_score"] == 0.0
