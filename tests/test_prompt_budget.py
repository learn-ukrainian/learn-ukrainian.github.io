"""Deterministic tests for v6 prompt composition metadata (#1280).

Tests the prompt manifest builders, audit functions, and context
shaping logic introduced to enforce prompt budgets per phase.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.v6_build import (
    CHUNK_PROMPT_MAX_CHARS,
    _audit_chunk_prompt,
    _build_chunk_prompt,
    _build_chunk_prompt_manifest,
    _build_skeleton_prompt_manifest,
    _section_has_dialogue_content,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_PLAN = {
    "title": "Test Module",
    "phase": "core",
    "word_target": 2000,
}

MINIMAL_SECTION = {
    "title": "## Test Section (~300 words total)",
    "body": "## Test Section (~300 words total)\n\n- P1 (~150 words): Intro.\n- P2 (~150 words): Detail.",
    "words": 300,
}

DIALOGUE_SECTION = {
    "title": "## Діалог: У кав'ярні (~400 words total)",
    "body": (
        "## Діалог: У кав'ярні (~400 words total)\n\n"
        "- P1 (~50 words): Scene-setting.\n"
        "- Dialogue (~200 words): Ordering coffee.\n"
        "> — **Оксана:** Добрий день!\n"
        "> — **Бариста:** Вітаю!\n"
        "- P2 (~150 words): Wrap-up."
    ),
    "words": 400,
}


# ---------------------------------------------------------------------------
# _section_has_dialogue_content
# ---------------------------------------------------------------------------

class TestSectionHasDialogueContent:

    def test_title_with_dialogue_keyword(self):
        assert _section_has_dialogue_content("plain body", "Діалог: У кав'ярні") is True

    def test_title_with_english_dialogue(self):
        assert _section_has_dialogue_content("plain body", "Dialogues and Greetings") is True

    def test_body_with_speaker_turn(self):
        body = "> — **Оксана:** Привіт!\n> — **Тарас:** Добрий день!"
        assert _section_has_dialogue_content(body, "Plain Title") is True

    def test_no_dialogue_content(self):
        assert _section_has_dialogue_content("Just normal prose.", "Grammar Rules") is False


# ---------------------------------------------------------------------------
# _build_chunk_prompt — structure validation
# ---------------------------------------------------------------------------

class TestBuildChunkPrompt:

    def _make_prompt(self, section=None, **overrides):
        defaults = dict(
            section=section or MINIMAL_SECTION,
            section_index=0,
            total_sections=4,
            previous_summary="",
            contract_content="current_section:\n  name: Test",
            section_excerpts="section: Test\nitems: []",
            level="a1",
            module_num=5,
            plan=MINIMAL_PLAN,
            slug="test-module",
            section_required_terms=["слово", "речення"],
            all_required_words=["слово", "речення", "граматика"],
        )
        defaults.update(overrides)
        return _build_chunk_prompt(**defaults)

    def test_no_wiki_chunk_context_placeholder(self):
        """Dead {WIKI_CHUNK_CONTEXT} placeholder must not appear."""
        prompt = self._make_prompt()
        assert "{WIKI_CHUNK_CONTEXT}" not in prompt

    def test_contains_section_skeleton(self):
        prompt = self._make_prompt()
        assert "Section Skeleton" in prompt

    def test_contains_forbidden_words(self):
        prompt = self._make_prompt()
        assert "FORBIDDEN WORDS" in prompt

    def test_contains_teacher_voice_block_before_contract(self):
        prompt = self._make_prompt()
        teacher_voice = "## Teacher voice (follow this shape)"
        contract = "## Shared Contract (authoritative — GH #1431)"
        assert teacher_voice in prompt
        assert prompt.index(teacher_voice) < prompt.index(contract)

    def test_dialogue_formatting_excluded_for_plain_section(self):
        prompt = self._make_prompt(section=MINIMAL_SECTION)
        assert "Dialogue formatting" not in prompt

    def test_dialogue_formatting_included_for_dialogue_section(self):
        prompt = self._make_prompt(section=DIALOGUE_SECTION)
        assert "Dialogue formatting" in prompt

    def test_previous_summary_excluded_on_first_section(self):
        prompt = self._make_prompt(previous_summary="")
        assert "Previous Sections" not in prompt

    def test_previous_summary_included_when_present(self):
        prompt = self._make_prompt(previous_summary="Previous content here.")
        assert "Previous Sections" in prompt

    def test_vocab_checklist_included_when_terms_exist(self):
        prompt = self._make_prompt(section_required_terms=["слово"])
        assert "REQUIRED VOCABULARY CHECKLIST" in prompt

    def test_vocab_checklist_excluded_when_no_terms(self):
        prompt = self._make_prompt(
            section_required_terms=[],
            all_required_words=[],
        )
        assert "REQUIRED VOCABULARY CHECKLIST" not in prompt


# ---------------------------------------------------------------------------
# _build_chunk_prompt_manifest
# ---------------------------------------------------------------------------

class TestBuildChunkPromptManifest:

    def _make_manifest(self, **overrides):
        defaults = dict(
            section_name="Test Section",
            section_index=1,
            total_sections=4,
            prompt="x" * 5000,
            contract_content="contract text",
            section_excerpts="excerpt text",
            previous_summary="previous summary",
            has_dialogue=False,
            has_vocab_checklist=True,
        )
        defaults.update(overrides)
        return _build_chunk_prompt_manifest(**defaults)

    def test_phase_is_write_chunk(self):
        m = self._make_manifest()
        assert m["phase"] == "write-chunk"

    def test_section_metadata(self):
        m = self._make_manifest(section_name="Діалог", section_index=2, total_sections=5)
        assert m["section"] == "Діалог"
        assert m["section_index"] == 2
        assert m["total_sections"] == 5

    def test_metrics_present(self):
        m = self._make_manifest()
        assert "prompt_chars" in m["metrics"]
        assert "prompt_words" in m["metrics"]
        assert "contract_chars" in m["metrics"]
        assert "excerpt_chars" in m["metrics"]
        assert "previous_summary_chars" in m["metrics"]

    def test_flags_reflect_dialogue(self):
        m1 = self._make_manifest(has_dialogue=False)
        assert m1["flags"]["includes_dialogue_formatting"] is False

        m2 = self._make_manifest(has_dialogue=True)
        assert m2["flags"]["includes_dialogue_formatting"] is True

    def test_components_include_dialogue_when_flagged(self):
        m = self._make_manifest(has_dialogue=True)
        assert "dialogue_formatting" in m["components"]

    def test_components_exclude_dialogue_when_not_flagged(self):
        m = self._make_manifest(has_dialogue=False)
        assert "dialogue_formatting" not in m["components"]

    def test_components_include_vocab_when_flagged(self):
        m = self._make_manifest(has_vocab_checklist=True)
        assert "required_vocab_checklist" in m["components"]

    def test_components_exclude_vocab_when_not_flagged(self):
        m = self._make_manifest(has_vocab_checklist=False)
        assert "required_vocab_checklist" not in m["components"]

    def test_previous_summary_flag(self):
        m1 = self._make_manifest(previous_summary="")
        assert m1["flags"]["includes_previous_summary"] is False

        m2 = self._make_manifest(previous_summary="content")
        assert m2["flags"]["includes_previous_summary"] is True


# ---------------------------------------------------------------------------
# _audit_chunk_prompt
# ---------------------------------------------------------------------------

class TestAuditChunkPrompt:

    def test_passes_under_budget(self):
        manifest = {
            "metrics": {"prompt_chars": CHUNK_PROMPT_MAX_CHARS - 1},
        }
        assert _audit_chunk_prompt(manifest) == []

    def test_fails_over_budget(self):
        manifest = {
            "metrics": {"prompt_chars": CHUNK_PROMPT_MAX_CHARS + 1},
        }
        failures = _audit_chunk_prompt(manifest)
        assert len(failures) == 1
        assert "exceeds max chars" in failures[0]

    def test_passes_exactly_at_budget(self):
        manifest = {
            "metrics": {"prompt_chars": CHUNK_PROMPT_MAX_CHARS},
        }
        assert _audit_chunk_prompt(manifest) == []


# ---------------------------------------------------------------------------
# _build_skeleton_prompt_manifest
# ---------------------------------------------------------------------------

class TestBuildSkeletonPromptManifest:

    def test_phase_is_skeleton(self):
        m = _build_skeleton_prompt_manifest(
            prompt="p" * 100,
            plan_content="plan",
            packet="packet",
            word_target=2000,
        )
        assert m["phase"] == "skeleton"

    def test_metrics_present(self):
        m = _build_skeleton_prompt_manifest(
            prompt="p" * 500,
            plan_content="plan" * 100,
            packet="packet" * 200,
            word_target=3000,
        )
        assert m["metrics"]["prompt_chars"] == 500
        assert m["metrics"]["plan_chars"] == 400
        assert m["metrics"]["packet_chars"] == 1200
        assert m["word_target"] == 3000

    def test_packet_truncated_flag(self):
        m = _build_skeleton_prompt_manifest(
            prompt="p",
            plan_content="plan",
            packet="some text... truncated for context window",
            word_target=1000,
        )
        assert m["flags"]["packet_truncated"] is True

    def test_packet_not_truncated_flag(self):
        m = _build_skeleton_prompt_manifest(
            prompt="p",
            plan_content="plan",
            packet="full packet content",
            word_target=1000,
        )
        assert m["flags"]["packet_truncated"] is False

    def test_components_list(self):
        m = _build_skeleton_prompt_manifest(
            prompt="p",
            plan_content="plan",
            packet="packet",
            word_target=1000,
        )
        assert "template" in m["components"]
        assert "plan_content" in m["components"]
        assert "knowledge_packet" in m["components"]
