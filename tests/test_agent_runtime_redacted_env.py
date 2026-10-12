"""Environment values remain usable without appearing in plan diagnostics."""

import copy
import dataclasses
import json
import logging
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
from scripts.agent_runtime.redacted_env import RedactedEnv

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


def run_failing_comparison(tmp_path, plan_type, verbosity, comparison, left_env, right_env, value=SENTINEL):
    repo = Path(__file__).resolve().parents[1]
    config = tmp_path / "pytest.ini"
    config.write_text("[pytest]\n", encoding="utf-8")
    module = tmp_path / "test_plan_failure.py"
    module.write_text(
        "import os, sys\n"
        f"sys.path.insert(0, {str(repo)!r})\n"
        "from tests.test_agent_runtime_redacted_env import make_plan, plan_env\n"
        f"from {plan_type.__module__} import {plan_type.__name__}\n"
        "def test_plan_equality():\n"
        f"    left = make_plan({plan_type.__name__}, {left_env})\n"
        f"    right = make_plan({plan_type.__name__}, {right_env})\n"
        f"    assert {comparison}\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(config),
            str(module),
            verbosity,
            "-p",
            "no:cacheprovider",
            "--color=no",
            "--showlocals",
        ],
        env={
            **os.environ,
            "PYTHONPATH": str(repo / "scripts"),
            "PLAN_TEST_VALUE": value,
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTEST_ADDOPTS": "",
            "PYTEST_PLUGINS": "",
        },
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "AssertionError" in output, output
    assert "1 failed" in output, output
    assert f">       assert {comparison}" in output, output
    assert "E       AssertionError: assert " in output, output
    return output


@pytest.mark.parametrize("plan_type", (InvocationPlan, HermesInvocationContext, CommitTree))
@pytest.mark.parametrize("verbosity", ("-q", "-vv"))
def test_real_pytest_plan_assertion_does_not_expose_values(tmp_path, plan_type, verbosity):
    output = run_failing_comparison(
        tmp_path,
        plan_type,
        verbosity,
        "left == right",
        "{'A': os.environ['PLAN_TEST_VALUE'], 'B': 'same'}",
        "{'A': 'different', 'B': 'same'}",
    )
    assert SENTINEL not in output, output


@pytest.mark.parametrize("plan_type", (InvocationPlan, HermesInvocationContext, CommitTree))
@pytest.mark.parametrize("verbosity", ("-q", "-vv"))
@pytest.mark.parametrize(
    ("comparison", "right_env", "exposes_value"),
    (
        ("left == right", "{'K': 'x\\nother'}", False),
        ("plan_env(left) == {'K': 'x\\nother'}", "{}", False),
        ("plan_env(left)['K'] == 'x\\nother'", "{}", True),
    ),
    ids=("plan", "plain-dict", "direct-value-known-limit"),
)
def test_real_pytest_multiline_comparison_redaction_boundary(
    tmp_path, plan_type, verbosity, comparison, right_env, exposes_value
):
    output = run_failing_comparison(
        tmp_path,
        plan_type,
        verbosity,
        comparison,
        "{'K': os.environ['PLAN_TEST_VALUE']}",
        right_env,
        value="prefix\n" + SENTINEL,
    )
    assert (SENTINEL in output) is exposes_value, output
    if exposes_value:
        assert f"E         + {SENTINEL}" in output, output


@pytest.mark.parametrize("plan_type", (InvocationPlan, HermesInvocationContext, CommitTree))
@pytest.mark.parametrize("verbosity", ("-q", "-vv"))
@pytest.mark.parametrize(
    ("comparison", "left_env", "right_env"),
    (
        ("plan_env(left) == {'A': 'different'}", "{'A': os.environ['PLAN_TEST_VALUE']}", "{}"),
        ("plan_env(left) == plan_env(right)", "{'A': os.environ['PLAN_TEST_VALUE']}", "{'A': 'different'}"),
        ("plan_env(left) == {}", "{'A': os.environ['PLAN_TEST_VALUE']}", "{}"),
        (
            "plan_env(left) == plan_env(right)",
            "{'A': os.environ['PLAN_TEST_VALUE'], 'B': 'left'}",
            "{'A': os.environ['PLAN_TEST_VALUE'], 'B': 'right'}",
        ),
        ("{} == plan_env(right)", "{}", "{'A': os.environ['PLAN_TEST_VALUE']}"),
    ),
    ids=("plain-dict", "differing", "left-extra", "common", "right-extra"),
)
def test_real_pytest_env_assertion_does_not_expose_values(
    tmp_path, plan_type, verbosity, comparison, left_env, right_env
):
    output = run_failing_comparison(tmp_path, plan_type, verbosity, comparison, left_env, right_env)
    assert SENTINEL not in output, output


@pytest.mark.parametrize(
    ("plan_type", "attributes", "tuple_text", "plan_text"),
    (
        (
            InvocationPlan,
            "{'cmd': ['agent'], 'cwd': PosixPath('.'), 'stdin_payload': '', 'output_file': None, "
            "'env_overrides': RedactedEnv(names=['A']), 'env_unsets': (), 'liveness_paths': (), "
            "'metadata': {}, 'host_harness': None}",
            "(['agent'], PosixPath('.'), '', None, RedactedEnv(names=['A']), (), (), {}, None)",
            "InvocationPlan(cmd=['agent'], cwd=PosixPath('.'), stdin_payload='', output_file=None, "
            "env_overrides=RedactedEnv(names=['A']), env_unsets=(), liveness_paths=(), metadata={}, host_harness=None)",
        ),
        (
            HermesInvocationContext,
            "{'config': {}, 'env_overrides': RedactedEnv(names=['A']), 'metadata': {}}",
            "({}, RedactedEnv(names=['A']), {})",
            "HermesInvocationContext(config={}, env_overrides=RedactedEnv(names=['A']), metadata={})",
        ),
        (
            CommitTree,
            "{'repo': PosixPath('.'), 'commit': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', "
            "'env': RedactedEnv(names=['A'])}",
            "(PosixPath('.'), 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', RedactedEnv(names=['A']))",
            "CommitTree(repo=PosixPath('.'), commit='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', env=RedactedEnv(names=['A']))",
        ),
    ),
)
def test_plan_attribute_serialization_and_logging_redact_values(plan_type, attributes, tuple_text, plan_text, caplog):
    plan = make_plan(plan_type, {"A": SENTINEL})
    for result in (repr(vars(plan)), repr(plan.__dict__), repr(dataclasses.asdict(plan))):
        assert result == attributes
        assert SENTINEL not in result
    result = repr(dataclasses.astuple(plan))
    assert result == tuple_text
    assert SENTINEL not in result
    logger = logging.getLogger(__name__)
    with caplog.at_level(logging.INFO, logger=__name__):
        logger.info("plan=%s", plan)
        logger.info("plan=%r", plan)
    str_text = "in commit aaaaaaaaaaaa" if plan_type is CommitTree else plan_text
    assert [record.getMessage() for record in caplog.records] == [f"plan={str_text}", f"plan={plan_text}"]
    assert SENTINEL not in caplog.text


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


@pytest.mark.parametrize("operation", ("init", "setitem", "update", "pairs", "setdefault", "ior", "fromkeys"))
def test_env_mutations_redact_value_representations(operation):
    env = RedactedEnv()
    if operation == "init":
        env = RedactedEnv(A=SENTINEL)
    elif operation == "setitem":
        env["A"] = SENTINEL
    elif operation == "update":
        env.update({"A": SENTINEL})
    elif operation == "pairs":
        env.update((("A", "unused"),), A=SENTINEL)
    elif operation == "setdefault":
        assert env.setdefault("A", SENTINEL) == SENTINEL
        assert env.setdefault("A", "unused") == SENTINEL
    elif operation == "ior":
        env |= {"A": SENTINEL}
    else:
        env = RedactedEnv.fromkeys(["A"], SENTINEL)
    assert env == {"A": SENTINEL}
    assert str(env["A"]) == SENTINEL
    for plain in (dict(env), {**env}):
        assert type(plain) is dict
        assert plain == {"A": SENTINEL}
    assert list(env) == ["A"]
    assert repr(env) == "RedactedEnv(names=['A'])"
    assert repr(list(env.items())) == "[('A', <redacted>)]"
    assert repr(list(env.values())) == "[<redacted>]"
    assert SENTINEL not in repr(list(env.items()))
    assert json.loads(json.dumps(env)) == {"A": SENTINEL}


def test_env_setdefault_and_fromkeys_preserve_default_none():
    env = RedactedEnv()
    assert env.setdefault("A") is None
    assert env == {"A": None}
    assert RedactedEnv.fromkeys(["A"]) == {"A": None}


@pytest.mark.parametrize("plan_type", (InvocationPlan, HermesInvocationContext, CommitTree))
@pytest.mark.parametrize("conversion", (dict, lambda env: {**env}), ids=("dict", "unpack"))
@pytest.mark.parametrize("value", (SENTINEL, "prefix\n" + SENTINEL), ids=("single-line", "multiline"))
def test_real_subprocess_receives_original_env_values(plan_type, conversion, value):
    env = conversion(plan_env(make_plan(plan_type, {"A": value})))
    assert type(env) is dict
    assert str(env["A"]) == value
    assert json.loads(json.dumps(env)) == {"A": value}
    result = subprocess.run(
        [sys.executable, "-c", "import os; print(os.environ['A'])"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert result.stdout == value + "\n"
    assert result.stderr == ""


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


@pytest.mark.parametrize("value", (SENTINEL, "prefix\n" + SENTINEL), ids=("single-line", "multiline"))
def test_runner_passes_plain_dict_with_original_values_to_popen(monkeypatch, tmp_path, value):
    plan = InvocationPlan(cmd=["agent"], cwd=tmp_path, env_overrides={"A": value})
    popen = Mock()
    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    runner._spawn_pipe_subprocess(plan.cmd, cwd=plan.cwd, env=plan.env_overrides, stdin=subprocess.DEVNULL)
    env = popen.call_args.kwargs["env"]
    assert type(env) is dict
    assert env == {"A": value}


@pytest.mark.parametrize("value", (SENTINEL, "prefix\n" + SENTINEL), ids=("single-line", "multiline"))
def test_commit_tree_optional_env_and_plain_dict_subprocess_seam(monkeypatch, value):
    assert CommitTree(repo=Path("."), commit="a" * 40).env is None
    run = Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=b"result"))
    monkeypatch.setattr(subprocess, "run", run)
    tree = make_plan(CommitTree, {"A": value})
    assert tree._git("show") == b"result"
    assert type(run.call_args.kwargs["env"]) is dict
    assert run.call_args.kwargs["env"] == {"A": value}
