"""Temporary #12310 diagnostics. Remove before the implementation review."""

from __future__ import annotations

import faulthandler
import json
import os
import sys
import threading
import time
import traceback
from pathlib import Path

import psutil
import pytest

DIRECTORY = Path("ci-artifacts/pytest-shard-12-diagnostics").resolve()
STOP = threading.Event()
THREAD = None
FATAL_STREAM = None


def counters():
    result = {}
    for name, path in {
        "meminfo": "/proc/meminfo",
        "vmstat": "/proc/vmstat",
        "cgroup_events": "/sys/fs/cgroup/memory.events",
        "cgroup_current": "/sys/fs/cgroup/memory.current",
        "cgroup_peak": "/sys/fs/cgroup/memory.peak",
        "cgroup_max": "/sys/fs/cgroup/memory.max",
    }.items():
        try:
            lines = Path(path).read_text().splitlines()
            result[name] = [line for line in lines if name not in {"meminfo", "vmstat"}
                            or line.startswith(("MemAvailable:", "MemTotal:", "SwapFree:", "oom_kill "))]
        except OSError:
            result[name] = "UNKNOWN"
    return result


def record(kind, **fields):
    try:
        DIRECTORY.mkdir(parents=True, exist_ok=True)
        row = {"event": kind, "time": time.time(), "monotonic": time.monotonic(),
               "pid": os.getpid(), "worker": os.environ.get("PYTEST_XDIST_WORKER", "controller"),
               **fields}
        with (DIRECTORY / f"events-{os.getpid()}.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
    except Exception:
        traceback.print_exc()


def sample():
    controller = psutil.Process()
    while not STOP.is_set():
        rows = []
        try:
            processes = [controller, *controller.children(recursive=True)]
        except psutil.Error:
            processes = []
        for process in processes:
            try:
                memory = process.memory_info()
                cpu = process.cpu_times()
                rows.append({"pid": process.pid, "ppid": process.ppid(), "name": process.name(),
                             "rss": memory.rss, "vms": memory.vms,
                             "cpu_seconds": cpu.user + cpu.system})
            except psutil.Error:
                continue
        record("sample", processes=rows, counters=counters())
        STOP.wait(1)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    global FATAL_STREAM
    import pytest_timeout

    DIRECTORY.mkdir(parents=True, exist_ok=True)
    FATAL_STREAM = (DIRECTORY / f"fatal-{os.getpid()}.log").open("a")
    # This registers fatal-signal output only. No native watchdog is armed.
    faulthandler.enable(file=FATAL_STREAM, all_threads=True)
    original_timer = pytest_timeout.timeout_timer

    def timer(item, settings):
        record("pytest_timeout", nodeid=item.nodeid, timeout=settings.timeout,
               counters=counters(), stacks={str(identity): traceback.format_stack(frame)
                                           for identity, frame in sys._current_frames().items()})
        return original_timer(item, settings)

    pytest_timeout.timeout_timer = timer
    record("configure", timeout=config.getoption("timeout"),
           timeout_method=config.getoption("timeout_method"),
           faulthandler_timeout=config.getini("faulthandler_timeout"), counters=counters())


def pytest_sessionstart(session):
    global THREAD
    if not hasattr(session.config, "workerinput"):
        THREAD = threading.Thread(target=sample, daemon=True)
        THREAD.start()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    record("start", nodeid=item.nodeid)
    try:
        yield
    finally:
        record("finish", nodeid=item.nodeid)


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error):
    process = getattr(getattr(node.gateway, "_io", None), "popen", None)
    record("worker_down", gateway=node.gateway.id, error=str(error),
           returncode=process.poll() if process is not None else "UNKNOWN", counters=counters())


def pytest_sessionfinish(session, exitstatus):
    STOP.set()
    if THREAD is not None:
        THREAD.join(timeout=2)
    record("session_finish", exitstatus=int(exitstatus), counters=counters())
