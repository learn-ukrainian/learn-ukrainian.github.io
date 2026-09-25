"""Shared utilities for MDX generation.

Provides JSX escaping, HTML-to-JSX conversion, JSON serialization for JSX
template literals, and shared path constants.
"""

from __future__ import annotations

import json
from pathlib import Path

from .unit_map import EditLog

# Shared path constants
SCRIPT_DIR = Path(__file__).resolve().parent.parent  # scripts/
PROJECT_ROOT = SCRIPT_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
STARLIGHT_DOCS_DIR = PROJECT_ROOT / "site" / "src" / "content" / "docs"


def dump_json_for_jsx(data, *, compact: bool = False):
    """Dump JSON string escaped for use inside a JSX template literal.

    The result is embedded as ``JSON.parse(`<result>`)``. A JS template literal
    *consumes* backslash escapes, so the JSON's own ``\\"`` / ``\\\\`` / ``\\n``
    sequences must be backslash-doubled (together with `` ` `` and ``${``) — and
    backslashes MUST be doubled FIRST — or ``JSON.parse`` receives corrupted
    input at render time. Concretely, any value containing a literal ``"`` is
    JSON-encoded as ``\\"``; without doubling, the template literal collapses it
    back to ``"`` and the page fails to render. This is the canonical, single
    escaper for every JSON-in-template-literal embed — see issue #3137.

    Pass ``compact=True`` for whitespace-free separators (smaller MDX payloads,
    e.g. VocabCard/FlashcardDeck word lists).
    """
    separators = (',', ':') if compact else None
    # allow_nan=False: NaN/Infinity are NOT valid JSON and would throw in JSON.parse
    # at render time — fail fast at assembly rather than emit unparseable output.
    s = json.dumps(data, ensure_ascii=False, separators=separators, allow_nan=False)
    # Escape backslashes FIRST to avoid double-escaping the chars below.
    s = s.replace('\\', '\\\\')
    # Escape backticks for template literals
    s = s.replace('`', '\\`')
    # Escape $ to avoid template interpolation
    s = s.replace('${', '\\${')
    return s


def escape_jsx(text: str) -> str:
    """Escape text for use in JSX strings (both template literals and double quotes).

    Uses HTML entities for special chars to avoid JSX parsing errors.
    See issue #396 for details.
    """
    if not text:
        return ''
    # Convert to string if not already (handles int/float from YAML)
    if not isinstance(text, str):
        text = str(text)
    # Escape backslashes first
    text = text.replace('\\', '\\\\')
    text = text.replace('`', '\\`')
    text = text.replace('"', '&quot;')  # HTML entity
    text = text.replace('<', '&lt;')    # Escape <
    text = text.replace('>', '&gt;')    # Escape >
    text = text.replace('${', '\\${')
    return text


def fix_html_for_jsx(text: str) -> str:
    """Convert HTML tags to JSX-compatible self-closing format."""
    log = EditLog(text, record=False)
    edit_fix_html_for_jsx(log)
    return log.text


def edit_fix_html_for_jsx(log: EditLog) -> None:
    """`fix_html_for_jsx` on an `EditLog`: every tag rewrite is reported as an edit."""
    # Convert <br> to <br />
    log.sub(r'<br\s*/?>', '<br />')
    # Convert <hr> to <hr />
    log.sub(r'<hr\s*/?>', '<hr />')
    # Convert <img ...> to <img ... />
    log.sub(r'<img([^>]*?)(?<!/)>', r'<img\1 />')
