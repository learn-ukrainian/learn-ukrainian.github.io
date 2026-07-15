#!/usr/bin/env python3
"""Scan generated ErrorCorrection embeds for sentence-shaped form values."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_EMBED_RE = re.compile(
    r"<ErrorCorrection\b[\s\S]*?items=\{JSON\.parse\(`([\s\S]*?)`\)\}[\s\S]*?/>"
)
_SENTENCE_PUNCTUATION = (".", "?", "!")


def parse_mdx_embeds(content: str) -> list[list[dict]]:
    """JSON-parse every ErrorCorrection items payload in an MDX document."""
    embeds: list[list[dict]] = []
    for match in _EMBED_RE.findall(content):
        payload = match.replace(r'\"', '"').replace(r"\`", "`").replace(r"\\", "\\")
        try:
            items = json.loads(payload)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid ErrorCorrection JSON payload: {error}") from error
        if not isinstance(items, list):
            raise ValueError("ErrorCorrection items payload is not a list")
        embeds.append(items)
    return embeds


def is_corrected_sentence(sentence: str, error_word: str, correct_form: str) -> bool:
    """Return whether the form retains the source sentence around the error."""
    if not error_word or not correct_form:
        return False

    normalized_sentence = " ".join(sentence.split())
    normalized_error = " ".join(error_word.split())
    normalized_form = " ".join(correct_form.split())
    start = 0
    while True:
        error_index = normalized_sentence.find(normalized_error, start)
        if error_index == -1:
            return False
        prefix = normalized_sentence[:error_index]
        suffix = normalized_sentence[error_index + len(normalized_error):]
        if (
            normalized_form.startswith(prefix)
            and normalized_form.endswith(suffix)
            and (prefix or suffix)
        ):
            return True
        start = error_index + 1


def is_sentence_shaped(correct_form: object, sentence: object, error_word: object) -> bool:
    """Predicate for forms that would mangle the word-level UI step."""
    if not all(isinstance(value, str) for value in (correct_form, sentence, error_word)):
        return False
    form = correct_form.strip()
    if form in _SENTENCE_PUNCTUATION:
        return False
    return form.endswith(_SENTENCE_PUNCTUATION) or is_corrected_sentence(
        sentence, error_word, correct_form
    )


def scan_tree(docs_dir: Path) -> dict[str, int]:
    """Return counts for generated embeds and sentence-shaped form defects."""
    counts = {
        "files": 0,
        "files_with_embeds": 0,
        "embeds": 0,
        "items": 0,
        "sentence_shaped_items": 0,
    }
    for path in sorted(docs_dir.rglob("*.mdx")):
        counts["files"] += 1
        embeds = parse_mdx_embeds(path.read_text(encoding="utf-8"))
        if embeds:
            counts["files_with_embeds"] += 1
        for embed in embeds:
            counts["embeds"] += 1
            for item in embed:
                counts["items"] += 1
                if is_sentence_shaped(
                    item.get("correctForm"),
                    item.get("sentence"),
                    item.get("errorWord"),
                ):
                    counts["sentence_shaped_items"] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default="site/src/content/docs")
    args = parser.parse_args()
    docs_dir = PROJECT_ROOT / args.dir
    if not docs_dir.is_dir():
        parser.error(f"MDX directory not found: {docs_dir}")

    counts = scan_tree(docs_dir)
    print(
        "ERRORCORRECTION_EMBED_SCAN "
        f"files={counts['files']} files_with_embeds={counts['files_with_embeds']} "
        f"embeds={counts['embeds']} items={counts['items']} "
        f"sentence_shaped_items={counts['sentence_shaped_items']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
