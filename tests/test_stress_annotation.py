"""Tests for stress_annotator.py (#988).

Validates post-processing stress annotation:
- Apostrophe words stressed correctly
- Proper nouns not double-stressed
- Code blocks and URLs untouched
- No duplicate stress on re-annotation
- Performance within budget
"""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

from scripts.pipeline.stress_annotator import (
    STRESS_MARK,
    _count_syllables,
    annotate_file,
    annotate_stress,
)


class TestOraclePedagogy:
    """Sources verify_stress oracle: repair, collapse, keep valid singles.

    These lookups hit the offline ULIF trie (no Stanza).
    """

    def test_retains_dual_accents_without_source_choice(self):
        result, count = annotate_stress("Це розбір і корисний приклад.")
        assert f"ро{STRESS_MARK}збі{STRESS_MARK}р" in result
        assert f"ко{STRESS_MARK}ри{STRESS_MARK}сний" in result
        assert count >= 2
        assert annotate_stress(result) == (result, 0)

    def test_repairs_wrong_single_acute(self):
        result, count = annotate_stress(f"Це се{STRESS_MARK}стра. Вона говори{STRESS_MARK}ть.")
        assert f"се{STRESS_MARK}стра" not in result
        assert f"говори{STRESS_MARK}ть" not in result
        assert f"сестра{STRESS_MARK}" in result
        assert f"гово{STRESS_MARK}рить" in result
        assert count >= 2

    def test_keeps_valid_single_on_dual_word(self):
        text = f"Розбі{STRESS_MARK}р."
        result, count = annotate_stress(text)
        assert f"Розбі{STRESS_MARK}р" in result
        assert f"Ро{STRESS_MARK}збі{STRESS_MARK}р" not in result
        assert count == 0

    def test_title_case_mene_uses_lowercase_oracle(self, ulif_stress_db, monkeypatch):
        from scripts.pipeline import stress_annotator as sa
        from scripts.verification.stress import verify_stress

        assert verify_stress("мене")["stress_source"] == "ulif"
        # Freeze the parser's pronoun analysis: the captured store also has a
        # distinct proper-name Мене reading. No host Stanza model is required.
        token = types.SimpleNamespace(
            start_char=0,
            end_char=4,
            to_dict=lambda: [{"lemma": "я", "upos": "PRON", "feats": "Case=Acc|Number=Sing|Person=1"}],
        )

        def parser(text):
            return types.SimpleNamespace(iter_tokens=lambda: iter([token]))

        monkeypatch.setattr(sa, "_get_stressifier", lambda: types.SimpleNamespace(nlp=parser))
        result, _count = annotate_stress("Мене звати Олег.")
        assert f"Ме{STRESS_MARK}не" not in result
        assert f"Мене{STRESS_MARK}" in result

    def test_ambiguous_metalanguage_stays_bare_without_context(self, monkeypatch):
        from scripts.pipeline import stress_annotator as sa

        monkeypatch.setattr(sa, "_get_stressifier", lambda: object())
        result, count = annotate_stress("Правила. Підсумок.")
        assert result == "Правила. Підсумок."
        assert count == 0

    def test_zavzhdy_override_not_last_vowel(self):
        result, _count = annotate_stress("Я завжди тут.")
        assert f"за{STRESS_MARK}вжди{STRESS_MARK}" not in result
        assert f"за{STRESS_MARK}вжди" in result
        assert f"завжди{STRESS_MARK}" not in result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stress_positions(word: str) -> list[int]:
    """Return indices of stress marks in *word*."""
    return [i for i, c in enumerate(word) if c == STRESS_MARK]


def _stressed_form(text: str, target: str) -> str | None:
    """Find the annotated form of *target* (unstressed) in *text*.

    Returns the form with stress mark(s) if found, else None.
    Handles combining accent marks (U+0301) that don't count as characters
    in the base word.
    """
    target_lower = target.lower()
    # Build a version of text stripped of stress marks, with a mapping
    # from stripped-index to original-index
    stripped_chars: list[str] = []
    orig_indices: list[int] = []
    for i, c in enumerate(text):
        if c == STRESS_MARK:
            continue
        stripped_chars.append(c)
        orig_indices.append(i)
    stripped = "".join(stripped_chars)

    idx = stripped.lower().find(target_lower)
    if idx == -1:
        return None

    # Map back: find the span in the original text
    orig_start = orig_indices[idx]
    orig_end_base = orig_indices[idx + len(target) - 1]
    # Include any trailing combining marks
    orig_end = orig_end_base + 1
    while orig_end < len(text) and text[orig_end] == STRESS_MARK:
        orig_end += 1

    return text[orig_start:orig_end]


# ---------------------------------------------------------------------------
# Unit tests for internal helpers
# ---------------------------------------------------------------------------


class TestCountSyllables:

    def test_apostrophe_word(self):
        # сім'я has 2 vowels → 2 syllables
        assert _count_syllables("сім'я") == 2


# ---------------------------------------------------------------------------
# Integration tests for annotate_stress
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestApostropheWords:
    """AC: apostrophe words (сім'я, м'ясо) stressed correctly."""

    def test_apostrophe_words_get_stressed(self):
        # п'ять is monosyllabic (1 vowel) so annotator correctly skips it
        text = "Це сім'я і м'ясо та п'ять."
        result, count = annotate_stress(text)
        assert count > 0, "Should stress at least one apostrophe word"

        # Multi-syllable apostrophe words should have exactly one stress mark
        for word in ["сім'я", "м'ясо"]:
            form = _stressed_form(result, word)
            assert form is not None, f"{word} should be found in result"
            positions = _stress_positions(form)
            assert len(positions) == 1, f"{word} should have exactly 1 stress mark, got {len(positions)} in '{form}'"

        # п'ять is monosyllabic — should NOT be stressed
        pyat_form = _stressed_form(result, "п'ять")
        if pyat_form is not None:
            assert STRESS_MARK not in pyat_form, "Monosyllabic п'ять should not be stressed"

    def test_simya_stress_on_ya(self):
        """сім'я́ — stress falls on the last syllable (я)."""
        text = "Моя сім'я велика."
        result, _ = annotate_stress(text)
        form = _stressed_form(result, "сім'я")
        if form is not None:
            # The stress mark should appear after я (the last vowel)
            assert STRESS_MARK in form, f"сім'я should be stressed, got '{form}'"
            # я is the stressed vowel — mark should follow it
            ya_idx = form.rfind("я")
            assert ya_idx != -1
            assert ya_idx + 1 < len(form) and form[ya_idx + 1] == STRESS_MARK, (
                f"Stress should be on я in сім'я, got '{form}'"
            )


@pytest.mark.slow
class TestApostropheSpellings:
    """Typographic ’ and the YAML '' escape are one word, not two (#7994)."""

    @pytest.mark.parametrize("apostrophe", ["'", "’", "ʼ", "''"])
    def test_contradicting_mark_is_replaced(self, apostrophe: str):
        wrong = f"дере{STRESS_MARK}в{apostrophe}яний"
        result, count = annotate_stress(f"Це {wrong} стіл.")
        assert count == 1
        assert wrong not in result
        assert f"дерев{apostrophe}я{STRESS_MARK}ний" in result

    @pytest.mark.parametrize("apostrophe", ["’", "''"])
    def test_unmarked_word_is_stressed_whole(self, apostrophe: str):
        result, _ = annotate_stress(f"- 'сім{apostrophe}я і дерев{apostrophe}яний'")
        assert f"сім{apostrophe}я{STRESS_MARK}" in result
        assert f"дерев{apostrophe}я{STRESS_MARK}ний" in result
        assert f"дере{STRESS_MARK}в" not in result
        assert annotate_stress(result)[1] == 0

    def test_module_md_and_activities_yaml_files_are_repaired(self, tmp_path: Path):
        wrong = f"дере{STRESS_MARK}в'яний"
        module = tmp_path / "module.md"
        module.write_text(f"Це **{wrong}** стіл.\n", encoding="utf-8")
        activities = tmp_path / "activities.yaml"
        activities.write_text(
            f"inline:\n- items:\n  - sentence: 'Це {wrong.replace(chr(39), chr(39) * 2)} стіл і сім''я.'\n",
            encoding="utf-8",
        )
        assert annotate_file(module) == 1
        assert annotate_file(activities) > 0
        assert f"дерев'я{STRESS_MARK}ний" in module.read_text(encoding="utf-8")
        import yaml

        sentence = yaml.safe_load(activities.read_text(encoding="utf-8"))["inline"][0]["items"][0]["sentence"]
        assert f"дерев'я{STRESS_MARK}ний" in sentence and f"сім'я{STRESS_MARK}" in sentence
        assert f"дере{STRESS_MARK}в" not in sentence


class TestProperNouns:
    """AC: proper nouns not double-stressed."""

    def test_single_stress_on_proper_noun(self):
        text = "Це Київ, столиця України."
        result, _ = annotate_stress(text)
        form = _stressed_form(result, "Київ")
        if form is not None:
            positions = _stress_positions(form)
            assert len(positions) <= 1, f"Київ should have at most 1 stress mark, got {len(positions)} in '{form}'"


@pytest.mark.slow
class TestNoDuplicateStress:
    """AC: running annotator twice shouldn't double-stress."""

    def test_marks_every_multi_syllable_occurrence(self):
        text = "Мама читає. Мама пише."
        result, count = annotate_stress(text)

        assert count >= 4
        assert result.count(STRESS_MARK) >= 4
        assert result.replace(STRESS_MARK, "") == text

    def test_idempotent(self):
        text = "Моя бабуся живе у Львові."
        result1, _count1 = annotate_stress(text)
        result2, count2 = annotate_stress(result1)
        # Second pass should add zero new marks
        assert count2 == 0, f"Second annotation pass should add 0 marks, added {count2}"
        # Text should be identical
        assert result1 == result2, "Double annotation changed the text"

    def test_single_syllable_and_english_untouched(self):
        text = "Кіт тут. English morning stays English."
        result, count = annotate_stress(text)

        assert count == 0
        assert result == text

    def test_dialoguebox_uk_attr_is_annotated(self):
        text = '<DialogueBox uk="Моя мама читає." en="My mother reads." />'
        result, count = annotate_stress(text)

        assert count > 0
        assert 'en="My mother reads."' in result
        assert f"ма{STRESS_MARK}ма" in result or f"чита{STRESS_MARK}є" in result
        assert '<DialogueBox uk="' in result


@pytest.mark.slow
class TestHeteronyms:
    """AC: heteronyms handled by Stanza context.

    The Stressifier uses Stanza for context-dependent stress placement.
    We verify it doesn't crash or produce garbage on heteronyms.
    """

    def test_zamok_context(self):
        """за́мок (castle) vs замо́к (lock) — context-dependent.

        Note: the Stressifier may decline to stress truly ambiguous words.
        We verify it either stresses correctly (1 mark) or leaves unstressed.
        """
        text = "Старий замок стоїть на горі."
        result, _count = annotate_stress(text)
        form = _stressed_form(result, "замок")
        if form is not None:
            positions = _stress_positions(form)
            # Must have 0 (library declined) or 1 stress mark — never 2+
            assert len(positions) <= 1, f"замок should have at most 1 stress, got {len(positions)} in '{form}'"


# ---------------------------------------------------------------------------
# annotate_file — safety check fix (#1052)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestAnnotateFileSafetyCheck:
    """The 2% safety check should only count stress marks in the body,
    not in Словник/Ресурси tabs that are pre-stressed by vocab_gen.py."""

    def test_slovnyk_stress_does_not_trigger_skip(self, tmp_path):
        """Stress marks in Словник section should NOT cause body to be skipped (#1052)."""
        from scripts.pipeline.stress_annotator import annotate_file

        # Simulate a module with pre-stressed vocabulary section but unstressed body
        body = "Моя мама працює в школі. Українська мова дуже гарна.\n" * 20
        # Add lots of stressed words in Словник (simulating vocab_gen.py output)
        stressed_vocab = f"ма{STRESS_MARK}ма | mother\n" * 50
        content = (
            f"<!-- TAB:Урок -->\n\n{body}\n\n"
            f"<!-- TAB:Словник -->\n\n{stressed_vocab}\n\n"
            f"<!-- TAB:Ресурси -->\n\nSome resources.\n"
        )

        md_file = tmp_path / "test-module.md"
        md_file.write_text(content, encoding="utf-8")

        count = annotate_file(md_file)
        # Body has Ukrainian words that should get stressed
        assert count > 0, "Body content should have been stress-annotated"


# ---------------------------------------------------------------------------
# Stanza model-download concurrency guard (CI flake regression)
#
# The Stressifier constructor lazily downloads the Stanza UK model into a
# shared resources dir. Under `pytest -n auto` (and concurrent V7 builds),
# multiple processes raced to write the same file, corrupting it and tripping
# Stanza's md5 check — failing the whole stress_annotator mutation class plus
# the ULP stress tests. `_get_stressifier` now serializes construction with an
# inter-process file lock. These tests pin that contract without touching the
# network or loading the real model.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]


def _venv_python() -> str:
    """The interpreter running pytest, for subprocess tests."""
    return sys.executable


# Each worker increments a shared counter via a non-atomic read-modify-write
# inside the download lock. With the lock, the final value equals the worker
# count; without it, the deliberate sleep window guarantees lost updates.
_LOCK_COUNTER_SNIPPET = """\
import os, sys, time
sys.path.insert(0, {repo_root!r})
os.environ["STANZA_RESOURCES_DIR"] = {resources_dir!r}
from scripts.pipeline.stress_annotator import _model_download_lock
counter = {counter!r}
with _model_download_lock():
    value = int(open(counter).read())
    time.sleep(0.05)
    open(counter, "w").write(str(value + 1))
"""


class TestModelDownloadLock:
    """The lazy Stressifier load must be concurrency-safe across processes."""

    def test_model_download_lock_serializes_across_processes(self, tmp_path):
        """Concurrent cold starts must not interleave (the #1448-style race)."""
        counter = tmp_path / "counter.txt"
        counter.write_text("0", encoding="utf-8")

        snippet = _LOCK_COUNTER_SNIPPET.format(
            repo_root=str(REPO_ROOT),
            resources_dir=str(tmp_path),
            counter=str(counter),
        )

        worker_count = 5
        python = _venv_python()
        procs = [subprocess.Popen([str(python), "-c", snippet]) for _ in range(worker_count)]
        for proc in procs:
            assert proc.wait(timeout=120) == 0, "lock worker subprocess failed"

        # No lost updates → every worker's increment landed.
        assert counter.read_text(encoding="utf-8") == str(worker_count)


_EC_ACTIVITIES = """\
inline:
- type: error-correction
  instruction: Find the word that lost its apostrophe.
  items:
  - sentence: "Це моя сімя."
    error: сімя
    correction: "сім'я"
    options:
    - сімя
    - "сім'я"
    - мама
    explanation: "Apostrophe before я: сім'я."
workbook:
- type: fill-in
  items:
  - sentence: "Мене звати ___."
    answer: "ім'я"
  - sentence: "Це дере\u0301в'яний стіл."
    answer: стіл
"""


class TestActivitiesYaml:
    """activities.yaml: dictionary stress everywhere except error chips (#7994)."""

    @pytest.fixture
    def annotated(self, tmp_path: Path) -> str:
        path = tmp_path / "activities.yaml"
        path.write_text(_EC_ACTIVITIES, encoding="utf-8")
        assert annotate_file(path) > 0
        return path.read_text(encoding="utf-8")

    def test_correction_and_explanation_gain_stress(self, annotated: str):
        marked = f"сім'я{STRESS_MARK}"
        assert f'correction: "{marked}"' in annotated
        assert f'    - "{marked}"' in annotated
        assert f"before я: {marked}." in annotated
        assert f'answer: "ім\'я{STRESS_MARK}"' in annotated

    def test_error_chip_and_its_copies_unchanged(self, annotated: str):
        assert "    error: сімя\n" in annotated
        assert "    - сімя\n" in annotated
        assert ' сімя."\n' in annotated  # the sentence keeps the spotted misspelling
        assert f"сімя{STRESS_MARK}" not in annotated

    def test_yaml_shape_and_idempotence(self, annotated: str, tmp_path: Path):
        import yaml

        original = yaml.safe_load(_EC_ACTIVITIES)
        parsed = yaml.safe_load(annotated)
        assert parsed["inline"][0]["items"][0]["error"] == original["inline"][0]["items"][0]["error"]
        assert parsed["inline"][0]["instruction"] == original["inline"][0]["instruction"]
        assert annotate_file(tmp_path / "activities.yaml") == 0

    def test_error_word_outside_its_item_is_not_protected(self, tmp_path: Path):
        path = tmp_path / "activities.yaml"
        path.write_text(
            "inline:\n- items:\n  - sentence: Це мама.\n    error: мама\n  - sentence: Це мама.\n    answer: мама\n",
            encoding="utf-8",
        )
        annotate_file(path)
        first, second = path.read_text(encoding="utf-8").split("  - sentence:")[1:]
        assert STRESS_MARK not in first
        assert second.count(f"ма{STRESS_MARK}ма") == 2

    def test_other_files_are_not_error_masked(self, tmp_path: Path):
        path = tmp_path / "vocabulary.yaml"
        path.write_text("- error: мама\n", encoding="utf-8")
        annotate_file(path)
        assert f"ма{STRESS_MARK}ма" in path.read_text(encoding="utf-8")
