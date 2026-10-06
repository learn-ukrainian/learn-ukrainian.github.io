"""Regenerate public lexical rows or extract host-local private reference meanings."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import pymupdf
import yaml

try:
    from scripts.lib.readonly_sqlite import SQLiteConnection
    from scripts.lib.readonly_sqlite import open_readonly as _open_readonly
except ModuleNotFoundError as exc:
    # Script execution puts the script directory on sys.path, so the
    # top-level package is absent (exc.name == "scripts"). Any other
    # import failure must propagate.
    if exc.name != "scripts":
        raise
    # lib.readonly_sqlite lives in scripts/, which file execution does not put on sys.path.
    _scripts_dir = next(
        parent for parent in Path(__file__).resolve().parents if parent.name == "scripts"
    )
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from lib.readonly_sqlite import SQLiteConnection  # type: ignore[no-redef]
    from lib.readonly_sqlite import open_readonly as _open_readonly  # type: ignore[no-redef]

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


def attest(row: dict, connection: SQLiteConnection) -> None:
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
    with pymupdf.open(pdf) as document, _open_readonly(db) as connection:
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


def private_glossary(lines: list[dict], page: int) -> tuple[list[dict], list[dict]]:
    """Consume italic meaning spans up to the next printed bold entry.

    Column changes close entries. Wrapped italic lines continue the active
    entry; a new bold entry on the same line closes the preceding one.
    Every physical line receives an entry, continuation or non-entry class.
    """
    entries, accounting = [], []
    active = None
    column = None
    pending = []
    recipients = []
    for number, line in enumerate(lines, 1):
        current_column = round(line["bbox"][0] / 270)
        if column != current_column:
            active = None
            pending = []
            recipients = []
        column = current_column
        touched = []
        started = False
        for span in line["spans"]:
            if abs(span["size"] - 9) >= 0.1:
                continue
            text = span["text"]
            if "Arial-Bold" in span["font"]:
                if active is None or active["meaning"] or active.get("labelled"):
                    active = {"head": "", "meaning": "", "lines": [], "page": page}
                    entries.append(active)
                    pending.append(active)
                    recipients = []
                    started = True
                active["head"] += text
            elif active and "Italic" in span["font"]:
                if not recipients:
                    recipients, pending = pending, []
                for recipient in recipients:
                    recipient["meaning"] += text
                    if number not in recipient["lines"]:
                        recipient["lines"].append(number)
            elif active and LABEL.match(text):
                active["labelled"] = True
            elif active and not active["meaning"] and re.fullmatch(r"[ ,]+", text):
                active["head"] += text
            elif active and active["meaning"]:
                for recipient in recipients:
                    recipient["meaning"] += text
            if active is not None:
                if number not in active["lines"]:
                    active["lines"].append(number)
                if len(entries) - 1 not in touched:
                    touched.append(len(entries) - 1)
        for recipient in recipients:
            recipient["meaning"] = recipient["meaning"].rstrip() + " "
        accounting.append(
            {
                "page": page,
                "line": number,
                "entries": touched,
                "classification": "entry" if started else "continuation" if touched else "non_entry",
            }
        )
    if any(not e["meaning"].strip() for e in entries):
        raise ValueError("private_meaning_boundary_missing")
    return entries, accounting


def extract_private(pdf: Path, inventory: Path) -> tuple[list[dict], list[dict]]:
    """Extract private meanings without mutating the public lexical inventory."""
    public = [r for s in yaml.safe_load(inventory.read_text())["sources"] for r in s["headwords"]]
    by_page = {}
    for index, row in enumerate(public):
        page = int(row["locator"].split()[0][1:])
        by_page.setdefault(page, []).append((index, row))
    output, accounting = [], []
    with pymupdf.open(pdf) as document:
        for page, records in sorted(by_page.items()):
            lines = [line for block in document[page - 1].get_text("dict")["blocks"] for line in block.get("lines", [])]
            if page <= 216:
                lines.sort(key=lambda l: (round(l["bbox"][0] / 270), l["bbox"][1]))
                entries, accounted = private_glossary(lines, page)
                accounting.extend(accounted)
                if len(entries) != len(records):
                    raise ValueError("private_glossary_count_mismatch")
                for (index, row), entry in zip(records, entries, strict=True):
                    # The public parser already resolves printed lexical variants.
                    parsed = headword_fields(entry["head"].strip(" ,"), row["pos"], page)
                    if parsed["stressed"] != row["stressed"]:
                        raise ValueError("private_glossary_label_mismatch")
                    output.append(
                        {
                            "locator": f"{row['locator']}#{index + 1}",
                            "printed_label": entry["head"].strip(" ,"),
                            "inventory_label": row["stressed"],
                            "meaning": " ".join(entry["meaning"].split()),
                            "source_lines": entry["lines"],
                        }
                    )
            else:
                # Appendix rows share one italic English cell across both aspects.
                heads = []
                for n, line in enumerate(lines, 1):
                    x, y, end, _ = line["bbox"]
                    text = "".join(s["text"] for s in line["spans"]).strip()
                    if y < (380 if page == 217 else 100) or y > 815:
                        continue
                    if x > 45 and end < 150 and re.fullmatch(r"[А-Яа-яІіЇїЄєҐґ́ ,’']+", text):
                        heads.append((y, text, n))
                heads.sort()
                groups = {}
                for index, row in records:
                    groups.setdefault(row["pair"], []).append((index, row))
                if len(heads) != len(groups):
                    raise ValueError("private_appendix_count_mismatch")
                used = set()
                for offset, ((y, _, head_line), group) in enumerate(zip(heads, groups.values(), strict=True)):
                    low = (heads[offset - 1][0] + y) / 2 if offset else y - 20
                    high = (heads[offset + 1][0] + y) / 2 if offset + 1 < len(heads) else y + 20
                    meaning_lines = [
                        (n, l)
                        for n, l in enumerate(lines, 1)
                        if low < l["bbox"][1] < high
                        and l["bbox"][0] > 445
                        and any("Italic" in s["font"] and abs(s["size"] - 10) < 0.1 for s in l["spans"])
                    ]
                    meaning_lines.sort(key=lambda pair: pair[1]["bbox"][1])
                    meaning = " ".join(
                        "".join(s["text"] for s in l["spans"] if "Italic" in s["font"]).strip()
                        for _, l in meaning_lines
                    )
                    if not meaning:
                        raise ValueError("private_appendix_meaning_missing")
                    used.update(n for n, _ in meaning_lines)
                    used.add(head_line)
                    for index, row in group:
                        output.append(
                            {
                                "locator": f"{row['locator']}#{index + 1}",
                                "printed_label": row["stressed"],
                                "meaning": " ".join(meaning.split()),
                                "source_lines": [n for n, _ in meaning_lines],
                            }
                        )
                used.update(
                    n
                    for n, l in enumerate(lines, 1)
                    if (380 if page == 217 else 100) < l["bbox"][1] < 815
                    and any(
                        "Bold" in s["font"]
                        and abs(s["size"] - 10) < 0.1
                        and (45 < s["bbox"][0] < 150 or 245 < s["bbox"][0] < 350)
                        for s in l["spans"]
                    )
                )
                accounting.extend(
                    {"page": page, "line": n, "classification": "entry_or_meaning" if n in used else "non_entry"}
                    for n in range(1, len(lines) + 1)
                )
    if len(output) != len(public):
        raise ValueError("private_inventory_coverage_invalid")
    return output, accounting


def require_private_path(path: Path, repo: Path) -> None:
    """Reject supplied and resolved paths in linked or primary Git trees."""
    import os
    import subprocess

    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    if any(
        candidate.is_relative_to(root)
        for candidate in (Path(os.path.abspath(path)), path.resolve())
        for root in (Path(common).parent, repo.resolve())
    ):
        raise ValueError("private_output_inside_repository")


def write_private(path: Path, rows: list[dict], repo: Path) -> None:
    """Private data must remain outside both linked and primary Git trees."""
    from scripts.curriculum.evidence.lock import atomic_write

    require_private_path(path, repo)
    atomic_write(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode(), mode=0o600)


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
    parser.add_argument("--vesum-db", type=Path, help="Existing VESUM database, opened read-only")
    parser.add_argument(
        "--inventory", type=Path, required=True, help="Existing YAML inventory whose authored metadata is retained"
    )
    parser.add_argument(
        "--private-meanings", type=Path, help="Write private JSONL outside Git instead of regenerating inventory"
    )
    args = parser.parse_args(argv)
    try:
        if args.private_meanings:
            rows, accounting = extract_private(args.pdf, args.inventory)
            write_private(args.private_meanings, rows, Path.cwd())
            print(f"Generated {len(rows)} private entries; accounted {len(accounting)} lines")
            return 0
        if not args.vesum_db:
            raise ValueError("vesum_database_required")
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
