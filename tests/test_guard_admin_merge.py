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
