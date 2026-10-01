"""Named-symlink layouts shared by the #9449 removal-route tests.

Each route test ignores ``ignored/`` in the checkout, builds one scenario,
names the returned path in the worker result and asserts the expectation:

* ``file_link``: ``ignored/link`` -> ignored ``ignored/report.bin`` (preserved);
* ``parent_link``: ``ignored/dir`` -> ``ignored/real`` (preserved);
* ``outbound``: ``ignored/link`` -> a file outside the checkout (refused);
* ``outbound_batch_state``: ``ignored/link`` -> primary ``batch_state`` (removed, no copy).
"""

from __future__ import annotations

from pathlib import Path

PAYLOAD = b"named report\x00\xff bytes"
SCENARIOS = ("file_link", "parent_link", "outbound", "outbound_batch_state")
REFUSAL = "links outside the checkout"


def build_named_link(worktree: Path, primary: Path, outside: Path, scenario: str) -> tuple[str, str | None, Path]:
    """Return the named path, the preserved relative path (or None) and the target file."""
    ignored = worktree / "ignored"
    ignored.mkdir(parents=True, exist_ok=True)
    if scenario == "file_link":
        target = ignored / "report.bin"
        target.write_bytes(PAYLOAD)
        (ignored / "link").symlink_to("report.bin")
        return "ignored/link", "ignored/report.bin", target
    if scenario == "parent_link":
        target = ignored / "real/report.bin"
        target.parent.mkdir()
        target.write_bytes(PAYLOAD)
        (ignored / "dir").symlink_to("real", target_is_directory=True)
        return "ignored/dir/report.bin", "ignored/real/report.bin", target
    if scenario == "outbound":
        target = outside / "report.bin"
    elif scenario == "outbound_batch_state":
        target = primary / "batch_state/shared/report.bin"
    else:
        raise ValueError(scenario)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(PAYLOAD)
    (ignored / "link").symlink_to(target)
    return "ignored/link", None, target
