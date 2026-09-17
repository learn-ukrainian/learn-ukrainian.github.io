"""TypeSafe System One Verbatim Structure Recovery & De-Hyphenation.

Adopts the Structure Recovery architectural pattern from TypeSafe AI:
https://docs.typesafe.ai/cookbooks/autoformat.md

Reconstructs structured Markdown from OCR'd or unformatted Ukrainian textbooks
and historical sources in data/sources.db.

Core Principles:
1. Pass 1 (Stitch): Batched Noul questions per line pair determine whether a line
   break splits a sentence or word mid-boundary.
2. Pass 2 (Classify): Batched Choice questions classify merged blocks into headings,
   paragraphs, list items, quotes, or exercises.
3. Verbatim Rendering: The model NEVER generates or rewrites text. Code applies Markdown
   formatting directly to the original characters, preserving 100% of the human source text.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class BlockType(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    QUOTE = "quote"
    EXERCISE = "exercise"


@dataclass
class RecoveredBlock:
    """A structural block parsed from raw lines."""

    block_id: int
    raw_lines: list[str]
    merged_text: str
    block_type: BlockType = BlockType.PARAGRAPH
    heading_level: int = 2
    confidence: float = 1.0


@dataclass
class RecoveryReport:
    """Audit report demonstrating 100% character preservation."""

    original_line_count: int
    recovered_block_count: int
    dehyphenated_count: int
    character_preservation_ratio: float
    rendered_markdown: str
    blocks: list[RecoveredBlock] = field(default_factory=list)


def _resolve_typesafe_key() -> str:
    """Resolve TypeSafe API key from environment or user home secrets."""
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key

    key_files = [
        Path.home() / ".config" / "typesafe" / "key",
        Path.home() / ".typesafe_api_key",
        Path.home() / ".gemini" / "antigravity-cli" / "typesafe_api_key",
    ]
    for p in key_files:
        if p.is_file():
            content = p.read_text(encoding="utf-8").strip()
            if content:
                return content
    return ""


class TypeSafeStructureRecovery:
    """Two-pass structure recovery engine backed by TypeSafe System One."""

    QUESTIONS_PASS1: ClassVar[dict[str, Any]] = {
        "is_continuation": {
            "type": "noul",
            "instructions": "Does Line 2 continue the sentence or hyphenated word broken across the line boundary from Line 1?",
            "criteria": {
                "true": "Line 1 ends mid-sentence or with a broken hyphenated word fragment (e.g. 'відро-'), and Line 2 immediately continues that sentence or word.",
                "false": "Line 1 ends with terminal punctuation (. ? ! :), or Line 2 starts a new paragraph, heading, list item, or independent clause.",
            },
        }
    }

    QUESTIONS_PASS2: ClassVar[dict[str, Any]] = {
        "block_type": {
            "type": "choice",
            "instructions": "What structural Markdown block element is this Ukrainian text block?",
            "options": {
                "heading": "A section title, chapter header, or topic label.",
                "paragraph": "Standard expository or narrative prose text.",
                "list_item": "An item in a list, enumeration, bullet, or sub-question.",
                "quote": "A cited quotation, epigraph, poem stanza, or literary excerpt.",
                "exercise": "A pedagogical instruction, task prompt, or assignment directive (e.g. 'Вправа 12. Спишіть...').",
            },
        },
        "heading_level": {
            "type": "score",
            "instructions": "If this block is a heading, rate its hierarchical level from 1 (major chapter) to 3 (sub-topic).",
            "levels": {
                "1": "Level 1 heading (#): main book division or major section.",
                "2": "Level 2 heading (##): topic title or lesson heading.",
                "3": "Level 3 heading (###): sub-section or rule header.",
            },
        },
    }

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.typesafe.ai"):
        self.api_key = api_key or _resolve_typesafe_key()
        self.base_url = base_url.rstrip("/")

    def recover(self, raw_text: str) -> RecoveryReport:
        """Execute two-pass structure recovery over raw text."""
        raw_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not raw_lines:
            return RecoveryReport(0, 0, 0, 1.0, "", [])

        # Pass 1: Stitch lines into blocks and dehyphenate
        blocks, dehyphen_count = self._pass1_stitch(raw_lines)

        # Pass 2: Classify blocks
        self._pass2_classify(blocks)

        # Pass 3: Render verbatim markdown
        rendered = self._render_markdown(blocks)

        # Calculate character preservation (excluding whitespace and hyphen removed by de-hyphenation)
        char_ratio = self._calculate_preservation(raw_text, blocks, dehyphen_count)

        return RecoveryReport(
            original_line_count=len(raw_lines),
            recovered_block_count=len(blocks),
            dehyphenated_count=dehyphen_count,
            character_preservation_ratio=char_ratio,
            rendered_markdown=rendered,
            blocks=blocks,
        )

    def _pass1_stitch(self, lines: list[str]) -> tuple[list[RecoveredBlock], int]:
        """Stitch adjacent lines into coherent blocks using continuation probabilities."""
        if len(lines) == 1:
            return [RecoveredBlock(block_id=1, raw_lines=[lines[0]], merged_text=lines[0])], 0

        blocks: list[RecoveredBlock] = []
        current_block_lines: list[str] = [lines[0]]
        dehyphen_count = 0

        for i in range(len(lines) - 1):
            line_a = lines[i]
            line_b = lines[i + 1]

            is_cont = self._evaluate_continuation(line_a, line_b)

            if is_cont:
                current_block_lines.append(line_b)
            else:
                # Merge current block lines
                merged, d_count = self._merge_lines(current_block_lines)
                dehyphen_count += d_count
                blocks.append(
                    RecoveredBlock(
                        block_id=len(blocks) + 1,
                        raw_lines=list(current_block_lines),
                        merged_text=merged,
                    )
                )
                current_block_lines = [line_b]

        if current_block_lines:
            merged, d_count = self._merge_lines(current_block_lines)
            dehyphen_count += d_count
            blocks.append(
                RecoveredBlock(
                    block_id=len(blocks) + 1,
                    raw_lines=list(current_block_lines),
                    merged_text=merged,
                )
            )

        return blocks, dehyphen_count

    def _evaluate_continuation(self, line_a: str, line_b: str) -> bool:
        """Determine if line_b continues line_a."""
        if self.api_key:
            try:
                p = self._call_pass1_api(line_a, line_b)
                return p >= 0.75
            except Exception:
                return self._heuristic_continuation(line_a, line_b)
        return self._heuristic_continuation(line_a, line_b)

    def _heuristic_continuation(self, line_a: str, line_b: str) -> bool:
        """Deterministic linguistic heuristic for sentence continuation."""
        # Broken hyphen: word- at end of line followed by letters on next line
        if re.search(r"[\wА-Яа-яІіЇїЄєҐґ]-\s*$", line_a) and re.match(r"^[а-яіїєґ]", line_b):
            return True

        # Terminal punctuation indicates end of block
        if re.search(r"[.?!:]\s*$", line_a):
            return False

        # Next line starts with list bullet or number
        if re.match(r"^(\d+[.)]|[-*•])\s+", line_b):
            return False

        # Next line starts with lowercase letter or comma continuation
        if re.match(r"^[а-яіїєґ,]", line_b):
            return True

        # If line A does not end in punctuation and line B starts with uppercase but is normal text length
        return bool(not re.search(r"[.?!:;,]\s*$", line_a) and len(line_a.split()) > 4)

    @staticmethod
    def _merge_lines(lines: list[str]) -> tuple[str, int]:
        """Merge a sequence of lines into a block with de-hyphenation."""
        if not lines:
            return "", 0

        merged = lines[0]
        dehyphens = 0

        for next_line in lines[1:]:
            # Check for end-of-line hyphenation (e.g. 'відро-' + 'дження')
            match = re.search(r"([\wА-Яа-яІіЇїЄєҐґ]+)-\s*$", merged)
            if match and re.match(r"^[а-яіїєґ]", next_line):
                # Remove hyphen and stitch directly
                merged = merged[: match.end() - 1] + next_line
                dehyphens += 1
            else:
                merged = f"{merged} {next_line}"

        return merged, dehyphens

    def _pass2_classify(self, blocks: list[RecoveredBlock]) -> None:
        """Classify each block into a markdown block type."""
        for block in blocks:
            if self.api_key:
                try:
                    b_type, h_level, conf = self._call_pass2_api(block.merged_text)
                    block.block_type = b_type
                    block.heading_level = h_level
                    block.confidence = conf
                    continue
                except Exception:
                    pass
            b_type, h_level, conf = self._heuristic_classify(block.merged_text)
            block.block_type = b_type
            block.heading_level = h_level
            block.confidence = conf

    def _heuristic_classify(self, text: str) -> tuple[BlockType, int, float]:
        """Deterministic heuristic for block classification."""
        clean = text.strip()

        # Exercise markers
        if re.match(r"^(вправа|завдання|питання|самостійна робота)\b", clean, flags=re.IGNORECASE):
            return BlockType.EXERCISE, 2, 0.95

        # List items
        if re.match(r"^(\d+[.)]|[-*•])\s+", clean):
            return BlockType.LIST_ITEM, 2, 0.95

        # Heading heuristic: short length, no terminal period, title case or all caps
        if len(clean.split()) <= 7 and not clean.endswith("."):
            if re.match(r"^(розділ|параграф|тема|урок)\b", clean, flags=re.IGNORECASE):
                return BlockType.HEADING, 1, 0.95
            if len(clean) < 60:
                return BlockType.HEADING, 2, 0.85

        # Quote / Poetry heuristic: starts with quotation marks or dash
        if clean.startswith(("«", '"', "—", "–")):
            return BlockType.QUOTE, 2, 0.80

        return BlockType.PARAGRAPH, 2, 0.90

    def _call_pass1_api(self, line_a: str, line_b: str) -> float:
        """Call remote TypeSafe API for Pass 1 continuation."""
        url = f"{self.base_url}/v1/system_one"
        payload = {
            "model": "jev-latest",
            "state": {"line_1": line_a, "line_2": line_b},
            "questions": self.QUESTIONS_PASS1,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "learn-ukrainian-autoformat/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return float(data["answers"]["is_continuation"]["noul"])

    def _call_pass2_api(self, text: str) -> tuple[BlockType, int, float]:
        """Call remote TypeSafe API for Pass 2 classification."""
        url = f"{self.base_url}/v1/system_one"
        payload = {
            "model": "jev-latest",
            "state": {"block_text": text},
            "questions": self.QUESTIONS_PASS2,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "learn-ukrainian-autoformat/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            b_type_str = data["answers"]["block_type"]["choice"]
            b_type = BlockType(b_type_str) if b_type_str in BlockType._value2member_map_ else BlockType.PARAGRAPH
            h_level = round(data["answers"]["heading_level"]["score"])
            conf = float(data["answers"]["block_type"].get("confidence", 1.0))
            return b_type, h_level, conf

    @staticmethod
    def _render_markdown(blocks: list[RecoveredBlock]) -> str:
        """Render blocks into clean Markdown without modifying source characters."""
        lines: list[str] = []
        for block in blocks:
            text = block.merged_text
            match block.block_type:
                case BlockType.HEADING:
                    prefix = "#" * max(1, min(3, block.heading_level))
                    lines.append(f"{prefix} {text}\n")
                case BlockType.LIST_ITEM:
                    if not re.match(r"^(\d+[.)]|[-*•])\s+", text):
                        lines.append(f"- {text}")
                    else:
                        lines.append(text)
                case BlockType.QUOTE:
                    lines.append(f"> {text}\n")
                case BlockType.EXERCISE:
                    lines.append(f"> **{text}**\n" if not text.startswith("**") else f"> {text}\n")
                case BlockType.PARAGRAPH:
                    lines.append(f"{text}\n")
        return "\n".join(lines).strip()

    @staticmethod
    def _calculate_preservation(raw_text: str, blocks: list[RecoveredBlock], dehyphen_count: int) -> float:
        """Verify 100% preservation of substantive characters."""
        raw_chars = re.sub(r"\s+", "", raw_text)
        merged_chars = "".join(re.sub(r"\s+", "", b.merged_text) for b in blocks)
        # Account for intentional dehyphenation removals
        if len(raw_chars) == len(merged_chars) + dehyphen_count:
            return 1.0
        return len(merged_chars) / max(1, len(raw_chars))


def recover_source_text(raw_text: str, engine: TypeSafeStructureRecovery | None = None) -> RecoveryReport:
    """Convenience helper for recovering raw text."""
    recovery_engine = engine or TypeSafeStructureRecovery()
    return recovery_engine.recover(raw_text)


def main() -> None:
    parser = argparse.ArgumentParser(description="TypeSafe Structure Recovery for Scanned Ukrainian Sources")
    parser.add_argument("file", help="Path to raw plain text file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"File not found: {path}")
        return

    text = path.read_text(encoding="utf-8")
    report = recover_source_text(text)
    print(f"Processed {report.original_line_count} lines into {report.recovered_block_count} blocks.")
    print(f"De-hyphenated words: {report.dehyphenated_count}")
    print(f"Character preservation ratio: {report.character_preservation_ratio:.4%}\n")
    print("--- Rendered Markdown ---")
    print(report.rendered_markdown)


if __name__ == "__main__":
    main()
