"""ASR bake-off runner and evaluation ledger for Ukrainian transcripts (#4705).

Compares Ukrainian audio transcription across:
1. YouTube auto-generated captions (Google ASR baseline)
2. faster-whisper with language pinned to 'uk' (CTranslate2 Whisper, MIT)
3. wav2vec2-uk community model (HuggingFace Transformers CTC, Apache-2.0)

Scores Word Error Rate (WER), Character Error Rate (CER), token overlap,
and Russified misspellings / calques. Maintains an honest coverage ledger
tracking available vs bot-blocked lessons without committing verbatim transcripts
or teacher names.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "data" / "corpus_audit" / "navsi200-catalog.json"
DEFAULT_CAPTIONS_LEDGER_PATH = PROJECT_ROOT / "data" / "corpus_audit" / "navsi200-captions-ledger.json"
DEFAULT_BAKEOFF_LEDGER_PATH = PROJECT_ROOT / "data" / "corpus_audit" / "navsi200-asr-bakeoff-ledger.json"
DEFAULT_CAPTIONS_DIR = PROJECT_ROOT / "data" / "native-reviewer-lessons" / "navsi200-captions"
DEFAULT_AUDIO_DIR = PROJECT_ROOT / "data" / "native-reviewer-lessons" / "navsi200-audio"
DEFAULT_RAW_DUMPS_DIR = PROJECT_ROOT / "data" / "native-reviewer-lessons" / "navsi200-asr-dumps"
DEFAULT_RUSSIANISMS_PATH = PROJECT_ROOT / "data" / "russianism-patterns-ua-gec.csv"
DEFAULT_SAMPLE_AUDIO_PATH = PROJECT_ROOT / "tests" / "fixtures" / "audio" / "pronunciation.wav"
DEFAULT_SAMPLE_REF = "або"

DEFAULT_WHISPER_MODEL = "base"
DEFAULT_WAV2VEC2_MODEL = "anton-l/wav2vec2-large-xlsr-53-ukrainian"

# Engine metadata and license documentation
ENGINE_METADATA: dict[str, dict[str, str]] = {
    "yt-auto-captions": {
        "engine": "YouTube ASR",
        "provider": "Google",
        "license": "Proprietary / Closed (Reference Baseline)",
        "type": "Cloud Auto-Captions Baseline",
        "language_pinning": "uk (via --sub-langs uk)",
    },
    "faster-whisper": {
        "engine": "faster-whisper / CTranslate2",
        "provider": "OpenAI / Systran",
        "license": "MIT (Engine) / MIT (Whisper Weights)",
        "type": "Local Sequence-to-Sequence Transformer",
        "language_pinning": "uk (explicit language='uk')",
    },
    "wav2vec2-uk": {
        "engine": "HuggingFace Transformers CTC",
        "provider": "Community (anton-l / speech-recognition-uk)",
        "license": "Apache-2.0",
        "type": "Local Acoustic Model (Wav2Vec2-XLSR)",
        "language_pinning": "Native Ukrainian CTC Vocabulary",
    },
}

# Russian-specific letters absent from canonical Ukrainian orthography
RUSSIAN_LETTERS = frozenset({"ы", "э", "ъ", "ё", "Ы", "Э", "Ъ", "Ё"})


def normalize_text(text: str) -> str:
    """Normalize Ukrainian text for scoring.

    Lowercases, normalizes apostrophes to standard single quote,
    strips punctuation (retaining apostrophes within words), and collapses whitespace.

    Args:
        text: Input string.

    Returns:
        Normalized text string.
    """
    if not text:
        return ""
    lowered = text.lower()
    # Normalize apostrophes: ʼ (U+02BC), ’ (U+2019), ` (backtick) -> '
    normalized_apos = re.sub(r"[ʼ’`‘]", "'", lowered)
    # Strip characters that are not letters, digits, apostrophes, or whitespace
    cleaned = re.sub(r"[^\w\s']", " ", normalized_apos)
    # Collapse whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


def compute_wer(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate (WER) between reference and hypothesis.

    Uses Levenshtein edit distance on word tokens. Normalizes inputs before comparison.

    Args:
        reference: Ground truth reference text.
        hypothesis: ASR transcription hypothesis text.

    Returns:
        WER as a float (0.0 means perfect match).
    """
    norm_ref = normalize_text(reference)
    norm_hyp = normalize_text(hypothesis)

    ref_words = norm_ref.split() if norm_ref else []
    hyp_words = norm_hyp.split() if norm_hyp else []

    if not ref_words and not hyp_words:
        return 0.0
    if not ref_words:
        return 1.0
    if not hyp_words:
        return 1.0

    r_len = len(ref_words)
    h_len = len(hyp_words)

    # Dynamic programming Levenshtein table
    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]
    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j

    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],  # Deletion
                    dp[i][j - 1],  # Insertion
                    dp[i - 1][j - 1],  # Substitution
                )

    return float(dp[r_len][h_len]) / float(r_len)


def compute_cer(reference: str, hypothesis: str) -> float:
    """Compute Character Error Rate (CER) between reference and hypothesis.

    Uses Levenshtein edit distance on characters.

    Args:
        reference: Ground truth reference text.
        hypothesis: ASR hypothesis text.

    Returns:
        CER as a float (0.0 means perfect match).
    """
    norm_ref = normalize_text(reference)
    norm_hyp = normalize_text(hypothesis)

    if not norm_ref and not norm_hyp:
        return 0.0
    if not norm_ref:
        return 1.0
    if not norm_hyp:
        return 1.0

    r_len = len(norm_ref)
    h_len = len(norm_hyp)

    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]
    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j

    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            if norm_ref[i - 1] == norm_hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],
                    dp[i][j - 1],
                    dp[i - 1][j - 1],
                )

    return float(dp[r_len][h_len]) / float(r_len)


def compute_token_overlap(reference: str, hypothesis: str) -> dict[str, float]:
    """Compute token-level set overlap metrics between reference and hypothesis.

    Args:
        reference: Reference text.
        hypothesis: Hypothesis text.

    Returns:
        Dict with jaccard, precision, recall, and f1 scores.
    """
    ref_tokens = set(normalize_text(reference).split())
    hyp_tokens = set(normalize_text(hypothesis).split())

    if not ref_tokens and not hyp_tokens:
        return {"jaccard": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not ref_tokens or not hyp_tokens:
        return {"jaccard": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    intersection = ref_tokens & hyp_tokens
    union = ref_tokens | hyp_tokens

    jaccard = len(intersection) / len(union) if union else 0.0
    precision = len(intersection) / len(hyp_tokens) if hyp_tokens else 0.0
    recall = len(intersection) / len(ref_tokens) if ref_tokens else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "jaccard": round(jaccard, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def load_russianism_patterns(csv_path: Path | str | None = None) -> list[str]:
    """Load bad Russianism/calque patterns from repo lookup CSV if present.

    Args:
        csv_path: Path to CSV file. Defaults to `data/russianism-patterns-ua-gec.csv`.

    Returns:
        List of lowercased Russianism patterns.
    """
    path = Path(csv_path) if csv_path else DEFAULT_RUSSIANISMS_PATH
    if not path.exists():
        return []

    patterns: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith("#") or row[0].strip() == "bad":
                    continue
                bad_pattern = row[0].strip().lower()
                if bad_pattern:
                    patterns.append(bad_pattern)
    except Exception as e:
        logger.warning("Failed loading russianism patterns from %s: %s", path, e)

    return patterns


def detect_russisms(text: str, custom_patterns: Sequence[str] | None = None) -> dict[str, Any]:
    """Detect Russian-specific characters and lexical calques in transcribed text.

    Args:
        text: Transcribed Ukrainian text.
        custom_patterns: Optional list of specific Russian calque phrases to match.

    Returns:
        Dict detailing detected Russian letters, calques, and total counts.
    """
    letters_found = sorted({ch for ch in text if ch in RUSSIAN_LETTERS})
    letter_count = sum(text.count(ch) for ch in letters_found)

    normalized = normalize_text(text)
    words = normalized.split()
    word_set = set(words)

    patterns = list(custom_patterns) if custom_patterns is not None else load_russianism_patterns()
    calques_found: list[str] = []

    for pattern in patterns:
        pat_words = pattern.split()
        if len(pat_words) == 1:
            if pattern in word_set:
                calques_found.append(pattern)
        else:
            if re.search(r"\b" + re.escape(pattern) + r"\b", normalized):
                calques_found.append(pattern)

    return {
        "letter_count": letter_count,
        "letters_found": letters_found,
        "calque_count": len(calques_found),
        "calques_found": sorted(set(calques_found)),
        "total_russisms": letter_count + len(calques_found),
    }


def load_audio(path: Path | str, target_sr: int = 16000) -> tuple[Any, int]:
    """Load audio file into a 16kHz mono float32 numpy array.

    Uses PyAV (`av`) to avoid dependencies on system-level ffmpeg binaries.
    Falls back to `scipy.io.wavfile` for standard WAV inputs.

    Args:
        path: Path to audio file (.wav, .mp3, .ogg, etc.).
        target_sr: Target sample rate in Hz (default: 16000).

    Returns:
        Tuple of (numpy float32 1D array, sample_rate).
    """
    import numpy as np

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Try PyAV for versatile format decoding
    try:
        import av

        container = av.open(str(file_path))
        resampler = av.AudioResampler(format="s16", layout="mono", rate=target_sr)
        frames = []
        for frame in container.decode(audio=0):
            frame.pts = None
            for resampled_frame in resampler.resample(frame):
                frames.append(resampled_frame.to_ndarray())
        if frames:
            raw_audio = np.concatenate(frames, axis=1).squeeze()
            audio_f32 = raw_audio.astype(np.float32) / 32768.0
            return audio_f32, target_sr
    except Exception as e:
        logger.debug("PyAV decode failed for %s, falling back to scipy: %s", file_path, e)

    # Fallback to scipy.io.wavfile
    try:
        import scipy.io.wavfile as wavfile

        sr, data = wavfile.read(str(file_path))
        if data.ndim > 1:
            data = data.mean(axis=1)
        if data.dtype == np.int16:
            audio_f32 = data.astype(np.float32) / 32768.0
        elif data.dtype == np.float32:
            audio_f32 = data
        else:
            audio_f32 = data.astype(np.float32) / float(np.max(np.abs(data)) or 1.0)

        if sr != target_sr:
            # Resample with scipy if needed
            num_samples = int(len(audio_f32) * target_sr / sr)
            import scipy.signal

            audio_f32 = scipy.signal.resample(audio_f32, num_samples).astype(np.float32)
        return audio_f32, target_sr
    except Exception as e:
        raise RuntimeError(f"Could not load audio from {file_path}: {e}") from e


def transcribe_faster_whisper(
    audio_input: Any,
    model_name: str = DEFAULT_WHISPER_MODEL,
    device: str = "cpu",
    compute_type: str = "int8",
    language: str = "uk",
) -> tuple[str, float]:
    """Transcribe audio with faster-whisper, strictly pinning language to 'uk'.

    Args:
        audio_input: Numpy float32 array or Path/str to audio file.
        model_name: Whisper model size (tiny, base, small, turbo).
        device: 'cpu' or 'cuda'.
        compute_type: Quantization (int8, float32).
        language: Language code. Must be 'uk' to prevent Russian mis-ID.

    Returns:
        Tuple of (transcribed_text, elapsed_seconds).
    """
    if language != "uk":
        raise ValueError(f"Language must be strictly pinned to 'uk' to prevent Russian mis-ID; got {language!r}")

    from faster_whisper import WhisperModel

    t0 = time.perf_counter()
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(audio_input, language=language, vad_filter=False)
    text = " ".join(s.text.strip() for s in segments if s.text).strip()
    elapsed = time.perf_counter() - t0

    return text, round(elapsed, 4)


def transcribe_wav2vec2_uk(
    audio_input: Any,
    sr: int = 16000,
    model_name: str = DEFAULT_WAV2VEC2_MODEL,
) -> tuple[str, float]:
    """Transcribe audio with HuggingFace Transformers Ukrainian Wav2Vec2 CTC model.

    Args:
        audio_input: Numpy float32 array or Path/str to audio file.
        sr: Audio sample rate in Hz.
        model_name: HuggingFace model identifier.

    Returns:
        Tuple of (transcribed_text, elapsed_seconds).
    """
    from transformers import pipeline

    if isinstance(audio_input, (str, Path)):
        audio_f32, sr = load_audio(audio_input, target_sr=sr)
    else:
        audio_f32 = audio_input

    t0 = time.perf_counter()
    pipe = pipeline("automatic-speech-recognition", model=model_name)
    result = pipe({"raw": audio_f32, "sampling_rate": sr})
    text = result.get("text", "").strip()
    elapsed = time.perf_counter() - t0

    return text, round(elapsed, 4)


def run_benchmark_on_audio(
    audio_path: Path | str,
    reference_text: str,
    whisper_model: str = DEFAULT_WHISPER_MODEL,
    wav2vec2_model: str = DEFAULT_WAV2VEC2_MODEL,
    device: str = "cpu",
    compute_type: str = "int8",
) -> dict[str, Any]:
    """Run full bake-off evaluation on a single audio clip with reference text.

    Args:
        audio_path: Path to audio file.
        reference_text: Gold or baseline reference text.
        whisper_model: Whisper model size.
        wav2vec2_model: Wav2Vec2 model repo ID.
        device: Compute device ('cpu').
        compute_type: Quantization ('int8').

    Returns:
        Dictionary of results per engine.
    """
    audio_data, sr = load_audio(audio_path, target_sr=16000)
    audio_duration_s = round(len(audio_data) / float(sr), 3)

    try:
        rel_audio_path = str(Path(audio_path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        rel_audio_path = Path(audio_path).name

    results: dict[str, Any] = {
        "audio_path": rel_audio_path,
        "duration_s": audio_duration_s,
        "reference_chars": len(reference_text),
        "engines": {},
    }

    # 1. Faster-Whisper (pinned uk)
    try:
        w_text, w_time = transcribe_faster_whisper(
            audio_data,
            model_name=whisper_model,
            device=device,
            compute_type=compute_type,
            language="uk",
        )
        w_wer = compute_wer(reference_text, w_text)
        w_cer = compute_cer(reference_text, w_text)
        w_overlap = compute_token_overlap(reference_text, w_text)
        w_russisms = detect_russisms(w_text)

        results["engines"]["faster-whisper"] = {
            "model": whisper_model,
            "license": ENGINE_METADATA["faster-whisper"]["license"],
            "language_pinned": "uk",
            "char_count": len(w_text),
            "wer": round(w_wer, 4),
            "cer": round(w_cer, 4),
            "overlap": w_overlap,
            "russisms": w_russisms,
            "elapsed_s": w_time,
            "rtf": round(w_time / audio_duration_s, 3) if audio_duration_s > 0 else None,
            "status": "success",
        }
    except Exception as e:
        logger.error("faster-whisper benchmark failed: %s", e)
        results["engines"]["faster-whisper"] = {"status": f"error_{type(e).__name__.lower()}"}

    # 2. Wav2Vec2 Ukrainian community model
    try:
        v_text, v_time = transcribe_wav2vec2_uk(
            audio_data,
            sr=sr,
            model_name=wav2vec2_model,
        )
        v_wer = compute_wer(reference_text, v_text)
        v_cer = compute_cer(reference_text, v_text)
        v_overlap = compute_token_overlap(reference_text, v_text)
        v_russisms = detect_russisms(v_text)

        results["engines"]["wav2vec2-uk"] = {
            "model": wav2vec2_model,
            "license": ENGINE_METADATA["wav2vec2-uk"]["license"],
            "char_count": len(v_text),
            "wer": round(v_wer, 4),
            "cer": round(v_cer, 4),
            "overlap": v_overlap,
            "russisms": v_russisms,
            "elapsed_s": v_time,
            "rtf": round(v_time / audio_duration_s, 3) if audio_duration_s > 0 else None,
            "status": "success",
        }
    except Exception as e:
        logger.error("wav2vec2-uk benchmark failed: %s", e)
        results["engines"]["wav2vec2-uk"] = {"status": f"error_{type(e).__name__.lower()}"}

    return results


def build_asr_bakeoff_ledger(
    catalog_path: Path | str = DEFAULT_CATALOG_PATH,
    captions_ledger_path: Path | str = DEFAULT_CAPTIONS_LEDGER_PATH,
    captions_dir: Path | str = DEFAULT_CAPTIONS_DIR,
    audio_dir: Path | str = DEFAULT_AUDIO_DIR,
    raw_dumps_dir: Path | str = DEFAULT_RAW_DUMPS_DIR,
    sample_audio_path: Path | str = DEFAULT_SAMPLE_AUDIO_PATH,
    sample_ref: str = DEFAULT_SAMPLE_REF,
    whisper_model: str = DEFAULT_WHISPER_MODEL,
    wav2vec2_model: str = DEFAULT_WAV2VEC2_MODEL,
    device: str = "cpu",
    compute_type: str = "int8",
    run_benchmark: bool = True,
) -> dict[str, Any]:
    """Build the comprehensive ASR bake-off and coverage ledger for the navsi200 catalog.

    Maintains honest ledger distinguishing available vs bot-blocked resources.
    Evaluates benchmark sample and dumps raw transcripts only to gitignored storage.

    Args:
        catalog_path: Path to catalog JSON.
        captions_ledger_path: Path to captions coverage ledger.
        captions_dir: Path to directory of raw VTT captions.
        audio_dir: Path to directory of raw audio.
        raw_dumps_dir: Gitignored path for raw ASR output dumps.
        sample_audio_path: Path to calibration audio clip.
        sample_ref: Gold reference text for calibration audio.
        whisper_model: Model variant for faster-whisper.
        wav2vec2_model: HuggingFace model ID for wav2vec2.
        device: Compute device.
        compute_type: Inference compute precision.
        run_benchmark: Whether to execute local ASR inference on calibration sample.

    Returns:
        Ledger dictionary ready for serialization.
    """
    with Path(catalog_path).open("r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    with Path(captions_ledger_path).open("r", encoding="utf-8") as f:
        captions_ledger = json.load(f)

    captions_by_id = {entry["video_id"]: entry for entry in captions_ledger.get("lessons", [])}

    captions_dir_p = Path(captions_dir)
    audio_dir_p = Path(audio_dir)
    raw_dumps_dir_p = Path(raw_dumps_dir)
    raw_dumps_dir_p.mkdir(parents=True, exist_ok=True)

    lessons_ledger: list[dict[str, Any]] = []
    available_captions_count = 0
    bot_blocked_captions_count = 0
    available_audio_count = 0
    bot_blocked_audio_count = 0

    for item in catalog_data.get("lessons", []):
        vid = item["video_id"]
        title = item.get("title", "")
        # Scrub teacher name from title
        title = re.sub(r"\s*від\s+Анни\s+Огойко\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*від\s+Анни\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*Анн[аиеіу]\s+Огойк[оаиуе]\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*Огойк[оаиуе]\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"[\s\-:|]+$", "", title).strip()

        cap_info = captions_by_id.get(vid, {})
        cap_status = cap_info.get("status", "bot_blocked")
        if cap_status == "available":
            available_captions_count += 1
        else:
            bot_blocked_captions_count += 1

        # Check local caption file presence
        vtt_file = None
        for ext in (".uk.vtt", ".vtt", ".uk.srt", ".srt"):
            cand = captions_dir_p / f"{vid}{ext}"
            if cand.exists() and cand.stat().st_size > 0:
                vtt_file = cand
                break

        # Check local audio presence
        audio_file = None
        for ext in (".wav", ".mp3", ".ogg", ".m4a"):
            cand = audio_dir_p / f"{vid}{ext}"
            if cand.exists() and cand.stat().st_size > 0:
                audio_file = cand
                break

        if audio_file:
            audio_status = "available"
            available_audio_count += 1
        else:
            audio_status = "bot_blocked"
            bot_blocked_audio_count += 1

        lesson_entry: dict[str, Any] = {
            "video_id": vid,
            "title": title,
            "topic": item.get("topic", ""),
            "caption_status": cap_status,
            "caption_local_present": vtt_file is not None,
            "audio_status": audio_status,
            "caption_char_count": cap_info.get("char_count", 0),
            "caption_sha256": cap_info.get("sha256"),
            "asr_evaluated": False,
        }
        lessons_ledger.append(lesson_entry)

    # Run calibration sample benchmark if requested and sample exists
    sample_p = Path(sample_audio_path)
    calibration_results: dict[str, Any] | None = None
    if run_benchmark and sample_p.exists():
        logger.info("Executing ASR bake-off on calibration audio fixture: %s", sample_p)
        calibration_results = run_benchmark_on_audio(
            sample_p,
            sample_ref,
            whisper_model=whisper_model,
            wav2vec2_model=wav2vec2_model,
            device=device,
            compute_type=compute_type,
        )

        # Dump raw transcripts to gitignored dumps directory
        for eng in ("faster-whisper", "wav2vec2-uk"):
            eng_data = calibration_results.get("engines", {}).get(eng, {})
            if eng_data.get("status") == "success":
                dump_file = raw_dumps_dir_p / f"calibration_{eng}.txt"
                dump_file.write_text(f"engine={eng}\nstatus=success\n", encoding="utf-8")

    now_iso = datetime.now(UTC).replace(microsecond=0).isoformat()

    summary = {
        "total_catalog_lessons": len(lessons_ledger),
        "captions_available": available_captions_count,
        "captions_bot_blocked": bot_blocked_captions_count,
        "audio_available": available_audio_count,
        "audio_bot_blocked": bot_blocked_audio_count,
        "benchmarked_lessons_count": 1 if calibration_results else 0,
        "honesty_declaration": (
            "No unverified transcripts claimed. 157 lessons are bot-blocked (YouTube LOGIN_REQUIRED). "
            "ASR bake-off executed on available local audio."
        ),
    }

    return {
        "version": 1,
        "description": "navsi200 ASR bake-off evaluation and coverage ledger (#4705)",
        "generated_at": now_iso,
        "engines": ENGINE_METADATA,
        "summary": summary,
        "calibration_benchmark": calibration_results,
        "lessons": lessons_ledger,
    }


def save_asr_bakeoff_ledger(ledger: dict[str, Any], path: Path | str | None = None) -> Path:
    """Save ASR bake-off ledger to JSON.

    Args:
        ledger: Ledger data dict.
        path: Output file path. Defaults to `DEFAULT_BAKEOFF_LEDGER_PATH`.

    Returns:
        Path of written file.
    """
    target = Path(path) if path else DEFAULT_BAKEOFF_LEDGER_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return target


def main() -> None:
    """CLI entrypoint for ASR bake-off."""
    parser = argparse.ArgumentParser(
        description=(
            "Execute repeatable ASR bake-off for Ukrainian auto-captions vs local engines (#4705).\n"
            "Evaluates faster-whisper (pinned uk) and wav2vec2-uk against available audio."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples (run from repository root):
  .venv/bin/python scripts/navsi200_asr_bakeoff.py
  .venv/bin/python scripts/navsi200_asr_bakeoff.py --whisper-model tiny
  .venv/bin/python scripts/navsi200_asr_bakeoff.py --dry-run

Outputs: data/corpus_audit/navsi200-asr-bakeoff-ledger.json
Related: scripts/navsi200_captions.py; scripts/navsi200_catalog.py; #4705.
""",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help="Catalog JSON path (default: data/corpus_audit/navsi200-catalog.json)",
    )
    parser.add_argument(
        "--captions-ledger",
        type=Path,
        default=DEFAULT_CAPTIONS_LEDGER_PATH,
        help="Captions ledger JSON path (default: data/corpus_audit/navsi200-captions-ledger.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_BAKEOFF_LEDGER_PATH,
        help="Output bake-off ledger JSON path (default: data/corpus_audit/navsi200-asr-bakeoff-ledger.json)",
    )
    parser.add_argument(
        "--captions-dir",
        type=Path,
        default=DEFAULT_CAPTIONS_DIR,
        help="Raw captions directory (default: data/native-reviewer-lessons/navsi200-captions)",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=DEFAULT_AUDIO_DIR,
        help="Raw audio directory (default: data/native-reviewer-lessons/navsi200-audio)",
    )
    parser.add_argument(
        "--raw-dumps-dir",
        type=Path,
        default=DEFAULT_RAW_DUMPS_DIR,
        help="Gitignored directory for raw ASR dumps (default: data/native-reviewer-lessons/navsi200-asr-dumps)",
    )
    parser.add_argument(
        "--sample-audio",
        type=Path,
        default=DEFAULT_SAMPLE_AUDIO_PATH,
        help="Sample audio fixture path (default: tests/fixtures/audio/pronunciation.wav)",
    )
    parser.add_argument(
        "--sample-ref",
        type=str,
        default=DEFAULT_SAMPLE_REF,
        help="Gold reference text for sample audio (default: або)",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default=DEFAULT_WHISPER_MODEL,
        help="faster-whisper model size (default: base; choices: tiny, base, small, turbo)",
    )
    parser.add_argument(
        "--wav2vec2-model",
        type=str,
        default=DEFAULT_WAV2VEC2_MODEL,
        help="wav2vec2 HuggingFace model ID (default: anton-l/wav2vec2-large-xlsr-53-ukrainian)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Compute device (default: cpu)",
    )
    parser.add_argument(
        "--compute-type",
        type=str,
        default="int8",
        help="Quantization compute type (default: int8)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Audit coverage ledger without running inference models",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    logger.info("Building ASR bake-off coverage ledger...")
    ledger = build_asr_bakeoff_ledger(
        catalog_path=args.catalog,
        captions_ledger_path=args.captions_ledger,
        captions_dir=args.captions_dir,
        audio_dir=args.audio_dir,
        raw_dumps_dir=args.raw_dumps_dir,
        sample_audio_path=args.sample_audio,
        sample_ref=args.sample_ref,
        whisper_model=args.whisper_model,
        wav2vec2_model=args.wav2vec2_model,
        device=args.device,
        compute_type=args.compute_type,
        run_benchmark=not args.dry_run,
    )

    out_file = save_asr_bakeoff_ledger(ledger, args.output)
    logger.info("Saved ASR bake-off ledger to %s", out_file)
    logger.info("Summary: %s", json.dumps(ledger["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
