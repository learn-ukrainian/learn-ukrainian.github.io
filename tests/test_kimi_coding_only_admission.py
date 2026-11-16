"""Kimi is retired: every product entry point refuses a Kimi seat or model with the retired-seat error.

The refusal itself lives in the installed release
(``lu_machinery.agent_runtime.retired_seat_admission``). These tests pin that
the product's runner, ACP, bridge and fleet-comms entry points still reach it
before any side effect, that stored Kimi rows are left as they are, and that
other seats pass the same gate unchanged.
"""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import subprocess
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lu_machinery.agent_runtime import retired_seat_admission

from scripts.fleet_comms.endpoints import load_endpoint_registry
from scripts.fleet_comms.request_executor import RequestExecutor

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOKEN = "Kimi is retired"


_REAL_RUN = subprocess.run
_REAL_POPEN = subprocess.Popen
# Read-only git plumbing an admission gate may run; the retired-seat gate runs none.
_GATE_GIT = frozenset({"rev-parse", "ls-tree", "cat-file"})


def _fail(*_args, **_kwargs):
    raise AssertionError("a refused Kimi call reached a side effect")


def _run(cmd, **kwargs) -> subprocess.CompletedProcess:
    """``subprocess.run`` itself, even while a test has replaced ``run`` and ``Popen`` with a failure."""
    patched = subprocess.Popen
    subprocess.Popen = _REAL_POPEN
    try:
        return _REAL_RUN(cmd, **kwargs)
    finally:
        subprocess.Popen = patched


def _refusal(participants=("kimi",), models=(), **overrides) -> str | None:
    """The product gate's refusal (``target_admission.refuse_disallowed_targets``), or None when admitted."""
    from scripts.agent_runtime.target_admission import refuse_disallowed_targets

    kwargs = {"mode": "workspace-write", "repo": "public-monorepo"}
    kwargs.update(overrides)
    try:
        refuse_disallowed_targets(participants, models, **kwargs)
    except retired_seat_admission.KimiAdmissionRefused as exc:
        return str(exc)
    return None


# --- the gate ------------------------------------------------------------------------


@pytest.mark.parametrize("agent", ["claude", "codex", "grok", "agy", "cursor"])
def test_other_seats_are_untouched(agent):
    assert _refusal(participants=(agent,), mode="read-only", review=True, paths=("docs/x.md",)) is None
    assert _refusal(participants=(agent,), models=("gpt-6-sol",), mode=retired_seat_admission.ACP_MODE) is None


def test_an_effective_kimi_model_on_any_seat_is_gated():
    message = _refusal(participants=("claude", "codex"), models=(None, "kimi-code/k3"), mode=retired_seat_admission.ACP_MODE)
    assert message and _TOKEN in message


# --- runtime boundary ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "tool_config"),
    [
        ("read-only", None),
        ("danger", None),
        ("read-only", {"harness": "kimicc", "trail_isolation": True}),
        ("workspace-write", {"review_id": "rev-1"}),
    ],
)
def test_runner_invoke_refuses_before_attribution_or_trail_provisioning(tmp_path, monkeypatch, mode, tool_config):
    from scripts.agent_runtime import runner

    monkeypatch.setattr(runner, "resolve_invocation_attribution", _fail)
    monkeypatch.setattr(runner, "prepare_trail_isolation", _fail)
    monkeypatch.setattr(runner, "_invoke_impl", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        runner.invoke("kimi", "Review this.", mode=mode, cwd=tmp_path, tool_config=tool_config)


def test_inter_agent_route_refuses_a_kimi_model_override():
    from scripts.agent_runtime import runner

    for participant, model in (("kimi", None), ("kimicc", None), ("claude", "kimi-code/k3")):
        with pytest.raises(runner.InterAgentTransportError, match=_TOKEN):
            runner.resolve_inter_agent_route(participant, model=model)


def test_no_non_kimi_acp_participant_pins_a_kimi_model():
    from scripts.agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    for name, route in ACPX_SUPPORTED_PARTICIPANTS.items():
        if retired_seat_admission.is_kimi_model(route.get("model")):
            assert retired_seat_admission.is_kimi_seat(name), name


def test_trail_isolation_refuses_kimi():
    from scripts.agent_runtime.trail_isolation import TrailIsolationError, prepare_trail_isolation

    with pytest.raises(TrailIsolationError, match=_TOKEN):
        prepare_trail_isolation(
            agent_name="kimi", mode="read-only", tool_config={"trail_isolation": True, "harness": "kimicc"}
        )


# --- ACP, bridge and fleet-comms entry points ------------------------------------------


def test_compat_ask_refuses_before_telemetry(monkeypatch):
    from lu_machinery.telemetry import legacy_bridge

    from scripts.ai_agent_bridge import _acp_compat

    monkeypatch.setattr(legacy_bridge, "start_bridge_invocation_safely", _fail)
    monkeypatch.setattr(_acp_compat, "_run_compat_ask_impl", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat.run_compat_ask("kimi", "Consult on this design.", task_id="kimi-consult")
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat.run_compat_ask("claude", "Consult.", task_id="kimi-model", model="kimi-code/k3")


def test_compat_ask_impl_refuses_before_the_job_host_forward(monkeypatch):
    from scripts.ai_agent_bridge import _acp_compat, _job_host_forward

    monkeypatch.setattr(_job_host_forward, "maybe_forward_compat_ask", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat._run_compat_ask_impl("kimi", "Consult.", task_id="kimi-forward")


def test_a_kimi_quota_substitute_is_refused_before_its_job_is_enqueued(monkeypatch, tmp_path):
    from scripts.ai_agent_bridge import _acp_compat
    from scripts.fleet_comms import authority

    config = tmp_path / "agent_fallback_substitutions.yaml"
    config.write_text("dispatch_fallbacks:\n  codex: kimi\n", encoding="utf-8")
    monkeypatch.setattr(_acp_compat, "_FALLBACK_SUBS_PATH", config)
    monkeypatch.setattr(authority, "AuthorityService", _fail)
    # The substitute is resolved and admitted in one step: a Kimi substitute never becomes a target.
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat._resolve_quota_substitution("codex", "rate_limited", already_substituted=False)
    # The job sink takes only an admitted target; a raw seat name is refused before the authority.
    with pytest.raises(TypeError, match="AdmittedTarget"):
        _acp_compat._run_single_acp_job(
            "kimi", "Consult.", task_id="t", source=None, effort=None, review=False, hard_timeout=60
        )


@pytest.mark.parametrize("extra", [[], ["--pr", "9158"], ["--review"]])
def test_ask_kimi_cli_refuses_before_pr_resolution_or_dispatch(monkeypatch, extra):
    from scripts.ai_agent_bridge import _acp_compat, _cli, _dispatch_wrappers

    monkeypatch.setattr(_cli, "_resolve_same_repo_pr_head", _fail)
    monkeypatch.setattr(_acp_compat, "run_compat_ask", _fail)
    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", _fail)
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(read=_fail))
    args = _cli._build_parser().parse_args(["ask-kimi", "-", "--task-id", "kimi-cli", *extra])
    with pytest.raises(SystemExit, match=_TOKEN):
        _cli._handle_ask_kimi(args)


def test_ask_review_dispatch_refuses_before_the_temporary_prompt(monkeypatch):
    from scripts.ai_agent_bridge import _dispatch_wrappers

    monkeypatch.setattr(_dispatch_wrappers, "_prompt_directory", _fail)
    monkeypatch.setattr(_dispatch_wrappers.subprocess, "run", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _dispatch_wrappers.run_ask_review_dispatch("kimi", "Review PR #1.", task_id="kimi-review")
    with pytest.raises(ValueError, match=_TOKEN):
        _dispatch_wrappers.run_ask_review_dispatch("claude", "Review PR #1.", task_id="r", model="kimi-code/k3")


def test_ask_review_dispatch_command_never_selects_a_kimi_harness(tmp_path):
    from lu_machinery.agent_runtime.retired_seat_admission import REVIEW_MODE

    from scripts.agent_runtime.target_admission import resolve_and_admit
    from scripts.ai_agent_bridge import _dispatch_wrappers

    (target,) = resolve_and_admit(("claude",), mode=REVIEW_MODE, review=True)
    cmd = _dispatch_wrappers.build_ask_review_dispatch_command(target, "t", tmp_path / "p.md", effort=None)
    assert "--harness" not in cmd


def test_authority_enqueue_request_refuses_before_any_write():
    from scripts.fleet_comms.authority import AuthorityService

    service = AuthorityService.__new__(AuthorityService)  # no connection: any write would raise AttributeError
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_request(recipient="kimi", body="Consult on this design.")
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_request(recipient="claude", body="Consult.", metadata={"requested_model": "kimi-code/k3"})


def test_authority_enqueue_discussion_refuses_before_any_write():
    from scripts.fleet_comms.authority import AuthorityService

    service = AuthorityService.__new__(AuthorityService)
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_discussion(
            channel="architecture",
            prompt="Compare the options.",
            participants=("claude", "kimicc"),
            rounds=1,
            task_digest="digest",
            correlation_id="corr",
            deadline_at="2026-09-30T00:00:00+00:00",
        )


def test_fleet_request_to_kimi_is_refused_before_any_insert():
    executor = RequestExecutor.__new__(RequestExecutor)
    executor.registry = load_endpoint_registry()
    with pytest.raises(ValueError, match=_TOKEN):
        executor.create_request(recipient="kimi", body="Consult on this design.")


@pytest.mark.parametrize(
    ("participants", "models"),
    [
        (("claude", "kimi"), None),
        (("claude", "codex"), {"claude": "kimi-code/k3"}),
        (("codex", "kimicc"), None),
    ],
)
def test_acp_discussion_refuses_on_effective_seats_and_models_before_the_plane(
    tmp_path, monkeypatch, participants, models
):
    from scripts.agent_runtime import acpx_discuss

    monkeypatch.setattr(acpx_discuss, "AcpxDiscussionController", _fail)
    monkeypatch.setattr(acpx_discuss, "ArtifactStore", _fail)
    monkeypatch.setattr(acpx_discuss, "default_plane_root", _fail)
    with pytest.raises(acpx_discuss.AcpxDiscussionError, match=_TOKEN):
        acpx_discuss.run_discussion(
            prompt="Compare the options.",
            cwd=tmp_path,
            task_id="t",
            correlation_id="c",
            idempotency_key="i",
            rounds=1,
            participants=participants,
            models=models,
        )


@pytest.mark.parametrize(("with_agents", "models"), [("claude,kimicc", None), ("claude,codex", "claude:kimi-code/k3")])
def test_ab_discuss_refuses_on_effective_models_before_any_channel_write(monkeypatch, capsys, with_agents, models):
    from scripts.ai_agent_bridge import _channels_cli
    from scripts.fleet_comms import authority

    monkeypatch.delenv("LU_AGENT_COMM_TRANSPORT", raising=False)
    monkeypatch.setattr(authority, "AuthorityService", _fail)
    args = types.SimpleNamespace(
        channel="architecture", body="Compare.", with_agents=with_agents, max_rounds=1, review=False, models=models
    )
    assert _channels_cli._handle_discuss(args) == 2
    assert _TOKEN in capsys.readouterr().err


def test_ab_inbox_run_for_kimi_is_refused_before_housekeeping(monkeypatch, capsys):
    from scripts.ai_agent_bridge import _channels, _channels_cli

    monkeypatch.setattr(_channels, "expire_stale_deliveries", _fail)
    args = types.SimpleNamespace(agent="kimi", once=True, until_idle=False, max_messages=None)
    assert _channels_cli._handle_inbox_run(args) == 2
    assert _TOKEN in capsys.readouterr().err


def test_inbox_worker_refuses_kimi_before_any_claim(monkeypatch):
    from scripts.ai_agent_bridge import _channels, _inbox

    monkeypatch.setattr(_inbox, "_claim_next_thread", _fail)
    monkeypatch.setattr(_channels, "expire_stale_deliveries", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _inbox.run_inbox("kimi")


# --- broker drain paths: a Kimi-addressed row is never processed ------------------------


@pytest.fixture
def broker_db(tmp_path, monkeypatch):
    """A migrated broker DB with a Kimi-addressed message (7), a Kimi-model ask (8) and an acknowledged one (9).

    Every reply, acknowledgement, failure record and ACP call raises;
    ``unchanged()`` compares the whole database with its seeded dump, and
    ``connects`` records every SQLite connection opened after seeding.
    """
    from scripts.ai_agent_bridge import _ask_lifecycle, _db, _messaging, _process

    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "messages.db")
    seed = _db.get_db()
    seed.executemany(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, message_type, content, data, timestamp, acknowledged)"
        " VALUES (?, 't', 'codex', ?, 'query', 'q', ?, '2026-09-30T00:00:00+00:00', ?)",
        [(7, "kimi", None, 0), (8, "claude", json.dumps({"to_model": "kimi-code/k3"}), 0), (9, "claude", None, 1)],
    )
    seed.commit()
    before = list(seed.iterdump())
    seed.close()
    real_connect = sqlite3.connect
    connects: list[str] = []

    def connect(database, *args, **kwargs):
        connects.append(str(database))
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
    for module, names in (
        (_process, ("send_message", "acknowledge", "record_ask_failure", "record_ask_reply", "run_compat_ask")),
        (_process, ("_notify_processing_failure", "_message_acknowledged")),
        (_ask_lifecycle, ("mark_ask_processing", "record_ask_failure", "_AskTerminalRecorder")),
        (_messaging, ("send_message", "acknowledge")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, _fail)

    def unchanged() -> bool:
        check = real_connect(_db.DB_PATH)
        try:
            return list(check.iterdump()) == before
        finally:
            check.close()

    return types.SimpleNamespace(connects=connects, unchanged=unchanged)


_SKIPPED = "skipped: Kimi is not a bridge recipient"


@pytest.mark.parametrize("message_id", [7, 8])
def test_a_kimi_addressed_message_is_never_processed(broker_db, capsys, message_id):
    from scripts.ai_agent_bridge import _process

    assert _process.process_message_for_recipient(message_id) is None
    assert capsys.readouterr().out.count(_SKIPPED) == 1
    assert broker_db.unchanged()
    assert not _process.recipient_has_acp_route("kimi")


def test_process_refuses_a_kimi_model_before_the_broker_is_opened(broker_db):
    from scripts.ai_agent_bridge import _process

    with pytest.raises(ValueError, match=_TOKEN):
        _process.process_message_for_recipient(9, model="kimi-code/k3")
    assert broker_db.connects == []


@pytest.mark.parametrize("argv", [["process", "9", "--model", "kimi-code/k3"], ["process-kimi", "7"]])
def test_process_cli_refuses_a_kimi_request_unopened(broker_db, argv):
    """A Kimi seat or model named on the command line is a Kimi request: refused before the broker is opened."""
    from scripts.ai_agent_bridge import _cli

    with pytest.raises(SystemExit, match=_TOKEN):
        _cli._dispatch_command(_cli._build_parser().parse_args(argv))
    assert broker_db.connects == []
    assert broker_db.unchanged()


@pytest.mark.parametrize("argv", [["process", "7"], ["process", "8"], ["process-claude", "7"], ["process-claude", "8"]])
def test_process_cli_skips_a_stored_kimi_row_and_records_nothing(broker_db, capsys, argv):
    """A generic drain reads the broker, then skips a stored Kimi-addressed row, reporting it once."""
    from scripts.ai_agent_bridge import _cli

    _cli._dispatch_command(_cli._build_parser().parse_args(argv))
    assert capsys.readouterr().out.count(_SKIPPED) == 1
    assert broker_db.unchanged()


def test_detached_ask_worker_refuses_a_kimi_target_unopened(broker_db, monkeypatch):
    from scripts.ai_agent_bridge import _ask_lifecycle

    monkeypatch.setattr(_ask_lifecycle.atexit, "register", _fail)
    with pytest.raises(SystemExit, match=_TOKEN):
        _ask_lifecycle.process_background_ask(7, "kimi")
    assert broker_db.connects == []
    assert broker_db.unchanged()


@pytest.mark.parametrize("message_id", [7, 8])
def test_detached_ask_worker_skips_a_stored_kimi_row(broker_db, monkeypatch, capsys, message_id):
    from scripts.ai_agent_bridge import _ask_lifecycle

    monkeypatch.setattr(_ask_lifecycle.atexit, "register", _fail)
    assert _ask_lifecycle.process_background_ask(message_id, "claude") is None
    assert capsys.readouterr().out.count(_SKIPPED) == 1
    assert broker_db.unchanged()


def test_the_query_only_connection_never_creates_or_writes_the_db(broker_db, tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import _db

    conn = _db.connect_readonly()
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("UPDATE messages SET acknowledged = 1")
    conn.close()
    assert broker_db.unchanged()
    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "absent.db")
    assert _db.connect_readonly() is None
    assert not (tmp_path / "absent.db").exists()


# --- capacity hint -----------------------------------------------------------------


# --- structural: no filesystem write before any Kimi refusal ---------------------------


class _WriteAttempt(BaseException):
    """A write before the refusal. A ``BaseException``, so no ``except Exception`` handler can swallow it."""


_WRITE_OPEN_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC


@pytest.fixture
def write_trap(tmp_path, monkeypatch):
    """Every filesystem, database and process creator raises and is recorded; reads still work.

    State roots (task records, the broker DB) live under ``tmp_path/state``, so
    a write the trap cannot see still shows up there. Tests seed state first,
    then call inside ``armed()``.
    """
    import builtins
    import io
    import shutil
    import tempfile

    state = tmp_path / "state"
    work = tmp_path / "work"
    state.mkdir()
    work.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(state / "tasks"))
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LU_AGENT_COMM_TRANSPORT", raising=False)
    from scripts.ai_agent_bridge import _db

    monkeypatch.setattr(_db, "DB_PATH", state / "broker" / "messages.db")
    attempts: list[str] = []

    def trap(name, real=None, reads=None):
        def creator(*args, **kwargs):
            if reads is not None and reads(*args, **kwargs):
                return real(*args, **kwargs)
            attempts.append(f"{name}{tuple(str(arg) for arg in args[:2])}")
            raise _WriteAttempt(f"{name} before the Kimi refusal: {args[:2]!r}")

        return creator

    def read_mode(_file, mode="r", *_args, **_kwargs):
        return not set(str(mode)) & set("wax+")

    def read_flags(_path, flags, *_args, **_kwargs):
        return not flags & _WRITE_OPEN_FLAGS

    def read_only_git(cmd, *_args, **_kwargs):
        return isinstance(cmd, (list, tuple)) and list(cmd[:1]) == ["git"] and cmd[1] in _GATE_GIT

    @contextlib.contextmanager
    def armed():
        """The trap, lifted on exit so nothing outside the call runs under it."""
        with pytest.MonkeyPatch.context() as trapped:
            _arm(trapped)
            yield attempts

    def _arm(monkeypatch) -> None:
        for owner, name in ((os, "mkdir"), (os, "makedirs"), (os, "replace"), (os, "rename"), (os, "remove")):
            monkeypatch.setattr(owner, name, trap(f"os.{name}"))
        for name in ("unlink", "rmdir", "symlink", "link", "truncate"):
            monkeypatch.setattr(os, name, trap(f"os.{name}"))
        monkeypatch.setattr(os, "open", trap("os.open", os.open, read_flags))
        monkeypatch.setattr(builtins, "open", trap("open", builtins.open, read_mode))
        monkeypatch.setattr(io, "open", trap("io.open", io.open, read_mode))
        for name in ("mkdir", "touch", "write_text", "write_bytes", "unlink", "rmdir", "rename", "replace"):
            monkeypatch.setattr(Path, name, trap(f"Path.{name}"))
        for name in ("mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile", "TemporaryDirectory"):
            monkeypatch.setattr(tempfile, name, trap(f"tempfile.{name}"))
        for name in ("copy", "copy2", "copyfile", "copytree", "move", "rmtree"):
            monkeypatch.setattr(shutil, name, trap(f"shutil.{name}"))
        # No refusal reads a database: even ``mode=ro`` creates -wal/-shm sidecars on a WAL-mode DB.
        monkeypatch.setattr(sqlite3, "connect", trap("sqlite3.connect"))
        monkeypatch.setattr(subprocess, "Popen", trap("subprocess.Popen", subprocess.Popen, read_only_git))

    return types.SimpleNamespace(state=state, work=work, armed=armed, monkeypatch=monkeypatch)


def _acp_ask(trap):
    from scripts.ai_agent_bridge import _acp_compat

    return _acp_compat.run_compat_ask("kimi", "Consult on this design.", task_id="kimi-consult")


def _acp_inter_agent(trap):
    from scripts.agent_runtime import runner

    trap.monkeypatch.setenv(runner.ACPX_TRANSPORT_ENV, "active")
    return runner.invoke_inter_agent(
        "kimi", "Consult.", cwd=trap.work, task_id="t", correlation_id="c", idempotency_key="i"
    )


def _acp_discuss(trap):
    from scripts.agent_runtime import acpx_discuss

    return acpx_discuss.run_discussion(
        prompt="Compare the options.",
        cwd=trap.work,
        task_id="t",
        correlation_id="c",
        idempotency_key="i",
        rounds=1,
        participants=("claude", "kimi"),
    )


def _bridge(*argv: str, legacy_plane: bool = False):
    def call(trap):
        from scripts.ai_agent_bridge import _channels_cli, _cli

        if legacy_plane:  # authority mode retires `inbox run` before the Kimi gate
            trap.monkeypatch.setattr(_channels_cli, "_legacy_writes_retired", lambda: False)
        trap.monkeypatch.setattr(sys, "argv", ["ab", *argv])
        return _cli.main()

    return call


# --- every Kimi recipient entry against EXISTING WAL-mode broker and authority DBs ---------


def _seed_broker(live_wal: bool) -> list[sqlite3.Connection]:
    """A migrated WAL-mode broker DB and authority plane, each holding Kimi-addressed rows.

    The seeded rows are checkpointed into the main files, as SQLite leaves them
    once the last connection closes (no sidecars). With ``live_wal`` a writer
    stays open on each DB with newer, un-checkpointed inserts and routing
    updates, so ``-wal``/``-shm`` exist; the caller closes the returned writers.
    """
    from scripts.ai_agent_bridge import _db
    from scripts.fleet_comms.authority import AuthorityService

    conn = _db.get_db()
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    conn.executemany(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, message_type, content, data, timestamp)"
        " VALUES (?, 't', 'codex', ?, 'query', 'q', ?, '2026-09-30T00:00:00+00:00')",
        [(7, "kimi", None), (8, "claude", json.dumps({"to_model": "kimi-code/k3"}))],
    )
    conn.commit()
    conn.close()
    plane = _db.DB_PATH.parent.parent / "plane"
    with AuthorityService(root=plane) as service:
        service.create_channel("ops", subscribers=["claude", "kimi"])  # a legacy Kimi subscriber row
        comms = Path(service.store.db_path)
    databases = (_db.DB_PATH, comms)
    sidecars = [path.with_name(path.name + suffix) for path in databases for suffix in ("-wal", "-shm")]
    assert not any(path.exists() for path in sidecars)
    if not live_wal:
        return []
    broker = sqlite3.connect(_db.DB_PATH)
    broker.execute(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, content, timestamp)"
        " VALUES (9, 't', 'codex', 'kimi', 'q', '2026-09-30T00:00:00+00:00')"
    )
    broker.execute("UPDATE messages SET to_llm = 'kimi', data = ? WHERE id = 8", (json.dumps({"to_model": "k3"}),))
    broker.commit()
    authority = sqlite3.connect(comms)
    authority.execute(
        "INSERT INTO authority_channel_subscribers(channel_id, recipient, metadata_json, created_at)"
        " SELECT channel_id, 'kimicc', '{}', '2026-09-30T00:00:00+00:00' FROM authority_channels WHERE name = 'ops'"
    )
    authority.execute(
        "UPDATE authority_channel_subscribers SET metadata_json = '{\"lane\": 1}' WHERE recipient = 'kimi'"
    )
    authority.commit()
    assert all(path.exists() for path in sidecars)
    return [broker, authority]


def _stat_tree(root: Path) -> dict[str, tuple[int, int, bytes]]:
    """Every entry under *root* with its size, mtime and bytes: a created, touched or grown sidecar shows up."""
    return {
        str(path.relative_to(root)): (stat.st_size, stat.st_mtime_ns, path.read_bytes() if path.is_file() else b"")
        for path in sorted(root.rglob("*"))
        for stat in (path.stat(),)
    }


def _fleet(*argv: str):
    def call(trap):
        from scripts.fleet_comms import cli as fleet_cli

        return fleet_cli.main([*argv, "--root", str(trap.state / "plane")])

    return call


def _send(**kwargs):
    def call(_trap):
        from scripts.ai_agent_bridge import _messaging

        return _messaging.send_message("Consult.", **kwargs)

    return call


def _post(**kwargs):
    def call(_trap):
        from scripts.ai_agent_bridge import _channels

        return _channels.post("ops", "claude", "Consult.", **kwargs)

    return call


def _new_channel(_trap):
    from scripts.ai_agent_bridge import _channels

    return _channels.create_channel("kimi-ops", subscribers=["kimi"])


_KIMI_MODEL = ("--to-model", "kimi-code/k3")


@pytest.mark.parametrize("live_wal", [False, True], ids=["wal-checkpointed", "wal-live"])
@pytest.mark.parametrize(
    "call",
    [
        pytest.param(_bridge("ask-kimi", "Consult.", "--task-id", "t"), id="ask"),
        pytest.param(_bridge("ask-claude", "Consult.", "--task-id", "t", *_KIMI_MODEL), id="ask-kimi-model"),
        pytest.param(_bridge("send", "Consult.", "--to", "kimi"), id="send"),
        pytest.param(_bridge("send", "Consult.", "--to", "claude", *_KIMI_MODEL), id="send-kimi-model"),
        pytest.param(_bridge("post", "ops", "Consult.", "--to", "claude,kimi"), id="post"),
        pytest.param(_bridge("post", "ops", "Consult.", "--to", "claude", "--model", "k3"), id="post-kimi-model"),
        pytest.param(_bridge("p", "ops", "kimicc", "Consult."), id="p"),
        pytest.param(_bridge("channel", "new", "kimi-ops", "--agents", "kimi"), id="channel-new"),
        pytest.param(_bridge("inbox", "--for", "kimi"), id="inbox"),
        pytest.param(_bridge("inbox", "show", "kimi"), id="inbox-show"),
        pytest.param(_bridge("inbox", "run", "kimi", "--once", legacy_plane=True), id="inbox-run"),
        pytest.param(_bridge("ack-all", "kimi"), id="ack-all"),
        pytest.param(_bridge("sync", "kimi"), id="sync"),
        pytest.param(_bridge("process-kimi", "7"), id="process-kimi"),
        pytest.param(_bridge("process-ask", "7", "kimi"), id="process-ask"),
        pytest.param(_bridge("process", "8", "--model", "kimi-code/k3"), id="process-kimi-model"),
        pytest.param(_bridge("discuss", "architecture", "Compare.", "--with", "claude,kimicc"), id="discuss"),
        pytest.param(_send(to_llm="kimi"), id="send-message"),
        pytest.param(_send(to_llm="claude", to_model="kimi-code/k3"), id="send-message-kimi-model"),
        pytest.param(_post(to_agents=["kimi"]), id="channel-post"),
        pytest.param(_post(to_agents=["claude"], to_model="k3"), id="channel-post-kimi-model"),
        pytest.param(_new_channel, id="create-channel"),
        pytest.param(_acp_ask, id="acp-ask"),
        pytest.param(_acp_inter_agent, id="acp-inter-agent"),
        pytest.param(_acp_discuss, id="acp-discuss"),
        pytest.param(
            _fleet(
                "channel",
                "publish",
                "ops",
                "Consult.",
                "--sender",
                "claude",
                "--recipient",
                "kimi",
                "--idempotency-key",
                "k",
            ),
            id="fleet-publish",
        ),
        pytest.param(_fleet("channel", "subscribe", "ops", "kimicc"), id="fleet-subscribe"),
        pytest.param(_fleet("channel", "create", "kimi-ops", "--subscriber", "kimi"), id="fleet-create"),
        pytest.param(_fleet("deliveries", "claim", "--recipient", "kimi", "--worker-id", "w"), id="fleet-claim"),
    ],
)
def test_every_kimi_recipient_entry_leaves_existing_wal_databases_untouched(write_trap, capsys, call, live_wal):
    """Kimi is not a bridge recipient: each refusal opens no database, so no file or sidecar changes at all."""
    writers = _seed_broker(live_wal)
    try:
        before = _stat_tree(write_trap.state)
        with write_trap.armed() as attempts:
            try:
                outcome = call(write_trap)
            except _WriteAttempt as exc:
                outcome = exc
            except SystemExit as exc:
                outcome = exc.code
            except Exception as exc:  # each entry point refuses with its own error type
                outcome = exc
        captured = capsys.readouterr()

        assert attempts == []
        assert _TOKEN in f"{outcome}\n{captured.out}\n{captured.err}"
        assert _stat_tree(write_trap.state) == before
    finally:
        for writer in writers:
            writer.close()


# --- a Kimi model or recipient named in request data is refused like an explicit one ------------

_DATA_PAYLOADS = {
    "to-model": {"to_model": "kimi-code/k3"},
    "to-model-alias": {"to_model": "k3"},
    "model": {"model": "kimi-code/k3"},
    "target-model": {"target_model": "kimi-code/k3"},
    "requested-model": {"requested_model": "kimi-code/k3"},
    "to": {"to": "kimi"},
    "to-llm": {"to_llm": "kimicc"},
    "to-agent": {"to_agent": "kimi"},
    "to-agents": {"to_agents": ["claude", "kimi"]},
    "agent": {"agent": "acpx-kimi"},
    "target": {"target": "kimi"},
    "route": {"route": "acpx-kimi"},
    "recipients": {"recipients": ["claude", "kimicc"]},
    "participant": {"participant": "kimi"},
}


def _entry_send_message(_trap, payload, _path):
    from scripts.ai_agent_bridge import _messaging

    return _messaging.send_message("Consult.", to_llm="claude", data=json.dumps(payload))


def _entry_send_cli(trap, _payload, path):
    return _bridge("send", "Consult.", "--to", "claude", "--data", path)(trap)


def _entry_ask_cli(trap, _payload, path):
    return _bridge("ask-claude", "Consult.", "--task-id", "t", "--data", path)(trap)


def _entry_post(_trap, payload, _path):
    from scripts.ai_agent_bridge import _channels

    return _channels.post("ops", "claude", "Consult.", to_agents=["claude"], attachments=[payload])


def _entry_acp(_trap, payload, _path):
    from scripts.ai_agent_bridge import _acp_compat

    return _acp_compat.run_compat_ask("claude", "Consult.", task_id="t", data=json.dumps(payload))


_DATA_ENTRIES = {
    "send-message": _entry_send_message,
    "send-cli": _entry_send_cli,
    "ask-cli": _entry_ask_cli,
    "channel-post": _entry_post,
    "acp-ask": _entry_acp,
}


@pytest.mark.parametrize("live_wal", [False, True], ids=["wal-checkpointed", "wal-live"])
@pytest.mark.parametrize("entry", _DATA_ENTRIES)
@pytest.mark.parametrize("payload", _DATA_PAYLOADS)
def test_kimi_named_in_request_data_refuses_with_zero_effects(write_trap, capsys, payload, entry, live_wal):
    """The gate reads the merged metadata: data naming Kimi leaves every database and sidecar untouched."""
    writers = _seed_broker(live_wal)
    try:
        attachment = write_trap.work / "attachment.json"
        attachment.write_text(json.dumps(_DATA_PAYLOADS[payload]), encoding="utf-8")
        before = _stat_tree(write_trap.state)
        with write_trap.armed() as attempts:
            try:
                outcome = _DATA_ENTRIES[entry](write_trap, _DATA_PAYLOADS[payload], str(attachment))
            except _WriteAttempt as exc:
                outcome = exc
            except SystemExit as exc:
                outcome = exc.code
            except Exception as exc:  # each entry point refuses with its own error type
                outcome = exc
        captured = capsys.readouterr()

        assert attempts == []
        assert _TOKEN in f"{outcome}\n{captured.out}\n{captured.err}"
        assert _stat_tree(write_trap.state) == before
    finally:
        for writer in writers:
            writer.close()


def test_send_message_stores_no_kimi_row_for_data_supplied_model(write_trap):
    """The probe that found the gap: neutral recipient, Kimi model only in ``data``."""
    from scripts.ai_agent_bridge import _db, _messaging

    with pytest.raises(ValueError, match=_TOKEN):
        _messaging.send_message("q", to_llm="claude", data='{"to_model":"kimi-code/k3"}', quiet=True)
    assert not _db.DB_PATH.exists()


def test_explicit_model_replaces_the_data_model_as_before(write_trap, monkeypatch):
    """An explicit non-Kimi model overrides a data ``to_model``: admitted, and the explicit model is stored."""
    from scripts.ai_agent_bridge import _db, _messaging

    monkeypatch.setattr(_messaging.subprocess, "run", lambda *_a, **_k: None)
    msg_id = _messaging.send_message(
        "q", to_llm="claude", to_model="claude-opus-5-5", data='{"to_model":"kimi-code/k3"}', quiet=True
    )
    conn = _db.get_db()
    try:
        stored = json.loads(conn.execute("SELECT data FROM messages WHERE id = ?", (msg_id,)).fetchone()[0])
    finally:
        conn.close()
    assert stored["to_model"] == "claude-opus-5-5"


def test_non_json_and_neutral_data_stay_admitted():
    """Plain text, JSON arrays and neutral selector values are not refused."""
    from scripts.ai_agent_bridge import _acp_compat

    for data in (None, "plain text naming kimi in prose", '["kimi"]', '{"to_model":"claude-opus-5-5","note":"kimi"}'):
        assert _acp_compat.require_compat_target("claude", data=data) == "claude"
    _acp_compat.refuse_kimi_recipients(("claude",), ("claude-opus-5-5",), attachments=({"to_model": "kimi-code/k3"},))


def test_authority_request_metadata_is_gated(tmp_path):
    """``enqueue_request`` refuses a Kimi model under any model key before writing."""
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "plane") as service:
        for key in retired_seat_admission.MODEL_SELECTOR_KEYS:
            with pytest.raises(retired_seat_admission.KimiAdmissionRefused):
                service.enqueue_request(recipient="claude", body="q", metadata={key: "kimi-code/k3"})
        job = service.enqueue_request(recipient="claude", body="q", metadata={"requested_model": "claude-opus-5-5"})
    assert job.job_id


class _KimiEffect(BaseException):
    """A Kimi-specific effect. A ``BaseException``, so no drain's ``except Exception`` can swallow it."""


@contextlib.contextmanager
def _kimi_effect_trap():
    """Arm, for a whole drain call, a trap on every Kimi-specific effect; generic broker reads stay allowed.

    Trapped: the ACP compat ask, the runtime runner and every legacy provider
    processor (adapter/runner invocation); process spawns and background
    relaunches; replies, acknowledgements, ask status and failure records,
    retry claims and terminal records (writes attributing processing); bridge
    usage telemetry. Every broker connection also gets an authorizer that
    records and denies any INSERT, UPDATE or DELETE on ``messages``.
    """
    from lu_machinery.telemetry import legacy_bridge

    from agent_runtime import runner as agent_runner
    from scripts.agent_runtime import runner as scripts_runner
    from scripts.ai_agent_bridge import (
        _acp_compat,
        _agy,
        _ask_lifecycle,
        _claude,
        _codex,
        _cursor,
        _grok_build,
        _messaging,
        _opencode,
        _process,
    )

    effects: list[str] = []

    def trap(name):
        def effect(*args, **_kwargs):
            effects.append(f"{name}{tuple(str(arg) for arg in args[:2])}")
            raise _KimiEffect(f"{name} on a stored Kimi row")

        return effect

    real_connect = sqlite3.connect

    def connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)

        def authorize(action, table, *_rest):
            if table == "messages" and action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE):
                effects.append(f"sqlite write {action} on messages")
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        conn.set_authorizer(authorize)
        return conn

    targets = [
        (_process, ("run_compat_ask", "send_message", "acknowledge", "record_ask_failure", "record_ask_reply")),
        (_process, ("_notify_processing_failure",)),
        (_acp_compat, ("run_compat_ask",)),
        (agent_runner, ("invoke", "invoke_inter_agent")),
        (scripts_runner, ("invoke", "invoke_inter_agent")),
        (_claude, ("process_for_claude",)),
        (_codex, ("process_for_codex",)),
        (_agy, ("process_for_agy",)),
        (_grok_build, ("process_for_grok_build",)),
        (_cursor, ("process_for_cursor",)),
        (_opencode, ("process_for_opencode",)),
        (_messaging, ("send_message", "acknowledge")),
        (_ask_lifecycle, ("mark_ask_processing", "record_ask_failure", "record_ask_reply", "_set_ask_status")),
        (_ask_lifecycle, ("claim_ask_retry", "launch_background_ask", "_AskTerminalRecorder", "_remove_pid_file")),
        (_ask_lifecycle.atexit, ("register",)),
        (subprocess, ("Popen",)),
        (os, ("fork", "posix_spawn", "posix_spawnp")),
        (legacy_bridge, ("start_bridge_invocation_safely", "finish_bridge_invocation_safely")),
        (legacy_bridge, ("record_bridge_invocation_start", "record_bridge_invocation_finish")),
    ]
    with pytest.MonkeyPatch.context() as trapped:
        for owner, names in targets:
            for name in names:
                trapped.setattr(owner, name, trap(f"{getattr(owner, '__name__', owner)}.{name}"))
        trapped.setattr(sqlite3, "connect", connect)
        yield effects


def _stored_drain_rows(writer: sqlite3.Connection) -> None:
    """Uncheckpointed Kimi-model rows addressed to the seats the batch drains select (10-12)."""
    writer.executemany(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, message_type, content, data, timestamp)"
        " VALUES (?, 't', 'agy', ?, 'query', 'q', ?, '2026-09-30T00:00:00+00:00')",
        [
            (10, "claude", json.dumps({"to_model": "kimi-code/k3"})),
            (11, "codex", json.dumps({"to_model": "k3"})),
            (12, "gemini", json.dumps({"to_model": "kimi-code/k3"})),
        ],
    )
    writer.commit()


def _direct(message_id):
    def call(_state):
        from scripts.ai_agent_bridge import _process

        return _process.process_message_for_recipient(message_id)

    return call


def _cli_argv(*argv):
    def call(_state):
        from scripts.ai_agent_bridge import _cli

        return _cli._dispatch_command(_cli._build_parser().parse_args(list(argv)))

    return call


def _interactive(message_id):
    def call(_state):
        from scripts.ai_agent_bridge import _cli

        return _cli._dispatch_interactive("process", ["process", str(message_id)])

    return call


def _target(message_id, target):
    def call(_state):
        from scripts.ai_agent_bridge import _ask_lifecycle

        return _ask_lifecycle._process_target(message_id, target, {"no_timeout": True})

    return call


def _background(message_id, target):
    def call(_state):
        from scripts.ai_agent_bridge import _ask_lifecycle

        return _ask_lifecycle.process_background_ask(message_id, target)

    return call


def _batch(seat):
    def call(_state):
        from scripts.ai_agent_bridge import _cli, _codex

        return {
            "claude": _cli.process_all_claude,
            "codex": _codex.process_all_codex,
            "gemini": _cli.process_all_gemini,
        }[seat]()

    return call


def _watchdog(agent, message_id=None):
    """The ask watchdog sweep, with a dead worker's launch record naming *agent*."""

    def call(_state):
        from scripts.ai_agent_bridge import _ask_lifecycle

        return _ask_lifecycle.run_ask_watchdog(message_id)

    call.launch_agent = agent
    return call


@pytest.mark.parametrize(
    ("call", "skips"),
    [
        pytest.param(_direct(8), 1, id="direct-routed-onto-kimi"),
        pytest.param(_direct(9), 1, id="direct-inserted-for-kimi"),
        pytest.param(_direct(10), 1, id="direct-kimi-model"),
        pytest.param(_cli_argv("process", "9"), 1, id="cli-process"),
        pytest.param(_cli_argv("process-claude", "8"), 1, id="cli-target"),
        pytest.param(_cli_argv("process-codex", "11"), 1, id="cli-target-kimi-model"),
        pytest.param(_interactive(9), 1, id="interactive-process"),
        pytest.param(_target(9, "claude"), 1, id="target-drain"),
        pytest.param(_background(9, "claude"), 1, id="background"),
        pytest.param(_background(10, "claude"), 1, id="background-kimi-model"),
        pytest.param(_batch("claude"), 1, id="process-all-claude"),
        pytest.param(_batch("codex"), 1, id="process-all-codex"),
        pytest.param(_batch("gemini"), 1, id="process-all-gemini"),
        pytest.param(_watchdog("kimi"), 3, id="ask-watchdog-kimi-launch"),
        pytest.param(_watchdog("claude", 10), 1, id="ask-watchdog-kimi-model"),
    ],
)
def test_generic_drains_skip_stored_kimi_rows_before_any_kimi_effect(tmp_path, monkeypatch, capsys, call, skips):
    """A generic drain skips a stored Kimi row before any Kimi-specific effect.

    Kimi is not a bridge recipient, and since sends refuse Kimi, a Kimi row
    can only be a legacy stored one. A generic drain (``process``,
    ``process-<seat>``, ``process-all``, a background worker, the ask
    watchdog) is not a Kimi request: reading the broker is its job, so it may
    open the WAL-mode DB and touch its ``-shm``. The binding invariant is that
    a stored Kimi-addressed row is skipped before any Kimi-specific effect —
    no adapter or runner invocation, no process, no reply row, no
    acknowledgement or status write attributing processing to Kimi, no Kimi
    telemetry — is left exactly as it was and is reported once as
    ``skipped: Kimi is not a bridge recipient``.

    The rows include uncheckpointed inserts and routing updates held in a
    live WAL (a writer stays open), and the trap is armed for the whole call.
    """
    from scripts.ai_agent_bridge import _ask_lifecycle, _db

    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "state" / "broker" / "messages.db")
    broker, authority = _seed_broker(live_wal=True)
    authority.close()
    try:
        _stored_drain_rows(broker)
        launch_agent = getattr(call, "launch_agent", None)
        if launch_agent:
            monkeypatch.setattr(_ask_lifecycle, "REPO_ROOT", tmp_path)
            launch = tmp_path / "batch_state" / "asks" / "t" / "launch.json"
            launch.parent.mkdir(parents=True)
            launch.write_text(
                json.dumps({"pid": 999_999_999, "agent": launch_agent, "started_at": _ask_lifecycle._now_iso()}),
                encoding="utf-8",
            )
        before = broker.execute("SELECT * FROM messages ORDER BY id").fetchall()
        assert {row[3] for row in before if row[0] in (8, 9)} == {"kimi"}  # the WAL routing update and insert
        with _kimi_effect_trap() as effects, contextlib.suppress(_KimiEffect):
            call(None)
        out = capsys.readouterr().out

        assert effects == []
        assert out.count(_SKIPPED) == skips
        assert broker.execute("SELECT * FROM messages ORDER BY id").fetchall() == before
        assert not (tmp_path / "batch_state" / "asks" / "t" / "retry-claim").exists()
    finally:
        broker.close()


def test_a_kimi_subscriber_gets_no_delivery(tmp_path):
    """An existing Kimi subscriber row stays, but a fan-out publish never creates a delivery for it."""
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "plane") as service:
        service.create_channel("ops", subscribers=["claude", "kimi", "kimicc"])
        message = service.publish_message(sender="codex", body="Status.", channel="ops", idempotency_key="k")
        recipients = {
            row["recipient"]
            for row in service._conn.execute(
                "SELECT recipient FROM authority_deliveries WHERE message_id = ?", (message.message_id,)
            )
        }
        assert recipients == {"claude"}
        assert set(service.get_channel("ops").subscribers) == {"claude", "kimi", "kimicc"}


@pytest.mark.parametrize("broadcast", [False, True])
def test_channel_default_recipients_skip_kimi_seats(monkeypatch, broadcast):
    from scripts.ai_agent_bridge import _channels, _channels_cli

    channel = {"subscribers": ["claude", "kimi", "kimicc", "codex"]}
    monkeypatch.setattr(_channels, "live_agents", lambda: ["claude", "kimi", "kimicc", "codex"])
    recipients = (
        _channels_cli._broadcast_recipients(channel) if broadcast else _channels_cli._subscriber_recipients(channel)
    )
    assert recipients == ["claude", "codex"]


# --- stored Kimi deliveries: generic drains and sweeps leave them untouched ----------

_OLD = "2020-01-01T00:00:00+00:00"


@pytest.fixture
def delivery_db(tmp_path, monkeypatch):
    """A channel broker with legacy Kimi deliveries (by seat and by model) and matching non-Kimi controls.

    Kimi rows are older than their controls, so a drain that ignored the
    filter would reach them first. Returns ``rows()``, the full deliveries
    table keyed by id.
    """
    from scripts.ai_agent_bridge import _channels, _db

    db_file = tmp_path / "messages.db"
    monkeypatch.setattr("scripts.ai_agent_bridge._config.DB_PATH", db_file)
    monkeypatch.setattr(_db, "DB_PATH", db_file)
    monkeypatch.setattr(_channels, "WAKE_ROOT", tmp_path / "wake")
    _db.init_db().close()
    _channels.create_channel("topic")
    conn = _db.get_db()
    rows = [
        # id, to_agent, to_model, status, lease_until, attempt_count, retry_after, created_at
        ("kimi-model", "claude", "kimi-code/k3", "pending", None, 0, None, "2020-01-01T00:00:00+00:00"),
        ("kimi-seat", "kimi", None, "pending", None, 0, None, "2020-01-01T00:00:01+00:00"),
        ("kimi-alias-lease", "claude", "k3", "processing", _OLD, 1, None, "2020-01-01T00:00:02+00:00"),
        ("kimi-exhausted", "claude", "kimi-code/k3", "pending", None, 9, _OLD, "2020-01-01T00:00:03+00:00"),
        ("claude-pending", "claude", None, "pending", None, 0, None, "2020-01-02T00:00:00+00:00"),
        ("claude-lease", "claude", None, "processing", _OLD, 1, None, "2020-01-02T00:00:01+00:00"),
        ("claude-exhausted", "claude", None, "pending", None, 9, _OLD, "2020-01-02T00:00:02+00:00"),
    ]
    for delivery_id, to_agent, to_model, status, lease, attempts, retry_after, created_at in rows:
        conn.execute(
            "INSERT INTO channel_messages (message_id, channel, thread_id, from_agent, body, created_at)"
            " VALUES (?, 'topic', ?, 'user', 'q', ?)",
            (f"m-{delivery_id}", f"t-{delivery_id}", created_at),
        )
        conn.execute(
            "INSERT INTO deliveries (delivery_id, message_id, to_agent, to_model, status, lease_until,"
            " attempt_count, retry_after) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (delivery_id, f"m-{delivery_id}", to_agent, to_model, status, lease, attempts, retry_after),
        )
    conn.commit()
    conn.close()

    def snapshot() -> dict[str, tuple]:
        check = sqlite3.connect(db_file)
        try:
            return {row[0]: tuple(row) for row in check.execute("SELECT * FROM deliveries ORDER BY delivery_id")}
        finally:
            check.close()

    return snapshot


def _kimi_rows(snapshot: dict[str, tuple]) -> dict[str, tuple]:
    return {key: row for key, row in snapshot.items() if key.startswith("kimi-")}


def _changed(before: dict[str, tuple], after: dict[str, tuple]) -> set[str]:
    return {key for key in before if before[key] != after[key]}


def _sweep(name):
    def call():
        from scripts.ai_agent_bridge import _channels, _reconcile

        return {
            "claim": lambda: _channels.claim_next_delivery("claude"),
            "release-leases": _channels.release_expired_leases,
            "expire-stale": _channels.expire_stale_deliveries,
            "expire-dead-lanes": lambda: _channels.bulk_expire_dead_lanes(frozenset({"claude", "kimi"})),
            "reconcile": _reconcile.reconcile_deliveries,
        }[name]()

    return call


@pytest.mark.parametrize(
    ("sweep", "control"),
    [
        ("claim", {"claude-pending"}),  # the oldest eligible non-Kimi row, not the older Kimi rows
        ("release-leases", {"claude-lease"}),
        ("expire-stale", {"claude-pending", "claude-exhausted"}),
        ("expire-dead-lanes", {"claude-pending", "claude-exhausted"}),
        ("reconcile", {"claude-lease", "claude-exhausted"}),
    ],
)
def test_channel_sweeps_leave_stored_kimi_deliveries_unwritten(delivery_db, sweep, control):
    """Every generic channel drain and sweep excludes a stored Kimi delivery before it writes."""
    before = delivery_db()
    _sweep(sweep)()
    after = delivery_db()
    assert _kimi_rows(after) == _kimi_rows(before)
    assert _changed(before, after) == control


def test_the_inbox_drain_skips_a_stored_kimi_delivery_before_claim_writes_or_telemetry(delivery_db, monkeypatch):
    """The reviewer's case: a delivery to Claude pinned to a Kimi model is never claimed, failed or reported.

    The drain's own sweeps expire the old Claude rows and it delivers a fresh
    one (non-Kimi paths unchanged).
    """
    from agent_runtime.result import Result
    from scripts.ai_agent_bridge import _channels, _inbox

    telemetry: list[tuple] = []
    for name in ("emit_delivery_failed", "emit_delivery_delivered", "emit_reply_started", "emit_reply_complete"):
        monkeypatch.setattr(_inbox, name, lambda *args, _name=name, **kwargs: telemetry.append((_name, args, kwargs)))
    monkeypatch.setattr(
        "scripts.fleet_comms.bottleneck_alerts.scan_bottlenecks_at_inbox_checkpoint", lambda **_kwargs: None
    )
    invoked: list[str] = []

    def invoke(agent, prompt, **kwargs):
        invoked.append(kwargs["task_id"])
        return Result(
            ok=True,
            agent=agent,
            model=kwargs.get("model") or "claude-opus-5-5",
            mode=kwargs["mode"],
            response="reply",
            stderr_excerpt="",
            duration_s=0.0,
            session_id="s",
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    monkeypatch.setattr(_inbox, "runtime_invoke", invoke)
    fresh = _channels.post("topic", "user", "q", to_agents=["claude"], auto_snapshot=False)
    before = delivery_db()

    summary = _inbox.run_inbox("claude")
    after = delivery_db()

    assert _kimi_rows(after) == _kimi_rows(before)
    kimi_threads = {f"t-{key}" for key in _kimi_rows(before)}
    assert not [event for event in telemetry if event[1] and event[1][0] in kimi_threads]
    session = _inbox._thread_session_key
    assert invoked == [session("topic", "t-claude-lease"), session("topic", str(fresh["thread_id"]))]
    delivered = {key for key, row in after.items() if row[4] == "delivered"}
    assert delivered == {"claude-lease", *(key for key in after if not key.startswith(("kimi-", "claude-")))}
    assert (summary.deliveries_claimed, summary.deliveries_failed) == (2, 0)


def test_fleet_comms_delivery_reclaim_leaves_a_stored_kimi_delivery_unwritten(tmp_path):
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "plane") as service:
        message = service.publish_message(sender="user", body="q", recipients=["claude"], deadline_at=_OLD)
        conn = service._conn
        conn.execute(
            "INSERT INTO authority_deliveries (delivery_id, message_id, recipient, state, deadline_at,"
            " created_at, updated_at) VALUES ('kimi-legacy', ?, 'kimi', 'queued', ?, ?, ?)",
            (message.message_id, _OLD, _OLD, _OLD),
        )
        conn.commit()
        dump = lambda: {row["delivery_id"]: tuple(row) for row in conn.execute("SELECT * FROM authority_deliveries")}  # noqa: E731
        dead_letters = lambda: conn.execute("SELECT COUNT(*) FROM authority_dead_letters").fetchone()[0]  # noqa: E731
        before, letters = dump(), dead_letters()

        assert service.reclaim_expired_deliveries() == 1
        after = dump()
        assert after["kimi-legacy"] == before["kimi-legacy"]
        assert [row[3] for key, row in after.items() if key != "kimi-legacy"] == ["expired"]
        assert dead_letters() == letters + 1


def test_the_stale_request_requeue_leaves_a_stored_kimi_request_running(tmp_path):
    """A stored request to a Kimi seat, or whose message metadata pins a Kimi model, is never requeued."""
    from scripts.fleet_comms.request_executor import RequestExecutor

    with RequestExecutor(root=tmp_path) as executor:
        kept = executor.create_request(recipient="codex", body="ping", metadata={"model": "gpt-6.1-sol"})
        legacy = executor.create_request(recipient="claude", body="ping")
        pinned = executor.create_request(recipient="claude", body="ping")
        conn = executor.store.connection
        conn.execute("UPDATE requests SET state = 'running', updated_at = '2000-01-01T00:00:00Z'")
        conn.execute("UPDATE requests SET resolved_recipient = 'kimi' WHERE request_id = ?", (legacy.request_id,))
        conn.execute(
            "UPDATE comms_messages SET metadata_json = ? WHERE message_id = ?",
            (json.dumps({"model": "kimi-code/k3"}), pinned.request_message_id),
        )
        conn.commit()

        assert executor.requeue_stale_running(stale_after_seconds=60) == [kept.request_id]
        assert executor.get_request(legacy.request_id).state == "running"
        assert executor.get_request(pinned.request_id).state == "running"


def test_create_request_refuses_a_kimi_model_in_its_metadata_before_any_insert(tmp_path):
    from lu_machinery.agent_runtime.retired_seat_admission import KimiAdmissionRefused

    from scripts.fleet_comms.request_executor import RequestExecutor

    with RequestExecutor(root=tmp_path) as executor:
        conn = executor.store.connection
        with pytest.raises(KimiAdmissionRefused):
            executor.create_request(recipient="claude", body="ping", metadata={"model": "k3"})
        assert conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM comms_messages").fetchone()[0] == 0


def test_the_ancient_message_sweep_leaves_a_stored_kimi_message_unacknowledged(broker_db, capsys):
    from scripts.ai_agent_bridge import _broker, _db

    check = sqlite3.connect(_db.DB_PATH)
    check.execute("UPDATE messages SET timestamp = ?", (_OLD,))
    check.execute("UPDATE messages SET acknowledged = 0")
    check.commit()
    assert _broker._cleanup_ancient_messages("force-ack", 1, dry_run=False) == 1
    acknowledged = dict(check.execute("SELECT id, acknowledged FROM messages"))
    check.close()
    assert acknowledged == {7: 0, 8: 0, 9: 1}
    assert capsys.readouterr().out.count(_SKIPPED) == 2


# --- stored Kimi authority jobs: generic reclaim and claim paths leave them untouched ----------

_FUTURE = "2999-01-01T00:00:00Z"


def _legacy_job(service, payload, *, kind="request", deadline_at=None, lease_expires_at=None):
    """A stored job written before enqueue refused Kimi (bypasses admission, as legacy rows did)."""
    from scripts.fleet_comms.contracts import new_id

    with service._write_transaction():
        job = service._enqueue_job_tx(
            job_kind=kind,
            subject_id=new_id("legacy-subject"),
            payload=payload,
            deadline_at=deadline_at,
            idempotency_key=new_id("legacy-key"),
        )
    if lease_expires_at is not None:
        service._conn.execute(
            "UPDATE authority_jobs SET state = 'running', lease_owner = 'w', lease_expires_at = ?, fence_token = 1"
            " WHERE job_id = ?",
            (lease_expires_at, job.job_id),
        )
        service._conn.commit()
    return job.job_id


@pytest.fixture
def job_plane(tmp_path):
    """An authority plane with stored Kimi jobs (by seat, model and participant) older than non-Kimi controls.

    Every Kimi job is due for a generic write: expired deadlines, a stale
    running lease, or simply queued first. Returns ``(service, kimi_ids,
    controls, state)`` where ``state()`` snapshots the job, event and
    dead-letter rows per job.
    """
    from scripts.fleet_comms.authority import AuthorityService

    service = AuthorityService(root=tmp_path / "plane")
    kimi_ids = {
        "seat-expired": _legacy_job(service, {"recipient": "kimi", "metadata": {}}, deadline_at=_OLD),
        "model-stale-lease": _legacy_job(
            service,
            {"recipient": "claude", "metadata": {"requested_model": "kimi-code/k3"}},
            lease_expires_at=_OLD,
        ),
        "participant-expired": _legacy_job(
            service, {"participants": ["claude", "kimicc"]}, kind="discussion", deadline_at=_OLD
        ),
        "alias-queued": _legacy_job(service, {"recipient": "codex", "metadata": {"model": "k3"}}),
    }
    controls = {
        "expired": _legacy_job(service, {"recipient": "codex", "metadata": {"task_id": "e"}}, deadline_at=_OLD),
        "stale-lease": _legacy_job(
            service, {"recipient": "codex", "metadata": {"task_id": "s"}}, lease_expires_at=_OLD
        ),
    }

    def state():
        conn = service._conn
        return {
            job_id: (
                tuple(conn.execute("SELECT * FROM authority_jobs WHERE job_id = ?", (job_id,)).fetchone()),
                conn.execute("SELECT COUNT(*) FROM authority_job_events WHERE job_id = ?", (job_id,)).fetchone()[0],
                conn.execute("SELECT COUNT(*) FROM authority_dead_letters WHERE job_id = ?", (job_id,)).fetchone()[0],
            )
            for job_id in (*kimi_ids.values(), *controls.values())
        }

    try:
        yield service, kimi_ids, controls, state
    finally:
        service.close()


def _job_state(service, job_id):
    return service.get_job(job_id).state


@pytest.mark.parametrize("entry", ["claim-job", "claim-next-job", "reclaim"])
def test_generic_job_reclaim_and_claims_leave_stored_kimi_jobs_unwritten(job_plane, entry):
    """The reviewer's case: claiming a non-Kimi job never expires, events or dead-letters a legacy Kimi job.

    ``claim_job`` (reached from the ACP compat ask and channel ``ask``) and
    ``claim_next_job`` both run the generic reclaim first; ``claim_next_job``
    also passes over the older queued Kimi jobs. Non-Kimi controls are
    reclaimed as before.
    """
    service, kimi_ids, controls, state = job_plane
    fresh = service.enqueue_request(recipient="claude", body="ping", deadline_at=_FUTURE)
    before = state()

    if entry == "claim-job":
        lease = service.claim_job(fresh.job_id, "worker", now="2026-09-30T00:00:00Z")
    elif entry == "claim-next-job":
        lease = service.claim_next_job("worker", now="2026-09-30T00:00:00Z")
    else:
        lease = None
        assert service.reclaim_expired_jobs(now="2026-09-30T00:00:00Z") == 2

    after = state()
    assert {job_id: after[job_id] for job_id in kimi_ids.values()} == {
        job_id: before[job_id] for job_id in kimi_ids.values()
    }
    assert _job_state(service, controls["expired"]) == "expired"
    assert after[controls["expired"]][2] == 1  # dead-lettered, as before
    if lease is not None:
        # claim_next_job takes the oldest non-Kimi queued job: the requeued control, then the fresh one.
        assert lease.job.job_id in {fresh.job_id, controls["stale-lease"]}
        assert lease.job.state == "running"
    if entry != "claim-next-job":
        assert _job_state(service, controls["stale-lease"]) == "queued"


@pytest.mark.parametrize("operation", ["claim_job", "retry_job", "redrive_job"])
def test_a_named_stored_kimi_job_is_refused_unwritten(job_plane, operation):
    """Claiming, retrying or redriving a stored Kimi job by id is refused before any write."""
    from scripts.fleet_comms.authority import AuthorityServiceError

    service, kimi_ids, _controls, state = job_plane
    job_id = kimi_ids["seat-expired"]
    service._conn.execute(
        "UPDATE authority_jobs SET state = ? WHERE job_id = ?",
        ("dead_lettered" if operation == "redrive_job" else "failed" if operation == "retry_job" else "queued", job_id),
    )
    service._conn.commit()
    before = state()
    call = getattr(service, operation)
    args = (job_id, "worker") if operation == "claim_job" else (job_id,)
    with pytest.raises(AuthorityServiceError, match=r"kimi_job_not_(claimable|retryable)"):
        call(*args, now="2026-09-30T00:00:00Z", **({} if operation == "claim_job" else {"deadline_at": _FUTURE}))
    assert state() == before


def test_an_unreadable_job_payload_is_left_unwritten(job_plane):
    """A payload that cannot be read is not provably non-Kimi, so a generic reclaim leaves the job (fail closed)."""
    service, _kimi_ids, controls, state = job_plane
    job = service.get_job(controls["expired"])
    service.store.get(job.payload_artifact_id).blob_path.write_bytes(b"tampered")
    service._kimi_payloads.clear()
    before = state()
    assert service.reclaim_expired_jobs(now="2026-09-30T00:00:00Z") == 1  # only the stale-lease control
    assert state()[controls["expired"]] == before[controls["expired"]]


def test_a_delivery_of_a_kimi_model_request_is_never_claimed_or_reclaimed(tmp_path):
    """A stored delivery to Claude of a request pinned to a Kimi model is passed over by claims and reclaims."""
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "plane") as service:
        legacy = service.publish_message(sender="user", body="old", recipients=["claude"], deadline_at=_FUTURE)
        stale = service.publish_message(sender="user", body="stale", recipients=["claude"], deadline_at=_OLD)
        for message in (legacy, stale):
            with service._write_transaction():
                service._enqueue_job_tx(
                    job_kind="request",
                    subject_id=message.message_id,
                    payload={"recipient": "claude", "metadata": {"requested_model": "kimi-code/k3"}},
                    deadline_at=None,
                    idempotency_key=f"legacy-{message.message_id}",
                )
        fresh = service.publish_message(sender="user", body="new", recipients=["claude"], deadline_at=_FUTURE)
        conn = service._conn
        dump = lambda: {row["delivery_id"]: tuple(row) for row in conn.execute("SELECT * FROM authority_deliveries")}  # noqa: E731
        kimi_deliveries = {*legacy.delivery_ids, *stale.delivery_ids}
        before = dump()

        lease = service.claim_next_delivery("claude", "worker", now="2026-09-30T00:00:00Z")
        assert lease is not None and lease.delivery.delivery_id == fresh.delivery_ids[0]
        after = dump()
        assert {key: after[key] for key in kimi_deliveries} == {key: before[key] for key in kimi_deliveries}
        assert not conn.execute(
            "SELECT COUNT(*) FROM authority_delivery_attempts WHERE delivery_id IN (?, ?)", tuple(kimi_deliveries)
        ).fetchone()[0]
        assert not conn.execute("SELECT COUNT(*) FROM authority_dead_letters").fetchone()[0]


# --- stored Kimi bridge messages: bulk acknowledgement, timeout notices, retention, migration ----------


@pytest.fixture
def message_db(tmp_path, monkeypatch):
    """A broker with stored Kimi messages (by seat, by ``to_model``, by another data key) and non-Kimi controls.

    Every row is old, acknowledged-or-timed-out and due for a generic write.
    Returns ``rows()``, the messages table keyed by id.
    """
    from scripts.ai_agent_bridge import _broker, _db

    db_file = tmp_path / "messages.db"
    monkeypatch.setattr(_db, "DB_PATH", db_file)
    monkeypatch.setattr(_broker, "DB_PATH", db_file)
    seed = _db.get_db()
    seed.executemany(
        "INSERT INTO messages (id, task_id, from_llm, to_llm, message_type, content, data, timestamp, acknowledged,"
        " status) VALUES (?, 't', 'codex', ?, 'query', 'q', ?, ?, ?, ?)",
        [
            (1, "kimi", None, _OLD, 0, "timed-out:x"),
            (2, "claude", json.dumps({"to_model": "kimi-code/k3"}), _OLD, 0, "timed-out:x"),
            (3, "claude", json.dumps({"model": "k3"}), _OLD, 0, "timed-out:x"),
            (4, "claude", None, _OLD, 0, "timed-out:x"),
            (5, "claude", json.dumps({"to_model": "claude-opus-5-5"}), _OLD, 0, "timed-out:x"),
        ],
    )
    seed.commit()
    seed.close()

    def rows() -> dict[int, tuple]:
        check = sqlite3.connect(db_file)
        try:
            return {row[0]: tuple(row) for row in check.execute("SELECT * FROM messages ORDER BY id")}
        finally:
            check.close()

    return rows


_KIMI_MESSAGES = (1, 2, 3)


def test_ack_all_leaves_a_stored_kimi_model_message_unacknowledged(message_db, capsys):
    from scripts.ai_agent_bridge import _messaging

    before = message_db()
    _messaging.acknowledge_all("claude", consumed_by_live_driver=True)
    after = message_db()
    assert {key for key in before if before[key] != after[key]} == {4, 5}
    assert "4, 5" in capsys.readouterr().out


def test_timeout_notices_neither_show_nor_mark_a_stored_kimi_ask(message_db, capsys):
    from scripts.ai_agent_bridge import _ask_lifecycle

    before = message_db()
    assert _ask_lifecycle.print_timeout_notice() == [4, 5]
    _ask_lifecycle.mark_timeout_notices_shown([1, 2, 3, 4, 5])
    after = message_db()
    assert {key for key in before if before[key] != after[key]} == {4, 5}
    assert "#1 " not in capsys.readouterr().err


def test_retention_keeps_stored_kimi_messages_and_deliveries(message_db, delivery_db):
    """``ab cleanup`` retention deletes old terminal rows but keeps stored Kimi ones and their channel messages."""
    from scripts.ai_agent_bridge import _broker, _db

    conn = _db.get_db()
    conn.execute("UPDATE messages SET acknowledged = 1")
    conn.execute("UPDATE deliveries SET status = 'delivered', lease_until = NULL")
    conn.commit()
    conn.close()
    deliveries_before = delivery_db()

    assert _broker.broker_retention_cleanup("1d", dry_run=True) == 2 + 3 + 3
    assert _broker.broker_retention_cleanup("1d") == 8

    assert set(message_db()) == set(_KIMI_MESSAGES)
    assert delivery_db() == _kimi_rows(deliveries_before)
    check = sqlite3.connect(_db.DB_PATH)
    try:
        kept = {row[0] for row in check.execute("SELECT message_id FROM channel_messages")}
    finally:
        check.close()
    assert kept == {f"m-{key}" for key in _kimi_rows(deliveries_before)}


def test_the_live_consumption_backfill_leaves_a_stored_kimi_message_as_it_is(tmp_path, monkeypatch):
    """The one-time ``consumed_by_live_driver`` backfill grandfathers acknowledged rows, except stored Kimi ones."""
    from scripts.ai_agent_bridge import _db

    db_file = tmp_path / "messages.db"
    monkeypatch.setattr(_db, "DB_PATH", db_file)
    legacy = sqlite3.connect(db_file)
    legacy.execute(
        "CREATE TABLE messages (id INTEGER PRIMARY KEY, task_id TEXT, from_llm TEXT NOT NULL, to_llm TEXT NOT NULL,"
        " message_type TEXT, content TEXT NOT NULL, data TEXT, timestamp TEXT NOT NULL, acknowledged INTEGER DEFAULT 0)"
    )
    legacy.executemany(
        "INSERT INTO messages (id, from_llm, to_llm, content, data, timestamp, acknowledged)"
        " VALUES (?, 'codex', ?, 'q', ?, ?, 1)",
        [(1, "kimi", None, _OLD), (2, "claude", json.dumps({"to_model": "k3"}), _OLD), (3, "claude", None, _OLD)],
    )
    legacy.commit()
    legacy.close()

    _db.get_db().close()
    check = sqlite3.connect(db_file)
    try:
        consumed = dict(check.execute("SELECT id, consumed_by_live_driver FROM messages"))
    finally:
        check.close()
    assert consumed == {1: 0, 2: 0, 3: 1}
