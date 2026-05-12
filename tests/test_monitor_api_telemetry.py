"""Monitor API endpoint tests for opt-in context telemetry."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api.main import app


def _write_transcript(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "usage": {
                                "input_tokens": 100_000,
                                "cache_read_input_tokens": 20_000,
                                "cache_creation_input_tokens": 5_000,
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "usage": {
                                "input_tokens": 150_000,
                                "cache_read_input_tokens": 30_000,
                                "cache_creation_input_tokens": 7_000,
                            }
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_rules_markdown_appends_footer_when_enabled(tmp_path, monkeypatch) -> None:
    transcript = tmp_path / "session.jsonl"
    _write_transcript(transcript)
    monkeypatch.setenv("LEARN_UKRAINIAN_TELEMETRY_FOOTER", "1")
    monkeypatch.setenv("LEARN_UKRAINIAN_TRANSCRIPT_PATH", str(transcript))

    response = TestClient(app).get("/api/rules?format=markdown")

    assert response.status_code == 200
    assert response.text.endswith(
        "\n\n[ctx: 187K (+62K this turn), tier: base, 13K to premium, turn: 2]\n"
    )
    assert response.headers["X-Rules-Hash"]
    assert "etag" not in response.headers


def test_manifest_json_adds_structured_telemetry_when_enabled(tmp_path, monkeypatch) -> None:
    transcript = tmp_path / "session.jsonl"
    _write_transcript(transcript)
    monkeypatch.setenv("LEARN_UKRAINIAN_TELEMETRY_FOOTER", "1")
    monkeypatch.setenv("LEARN_UKRAINIAN_TRANSCRIPT_PATH", str(transcript))

    response = TestClient(app).get("/api/state/manifest")

    assert response.status_code == 200
    assert response.json()["_telemetry"] == {
        "ctx": 187_000,
        "prev_ctx": 125_000,
        "delta": 62_000,
        "tier": "base",
        "distance_tokens": 13_000,
        "distance_label": "to premium",
        "turn": 2,
        "source": "transcript-jsonl",
    }
