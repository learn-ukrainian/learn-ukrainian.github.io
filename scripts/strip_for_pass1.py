#!/usr/bin/env python3
"""Build a Ukrainian-only Pass 1 artifact with hash anchors.

This is a one-off experiment helper for the Pass-2-only contract test. It
extracts learner-facing Ukrainian from an English-scaffolded module and writes
an anchor manifest that downstream checks can compare byte-for-byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

UKRAINIAN_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]")
UKRAINIAN_WORD_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ'’ʼ-]*")
ALPHA_WORD_RE = re.compile(
    r"[A-Za-zА-ЩЬЮЯЄІЇҐа-щьюяєіїґ][A-Za-zА-ЩЬЮЯЄІЇҐа-щьюяєіїґ'’ʼ-]*"
)
DIALOGUE_RE = re.compile(r"^>\s+\*\*(?P<speaker>[^*]+):\*\*\s+(?P<body>.+)$")
TABLE_ROW_RE = re.compile(r"^\|\s*(?P<cells>.+?)\s*\|$")
TRANSLATION_SPLIT_RE = re.compile(r"\s+[—-]\s+\*")


@dataclass(frozen=True)
class Anchor:
    anchor_id: str
    kind: str
    content: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


def _strip_inline_translation(text: str) -> str:
    """Remove the obvious English gloss after a Ukrainian example."""
    text = text.strip()
    split = TRANSLATION_SPLIT_RE.split(text, maxsplit=1)
    return split[0].strip()


def _clean_markdown_cell(cell: str) -> str:
    cell = cell.strip()
    cell = re.sub(r"\*\*(.*?)\*\*", r"\1", cell)
    cell = re.sub(r"\*(.*?)\*", r"\1", cell)
    cell = cell.replace("&nbsp;", " ")
    return " ".join(cell.split())


def _has_ukrainian(text: str) -> bool:
    return bool(UKRAINIAN_RE.search(text))


def _ukrainian_ratio(text: str) -> float:
    words = ALPHA_WORD_RE.findall(text)
    if not words:
        return 0.0
    uk_words = [word for word in words if UKRAINIAN_RE.search(word)]
    return len(uk_words) / len(words)


def _is_ukrainian_dominant(text: str, *, min_words: int = 2) -> bool:
    return len(UKRAINIAN_WORD_RE.findall(text)) >= min_words and _ukrainian_ratio(text) >= 0.5


def _is_separator_row(line: str) -> bool:
    chars = set(line.strip().replace("|", "").replace(" ", ""))
    return bool(chars) and chars <= {"-", ":"}


def _anchor(anchor_id: str, kind: str, content: str) -> Anchor:
    return Anchor(anchor_id=anchor_id, kind=kind, content=content.rstrip())


def extract_module_anchors(module_text: str) -> list[Anchor]:
    anchors: list[Anchor] = []
    counters = {"uk-dlg": 0, "uk-ex": 0, "uk-tbl": 0}
    seen: set[tuple[str, str]] = set()

    def add(kind: str, content: str) -> None:
        content = content.rstrip()
        if not content or not _has_ukrainian(content):
            return
        key = (kind, content)
        if key in seen:
            return
        seen.add(key)
        counters[kind] += 1
        anchors.append(_anchor(f"{kind}-{counters[kind]}", kind, content))

    for raw_line in module_text.splitlines():
        line = raw_line.rstrip()
        dialogue_match = DIALOGUE_RE.match(line)
        if dialogue_match:
            body = _strip_inline_translation(dialogue_match.group("body"))
            add("uk-dlg", f"**{dialogue_match.group('speaker')}:** {body}")
            continue

        if line.startswith(">"):
            quote_body = line.lstrip("> ").strip()
            quote_body = _strip_inline_translation(quote_body)
            if quote_body.startswith("—"):
                continue
            if _is_ukrainian_dominant(quote_body):
                add("uk-ex", quote_body)
            continue

        if TABLE_ROW_RE.match(line) and not _is_separator_row(line):
            table_match = TABLE_ROW_RE.match(line)
            assert table_match is not None
            cells = [_clean_markdown_cell(cell) for cell in table_match.group("cells").split("|")]
            for cell in cells:
                if _has_ukrainian(cell) and cell not in {"Особа"}:
                    add("uk-tbl", cell)
            continue

        stripped = _strip_inline_translation(line.strip())
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        if (
            _is_ukrainian_dominant(stripped, min_words=2)
            and not stripped.startswith("<!--")
            and not stripped.startswith("#")
            and not stripped.startswith("—")
        ):
            add("uk-ex", stripped)

    return anchors


def extract_vocabulary_anchors(vocabulary_path: Path, start_index: int = 0) -> list[Anchor]:
    data = yaml.safe_load(vocabulary_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{vocabulary_path} must contain a YAML list")

    anchors: list[Anchor] = []
    for offset, item in enumerate(data, start=1):
        if not isinstance(item, dict) or "lemma" not in item:
            continue
        lemma = str(item["lemma"]).strip()
        if _has_ukrainian(lemma):
            anchors.append(_anchor(f"uk-vocab-{start_index + offset}", "uk-vocab", lemma))
    return anchors


def render_pass1(anchors: list[Anchor]) -> str:
    sections = [
        ("## Діалоги", "uk-dlg"),
        ("## Приклади", "uk-ex"),
        ("## Табличні форми", "uk-tbl"),
        ("## Лексика", "uk-vocab"),
    ]
    lines = [
        "# Pass 1 stripped Ukrainian anchors",
        "",
        "Source: audit/bakeoff-2026-05-13-midday/claude/module.md",
        "",
    ]
    for heading, kind in sections:
        section_anchors = [anchor for anchor in anchors if anchor.kind == kind]
        if not section_anchors:
            continue
        lines.extend([heading, ""])
        for anchor in section_anchors:
            lines.append(f"<!-- ANCHOR {anchor.anchor_id} -->")
            lines.append(anchor.content)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def manifest(anchors: list[Anchor]) -> dict[str, Any]:
    return {
        "anchor_count": len(anchors),
        "anchors": [
            {
                "id": anchor.anchor_id,
                "kind": anchor.kind,
                "sha256": anchor.sha256,
                "content": anchor.content,
            }
            for anchor in anchors
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--vocabulary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--anchors-json", type=Path, required=True)
    args = parser.parse_args()

    module_anchors = extract_module_anchors(args.module.read_text(encoding="utf-8"))
    vocab_anchors = extract_vocabulary_anchors(args.vocabulary)
    anchors = [*module_anchors, *vocab_anchors]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.anchors_json.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_pass1(anchors), encoding="utf-8")
    args.anchors_json.write_text(
        json.dumps(manifest(anchors), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"anchor_count={len(anchors)}")
    print(f"pass1={args.output}")
    print(f"anchors_json={args.anchors_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
