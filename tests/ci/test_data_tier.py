"""Audited nightly data-tier selection, receipt, and single-issue reporting."""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ci import data_tier


def test_selection_matches_class_c_audit_and_excludes_opt_ins() -> None:
    selection = data_tier.load_selection()
    assert selection["source_run"] == 36611889906
    assert selection["source_sha"] == "410da34bb875aca2acfc960da4d8c9b87ae7867b"
    assert selection["class_c_merge_group"] == 614
    assert selection["class_c_nightly"] == 1
    assert len(selection["nodeids"]) == 614
    assert len(selection["files"]) == 104
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


def test_collection_time_data_skip_is_in_junit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = "tests/test_citation_resolution_invariant.py"
    monkeypatch.setattr(data_tier, "load_selection", lambda: {"nodeids": [module], "files": [module]})

    def collect(_argv: list[str], *, plugins: list[data_tier.SelectionPlugin]) -> int:
        report = SimpleNamespace(skipped=True, nodeid=module, longrepr=(module, 1, "sources.db absent"))
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
    assert data_tier.report(clean, baseline) == "commented once on issue #77"
    assert data_tier.report(clean, baseline) == "no issue change"
    result = json.loads(state.read_text(encoding="utf-8"))
    assert "known issue #8403" in result["body"]
    assert len(result["comments"]) == 1
    assert result["calls"].count(["issue", "create"]) == 1
    assert result["calls"].count(["issue", "edit"]) == 1
