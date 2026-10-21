"""The driver lane registry and the per-host local config (#10814)."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops import driver_lanes as dl
from tests._host_path_guard import assert_no_host_facts

REPO = Path(__file__).resolve().parents[2]


def test_registry_holds_the_seven_lanes_with_generic_launchers() -> None:
    registry = dl.load_registry()
    assert [lane.session for lane in registry.lanes] == [
        "infra-muse", "devops-muse", "harness", "atlas", "practice", "open-model-data", "cto",
    ]
    assert [lane.session for lane in registry.lanes if lane.lead] == ["cto"]
    for lane in registry.lanes:
        assert (REPO / lane.launcher).is_file()
        assert lane.target == f"={lane.session}:"
        if lane.kind == "codex":
            assert lane.path_prepend[0] == "scripts/agent_runtime/shims"
    assert_no_host_facts(dl.DATA_FILE.read_text(encoding="utf-8"), dl.DATA_FILE.name)


def test_lane_models_are_active_catalog_models() -> None:
    from scripts.review.model_catalog import canonical_model_id, load_model_catalog, retired_model_refusal

    catalog = load_model_catalog()
    for lane in dl.load_registry().lanes:
        assert canonical_model_id(lane.model, catalog) == lane.model, lane.session
        assert retired_model_refusal(lane.model, catalog) is None, lane.session


def test_practice_lane_uses_the_infra_claude_pattern() -> None:
    registry = dl.load_registry()
    lane = registry.by_session("practice")
    infra = registry.by_session("infra-muse")
    assert (lane.name, lane.kind, lane.epic, lane.sender) == (
        "practice", "claude", "practice", "claude-practice",
    )
    assert lane.goal == ".claude/practice-epic/DRIVER-STATE.md"
    assert (lane.launcher, lane.model, lane.effort) == (
        "start-claude-driver.sh", "claude-sonnet-5-5", "high",
    )
    assert lane.account_env == infra.account_env == ("CLAUDE_CONFIG_DIR",)
    assert lane.provider_args == infra.provider_args == ("--dangerously-skip-permissions",)
    assert lane.kick == infra.kick.replace("Infra", "Practice").replace("infra", "practice")
    assert dl.generic_argv(lane) == (
        "./start-claude-driver.sh", "--epic", "practice", "--model", "claude-sonnet-5-5",
        "--effort", "high", lane.kick, "--", "--dangerously-skip-permissions",
    )
    plan = dl.launch_plan(lane, repo_root=REPO, local={})
    assert plan.env == {}  # Account choice belongs to ignored local config.


def test_generic_command_is_repo_relative() -> None:
    lane = dl.load_registry().by_session("harness")
    argv = dl.generic_argv(lane)
    assert argv[:4] == ("./start-codex-driver.sh", "--epic", "monitor", "--model")
    assert argv[-2:] == ("--effort", lane.effort)
    claude = dl.generic_argv(dl.load_registry().by_session("infra-muse"))
    assert claude[-2:] == ("--", "--dangerously-skip-permissions")


def test_local_wrapper_and_env_override_the_generic_launch(tmp_path: Path) -> None:
    local = tmp_path / "local.json"
    local.write_text(json.dumps({"lanes": {"infra-muse": {"wrapper": "lane-wrapper-infra", "env": {"CLAUDE_CONFIG_DIR": "x"}}}}))
    local.chmod(0o600)
    overrides = dl.load_local_config(local)
    plan = dl.launch_plan(dl.load_registry().by_session("infra-muse"), repo_root=tmp_path, local=overrides)
    assert plan.command == "lane-wrapper-infra" and plan.wrapper
    assert plan.env == {"CLAUDE_CONFIG_DIR": "x"}
    assert plan.describe()["env_keys"] == ["CLAUDE_CONFIG_DIR"]
    assert "x" not in json.dumps(plan.describe()["env_keys"])


def test_missing_local_config_means_no_overrides(tmp_path: Path) -> None:
    assert dl.load_local_config(tmp_path / "absent.json") == {}


@pytest.mark.parametrize("mode", [0o620, 0o602])
def test_writable_local_config_is_refused(tmp_path: Path, mode: int) -> None:
    local = tmp_path / "local.json"
    local.write_text("{}")
    local.chmod(mode)
    with pytest.raises(dl.LaneConfigError, match="writable"):
        dl.load_local_config(local)


def test_symlinked_local_config_is_refused(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    real.write_text("{}")
    real.chmod(0o600)
    link = tmp_path / "local.json"
    link.symlink_to(real)
    with pytest.raises(dl.LaneConfigError, match="symlink"):
        dl.load_local_config(link)


def test_local_config_path_defaults_to_xdg_config_home() -> None:
    assert dl.default_local_config_path({"XDG_CONFIG_HOME": "/cfg"}) == Path("/cfg/learn-ukrainian/driver-lanes.local.json")
    assert dl.default_local_config_path({"LU_DRIVER_LANES_LOCAL": "/x.json"}) == Path("/x.json")


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d["lanes"][0].update(session="%7"), "plain tmux session"),
        (lambda d: d["lanes"][0].update(launcher="/abs/start.sh"), "repo-relative"),
        (lambda d: d["lanes"][1].update(session="infra-muse"), "duplicate"),
        (lambda d: d["lanes"][0].update(kind="gemini"), "kind"),
        (lambda d: d.update(claude_handoff_pct=0), "claude_handoff_pct"),
    ],
)
def test_invalid_lane_data_is_rejected(mutate, message: str) -> None:
    data = json.loads(dl.DATA_FILE.read_text(encoding="utf-8"))
    mutate(data)
    with pytest.raises(dl.LaneConfigError, match=message):
        dl.parse_registry(data)


@pytest.mark.parametrize("style", ["file", "module"])
def test_cli_prints_the_registry_both_ways(style: str) -> None:
    argv = [str(REPO / "scripts/ops/driver_lanes.py")] if style == "file" else ["-m", "scripts.ops.driver_lanes"]
    result = subprocess.run(
        [sys.executable, *argv], cwd=REPO, capture_output=True, text=True, check=True, timeout=60,
        env={**os.environ, "PYTHONPATH": ""},
    )
    payload = json.loads(result.stdout)
    assert payload["settings"]["claude_handoff_pct"] == 70
    assert payload["lanes"][-1]["target"] == "=cto:"


# ---- wrappers never reach a shell (review of 69264fbb, #10814) ---------------------
def write_local(tmp_path: Path, lanes: dict) -> Path:
    local = tmp_path / "local.json"
    local.write_text(json.dumps({"lanes": lanes}), encoding="utf-8")
    local.chmod(0o600)
    return local


@pytest.mark.parametrize(
    "wrapper",
    [
        "printf expected; printf INJECTED",
        "lane-wrapper&&touch",
        "lane-wrapper$(id)",
        "lane-wrapper`id`",
        "lane-wrapper>out",
        "lane-wrapper<in",
        "lane-wrapper|tee",
        "lane-wrapper\ntouch",
        "lane wrapper",
        "lane-wrapper\t",
        "~/lane-wrapper",
        "",
        42,
        [],
        ["lane-wrapper", "x;touch"],
        ["lane-wrapper", "$(id)"],
        ["lane-wrapper", "a b"],
        ["lane-wrapper", 7],
        ["--lane-wrapper"],
    ],
)
def test_wrapper_with_shell_syntax_is_refused_for_that_lane_only(tmp_path: Path, wrapper: object) -> None:
    overrides = dl.load_local_config(write_local(tmp_path, {
        "cto": {"wrapper": wrapper},
        "harness": {"wrapper": ["lane-wrapper-harness", "--profile=monitor"]},
    }))
    registry = dl.load_registry()
    with pytest.raises(dl.LaneConfigError, match="local lane config: cto: "):
        dl.launch_plan(registry.by_session("cto"), repo_root=tmp_path, local=overrides)
    plan = dl.launch_plan(registry.by_session("harness"), repo_root=tmp_path, local=overrides)
    assert plan.argv == ("lane-wrapper-harness", "--profile=monitor") and plan.wrapper


@pytest.mark.parametrize(
    ("wrapper", "argv"),
    [
        ("/opt/lanes/cto-wrapper.sh", ("/opt/lanes/cto-wrapper.sh",)),
        (["lane-wrapper", "--dir", "a/b.c", "--n=2"], ("lane-wrapper", "--dir", "a/b.c", "--n=2")),
    ],
)
def test_wrapper_path_or_word_list_becomes_the_launcher_argv(tmp_path: Path, wrapper: object, argv: tuple) -> None:
    overrides = dl.load_local_config(write_local(tmp_path, {"cto": {"wrapper": wrapper}}))
    plan = dl.launch_plan(dl.load_registry().by_session("cto"), repo_root=tmp_path, local=overrides)
    assert plan.argv == argv
    assert plan.pane_argv() == ["bash", "-c", dl.PANE_SCRIPT, dl.PANE_ARGV0, *argv]


def test_invalid_local_env_is_refused_for_that_lane_only(tmp_path: Path) -> None:
    overrides = dl.load_local_config(write_local(tmp_path, {"cto": {"env": {"bad key": "x"}}, "atlas": "x"}))
    for session in ("cto", "atlas"):
        with pytest.raises(dl.LaneConfigError, match=f"local lane config: {session}: "):
            dl.launch_plan(dl.load_registry().by_session(session), repo_root=tmp_path, local=overrides)


def test_pane_command_runs_launcher_words_without_shell_parsing(tmp_path: Path) -> None:
    marker = tmp_path / "pwned"
    words = ("printf", "%s|", "expected; printf INJECTED", f"$(touch {marker})", f"`touch {marker}`", ">out", "a b\nc")
    plan = dl.LaunchPlan(session="cto", argv=words, cwd=str(tmp_path))
    result = subprocess.run(
        plan.pane_argv(), cwd=tmp_path, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        check=False,
    )
    assert result.stdout == "|".join(words[2:]) + f"|\n{dl.EXIT_MARKER}0\n"
    assert not marker.exists() and not (tmp_path / "out").exists()
    assert plan.command == shlex.join(words)  # display only
