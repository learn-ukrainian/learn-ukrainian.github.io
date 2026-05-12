#!/usr/bin/env python3
"""Deterministically verify Pass 2 preserved Pass 1 anchor content."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ANCHOR_PREFIX = "<!-- ANCHOR "
ANCHOR_SUFFIX = " -->"


@dataclass(frozen=True)
class AnchorBlock:
    anchor_id: str
    content: str
    line_no: int

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


def _anchor_id_from_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith(ANCHOR_PREFIX) or not stripped.endswith(ANCHOR_SUFFIX):
        return None
    return stripped[len(ANCHOR_PREFIX) : -len(ANCHOR_SUFFIX)].strip()


def extract_anchor_blocks(text: str) -> dict[str, AnchorBlock]:
    """Extract anchors as the marker plus the next physical content line."""
    lines = text.splitlines()
    anchors: dict[str, AnchorBlock] = {}
    for index, line in enumerate(lines):
        anchor_id = _anchor_id_from_line(line)
        if anchor_id is None:
            continue
        if index + 1 >= len(lines):
            raise ValueError(f"{anchor_id}: marker at line {index + 1} has no content line")
        if anchor_id in anchors:
            raise ValueError(f"{anchor_id}: duplicate marker at line {index + 1}")
        anchors[anchor_id] = AnchorBlock(
            anchor_id=anchor_id,
            content=lines[index + 1],
            line_no=index + 1,
        )
    return anchors


def load_expected(path: Path) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    anchors = data.get("anchors")
    if not isinstance(anchors, list):
        raise ValueError(f"{path} must contain an anchors list")
    expected: dict[str, dict[str, str]] = {}
    for item in anchors:
        if not isinstance(item, dict):
            raise ValueError(f"{path} contains a non-object anchor entry")
        anchor_id = str(item["id"])
        expected[anchor_id] = {
            "sha256": str(item["sha256"]),
            "content": str(item["content"]),
        }
    return expected


def compare_anchors(expected_path: Path, module_path: Path) -> dict[str, Any]:
    expected = load_expected(expected_path)
    actual = extract_anchor_blocks(module_path.read_text(encoding="utf-8"))

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    mismatches = []
    for anchor_id in sorted(set(expected) & set(actual)):
        expected_hash = expected[anchor_id]["sha256"]
        actual_hash = actual[anchor_id].sha256
        if expected_hash == actual_hash:
            continue
        expected_content = expected[anchor_id]["content"]
        actual_content = actual[anchor_id].content
        mismatches.append(
            {
                "id": anchor_id,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "line_no": actual[anchor_id].line_no,
                "diff": "\n".join(
                    difflib.unified_diff(
                        [expected_content],
                        [actual_content],
                        fromfile=f"pass1/{anchor_id}",
                        tofile=f"pass2/{anchor_id}",
                        lineterm="",
                    )
                ),
            }
        )

    passed = not missing and not extra and not mismatches
    return {
        "passed": passed,
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing": missing,
        "extra": extra,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchors-json", type=Path, required=True)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = compare_anchors(args.anchors_json, args.module)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.json_out:
        args.json_out.write_text(output + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
