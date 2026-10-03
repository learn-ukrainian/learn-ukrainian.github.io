"""Regenerate lexical rows from an owned local PDF; never retain glosses or prose."""

from __future__ import annotations

import argparse
import re
import sqlite3
import unicodedata
from pathlib import Path

import pymupdf
import yaml

LABEL = re.compile(r"^\s*,?\s*(ч\.|ж\.|с\.|недок\.|док\.|прикм\.|присл\.)")
POS = {"ч.": "noun", "ж.": "noun", "с.": "noun", "недок.": "verb", "док.": "verb", "прикм.": "adj", "присл.": "adv"}
TOKEN = re.compile(r"[А-Яа-яІіЇїЄєҐґ]+(?:[’'-][А-Яа-яІіЇїЄєҐґ]+)*")


def lexical(text: str, *, unstress: bool = False) -> str:
    text = text.translate(str.maketrans({"é": "е́", "á": "а́", "c": "с", "'": "’", "ʼ": "’"}))
    if unstress:
        text = text.replace("\u0301", "")
    return " ".join(unicodedata.normalize("NFC", text).split())


def glossary_groups(spans: list[dict]) -> list[tuple[str, str]]:
    """A POS delimiter closes one entry; spans before that delimiter stay together."""
    groups = []
    head = ""
    pending = ""
    for span in spans:
        text = span["text"]
        if "Arial-Bold" in span["font"] and abs(span["size"] - 9) < 0.1:
            head += pending + text
            pending = ""
        elif head and (label := LABEL.match(text)):
            groups.append((head.rstrip(" ,"), POS[label[1]]))
            head = ""
            pending = ""
        elif head and re.fullmatch(r"[ ,]+", text):
            pending += text
    if head.strip():
        groups.append((head.strip(), "unlabelled"))
    return groups


def headword_fields(head: str, pos: str, page: int, pair: str | None = None) -> dict:
    """Keep parenthetical lexical variants and formulas without example subjects."""
    head = lexical(head)
    variants = []
    if "(" in head:
        match = re.fullmatch(r"(.*?)\((.*?)\)(.*)", head)
        if not match:
            raise ValueError("unparsed headword parentheses")
        base, inside, tail = match.groups()
        if pos == "verb" and " " in inside.strip():
            # A printed subject is not part of the lexical conjugation variant.
            variants = [" ".join(v.strip().split()[1:]) for v in inside.split(",")]
        elif tail.strip() or not base.strip() or (pos == "noun" and " " not in base.strip()):
            variants = [base + inside + tail]
        elif pos != "verb":
            variants = [v.strip() for v in inside.split(",")]
        head = lexical(base + tail)
    # These are alternate spellings, rather than multiword formulas.
    if "," in head and all(" " not in v.strip() for v in head.split(",")):
        head, *spellings = head.split(",")
        variants.extend(spellings)
    farewell = lexical(head, unstress=True) == "Бувай! Бувайте!"
    if farewell:
        printed_farewell, variant = head.split()
        head = printed_farewell.rstrip("!").lower()
        variants = [variant.rstrip("!").lower()]
    head = lexical(head)
    kind = "verb_pair_member" if pair else "phrase" if " " in head or re.search(r"[!?,.]", head) else "word"
    row = {
        "lemma": lexical(head, unstress=True),
        "stressed": head,
        "pos": pos,
        "kind": kind,
        "locator": f"p{page} " + ("Додаток" if pair else "Словничок"),
    }
    if farewell:
        row["stressed"] = printed_farewell
    if variants:
        row["variants"] = [lexical(v, unstress=True) for v in variants]
    if pair:
        row["pair"] = pair
    if kind == "phrase":
        words = TOKEN.findall(row["lemma"])
        for variant in row.get("variants", []):
            words.extend(w for w in TOKEN.findall(variant) if w not in words)
        row["tokens"] = [{"form": w} for w in words]
    return row


def attest(row: dict, connection: sqlite3.Connection) -> None:
    """Attest forms read-only; POS/proper tags must be bound to the selected lemma."""

    def analyses(form):
        form = lexical(form, unstress=True)
        return connection.execute(
            "SELECT lemma, pos, tags FROM forms WHERE word_form IN (?,?,?,?)",
            (form, form.replace("’", "'"), form.lower(), form.lower().replace("’", "'")),
        ).fetchall()

    if row["kind"] == "phrase":
        for token in row["tokens"]:
            token["vesum"] = "found" if analyses(token["form"]) else "missing"
    else:
        found = analyses(row["lemma"])
        bound = [(p, t) for lemma, p, t in found if lexical(lemma, unstress=True).lower() == row["lemma"].lower()]
        row["vesum"] = "found" if found else "missing"
        if row["pos"] == "unlabelled":
            row["vesum_pos"] = sorted({p for p, _ in bound})
        proper = sorted({t for _, t in bound if "prop" in t.split(":")})
        if proper:
            row["vesum_tags"] = proper


def extract(pdf: Path, db: Path) -> tuple[list[dict], list[dict]]:
    """Extract every glossary entry and appendix infinitive, with line accounting."""
    rows, accounting = [], []
    with pymupdf.open(pdf) as document, sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        for page in range(200, 217):
            lines = [line for block in document[page - 1].get_text("dict")["blocks"] for line in block.get("lines", [])]
            lines.sort(key=lambda line: (round(line["bbox"][0] / 270), line["bbox"][1]))
            for number, line in enumerate(lines, 1):
                before = len(rows)
                for head, pos in glossary_groups(line["spans"]):
                    row = headword_fields(head, pos, page)
                    attest(row, connection)
                    rows.append(row)
                accounting.append(
                    {
                        "page": page,
                        "line": number,
                        "entries": list(range(before, len(rows))),
                        "non_entry": None
                        if len(rows) > before
                        else "heading, abbreviation key, continuation or footer",
                    }
                )
        pair_number = 0
        for page in range(217, 224):
            lines = [line for block in document[page - 1].get_text("dict")["blocks"] for line in block.get("lines", [])]
            left, right = [], []
            for number, line in enumerate(lines, 1):
                x, y, end, _ = line["bbox"]
                text = "".join(s["text"] for s in line["spans"]).strip()
                if y < 100 or y > 815 or (page == 217 and y < 380):
                    continue
                # Last infinitive touches the neighbouring stem cell in the text layer.
                if page == 223 and text.startswith("сфотографува́тися"):
                    text, end = "сфотографува́тися", 340
                if re.fullmatch(r"[А-Яа-яІіЇїЄєҐґ́ ,’']+", text):
                    if x > 45 and end < 150:
                        left.append((y, text, number))
                    elif x > 245 and end < 350:
                        right.append((y, text, number))
            used = set()
            for y, head, number in sorted(left):
                pair_number += 1
                before = len(rows)
                mates = sorted((ry, text, n) for ry, text, n in right if abs(ry - y) < 14)
                for text in [head, *(m[1] for m in mates)]:
                    for word in text.split(","):
                        if not word.strip():
                            continue
                        row = headword_fields(word.strip(), "verb", page, f"vp-{pair_number:03d}")
                        attest(row, connection)
                        rows.append(row)
                used.update(m[2] for m in mates)
                accounting.append(
                    {
                        "page": page,
                        "line": number,
                        "right_lines": [m[2] for m in mates],
                        "entries": list(range(before, len(rows))),
                    }
                )
            if used != {m[2] for m in right}:
                raise ValueError("unmapped appendix infinitive cell")
    return rows, accounting


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate words-only A1 reference headwords from the owned PDF.\n"
        "Use locally for #9582 regeneration; never supply unit text or publish the PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.ingest.build_ohoiko_a1_reference --pdf /private/book.pdf "
        "--vesum-db /local/vesum.db --inventory registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml\n"
        "Outputs: replaces headword rows in the existing YAML; databases are read-only.\n"
        "Exit codes: 0 generated; 1 input or extraction failure.\nRelated: #9582; prove_ohoiko_a1_reference",
    )
    parser.add_argument("--pdf", type=Path, required=True, help="Owned local workbook PDF, e.g. /private/book.pdf")
    parser.add_argument("--vesum-db", type=Path, required=True, help="Existing VESUM database, opened read-only")
    parser.add_argument(
        "--inventory", type=Path, required=True, help="Existing YAML inventory whose authored metadata is retained"
    )
    args = parser.parse_args(argv)
    try:
        payload = yaml.safe_load(args.inventory.read_text())
        rows, _ = extract(args.pdf, args.vesum_db)
        payload["sources"][0]["headwords"] = rows
        args.inventory.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=96))
    except (OSError, ValueError, sqlite3.Error) as error:
        print(f"Generation failed: {type(error).__name__}")
        return 1
    print(f"Generated {len(rows)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
