"""#10630 S2: the Claude account is part of the route key (#10619, #10733).

Three properties, each against the real code paths:

- The snapshot read API has no default account: a call without a
  ``ClaudeAccount`` fails at type-check time (mypy) and at run time.
- Every final claude route resolves and binds its account before admission;
  an unresolved account removes the claude seats and no other (#10733).
- For one routing snapshot and one account, the five decision consumers reach
  the same capacity verdict: the owner (``claude_account_lane.capacity_verdict``),
  the dispatch budget guard, the plan-headroom stop (``model_pause``), reviewer
  admission (``target_admission``) and ``closeout_cli resolve-reviewer``.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import delegate
from scripts.agent_runtime import attempt_boundary, model_pause, target_admission
from scripts.agent_runtime.mechanical_admission import MechanicalAdmissionRefused
from scripts.fleet import claude_account_lane
from scripts.fleet.claude_account_lane import HEALTHY, HOT, UNKNOWN, ClaudeAccount
from scripts.review import closeout_cli
from tests.claude_route_accounts import HOST_ACCOUNT, account, unresolved
from tests.test_delegate import _bind_claude_account_b, _default_account_file
from tests.test_delegate_check_budget import (
    _UNVERIFIED_ROW,
    _account_row,
    _accounts_budget,
    _default_claude_lane,
    _fresh_lane,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
HEADROOM_CAP = 90


# --- row 1: the snapshot read API requires a named account ----------------------------------


def _budget() -> dict:
    return _accounts_budget(_default_claude_lane("near_cap"), {"b": _account_row(89.0)})


READERS = {
    "select_account": lambda payload, **kw: claude_account_lane.select_account(payload, **kw),
    "account_agents": lambda payload, **kw: claude_account_lane.account_agents(payload, **kw),
    "lane_record": lambda payload, **kw: claude_account_lane.lane_record(payload, "claude", **kw),
    "account_weekly_used_pct": lambda payload, **kw: claude_account_lane.account_weekly_used_pct(payload, **kw),
    "capacity_verdict": lambda payload, **kw: claude_account_lane.capacity_verdict(payload, **kw),
}


@pytest.mark.parametrize("reader", sorted(READERS))
def test_snapshot_readers_have_no_default_account(reader):
    read = READERS[reader]
    with pytest.raises(TypeError, match="account"):
        read(_budget())
    for bare in (None, "a", "b", ("b", "explicit")):
        with pytest.raises(TypeError, match="named ClaudeAccount"):
            read(_budget(), account=bare)
    read(_budget(), account=HOST_ACCOUNT)


def test_the_claude_lane_is_only_read_for_a_named_account():
    budget = _budget()
    assert claude_account_lane.lane_record(budget, "claude", account=HOST_ACCOUNT)["remaining_pct"] == 0.5
    assert claude_account_lane.lane_record(budget, "claude", account=account("b"))["remaining_pct"] == 89.0
    assert claude_account_lane.other_lane_record(budget, "codex") is budget["agents"]["codex"]
    for lane in ("claude", " Claude "):
        with pytest.raises(ValueError, match="named account"):
            claude_account_lane.other_lane_record(budget, lane)
    with pytest.raises(TypeError):
        claude_account_lane.select_account(budget, account("b"))  # keyword only


def test_an_unresolved_account_reads_route_facts_with_an_unknown_meter():
    budget = _budget()
    view, evidence = claude_account_lane.select_account(budget, account=unresolved("claude_account_binding_missing"))
    claude = view["agents"]["claude"]
    assert claude["status"] == "unknown" and claude["freshness"] == "unavailable"
    assert claude["health"] == budget["agents"]["claude"]["health"]  # a route fact no account owns
    assert "remaining_pct" not in claude and "codexbar" not in claude
    assert evidence == {"label": None, "meter": None, "state": "unresolved", "reason": "claude_account_binding_missing"}
    assert claude_account_lane.account_weekly_used_pct(budget, account=unresolved("claude_account_unknown")) is None


@pytest.mark.parametrize(
    ("label", "source", "refusal"),
    [
        ("c", "explicit", None),
        ("b", "guessed", None),
        ("b", "explicit", "claude_account_unknown"),
        (None, "unresolved", None),
        (None, "unresolved", "not_a_registered_code"),
        (None, "builtin", "claude_account_unknown"),
    ],
)
def test_a_route_key_account_is_a_resolved_label_or_a_registered_refusal(label, source, refusal):
    with pytest.raises(ValueError, match="invalid Claude account route key"):
        ClaudeAccount(label, source, refusal)


def test_mypy_refuses_a_claude_reading_without_a_named_account(tmp_path):
    """Type-check half of row 1: a missing account or a bare label is a mypy error at the call site."""
    snippet = tmp_path / "snippet.py"
    snippet.write_text(
        "from scripts.agent_runtime.model_pause import account_used_pct, routing_budget_used_pct\n"
        "from scripts.fleet.claude_account_lane import lane_record, select_account\n"
        "\n"
        "payload: dict = {}\n"
        "select_account(payload)\n"
        'select_account(payload, account="b")\n'
        'lane_record(payload, "claude", account=None)\n'
        'routing_budget_used_pct("claude")\n'
        'account_used_pct("b")\n'
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--follow-imports=silent",
            "--no-incremental",
            "--config-file",
            str(REPO_ROOT / "pyproject.toml"),
            str(snippet),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    errors = [line.split(": error: ", 1)[1] for line in result.stdout.splitlines() if ": error: " in line]
    assert result.returncode == 1, result.stdout + result.stderr
    assert errors == [
        'Missing named argument "account" for "select_account"  [call-arg]',
        'Argument "account" to "select_account" has incompatible type "str"; expected "ClaudeAccount"  [arg-type]',
        'Argument "account" to "lane_record" has incompatible type "None"; expected "ClaudeAccount"  [arg-type]',
        'Missing named argument "account" for "routing_budget_used_pct"  [call-arg]',
        'Argument 1 to "account_used_pct" has incompatible type "str"; expected "ClaudeAccount | None"  [arg-type]',
    ]


# --- row 5: every final claude route resolves and binds its account before admission ----------


def _dispatch_args(*argv: str):
    return delegate.build_parser().parse_args(["dispatch", "--task-id", "route-key", "--prompt", "x", *argv])


def _review_args(agent: str):
    return _dispatch_args(
        "--agent", agent, "--mode", "read-only", "--require-review-verdict", "--review-author-model", "gpt-6.1-sol"
    )


def test_a_claude_request_on_an_unresolvable_account_is_refused(tmp_path, monkeypatch):
    _default_account_file(tmp_path, monkeypatch, b"c\n")
    with pytest.raises(attempt_boundary.ClaudeAccountRefused, match="claude_account_default_file_invalid"):
        delegate._resolve_dispatch_claude_account(_dispatch_args("--agent", "claude"))


@pytest.mark.parametrize("agent", ["codex", "agy", "cursor"])
def test_another_seats_review_resolves_the_account_a_claude_reviewer_would_run_as(tmp_path, monkeypatch, agent):
    _default_account_file(tmp_path, monkeypatch, b"c\n")
    assert delegate._resolve_dispatch_claude_account(_review_args(agent)) == unresolved(
        "claude_account_default_file_invalid"
    )
    _default_account_file(tmp_path, monkeypatch, b"b\n")
    for bound, expected in (
        (False, unresolved("claude_account_binding_missing")),
        (True, account("b", "default-file")),
    ):
        login = tmp_path / ("bound" if bound else "unbound")
        login.mkdir(mode=0o700)
        _bind_claude_account_b(login, monkeypatch, bound=bound)
        assert delegate._resolve_dispatch_claude_account(_review_args(agent)) == expected


def test_another_seats_ordinary_dispatch_reaches_no_claude_route_and_reads_no_account(tmp_path, monkeypatch):
    _default_account_file(tmp_path, monkeypatch, b"c\n")
    monkeypatch.setattr(
        attempt_boundary, "resolve_dispatch_claude_account", lambda *_a, **_k: pytest.fail("read the account file")
    )
    resolved = delegate._resolve_dispatch_claude_account(_dispatch_args("--agent", "codex"))
    assert resolved == claude_account_lane.no_claude_account()
    with pytest.raises(attempt_boundary.ClaudeAccountRefused, match="claude_account_seat_unsupported"):
        delegate._resolve_dispatch_claude_account(_dispatch_args("--agent", "codex", "--claude-account", "b"))


def test_no_dispatch_fallback_maps_onto_a_claude_seat():
    """Why an ordinary dispatch of another seat has no claude account: no fallback can reach claude."""
    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    fallbacks = load_dispatch_fallbacks(delegate._FALLBACK_SUBS_PATH)
    assert fallbacks and "claude" not in set(fallbacks.values())


def test_admission_refuses_any_final_claude_route_on_an_unresolved_account():
    """The backstop: whatever step chose claude, admission refuses it on an unresolved account."""

    def route(request):
        assert request.claude_account == unresolved("claude_account_default_file_invalid")
        return "claude", "claude-opus-5-5", "route:fixture"

    with pytest.raises(MechanicalAdmissionRefused, match="CLAUDE_ACCOUNT_REFUSED: claude_account_default_file_invalid"):
        target_admission.resolve_and_admit(
            ("codex",),
            mode="read-only",
            route=route,
            new_dispatch=True,
            claude_account=unresolved("claude_account_default_file_invalid"),
        )
    (target,) = target_admission.resolve_and_admit(
        ("codex",),
        mode="read-only",
        route=lambda request: ("codex", "gpt-6.1-sol", "route:fixture"),
        new_dispatch=True,
        claude_account=unresolved("claude_account_default_file_invalid"),
    )
    assert target.recipient == "codex"


def test_a_new_or_review_dispatch_must_name_the_account():
    for flags in ({"new_dispatch": True}, {"review_dispatch": True}):
        with pytest.raises(TypeError, match="names the ClaudeAccount"):
            target_admission.resolve_and_admit(("codex",), mode="read-only", **flags)
    # Messaging and other admissions make no claude reading.
    (target,) = target_admission.resolve_and_admit(("codex",), mode="bridge")
    assert target.recipient == "codex"


def test_no_record_names_an_unresolved_account():
    args = _dispatch_args("--agent", "codex")
    code = "claude_account_default_file_invalid"
    with pytest.raises(attempt_boundary.ClaudeAccountRefused, match=code):
        delegate._claude_account_state(args, unresolved(code), "claude")
    assert delegate._claude_account_state(args, unresolved(code), "codex") == {}
    assert delegate._claude_account_state(args, account("b", "default-file"), "claude") == {
        "claude_account": "b",
        "claude_account_source": "default-file",
        "claude_account_user_scope_omitted": True,
    }


# --- row 3: the five decision consumers agree on one snapshot and one account -----------------


def _agreement_snapshot(a_state: str, b_row: dict | None) -> dict:
    if a_state == "unknown":
        lane = {"status": "unknown", "freshness": "unavailable", "health": {"healthy": True}}
    else:
        lane = _default_claude_lane(a_state)
        lane["codexbar"]["stale"] = False  # the producer publishes the probe's stale flag
    budget = _accounts_budget(lane, {"b": b_row})
    for seat in ("grok", "cursor"):
        budget["agents"][seat] = _fresh_lane(
            status="cool", remaining_pct=80.0, codexbar={"weekly_remaining_pct": 80.0, "will_last_to_reset": True}
        )
    budget["diagnostics"] = {"records_loaded": 5, "stale": False, "codexbar_data_available": True}
    return budget


# case: (lane row state of account a, account b's row, default-account file, owner verdict)
AGREEMENT_CASES = {
    "a_hot": ("near_cap", _account_row(89.0), b"a\n", HOT),
    "a_healthy": ("healthy", _account_row(0.5), b"a\n", HEALTHY),
    "a_unknown": ("unknown", _account_row(89.0), None, UNKNOWN),
    "b_healthy_while_a_is_hot": ("near_cap", _account_row(89.0), b"b\n", HEALTHY),
    "b_hot_while_a_is_healthy": ("healthy", _account_row(0.5), b"b\n", HOT),
    "b_unknown_meter": ("healthy", _UNVERIFIED_ROW, b"b\n", UNKNOWN),
    "b_without_a_row": ("healthy", None, b"b\n", UNKNOWN),
    "unresolved_default_file": ("healthy", _account_row(89.0), b"c\n", UNKNOWN),
    "unbound_b": ("near_cap", _account_row(89.0), b"unbound-b", UNKNOWN),
}


def _route_key_for(tmp_path, monkeypatch, default_file: bytes | None) -> ClaudeAccount:
    """Set the operator's default-account file, then resolve the account the way every consumer does."""
    if default_file == b"unbound-b":
        _bind_claude_account_b(tmp_path, monkeypatch, bound=False)
        default_file = b"b\n"
    elif default_file == b"b\n":
        _bind_claude_account_b(tmp_path, monkeypatch)
    if default_file is None:
        monkeypatch.setenv("LU_CLAUDE_DEFAULT_ACCOUNT_FILE", "")
    else:
        _default_account_file(tmp_path, monkeypatch, default_file)
    return claude_account_lane.resolve_route_account(None, strict=False)


def _guard_verdict(monkeypatch, capsys, budget: dict, route_account: ClaudeAccount) -> str:
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: {})
    sink: dict = {}
    try:
        seat = delegate._resolve_agent_with_budget_guard(
            "claude", fallbacks={"claude": "codex"}, diagnostic_sink=sink, claude_account=route_account
        )
    except delegate.BudgetGuardRefuseError as exc:
        # Only an unresolved account refuses before any reading: the claude seat is removed.
        assert "CLAUDE_ACCOUNT_REFUSED" in str(exc) and not route_account.resolved
        return UNKNOWN
    err = capsys.readouterr().err
    assert sink["claude_account"]["label"] == route_account.label
    if seat != "claude":
        assert "HARD AUTO-SUBSTITUTE" in err
        return HOT
    if sink["capacity"] == "verified":
        assert "ROUTING CHECK UNKNOWN" not in err
        return HEALTHY
    assert sink["capacity"] in {"unknown", "unknown_stale"}
    if route_account.label != "a":
        assert f"ROUTING CHECK UNKNOWN: claude account {route_account.label} meter unavailable" in err
    return UNKNOWN


def _headroom_verdict(tmp_path, monkeypatch, budget: dict, route_account: ClaudeAccount) -> str:
    policy = {"headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": HEADROOM_CAP}]}
    monkeypatch.setattr(model_pause.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps(budget)))
    used = model_pause.routing_budget_used_pct("claude", account=route_account)
    held = model_pause.refusal_reason(
        "claude-opus-5-5", policy=policy, used_pct=model_pause.account_used_pct(route_account)
    )
    assert (held is not None) == (used is not None and used >= HEADROOM_CAP)
    return UNKNOWN if used is None else HOT if held else HEALTHY


def _admission_selects_claude(budget: dict, route_account: ClaudeAccount) -> bool:
    """Reviewer admission for a GPT author at critical risk, given the raw snapshot: does it keep claude?"""
    seat, _model = target_admission._resolve_review_target(
        "claude",
        "claude-opus-5-5",
        author_model="gpt-6.1-sol",
        risk="critical",
        profile="code",
        attempt=False,
        snapshot=budget,
        budget_seat="claude",
        owned_paths=("ordinary.py",),
        claude_account=route_account,
    )
    return seat == "claude"


def _closeout_selects_claude(tmp_path, capsys, budget: dict, route_account: ClaudeAccount) -> bool:
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(budget))
    closeout_cli.main(
        [
            "--state-file",
            str(tmp_path / "state.json"),
            "resolve-reviewer",
            "--author-model",
            "gpt-6.1-sol",
            "--risk",
            "critical",
            "--owned-path",
            "ordinary.py",
            "--routing-snapshot-file",
            str(path),
        ]
    )
    result = json.loads(capsys.readouterr().out)
    if not route_account.resolved:
        assert result["claude_account_unresolved"] == route_account.refusal
    elif route_account.label != "a":
        assert result["claude_account"]["label"] == route_account.label
    return (result["selected"] or {}).get("route") == "claude"


@pytest.mark.parametrize("case", sorted(AGREEMENT_CASES))
def test_the_five_decision_consumers_agree_on_one_snapshot_and_account(case, tmp_path, monkeypatch, capsys):
    a_state, b_row, default_file, expected = AGREEMENT_CASES[case]
    budget = _agreement_snapshot(a_state, b_row)
    route_account = _route_key_for(tmp_path, monkeypatch, default_file)
    if case.startswith("unresolved") or case.startswith("unbound"):
        assert not route_account.resolved
    else:
        assert route_account.label == ("b" if default_file == b"b\n" else "a")

    verdicts = {
        "claude_account_lane": claude_account_lane.capacity_verdict(budget, account=route_account),
        "delegate budget guard": _guard_verdict(monkeypatch, capsys, budget, route_account),
        "model_pause headroom": _headroom_verdict(tmp_path, monkeypatch, budget, route_account),
    }
    admitted = _admission_selects_claude(budget, route_account)
    selected = _closeout_selects_claude(tmp_path, capsys, budget, route_account)

    assert verdicts == dict.fromkeys(verdicts, expected)
    # Reviewer selection keeps a claude seat exactly when its account is resolved and not hot:
    # a hot meter excludes it for capacity, an unknown one is advisory, an unresolved account removes it.
    keeps_claude = route_account.resolved and expected != HOT
    assert {"target_admission": admitted, "closeout_cli": selected} == dict.fromkeys(
        ("target_admission", "closeout_cli"), keeps_claude
    )
