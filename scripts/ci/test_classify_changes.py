"""Stdlib acceptance checks for the standalone candidate selector."""

import unittest

from scripts.ci.classify_changes import SAFETY_NET, SELECTED_CANDIDATE_CEILING, build_selected_candidates
from scripts.ci.test_impact import build_graph


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.sources = {
            "scripts/tool.py": "VALUE = 1",
            "tests/test_tool.py": "import scripts.tool",
            "tests/test_indirect.py": "from scripts import tool",
            SAFETY_NET: "",
        }

    def select(self, paths):
        return build_selected_candidates(paths, self.sources, impact_graph=build_graph(sources=self.sources))

    def test_union_of_stems_importers_and_safety_net(self):
        self.sources["tests/test_tool_extra.py"] = ""
        self.assertEqual(self.select(["scripts/tool.py"]), [
            SAFETY_NET, "tests/test_indirect.py", "tests/test_tool.py", "tests/test_tool_extra.py",
        ])

    def test_graph_only_selection_without_stem_match(self):
        self.sources.pop("tests/test_tool.py")
        self.assertEqual(self.select(["scripts/tool.py"]), [SAFETY_NET, "tests/test_indirect.py"])

    def test_stem_match_does_not_override_no_dependents(self):
        self.sources["tests/test_tool.py"] = ""
        self.sources["tests/test_indirect.py"] = ""
        self.assertIsNone(self.select(["scripts/tool.py"]))

    def test_uncertainty_outside_reverse_closure_fails_closed(self):
        self.sources["tests/test_loader.py"] = "__import__(target)"
        self.assertIsNone(self.select(["scripts/tool.py"]))
        self.sources["scripts/loader.py"] = "import scripts.tool\n__import__(target)"
        self.assertIsNone(self.select(["scripts/tool.py"]))

    def test_existing_full_triggers(self):
        for path in (
            "scripts/ci/tool.py", "tests/conftest.py", "tests/deleted.py",
            "scripts/deleted.py", "scripts/tool.sh", "requirements.txt", "pyproject.toml",
        ):
            with self.subTest(path=path):
                self.assertIsNone(self.select([path]))

    def test_ambiguous_stems_and_missing_safety_net(self):
        self.sources["scripts/other/tool.py"] = ""
        self.assertIsNone(self.select(["scripts/tool.py"]))
        self.sources.pop("scripts/other/tool.py")
        self.sources.pop(SAFETY_NET)
        self.assertIsNone(self.select(["scripts/tool.py"]))

    def test_ceiling_and_empty_changes(self):
        self.assertIsNone(self.select([]))
        self.sources.update({
            f"tests/test_other_{index}.py": "import scripts.tool" for index in range(SELECTED_CANDIDATE_CEILING)
        })
        self.assertIsNone(self.select(["scripts/tool.py"]))

    def test_test_only_includes_importers_and_safety_tests(self):
        self.sources["tests/test_indirect.py"] = "import tests.test_tool"
        self.sources["tests/test_invariant.py"] = "import pytest\npytestmark = pytest.mark.repo_wide"
        self.assertEqual(self.select(["tests/test_tool.py"]), [
            SAFETY_NET, "tests/test_indirect.py", "tests/test_invariant.py", "tests/test_tool.py",
        ])


if __name__ == "__main__":
    unittest.main()
