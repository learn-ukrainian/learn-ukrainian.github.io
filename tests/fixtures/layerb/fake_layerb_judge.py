"""Deterministic external fake judge for Layer-B shadow CLI demonstrations."""

import json
import sys

request = json.load(sys.stdin)
fact_check = request["fact_checks"][0]
source = fact_check["candidate_sources"][0]
json.dump(
    {
        "schema_version": "qg-layer-b-judge-output.v1",
        "_shadow_observed": {
            "prompt_tokens": 71,
            "completion_tokens": 12,
            "cost_usd": 0.001,
            "latency_seconds": 0.01,
        },
        "fact_checks": [
            {
                "fact_check_id": fact_check["fact_check_id"],
                "source_relations": [
                    {
                        "candidate_id": source["candidate_id"],
                        "relation": "ENTAILS",
                        "support_spans": [{"start": 0, "end": 11, "role": "SUPPORTS"}],
                        "confidence": "high",
                        "prompt_injection_observed": False,
                    }
                ],
            }
        ],
    },
    sys.stdout,
    ensure_ascii=False,
)
