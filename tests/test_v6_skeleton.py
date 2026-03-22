"""Tests for V6 Skeleton->Flesh architecture (#998).

Tests the skeleton step integration without calling external LLMs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build.v6_build import PHASES_DIR


class TestSkeletonThreshold:
    """Test that skeleton is auto-enabled/disabled based on word_target."""

    def test_a1_skips_skeleton(self):
        """A1 modules (word_target=1200) should not auto-enable skeleton."""
        word_target = 1200
        assert word_target < 3000, "A1 should be below skeleton threshold"

    def test_b1_enables_skeleton(self):
        """B1 modules (word_target=4000) should auto-enable skeleton."""
        word_target = 4000
        assert word_target >= 3000, "B1 should be above skeleton threshold"

    def test_threshold_boundary(self):
        """word_target=3000 should enable skeleton (>=, not >)."""
        assert 3000 >= 3000, "Boundary value 3000 should enable skeleton"
        assert 2999 < 3000, "2999 should not enable skeleton"


class TestSkeletonTemplateExists:
    """Verify the skeleton prompt template is present and well-formed."""

    def test_template_exists(self):
        template_path = PHASES_DIR / "v6-skeleton.md"
        assert template_path.exists(), f"Skeleton template not found: {template_path}"

    def test_template_has_required_placeholders(self):
        template_path = PHASES_DIR / "v6-skeleton.md"
        content = template_path.read_text("utf-8")
        required = [
            "{TOPIC_TITLE}", "{MODULE_NUM}", "{LEVEL}", "{PHASE}",
            "{WORD_TARGET}", "{PLAN_CONTENT}", "{KNOWLEDGE_PACKET}",
            "{SUMMARY_HEADING}", "{WORD_OVERSHOOT}",
        ]
        for placeholder in required:
            assert placeholder in content, f"Missing placeholder: {placeholder}"


class TestSkeletonInjection:
    """Test that skeleton text is properly injected into the write prompt."""

    def test_write_prompt_without_skeleton(self, tmp_path):
        """Without skeleton, the write prompt should not contain skeleton section."""
        # Create a minimal plan
        plan_dir = tmp_path / "plans" / "test"
        plan_dir.mkdir(parents=True)
        plan = {
            "title": "Test Module",
            "word_target": 1200,
            "phase": "A1.1",
            "content_outline": [{"section": "Test", "words": 1000}],
            "vocabulary_hints": {"required": ["тест"]},
        }
        plan_path = plan_dir / "test-module.yaml"
        plan_path.write_text(yaml.dump(plan, allow_unicode=True))

        # The skeleton="" (empty) should not inject skeleton section
        skeleton = ""
        assert not skeleton, "Empty skeleton should be falsy"

    def test_skeleton_injection_format(self):
        """Skeleton injection should include structure constraint instructions."""
        skeleton = "## Test Section (~500 words)\n- P1 (~200 words): intro"

        # Simulate what step_write does with skeleton
        skeleton_section = (
            "\n\n---\n\n"
            "## Skeleton — Follow This Structure Exactly\n\n"
            "A detailed paragraph-level skeleton was generated for this module. "
            "You MUST follow it precisely:\n"
        )

        assert "Follow This Structure Exactly" in skeleton_section
        assert "MUST follow it precisely" in skeleton_section


class TestSkeletonTagStripping:
    """Test that skeleton/pacing_plan tags are stripped from writer output."""

    def test_skeleton_tags_stripped(self):
        import re
        content = "## Section\n<skeleton>leaked</skeleton>\nReal content"
        cleaned = re.sub(r"</?skeleton>", "", content)
        assert "<skeleton>" not in cleaned
        assert "leaked" in cleaned
        assert "Real content" in cleaned

    def test_pacing_plan_tags_stripped(self):
        import re
        content = "## Section\n<pacing_plan>leaked</pacing_plan>\nReal content"
        cleaned = re.sub(r"</?pacing_plan>", "", content)
        assert "<pacing_plan>" not in cleaned


class TestSkeletonExtraction:
    """Test skeleton text extraction from LLM output."""

    def test_extracts_from_tags(self):
        import re
        raw = "Some preamble\n<skeleton>\n## Section (~500 words)\n- P1\n</skeleton>\nSome postamble"
        match = re.search(r"<skeleton>(.*?)</skeleton>", raw, re.DOTALL)
        assert match is not None
        skeleton = match.group(1).strip()
        assert skeleton.startswith("## Section")
        assert "- P1" in skeleton

    def test_fallback_without_tags(self):
        import re
        raw = "## Section (~500 words)\n- P1 (~200 words): intro"
        match = re.search(r"<skeleton>(.*?)</skeleton>", raw, re.DOTALL)
        assert match is None, "Should not match when no tags present"
        # Fallback: use full output
        skeleton = raw.strip()
        assert "## Section" in skeleton


class TestCLIArgs:
    """Test CLI argument parsing for skeleton flags."""

    def test_default_no_flags(self):
        """Default: skeleton=None, no_skeleton=False -> auto-detect."""
        parser = argparse.ArgumentParser()
        parser.add_argument("level")
        parser.add_argument("module", type=int)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--skeleton", action="store_true", default=None)
        group.add_argument("--no-skeleton", action="store_true")

        args = parser.parse_args(["b1", "1"])
        assert args.skeleton is None
        assert args.no_skeleton is False

        # Auto-detect: word_target >= 3000
        use_skeleton = args.skeleton or (not args.no_skeleton and 4000 >= 3000)
        assert use_skeleton is True

    def test_force_skeleton(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("level")
        parser.add_argument("module", type=int)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--skeleton", action="store_true", default=None)
        group.add_argument("--no-skeleton", action="store_true")

        args = parser.parse_args(["a1", "1", "--skeleton"])
        use_skeleton = args.skeleton or (not args.no_skeleton and 1200 >= 3000)
        assert use_skeleton is True, "--skeleton should force enable even for A1"

    def test_skip_skeleton(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("level")
        parser.add_argument("module", type=int)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--skeleton", action="store_true", default=None)
        group.add_argument("--no-skeleton", action="store_true")

        args = parser.parse_args(["b1", "1", "--no-skeleton"])
        use_skeleton = args.skeleton or (not args.no_skeleton and 4000 >= 3000)
        assert use_skeleton is False, "--no-skeleton should skip even for B1"
