#!/usr/bin/env python3
"""Run the existing immersion gate against the Pass 2 module."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.build.linear_pipeline import _immersion_gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = _immersion_gate(
        args.module.read_text(encoding="utf-8"),
        {"level": "a1", "sequence": 20},
    )
    result["experiment_target_min_pct"] = 18
    result["experiment_target_max_pct"] = 22
    result["experiment_cap_pct"] = 24
    result["experiment_passed"] = 18 <= float(result["pct"]) <= 22
    result["experiment_cap_passed"] = float(result["pct"]) <= 24
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.json_out:
        args.json_out.write_text(output + "\n", encoding="utf-8")
    return 0 if result["experiment_cap_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
