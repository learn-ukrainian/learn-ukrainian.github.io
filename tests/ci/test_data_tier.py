"""Audited nightly data-tier selection, receipt, and single-issue reporting."""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ci import data_tier

pytestmark = pytest.mark.reads_content


def test_selection_matches_class_c_audit_and_excludes_opt_ins() -> None:
    selection = data_tier.load_selection()
    assert selection["source_run"] == 36611889906
    assert selection["source_sha"] == "410da34bb875aca2acfc960da4d8c9b87ae7867b"
    # 614 audited ids less 72 removed by #9607: 28 from the two test files archived with their
    # generators and 44 that read the quarantined artifacts through loaders that now refuse them.
    assert selection["class_c_merge_group"] == 542
    assert selection["class_c_nightly"] == 1
    assert len(selection["nodeids"]) == 542
    assert len(selection["files"]) == 102
    assert "tests/test_citation_resolution_invariant.py" in selection["nodeids"]
    assert "tests/test_site_links.py::TestCurriculumSync::test_manifest_modules_have_mdx[a1]" in selection["nodeids"]
    assert len([nodeid for nodeid in selection["nodeids"] if nodeid.startswith("sha256:")]) == 5
    assert set(selection["artifact_groups"]) == {
        "open_model_other_indexes",
        "open_model_release_payload",
        "open_model_evidence_indexes",
        "open_model_component_payload",
        "open_model_archive_payload",
        "open_model_study_outputs",
        "corpus_audit_snapshots",
        "lexicon_candidates",
        "lexicon_recovery_snapshots",
    }
    assert all(Path(path).is_file() for path in selection["files"])
    joined = "\n".join(selection["nodeids"])
    assert "/home/" not in joined
    for forbidden in ("TYPESAFE_LIVE", "RUN_BRIDGE_INBOX_INTEGRATION", "ZNO_LIVE", "sandbox-exec", "mlx_"):
        assert forbidden not in joined


def test_junit_summary_and_known_citation_issue(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(
        '<testsuite><testcase classname="tests.test_citation_resolution_invariant" '
        'name="test_published_citations_resolve_invariant[wiki/grammar/b2/academic-writing.md]"><failure message="drift"/></testcase>'
        f'<testcase classname="tests.test_vesum" name="test_db"><skipped message="missing {Path.home()}/db"/></testcase>'
        '<testcase classname="tests.test_vesum" name="test_ok"/></testsuite>',
        encoding="utf-8",
    )
    data_tier.sanitize_junit(junit)
    summary = data_tier.junit_summary(junit)
    assert (summary["ran"], summary["passed"], summary["failed"], summary["skipped"]) == (3, 1, 1, 1)
    assert summary["skip_reasons"] == {"missing <host-path>": 1}
    assert (
        data_tier.known_issue(
            summary["failing_tests"][0],
            {
                "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant[wiki/grammar/b2/academic-writing.md]": 8403,
            },
        )
        == 8403
    )


def test_known_issue_maps_whole_test_function_and_exact_ids() -> None:
    whole = "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant"
    exact = "tests/test_x.py::test_y[case-a]"
    baseline = {whole: 8403, exact: 11, "tests/test_x.py::test_y": 12}
    assert data_tier.known_issue(f"{whole}[wiki/grammar/b2/academic-writing.md]", baseline) == 8403
    assert data_tier.known_issue(f"{whole}[wiki/grammar/b1/aspect.md]", baseline) == 8403
    assert data_tier.known_issue(whole, baseline) == 8403
    assert data_tier.known_issue(exact, baseline) == 11
    assert data_tier.known_issue("tests/test_x.py::test_y[case-b]", baseline) == 12
    assert data_tier.known_issue(f"{whole}_other[wiki/a.md]", baseline) is None
    assert data_tier.known_issue("tests/test_x.py::test_z[case-a]", baseline) is None
    assert data_tier.known_issue("tests/test_citation_resolution_invariant.py::test_other", baseline) is None


def test_shipped_baseline_maps_every_citation_parametrization_to_8403() -> None:
    baseline = json.loads(data_tier.BASELINE.read_text(encoding="utf-8"))["known_failures"]
    body = data_tier.issue_body(
        {
            "run_key": "run-1",
            "main_sha": "abc",
            "ran": 2,
            "passed": 0,
            "failed": 2,
            "skipped": 0,
            "failing_tests": [
                "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant[wiki/grammar/b2/dim-zhytlo.md]",
                "tests/test_esum_search.py::test_search_esum_berkut_returns_turkic_origin",
            ],
            "skip_reasons": {},
        },
        baseline,
    )
    assert "dim-zhytlo.md]` — known issue #8403" in body
    assert "test_search_esum_berkut_returns_turkic_origin` — new" in body


def test_memory_floor_is_a_stop_condition(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data_tier, "available_memory", lambda: 6 * 1024**3 - 1)
    with pytest.raises(data_tier.DataTierError, match="below the 6 GiB floor"):
        data_tier.require_memory()


def test_selection_filters_exact_ids_before_xdist(tmp_path: Path) -> None:
    ordinary = "tests/test_sample.py::test_data"
    private = "tests/test_sample.py::test_bulk[private fixture]"
    citation = "tests/test_citation_resolution_invariant.py::test_one[wiki/a1/example.md]"
    selection = {
        "nodeids": [ordinary, data_tier._key(private), "tests/test_citation_resolution_invariant.py"],
        "bulk_nodeids": [data_tier._key(private)],
    }

    class Item:
        def __init__(self, nodeid: str, live: bool = False) -> None:
            self.nodeid = nodeid
            self.live = live

        def get_closest_marker(self, marker: str) -> object | None:
            return object() if self.live and marker == "live_network" else None

    deselected = []
    config = SimpleNamespace(hook=SimpleNamespace(pytest_deselected=lambda items: deselected.extend(items)))
    plugin = data_tier.SelectionPlugin(selection, None, "mount absent", tmp_path / "collected.json")
    items = [Item(ordinary), Item(private), Item(citation), Item("tests/test_sample.py::test_live", live=True)]
    plugin.pytest_collection_modifyitems(items, config)

    assert plugin.selected_nodeids == [ordinary, citation]
    assert plugin.bulk_skipped == [private]
    assert [item.nodeid for item in items] == [ordinary, citation]
    assert len(deselected) == 2
    assert json.loads((tmp_path / "collected.json").read_text()) == [ordinary, citation]


def test_child_passes_only_selected_ids_to_two_workers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = "tests/test_sample.py::test_data"
    ignored = "tests/test_sample.py::test_unrelated"
    monkeypatch.setattr(
        data_tier,
        "load_selection",
        lambda: {"nodeids": [selected], "files": ["tests/test_sample.py"], "bulk_nodeids": []},
    )

    class Item:
        def __init__(self, nodeid: str) -> None:
            self.nodeid = nodeid

        def get_closest_marker(self, _marker: str) -> None:
            return None

    def collect(_argv: list[str], *, plugins: list[data_tier.SelectionPlugin]) -> int:
        items = [Item(selected), Item(ignored)]
        config = SimpleNamespace(hook=SimpleNamespace(pytest_deselected=lambda items: None))
        plugins[0].pytest_collection_modifyitems(items, config)
        return 0

    calls = []

    def execute(argv: list[str], *, timeout: int) -> int:
        calls.append(argv)
        assert timeout == 21600
        junit.write_text('<testsuite><testcase classname="tests.test_sample" name="test_data"/></testsuite>')
        return 0

    monkeypatch.setattr(data_tier.pytest, "main", collect)
    monkeypatch.setattr(data_tier, "run_process_group", execute)
    junit = tmp_path / "junit.xml"
    args = SimpleNamespace(junit=str(junit), collected=str(tmp_path / "collected.json"), only=None, bulk_reason=None)
    assert data_tier.pytest_child(args) == 0
    assert len(calls) == 1
    assert calls[0][-1] == selected
    assert ignored not in calls[0]
    assert calls[0][calls[0].index("-n") + 1] == "2"
    assert "--require-data" in calls[0]


def test_collection_time_data_skip_is_in_junit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = "tests/test_citation_resolution_invariant.py"
    monkeypatch.setattr(data_tier, "load_selection", lambda: {"nodeids": [module], "files": [module]})

    def collect(_argv: list[str], *, plugins: list[data_tier.SelectionPlugin]) -> int:
        report = SimpleNamespace(failed=False, skipped=True, nodeid=module, longrepr=(module, 1, "sources.db absent"))
        plugins[0].pytest_collectreport(report)
        return 5

    monkeypatch.setattr(data_tier.pytest, "main", collect)
    junit = tmp_path / "junit.xml"
    args = SimpleNamespace(junit=str(junit), collected=str(tmp_path / "collected.json"), only=None, bulk_reason=None)
    assert data_tier.pytest_child(args) == 0
    assert data_tier.junit_summary(junit)["skip_reasons"] == {"sources.db absent": 1}


def test_failure_reporting_uses_one_fake_gh_issue_and_clean_comment_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(data_tier.github_client, "run", subprocess.run)
    executable = tmp_path / "gh"
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"issue": None, "comments": [], "calls": []}), encoding="utf-8")
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json, pathlib, sys\n"
        f"path = pathlib.Path({str(state)!r})\n"
        "state = json.loads(path.read_text())\n"
        "args = sys.argv[1:]\n"
        "state['calls'].append(args[:2])\n"
        "if args[:2] == ['issue', 'list']:\n"
        "    print(json.dumps([state['issue']] if state['issue'] else []))\n"
        "elif args[:2] == ['issue', 'create']:\n"
        "    state['issue'] = {'number': 77, 'title': '[infra][tests] Nightly data-tier failures', 'state': 'OPEN'}\n"
        "    state['body'] = sys.stdin.read()\n"
        "    print('issue 77')\n"
        "elif args[:2] == ['issue', 'edit']:\n"
        "    state['body'] = sys.stdin.read()\n"
        "elif args[:2] == ['issue', 'view']:\n"
        "    print(json.dumps({'comments': [{'body': body} for body in state['comments']]}))\n"
        "elif args[:2] == ['issue', 'comment']:\n"
        "    state['comments'].append(args[-1])\n"
        "elif args[:2] == ['issue', 'close']:\n"
        "    state['issue']['state'] = 'CLOSED'\n"
        "elif args[:2] == ['issue', 'reopen']:\n"
        "    state['issue']['state'] = 'OPEN'\n"
        "else:\n"
        "    sys.exit(4)\n"
        "path.write_text(json.dumps(state))\n",
        encoding="utf-8",
    )
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    failed = {
        "run_key": "run-1",
        "main_sha": "a" * 40,
        "ran": 2,
        "passed": 1,
        "failed": 1,
        "skipped": 0,
        "failing_tests": [
            "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant[wiki/grammar/b2/academic-writing.md]"
        ],
        "skip_reasons": {},
    }
    baseline = {
        "tests/test_citation_resolution_invariant.py::test_published_citations_resolve_invariant[wiki/grammar/b2/academic-writing.md]": 8403
    }
    assert data_tier.report(failed, baseline).startswith("created")
    assert data_tier.report(failed, baseline) == "updated issue #77"
    clean = {**failed, "failed": 0, "passed": 2, "failing_tests": []}
    for errors in (
        {"runner_errors": ["memory guard stopped the run"]},
        {"hydration_errors": {"group": "hydrate failed"}},
        {"missing_databases": ["sources.db"]},
    ):
        assert data_tier.report({**clean, **errors}, baseline) == "updated issue #77"
        assert json.loads(state.read_text())["comments"] == []
    assert data_tier.report(failed, baseline) == "updated issue #77"
    assert data_tier.report(clean, baseline) == "closed issue #77 after clean run"
    assert data_tier.report({**clean, "run_key": "run-2"}, baseline) == "no issue change"
    result = json.loads(state.read_text(encoding="utf-8"))
    assert "known issue #8403" in result["body"]
    assert len(result["comments"]) == 1
    assert result["calls"].count(["issue", "create"]) == 1
    assert result["calls"].count(["issue", "edit"]) == 5
    assert result["issue"]["state"] == "CLOSED"
    assert result["calls"].count(["issue", "close"]) == 1
    assert data_tier.report({**failed, "run_key": "run-3"}, baseline) == "updated issue #77"
    assert data_tier.report({**clean, "run_key": "run-4"}, baseline) == "closed issue #77 after clean run"
    result = json.loads(state.read_text())
    assert len(result["comments"]) == 2
    assert result["calls"].count(["issue", "create"]) == 1


@pytest.mark.parametrize(
    ("active", "current", "maximum", "error"),
    [
        ("inactive", "[not set]", "infinity", None),
        ("active", "1024", "infinity", None),
        ("active", "1024", str(8 * 1024**3), None),
        ("active", "[not set]", "infinity", "unknown"),
        ("active", "1024", "invalid", "unknown"),
        ("active", str(8 * 1024**3), str(10 * 1024**3), "headroom"),
    ],
)
def test_slice_memory_states(
    monkeypatch: pytest.MonkeyPatch, active: str, current: str, maximum: str, error: str | None
) -> None:
    monkeypatch.setattr(data_tier, "available_memory", lambda: 10 * 1024**3)
    monkeypatch.setattr(
        data_tier,
        "command",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=f"LoadState=loaded\nActiveState={active}\nMemoryCurrent={current}\nMemoryMax={maximum}\n"
        ),
    )
    if error:
        with pytest.raises(data_tier.DataTierError, match=error):
            data_tier.require_memory()
    else:
        data_tier.require_memory()


def test_collection_error_keeps_healthy_selected_test_and_junit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test_good.py").write_text("def test_ok():\n    assert True\n")
    (tmp_path / "test_bad.py").write_text("raise ImportError('broken import')\n")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setattr(
        data_tier,
        "load_selection",
        lambda: {
            "nodeids": ["test_good.py::test_ok"],
            "files": ["test_good.py", "test_bad.py"],
        },
    )
    junit = tmp_path / "junit.xml"
    calls = []

    def execute(argv: list[str], *, timeout: int) -> int:
        calls.append(argv)
        junit.write_text('<testsuite tests="1"><testcase classname="test_good" name="test_ok"/></testsuite>')
        return 0

    monkeypatch.setattr(data_tier, "run_process_group", execute)
    args = SimpleNamespace(junit=str(junit), collected=str(tmp_path / "collected.json"), only=None, bulk_reason=None)
    assert data_tier.pytest_child(args) == 1
    assert calls[0][-1] == "test_good.py::test_ok"
    summary = data_tier.junit_summary(junit)
    assert (summary["passed"], summary["failed"]) == (1, 1)
    assert "test_bad.py" in summary["failing_tests"]


@pytest.fixture
def nightly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    primary = tmp_path / "primary"
    project_python = primary / ".venv" / "bin" / "python"
    project_python.parent.mkdir(parents=True)
    project_python.touch()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    events = []
    reports = []
    monkeypatch.setattr(data_tier, "primary_checkout", lambda: primary)
    monkeypatch.setattr(data_tier, "project_interpreter", lambda root: project_python if root == primary else None)
    monkeypatch.setattr(data_tier, "require_memory", lambda: None)
    monkeypatch.setattr(data_tier, "prune_stale_worktrees", lambda _primary: None)
    monkeypatch.setattr(data_tier, "make_test_worktree", lambda _primary: checkout)
    monkeypatch.setattr(data_tier, "command", lambda *args, **kwargs: SimpleNamespace(stdout="a" * 40))
    monkeypatch.setattr(data_tier, "snapshot_databases", lambda *args, **kwargs: [])
    monkeypatch.setattr(data_tier, "provision_host_files", lambda *args: None)
    monkeypatch.setattr(data_tier, "hydrate", lambda *args: {})
    monkeypatch.setattr(data_tier, "bulk_status", lambda *args: (None, "unavailable"))
    monkeypatch.setattr(data_tier, "stop_scope", lambda unit: events.append("stop"))
    monkeypatch.setattr(data_tier, "remove_test_worktree", lambda *args: events.append("remove"))

    def execute(argv: list[str], **kwargs: object) -> int:
        assert kwargs["cwd"] == checkout
        assert "scripts.ci.data_tier" in argv
        assert "-m" in argv
        assert 0 < kwargs["timeout"] <= data_tier.RUN_BUDGET_SECONDS
        Path(argv[argv.index("--junit") + 1]).write_text('<testsuite><testcase name="test_ok"/></testsuite>')
        return 0

    monkeypatch.setattr(data_tier, "run_process_group", execute)

    def report(summary: dict, baseline: dict) -> str:
        reports.append(json.loads(json.dumps(summary)))
        return "reported"

    monkeypatch.setattr(data_tier, "report", report)
    return SimpleNamespace(primary=primary, events=events, reports=reports, execute=execute)


@pytest.mark.parametrize("action", ["removed", "skipped", "error"])
def test_checkout_cleanup_obeys_guard_outcome(action: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checkout = tmp_path / ".worktrees" / "data-tier" / ("run-" + "a" * 32)
    calls = []

    def remove(path: Path, **kwargs: object) -> SimpleNamespace:
        calls.append((path, kwargs))
        return SimpleNamespace(
            action=action, reason="guard outcome", error="guard failure" if action == "error" else None
        )

    monkeypatch.setattr(data_tier.worktree_claims, "remove_unclaimed_worktree", remove)
    if action == "removed":
        data_tier.remove_test_worktree(tmp_path, checkout)
    else:
        with pytest.raises(data_tier.DataTierError, match=f"checkout cleanup {action}: guard outcome"):
            data_tier.remove_test_worktree(tmp_path, checkout)
    assert calls == [
        (
            checkout,
            {
                "repo_root": tmp_path,
                "reason": "data-tier checkout cleanup",
                "owner_task_id": None,
                "force": True,
            },
        )
    ]


def test_checkout_creation_failure_uses_guarded_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    created = []
    removed = []

    def command(argv: list[str], **kwargs: object) -> SimpleNamespace:
        if "add" in argv:
            created.append(Path(argv[-2]))
            return SimpleNamespace(stdout="")
        raise data_tier.DataTierError("fetch failed")

    monkeypatch.setattr(data_tier, "command", command)
    monkeypatch.setattr(
        data_tier, "remove_test_worktree", lambda primary, checkout: removed.append((primary, checkout))
    )
    with pytest.raises(data_tier.DataTierError, match="fetch failed"):
        data_tier.make_test_worktree(tmp_path)
    assert len(created) == 1
    assert removed == [(tmp_path, created[0])]


def test_interpreter_resolver_refusal_is_reported(nightly: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    def resolve(root: Path) -> Path:
        assert root == nightly.primary
        raise FileNotFoundError("unavailable")

    monkeypatch.setattr(data_tier, "project_interpreter", resolve)
    assert data_tier.run(SimpleNamespace(only=None, no_report=False)) == 1
    assert nightly.reports[0]["runner_errors"] == ["shared project interpreter unavailable"]
    assert nightly.events == []


@pytest.mark.parametrize(
    "failure",
    [
        "selection",
        "memory",
        "interpreter",
        "worktree",
        "snapshot",
        "hydration",
        "missing_database",
        "bulk",
        "second_memory",
        "collection",
        "runner_exit",
        "timeout",
        "malformed_junit",
        "cleanup",
        "scope_cleanup",
        "signal",
        "budget",
    ],
)
def test_every_runner_failure_reaches_report(
    nightly: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise data_tier.DataTierError("runner failed at /private/example.db")

    if failure in {"selection", "memory", "worktree", "snapshot", "bulk", "cleanup", "scope_cleanup"}:
        helper = {
            "selection": "load_selection",
            "memory": "require_memory",
            "worktree": "make_test_worktree",
            "snapshot": "snapshot_databases",
            "bulk": "bulk_status",
            "cleanup": "remove_test_worktree",
            "scope_cleanup": "stop_scope",
        }[failure]
        monkeypatch.setattr(data_tier, helper, fail)
    elif failure == "interpreter":
        (nightly.primary / ".venv" / "bin" / "python").unlink()
    elif failure == "hydration":
        monkeypatch.setattr(data_tier, "hydrate", lambda *args: {"group": "missing /private/artifact"})
    elif failure == "missing_database":
        monkeypatch.setattr(data_tier, "snapshot_databases", lambda *args, **kwargs: ["sources.db"])
    elif failure == "second_memory":
        memory_calls = iter([None, "fail"])

        def memory() -> None:
            if next(memory_calls):
                fail()

        monkeypatch.setattr(data_tier, "require_memory", memory)
    elif failure == "budget":
        clock = iter([0, data_tier.RUN_BUDGET_SECONDS + 1])
        monkeypatch.setattr(data_tier.time, "monotonic", lambda: next(clock))
    else:

        def execute(argv: list[str], **kwargs: object) -> int:
            if failure == "timeout":
                raise subprocess.TimeoutExpired("pytest", 1)
            if failure == "signal":
                os.kill(os.getpid(), data_tier.signal.SIGTERM)
            if failure == "collection":
                return 2
            nightly.execute(argv, **kwargs)
            if failure == "malformed_junit":
                Path(argv[argv.index("--junit") + 1]).write_text("invalid xml")
            return 3 if failure == "runner_exit" else 0

        monkeypatch.setattr(data_tier, "run_process_group", execute)
    assert data_tier.main(["run"]) == 1
    assert len(nightly.reports) == 1
    summary = nightly.reports[0]
    assert data_tier.run_failed(summary)
    body = data_tier.issue_body(summary, {})
    assert "/private/" not in body
    assert summary["run_key"] in body
    assert summary["runner_errors"] or summary["hydration_errors"] or summary["missing_databases"]
    receipts = list((nightly.primary / "batch_state" / "data-tier").glob("*.summary.json"))
    if failure != "selection":
        assert json.loads(receipts[0].read_text()) == summary
    if "stop" in nightly.events and failure != "cleanup":
        assert nightly.events == ["stop", "remove"]
    if failure == "scope_cleanup":
        assert nightly.events == []


def test_github_failure_is_single_attempt_and_persisted(
    nightly: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def report(summary: dict, baseline: dict) -> str:
        calls.append(json.loads(json.dumps(summary)))
        raise data_tier.DataTierError("gh unavailable at /private/gh")

    monkeypatch.setattr(data_tier, "report", report)
    assert data_tier.run(SimpleNamespace(only=None, no_report=False)) == 1
    assert len(calls) == 1
    summary = json.loads(next((nightly.primary / "batch_state" / "data-tier").glob("*.summary.json")).read_text())
    assert len(summary["runner_errors"]) == 1
    assert "/private/" not in json.dumps(summary)


def test_clean_run_and_no_report(nightly: SimpleNamespace) -> None:
    assert data_tier.run(SimpleNamespace(only=None, no_report=True)) == 0
    assert nightly.reports == []
    assert nightly.events == ["stop", "remove"]


def test_issue_body_is_bounded_with_total_and_runner_errors() -> None:
    summary = {
        "run_key": "run-1",
        "main_sha": "a" * 40,
        "ran": 700,
        "passed": 0,
        "failed": 700,
        "skipped": 0,
        "failing_tests": [f"test_{i}" + "x" * 1000 for i in range(700)],
        "skip_reasons": {},
        "runner_errors": ["runner failed at /private/log"],
        "hydration_errors": {"group": "hydrate failed"},
        "missing_databases": ["sources.db"],
    }
    body = data_tier.issue_body(summary, {})
    assert len(body) <= data_tier.ISSUE_BODY_LIMIT
    assert "700 total" in body
    assert "runner failed at <host-path>" in body
    assert "hydrate failed" in body and "sources.db" in body
    assert "Truncated" in body and "local run JUnit" in body


def test_hydration_has_total_budget_and_records_timeouts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = iter([0, 0, data_tier.HYDRATION_BUDGET_SECONDS - 10, data_tier.HYDRATION_BUDGET_SECONDS + 1])
    monkeypatch.setattr(data_tier.time, "monotonic", lambda: next(clock))
    calls = []

    def run(argv: list[str], **kwargs: object) -> None:
        calls.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(data_tier.subprocess, "run", run)
    errors = data_tier.hydrate(tmp_path, ["first", "second", "third"], Path(sys.executable))
    assert calls == [1800, 10]
    assert errors == {
        "first": "hydration timed out",
        "second": "hydration timed out",
        "third": "hydration budget exhausted",
    }


def test_stale_worktrees_pruned_only_without_active_scopes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = tmp_path / ".worktrees" / "data-tier"
    old = parent / ("run-" + "a" * 32)
    recent = parent / ("run-" + "b" * 32)
    unrelated = parent / "run-unrelated"
    for path in (old, recent, unrelated):
        path.mkdir(parents=True)
    os.utime(old, (0, 0))
    removed = []
    monkeypatch.setattr(data_tier, "remove_test_worktree", lambda primary, checkout: removed.append(checkout))
    monkeypatch.setattr(data_tier, "command", lambda *args, **kwargs: SimpleNamespace(stdout="active.scope"))
    with pytest.raises(data_tier.DataTierError, match="still active"):
        data_tier.prune_stale_worktrees(tmp_path)
    assert removed == []
    monkeypatch.setattr(data_tier, "command", lambda *args, **kwargs: SimpleNamespace(stdout=""))
    data_tier.prune_stale_worktrees(tmp_path)
    assert removed == [old]


def test_scope_stop_handles_collected_and_loaded_units(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    state = "not-found"

    def command(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(argv)
        return SimpleNamespace(stdout=f"LoadState={state}\n", returncode=1 if state == "not-found" else 0, stderr="")

    monkeypatch.setattr(data_tier, "command", command)
    monkeypatch.setattr(data_tier.subprocess, "run", command)
    data_tier.stop_scope("lu-data-tier-test.scope")
    assert len(calls) == 1
    state = "loaded"
    data_tier.stop_scope("lu-data-tier-test.scope")
    assert calls[-1] == ["systemctl", "--user", "stop", "lu-data-tier-test.scope"]


@pytest.mark.parametrize("interrupted", [False, True])
def test_process_group_stops_descendants_on_timeout_or_interruption(
    monkeypatch: pytest.MonkeyPatch, interrupted: bool
) -> None:
    waits = []
    signals = []

    class Process:
        pid = 123

        def wait(self, *, timeout: int) -> int:
            waits.append(timeout)
            if len(waits) == 1 and interrupted:
                raise data_tier.DataTierError("run interrupted")
            if len(waits) < 3:
                raise subprocess.TimeoutExpired("child", timeout)
            return 0

    monkeypatch.setattr(data_tier.subprocess, "Popen", lambda *args, **kwargs: Process())
    monkeypatch.setattr(data_tier.os, "killpg", lambda pid, sig: signals.append(sig))
    with pytest.raises(data_tier.DataTierError, match="interrupted" if interrupted else "timed out"):
        data_tier.run_process_group([sys.executable, "-c", "pass"], timeout=2)
    assert signals == [data_tier.signal.SIGTERM, data_tier.signal.SIGKILL]
    assert waits == [2, 30, 10]


@pytest.mark.parametrize("only", [None, "tests/test_input.py"])
def test_snapshots_keep_logical_stores_outside_checkout(tmp_path, only):
    primary = tmp_path / "primary"
    (primary / "data").mkdir(parents=True)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    snapshots = tmp_path / "scratch"
    for name in data_tier.HOST_DATABASES:
        with sqlite3.connect(primary / "data" / name) as connection:
            connection.execute("CREATE TABLE witness (value TEXT)")
            connection.execute("INSERT INTO witness VALUES ('snapshot')")
    assert data_tier.snapshot_databases(primary, checkout, snapshots, only=only) == []
    for name in ("sources.db", "vesum.db"):
        assert not (checkout / "data" / name).exists()
        with sqlite3.connect((snapshots / name).as_uri() + "?mode=ro", uri=True) as connection:
            assert connection.execute("SELECT value FROM witness").fetchone() == ("snapshot",)
    assert (checkout / "data" / "atlas.db").exists() == (only is None)


def test_nightly_exports_snapshot_bindings_and_reaps_them(nightly, monkeypatch):
    seen = []

    def execute(argv, **kwargs):
        env = kwargs["env"]
        sources, vesum = (Path(env[key]) for key in ("LU_SOURCES_DB", "LU_VESUM_DB"))
        assert sources.parent == vesum.parent
        assert sources.parent.is_dir()
        assert not sources.is_relative_to(nightly.primary)
        assert not sources.is_relative_to(kwargs["cwd"])
        seen.append(sources.parent)
        return nightly.execute(argv, **kwargs)

    monkeypatch.setenv("LU_SOURCES_DB", "inherited-live-store")
    monkeypatch.setenv("LU_VESUM_DB", "inherited-live-store")
    monkeypatch.setattr(data_tier, "run_process_group", execute)
    assert data_tier.run(SimpleNamespace(only=None, no_report=True)) == 0
    assert len(seen) == 1
    assert not seen[0].exists()


@pytest.mark.parametrize("available", [True, False])
def test_data_tier_child_executes_in_real_linked_worktree(tmp_path, available):
    """Exercise backup -> overrides -> resolver -> required child with real Git."""
    primary = tmp_path / "primary"
    primary.mkdir()

    def git(*args):
        subprocess.run(["git", *args], cwd=primary, check=True, capture_output=True, text=True, timeout=30)

    git("init", "-q")
    (primary / "sentinel").write_text("synthetic repository\n", encoding="utf-8")
    git("add", "sentinel")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
    checkout = tmp_path / "linked"
    git("worktree", "add", "--detach", str(checkout), "HEAD")
    assert (checkout / ".git").is_file()
    (checkout / "scripts").mkdir()
    (checkout / "data").mkdir()
    (primary / "data").mkdir()
    if available:
        for name in ("sources.db", "vesum.db"):
            with sqlite3.connect(primary / "data" / name) as connection:
                connection.execute("CREATE TABLE witness (value TEXT)")
                connection.execute("INSERT INTO witness VALUES ('snapshot')")
    snapshots = tmp_path / "scratch"
    missing = data_tier.snapshot_databases(primary, checkout, snapshots, only="tests/test_input.py")
    assert missing == ([] if available else ["sources.db", "vesum.db"])
    root = Path(data_tier.__file__).resolve().parents[2]
    (checkout / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (checkout / "conftest.py").write_text(
        f"import sys\nsys.path.insert(0, {str(root)!r})\n"
        "pytest_plugins = ['tests.data_store_fixtures']\n", encoding="utf-8",
    )
    tests = checkout / "tests"
    tests.mkdir()
    (tests / "test_input.py").write_text(
        "import sqlite3\nimport pytest\nfrom pathlib import Path\n"
        "@pytest.mark.parametrize('store', ['sources', 'vesum'])\n"
        "def test_snapshot(store, data_store_factory):\n"
        "    assert Path('.git').is_file()\n"
        "    path = data_store_factory(store, required_sqlite_tables=('witness',))\n"
        "    assert not path.is_relative_to(Path.cwd())\n"
        "    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as conn:\n"
        "        assert conn.execute('SELECT value FROM witness').fetchone() == ('snapshot',)\n",
        encoding="utf-8",
    )
    junit = tmp_path / "result.xml"
    code = (
        f"import sys\nsys.path.insert(0, {str(root)!r})\n"
        "from scripts.ci import data_tier\nfrom types import SimpleNamespace\n"
        "data_tier.load_selection = lambda: {'files': ['tests/test_input.py'], "
        "'nodeids': ['tests/test_input.py'], 'bulk_nodeids': []}\n"
        f"raise SystemExit(data_tier.pytest_child(SimpleNamespace(junit={str(junit)!r}, "
        f"collected={str(tmp_path / 'collected.json')!r}, only=None, bulk_reason=None)))\n"
    )
    env = {**os.environ, "LU_SOURCES_DB": str(snapshots / "sources.db"),
           "LU_VESUM_DB": str(snapshots / "vesum.db")}
    env.pop("GITHUB_STEP_SUMMARY", None)
    result = subprocess.run([sys.executable, "-c", code], cwd=checkout, env=env,
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == (0 if available else 1), result.stdout + result.stderr
    summary = data_tier.junit_summary(junit)
    assert summary["ran"] == 2
    assert summary["skipped"] == 0
    assert summary["passed"] == (2 if available else 0)
    assert summary["failed"] == (0 if available else 2)
    if not available:
        assert "reason=store_missing" in result.stdout
        assert "worktree_local_store" not in result.stdout


def test_nightly_rejects_scratch_inside_a_checkout(nightly, monkeypatch):
    (nightly.primary / ".git").mkdir()
    scratch = nightly.primary / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(data_tier.tempfile, "gettempdir", lambda: str(scratch))
    assert data_tier.run(SimpleNamespace(only=None, no_report=False)) == 1
    assert nightly.reports[-1]["runner_errors"] == ["runner scratch root must be outside any Git checkout"]
    assert nightly.events == ["remove"]
