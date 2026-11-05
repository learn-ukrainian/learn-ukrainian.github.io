#!/usr/bin/env python3
"""Rename machinery paths in structured metadata files whose schema is known, failing closed.

Uses the ownership model in ``rename_python.py``. Each known file has a schema here that says
which fields hold repository file paths. Only those fields are rewritten, and only when the map
says the path is a machinery file. Messages and other free text are left as written; a machinery
name in them is reported. A file that does not match its schema is reported and left unchanged.
rename_nonpython.py skips every file listed here.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


def _load_rename_python() -> ModuleType:
    name = "machinery_move_rename_python"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().with_name("rename_python.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rp = _load_rename_python()
MACHINERY, PRODUCT = rp.MACHINERY, rp.PRODUCT
OLD_ROOT, NEW_ROOT = rp.OLD_ROOT, rp.NEW_ROOT
Finding, OwnershipMap, Report = rp.Finding, rp.OwnershipMap, rp.Report


# -- a JSON reader that keeps where each string is ----------------------------


@dataclass(frozen=True)
class JString:
    start: int  # the opening quote
    end: int  # after the closing quote
    value: str
    plain: bool  # no escapes: the source text between the quotes is the value


JValue = object  # dict[str, tuple[JString, JValue]] | list[JValue] | JString | int | float | bool | None
NUMBER = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][-+]?\d+)?")
WHITESPACE = re.compile(r"[ \t\n\r]*")


class JSONShapeError(ValueError):
    """The file is not the JSON its schema expects."""


def parse_json(text: str) -> JValue:
    value, end = _value(text, WHITESPACE.match(text, 0).end())  # type: ignore[union-attr]
    end = WHITESPACE.match(text, end).end()  # type: ignore[union-attr]
    if end != len(text):
        raise JSONShapeError(f"extra data at offset {end}")
    return value


def _value(text: str, i: int) -> tuple[JValue, int]:
    if i >= len(text):
        raise JSONShapeError("unexpected end of file")
    char = text[i]
    if char == '"':
        try:
            value, end = json.decoder.scanstring(text, i + 1)  # type: ignore[attr-defined]
        except json.JSONDecodeError as exc:
            raise JSONShapeError(str(exc)) from exc
        return JString(i, end, value, text[i + 1 : end - 1] == value), end
    if char == "{":
        members: dict[str, tuple[JString, JValue]] = {}
        i = _skip(text, i + 1)
        if text.startswith("}", i):
            return members, i + 1
        while True:
            key, i = _value(text, i)
            if not isinstance(key, JString) or key.value in members:
                raise JSONShapeError(f"bad or repeated key at offset {i}")
            i = _expect(text, _skip(text, i), ":")
            item, i = _value(text, _skip(text, i))
            members[key.value] = (key, item)
            i = _skip(text, i)
            if text.startswith("}", i):
                return members, i + 1
            i = _skip(text, _expect(text, i, ","))
    if char == "[":
        items: list[JValue] = []
        i = _skip(text, i + 1)
        if text.startswith("]", i):
            return items, i + 1
        while True:
            item, i = _value(text, i)
            items.append(item)
            i = _skip(text, i)
            if text.startswith("]", i):
                return items, i + 1
            i = _skip(text, _expect(text, i, ","))
    for word, value in (("true", True), ("false", False), ("null", None)):
        if text.startswith(word, i):
            return value, i + len(word)
    number = NUMBER.match(text, i)
    if number is None:
        raise JSONShapeError(f"unexpected {char!r} at offset {i}")
    return json.loads(number.group(0)), number.end()


def _skip(text: str, i: int) -> int:
    return WHITESPACE.match(text, i).end()  # type: ignore[union-attr]


def _expect(text: str, i: int, char: str) -> int:
    if not text.startswith(char, i):
        raise JSONShapeError(f"expected {char!r} at offset {i}")
    return i + 1


# -- schemas -------------------------------------------------------------------


@dataclass
class Plan:
    """What one file's schema decided: string fields to rename, and references to report."""

    renames: list[JString]
    findings: list[tuple[int, str, str, str, str]]  # (offset, kind, text, detail, target)


def _members(value: JValue, keys: set[str], where: str) -> dict[str, tuple[JString, JValue]]:
    if not isinstance(value, dict) or set(value) != keys:
        found = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise JSONShapeError(f"{where}: expected exactly the keys {sorted(keys)}, found {found}")
    return value


def _string(value: JValue, where: str) -> JString:
    if not isinstance(value, JString):
        raise JSONShapeError(f"{where}: expected a string")
    return value


def path_field(ownership: OwnershipMap, field: JString, plan: Plan) -> None:
    """A field that holds one repository file path."""

    path = field.value
    if not path.startswith(OLD_ROOT + "/"):
        return  # outside scripts/ (or already renamed)
    owner = ownership.files.get(path)
    if owner == PRODUCT:
        return
    if owner == MACHINERY and field.plain:
        plan.renames.append(field)
        return
    detail = "the path has escapes" if owner == MACHINERY else "the map has no such file"
    plan.findings.append(
        (field.start, "unknown_path" if owner is None else "escaped_path", path, detail, owner or "unknown")
    )


def text_field(ownership: OwnershipMap, field: JString, plan: Plan, kind: str) -> None:
    """Free text: left as written; a machinery or unknown scripts name in it is reported."""

    mentions = [ref for ref in rp.text_references(ownership, field.value) if ref.target != PRODUCT]
    if mentions:
        shown = ", ".join(ref.text for ref in mentions)
        plan.findings.append((field.start, kind, shown, "free text is left as written", rp.worst_target(mentions)))


def mypy_baseline(ownership: OwnershipMap, payload: JValue) -> Plan:
    """``scripts/lint/mypy_ratchet.py`` baseline: identity is (path, code, message), so only ``path`` changes.

    A message that names a machinery module will change when mypy reports the renamed module; it is
    reported for the baseline refresh, not edited.
    """

    plan = Plan([], [])
    top = _members(payload, {"schema", "mypy", "entries"}, "top level")
    if _string(top["schema"][1], "schema").value != "mypy-ratchet-baseline.v1":
        raise JSONShapeError("schema: expected mypy-ratchet-baseline.v1")
    _string(top["mypy"][1], "mypy")
    entries = top["entries"][1]
    if not isinstance(entries, list):
        raise JSONShapeError("entries: expected a list")
    for index, entry in enumerate(entries):
        fields = _members(entry, {"path", "code", "message"}, f"entries[{index}]")
        path_field(ownership, _string(fields["path"][1], f"entries[{index}].path"), plan)
        _string(fields["code"][1], f"entries[{index}].code")
        text_field(ownership, _string(fields["message"][1], f"entries[{index}].message"), plan, "message_reference")
    return plan


# Repository path (original layout) -> the schema that reads it.
SCHEMAS: dict[str, Callable[[OwnershipMap, JValue], Plan]] = {
    "scripts/lint/mypy_baseline.json": mypy_baseline,
}


def scan_file(ownership: OwnershipMap, rel: str, text: str, report: Report) -> str | None:
    """Rewrite one known file's path fields; return the new text, or None when nothing changes."""

    schema = SCHEMAS[ownership.original_path(rel)]
    try:
        plan = schema(ownership, parse_json(text))
    except JSONShapeError as exc:
        report.unresolved.append(
            Finding(rel, 1, "schema_mismatch", rel, detail=f"{exc}; nothing in this file was changed", target="unknown")
        )
        return None
    for offset, kind, shown, detail, target in plan.findings:
        report.unresolved.append(
            Finding(rel, text.count("\n", 0, offset) + 1, kind, shown, detail=detail, target=target)
        )
    new_text = text
    for field in sorted(plan.renames, key=lambda f: f.start, reverse=True):
        start = field.start + 1
        new_text = new_text[:start] + NEW_ROOT + new_text[start + len(OLD_ROOT) :]
    for field in plan.renames:
        line = text.count("\n", 0, field.start) + 1
        report.rewrites.append(Finding(rel, line, "path_field", field.value, NEW_ROOT + field.value[len(OLD_ROOT) :]))
    if new_text == text:
        return None
    # Post-condition: the result is valid JSON of the same shape, and a second pass renames nothing.
    second = schema(ownership, parse_json(new_text))
    if second.renames:
        report.unresolved.append(
            Finding(rel, 1, "rewrite_not_applied", rel, detail="paths still pending after the rewrite")
        )
    return new_text


def run(ownership: OwnershipMap, root: Path, targets: Sequence[str], apply: bool) -> Report:
    report = Report("rename_structured", "apply" if apply else "check", ownership.sha256)
    wanted = {Path(t).as_posix().strip("/") for t in targets}
    for original in sorted(SCHEMAS):
        # filter-repo may already have moved it, whatever the map says about the file itself
        candidates = [original, NEW_ROOT + original[len(OLD_ROOT) :]]
        for rel in candidates:
            path = root / rel
            if wanted and not any(rel == w or rel.startswith(w + "/") for w in wanted):
                continue
            if not path.exists() and not path.is_symlink():
                continue
            if path.resolve() != root.resolve().joinpath(rel) or not path.is_file():
                # A symlink on the way (the file or a directory above it) could lead outside --root.
                report.unresolved.append(
                    Finding(
                        rel, 1, "symlinked_path", rel, detail="a symlink on the path; left unchanged", target="unknown"
                    )
                )
                continue
            report.files_scanned += 1
            try:
                text = path.read_text(encoding="utf-8")
                new_text = scan_file(ownership, rel, text, report)
            except Exception as exc:  # one unexpected input must not stop the run or half-write a file
                detail = f"the transform failed ({type(exc).__name__}: {exc}); file left unchanged"
                report.unresolved.append(Finding(rel, 1, "tool_error", rel, detail=detail))
                continue
            if new_text is None:
                continue
            report.files_changed.append(rel)
            if apply:
                rp.write_atomically(path, new_text.encode("utf-8"))
    return report


def build_parser() -> argparse.ArgumentParser:
    known = "\n".join(f"  {path}" for path in sorted(SCHEMAS))
    parser = argparse.ArgumentParser(
        prog="rename_structured.py",
        description=(
            "Rename machinery file paths to lu_machinery in the path fields of known structured metadata files,\n"
            "leave messages as written, and report anything that does not match the file's schema. Use it on a\n"
            "disposable clone during the machinery move; never on the live product tree."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""\
Examples:
  python packaging/machinery-move/rename_structured.py --map ownership.json --root "$CLONE" --check
  python packaging/machinery-move/rename_structured.py --map ownership.json --root "$CLONE" --apply --report st.json

Known files (original layout; the machinery-moved location is read too):
{known}

Rules:
  A path field is renamed when it is exactly a machinery file in the map. Product paths and paths outside
  scripts/ are kept; a scripts/ path the map lacks is reported. A machinery or unknown scripts name in a
  message is reported. A file that is not exactly the expected JSON is reported and left unchanged.
  rename_nonpython.py skips the files listed above.

Exit codes:
  0  no unresolved references
  1  at least one unresolved reference; --apply still wrote every resolved rewrite
  2  usage error, or an unreadable or malformed ownership map

Related:
  packaging/machinery-move/README.md, rename_python.py, rename_nonpython.py.
""",
    )
    rp.add_common_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ownership = OwnershipMap.from_file(args.map)
        report = run(ownership, args.root, args.paths, apply=args.apply)
    except rp.MapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return rp.EXIT_USAGE
    return rp.emit(report, args.report)


if __name__ == "__main__":
    sys.exit(main())
