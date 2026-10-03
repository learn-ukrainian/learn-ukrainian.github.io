"""Independent local PDF boundary proof. Does not import the inventory generator."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import unicodedata
from collections import Counter
from itertools import groupby, pairwise
from pathlib import Path

import pymupdf
import yaml


def clean(text: str, stress_free: bool = False) -> str:
    text = text.replace("c", "с").replace("á", "а\u0301").replace("é", "е\u0301").replace("'", "’").replace("ʼ", "’")
    if stress_free:
        text = text.replace("\u0301", "")
    return " ".join(unicodedata.normalize("NFC", text).split())


def expected(head: str, pos: str, page: int, appendix: bool = False) -> tuple:
    """Independently transcribe lexical notation after boundaries are determined."""
    text = clean(head)
    alternatives = []
    parenthetical = re.search(r"\(([^()]*)\)", text)
    if parenthetical:
        prefix, suffix = text[: parenthetical.start()], text[parenthetical.end() :]
        inside = parenthetical[1]
        if pos == "verb" and len(inside.split()) > 1:
            alternatives = [" ".join(v.split()[1:]) for v in inside.split(",")]
        elif suffix.strip() or not prefix.strip() or (pos == "noun" and len(prefix.strip().split()) == 1):
            alternatives = [prefix + inside + suffix]
        elif pos != "verb":
            alternatives = inside.split(",")
        text = clean(prefix + suffix)
    if "," in text and all(len(v.split()) == 1 for v in text.split(",")):
        spellings = text.split(",")
        text = clean(spellings[0])
        alternatives += spellings[1:]
    lemma = clean(text, True)
    if lemma == "Бувай! Бувайте!":
        text = text.split()[0]
        lemma, alternatives, kind = "бувай", ["бувайте"], "word"
    else:
        kind = "verb_pair_member" if appendix else "phrase" if " " in lemma or re.search(r"[!?,.]", lemma) else "word"
    return (page, kind, lemma, text, tuple(clean(v, True) for v in alternatives), pos)


def line_entries(line: dict, page: int) -> list[tuple]:
    """Find label offsets in a regular-font mask, then consume each bold interval."""
    characters, bold, regular = [], [], []
    for span in line["spans"]:
        for char in span["chars"]:
            characters.append(char["c"])
            bold.append("Bold" in span["font"] and abs(span["size"] - 9) < 0.01)
            regular.append(span["font"] == "ArialMT")
    label_mask = "".join(c if r else " " for c, r in zip(characters, regular, strict=True))
    labels = list(re.finditer(r"(?<![А-Яа-яІіЇїЄєҐґ])(недок|док|прикм|присл|ч|ж|с)\.", label_mask))
    mapping = {"недок": "verb", "док": "verb", "прикм": "adj", "присл": "adv", "ч": "noun", "ж": "noun", "с": "noun"}
    intervals = []
    start = 0
    for label in labels:
        intervals.append((start, label.start(), mapping[label[1]]))
        start = label.end()
    intervals.append((start, len(characters), "unlabelled"))
    result = []
    for start, end, pos in intervals:
        indexes = [i for i in range(start, end) if bold[i] and not characters[i].isspace()]
        if not indexes:
            continue
        first, last = min(indexes), max(indexes)
        # Preserve non-bold lexical separators inside the bold headword interval.
        head = "".join(
            characters[i] for i in range(first, last + 1) if bold[i] or (regular[i] and characters[i] in " ,")
        )
        result.append(expected(head, pos, page))
    return result


def pdf_entries(path: Path) -> tuple[list[tuple], dict]:
    """Use raw character dictionaries, label positions and appendix bold columns."""
    result, pages = [], {}
    with pymupdf.open(path) as document:
        for page in range(200, 224):
            before = len(result)
            lines = [
                line for block in document[page - 1].get_text("rawdict")["blocks"] for line in block.get("lines", [])
            ]
            entry_lines = 0
            for line in lines:
                if page <= 216:
                    entries = line_entries(line, page)
                else:
                    # Select infinitive glyphs by font and physical column, independently
                    # of generator row pairing and whole-line bounding boxes.
                    left, right = [], []
                    for span in line["spans"]:
                        if "Bold" not in span["font"] or abs(span["size"] - 10) > 0.01:
                            continue
                        for char in span["chars"]:
                            x, y = char["bbox"][:2]
                            if y < (380 if page == 217 else 100) or y > 815:
                                continue
                            if 45 < x < 150:
                                left.append(char["c"])
                            elif 245 < x < 350:
                                right.append(char["c"])
                    entries = [
                        expected(text.strip(), "verb", page, True)
                        for column in (left, right)
                        for text in "".join(column).split(",")
                        if text.strip()
                    ]
                if entries:
                    entry_lines += 1
                    result.extend(entries)
            pages[page] = {
                "entry_lines": entry_lines,
                "entries": len(result) - before,
                "non_entry_lines": len(lines) - entry_lines,
            }
    return result, pages


def signature(row: dict) -> tuple:
    return (
        int(row["locator"].split()[0][1:]),
        row["kind"],
        row["lemma"],
        row["stressed"],
        tuple(row.get("variants", [])),
        row["pos"],
    )


def compare(pdf: Path, inventory: Path, seed: int = 9582) -> dict:
    expected_rows, pages = pdf_entries(pdf)
    actual_rows = yaml.safe_load(inventory.read_text())["sources"][0]["headwords"]
    expected_counts = Counter(expected_rows)
    actual_counts = Counter(signature(row) for row in actual_rows)
    missing, extra = expected_counts - actual_counts, actual_counts - expected_counts
    rng = random.Random(seed)
    selected = []
    for page in range(200, 224):
        selected.append(rng.choice([i for i, r in enumerate(actual_rows) if signature(r)[0] == page]))
    for kind in ("phrase", "verb_pair_member"):
        selected.append(rng.choice([i for i, r in enumerate(actual_rows) if r["kind"] == kind and i not in selected]))
    selected.extend(rng.sample([i for i in range(len(actual_rows)) if i not in selected], 100 - len(selected)))
    sample = [
        {
            "lemma": actual_rows[i]["lemma"],
            "page": signature(actual_rows[i])[0],
            "boundary_match": expected_counts[signature(actual_rows[i])] == actual_counts[signature(actual_rows[i])],
        }
        for i in selected
    ]
    return {
        "inventory_sha256": hashlib.sha256(inventory.read_bytes()).hexdigest(),
        "expected_entries": len(expected_rows),
        "actual_entries": len(actual_rows),
        "unexplained_differences": sum(missing.values()) + sum(extra.values()),
        "missing": [[*key, count] for key, count in sorted(missing.items())],
        "extra": [[*key, count] for key, count in sorted(extra.items())],
        "pages": pages,
        "seed": seed,
        "sample_matches": sum(r["boundary_match"] for r in sample),
        "sample": sample,
    }


def raw_glossary_meanings(lines: list[dict], page: int) -> list[tuple[tuple, str]]:
    """Independent character masks: English intervals between lexical heads.

    Label offsets partition multi-entry lines. Italic glyphs belong to the
    preceding head interval; a single shared cell serves preceding empty
    intervals. Headless italic lines continue the preceding cell.
    """
    result = []
    recipients = []
    previous_column = None
    for line in sorted(lines, key=lambda l: (int(l["bbox"][0] >= 270), l["bbox"][1])):
        column = int(line["bbox"][0] >= 270)
        if column != previous_column:
            recipients = []
        previous_column = column
        glyphs = [
            (
                c["c"],
                "Bold" in s["font"] and abs(s["size"] - 9) < 0.01,
                "Italic" in s["font"] and abs(s["size"] - 9) < 0.01,
                s["font"] == "ArialMT",
            )
            for s in line["spans"]
            for c in s["chars"]
        ]
        text = "".join(c if regular else " " for c, _, _, regular in glyphs)
        labels = list(re.finditer(r"(?<![А-Яа-яІіЇїЄєҐґ])(недок|док|прикм|присл|ч|ж|с)\.", text))
        positions = [0, *(m.end() for m in labels), len(glyphs)]
        heads = []
        for begin, end in pairwise(positions):
            bold = [i for i in range(begin, end) if glyphs[i][1] and not glyphs[i][0].isspace()]
            if bold:
                heads.append((min(bold), max(bold)))
        signatures = line_entries(line, page)
        if len(heads) != len(signatures):
            raise ValueError("proof_head_interval_mismatch")
        if heads:
            recipients = []
            pending = []
            for number, ((_, end), signature_value) in enumerate(zip(heads, signatures, strict=True)):
                result.append([signature_value, ""])
                pending.append(len(result) - 1)
                boundary = heads[number + 1][0] if number + 1 < len(heads) else len(glyphs)
                italic = [i for i in range(end + 1, boundary) if glyphs[i][2]]
                english = "".join(glyphs[i][0] for i in range(min(italic), max(italic) + 1)) if italic else ""
                if english.strip():
                    recipients = pending
                    pending = []
                    for index in recipients:
                        result[index][1] += english + " "
            if pending:
                recipients = pending
        else:
            english = "".join(c for c, _, italic, _ in glyphs if italic)
            if english.strip():
                if not recipients:
                    raise ValueError("proof_orphan_meaning_line")
                for index in recipients:
                    result[index][1] += english + " "
    return [(s, " ".join(m.split())) for s, m in result]


def prove_meanings(pdf: Path, inventory: Path, meanings: Path) -> dict:
    """Compare raw glyph boundaries with private JSONL, reporting locators only."""
    public = [r for s in yaml.safe_load(inventory.read_text())["sources"] for r in s["headwords"]]
    private = [json.loads(l) for l in meanings.read_text().splitlines() if l.strip()]
    private_by_locator = {r["locator"]: r for r in private}
    expected_values = []
    expected_locators = {f"{row['locator']}#{i + 1}" for i, row in enumerate(public)}
    unknown_locators = len(set(private_by_locator) - expected_locators)
    invalid_labels = sum(
        expected(
            private_by_locator.get(f"{row['locator']}#{i + 1}", {}).get("printed_label", ""),
            row["pos"],
            int(row["locator"].split()[0][1:]),
            bool(row.get("pair")),
        )
        != signature(row)
        for i, row in enumerate(public)
    )
    accounted = 0
    with pymupdf.open(pdf) as document:
        for page in range(200, 224):
            lines = [l for b in document[page - 1].get_text("rawdict")["blocks"] for l in b.get("lines", [])]
            accounted += len(lines)
            if page <= 216:
                expected_values.extend(raw_glossary_meanings(lines, page))
            else:
                # Build physical rows from left-column bold glyph baselines,
                # not from generator pair ids, text lines or source_lines.
                centres = sorted(
                    {
                        round(c["bbox"][1], 2)
                        for l in lines
                        for s in l["spans"]
                        if "Bold" in s["font"] and abs(s["size"] - 10) < 0.01
                        for c in s["chars"]
                        if 45 < c["bbox"][0] < 150 and (380 if page == 217 else 100) < c["bbox"][1] < 815
                    }
                )
                cells = {centre: {"left": [], "right": [], "meaning": []} for centre in centres}
                for line in lines:
                    for span in line["spans"]:
                        if abs(span["size"] - 10) >= 0.01:
                            continue
                        for char in span["chars"]:
                            x, y = char["bbox"][:2]
                            if not centres or y < (380 if page == 217 else 100) or y > 815:
                                continue
                            centre = min(centres, key=lambda v: abs(v - y))
                            category = (
                                ("left" if 45 < x < 150 else "right" if 245 < x < 350 else None)
                                if "Bold" in span["font"]
                                else "meaning"
                                if "Italic" in span["font"] and x > 445
                                else None
                            )
                            if category:
                                cells[centre][category].append(
                                    (round(line["bbox"][1], 1), len(cells[centre][category]), char["c"])
                                )
                for centre in centres:
                    cell = cells[centre]
                    meaning = " ".join(
                        "".join(c for _, _, c in group)
                        for _, group in groupby(sorted(cell["meaning"]), key=lambda item: item[0])
                    )
                    meaning = " ".join(meaning.split())
                    for side in ("left", "right"):
                        label = " ".join(
                            "".join(c for _, _, c in group)
                            for _, group in groupby(sorted(cell[side]), key=lambda item: item[0])
                        )
                        for head in label.split(","):
                            if head.strip():
                                expected_values.append((expected(head.strip(), "verb", page, True), meaning))
    # Both multisets must account for every entry, including repeated lemmas.
    expected_counts = Counter(expected_values)
    actual_values = [
        (signature(row), private_by_locator.get(f"{row['locator']}#{i + 1}", {}).get("meaning", ""))
        for i, row in enumerate(public)
    ]
    actual_counts = Counter(actual_values)
    mismatches = [
        f"{row['locator']}#{i + 1}"
        for i, row in enumerate(public)
        if i >= len(expected_values) or actual_values[i] != expected_values[i]
    ]
    return {
        "expected_entries": len(expected_values),
        "actual_entries": len(private),
        "accounted_lines": accounted,
        "unexplained_differences": sum((expected_counts - actual_counts).values())
        + sum((actual_counts - expected_counts).values()),
        "duplicate_locators": len(private) - len(private_by_locator),
        "unknown_locators": unknown_locators,
        "invalid_labels": invalid_labels,
        "mismatch_locators": mismatches,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Independently prove A1 reference boundaries against the owned local PDF.\n"
        "Run locally after regeneration; not in CI because the PDF is private.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.ingest.prove_ohoiko_a1_reference --pdf /private/book.pdf "
        "--inventory registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml\n"
        "Outputs: JSON lexical differences, per-page counts and seeded boundary sample to stdout.\n"
        "Exit codes: 0 no differences and 100/100 sample; 1 mismatch; 2 input failure.\nRelated: #9582",
    )
    parser.add_argument("--pdf", type=Path, required=True, help="Owned local workbook PDF, e.g. /private/book.pdf")
    parser.add_argument("--inventory", type=Path, required=True, help="Committed words-only reference YAML to compare")
    parser.add_argument("--seed", type=int, default=9582, help="Stratified 100-entry sample RNG seed (default: 9582)")
    parser.add_argument(
        "--meanings",
        type=Path,
        help="Privately prove JSONL meaning boundaries; output contains counts and locators only",
    )
    args = parser.parse_args(argv)
    try:
        if args.meanings:
            proof = prove_meanings(args.pdf, args.inventory, args.meanings)
            print(json.dumps(proof, ensure_ascii=False))
            return int(
                bool(
                    proof["unexplained_differences"]
                    or proof["mismatch_locators"]
                    or proof["duplicate_locators"]
                    or proof["unknown_locators"]
                    or proof["invalid_labels"]
                )
            )
        proof = compare(args.pdf, args.inventory, args.seed)
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": type(error).__name__}))
        return 2
    print(json.dumps(proof, ensure_ascii=False, indent=2))
    return int(proof["unexplained_differences"] != 0 or proof["sample_matches"] != 100)


if __name__ == "__main__":
    raise SystemExit(main())
