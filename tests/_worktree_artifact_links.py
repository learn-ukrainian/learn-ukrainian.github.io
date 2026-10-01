"""Named-symlink layouts shared by the #9449 removal-route tests.

Each route test ignores ``ignored/`` in the checkout, builds one scenario,
names the returned path in the worker result and asserts the expectation:

* ``file_link``: ``ignored/link`` -> ignored ``ignored/report.bin`` (preserved);
* ``parent_link``: ``ignored/dir`` -> ``ignored/real`` (preserved);
* ``dotdot_after_link``: ``ignored/dir`` -> ``real/sub`` named as
  ``ignored/dir/../report.bin``, i.e. ``ignored/real/report.bin`` (preserved);
* ``outbound``: ``ignored/link`` -> a file outside the checkout (refused);
* ``outbound_batch_state``: ``ignored/link`` -> primary ``batch_state`` (removed, no copy);
* ``link_loop``, ``nul_name``, ``overlong_name``: unresolvable names (refused).

Refused scenarios map to the reason text in ``REFUSALS``; their target is
``None`` when no file exists behind the name.
"""

from __future__ import annotations

from pathlib import Path

PAYLOAD = b"named report\x00\xff bytes"
SCENARIOS = (
    "file_link",
    "parent_link",
    "dotdot_after_link",
    "outbound",
    "outbound_batch_state",
    "link_loop",
    "nul_name",
    "overlong_name",
)
REFUSAL = "links outside the checkout"
REFUSALS = {
    "outbound": REFUSAL,
    "link_loop": "cannot be resolved (symlink loop)",
    "nul_name": "cannot be resolved (embedded NUL)",
    "overlong_name": "cannot be resolved (name too long)",
}


def build_named_link(
    worktree: Path, primary: Path, outside: Path, scenario: str
) -> tuple[str, str | None, Path | None]:
    """Return the named path, the preserved relative path (or None) and the target file (or None)."""
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
    if scenario == "dotdot_after_link":
        target = ignored / "real/report.bin"
        (ignored / "real/sub").mkdir(parents=True)
        target.write_bytes(PAYLOAD)
        (ignored / "dir").symlink_to("real/sub", target_is_directory=True)
        return "ignored/dir/../report.bin", "ignored/real/report.bin", target
    if scenario == "link_loop":
        (ignored / "loop").symlink_to("loop")
        return "ignored/loop", None, None
    if scenario == "nul_name":
        return "ignored/report\x00.bin", None, None
    if scenario == "overlong_name":
        return "ignored/" + "x" * 300, None, None
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
