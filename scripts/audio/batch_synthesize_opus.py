"""Batch Piper Opus synthesis tool for Word Atlas and Practice Hub (#7873).

Generates 24 kbps mono OGG/Opus audio clips using Piper TTS (lada / uk_UA-ukrainian_tts-medium)
with unambiguous lexical stress marks. Supports deterministic lemma-hash naming, sharded
directory structure, incremental delta diffs, and atomic manifest publishing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import wave
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.request import urlopen

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _find_default_manifest() -> Path | None:
    for p in [_REPO_ROOT, *_REPO_ROOT.parents]:
        candidate = p / "site" / "src" / "data" / "lexicon-manifest.json"
        if candidate.is_file():
            return candidate
    return None


DEFAULT_MANIFEST = _find_default_manifest()

REVISION = "1162a9173d0ce503555aed757976b7a9912eae4c"
VOICE = "uk_UA-ukrainian_tts-medium"
MODEL_FILES = {
    "voice.onnx": "7920419ac5f6fd8b6450520f24b52ed5a319cb53dd018fbcd71c9e079cbac84f",
    "voice.onnx.json": "4e96e72917ca9b94edc77d6ccfee03a73f450ba2fc1ca93c2e562bc014e5aa55",
}
DEFAULT_BITRATE = "24k"


def plain(text: str) -> str:
    """Normalize lemma: casefold, NFC, remove stress marks, and fold apostrophes."""
    return unicodedata.normalize(
        "NFC",
        text.casefold().replace("\u0301", "").replace("\u0300", "").replace("’", "'").replace("ʼ", "'").strip(),
    )


def lemma_digest(lemma: str) -> str:
    """Deterministic SHA-256 of normalized lemma key."""
    return hashlib.sha256(plain(lemma).encode("utf-8")).hexdigest()


def audio_relpath(lemma: str, ext: str = "opus", shard: bool = True) -> str:
    """Relative audio path. If shard=True: xx/xxxx...opus; else: xxxx...opus."""
    h = lemma_digest(lemma)
    if shard:
        return f"{h[:2]}/{h}.{ext}"
    return f"{h}.{ext}"


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(data)
    try:
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def encode_opus(wav_path: Path, opus_path: Path, bitrate: str = DEFAULT_BITRATE) -> int:
    """Encode PCM16 WAV to Ogg Opus at specified bitrate mono using ffmpeg."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH; required for Opus transcoding")
    opus_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        str(wav_path),
        "-c:a",
        "libopus",
        "-b:a",
        bitrate,
        "-vbr",
        "on",
        "-application",
        "voip",
        str(opus_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg encoding failed: {proc.stderr}")
    return validate_opus(opus_path)


def validate_opus(path: Path) -> int:
    """Validate that path exists, starts with OggS container header, and is non-trivial."""
    if not path.is_file():
        raise ValueError(f"opus file does not exist: {path}")
    size = path.stat().st_size
    if size < 100:
        raise ValueError(f"opus file suspiciously small ({size} bytes): {path}")
    header = path.read_bytes()[:100]
    if not header.startswith(b"OggS") or b"OpusHead" not in header:
        raise ValueError(f"invalid Ogg Opus header: {path}")
    return size


def validate_wav(path: Path) -> float:
    """Validate PCM16 mono audio at 22050 Hz."""
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 22050):
            raise ValueError("expected mono PCM16 at 22050 Hz")
        frames = wav.getnframes()
        data = wav.readframes(frames)
        duration = frames / wav.getframerate()
        if len(data) != frames * 2 or not 0.1 <= duration <= 15 or not any(data):
            raise ValueError("invalid, silent, or truncated audio")
        return duration


def resolve_stress(lemma: str, pos: str | None, oracle: Callable[..., dict[str, Any]]) -> tuple[str | None, str | None]:
    """Resolve spoken text with verified acute stress marks. Never guess ambiguous stress."""
    p_lemma = plain(lemma)
    if not p_lemma:
        return None, "empty_lemma"

    # Monosyllable check: Ukrainian words with exactly one vowel have unambiguous stress
    vowels = "аеєиіїоуюя"
    is_cyrillic = bool(re.fullmatch(r"[а-щьюяєіїґ'-]+", p_lemma))
    vowel_count = sum(ch in vowels for ch in p_lemma)
    if is_cyrillic and vowel_count == 1:
        return p_lemma, None

    # Query oracle
    result = oracle(p_lemma, pos=pos)
    status = result.get("status")
    if status == "ok":
        matches = result.get("matches", [])
        if len(matches) == 1 and plain(matches[0].get("stressed_form", "")) == p_lemma:
            return matches[0]["stressed_form"], None
        return None, "multiple_matches"
    return None, status or "oracle_rejected"


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
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("downloaded model checksum mismatch")
            atomic_write(path, data)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"model checksum mismatch: {name}")
    return directory / "voice.onnx"


def scan_batch(
    items: list[dict[str, Any]],
    out_dir: Path,
    oracle: Callable[..., dict[str, Any]],
    shard: bool = True,
    limit: int = 0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Sort items into existing, pending, and excluded."""
    existing = []
    pending = []
    excluded = []

    seen = set()
    for item in items:
        raw_lemma = item.get("lemma") or item.get("lemmaPlain") or ""
        p_lemma = plain(raw_lemma)
        if not p_lemma or p_lemma in seen:
            continue
        seen.add(p_lemma)

        rel = audio_relpath(p_lemma, ext="opus", shard=shard)
        target = out_dir / rel
        if target.is_file() and target.stat().st_size >= 100:
            existing.append({"lemma": p_lemma, "relpath": rel, "bytes": target.stat().st_size})
            continue

        pos = item.get("pos")
        stressed_text, reason = resolve_stress(p_lemma, pos, oracle)
        if stressed_text is not None:
            pending.append({"lemma": p_lemma, "text": stressed_text, "relpath": rel, "pos": pos})
            if 0 < limit <= len(pending):
                break
        else:
            excluded.append({"lemma": p_lemma, "reason": reason})

    return existing, pending, excluded


def synthesize_batch(
    pending: list[dict[str, Any]],
    out_dir: Path,
    synthesize_wav_fn: Callable[[str, Path], None],
    bitrate: str = DEFAULT_BITRATE,
) -> list[dict[str, Any]]:
    """Synthesize speech to WAV, encode to Opus, and atomically place in output directory."""
    completed = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        wav_file = tmp_dir / "temp.wav"
        opus_file = tmp_dir / "temp.opus"

        for entry in pending:
            synthesize_wav_fn(entry["text"], wav_file)
            duration = validate_wav(wav_file)
            size = encode_opus(wav_file, opus_file, bitrate=bitrate)

            target = out_dir / entry["relpath"]
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(target, opus_file.read_bytes())

            completed.append(
                {
                    "lemma": entry["lemma"],
                    "text": entry["text"],
                    "relpath": entry["relpath"],
                    "bytes": size,
                    "seconds": round(duration, 3),
                }
            )
            wav_file.unlink(missing_ok=True)
            opus_file.unlink(missing_ok=True)

    return completed


def build_manifest(
    existing: list[dict[str, Any]],
    completed: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
    out_dir: Path,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Publish versioned manifest and manifest.json."""
    entries = {}
    for item in existing:
        entries[item["lemma"]] = {"file": item["relpath"], "bytes": item.get("bytes", 0)}
    for item in completed:
        entries[item["lemma"]] = {
            "file": item["relpath"],
            "text": item.get("text", ""),
            "bytes": item.get("bytes", 0),
            "seconds": item.get("seconds", 0.0),
        }

    manifest = {
        "schemaVersion": 1,
        "format": "ogg/opus",
        "bitrate": DEFAULT_BITRATE,
        "totalCount": len(entries),
        "existingCount": len(existing),
        "synthesizedCount": len(completed),
        "excludedCount": len(excluded),
        "engine": provenance,
        "excluded": excluded[:100],  # sample
        "entries": entries,
    }
    encoded = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    digest_hex = hashlib.sha256(encoded).hexdigest()
    atomic_write(out_dir / f"manifest-{digest_hex}.json", encoded)
    atomic_write(out_dir / "manifest.json", encoded)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch Piper Opus synthesis tool for Word Atlas and Practice Hub (#7873).\n"
        "Encodes 24 kbps mono OGG/Opus clips with deterministic lemma hashing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Input Atlas/lexicon manifest JSON",
    )
    parser.add_argument("--deck", type=Path, help="Input Practice deck JSON")
    parser.add_argument("--out-dir", type=Path, default=Path("batch_state/audio_opus"), help="Output directory")
    parser.add_argument("--limit", type=int, default=0, help="Max words to synthesize (0=unlimited)")
    parser.add_argument("--no-shard", action="store_true", help="Store files flat instead of 2-char prefix subdirs")
    parser.add_argument("--bitrate", default=DEFAULT_BITRATE, help="Opus bitrate (default: 24k)")
    parser.add_argument("--model-dir", type=Path, default=Path("batch_state/tts-model"), help="Model cache directory")
    parser.add_argument("--runtime-dir", type=Path, default=Path("batch_state/tts-runtime"), help="Runtime directory")
    parser.add_argument("--download-model", action="store_true", help="Download missing model files")
    parser.add_argument("--dry-run", action="store_true", help="Scan and report pending delta without synthesis")
    args = parser.parse_args()

    items = []
    if args.deck and args.deck.is_file():
        data = json.loads(args.deck.read_text())
        for e in data.get("lexemes", []):
            items.append({"lemma": e.get("lemmaPlain"), "pos": e.get("pos")})
    elif args.manifest and args.manifest.is_file():
        data = json.loads(args.manifest.read_text())
        raw_entries = data.get("entries", [])
        if isinstance(raw_entries, dict):
            for k, v in raw_entries.items():
                items.append({"lemma": k, "pos": v.get("pos") if isinstance(v, dict) else None})
        elif isinstance(raw_entries, list):
            for e in raw_entries:
                if isinstance(e, dict):
                    items.append({"lemma": e.get("lemma"), "pos": e.get("pos")})
    else:
        parser.error("Specify either --manifest or --deck (or ensure site/src/data/lexicon-manifest.json exists)")

    if args.runtime_dir.is_dir():
        sys.path.insert(0, str(args.runtime_dir.resolve()))

    from scripts.verification.stress import source_info, verify_stress

    shard = not args.no_shard
    existing, pending, excluded = scan_batch(items, args.out_dir, verify_stress, shard=shard, limit=args.limit)

    print(f"Total candidate words: {len(items)}")
    print(f"Already existing on disk: {len(existing)}")
    print(f"Pending synthesis: {len(pending)}")
    print(f"Excluded (ambiguous/unknown stress): {len(excluded)}")

    if args.dry_run:
        print("Dry-run complete. Exiting without synthesis.")
        return

    if not pending:
        print("No new words to synthesize.")
        return

    from piper import PiperVoice, SynthesisConfig

    model = ensure_model(args.model_dir, args.download_model)
    voice = PiperVoice.load(str(model))
    config = SynthesisConfig(speaker_id=0)

    def synth_wav(text: str, path: Path) -> None:
        unsupported = set(unicodedata.normalize("NFD", text)) - voice.config.phoneme_id_map.keys()
        if unsupported:
            raise ValueError(f"input has unsupported codepoints: {unsupported}")
        with wave.open(str(path), "wb") as wav:
            voice.synthesize_wav(text, wav, syn_config=config)

    provenance = {
        "name": "piper",
        "voice": VOICE,
        "speaker": "lada",
        "format": "ogg/opus",
        "bitrate": args.bitrate,
        "sharded": shard,
        "stressSource": source_info(),
    }

    print(f"Synthesizing {len(pending)} words to Opus...")
    completed = synthesize_batch(pending, args.out_dir, synth_wav, bitrate=args.bitrate)
    manifest = build_manifest(existing, completed, excluded, args.out_dir, provenance)
    print(f"Synthesized {len(completed)} clips successfully. Manifest published ({manifest['totalCount']} total).")


if __name__ == "__main__":
    main()
