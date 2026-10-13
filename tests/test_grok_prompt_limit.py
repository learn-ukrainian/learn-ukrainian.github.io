"""Grok prompt delivery stays under Linux MAX_ARG_STRLEN (#10522).

The kernel rejects one argv element at 131072 bytes (the count includes the
terminating NUL). These tests pin both the ordinary and isolated-review
paths: oversized prompts, in bytes, go through a private ``--prompt-file``.
"""

from __future__ import annotations

import stat
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.grok_build import (
    _ISOLATED_PROMPT_FILENAME,
    _PROMPT_FILE_SUFFIX,
    GrokBuildAdapter,
)

FAKE_GROK = "/usr/local/bin/grok"
# Linux MAX_ARG_STRLEN. strnlen_user counts the NUL, so 131072 bytes of text
# cannot be exec'd. An argv element must stay strictly below this.
_MAX_ARG_STRLEN = 131_072
_CYRILLIC = "а"  # U+0430, two UTF-8 bytes


def _inline_limit() -> int:
    from agent_runtime.adapters import grok_build

    limit = getattr(grok_build, "_INLINE_PROMPT_LIMIT_BYTES", None)
    if not isinstance(limit, int):
        raise AssertionError("grok_build._INLINE_PROMPT_LIMIT_BYTES is missing")
    return limit


def _build(prompt: str, tmp_path: Path, **kw):
    mode = kw.pop("mode", "read-only")
    tool_config = kw.pop("tool_config", None)
    previous_tempdir = tempfile.tempdir
    try:
        with (
            patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK),
            patch.dict("os.environ", {"TMPDIR": str(tmp_path)}),
        ):
            # NamedTemporaryFile caches the first temp directory it sees.
            # Drop that cache so this call honors the tmp_path TMPDIR.
            tempfile.tempdir = None
            return GrokBuildAdapter().build_invocation(
                prompt=prompt,
                mode=mode,
                cwd=tmp_path,
                model=kw.pop("model", None),
                task_id=kw.pop("task_id", None),
                session_id=kw.pop("session_id", None),
                tool_config=tool_config,
                effort=kw.pop("effort", None),
            )
    finally:
        tempfile.tempdir = previous_tempdir


def _isolated(prompt: str, tmp_path: Path, **kw):
    review_root = tmp_path / "review"
    for child in ("tmp", "home", "exec"):
        (review_root / child).mkdir(parents=True)
    extra = kw.pop("tool_config", None) or {}
    tool_config = {
        "review_isolation": True,
        "review_engine_binary": "/usr/bin/true",
        **extra,
    }
    with patch(
        "scripts.review.isolation.validated_review_write_root",
        return_value=review_root,
    ):
        return _build(prompt, tmp_path, mode="read-only", tool_config=tool_config, **kw), review_root


def _prompt_file(plan) -> Path:
    inline_sizes = [
        len(plan.cmd[index + 1].encode("utf-8"))
        for index, item in enumerate(plan.cmd)
        if item == "-p" and index + 1 < len(plan.cmd)
    ]
    if inline_sizes:
        raise AssertionError(f"prompt was passed inline with -p; element sizes {inline_sizes}")
    paths = [plan.cmd[index + 1] for index, item in enumerate(plan.cmd) if item == "--prompt-file"]
    if len(paths) != 1:
        raise AssertionError(f"expected one --prompt-file, found {len(paths)}")
    return Path(paths[0])


def _assert_prompt_file(plan, prompt: str) -> Path:
    path = _prompt_file(plan)
    got = path.read_bytes()
    expected = prompt.encode("utf-8")
    if got != expected:
        raise AssertionError(f"prompt file has {len(got)} bytes, prompt has {len(expected)}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        raise AssertionError(f"prompt file mode is {mode:04o}, expected 0600")
    oversized = [
        len(element.encode("utf-8")) for element in plan.cmd if len(element.encode("utf-8")) >= _MAX_ARG_STRLEN
    ]
    if oversized:
        raise AssertionError(f"oversized argv element sizes: {oversized}")
    return path


def _assert_removed(plan, path: Path) -> None:
    try:
        GrokBuildAdapter().cleanup_invocation(plan)
        if path.exists():
            raise AssertionError(f"prompt file was not removed: {path.name}")
    finally:
        path.unlink(missing_ok=True)


def test_ascii_200_kib_ordinary_uses_private_prompt_file(tmp_path: Path) -> None:
    prompt = "a" * (200 * 1024)
    assert len(prompt.encode("utf-8")) > _MAX_ARG_STRLEN
    plan = _build(prompt, tmp_path)
    path = _assert_prompt_file(plan, prompt)
    _assert_removed(plan, path)


def test_cyrillic_70k_chars_ordinary_uses_private_prompt_file(tmp_path: Path) -> None:
    prompt = _CYRILLIC * 70_000
    encoded = len(prompt.encode("utf-8"))
    assert len(prompt) == 70_000
    assert len(prompt) < 100_000
    assert encoded > _MAX_ARG_STRLEN
    plan = _build(prompt, tmp_path)
    path = _assert_prompt_file(plan, prompt)
    _assert_removed(plan, path)


def test_ascii_200_kib_isolated_review_uses_private_prompt_file(tmp_path: Path) -> None:
    prompt = "b" * (200 * 1024)
    plan, review_root = _isolated(prompt, tmp_path)
    path = _assert_prompt_file(plan, prompt)
    if not path.is_relative_to(review_root):
        raise AssertionError(f"isolated prompt file {path.name} is outside the review write root")
    _assert_removed(plan, path)


def test_cyrillic_70k_chars_isolated_review_uses_private_prompt_file(tmp_path: Path) -> None:
    prompt = _CYRILLIC * 70_000
    plan, review_root = _isolated(prompt, tmp_path)
    path = _assert_prompt_file(plan, prompt)
    if not path.is_relative_to(review_root):
        raise AssertionError(f"isolated prompt file {path.name} is outside the review write root")
    _assert_removed(plan, path)


def test_prompt_exactly_at_inline_limit_stays_inline(tmp_path: Path) -> None:
    limit = _inline_limit()
    prompt = "c" * limit
    if len(prompt.encode("utf-8")) != limit:
        raise AssertionError("ASCII prompt byte length drifted from the inline limit")
    plan = _build(prompt, tmp_path)
    inline = [plan.cmd[index + 1] for index, item in enumerate(plan.cmd) if item == "-p"]
    if "--prompt-file" in plan.cmd or len(inline) != 1 or inline[0] != prompt:
        raise AssertionError(
            f"expected one inline -p of {limit} bytes; -p count={len(inline)} prompt-file={'--prompt-file' in plan.cmd}"
        )


def test_prompt_one_byte_over_inline_limit_uses_prompt_file(tmp_path: Path) -> None:
    prompt = "d" * (_inline_limit() + 1)
    plan = _build(prompt, tmp_path)
    path = _assert_prompt_file(plan, prompt)
    _assert_removed(plan, path)


def test_hyphen_leading_prompt_still_uses_private_prompt_file(tmp_path: Path) -> None:
    prompt = "--- context: shared\nfix it"
    if len(prompt.encode("utf-8")) >= _MAX_ARG_STRLEN:
        raise AssertionError("hyphen fixture is not a short prompt")
    plan = _build(prompt, tmp_path)
    path = _assert_prompt_file(plan, prompt)
    _assert_removed(plan, path)


def test_inline_limit_constant_is_under_the_kernel_ceiling() -> None:
    limit = _inline_limit()
    if not 0 < limit < _MAX_ARG_STRLEN:
        raise AssertionError(f"inline limit {limit} is not a margin under {_MAX_ARG_STRLEN}")


_OVERSIZED = "x" * 100_001
_EFFORT_ERROR = "native Grok CLI supports --effort values ['high', 'low', 'medium']; got 'invalid'"
_SCHEMA_ERROR = "output_schema_path must be a non-empty absolute path"
_SCHEMA_CONFIG = {
    "output_schema_path": "relative.json",
    "output_schema_sha256": "ab" * 32,
}
_GUARD_SUFFIXES = (".grok-reviewer-agent.md", ".grok-write-agent.md")


def _prompt_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and (path.name == _ISOLATED_PROMPT_FILENAME or path.name.endswith(_PROMPT_FILE_SUFFIX))
    ]


def _guard_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file() and path.name.endswith(_GUARD_SUFFIXES)]


def _expect(fn, exc_type: type[BaseException], message: str) -> None:
    try:
        fn()
    except exc_type as exc:
        if str(exc) != message or exc.__cause__ is not None:
            raise AssertionError(f"exception changed: {exc!r} cause={exc.__cause__!r}") from exc
    else:
        raise AssertionError(f"expected {exc_type.__name__}: {message}")


def _assert_no_prompt_files(root: Path) -> None:
    leaked = _prompt_files(root)
    if leaked:
        raise AssertionError(f"prompt files left behind: {[path.name for path in leaked]}")


@pytest.mark.parametrize(
    ("kind", "effort", "extra", "message"),
    [
        ("ordinary", "invalid", None, _EFFORT_ERROR),
        ("isolated", "invalid", None, _EFFORT_ERROR),
        ("ordinary", "high", _SCHEMA_CONFIG, _SCHEMA_ERROR),
        ("isolated", "high", _SCHEMA_CONFIG, _SCHEMA_ERROR),
        (
            "isolated",
            "high",
            {"review_deny_tools": "Bash"},
            "GrokBuildAdapter: review_deny_tools must be a list or tuple",
        ),
        (
            "isolated",
            "high",
            {"review_deny_tools": ["NotebookEdit"]},
            "GrokBuildAdapter: review_deny_tools contains unsupported Grok permission prefixes: ['NotebookEdit']",
        ),
        (
            "isolated",
            "high",
            {"review_deny_tools": ["Write", "Bash"]},
            "GrokBuildAdapter: review_deny_tools must retain fail-closed rules: ['Edit']",
        ),
    ],
)
def test_oversized_prompt_failure_leaves_no_prompt_file(
    tmp_path: Path, kind: str, effort: str, extra, message: str
) -> None:
    prompt = _OVERSIZED

    def invoke() -> None:
        if kind == "ordinary":
            _build(prompt, tmp_path, effort=effort, tool_config=extra)
        else:
            _isolated(prompt, tmp_path, effort=effort, tool_config=extra)

    _expect(invoke, ValueError, message)
    _assert_no_prompt_files(tmp_path)


def test_short_prompt_invalid_effort_leaves_no_prompt_file(tmp_path: Path) -> None:
    def invoke() -> None:
        _build("short", tmp_path, effort="invalid")

    _expect(invoke, ValueError, _EFFORT_ERROR)
    _assert_no_prompt_files(tmp_path)


def test_isolated_short_prompt_invalid_effort_leaves_no_prompt_file(tmp_path: Path) -> None:
    def invoke() -> None:
        _isolated("short", tmp_path, effort="invalid")

    _expect(invoke, ValueError, _EFFORT_ERROR)
    _assert_no_prompt_files(tmp_path)


def test_hyphen_prompt_invalid_effort_leaves_no_prompt_file(tmp_path: Path) -> None:
    def invoke() -> None:
        _build("--- context: shared\nfix it", tmp_path, effort="invalid")

    _expect(invoke, ValueError, _EFFORT_ERROR)
    _assert_no_prompt_files(tmp_path)


def test_write_mode_invalid_effort_leaves_no_guard_or_prompt_file(tmp_path: Path) -> None:
    def invoke() -> None:
        _build(_OVERSIZED, tmp_path, mode="workspace-write", effort="invalid")

    _expect(invoke, ValueError, _EFFORT_ERROR)
    _assert_no_prompt_files(tmp_path)
    guards = _guard_files(tmp_path)
    if guards:
        raise AssertionError(f"guard files left behind: {[path.name for path in guards]}")


def _raise_after_prompt_file(tmp_path: Path, fn) -> None:
    with patch.object(
        GrokBuildAdapter,
        "_reset_per_invocation_state",
        side_effect=RuntimeError("snapshot failed"),
    ):
        _expect(fn, RuntimeError, "snapshot failed")
    _assert_no_prompt_files(tmp_path)
    guards = _guard_files(tmp_path)
    if guards:
        raise AssertionError(f"guard files left behind: {[path.name for path in guards]}")


def test_exception_after_prompt_file_creation_removes_it(tmp_path: Path) -> None:
    _raise_after_prompt_file(tmp_path, lambda: _build(_OVERSIZED, tmp_path, effort="high"))


def test_isolated_exception_after_prompt_file_creation_removes_it(tmp_path: Path) -> None:
    _raise_after_prompt_file(tmp_path, lambda: _isolated(_OVERSIZED, tmp_path, effort="high"))


def test_write_mode_exception_after_files_are_created_removes_them(tmp_path: Path) -> None:
    _raise_after_prompt_file(
        tmp_path,
        lambda: _build(_OVERSIZED, tmp_path, mode="workspace-write", effort="high"),
    )
