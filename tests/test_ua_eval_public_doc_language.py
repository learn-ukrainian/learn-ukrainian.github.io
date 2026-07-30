"""Tests for the public English UA-eval document language gate."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from audit.check_ua_eval_public_doc_language import (
    PUBLIC_ENGLISH_DOCS,
    governed_paths,
    scan_text,
)


def test_rejects_hybrid_running_prose() -> None:
    text = "# Reproduction\n\nSmoke спочатку перевіряє freeze manifest and all frozen hashes.\n"

    findings = scan_text(text)

    assert len(findings) == 2
    assert [finding.line for finding in findings] == [3, 3]
    assert [finding.column for finding in findings] == [7, 16]
    assert all("Smoke спочатку" in finding.excerpt for finding in findings)


def test_allows_ukrainian_only_in_explicit_code() -> None:
    text = """# Examples

The surface form `тьоті` is retained as evidence.

```text
Це точний український приклад.
```

The prose returns to English.
"""

    assert scan_text(text) == []


def test_allows_multiline_and_variable_width_code_spans() -> None:
    text = """English ``first `український`
second`` prose.

````text
```
Український приклад
```
````
"""

    assert scan_text(text) == []


def test_rejects_unclosed_fence_instead_of_hiding_rest_of_document() -> None:
    text = """# Examples

```text
Example output.

Український prose that must not be hidden.
"""

    findings = scan_text(text)

    assert len(findings) == 1
    assert findings[0].line == 3
    assert "Unclosed fenced code block" in findings[0].message


def test_stray_backticks_cannot_mask_across_markdown_blocks() -> None:
    text = """English paragraph with a stray ` backtick.

Український prose in another paragraph with ` another backtick.
"""

    findings = scan_text(text)

    assert len(findings) == 1
    assert findings[0].line == 3
    assert "Український prose" in findings[0].excerpt


def test_rejects_visible_markdown_formatting_and_link_labels() -> None:
    text = "This **український text** is visible.\nThis [українська назва](https://example.test) is also visible.\n"

    findings = scan_text(text)

    assert [finding.line for finding in findings] == [1, 2, 2]


def test_rejects_internal_project_terms_in_running_prose() -> None:
    text = "See issue #1234 and send the examples to Hramatka canaries.\n"

    findings = scan_text(text)

    assert len(findings) == 3
    assert [finding.column for finding in findings] == [
        text.index("issue") + 1,
        text.index("Hramatka") + 1,
        text.index("canaries") + 1,
    ]
    assert all("Internal project terminology" in finding.message for finding in findings)


def test_rejects_every_repeated_internal_term_in_one_fragment() -> None:
    text = "Atlas notes mention Atlas again.\n"

    findings = scan_text(text)

    assert len(findings) == 2
    assert [finding.column for finding in findings] == [
        text.index("Atlas") + 1,
        text.rindex("Atlas") + 1,
    ]


def test_reports_multiline_internal_term_on_its_source_line() -> None:
    text = "Public release prose continues here.\nHramatka is an internal product name.\n"

    findings = scan_text(text)

    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].column == 1


def test_allows_internal_looking_tokens_only_as_code_evidence() -> None:
    text = "A migration test may contain the literal path `issues/1234`.\n"

    assert scan_text(text) == []


def test_governed_set_is_explicit_and_current() -> None:
    assert (
        Path("docs/projects/ua-eval-harness/DATA_CARD.en.md"),
        Path("docs/projects/ua-eval-harness/README.md"),
        Path("docs/projects/ua-eval-harness/RELEASE_NOTES.md"),
        Path("docs/projects/ua-eval-harness/REPRODUCING.md"),
        Path("docs/projects/ua-eval-harness/THIRD_PARTY_NOTICES.md"),
        Path("docs/projects/ua-eval-harness/contamination-policy.md"),
    ) == PUBLIC_ENGLISH_DOCS


def test_repository_public_english_docs_have_no_cyrillic_prose() -> None:
    paths = governed_paths()

    assert all(path.is_file() for path in paths)
    findings = [finding for path in paths for finding in scan_text(path.read_text(encoding="utf-8"), path)]
    assert findings == []
