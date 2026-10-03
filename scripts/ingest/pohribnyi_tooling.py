"""Private page-image and transcription tooling for #9604; no source text in git."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pymupdf
from jsonschema import Draft202012Validator

PDF_SHA256 = "5ea396063526800ebe095d0e8dc99477caf56964bf0ecbe13f14995c750e1555"
NOTATION_PATH = Path(__file__).with_name("pohribnyi_notation.json")
CACHE_DIR = Path(".cache/pohribnyi")


def load_notation(path: Path = NOTATION_PATH) -> dict:
    """Validate the notation-table schema before using its allowlist."""
    table = json.loads(path.read_text(encoding="utf-8"))
    validate_notation(table)
    return table


def validate_notation(table: dict) -> None:
    """Check schema, Unicode constraints and the provisional/frozen boundary."""
    schema = json.loads(NOTATION_PATH.with_suffix(".schema.json").read_text(encoding="utf-8"))
    if not Draft202012Validator(schema).is_valid(table):
        raise ValueError("Invalid notation table schema")
    letters = table["letters"]
    if (
        any("CYRILLIC" not in unicodedata.name(c, "") for c in letters)
        or unicodedata.normalize("NFC", letters) != letters
    ):
        raise ValueError("Notation letters must be NFC Cyrillic")
    roles, points = set(), set()
    for symbol in table.get("symbols", []):
        role, point = symbol.get("role"), symbol.get("codepoint")
        if role in roles:
            raise ValueError("Invalid or duplicate symbol role")
        number = int(point[2:], 16)
        if number > 0x10FFFF or 0xD800 <= number <= 0xDFFF or point in points:
            raise ValueError("Invalid or duplicate codepoint")
        if "LATIN" in unicodedata.name(chr(number), ""):
            raise ValueError("Latin symbol in notation table")
        if not table["provisional"] and symbol["provisional"]:
            raise ValueError("Frozen table contains provisional symbols")
        roles.add(role)
        points.add(point)
    if not table["provisional"] and (
        table.get("pending_classes") != [] or len(set(table.get("freeze_reviewers", []))) < 2
    ):
        raise ValueError("Frozen notation needs two reviewers and no pending classes")


def bracketed_spans(text: str) -> list[dict]:
    """Return every bracketed span with codepoint offsets; refuse malformed brackets."""
    spans, start = [], None
    for offset, char in enumerate(text):
        if char == "[":
            if start is not None:
                raise ValueError("Nested transcription brackets")
            start = offset
        elif char == "]":
            if start is None:
                raise ValueError("Unmatched closing bracket")
            if offset == start + 1:
                raise ValueError("Empty transcription")
            spans.append({"start": start, "end": offset + 1, "text": text[start : offset + 1]})
            start = None
    if start is not None:
        raise ValueError("Unclosed transcription bracket")
    return spans


def validate_text(text: str, table: dict) -> list[dict]:
    """Reject non-NFC input and Latin/unknown symbols inside bracketed transcriptions."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Paragraph text must be nonempty")
    if unicodedata.normalize("NFC", text) != text:
        raise ValueError("Text is not NFC; normalization must precede offset assignment")
    allowed = set(table["letters"]) | {chr(int(s["codepoint"][2:], 16)) for s in table["symbols"]}
    spans = bracketed_spans(text)
    for span in spans:
        for char in span["text"][1:-1]:
            if "LATIN" in unicodedata.name(char, ""):
                raise ValueError(f"Latin codepoint U+{ord(char):04X} inside transcription")
            if char not in allowed:
                raise ValueError(f"Unknown transcription symbol U+{ord(char):04X}")
    return spans


def validate_rows(rows: list[dict], table: dict, *, adjudicated: bool = False) -> None:
    """Validate locators, text and underlining; ingestion also requires adjudication."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("Expected nonempty paragraph rows")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Paragraph row must be an object")
        page, paragraph = row.get("page"), row.get("paragraph")
        if type(page) is not int or not 1 <= page <= 28 or type(paragraph) is not int or paragraph < 1:
            raise ValueError("Invalid page/paragraph locator")
        if (page, paragraph) in seen:
            raise ValueError("Duplicate page/paragraph locator")
        seen.add((page, paragraph))
        validate_text(row.get("text"), table)
        underlining = row.get("underlining")
        if not isinstance(underlining, list):
            raise ValueError("Explicit underlining field required (empty list if absent)")
        last_end = 0
        for interval in underlining:
            if not isinstance(interval, dict):
                raise ValueError("Underlining interval must be an object")
            start, end = interval.get("start"), interval.get("end")
            if type(start) is not int or type(end) is not int or not last_end <= start < end <= len(row["text"]):
                raise ValueError("Invalid or overlapping underlining range")
            last_end = end
        if adjudicated and (
            row.get("status") != "adjudicated"
            or not isinstance(row.get("adjudicated_by"), str)
            or not row["adjudicated_by"].strip()
        ):
            raise ValueError("Adjudication status and adjudicated_by are required")


def diff_transcriptions(left: list[dict], right: list[dict], table: dict) -> dict:
    """Compare paragraph prose, underlining and aligned bracket spans; never resolve by guess."""
    validate_rows(left, table)
    validate_rows(right, table)
    a = {(r["page"], r["paragraph"]): r for r in left}
    b = {(r["page"], r["paragraph"]): r for r in right}
    disagreements = []
    for page, paragraph in sorted(a.keys() | b.keys()):
        x, y = a.get((page, paragraph)), b.get((page, paragraph))

        def add(kind: str, lhs: object, rhs: object, page: int = page, paragraph: int = paragraph) -> None:
            disagreements.append(
                {
                    "page": page,
                    "paragraph": paragraph,
                    "kind": kind,
                    "left": lhs,
                    "right": rhs,
                    "resolution": None,
                    "resolved_by": None,
                }
            )

        if x is None or y is None:
            add("missing_paragraph", x, y)
            for span in bracketed_spans((x or y)["text"]):
                add("bracketed_span", span if x else None, span if y else None)
            continue
        if x["text"] != y["text"]:
            add("paragraph_text", x["text"], y["text"])
        if x["underlining"] != y["underlining"]:
            add("underlining", x["underlining"], y["underlining"])
        xs, ys = bracketed_spans(x["text"]), bracketed_spans(y["text"])
        matcher = SequenceMatcher(a=[s["text"] for s in xs], b=[s["text"] for s in ys], autojunk=False)
        for tag, i, j, k, l in matcher.get_opcodes():
            if tag != "equal":
                # Each span is listed, even when the opposing seat omitted it.
                for index in range(max(j - i, l - k)):
                    add(
                        "bracketed_span",
                        xs[i + index] if i + index < j else None,
                        ys[k + index] if k + index < l else None,
                    )
    pages = []
    for page in sorted({key[0] for key in a.keys() | b.keys()}):
        summary = {"page": page}
        for side, paragraphs in (("left", a), ("right", b)):
            texts = [r["text"] for key, r in paragraphs.items() if key[0] == page]
            summary[f"{side}_paragraphs"] = len(texts)
            summary[f"{side}_bracketed_spans"] = sum(len(bracketed_spans(t)) for t in texts)
        pages.append(summary)
    return {
        "schema_version": 1,
        "provisional_notation": table["provisional"],
        "pages": pages,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
    }


def render_pages(
    pdf: Path, cache: Path = CACHE_DIR, *, expected_sha256: str = PDF_SHA256, expected_pages: int = 28
) -> dict:
    """Render hash-verified PDF to a Git-ignored cache, recording page hashes and dimensions."""
    payload = pdf.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError("PDF SHA-256 does not match held artifact")
    cache = cache.resolve()
    repo = Path.cwd().resolve()
    try:
        relative = cache.relative_to(repo)
    except ValueError as exc:
        raise ValueError("Cache must be inside the worktree and Git-ignored") from exc
    targets = [relative / "manifest.json"] + [
        relative / f"page-{number:02d}.png" for number in range(1, expected_pages + 1)
    ]
    for target in targets:
        ignored = subprocess.run(["git", "check-ignore", "-q", "--", str(target)], cwd=repo, check=False, timeout=30)
        if ignored.returncode != 0:
            raise ValueError("Cache must be Git-ignored")
    with pymupdf.open(stream=payload, filetype="pdf") as document:
        if len(document) != expected_pages:
            raise ValueError("PDF page count does not match expected denominator")
        cache.mkdir(parents=True, exist_ok=True)
        pages = []
        for number, page in enumerate(document, 1):
            target = cache / f"page-{number:02d}.png"
            pixmap = page.get_pixmap(dpi=300, alpha=False)
            pixmap.save(target)
            pages.append(
                {
                    "page": number,
                    "file": target.name,
                    "width": pixmap.width,
                    "height": pixmap.height,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                }
            )
    manifest = {
        "pdf_sha256": digest,
        "dpi": 300,
        "page_count": len(pages),
        "renderer": f"PyMuPDF {pymupdf.VersionBind}",
        "pages": pages,
    }
    (cache / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render, validate or diff private Pohribnyi transcription inputs.\n"
        "Use before adjudication; this tool does not transcribe or ingest text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.ingest.pohribnyi_tooling render --pdf held.pdf\n"
        "  .venv/bin/python -m scripts.ingest.pohribnyi_tooling validate --input .cache/rows.json\n"
        "  .venv/bin/python -m scripts.ingest.pohribnyi_tooling diff --left .cache/a.json "
        "--right .cache/b.json --output .cache/diff.json\n"
        "Outputs: ignored PNGs/manifest or private JSON diff; no database writes.\n"
        "Exit codes: 0 success (diff may contain disagreements); 1 invalid input.\n"
        "Related: #9604; pohribnyi_notation.json; docs/projects/open-model-data/PLAN.md.",
    )
    parser.add_argument(
        "--notation",
        type=Path,
        default=NOTATION_PATH,
        help="Notation JSON table (default: bundled provisional pohribnyi_notation.json).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="Render the held 28-page PDF at 300 dpi.")
    render.add_argument("--pdf", type=Path, required=True, help="Held PDF path, e.g. held.pdf; SHA checked.")
    render.add_argument(
        "--cache", type=Path, default=CACHE_DIR, help="Git-ignored image directory (default: .cache/pohribnyi)."
    )
    validate = sub.add_parser("validate", help="Validate private paragraph JSON rows.")
    validate.add_argument("--input", type=Path, required=True, help="Paragraph-array JSON, e.g. .cache/rows.json.")
    diff = sub.add_parser("diff", help="List unresolved differences by page, paragraph and bracketed span.")
    diff.add_argument(
        "--left", type=Path, required=True, help="First independent transcription JSON, e.g. .cache/a.json."
    )
    diff.add_argument(
        "--right", type=Path, required=True, help="Second independent transcription JSON, e.g. .cache/b.json."
    )
    diff.add_argument(
        "--output", type=Path, required=True, help="Private diff JSON destination, e.g. .cache/diff.json."
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            report = render_pages(args.pdf, args.cache)
            print(
                json.dumps(
                    {"page_count": report["page_count"], "dpi": report["dpi"], "pdf_sha256": report["pdf_sha256"]}
                )
            )
        else:
            table = load_notation(args.notation)
            if args.command == "validate":
                rows = json.loads(args.input.read_text(encoding="utf-8"))
                validate_rows(rows, table)
                print(json.dumps({"valid_rows": len(rows), "provisional_notation": table["provisional"]}))
            else:
                report = diff_transcriptions(
                    json.loads(args.left.read_text(encoding="utf-8")),
                    json.loads(args.right.read_text(encoding="utf-8")),
                    table,
                )
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(json.dumps({"disagreement_count": report["disagreement_count"]}))
    except (ValueError, OSError) as exc:
        # Validation errors omit private paragraph text.
        parser.exit(1, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
