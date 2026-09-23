#!/usr/bin/env python3
"""Generate the per-level accepted-decisions record from the accepted documents.

The review manifests (docs/epics/fresh-build-review-contracts.md) hand the
reviewer "the record of decisions the operator accepted for this level". That
content lives as prose sections in several documents. This script copies those
sections, verbatim, into curriculum/l2-uk-en/lesson-plans/<level>/_decisions.yaml
so the record has one hashable file.

The record is a copy, never a summary: each source section is taken byte-for-byte
from its heading line up to (not including) the next heading of the same or a
higher level, normalised only to LF line endings. Which sections, and the
acceptance date plus the verbatim line that evidences it, come from the explicit
map scripts/curriculum/arc/decision_sources.yaml. A heading that matches zero or
several lines, or an evidence line that is absent from its document, fails
generation with a named error — never an empty or guessed entry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[3]

SOURCES_REL = "scripts/curriculum/arc/decision_sources.yaml"
SCHEMA_REL = "schemas/decisions-record-v1.schema.json"
OUT_REL = "curriculum/l2-uk-en/lesson-plans/{level}/_decisions.yaml"
GENERATOR_REL = "scripts/curriculum/arc/generate_decisions.py"
SUPPORTED_LEVELS = ("a1", "a2", "b1", "b2")

HEADING_RE = re.compile(r"^(#{1,6}) \S")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class DecisionsGenerationError(Exception):
    """A source section, its acceptance evidence, or the source map is unusable."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel_or_abs(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve(doc: str, overrides: dict[str, Path]) -> Path:
    if doc in overrides:
        return overrides[doc]
    path = Path(doc)
    return path if path.is_absolute() else REPO_ROOT / path


def _read_doc(doc: str, overrides: dict[str, Path]) -> bytes:
    path = _resolve(doc, overrides)
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise DecisionsGenerationError(f"source document {doc!r} does not exist at {path}") from exc


def _lf_lines(doc_bytes: bytes, doc: str) -> list[str]:
    try:
        text = doc_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DecisionsGenerationError(f"{doc!r} is not valid UTF-8: {exc}") from exc
    return text.replace("\r\n", "\n").splitlines(keepends=True)


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line index, level, line without newline) of every heading outside fenced code."""
    found: list[tuple[int, int, str]] = []
    fence: str | None = None
    for index, line in enumerate(lines):
        stripped = line.rstrip("\n")
        fence_match = FENCE_RE.match(stripped)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker[0] * len(marker)
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        heading = HEADING_RE.match(stripped)
        if heading:
            found.append((index, len(heading.group(1)), stripped))
    return found


def extract_section(doc_bytes: bytes, doc: str, heading: str) -> str:
    """Return the verbatim body of one section: its heading line to the next heading of the same or higher level."""
    lines = _lf_lines(doc_bytes, doc)
    headings = _headings(lines)
    matches = [item for item in headings if item[2] == heading]
    if not matches:
        raise DecisionsGenerationError(f"heading {heading!r} matches no line in {doc!r}")
    if len(matches) > 1:
        numbers = ", ".join(str(item[0] + 1) for item in matches)
        raise DecisionsGenerationError(f"heading {heading!r} is ambiguous in {doc!r}: matches lines {numbers}")
    start, level, _ = matches[0]
    end = len(lines)
    for index, other_level, _ in headings:
        if index > start and other_level <= level:
            end = index
            break
    return "".join(lines[start:end])


def _check_evidence(evidence: dict[str, Any], accepted: str, overrides: dict[str, Path]) -> None:
    doc, line = evidence["doc"], evidence["line"]
    doc_lines = [item.rstrip("\n") for item in _lf_lines(_read_doc(doc, overrides), doc)]
    count = doc_lines.count(line)
    if count != 1:
        raise DecisionsGenerationError(
            f"acceptance evidence line {line!r} occurs {count} times in {doc!r}; it must occur exactly once"
        )
    if accepted not in line:
        raise DecisionsGenerationError(
            f"acceptance evidence line in {doc!r} does not state the date {accepted}: {line!r}"
        )


def load_sources(sources_path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DecisionsGenerationError(f"source map {sources_path} does not exist") from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise DecisionsGenerationError(f"{sources_path}: expected a mapping with `schema: 1`")
    if not isinstance(data.get("levels"), dict) or not isinstance(data.get("shared"), list):
        raise DecisionsGenerationError(f"{sources_path}: expected `levels:` (mapping) and `shared:` (list)")
    return data


def _validate_entry(entry: Any, where: str) -> None:
    if not isinstance(entry, dict) or set(entry) != {"doc", "heading", "accepted", "accepted_evidence"}:
        raise DecisionsGenerationError(f"{where}: entry needs exactly doc, heading, accepted, accepted_evidence")
    if not all(isinstance(entry[key], str) and entry[key] for key in ("doc", "heading", "accepted")):
        raise DecisionsGenerationError(f"{where}: doc, heading and accepted must be non-empty strings (quote dates)")
    if not DATE_RE.match(entry["accepted"]):
        raise DecisionsGenerationError(f"{where}: accepted must be YYYY-MM-DD, got {entry['accepted']!r}")
    evidence = entry["accepted_evidence"]
    if (
        not isinstance(evidence, dict)
        or set(evidence) != {"doc", "line"}
        or not all(isinstance(evidence[key], str) and evidence[key] for key in ("doc", "line"))
    ):
        raise DecisionsGenerationError(f"{where}: accepted_evidence needs exactly non-empty doc and line strings")


def render_record(
    level: str,
    sources: dict[str, Any],
    generator_sha256: str,
    overrides: dict[str, Path] | None = None,
) -> str:
    """Render the full _decisions.yaml text for one level."""
    overrides = overrides or {}
    if level not in sources["levels"]:
        raise DecisionsGenerationError(f"level {level!r} has no entry under `levels:` in the source map")
    entries = list(sources["levels"][level]) + list(sources["shared"])
    records = []
    for position, entry in enumerate(entries, start=1):
        _validate_entry(entry, f"source #{position} of level {level!r}")
        doc_bytes = _read_doc(entry["doc"], overrides)
        text = extract_section(doc_bytes, entry["doc"], entry["heading"])
        _check_evidence(entry["accepted_evidence"], entry["accepted"], overrides)
        records.append(
            {
                "doc": entry["doc"],
                "heading": entry["heading"],
                "accepted": entry["accepted"],
                "accepted_evidence": {
                    "doc": entry["accepted_evidence"]["doc"],
                    "line": entry["accepted_evidence"]["line"],
                },
                "doc_sha256": _sha256(doc_bytes),
                "section_sha256": _sha256(text.encode("utf-8")),
                "text": text,
            }
        )
    data = {
        "schema": 1,
        "generator": {"path": GENERATOR_REL, "sha256": generator_sha256},
        "level": level,
        "sources": records,
    }
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda err: list(err.absolute_path))
    if errors:
        raise DecisionsGenerationError(
            "generated record violates "
            + SCHEMA_REL
            + ": "
            + "; ".join(f"{'/'.join(map(str, err.absolute_path)) or '<root>'}: {err.message[:120]}" for err in errors)
        )
    rendered = yaml.dump(data, Dumper=_LiteralDumper, sort_keys=False, allow_unicode=True, width=10**6)
    _verify_round_trip(rendered, data)
    return rendered


class _LiteralDumper(yaml.SafeDumper):
    """SafeDumper that writes multi-line strings as literal blocks."""


def _represent_str(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|" if "\n" in value else None)


_LiteralDumper.add_representer(str, _represent_str)


def _verify_round_trip(rendered: str, data: dict[str, Any]) -> None:
    """The YAML must load back to exactly the data, with every `text` as a literal block."""
    if yaml.safe_load(rendered) != data:
        raise DecisionsGenerationError("rendered YAML does not load back to the generated data (verbatim copy broken)")
    literal_lines = sum(1 for line in rendered.splitlines() if re.fullmatch(r"  text: \|[+-]?\d*", line))
    if literal_lines != len(data["sources"]):
        raise DecisionsGenerationError(
            "a section could not be written as a YAML literal block (trailing whitespace or control characters in the source?)"
        )


def _parse_doc_overrides(values: list[str]) -> dict[str, Path]:
    overrides: dict[str, Path] = {}
    for value in values:
        rel, sep, path = value.partition("=")
        if not sep or not rel or not path:
            raise DecisionsGenerationError(f"--doc expects REL=PATH, got {value!r}")
        overrides[rel] = Path(path)
    return overrides


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate curriculum/l2-uk-en/lesson-plans/<level>/_decisions.yaml: a verbatim copy of the "
            "operator-accepted decision sections for one level (its arc doc's §2 and open-questions "
            "section plus the shared plan-schema, writer-contract and build-program sections), each with its "
            "source, acceptance date and hashes.\n"
            "Use it after any of those sections changes, and with --check in CI; never edit _decisions.yaml by "
            "hand and never use it to summarise — the record is a copy, and the committed file must be "
            "byte-identical to a fresh run."
        ),
        epilog="""Examples:
  .venv/bin/python scripts/curriculum/arc/generate_decisions.py --level a2
  .venv/bin/python scripts/curriculum/arc/generate_decisions.py --all --check

Outputs:
  default   writes curriculum/l2-uk-en/lesson-plans/<level>/_decisions.yaml (overwrites), one per level
  --check   writes nothing; compares a fresh generation against the committed file(s)
Exit codes:
  0  generation succeeded / every committed file is byte-identical
  1  --check found a committed file missing or different
  2  a source section, heading, evidence line or the source map could not be used, or bad CLI usage
Related:
  Source map: scripts/curriculum/arc/decision_sources.yaml; schema: schemas/decisions-record-v1.schema.json
  Sibling: scripts/curriculum/arc/generate_arc.py; consumers: docs/epics/fresh-build-review-contracts.md; issues #8397, #8430
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--level", choices=SUPPORTED_LEVELS, help="Generate the record for one level, e.g. a2")
    scope.add_argument("--all", action="store_true", help="Generate the records for all levels (a1, a2, b1, b2)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Write nothing; compare a fresh generation against the committed file; exit 1 if missing or different "
        "(default: write mode)",
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=None,
        help=f"Override the source map (default: {SOURCES_REL}); doc paths in it are repo-relative or absolute",
    )
    parser.add_argument(
        "--doc",
        action="append",
        default=[],
        metavar="REL=PATH",
        help="Read the source document named REL in the map from PATH instead (repeatable), e.g. "
        "--doc docs/epics/fresh-build-a2-arc.md=/tmp/arc.md; the record still names REL. Used by tests",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override the _decisions.yaml path that the write and --check modes use "
        "(default: curriculum/l2-uk-en/lesson-plans/<level>/_decisions.yaml); needs --level, not --all",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.output is not None and args.all:
        parser.error("--output needs --level, not --all")
    try:
        overrides = _parse_doc_overrides(args.doc)
        sources = load_sources(args.sources or REPO_ROOT / SOURCES_REL)
        generator_sha256 = _sha256((REPO_ROOT / GENERATOR_REL).read_bytes())
        levels = SUPPORTED_LEVELS if args.all else (args.level,)
        generated = {level: render_record(level, sources, generator_sha256, overrides) for level in levels}
    except DecisionsGenerationError as exc:
        print(f"error: cannot generate the decisions record: {exc}", file=sys.stderr)
        return 2
    status = 0
    for level, text in generated.items():
        out_path = args.output or REPO_ROOT / OUT_REL.format(level=level)
        if not args.check:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(text.encode("utf-8"))
            print(f"wrote {_rel_or_abs(out_path)} ({len(text.splitlines())} lines)")
        elif not out_path.exists():
            print(f"error: {out_path} does not exist; run without --check", file=sys.stderr)
            status = 1
        elif out_path.read_bytes() != text.encode("utf-8"):
            print(
                f"error: {out_path} differs from a fresh generation; regenerate (never edit _decisions.yaml by hand)",
                file=sys.stderr,
            )
            status = 1
        else:
            print(f"ok: {_rel_or_abs(out_path)} is byte-identical to a fresh generation")
    return status


if __name__ == "__main__":
    sys.exit(main())
