"""Extract text from PDF textbooks into structured chunks.

Uses marker-pdf for section-aware markdown conversion,
then splits into chunks respecting section boundaries.

Usage:
    .venv/bin/python scripts/rag/extract_text.py data/textbooks/grade-01/1-klas-bukvar-bolshakova-2025-1.pdf
    .venv/bin/python scripts/rag/extract_text.py --all          # Process all PDFs
    .venv/bin/python scripts/rag/extract_text.py --grade 1 3    # Process grades 1 and 3
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import (
    CHUNK_MAX_TOKENS,
    CHUNK_MIN_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    CHUNKS_DIR,
    MIN_CLEAN_CHAR_RATIO,
    TEXTBOOKS_DIR,
    UKRAINIAN_CHARS,
    parse_pdf_metadata,
)


def extract_markdown(pdf_path: Path) -> str:
    """Convert PDF to structured markdown using marker."""
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    models = create_model_dict()
    converter = PdfConverter(artifact_dict=models)
    result = converter(str(pdf_path))
    return result.markdown


def split_into_sections(markdown: str) -> list[dict]:
    """Split markdown into sections at H1/H2 boundaries.

    Returns list of {title, level, text, page_hint} dicts.
    """
    sections = []
    # Split on H1 or H2 headings
    pattern = r'^(#{1,2})\s+(.+)$'
    parts = re.split(pattern, markdown, flags=re.MULTILINE)

    # First part is text before any heading
    if parts[0].strip():
        sections.append({
            "title": "Вступ",
            "level": 0,
            "text": parts[0].strip(),
        })

    # Process heading + content pairs (groups of 3: marker, title, content)
    i = 1
    while i < len(parts) - 2:
        heading_marker = parts[i]
        heading_title = parts[i + 1].strip()
        content = parts[i + 2].strip() if i + 2 < len(parts) else ""

        sections.append({
            "title": heading_title,
            "level": len(heading_marker),
            "text": content,
        })
        i += 3

    return sections


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~1.5 chars per token for Ukrainian Cyrillic."""
    return max(1, len(text) // 4)


def chunk_text(text: str, section_title: str) -> list[dict]:
    """Split text into overlapping chunks respecting paragraph boundaries.

    Returns list of {text, token_count} dicts.
    """
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current_parts = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If single paragraph exceeds max, force-split it
        if para_tokens > CHUNK_MAX_TOKENS:
            # Flush current buffer first
            if current_parts:
                chunk_text_joined = "\n\n".join(current_parts)
                chunks.append({
                    "text": chunk_text_joined,
                    "token_count": estimate_tokens(chunk_text_joined),
                })
                current_parts = []
                current_tokens = 0

            # Split long paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            sent_buf = []
            sent_tokens = 0
            for sent in sentences:
                st = estimate_tokens(sent)
                if sent_tokens + st > CHUNK_MAX_TOKENS and sent_buf:
                    chunk_text_joined = " ".join(sent_buf)
                    chunks.append({
                        "text": chunk_text_joined,
                        "token_count": estimate_tokens(chunk_text_joined),
                    })
                    # Overlap: keep last sentence
                    sent_buf = sent_buf[-1:] if CHUNK_OVERLAP_TOKENS > 0 else []
                    sent_tokens = estimate_tokens(" ".join(sent_buf))
                sent_buf.append(sent)
                sent_tokens += st
            if sent_buf:
                chunk_text_joined = " ".join(sent_buf)
                chunks.append({
                    "text": chunk_text_joined,
                    "token_count": estimate_tokens(chunk_text_joined),
                })
            continue

        # Would adding this paragraph exceed max?
        if current_tokens + para_tokens > CHUNK_MAX_TOKENS and current_parts:
            chunk_text_joined = "\n\n".join(current_parts)
            chunks.append({
                "text": chunk_text_joined,
                "token_count": estimate_tokens(chunk_text_joined),
            })
            # Overlap: keep last paragraph
            if CHUNK_OVERLAP_TOKENS > 0 and current_parts:
                last = current_parts[-1]
                current_parts = [last]
                current_tokens = estimate_tokens(last)
            else:
                current_parts = []
                current_tokens = 0

        current_parts.append(para)
        current_tokens += para_tokens

    # Flush remaining
    if current_parts:
        chunk_text_joined = "\n\n".join(current_parts)
        tokens = estimate_tokens(chunk_text_joined)
        # Merge tiny remainder into previous chunk if possible
        if tokens < CHUNK_MIN_TOKENS and chunks:
            prev = chunks[-1]
            merged = prev["text"] + "\n\n" + chunk_text_joined
            chunks[-1] = {
                "text": merged,
                "token_count": estimate_tokens(merged),
            }
        else:
            chunks.append({
                "text": chunk_text_joined,
                "token_count": tokens,
            })

    return chunks


def check_quality(text: str) -> tuple[bool, float]:
    """Check if chunk text is clean Ukrainian.

    Returns (is_clean, ratio) where ratio is the fraction of
    recognized Ukrainian characters.
    """
    if not text:
        return False, 0.0

    clean_count = 0
    total_count = 0
    for ch in text:
        if unicodedata.category(ch).startswith("C"):  # Control chars
            continue
        total_count += 1
        if ch in UKRAINIAN_CHARS:
            clean_count += 1

    if total_count == 0:
        return False, 0.0

    ratio = clean_count / total_count
    return ratio >= MIN_CLEAN_CHAR_RATIO, ratio


def process_pdf(pdf_path: Path, output_dir: Path | None = None) -> dict:
    """Process a single PDF into chunks.

    Returns summary dict with counts and quality stats.
    """
    pdf_path = Path(pdf_path)
    meta = parse_pdf_metadata(pdf_path)

    if output_dir is None:
        output_dir = CHUNKS_DIR / f"grade-{meta['grade']:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[extract] Processing {pdf_path.name}...")
    print(f"  Metadata: grade={meta['grade']}, author={meta['author']}, "
          f"year={meta['year']}, trust_tier={meta['trust_tier']}")

    # Step 1: PDF → markdown
    print("  Converting PDF → markdown...")
    markdown = extract_markdown(pdf_path)
    print(f"  Markdown length: {len(markdown)} chars")

    # Step 2: Split into sections
    sections = split_into_sections(markdown)
    print(f"  Found {len(sections)} sections")

    # Step 3: Chunk each section
    all_chunks = []
    quality_stats = {"clean": 0, "flagged": 0}

    for section in sections:
        chunks = chunk_text(section["text"], section["title"])
        for i, chunk in enumerate(chunks):
            is_clean, ratio = check_quality(chunk["text"])

            chunk_record = {
                "chunk_id": f"{meta['pdf_stem']}_s{len(all_chunks):04d}",
                "text": chunk["text"],
                "token_count": chunk["token_count"],
                "section_title": section["title"],
                "section_level": section["level"],
                "quality": {
                    "is_clean": is_clean,
                    "clean_ratio": round(ratio, 3),
                },
                **{k: v for k, v in meta.items() if k != "pdf_stem"},
                "pdf_stem": meta["pdf_stem"],
            }
            all_chunks.append(chunk_record)

            if is_clean:
                quality_stats["clean"] += 1
            else:
                quality_stats["flagged"] += 1

    # Save chunks as JSONL
    output_file = output_dir / f"{meta['pdf_stem']}.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    summary = {
        "pdf": pdf_path.name,
        "total_chunks": len(all_chunks),
        "clean_chunks": quality_stats["clean"],
        "flagged_chunks": quality_stats["flagged"],
        "sections": len(sections),
        "output_file": str(output_file),
    }
    print(f"  Result: {summary['total_chunks']} chunks "
          f"({summary['clean_chunks']} clean, {summary['flagged_chunks']} flagged)")
    print(f"  Saved to {output_file}")

    return summary


def find_pdfs(grades: list[int] | None = None) -> list[Path]:
    """Find all PDF files, optionally filtered by grade."""
    pdfs = []
    for grade_dir in sorted(TEXTBOOKS_DIR.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue
        grade_num = int(grade_dir.name.split("-")[1])
        if grades and grade_num not in grades:
            continue
        for pdf in sorted(grade_dir.glob("*.pdf")):
            pdfs.append(pdf)
    return pdfs


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF textbooks")
    parser.add_argument("pdf", nargs="?", help="Path to a single PDF file")
    parser.add_argument("--all", action="store_true", help="Process all PDFs")
    parser.add_argument("--grade", type=int, nargs="+", help="Process specific grades")
    args = parser.parse_args()

    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"Error: {pdf_path} not found", file=sys.stderr)
            sys.exit(1)
        summary = process_pdf(pdf_path)
        print(f"\nDone: {json.dumps(summary, indent=2)}")

    elif args.all or args.grade:
        pdfs = find_pdfs(args.grade)
        if not pdfs:
            print("No PDFs found", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(pdfs)} PDFs to process\n")
        summaries = []
        for pdf in pdfs:
            summary = process_pdf(pdf)
            summaries.append(summary)
            print()
        total_chunks = sum(s["total_chunks"] for s in summaries)
        total_flagged = sum(s["flagged_chunks"] for s in summaries)
        print(f"=== Total: {total_chunks} chunks from {len(pdfs)} PDFs "
              f"({total_flagged} flagged) ===")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
