"""Parameterized stdin/stdout stub for module-envelope qualification tests."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _role(relation: str) -> str | None:
    return {
        "ENTAILS": "SUPPORTS",
        "CONTRADICTS": "CONTRADICTS",
        "EXPLICITLY_UNCERTAIN": "UNCERTAINTY",
    }.get(relation)


def main() -> int:
    request = json.load(sys.stdin)
    counter = os.environ.get("LAYERB_STUB_COUNTER")
    if counter:
        with Path(counter).open("a", encoding="utf-8") as handle:
            handle.write("1\n")
    if os.environ.get("LAYERB_STUB_EXIT"):
        return int(os.environ["LAYERB_STUB_EXIT"])
    relation = os.environ.get("LAYERB_STUB_RELATION", "ENTAILS")
    confidence = os.environ.get("LAYERB_STUB_CONFIDENCE", "high")
    injection = os.environ.get("LAYERB_STUB_INJECTION", "false").casefold() == "true"
    span_mode = os.environ.get("LAYERB_STUB_SPANS", "valid")
    fact_checks = []
    for fact_check in request["fact_checks"]:
        source_relations = []
        for source in fact_check["candidate_sources"]:
            role = _role(relation)
            spans = [] if role is None else [{"start": 0, "end": source["raw_window_end"], "role": role}]
            if span_mode == "empty":
                spans = []
            elif span_mode == "out-of-bounds" and role is not None:
                spans = [{"start": 0, "end": source["raw_window_end"] + 1, "role": role}]
            source_relations.append(
                {
                    "candidate_id": source["candidate_id"],
                    "relation": relation,
                    "support_spans": spans,
                    "confidence": confidence,
                    "prompt_injection_observed": injection,
                }
            )
        fact_checks.append({"fact_check_id": fact_check["fact_check_id"], "source_relations": source_relations})
    json.dump(
        {
            "schema_version": "qg-layer-b-judge-output.v1",
            "_shadow_observed": {
                "prompt_tokens": 120,
                "completion_tokens": 30,
                "cost_usd": 0.001,
                "latency_seconds": 0.01,
            },
            "fact_checks": fact_checks,
        },
        sys.stdout,
        ensure_ascii=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
