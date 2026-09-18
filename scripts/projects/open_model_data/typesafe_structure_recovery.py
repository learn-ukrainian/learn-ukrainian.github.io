"""TypeSafe System One Verbatim Structure Recovery & De-Hyphenation.

Adopts the Structure Recovery architectural pattern from TypeSafe AI:
https://docs.typesafe.ai/cookbooks/autoformat.md

Reconstructs structured Markdown from OCR'd or unformatted Ukrainian textbooks
and historical sources in data/sources.db.

Core Principles:
1. Pass 1 (Stitch): Batched Noul questions per line pair determine whether a line
   break splits a sentence or word mid-boundary.
2. Pass 2 (Classify): Batched Choice & Score questions classify merged blocks into
   headings, paragraphs, list items, quotes, or exercises.
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
    """Resolve TypeSafe API key from environment or host secrets."""
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key

    key_files = [
        Path.home() / ".secrets" / "typesafe-ai.key",
        Path.home() / ".secrets" / "typsafe-ai.key",
    ]
    for p in key_files:
        if p.is_file():
            try:
                content = p.read_text(encoding="utf-8").strip()
                if content:
                    return content
            except OSError:
                continue
    return ""


class TypeSafeStructureRecovery:
    """Two-pass structure recovery engine backed by TypeSafe System One."""

    QUESTIONS_PASS1: ClassVar[dict[str, Any]] = {
        "is_continuation": {
            "type": "noul",
            "instructions": "Does `state.line_2` continue the sentence or hyphenated word broken across the line boundary from `state.line_1`?",
            "criteria": {
                "true": "line_1 ends mid-sentence or with a broken hyphenated word fragment (e.g. 'відро-'), and line_2 immediately continues that sentence or word.",
                "false": "line_1 ends with terminal punctuation (. ? ! :), or line_2 starts a new paragraph, heading, list item, or independent clause.",
            },
        }
    }

    QUESTIONS_PASS2: ClassVar[dict[str, Any]] = {
        "block_type": {
            "type": "choice",
            "instructions": "What structural Markdown block element is this Ukrainian text block?",
            "criteria": {
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
            "criteria": [
                "Level 1 heading (#): main book division or major section.",
                "Level 2 heading (##): topic title or lesson heading.",
                "Level 3 heading (###): sub-section or rule header.",
            ],
        },
    }

    KNOWN_COMPOUND_PREFIXES: ClassVar[set[str]] = {
        "будь", "небудь", "хто", "де", "по", "темно", "світло", "яскраво",
        "жовто", "синьо", "військово", "науково", "фізико", "хіміко",
        "історико", "суспільно", "соціально", "пів", "макро", "мікро",
    }

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.typesafe.ai",
        batch_size: int = 15,
    ) -> None:
        self.api_key = api_key if api_key is not None else _resolve_typesafe_key()
        self.base_url = base_url.rstrip("/")
        self.batch_size = max(1, batch_size)
        self.api_calls: int = 0

    def recover(self, raw_text: str) -> RecoveryReport:
        """Execute two-pass structure recovery over raw text, preserving blank-line paragraph gaps."""
        paragraph_chunks = [p.strip() for p in re.split(r"\n\s*\n+", raw_text) if p.strip()]
        if not paragraph_chunks:
            return RecoveryReport(0, 0, 0, 1.0, "", [])

        all_raw_lines: list[str] = []
        blocks: list[RecoveredBlock] = []
        total_dehyphen_count = 0

        for chunk in paragraph_chunks:
            chunk_lines = [line.strip() for line in chunk.splitlines() if line.strip()]
            if not chunk_lines:
                continue
            all_raw_lines.extend(chunk_lines)
            chunk_blocks, d_count = self._pass1_stitch(chunk_lines, start_block_id=len(blocks) + 1)
            blocks.extend(chunk_blocks)
            total_dehyphen_count += d_count

        # Pass 2: Classify blocks
        self._pass2_classify(blocks)

        # Pass 3: Render verbatim markdown
        rendered = self._render_markdown(blocks)

        # Calculate character preservation (excluding whitespace and justified de-hyphenation)
        char_ratio = self._calculate_preservation(raw_text, blocks, total_dehyphen_count)

        return RecoveryReport(
            original_line_count=len(all_raw_lines),
            recovered_block_count=len(blocks),
            dehyphenated_count=total_dehyphen_count,
            character_preservation_ratio=char_ratio,
            rendered_markdown=rendered,
            blocks=blocks,
        )

    def _pass1_stitch(self, lines: list[str], start_block_id: int = 1) -> tuple[list[RecoveredBlock], int]:
        """Stitch adjacent lines within a paragraph chunk into coherent blocks using continuation probabilities."""
        if len(lines) == 1:
            return [RecoveredBlock(block_id=start_block_id, raw_lines=[lines[0]], merged_text=lines[0])], 0

        # Pre-evaluate continuations for all adjacent pairs
        continuations = self._evaluate_all_continuations(lines)

        blocks: list[RecoveredBlock] = []
        current_block_lines: list[str] = [lines[0]]
        dehyphen_count = 0

        for i in range(len(lines) - 1):
            is_cont = continuations[i]

            if is_cont:
                current_block_lines.append(lines[i + 1])
            else:
                merged, d_count = self._merge_lines(current_block_lines)
                dehyphen_count += d_count
                blocks.append(
                    RecoveredBlock(
                        block_id=start_block_id + len(blocks),
                        raw_lines=list(current_block_lines),
                        merged_text=merged,
                    )
                )
                current_block_lines = [lines[i + 1]]

        if current_block_lines:
            merged, d_count = self._merge_lines(current_block_lines)
            dehyphen_count += d_count
            blocks.append(
                RecoveredBlock(
                    block_id=start_block_id + len(blocks),
                    raw_lines=list(current_block_lines),
                    merged_text=merged,
                )
            )

        return blocks, dehyphen_count

    def _evaluate_all_continuations(self, lines: list[str]) -> list[bool]:
        """Evaluate continuation for each pair of adjacent lines, batching where possible."""
        n_pairs = len(lines) - 1
        results: list[bool] = [False] * n_pairs

        pairs = [{"line_1": lines[i], "line_2": lines[i + 1]} for i in range(n_pairs)]

        if self.api_key:
            # Process in batches
            for offset in range(0, n_pairs, self.batch_size):
                batch = pairs[offset : offset + self.batch_size]
                try:
                    batch_res = self._call_pass1_batch_api(batch)
                    for j, is_c in enumerate(batch_res):
                        results[offset + j] = is_c
                    continue
                except Exception:
                    pass
                # Fallback for this batch
                for j, p in enumerate(batch):
                    results[offset + j] = self._heuristic_continuation(p["line_1"], p["line_2"])
        else:
            for i, p in enumerate(pairs):
                results[i] = self._heuristic_continuation(p["line_1"], p["line_2"])

        return results

    def _call_pass1_batch_api(self, batch_pairs: list[dict[str, str]]) -> list[bool]:
        """Batch call remote TypeSafe System One API for line continuations."""
        if len(batch_pairs) == 1:
            p = self._call_pass1_single_api(batch_pairs[0]["line_1"], batch_pairs[0]["line_2"])
            return [p >= 0.75]

        questions: dict[str, Any] = {}
        for idx in range(len(batch_pairs)):
            questions[f"p{idx}_cont"] = {
                "type": "noul",
                "instructions": (
                    f"Does line_2 continue the sentence or hyphenated word broken across "
                    f"the line boundary from line_1 in state.pairs[{idx}]?"
                ),
                "criteria": {
                    "true": "line_1 ends mid-sentence or with a broken hyphenated word fragment, and line_2 continues it.",
                    "false": "line_1 ends with terminal punctuation or line_2 starts a new independent structural element.",
                },
            }

        url = f"{self.base_url}/v1/systemone"
        payload = {
            "model": "jev-latest",
            "state": {"pairs": batch_pairs},
            "questions": questions,
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
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            answers = data.get("answers", {})
            out: list[bool] = []
            for idx in range(len(batch_pairs)):
                q_ans = answers.get(f"p{idx}_cont", {})
                noul_val = float(q_ans.get("noul", 0.0))
                out.append(noul_val >= 0.75)
            self.api_calls += 1
            return out

    def _call_pass1_single_api(self, line_a: str, line_b: str) -> float:
        """Single line pair remote TypeSafe API call for Pass 1 continuation."""
        url = f"{self.base_url}/v1/systemone"
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
            self.api_calls += 1
            return float(data["answers"]["is_continuation"]["noul"])

    @staticmethod
    def _heuristic_continuation(line_a: str, line_b: str) -> bool:
        """Deterministic linguistic heuristic for sentence continuation."""
        # Broken hyphen: word- or word\u00ad at end of line followed by letters on next line
        if re.search(r"[\wА-Яа-яІіЇїЄєҐґ][-\u00ad]\s*$", line_a) and re.match(r"^[а-яіїєґ]", line_b):
            return True

        # Headings and exercise markers are block boundaries
        if re.match(r"^(розділ|параграф|тема|урок|вправа|завдання)\b", line_a, flags=re.IGNORECASE):
            return False
        if re.match(r"^(розділ|параграф|тема|урок|вправа|завдання)\b", line_b, flags=re.IGNORECASE):
            return False

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

    @classmethod
    def _merge_lines(cls, lines: list[str]) -> tuple[str, int]:
        """Merge a sequence of lines into a block with verified de-hyphenation."""
        if not lines:
            return "", 0

        merged = lines[0]
        dehyphens = 0

        for next_line in lines[1:]:
            # 1. Unicode soft hyphen \u00ad: always a line-wrap formatting artifact
            match_soft = re.search(r"([\wА-Яа-яІіЇїЄєҐґ]+)\u00ad\s*$", merged)
            if match_soft and re.match(r"^[а-яіїєґ]", next_line):
                merged = merged[: match_soft.end() - 1] + next_line
                dehyphens += 1
                continue

            # 2. ASCII hyphen - at end of line: check if wrapping vs lexical compound
            match_ascii = re.search(r"([а-яіїєґА-ЯІЇЄҐ]+)-\s*$", merged)
            match_next = re.match(r"^([а-яіїєґ]+)", next_line)
            if match_ascii and match_next:
                part1 = match_ascii.group(1)
                part2 = match_next.group(1)
                is_compound = (
                    len(part1) < 2
                    or len(part2) < 2
                    or part1.lower() in cls.KNOWN_COMPOUND_PREFIXES
                )
                if not is_compound:
                    # De-hyphenate line-wrapped word
                    merged = merged[: match_ascii.end() - 1] + next_line
                    dehyphens += 1
                    continue

            merged = f"{merged} {next_line}"

        return merged, dehyphens

    def _pass2_classify(self, blocks: list[RecoveredBlock]) -> None:
        """Classify each block into a markdown block type with batched API calls."""
        if not blocks:
            return

        if self.api_key:
            for offset in range(0, len(blocks), self.batch_size):
                batch = blocks[offset : offset + self.batch_size]
                try:
                    results = self._call_pass2_batch_api([b.merged_text for b in batch])
                    for j, (b_type, h_lvl, conf) in enumerate(results):
                        batch[j].block_type = b_type
                        batch[j].heading_level = h_lvl
                        batch[j].confidence = conf
                    continue
                except Exception:
                    pass
                # Fallback for this batch
                for b in batch:
                    b_type, h_lvl, conf = self._heuristic_classify(b.merged_text)
                    b.block_type = b_type
                    b.heading_level = h_lvl
                    b.confidence = conf
        else:
            for b in blocks:
                b_type, h_lvl, conf = self._heuristic_classify(b.merged_text)
                b.block_type = b_type
                b.heading_level = h_lvl
                b.confidence = conf

    def _call_pass2_batch_api(self, texts: list[str]) -> list[tuple[BlockType, int, float]]:
        """Batch call remote TypeSafe System One API for block classification."""
        if len(texts) == 1:
            res = self._call_pass2_single_api(texts[0])
            return [res]

        questions: dict[str, Any] = {}
        for idx in range(len(texts)):
            questions[f"b{idx}_type"] = {
                "type": "choice",
                "instructions": f"What structural Markdown block element is state.blocks[{idx}]?",
                "criteria": self.QUESTIONS_PASS2["block_type"]["criteria"],
            }
            questions[f"b{idx}_level"] = {
                "type": "score",
                "instructions": f"If state.blocks[{idx}] is a heading, rate its hierarchical level from 1 (major chapter) to 3 (sub-topic).",
                "criteria": self.QUESTIONS_PASS2["heading_level"]["criteria"],
            }

        url = f"{self.base_url}/v1/systemone"
        payload = {
            "model": "jev-latest",
            "state": {"blocks": texts},
            "questions": questions,
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
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            answers = data.get("answers", {})
            out: list[tuple[BlockType, int, float]] = []
            for idx in range(len(texts)):
                ans_type = answers.get(f"b{idx}_type", {})
                ans_lvl = answers.get(f"b{idx}_level", {})

                b_type_str = str(ans_type.get("choice", "paragraph"))
                b_type = BlockType(b_type_str) if b_type_str in BlockType._value2member_map_ else BlockType.PARAGRAPH

                # Jev score is continuous 0.0 to 2.0; map 0 -> level 1, 1 -> level 2, 2 -> level 3
                raw_score = float(ans_lvl.get("score", 1.0))
                h_level = max(1, min(3, round(raw_score) + 1))
                conf = float(ans_type.get("confidence", 1.0))
                out.append((b_type, h_level, conf))
            self.api_calls += 1
            return out

    def _call_pass2_single_api(self, text: str) -> tuple[BlockType, int, float]:
        """Single block remote TypeSafe API call for Pass 2 classification."""
        url = f"{self.base_url}/v1/systemone"
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
            raw_score = float(data["answers"]["heading_level"]["score"])
            h_level = max(1, min(3, round(raw_score) + 1))
            conf = float(data["answers"]["block_type"].get("confidence", 1.0))
            self.api_calls += 1
            return b_type, h_level, conf

    @staticmethod
    def _heuristic_classify(text: str) -> tuple[BlockType, int, float]:
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
        """Verify verbatim character preservation with sequence matching."""
        import difflib

        raw_chars = [c for c in raw_text if not c.isspace()]
        rec_chars = [c for c in "".join(b.merged_text for b in blocks) if not c.isspace()]

        if not raw_chars:
            return 1.0 if not rec_chars else 0.0

        matcher = difflib.SequenceMatcher(None, raw_chars, rec_chars)
        matched_count = 0
        deleted_hyphens = 0

        for tag, i1, i2, _j1, _j2 in matcher.get_opcodes():
            if tag == "equal":
                matched_count += (i2 - i1)
            elif tag == "delete":
                # Deletions from raw_chars are only excused if they are hyphens removed by dehyphenation
                deleted_chars = raw_chars[i1:i2]
                for c in deleted_chars:
                    if c in {"-", "\u00ad"} and deleted_hyphens < dehyphen_count:
                        deleted_hyphens += 1
                        matched_count += 1

        total_expected = len(raw_chars)
        return min(1.0, matched_count / max(1, total_expected))


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
