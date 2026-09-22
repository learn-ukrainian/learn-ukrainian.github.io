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
                "backend": "true",
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
                "backend": "true",
                "shards": "[1]",
                "pytest_mode": "docs",
                "shard_count": "1",
                "pytest_candidates": "[]",
            },
        )

    def assert_selected(self, result, candidates):
        self.assertEqual(result["docs_only"], "false")
        self.assertEqual(result["frontend"], "false")
        self.assertEqual(result["backend"], "true")
        self.assertEqual(result["shards"], "[1]")
        self.assertEqual(result["pytest_mode"], "selected")
        self.assertEqual(result["shard_count"], "1")
        self.assertEqual(json.loads(result["pytest_candidates"]), sorted(candidates))

    def assert_frontend_only(self, result):
        self.assertEqual(
            result,
            {
                "docs_only": "false",
                "frontend": "true",
                "backend": "false",
                "shards": "[]",
                "pytest_mode": "frontend",
                "shard_count": "0",
                "pytest_candidates": "[]",
            },
        )

    def assert_content(self, result):
        self.assertEqual(
            result,
            {
                "docs_only": "false",
                "frontend": "true",
                "backend": "true",
                "shards": "[1]",
                "pytest_mode": "content",
                "shard_count": "1",
                "pytest_candidates": "[]",
            },
        )

    def test_documentation_selection(self):
        for path in (
            "docs/runbooks/ci-gate.md",
            "README.md",
            "agents_extensions/shared/skills/example/SKILL.md",
            ".codex/skills/example.md",
        ):
            with self.subTest(path=path):
                self.assert_docs(self.classify([path]))
        # D2 (#8399): curriculum/wiki-only PRs keep the pre-existing docs
        # fast path; the merge queue pays the content lane for them instead.
        # wiki/ is a content-class root, so a wiki-only group is content;
        # curriculum/ outside the class roots (e.g. example.yaml at the
        # curriculum root) is full on the queue.
        self.assert_docs(self.classify(["wiki/example.yaml"]))
        self.assert_docs(self.classify(["wiki/example.yaml"], event="merge_group"))
        self.assert_docs(self.classify(["curriculum/example.yaml"]))
        self.assert_docs(self.classify(["curriculum/example.yaml"], event="merge_group"))

    def test_content_class_roots(self):
        content_paths = [
            "curriculum/l2-uk-en/a1/module/lesson-1/module.md",
            "curriculum/l2-uk-en/b1/plans/module.yaml",
            "curriculum/l2-uk-direct/a1/module/lesson-1/activities.yaml",
            "site/src/content/docs/a1/module/1.mdx",
            "wiki/figures/example.md",
            "wiki/periods/kyivan-rus.sources.yaml",
        ]
        # Additions and deletions reach the classifier as the same path list.
        # The PR content class requires a site/src/content/docs path (D2).
        with self.subTest(change="addition"):
            self.assert_content(self.classify(content_paths))
        with self.subTest(change="deletion"):
            self.assert_content(self.classify(list(reversed(content_paths))))
        with self.subTest(change="single", event="merge_group"):
            for path in content_paths:
                if path.startswith("site/"):
                    self.assert_content(self.classify([path], event="merge_group"))
                else:
                    self.assert_docs(self.classify([path], event="merge_group"))
        with self.subTest(change="single-pr-curriculum-wiki-keeps-docs"):
            for path in content_paths:
                if path.startswith("site/"):
                    self.assert_content(self.classify([path]))
                else:
                    self.assert_docs(self.classify([path]))

    def test_content_plus_script_forces_full(self):
        tree = _tree(
            "scripts/delegate.py",
            "tests/test_delegate.py",
            "tests/test_ci_shard_partition.py",
        )
        self.assert_full(
            self.classify(
                ["curriculum/l2-uk-en/a1/module/lesson-1/module.md", "scripts/delegate.py"],
                tree_paths=tree,
            ),
            frontend="false",
        )

    def test_content_plus_code_load_bearing_file_forces_full(self):
        # D3 (#8399): real code-imported files inside the content roots.
        for path in (
            "curriculum/l2-uk-en/curriculum.yaml",
            "curriculum/l2-uk-direct/manifest.yaml",
            "curriculum/l2-uk-direct/bolshakova-letter-order.yaml",
            "curriculum/l2-uk-en/module-mapping.json",
            "curriculum/l2-uk-en/vocabulary.db",
            # Extension rules: code/data surface anywhere under the roots,
            # JSON at a track root.
            "curriculum/l2-uk-en/tools/build.py",
            "curriculum/l2-uk-direct/state.sqlite",
            "curriculum/l2-uk-en/new-track-root.json",
        ):
            for event in ("pull_request", "merge_group"):
                with self.subTest(path=path, event=event):
                    self.assertFalse(scope.is_docs(path))
                    self.assertFalse(scope.is_content_class_path(path))
                    self.assert_full(
                        self.classify(
                            [path, "curriculum/l2-uk-en/a1/module/lesson-1/module.md"],
                            event=event,
                        ),
                        frontend="false",
                    )

    def test_content_outside_roots(self):
        # D2 (#8399): assert the real expected class per case, per event.
        # curriculum/l1-uk is outside the content-class roots but still a
        # docs path on PR; the merge queue pays full for it.
        pr_docs = ["curriculum/l1-uk/a1/module.md", "wiki/figures/example.md"]
        self.assert_docs(self.classify(pr_docs))
        self.assert_docs(self.classify(pr_docs, event="merge_group"))
        # site/ paths outside src/content/docs hit the frontend denominator
        # and are not content class: full on both events.
        for path in ("site/src/content/readings/a1/x.mdx", "site/src/components/X.astro"):
            for event in ("pull_request", "merge_group"):
                with self.subTest(path=path, event=event):
                    self.assert_full(
                        self.classify([path, "wiki/figures/example.md"], event=event),
                        frontend="true",
                    )

    def test_content_pr_requires_site_docs_path(self):
        # D2 (#8399): the PR content class exists for all-content changes that
        # today fall to full because frontend is true (PR #8384). Without a
        # site/src/content/docs path a PR keeps the docs fast path; the queue
        # pays the content lane either way.
        curriculum_only = ["curriculum/l2-uk-en/a1/module/lesson-1/module.md"]
        with_site = [*curriculum_only, "site/src/content/docs/a1/module/1.mdx"]
        self.assert_docs(self.classify(curriculum_only))
        self.assert_content(self.classify(with_site))
        self.assert_docs(self.classify(curriculum_only, event="merge_group"))
        self.assert_content(self.classify(with_site, event="merge_group"))

    def test_merge_group_content_class(self):
        # #8437: curriculum markdown without learner pages stays on the docs lane.
        self.assert_docs(self.classify(["curriculum/l2-uk-en/a1/module/lesson-1/module.md"], event="merge_group"))

    def test_merge_group_docs_only_stays_docs(self):
        # #8437: a docs merge does not rebuild the site or run four shards.
        self.assert_docs(
            self.classify(["docs/guide.md", "README.md"], event="merge_group"),
        )

    def test_merge_group_script_and_test_forces_full(self):
        # D1 (#8399): what would be `selected` on a pull request is full on
        # the queue.
        tree = _tree(
            "scripts/delegate.py",
            "tests/test_delegate.py",
            "tests/test_ci_shard_partition.py",
        )
        paths = ["scripts/delegate.py", "tests/test_delegate.py"]
        expected = ["tests/test_ci_shard_partition.py", "tests/test_delegate.py"]
        self.assert_selected(self.classify(paths, tree_paths=tree), expected)
        self.assert_selected(
            self.classify(paths, event="merge_group", tree_paths=tree),
            expected,
        )

    def test_merge_group_mixed_forces_full(self):
        tree = _tree(
            "scripts/delegate.py",
            "tests/test_delegate.py",
            "tests/test_ci_shard_partition.py",
        )
        # Non-content merge groups resolve to full exactly as on main:
        # frontend is forced on.
        self.assert_full(
            self.classify(
                ["curriculum/l2-uk-en/a1/module/lesson-1/module.md", "scripts/delegate.py"],
                event="merge_group",
                tree_paths=tree,
            ),
            frontend="false",
        )

    def test_merge_group_compare_failure_fails_closed(self):
        env = {
            "PYTEST_SHARD_COUNT": "4",
            "EVENT_NAME": "merge_group",
            "BASE": "base",
            "HEAD": "head",
            "REPO": "owner/repo",
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            env["GITHUB_OUTPUT"] = str(output)
            with (
                patch.dict(os.environ, env, clear=True),
                patch.object(scope, "compare_paths", side_effect=OSError()),
                contextlib.redirect_stdout(io.StringIO()) as stdout,
            ):
                scope.main()
        self.assertIn("files=0", stdout.getvalue())
        self.assertIn("pytest_mode=full", stdout.getvalue())
        self.assertIn("docs_only=false", stdout.getvalue())

    def test_content_rename_within_roots(self):
        # D6 (#8399): compare_paths emits both rename endpoints; a rename that
        # stays inside the content roots is still content class on the queue.
        paths = [
            "curriculum/l2-uk-en/a1/module/lesson-1/module.md",
            "curriculum/l2-uk-en/a1/module/lesson-1/module-renamed.md",
        ]
        self.assert_docs(self.classify(paths, event="merge_group"))

    def test_rename_from_content_root_to_outside_forces_full(self):
        # D6 (#8399): the rename destination is outside every docs/content
        # exemption, so the change is full on both events.
        paths = [
            "curriculum/l2-uk-en/a1/module/lesson-1/module.md",
            "dashboards/moved.md",
        ]
        self.assert_full(self.classify(paths), frontend="false")
        self.assert_full(self.classify(paths, event="merge_group"), frontend="false")

    def test_content_change_plus_deleted_reads_content_test_forces_full(self):
        # D6 (#8399): a content change that also deletes a reads_content test
        # module must not run the content lane that relies on it. The deleted
        # path is absent from the HEAD tree.
        tree = _tree(
            "curriculum/l2-uk-en/a1/module/lesson-1/module.md",
            "tests/test_ci_shard_partition.py",
        )
        paths = [
            "curriculum/l2-uk-en/a1/module/lesson-1/module.md",
            "tests/test_reads_content_marker_invariant.py",
        ]
        self.assert_full(self.classify(paths, tree_paths=tree), frontend="false")
        self.assert_full(self.classify(paths, event="merge_group", tree_paths=tree), frontend="false")

    def test_full_ci_label_forces_full_over_content(self):
        self.assert_full(
            self.classify(["curriculum/l2-uk-en/a1/module/lesson-1/module.md"], labels=["full-ci"]),
            frontend="true",
        )

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
                if entry in {"site/", "packages/activity-kit/"}:
                    self.assert_frontend_only(self.classify([path]))
                else:
                    self.assert_full(self.classify([path]), frontend="true")
        self.assert_frontend_only(self.classify(["packages/activity-kit/src/index.ts"]))

    def test_event_and_label_overrides(self):
        # Only pull_request and merge_group classify by changed paths (#8399);
        # every other event forces the full tier including frontend.
        for event in ("schedule", "workflow_dispatch", "unknown"):
            with self.subTest(event=event):
                self.assert_full(self.classify(["docs/guide.md"], event=event), frontend="true")
        self.assert_full(self.classify(["docs/guide.md"], labels=["full-ci"]), frontend="true")
        self.assert_docs(self.classify(["docs/guide.md"], labels=["unrelated"]))
        # #8437: a docs merge stays on the docs lane.
        self.assert_docs(self.classify(["docs/guide.md"], event="merge_group"))

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
        command.return_value = json.dumps(
            {
                "files": [
                    {"filename": "docs/moved.md", "previous_filename": "scripts/ci/README.md"},
                    {"filename": "unknown/line\nbreak.md"},
                ]
            }
        )
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
                "docs_only=false\nfrontend=true\nbackend=true\nshards=[1, 2, 3, 4]\n"
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
                with (
                    self.subTest(error=type(error).__name__),
                    patch.dict(os.environ, env),
                    patch.object(scope, "compare_paths", side_effect=error),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    output.write_text("")
                    scope.main()
                    self.assertEqual(output.read_text(), full_line)
            with (
                patch.dict(os.environ, env),
                patch.object(scope, "compare_paths", return_value=["docs/guide.md"]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                output.write_text("")
                scope.main()
                self.assertEqual(
                    output.read_text(),
                    "docs_only=true\nfrontend=false\nbackend=true\nshards=[1]\n"
                    "pytest_mode=docs\nshard_count=1\npytest_candidates=[]\n",
                )

    def test_forced_events_do_not_need_compare_api(self):
        # schedule stays force-full without touching the compare API.
        with (
            patch.dict(os.environ, {"PYTEST_SHARD_COUNT": "4", "EVENT_NAME": "schedule"}, clear=True),
            patch.object(scope, "compare_paths") as compare,
            contextlib.redirect_stdout(io.StringIO()) as stdout,
        ):
            scope.main()
            compare.assert_not_called()
            self.assertIn("docs_only=false", stdout.getvalue())
            self.assertIn("frontend=true", stdout.getvalue())
            self.assertIn("pytest_mode=full", stdout.getvalue())
            self.assertIn("shard_count=4", stdout.getvalue())
            self.assertIn("shards=[1, 2, 3, 4]", stdout.getvalue())
            self.assertIn("pytest_candidates=[]", stdout.getvalue())

    def test_merge_group_without_event_env_fails_closed(self):
        # merge_group classifies by paths (#8399), but a missing REPO env must
        # fail closed to full before the compare API is ever called.
        with (
            patch.dict(os.environ, {"PYTEST_SHARD_COUNT": "4", "EVENT_NAME": "merge_group"}, clear=True),
            patch.object(scope, "compare_paths") as compare,
            contextlib.redirect_stdout(io.StringIO()) as stdout,
        ):
            scope.main()
            compare.assert_not_called()
            self.assertIn("pytest_mode=full", stdout.getvalue())
            self.assertIn("docs_only=false", stdout.getvalue())

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

    def test_inbox_watch_selected(self):
        tree = _tree(
            "scripts/ai_agent_bridge/_inbox_watch.py",
            "tests/ai_agent_bridge/test_inbox_watch.py",
            "tests/test_ci_shard_partition.py",
        )
        # PR #8496 pattern: changed script and test file
        result = self.classify(
            ["scripts/ai_agent_bridge/_inbox_watch.py", "tests/ai_agent_bridge/test_inbox_watch.py"],
            tree_paths=tree,
        )
        self.assert_selected(
            result,
            [
                "tests/ai_agent_bridge/test_inbox_watch.py",
                "tests/test_ci_shard_partition.py",
            ],
        )
        # Script change alone finds matching test in tree
        result_script_only = self.classify(
            ["scripts/ai_agent_bridge/_inbox_watch.py"],
            tree_paths=tree,
        )
        self.assert_selected(
            result_script_only,
            [
                "tests/ai_agent_bridge/test_inbox_watch.py",
                "tests/test_ci_shard_partition.py",
            ],
        )

    def test_leading_underscore_stem_collision_forces_full(self):
        tree = _tree(
            "scripts/ai_agent_bridge/_inbox_watch.py",
            "scripts/other/inbox_watch.py",
            "tests/ai_agent_bridge/test_inbox_watch.py",
            "tests/test_ci_shard_partition.py",
        )
        # Stripped stem 'inbox_watch' collides with scripts/other/inbox_watch.py
        self.assert_full(
            self.classify(["scripts/ai_agent_bridge/_inbox_watch.py"], tree_paths=tree),
            frontend="false",
        )

    def test_package_mapping_positive_and_negative(self):
        tree_pos = _tree(
            "scripts/ai_agent_bridge/custom_worker.py",
            "tests/ai_agent_bridge/test_custom_worker.py",
            "tests/test_ci_shard_partition.py",
        )
        self.assertEqual(
            scope._package_map_tests("scripts/ai_agent_bridge/custom_worker.py", tree_pos),
            ["tests/ai_agent_bridge/test_custom_worker.py"],
        )
        self.assert_selected(
            self.classify(["scripts/ai_agent_bridge/custom_worker.py"], tree_paths=tree_pos),
            [
                "tests/ai_agent_bridge/test_custom_worker.py",
                "tests/test_ci_shard_partition.py",
            ],
        )

        tree_neg = _tree(
            "scripts/pkg_a/worker.py",
            "tests/pkg_b/test_worker.py",
            "tests/test_ci_shard_partition.py",
        )
        self.assertEqual(
            scope._package_map_tests("scripts/pkg_a/worker.py", tree_neg),
            [],
        )
        self.assertEqual(
            scope._package_map_tests("scripts/delegate.py", tree_pos),
            [],
        )

    def test_new_fail_closed_triggers_force_full(self):
        triggers = (
            "pytest.ini",
            "setup.cfg",
            "tox.ini",
            "tests/conftest.py",
            "tests/sub/conftest.py",
            "tests/helpers.py",
            "tests/fixtures/data.json",
        )
        for path in triggers:
            with self.subTest(path=path):
                tree = _tree(path, "tests/test_x.py", "tests/test_ci_shard_partition.py")
                self.assertTrue(scope.hits_shared_root_denylist(path))
                self.assert_full(self.classify([path], tree_paths=tree), frontend="false")


if __name__ == "__main__":
    unittest.main()
