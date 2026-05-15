"""Bulk OCR ESUM JP2 scans with Gemini Flash.

This runner is intentionally idempotent:
- archives are extracted only when the expected JP2 files are missing,
- JP2 pages are decoded only when the matching PNG is missing or empty,
- Gemini OCR is called only when the per-page Markdown output is missing.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
RAW_ESUM = ROOT / "data/raw/esum"
JP2_STAGING = RAW_ESUM / "jp2-staging"
OCR_DIR = RAW_ESUM / "gemini-ocr"
DEFAULT_PROMPT = ROOT / "audit/etymology-ocr-feasibility/prompts/transcription-v1.txt"
DEFAULT_LOG = ROOT / "audit/etymology-ocr-feasibility/bulk-run-log.jsonl"
GEMINI_TMP_DIR = ROOT / "gemini_ocr_images"
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_CONCURRENCY = 10
DEFAULT_RPM = 15
ROLLING_WINDOW = 100
ROLLING_ERROR_LIMIT = 20

ZIP_RE = re.compile(r"etslukrmov(\d+)_jp2\.zip$")
PAGE_RE = re.compile(r"_(\d+)\.jp2$", re.IGNORECASE)
ONLY_RE = re.compile(r"^vol(\d+)/p(\d{1,4})$")

DAILY_QUOTA_RE = re.compile(
    r"Quota exceeded for quota metric.*(?:Daily|PerDay)"
    r"|RESOURCE_EXHAUSTED.*daily"
    r"|requests_per_day"
    r"|PERMISSION_DENIED"
    r"|invalid_grant"
    # Observed in 2026-05-15 Gemini CLI 0.42 free-tier hit:
    #   "TerminalQuotaError: You have exhausted your capacity on this model.
    #    Your quota will reset after 19h25m58s."
    # The multi-hour reset window indicates daily quota; "TerminalQuotaError" /
    # "QUOTA_EXHAUSTED" are the @google/gemini-cli classifyGoogleError tags.
    r"|TerminalQuotaError"
    r"|QUOTA_EXHAUSTED"
    r"|quota will reset after \d+h",
    re.IGNORECASE | re.DOTALL,
)
RPM_RE = re.compile(r"RequestsPerMinute|60s", re.IGNORECASE)
TRANSIENT_RE = re.compile(
    r"HTTP\s*5\d\d|(?:^|\D)5\d\d(?:\D|$)|network timeout|timed out|UNAVAILABLE|INTERNAL"
    r"|ECONNRESET|ETIMEDOUT"
    # Gemini free-tier server-side capacity issues (observed 2026-05-15 run #7+#8):
    # The composite router emits "No capacity available for model X" when all
    # variants are overloaded; retrying after backoff usually succeeds.
    r"|No capacity available"
    # The streaming response parser fails intermittently with "Invalid stream"
    # / "Invalid chunk" — pure server-side transient.
    r"|Invalid (?:stream|chunk|response)"
    # Internal retry inside gemini-cli exhausted; one more script-level retry
    # sometimes recovers because the server-side state changes between attempts.
    r"|Retry attempts exhausted"
    # 429 / RESOURCE_EXHAUSTED when NOT daily (DAILY_QUOTA_RE catches the
    # multi-hour-reset case first). Account-level burst rate-limit recovers
    # within seconds; backoff is enough.
    r"|\b429\b|RESOURCE_EXHAUSTED(?!.*daily)|\brate[- ]?limit"
    # Silent failure: gemini-cli exits 0 with only the --allowed-tools
    # deprecation warning + YOLO mode message + Ripgrep notice on stderr, and
    # no usable output. is_low_quality_output() catches the output side; this
    # regex lets classify_error see the deprecation-only stderr and route to
    # transient retry. ~13% of stderr observed in run #8 is this pattern.
    r"|allowed-tools.*deprecated",
    re.IGNORECASE,
)
IMAGE_REFUSAL_RE = re.compile(
    r"cannot\s+(?:directly\s+)?(?:see|view|access|read).*image"
    r"|unable to access the image file"
    r"|unable to locate or read the file"
    r"|unable to perform OCR on local image files"
    r"|outside my permitted workspace"
    r"|provide the text content of the page"
    r"|update_topic\("
    r"|saved in `?transcription\.txt",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class Volume:
    number: int
    zip_path: Path
    extract_dir: Path
    jp2_members: tuple[str, ...]

    @property
    def expected_jp2_count(self) -> int:
        return len(self.jp2_members)


@dataclass(frozen=True)
class Page:
    vol: int
    idx: int
    jp2_path: Path
    png_path: Path
    md_path: Path

    @property
    def key(self) -> str:
        return f"vol{self.vol}/p{self.idx:04d}"


@dataclass
class PageResult:
    status: str
    page: Page
    duration_s: float = 0.0
    retries: int = 0
    stderr_tail: str = ""


@dataclass
class RunStats:
    total: int
    ok: int = 0
    error: int = 0
    quota_halt: bool = False
    quality_halt: bool = False
    last_successful_page: str | None = None
    consecutive_quota_errors: int = 0
    duration_s: float = 0.0


class JsonlLogger:
    def __init__(self, path: Path, dry_run: bool = False) -> None:
        self.path = path
        self.dry_run = dry_run
        self._lock = asyncio.Lock()

    async def write(self, event: dict[str, object]) -> None:
        if self.dry_run:
            return
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        async with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")


class RateLimiter:
    def __init__(self, rpm: int) -> None:
        self.rpm = rpm
        self.starts: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def wait_for_slot(self, page: Page) -> None:
        if self.rpm <= 0:
            return

        while True:
            async with self._lock:
                now = time.monotonic()
                while self.starts and now - self.starts[0] >= 60:
                    self.starts.popleft()
                if len(self.starts) < self.rpm:
                    self.starts.append(now)
                    return
                sleep_s = max(0.1, 60 - (now - self.starts[0]) + 0.1)

            print(f"rate-limit {page.key} sleep={sleep_s:.1f}s", flush=True)
            await sleep_with_heartbeat(sleep_s, f"rate-limit {page.key}")


def _safe_print(message: str, *, file: object | None = None) -> None:
    try:
        print(message, file=file or sys.stdout, flush=True)
    except BrokenPipeError:
        raise SystemExit(0) from None


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _tail(text: str, limit: int = 2000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _has_content(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def parse_only(raw_only: str | None) -> set[tuple[int, int]] | None:
    if not raw_only:
        return None
    selected: set[tuple[int, int]] = set()
    for raw_part in raw_only.split(","):
        part = raw_part.strip()
        if not part:
            continue
        match = ONLY_RE.match(part)
        if not match:
            raise ValueError(f"Invalid --only page {part!r}; expected volN/pNNNN")
        selected.add((int(match.group(1)), int(match.group(2))))
    return selected


def page_index(path: str | Path) -> int:
    name = path.name if isinstance(path, Path) else PurePosixPath(path).name
    match = PAGE_RE.search(name)
    if not match:
        raise ValueError(f"Cannot parse page number from {name!r}")
    return int(match.group(1))


def discover_volumes() -> list[Volume]:
    volumes: list[Volume] = []
    for zip_path in sorted(JP2_STAGING.glob("etslukrmov*_jp2.zip")):
        match = ZIP_RE.match(zip_path.name)
        if not match:
            continue
        try:
            with zipfile.ZipFile(zip_path) as zf:
                jp2_members = tuple(sorted(name for name in zf.namelist() if name.lower().endswith(".jp2")))
        except zipfile.BadZipFile as exc:
            raise RuntimeError(f"Bad ZIP archive {_rel(zip_path)}; redownload or resume this archive") from exc
        if not jp2_members:
            raise RuntimeError(f"No JP2 members found in {_rel(zip_path)}")
        roots = {PurePosixPath(member).parts[0] for member in jp2_members}
        if len(roots) != 1:
            raise RuntimeError(f"Expected one root directory in {_rel(zip_path)}, found {sorted(roots)}")
        extract_dir = JP2_STAGING / next(iter(roots))
        volumes.append(
            Volume(
                number=int(match.group(1)),
                zip_path=zip_path,
                extract_dir=extract_dir,
                jp2_members=jp2_members,
            )
        )
    if not volumes:
        raise RuntimeError(f"No ESUM JP2 ZIPs found in {_rel(JP2_STAGING)}")
    return volumes


def collect_pages(volumes: list[Volume], selected: set[tuple[int, int]] | None = None) -> list[Page]:
    pages: list[Page] = []
    for volume in volumes:
        if selected and all(vol != volume.number for vol, _idx in selected):
            continue

        if volume.extract_dir.exists():
            jp2_paths = sorted(volume.extract_dir.rglob("*.jp2"), key=page_index)
        else:
            jp2_paths = [JP2_STAGING / member for member in sorted(volume.jp2_members, key=page_index)]

        for jp2_path in jp2_paths:
            idx = page_index(jp2_path)
            if selected and (volume.number, idx) not in selected:
                continue
            md_path = OCR_DIR / f"vol{volume.number}" / f"p{idx:04d}.md"
            pages.append(Page(volume.number, idx, jp2_path, jp2_path.with_suffix(".png"), md_path))
    return sorted(pages, key=lambda page: (page.vol, page.idx))


def count_existing_jp2(volume: Volume) -> int:
    if not volume.extract_dir.exists():
        return 0
    return sum(1 for path in volume.extract_dir.rglob("*.jp2") if _has_content(path))


def extract_archives(volumes: list[Volume]) -> None:
    for volume in volumes:
        existing = count_existing_jp2(volume)
        total = volume.expected_jp2_count
        if existing >= total:
            _safe_print(f"extracting vol{volume.number} skip-existing ({existing}/{total})")
            continue

        with zipfile.ZipFile(volume.zip_path) as zf:
            for i, member in enumerate(volume.jp2_members, start=1):
                target = JP2_STAGING / member
                if not _has_content(target):
                    zf.extract(member, JP2_STAGING)
                if i == 1 or i == total or i % 20 == 0:
                    _safe_print(f"extracting vol{volume.number} ({i}/{total})")

        extracted = count_existing_jp2(volume)
        if extracted < total:
            raise RuntimeError(
                f"Extraction incomplete for vol{volume.number}: expected {total} JP2 files, found {extracted}"
            )


def decode_pages(pages: list[Page]) -> None:
    total = len(pages)
    for i, page in enumerate(pages, start=1):
        if _has_content(page.png_path):
            _safe_print(f"decoded {page.key} skip-existing ({i}/{total})")
            continue

        page.png_path.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        proc = subprocess.run(
            ["opj_decompress", "-i", str(page.jp2_path), "-o", str(page.png_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        duration = time.monotonic() - started
        if proc.returncode != 0 or not _has_content(page.png_path):
            raise RuntimeError(
                f"opj_decompress failed for {page.key} rc={proc.returncode} stderr={_tail(proc.stderr)!r}"
            )
        _safe_print(f"decoded {page.key} ({i}/{total}) duration={duration:.1f}s")


async def sleep_with_heartbeat(seconds: float, label: str) -> None:
    remaining = float(seconds)
    while remaining > 0:
        interval = min(30.0, remaining)
        await asyncio.sleep(interval)
        remaining -= interval
        if remaining > 0:
            _safe_print(f"{label} waiting remaining={remaining:.1f}s")


async def communicate_with_heartbeat(
    proc: asyncio.subprocess.Process,
    page: Page,
    prompt_text: str,
    attempt: int,
) -> tuple[bytes, bytes]:
    started = time.monotonic()
    task = asyncio.create_task(proc.communicate(input=prompt_text.encode("utf-8")))
    try:
        while not task.done():
            done, _pending = await asyncio.wait({task}, timeout=30)
            if not done:
                elapsed = time.monotonic() - started
                _safe_print(f"ocr {page.key} running attempt={attempt} elapsed={elapsed:.1f}s")
        return await task
    except asyncio.CancelledError:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except TimeoutError:
                proc.kill()
                await proc.wait()
        raise


async def run_gemini_once(page: Page, prompt_text: str, model: str, attempt: int) -> tuple[int, bytes, bytes]:
    image_path = prepare_gemini_image(page)
    image_arg = f"@{_rel(image_path)}"
    try:
        proc = await asyncio.create_subprocess_exec(
            "gemini",
            "-p",
            image_arg,
            "--model",
            model,
            "--output-format",
            "text",
            "--allowed-tools",
            "read_file",
            "-y",
            cwd=ROOT,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await communicate_with_heartbeat(proc, page, prompt_text, attempt)
        return proc.returncode or 0, stdout, stderr
    finally:
        image_path.unlink(missing_ok=True)


def prepare_gemini_image(page: Page) -> Path:
    """Copy image to a no-spaces path because Gemini's @ parser splits paths."""

    GEMINI_TMP_DIR.mkdir(parents=True, exist_ok=True)
    safe_path = GEMINI_TMP_DIR / f"vol{page.vol}-p{page.idx:04d}.png"
    shutil.copy2(page.png_path, safe_path)
    return safe_path


def is_non_ocr_response(stdout_text: str) -> bool:
    return bool(IMAGE_REFUSAL_RE.search(stdout_text))


# Content-quality gate added 2026-05-15 after empirical sweep found 21/557 (3.8%)
# .md files were silent failures: gemini-cli exited 0 but emitted <500b of
# garbage like "<ctrl46><ctrl46>..." (control-char markers). The success path
# below treats these as errors so they get retried instead of silently shipped
# as bad data.
MIN_OUTPUT_BYTES = 500
CONTROL_GARBAGE_RE = re.compile(r"<ctrl\d+>")


def is_low_quality_output(stdout_text: str) -> bool:
    """True if stdout looks like a silent OCR failure (garbage, refusal, too short).

    Patterns observed in vol1 of the first run:
    - Output under 500 bytes (real page transcripts are 3-10KB).
    - Output dominated by `<ctrl\\d+>` markers (Gemini CLI control-char fallback).
    - Output with fewer than 100 letter characters total.
    """
    if len(stdout_text.encode("utf-8")) < MIN_OUTPUT_BYTES:
        return True
    ctrl_matches = len(CONTROL_GARBAGE_RE.findall(stdout_text))
    word_chars = sum(1 for c in stdout_text if c.isalpha())
    if ctrl_matches > 5 and ctrl_matches > word_chars * 0.1:
        return True
    return word_chars < 100


# Observed 2026-05-15: ~3/8 random pages leaked the model's internal planning
# preamble before the real transcription. The leak shape is consistent:
#   "<ctrl46><ctrl46>...update_topic{strategic_intent:...,summary:...}<real text>"
# Strip these from stdout BEFORE writing the .md. The transcription below the
# leak is clean.
PREAMBLE_CTRL_RE = re.compile(r"<ctrl\d+>")
# 2.5-flash leak: update_topic{strategic_intent:...page number at the (end|bottom).<HEADWORD>
PREAMBLE_UPDATE_TOPIC_RE = re.compile(
    r"update_topic\{.*?page number at the (?:end|bottom)\.?",
    re.DOTALL,
)
# auto/3.x leak (English conversational, e.g.:
#   "Wait! I can see the image now."
#   "Let me transcribe the image verbatim exactly as requested."
#   "The left column contains:"
# ). Strip all leading lines that have NO substantial Cyrillic content
# (>=3 consecutive Cyrillic letters); stop at first content-bearing line.
CYRILLIC_RUN_RE = re.compile(r"[А-ЯҐЄІЇа-яґєії]{3,}")


def strip_planning_preamble(text: str) -> str:
    """Remove leaked planning preamble from OCR output. Two leak families:
    1. 2.5-flash control-char + JSON-tool-call dump.
    2. auto/3.x English conversational "Wait! I can see..." prose.
    Idempotent — clean pages pass through unchanged.
    """
    text = PREAMBLE_CTRL_RE.sub("", text)
    text = PREAMBLE_UPDATE_TOPIC_RE.sub("", text)
    # Walk lines from top; drop any line until we find one with substantial
    # Cyrillic content. ESUM pages always have Cyrillic on every content line.
    lines = text.split("\n")
    first_content_idx = 0
    for i, line in enumerate(lines):
        if CYRILLIC_RUN_RE.search(line):
            first_content_idx = i
            break
    else:
        # No Cyrillic content found — return empty (low_quality check will reject)
        return ""
    return "\n".join(lines[first_content_idx:]).lstrip()


def classify_error(stderr_text: str, stdout_text: str) -> str:
    combined = f"{stderr_text}\n{stdout_text}"
    if DAILY_QUOTA_RE.search(combined):
        return "daily_quota"
    if RPM_RE.search(combined):
        return "rpm"
    if TRANSIENT_RE.search(combined):
        return "transient"
    return "error"


async def ocr_page(
    page: Page,
    prompt_text: str,
    model: str,
    logger: JsonlLogger,
    rate_limiter: RateLimiter,
    semaphore: asyncio.Semaphore,
    halt_event: asyncio.Event,
) -> PageResult:
    if halt_event.is_set():
        return PageResult("skipped", page)

    async with semaphore:
        if halt_event.is_set():
            return PageResult("skipped", page)

        transient_retries = 0
        rpm_retries = 0
        total_retries = 0
        attempt = 1
        started = time.monotonic()

        while True:
            await rate_limiter.wait_for_slot(page)
            returncode, stdout, stderr = await run_gemini_once(page, prompt_text, model, attempt)
            duration = time.monotonic() - started
            stderr_text = stderr.decode("utf-8", errors="replace")
            stdout_text = stdout.decode("utf-8", errors="replace")

            non_ocr_response = is_non_ocr_response(stdout_text)
            # Strip leaked planning preamble BEFORE quality check so a real page
            # with a small preamble passes through cleanly.
            cleaned_text = strip_planning_preamble(stdout_text)
            cleaned_bytes = cleaned_text.encode("utf-8")
            low_quality = is_low_quality_output(cleaned_text)
            if returncode == 0 and cleaned_text.strip() and not non_ocr_response and not low_quality:
                page.md_path.parent.mkdir(parents=True, exist_ok=True)
                page.md_path.write_bytes(cleaned_bytes)
                await logger.write(
                    {
                        "event": "ok",
                        "page": page.key,
                        "duration_s": round(duration, 1),
                        "bytes_out": len(stdout),
                    }
                )
                _safe_print(f"ocr {page.key} ok duration={duration:.1f}s")
                return PageResult("ok", page, duration, total_retries)

            category = "error" if non_ocr_response else classify_error(stderr_text, stdout_text)
            stderr_tail = _tail(stderr_text or stdout_text or f"empty output rc={returncode}")

            if category == "daily_quota":
                await logger.write(
                    {
                        "event": "error",
                        "page": page.key,
                        "stderr_tail": stderr_tail,
                        "retries": total_retries,
                    }
                )
                _safe_print(f"ocr {page.key} daily-quota-error retries={total_retries}")
                return PageResult("quota", page, duration, total_retries, stderr_tail)

            if category == "rpm" and rpm_retries < 3:
                rpm_retries += 1
                total_retries += 1
                sleep_s = 60
                _safe_print(f"backoff {page.key} attempt={attempt} sleep={sleep_s}s")
                await sleep_with_heartbeat(sleep_s, f"backoff {page.key} attempt={attempt}")
                attempt += 1
                continue

            if category == "transient" and transient_retries < 5:
                transient_retries += 1
                total_retries += 1
                sleep_s = min(2 ** (transient_retries - 1), 32)
                _safe_print(f"backoff {page.key} attempt={attempt} sleep={sleep_s}s")
                await sleep_with_heartbeat(sleep_s, f"backoff {page.key} attempt={attempt}")
                attempt += 1
                continue

            await logger.write(
                {
                    "event": "error",
                    "page": page.key,
                    "stderr_tail": stderr_tail,
                    "retries": total_retries,
                }
            )
            _safe_print(f"ocr {page.key} error category={category} retries={total_retries}")
            return PageResult("error", page, duration, total_retries, stderr_tail)


async def run_ocr_pages(
    pages: list[Page],
    prompt_text: str,
    model: str,
    concurrency: int,
    rpm: int,
    logger: JsonlLogger,
) -> RunStats:
    stats = RunStats(total=len(pages))
    started = time.monotonic()
    halt_event = asyncio.Event()
    semaphore = asyncio.Semaphore(concurrency)
    rate_limiter = RateLimiter(rpm)
    recent: deque[bool] = deque(maxlen=ROLLING_WINDOW)

    tasks = {
        asyncio.create_task(ocr_page(page, prompt_text, model, logger, rate_limiter, semaphore, halt_event)): page
        for page in pages
    }
    pending = set(tasks)

    try:
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                result = task.result()
                if result.status == "ok":
                    stats.ok += 1
                    stats.last_successful_page = result.page.key
                    stats.consecutive_quota_errors = 0
                    recent.append(False)
                elif result.status == "quota":
                    stats.error += 1
                    stats.consecutive_quota_errors += 1
                    if stats.consecutive_quota_errors >= 3:
                        stats.quota_halt = True
                        halt_event.set()
                        await logger.write(
                            {
                                "event": "QUOTA_HALT",
                                "page": result.page.key,
                                "consecutive_quota_errors": stats.consecutive_quota_errors,
                            }
                        )
                        _safe_print(f"QUOTA_HALT page={result.page.key}")
                        for pending_task in pending:
                            pending_task.cancel()
                        await asyncio.gather(*pending, return_exceptions=True)
                        pending.clear()
                        break
                elif result.status == "error":
                    stats.error += 1
                    stats.consecutive_quota_errors = 0
                    recent.append(True)
                    if len(recent) == ROLLING_WINDOW and sum(recent) > ROLLING_ERROR_LIMIT:
                        stats.quality_halt = True
                        halt_event.set()
                        await logger.write(
                            {
                                "event": "BULK_QUALITY_HALT",
                                "page": result.page.key,
                                "errors_last_100": sum(recent),
                            }
                        )
                        _safe_print(f"BULK_QUALITY_HALT page={result.page.key} errors_last_100={sum(recent)}")
                        for pending_task in pending:
                            pending_task.cancel()
                        await asyncio.gather(*pending, return_exceptions=True)
                        pending.clear()
                        break
    finally:
        stats.duration_s = time.monotonic() - started

    return stats


def complete_volume_pages(volume: Volume) -> list[Path]:
    md_paths = [
        OCR_DIR / f"vol{volume.number}" / f"p{page_index(member):04d}.md"
        for member in sorted(volume.jp2_members, key=page_index)
    ]
    if all(_has_content(path) for path in md_paths):
        return md_paths
    return []


def concatenate_completed_volumes(volumes: list[Volume]) -> list[Path]:
    outputs: list[Path] = []
    for volume in volumes:
        md_paths = complete_volume_pages(volume)
        if not md_paths:
            continue

        output_path = RAW_ESUM / f"vol{volume.number}-gemini.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as out:
            for md_path in md_paths:
                data = md_path.read_bytes()
                out.write(data)
                if not data.endswith(b"\n"):
                    out.write(b"\n")
                out.write(b"\n")
        outputs.append(output_path)
        _safe_print(f"concatenated vol{volume.number} pages={len(md_paths)} output={_rel(output_path)}")
    return outputs


def print_dry_run(pages: list[Page]) -> None:
    existing_md = sum(1 for page in pages if _has_content(page.md_path))
    existing_png = sum(1 for page in pages if _has_content(page.png_path))
    existing_jp2 = sum(1 for page in pages if _has_content(page.jp2_path))
    pending_ocr = len(pages) - existing_md
    _safe_print(
        "dry-run "
        f"total_pages={len(pages)} existing_md={existing_md} existing_png={existing_png} "
        f"existing_jp2={existing_jp2} pending_ocr={pending_ocr}"
    )
    for page in pages:
        if _has_content(page.md_path):
            action = "skip-output-exists"
        elif _has_content(page.png_path):
            action = "ocr"
        elif _has_content(page.jp2_path):
            action = "decode+ocr"
        else:
            action = "extract+decode+ocr"
        _safe_print(f"dry-run {page.key} {action} png={_rel(page.png_path)} md={_rel(page.md_path)}")


def quota_halt_message(stats: RunStats, pages: list[Page]) -> str:
    remaining = sum(1 for page in pages if not _has_content(page.md_path))
    last = stats.last_successful_page or "none"
    return "\n".join(
        [
            "============================================================",
            "QUOTA_HALT — Gemini daily quota likely exhausted.",
            f"Last successful page: {last}",
            f"Pages completed this run: {stats.ok} / {len(pages)}",
            f"Pages remaining: {remaining}",
            "Resume: gemini /auth (swap to another Google account), then re-run:",
            "  .venv/bin/python scripts/etymology/bulk_ocr_gemini.py",
            "Idempotent — already-completed pages will be skipped.",
            "============================================================",
        ]
    )


def quality_halt_message() -> str:
    return "\n".join(
        [
            "============================================================",
            "BULK_QUALITY_HALT — failure rate exceeded 5% in a 100-page rolling window.",
            "Inspect audit/etymology-ocr-feasibility/bulk-run-log.jsonl before resuming.",
            "============================================================",
        ]
    )


async def run(args: argparse.Namespace) -> int:
    selected = parse_only(args.only)
    volumes = discover_volumes()
    if selected:
        selected_vols = {vol for vol, _idx in selected}
        volumes = [volume for volume in volumes if volume.number in selected_vols]

    pages = collect_pages(volumes, selected)
    if args.dry_run:
        print_dry_run(pages)
        return 0

    extract_archives(volumes)
    pages = collect_pages(volumes, selected)
    decode_pages(pages)

    pending_ocr = [page for page in pages if not _has_content(page.md_path)]
    skipped = len(pages) - len(pending_ocr)
    _safe_print(f"ocr plan total_pages={len(pages)} skip_existing={skipped} pending={len(pending_ocr)}")

    logger = JsonlLogger(args.log)
    prompt_text = args.prompt.read_text(encoding="utf-8")
    if pending_ocr:
        stats = await run_ocr_pages(pending_ocr, prompt_text, args.model, args.concurrency, args.rpm, logger)
    else:
        stats = RunStats(total=0)
    concatenate_completed_volumes(volumes)

    await logger.write(
        {
            "event": "summary",
            "total": stats.total,
            "ok": stats.ok,
            "error": stats.error,
            "duration_s": round(stats.duration_s, 1),
        }
    )

    if stats.quota_halt:
        _safe_print(quota_halt_message(stats, pages), file=sys.stderr)
        return 2
    if stats.quality_halt:
        _safe_print(quality_halt_message(), file=sys.stderr)
        return 3
    if stats.error:
        _safe_print(f"OCR completed with {stats.error} page error(s); inspect {_rel(args.log)}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Plan work without extracting, decoding, or calling Gemini")
    parser.add_argument("--only", help="Comma-separated pages to process, e.g. vol5/p0216,vol5/p0221")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--rpm", type=int, default=DEFAULT_RPM)
    return parser


def main() -> int:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    parser = build_parser()
    args = parser.parse_args()
    if args.concurrency < 1 or args.concurrency > DEFAULT_CONCURRENCY:
        parser.error(f"--concurrency must be between 1 and {DEFAULT_CONCURRENCY}")
    if args.rpm < 0:
        parser.error("--rpm must be non-negative")
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
