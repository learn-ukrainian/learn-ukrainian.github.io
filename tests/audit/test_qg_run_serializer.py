from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.audit import llm_reviewer_dispatch, qg_bakeoff

PRE_EXTRACTION_ARTIFACT_SHA256 = "0b06f32e84f99d8e5949b70b3bdf90eb96710d9a411465830f4bee06ce589b20"


def test_bakeoff_tooled_artifact_matches_pre_extraction_golden_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The extraction preserves the existing sorted JSON artifact byte-for-byte."""

    monkeypatch.setenv("QG_BAKEOFF", "1")
    monkeypatch.setattr(qg_bakeoff, "_now_z", lambda: "2026-07-14T00:00:00Z")
    monkeypatch.setattr(qg_bakeoff.time, "monotonic", lambda: 0.0)
    route = qg_bakeoff.bakeoff_route_for_model("openrouter/test/parity-model")
    fixture = qg_bakeoff.BakeoffFixture(
        slug="parity",
        title="Parity",
        passage_md="Веснянки — це весняні обрядові пісні.",
        claims=(
            qg_bakeoff.FixtureClaim(
                "claim-1",
                "Веснянки — це весняні обрядові пісні.",
                True,
            ),
        ),
    )
    response = {
        "findings": [],
        "fact_checks": [
            {
                "claim": "Веснянки — це весняні обрядові пісні.",
                "verdict": "CONFIRMED",
                "grounding": {
                    "tool": "sources_query_wikipedia",
                    "query": "веснянки",
                    "evidence_excerpt": "Веснянки — це весняні обрядові пісні.",
                    "tool_call_id": "call-1",
                },
            }
        ],
        "evidence_gaps": [],
    }

    def runner(
        selected_route: llm_reviewer_dispatch.ReviewerRoute,
        _prompt: str,
        _task_id: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        return llm_reviewer_dispatch.DispatchResult(
            response_text=json.dumps(response, ensure_ascii=False),
            reviewer_model_id=selected_route.reviewer_model_id,
            reviewer_family=selected_route.reviewer_family,
            route_name=selected_route.route_name,
            tool_call_count=1,
            tools_used=("sources_query_wikipedia",),
            tool_events=(
                {
                    "tool": "sources_query_wikipedia",
                    "input": {"query": "веснянки"},
                    "status": "completed",
                    "tool_call_id": "call-1",
                    "output": "Веснянки — це весняні обрядові пісні.",
                },
            ),
        )

    artifact = qg_bakeoff.run_one(route, fixture, output_dir=tmp_path, runner=runner)

    assert hashlib.sha256(artifact.artifact_path.read_bytes()).hexdigest() == PRE_EXTRACTION_ARTIFACT_SHA256
