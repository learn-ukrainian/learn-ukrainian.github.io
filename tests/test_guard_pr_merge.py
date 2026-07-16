"""Unit tests for the PR-merge guard hook (#189 class / free-plan protection gap).

Exercises the pure decision logic in
``agents_extensions/shared/hooks/guard-pr-merge.py``:

  * `gh pr merge` detection (incl. wrappers, a positional PR number, and the
    `--admin` / `--disable-auto` segments this hook deliberately leaves alone),
  * the quote-aware tokenizer (a `gh pr merge` inside a quoted commit body is NOT a merge),
  * failing/pending check classification against the advisory allowlist,
  * the fail-CLOSED `main()` decision (block on draft, red checks, pending-without-auto,
    --auto on an unprotected base, and on anything undeterminable; allow on green).

The hook filename has hyphens, so it is loaded by path via importlib. `main()` is guarded
by `__name__ == "__main__"`, so import has no side effects. Network functions
(`_pr_ref`, `_pr_meta`, `_check_states`, `_base_protected`) are monkeypatched — no
`gh`/network in tests.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-pr-merge.py"
_URL = "https://github.com/owner/repo/pull/5"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_pr_merge", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()


def _run(
    monkeypatch,
    command: str,
    *,
    pr: str | None = "5",
    meta: dict | None = None,
    checks: tuple[list[str], list[str]] | None = ([], []),
    owner_repo: str | None = "owner/repo",
    protected: bool | None = False,
) -> int:
    """Drive main() with a simulated stdin payload + monkeypatched network calls.

    Defaults describe this repo today: a ready PR, all checks green, unprotected base.
    """
    payload = json.dumps({"tool_input": {"command": command}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_pr_ref", lambda args, repo=None: pr)
    monkeypatch.setattr(
        guard,
        "_pr_meta",
        lambda p, repo=None: ({"isDraft": False, "baseRefName": "main", "url": _URL} if meta is None else meta),
    )
    monkeypatch.setattr(guard, "_check_states", lambda p, repo=None: checks)
    monkeypatch.setattr(guard, "_owner_repo_from_url", lambda u: owner_repo)
    monkeypatch.setattr(guard, "_base_protected", lambda o, b: protected)
    return guard.main()


# --- detection (pure, no network) ------------------------------------------


@pytest.mark.parametrize(
    "seg,judged",
    [
        (["gh", "pr", "merge"], True),
        (["gh", "pr", "merge", "123", "--squash", "--delete-branch"], True),
        (["gh", "pr", "merge", "--auto", "--squash"], True),
        (["sudo", "gh", "pr", "merge", "5"], True),
        # guard-admin-merge.py's job — never double-judge.
        (["gh", "pr", "merge", "5", "--admin"], False),
        # Disarms auto-merge rather than merging; it is the remedy, not the offence.
        (["gh", "pr", "merge", "5", "--disable-auto"], False),
        (["gh", "pr", "view", "5"], False),
        (["gh", "pr", "create"], False),
        (["git", "push"], False),
    ],
)
def test_merge_detection(seg, judged):
    assert (guard._merge_args(seg) is not None) is judged


def test_quoted_merge_not_detected():
    # `gh pr merge` inside a quoted commit body must NOT be seen as a merge command.
    segs = guard._segments('git commit -m "docs: never run gh pr merge 5 on a draft"')
    assert all(guard._merge_args(s) is None for s in segs)


def test_is_advisory():
    assert guard._is_advisory("pip-audit (advisory)")
    assert not guard._is_advisory("boundary-and-tests")
    assert not guard._is_advisory("Test (pytest)")


# --- main() decision (fail-closed) -----------------------------------------


def test_non_merge_command_is_untouched(monkeypatch):
    assert _run(monkeypatch, "gh pr view 5 --json state") == 0


def test_unrelated_command_is_untouched(monkeypatch):
    assert _run(monkeypatch, "git push origin main") == 0


def test_admin_merge_is_other_guards_job(monkeypatch):
    # Red checks + --admin → still 0 from THIS hook; guard-admin-merge.py judges it.
    assert _run(monkeypatch, "gh pr merge 5 --admin", checks=(["Test (pytest)"], [])) == 0


def test_disable_auto_is_not_a_merge(monkeypatch):
    # Disarming auto-merge on a draft is the remedy this guard asks for — never block it.
    assert _run(
        monkeypatch, "gh pr merge 5 --disable-auto", meta={"isDraft": True, "baseRefName": "main", "url": _URL}
    ) == 0


def test_draft_is_blocked(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --squash", meta={"isDraft": True, "baseRefName": "main", "url": _URL}) == 2


def test_red_non_advisory_check_is_blocked(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --squash", checks=(["boundary-and-tests"], [])) == 2


def test_green_is_allowed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --squash --delete-branch") == 0


def test_pending_without_auto_is_blocked(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --squash", checks=([], ["Test (pytest)"])) == 2


def test_auto_on_protected_base_is_allowed(monkeypatch):
    # Protection with required status checks → --auto waits for them, as advertised.
    assert _run(monkeypatch, "gh pr merge 5 --auto --squash", checks=([], ["Test (pytest)"]), protected=True) == 0


def test_auto_on_unprotected_base_is_blocked(monkeypatch):
    # 403/404 → the repo enforces nothing → auto-merge fires regardless of checks.
    assert _run(monkeypatch, "gh pr merge 5 --auto --squash", protected=False) == 2


def test_auto_with_undeterminable_protection_fails_closed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --auto --squash", protected=None) == 2


def test_auto_with_unknown_repo_fails_closed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --auto --squash", owner_repo=None) == 2


def test_unknown_pr_fails_closed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge --squash", pr=None) == 2


def test_undeterminable_pr_meta_fails_closed(monkeypatch):
    # _pr_meta returning None (gh error/timeout) → block, never "assume not a draft".
    monkeypatch.setattr(guard, "_pr_meta", lambda p, repo=None: None)
    payload = json.dumps({"tool_input": {"command": "gh pr merge 5 --squash"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_pr_ref", lambda args, repo=None: "5")
    assert guard.main() == 2


def test_undeterminable_checks_fails_closed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --squash", checks=None) == 2


# --- _pr_meta / _check_states: gh-output handling (fail-open regression) -----


def _fake_gh(monkeypatch, *, returncode: int, stdout: str, stderr: str = ""):
    import types

    def fake_run(*_a, **_k):
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(guard.subprocess, "run", fake_run)


def test_pr_meta_parses_draft(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout='{"isDraft":true,"baseRefName":"main"}')
    assert guard._pr_meta("5") == {"isDraft": True, "baseRefName": "main"}


def test_pr_meta_error_rc_is_failclosed(monkeypatch):
    _fake_gh(monkeypatch, returncode=1, stdout="")
    assert guard._pr_meta("99999") is None


def test_pr_meta_without_isdraft_is_failclosed(monkeypatch):
    # An empty/partial payload must not read as "not a draft".
    _fake_gh(monkeypatch, returncode=0, stdout="{}")
    assert guard._pr_meta("5") is None


def test_pr_meta_garbage_output_is_failclosed(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout="not json")
    assert guard._pr_meta("5") is None


def test_check_states_empty_output_with_error_rc_is_failclosed(monkeypatch):
    # Bogus/non-existent PR → gh errors with EMPTY stdout. Must be None (fail-closed),
    # not ([], []) — reading an error as "all green" is the fail-open bug.
    _fake_gh(monkeypatch, returncode=1, stdout="")
    assert guard._check_states("99999") is None


def test_check_states_empty_output_with_ok_rc_is_no_checks(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout="")
    assert guard._check_states("5") == ([], [])


def test_check_states_splits_failing_and_pending(monkeypatch):
    rows = (
        '[{"name":"boundary-and-tests","bucket":"fail"},'
        '{"name":"Test (pytest)","bucket":"pending"},'
        '{"name":"Lint (ruff)","bucket":"pass"},'
        '{"name":"pip-audit (advisory)","bucket":"fail"}]'
    )
    _fake_gh(monkeypatch, returncode=8, stdout=rows)
    assert guard._check_states("5") == (["boundary-and-tests"], ["Test (pytest)"])


def test_check_states_garbage_output_is_failclosed(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout="not json")
    assert guard._check_states("5") is None


def test_base_protected_true_only_with_required_checks(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout='{"required_status_checks":{"contexts":["Test (pytest)"]}}')
    assert guard._base_protected("owner/repo", "main") is True


def test_base_protected_without_required_checks_is_false(monkeypatch):
    # Protected, but nothing required → --auto still merges regardless of checks.
    _fake_gh(monkeypatch, returncode=0, stdout='{"allow_force_pushes":{"enabled":false}}')
    assert guard._base_protected("owner/repo", "main") is False


def test_base_protected_with_empty_required_checks_is_false(monkeypatch):
    # required_status_checks can exist while requiring NOTHING: a truthy dict whose
    # contexts and checks are both empty. Auto-merge would then wait for nothing and
    # merge red — the same hole as an unprotected branch, wearing protection's clothes.
    _fake_gh(monkeypatch, returncode=0, stdout='{"required_status_checks":{"contexts":[],"checks":[],"strict":false}}')
    assert guard._base_protected("owner/repo", "main") is False


def test_base_protected_with_checks_but_no_contexts_is_true(monkeypatch):
    # The modern shape: `checks` populated, legacy `contexts` empty. Still enforcing.
    _fake_gh(
        monkeypatch,
        returncode=0,
        stdout='{"required_status_checks":{"contexts":[],"checks":[{"context":"CI Gate","app_id":15368}]}}',
    )
    assert guard._base_protected("owner/repo", "main") is True


def test_base_protected_with_non_dict_required_checks_is_false(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout='{"required_status_checks":"weird"}')
    assert guard._base_protected("owner/repo", "main") is False


def test_auto_on_base_with_empty_required_checks_is_blocked(monkeypatch):
    # End-to-end: the empty-required-checks branch must refuse --auto like any other
    # base that enforces nothing.
    monkeypatch.setattr(guard, "_base_protected", lambda o, b: False)
    payload = json.dumps({"tool_input": {"command": "gh pr merge 5 --auto --squash"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_pr_ref", lambda args, repo=None: "5")
    monkeypatch.setattr(guard, "_pr_meta", lambda p, repo=None: {"isDraft": False, "baseRefName": "main", "url": _URL})
    monkeypatch.setattr(guard, "_check_states", lambda p, repo=None: ([], []))
    monkeypatch.setattr(guard, "_owner_repo_from_url", lambda u: "owner/repo")
    assert guard.main() == 2


@pytest.mark.parametrize("err", ["HTTP 403: Upgrade to GitHub Pro", "HTTP 404: Branch not protected"])
def test_base_protected_403_404_is_false(monkeypatch, err):
    _fake_gh(monkeypatch, returncode=1, stdout="", stderr=err)
    assert guard._base_protected("owner/repo", "main") is False


def test_base_protected_other_error_is_undeterminable(monkeypatch):
    _fake_gh(monkeypatch, returncode=1, stdout="", stderr="HTTP 500: Internal Server Error")
    assert guard._base_protected("owner/repo", "main") is None


# --- codex adversarial round (PR #5324): confirmed fail-open holes -----------
#
# Every case below was a REAL hole, reproduced against the code before the fix.
# gh is cobra/pflag, so `--auto=true` is the same flag as `--auto` — verified live:
# `gh pr list --draft=notabool` errors with "strconv.ParseBool: invalid syntax",
# proving the =value spelling parses.


def test_flag_enabled_spellings():
    assert guard._flag_enabled(["--auto"], "auto")
    assert guard._flag_enabled(["--auto=true"], "auto")
    assert guard._flag_enabled(["--auto=1"], "auto")
    assert guard._flag_enabled(["--auto=T"], "auto")
    assert not guard._flag_enabled(["--auto=false"], "auto")
    assert not guard._flag_enabled(["--auto=0"], "auto")
    assert not guard._flag_enabled(["--squash"], "auto")
    # Malformed → gh itself would exit non-zero; reading it as ON is fail-closed.
    assert guard._flag_enabled(["--auto=maybe"], "auto")


def test_auto_equals_true_on_unprotected_base_is_blocked(monkeypatch):
    # F001: `--auto=true` skipped the protection check entirely and armed auto-merge
    # on a base that enforces nothing — the exact incident this hook exists to stop.
    assert _run(monkeypatch, "gh pr merge 5 --auto=true --squash", protected=False) == 2


def test_auto_equals_false_is_a_normal_merge(monkeypatch):
    # Not an auto-merge → judged as a manual merge: green passes, pending blocks.
    assert _run(monkeypatch, "gh pr merge 5 --auto=false --squash", protected=False) == 0
    assert _run(monkeypatch, "gh pr merge 5 --auto=false --squash", checks=([], ["Test (pytest)"])) == 2


def test_disable_auto_equals_true_is_not_a_merge(monkeypatch):
    # F005: the safe disarm was judged (and blocked) in its `=true` spelling.
    assert _run(
        monkeypatch, "gh pr merge 5 --disable-auto=true", meta={"isDraft": True, "baseRefName": "main", "url": _URL}
    ) == 0


def test_admin_equals_true_is_judged_here(monkeypatch):
    # guard-admin-merge.py matches the exact token "--admin" only, so `--admin=true`
    # is invisible to it. Judging it here closes the gap between the two hooks rather
    # than letting a red admin merge fall between them. (Bare --admin stays its job.)
    assert _run(monkeypatch, "gh pr merge 5 --admin=true", checks=(["Test (pytest)"], [])) == 2


@pytest.mark.parametrize(
    "cmd",
    [
        "sudo -u bot gh pr merge 5 --squash",
        "env -i gh pr merge 5 --squash",
        "env -u FOO gh pr merge 5 --auto",
    ],
)
def test_wrapper_with_options_is_still_judged(cmd):
    # F002: _skip_command_prefix consumed the wrapper but not its options, so the
    # `['gh','pr','merge']` match failed and the merge was never judged.
    assert _any_merge(cmd)


def test_unwrapped_mention_is_not_a_merge():
    # The wrapper scan must not turn any stray token run into a merge.
    assert not _any_merge("echo gh pr merge 5")


def test_unknown_check_bucket_fails_closed(monkeypatch):
    # F003: an unrecognized (or future) bucket fell through as neither failing nor
    # pending — i.e. green. Schema drift must block, not merge.
    _fake_gh(monkeypatch, returncode=0, stdout='[{"name":"CI Gate","bucket":"mystery","state":"mystery"}]')
    assert guard._check_states("5") is None


def test_missing_check_bucket_fails_closed(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout='[{"name":"CI Gate"}]')
    assert guard._check_states("5") is None


def test_known_pass_buckets_are_green(monkeypatch):
    rows = '[{"name":"CI Gate","bucket":"pass"},{"name":"Flaky","bucket":"skipping"},{"name":"N","bucket":"neutral"}]'
    _fake_gh(monkeypatch, returncode=0, stdout=rows)
    assert guard._check_states("5") == ([], [])


@pytest.mark.parametrize("draft", ["null", '"false"', "0"])
def test_non_bool_isdraft_fails_closed(monkeypatch, draft):
    # F004: `isDraft: null` is falsey → was read as a confirmed non-draft and allowed.
    _fake_gh(monkeypatch, returncode=0, stdout=f'{{"isDraft":{draft},"baseRefName":"main"}}')
    assert guard._pr_meta("5") is None


# --- codex re-review round 2 (PR #5324): three more confirmed holes ----------


def test_flag_enabled_last_occurrence_wins():
    # pflag applies repeated flags in order, so `--auto=false --auto` IS auto-merge.
    # Verified live: `gh pr list --draft=false --draft=true` returns draft PRs.
    # Returning on the first match read this as "off" and waved the merge through.
    assert guard._flag_enabled(["--auto=false", "--auto"], "auto")
    assert guard._flag_enabled(["--auto", "--auto=true"], "auto")
    assert not guard._flag_enabled(["--auto", "--auto=false"], "auto")
    assert not guard._flag_enabled(["--auto=true", "--auto=false"], "auto")


def test_repeated_auto_flags_on_unprotected_base_is_blocked(monkeypatch):
    # The fail-open: green checks + `--auto=false --auto` → gh arms auto-merge on a base
    # that requires nothing, and a later red check does not stop it.
    assert _run(monkeypatch, "gh pr merge 5 --auto=false --auto --squash", protected=False) == 2


@pytest.mark.parametrize(
    "cmd",
    [
        "bash -c 'gh pr merge 5 --squash'",
        'sh -c "gh pr merge 5 --auto"',
        "/bin/bash -c 'gh pr merge 5 --squash'",
        "bash -lc 'gh pr merge 5 --squash'",
        "zsh -c 'true; gh pr merge 5 --squash'",
        # Nested one level deeper.
        "bash -c \"bash -c 'gh pr merge 5 --squash'\"",
    ],
)
def test_shell_c_payload_is_judged(cmd):
    # A `bash -c` payload really executes the merge; the segment merely starts with `bash`.
    assert any(guard._merge_args(s) is not None for s in guard._judged_segments(cmd))


def test_shell_c_without_merge_is_not_judged():
    assert not any(guard._merge_args(s) is not None for s in guard._judged_segments("bash -c 'git status'"))


def test_shell_c_merge_blocks_end_to_end(monkeypatch):
    assert _run(monkeypatch, "bash -c 'gh pr merge 5 --squash'", checks=(["boundary-and-tests"], [])) == 2


@pytest.mark.parametrize(
    "args,expected",
    [
        (["5", "--squash"], "5"),
        (["--squash", "5"], "5"),
        # The value of a value-taking flag is NOT the PR: judging PR #5 here while gh
        # merges the current branch's PR is a fail-open.
        (["--subject", "5", "--squash"], None),
        (["-t", "5", "--squash"], None),
        (["--body", "5"], None),
        (["--match-head-commit", "1234567", "--squash"], None),
        (["--subject=5", "--squash"], None),
        # gh accepts url and branch selectors too — pass them through verbatim.
        (["https://github.com/other/repo/pull/9", "--squash"], "https://github.com/other/repo/pull/9"),
        (["some-branch", "--squash"], "some-branch"),
        (["--squash", "--delete-branch"], None),
    ],
)
def test_pr_selector(args, expected):
    assert guard._pr_selector(args) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5324", "learn-ukrainian/learn-ukrainian.github.io"),
        ("https://github.com/other/repo/pull/9", "other/repo"),
        ("https://ghe.example.com/o/r/pull/1", "o/r"),
        ("not a url", None),
        ("", None),
    ],
)
def test_owner_repo_from_url(url, expected):
    # Identity comes from the PR's own url — the BASE repo, fork-safe, and correct even
    # when cwd is a different repo entirely (a URL selector).
    assert guard._owner_repo_from_url(url) == expected


def test_cross_repo_url_selector_uses_that_repo(monkeypatch):
    # The PR url decides which repo's protection is read, not the cwd.
    seen = {}
    monkeypatch.setattr(guard, "_pr_ref", lambda args, repo=None: "https://github.com/other/repo/pull/9")
    monkeypatch.setattr(
        guard,
        "_pr_meta",
        lambda p, repo=None: {"isDraft": False, "baseRefName": "main", "url": "https://github.com/other/repo/pull/9"},
    )
    monkeypatch.setattr(guard, "_check_states", lambda p, repo=None: ([], []))
    monkeypatch.setattr(guard, "_base_protected", lambda o, b: seen.setdefault("repo", o) and True)
    payload = json.dumps({"tool_input": {"command": "gh pr merge https://github.com/other/repo/pull/9 --auto"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    guard.main()
    assert seen["repo"] == "other/repo"


def test_pr_meta_requires_url_field(monkeypatch):
    # url is load-bearing for the protection lookup; gh must actually return it.
    _fake_gh(monkeypatch, returncode=0, stdout='{"isDraft":false,"baseRefName":"main","url":"https://github.com/o/r/pull/5"}')
    assert guard._pr_meta("5") == {
        "isDraft": False,
        "baseRefName": "main",
        "url": "https://github.com/o/r/pull/5",
    }


# --- codex re-review round 3 (PR #5324): four more confirmed holes -----------


@pytest.mark.parametrize("cmd", ["bash -cx 'gh pr merge 5 --squash'", 'sh -cx "gh pr merge 5"'])
def test_clustered_c_not_last_is_judged(cmd):
    # `bash -cx 'cmd'` runs cmd (verified: `bash -cx 'echo hi'` executes, exit 0), so
    # requiring the cluster to END in c missed a real merge.
    assert any(guard._merge_args(s) is not None for s in guard._judged_segments(cmd))


@pytest.mark.parametrize(
    "cmd",
    [
        "bash -c $'gh pr merge 5 --squash'",
        'bash -c $"gh pr merge 5"',
    ],
)
def test_dollar_quoted_shell_payload_is_judged(cmd):
    # Bash's $'...' (ANSI-C) and $"..." (locale) quoting run the command for real, but
    # survive tokenizing as a literal `$` glued to the payload — first token `$gh`,
    # matching nothing. Verified: `bash -c $'echo ansi-c-ran'` executes.
    assert any(guard._merge_args(s) is not None for s in guard._judged_segments(cmd))


def test_strip_dollar_quote():
    assert guard._strip_dollar_quote("$gh pr merge 5") == "gh pr merge 5"
    assert guard._strip_dollar_quote("gh pr merge 5") == "gh pr merge 5"


def test_valid_nested_shell_is_judged():
    assert any(
        guard._merge_args(s) is not None
        for s in guard._judged_segments("""bash -c 'bash -c "gh pr merge 5 --squash"'""")
    )


def test_recursion_cap_fails_closed(monkeypatch):
    # At the cap the payload is NOT inspected, so it must be refused rather than passed
    # through. Regression for an inert sentinel: the marker segment carries no PR
    # selector, and _pr_ref falls back to the CURRENT BRANCH's PR — so without an
    # explicit marker check, a green current branch would approve an unread payload.
    monkeypatch.setattr(guard, "_pr_ref", lambda args, repo=None: "5")
    monkeypatch.setattr(guard, "_pr_meta", lambda p, repo=None: {"isDraft": False, "baseRefName": "main", "url": _URL})
    monkeypatch.setattr(guard, "_check_states", lambda p, repo=None: ([], []))  # all green
    assert guard._judge([guard._UNREADABLE_MARKER]) is not None


def test_deep_nesting_emits_unparsed_marker():
    segs = guard._judged_segments("bash -c 'gh pr merge 5 --squash'", guard._MAX_SHELL_DEPTH)
    assert guard._UNPARSED in segs


@pytest.mark.parametrize(
    "cmd",
    [
        "gh pr merge 5 --subject --disable-auto",
        "gh pr merge 5 --subject --admin",
        "gh pr merge 5 --body --disable-auto --squash",
    ],
)
def test_flag_looking_values_do_not_suppress_judging(cmd):
    # pflag takes the next token as a string flag's VALUE even when it looks like a flag.
    # `--subject --disable-auto` is a normal merge whose subject is "--disable-auto";
    # reading that value as the flag skipped judging entirely — a fail-open.
    assert any(guard._merge_args(s) is not None for s in guard._judged_segments(cmd))


def test_flag_looking_value_does_not_force_auto_path():
    # The mirror image: `--subject --auto` must not be read as arming auto-merge.
    flags, _ = guard._classify(["5", "--subject", "--auto"])
    assert not guard._flag_enabled(flags, "auto")


def test_real_control_flags_still_recognized():
    assert guard._merge_args(["gh", "pr", "merge", "5", "--disable-auto"]) is None
    assert guard._merge_args(["gh", "pr", "merge", "5", "--admin"]) is None
    assert guard._flag_enabled(guard._classify(["5", "--auto"])[0], "auto")


@pytest.mark.parametrize(
    "args,repo",
    [
        (["--repo", "other/repo", "9"], "other/repo"),
        (["--repo=other/repo", "9"], "other/repo"),
        (["-R", "o/r", "9"], "o/r"),
        (["9", "--squash"], None),
        # A VALUE that looks like --repo is not a repo selector.
        (["5", "--subject", "--repo"], None),
    ],
)
def test_repo_option(args, repo):
    assert guard._repo_option(args) == repo


def test_repo_option_value_is_not_the_pr_selector():
    # `gh pr merge --repo other/repo 9` targets PR 9 — not a PR named "other/repo".
    assert guard._pr_selector(["--repo", "other/repo", "9", "--auto"]) == "9"


def test_repo_is_propagated_to_every_gh_lookup(monkeypatch):
    # `gh pr merge --repo other/repo 9` merges other/repo#9. If the guard reads THIS
    # repo's #9 instead, it judges a different PR than the one being merged.
    calls = []

    def fake_run(argv, *_a, **_k):
        import types

        calls.append(argv)
        if argv[:3] == ["gh", "pr", "view"]:
            return types.SimpleNamespace(
                returncode=0, stdout='{"isDraft":false,"baseRefName":"main","url":"https://github.com/other/repo/pull/9"}', stderr=""
            )
        return types.SimpleNamespace(returncode=0, stdout="[]", stderr="")

    monkeypatch.setattr(guard.subprocess, "run", fake_run)
    guard._judge(["--repo", "other/repo", "9", "--squash"])
    assert all("--repo" in c and "other/repo" in c for c in calls), calls


# --- codex re-review round 4 (PR #5324): pflag shorthands + shell escaping ---


def test_escaped_gh_still_reaches_the_parser(monkeypatch):
    # The shell strips the backslash BEFORE running the command: `bash -c 'g\h --version'`
    # prints gh's version. A fast path over raw source let `g\h pr merge` past the early
    # return entirely. Normalizing quotes/backslashes first closes it.
    assert _run(monkeypatch, r"g\h pr merge 5 --squash", checks=(["boundary-and-tests"], [])) == 2
    assert _run(monkeypatch, "g'h' pr merge 5 --squash", checks=(["boundary-and-tests"], [])) == 2


def test_fast_path_still_ignores_unrelated_commands(monkeypatch):
    assert _run(monkeypatch, "git push origin main") == 0
    assert _run(monkeypatch, "echo 'nothing to see'") == 0


@pytest.mark.parametrize(
    "cmd",
    [
        "gh pr merge --help",
        "gh pr merge -h",
        "gh pr merge 5 --help",
        # --help is a bool like any other, so it has the =value spelling too.
        "gh pr merge --help=true",
    ],
)
def test_help_is_not_a_merge(monkeypatch, cmd):
    # Reading the manual merges nothing. Blocking it (on a draft, say) would just teach
    # people the guard is noise.
    assert _run(monkeypatch, cmd, meta={"isDraft": True, "baseRefName": "main", "url": _URL}) == 0


@pytest.mark.parametrize(
    "cmd",
    [
        "git commit -m 'fix: pr merge notes'",
        "gh pr create --title x --body y",
        "gh pr view 5 --json state",
        "gh pr checks 5",
        "gh pr ready 5",
        "grep -r 'gh pr merge' docs/",
        "python scripts/merge_data.py --pr 5",
        "git merge origin/main",
    ],
)
def test_ordinary_commands_are_untouched(monkeypatch, cmd):
    # The guard must be invisible in normal use; a red PR is the harshest setting here.
    assert _run(monkeypatch, cmd, checks=(["boundary-and-tests"], [])) == 0


@pytest.mark.parametrize(
    "args,repo",
    [
        # Attached short value — verified against real gh: `gh pr view -R<owner>/<repo> N`.
        (["-Rother/repo", "9"], "other/repo"),
        (["-R=other/repo", "9"], "other/repo"),
        (["-R", "other/repo", "9"], "other/repo"),
        (["--repo=other/repo", "9"], "other/repo"),
        # -R as the last letter of a cluster, value in the next token.
        (["-sR", "other/repo", "9"], "other/repo"),
        (["9", "--squash"], None),
    ],
)
def test_repo_option_all_spellings(args, repo):
    assert guard._repo_option(args) == repo


@pytest.mark.parametrize(
    "args,selector",
    [
        # `-st green-subject`: -s is squash, -t consumes the subject → target is the
        # CURRENT branch's PR, not a PR called "green-subject".
        (["-st", "green-subject", "--auto"], None),
        (["-tgreen-subject", "--auto"], None),
        (["-t=green-subject"], None),
        (["-Rother/repo", "9"], "9"),
        (["-sR", "other/repo", "9"], "9"),
        # A non-value shorthand must NOT swallow the selector.
        (["-s", "9"], "9"),
        (["-d", "branch-name"], "branch-name"),
    ],
)
def test_pr_selector_with_shorthand_clusters(args, selector):
    assert guard._pr_selector(args) == selector


def test_cluster_value():
    assert guard._cluster_value("-st") == ("--subject", None, True)
    assert guard._cluster_value("-tsubj") == ("--subject", "subj", False)
    assert guard._cluster_value("-t=subj") == ("--subject", "subj", False)
    assert guard._cluster_value("-Rowner/repo") == ("--repo", "owner/repo", False)
    assert guard._cluster_value("-sd") == (None, None, False)


def test_xargs_shell_form_is_judged():
    assert any(
        guard._merge_args(s) is not None
        for s in guard._judged_segments("printf '' | xargs sh -c 'gh pr merge 5 --auto'")
    )


# --- codex re-review round 5 (PR #5324): xargs is not a transparent prefix ----


def test_xargs_fed_selector_fails_closed(monkeypatch):
    # `printf '5' | xargs gh pr merge --squash` runs `gh pr merge --squash 5`, but 5 is
    # on stdin. Falling back to the current branch's PR would verify one PR while gh
    # merges another — so refuse. Green current branch must NOT rescue it.
    assert _run(monkeypatch, "printf '5' | xargs gh pr merge --squash", checks=([], [])) == 2


def test_xargs_with_explicit_selector_is_judged_normally(monkeypatch):
    assert _run(monkeypatch, "printf '' | xargs gh pr merge 5 --squash", checks=(["boundary-and-tests"], [])) == 2
    assert _run(monkeypatch, "printf '' | xargs gh pr merge 5 --squash", checks=([], [])) == 0


def test_xargs_options_are_stepped_over(monkeypatch):
    # -n1 / -I{} carry their own values; the invoked command still starts at gh.
    assert _run(monkeypatch, "printf '' | xargs -n1 gh pr merge 5 --squash", checks=(["x"], [])) == 2
    assert _run(monkeypatch, "printf '' | xargs -t -n 1 gh pr merge 5", checks=(["x"], [])) == 2


@pytest.mark.parametrize(
    "cmd",
    [
        # `xargs echo gh pr merge 5` runs ECHO with data appended — not a merge. Treating
        # xargs' operands as an invoked command blocked a plain logging line.
        "printf 'x' | xargs echo gh pr merge 5",
        "printf 'x' | xargs -n1 echo gh pr merge 5",
    ],
)
def test_xargs_operands_are_not_a_merge(monkeypatch, cmd):
    assert _run(monkeypatch, cmd, meta={"isDraft": True, "baseRefName": "main", "url": _URL}) == 0


def test_invoked_start():
    assert guard._invoked_start(["gh", "pr", "merge", "5"]) == (0, False)
    assert guard._invoked_start(["xargs", "gh", "pr", "merge"]) == (1, True)
    assert guard._invoked_start(["xargs", "-n", "1", "gh", "pr", "merge"]) == (3, True)
    assert guard._invoked_start(["xargs", "-t", "gh", "pr", "merge"]) == (2, True)
    assert guard._invoked_start(["sudo", "gh", "pr", "merge"]) == (1, False)


# --- #4876: glued-operator evasion class ------------------------------------


def _any_merge(command: str) -> bool:
    return any(guard._merge_args(s) is not None for s in guard._segments(command))


@pytest.mark.parametrize(
    "cmd",
    [
        "true 2>&1 | head -1; gh pr merge 5 --squash",
        "gh pr view 5 --jq '{state}'; gh pr merge 5 --auto --squash",
        "echo hi\ngh pr merge 5 --squash",
        "true;gh pr merge 5",
        "env FOO=1 gh pr merge 5 --squash",
        "FOO=1 gh pr merge 5 --squash",
        "{ gh pr merge 5 --squash; }",
    ],
)
def test_glued_operator_merge_detected(cmd):
    assert _any_merge(cmd)


def test_heredoc_merge_mention_not_detected():
    cmd = "cat > /tmp/n.md <<'EOF'\nrun gh pr merge 5 --squash manually\nEOF"
    assert not _any_merge(cmd)


def test_unclosed_heredoc_does_not_hide_merge():
    assert _any_merge("cat <<'NOEND'\nnote\ngh pr merge 5 --squash")


def test_backslash_continuation_merge_detected():
    assert _any_merge("gh pr merge 5 \\\n  --auto --squash")


# --- colorized gh output (review B1, PR #5324) ------------------------------
# Agent harnesses export CLICOLOR_FORCE/FORCE_COLOR (beating NO_COLOR), and gh
# then colorizes piped --json output — raw json.loads fails and every merge
# fail-closes. The guard must scrub the env AND tolerate residual ANSI.

_COLORIZED_JSON = (
    '\x1b[1;37m{\x1b[m\n'
    '  \x1b[1;34m"baseRefName"\x1b[m: \x1b[32m"main"\x1b[m,\n'
    '  \x1b[1;34m"isDraft"\x1b[m: \x1b[35mfalse\x1b[m,\n'
    '  \x1b[1;34m"url"\x1b[m: \x1b[32m"https://github.com/owner/repo/pull/5"\x1b[m\n'
    '\x1b[1;37m}\x1b[m\n'
)


def test_gh_env_scrubs_color_forcers(monkeypatch):
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("NO_COLOR", "1")
    env = guard._gh_env()
    assert "CLICOLOR_FORCE" not in env
    assert "FORCE_COLOR" not in env
    assert env["NO_COLOR"] == "1"
    assert env["CLICOLOR"] == "0"


def test_decolorize_recovers_parseable_json():
    cleaned = guard._decolorize(_COLORIZED_JSON)
    parsed = json.loads(cleaned)
    assert parsed == {
        "baseRefName": "main",
        "isDraft": False,
        "url": "https://github.com/owner/repo/pull/5",
    }


def test_colorized_check_rows_still_judged(monkeypatch):
    """End-to-end through _check_states' parser: colorized rows must not read as
    undeterminable (which would block every green merge)."""
    rows = '\x1b[1;37m[{"name": "pytest", "bucket": "pass", "state": "SUCCESS"}]\x1b[m'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=rows, stderr="")
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **k: completed)
    failing, pending = guard._check_states("5")
    assert failing == [] and pending == []


def test_colorized_pr_meta_still_parses(monkeypatch):
    """_check_states was decolorized but _pr_meta was not (review B1 follow-up). Raw
    parsing here raises JSONDecodeError -> None -> undeterminable -> every merge blocked,
    draft or not. The payload must survive ANSI and keep isDraft a real boolean."""
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=_COLORIZED_JSON, stderr="")
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **k: completed)
    assert guard._pr_meta("5") == {
        "baseRefName": "main",
        "isDraft": False,
        "url": "https://github.com/owner/repo/pull/5",
    }


def test_colorized_pr_meta_honors_draft(monkeypatch):
    """The draft bit must be read THROUGH the colorization, not lost to it: a colorized
    draft payload has to still block."""
    colorized_draft = '\x1b[1;37m{\x1b[m\x1b[1;34m"isDraft"\x1b[m: \x1b[35mtrue\x1b[m, \x1b[1;34m"baseRefName"\x1b[m: \x1b[32m"main"\x1b[m\x1b[1;37m}\x1b[m'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=colorized_draft, stderr="")
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **k: completed)
    meta = guard._pr_meta("5")
    assert meta is not None and meta["isDraft"] is True


def test_colorized_base_protection_still_classified(monkeypatch):
    """_base_protected's parse was raw too. Colorized protection JSON must classify as
    protected — reading it as undeterminable blocks legitimate --auto on a guarded base."""
    colorized = (
        '\x1b[1;37m{\x1b[m\n'
        '  \x1b[1;34m"required_status_checks"\x1b[m: \x1b[1;37m{\x1b[m\n'
        '    \x1b[1;34m"contexts"\x1b[m: [\x1b[32m"Test (pytest)"\x1b[m],\n'
        '    \x1b[1;34m"strict"\x1b[m: \x1b[35mtrue\x1b[m\n'
        '  \x1b[1;37m}\x1b[m\n'
        '\x1b[1;37m}\x1b[m\n'
    )
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=colorized, stderr="")
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **k: completed)
    assert guard._base_protected("owner/repo", "main") is True


def test_colorized_empty_required_checks_still_unprotected(monkeypatch):
    """Decolorizing must not flip the empty-required-checks verdict: protection that
    requires NOTHING is still False (auto-merge would wait for nothing and merge red)."""
    colorized = '\x1b[1;37m{\x1b[m\x1b[1;34m"required_status_checks"\x1b[m: \x1b[1;37m{\x1b[m\x1b[1;34m"contexts"\x1b[m: [], \x1b[1;34m"checks"\x1b[m: []\x1b[1;37m}\x1b[m\x1b[1;37m}\x1b[m'
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=colorized, stderr="")
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **k: completed)
    assert guard._base_protected("owner/repo", "main") is False
