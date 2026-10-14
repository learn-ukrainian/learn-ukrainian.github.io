"""Muse transport and fail-closed mode contract (#10511)."""

import json

import pytest


def adapter():
    from scripts.agent_runtime.adapters.muse import MuseAdapter

    return MuseAdapter()


def build(tmp_path, **kwargs):
    return adapter().build_invocation(
        prompt=kwargs.pop("prompt", "bounded public code task"),
        mode=kwargs.pop("mode", "read-only"),
        cwd=tmp_path,
        model=kwargs.pop("model", "muse-wonder-1.0"),
        task_id="muse-test",
        session_id=None,
        tool_config=kwargs.pop("tool_config", None),
        **kwargs,
    )


def event(kind, payload):
    return json.dumps({"payload_type": kind, "payload": payload})


def parse(stdout, **kwargs):
    return adapter().parse_response(
        stdout=stdout,
        stderr=kwargs.pop("stderr", ""),
        returncode=kwargs.pop("returncode", 0),
        output_file=None,
        **kwargs,
    )


@pytest.mark.parametrize("model", ["muse-wonder-1.0", "muse-wonder-full-1.0"])
@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_unproven_modes_refuse_before_creating_files(tmp_path, mode, model):
    from scripts.agent_runtime.adapters.muse import MuseGuardParityRefused

    with pytest.raises(MuseGuardParityRefused, match="MUSE_GUARD_PARITY_UNPROVEN"):
        build(tmp_path, mode=mode, model=model)
    assert list(tmp_path.iterdir()) == []


def test_refusal_creates_no_prompt_even_for_large_or_secret_input(tmp_path):
    with pytest.raises(ValueError) as refused:
        build(tmp_path, prompt="synthetic_secret_token" * 20000)
    assert "synthetic_secret_token" not in str(refused.value)
    assert list(tmp_path.iterdir()) == []


def test_terminal_and_usage_model_attestation():
    stream = "\n".join(
        [
            event(
                "task.lifecycle.status",
                {
                    "event": {
                        "details": {
                            "facets": [{"kind": "producer", "detail": {"provider": "meta", "model": "muse-wonder-1.0"}}]
                        }
                    }
                },
            ),
            event("session.tokenUsage", {"usage": {"inputTokens": 10, "outputTokens": 5, "reasoningTokens": 3}}),
            event("task.lifecycle.proposed", {"event": {"task_kind": "tool.read_file"}}),
            event("run.terminal.completed", {"terminal": "completed", "text": "42"}),
        ]
    )
    result = parse(stream)
    assert result.ok and result.response == "42"
    assert result.tokens == 15
    assert result.substitution["reasoning_tokens"] == 3
    assert len(result.tool_calls) == 1
    assert result.substitution["actual_model"] == "muse-wonder-1.0"
    assert result.substitution["actual_model_known"] is True


@pytest.mark.parametrize(
    "stream,code",
    [
        ("", 0),
        ("{bad", 0),
        ("[]", 0),
        (event("run.terminal.completed", {"terminal": "completed", "text": "42"}) + "\n{bad", 0),
        (event("run.terminal.completed", {"terminal": "completed", "text": "42"}), 1),
        (event("run.terminal.failed", {"terminal": "failed", "text": "partial"}), 0),
    ],
)
def test_incomplete_malformed_and_nonzero_fail_closed(stream, code):
    result = parse(stream, returncode=code, stderr="authorization: Bearer synthetic_secret_token")
    assert result.ok is False
    assert "synthetic_secret_token" not in (result.stderr_excerpt or "")
    assert result.response == ""


def test_unattested_identity_is_unknown():
    result = parse(event("run.terminal.completed", {"terminal": "completed", "text": "42"}))
    assert result.ok
    assert result.substitution["source"] == "unattested-harness"
    assert result.substitution["actual_model"] is None


@pytest.mark.parametrize("separator", ["\x85", "\u2028", "\u2029"])
def test_jsonl_preserves_unicode_separators_inside_response(separator):
    response = "before" + separator + "after"
    stream = json.dumps(
        {"payload_type": "run.terminal.completed", "payload": {"terminal": "completed", "text": response}},
        ensure_ascii=False,
    )
    result = parse(stream + "\n")
    assert result.ok is True
    assert result.response == response


def test_liveness_is_stdout_only(tmp_path):
    from scripts.agent_runtime.adapters.base import InvocationPlan

    assert adapter().liveness_signal_paths(InvocationPlan(cmd=["muse"], cwd=tmp_path)) == ()


def test_configured_identity_is_not_attestation():
    stream = (
        event("run.model.configured", {"model_id": "muse-wonder-1.0"})
        + "\n"
        + event("run.terminal.completed", {"terminal": "completed", "text": "42"})
    )
    result = parse(stream)
    assert result.substitution["actual_model"] is None
    assert result.tokens is None


def test_requested_model_and_substitution_are_observable(tmp_path):
    from scripts.agent_runtime.adapters.base import InvocationPlan

    plan = InvocationPlan(cmd=["muse", "--model", "muse-wonder-1.0"], cwd=tmp_path)
    stream = (
        event(
            "task.lifecycle.status",
            {
                "event": {
                    "details": {
                        "facets": [{"kind": "producer", "detail": {"provider": "meta", "model": "other-model"}}]
                    }
                }
            },
        )
        + "\n"
        + event("run.terminal.completed", {"terminal": "completed", "text": "42"})
    )
    assert parse(stream, plan=plan).substitution["substituted"] is True


def test_mislabeled_and_duplicate_terminal_records_fail():
    assert not parse(event("run.terminal.failed", {"terminal": "completed", "text": "42"})).ok
    terminal = event("run.terminal.completed", {"terminal": "completed", "text": "42"})
    assert not parse(terminal + "\n" + terminal).ok


def test_native_held_probe_receipt_is_parsed_with_unknown_usage():
    # A minimal held native event pair, with no synthetic usage.
    stream = event(
        "task.lifecycle.status",
        {
            "event": {
                "details": {
                    "phase": "stream_succeeded",
                    "facets": [
                        {
                            "kind": "producer",
                            "detail": {"kind": "provider", "provider": "meta", "model": "muse-wonder-1.0"},
                        }
                    ],
                }
            }
        },
    )
    stream += "\n" + event("run.terminal.completed", {"terminal": "completed", "text": "ANSWER=42"})
    result = parse(stream)
    assert result.ok and result.response == "ANSWER=42"
    assert result.tokens is None and result.substitution["actual_model"] == "muse-wonder-1.0"
