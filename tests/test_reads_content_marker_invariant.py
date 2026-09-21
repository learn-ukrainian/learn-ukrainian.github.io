"""reads_content marker invariant (#8399).

The content CI class (``pytest_mode=content`` in
``scripts/ci/classify_changes.py``) runs exactly the test modules marked
``reads_content`` plus the shard safety net. Any test module that references a
content root — ``curriculum/l2-uk-en``, ``curriculum/l2-uk-direct``,
``site/src/content/docs``, or ``wiki/`` — must carry the marker, or a
content-only PR could silently lose the test that covers its content.

This scan is deliberately textual and conservative: a module that merely
mentions a content root in a fixture path is still required to carry the
marker. Over-marking costs a little content-lane runtime; under-marking costs
correctness.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.repo_invariant, pytest.mark.reads_content]

_TESTS_ROOT = Path(__file__).resolve().parent

# References that flag a module as content-reading. Keep in sync with the
# content-class roots in scripts/ci/classify_changes.py:
# - l2-uk-en / l2-uk-direct: track slugs, matched bare so both
#   "curriculum/l2-uk-en/..." literals and Path("curriculum") / "l2-uk-en"
#   joins are caught.
# - site/src/content/docs: the learner-docs MDX tree.
# - CURRICULUM_DIR / CURRICULUM_ROOT / CURRICULUM_PATH / PLANS_DIR: path
#   constants scripts define over the curriculum tree.
# - _vocabulary_modules / expected_vocabulary_coverage: helpers in
#   scripts/lexicon/check_manifest_vocabulary_coverage.py that walk the real
#   curriculum tree; importing them means reading content.
# - Path("curriculum") / Path("wiki") literals and / "curriculum" / "wiki"
#   joins: indirect root construction that the slug patterns above miss.
# - wiki/ at a string boundary (not openwiki/, wikipedia URLs, or a/b/wiki/):
#   the compiled-wiki content tree.
CONTENT_REFERENCE_RE = re.compile(
    r"l2-uk-en|l2-uk-direct|site/src/content/docs|"
    r"CURRICULUM_DIR|CURRICULUM_ROOT|CURRICULUM_PATH|PLANS_DIR|"
    r"_vocabulary_modules|expected_vocabulary_coverage|"
    r"Path\([\"']curriculum[\"']\)|Path\([\"']wiki[\"']\)|"
    r"/\s*[\"']curriculum[\"']|/\s*[\"']wiki[\"']|"
    r"(?<![\w/.-])wiki/"
)

MARKER_RE = re.compile(r"reads_content")

_TEST_FILE_RE = re.compile(r"test_[^/]+\.py$")


def test_content_referencing_modules_are_marked() -> None:
    missing: list[str] = []
    for module in sorted(_TESTS_ROOT.rglob("test_*.py")):
        if not _TEST_FILE_RE.search(module.name):
            continue
        text = module.read_text(encoding="utf-8")
        if CONTENT_REFERENCE_RE.search(text) and not MARKER_RE.search(text):
            missing.append(module.relative_to(_TESTS_ROOT.parent).as_posix())
    assert not missing, (
        "test modules reference curriculum/site-content/wiki roots but lack "
        "the reads_content marker (module-level pytestmark); without it the "
        "content CI class cannot see them:\n" + "\n".join(missing)
    )
