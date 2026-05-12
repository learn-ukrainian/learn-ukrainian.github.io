#!/usr/bin/env python3
"""Invoke the Claude adapter once and save Pass 2 artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.agent_runtime.runner import invoke
from scripts.build import linear_pipeline
from scripts.build.linear_pipeline import LinearPipelineError


def _extract_fenced_artifacts(raw_output: str, out_dir: Path) -> list[str]:
    extracted = []
    for name in linear_pipeline.WRITER_ARTIFACTS:
        pattern = re.compile(
            rf"(?m)^{re.escape(name)}\s*\n"
            rf"```[^\n]*\b(?:file=)?{re.escape(name)}\b[^\n]*\n"
            r"(?P<body>.*?)\n```",
            re.DOTALL,
        )
        match = pattern.search(raw_output)
        if match is None:
            continue
        (out_dir / name).write_text(match.group("body").strip() + "\n", encoding="utf-8")
        extracted.append(name)
    return extracted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    prompt = args.prompt.read_text(encoding="utf-8")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    result = invoke(
        "claude",
        prompt,
        mode="workspace-write",
        cwd=Path.cwd(),
        model=linear_pipeline.WRITER_DEFAULTS["claude-tools"]["model"],
        effort=linear_pipeline.WRITER_DEFAULTS["claude-tools"]["effort"],
        task_id="pass2-only-contract-test-2026-05-13",
        entrypoint="dispatch",
        tool_config=linear_pipeline._runtime_tool_config("claude-tools"),
        hard_timeout=7200,
        stdout_silence_timeout=1800,
    )
    duration_s = round(time.monotonic() - started, 3)

    raw_path = args.out_dir / "writer_output.raw.md"
    raw_path.write_text(result.response, encoding="utf-8")
    (args.out_dir / "writer_tool_calls.json").write_text(
        json.dumps(result.tool_calls, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    metadata = {
        "ok": result.ok,
        "agent": result.agent,
        "model": result.model,
        "effort": result.effort,
        "cli_version": result.cli_version,
        "duration_s": duration_s,
        "usage_record": result.usage_record,
        "tokens": result.usage_record.get("tokens"),
        "input_chars": result.usage_record.get("input_chars"),
        "output_chars": result.usage_record.get("output_chars"),
    }
    (args.out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    try:
        artifacts = linear_pipeline.parse_writer_output(result.response)
    except LinearPipelineError as exc:
        (args.out_dir / "parse_error.txt").write_text(str(exc) + "\n", encoding="utf-8")
        extracted = _extract_fenced_artifacts(result.response, args.out_dir)
        print(f"strict_parse=FAIL: {exc}")
        print(f"raw_fences_extracted={','.join(extracted)}")
        return 2

    for name, content in artifacts.items():
        (args.out_dir / name).write_text(content, encoding="utf-8")

    print(f"duration_s={duration_s}")
    print(f"tokens={metadata['tokens']}")
    print(f"input_chars={metadata['input_chars']}")
    print(f"output_chars={metadata['output_chars']}")
    print(f"raw_output={raw_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
