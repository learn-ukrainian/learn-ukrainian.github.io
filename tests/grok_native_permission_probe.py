"""Deterministic native Grok permission probe; no paid provider or real credentials.

Run from the import root with the project's interpreter. All tool requests and
responses are synthetic fixtures; only summary booleans leave the scratch lease.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from scripts.agent_runtime.grok_reviewer_permissions import GROK_REVIEWER_READ_COMMANDS, REFUSAL_CODE

ROOT = Path(__file__).resolve().parents[1]


def probe(grok: str, mode: str, hook: str, action: str, deny_bash: bool = False) -> dict[str, Any]:
    """Run one synthetic tool call, observing execution independently of narration."""
    with tempfile.TemporaryDirectory(prefix="grok-permission-", dir=os.environ["TMPDIR"]) as scratch:
        base = Path(scratch)
        repo = base / "checkout"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=10)
        (repo / "tracked.txt").write_text("TRACKED_READ_FIXTURE\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True, timeout=10)
        requests = []
        tool = "read_file" if action == "read" else "run_terminal_command"
        inputs = {"target_file": "tracked.txt"} if action == "read" else {"command": {
            "literal": GROK_REVIEWER_READ_COMMANDS[0],
            "write": "awk 'BEGIN { print \"EXECUTED\" > \"forbidden-marker\" }'",
            "redirect": "pwd > forbidden-marker",
        }[action], "description": "Synthetic scratch-only fixture", "is_background": False}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                data = json.dumps({"object": "list", "data": [{"id": "permission-fixture", "object": "model"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append(request)
                result_seen = any(message.get("role") == "tool" for message in request.get("messages", []))
                message = {"role": "assistant", "content": "FIXTURE_END"}
                finish = "stop"
                if not result_seen:
                    message["content"] = None
                    message["tool_calls"] = [{"id": "call_fixture", "type": "function", "function": {
                        "name": tool, "arguments": json.dumps(inputs),
                    }}]
                    finish = "tool_calls"
                if request.get("stream"):
                    delta = {"role": "assistant"}
                    if "tool_calls" in message:
                        delta["tool_calls"] = [{"index": 0, **message["tool_calls"][0]}]
                    else:
                        delta["content"] = message["content"]
                    chunks = [{"id": "fixture", "object": "chat.completion.chunk", "created": 0,
                               "model": "permission-fixture", "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                              {"id": "fixture", "object": "chat.completion.chunk", "created": 0,
                               "model": "permission-fixture", "choices": [{"index": 0, "delta": {}, "finish_reason": finish}]}]
                    data = ("".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks) + "data: [DONE]\n\n").encode()
                    content_type = "text/event-stream"
                else:
                    data = json.dumps({"id": "fixture", "object": "chat.completion", "created": 0,
                                       "model": "permission-fixture", "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                                       "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}).encode()
                    content_type = "application/json"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        grok_home = base / "grok-home"
        grok_home.mkdir()
        config = f'''[cli]
use_leader = false
[compat.claude]
agents = false
hooks = false
mcps = false
rules = false
skills = false
[features]
telemetry = "off"
[telemetry]
otel_enabled = false
trace_upload = false
[model.permission-fixture]
model = "permission-fixture"
base_url = "http://127.0.0.1:{server.server_port}/v1"
api_key = "local-fixture"
api_backend = "chat_completions"
max_retries = 0
'''
        (grok_home / "config.toml").write_text(config, encoding="utf-8")
        env = {key: os.environ[key] for key in ("PATH", "HOME", "TMPDIR", "LANG") if key in os.environ}
        env.update(GROK_HOME=str(grok_home), GROK_CLAUDE_HOOKS_ENABLED="0", GROK_CLAUDE_MCPS_ENABLED="0")
        cmd = [grok, "-p", "Synthetic permission fixture", "--cwd", str(repo), "-m", "permission-fixture",
               "--output-format", "json", "--no-alt-screen", "--no-subagents", "--disable-web-search",
               "--max-turns", "3", "--permission-mode", mode, "--tools", "read_file,list_dir,grep,run_terminal_command",
               "--deny", "Write", "--deny", "Edit", "--deny", "MCPTool", "--deny", "WebFetch"]
        if deny_bash:
            cmd.extend(["--deny", "Bash"])
        for rule in ("Read", "Grep", *(f"Bash({command})" for command in GROK_REVIEWER_READ_COMMANDS)):
            cmd.extend(["--allow", rule])
        if hook != "removed":
            command = shlex.join([str(ROOT / "scripts/agent_runtime/grok_reviewer_permissions.py"), "--review-root", str(repo)])
            # Use the interpreter supplied to the harness, never an unqualified Python.
            command = shlex.quote(os.environ["LU_PROBE_INTERPRETER"]) + " " + command
            if hook == "crashing":
                command = f"printf entered > {shlex.quote(str(base / 'hook-entered'))}; exit 1"
            if hook == "missing-interpreter":
                command = shlex.join([str(base / "missing-interpreter"), "guard"])
            agent = base / "agent.md"
            agent.write_text("---\nname: permission-fixture\ndescription: Synthetic permission test\nhooks:\n"
                             "  PreToolUse:\n    - matcher: \".*\"\n      hooks:\n        - type: command\n"
                             f"          command: {json.dumps(command)}\n          timeout: 15\n---\nSynthetic fixture.\n", encoding="utf-8")
            cmd.extend(["--agent", str(agent)])
        try:
            completed = subprocess.run(cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=45)
            try:
                envelope = json.loads(completed.stdout)
            except ValueError:
                envelope = {}
            tool_results = [message for request in requests for message in request.get("messages", []) if message.get("role") == "tool"]
            rendered = json.dumps(tool_results)
            # No raw session, request, response, stderr or paths are printed.
            return {"mode": mode, "hook": hook, "action": action, "deny_bash": deny_bash,
                    "returncode": completed.returncode, "stopReason": envelope.get("stopReason"),
                    "provider_requests": len(requests), "tool_result_seen": bool(tool_results),
                    "typed_refusal_seen": REFUSAL_CODE in rendered,
                    "read_fixture_seen": "TRACKED_READ_FIXTURE" in rendered,
                    "marker_written": (repo / "forbidden-marker").exists(),
                    "cancelled": envelope.get("stopReason") == "cancelled",
                    "permission_denied_seen": "denied" in rendered.lower() or "blocked" in rendered.lower(),
                    "literal_fixture_seen": "exit: 0\\nA  tracked.txt" in rendered,
                    "invalid_arguments": "Failed to parse arguments" in rendered,
                    "hook_entered": (base / "hook-entered").exists(),
                    "stderr_present": bool(completed.stderr.strip())}
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe native Grok permissions with a local scripted provider.\nUse for #9987 reproduction, never as a real model evaluation.",
        epilog="Examples: <project-interpreter> -m tests.grok_native_permission_probe --mode dontAsk\n"
               "Outputs: summary JSON lines; scratch checkouts and Grok state removed on exit.\n"
               "Exit codes: 0 probes ran; nonzero harness/configuration error.\nRelated: #9987; grok_reviewer_permissions.py.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--matrix", action="store_true", help="Run the documented mode/hook matrix (default: off); overrides individual probe flags.")
    parser.add_argument("--mode", default="dontAsk", choices=["default", "acceptEdits", "auto", "dontAsk", "bypassPermissions", "plan"], help="Native permission mode (default: dontAsk).")
    parser.add_argument("--hook", default="working", choices=["working", "removed", "crashing", "missing-interpreter"], help="Hook condition (default: working).")
    parser.add_argument("--action", default="write", choices=["read", "literal", "write", "redirect"], help="Scripted tool request (default: write); writes stay inside scratch checkout.")
    parser.add_argument("--deny-bash", action="store_true", help="Add blanket Bash deny (default: off) to test deny precedence.")
    args = parser.parse_args()
    grok = shutil.which("grok")
    if not grok:
        parser.error("native grok CLI is required")
    if not os.environ.get("TMPDIR") or not os.environ.get("LU_PROBE_INTERPRETER"):
        parser.error("TMPDIR and LU_PROBE_INTERPRETER must be configured")
    if args.matrix:
        cases = [
            (mode, "working", action, False)
            for mode in ("default", "acceptEdits", "auto", "dontAsk", "plan", "bypassPermissions")
            for action in ("read", "literal", "write")
        ]
        cases += [(mode, hook, "write", deny)
                  for mode, deny in (("dontAsk", False), ("bypassPermissions", False), ("auto", True))
                  for hook in ("removed", "crashing", "missing-interpreter")]
        cases += [("auto", "working", "read", True), ("auto", "working", "literal", True)]
    else:
        cases = [(args.mode, args.hook, args.action, args.deny_bash)]
    for mode, hook, action, deny in cases:
        result = probe(grok, mode, hook, action, deny)
        print(json.dumps(result), flush=True)
        if result["invalid_arguments"] or result["provider_requests"] == 0 or result["stopReason"] is None:
            return 1  # A parsing/provider failure is never permission evidence.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
