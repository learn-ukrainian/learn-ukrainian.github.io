"""Build a bounded, stress-verified local Piper pronunciation slice (#4696)."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import sys
import tempfile
import unicodedata
import wave
from pathlib import Path
from urllib.request import urlopen

REVISION = "1162a9173d0ce503555aed757976b7a9912eae4c"
VOICE = "uk_UA-ukrainian_tts-medium"
MODEL_FILES = {
    "voice.onnx": "7920419ac5f6fd8b6450520f24b52ed5a319cb53dd018fbcd71c9e079cbac84f",
    "voice.onnx.json": "4e96e72917ca9b94edc77d6ccfee03a73f450ba2fc1ca93c2e562bc014e5aa55",
}
MAX_LEMMAS = 500


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plain(text: str) -> str:
    """The practice deck key: casefold, stress removal and apostrophe folding."""
    return unicodedata.normalize(
        "NFC", text.casefold().replace("\u0301", "").replace("\u0300", "").replace("’", "'").replace("ʼ", "'").strip()
    )


def select_slice(deck: dict, limit: int, oracle) -> tuple[list[dict], list[dict]]:
    """Preserve hydrated deck order; do not guess ambiguous/unknown stress."""
    if not 1 <= limit <= MAX_LEMMAS:
        raise ValueError(f"limit must be between 1 and {MAX_LEMMAS}")
    if not isinstance(deck.get("deckVersion"), str) or not deck["deckVersion"]:
        raise ValueError("missing deckVersion")
    rows = deck.get("lexemes")
    if not isinstance(rows, list) or not rows:
        raise ValueError("missing lexemes")
    lemmas = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid lexeme row")
        lemma = row.get("lemmaPlain")
        if not isinstance(lemma, str) or not lemma.strip() or lemma != lemma.strip():
            raise ValueError("invalid lemmaPlain")
        lemmas.setdefault(plain(lemma), row.get("pos"))
    selected, excluded = [], []
    for lemma, pos in lemmas.items():
        result = oracle(lemma, pos=pos)
        # The stress oracle deliberately rejects monosyllables: there is no
        # stress-position choice. Keep only a single Ukrainian word with one vowel.
        monosyllable = (
            result["status"] == "invalid_input"
            and re.fullmatch("[а-щьюяєіїґ'-]+", lemma)
            and sum(ch in "аеєиіїоуюя" for ch in lemma) == 1
        )
        if monosyllable:
            text = lemma
        elif result["status"] == "ok":
            matches = result["matches"]
            if len(matches) != 1 or plain(matches[0]["stressed_form"]) != lemma:
                raise ValueError("stress oracle changed lemma or returned multiple readings")
            text = matches[0]["stressed_form"]
        else:
            excluded.append({"lemma": lemma, "reason": result["status"]})
            continue
        selected.append({"lemma": lemma, "text": text})
        if len(selected) == limit:
            break
    if len(selected) != limit:
        raise ValueError(f"only {len(selected)} eligible lemmas; requested {limit}")
    return selected, excluded


def validate_wav(path: Path) -> float:
    """Reject malformed, empty, silent or implausibly long output; not a language test."""
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 22050):
            raise ValueError("expected mono PCM16 at 22050 Hz")
        frames = wav.getnframes()
        data = wav.readframes(frames)
        duration = frames / wav.getframerate()
        if len(data) != frames * 2 or not 0.1 <= duration <= 15 or not any(data):
            raise ValueError("invalid, silent or truncated audio")
        return duration


def atomic_write(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_model(directory: Path, download: bool) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name, expected in MODEL_FILES.items():
        path = directory / name
        if not path.exists():
            if not download:
                raise ValueError("model missing; use --download-model")
            suffix = ".onnx.json" if name.endswith("json") else ".onnx"
            url = f"https://huggingface.co/rhasspy/piper-voices/resolve/{REVISION}/uk/uk_UA/ukrainian_tts/medium/{VOICE}{suffix}"
            with urlopen(url, timeout=120) as response:
                data = response.read()
            if digest(data) != expected:
                raise ValueError("downloaded model checksum mismatch")
            atomic_write(path, data)
        if digest(path.read_bytes()) != expected:
            raise ValueError(f"model checksum mismatch: {name}")
    return directory / "voice.onnx"


def generate(deck_path: Path, output: Path, limit: int, oracle, synthesize, provenance: dict) -> dict:
    source = deck_path.read_bytes()
    deck = json.loads(source)
    selected, excluded = select_slice(deck, limit, oracle)
    output.mkdir(parents=True, exist_ok=True)
    entries = {}
    # Publish manifest last: failed synthesis cannot expose a partial slice.
    with tempfile.TemporaryDirectory(dir=output) as staging:
        for item in selected:
            wav = Path(staging) / "audio.wav"
            synthesize(item["text"], wav)
            duration = validate_wav(wav)
            data = wav.read_bytes()
            filename = f"{digest(data)}.wav"
            atomic_write(output / filename, data)
            entries[item["lemma"]] = {"file": filename, "text": item["text"], "seconds": round(duration, 3)}
    manifest = {
        "schemaVersion": 1,
        "deckVersion": deck["deckVersion"],
        "deckSha256": digest(source),
        "sourceCount": len(deck["lexemes"]),
        "count": len(entries),
        "limit": limit,
        "selectionOrder": "hydrated-lexeme-order",
        "engine": provenance,
        "excluded": excluded,
        "entries": entries,
        "listeningEnabled": False,
    }
    encoded = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    atomic_write(output / f"manifest-{digest(encoded)}.json", encoded)
    atomic_write(output / "manifest.json", encoded)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate local Ukrainian pronunciation WAVs for a bounded hydrated A1 deck slice.\n"
        "Use before a site build; this does not certify pronunciation or enable listening mode.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  make pronunciation-audio PYTHON=/absolute/path/to/project/python\n"
        "  /absolute/path/to/project/python -m scripts.audio.generate_pronunciation --limit 200 --download-model\n"
        "Outputs: ignored WAVs, versioned manifest and manifest.json in site/public/audio/pronunciation.\n"
        "Exit codes: 0 success; nonzero invalid input, model, stress source or synthesis.\n"
        "Related: docs/runbooks/pronunciation-audio.md; #4696.",
    )
    parser.add_argument(
        "--deck",
        type=Path,
        default=Path("site/public/lexicon/practice-lexemes.A1.json"),
        help="Hydrated lexeme JSON (default: site/public/lexicon/practice-lexemes.A1.json)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("site/public/audio/pronunciation"),
        help="Public output directory (default: site/public/audio/pronunciation)",
    )
    parser.add_argument("--limit", type=int, default=200, help="Exact eligible lemma count, 1–500 (default: 200)")
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("batch_state/tts-model"),
        help="Pinned model cache (default: batch_state/tts-model)",
    )
    parser.add_argument(
        "--runtime-dir",
        type=Path,
        default=Path("batch_state/tts-runtime"),
        help="Optional pip --target directory (default: batch_state/tts-runtime); no virtualenv required",
    )
    parser.add_argument(
        "--download-model",
        action="store_true",
        help="Download missing pinned model files (default: offline, no download)",
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= MAX_LEMMAS:
        parser.error("limit must be between 1 and 500")
    if args.runtime_dir.is_dir():
        sys.path.insert(0, str(args.runtime_dir.resolve()))
    from piper import PiperVoice, SynthesisConfig

    from scripts.verification.stress import source_info, verify_stress

    if importlib.metadata.version("piper-tts") != "1.3.0":
        raise ValueError("install piper-tts==1.3.0")
    model = ensure_model(args.model_dir, args.download_model)
    voice = PiperVoice.load(str(model))
    config = SynthesisConfig(speaker_id=0)

    def synthesize(text: str, path: Path) -> None:
        unsupported = set(unicodedata.normalize("NFD", text)) - voice.config.phoneme_id_map.keys()
        if unsupported:
            raise ValueError("input has unsupported model codepoints")
        with wave.open(str(path), "wb") as wav:
            voice.synthesize_wav(text, wav, syn_config=config)

    provenance = {
        "name": "piper",
        "version": "1.3.0",
        "license": "GPL-3.0-or-later",
        "voice": VOICE,
        "speaker": "lada",
        "speakerId": 0,
        "modelRevision": REVISION,
        "modelSha256": MODEL_FILES["voice.onnx"],
        "modelLicense": "MIT",
        "datasetLicense": "CC0",
        "stressSource": source_info(),
    }
    manifest = generate(args.deck, args.out_dir, args.limit, verify_stress, synthesize, provenance)
    print(
        f"Generated {manifest['count']} lemmas from {manifest['sourceCount']} source rows; "
        f"{len(manifest['excluded'])} excluded before cap; listening remains disabled."
    )


if __name__ == "__main__":
    main()
