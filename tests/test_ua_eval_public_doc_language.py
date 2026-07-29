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

    assert len(findings) == 1
    assert findings[0].line == 3
    assert findings[0].column == 7
    assert "Smoke спочатку" in findings[0].excerpt


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

    assert [finding.line for finding in findings] == [1, 2]


def test_governed_set_is_explicit_and_current() -> None:
    assert (
        Path("docs/projects/ua-eval-harness/DATA_CARD.en.md"),
        Path("docs/projects/ua-eval-harness/README.md"),
        Path("docs/projects/ua-eval-harness/REPRODUCING.md"),
        Path("docs/projects/ua-eval-harness/THIRD_PARTY_NOTICES.md"),
        Path("docs/projects/ua-eval-harness/contamination-policy.md"),
    ) == PUBLIC_ENGLISH_DOCS


def test_repository_public_english_docs_have_no_cyrillic_prose() -> None:
    paths = governed_paths()

    assert all(path.is_file() for path in paths)
    findings = [finding for path in paths for finding in scan_text(path.read_text(encoding="utf-8"), path)]
    assert findings == []
