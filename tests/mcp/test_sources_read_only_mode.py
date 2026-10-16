"""The sources server a Cursor author sees cannot write (#10837).

The author mirror launches the server with ``LU_SOURCES_READ_ONLY=1``. These tests
attempt every tool that persists a live fetch against that mode and check the stores
are byte-identical afterwards, with a positive control showing the same calls do
change them without the mode. The probe runs hermetically: scratch stores and a fake
network (``sources_side_effects_probe.py``). The stdio test launches the exact entry
the mirror writes and talks MCP to it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import mcp  # noqa: F401  # Declares the Sources wire dependency to the CI fastlane.
import pytest

from scripts.agent_runtime import review_mcp
from scripts.agent_runtime.sources_read_only import READ_ONLY_ENV, server_read_only_env, sources_tool_sets
from scripts.common.repo_root import project_interpreter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROBE = Path(__file__).with_name("sources_side_effects_probe.py")
SERVER_PATH = PROJECT_ROOT / ".mcp" / "servers" / "sources" / "server.py"
READ_ONLY_TOOLS, PERSISTING_TOOLS = sources_tool_sets(SERVER_PATH)
# The writers the side-effect audit found (#9551); the mode must hold whatever the annotations say.
KNOWN_WRITERS = (
    "query_ulif",
    "query_ulif_antonyms",
    "query_ulif_phraseology",
    "query_ulif_synonyms",
    "query_wikipedia",
)
# Read-only lookups that must keep working in the mode (each has a hermetic fixture row).
READ_ONLY_SAMPLE = ("query_ulif_records", "search_text", "verify_words")


def _run_probe(scratch: Path, *flags: str, tools: tuple[str, ...]) -> tuple[dict[str, dict], dict]:
    args = [arg for name in tools for arg in ("--tool", name)]
    env = {key: value for key, value in os.environ.items() if key != READ_ONLY_ENV}
    proc = subprocess.run(
        [sys.executable, str(PROBE), "--scratch", str(scratch), "--hermetic", *flags, *args],
        capture_output=True,
        text=True,
        env={**env, "PYTHONDONTWRITEBYTECODE": "1"},
        cwd=PROJECT_ROOT,
        timeout=600,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-4000:]
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    stores = [line["stores"] for line in lines if "stores" in line]
    assert len(stores) == 1, lines
    return {line["tool"]: line for line in lines if "tool" in line}, stores[0]


def test_the_persisting_tools_are_the_audited_writers() -> None:
    assert PERSISTING_TOOLS == KNOWN_WRITERS
    assert server_read_only_env(SERVER_PATH) == READ_ONLY_ENV


def test_read_only_mode_refuses_every_writer_before_any_write_attempt(tmp_path: Path) -> None:
    """Audited: no persisting tool reaches a write, a network fetch or a store, and read-only lookups still answer."""
    results, stores = _run_probe(tmp_path, "--read-only-mode", tools=PERSISTING_TOOLS + READ_ONLY_SAMPLE)
    for name in PERSISTING_TOOLS:
        result = results[name]
        assert result["is_error"] is True, result
        assert result["result_head"] == f"Tool {name} is not served in read-only mode.", result
        assert (result["writes"], result["network"]) == ([], []), result
    for name in READ_ONLY_SAMPLE:
        assert (results[name]["is_error"], results[name]["hit"]) == (False, True), results[name]
    assert stores["before"] == stores["after"]


def test_read_only_mode_leaves_the_stores_byte_identical_when_writes_are_possible(tmp_path: Path) -> None:
    """Unaudited, so nothing but the mode stands between each writer and the stores."""
    results, stores = _run_probe(tmp_path, "--read-only-mode", "--unaudited", tools=PERSISTING_TOOLS)
    assert sorted(results) == sorted(PERSISTING_TOOLS)
    assert all(result["is_error"] and result["network"] == [] for result in results.values()), results
    assert stores["before"] == stores["after"]
    assert "wiki_cache.db" not in stores["after"]


def test_without_the_mode_the_same_calls_change_the_stores(tmp_path: Path) -> None:
    """Positive control: the byte comparison above can fail."""
    results, stores = _run_probe(tmp_path, "--unaudited", tools=PERSISTING_TOOLS)
    assert not any(result["is_error"] for result in results.values()), results
    assert "wiki_cache.db" in stores["after"] and "wiki_cache.db" not in stores["before"]
    assert stores["after"]["sources.db"] != stores["before"]["sources.db"]


def _rpc(proc: subprocess.Popen, message: dict) -> dict:
    """Send one request and return its reply (notifications in between are skipped)."""
    proc.stdin.write(json.dumps(message).encode("utf-8") + b"\n")
    proc.stdin.flush()
    while True:
        line = proc.stdout.readline()
        assert line, "the server closed its output"
        reply = json.loads(line)
        if reply.get("id") == message["id"]:
            return reply


def test_the_mirrored_launch_serves_read_only_mode_over_stdio(tmp_path: Path) -> None:
    """The exact entry the mirror writes, started the way Cursor starts it, lists no writer and refuses each one.

    The session environment tries to switch the mode off; ``env -i`` keeps it out.
    """
    server = review_mcp.read_only_sources_mcp_server(project_interpreter(), SERVER_PATH)
    assert server["command"] == "/usr/bin/env"
    assert f"{READ_ONLY_ENV}=1" in server["args"]
    session_env = {**os.environ, READ_ONLY_ENV: "", "LU_MCP_SOURCES_LOG_DIR": str(tmp_path / "logs")}
    proc = subprocess.Popen(
        [server["command"], *server["args"]],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=session_env,
        cwd=tmp_path,
    )
    timer = threading.Timer(120, proc.kill)
    timer.start()
    try:
        init = {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}}
        assert _rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": init})["result"]
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode() + b"\n")
        listed = _rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        names = sorted(tool["name"] for tool in listed["result"]["tools"])
        replies = {}
        for index, name in enumerate(PERSISTING_TOOLS):
            # Valid arguments, so a refusal is the mode's and not schema validation's.
            arguments = {"query": "мова"} if name == "query_wikipedia" else {"word": "мова"}
            params = {"name": name, "arguments": arguments}
            replies[name] = _rpc(proc, {"jsonrpc": "2.0", "id": 3 + index, "method": "tools/call", "params": params})
        _, stderr = proc.communicate()  # Closes stdin: the server exits at end of input.
    finally:
        timer.cancel()
        if proc.poll() is None:
            proc.kill()
    assert names == list(READ_ONLY_TOOLS), stderr.decode("utf-8", "replace")[-2000:]
    for name, reply in replies.items():
        assert reply["result"]["isError"] is True, (name, reply)
    assert not (tmp_path / "logs").exists()


@pytest.mark.parametrize("declaration", ["", 'READ_ONLY_ENV = "LU_SOMETHING_ELSE"\n'])
def test_server_read_only_env_reads_the_declaration(tmp_path: Path, declaration: str) -> None:
    server = tmp_path / "server.py"
    server.write_text(f"import os\n{declaration}", encoding="utf-8")
    assert server_read_only_env(server) == ("LU_SOMETHING_ELSE" if declaration else None)
