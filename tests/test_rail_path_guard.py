"""Mutation-honest tests for layered rail-path authorization (P6 / #5885)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import types
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from scripts.orchestration import rail_path_guard as guard

NOW = datetime(2026, 7, 28, tzinfo=UTC)
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
TASK = "rail-p6-path-guard"
OWNED_RAIL_PATH = "agents_extensions/shared/hooks/guard-pr-merge.py"
RECEIPT_ID = "rail-approval-" + "1" * 32


class _ReceiptStore:
    source_id = "operator-approval-api"
    source_kind = "api"

    def __init__(self, receipts: dict[str, dict]) -> None:
        self.receipts = receipts

    def fetch_rail_approval_receipt(self, receipt_id: str) -> dict:
        return self.receipts[receipt_id]


class _UnreadableReceiptStore(_ReceiptStore):
    def fetch_rail_approval_receipt(self, receipt_id: str) -> dict:
        raise OSError("approval store unavailable")


class _LocalFileReceiptStore(_ReceiptStore):
    source_kind = "file"


def _receipt(**overrides: object) -> dict:
    receipt = {
        "schema_version": "rail-approval-receipt.v1",
        "receipt_id": RECEIPT_ID,
        "issuer": "operator",
        "issued_at": "2026-07-28T00:00:00Z",
        "expires_at": "2026-07-29T00:00:00Z",
        "action": "rail-path-mutation",
        "task_id": TASK,
        "head_sha": HEAD,
        "owned_paths": [OWNED_RAIL_PATH],
    }
    receipt.update(overrides)
    return receipt


def _verified(**overrides: object) -> guard.VerifiedRailApprovalReceipt:
    receipt = _receipt(**overrides)
    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore({receipt["receipt_id"]: receipt}), now=lambda: NOW
    )
    return resolver.fetch(str(receipt["receipt_id"]))


def _decide(*paths: str, receipt: guard.VerifiedRailApprovalReceipt | None = None, **kwargs):
    return guard.decide_rail_path_mutation(
        task_id=kwargs.pop("task_id", TASK),
        candidate_paths=paths,
        head_sha=kwargs.pop("head_sha", HEAD),
        receipt=receipt,
        now=lambda: NOW,
        **kwargs,
    )


def test_rail_patterns_are_full_path_globs_not_substrings() -> None:
    assert guard.is_rail_path("agents_extensions/shared/rules/model-assignment.md")
    assert guard.is_rail_path("agents_extensions/codex/agents/infra.md")
    assert guard.is_rail_path("scripts/config/trails/rb1.trail.yaml")
    assert guard.is_rail_path("agents_extensions/shared/schemas/trailspec/v2/schema.json")
    assert guard.is_rail_path("scripts/orchestration/rail_status.py")
    assert guard.is_rail_path("scripts/fleet_comms/review_publisher.py")
    assert guard.is_rail_path("scripts/ai_agent_bridge/_review_verdict.py")
    assert not guard.is_rail_path("docs/model_catalog.yaml-not-a-rail")
    assert not guard.is_rail_path("docs/notes/agents_extensions/shared/rules.md")


def test_bracketed_filenames_are_literal_path_candidates() -> None:
    """Glob metacharacters in a filename are data, never candidate patterns."""
    rail_path = ".claude/x[1].md"
    non_rail_path = "docs/some[draft].md"

    assert guard.normalize_repository_path(rail_path) == rail_path
    assert guard.is_rail_path(rail_path) is True
    assert guard.normalize_repository_path(non_rail_path) == non_rail_path
    assert guard.is_rail_path(non_rail_path) is False
    assert guard.rail_paths_from_candidates([rail_path, non_rail_path]) == (rail_path,)


@pytest.mark.parametrize(
    ("path", "message"),
    [
        ("", "non-empty string"),
        ("/docs/example.md", "relative POSIX path"),
        ("docs/../example.md", "not normalized"),
        (r"docs\\example.md", "relative POSIX path"),
    ],
)
def test_normalize_repository_path_keeps_structural_rejections(
    path: str, message: str
) -> None:
    with pytest.raises(guard.RailApprovalReceiptError, match=message):
        guard.normalize_repository_path(path)


def test_receipt_id_grammar_is_identical_in_code_and_the_versioned_schema() -> None:
    schema = json.loads(guard.RAIL_APPROVAL_RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert guard.RAIL_APPROVAL_RECEIPT_ID.fullmatch(RECEIPT_ID)
    assert schema["$defs"]["rail_approval_receipt_id"]["pattern"] == (
        rf"^{guard.RAIL_APPROVAL_RECEIPT_ID_PATTERN}$"
    )


def test_non_rail_paths_are_unaffected_without_receipt() -> None:
    decision = _decide(
        "docs/projects/fleet-trails/rail-system-completion-memo.md",
        task_id="",
        head_sha="not-a-commit",
    )

    assert decision.allowed is True
    assert decision.reason == "non_rail_paths"
    assert decision.rail_paths == ()


def test_production_receipt_uses_one_clock_for_resolution_and_authorization() -> None:
    calls = 0

    def clock() -> datetime:
        nonlocal calls
        calls += 1
        return NOW

    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore({RECEIPT_ID: _receipt()}),
        now=clock,
    )

    decision = guard.decide_rail_path_mutation_with_production_receipt(
        task_id=TASK,
        candidate_paths=[OWNED_RAIL_PATH],
        head_sha=HEAD,
        receipt_id=RECEIPT_ID,
        resolver=resolver,
    )

    assert decision.allowed is True
    assert decision.reason == "rail_approval_verified"
    assert calls == 1


def test_production_receipt_explicit_clock_overrides_resolver_clock() -> None:
    resolver_calls = 0
    explicit_calls = 0

    def resolver_clock() -> datetime:
        nonlocal resolver_calls
        resolver_calls += 1
        return datetime(2026, 7, 30, tzinfo=UTC)

    def explicit_clock() -> datetime:
        nonlocal explicit_calls
        explicit_calls += 1
        return NOW

    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore({RECEIPT_ID: _receipt()}),
        now=resolver_clock,
    )

    decision = guard.decide_rail_path_mutation_with_production_receipt(
        task_id=TASK,
        candidate_paths=[OWNED_RAIL_PATH],
        head_sha=HEAD,
        receipt_id=RECEIPT_ID,
        resolver=resolver,
        now=explicit_clock,
    )

    assert decision.allowed is True
    assert decision.reason == "rail_approval_verified"
    assert explicit_calls == 1
    assert resolver_calls == 0


def test_path_classification_imports_without_jsonschema_but_receipt_validation_denies(
    tmp_path: Path,
) -> None:
    """#5992: only receipt validation, not path classification, needs jsonschema."""
    poison = tmp_path / "poison"
    poison.mkdir()
    (poison / "jsonschema.py").write_text(
        "raise ImportError('jsonschema deliberately masked')\n", encoding="utf-8"
    )
    receipt = _receipt()
    script = f"""
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('masked_rail_guard', {str(Path(__file__).resolve().parents[1] / 'scripts/orchestration/rail_path_guard.py')!r})
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

class Store:
    source_id = 'test-api'
    source_kind = 'api'
    def fetch_rail_approval_receipt(self, receipt_id):
        return {receipt!r}

resolver = module.ApprovedRailApprovalReceiptResolver(Store(), now=lambda: module.datetime(2026, 7, 28, tzinfo=module.UTC))
non_rail = module.decide_rail_path_mutation_with_production_receipt(
    task_id='not-used', candidate_paths=('docs/notes.md',), head_sha={'a' * 40!r}, receipt_id=None
)
rail = module.decide_rail_path_mutation_with_production_receipt(
    task_id={TASK!r}, candidate_paths=({OWNED_RAIL_PATH!r},), head_sha={'a' * 40!r}, receipt_id={RECEIPT_ID!r}, resolver=resolver
)
print(json.dumps({{'non_rail': non_rail.reason, 'rail': rail.reason}}))
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(poison)
    # Mirror tests/test_guard_primary_checkout_write.py's `_python()` fallback:
    # a missing venv must not turn this test into a low-signal FileNotFoundError
    # (sealed review F001 on #6001).
    venv_python = Path(__file__).resolve().parents[1] / ".venv/bin/python"
    python = venv_python if venv_python.exists() else Path(sys.executable)

    result = subprocess.run(
        [str(python), "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "non_rail": "non_rail_paths",
        "rail": "rail_approval_validator_unavailable",
    }


def test_direct_receipt_authorization_maps_missing_validator_to_its_own_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct receipt callers must not misreport a missing validator as invalid."""
    receipt = _direct_payload_receipt()

    def unavailable():
        raise guard.RailApprovalValidatorUnavailableError("validator unavailable")

    monkeypatch.setattr(guard, "_validator", unavailable)

    decision = _decide(OWNED_RAIL_PATH, receipt=receipt)

    assert decision.allowed is False
    assert decision.reason == "rail_approval_validator_unavailable"


def test_rail_path_without_receipt_is_refused() -> None:
    decision = _decide(OWNED_RAIL_PATH)

    assert decision.allowed is False
    assert decision.reason == "rail_approval_receipt_required"
    assert decision.rail_paths == (OWNED_RAIL_PATH,)


def test_valid_receipt_admits_exact_owned_rail_path_and_not_more() -> None:
    """Mutation hooks retain containment semantics for bounded write attempts."""
    receipt = _verified()

    allowed = _decide(OWNED_RAIL_PATH, receipt=receipt)
    extra = _decide("agents_extensions/shared/hooks/guard-admin-merge.py", receipt=receipt)

    assert allowed.allowed is True
    assert allowed.reason == "rail_approval_verified"
    assert extra.allowed is False
    assert extra.reason == "rail_approval_path_mismatch"


def test_merge_guard_requires_the_receipt_owned_paths_to_equal_the_rail_diff() -> None:
    """A PR receipt cannot retain surplus protected paths after its diff changes."""
    extra_rail_path = "scripts/orchestration/rail_path_guard.py"
    superset = _verified(owned_paths=[OWNED_RAIL_PATH, extra_rail_path])

    denied = _decide(
        OWNED_RAIL_PATH,
        receipt=superset,
        path_binding=guard.RailApprovalPathBinding.PR_DIFF_EXACT_SET,
    )
    allowed = _decide(
        OWNED_RAIL_PATH,
        receipt=_verified(),
        path_binding=guard.RailApprovalPathBinding.PR_DIFF_EXACT_SET,
    )

    assert denied.allowed is False
    assert denied.reason == "rail_approval_path_set_mismatch"
    assert allowed.allowed is True
    assert allowed.reason == "rail_approval_verified"


@pytest.mark.parametrize(
    "overrides, kwargs, reason",
    [
        ({}, {"task_id": "other-task"}, "rail_approval_task_mismatch"),
        ({}, {"head_sha": OTHER_HEAD}, "rail_approval_head_mismatch"),
    ],
)
def test_bound_receipt_mismatches_are_refused(overrides, kwargs, reason) -> None:
    receipt = _verified(**overrides)

    decision = _decide(OWNED_RAIL_PATH, receipt=receipt, **kwargs)

    assert decision.allowed is False
    assert decision.reason == reason


def test_expired_receipt_is_refused_by_external_resolver() -> None:
    expired = _receipt(
        issued_at="2026-07-27T00:00:00Z",
        expires_at="2026-07-28T00:00:00Z",
    )
    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore({RECEIPT_ID: expired}), now=lambda: NOW
    )

    with pytest.raises(guard.RailApprovalReceiptError, match="has expired"):
        resolver.fetch(RECEIPT_ID)


def test_forged_or_local_receipts_are_refused_before_decision() -> None:
    forged = _receipt(issuer="self-declared-model-tier")
    with pytest.raises(guard.RailApprovalReceiptError, match="schema violation"):
        guard.ApprovedRailApprovalReceiptResolver(
            _ReceiptStore({RECEIPT_ID: forged}), now=lambda: NOW
        ).fetch(RECEIPT_ID)

    with pytest.raises(guard.RailApprovalReceiptError, match="bridge or API"):
        guard.ApprovedRailApprovalReceiptResolver(_LocalFileReceiptStore({}), now=lambda: NOW)


def test_unreadable_receipt_store_fails_closed() -> None:
    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _UnreadableReceiptStore({}), now=lambda: NOW
    )

    with pytest.raises(guard.RailApprovalReceiptError, match="could not re-fetch"):
        resolver.fetch(RECEIPT_ID)


def test_default_monitor_fetch_does_not_import_bridge_package(monkeypatch: pytest.MonkeyPatch) -> None:
    """The by-file client load preserves its relative import without bridge startup."""
    package_name = "scripts.ai_agent_bridge"
    monkeypatch.setitem(sys.modules, package_name, types.ModuleType(package_name))
    monkeypatch.delitem(sys.modules, f"{package_name}.monitor_client", raising=False)

    class Response:
        status = 200

        def __init__(self) -> None:
            self.headers: dict[str, str] = {}

        def read(self) -> bytes:
            return json.dumps(_receipt()).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *_args, **_kwargs: Response())

    receipt = guard.MonitorRailApprovalReceiptStore().fetch_rail_approval_receipt(RECEIPT_ID)

    assert receipt["receipt_id"] == RECEIPT_ID
    assert f"{package_name}.monitor_client" not in sys.modules


@pytest.mark.parametrize(
    "bypass_claim",
    [
        {"X-Agent": "codex/rail-p6-path-guard"},
        {"model": "gpt-5.6-sol"},
        {"self_declared_tier": "advisor"},
    ],
)
def test_identity_strings_never_bypass_rail_receipt(bypass_claim: dict[str, str]) -> None:
    # A caller can label itself anything it wants. The versioned schema refuses
    # these claims, and the decision API does not accept identity as authority.
    forged = _receipt(**bypass_claim)
    resolver = guard.ApprovedRailApprovalReceiptResolver(
        _ReceiptStore({RECEIPT_ID: forged}), now=lambda: NOW
    )

    with pytest.raises(guard.RailApprovalReceiptError, match="schema violation"):
        resolver.fetch(RECEIPT_ID)


def test_missing_rail_classifier_mutation_is_observable(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the deny-list call is removed, this test turns red rather than passing vacuously."""
    assert _decide(OWNED_RAIL_PATH).allowed is False

    monkeypatch.setattr(guard, "is_rail_path", lambda _path: False)

    assert _decide(OWNED_RAIL_PATH).allowed is True


def test_missing_receipt_binding_mutation_is_observable(monkeypatch: pytest.MonkeyPatch) -> None:
    """If task/head/path binding is removed, this test exposes the newly allowed write."""
    receipt = _verified()
    assert _decide(OWNED_RAIL_PATH, receipt=receipt, task_id="other-task").allowed is False

    monkeypatch.setattr(guard, "_receipt_authorizes", lambda _receipt, **_kwargs: None)

    assert _decide(OWNED_RAIL_PATH, receipt=receipt, task_id="other-task").allowed is True


@pytest.mark.parametrize(
    ("body", "kind"),
    [
        ("", guard.RailApprovalDeclarationKind.MISSING),
        (
            "Rail-Approval-Receipt: rail-approval-" + "a" * 32
            + "\nRail-Approval-Receipt: rail-approval-"
            + "b" * 32,
            guard.RailApprovalDeclarationKind.MULTIPLE,
        ),
        (
            "Rail-Approval-Receipt: rail-approval-" + "A" * 32,
            guard.RailApprovalDeclarationKind.MALFORMED,
        ),
    ],
)
def test_rail_diff_declaration_rejects_absent_multiple_and_malformed_trailers(
    monkeypatch: pytest.MonkeyPatch,
    body: str,
    kind: guard.RailApprovalDeclarationKind,
) -> None:
    """The CI declaration path cannot call the authoritative decision function."""
    monkeypatch.setattr(
        guard,
        "decide_rail_path_mutation",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("CI must not decide authorization")),
    )

    declaration = guard.inspect_rail_approval_declaration(
        candidate_paths=[OWNED_RAIL_PATH],
        body=body,
    )

    assert declaration.kind is kind
    assert declaration.is_present is False
    assert declaration.receipt_id is None


def test_rail_diff_declaration_accepts_one_exact_trailer_without_authorizing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A present declaration remains a locator, even when decision code is unavailable."""
    monkeypatch.setattr(
        guard,
        "decide_rail_path_mutation",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("CI must not decide authorization")),
    )
    body = f"Summary\n\nRail-Approval-Receipt: {RECEIPT_ID}\n"

    declaration = guard.inspect_rail_approval_declaration(
        candidate_paths=[OWNED_RAIL_PATH],
        body=body,
    )

    assert declaration.kind is guard.RailApprovalDeclarationKind.PRESENT
    assert declaration.is_present is True
    assert declaration.receipt_id == RECEIPT_ID


def test_rail_ci_event_dispatch_is_honest_about_declaration_context() -> None:
    pull_request = guard.inspect_rail_ci_event(
        event_name="pull_request",
        candidate_paths=[OWNED_RAIL_PATH],
    )
    merge_group_rail = guard.inspect_rail_ci_event(
        event_name="merge_group",
        candidate_paths=[OWNED_RAIL_PATH],
    )
    merge_group_non_rail = guard.inspect_rail_ci_event(
        event_name="merge_group",
        candidate_paths=["docs/some[draft].md"],
    )
    push = guard.inspect_rail_ci_event(event_name="push")

    assert pull_request.disposition is guard.RailCIEventDisposition.DECLARATION
    assert pull_request.rail_paths == (OWNED_RAIL_PATH,)
    assert merge_group_rail.disposition is guard.RailCIEventDisposition.DENY
    assert merge_group_rail.reason == (
        "merge-queue flow does not carry a rail declaration; "
        "merge rail PRs via the direct auto-merge path"
    )
    assert merge_group_rail.rail_paths == (OWNED_RAIL_PATH,)
    assert merge_group_non_rail.disposition is guard.RailCIEventDisposition.SKIP
    assert merge_group_non_rail.reason == (
        "merge-queue diff has no rail paths; declaration check skipped"
    )
    assert push.disposition is guard.RailCIEventDisposition.SKIP
    assert push.reason == "post-merge informational — enforcement happened at PR time"


def _direct_payload_receipt(**overrides: object) -> guard.VerifiedRailApprovalReceipt:
    """Build a receipt the way a direct-payload caller (delegate.py) can: NO resolver.

    The resolver refuses expired/forged receipts itself, so resolver-built
    fixtures can never exercise the decision layer's own re-checks — which are
    load-bearing for callers that pass a VerifiedRailApprovalReceipt directly.
    Mutation-proven: disabling the decision-layer expiry check previously left
    the whole suite green (orchestrator probe, PR #5980).
    """
    return guard.VerifiedRailApprovalReceipt(
        payload=_receipt(**overrides),
        source_id="bridge:test",
        digest="d" * 64,
    )


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        # Reachable ONLY via a direct payload: schema cannot see the clock.
        # (Ordering stays valid — issued before expiry — but the window is past.)
        (
            {"issued_at": "2026-07-26T00:00:00Z", "expires_at": "2026-07-27T00:00:00Z"},
            "expired_rail_approval_receipt",
        ),
        # Schema enum rejects a forged issuer at the decision layer's re-validation;
        # the in-code APPROVED_ISSUERS check behind it is drift armor for the schema.
        ({"issuer": "self-declared-model-tier"}, "invalid_rail_approval_receipt"),
        ({"task_id": "another-task"}, "rail_approval_task_mismatch"),
        ({"head_sha": "b" * 40}, "rail_approval_head_mismatch"),
        ({"owned_paths": ["scripts/config/trails/other.trail.yaml"]}, "rail_approval_path_mismatch"),
        # Structurally invalid payload (missing required field) → schema refusal.
        ({"head_sha": None}, "invalid_rail_approval_receipt"),
    ],
)
def test_decision_layer_denies_bad_direct_payloads(
    overrides: dict, expected_reason: str
) -> None:
    """Every deny reason of the pure decision layer fires on a direct payload."""
    receipt = _direct_payload_receipt(**overrides)
    decision = _decide(OWNED_RAIL_PATH, receipt=receipt)
    assert decision.allowed is False
    assert decision.reason == expected_reason


def test_ci_gate_requires_the_shared_rail_path_module() -> None:
    """CI declares receipt syntax only; the merge guard remains authoritative."""
    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    rail_job = workflow["jobs"]["rail-path"]
    rail_step = next(
        step
        for step in rail_job["steps"]
        if isinstance(step, dict) and step.get("name") == "Rail approval declaration"
    )
    run_steps = "\n".join(
        str(step.get("run", "")) for step in rail_job["steps"] if isinstance(step, dict)
    )

    assert rail_job["name"] == "Rail approval declaration"
    assert "Rail approval declaration" in [step.get("name") for step in rail_job["steps"] if isinstance(step, dict)]
    assert "edited" in workflow[True]["pull_request"]["types"]
    assert "merge_group" in workflow[True]
    assert workflow[True]["push"]["branches"] == ["main"]
    assert "inspect_rail_approval_declaration" in run_steps
    assert "inspect_rail_ci_event" in run_steps
    assert "RAIL_EVENT_NAME" in run_steps
    assert rail_step["env"]["RAIL_EVENT_NAME"] == "${{ github.event_name }}"
    assert "github.event.merge_group.base_sha" in rail_step["env"]["RAIL_BASE_SHA"]
    assert "github.event.merge_group.head_sha" in rail_step["env"]["RAIL_HEAD_SHA"]
    assert 'event_name in {"push", "workflow_dispatch"}' in run_steps
    assert "RailCIEventDisposition.DENY" in run_steps
    assert "RailCIEventDisposition.SKIP" in run_steps
    assert "decide_rail_path_mutation" not in run_steps
    assert "build_production_rail_approval_receipt_resolver" not in run_steps
    assert "rail-path" in workflow["jobs"]["ci-gate"]["needs"]


@pytest.mark.parametrize(
    ("path", "is_rail"),
    [
        # Sibling deploy targets are the same tamper class as .claude/**.
        (".gemini/hooks/check-claude-inbox.sh", True),
        (".gemini/rules/critical-rules.md", True),
        (".codex/agents/curriculum-orchestrator.toml", True),
        # .agent/** is deliberate runtime-scratch exclusion (babysit/handoffs/tmp):
        # requiring receipts for per-session state would halt live drivers.
        (".agent/claude-infra-babysit-prs.txt", False),
        (".agent/tmp/reviews/some-brief.md", False),
    ],
)
def test_deploy_target_siblings_rail_classification(path: str, is_rail: bool) -> None:
    """Deployed-copy dirs are rails; per-session runtime scratch deliberately is not."""
    assert guard.is_rail_path(guard.normalize_repository_path(path)) is is_rail
