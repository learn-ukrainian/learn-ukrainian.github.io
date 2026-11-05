#!/usr/bin/env python3
"""Count-check the machinery rename on one frozen tree: soundness, completeness and name fragments.

The checks parse nothing. They compare bytes, find ``scripts`` tokens by regular expressions and look names up
in the ownership map, so they are independent of how the rename tools read Python, shell or text.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

OLD, NEW = b"scripts", b"lu_machinery"
IDENT = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_")
NAME = rb"[A-Za-z_][A-Za-z0-9_]*"
DOTTED = re.compile(NAME + rb"(?:\." + NAME + rb")*")
# A ``scripts`` token: the word, then the characters of a path or a dotted module name; or ``scripts import x``.
TOKEN = re.compile(rb"(?<![A-Za-z0-9_])scripts(?=[./])[A-Za-z0-9_./-]*")
FROM_IMPORT = re.compile(rb"(?<![A-Za-z0-9_])scripts[ \t]+import[ \t]+\(?[ \t]*(" + NAME + rb")")
IMPORT_AFTER = re.compile(rb"[ \t]+import[ \t]+\(?[ \t]*(" + NAME + rb")")
RELATIVE = re.compile(rb"(\.+)(" + DOTTED.pattern + rb")?")
ABSOLUTE = re.compile(rb"lu_machinery(?:\." + NAME + rb")*")
# One import line: indent, module, names. A split turns one ``scripts`` line into one line for each owner.
IMPORT_LINE = re.compile(
    rb"([ \t]*)from[ \t]+((?:scripts|lu_machinery)(?:\."
    + NAME
    + rb")*)[ \t]+import[ \t]+([^\n#()]+?)[ \t]*(?:#[^\n]*)?"
)
# I7: the module operand of an import statement. ``WS`` is Python's inline white space, a backslash continuation
# included. The prefix runs from the start of the logical line to the operand: an optional statement before it
# that ends in ``;`` or ``:`` (``if x: from lib import y``) and holds no ``#``, then the keyword. A plain
# ``import`` may list earlier modules, each with an optional ``as`` alias, before this one.
WS = rb"(?:[ \t\f]|\\\r?\n)"
STATEMENT = rb"(?:[^#]*?[;:])?" + WS + rb"*"
ALIAS = WS + rb"+as" + WS + rb"+" + NAME
FROM_PREFIX = re.compile(STATEMENT + rb"from" + WS + rb"+")
IMPORT_PREFIX = re.compile(
    STATEMENT + rb"import" + WS + rb"+(?:" + DOTTED.pattern + rb"(?:" + ALIAS + rb")?" + WS + rb"*," + WS + rb"*)*"
)
FROM_SUFFIX = re.compile(WS + rb"+import(?![A-Za-z0-9_])")
IMPORT_SUFFIX = re.compile(ALIAS + rb"|" + WS + rb"*(?:[,;#]|\r?\n|\Z)")
MAX_LOGICAL_LINES = 64  # a longer backslash-continued statement is no import operand
QUOTE_LEAD = 8  # how many lines before its entry's line a quoted text may start
# A proper fragment of ``scripts`` next to a quote, a backtick, ``$``, a brace, a backslash or a line end.
NEXT = rb"['\"`${}\\]"
FRAGMENT = re.compile(
    rb"(?<![A-Za-z0-9_])(?:scr|scri|scrip)(?="
    + NEXT
    + rb"|\r?$)|(?:(?<="
    + NEXT
    + rb")|^)(?:ipts|ripts|cripts)(?![A-Za-z0-9_])",
    re.M | re.I,
)


class Owners:
    """Owner lookups in the ownership map: a file, a directory (one owner for every file under it), a module."""

    def __init__(self, files: dict[str, str]) -> None:
        self.files = files
        self.dirs: dict[str, set[str]] = defaultdict(set)
        for path, owner in files.items():
            parts = path.split("/")
            for end in range(1, len(parts)):
                self.dirs["/".join(parts[:end])].add(owner)

    def path(self, path: str) -> str | None:
        path = path.rstrip("/")
        owners = self.dirs.get(path, set())
        return self.files.get(path) or (next(iter(owners)) if len(owners) == 1 else "mixed" if owners else None)

    def module(self, dotted: str, data: bytes = b"", end: int = 0) -> str | None:
        """The longest prefix that is a module or a package; with ``from dotted import x``, ``dotted.x`` first."""

        after = IMPORT_AFTER.match(data, end) if data else None
        names = [dotted + "." + after.group(1).decode(), dotted] if after else [dotted]
        for name in names:
            parts = name.split(".")
            for stop in range(len(parts), 0, -1):
                base = "/".join(parts[:stop])
                owner = self.files.get(base + ".py") or self.files.get(base + "/__init__.py")
                if owner or (stop > 1 and base in self.dirs):
                    return owner or self.path(base)
                if name is not names[-1]:
                    break  # ``dotted.x`` is no module: judge ``dotted`` itself
        return None

    def token(self, data: bytes, start: int) -> tuple[str | None, str]:
        """(owner, text) of the ``scripts`` token at ``start``."""

        if match := TOKEN.match(data, start):
            text = match.group(0).decode("utf-8", "replace").rstrip(".,:;")
            if text.startswith("scripts/"):
                return self.path(text), text
            return self.module(text.split(":")[0], data, start + len(text)), text
        if match := FROM_IMPORT.match(data, start):
            return self.module("scripts", data, start + len(OLD)), " ".join(match.group(0).decode().split())
        return None, "scripts"

    def tokens(self, data: bytes) -> list[int]:
        """Where the machinery tokens of a text start."""

        starts = {m.start() for m in TOKEN.finditer(data)} | {m.start() for m in FROM_IMPORT.finditer(data)}
        return sorted(s for s in starts if self.token(data, s)[0] == "machinery")


def _logical_line_start(data: bytes, offset: int) -> int | None:
    """Where the logical line holding ``data[offset]`` starts: back over backslash continuations, at most
    ``MAX_LOGICAL_LINES`` physical lines; None when it is longer."""

    start = data.rfind(b"\n", 0, offset) + 1
    for _ in range(MAX_LOGICAL_LINES):
        if data.endswith(b"\\\n", 0, start) or data.endswith(b"\\\r\n", 0, start):
            start = data.rfind(b"\n", 0, start - 2) + 1
        else:
            return start
    return None


def import_operand(data: bytes, start: int, end: int, *, plain_import: bool = True) -> bool:
    """I7: whether ``data[start:end]`` is a module operand of an import statement.

    That is the text between ``from`` and ``import``, or one comma-separated module of a plain ``import``
    statement (its ``as`` alias excluded). Names after ``from X import``, aliases and parenthesised imported names
    are no operands. A bounded check by regular expressions: strings and comments are not parsed."""

    line = _logical_line_start(data, start)
    if line is None:
        return False
    if FROM_PREFIX.fullmatch(data, line, start) and FROM_SUFFIX.match(data, end):
        return True
    return plain_import and bool(IMPORT_PREFIX.fullmatch(data, line, start) and IMPORT_SUFFIX.match(data, end))


def _form(owners: Owners, rel: str, a: bytes, b: bytes, i: int, j: int) -> tuple[str, str, str | None, int, int] | None:
    """(form, token, owner, end in a, end in b) of a mapped substitution starting at ``a[i]`` and ``b[j]``.

    ``i`` is the true start of the hit (``substitutions`` steps back over a shared token prefix), so the I7
    context test of the unprefixed and relative forms looks at the bytes in front of the whole operand."""

    if i and a[i - 1] in IDENT:
        return None
    if a.startswith(OLD, i) and b.startswith(NEW, j):
        owner, text = owners.token(a, i)
        return "plain", text, owner, i + len(OLD), j + len(NEW)
    if i and a[i - 1] == 46:  # ``.``: inside a dotted name, so no import token starts here
        return None
    token = DOTTED.match(a, i)
    if token and b.startswith(NEW + b"." + token.group(0), j) and import_operand(a, i, token.end()):
        text = token.group(0).decode()  # an unprefixed import
        return "unprefixed", text, owners.module("scripts." + text, a, token.end()), token.end(), j + 13 + len(text)
    relative, absolute = RELATIVE.match(a, i), ABSOLUTE.match(b, j)
    package = rel.split("/")[:-1]
    if relative and absolute and package[:1] == ["scripts"] and len(relative.group(1)) <= len(package):
        base = package[: len(package) - len(relative.group(1)) + 1]
        rest = relative.group(2).decode().split(".") if relative.group(2) else []
        if absolute.group(0).decode() == ".".join(["lu_machinery", *base[1:], *rest]) and import_operand(
            a,
            i,
            relative.end(),
            plain_import=False,  # a relative module is an operand of ``from`` only
        ):
            owner = owners.module(".".join(["scripts", *base[1:], *rest]), a, relative.end())
            return "relative", relative.group(0).decode(), owner, relative.end(), absolute.end()
    return None


def _split(owners: Owners, a: bytes, b: bytes, i: int, j: int) -> tuple[int, int] | None:
    """(end in a, end in b) when the line at ``a[i]`` is ``from scripts.P import x, y`` and ``b[j]`` starts the
    same import as one line for each owner, with the same indent and names."""

    end_a = _eol(a, i)
    line = IMPORT_LINE.fullmatch(a, i, end_a)
    if (
        line is None
        or b"," not in line.group(3)
        or not line.group(2).startswith(OLD)
        or b.startswith(a[i:end_a] + b"\n", j)
    ):
        return None
    module = line.group(2).decode()
    names = sorted(n.strip() for n in line.group(3).decode().split(","))
    seen: list[str] = []
    k = j
    for _ in names:
        end_b = _eol(b, k)
        out = IMPORT_LINE.fullmatch(b, k, end_b)
        if out is None or out.group(1) != line.group(1) or out.group(2).replace(NEW, OLD, 1).decode() != module:
            return None
        for name in (n.strip() for n in out.group(3).decode().split(",")):
            machinery = owners.module(module + "." + name.split(" as ")[0]) == "machinery"
            if machinery != out.group(2).startswith(NEW):
                return None
            seen.append(name)
        if sorted(seen) == names:
            return (end_a, end_b) if k > j else None
        k = end_b + 1
    return None


def substitutions(
    owners: Owners, rel: str, a: bytes, b: bytes
) -> tuple[list[tuple[int, str, str, str | None]], list[tuple[int, int]], int | None]:
    """The mapped substitutions that turn ``a`` into ``b`` as (offset in a, form, token, owner); the spans in ``b``
    that splits produced; and the offset in ``a`` of the first change that is no mapped substitution, or None."""

    i = j = 0
    found: list[tuple[int, str, str, str | None]] = []
    split_spans: list[tuple[int, int]] = []
    while i < len(a) or j < len(b):
        if (i == 0 or a[i - 1] == 10) and (split := _split(owners, a, b, i, j)):
            found.append((i, "split", a[i : split[0]].decode().strip(), "machinery"))
            split_spans.append((j, split[1]))
            i, j = split
        elif i < len(a) and j < len(b) and a[i] == b[j]:
            i, j = i + 1, j + 1
        else:
            back = 0  # the change may start inside a token prefix both texts share (``lib`` -> ``lu_machinery.lib``)
            while (
                not (hit := _form(owners, rel, a, b, i - back, j - back))
                and back < min(i, j, 64)
                and a[i - back - 1] in IDENT
            ):
                back += 1
            if not hit:
                return found, split_spans, i
            found.append((i - back, *hit[:3]))
            i, j = hit[3], hit[4]
    return found, split_spans, None


def _eol(data: bytes, start: int) -> int:
    end = data.find(b"\n", start)
    return len(data) if end < 0 else end


def _line(data: bytes, offset: int) -> int:
    return data.count(b"\n", 0, offset) + 1


def _canon(text: str) -> str:
    """One spelling for a name: ``scripts import x`` (a ``from scripts import x`` token) is ``scripts.x``."""

    return re.sub(r"^scripts import \(? ?", "scripts.", text)


def _line_starts(data: bytes) -> list[int]:
    return [0, *(m.end() for m in re.finditer(rb"\n", data))]


def _matches(data: bytes, starts: list[int], line: int, shown: bytes) -> list[list[int]]:
    """Each match of an entry's quoted text that holds a byte of ``line``, as the offset in ``data`` of each byte
    of it. A match may start up to ``QUOTE_LEAD`` lines earlier: a tool gives a parenthesised expression the line
    of what is inside, and quotes the ``(`` before it.

    The tools quote source text with its white space collapsed, so a quoted space matches any white space or
    none."""

    words = shown.split()
    if not words or not 1 <= line <= len(starts):
        return []
    begin, end, found = starts[line - 1], _eol(data, starts[line - 1]), []
    pattern = re.compile(rb"\s*".join(re.escape(word) for word in words))
    for match in pattern.finditer(data, starts[max(0, line - 1 - QUOTE_LEAD)]):
        if match.start() > end:
            break
        if match.end() <= begin:
            continue
        where, k = [], match.start()
        for char in shown:
            while char == 32 and data[k : k + 1].isspace():
                k += 1
            where.append(k)
            k += char != 32
        found.append(where)
    return found


Entry = tuple[int, int, str, str, list[tuple[int, str, bool]]]  # report, line, quoted text, kind, tokens


def residue_entries(owners: Owners, reports: list[dict]) -> dict[str, list[Entry]]:
    """I8: the residue entries of each file with their mentions. A mention is one token inside one entry's
    quoted ``before`` text, as (offset in that text, token, whether it names machinery).

    An unresolved entry, and an inventory entry without ``after``, is residue: its text is left as written. An
    inventory entry with ``after`` records a rewrite that was applied, so it is no residue."""

    found: dict[str, list[Entry]] = defaultdict(list)
    for number, report in enumerate(reports):
        for entry in report["unresolved"] + [entry for entry in report["inventory"] if "after" not in entry]:
            shown = " ".join((entry.get("before") or "").split())
            data = shown.encode()
            tokens = []
            for start in sorted(
                {m.start() for m in TOKEN.finditer(data)} | {m.start() for m in FROM_IMPORT.finditer(data)}
            ):
                owner, text = owners.token(data, start)
                tokens.append((start, _canon(text), owner == "machinery"))
            if tokens:
                found[entry["path"]].append((number, int(entry["line"]), shown, entry["kind"], tokens))
    return found


def match_residue(
    rel: str, a: bytes, b: bytes, occurrences: list[tuple[int, str]], entries: list[Entry]
) -> tuple[list[dict], list[dict]]:
    """I8: every output occurrence of an old name consumes exactly one residue mention of its file.

    Each mention is placed at its token's offset in the input file by finding the entry's quoted text on the
    entry's line, longer entries first: at the first match whose tokens its own report has placed least often.
    Mentions at one offset with one token are one occurrence, however many entries or reports quote it (an
    expression and a literal inside it, say), and equal entries of one report on one line take successive
    matches. A mention whose text is not found there covers nothing (a machinery one is unbalanced). Occurrences and mentions pair by token text in
    file order, not by line, so line shifts do not matter. Returns what is left on each side: (unreported
    occurrences, unbalanced machinery mentions)."""

    starts = _line_starts(a)
    order: dict[tuple[int, str], tuple[int, bool, str]] = {}  # (offset in a, token) -> (line, machinery, kind)
    unbalanced: list[dict] = []
    placed: dict[int, set[int]] = defaultdict(set)  # report -> token offsets in a its entries took
    for number, line, shown, kind, tokens in sorted(entries, key=lambda entry: -len(entry[2])):
        matches = _matches(a, starts, line, shown.encode())
        if not matches:  # fail closed: a mention not found where its entry says covers nothing
            unbalanced += [
                {"path": rel, "line": line, "token": text, "kind": kind, "reason": "the quoted text is not there"}
                for _start, text, machinery in tokens
                if machinery
            ]
            continue
        where = min(matches, key=lambda where: sum(where[start] in placed[number] for start, _t, _m in tokens))
        for start, text, machinery in tokens:
            placed[number].add(where[start])
            order.setdefault((where[start], text), (line, machinery, kind))
    side: dict[str, list[tuple[int, int, bool, str]]] = defaultdict(list)
    for (offset, text), (line, machinery, kind) in order.items():
        side[text].append((offset, line, machinery, kind))
    used: Counter[str] = Counter()
    unreported = []
    for offset, text in occurrences:  # in file order
        if used[text] < len(side[text]):
            used[text] += 1
        else:
            unreported.append({"path": rel, "line": _line(b, offset), "token": text})
    unbalanced += [
        {"path": rel, "line": line, "token": text, "kind": kind, "reason": "no occurrence is left for it"}
        for text, mentions in side.items()
        for _offset, line, machinery, kind in sorted(mentions)[used[text] :]
        if machinery
    ]
    return unreported, unbalanced


def _files(root: Path) -> set[str]:
    found = set()
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        found |= {
            (Path(directory) / n).relative_to(root).as_posix()
            for n in filenames
            if not (Path(directory) / n).is_symlink()
        }
    return found


def check(owners: Owners, before: Path, after: Path, reports: list[dict]) -> dict:
    entry_lines: dict[str, set[int]] = defaultdict(set)
    for report in reports:
        for entry in report["unresolved"] + report["inventory"]:
            entry_lines[entry["path"]].add(int(entry["line"]))
    residue = residue_entries(owners, reports)
    unsound, incomplete, uncovered, unbalanced, fragments = [], [], [], [], []
    forms: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    inputs, outputs = _files(before), _files(after)
    for rel in sorted(inputs | outputs):
        if rel not in inputs or rel not in outputs:
            unsound.append({"path": rel, "reason": "the file is only in one tree"})
            continue
        a, b = (before / rel).read_bytes(), (after / rel).read_bytes()
        fragments += [
            {
                "path": rel,
                "line": _line(a, m.start()),
                "fragment": m.group(0).decode("utf-8", "replace"),
                "covered": _line(a, m.start()) in entry_lines[rel],
            }
            for m in FRAGMENT.finditer(a)
        ]
        if OLD not in a and a == b:
            unbalanced += match_residue(rel, a, b, [], residue.get(rel, []))[1]
            continue
        subs, split_spans, failed = substitutions(owners, rel, a, b) if a != b else ([], [], None)
        if failed is not None:
            unsound.append({"path": rel, "line": _line(a, failed), "reason": "a change that is no mapped substitution"})
            continue
        for offset, form, text, owner in subs:
            forms[form] += 1
            if owner != "machinery":
                unsound.append(
                    {
                        "path": rel,
                        "line": _line(a, offset),
                        "form": form,
                        "token": text,
                        "owner": owner,
                        "reason": "not a machinery name",
                    }
                )
        split_lines = {_line(a, offset) for offset, form, _t, _o in subs if form == "split"}
        left_in = [o for o in owners.tokens(a) if _line(a, o) not in split_lines]
        left_out = [o for o in owners.tokens(b) if not any(s <= o < e for s, e in split_spans)]
        plain = sum(1 for _o, form, _t, owner in subs if form == "plain" and owner == "machinery")
        totals.update(input_tokens=len(left_in), plain=plain, output_tokens=len(left_out))
        if len(left_in) != plain + len(left_out):
            incomplete.append({"path": rel, "input": len(left_in), "plain": plain, "output": len(left_out)})
        occurrences = [(offset, _canon(owners.token(b, offset)[1])) for offset in left_out]
        unreported, left = match_residue(rel, a, b, occurrences, residue.get(rel, []))
        uncovered += unreported
        unbalanced += left
    unbalanced += [
        {"path": rel, "line": line, "token": text, "kind": kind, "reason": "the file is in no tree"}
        for rel in sorted(set(residue) - inputs - outputs)
        for _n, line, _s, kind, tokens in residue[rel]
        for _start, text, machinery in tokens
        if machinery
    ]
    return {
        "totals": dict(totals),
        "substitutions": dict(forms),
        "unsound": unsound,
        "incomplete": incomplete,
        "uncovered": uncovered,
        "unbalanced_mentions": unbalanced,
        "fragments": fragments,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_rename_counts.py",
        description=(
            "Count-check one run of the machinery rename tools on a frozen tree: every change is a mapped\n"
            "substitution, and every machinery name left is reported. Use it after --apply on a disposable copy."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python packaging/machinery-move/check_rename_counts.py --tree-sha "$SHA" --map ownership.json \\
      --input "$FROZEN" --output "$APPLIED" --report py.json --report np.json --report st.json --out counts.json

Checks (no parsing: bytes, regular expressions and the map):
  soundness     every difference between --input and --output is one mapped substitution with identical
                bytes around it: scripts -> lu_machinery at a token that names machinery (plain); T ->
                lu_machinery.T where scripts.T is a machinery module (unprefixed import); a relative module ->
                lu_machinery.<the module it names from the file's path> (relative import); one line
                `from scripts.P import x, y` -> one line for each owner with the same indent and names (split).
                I7: an unprefixed or relative substitution is sound only as the module operand of an import
                statement: the text between `from` and `import`, or one comma-separated module of a plain
                `import` (its `as` alias excluded; relative only after `from`). The keyword starts the logical
                line after indentation, `;` or a one-line `if x:`, and may be followed by a backslash
                continuation. Imported names, aliases, parenthesised names and every other place are unsound.
  completeness  per file, machinery tokens in --input = plain substitutions + machinery tokens in --output.
                I8: every machinery token left in --output consumes exactly one residue mention: one token
                inside the quoted `before` text of one unresolved entry, or of one inventory entry without
                `after` (an entry with `after` records an applied rewrite). Each mention is placed in --input by
                finding its entry's text on the entry's line; one occurrence quoted by several entries or reports
                counts once, and a mention not found there covers nothing. Tokens and mentions pair by text in
                file order, never by line. A token left over is uncovered; a machinery mention left over or not
                found (a name the tools rewrote, or text not in the file) is an unbalanced mention.
  fragments     every proper fragment of scripts (scr, scri, scrip at a word start; ipts, ripts, cripts at a
                word end) next to a quote, a backtick, $, a brace, a backslash or a line end in --input, and
                whether an entry covers its line (listed; it does not change the exit code).

Outputs:
  stdout: the tree SHA and a JSON summary (counts only). --out: the summary with every failure and fragment,
  each with its file and line, as JSON.

Exit codes:
  0  soundness and completeness hold
  1  at least one unsound change, unbalanced file or uncovered machinery token
  2  usage error, or an unreadable map, tree or report
  3  only unbalanced mentions: a residue entry names a machinery token that is not left in --output

Related:
  packaging/machinery-move/README.md, rename_python.py, rename_nonpython.py, rename_structured.py;
  decision FROZEN-INPUT-1105 (acceptance on one frozen tree).
""",
    )
    parser.add_argument(
        "--tree-sha", required=True, help="the commit the frozen --input tree was exported from; printed"
    )
    parser.add_argument("--map", type=Path, required=True, help="the ownership map JSON the tools ran with")
    parser.add_argument("--input", type=Path, required=True, help="the frozen tree before the tools ran (a directory)")
    parser.add_argument(
        "--output", type=Path, required=True, help="a copy of that tree after --apply of all three tools"
    )
    parser.add_argument(
        "--report", type=Path, action="append", required=True, help="a tool's --report JSON; repeat per tool"
    )
    parser.add_argument("--out", type=Path, required=True, help="where to write the full result as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        owners = Owners(json.loads(args.map.read_text(encoding="utf-8")))
        reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.report]
        if not (args.input.is_dir() and args.output.is_dir()):
            raise OSError("--input and --output must be directories")
        result = check(owners, args.input, args.output, reports)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = {"tree_sha": args.tree_sha, **{k: result[k] for k in ("totals", "substitutions")}}
    summary |= {k: len(result[k]) for k in ("unsound", "incomplete", "uncovered", "unbalanced_mentions", "fragments")}
    summary["fragments_uncovered"] = sum(1 for f in result["fragments"] if not f["covered"])
    args.out.write_text(json.dumps({"summary": summary, **result}, indent=1) + "\n", encoding="utf-8")
    print(f"tree {args.tree_sha}")
    print(json.dumps(summary, indent=1))
    if result["unsound"] or result["incomplete"] or result["uncovered"]:
        return 1
    return 3 if result["unbalanced_mentions"] else 0


if __name__ == "__main__":
    sys.exit(main())
