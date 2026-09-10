"""Unit tests for batch Piper Opus audio synthesis tool (#7873)."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.audio.batch_synthesize_opus import (
    audio_relpath,
    build_manifest,
    encode_opus,
    lemma_digest,
    plain,
    resolve_stress,
    scan_batch,
    synthesize_batch,
    validate_opus,
)

FIXTURE_WAV = Path(__file__).parent / "fixtures/audio/pronunciation.wav"


def test_plain_and_lemma_digest():
    assert plain("Кни́га") == "книга"
    assert plain("сім’я́") == "сім'я"
    assert plain("памʼять") == "пам'ять"
    assert plain("  АВТО́БУС  ") == "автобус"

    expected_hash = hashlib.sha256("книга".encode()).hexdigest()
    assert lemma_digest("Кни́га") == expected_hash
    assert lemma_digest("книга") == expected_hash


def test_audio_relpath():
    h = lemma_digest("книга")
    assert audio_relpath("книга", ext="opus", shard=True) == f"{h[:2]}/{h}.opus"
    assert audio_relpath("книга", ext="opus", shard=False) == f"{h}.opus"


def test_resolve_stress_monosyllables():
    def oracle(lemma, pos=None):
        return {"status": "invalid_input"}

    text, reason = resolve_stress("ліс", None, oracle)
    assert text == "ліс"
    assert reason is None

    text, reason = resolve_stress("хліб", None, oracle)
    assert text == "хліб"
    assert reason is None


def test_resolve_stress_oracle():
    def mock_oracle(lemma, pos=None):
        if lemma == "книга":
            return {"status": "ok", "matches": [{"stressed_form": "кни́га"}]}
        if lemma == "замок":
            return {"status": "ambiguous", "matches": []}
        return {"status": "not_found"}

    text, reason = resolve_stress("книга", None, mock_oracle)
    assert text == "кни́га"
    assert reason is None

    text, reason = resolve_stress("замок", None, mock_oracle)
    assert text is None
    assert reason == "ambiguous"

    text, reason = resolve_stress("невідомо", None, mock_oracle)
    assert text is None
    assert reason == "not_found"


def make_dummy_opus(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = bytearray(b"OggS" + b"\x00" * 24 + b"OpusHead" + b"\x00" * 100)
    path.write_bytes(payload)
    return len(payload)


def test_validate_opus_rejects_invalid_files(tmp_path: Path):
    empty = tmp_path / "empty.opus"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="suspiciously small"):
        validate_opus(empty)

    corrupt = tmp_path / "corrupt.opus"
    corrupt.write_bytes(b"A" * 200)
    with pytest.raises(ValueError, match="invalid Ogg Opus header"):
        validate_opus(corrupt)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed on system")
def test_encode_opus_ffmpeg(tmp_path: Path):
    opus_path = tmp_path / "audio.opus"
    size = encode_opus(FIXTURE_WAV, opus_path, bitrate="24k")
    assert size > 500
    assert opus_path.is_file()
    assert validate_opus(opus_path) == size


def test_scan_batch_incremental_diff(tmp_path: Path):
    out_dir = tmp_path / "audio"
    out_dir.mkdir(parents=True)

    # Pre-populate one existing file
    h = lemma_digest("книга")
    existing_file = out_dir / f"{h[:2]}/{h}.opus"
    make_dummy_opus(existing_file)

    def mock_oracle(lemma, pos=None):
        return {"status": "ok", "matches": [{"stressed_form": f"{lemma}́"}]}

    items = [
        {"lemma": "книга"},  # existing
        {"lemma": "школа"},  # pending
        {"lemma": "ліс"},  # pending monosyllable
    ]

    existing, pending, excluded = scan_batch(items, out_dir, mock_oracle, shard=True)
    assert len(existing) == 1
    assert existing[0]["lemma"] == "книга"
    assert len(pending) == 2
    assert {p["lemma"] for p in pending} == {"школа", "ліс"}
    assert len(excluded) == 0


def test_synthesize_batch_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    out_dir = tmp_path / "audio"
    out_dir.mkdir(parents=True)

    def fake_synth(text: str, path: Path):
        shutil.copyfile(FIXTURE_WAV, path)

    monkeypatch.setattr(
        "scripts.audio.batch_synthesize_opus.encode_opus",
        lambda wav, opus, bitrate="24k": make_dummy_opus(opus),
    )

    pending = [
        {"lemma": "школа", "text": "шко́ла", "relpath": audio_relpath("школа")},
        {"lemma": "ліс", "text": "ліс", "relpath": audio_relpath("ліс")},
    ]

    completed = synthesize_batch(pending, out_dir, fake_synth, bitrate="24k")
    assert len(completed) == 2
    for c in completed:
        assert (out_dir / c["relpath"]).is_file()
        assert validate_opus(out_dir / c["relpath"]) > 0

    manifest = build_manifest([], completed, [], out_dir, {"engine": "test"})
    assert manifest["totalCount"] == 2
    assert manifest["synthesizedCount"] == 2
    assert (out_dir / "manifest.json").is_file()
    loaded = json.loads((out_dir / "manifest.json").read_text())
    assert loaded["totalCount"] == 2
    assert "школа" in loaded["entries"]


def test_default_manifest_discovery():
    from scripts.audio.batch_synthesize_opus import _find_default_manifest

    manifest_path = _find_default_manifest()
    if manifest_path is not None:
        assert manifest_path.name == "lexicon-manifest.json"
        assert manifest_path.is_file()


def test_cli_dry_run_subprocess(tmp_path: Path):
    import os
    import subprocess
    import sys

    dummy_manifest = tmp_path / "manifest.json"
    dummy_manifest.write_text(
        json.dumps({"entries": [{"lemma": "хліб", "pos": "noun"}, {"lemma": "невідомеслово", "pos": "noun"}]})
    )

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    script_path = Path(__file__).resolve().parents[1] / "scripts/audio/batch_synthesize_opus.py"
    proc = subprocess.run(
        [sys.executable, str(script_path), "--manifest", str(dummy_manifest), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "Total candidate words: 2" in proc.stdout
    assert "Pending synthesis: 1" in proc.stdout
    assert "Dry-run complete." in proc.stdout
