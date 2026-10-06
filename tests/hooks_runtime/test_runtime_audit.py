"""Runtime process-start audit for deployed hook entry points (#9807).

The child interpreter installs a PEP 578 audit hook before the entry executes.
A shell syntax check, a git or gh argv outside the reviewed templates, or a
hook-controlled configuration, pager, editor, askpass, or browser value fails
the run. Templates and launch explanations are fixtures, not exemptions.
"""

from __future__ import annotations

import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from tests.hooks_runtime.adapter import EntryReceipt, run_entry
from tests.hooks_runtime.conftest import REPORT
from tests.hooks_runtime.inventory import (
    CLASSIFICATION,
    COMMAND_PROCESSING,
    command_processing_paths,
    denominator_text,
    excluded_surfaces,
    hook_root_files,
    unclassified,
)
from tests.hooks_runtime.policy import (
    ObservedStart,
    classify_start,
    is_command_variable,
    load_explanations,
    load_templates,
    matches_template,
)
from tests.hooks_runtime.probes.cases import DESCENDANT_ARGV
from tests.test_guard_benign_corpus import _literal_corpus
from tests.test_hook_single_parser import REPO_ROOT

PROBE = Path(__file__).resolve().parent / "probes" / "cases.py"
_COMMAND_VARIABLES = (
    "BROWSER",
    "EDITOR",
    "GH_BROWSER",
    "GH_EDITOR",
    "GH_PAGER",
    "GIT_ASKPASS",
    "GIT_CONFIG_COUNT",
    "GIT_EDITOR",
    "GIT_EXTERNAL_DIFF",
    "GIT_PAGER",
    "GIT_SEQUENCE_EDITOR",
    "GIT_SSH",
    "GIT_SSH_COMMAND",
    "PAGER",
    "SSH_ASKPASS",
    "SSH_ASKPASS_REQUIRE",
    "VISUAL",
)


def _work(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.mkdir()
    return path


def _run(tmp_path: Path, case: str, **kwargs) -> EntryReceipt:
    extra = {"HOOK_RUNTIME_CASE": case}
    extra.update(kwargs.pop("extra_env", {}))
    name = kwargs.pop("name", case)
    return run_entry(
        PROBE,
        [case],
        cwd=_work(tmp_path, name),
        timeout=kwargs.pop("timeout", 20),
        extra_env=extra,
        allow_argv=kwargs.pop("allow_argv", None),
    )


def _text(receipt: EntryReceipt, cwd: Path | None = None) -> str:
    rendered = "\n".join(receipt.violations)
    if cwd is not None:
        rendered = rendered.replace(str(cwd), "<cwd>")
    return rendered


def _assert_blocked(receipt: EntryReceipt, *needles: str, cwd: Path | None = None) -> None:
    assert receipt.canary, receipt.driver_error or "missing canary"
    assert not receipt.timed_out
    assert not receipt.driver_error, receipt.driver_error
    assert not receipt.pair_errors, receipt.pair_errors
    rendered = _text(receipt, cwd)
    for needle in needles:
        assert needle in rendered, rendered
    assert not receipt.passed


def test_hook_roots_are_classified_once() -> None:
    on_disk = hook_root_files()
    assert unclassified() == ()
    assert set(on_disk) == set(CLASSIFICATION)
    assert len(on_disk) == len(CLASSIFICATION)
    driven = command_processing_paths()
    assert len(driven) == 8
    assert all(CLASSIFICATION[path] == COMMAND_PROCESSING for path in driven)


def test_templates_and_explanations_are_fixtures_not_exemptions(monkeypatch: pytest.MonkeyPatch) -> None:
    templates = load_templates()
    assert [name for name, _parts in templates] == ["git", "git", "git", "git", "git", "gh", "gh"]
    explanations = load_explanations()
    assert len(explanations) == 50
    assert all(item.get("explanation") for item in explanations)

    def boom() -> tuple[dict[str, str], ...]:
        raise AssertionError("launch explanations were consulted")

    monkeypatch.setattr("tests.hooks_runtime.policy.load_explanations", boom)
    start = ObservedStart(
        event="subprocess.Popen",
        pid=1,
        parent_pid=1,
        pair_index=0,
        executable="git",
        argv=("git", "-C", "<cwd>", "status"),
        explicit_env=None,
        inherited_dangerous={},
    )
    assert "unclassified-argv" in classify_start(start)
    assert matches_template(("gh", "api", "user"))
    assert not matches_template(("gh", "api", "--paginate"))
    assert not matches_template(("git", "-c", "core.pager=less", "rev-parse", "--git-dir"))
    assert not matches_template(("git", "-cname=value", "status"))
    assert not matches_template(("git", "--config-env", "foo=BAR", "status"))
    for name in _COMMAND_VARIABLES:
        assert is_command_variable(name), name
    assert not is_command_variable("NO_COLOR")
    assert not is_command_variable("CLICOLOR")


def test_second_level_helper_is_rejected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "second_level")
    _assert_blocked(receipt, "unclassified-argv", "config-injection:", "alias.x=!bash -n bad.sh")


def test_runner_passed_as_a_value_is_rejected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "value_runner")
    _assert_blocked(receipt, "syntax-check:bash -n")


def test_explicit_pager_is_rejected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "explicit_pager")
    _assert_blocked(receipt, "env-injection:GH_PAGER")


def test_inherited_pager_is_rejected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "inherited_pager", extra_env={"GH_FORCE_TTY": "1", "PAGER": "cat"})
    _assert_blocked(receipt, "env-injection:PAGER")
    assert "GH_FORCE_TTY" not in _text(receipt)


def test_launch_replacement_does_not_inherit_a_template(tmp_path: Path) -> None:
    keyword = _run(tmp_path, "launch_keyword")
    _assert_blocked(keyword, "launch-replacement")
    assert "unclassified-argv" not in _text(keyword)
    positional = _run(tmp_path, "launch_positional")
    _assert_blocked(positional, "launch-replacement", "unclassified-argv")


@pytest.mark.parametrize(
    ("case", "detail"),
    [
        ("asyncio_exec", "syntax-check:bash -n"),
        ("bytes_argv", "syntax-check:bash -xn"),
        ("os_system", "syntax-check:bash -n"),
        ("posix_spawn", "syntax-check:bash -n"),
        ("os_exec", "syntax-check:bash --noexec"),
    ],
)
def test_process_channels_reject_syntax_checks(tmp_path: Path, case: str, detail: str) -> None:
    _assert_blocked(_run(tmp_path, case), detail)


def test_overlapping_starts_are_both_recorded(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "concurrent_starts", extra_env={"HOOK_RUNTIME_HOLD_HOOK": "1"})
    assert receipt.canary and not receipt.pair_errors, receipt.driver_error or receipt.pair_errors
    recorded = {event.argv for event in receipt.events}
    assert ("__concurrent_a__", "intercept") in recorded
    assert ("__concurrent_b__", "intercept") in recorded


def test_swallowed_exception_still_records_the_violation(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "swallow")
    _assert_blocked(receipt, "syntax-check:bash -n")


def test_command_variables_and_config_forms_are_rejected(tmp_path: Path) -> None:
    env_receipt = _run(tmp_path, "command_env")
    rendered = _text(env_receipt)
    _assert_blocked(env_receipt, "env-injection:")
    for name in _COMMAND_VARIABLES:
        assert name in rendered, rendered
    assert "NO_COLOR" not in rendered
    assert "CLICOLOR" not in rendered
    shapes = _run(tmp_path, "config_shapes")
    _assert_blocked(shapes, "config-injection:-c", "config-injection:-cname=value", "config-injection:--config-env")
    assert "gh api --paginate" in _text(shapes)


def test_fork_child_exec_is_collected(tmp_path: Path) -> None:
    receipt = _run(tmp_path, "fork_child")
    assert receipt.canary and receipt.passed, _text(receipt) or receipt.driver_error or receipt.pair_errors
    collected = [
        event
        for event in receipt.events
        if event.event == "os.exec" and event.child_of_fork and event.argv[:1] == ("/bin/echo",)
    ]
    assert collected


def test_descendant_beyond_the_shell_is_unobserved(tmp_path: Path) -> None:
    work = _work(tmp_path, "descendant")
    receipt = run_entry(
        PROBE,
        ["descendant"],
        cwd=work,
        timeout=20,
        extra_env={"HOOK_RUNTIME_CASE": "descendant"},
        allow_argv=DESCENDANT_ARGV,
    )
    assert receipt.canary and receipt.passed, _text(receipt) or receipt.driver_error or receipt.pair_errors
    assert (work / "descendant-marker").read_text(encoding="utf-8").strip() == "UNOBSERVED_CHILD"
    assert any(event.argv == DESCENDANT_ARGV for event in receipt.events)
    assert not any(event.argv and event.argv[0].endswith("echo") for event in receipt.events)


def test_missing_canary_missing_receipt_crash_and_timeout_fail(tmp_path: Path) -> None:
    quiet = _run(tmp_path, "noop", name="skip-canary", extra_env={"HOOK_RUNTIME_SKIP_CANARY": "1"})
    assert quiet.driver_error == "missing-canary"
    assert not quiet.passed
    omitted = _run(tmp_path, "noop", name="omit-summary", extra_env={"HOOK_RUNTIME_OMIT_SUMMARY": "1"})
    assert omitted.driver_error == "missing-receipt"
    assert omitted.canary
    assert not omitted.passed
    crashed = _run(tmp_path, "crash")
    assert crashed.pair_errors and "RuntimeError" in crashed.pair_errors[0]
    assert crashed.canary and not crashed.passed
    timed = _run(tmp_path, "sleeper", timeout=1)
    assert timed.timed_out and timed.driver_error == "timeout"
    assert not timed.passed


def _redact(text: str, cwd: Path) -> str:
    redacted = text.replace(str(cwd), "<cwd>")
    tmp = os.environ.get("TMPDIR", "").rstrip("/")
    if tmp:
        redacted = redacted.replace(tmp, "<tmpdir>")
    return redacted


def _shapes(receipt: EntryReceipt, cwd: Path) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter(_redact(item, cwd) for item in receipt.violations)
    return counter.most_common(12)


def test_command_processing_corpus_rejects_unreviewed_starts(tmp_path: Path) -> None:
    """Drive every command-processing entry through the benign-command corpus."""
    corpus = _literal_corpus()
    rows: list[tuple[str, int, int, int, str]] = []
    details: list[str] = []

    def one(relative: str) -> tuple[str, EntryReceipt, Path]:
        work = _work(tmp_path, Path(relative).name)
        receipt = run_entry(REPO_ROOT / relative, corpus, cwd=work, timeout=90)
        return relative, receipt, work

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, command_processing_paths()))
    for relative, receipt, work in results:
        if receipt.passed:
            status = "pass"
        elif receipt.driver_error or receipt.pair_errors:
            status = receipt.driver_error or "pair-error"
        else:
            status = "violations"
        rows.append((relative, len(corpus), receipt.pairs_completed, len(receipt.violations), status))
        if not receipt.passed:
            shown = [f"{count} {shape}" for shape, count in _shapes(receipt, work)]
            problems = "; ".join(receipt.pair_errors[:3])
            details.append(f"{Path(relative).name}: {receipt.driver_error} {problems}\n" + "\n".join(shown))
    text = denominator_text(rows=rows)
    REPORT.write_text(text + "\n", encoding="utf-8")
    assert not details, text + "\n" + "\n".join(details)
    assert excluded_surfaces()
