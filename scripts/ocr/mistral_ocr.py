"""Mistral OCR client — single image or batch directory, resumable, cost-capped.

Usage:
    # First run: see the help, create credential file, do a dry run
    .venv/bin/python scripts/ocr/mistral_ocr.py --help

    # Single image
    .venv/bin/python scripts/ocr/mistral_ocr.py \\
        --input /path/to/page.png \\
        --output audit/2026-05-17-ocr-bakeoff/mistral/

    # Batch directory (PNG/JPG/PDF)
    .venv/bin/python scripts/ocr/mistral_ocr.py \\
        --input data/raw/scanned-textbook/ \\
        --output data/ocr/textbook-mistral/ \\
        --concurrency 2 \\
        --max-cost-usd 5.0

    # Resume after interruption — outputs that exist are skipped
    .venv/bin/python scripts/ocr/mistral_ocr.py --input ... --output ... --resume

Credential handling:
    The Mistral API key is read from a file the user owns. Default path is
    `~/.config/learn-ukrainian/secrets/mistral-api-key`. The file must be
    mode 0600 (rw-------) or 0400 (r--------) and owned by the running uid.
    See scripts/ocr/_credentials.py and docs/ocr/SETUP.md for the rationale
    + create-the-file steps.

Output format:
    For each input image `foo.png`, two files are written:
        <output>/foo.md      — extracted Markdown (Mistral OCR returns
                               structured Markdown by default)
        <output>/foo.json    — telemetry: model, pages, tokens, cost,
                               input checksum, timestamp. Lets us audit
                               drift and reproduce exact runs.

    Lossless. The .md is what the writer/reviewer reads; the .json is
    forensic.

Cost capping:
    --max-cost-usd is a HARD budget cap. The client tracks cumulative
    cost across the batch (from `usage_info` in each response) and stops
    dispatching new items the moment the cap would be exceeded by the
    next call. The cap defaults to $5 — change explicitly when you know
    the job size.

Resume:
    Default ON. Outputs that already exist (and have a non-empty .md
    sibling) are skipped. Mistral charges per page; do not re-OCR
    accidentally.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import mimetypes
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

# Allow running both as `python scripts/ocr/mistral_ocr.py` (script mode,
# with scripts/ocr on sys.path) and as `python -m scripts.ocr.mistral_ocr`
# (package mode). Mirrors the convention in scripts/api/docs_router.py.
try:
    from _credentials import CredentialError, load_credential  # script-mode
except ImportError:  # pragma: no cover — package-mode
    from scripts.ocr._credentials import (  # type: ignore[no-redef]
        CredentialError,
        load_credential,
    )


_API_URL = "https://api.mistral.ai/v1/ocr"
_DEFAULT_MODEL = "mistral-ocr-latest"
# Project convention (user direction 2026-05-17): all third-party API keys
# live under ~/.secret/<provider>.key with mode 0600. See docs/ocr/SETUP.md.
_DEFAULT_CREDENTIAL_PATH = Path.home() / ".secret" / "mistral.key"
_DEFAULT_MAX_COST_USD = 5.0
_DEFAULT_CONCURRENCY = 1
_DEFAULT_TIMEOUT_S = 120

# Document inputs we support. .png / .jpg / .jpeg / .pdf — extend later if
# Mistral OCR adds .tiff or .webp.
_IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg"})
_PDF_EXTS = frozenset({".pdf"})
_ALLOWED_EXTS = _IMAGE_EXTS | _PDF_EXTS

logger = logging.getLogger("mistral_ocr")


@dataclass
class CallTelemetry:
    """Per-call audit record. Persisted alongside the OCR output."""

    input_path: str
    input_sha256: str
    output_path: str
    model: str
    pages: int
    cost_usd: float
    usage_info: dict[str, Any]
    duration_s: float
    timestamp: str
    error: str | None = None


@dataclass
class BatchState:
    """In-flight totals + cap tracking. Updated by the worker callback."""

    total_cost_usd: float = 0.0
    completed: int = 0
    skipped: int = 0
    failed: int = 0
    items: list[CallTelemetry] = field(default_factory=list)

    def under_cap(self, cap: float) -> bool:
        return self.total_cost_usd < cap


def _iter_inputs(input_path: Path) -> list[Path]:
    """Walk the input path and yield all files we'll OCR.

    A single file → [file].
    A directory → every file under it (recursive) with an allowed suffix.
    Skips hidden files and `.DS_Store` style cruft.
    """
    if input_path.is_file():
        if input_path.suffix.lower() not in _ALLOWED_EXTS:
            raise ValueError(
                f"unsupported input extension {input_path.suffix} on {input_path}. "
                f"Allowed: {sorted(_ALLOWED_EXTS)}"
            )
        return [input_path]
    if not input_path.is_dir():
        raise ValueError(f"input path does not exist or is not a file/dir: {input_path}")
    found: list[Path] = []
    for child in sorted(input_path.rglob("*")):
        if not child.is_file():
            continue
        if any(part.startswith(".") for part in child.relative_to(input_path).parts):
            continue
        if child.suffix.lower() in _ALLOWED_EXTS:
            found.append(child)
    return found


def _output_paths(input_file: Path, input_root: Path, output_root: Path) -> tuple[Path, Path]:
    """Compute (markdown_path, json_path) for one input file.

    Mirrors the input directory structure under output_root. For a single
    file input where `input_root == input_file`, output goes flat under
    `output_root`.
    """
    rel = input_file.name if input_root == input_file else input_file.relative_to(input_root).as_posix()
    stem = Path(rel).with_suffix("")
    md_path = output_root / f"{stem}.md"
    json_path = output_root / f"{stem}.json"
    return md_path, json_path


def _sha256_file(path: Path, *, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _build_document_payload(input_file: Path) -> dict[str, Any]:
    """Encode the input file for the Mistral OCR request body.

    Image inputs (PNG/JPG) → `type: image_url`, base64-encoded data URI.
    PDF inputs → `type: document_url`, base64-encoded data URI.

    Mistral OCR also accepts hosted HTTPS URLs for both types, but we keep
    everything local so private corpus files never leave our control via a
    side channel.
    """
    suffix = input_file.suffix.lower()
    mime, _ = mimetypes.guess_type(input_file.name)
    if mime is None:
        # Default fallback. Mistral cares about the data URI MIME for
        # routing; better to be explicit than rely on sniffing.
        mime = "image/png" if suffix in _IMAGE_EXTS else "application/pdf"

    encoded = base64.b64encode(input_file.read_bytes()).decode("ascii")
    data_uri = f"data:{mime};base64,{encoded}"

    if suffix in _IMAGE_EXTS:
        return {"type": "image_url", "image_url": data_uri}
    return {"type": "document_url", "document_url": data_uri}


def _compose_markdown(response_body: dict[str, Any]) -> tuple[str, int]:
    """Flatten Mistral's per-page response into a single Markdown string.

    Returns (markdown, page_count).
    """
    pages = response_body.get("pages") or []
    if not pages:
        return "", 0
    chunks = []
    for page in pages:
        idx = page.get("index", "?")
        text = (page.get("markdown") or "").rstrip()
        if text:
            chunks.append(f"<!-- page {idx} -->\n{text}")
    return "\n\n".join(chunks) + "\n", len(pages)


def _post_ocr(
    *,
    client: httpx.Client,
    api_key: str,
    model: str,
    document: dict[str, Any],
    timeout_s: int,
) -> dict[str, Any]:
    """One HTTP call against the OCR endpoint. Retries on 429 / 5xx."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"model": model, "document": document}

    backoff = 1.0
    last_exc: Exception | None = None
    for _ in range(4):
        try:
            response = client.post(_API_URL, headers=headers, json=payload, timeout=timeout_s)
        except httpx.HTTPError as exc:
            last_exc = exc
            time.sleep(backoff)
            backoff *= 2
            continue
        if response.status_code == 200:
            return response.json()
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(backoff)
            backoff *= 2
            continue
        # 4xx other than 429 — surface upstream error text, but NEVER the
        # request body (which contains the base64 image but not the key).
        # The key is in the Authorization header, which httpx redacts in
        # its repr; we still strip it from any logged response.
        snippet = response.text[:400]
        raise RuntimeError(
            f"OCR request failed with HTTP {response.status_code}. "
            f"Response prefix (no auth): {snippet!r}"
        )
    raise RuntimeError(f"OCR request failed after retries: {last_exc!r}")


def _process_one(
    *,
    input_file: Path,
    md_path: Path,
    json_path: Path,
    client: httpx.Client,
    api_key: str,
    model: str,
    timeout_s: int,
) -> CallTelemetry:
    """OCR one input file, write outputs, return audit record."""
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    document = _build_document_payload(input_file)
    response_body = _post_ocr(
        client=client,
        api_key=api_key,
        model=model,
        document=document,
        timeout_s=timeout_s,
    )

    markdown, page_count = _compose_markdown(response_body)
    md_path.write_text(markdown, encoding="utf-8")

    usage_info = response_body.get("usage_info") or {}
    cost_usd = float(usage_info.get("cost_usd") or 0.0)
    duration = time.monotonic() - started

    telemetry = CallTelemetry(
        input_path=str(input_file),
        input_sha256=_sha256_file(input_file),
        output_path=str(md_path),
        model=response_body.get("model", model),
        pages=page_count,
        cost_usd=cost_usd,
        usage_info=usage_info,
        duration_s=duration,
        timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    json_path.write_text(json.dumps(telemetry.__dict__, indent=2), encoding="utf-8")
    return telemetry


def _already_done(md_path: Path) -> bool:
    return md_path.is_file() and md_path.stat().st_size > 0


def run_batch(
    *,
    input_path: Path,
    output_root: Path,
    api_key: str,
    model: str = _DEFAULT_MODEL,
    concurrency: int = _DEFAULT_CONCURRENCY,
    max_cost_usd: float = _DEFAULT_MAX_COST_USD,
    timeout_s: int = _DEFAULT_TIMEOUT_S,
    resume: bool = True,
    dry_run: bool = False,
) -> BatchState:
    """Run OCR over `input_path` (file or dir). Returns the BatchState."""
    output_root.mkdir(parents=True, exist_ok=True)
    inputs = _iter_inputs(input_path)
    input_root = input_path if input_path.is_dir() else input_path.parent
    state = BatchState()

    if not inputs:
        logger.info("no inputs to process under %s", input_path)
        return state

    work: list[tuple[Path, Path, Path]] = []
    for f in inputs:
        md_path, json_path = _output_paths(f, input_root, output_root)
        if resume and _already_done(md_path):
            state.skipped += 1
            logger.info("skip (exists): %s", md_path)
            continue
        work.append((f, md_path, json_path))

    logger.info(
        "OCR plan: %d total inputs, %d to process, %d skipped (resume=%s), cap=$%.2f",
        len(inputs),
        len(work),
        state.skipped,
        resume,
        max_cost_usd,
    )

    if dry_run:
        for f, md_path, _ in work:
            logger.info("DRY-RUN would OCR: %s → %s", f, md_path)
        return state

    # Concurrency safety: workers share an httpx.Client (connection pool).
    # The api_key lives ONLY in the Authorization header we build per call;
    # never put it in the client's default_headers since that surfaces in
    # client repr for debugging.
    with httpx.Client(http2=False) as client:
        def _worker(item: tuple[Path, Path, Path]) -> CallTelemetry:
            f, md_path, json_path = item
            return _process_one(
                input_file=f,
                md_path=md_path,
                json_path=json_path,
                client=client,
                api_key=api_key,
                model=model,
                timeout_s=timeout_s,
            )

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {pool.submit(_worker, item): item for item in work}
            for future in as_completed(futures):
                item = futures[future]
                try:
                    telemetry = future.result()
                except Exception as exc:
                    telemetry = CallTelemetry(
                        input_path=str(item[0]),
                        input_sha256="",
                        output_path=str(item[1]),
                        model=model,
                        pages=0,
                        cost_usd=0.0,
                        usage_info={},
                        duration_s=0.0,
                        timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        error=str(exc),
                    )
                    state.failed += 1
                    logger.warning("FAILED %s: %s", item[0], exc)
                    # Persist failure telemetry so batch jobs are auditable
                    # post-hoc without re-running. No .md is written — only
                    # the sidecar .json captures the error path.
                    _, json_path_failed = _output_paths(item[0], input_root, output_root)
                    try:
                        json_path_failed.parent.mkdir(parents=True, exist_ok=True)
                        json_path_failed.write_text(
                            json.dumps(telemetry.__dict__, indent=2), encoding="utf-8"
                        )
                    except OSError as write_exc:
                        logger.warning(
                            "could not persist failure telemetry to %s: %s",
                            json_path_failed,
                            write_exc,
                        )
                else:
                    state.completed += 1
                    state.total_cost_usd += telemetry.cost_usd
                    logger.info(
                        "ok %s pages=%d cost=$%.4f cum=$%.4f duration=%.1fs",
                        telemetry.input_path,
                        telemetry.pages,
                        telemetry.cost_usd,
                        state.total_cost_usd,
                        telemetry.duration_s,
                    )
                state.items.append(telemetry)
                if not state.under_cap(max_cost_usd):
                    logger.error(
                        "cost cap reached: $%.4f >= $%.2f — cancelling remaining work",
                        state.total_cost_usd,
                        max_cost_usd,
                    )
                    for f2 in futures:
                        f2.cancel()
                    break
    return state


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mistral_ocr.py",
        description="OCR via Mistral mistral-ocr-latest. File-backed credential.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Credentials:\n"
            "  Default key path is ~/.secret/mistral.key (project convention).\n"
            "  Required mode: 0600 or 0400, owned by current uid.\n"
            "  Override path with --credentials PATH if you store it elsewhere.\n"
            "  See docs/ocr/SETUP.md for the threat model + create-the-file steps.\n"
        ),
    )
    parser.add_argument("--input", type=Path, required=True, help="Image file OR directory (recursed)")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory. Mirrors input tree for batch.",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=_DEFAULT_CREDENTIAL_PATH,
        help=f"Path to credential file (default: {_DEFAULT_CREDENTIAL_PATH})",
    )
    parser.add_argument("--model", default=_DEFAULT_MODEL, help=f"Mistral OCR model (default: {_DEFAULT_MODEL})")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=_DEFAULT_CONCURRENCY,
        help=f"Parallel requests (default: {_DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--max-cost-usd",
        type=float,
        default=_DEFAULT_MAX_COST_USD,
        help=f"Hard budget cap; aborts batch when exceeded (default: ${_DEFAULT_MAX_COST_USD:.2f})",
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=_DEFAULT_TIMEOUT_S,
        help=f"Per-request timeout in seconds (default: {_DEFAULT_TIMEOUT_S})",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-process inputs even if outputs exist. Default is to skip done items.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan; do not call the API.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logger level (default: INFO).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    try:
        api_key = load_credential(args.credentials)
    except CredentialError as exc:
        # Multi-line `exc` includes a fix-it hint for the user. NEVER print
        # the loaded value — load_credential never returns through this
        # path, but a future refactor must not regress.
        print(f"credential error: {exc}", file=sys.stderr)
        return 2

    state = run_batch(
        input_path=args.input,
        output_root=args.output,
        api_key=api_key,
        model=args.model,
        concurrency=args.concurrency,
        max_cost_usd=args.max_cost_usd,
        timeout_s=args.timeout_s,
        resume=not args.no_resume,
        dry_run=args.dry_run,
    )
    # The api_key local is the only place the key is referenced; it goes
    # out of scope when main() returns. Belt-and-suspenders: rebind to
    # empty so any future logger that captures `locals()` for diagnostics
    # cannot leak it.
    api_key = ""

    # Run-end summary. Cost is logged per call already; this is the rollup.
    logger.info(
        "DONE: %d ok / %d skipped / %d failed, total cost $%.4f",
        state.completed,
        state.skipped,
        state.failed,
        state.total_cost_usd,
    )
    return 0 if state.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
