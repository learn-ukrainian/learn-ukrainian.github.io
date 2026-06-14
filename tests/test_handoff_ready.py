"""Tests for handoff_ready — the machine-checked readiness predicate (#3138).

All git/gh/API calls are monkeypatched so the predicate logic is exercised with
no network, no repo state, and no gh auth.
"""

from __future__ import annotations

import scripts.orchestration.handoff_ready as hr


def _all_ok(monkeypatch):
    monkeypatch.setattr(hr, "check_tree_clean", lambda: (hr.OK, "clean"))
    monkeypatch.setattr(hr, "check_no_inflight", lambda: (hr.OK, "0 in flight"))
    monkeypatch.setattr(hr, "check_branch_pushed", lambda b: (hr.OK, "pushed"))
    monkeypatch.setattr(hr, "check_pr_checks", lambda pr: (hr.OK, "green"))
    monkeypatch.setattr(hr, "check_handoff_bundled", lambda b, h: (hr.OK, "bundled"))


def test_ready_when_all_ok(monkeypatch):
    _all_ok(monkeypatch)
    rep = hr.evaluate("br", 5, "h.md")
    assert rep["ready"] is True


def test_red_blocks_ready(monkeypatch):
    _all_ok(monkeypatch)
    monkeypatch.setattr(hr, "check_tree_clean", lambda: (hr.RED, "3 uncommitted"))
    assert hr.evaluate("br", 5, "h.md")["ready"] is False


def test_unknown_blocks_ready(monkeypatch):
    """Anti-fabrication: a check you could not run ⇒ NOT ready (#M-4)."""
    _all_ok(monkeypatch)
    monkeypatch.setattr(hr, "check_pr_checks", lambda pr: (hr.UNKNOWN, "gh unavailable"))
    assert hr.evaluate("br", 5, "h.md")["ready"] is False


def test_branch_pushed_logic(monkeypatch):
    state = {"remote": ""}

    def fake_git(*args):
        if args[0] == "rev-parse":
            return 0, "abc123def"
        if args[0] == "ls-remote":
            return 0, state["remote"]
        return 1, ""

    monkeypatch.setattr(hr, "_git", fake_git)

    state["remote"] = "abc123def\trefs/heads/br"
    assert hr.check_branch_pushed("br")[0] == hr.OK  # local == origin

    state["remote"] = "0000000ff\trefs/heads/br"
    assert hr.check_branch_pushed("br")[0] == hr.RED  # unpushed commits

    state["remote"] = ""
    assert hr.check_branch_pushed("br")[0] == hr.RED  # not pushed at all


def test_handoff_bundled_logic(monkeypatch):
    handoff = "docs/folk-epic/CLAUDE-DRIVER-HANDOFF.md"
    monkeypatch.setattr(hr, "_git", lambda *a: (0, f"{handoff}\nfoo.py\nbar.py"))
    assert hr.check_handoff_bundled("br", handoff)[0] == hr.OK

    monkeypatch.setattr(hr, "_git", lambda *a: (0, "foo.py\nbar.py"))
    assert hr.check_handoff_bundled("br", handoff)[0] == hr.RED


def test_no_inflight_logic(monkeypatch):
    import json

    class _Resp:
        def __init__(self, payload):
            self._p = payload.encode()

        def read(self):
            return self._p

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(
        hr.urllib.request, "urlopen", lambda *a, **k: _Resp(json.dumps({"total": 0, "tasks": []}))
    )
    assert hr.check_no_inflight()[0] == hr.OK

    monkeypatch.setattr(
        hr.urllib.request,
        "urlopen",
        lambda *a, **k: _Resp(json.dumps({"total": 2, "tasks": [{"task_id": "t1"}, {"task_id": "t2"}]})),
    )
    assert hr.check_no_inflight()[0] == hr.RED


def test_api_down_is_unknown(monkeypatch):
    def boom(*a, **k):
        raise OSError("connection refused")

    monkeypatch.setattr(hr.urllib.request, "urlopen", boom)
    assert hr.check_no_inflight()[0] == hr.UNKNOWN
