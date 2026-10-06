"""Show the entry-point denominator even when pytest is quiet."""

from __future__ import annotations

import os
from pathlib import Path

REPORT = Path(os.environ.get("TMPDIR", ".")) / "impl-9807-n-denominator.txt"


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    del exitstatus, config
    if REPORT.is_file():
        terminalreporter.write_line(REPORT.read_text(encoding="utf-8"))
