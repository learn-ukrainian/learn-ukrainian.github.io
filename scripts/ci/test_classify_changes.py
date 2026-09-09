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


class ClassifierTests(unittest.TestCase):
    def classify(self, paths, event="pull_request", labels=None):
        return scope.classify(paths, event=event, labels=labels or [], shard_count=4,
                              denominator=load_denominator()["paths"])

    def assert_full(self, result, frontend="false"):
        self.assertEqual(result, {"docs_only": "false", "frontend": frontend, "shards": "[1, 2, 3, 4]"})

    def test_documentation_selection(self):
        for path in ("docs/runbooks/ci-gate.md", "README.md", "agents_extensions/shared/skills/example/SKILL.md",
                     ".codex/skills/example.md", "wiki/example.yaml", "curriculum/example.yaml"):
            with self.subTest(path=path):
                self.assertEqual(self.classify([path]), {"docs_only": "true", "frontend": "false", "shards": "[1]"})

    def test_contract_and_unknown_paths_cannot_skip(self):
        for path in ("docs/lesson-schema.yaml", "docs/contracts/nested/schema.yaml", "schemas/README.md",
                     "packages/README.md", "dashboards/README.md", "package.json", "package-lock.json",
                     "pnpm-lock.yaml", "requirements.txt", "requirements-dev.txt", ".pre-commit-config.yaml",
                     "scripts/config/README.md", "scripts/ci/README.md", "scripts/example.py",
                     "unknown/path.bin", "unknown/README.md", "docs/data.json", ".codex/unknown.py"):
            with self.subTest(path=path):
                self.assert_full(self.classify(["docs/guide.md", path]))

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
        self.assertEqual(self.classify(["docs/guide.md"], labels=["unrelated"])["docs_only"], "true")

    def test_empty_and_capped_changes(self):
        for paths in ([], [f"docs/{i}.md" for i in range(300)]):
            self.assert_full(self.classify(paths), frontend="true")
        self.assertEqual(self.classify([f"docs/{i}.md" for i in range(299)])["docs_only"], "true")

    def test_shard_count_is_not_hardcoded(self):
        self.assertEqual(scope.classify(["unknown"], event="pull_request", labels=[], shard_count=7,
                                       denominator=[])["shards"], "[1, 2, 3, 4, 5, 6, 7]")
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
            env = {"PYTEST_SHARD_COUNT": "4", "EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": str(event),
                   "GITHUB_OUTPUT": str(output), "BASE": "base", "HEAD": "head", "REPO": "owner/repo"}
            for error in (OSError(), ValueError(), KeyError(), TypeError(), subprocess.CalledProcessError(1, "gh"),
                          subprocess.TimeoutExpired("gh", 60)):
                with self.subTest(error=type(error).__name__), patch.dict(os.environ, env), \
                     patch.object(scope, "compare_paths", side_effect=error), contextlib.redirect_stdout(io.StringIO()):
                    output.write_text("")
                    scope.main()
                    self.assertEqual(output.read_text(), "docs_only=false\nfrontend=true\nshards=[1, 2, 3, 4]\n")
            with patch.dict(os.environ, env), patch.object(scope, "compare_paths", return_value=["docs/guide.md"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                output.write_text("")
                scope.main()
                self.assertEqual(output.read_text(), "docs_only=true\nfrontend=false\nshards=[1]\n")

    def test_forced_events_do_not_need_compare_api(self):
        with patch.dict(os.environ, {"PYTEST_SHARD_COUNT": "4", "EVENT_NAME": "merge_group"}, clear=True), \
             patch.object(scope, "compare_paths") as compare, contextlib.redirect_stdout(io.StringIO()) as stdout:
            scope.main()
            compare.assert_not_called()
            self.assertIn("docs_only=false frontend=true shards=[1, 2, 3, 4]", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
