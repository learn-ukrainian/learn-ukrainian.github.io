"""Unit tests for the admin-merge guard hook (#M-0.5 / #1908).

Exercises the pure decision logic in
``agents_extensions/shared/hooks/guard-admin-merge.py``:

  * `gh pr merge ... --admin` detection (incl. wrappers + a positional PR number),
  * the quote-aware tokenizer (a `--admin` inside a quoted commit body is NOT a merge),
  * advisory-vs-blocking classification,
  * the fail-CLOSED `main()` decision (block on failing required check, on unknown PR,
    and on undeterminable check states; allow on green / advisory-only).

The hook filename has hyphens, so it is loaded by path via importlib. `main()` is guarded
by `__name__ == "__main__"`, so import has no side effects. Network functions
(`_pr_number`, `_failing_blocking_checks`) are monkeypatched — no `gh`/network in tests.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-admin-merge.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_admin_merge", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()


def _run(monkeypatch, command: str, *, pr: str | None = "5", failing=()) -> int:
    """Drive main() with a simulated stdin payload + monkeypatched network calls."""
    payload = json.dumps({"tool_input": {"command": command}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_pr_number", lambda args: pr)
    monkeypatch.setattr(
        guard, "_failing_blocking_checks", lambda p: (list(failing) if failing is not None else None)
    )
    return guard.main()


# --- detection (pure, no network) ------------------------------------------


@pytest.mark.parametrize(
    "seg,is_admin",
    [
        (["gh", "pr", "merge", "--admin"], True),
        (["gh", "pr", "merge", "123", "--admin", "--squash"], True),
        (["sudo", "gh", "pr", "merge", "--admin"], True),
        (["gh", "pr", "merge", "--squash"], False),
        (["gh", "pr", "merge", "--squash", "--delete-branch"], False),
        (["gh", "pr", "view", "5"], False),
        (["git", "push"], False),
    ],
)
def test_admin_merge_detection(seg, is_admin):
    assert (guard._admin_merge_args(seg) is not None) is is_admin


def test_quoted_admin_not_detected():
    # `--admin` inside a quoted commit body must NOT be seen as a merge command.
    segs = guard._segments('git commit -m "ref: gh pr merge --admin notes"')
    assert all(guard._admin_merge_args(s) is None for s in segs)


def test_is_advisory():
    assert guard._is_advisory("pip-audit (advisory)")
    assert guard._is_advisory("npm-audit (advisory)")
    assert not guard._is_advisory("Test (pytest)")
    assert not guard._is_advisory("Lint (ruff)")
    assert not guard._is_advisory("Frontend (build + vitest)")


# --- main() decision (fail-closed) -----------------------------------------


def test_non_admin_command_is_untouched(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --squash --delete-branch") == 0


def test_unrelated_command_is_untouched(monkeypatch):
    assert _run(monkeypatch, "git push origin main") == 0


def test_admin_with_failing_required_check_blocked(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --admin", failing=["Test (pytest)"]) == 2


def test_admin_with_only_green_or_advisory_allowed(monkeypatch):
    # No failing *required* checks (advisory-only or all green) → the legitimate --admin.
    assert _run(monkeypatch, "gh pr merge 5 --admin", failing=[]) == 0


def test_admin_unknown_pr_fails_closed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge --admin", pr=None) == 2


def test_admin_undeterminable_checks_fails_closed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --admin", failing=None) == 2


# --- _failing_blocking_checks: gh-output handling (fail-open regression) -----


def _fake_gh(monkeypatch, *, returncode: int, stdout: str):
    import types

    def fake_run(*_a, **_k):
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(guard.subprocess, "run", fake_run)


def test_failing_checks_empty_output_with_error_rc_is_failclosed(monkeypatch):
    # Regression: bogus/non-existent PR → gh errors with EMPTY stdout. Must be None
    # (fail-closed), NOT [] — `json.loads("[]")` once silently read this as "no failing
    # checks" and let the --admin bypass through.
    _fake_gh(monkeypatch, returncode=1, stdout="")
    assert guard._failing_blocking_checks("99999") is None


def test_failing_checks_empty_output_with_ok_rc_is_no_checks(monkeypatch):
    # PR genuinely has zero checks → rc 0, empty output → [] (nothing to bypass → allow).
    _fake_gh(monkeypatch, returncode=0, stdout="")
    assert guard._failing_blocking_checks("5") == []


def test_failing_checks_reports_failing_non_advisory(monkeypatch):
    rows = '[{"name":"Test (pytest)","bucket":"fail"},{"name":"pip-audit (advisory)","bucket":"fail"}]'
    _fake_gh(monkeypatch, returncode=8, stdout=rows)
    assert guard._failing_blocking_checks("5") == ["Test (pytest)"]


def test_failing_checks_advisory_only_is_empty(monkeypatch):
    rows = '[{"name":"pip-audit (advisory)","bucket":"fail"},{"name":"Test (pytest)","bucket":"pass"}]'
    _fake_gh(monkeypatch, returncode=8, stdout=rows)
    assert guard._failing_blocking_checks("5") == []


def test_failing_checks_garbage_output_is_failclosed(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout="not json")
    assert guard._failing_blocking_checks("5") is None


# --- #4876: glued-operator evasion class ------------------------------------


def _any_admin(command: str) -> bool:
    return any(
        guard._admin_merge_args(s) is not None for s in guard._segments(command)
    )


@pytest.mark.parametrize(
    "cmd",
    [
        "true 2>&1 | head -1; gh pr merge 5 --admin",
        "gh pr view 5 --jq '{state}'; gh pr merge 5 --admin --squash",
        "echo hi\ngh pr merge 5 --admin",
        "true;gh pr merge 5 --admin",
    ],
)
def test_glued_operator_admin_merge_detected(cmd):
    assert _any_admin(cmd)


def test_heredoc_admin_mention_not_detected():
    cmd = "cat > /tmp/n.md <<'EOF'\nrun gh pr merge 5 --admin manually\nEOF"
    assert not _any_admin(cmd)


def test_backslash_continuation_admin_detected():
    assert _any_admin("gh pr merge 5 \\\n  --admin --squash")


# --- #4877 adversarial round (grok-build msg 2334) ---


@pytest.mark.parametrize(
    "cmd",
    [
        "env FOO=1 gh pr merge 5 --admin",
        "FOO=1 gh pr merge 5 --admin",
        "{ gh pr merge 5 --admin; }",
    ],
)
def test_wrapper_assignment_brace_admin_detected(cmd):
    assert _any_admin(cmd)


def test_unclosed_heredoc_does_not_hide_admin():
    assert _any_admin("cat <<'NOEND'\nnote\ngh pr merge 5 --admin")


# --- colorized gh output (review B1, PR #5324) ------------------------------
# Agent harnesses export CLICOLOR_FORCE/FORCE_COLOR (beating NO_COLOR), and gh then
# colorizes piped --json output. The bare `json.loads` here raised JSONDecodeError ->
# None -> "undeterminable" -> BLOCK, so the one legitimate use of --admin this hook
# exists to permit (advisory-only failures, #M-0.5) was refused inside every agent
# harness. Same bug class as the sibling's B1; the guard must scrub the env AND
# tolerate residual ANSI.

# Escapes sit OUTSIDE the string tokens, as gh's colorizer actually emits them.
_COLORIZED_ROWS = (
    '\x1b[1;37m[\x1b[m{\n'
    '  \x1b[1;34m"name"\x1b[m: \x1b[32m"Test (pytest)"\x1b[m,\n'
    '  \x1b[1;34m"bucket"\x1b[m: \x1b[32m"pass"\x1b[m,\n'
    '  \x1b[1;34m"state"\x1b[m: \x1b[32m"SUCCESS"\x1b[m\n'
    '}\x1b[1;37m]\x1b[m\n'
)


def _capture_gh(monkeypatch, *, returncode: int = 0, stdout: str = "[]"):
    """Like _fake_gh, but records each call's argv + kwargs so the env can be asserted."""
    import types

    calls: list[tuple] = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(guard.subprocess, "run", fake_run)
    return calls


def test_gh_env_scrubs_color_forcers(monkeypatch):
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    env = guard._gh_env()
    assert "CLICOLOR_FORCE" not in env
    assert "FORCE_COLOR" not in env
    assert env["NO_COLOR"] == "1"
    assert env["CLICOLOR"] == "0"


def test_decolorize_recovers_parseable_json():
    assert json.loads(guard._decolorize(_COLORIZED_ROWS)) == [
        {"name": "Test (pytest)", "bucket": "pass", "state": "SUCCESS"}
    ]


def test_colorized_check_rows_still_parse(monkeypatch):
    """The B1 bug itself: colorized rows must not read as undeterminable (None), which
    would fail-close and block a green PR's --admin merge."""
    _fake_gh(monkeypatch, returncode=0, stdout=_COLORIZED_ROWS)
    assert guard._failing_blocking_checks("5") == []


def test_colorized_advisory_only_failure_still_allows(monkeypatch):
    """End-to-end verdict, the user-level consequence: an advisory-only failure is the
    ONE legitimate --admin case (#M-0.5). Colorized, it was blocked."""
    rows = (
        '\x1b[1;37m[\x1b[m{\x1b[1;34m"name"\x1b[m: \x1b[32m"pip-audit (advisory)"\x1b[m, '
        '\x1b[1;34m"bucket"\x1b[m: \x1b[31m"fail"\x1b[m}\x1b[1;37m]\x1b[m'
    )
    _fake_gh(monkeypatch, returncode=0, stdout=rows)
    monkeypatch.setattr(guard, "_pr_number", lambda args: "5")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": "gh pr merge 5 --admin"}})))
    assert guard.main() == 0


def test_colorized_blocking_failure_still_blocks(monkeypatch):
    """Verdict unflipped in the anti-bypass direction: decolorizing must not lose the
    `fail` bucket and let a red blocking check through."""
    rows = (
        '\x1b[1;37m[\x1b[m{\x1b[1;34m"name"\x1b[m: \x1b[32m"Test (pytest)"\x1b[m, '
        '\x1b[1;34m"bucket"\x1b[m: \x1b[31m"fail"\x1b[m}\x1b[1;37m]\x1b[m'
    )
    _fake_gh(monkeypatch, returncode=0, stdout=rows)
    assert guard._failing_blocking_checks("5") == ["Test (pytest)"]


def test_colorized_pr_number_recovered(monkeypatch):
    """`-q .number` output is passed to the NEXT gh call as the selector, so escapes
    there break it just as surely as a failed parse."""
    _fake_gh(monkeypatch, returncode=0, stdout="\x1b[32m5\x1b[m\n")
    assert guard._pr_number(["--admin"]) == "5"


def test_both_gh_sites_run_with_scrubbed_env(monkeypatch):
    """Both subprocess sites, not just one: the sibling's B1 fix was partial exactly
    because a second raw call site was missed."""
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    calls = _capture_gh(monkeypatch, returncode=0, stdout="[]")
    guard._pr_number(["--admin"])
    guard._failing_blocking_checks("5")
    assert len(calls) == 2
    for cmd, kwargs in calls:
        env = kwargs.get("env")
        assert env is not None, f"{cmd} ran without a scrubbed env"
        assert "CLICOLOR_FORCE" not in env and "FORCE_COLOR" not in env
        assert env["NO_COLOR"] == "1" and env["CLICOLOR"] == "0"


def test_gh_timeouts_stay_within_hook_budget(monkeypatch):
    """Both gh calls can run in one main() pass; their timeouts must fit the hook's
    registered 30s budget (settings.json) with headroom, else a slow gh is killed by the
    harness mid-verdict rather than fail-closing cleanly."""
    calls = _capture_gh(monkeypatch, returncode=0, stdout="[]")
    guard._pr_number(["--admin"])
    guard._failing_blocking_checks("5")
    timeouts = [kwargs["timeout"] for _cmd, kwargs in calls]
    assert all(t > 0 for t in timeouts)
    assert sum(timeouts) < 30
