"""Isolate coverage storage and timed diagnostics in the measurement interpreter.

Installed only in the disposable coverage-ref runner interpreter. The source
write/network/process guards still run for all operations of measured code.
Coverage 7.16.2 uses sqlite3.connect and os.remove when saving subprocess data:
https://coverage.readthedocs.io/en/7.16.2/subprocess.html
"""

from __future__ import annotations

import argparse
import faulthandler
import math
import os
import shutil
import sys
import sysconfig
import threading
from pathlib import Path


class TracebackWatchdog:
    """Dump while holding the GIL, avoiding CPython's native watchdog race.

    The GIL-free dump_traceback_later walker can follow freed frames during
    covered ast.unparse (shard 13). Keep its timeout, repeat and cancellation
    behavior, but call dump_traceback from a Python thread with the GIL held.
    https://github.com/python/cpython/issues/140815
    """

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.timer: threading.Timer | None = None

    def cancel(self) -> None:
        """Wait out an active dump so callers can safely close its descriptor."""
        with self.lock:
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None

    def schedule(self, timeout, repeat=False, file=None, exit=False) -> None:
        """Replace the pending diagnostic without changing pytest's test deadline."""
        timeout = float(timeout)
        if not math.isfinite(timeout) or timeout > threading.TIMEOUT_MAX:
            raise OverflowError("timeout is too large")
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        stream = sys.stderr if file is None else file
        descriptor = stream if isinstance(stream, int) else stream.fileno()
        os.fstat(descriptor)

        def dump() -> None:
            with self.lock:
                if self.timer is not threading.current_thread():
                    return
                os.write(descriptor, f"Timeout ({timeout:g} seconds)!\n".encode())
                faulthandler.dump_traceback(file=descriptor, all_threads=True)
                if exit:
                    os._exit(1)
                self.timer = None
                if repeat:
                    self.schedule(timeout, repeat=True, file=descriptor, exit=exit)

        with self.lock:
            self.cancel()
            self.timer = threading.Timer(timeout, dump)
            self.timer.daemon = True
            self.timer.start()


def install() -> None:
    """Install measurement-only diagnostics and coverage storage exemptions."""
    data_file = os.environ.get("COVERAGE_FILE")
    if not data_file or not os.path.isabs(data_file) or getattr(sys.addaudithook, "coverage_ref", False):
        return
    import coverage.sqldata
    import coverage.sqlitedb

    watchdog = TracebackWatchdog()
    faulthandler.cancel_dump_traceback_later()
    faulthandler.dump_traceback_later = watchdog.schedule
    faulthandler.cancel_dump_traceback_later = watchdog.cancel
    os.register_at_fork(after_in_child=watchdog.__init__)

    storage_code = {coverage.sqldata.__file__, coverage.sqlitedb.__file__}
    data_path = Path(data_file).resolve()
    add_hook = sys.addaudithook

    def add_measurement_hook(hook):
        def measured_hook(event, args):
            if event in {"os.remove", "sqlite3.connect"} and args and isinstance(args[0], str):
                path = args[0]
                target = Path(path)
                if (path == data_file or path.startswith(data_file + ".")) and (
                    target.resolve().parent == data_path.parent
                    and (target.name == data_path.name or target.name.startswith(data_path.name + "."))
                ):
                    # coverage.misc.file_be_gone delegates os.remove; sqlite's
                    # connection event originates in coverage.sqlitedb.
                    frame = sys._getframe(1)
                    for _ in range(3):
                        if frame is None:
                            break
                        if frame.f_code.co_filename in storage_code:
                            return
                        frame = frame.f_back
            hook(event, args)

        add_hook(measured_hook)

    add_measurement_hook.coverage_ref = True
    sys.addaudithook = add_measurement_hook


def main(argv: list[str] | None = None) -> None:
    """Install startup handling in the workflow's disposable venv, never the source tree."""
    parser = argparse.ArgumentParser(
        description=(
            "Install coverage-ref subprocess storage isolation in this interpreter's site-packages.\n"
            "Use only in a disposable coverage-ref runner venv, never in a shared interpreter."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example: .venv/bin/python scripts/ci/coverage_ref_environment.py\n"
            "Outputs: coverage_ref_environment.py and .pth in the disposable runner venv.\n"
            "Exit codes: 0 = installed or help; 2 = usage error.\n"
            "Requires: a disposable coverage-ref interpreter; do not install in a shared venv.\n"
            "Related: .github/workflows/coverage-ref.yml; scripts/ci/coverage_ref.py."
        ),
    )
    parser.parse_args(argv)
    site = Path(sysconfig.get_paths()["purelib"])
    shutil.copyfile(__file__, site / "coverage_ref_environment.py")
    (site / "coverage_ref_environment.pth").write_text(
        "import coverage_ref_environment; coverage_ref_environment.install()\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
