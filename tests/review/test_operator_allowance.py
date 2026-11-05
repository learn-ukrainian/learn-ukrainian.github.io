"""Operator-signed ACP consult allowance (scripts/review/operator_allowance.py).

Each test signs records with a throwaway ed25519 key made by ``ssh-keygen`` in
``tmp_path`` and points the module's fixed signer path at a temporary file. Only
this harness replaces those module attributes; production code has no other way
to change them. Provider execution is the only thing mocked in the end-to-end
admission tests: route admission, the launch check, adapter construction and the
durable receipts all run for real.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters import acpx as acpx_module
from scripts.agent_runtime.result import ParseResult
from scripts.review import model_catalog
from scripts.review import operator_allowance as oa

pytestmark = pytest.mark.skipif(shutil.which("ssh-keygen") is None, reason="needs OpenSSH ssh-keygen")

ASTRA = "gpt-6-astra"
FABLE = "claude-fable-5-1"
FABLE_ALIAS = "claude-fable-5-1-thinking-high"
TASK = "task-allow-1"
ASTRA_REFUSAL = "ACP participant 'codex' refuses non-active model 'gpt-6-astra'"
FABLE_REFUSAL = (
    "ACP participant 'claude' refuses model 'claude-fable-5-1' (claude-fable-5-1) holds no ACP ask, consult "
    "or discussion role in the model catalog (roles: long_horizon_coding, orchestration; "
    "review_scheduler.activity_roles.consult, #9583)"
)


def _stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _keygen(path: Path) -> Path:
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "test", "-f", str(path)], check=True, timeout=30
    )
    return path


class Harness:
    """A temporary operator key, pinned signer file and per-user record directory."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.tmp = tmp_path
        self.monkeypatch = monkeypatch
        self.key = _keygen(tmp_path / "operator_key")
        self.signers = tmp_path / "trust" / "allowed_signers"
        self.signers.parent.mkdir()
        self.pin(self.key)
        monkeypatch.setattr(oa, "_SIGNERS_PATH", self.signers)
        monkeypatch.setattr(oa, "_TRUSTED_OWNER_UID", os.getuid())
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
        self.records = oa.allowance_dir()
        self.records.mkdir(parents=True)
        self.now = datetime.now(UTC).replace(microsecond=0)

    def pin(self, key: Path, *, identity: str = oa.SIGNER_IDENTITY, namespace: str = oa.SIGNATURE_NAMESPACE) -> None:
        public = key.with_name(key.name + ".pub").read_text(encoding="utf-8").strip()
        self.signers.write_text(f'{identity} namespaces="{namespace}" {public}\n', encoding="utf-8")
        self.signers.chmod(0o644)

    def record(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "schema": oa.ALLOWANCE_SCHEMA,
            "model": ASTRA,
            "activity": "consult",
            "scope": {"kind": "window"},
            "order_ref": "chat-2026-11-05",
            "issued_at": _stamp(self.now - timedelta(minutes=5)),
            "expires_at": _stamp(self.now + timedelta(hours=1)),
        }
        base.update(overrides)
        return base

    def write(
        self,
        record: dict[str, object] | None = None,
        *,
        name: str = "allowance",
        raw: bytes | None = None,
        key: Path | None = None,
        namespace: str = oa.SIGNATURE_NAMESPACE,
        sign: bool = True,
    ) -> Path:
        data = (
            raw
            if raw is not None
            else (json.dumps(record or self.record(), sort_keys=True, separators=(",", ":")).encode() + b"\n")
        )
        path = self.records / f"{name}.json"
        path.write_bytes(data)
        if sign:
            subprocess.run(
                ["ssh-keygen", "-q", "-Y", "sign", "-f", str(key or self.key), "-n", namespace, str(path)],
                check=True,
                timeout=30,
            )
        return path

    def find(self, model: str = ASTRA, task_id: str = TASK, **kwargs: object) -> oa.OperatorAllowance | None:
        options: dict[str, object] = {"purpose": "consult", "sealed_review": False}
        options.update(kwargs)
        return oa.find_consult_allowance(model, task_id=task_id, **options)


@pytest.fixture
def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Harness:
    return Harness(tmp_path, monkeypatch)


# ---------- signature, signer file and record validation (A4) ----------


def test_valid_window_allowance_verifies_and_names_itself(harness: Harness) -> None:
    harness.write()
    allowance = harness.find()
    assert allowance is not None
    receipt = allowance.receipt()
    assert receipt["model"] == ASTRA
    assert receipt["activity"] == "consult"
    assert receipt["scope"] == {"kind": "window"}
    assert receipt["order_ref"] == "chat-2026-11-05"
    assert len(receipt["record_sha256"]) == 64


def test_production_defaults_admit_nothing_without_the_root_installed_signer_file(
    harness: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness.write()
    monkeypatch.setattr(oa, "_SIGNERS_PATH", Path("/etc/learn-ukrainian/operator-allowance-signers"))
    monkeypatch.setattr(oa, "_TRUSTED_OWNER_UID", 0)
    if not oa._SIGNERS_PATH.exists():
        assert harness.find() is None


def test_signer_source_ignores_environment_and_caller_inputs(harness: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    rogue = _keygen(harness.tmp / "rogue_key")
    rogue_signers = harness.tmp / "rogue_signers"
    public = rogue.with_name("rogue_key.pub").read_text(encoding="utf-8").strip()
    rogue_signers.write_text(f'{oa.SIGNER_IDENTITY} namespaces="lu-allowance" {public}\n', encoding="utf-8")
    for name in ("LU_ALLOWANCE_SIGNERS", "LU_OPERATOR_ALLOWANCE_SIGNERS", "SSH_ALLOWED_SIGNERS"):
        monkeypatch.setenv(name, str(rogue_signers))
    (harness.records / "allowed_signers").write_text(rogue_signers.read_text(encoding="utf-8"), encoding="utf-8")
    harness.write(key=rogue)
    assert harness.find() is None


@pytest.mark.parametrize(
    "case",
    ["unsigned", "wrong_key", "wrong_namespace", "tampered", "non_canonical", "malformed", "duplicate_key"],
)
def test_unauthenticated_or_altered_records_are_refused(harness: Harness, case: str) -> None:
    if case == "unsigned":
        harness.write(sign=False)
    elif case == "wrong_key":
        harness.write(key=_keygen(harness.tmp / "self_issued"))
    elif case == "wrong_namespace":
        harness.write(namespace="file")
    elif case == "tampered":
        path = harness.write()
        path.write_bytes(path.read_bytes().replace(b"chat-2026-11-05", b"chat-2026-11-06"))
    elif case == "non_canonical":
        harness.write(raw=json.dumps(harness.record(), indent=1).encode())
    elif case == "malformed":
        harness.write(raw=b'{"schema":')
    else:
        canonical = json.dumps(harness.record(), sort_keys=True, separators=(",", ":"))
        harness.write(raw=(canonical[:-1] + ',"model":"gpt-6-astra"}').encode())
    assert harness.find() is None


def test_one_byte_difference_after_signing_is_refused(harness: Harness) -> None:
    path = harness.write()
    assert harness.find() is not None
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    assert harness.find() is None


def test_signer_identity_must_be_the_fixed_operator_principal(harness: Harness) -> None:
    harness.pin(harness.key, identity="someone@else")
    harness.write()
    assert harness.find() is None


@pytest.mark.parametrize("case", ["replaced", "user_owned", "group_writable", "world_writable", "symlink", "missing"])
def test_untrusted_signer_file_is_refused(harness: Harness, monkeypatch: pytest.MonkeyPatch, case: str) -> None:
    harness.write()
    assert harness.find() is not None
    if case == "replaced":
        harness.pin(_keygen(harness.tmp / "replacement"))
    elif case == "user_owned":
        monkeypatch.setattr(oa, "_TRUSTED_OWNER_UID", 0)
    elif case == "group_writable":
        harness.signers.chmod(0o664)
    elif case == "world_writable":
        harness.signers.chmod(0o646)
    elif case == "symlink":
        target = harness.tmp / "trust" / "real_signers"
        harness.signers.rename(target)
        harness.signers.symlink_to(target)
    else:
        harness.signers.unlink()
    assert harness.find() is None


def test_writable_signer_directory_is_refused(harness: Harness) -> None:
    harness.write()
    harness.signers.parent.chmod(0o777)
    try:
        assert harness.find() is None
    finally:
        harness.signers.parent.chmod(0o755)


@pytest.mark.parametrize(
    ("overrides", "call_model"),
    [
        ({"model": "gpt-9-imaginary"}, "gpt-9-imaginary"),
        ({"model": FABLE_ALIAS}, FABLE_ALIAS),
        ({"model": FABLE}, FABLE_ALIAS),
        ({"activity": "review"}, ASTRA),
        ({"schema": "lu-operator-allowance.v0"}, ASTRA),
        ({"order_ref": ""}, ASTRA),
        ({"scope": {}}, ASTRA),
        ({"scope": {"kind": "task"}}, ASTRA),
        ({"scope": {"kind": "window", "task_id": TASK}}, ASTRA),
        ({"scope": {"kind": "forever"}}, ASTRA),
        ({"issued_at": "2026-11-05 09:00:00"}, ASTRA),
    ],
    ids=[
        "unknown-model",
        "alias-record",
        "alias-call",
        "review-activity",
        "schema",
        "empty-order",
        "missing-scope",
        "task-without-id",
        "both-scopes",
        "unknown-scope",
        "bad-time",
    ],
)
def test_invalid_record_fields_are_refused(harness: Harness, overrides: dict, call_model: str) -> None:
    harness.write(harness.record(**overrides))
    assert harness.find(call_model) is None


def test_missing_scope_key_is_refused(harness: Harness) -> None:
    record = harness.record()
    del record["scope"]
    harness.write(record)
    assert harness.find() is None


def test_window_scope_is_capped_at_24_hours(harness: Harness) -> None:
    start = harness.now - timedelta(minutes=1)
    harness.write(harness.record(issued_at=_stamp(start), expires_at=_stamp(start + timedelta(hours=24))), name="a")
    assert harness.find() is not None
    (harness.records / "a.json").unlink()
    harness.write(
        harness.record(issued_at=_stamp(start), expires_at=_stamp(start + timedelta(hours=24, seconds=1))), name="b"
    )
    assert harness.find() is None


def test_clock_boundaries_are_issued_inclusive_and_expiry_exclusive(harness: Harness) -> None:
    issued = harness.now - timedelta(minutes=5)
    expires = harness.now + timedelta(minutes=5)
    harness.write(harness.record(issued_at=_stamp(issued), expires_at=_stamp(expires)))
    assert harness.find(now=issued) is not None
    assert harness.find(now=expires - timedelta(seconds=1)) is not None
    assert harness.find(now=issued - timedelta(seconds=1)) is None
    assert harness.find(now=expires) is None
    allowance = harness.find()
    assert allowance is not None
    assert not allowance.admits(ASTRA, activity="consult", task_id=TASK, now=expires)


def test_expired_record_is_refused(harness: Harness) -> None:
    harness.write(
        harness.record(
            issued_at=_stamp(harness.now - timedelta(hours=2)), expires_at=_stamp(harness.now - timedelta(hours=1))
        )
    )
    assert harness.find() is None


def test_task_scope_admits_only_its_own_task(harness: Harness) -> None:
    harness.write(harness.record(scope={"kind": "task", "task_id": TASK}))
    allowance = harness.find(task_id=TASK)
    assert allowance is not None
    assert allowance.receipt()["scope"] == {"kind": "task", "task_id": TASK}
    assert harness.find(task_id="task-allow-2") is None
    assert not allowance.admits(ASTRA, activity="consult", task_id="task-allow-2")
    assert not allowance.admits(ASTRA, activity="consult", task_id=None)


@pytest.mark.parametrize(
    "kwargs", [{"purpose": None}, {"purpose": "review"}, {"purpose": "consult", "sealed_review": True}]
)
def test_only_an_explicit_unsealed_consult_purpose_reads_an_allowance(harness: Harness, kwargs: dict) -> None:
    harness.write()
    assert harness.find(**kwargs) is None


def test_allowances_cannot_be_forged_in_process(harness: Harness) -> None:
    harness.write()
    genuine = harness.find()
    assert genuine is not None
    with pytest.raises(TypeError):
        oa.OperatorAllowance(
            model=ASTRA,
            activity="consult",
            scope_kind="window",
            task_id=None,
            order_ref="x",
            issued_at=harness.now,
            expires_at=harness.now + timedelta(hours=1),
            record_sha256="0" * 64,
        )
    with pytest.raises(TypeError):
        with oa.activate(object()):  # type: ignore[arg-type]
            pass
    assert not genuine.admits(ASTRA, activity="review", task_id=TASK)


# ---------- catalog gates (b) and (d) ----------


def test_catalog_gates_admit_consult_only_with_a_matching_allowance(harness: Harness) -> None:
    harness.write(harness.record(model=FABLE), name="fable")
    harness.write(harness.record(model=ASTRA), name="astra")
    fable = harness.find(FABLE)
    astra = harness.find(ASTRA)
    assert fable is not None and astra is not None

    assert "holds no ACP ask, consult or discussion role" in model_catalog.activity_role_refusal(FABLE, "consult")
    assert model_catalog.activity_role_refusal(FABLE, "consult", consult_allowance=fable, consult_task_id=TASK) is None
    assert "red-team exception expired" in model_catalog.retired_model_refusal(ASTRA)
    assert model_catalog.retired_model_refusal(ASTRA, consult_allowance=astra, consult_task_id=TASK) is None
    assert model_catalog.activity_role_refusal(ASTRA, "consult", consult_allowance=astra, consult_task_id=TASK) is None
    # The wrong model's allowance, the review activity and a review context never use it.
    assert model_catalog.activity_role_refusal(FABLE, "consult", consult_allowance=astra, consult_task_id=TASK)
    assert model_catalog.activity_role_refusal(FABLE, "review", consult_allowance=fable, consult_task_id=TASK)
    assert model_catalog.activity_role_refusal(ASTRA, "review", consult_allowance=astra, consult_task_id=TASK)
    assert model_catalog.retired_model_refusal(
        ASTRA,
        consult_allowance=astra,
        consult_task_id=TASK,
        review_context={"review_mode": "red_team"},
    )


# ---------- generic helpers stay allowance-free (A3) ----------


@pytest.fixture
def ambient_allowances(harness: Harness):
    """Valid allowances for both models on disk, and one installed as the active consult allowance."""
    harness.write(harness.record(model=FABLE), name="fable")
    harness.write(harness.record(model=ASTRA), name="astra")
    astra = harness.find(ASTRA)
    assert astra is not None
    with oa.activate(astra):
        yield harness


def _outcome(call):
    try:
        return ("ok", call())
    except Exception as exc:
        return (type(exc).__name__, str(exc))


def _same_with_and_without(harness: Harness, call) -> None:
    with_allowance = _outcome(call)
    with oa.activate(None):
        harness.monkeypatch.setenv("XDG_CONFIG_HOME", str(harness.tmp / "empty-config"))
        without = _outcome(call)
        harness.monkeypatch.setenv("XDG_CONFIG_HOME", str(harness.tmp / "config"))
    assert with_allowance == without


@pytest.mark.parametrize("model", [FABLE, ASTRA])
def test_target_admission_review_refusal_ignores_allowances(ambient_allowances: Harness, model: str) -> None:
    from scripts.agent_runtime import target_admission

    _same_with_and_without(ambient_allowances, lambda: target_admission._refuse_non_review_models([model]))
    assert _outcome(lambda: target_admission._refuse_non_review_models([model]))[0] != "ok"


@pytest.mark.parametrize(("model", "family"), [(FABLE, "anthropic"), (ASTRA, "openai")])
def test_record_cf_verdict_reviewer_admission_ignores_allowances(
    ambient_allowances: Harness, model: str, family: str
) -> None:
    from scripts.review import record_cf_verdict

    def call():
        return record_cf_verdict._require_formal_reviewer(cursor=False, reported=None, model=model, family=family)

    _same_with_and_without(ambient_allowances, call)
    with pytest.raises(record_cf_verdict.RecordError, match="reviewer model refused"):
        call()


@pytest.mark.parametrize("model", [FABLE, ASTRA])
def test_reviewer_resolver_never_selects_an_allowed_model(ambient_allowances: Harness, model: str) -> None:
    from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, evaluate_candidate, resolve_reviewer
    from tests.claude_route_accounts import HOST_ACCOUNT

    route = "claude" if model == FABLE else "codex"
    author = "gpt-6.1-sol" if route == "claude" else "claude-opus-5-5"
    base = next(candidate for candidate in REVIEW_CANDIDATES.values() if candidate.route == route)

    def evaluated():
        result = evaluate_candidate(
            replace(base, concrete_model=model),
            ResolverInputs(author_model=author, risk="low", claude_account=HOST_ACCOUNT),
        )
        return result.status, result.reason

    def pinned():
        resolution = resolve_reviewer(
            ResolverInputs(
                author_model=author,
                risk="low",
                pinned_candidate=model,
                pressure_override_reason="allowance leak probe",
                claude_account=HOST_ACCOUNT,
            )
        )
        return getattr(resolution.selected, "name", None), resolution.fail_closed_reason

    _same_with_and_without(ambient_allowances, evaluated)
    _same_with_and_without(ambient_allowances, pinned)
    assert pinned()[0] is None


@pytest.mark.parametrize("model", [FABLE, ASTRA])
def test_catalog_ladder_validation_ignores_allowances(ambient_allowances: Harness, model: str) -> None:
    """A ladder or formal reviewer list naming an allowed model still fails catalog validation."""
    catalog = json.loads(json.dumps(model_catalog.load_model_catalog()))
    risk = next(iter(catalog["review_scheduler"]["risk_reviewer_models"]))
    catalog["review_scheduler"]["risk_reviewer_models"][risk] = [model]
    if model == ASTRA:
        catalog["models"][ASTRA].pop("red_team_only")
        catalog["models"][ASTRA]["roles"] = ["long_horizon_coding"]

    def call():
        return model_catalog._validate_activity_role_holders(catalog)

    _same_with_and_without(ambient_allowances, call)
    with pytest.raises(model_catalog.ModelCatalogError, match="no review"):
        call()


@pytest.mark.parametrize("model", [FABLE, ASTRA])
def test_substitution_admission_ignores_allowances(ambient_allowances: Harness, model: str) -> None:
    catalog = model_catalog.load_model_catalog()
    for lane in ("claude", "codex", "acpx-claude-shadow", "acpx-codex-shadow"):
        _same_with_and_without(
            ambient_allowances, lambda lane=lane: model_catalog.substitution_model_admitted(catalog, lane, model)
        )
    # Astra stays refused as a substitute; Fable keeps exactly its pre-allowance answer.
    assert model_catalog.substitution_model_admitted(catalog, "codex", ASTRA) is False


@pytest.mark.parametrize(("model", "transport"), [(FABLE, "native_claude"), (ASTRA, "native_codex")])
def test_execution_model_check_ignores_allowances(ambient_allowances: Harness, model: str, transport: str) -> None:
    _same_with_and_without(
        ambient_allowances, lambda: model_catalog.require_execution_model(model, transport=transport)
    )


def test_astra_execution_stays_refused_under_an_allowance(ambient_allowances: Harness) -> None:
    with pytest.raises(model_catalog.ModelCatalogError, match="red-team exception expired"):
        model_catalog.require_execution_model(ASTRA, transport="native_codex")


def test_public_invoke_launch_check_ignores_an_active_allowance(ambient_allowances: Harness) -> None:
    for tool_config in (None, {}, {"acpx_transport": True}):
        _same_with_and_without(
            ambient_allowances, lambda tc=tool_config: runner._refuse_retired_launch_model("codex", ASTRA, tc)
        )
    with pytest.raises(ValueError, match="red-team exception expired"):
        runner._refuse_retired_launch_model("codex", ASTRA, {"acpx_transport": True})


@pytest.mark.parametrize(
    ("command", "handler", "model"),
    [
        ("ask-codex", "_handle_ask_codex", ASTRA),
        ("ask-claude", "_handle_ask_claude", FABLE),
    ],
)
def test_native_review_routing_is_unchanged_by_allowances(
    ambient_allowances: Harness, monkeypatch: pytest.MonkeyPatch, command: str, handler: str, model: str
) -> None:
    """Review intent from the bridge CLI goes to headless review dispatch, never to an ACP consult."""
    from scripts.ai_agent_bridge import _acp_compat, _cli, _dispatch_wrappers

    monkeypatch.setattr(_acp_compat, "run_compat_ask", Mock(side_effect=AssertionError("ACP ask reached")))
    captured: list[dict] = []

    def fake_dispatch(agent, content, **kwargs):
        captured.append({"agent": agent, **kwargs})
        return {"ok": True, "status": "done", "response": "VERDICT: APPROVED\nEvidence: reviewed diff."}

    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", fake_dispatch)

    def call():
        args = _cli._build_parser().parse_args(
            [command, "question", "--task-id", TASK, "--from", "claude", "--to-model", model, "--type", "review"]
        )
        getattr(_cli, handler)(args)
        return captured[-1]["agent"], captured[-1].get("model")

    _same_with_and_without(ambient_allowances, call)


# ---------- end-to-end admission through the runner and real adapters (A1, A2, A4, A5) ----------


def _stub_acp_host(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[object]:
    """Stub the local acpx/Claude Code binaries; capture the plan instead of running a provider."""
    binary = tmp_path / "fake-acpx"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.setattr(acpx_module, "_ACPX_BINARY", binary)
    monkeypatch.setattr(acpx_module, "_probe_acpx_cli_compatibility", lambda _b, *, builtin_agent: ("0.13.0", ()))
    monkeypatch.setattr(acpx_module, "_require_non_primary_worktree", lambda *_a, **_k: None)
    monkeypatch.setattr(acpx_module, "_require_codex_cli", lambda: ("/installed/codex", "0.159.2"))
    monkeypatch.setattr(
        acpx_module,
        "_require_local_claude_acp_adapter",
        lambda _b, *, adapter_label: {
            "claude_acp_adapter_version": "0.64.2",
            "claude_acp_compatibility": "installed>=0.64.2<1",
            "claude_acp_launch_source": "installed",
        },
    )
    monkeypatch.setattr(
        acpx_module,
        "_require_host_claude_code",
        lambda *, model, adapter_label: {
            "claude_code_executable": "/installed/claude/versions/2.1.296",
            "claude_code_launch_identity": "1:2:3:4:5",
            "claude_code_executable_identity": "1:2:3:4000000000:5000000000",
            "claude_code_version": "2.1.296",
            "claude_code_version_floor": "2.1.116",
        },
    )
    monkeypatch.setattr(
        acpx_module, "_require_claude_acp_launcher", lambda *, adapter_label: "/repo/claude_acp_exec.sh"
    )
    plans: list[object] = []
    records: list[dict] = []

    def provider(**kwargs):
        plans.append(kwargs["plan"])
        return runner._ExecutionOutcome(
            parse=ParseResult(ok=True, response="consult answer", stderr_excerpt=None, rate_limited=False),
            duration_s=0.01,
            returncode=0,
            kill_reason=None,
            stdout_text="",
            stderr_text="",
            liveness_paths=(),
        )

    monkeypatch.setattr(runner, "_execute_invocation_plan", provider)
    monkeypatch.setattr(runner, "write_record", records.append)
    plans.append(records)
    return plans


def _invoke(participant: str, model: str, tmp_path: Path, *, task_id: str = TASK, **kwargs):
    return runner.invoke_inter_agent(
        participant,
        "Which of two bounded options is simpler?",
        cwd=tmp_path,
        task_id=task_id,
        correlation_id=task_id,
        idempotency_key=f"idem-{task_id}",
        source="claude-cto",
        model=model,
        **kwargs,
    )


@pytest.mark.parametrize(
    ("participant", "model", "refusal"), [("codex", ASTRA, ASTRA_REFUSAL), ("claude", FABLE, FABLE_REFUSAL)]
)
def test_a1_without_an_allowance_both_consults_are_refused_exactly_as_today(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, participant: str, model: str, refusal: str
) -> None:
    plans = _stub_acp_host(monkeypatch, tmp_path)
    for purpose in (None, "consult"):
        with pytest.raises(runner.InterAgentTransportError) as raised:
            _invoke(participant, model, tmp_path, purpose=purpose)
        assert str(raised.value) == refusal
    assert plans == [[]]


@pytest.mark.parametrize(("participant", "model"), [("codex", ASTRA), ("claude", FABLE)])
def test_a2_a5_a_valid_consult_allowance_admits_and_is_recorded_durably(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, participant: str, model: str
) -> None:
    harness.write(harness.record(model=model, scope={"kind": "task", "task_id": TASK}))
    plans = _stub_acp_host(monkeypatch, tmp_path)
    records = plans.pop()

    result = _invoke(participant, model, tmp_path, purpose="consult")

    assert result.ok is True
    plan = plans[0]
    assert ("--model", model) in list(zip(plan.cmd, plan.cmd[1:], strict=False))
    allowance = result.usage_record["operator_allowance"]
    assert allowance["model"] == model
    assert allowance["activity"] == "consult"
    assert allowance["scope"] == {"kind": "task", "task_id": TASK}
    assert allowance["order_ref"] == "chat-2026-11-05"
    assert [record["operator_allowance"] for record in records] == [allowance]

    from scripts.ai_agent_bridge import _acp_compat

    stored = _acp_compat._result_receipt(result, model_requested=model)
    assert json.loads(stored)["operator_allowance"] == allowance
    replayed = _acp_compat._replay_result(stored)
    assert replayed.usage_record["operator_allowance"] == allowance


@pytest.mark.parametrize(("participant", "model"), [("codex", ASTRA), ("claude", FABLE)])
def test_a4_allowance_is_not_reused_across_tasks_or_for_sealed_or_undeclared_calls(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, participant: str, model: str
) -> None:
    harness.write(harness.record(model=model, scope={"kind": "task", "task_id": TASK}))
    plans = _stub_acp_host(monkeypatch, tmp_path)
    sealed = tmp_path / "sealed.json"
    sealed.write_text("{}", encoding="utf-8")
    attempts = [
        {"task_id": "task-allow-2", "purpose": "consult"},
        {"purpose": None},
        {"purpose": "consult", "sealed_review_mcp_config": sealed},
    ]
    for attempt in attempts:
        with pytest.raises(runner.InterAgentTransportError, match="refuses"):
            _invoke(participant, model, tmp_path, **attempt)
    with pytest.raises(runner.InterAgentTransportError, match="purpose"):
        _invoke(participant, model, tmp_path, purpose="review")
    assert plans == [[]]


def test_a4_alias_call_is_refused_even_with_a_canonical_allowance(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    harness.write(harness.record(model=FABLE))
    _stub_acp_host(monkeypatch, tmp_path)
    with pytest.raises(runner.InterAgentTransportError, match="holds no ACP ask, consult or discussion role"):
        _invoke("claude", FABLE_ALIAS, tmp_path, purpose="consult")


def test_a4_an_allowance_does_not_open_another_participant_transport(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    harness.write(harness.record(model=FABLE))
    _stub_acp_host(monkeypatch, tmp_path)
    with pytest.raises(runner.InterAgentTransportError, match="does not implement catalog transport 'cursor'"):
        _invoke("cursor", FABLE, tmp_path, purpose="consult")


@pytest.mark.parametrize(
    ("adapter_cls", "model"), [(acpx_module.AcpxAdapter, ASTRA), (acpx_module.AcpxClaudeShadowAdapter, FABLE)]
)
def test_adapter_allow_lists_refuse_without_the_installed_allowance(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, adapter_cls, model: str
) -> None:
    """The adapters read only the allowance invoke_inter_agent installed, never one on disk."""
    harness.write(harness.record(model=model))
    _stub_acp_host(monkeypatch, tmp_path)
    tool_config = {
        "acpx_transport": True,
        "target_agent": adapter_cls.target_agent if hasattr(adapter_cls, "target_agent") else "codex",
        "correlation_id": TASK,
        "idempotency_key": "idem",
    }
    target = tool_config["target_agent"]
    scope = acpx_module.active_communication_scope(source="claude-cto", agent=target, target_agent=target)
    with scope, pytest.raises(acpx_module.AcpxShadowRefusalError, match="rejected"):
        adapter_cls().build_invocation(
            prompt="p",
            mode="read-only",
            cwd=tmp_path,
            model=model,
            task_id=TASK,
            session_id=None,
            tool_config=tool_config,
        )


def test_cursor_allow_list_ignores_an_installed_allowance(harness: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    assert acpx_module.AcpxCursorShadowAdapter.operator_allowance_eligible is False
    assert acpx_module.AcpxClaudeShadowAdapter.operator_allowance_eligible is True


def _discussion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from scripts.agent_runtime import acpx_discuss

    monkeypatch.setattr(acpx_discuss, "classify_repo_path", lambda *_a, **_k: "dispatch_worktree")
    synthesis = Mock(
        side_effect=lambda *_a, **_k: runner.Result(
            ok=True,
            agent="synthesis",
            model="fixture",
            mode="read-only",
            response="synthesis",
            stderr_excerpt=None,
            duration_s=0.01,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={"outcome": "ok"},
        )
    )
    controller = acpx_discuss.AcpxDiscussionController(root=tmp_path / "plane", synthesis_call=synthesis)
    return acpx_discuss, controller


def _discuss(controller, tmp_path: Path, key: str):
    return controller.run(
        prompt="Compare two bounded options.",
        cwd=tmp_path,
        task_id=TASK,
        correlation_id=TASK,
        idempotency_key=key,
        rounds=1,
        participants=("codex", "claude"),
        models={"codex": ASTRA},
        source="claude-cto",
    )


def test_a1_discussion_refuses_astra_without_an_allowance(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plans = _stub_acp_host(monkeypatch, tmp_path)
    acpx_discuss, controller = _discussion(tmp_path, monkeypatch)
    try:
        with pytest.raises(acpx_discuss.AcpxDiscussionError) as raised:
            _discuss(controller, tmp_path, "idem-discuss-none")
    finally:
        controller.close()
    assert str(raised.value) == f"invalid ACP participant selection for 'codex': {ASTRA_REFUSAL}"
    assert plans == [[]]


def test_a2_a5_discussion_leg_runs_astra_under_an_allowance_and_records_it(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    harness.write(harness.record(model=ASTRA, scope={"kind": "task", "task_id": TASK}))
    plans = _stub_acp_host(monkeypatch, tmp_path)
    records = plans.pop()
    _acpx_discuss, controller = _discussion(tmp_path, monkeypatch)
    try:
        payload = _discuss(controller, tmp_path, "idem-discuss-allowed")
    finally:
        controller.close()
    assert payload["state"] == "COMPLETE", payload
    pinned = [("--model", ASTRA) in list(zip(plan.cmd, plan.cmd[1:], strict=False)) for plan in plans]
    assert pinned.count(True) == 1 and len(plans) == 2
    allowed = [record["operator_allowance"] for record in records if "operator_allowance" in record]
    assert allowed and all(entry["model"] == ASTRA and entry["scope"]["task_id"] == TASK for entry in allowed)
    assert all("operator_allowance" not in record for record in records if record.get("model") != ASTRA)
