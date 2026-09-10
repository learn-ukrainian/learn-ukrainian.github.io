"""Classifier safety cases, run in Changes before outputs can skip CI jobs."""

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ci import classify_changes as scope
from scripts.ci.frontend_change_scope import load_denominator


def _tree(*paths: str) -> frozenset[str]:
    return frozenset(paths)


class ClassifierTests(unittest.TestCase):
    def classify(self, paths, event="pull_request", labels=None, tree_paths=None):
        return scope.classify(
            paths,
            event=event,
            labels=labels or [],
            shard_count=4,
            denominator=load_denominator()["paths"],
            tree_paths=tree_paths if tree_paths is not None else frozenset(),
        )

    def assert_full(self, result, frontend="false"):
        self.assertEqual(
            result,
            {
                "docs_only": "false",
                "frontend": frontend,
                "shards": "[1, 2, 3, 4]",
                "pytest_mode": "full",
                "shard_count": "4",
                "pytest_candidates": "[]",
            },
        )

    def assert_docs(self, result):
        self.assertEqual(
            result,
            {
                "docs_only": "true",
                "frontend": "false",
                "shards": "[1]",
                "pytest_mode": "docs",
                "shard_count": "1",
                "pytest_candidates": "[]",
            },
        )

    def assert_selected(self, result, candidates):
        self.assertEqual(result["docs_only"], "false")
        self.assertEqual(result["frontend"], "false")
        self.assertEqual(result["shards"], "[1]")
        self.assertEqual(result["pytest_mode"], "selected")
        self.assertEqual(result["shard_count"], "1")
        self.assertEqual(json.loads(result["pytest_candidates"]), sorted(candidates))

    def test_documentation_selection(self):
        for path in (
            "docs/runbooks/ci-gate.md",
            "README.md",
            "agents_extensions/shared/skills/example/SKILL.md",
            ".codex/skills/example.md",
            "wiki/example.yaml",
            "curriculum/example.yaml",
        ):
            with self.subTest(path=path):
                self.assert_docs(self.classify([path]))

    def test_contract_and_unknown_paths_cannot_skip(self):
        for path in (
            "docs/lesson-schema.yaml",
            "docs/contracts/nested/schema.yaml",
            "schemas/README.md",
            "packages/README.md",
            "dashboards/README.md",
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "requirements.txt",
            "requirements-dev.txt",
            ".pre-commit-config.yaml",
            "scripts/config/README.md",
            "scripts/ci/README.md",
            "scripts/example.py",
            "unknown/path.bin",
            "unknown/README.md",
            "docs/data.json",
            ".codex/unknown.py",
        ):
            with self.subTest(path=path):
                # Mixed with docs → never selected; docs+non-docs → full.
                tree = _tree(
                    "scripts/example.py",
                    "tests/test_example.py",
                    "tests/test_ci_shard_partition.py",
                )
                self.assert_full(self.classify(["docs/guide.md", path], tree_paths=tree))

    def test_frontend_denominator(self):
        for entry in load_denominator()["paths"]:
            path = entry + "README.md" if entry.endswith("/") else entry
            with self.subTest(path=path):
                self.assert_full(self.classify([path]), frontend="true")
        self.assert_full(self.classify(["packages/activity-kit/src/index.ts"]), frontend="true")

    def test_event_and_label_overrides(self):
        for event in ("merge_group", "schedule", "workflow_dispatch", "unknown"):
            with self.subTest(event=event):
                self.assert_full(self.classify(["docs/guide.md"], event=event), frontend="true")
        self.assert_full(self.classify(["docs/guide.md"], labels=["full-ci"]), frontend="true")
        self.assert_docs(self.classify(["docs/guide.md"], labels=["unrelated"]))

    def test_empty_and_capped_changes(self):
        for paths in ([], [f"docs/{i}.md" for i in range(300)]):
            self.assert_full(self.classify(paths), frontend="true")
        self.assert_docs(self.classify([f"docs/{i}.md" for i in range(299)]))

    def test_shard_count_is_not_hardcoded(self):
        result = scope.classify(
            ["unknown"],
            event="pull_request",
            labels=[],
            shard_count=7,
            denominator=[],
            tree_paths=frozenset(),
        )
        self.assertEqual(result["shards"], "[1, 2, 3, 4, 5, 6, 7]")
        self.assertEqual(result["shard_count"], "7")
        self.assertEqual(result["pytest_mode"], "full")
        self.assertEqual(result["pytest_candidates"], "[]")
        with self.assertRaises(ValueError):
            scope.classify([], event="schedule", labels=[], shard_count=0, denominator=[])

    @patch.object(scope.subprocess, "check_output")
    def test_rename_source_and_odd_filenames(self, command):
        command.return_value = json.dumps({"files": [
            {"filename": "docs/moved.md", "previous_filename": "scripts/ci/README.md"},
            {"filename": "unknown/line\nbreak.md"},
        ]})
        paths = scope.compare_paths("base", "head", "owner/repo")
        self.assertEqual(paths, ["docs/moved.md", "scripts/ci/README.md", "unknown/line\nbreak.md"])
        self.assert_full(self.classify(paths))

    def test_main_outputs_and_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            output = Path(directory) / "output"
            event.write_text(json.dumps({"pull_request": {"labels": []}}))
            env = {
                "PYTEST_SHARD_COUNT": "4",
                "EVENT_NAME": "pull_request",
                "GITHUB_EVENT_PATH": str(event),
                "GITHUB_OUTPUT": str(output),
                "BASE": "base",
                "HEAD": "head",
                "REPO": "owner/repo",
            }
            full_line = (
                "docs_only=false\nfrontend=true\nshards=[1, 2, 3, 4]\n"
                "pytest_mode=full\nshard_count=4\npytest_candidates=[]\n"
            )
            for error in (
                OSError(),
                ValueError(),
                KeyError(),
                TypeError(),
                subprocess.CalledProcessError(1, "gh"),
                subprocess.TimeoutExpired("gh", 60),
            ):
                with self.subTest(error=type(error).__name__), patch.dict(os.environ, env), \
                     patch.object(scope, "compare_paths", side_effect=error), \
                     contextlib.redirect_stdout(io.StringIO()):
                    output.write_text("")
                    scope.main()
                    self.assertEqual(output.read_text(), full_line)
            with patch.dict(os.environ, env), \
                 patch.object(scope, "compare_paths", return_value=["docs/guide.md"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                output.write_text("")
                scope.main()
                self.assertEqual(
                    output.read_text(),
                    "docs_only=true\nfrontend=false\nshards=[1]\n"
                    "pytest_mode=docs\nshard_count=1\npytest_candidates=[]\n",
                )

    def test_forced_events_do_not_need_compare_api(self):
        with patch.dict(os.environ, {"PYTEST_SHARD_COUNT": "4", "EVENT_NAME": "merge_group"}, clear=True), \
             patch.object(scope, "compare_paths") as compare, contextlib.redirect_stdout(io.StringIO()) as stdout:
            scope.main()
            compare.assert_not_called()
            self.assertIn("docs_only=false", stdout.getvalue())
            self.assertIn("frontend=true", stdout.getvalue())
            self.assertIn("pytest_mode=full", stdout.getvalue())
            self.assertIn("shard_count=4", stdout.getvalue())
            self.assertIn("shards=[1, 2, 3, 4]", stdout.getvalue())
            self.assertIn("pytest_candidates=[]", stdout.getvalue())

    def test_selected_test_file_only(self):
        tree = _tree("tests/test_x.py", "tests/test_ci_shard_partition.py")
        result = self.classify(["tests/test_x.py"], tree_paths=tree)
        self.assert_selected(result, ["tests/test_x.py"])

    def test_selected_delegate_stem_map(self):
        tree = _tree(
            "scripts/delegate.py",
            "tests/test_delegate.py",
            "tests/test_delegate_check_budget.py",
            "tests/test_delegate_api.py",
            "tests/test_ci_shard_partition.py",
            "scripts/other/cli.py",
            "scripts/tools/cli.py",
        )
        result = self.classify(["scripts/delegate.py"], tree_paths=tree)
        self.assert_selected(
            result,
            [
                "tests/test_ci_shard_partition.py",
                "tests/test_delegate.py",
                "tests/test_delegate_api.py",
                "tests/test_delegate_check_budget.py",
            ],
        )

    def test_scripts_ci_denylist_forces_full(self):
        tree = _tree(
            "scripts/ci/classify_changes.py",
            "tests/test_classify_changes.py",
            "tests/test_ci_shard_partition.py",
        )
        self.assert_full(
            self.classify(["scripts/ci/classify_changes.py"], tree_paths=tree),
            frontend="false",
        )

    def test_unmapped_script_forces_full(self):
        tree = _tree(
            "scripts/foo.py",
            "tests/test_ci_shard_partition.py",
            "tests/test_other.py",
        )
        self.assert_full(self.classify(["scripts/foo.py"], tree_paths=tree), frontend="false")

    def test_non_py_under_scripts_forces_full(self):
        tree = _tree("scripts/foo.sh", "tests/test_ci_shard_partition.py")
        self.assert_full(self.classify(["scripts/foo.sh"], tree_paths=tree), frontend="false")

    def test_non_test_under_tests_forces_full(self):
        for path in ("tests/conftest.py", "tests/fixtures/data.json", "tests/helpers.py"):
            with self.subTest(path=path):
                tree = _tree(path, "tests/test_x.py", "tests/test_ci_shard_partition.py")
                self.assert_full(self.classify([path], tree_paths=tree), frontend="false")

    def test_deleted_test_file_forces_full(self):
        tree = _tree("tests/test_y.py", "tests/test_ci_shard_partition.py")
        self.assert_full(
            self.classify(["tests/test_x.py", "tests/test_y.py"], tree_paths=tree),
            frontend="false",
        )

    def test_stem_collision_forces_full(self):
        tree = _tree(
            "scripts/a/cli.py",
            "scripts/b/cli.py",
            "tests/test_cli.py",
            "tests/test_ci_shard_partition.py",
        )
        self.assert_full(self.classify(["scripts/a/cli.py"], tree_paths=tree), frontend="false")

    def test_mixed_scripts_and_site_forces_full(self):
        tree = _tree(
            "scripts/delegate.py",
            "tests/test_delegate.py",
            "tests/test_ci_shard_partition.py",
            "site/index.html",
        )
        self.assert_full(
            self.classify(["scripts/delegate.py", "site/index.html"], tree_paths=tree),
            frontend="true",
        )

    def test_selected_emits_shard_count_one_and_candidates(self):
        tree = _tree("tests/test_x.py")
        result = self.classify(["tests/test_x.py"], tree_paths=tree)
        self.assertEqual(result["shard_count"], "1")
        self.assertEqual(result["pytest_mode"], "selected")
        self.assertNotEqual(json.loads(result["pytest_candidates"]), [])

    def test_full_emits_shard_count_four_and_empty_candidates(self):
        result = self.classify(["unknown/path.bin"])
        self.assertEqual(result["shard_count"], "4")
        self.assertEqual(result["pytest_mode"], "full")
        self.assertEqual(result["pytest_candidates"], "[]")

    def test_candidate_ceiling_forces_full(self):
        tests = [f"tests/test_{i}.py" for i in range(80)]
        tree = _tree(*tests)
        self.assert_full(self.classify(tests, tree_paths=tree), frontend="false")

    def test_missing_safety_net_with_script_forces_full(self):
        tree = _tree("scripts/delegate.py", "tests/test_delegate.py")
        self.assert_full(self.classify(["scripts/delegate.py"], tree_paths=tree), frontend="false")

    def test_shards_length_matches_shard_count(self):
        docs = self.classify(["docs/guide.md"])
        self.assertEqual(len(json.loads(docs["shards"])), int(docs["shard_count"]))
        tree = _tree("tests/test_x.py")
        selected = self.classify(["tests/test_x.py"], tree_paths=tree)
        self.assertEqual(len(json.loads(selected["shards"])), int(selected["shard_count"]))
        full = self.classify(["unknown.bin"])
        self.assertEqual(len(json.loads(full["shards"])), int(full["shard_count"]))


if __name__ == "__main__":
    unittest.main()
