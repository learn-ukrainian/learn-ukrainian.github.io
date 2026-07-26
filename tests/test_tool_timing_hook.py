"""Contract tests for the fire-and-forget tool-timing hook."""

from __future__ import annotations

import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from scripts.api.telemetry_router import ToolTimingIngest

_ROOT = Path(__file__).resolve().parents[1]
_HOOK = _ROOT / "agents_extensions" / "shared" / "hooks" / "tool-timing.sh"


@pytest.mark.parametrize(
    "event_result",
    [
        {"hook_event_name": "PostToolUseFailure"},
        {
            "hook_event_name": "PostToolUse",
            "tool_response": {"exit_code": 1},
        },
    ],
)
def test_hook_posts_json_that_validates_against_tool_timing_model(
    event_result: dict[str, object],
) -> None:
    posted: list[dict[str, object]] = []
    received = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers["Content-Length"])
            posted.append(json.loads(self.rfile.read(content_length)))
            self.send_response(200)
            self.end_headers()
            received.set()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        event: dict[str, object] = {
            "tool_name": 'Bash "quoted" \\ path\nnext',
            "duration_ms": 12.5,
            "tool_use_id": 'tool "id"',
            "session_id": "session\\id",
            **event_result,
        }
        environment = os.environ.copy()
        environment["TOOL_TIMING_API_URL"] = f"http://127.0.0.1:{server.server_port}/tool-timings"
        result = subprocess.run(
            ["/bin/bash", str(_HOOK)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            env=environment,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert received.wait(timeout=3), "hook did not post telemetry"
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()

    assert len(posted) == 1
    payload = posted[0]
    model = ToolTimingIngest.model_validate(payload)
    assert model.tool_name == event["tool_name"]
    assert model.duration_ms == 13
    assert model.tool_use_id == event["tool_use_id"]
    assert model.session_id == event["session_id"]
    assert model.failed is True
