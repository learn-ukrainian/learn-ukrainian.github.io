"""Environment values remain usable without appearing in plan diagnostics."""

import copy
import dataclasses
import json
import os
import pickle
import pprint
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters.acpx import InvocationPlan as AcpxInvocationPlan
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.hermes_common import HermesInvocationContext
from scripts.agent_runtime.kimi_admission import CommitTree

SENTINEL = "sentinel-not-a-real-value-XYZ"
PLAN_TYPES = (InvocationPlan, AcpxInvocationPlan, HermesInvocationContext, CommitTree)


def make_plan(plan_type, env):
    if plan_type is HermesInvocationContext:
        return plan_type(config={}, env_overrides=env, metadata={})
    if plan_type is CommitTree:
        return plan_type(repo=Path("."), commit="a" * 40, env=env)
    return plan_type(cmd=["agent"], cwd=Path("."), env_overrides=env)


def plan_env(plan):
    return plan.env if isinstance(plan, CommitTree) else plan.env_overrides


@pytest.mark.parametrize("plan_type", PLAN_TYPES)
def test_plan_diagnostics_and_copies_redact_values(plan_type):
    plan = make_plan(plan_type, {"B": SENTINEL, "A": "another-value"})
    for candidate in (
        plan,
        copy.copy(plan),
        copy.deepcopy(plan),
        pickle.loads(pickle.dumps(plan)),
        dataclasses.replace(plan),
    ):
        for output in (repr(candidate), str(candidate), f"{candidate}", pprint.pformat(candidate, width=1)):
            assert SENTINEL not in output
        env = plan_env(candidate)
        assert repr(env) == "RedactedEnv(names=['A', 'B'])"
        assert str(env) == repr(env)
        assert pprint.pformat(env, width=1) == repr(env)
        assert env == {"A": "another-value", "B": SENTINEL}
        assert json.loads(json.dumps(env)) == dict(env)
        assert make_plan(plan_type, dict(env)) == candidate
        assert make_plan(plan_type, {"B": "different"}) != candidate


@pytest.mark.parametrize("plan_type", (InvocationPlan, HermesInvocationContext, CommitTree))
@pytest.mark.parametrize("verbosity", ("-q", "-vv"))
def test_real_pytest_plan_assertion_does_not_expose_values(tmp_path, plan_type, verbosity):
    module = tmp_path / "test_plan_failure.py"
    module.write_text(
        "import os, sys\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r})\n"
        "from tests.test_agent_runtime_redacted_env import make_plan\n"
        f"from {plan_type.__module__} import {plan_type.__name__}\n"
        "def test_plan_equality():\n"
        f"    left = make_plan({plan_type.__name__}, {{'A': os.environ['PLAN_TEST_VALUE'], 'B': 'same'}})\n"
        f"    right = make_plan({plan_type.__name__}, {{'A': 'different', 'B': 'same'}})\n"
        "    assert left == right\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(module),
            verbosity,
            "-p",
            "no:cacheprovider",
            "--color=no",
            "--showlocals",
        ],
        env={**os.environ, "PLAN_TEST_VALUE": SENTINEL, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": ""},
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "AssertionError" in output, output
    assert "1 failed" in output, output
    assert SENTINEL not in output, output


def test_env_copy_and_mutation_keep_dict_behavior():
    env = InvocationPlan(cmd=[], cwd=Path("."), env_overrides={"A": SENTINEL}).env_overrides
    for clone in (env.copy(), copy.copy(env), copy.deepcopy(env), pickle.loads(pickle.dumps(env))):
        assert type(clone) is type(env)
        assert clone == {"A": SENTINEL}
        assert SENTINEL not in repr(clone)
        clone["B"] = "new"
        assert list(clone) == ["A", "B"]
        assert clone.pop("A") == SENTINEL
    assert env == {"A": SENTINEL}
    assert type(dict(env)) is dict


@pytest.mark.parametrize("plan_type", (InvocationPlan, HermesInvocationContext, CommitTree))
def test_plan_equality_retains_type_and_other_field_comparisons(plan_type):
    plan = make_plan(plan_type, {"A": SENTINEL})
    assert plan.__eq__(object()) is NotImplemented
    field = "config" if plan_type is HermesInvocationContext else "commit" if plan_type is CommitTree else "cmd"
    value = {"option": True} if field == "config" else "b" * 40 if field == "commit" else ["other-agent"]
    assert dataclasses.replace(plan, **{field: value}) != plan


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_protocols_preserve_env_redaction(protocol):
    env = InvocationPlan(cmd=[], cwd=Path("."), env_overrides={"A": SENTINEL}).env_overrides
    restored = pickle.loads(pickle.dumps(env, protocol=protocol))
    assert type(restored) is type(env)
    assert restored == {"A": SENTINEL}
    assert repr(restored) == "RedactedEnv(names=['A'])"


def test_runner_passes_plain_dict_with_original_values_to_popen(monkeypatch, tmp_path):
    plan = InvocationPlan(cmd=["agent"], cwd=tmp_path, env_overrides={"A": SENTINEL})
    popen = Mock()
    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    runner._spawn_pipe_subprocess(plan.cmd, cwd=plan.cwd, env=plan.env_overrides, stdin=subprocess.DEVNULL)
    env = popen.call_args.kwargs["env"]
    assert type(env) is dict
    assert env == {"A": SENTINEL}


def test_commit_tree_optional_env_and_plain_dict_subprocess_seam(monkeypatch):
    assert CommitTree(repo=Path("."), commit="a" * 40).env is None
    run = Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=b"result"))
    monkeypatch.setattr(subprocess, "run", run)
    tree = make_plan(CommitTree, {"A": SENTINEL})
    assert tree._git("show") == b"result"
    assert type(run.call_args.kwargs["env"]) is dict
    assert run.call_args.kwargs["env"] == {"A": SENTINEL}
