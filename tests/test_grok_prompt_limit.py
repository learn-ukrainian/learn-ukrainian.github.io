"""Grok prompt delivery stays under Linux MAX_ARG_STRLEN (#10522).

The kernel rejects one argv element at 131072 bytes (the count includes the
terminating NUL). These tests pin both the ordinary and isolated-review
paths: oversized prompts, in bytes, go through a private ``--prompt-file``.
"""

from __future__ import annotations

import stat
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.grok_build import GrokBuildAdapter

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
    with (
        patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK),
        patch.dict("os.environ", {"TMPDIR": str(tmp_path)}),
    ):
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


def _isolated(prompt: str, tmp_path: Path):
    review_root = tmp_path / "review"
    for child in ("tmp", "home", "exec"):
        (review_root / child).mkdir(parents=True)
    tool_config = {
        "review_isolation": True,
        "review_engine_binary": "/usr/bin/true",
    }
    with patch(
        "scripts.review.isolation.validated_review_write_root",
        return_value=review_root,
    ):
        return _build(prompt, tmp_path, mode="read-only", tool_config=tool_config), review_root


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
