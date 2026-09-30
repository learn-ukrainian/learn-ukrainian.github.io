"""Every seat loads the rules core: one deterministic test per loading-matrix row.

Each row builds the context that seat would actually receive — a launcher's exact
dry-run argv (``LAUNCHER_DRY_RUN_ARGV_FILE``), a ``delegate.py`` worker prompt handed
to each adapter's ``build_invocation``, an ACP call through ``invoke_inter_agent``,
a legacy bridge prompt — and asserts that the core's first and last pillar anchors
are in it. Bytes carried per row are printed (``pytest -s``).

The core is ``agents_extensions/shared/rules/core.md`` when this checkout has it;
otherwise ``tests/fixtures/rules_core/`` stands in, through the loader's
``LU_RULES_CORE_DIR`` seam.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from scripts.lib import rules_core
from tests.test_launcher_contract import REPO, hermes_stub_env

REAL_CORE_DIR = REPO / rules_core.RULES_DIR_REL
FIXTURE_CORE_DIR = REPO / "tests" / "fixtures" / "rules_core"
CORE_DIR = (
    REAL_CORE_DIR
    if (REAL_CORE_DIR / "core.md").is_file() and (REAL_CORE_DIR / "core-curriculum.md").is_file()
    else FIXTURE_CORE_DIR
)


@pytest.fixture(autouse=True)
def _core_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """Opt back in to the core (tests/conftest.py keeps it out of other tests)."""
    monkeypatch.setenv(rules_core.CORE_DIR_ENV, str(CORE_DIR))
    monkeypatch.delenv(rules_core.SEAT_ENV, raising=False)


def _anchors(seat: str) -> tuple[str, ...]:
    first, last = rules_core.pillar_anchors(rules_core.core_text("core"))
    if seat == "core":
        return first, last
    addendum = [
        line for line in (CORE_DIR / "core-curriculum.md").read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    return first, last, addendum[0], addendum[-1]


def _assert_core(context: str, seat: str, row: str, *, context_bytes: int | None = None) -> None:
    block = rules_core.core_block(seat)
    assert block in context, f"{row}: the exact {seat} block is not in the assembled context"
    for anchor in _anchors(seat):
        assert anchor in context, f"{row}: anchor {anchor!r} missing"
    if seat == "core":
        addendum_first = _anchors("content")[2]
        assert addendum_first not in context, f"{row}: a core seat must not carry the curriculum addendum"
    if context_bytes is None:
        context_bytes = len(context.encode("utf-8"))
    print(
        f"[rules-core bytes] {row}: seat={seat} core_bytes={len(block.encode('utf-8'))} context_bytes={context_bytes}"
    )


# --------------------------------------------------------------------------- loader


def test_canonical_core_paths_are_the_rules_directory() -> None:
    assert rules_core.CORE_REL == "agents_extensions/shared/rules/core.md"
    assert rules_core.CONTENT_ADDENDUM_REL == "agents_extensions/shared/rules/core-curriculum.md"


def test_seat_resolution_explicit_env_then_lane(monkeypatch: pytest.MonkeyPatch) -> None:
    assert rules_core.resolve_seat() == "core"
    assert rules_core.resolve_seat("content") == "content"
    assert rules_core.resolve_seat(lane="core", provider="claude") == "content"
    assert rules_core.resolve_seat(lane="infra", provider="claude") == "core"
    monkeypatch.setenv(rules_core.SEAT_ENV, "content")
    assert rules_core.resolve_seat() == "content"
    assert rules_core.resolve_seat("core") == "core"
    monkeypatch.setenv(rules_core.SEAT_ENV, "bogus")
    assert rules_core.resolve_seat() == "core"


def test_block_frames_the_text_with_its_digest() -> None:
    text = rules_core.core_text("content")
    block = rules_core.core_block("content")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert block == f'<rules-core seat="content" sha256="{digest}">\n{text}</rules-core>'
    assert text.startswith((CORE_DIR / "core.md").read_text(encoding="utf-8").rstrip())


def test_with_core_prepends_once_and_fails_open(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    once = rules_core.with_core("task")
    assert once == rules_core.core_block("core") + "\n\ntask"
    assert rules_core.with_core(once) == once
    monkeypatch.setenv(rules_core.CORE_DIR_ENV, str(tmp_path / "missing"))
    assert rules_core.with_core("task") == "task"
    assert "continuing without the rules core" in capsys.readouterr().err


def test_toml_and_kimi_forms_round_trip() -> None:
    block = rules_core.core_block("core")
    assert tomllib.loads("v=" + rules_core.toml_basic_string(block + '\t"\\\x01'))["v"] == block + '\t"\\\x01'
    agent_file = rules_core.kimi_agent_file_text(block)
    assert agent_file.startswith("---\nname: rules-core\n")
    assert "${base_prompt}\n\n" + block in agent_file
    with pytest.raises(rules_core.RulesCoreError):
        rules_core.kimi_agent_file_text("x ${injected} y")


def test_cli_reports_anchors_and_exits_3_when_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    script = REPO / "scripts" / "lib" / "rules_core.py"
    ok = subprocess.run(
        [sys.executable, os.fspath(script), "--format", "json"], capture_output=True, text=True, check=False, timeout=60
    )
    assert ok.returncode == 0, ok.stderr
    payload = json.loads(ok.stdout)
    assert (payload["first_anchor"], payload["last_anchor"]) == _anchors("core")
    monkeypatch.setenv(rules_core.CORE_DIR_ENV, str(tmp_path / "missing"))
    missing = subprocess.run(
        [sys.executable, os.fspath(script)], capture_output=True, text=True, check=False, timeout=60
    )
    assert missing.returncode == 3
    assert "rules source unavailable" in missing.stderr


def test_shell_ack_matches_the_python_ack() -> None:
    shell = (REPO / "scripts" / "lib" / "rules_core.sh").read_text(encoding="utf-8")
    assert f'text="{rules_core.ACK_PROMPT}"' in shell


# --------------------------------------------------------------------------- launchers

_KIMI_CREDENTIALS = {"KIMICC_AUTH_TOKEN": "test-key", "MOONSHOT_API_KEY": "", "KIMI_API_KEY": ""}
_GLM_CREDENTIALS = {"GLMCC_AUTH_TOKEN": "", "ZAI_API_KEY": "test-key", "ZHIPU_API_KEY": "", "GLM_API_KEY": ""}

# (row, launcher, args, extra env kind, carrier, seat)
LAUNCHER_ROWS = (
    ("claude-interactive", "start-claude.sh", (), None, "--append-system-prompt", "core"),
    ("claude-driver", "start-claude-driver.sh", ("--epic", "infra"), None, "--append-system-prompt", "core"),
    (
        "claude-driver-curriculum",
        "start-claude-driver.sh",
        ("--epic", "curriculum-upgrade"),
        None,
        "--append-system-prompt",
        "content",
    ),
    ("codex-interactive", "start-codex.sh", (), None, "developer_instructions", "core"),
    ("codex-driver", "start-codex-driver.sh", ("--epic", "devops"), None, "developer_instructions", "core"),
    ("codex-claude-code", "start-codex.sh", ("--harness", "claude-code"), None, "--append-system-prompt", "core"),
    ("codex-hermes", "start-codex.sh", ("--harness", "hermes"), "hermes", "--query", "core"),
    ("gemini-agy-interactive", "start-gemini.sh", (), None, "-i", "core"),
    ("gemini-agy-driver", "start-gemini-driver.sh", ("--epic", "infra"), None, "-i", "core"),
    ("cursor-driver", "start-cursor-driver.sh", ("--epic", "infra"), None, "positional", "core"),
    ("grok-interactive", "start-grok.sh", (), None, "--rules", "core"),
    ("grok-driver", "start-grok-driver.sh", ("--epic", "infra"), None, "--rules", "core"),
    ("grok-hermes", "start-grok.sh", ("--harness", "hermes"), "hermes", "--query", "core"),
    ("kimi-native", "start-kimi.sh", (), None, "--agent-file", "core"),
    ("kimicc", "start-kimicc.sh", (), "kimi", "--append-system-prompt", "core"),
    ("glm-opencode", "start-glm.sh", (), None, "positional", "core"),
    ("glmcc", "start-glmcc.sh", (), "glm", "--append-system-prompt", "core"),
)


def _launch(
    name: str, args: tuple[str, ...], tmp_path: Path, env_kind: str | None, extra_env: dict[str, str] | None = None
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    argv_file = tmp_path / "argv.bin"
    env = {**os.environ, "LAUNCHER_DRY_RUN": "1", "LAUNCHER_DRY_RUN_ARGV_FILE": str(argv_file), "TMPDIR": str(tmp_path)}
    if env_kind == "hermes":
        env.update(hermes_stub_env(tmp_path))
    elif env_kind == "kimi":
        env.update({**_KIMI_CREDENTIALS, "HOME": str(tmp_path / "home")})
    elif env_kind == "glm":
        env.update({**_GLM_CREDENTIALS, "HOME": str(tmp_path / "home")})
    env.update(extra_env or {})
    result = subprocess.run(
        [str(REPO / name), *args], cwd=REPO, env=env, text=True, capture_output=True, check=False, timeout=120
    )
    assert result.returncode == 0, result.stderr
    assert argv_file.is_file(), result.stdout
    argv = argv_file.read_bytes().decode("utf-8").split("\0")[:-1]
    return result, argv


def _carrier(argv: list[str], carrier: str) -> str:
    """The text the harness receives the core through."""
    if carrier == "developer_instructions":
        values = [
            tomllib.loads(arg)["developer_instructions"] for arg in argv if arg.startswith("developer_instructions=")
        ]
        assert len(values) == 1, argv[:12]
        return values[0]
    if carrier == "positional":
        values = [arg for arg in argv if arg.startswith(rules_core.BLOCK_OPEN)]
        assert len(values) == 1
        return values[0]
    assert argv.count(carrier) == 1, f"expected one {carrier} in {argv[:12]}"
    value = argv[argv.index(carrier) + 1]
    if carrier == "--agent-file":
        text = Path(value).read_text(encoding="utf-8")
        assert "${base_prompt}" in text, "the Kimi agent file must keep the default prompt"
        return text
    return value


@pytest.mark.parametrize(
    ("row", "name", "args", "env_kind", "carrier", "seat"), LAUNCHER_ROWS, ids=[row[0] for row in LAUNCHER_ROWS]
)
def test_launcher_row_carries_the_core(row, name, args, env_kind, carrier, seat, tmp_path: Path) -> None:
    result, argv = _launch(name, args, tmp_path, env_kind)
    text = _carrier(argv, carrier)
    _assert_core(text, seat, row)
    assert text.startswith(rules_core.core_block(seat)) or carrier == "--agent-file"
    # stdout names the seat and size, never the 20 KB body
    assert f"launcher: rules core seat={seat} bytes=" in result.stdout
    if carrier != "--agent-file":
        assert f"<rules-core seat={seat} bytes=" in result.stdout.replace("\\", "")
    assert _anchors("core")[0] not in result.stdout


def test_launcher_seat_env_makes_an_interactive_seat_content(tmp_path: Path) -> None:
    _, argv = _launch("start-claude.sh", (), tmp_path, None, {rules_core.SEAT_ENV: "content"})
    _assert_core(_carrier(argv, "--append-system-prompt"), "content", "claude-interactive-content-env")


def test_driver_binding_follows_the_core_in_initial_prompt_harnesses(tmp_path: Path) -> None:
    _, argv = _launch("start-gemini-driver.sh", ("--epic", "infra"), tmp_path, None)
    seed = _carrier(argv, "-i")
    assert seed.startswith(
        rules_core.core_block("core") + "\n\nLoad agents_extensions/shared/skills/drive-epic/SKILL.md"
    )


def test_agy_forwarded_prompt_is_prefixed_not_duplicated(tmp_path: Path) -> None:
    _, argv = _launch("start-gemini.sh", ("--", "-p", "hello"), tmp_path, None)
    assert argv.count("-i") == 0 and argv.count("-p") == 1
    assert argv[argv.index("-p") + 1] == rules_core.core_block("core") + "\n\nhello"


def test_kimi_resume_keeps_its_bound_agent(tmp_path: Path) -> None:
    result, argv = _launch("start-kimi.sh", ("--", "--continue"), tmp_path, None)
    assert "--agent-file" not in argv
    assert "already bind a Kimi agent or resume a session" in result.stderr


def test_launcher_without_the_core_warns_and_still_launches(tmp_path: Path) -> None:
    result, argv = _launch("start-claude.sh", (), tmp_path, None, {rules_core.CORE_DIR_ENV: str(tmp_path / "missing")})
    assert "--append-system-prompt" not in argv
    assert "WARNING: rules core not loaded" in result.stderr


# --------------------------------------------------------------------------- delegate.py workers


def _dispatched_worker_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extra: list[str]) -> tuple[dict, str]:
    from scripts import delegate

    written: list[str] = []

    class _FakeProc:
        pid = 24684

        class stdin:
            write = staticmethod(lambda data: written.append(data.decode() if isinstance(data, bytes) else data))
            close = staticmethod(lambda: None)

    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path))
    task_id = "rules-core-" + hashlib.sha256(" ".join(extra).encode()).hexdigest()[:8]
    args = delegate.build_parser().parse_args(
        ["dispatch", "--agent", "codex", "--task-id", task_id, "--prompt", "the source prompt", *extra]
    )
    args.cwd = str(delegate._REPO_ROOT)
    with monkeypatch.context() as scoped:
        scoped.setattr(delegate.subprocess, "Popen", lambda cmd, **kwargs: _FakeProc())
        assert delegate.cmd_dispatch(args) == 0
    state = delegate._read_state(delegate._state_path(task_id))
    assert state is not None
    return state, "".join(written)


def test_delegate_dispatch_leads_with_the_core(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state, prompt = _dispatched_worker_prompt(tmp_path, monkeypatch, [])
    assert state["prompt_blocks"] == ["rules_core"]
    assert state["effective_prompt_sha256"] == hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    assert prompt == rules_core.core_block("core") + "\n\nthe source prompt"
    _assert_core(prompt, "core", "delegate-dispatch")


def test_delegate_rules_seat_flag_and_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, flagged = _dispatched_worker_prompt(tmp_path, monkeypatch, ["--rules-seat", "content"])
    _assert_core(flagged, "content", "delegate-dispatch-content-flag")
    monkeypatch.setenv(rules_core.SEAT_ENV, "content")
    _, inherited = _dispatched_worker_prompt(tmp_path, monkeypatch, ["--mode", "read-only"])
    _assert_core(inherited, "content", "delegate-dispatch-content-env")


# (row, adapter "module:Class", mode, tool_config) — review dispatches reuse these adapters read-only
WORKER_ROWS = (
    ("codex", "scripts.agent_runtime.adapters.codex:CodexAdapter", "read-only", None),
    ("claude", "scripts.agent_runtime.adapters.claude:ClaudeAdapter", "read-only", None),
    ("agy", "scripts.agent_runtime.adapters.agy:AgyAdapter", "read-only", None),
    ("gemini-legacy", "scripts.agent_runtime.adapters.gemini:GeminiAdapter", "read-only", None),
    ("grok", "scripts.agent_runtime.adapters.grok_build:GrokBuildAdapter", "read-only", None),
    ("cursor", "scripts.agent_runtime.adapters.cursor:CursorAdapter", "read-only", None),
    ("kimi-native", "scripts.agent_runtime.adapters.kimi:KimiAdapter", "workspace-write", None),
    ("kimicc", "scripts.agent_runtime.adapters.kimi:KimiAdapter", "read-only", {"harness": "kimicc"}),
    ("glm", "scripts.agent_runtime.adapters.glm:GlmAdapter", "read-only", None),
    ("deepseek", "scripts.agent_runtime.adapters.deepseek:DeepSeekAdapter", "read-only", None),
    ("hermes-deepseek", "scripts.agent_runtime.adapters.hermes_deepseek:HermesDeepSeekAdapter", "read-only", None),
)


def _json_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in _json_strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in _json_strings(item)]
    return []


def _plan_context(plan) -> str:
    """argv plus stdin, with JSON stdin lines decoded (AGY stream-json)."""
    parts = [*plan.cmd, plan.stdin_payload]
    for line in plan.stdin_payload.splitlines():
        try:
            parts.extend(_json_strings(json.loads(line)))
        except ValueError:
            continue
    return "\n".join(parts)


@pytest.mark.parametrize(("row", "adapter", "mode", "tool_config"), WORKER_ROWS, ids=[row[0] for row in WORKER_ROWS])
def test_worker_row_carries_the_core(
    row, adapter, mode, tool_config, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import importlib

    _, prompt = _dispatched_worker_prompt(tmp_path, monkeypatch, [])
    module, cls = adapter.split(":")
    plan = getattr(importlib.import_module(module), cls)().build_invocation(
        prompt=prompt,
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id="rules-core",
        session_id=None,
        tool_config=tool_config,
    )
    sent = len("\0".join(plan.cmd).encode("utf-8")) + len(plan.stdin_payload.encode("utf-8"))
    _assert_core(_plan_context(plan), "core", f"delegate-worker-{row}", context_bytes=sent)


# --------------------------------------------------------------------------- ACP asks, discussion legs, sealed reviews


def test_acp_inter_agent_call_carries_the_core(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.agent_runtime import runner

    seen: list[str] = []

    class _Captured(Exception):
        pass

    def fake_direct(seat, prompt, **kwargs):
        seen.append(prompt)
        raise _Captured

    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.setattr(runner, "_invoke_direct_only", fake_direct)
    with pytest.raises(_Captured):
        runner.invoke_inter_agent(
            "codex",
            "review this",
            cwd=tmp_path,
            task_id="t-acp",
            correlation_id="c-acp",
            idempotency_key="k-acp",
            source="claude",
        )
    assert seen, "invoke_inter_agent did not reach the transport"
    assert seen[0] == rules_core.core_block("core") + "\n\nreview this"
    _assert_core(seen[0], "core", "acp-inter-agent")


# --------------------------------------------------------------------------- legacy bridge builders


def _msg() -> dict:
    return {"from": "claude", "task_id": "t1", "type": "query", "content": "hello", "data": None}


def _legacy_rows():
    from scripts.ai_agent_bridge import _grok_build, _kimi, _prompts

    return (
        ("bridge-claude", lambda: _prompts.build_claude_prompt(_msg())),
        ("bridge-claude-review", lambda: _prompts.build_claude_prompt(_msg(), review=True, review_branch="b")),
        ("bridge-codex", lambda: _prompts.build_codex_prompt(_msg())),
        ("bridge-agy", lambda: _prompts.build_agy_prompt(_msg())),
        ("bridge-gemini", lambda: _prompts.build_gemini_prompt(_msg(), False, None, False, None)),
        ("bridge-kimi", lambda: _kimi._build_kimi_prompt(_msg())),
        ("bridge-grok-build", lambda: _grok_build._build_grok_build_prompt(_msg())),
    )


@pytest.mark.parametrize("index", range(7))
def test_legacy_bridge_builder_leads_with_the_core(index: int) -> None:
    row, build = _legacy_rows()[index]
    prompt = build()
    assert prompt.startswith(rules_core.core_block("core") + "\n\n"), row
    _assert_core(prompt, "core", row)


def test_legacy_inline_digests_are_kept_alongside_the_core() -> None:
    from scripts.ai_agent_bridge import _prompts

    agy = _prompts.build_agy_prompt(_msg())
    codex = _prompts.build_codex_prompt(_msg())
    assert _prompts.OPERATOR_CONTRACT_DIGEST in agy
    assert _prompts._CODEX_STANDING_RULES in codex
    review = _prompts.build_claude_prompt(_msg(), review=True)
    assert review.index("</rules-core>") < review.index(_prompts.review_protocol_prefix().strip()[:40])


# --------------------------------------------------------------------------- /api/rules scopes


@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient

    import scripts.api.main as api_main

    return TestClient(api_main.app, raise_server_exceptions=False)


def test_legacy_bundle_is_unchanged(api_client) -> None:
    from scripts.api import rules_router

    body = api_client.get("/api/rules?format=json").json()
    assert set(body) >= {"hash", "bytes", "sources", "markdown"}
    assert "scope" not in body
    assert body["sources"] == [rel for rel in rules_router.RULE_SOURCES if (REPO / rel).is_file()]
    assert body["hash"] == hashlib.sha256(body["markdown"].encode("utf-8")).hexdigest()
    plain = api_client.get("/api/rules")
    assert "x-rules-scope" not in plain.headers


@pytest.mark.parametrize("scope", ("core", "content"))
def test_core_scopes_match_the_offline_loader(api_client, scope: str) -> None:
    from scripts.api import rules_router

    body = api_client.get(f"/api/rules?scope={scope}&format=json").json()
    offline = rules_core.core_text(scope)
    assert body["markdown"] == offline
    assert body["sources"] == list(rules_core.seat_sources(scope))
    assert body["scope"] == scope
    assert body["hash"] == rules_router.scope_digest(scope, offline)
    assert body["hash"] != hashlib.sha256(offline.encode("utf-8")).hexdigest()
    markdown = api_client.get(f"/api/rules?scope={scope}")
    assert markdown.text == offline
    assert markdown.headers["x-rules-scope"] == scope
    assert (
        api_client.get(f"/api/rules?scope={scope}", headers={"If-None-Match": f'"{body["hash"]}"'}).status_code == 304
    )
    manifest = api_client.get("/api/state/manifest").json()
    assert manifest[f"rules_{scope}"]["hash"] == body["hash"]


def test_task_scope_serves_its_row_sources(api_client) -> None:
    body = api_client.get("/api/rules?scope=task:cli&format=json").json()
    assert body["sources"] == ["agents_extensions/shared/rules/cli-help-standard.md"]
    assert body["markdown"] == (REPO / body["sources"][0]).read_text(encoding="utf-8").rstrip() + "\n"
    assert api_client.get("/api/rules?scope=task:nope").status_code == 400
    assert api_client.get("/api/rules?scope=everything").status_code == 400


def test_missing_core_scope_is_unavailable_not_empty(api_client, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(rules_core.CORE_DIR_ENV, str(tmp_path / "missing"))
    assert api_client.get("/api/rules?scope=core").status_code == 503
    assert api_client.get("/api/rules").status_code == 200


def test_sdk_caches_each_scope_under_its_own_key(monkeypatch) -> None:
    from scripts.ai_agent_bridge import monitor_client

    calls: list[tuple[str, str, str]] = []

    def fake_cached(self, *, key, manifest_key, manifest, default_url):
        calls.append((key, manifest_key, default_url))

    monkeypatch.setattr(monitor_client.MonitorClient, "_cached_component", fake_cached)
    client = monitor_client.MonitorClient.__new__(monitor_client.MonitorClient)
    client.rules(manifest={})
    client.rules(manifest={}, scope="core")
    client.rules(manifest={}, scope="task:driver")
    assert calls == [
        ("rules", "rules", "/api/rules?format=markdown"),
        ("rules:core", "rules_core", "/api/rules?scope=core&format=markdown"),
        ("rules:task:driver", "", "/api/rules?scope=task:driver&format=markdown"),
    ]


# --------------------------------------------------------------------------- online/offline parity


def test_task_scopes_match_task_scoped_reading_rows() -> None:
    table = (REPO / rules_core.RULES_DIR_REL / "task-scoped-reading.md").read_text(encoding="utf-8")
    rows = [line for line in table.splitlines() if line.startswith("| ") and not line.startswith("| ---")]
    for name, scope in rules_core.TASK_SCOPES.items():
        matches = [line for line in rows if scope.row in line]
        assert len(matches) == 1, f"task:{name} names no single row ({scope.row!r})"
        for rel in scope.sources:
            path = Path(rel)
            token = path.parent.name if path.name == "SKILL.md" else path.name
            assert token in matches[0], f"task:{name}: {rel} is not selected by its row"
            assert (REPO / rel).is_file(), rel
        assert f"`{name}`" in table


def test_offline_list_names_every_scope_and_source() -> None:
    offline = (REPO / rules_core.RULES_DIR_REL / "_load-via-api.md").read_text(encoding="utf-8")
    for seat in rules_core.SEATS:
        assert f"scope={seat} " in offline
        for rel in rules_core.seat_sources(seat):
            assert rel in offline
    for name, scope in rules_core.TASK_SCOPES.items():
        assert f"scope=task:{name} " in offline
        for rel in scope.sources:
            assert rel in offline
