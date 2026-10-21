"""Runtime shard exporter compression tests, split for loadfile scheduling."""

from __future__ import annotations

import hashlib
import random
import tracemalloc
import zlib
from pathlib import Path

import pytest

from scripts.atlas import export_runtime_shards as exporter
from scripts.atlas.export_runtime_shards import ExportError, gzip_bytes
from tests.test_export_runtime_shards import (
    _STORED_PATTERN,
    _export,
    _framed,
    _live_zlib_one_shot_blocks,
    _model_compressobj_blocks,
    _reference_export,
    _stored_sweep_lengths,
    _StoredFrameReader,
    _system_libz_version,
)

pytest_plugins = ("tests._export_runtime_shards_fixtures",)

def test_level0_framing_matches_one_shot_gzip_at_boundaries_random_and_buffer_growths() -> None:
    for length in _stored_sweep_lengths():
        data = _STORED_PATTERN[:length]
        assert _framed(data) == gzip_bytes(data, compression_level=0), length


@pytest.mark.parametrize("chunking", ["bytes", "odd", "block+3", "random"])
def test_level0_stream_is_chunking_independent_and_exact(chunking: str) -> None:
    rng = random.Random(chunking)
    for length in (0, 1, 32_753, 65_532, 100_000, 400_000, 1_500_000):
        data = _STORED_PATTERN[:length]
        if chunking == "bytes":
            data = data[:3_000]
            sizes = [1] * len(data)
        elif chunking == "odd":
            sizes = [7] * (len(data) // 7 + 1)
        elif chunking == "block+3":
            sizes = [65_538] * (len(data) // 65_538 + 1)
        else:
            sizes = [rng.randrange(0, 90_000) for _ in range(len(data) // 20_000 + 4)] + [len(data)]
        chunks, position = [], 0
        for size in sizes:
            chunks.append(data[position : position + size])
            position += size
        expected = gzip_bytes(data, compression_level=0)
        pieces: list[bytes] = []
        result = exporter.stream_gzip(lambda chunks=chunks: iter(chunks), compression_level=0, sink=pieces.append)
        assert b"".join(pieces) == expected
        assert result == exporter.GzipResult(
            len(expected), hashlib.sha256(expected).hexdigest(), len(data), hashlib.sha256(data).hexdigest()
        )
        assert exporter.gzip_size(lambda chunks=chunks: iter(chunks), compression_level=0) == len(expected)
        assert max(len(piece) for piece in pieces) <= max(65_535, max(sizes, default=0)), "streamed, not joined"


def test_stored_model_no_flush_path_matches_real_zlib_streams() -> None:
    """``Z_NO_FLUSH`` (the path of every UINT_MAX input slice but the last) against live zlib."""
    rng = random.Random(3)
    for _ in range(120):
        total = rng.choice((rng.randrange(0, 200_000), rng.randrange(0, 2_500_000)))
        cuts = sorted(rng.randrange(0, total + 1) for _ in range(rng.randrange(0, 10)))
        lengths = [end - start for start, end in zip([0, *cuts], [*cuts, total], strict=True)]
        compressor = zlib.compressobj(0, zlib.DEFLATED, 31)
        real, position = b"", 0
        for length in lengths:
            real += compressor.compress(_STORED_PATTERN[position : position + length])
            position += length
        real += compressor.flush()
        pieces: list[bytes] = []
        exporter._frame_stored_gzip(
            lambda total=total: (_STORED_PATTERN[:total],), _model_compressobj_blocks(lengths), pieces.append
        )
        assert b"".join(pieces) == real, lengths


def test_stored_block_plan_beyond_uint_max_without_allocating() -> None:
    """``zlib_compress_impl`` hands zlib ``UINT_MAX`` slices: ``Z_NO_FLUSH`` then ``Z_FINISH``.

    Source-derived: the ``Z_NO_FLUSH`` slice never writes a block shorter than
    ``min_block`` (32 KiB), so its tail stays in the window and the ``Z_FINISH``
    slice emits it together with the rest — the >4 GiB plan is the UINT_MAX plan
    with its final block extended (and split at 65535) by the extra bytes.
    """
    uint_max = exporter._UINT_MAX
    tracemalloc.start()
    try:
        base = exporter.stored_block_plan(uint_max)
        for extra in (1, 12_345, 70_000):
            plan = exporter.stored_block_plan(uint_max + extra)
            tail = base[-1][0] + extra
            expected_tail = [(65_535, 0)] * ((tail - 1) // 65_535) + [((tail - 1) % 65_535 + 1, 1)]
            assert plan == base[:-1] + expected_tail, extra
            assert sum(length for length, _last in plan) == uint_max + extra
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert base[:2] == [(65_531, 0), (32_773, 0)] and base[-1][1] == 1
    assert peak < 64 * 1024 * 1024, "a length-only plan, never the bytes"


@pytest.mark.slow
@pytest.mark.skipif(
    _system_libz_version() != zlib.ZLIB_RUNTIME_VERSION, reason="system libz.so.1 is not this runtime's zlib"
)
def test_stored_block_plan_matches_live_zlib_beyond_uint_max() -> None:
    """The length-only plan against the live library past ``UINT_MAX`` (two input slices)."""
    one_shot = _StoredFrameReader()
    one_shot.feed(memoryview(gzip_bytes(bytes(3_000_000), compression_level=0)))
    assert _live_zlib_one_shot_blocks(3_000_000) == one_shot.blocks  # the driver is CPython's one-shot path
    for total in (exporter._UINT_MAX + 1, exporter._UINT_MAX + 70_000):
        assert _live_zlib_one_shot_blocks(total) == exporter.stored_block_plan(total), total


def test_stored_planner_canary_fails_closed_on_runtime_disagreement(
    edge_db: Path, tmp_path: Path, monkeypatch
) -> None:
    exporter.check_stored_gzip_runtime()
    monkeypatch.setattr(exporter, "_stored_canary_passed", False)
    # A runtime whose output buffer grows differently frames stored blocks differently.
    monkeypatch.setattr(exporter, "_OUTPUT_BLOCK_SIZES", (16 * 1024, *exporter._OUTPUT_BLOCK_SIZES[1:]))
    with pytest.raises(ExportError, match="planner disagrees with this runtime"):
        exporter.check_stored_gzip_runtime()
    with pytest.raises(ExportError, match="planner disagrees"):
        exporter.stream_gzip(lambda: (b"x",), compression_level=0, sink=lambda _piece: None)
    with pytest.raises(ExportError, match="planner disagrees"):
        _export(edge_db, tmp_path / "out", compression_level=0)
    assert not (tmp_path / "out" / "atlas" / "current.json").exists()
    assert exporter._stored_canary_passed is False


def test_level0_replay_that_drifts_between_passes_fails_closed() -> None:
    calls = {"n": 0}

    def drifting():
        calls["n"] += 1
        return (b"a" * 70_000,) if calls["n"] == 1 else (b"b" * 70_000,)

    with pytest.raises(ExportError, match="replay differs"):
        exporter.stream_gzip(drifting, compression_level=0, sink=lambda _piece: None)
    calls["n"] = 0

    def growing():
        calls["n"] += 1
        return (b"a" * (70_000 + calls["n"]),)

    with pytest.raises(ExportError, match="more bytes than planned"):
        exporter.stream_gzip(growing, compression_level=0, sink=lambda _piece: None)


@pytest.mark.parametrize("level", [0, 1, 6, 9])
def test_oversized_entry_leaf_error_matches_reference_at_every_level(
    edge_db: Path, tmp_path: Path, level: int
) -> None:
    with pytest.raises(ExportError) as expected:
        _reference_export(edge_db, compression_level=level, entry_max=300, search_max=524_288)
    with pytest.raises(ExportError) as actual:
        _export(edge_db, tmp_path / "out", compression_level=level, entry_max_gzip_bytes=300)
    assert str(actual.value) == str(expected.value)
    assert "single entry record exceeds" in str(actual.value)


@pytest.mark.parametrize("level", [0, 1, 6, 9])
def test_unsplittable_search_error_matches_reference_at_every_level(
    edge_db: Path, tmp_path: Path, level: int
) -> None:
    with pytest.raises(ExportError) as expected:
        _reference_export(edge_db, compression_level=level, entry_max=1_048_576, search_max=150)
    with pytest.raises(ExportError) as actual:
        _export(edge_db, tmp_path / "out", compression_level=level, search_max_gzip_bytes=150)
    assert str(actual.value) == str(expected.value)
    assert "cannot split" in str(actual.value)
