"""Keep coverage's data storage outside import-smoke audit enforcement.

Installed only in the disposable coverage-ref runner interpreter. The source
write/network/process guards still run for all operations of measured code.
Coverage 7.16.2 uses sqlite3.connect and os.remove when saving subprocess data:
https://coverage.readthedocs.io/en/7.16.2/subprocess.html
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import sysconfig
from pathlib import Path


def install() -> None:
    """Exempt only coverage's own storage calls on this run's data files."""
    data_file = os.environ.get("COVERAGE_FILE")
    if not data_file or not os.path.isabs(data_file) or getattr(sys.addaudithook, "coverage_ref", False):
        return
    import coverage.sqldata
    import coverage.sqlitedb

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
