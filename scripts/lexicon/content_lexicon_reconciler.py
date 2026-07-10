#!/usr/bin/env python3
"""Report content lemmas that are missing from the Word Atlas lexicon.

This is the Phase 1 stateless reconciler for #3675: scan built MDX content,
lemmatize Ukrainian surface forms with the local VESUM SQLite database, and
report ``content lemmas - lexicon manifest lemmas``. It only reports the delta;
it does not generate pages, enrich entries, or open pull requests.

Run from the repository root:

    .venv/bin/python scripts/lexicon/content_lexicon_reconciler.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import check_mdx_source_parity
from scripts.verification.vesum import verify_words

DOCS_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "docs"
READINGS_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "readings"
CONTENT_ROOTS = (DOCS_ROOT, READINGS_ROOT)
LEXICON_MANIFEST_PATH = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
VERIFY_BATCH_SIZE = 500

_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_IMPORT_EXPORT_RE = re.compile(r"^\s*(?:import|export)\b")
_COMPONENT_LINE_RE = re.compile(r"^\s*</?[A-Z][A-Za-z0-9_.:-]*(?:\s|>|/>)")
_INLINE_COMPONENT_RE = re.compile(r"</?[A-Z][A-Za-z0-9_.:-]*(?:\s+[^<>]*)?/?>")
_MARKDOWN_LINK_RE = re.compile(r"!?\[([^\]]*)\]\((?:[^()\\]|\\.|\([^)]*\))*\)")
_RAW_URL_RE = re.compile(r"https?://\S+")
_STRESS_RE = re.compile("[\u0300\u0301]")
_CYRILLIC_LETTER = r"\u0400-\u052f"
_CYRILLIC_TOKEN_RE = re.compile(
    rf"[{_CYRILLIC_LETTER}]+(?:['\-][{_CYRILLIC_LETTER}]+)*",
    re.IGNORECASE,
)
_TEXT_TRANSLATION = str.maketrans(
    {
        "ʼ": "'",
        "’": "'",
        "`": "'",
        "′": "'",
        "‐": "-",
        "‑": "-",
    }
)

VesumLookup = Callable[[list[str]], dict[str, list[dict[str, Any]]]]


@dataclass(frozen=True)
class LemmaExample:
    """One missing lemma plus a deterministic source example."""

    lemma: str
    example_form: str
    example_source: Path


@dataclass(frozen=True)
class FormExample:
    """One unrecognized surface form plus a deterministic source example."""

    form: str
    example_source: Path


@dataclass(frozen=True)
class ReconciliationResult:
    """Complete reconciliation data with count helpers for output formats."""

    files_scanned: int
    unique_forms: tuple[str, ...]
    recognized_lemmas: tuple[str, ...]
    already_in_lexicon: tuple[str, ...]
    missing_lemmas: tuple[LemmaExample, ...]
    unrecognized_forms: tuple[FormExample, ...]

    @property
    def summary(self) -> dict[str, int]:
        return {
            "files_scanned": self.files_scanned,
            "unique_forms": len(self.unique_forms),
            "recognized_lemmas": len(self.recognized_lemmas),
            "already_in_lexicon": len(self.already_in_lexicon),
            "missing_delta": len(self.missing_lemmas),
            "unrecognized": len(self.unrecognized_forms),
        }


def strip_mdx_to_prose(text: str) -> str:
    """Strip frontmatter, fenced code, imports, and MDX component syntax."""
    text = _HTML_COMMENT_RE.sub("", _strip_frontmatter(text))
    lines: list[str] = []
    in_fence = False
    in_multiline_component = False

    for raw_line in text.splitlines():
        line = raw_line

        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if in_multiline_component:
            if "/>" in line or ">" in line:
                in_multiline_component = False
            continue

        if _IMPORT_EXPORT_RE.match(line):
            continue

        if _COMPONENT_LINE_RE.match(line):
            stripped = line.strip()
            if not stripped.startswith("</") and ">" not in stripped:
                in_multiline_component = True
            continue

        line = _MARKDOWN_LINK_RE.sub(r"\1", line)
        line = _RAW_URL_RE.sub(" ", line)
        line = _INLINE_COMPONENT_RE.sub(" ", line)
        lines.append(line)

    return "\n".join(lines)


def extract_ukrainian_tokens(text: str) -> list[str]:
    """Return lowercase Cyrillic word tokens, preserving internal apostrophe/hyphen."""
    normalized = unicodedata.normalize("NFC", text).translate(_TEXT_TRANSLATION).casefold()
    normalized = _STRESS_RE.sub("", normalized)
    return [match.group(0) for match in _CYRILLIC_TOKEN_RE.finditer(normalized)]


def collect_forms(paths: Sequence[Path]) -> dict[str, Path]:
    """Return the first source file where each unique Ukrainian surface appears."""
    first_source_by_form: dict[str, Path] = {}
    for path in sorted(paths):
        prose = strip_mdx_to_prose(path.read_text(encoding="utf-8"))
        for token in extract_ukrainian_tokens(prose):
            first_source_by_form.setdefault(token, path)
    return first_source_by_form


def load_lexicon_lemma_keys(manifest_path: Path = LEXICON_MANIFEST_PATH) -> set[str]:
    """Load normalized ``entries[].lemma`` keys from the built Word Atlas manifest."""
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"Lexicon manifest has no entries list: {manifest_path}")

    lemmas: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        lemma = entry.get("lemma")
        if isinstance(lemma, str) and lemma.strip():
            lemmas.add(_lemma_key(lemma))
    return lemmas


def lemmatize_forms(
    forms: Sequence[str],
    *,
    vesum_lookup: VesumLookup = verify_words,
) -> dict[str, list[dict[str, Any]]]:
    """Lookup VESUM matches in chunks to stay below SQLite variable limits."""
    results: dict[str, list[dict[str, Any]]] = {form: [] for form in forms}
    for chunk in _chunks(list(forms), VERIFY_BATCH_SIZE):
        batch = vesum_lookup(chunk)
        for form in chunk:
            matches = batch.get(form, [])
            results[form] = matches if isinstance(matches, list) else []
    return results


def reconcile_content(
    paths: Sequence[Path],
    *,
    manifest_path: Path = LEXICON_MANIFEST_PATH,
    vesum_lookup: VesumLookup = verify_words,
) -> ReconciliationResult:
    """Compute recognized content lemmas missing from the actual lexicon set."""
    source_by_form = collect_forms(paths)
    forms = tuple(sorted(source_by_form))
    lexicon_lemma_keys = load_lexicon_lemma_keys(manifest_path)
    matches_by_form = lemmatize_forms(forms, vesum_lookup=vesum_lookup)

    lemma_by_key: dict[str, str] = {}
    example_by_lemma_key: dict[str, tuple[str, Path]] = {}
    unrecognized: list[FormExample] = []

    for form in forms:
        raw_matches = matches_by_form.get(form, [])
        lemmas = sorted(
            {
                str(match.get("lemma", "")).strip()
                for match in raw_matches
                if isinstance(match, dict) and str(match.get("lemma", "")).strip()
            },
            key=_lemma_key,
        )
        if not lemmas:
            unrecognized.append(FormExample(form=form, example_source=source_by_form[form]))
            continue

        for lemma in lemmas:
            key = _lemma_key(lemma)
            lemma_by_key.setdefault(key, lemma)
            example_by_lemma_key.setdefault(key, (form, source_by_form[form]))

    recognized_keys = set(lemma_by_key)
    already_keys = recognized_keys & lexicon_lemma_keys
    missing_keys = recognized_keys - lexicon_lemma_keys

    missing = tuple(
        LemmaExample(
            lemma=lemma_by_key[key],
            example_form=example_by_lemma_key[key][0],
            example_source=example_by_lemma_key[key][1],
        )
        for key in sorted(missing_keys, key=lambda item: _lemma_key(lemma_by_key[item]))
    )

    return ReconciliationResult(
        files_scanned=len(paths),
        unique_forms=forms,
        recognized_lemmas=tuple(
            lemma_by_key[key] for key in sorted(recognized_keys, key=lambda item: _lemma_key(lemma_by_key[item]))
        ),
        already_in_lexicon=tuple(
            lemma_by_key[key] for key in sorted(already_keys, key=lambda item: _lemma_key(lemma_by_key[item]))
        ),
        missing_lemmas=missing,
        unrecognized_forms=tuple(sorted(unrecognized, key=lambda item: item.form)),
    )


def discover_content_mdx_paths() -> list[Path]:
    """Return all module and reading MDX files in deterministic order."""
    paths: set[Path] = set()
    for root in CONTENT_ROOTS:
        paths.update(path.resolve() for path in root.glob("**/*.mdx") if path.is_file())
    return sorted(paths)


def changed_content_mdx_paths(base: str) -> list[Path]:
    """Return content MDX changed against ``base``, including unstaged/staged edits."""
    changed_files = [
        *check_mdx_source_parity.get_changed_files(base=base),
        *_get_local_changed_files(cached=False),
        *_get_local_changed_files(cached=True),
    ]
    return sorted(
        {
            path.resolve()
            for path in changed_files
            if path.exists() and path.suffix == ".mdx" and _is_content_mdx(path)
        }
    )


def result_to_json_payload(
    result: ReconciliationResult,
    *,
    limit: int | None = None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    missing = _limit_sequence(result.missing_lemmas, limit)
    unrecognized = _limit_sequence(result.unrecognized_forms, limit)
    return {
        "summary": result.summary,
        "missing_lemmas": [
            {
                "lemma": item.lemma,
                "example_form": item.example_form,
                "example_source": _display_path(item.example_source, project_root),
            }
            for item in missing
        ],
        "unrecognized_forms": [
            {
                "form": item.form,
                "example_source": _display_path(item.example_source, project_root),
            }
            for item in unrecognized
        ],
        "limit": limit,
        "truncated": {
            "missing_lemmas": limit is not None and len(result.missing_lemmas) > limit,
            "unrecognized_forms": limit is not None and len(result.unrecognized_forms) > limit,
        },
    }


def format_human_summary(
    result: ReconciliationResult,
    *,
    limit: int | None = None,
    project_root: Path = PROJECT_ROOT,
) -> str:
    """Format counts plus sorted missing/unrecognized examples for humans."""
    summary = result.summary
    lines = [
        "Content lexicon reconciliation",
        f"Files scanned: {summary['files_scanned']}",
        f"Unique Ukrainian forms: {summary['unique_forms']}",
        f"Recognized lemmas: {summary['recognized_lemmas']}",
        f"Already in lexicon: {summary['already_in_lexicon']}",
        f"MISSING delta: {summary['missing_delta']}",
        f"Unrecognized forms: {summary['unrecognized']}",
        "",
        "Missing lemmas:",
    ]

    missing = _limit_sequence(result.missing_lemmas, limit)
    if missing:
        for item in missing:
            source = _display_path(item.example_source, project_root)
            lines.append(f"- {item.lemma} (form: {item.example_form}; source: {source})")
        lines.extend(_truncation_lines(len(result.missing_lemmas), len(missing), "missing lemmas"))
    else:
        lines.append("- none")

    lines.extend(["", "Unrecognized forms:"])
    unrecognized = _limit_sequence(result.unrecognized_forms, limit)
    if unrecognized:
        for item in unrecognized:
            source = _display_path(item.example_source, project_root)
            lines.append(f"- {item.form} (source: {source})")
        lines.extend(_truncation_lines(len(result.unrecognized_forms), len(unrecognized), "unrecognized forms"))
    else:
        lines.append("- none")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report Ukrainian content lemmas missing from the Word Atlas lexicon."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    parser.add_argument("--limit", type=int, help="Limit listed missing/unrecognized examples")
    parser.add_argument(
        "--changed-vs-base",
        metavar="BASE",
        help="Only scan content MDX changed against BASE, including local edits",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    paths = (
        changed_content_mdx_paths(args.changed_vs_base)
        if args.changed_vs_base
        else discover_content_mdx_paths()
    )

    try:
        result = reconcile_content(paths)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                result_to_json_payload(result, limit=args.limit),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_human_summary(result, limit=args.limit))

    return 0


def _strip_frontmatter(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "".join(lines[index + 1 :])
    return text


def _get_local_changed_files(*, cached: bool) -> list[Path]:
    cmd = ["git", "diff", "--name-only"]
    if cached:
        cmd.append("--cached")
    try:
        output = subprocess.check_output(cmd, cwd=PROJECT_ROOT, text=True)
    except subprocess.CalledProcessError:
        return []
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def _is_content_mdx(path: Path) -> bool:
    resolved = path.resolve()
    return any(_is_relative_to(resolved, root) for root in CONTENT_ROOTS)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _lemma_key(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).translate(_TEXT_TRANSLATION).casefold()
    normalized = _STRESS_RE.sub("", normalized)
    return re.sub(r"\s+", " ", normalized.strip())


def _chunks(items: Sequence[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield list(items[index : index + size])


def _limit_sequence[T](items: Sequence[T], limit: int | None) -> Sequence[T]:
    if limit is None:
        return items
    return items[:limit]


def _truncation_lines(total: int, shown: int, label: str) -> list[str]:
    if shown >= total:
        return []
    return [f"... {total - shown} more {label} not shown"]


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
