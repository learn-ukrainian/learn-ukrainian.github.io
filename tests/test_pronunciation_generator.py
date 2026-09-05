"""Structural and failure-path tests; these do not certify spoken Ukrainian."""

import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import pytest

from scripts.audio.generate_pronunciation import generate, select_slice, validate_wav

FIXTURE = Path(__file__).parent / "fixtures/audio/pronunciation.wav"


def oracle(lemma, pos=None):
    return {"status": "ok", "matches": [{"stressed_form": lemma}]}


def deck_file(tmp_path, lemmas=("б", "а", "а")):
    path = tmp_path / "deck.json"
    path.write_text(json.dumps({"deckVersion": "test-v1", "lexemes": [{"lemmaPlain": x} for x in lemmas]}))
    return path


def test_deduplicates_preserves_deck_order_and_caps(tmp_path):
    deck = json.loads(deck_file(tmp_path).read_text())
    selected, excluded = select_slice(deck, 2, oracle)
    assert [x["lemma"] for x in selected] == ["б", "а"]
    assert excluded == []


@pytest.mark.parametrize("limit", [0, -1, 501])
def test_hard_cap(limit):
    with pytest.raises(ValueError, match="limit"):
        select_slice({}, limit, oracle)


def test_ambiguous_stress_excluded_not_guessed(tmp_path):
    def stress(lemma, pos=None):
        return {"status": "ambiguous"} if lemma == "а" else oracle(lemma)

    selected, excluded = select_slice(json.loads(deck_file(tmp_path, ("а", "б")).read_text()), 1, stress)
    assert selected == [{"lemma": "б", "text": "б"}]
    assert excluded == [{"lemma": "а", "reason": "ambiguous"}]


def test_short_slice_fails(tmp_path):
    with pytest.raises(ValueError, match="only 2 eligible"):
        select_slice(json.loads(deck_file(tmp_path).read_text()), 3, oracle)


def test_stress_cannot_change_lemma(tmp_path):
    with pytest.raises(ValueError, match="changed lemma"):
        select_slice(
            json.loads(deck_file(tmp_path).read_text()),
            1,
            lambda _, pos=None: {"status": "ok", "matches": [{"stressed_form": "different"}]},
        )


def test_manifest_and_content_addressed_wav(tmp_path):
    output = tmp_path / "audio"
    result = generate(
        deck_file(tmp_path), output, 2, oracle, lambda text, path: shutil.copyfile(FIXTURE, path), {"name": "fixture"}
    )
    assert result["count"] == 2
    assert result["sourceCount"] == 3
    assert result["listeningEnabled"] is False
    assert len(list(output.glob("manifest-*.json"))) == 1
    assert json.loads((output / "manifest.json").read_text()) == result
    for entry in result["entries"].values():
        assert len(entry["file"]) == 68
        assert validate_wav(output / entry["file"]) > 0


def test_failed_second_file_preserves_published_manifest(tmp_path):
    output = tmp_path / "audio"
    output.mkdir()
    (output / "manifest.json").write_text("previous")
    calls = 0

    def synthesize(text, path):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("engine failed")
        shutil.copyfile(FIXTURE, path)

    with pytest.raises(RuntimeError, match="engine failed"):
        generate(deck_file(tmp_path), output, 2, oracle, synthesize, {})
    assert (output / "manifest.json").read_text() == "previous"


def test_silence_rejected(tmp_path):
    path = tmp_path / "silent.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
        wav.writeframes(b"\0" * 22050)
    with pytest.raises(ValueError, match="silent"):
        validate_wav(path)


def test_help_runs_without_engine():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.audio.generate_pronunciation", "--help"],
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "Exit codes:" in result.stdout
    assert "--limit" in result.stdout


def test_monosyllable_has_no_invented_stress(tmp_path):
    result, excluded = select_slice(
        json.loads(deck_file(tmp_path, ("так",)).read_text()), 1, lambda _, pos=None: {"status": "invalid_input"}
    )
    assert result == [{"lemma": "так", "text": "так"}]
    assert excluded == []


def test_normalizes_atlas_display_keys():
    from scripts.audio.generate_pronunciation import plain

    assert plain("Інтерне́т") == "інтернет"
    assert plain("п’ять") == plain("пʼять") == "п'ять"


def test_passes_pos_to_stress_oracle(tmp_path):
    calls = []

    def stress(lemma, pos=None):
        calls.append(pos)
        return oracle(lemma)

    select_slice({"deckVersion": "v", "lexemes": [{"lemmaPlain": "слово", "pos": "noun"}]}, 1, stress)
    assert calls == ["noun"]


def test_corrupt_cached_model_fails_before_synthesis(tmp_path):
    from scripts.audio.generate_pronunciation import ensure_model

    (tmp_path / "voice.onnx").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum mismatch"):
        ensure_model(tmp_path, download=False)


def test_missing_model_does_not_download_without_flag(tmp_path):
    from scripts.audio.generate_pronunciation import ensure_model

    with pytest.raises(ValueError, match="model missing"):
        ensure_model(tmp_path, download=False)


def test_malformed_lexeme_fails_before_any_synthesis(tmp_path):
    path = tmp_path / "deck.json"
    path.write_text(json.dumps({"deckVersion": "v", "lexemes": [None]}))
    with pytest.raises(ValueError, match="invalid lexeme row"):
        generate(path, tmp_path / "audio", 1, oracle, lambda *_: pytest.fail("must not synthesize"), {})
