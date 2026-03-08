"""Shared utilities for MDX generation.

Provides JSX escaping, HTML-to-JSX conversion, JSON serialization for JSX
template literals, and shared path constants.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Shared path constants
SCRIPT_DIR = Path(__file__).resolve().parent.parent  # scripts/
PROJECT_ROOT = SCRIPT_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
DOCUSAURUS_DIR = PROJECT_ROOT / "starlight" / "src" / "content" / "docs"


def dump_json_for_jsx(data):
    """Dump JSON string escaped for use inside a JSX template literal."""
    s = json.dumps(data, ensure_ascii=False)
    # Escape backslashes first to avoid double escaping other chars
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
    # Convert <br> to <br />
    text = re.sub(r'<br\s*/?>', '<br />', text)
    # Convert <hr> to <hr />
    text = re.sub(r'<hr\s*/?>', '<hr />', text)
    # Convert <img ...> to <img ... />
    text = re.sub(r'<img([^>]*?)(?<!/)>', r'<img\1 />', text)
    return text
