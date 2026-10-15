"""systemd notifications and the lock-sensitive watchdog probe (#10674)."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import secrets
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.rag import sources_supervision as sup
from scripts.rag.call_governor import CallGovernor, CallRefused, GovernorLimits
from scripts.verification import vesum

ROOT = Path(__file__).resolve().parents[2]
QUIET = logging.getLogger("test.sources.supervision")
QUIET.addHandler(logging.NullHandler())
QUIET.propagate = False


class NotifyListener:
    """A fake systemd notify socket that timestamps every datagram."""

    def __init__(self, sock: socket.socket, env_value: str) -> None:
        self.sock = sock
        self.env_value = env_value
        self.messages: list[tuple[float, str]] = []
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()

    def _read(self) -> None:
        while True:
            try:
                data = self.sock.recv(4096)
            except OSError:
                return
            with self._lock:
                self.messages.append((time.monotonic(), data.decode()))

    def pings(self, since: float = 0.0) -> list[float]:
        with self._lock:
            return [at for at, text in self.messages if text == "WATCHDOG=1" and at >= since]

    def texts(self) -> list[str]:
        with self._lock:
            return [text for _at, text in self.messages]

    def wait_for(self, predicate, timeout: float = 10.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.02)
        raise AssertionError(f"timed out; messages so far: {self.texts()}")


@pytest.fixture
def abstract_listener() -> Iterator[NotifyListener]:
    name = f"lu-test-notify-{secrets.token_hex(6)}"
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.bind("\0" + name)
    try:
        yield NotifyListener(sock, "@" + name)
    finally:
        sock.close()


@contextlib.contextmanager
def serving_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    try:
        yield loop
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(5)
        loop.close()


def _target(listener: NotifyListener, usec: int | None = 400_000) -> sup.NotifyTarget:
    environ = {"NOTIFY_SOCKET": listener.env_value}
    if usec is not None:
        environ["WATCHDOG_USEC"] = str(usec)
    target = sup.notify_target(environ, os.getpid(), QUIET)
    assert target is not None
    return target


def _governor(**limits: float) -> CallGovernor:
    return CallGovernor(GovernorLimits(**limits), logger=QUIET)  # type: ignore[arg-type]


# --- protocol -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("environ", "expected"),
    [
        ({}, None),
        ({"NOTIFY_SOCKET": "/run/systemd/notify"}, sup.NotifyTarget("/run/systemd/notify", None)),
        ({"NOTIFY_SOCKET": "@abstract/name"}, sup.NotifyTarget("\0abstract/name", None)),
        ({"NOTIFY_SOCKET": "vsock:2:1234"}, None),
        ({"NOTIFY_SOCKET": "relative/path"}, None),
        ({"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "90000000"}, sup.NotifyTarget("\0n", 90_000_000)),
        (
            {"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "90000000", "WATCHDOG_PID": "4242"},
            sup.NotifyTarget("\0n", 90_000_000),
        ),
        ({"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "90000000", "WATCHDOG_PID": "4243"}, sup.NotifyTarget("\0n", None)),
        ({"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "90000000", "WATCHDOG_PID": "x"}, sup.NotifyTarget("\0n", None)),
        ({"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "0"}, sup.NotifyTarget("\0n", None)),
        ({"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "-5"}, sup.NotifyTarget("\0n", None)),
        ({"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "1e6"}, sup.NotifyTarget("\0n", None)),
        ({"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "١٢"}, sup.NotifyTarget("\0n", None)),
        ({"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": str(2**64 - 1)}, sup.NotifyTarget("\0n", None)),
    ],
)
def test_notify_settings_are_validated(environ: dict[str, str], expected: sup.NotifyTarget | None) -> None:
    assert sup.notify_target(environ, 4242, QUIET) == expected


def test_settings_are_removed_from_the_environment_for_child_processes() -> None:
    environ = {"NOTIFY_SOCKET": "@n", "WATCHDOG_USEC": "1000", "WATCHDOG_PID": "7", "OTHER": "kept"}
    assert sup.take_notify_target(environ, pid=7, logger=QUIET) == sup.NotifyTarget("\0n", 1000)
    assert environ == {"OTHER": "kept"}


def test_everything_is_off_outside_systemd() -> None:
    environ = {"PATH": "/usr/bin"}

    async def start() -> sup.HealthPinger | None:
        return sup.start_supervision(object(), object(), environ=environ, logger=QUIET)

    assert asyncio.run(start()) is None
    assert not any(thread.name == "sources-watchdog-pinger" for thread in threading.enumerate())


def test_notifier_sends_to_a_path_socket() -> None:
    directory = tempfile.mkdtemp(prefix="n")  # short: AF_UNIX paths stop at 108 bytes
    path = os.path.join(directory, "notify")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.bind(path)
        sock.settimeout(5)
        notifier = sup.Notifier(sup.NotifyTarget(path, None), QUIET)
        assert notifier.send("READY=1")
        assert sock.recv(64) == b"READY=1"
    finally:
        sock.close()
        with contextlib.suppress(OSError):
            os.unlink(path)
        os.rmdir(directory)


def test_a_missing_socket_is_logged_not_raised() -> None:
    notifier = sup.Notifier(sup.NotifyTarget("\0lu-test-nobody-" + secrets.token_hex(6), None), QUIET)
    assert notifier.send("WATCHDOG=1") is False


# --- readiness and pings --------------------------------------------------------


def test_ready_waits_for_the_listener_and_a_probe_then_pings_follow(abstract_listener: NotifyListener) -> None:
    listening = threading.Event()
    order: list[str] = []
    with serving_loop() as loop:
        pinger = sup.HealthPinger(
            sup.Notifier(_target(abstract_listener), QUIET),
            loop,
            _governor(max_concurrent=2, queue_timeout=1, call_timeout=1),
            ready=listening.is_set,
            operation=lambda: order.append("probe"),
            logger=QUIET,
            on_ready=lambda: order.append("on_ready"),
        ).start()
        try:
            time.sleep(0.4)
            assert abstract_listener.texts() == []
            assert order == []
            listening.set()
            abstract_listener.wait_for(lambda: len(abstract_listener.pings()) >= 3)
        finally:
            pinger.stop()
    texts = abstract_listener.texts()
    assert texts[0] == "READY=1"
    assert set(texts[1:]) == {"WATCHDOG=1"}
    assert order[:2] == ["probe", "on_ready"]


def test_without_a_watchdog_only_ready_is_sent(abstract_listener: NotifyListener) -> None:
    with serving_loop() as loop:
        pinger = sup.HealthPinger(
            sup.Notifier(_target(abstract_listener, usec=None), QUIET),
            loop,
            _governor(max_concurrent=2, queue_timeout=1, call_timeout=1),
            ready=lambda: True,
            operation=lambda: None,
            logger=QUIET,
        ).start()
        abstract_listener.wait_for(lambda: abstract_listener.texts() == ["READY=1"])
        pinger._thread.join(5)  # type: ignore[union-attr]
        assert not pinger._thread.is_alive()  # type: ignore[union-attr]
    assert abstract_listener.texts() == ["READY=1"]


def _pinging(
    listener: NotifyListener, loop: asyncio.AbstractEventLoop, governor: CallGovernor, operation
) -> sup.HealthPinger:
    pinger = sup.HealthPinger(
        sup.Notifier(_target(listener), QUIET), loop, governor, ready=lambda: True, operation=operation, logger=QUIET
    ).start()
    listener.wait_for(lambda: len(listener.pings()) >= 2)
    return pinger


def test_a_blocked_event_loop_stops_the_pings(abstract_listener: NotifyListener) -> None:
    """The probe runs on the serving loop: while it is blocked nothing is pinged."""
    with serving_loop() as loop:
        pinger = _pinging(
            abstract_listener, loop, _governor(max_concurrent=2, queue_timeout=1, call_timeout=1), lambda: None
        )
        try:
            blocked_at = time.monotonic()
            started_before = pinger.probes_started
            loop.call_soon_threadsafe(time.sleep, 1.5)
            time.sleep(1.4)
            # A probe that finished just before the block may still ping once.
            assert abstract_listener.pings(since=blocked_at + 0.3) == []
            assert pinger.probes_started - started_before <= 1
            abstract_listener.wait_for(lambda: abstract_listener.pings(since=blocked_at + 1.5))
        finally:
            pinger.stop()


def test_a_saturated_governor_stops_the_pings(abstract_listener: NotifyListener) -> None:
    """The probe enters the real governor: with every slot held by stuck work it is refused."""
    governor = _governor(max_concurrent=1, queue_timeout=0.5, call_timeout=0.1)
    release = threading.Event()

    async def stuck() -> None:
        await asyncio.to_thread(release.wait, 20)

    with serving_loop() as loop:
        pinger = _pinging(abstract_listener, loop, governor, lambda: None)
        try:
            with pytest.raises(CallRefused, match="call_timeout"):
                asyncio.run_coroutine_threadsafe(governor.run("stuck_tool", stuck), loop).result(5)
            saturated_at = time.monotonic()
            time.sleep(1.0)
            assert abstract_listener.pings(since=saturated_at + 0.3) == []
            released_at = time.monotonic()
            release.set()
            abstract_listener.wait_for(lambda: abstract_listener.pings(since=released_at))
        finally:
            release.set()
            pinger.stop()


def _vesum_db(path: Path) -> Path:
    with contextlib.closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.executemany(
            "INSERT INTO forms VALUES (?, ?, ?, ?)", [(f"w{i}", f"l{i % 97}", "noun", "") for i in range(5000)]
        )
        conn.execute("CREATE INDEX forms_word_form ON forms(word_form)")
        conn.commit()
    return path


def test_a_held_vesum_connection_lock_stops_the_pings_without_piling_up_probes(
    abstract_listener: NotifyListener, tmp_path: Path
) -> None:
    """The probe takes the VESUM connection lock every VESUM tool takes.

    While another thread holds it the probe misses its deadline, no ping is
    sent, and no second probe job starts; the stuck one finishes, and pings
    resume, once the lock is free.
    """
    db = _vesum_db(tmp_path / "vesum.db")
    entered = []

    def operation() -> None:
        entered.append(time.monotonic())
        sup.vesum_probe(db)

    try:
        with serving_loop() as loop:
            pinger = _pinging(
                abstract_listener, loop, _governor(max_concurrent=4, queue_timeout=1, call_timeout=30), operation
            )
            try:
                with vesum._CONN_LOCK:
                    held_at = time.monotonic()
                    jobs_before, probes_before = len(entered), pinger.probes_started
                    time.sleep(1.5)
                    assert abstract_listener.pings(since=held_at + 0.3) == []
                    assert len(entered) - jobs_before <= 1
                    assert pinger.probes_started - probes_before <= 1
                abstract_listener.wait_for(lambda: abstract_listener.pings(since=held_at + 1.5))
            finally:
                pinger.stop()
    finally:
        vesum.close_vesum_conn()


def test_a_missing_vesum_database_does_not_fail_the_probe(tmp_path: Path) -> None:
    sup.vesum_probe(tmp_path / "absent.db")


# --- the original deadlock, reproduced in a child process -----------------------------

DEADLOCK_CHILD = """\
import asyncio, faulthandler, functools, logging, random, sqlite3, sys, threading, time
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from scripts.rag.call_governor import CallGovernor, GovernorLimits
from scripts.rag.hang_diagnostics import arm_abort_dump
from scripts.rag.sources_supervision import HealthPinger, Notifier, take_notify_target, vesum_probe
from scripts.verification import vesum

db, mode, warmup = Path(sys.argv[2]), sys.argv[3], float(sys.argv[4])
# A deadlock freezes every Python thread; only a C-level timer can end it.
faulthandler.dump_traceback_later(60, exit=True)
arm_abort_dump()
quiet = logging.getLogger("child")
quiet.addHandler(logging.NullHandler())
quiet.propagate = False
loop = asyncio.new_event_loop()
threading.Thread(target=loop.run_forever, daemon=True).start()
governor = CallGovernor(GovernorLimits(max_concurrent=12, queue_timeout=5, call_timeout=30), logger=quiet)
target = take_notify_target(logger=quiet)
HealthPinger(
    Notifier(target, quiet), loop, governor, ready=lambda: True,
    operation=functools.partial(vesum_probe, db), logger=quiet,
).start()
time.sleep(warmup)
conn = vesum.get_vesum_conn(db)
if mode == "hold":
    # One long step holds SQLite's mutex on the shared connection for about
    # 4 s, with the GIL released: no Python callback, no deadlock.
    count = "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c WHERE x < ?) SELECT count(*) FROM c"
    began = time.monotonic()
    sqlite3.connect(":memory:").execute(count, (1_000_000,)).fetchone()
    rows = int(1_000_000 * 4.0 / max(time.monotonic() - began, 1e-3))
    Notifier(target, quiet).send("X-LOAD=1")
    conn.execute(count, (rows,)).fetchone()
    Notifier(target, quiet).send("X-DONE=1")
    time.sleep(60)
if mode == "bug":
    # open_readonly before the #10674 fix: a Python authorizer on the
    # connection every worker thread shares.
    conn.set_authorizer(lambda *args: sqlite3.SQLITE_OK)
Notifier(target, quiet).send("X-LOAD=1")

def reader(seed):
    rnd = random.Random(seed)
    while True:
        # A new IN-list width misses the statement cache, so SQLite prepares
        # again and calls the authorizer under its connection mutex.
        vesum.verify_words([f"w{rnd.randint(0, 5000)}" for _ in range(rnd.randint(1, 200))], db_path=db)

for seed in range(8):
    threading.Thread(target=reader, args=(seed,), daemon=True).start()
time.sleep(60)
"""


def _run_deadlock_child(
    listener: NotifyListener, tmp_path: Path, mode: str, *, watch_s: float
) -> tuple[subprocess.Popen[bytes], float, Path]:
    db = _vesum_db(tmp_path / "vesum.db")
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    env = {
        **{key: value for key, value in os.environ.items() if key not in sup.NOTIFY_ENV},
        "NOTIFY_SOCKET": listener.env_value,
        "WATCHDOG_USEC": "2000000",
        "STATE_DIRECTORY": str(state),
    }
    child = subprocess.Popen(
        [sys.executable, "-c", DEADLOCK_CHILD, str(ROOT), str(db), mode, "2"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    listener.wait_for(lambda: "X-LOAD=1" in listener.texts(), timeout=30)
    load_at = next(at for at, text in listener.messages if text == "X-LOAD=1")
    time.sleep(max(0.0, load_at + watch_s - time.monotonic()))
    return child, load_at, state


def test_the_original_shared_connection_deadlock_stops_the_pings_and_sigabrt_dumps_it(
    abstract_listener: NotifyListener, tmp_path: Path
) -> None:
    """#10674's hang: a Python callback on the shared VESUM connection.

    Pings flow until the readers start, then stop for good. The watchdog's
    SIGABRT then writes every thread's stack and ends the process.
    """
    child, load_at, state = _run_deadlock_child(abstract_listener, tmp_path, "bug", watch_s=4.0)
    try:
        assert len(abstract_listener.pings()) >= 2, abstract_listener.texts()
        assert child.poll() is None
        # The 2 s watchdog gives a 1 s probe deadline: a probe already in
        # flight when the load starts may still ping inside it, none after.
        assert abstract_listener.pings(since=load_at + 1.5) == []
        child.send_signal(signal.SIGABRT)
        assert child.wait(20) == -signal.SIGABRT
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(10)
        child.stderr.close()  # type: ignore[union-attr]
    dumps = sorted(state.glob("abort-*.txt"))
    assert len(dumps) == 1
    text = dumps[0].read_text(encoding="utf-8")
    # Every thread, frozen where the deadlock caught it: the main thread, the
    # loop, the pinger and at least one reader inside verify_words.
    assert text.startswith("Fatal Python error: Aborted")
    assert text.count("Thread 0x") >= 4, text[:2000]
    assert "in verify_words" in text and "in reader" in text
    assert oct(dumps[0].stat().st_mode & 0o777) == "0o600"


def test_a_held_sqlite_connection_mutex_stops_the_pings(abstract_listener: NotifyListener, tmp_path: Path) -> None:
    """The probe's query waits for SQLite's mutex on the shared VESUM connection.

    While another thread holds it no ping is sent; pings resume when it is
    released. A probe that only took the Python-level connection lock, or ran
    an unrelated query, would keep pinging here.
    """
    child, load_at, _state = _run_deadlock_child(abstract_listener, tmp_path, "hold", watch_s=0.0)
    try:
        abstract_listener.wait_for(lambda: "X-DONE=1" in abstract_listener.texts(), timeout=60)
        done_at = next(at for at, text in abstract_listener.messages if text == "X-DONE=1")
        assert done_at - load_at >= 2.5, "the mutex was not held long enough to judge"
        assert [at for at in abstract_listener.pings(since=load_at + 1.5) if at < done_at] == []
        abstract_listener.wait_for(lambda: abstract_listener.pings(since=done_at))
    finally:
        child.kill()
        child.wait(10)
        child.stderr.close()  # type: ignore[union-attr]


def test_the_same_load_without_the_callback_keeps_pinging(abstract_listener: NotifyListener, tmp_path: Path) -> None:
    """Control: the readers alone do not stop the pings; the deadlock does."""
    child, load_at, _state = _run_deadlock_child(abstract_listener, tmp_path, "fixed", watch_s=4.0)
    try:
        assert len(abstract_listener.pings(since=load_at + 1.5)) >= 3, abstract_listener.texts()
        assert child.poll() is None
    finally:
        child.kill()
        child.wait(10)
        child.stderr.close()  # type: ignore[union-attr]


# --- the unit's narrow view under ProtectHome=tmpfs --------------------------------------


def _fake_checkout(root: Path, base_bin: Path, *, data: Path | None = None) -> Path:
    """A checkout whose virtual environment's interpreter links to a base installation."""
    base_bin.mkdir(parents=True)
    (base_bin / "python3.12").touch()
    (base_bin.parent / "lib" / "python3.12").mkdir(parents=True)
    (root / ".venv" / "bin").mkdir(parents=True)
    (root / ".venv" / "bin" / "python").symlink_to(base_bin / "python3.12")
    (root / ".venv" / "pyvenv.cfg").write_text(f"home = {base_bin}\nversion_info = 3.12.14\n", encoding="utf-8")
    if data is None:
        data = root / "data"
    else:
        (root / "data").symlink_to(data)
    data.mkdir(parents=True, exist_ok=True)
    for name in sup.DATABASES:
        (data / name).touch()
    return root


@pytest.fixture
def hidden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setattr(sup, "PROTECT_HOME_HIDDEN", (home, tmp_path / "root", tmp_path / "run" / "user"))
    return home


def test_a_checkout_in_a_home_directory_is_bound_back_narrowly(hidden: Path, capsys) -> None:
    """The live layout: checkout and managed interpreter both inside one home directory."""
    repo = _fake_checkout(hidden / "op" / "repo", hidden / "op" / ".local" / "python" / "cpython-3.12" / "bin")
    paths, needed = sup.resolve_unit_paths(repo)
    assert paths == sup.UnitPaths(
        repo_root=repo,
        venv_root=repo / ".venv",
        python_root=hidden / "op" / ".local" / "python" / "cpython-3.12",
        data_root=repo / "data",
    )
    coverage = {label: sup.bind_coverage(path, writable, paths) for label, path, writable in needed}
    assert coverage == {
        "checkout": "BindReadOnlyPaths=",
        "virtual environment": "BindReadOnlyPaths=",
        "interpreter": "BindReadOnlyPaths=",
        "standard library": "BindReadOnlyPaths=",
        "data": "BindPaths=",
        "sources.db directory": "BindPaths=",
        "vesum.db directory": "BindPaths=",
    }
    assert sup.broad_binds(paths) == []
    assert sup.main(["check-paths", "--repo-root", str(repo)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert sum(line.startswith("ok: ") for line in out) == 8  # every needed path is printed
    assert f"@PYTHON_ROOT@={paths.python_root}" in out and f"@DATA_ROOT@={repo / 'data'}" in out


def test_a_checkout_outside_the_home_trees_still_gets_a_writable_data_directory(tmp_path: Path, hidden: Path) -> None:
    repo = _fake_checkout(tmp_path / "srv" / "repo", tmp_path / "usr" / "bin")
    paths, needed = sup.resolve_unit_paths(repo)
    assert paths.python_root == tmp_path / "usr"
    assert {label: sup.bind_coverage(path, writable, paths) for label, path, writable in needed}["data"] == "BindPaths="
    assert sup.main(["check-paths", "--repo-root", str(repo)]) == 0


def test_a_data_directory_elsewhere_is_bound_where_it_resolves(tmp_path: Path, hidden: Path) -> None:
    repo = _fake_checkout(hidden / "op" / "repo", hidden / "op" / "py" / "bin", data=tmp_path / "volume" / "data")
    paths, _needed = sup.resolve_unit_paths(repo)
    assert paths.data_root == tmp_path / "volume" / "data"
    assert sup.main(["check-paths", "--repo-root", str(repo)]) == 0


def test_a_writable_path_outside_the_data_bind_is_reported_hidden(hidden: Path, capsys) -> None:
    """A database linked out of the data directory would be read-only under ProtectSystem=strict."""
    repo = _fake_checkout(hidden / "op" / "repo", hidden / "op" / "py" / "bin")
    elsewhere = hidden / "op" / "bulk"
    elsewhere.mkdir()
    (elsewhere / "sources.db").touch()
    (repo / "data" / "sources.db").unlink()
    (repo / "data" / "sources.db").symlink_to(elsewhere / "sources.db")
    assert sup.main(["check-paths", "--repo-root", str(repo)]) == 1
    assert f"HIDDEN: sources.db directory {elsewhere} (writable, not exposed)" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("layout", "placeholder"),
    [
        ("interpreter_is_a_whole_home", "@PYTHON_ROOT@"),
        ("data_is_the_checkout", "@DATA_ROOT@"),
        ("checkout_is_a_whole_home", "@REPO_ROOT@"),
    ],
)
def test_a_bind_broader_than_the_unit_needs_is_refused(hidden: Path, layout: str, placeholder: str, capsys) -> None:
    if layout == "interpreter_is_a_whole_home":
        repo = _fake_checkout(hidden / "op" / "repo", hidden / "op" / "bin")  # bind would be the home directory
    elif layout == "data_is_the_checkout":
        repo = _fake_checkout(hidden / "op" / "repo", hidden / "op" / "py" / "bin", data=hidden / "op" / "repo-data")
        (repo / "data").unlink()
        (repo / "data").symlink_to(repo)
        for name in sup.DATABASES:
            (repo / name).touch()
    else:
        repo = _fake_checkout(hidden / "op", hidden / "other" / "py" / "bin")
    assert sup.main(["check-paths", "--repo-root", str(repo)]) == 1
    assert any(line.startswith(f"BROAD: {placeholder} ") for line in capsys.readouterr().out.splitlines()), placeholder


def test_a_missing_dependency_is_reported(hidden: Path, capsys) -> None:
    repo = _fake_checkout(hidden / "op" / "repo", hidden / "op" / "py" / "bin")
    (repo / "data" / "vesum.db").unlink()
    assert sup.main(["check-paths", "--repo-root", str(repo)]) == 1
    assert capsys.readouterr().out.startswith("error: a path the unit needs is missing")


def test_render_fills_every_placeholder_and_refuses_after_a_failed_check(hidden: Path, capsys) -> None:
    repo = _fake_checkout(hidden / "op" / "repo", hidden / "op" / "py" / "bin")
    template = Path(__file__).resolve().parents[2] / "packaging" / "systemd" / "learn-ukrainian-sources.service"
    assert sup.main(["render", "--repo-root", str(repo), str(template)]) == 0
    rendered = capsys.readouterr().out
    assert "@" not in rendered.replace("~@debug", "")
    assert f"BindReadOnlyPaths={repo}\n" in rendered and f"BindPaths={repo / 'data'}\n" in rendered
    paths, _needed = sup.resolve_unit_paths(repo)
    with pytest.raises(sup.PathCheckError, match="@UNKNOWN@"):
        sup.render_unit("ExecStart=@REPO_ROOT@/x @UNKNOWN@\n", paths)
    (repo / "data" / "sources.db").unlink()
    assert sup.main(["render", "--repo-root", str(repo), str(template)]) == 1
    assert capsys.readouterr().out == ""
