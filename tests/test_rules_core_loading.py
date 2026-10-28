"""Every seat loads the rules core: one deterministic test per loading-matrix row.

Each row builds the context that seat would actually receive — a launcher's exact
dry-run argv (``LAUNCHER_DRY_RUN_ARGV_FILE``), a ``delegate.py`` worker prompt handed
to each adapter's ``build_invocation``, an ACP call through ``invoke_inter_agent``,
a legacy bridge prompt — and asserts that the core's first and last pillar anchors
are in it. Bytes carried per row are printed (``pytest -s``).

The core is ``agents_extensions/shared/rules/core.md`` when this checkout has it;
otherwise ``tests/fixtures/rules_core/`` stands in: in-process through the loader's
``core_dir`` resolver, and for launcher and CLI subprocesses through a checkout view
(``tests/rules_core_view.py``) whose rules directory holds the fixture. Nothing in the
environment can move the core.

A missing core refuses: each entry point (launcher, ``delegate.py`` dispatch, ACP call and
discussion, bridge builder, ``ask-*`` prompt, ``/api/rules`` scope) is exercised without the
core and must refuse, naming the path, before its first side effect.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from scripts.lib import rules_core
from tests.rules_core_view import absent_checkout, checkout_view
from tests.test_launcher_contract import REPO, hermes_stub_env

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

REAL_CORE_DIR = REPO / rules_core.RULES_DIR_REL
FIXTURE_CORE_DIR = REPO / "tests" / "fixtures" / "rules_core"
CORE_DIR = (
    REAL_CORE_DIR
    if (REAL_CORE_DIR / "core.md").is_file() and (REAL_CORE_DIR / "core-curriculum.md").is_file()
    else FIXTURE_CORE_DIR
)
CHECKOUT_CORE_DIR = rules_core.core_dir
OLD_OVERRIDE_ENV = "LU_RULES_CORE_DIR"


@pytest.fixture(autouse=True)
def _core_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """In-process code reads CORE_DIR (the fixture stands in for a checkout without the core)."""
    if CORE_DIR != REAL_CORE_DIR:
        monkeypatch.setattr(rules_core, "core_dir", lambda root=None: CORE_DIR)


@pytest.fixture(scope="module")
def core_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The checkout launchers and the CLI run from: this one, or a view carrying the fixture."""
    if CORE_DIR == REAL_CORE_DIR:
        return REPO
    return checkout_view(tmp_path_factory.mktemp("rules-core-present") / "checkout", FIXTURE_CORE_DIR)


@pytest.fixture
def absent_root(request: pytest.FixtureRequest) -> Path:
    """The checkout view without the rules core (shared with ``rules_core_absent`` tests)."""
    return absent_checkout(request)


@pytest.fixture
def missing_core(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """In-process loader reads a rules directory that holds no core."""
    empty = tmp_path / "no-core"
    empty.mkdir()
    monkeypatch.setattr(rules_core, "core_dir", lambda root=None: empty)
    return empty


@pytest.fixture
def core_without_addendum(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """In-process loader reads ``core.md`` but no ``core-curriculum.md``."""
    partial = tmp_path / "core-only"
    partial.mkdir()
    (partial / "core.md").write_text((CORE_DIR / "core.md").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(rules_core, "core_dir", lambda root=None: partial)
    return partial


def _hostile_core_dir(tmp_path: Path) -> Path:
    hostile = tmp_path / "hostile"
    hostile.mkdir()
    for name in ("core.md", "core-curriculum.md"):
        (hostile / name).write_text("## P1 — HOSTILE REPLACEMENT\n", encoding="utf-8")
    return hostile


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
    # #10959: the framed content-seat block measures 41201 bytes.
    ceiling = 42_000 if seat == "content" else 40_960
    assert len(block.encode("utf-8")) <= ceiling, f"{row}: binding {seat} block exceeds {ceiling} bytes"
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


def test_block_frames_the_text_with_its_digest() -> None:
    text = rules_core.core_text("content")
    block = rules_core.core_block("content")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert block == f'<rules-core seat="content" sha256="{digest}">\n{text}</rules-core>'
    assert text.startswith((CORE_DIR / "core.md").read_text(encoding="utf-8").rstrip())


def test_with_core_prepends_once() -> None:
    once = rules_core.with_core("task")
    assert once == rules_core.core_block("core") + "\n\ntask"
    assert rules_core.with_core(once) == once
    assert rules_core.require_core() == "core"
    assert rules_core.require_core("content") == "content"


def test_a_missing_core_refuses_every_loader_entry(missing_core: Path, capsys) -> None:
    for call in (
        lambda: rules_core.with_core("task"),
        lambda: rules_core.core_block("core"),
        lambda: rules_core.core_text("content"),
        lambda: rules_core.require_core(),
        lambda: rules_core.require_core("content"),
    ):
        with pytest.raises(rules_core.RulesCoreMissing, match=r"agents_extensions/shared/rules/core\.md"):
            call()
    assert "continuing without" not in capsys.readouterr().err


@pytest.mark.parametrize("damage", ["empty", "blank", "directory"])
def test_an_empty_or_unreadable_core_is_missing(damage: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    broken = tmp_path / "broken"
    broken.mkdir()
    if damage == "directory":
        (broken / "core.md").mkdir()
    else:
        (broken / "core.md").write_text("" if damage == "empty" else " \n\t\n", encoding="utf-8")
    monkeypatch.setattr(rules_core, "core_dir", lambda root=None: broken)
    with pytest.raises(rules_core.RulesCoreMissing, match=r"core\.md"):
        rules_core.with_core("task")


def test_a_content_seat_also_needs_the_curriculum_addendum(core_without_addendum: Path) -> None:
    assert rules_core.with_core("task").startswith(rules_core.BLOCK_OPEN)
    assert rules_core.require_core("core") == "core"
    for call in (lambda: rules_core.require_core("content"), lambda: rules_core.with_core("task", "content")):
        with pytest.raises(rules_core.RulesCoreMissing, match=r"core-curriculum\.md"):
            call()


def test_a_core_quoted_in_an_attachment_does_not_replace_the_preamble() -> None:
    block = rules_core.core_block("core")
    attached = f"Review the attached file.\n\n```markdown\n{block}\n```\n"
    assert rules_core.with_core(attached) == f"{block}\n\n{attached}"


def test_the_old_env_override_has_no_effect(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, core_root: Path) -> None:
    monkeypatch.setenv(OLD_OVERRIDE_ENV, str(_hostile_core_dir(tmp_path)))
    monkeypatch.chdir(tmp_path)
    assert CHECKOUT_CORE_DIR() == REPO / rules_core.RULES_DIR_REL
    assert CHECKOUT_CORE_DIR(core_root) == core_root / rules_core.RULES_DIR_REL
    monkeypatch.setattr(rules_core, "core_dir", CHECKOUT_CORE_DIR)
    text = rules_core.core_text("content", core_root)
    assert "HOSTILE" not in text
    assert text.startswith((CORE_DIR / "core.md").read_text(encoding="utf-8").rstrip())
    script = REPO / "scripts" / "lib" / "rules_core.py"
    cli = subprocess.run(
        [sys.executable, os.fspath(script), "--root", os.fspath(core_root), "--format", "text"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert cli.returncode == 0, cli.stderr
    assert cli.stdout == rules_core.core_text("core", core_root)


def test_toml_and_kimi_forms_round_trip() -> None:
    block = rules_core.core_block("core")
    assert tomllib.loads("v=" + rules_core.toml_basic_string(block + '\t"\\\x01'))["v"] == block + '\t"\\\x01'
    agent_file = rules_core.kimi_agent_file_text(block)
    assert agent_file.startswith("---\nname: rules-core\n")
    assert "${base_prompt}\n\n" + block in agent_file
    with pytest.raises(rules_core.RulesCoreError):
        rules_core.kimi_agent_file_text("x ${injected} y")


def test_cli_reports_anchors_and_exits_3_when_missing(core_root: Path, absent_root: Path) -> None:
    script = core_root / "scripts" / "lib" / "rules_core.py"
    ok = subprocess.run(
        [sys.executable, os.fspath(script), "--root", os.fspath(core_root), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ok.returncode == 0, ok.stderr
    payload = json.loads(ok.stdout)
    assert (payload["first_anchor"], payload["last_anchor"]) == _anchors("core")
    absent = absent_root
    missing = subprocess.run(
        [sys.executable, os.fspath(absent / "scripts" / "lib" / "rules_core.py"), "--root", os.fspath(absent)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert missing.returncode == 3
    assert "rules source unavailable: agents_extensions/shared/rules/core.md" in missing.stderr


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
    ("glm-opencode", "start-glm.sh", (), None, "positional", "core"),
    ("glmcc", "start-glmcc.sh", (), "glm", "--append-system-prompt", "core"),
)


def _launch(
    root: Path,
    name: str,
    args: tuple[str, ...],
    tmp_path: Path,
    env_kind: str | None,
    extra_env: dict[str, str] | None = None,
    *,
    expect_launch: bool = True,
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
        [str(root / name), *args], cwd=root, env=env, text=True, capture_output=True, check=False, timeout=120
    )
    if not expect_launch:
        assert not argv_file.exists(), "a refused launch must not reach exec"
        return result, []
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
def test_launcher_row_carries_the_core(row, name, args, env_kind, carrier, seat, tmp_path: Path, core_root) -> None:
    if row in {"glm-opencode", "glmcc"}:
        result, argv = _launch(core_root, name, args, tmp_path, env_kind, expect_launch=False)
        assert result.returncode == 2 and "is retired in the model catalog" in result.stderr
        assert argv == []
        return
    result, argv = _launch(core_root, name, args, tmp_path, env_kind)
    text = _carrier(argv, carrier)
    _assert_core(text, seat, row)
    assert text.startswith(rules_core.core_block(seat)) or carrier == "--agent-file"
    # stdout names the seat and size, never the 20 KB body
    assert f"launcher: rules core seat={seat} bytes=" in result.stdout
    if carrier != "--agent-file":
        assert f"<rules-core seat={seat} bytes=" in result.stdout.replace("\\", "")
    assert _anchors("core")[0] not in result.stdout


def test_launcher_seat_env_makes_an_interactive_seat_content(tmp_path: Path, core_root: Path) -> None:
    _, argv = _launch(core_root, "start-claude.sh", (), tmp_path, None, {rules_core.SEAT_ENV: "content"})
    _assert_core(_carrier(argv, "--append-system-prompt"), "content", "claude-interactive-content-env")


def test_gemini_driver_core_leads_the_drive_epic_binding(tmp_path: Path, core_root: Path) -> None:
    _, argv = _launch(core_root, "start-gemini-driver.sh", ("--epic", "infra"), tmp_path, None)
    assert argv[:3] == ["agy", "--model", "gemini-3.8-flash-high"]
    assert argv.count("-i") == 1
    prompt = argv[argv.index("-i") + 1]
    assert prompt.startswith(rules_core.core_block("core") + "\n\n")
    assert "agents_extensions/shared/skills/drive-epic/SKILL.md" in prompt


def test_agy_forwarded_prompt_is_prefixed_not_duplicated(tmp_path: Path, core_root: Path) -> None:
    _, argv = _launch(core_root, "start-gemini.sh", ("--", "-p", "hello"), tmp_path, None)
    assert argv.count("-i") == 0 and argv.count("-p") == 1
    assert argv[argv.index("-p") + 1] == rules_core.core_block("core") + "\n\nhello"


_KIMI_REFUSED = (
    ("--continue",),
    ("-c",),
    ("-C",),
    ("-yc",),
    ("-cy",),
    ("--session",),
    ("--session=abc",),
    ("-S",),
    ("-S", "abc"),
    ("-Sabc",),
    ("-ySabc",),
    ("--resume",),
    ("--resume=abc",),
    ("-r",),
    ("-rabc",),
    ("--agent", "okabe"),
    ("--agent=okabe",),
    ("--agent-file", "/tmp/custom.md"),
    ("--agent-file=/tmp/custom.md",),
    ("--model", "k2.7"),
    ("-m", "k2.7"),
    ("--unknown-flag",),
    ("-Z",),
    ("session",),
    ("fork", "abc"),
    ("--",),
    ("-",),
    ("--yolo", "--prompt"),
    ("-p",),
    ("-p", "--continue"),
    ("--prompt", "-S"),
    ("-p-c",),
)


@pytest.mark.parametrize("forwarded", _KIMI_REFUSED, ids=lambda forwarded: " ".join(forwarded))
def test_kimi_code_admits_only_fresh_session_flags(forwarded, tmp_path: Path, core_root: Path) -> None:
    """OO-58: the retired default refuses before the fresh-session classifier, and nothing execs."""
    result, _ = _launch(core_root, "start-kimi.sh", ("--", *forwarded), tmp_path, None, expect_launch=False)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "is retired in the model catalog" in result.stderr


@pytest.mark.parametrize(
    "forwarded",
    (
        (),
        ("--yolo",),
        ("-y",),
        ("--auto",),
        ("--plan",),
        ("-yp", "hello"),
        ("-phello",),
        ("--prompt=hello",),
        ("--prompt", "hello", "--output-format", "text"),
        ("--output-format=stream-json", "--yolo"),
        ("--skills-dir", "/tmp/skills", "--add-dir=/tmp/extra", "--add-dir", "/tmp/more"),
    ),
    ids=lambda forwarded: " ".join(forwarded) or "plain",
)
def test_kimi_code_fresh_launch_carries_the_core(forwarded, tmp_path: Path, core_root: Path) -> None:
    """OO-58: a fresh Kimi launch is refused before argv, so the core is never attached to a command."""
    result, _ = _launch(
        core_root,
        "start-kimi.sh",
        ("--", *forwarded) if forwarded else (),
        tmp_path,
        None,
        expect_launch=False,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "is retired in the model catalog" in result.stderr


def test_kimi_on_claude_code_keeps_the_core_when_resuming(tmp_path: Path, core_root: Path) -> None:
    """OO-58: kimicc resume is refused with the retired default before a core-bearing argv exists."""
    result, _ = _launch(
        core_root, "start-kimicc.sh", ("--", "--continue"), tmp_path, "kimi", expect_launch=False
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "is retired in the model catalog" in result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.parametrize(
    ("row", "name", "args", "env_kind", "carrier", "seat"), LAUNCHER_ROWS, ids=[row[0] for row in LAUNCHER_ROWS]
)
def test_launcher_without_the_core_refuses_before_any_side_effect(
    row, name, args, env_kind, carrier, seat, tmp_path: Path, absent_root: Path
) -> None:
    result, _ = _launch(absent_root, name, args, tmp_path, env_kind, expect_launch=False)
    if row in {"glm-opencode", "glmcc"}:
        assert result.returncode == 2 and "is retired in the model catalog" in result.stderr
        assert "would exec" not in result.stdout
        assert "would deploy agent extensions" not in result.stdout
        return
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert "refusing to launch" in result.stderr
    assert "agents_extensions/shared/rules/core.md" in result.stderr
    assert "would deploy agent extensions" not in result.stdout, "the refusal must precede the deploy step"
    assert "would exec" not in result.stdout


@pytest.fixture(scope="module")
def addendum_less_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A checkout view carrying ``core.md`` but not ``core-curriculum.md``."""
    core_only = tmp_path_factory.mktemp("rules-core-partial") / "rules"
    core_only.mkdir()
    (core_only / "core.md").write_text((CORE_DIR / "core.md").read_text(encoding="utf-8"), encoding="utf-8")
    return checkout_view(core_only.parent / "checkout", core_only)


def test_content_seat_launcher_needs_the_addendum_but_a_core_seat_does_not(
    tmp_path: Path, addendum_less_root: Path
) -> None:
    refused, _ = _launch(
        addendum_less_root,
        "start-claude-driver.sh",
        ("--epic", "curriculum-upgrade"),
        tmp_path,
        None,
        expect_launch=False,
    )
    assert refused.returncode == 1, refused.stderr
    assert "core-curriculum.md" in refused.stderr
    _, argv = _launch(addendum_less_root, "start-claude-driver.sh", ("--epic", "infra"), tmp_path, None)
    assert _carrier(argv, "--append-system-prompt") == rules_core.core_block("core")


# --------------------------------------------------------------------------- delegate.py workers


# (row, adapter "module:Class", mode, tool_config) — review dispatches reuse these adapters read-only
# (Kimi rows are workspace-write: the coding-only gate admits nothing else)


# Every CLI a WORKER_ROWS adapter resolves at plan time; stubs keep the rows host-independent.


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


def test_acp_inter_agent_call_without_the_core_is_a_typed_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing_core: Path
) -> None:
    from scripts.agent_runtime import runner

    def _spawn(*_a, **_k):
        raise AssertionError("an ACP call without the rules core must not reach the transport")

    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.setattr(runner, "_invoke_direct_only", _spawn)
    with pytest.raises(runner.InterAgentTransportError, match=r"agents_extensions/shared/rules/core\.md"):
        runner.invoke_inter_agent(
            "codex",
            "review this",
            cwd=tmp_path,
            task_id="t-acp",
            correlation_id="c-acp",
            idempotency_key="k-acp",
            source="claude",
        )


def test_acp_discussion_without_the_core_refuses_before_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing_core: Path
) -> None:
    from scripts.agent_runtime import acpx_discuss

    def _leg(*_a, **_k):
        raise AssertionError("a discussion without the rules core must not call a participant")

    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.setattr(acpx_discuss, "classify_repo_path", lambda *_a, **_k: "dispatch_worktree")
    controller = acpx_discuss.AcpxDiscussionController(
        root=tmp_path / "plane", participant_call=_leg, synthesis_call=_leg
    )
    try:
        with pytest.raises(acpx_discuss.AcpxDiscussionError, match=r"core\.md"):
            controller.run(
                prompt="Solve the bounded fixture.",
                cwd=Path.cwd(),
                task_id="task-core",
                correlation_id="corr-core",
                idempotency_key="idem-core",
            )
        count = controller.conn.execute("SELECT COUNT(*) FROM acp_conversation_events").fetchone()[0]
    finally:
        controller.close()
    assert count == 0, "a refused discussion admits no conversation"


# --------------------------------------------------------------------------- legacy bridge builders


def _msg() -> dict:
    return {"from": "claude", "task_id": "t1", "type": "query", "content": "hello", "data": None}


def _legacy_rows():
    from scripts.ai_agent_bridge import _grok_build, _prompts

    return (
        ("bridge-claude", lambda: _prompts.build_claude_prompt(_msg())),
        ("bridge-claude-review", lambda: _prompts.build_claude_prompt(_msg(), review=True, review_branch="b")),
        ("bridge-codex", lambda: _prompts.build_codex_prompt(_msg())),
        ("bridge-agy", lambda: _prompts.build_agy_prompt(_msg())),
        ("bridge-gemini", lambda: _prompts.build_gemini_prompt(_msg(), False, None, False, None)),
        ("bridge-grok-build", lambda: _grok_build._build_grok_build_prompt(_msg())),
    )


@pytest.mark.parametrize("index", range(6))
def test_legacy_bridge_builder_leads_with_the_core(index: int) -> None:
    row, build = _legacy_rows()[index]
    prompt = build()
    assert prompt.startswith(rules_core.core_block("core") + "\n\n"), row
    _assert_core(prompt, "core", row)


@pytest.mark.parametrize("index", range(6))
def test_legacy_bridge_builder_without_the_core_refuses(index: int, missing_core: Path) -> None:
    _, build = _legacy_rows()[index]
    with pytest.raises(SystemExit, match=r"bridge: refused: .*core\.md"):
        build()


def test_ask_transports_without_the_core_refuse_before_spawning(
    monkeypatch: pytest.MonkeyPatch, missing_core: Path
) -> None:
    from scripts.ai_agent_bridge import _cursor, _hermes, _opencode

    def _spawn(*_a, **_k):
        raise AssertionError("an ask without the rules core must not spawn a process")

    monkeypatch.setattr(_hermes, "_run_hermes_subprocess", _spawn)
    for module in (_cursor, _opencode):
        monkeypatch.setattr(module.subprocess, "run", _spawn)
    # Binary lookup is the shared resolver on the bridge module.
    monkeypatch.setattr(_cursor, "resolve_cursor_agent_binary", lambda: "/stub/cursor-agent")
    monkeypatch.setattr(_opencode.shutil, "which", lambda name: f"/stub/{name}")
    with pytest.raises(SystemExit, match=r"ask-cursor: refused: .*core\.md"):
        _cursor._invoke_cursor("hello", "grok-4.7-high")
    with pytest.raises(SystemExit, match=r"ask-hermes: refused: .*core\.md"):
        _hermes._invoke_hermes("hello", "deepseek-v4.1-flash")
    with pytest.raises(SystemExit, match=r"ask-opencode: refused: .*core\.md"):
        _opencode._run_opencode("hello", "deepseek/deepseek-v4.1-flash")


# --------------------------------------------------------------------------- public entries, before any write

# Everything a public ask or discussion entry could write or start: a spy on each
# records the call instead of doing it, so a refusal must leave every list empty.
_ASK_SIDE_EFFECTS = (
    "send_message",
    "register_ask",
    "launch_background_ask",
    "_send_gemini_message",
    "process_and_respond",
)


def _spy_side_effects(monkeypatch: pytest.MonkeyPatch, modules, names) -> list[str]:
    calls: list[str] = []
    for module in modules:
        for name in names:
            if hasattr(module, name):
                monkeypatch.setattr(module, name, lambda *_a, _n=name, **_k: calls.append(_n))
    return calls


def _bridge_asks():
    # No ask-kimi: Kimi is not a bridge recipient and is refused before any rules-core step.
    from scripts.ai_agent_bridge import _agy, _claude, _codex, _cursor, _gemini, _grok_build, _hermes, _opencode

    return (
        ("ask-cursor", _cursor, "ask_cursor"),
        ("ask-hermes", _hermes, "ask_hermes"),
        ("ask-opencode", _opencode, "ask_opencode"),
        ("ask-pool", _opencode, "ask_pool"),
        ("ask-glm", _opencode, "ask_glm"),
        ("ask-gemma", _opencode, "ask_gemma"),
        ("ask-claude", _claude, "ask_claude"),
        ("ask-codex", _codex, "ask_codex"),
        ("ask-agy", _agy, "ask_agy"),
        ("ask-grok", _grok_build, "ask_grok_build"),
        ("ask-gemini", _gemini, "ask_gemini"),
    )


@pytest.mark.parametrize("background", [False, True], ids=["foreground", "background"])
@pytest.mark.parametrize("index", range(11))
def test_bridge_ask_without_the_core_refuses_before_any_send(
    index: int, background: bool, monkeypatch: pytest.MonkeyPatch, missing_core: Path
) -> None:
    from scripts.ai_agent_bridge import _ask_lifecycle, _messaging

    who, module, name = _bridge_asks()[index]
    calls = _spy_side_effects(monkeypatch, (module, _messaging, _ask_lifecycle), _ASK_SIDE_EFFECTS)
    mode = {"async_mode": background} if name == "ask_gemini" else {"background": background}
    with pytest.raises(SystemExit, match=rf"{who}: refused: .*core\.md"):
        getattr(module, name)("hello", "t-core", **mode)
    assert calls == [], f"{who} wrote before refusing: {calls}"


def test_acp_ask_without_the_core_refuses_before_forward_or_enqueue(
    monkeypatch: pytest.MonkeyPatch, missing_core: Path
) -> None:
    from agent_runtime.runner import InterAgentTransportError
    from scripts.ai_agent_bridge import _acp_compat, _job_host_forward
    from scripts.fleet_comms import authority
    from scripts.telemetry import legacy_bridge

    calls = _spy_side_effects(
        monkeypatch,
        (legacy_bridge, _job_host_forward, authority),
        ("start_bridge_invocation_safely", "maybe_forward_compat_ask", "AuthorityService"),
    )
    with pytest.raises(InterAgentTransportError, match=r"ask-codex refused: .*core\.md"):
        _acp_compat.run_compat_ask("codex", "hello", task_id="t-core", source="claude")
    assert calls == [], f"the ACP ask wrote before refusing: {calls}"


@pytest.mark.parametrize("review", [False, True], ids=["ask", "review"])
def test_ask_cli_without_the_core_refuses_before_dispatch(
    review: bool, monkeypatch: pytest.MonkeyPatch, missing_core: Path
) -> None:
    import argparse

    from scripts.ai_agent_bridge import _acp_compat, _cli

    calls = _spy_side_effects(
        monkeypatch,
        (_cli, _acp_compat),
        ("_resolve_same_repo_pr_head", "_dispatch_headless_review", "run_compat_ask"),
    )
    args = argparse.Namespace(
        content="hello", task_id="t-core", review=review, type="review" if review else "query", pr=None, branch=None
    )
    with pytest.raises(SystemExit, match=r"ask-cursor: refused: .*core\.md"):
        _cli._handle_acp_compat(args, "cursor")
    assert calls == [], f"ask-cursor dispatched before refusing: {calls}"


def test_discuss_cli_without_the_core_refuses_before_any_channel_write(
    monkeypatch: pytest.MonkeyPatch, missing_core: Path, capsys
) -> None:
    import argparse

    from scripts.ai_agent_bridge import _channels_cli
    from scripts.fleet_comms import authority

    calls = _spy_side_effects(monkeypatch, (authority,), ("AuthorityService",))
    monkeypatch.setenv("LU_AGENT_COMM_TRANSPORT", "acp")
    args = argparse.Namespace(
        channel="core-check",
        with_agents="codex,claude",
        body="Solve the bounded fixture.",
        max_rounds=1,
        models=None,
        efforts=None,
        review=False,
        review_profile=None,
        idempotency_key=None,
    )
    assert _channels_cli._handle_discuss(args) == 1
    assert calls == [], f"the discussion wrote before refusing: {calls}"
    assert re.search(r"discussion refused: .*core\.md", capsys.readouterr().err)


# --------------------------------------------------------------------------- /api/rules scopes


@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient

    import scripts.api.main as api_main

    return TestClient(api_main.app, raise_server_exceptions=False)


def test_default_binding_bundle_is_the_bounded_core(api_client) -> None:
    body = api_client.get("/api/rules?format=json").json()
    assert body == api_client.get("/api/rules?scope=core&format=json").json()
    assert body["scope"] == "core"
    assert body["sources"] == [rules_core.CORE_REL]
    assert body["markdown"] == rules_core.core_text()
    assert body["bytes"] == len(body["markdown"].encode("utf-8")) <= 40_960
    plain = api_client.get("/api/rules")
    assert plain.text == body["markdown"]
    assert plain.headers["x-rules-scope"] == "core"
    assert api_client.get("/api/rules", headers={"If-None-Match": plain.headers["etag"]}).status_code == 304


def test_full_reference_is_preserved_only_by_explicit_scope(api_client) -> None:
    from scripts.api import rules_router

    body = api_client.get("/api/rules?scope=full&format=json").json()
    assert set(body) >= {"hash", "bytes", "sources", "markdown"}
    assert body["scope"] == "full"
    assert body["sources"] == [rel for rel in rules_router.RULE_SOURCES if (REPO / rel).is_file()]
    expected, sources, digest = rules_router._assemble_rules(REPO)
    assert (body["markdown"], body["sources"], body["hash"]) == (expected, sources, digest)
    assert body["hash"] == hashlib.sha256(body["markdown"].encode("utf-8")).hexdigest()
    assert body["bytes"] == len(expected.encode("utf-8"))
    plain = api_client.get("/api/rules?scope=full")
    assert plain.headers["x-rules-scope"] == "full"
    assert plain.text == expected
    assert rules_router.rules_hash(project_root=REPO, scope="full") == digest
    assert api_client.get("/api/rules?scope=full", headers={"If-None-Match": plain.headers["etag"]}).status_code == 304
    assert api_client.get("/api/rules", headers={"If-None-Match": plain.headers["etag"]}).status_code == 200


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
    monkeypatch.setattr(rules_core, "core_dir", lambda root=None: tmp_path / "missing")
    for scope in ("core", "content"):
        response = api_client.get(f"/api/rules?scope={scope}")
        assert response.status_code == 503
        assert "agents_extensions/shared/rules/core.md" in response.json()["detail"]
    assert api_client.get("/api/rules").status_code == 503
    assert api_client.get("/api/rules?scope=full").status_code == 200


def test_content_scope_without_the_addendum_is_unavailable(api_client, core_without_addendum: Path) -> None:
    assert api_client.get("/api/rules?scope=core").status_code == 200
    response = api_client.get("/api/rules?scope=content")
    assert response.status_code == 503
    assert "core-curriculum.md" in response.json()["detail"]


# --------------------------------------------------------------------------- online/offline parity
