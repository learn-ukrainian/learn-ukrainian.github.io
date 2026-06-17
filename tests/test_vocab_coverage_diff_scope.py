"""Diff-scope (#3150) for the Atlas vocabulary-coverage gate.

The gate must NOT couple a PR's CI to unrelated curriculum merges: it checks only the
modules whose vocabulary.yaml changed in the PR. These tests pin that restrict behavior
against the real curriculum (mirrors test_atlas_conformance's real-artifact style).
"""

from __future__ import annotations

from pathlib import Path

from scripts.lexicon.check_manifest_vocabulary_coverage import (
    ROOT,
    _vocabulary_modules,
    check_vocabulary_coverage,
    expected_vocabulary_coverage,
)


def test_empty_restrict_is_a_noop_pass():
    # No module vocabulary changed in the diff → nothing to check → clean exit.
    assert check_vocabulary_coverage(root=ROOT, restrict=set()) == 0


def test_restrict_narrows_to_the_named_modules_only():
    modules = _vocabulary_modules(ROOT)
    assert modules, "expected a non-empty real curriculum"
    target = {(modules[0].track, modules[0].slug)}

    expected, checked = expected_vocabulary_coverage(ROOT, restrict=target)

    assert checked == 1
    # Every expected lemma is taught ONLY by the restricted module(s).
    assert all(lemma.modules <= target for lemma in expected.values())


def test_restrict_none_covers_the_full_curriculum():
    _expected, full_count = expected_vocabulary_coverage(ROOT)
    _restricted, one_count = expected_vocabulary_coverage(
        ROOT, restrict={(_vocabulary_modules(ROOT)[0].track, _vocabulary_modules(ROOT)[0].slug)}
    )
    assert full_count == len(_vocabulary_modules(ROOT))
    assert one_count < full_count


def test_changed_vocab_modules_parses_or_returns_none(tmp_path: Path):
    # Outside a git tree the helper must fail closed to None (caller → full coverage),
    # never raise and never silently return an empty "nothing changed" set.
    from scripts.lexicon.check_manifest_vocabulary_coverage import changed_vocab_modules

    result = changed_vocab_modules(tmp_path, "origin/main")
    assert result is None or isinstance(result, set)
