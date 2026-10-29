"""Operator-approved account selection and meter arithmetic checks."""

import dataclasses
import json
from decimal import Decimal

import pytest

from scripts.agent_runtime.codex_accounts import CodexAccountRefused
from scripts.dispatcher import admission, cli, store, worker
from scripts.dispatcher.codex_meter import estimate, task_cost
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import TaskSpec


def test_label_selection_and_ambient_conflict(tmp_path, monkeypatch):
    api = tmp_path / "api"
    api.mkdir(mode=0o700)
    binding = tmp_path / "codex_accounts.json"
    binding.write_text(json.dumps({"schema_version": 1, "accounts": {
        "api": {"codex_home": str(api), "budget_usd": 200}}}))
    binding.chmod(0o600)
    monkeypatch.setenv("LU_CODEX_ACCOUNTS_FILE", str(binding))
    for name in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "CODEX_HOME"):
        monkeypatch.delenv(name, raising=False)
    assert admission.codex_account("codex", None) == {"codex_account": "sub"}
    assert admission.codex_account("codex", "sub") == {"codex_account": "sub"}
    assert admission.codex_account("codex", "api") == {"codex_account": "api"}
    args = cli.build_parser().parse_args(["dispatch", "--agent", "codex", "--model", "gpt-6-luna", "--codex-account", "api"])
    assert args.codex_account == "api"
    spec = TaskSpec("account", "codex", "gpt-6-luna", "high", "read-only", tmp_path,
                    tmp_path / "prompt", tmp_path / "result", codex_account="api")
    env = child_env(spec)
    assert env["CODEX_HOME"] == str(api)
    assert not {"OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN"} & env.keys()
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    spec.prompt_file.write_text("fixture prompt")
    record = store.new_record(spec, {"key": "public", "github": "example/repo"}, "codex/account", "a" * 40, {"research_owned_path": []})
    assert record["codex_account"] == "api"
    assert worker._spec(record, {}).codex_account == "api"
    monkeypatch.setenv("CODEX_HOME", str(api))
    assert child_env(spec)["CODEX_HOME"] == str(api)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    with pytest.raises(CodexAccountRefused, match="codex_account_ambient_conflict"):
        admission.codex_account("codex", "api")
    monkeypatch.delenv("CODEX_HOME")
    for name in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN"):
        monkeypatch.setenv(name, "fixture-credential")
        with pytest.raises(CodexAccountRefused, match="codex_account_ambient_conflict"):
            admission.codex_account("codex", "api")
        with pytest.raises(CodexAccountRefused, match="codex_account_ambient_conflict"):
            child_env(spec)
        # The subscription default retains today's environment behaviour.
        assert admission.codex_account("codex", None) == {"codex_account": "sub"}
        if name != "CODEX_ACCESS_TOKEN":
            assert child_env(dataclasses.replace(spec, codex_account="sub"))[name] == "fixture-credential"
        monkeypatch.delenv(name)
    with pytest.raises(CodexAccountRefused, match="codex_account_unknown"):
        admission.codex_account("codex", "API")
    with pytest.raises(CodexAccountRefused, match="codex_account_seat_unsupported"):
        admission.codex_account("claude", "api")


def test_meter_price_arithmetic(tmp_path):
    usage = {"input_tokens": 1_000_000, "cached_input_tokens": 400_000, "output_tokens": 200_000}
    record = {"agent": "codex", "codex_account": "api", "usage": usage, "status": "done"}
    for model, expected in (("gpt-6-luna", "0.164"), ("gpt-6.1-terra", "1.62"), ("gpt-6.1-sol", "3.24")):
        task = {**record, "model": model}
        assert task_cost(task) == Decimal(expected)
        (tmp_path / f"{model}.json").write_text(json.dumps(task))
    (tmp_path / "sub.json").write_text(json.dumps({**record, "codex_account": "sub"}))
    (tmp_path / "pending.json").write_text(json.dumps({**record, "status": "running", "usage": None}))
    report = estimate(tmp_path, Decimal(200))
    assert Decimal(report["spent_usd"]) == Decimal("5.024")
    assert Decimal(report["remaining_usd"]) == Decimal("194.976")
    assert report["priced_tasks"] == 3
    assert report["pending_tasks"] == 1
    assert report["unknown_tasks"] == 0
    (tmp_path / "unknown.json").write_text(json.dumps({**record, "model": "unknown-model"}))
    report = estimate(tmp_path, Decimal(200))
    assert report["remaining_usd"] is None
    assert report["unknown_tasks"] == 1
    for invalid in ({}, {**usage, "cached_input_tokens": 1_000_001}, {**usage, "output_tokens": -1}):
        with pytest.raises(ValueError):
            task_cost({**record, "model": "gpt-6-luna", "usage": invalid})
