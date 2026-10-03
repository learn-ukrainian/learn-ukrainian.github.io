#!/usr/bin/env python3
"""Ingest the official «Український правопис» (2019) into ``sources.db`` (#9610).

Only a byte-exact official PDF is accepted (its SHA-256 must be one of
``OFFICIAL_FILES``).  The run parses every § of the printed body, checks the
count and start pages against the printed table of contents, and replaces the
stored edition in one transaction; any disagreement aborts without writing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import requests

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from scripts.wiki.pravopys_official import (
        OFFICIAL_FILES,
        ULIF_PDF_URL,
        OfficialFile,
        PravopysParseError,
        parse_edition,
        store_edition,
        utc_now,
        validate_against_toc,
        vesum_word_predicate,
    )
except ImportError:  # pragma: no cover - direct script execution
    from wiki.pravopys_official import (
        OFFICIAL_FILES,
        ULIF_PDF_URL,
        OfficialFile,
        PravopysParseError,
        parse_edition,
        store_edition,
        utc_now,
        validate_against_toc,
        vesum_word_predicate,
    )

USER_AGENT = "learn-ukrainian-pravopys-ingest/1.0 (noncommercial educational corpus; issue 9610)"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def official_file_for(path: Path) -> OfficialFile:
    """The pinned official distribution matching ``path`` byte for byte."""
    sha = file_sha256(path)
    official = OFFICIAL_FILES.get(sha)
    if official is None:
        raise PravopysParseError(f"{path}: sha256 {sha} is not a pinned official file of the 2019 edition")
    return official


def fetch_official_pdf(dest_dir: Path, *, url: str = ULIF_PDF_URL, timeout: int = 120) -> tuple[Path, str]:
    """Download the official PDF, verify its pinned hash, return (path, retrieved_at)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / "pravopys-2019-ulif.pdf"
    retrieved_at = utc_now()
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    partial = target.with_suffix(".part")
    partial.write_bytes(response.content)
    sha = hashlib.sha256(response.content).hexdigest()
    if sha not in OFFICIAL_FILES:
        partial.unlink()
        raise PravopysParseError(f"{url}: downloaded sha256 {sha} is not the pinned official file")
    partial.replace(target)
    return target, retrieved_at


def ingest(
    pdf_path: Path,
    *,
    db_path: Path | None,
    retrieved_at: str,
    vesum_db: Path | None,
) -> dict[str, object]:
    """Parse and (unless ``db_path`` is None) store the edition; return a JSON-ready receipt."""
    official = official_file_for(pdf_path)
    parsed = parse_edition(pdf_path, official)
    problems = validate_against_toc(parsed)
    receipt: dict[str, object] = {
        "pdf": str(pdf_path),
        "file_sha256": official.sha256,
        "file_url": official.url,
        "retrieved_at": retrieved_at,
        "paragraphs": len(parsed.paragraphs),
        "sections": len(parsed.sections),
        "toc_paragraphs": sum(1 for entry in parsed.toc if entry.kind == "paragraph"),
        "toc_problems": problems,
        "written": False,
    }
    if problems:
        raise PravopysParseError("; ".join(problems))
    if db_path is None:
        return receipt
    is_word = vesum_word_predicate(vesum_db) if vesum_db else None
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        counts = store_edition(conn, parsed, official, retrieved_at=retrieved_at, is_word=is_word)
        stored = conn.execute("SELECT COUNT(*) FROM pravopys_paragraphs").fetchone()[0]
        stored_sections = conn.execute("SELECT COUNT(*) FROM pravopys_sections").fetchone()[0]
    finally:
        conn.close()
    receipt.update(
        written=True,
        db=str(db_path),
        stored_paragraphs=stored,
        stored_sections=stored_sections,
        unresolved_hyphenations=counts.unresolved_hyphenations,
    )
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest the official Ukrainian orthography (Український правопис, 2019 authorized edition) "
            "into sources.db by section and §.\n"
            "Use once per official file; normal lookups (query_pravopys) then read the tables offline. "
            "Do not use for any other edition: only pinned official PDFs are accepted."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/ingest/pravopys_2019_ingest.py --fetch /tmp/pravopys --dry-run
  .venv/bin/python scripts/ingest/pravopys_2019_ingest.py --pdf /tmp/pravopys/pravopys-2019-ulif.pdf \\
      --retrieved-at 2026-10-03T15:05:00Z --db /path/to/data/sources.db --vesum /path/to/data/vesum.db

Outputs:
  Replaces the rows of source_id 'pravopys_2019_official' in pravopys_sources, pravopys_sections and
  pravopys_paragraphs of --db in one transaction (tables created if missing). --fetch writes the
  verified PDF into its directory. A JSON receipt with the row counts is printed to stdout.

Exit codes:
  0  parsed (and written unless --dry-run); 168 §§ match the printed contents
  1  not a pinned official file, download failed, or the parse disagrees with the contents (nothing written)

Related:
  scripts/wiki/pravopys_official.py; docs/sources/pravopys-2019-official-source.md;
  issue #9610 (epic #6321, plan step E3b)
""",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pdf", type=Path, help="Path to an already downloaded official PDF (hash is verified).")
    source.add_argument(
        "--fetch",
        type=Path,
        metavar="DIR",
        help=f"Download the official PDF from {ULIF_PDF_URL} into DIR, verify its hash and use it.",
    )
    parser.add_argument(
        "--retrieved-at",
        help="UTC retrieval time of --pdf (ISO 8601, e.g. 2026-10-03T15:05:00Z). Required with --pdf; "
        "--fetch records the download time itself.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        help="sources.db to write (required unless --dry-run; no default, so a worktree never gets a stray DB).",
    )
    parser.add_argument(
        "--vesum",
        type=Path,
        help="vesum.db (read-only) used to resolve line-end hyphens in text_normalized. Default: none "
        "(every line-end hyphen is then decided by rule and counted as unresolved).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate only; write nothing to --db.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.pdf and not args.retrieved_at:
        parser.error("--retrieved-at is required with --pdf")
    if not args.dry_run and args.db is None:
        parser.error("--db is required unless --dry-run")
    try:
        if args.fetch:
            pdf_path, retrieved_at = fetch_official_pdf(args.fetch)
        else:
            pdf_path, retrieved_at = args.pdf, args.retrieved_at
        receipt = ingest(
            pdf_path,
            db_path=None if args.dry_run else args.db,
            retrieved_at=retrieved_at,
            vesum_db=args.vesum,
        )
    except (PravopysParseError, requests.RequestException, OSError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
