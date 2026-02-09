#!/usr/bin/env python3
"""Utility for extracting delimited content from Gemini/Claude output."""

import re
from pathlib import Path

def extract_delimited(filepath: str | Path, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiters, handling code block wrapping and whitespace.

    Args:
        filepath: Path to the file containing raw LLM output.
        start_tag: The starting delimiter (e.g., '===CONTENT_START===').
        end_tag: The ending delimiter (e.g., '===CONTENT_END===').

    Returns:
        The extracted content as a string, or None if delimiters are not found.
    """
    path = Path(filepath)
    if not path.exists():
        return None

    text = path.read_text()

    # Common pattern: Gemini sometimes wraps delimiters in code blocks
    # ```
    # ===CONTENT_START===
    # ...
    # ===CONTENT_END===
    # ```
    # We strip these markers if they appear immediately before/after delimiters
    cleaned = re.sub(r'```\w*\n', '', text)
    cleaned = re.sub(r'\n```', '', cleaned)

    # Regex to find content between delimiters
    # Use re.DOTALL to match across multiple lines
    # Use non-greedy match .*? to handle multiple delimited blocks if they exist
    pattern = re.compile(
        rf'{re.escape(start_tag)}\s*\n(.*?)\n\s*{re.escape(end_tag)}',
        re.DOTALL
    )

    match = pattern.search(cleaned)
    if match:
        return match.group(1).strip()

    # Fallback: try without cleaning and without strict newline requirements
    pattern_fallback = re.compile(
        rf'{re.escape(start_tag)}(.*?){re.escape(end_tag)}',
        re.DOTALL
    )
    match = pattern_fallback.search(text)
    if match:
        return match.group(1).strip()

    return None

if __name__ == "__main__":
    # Simple test
    test_content = """
Thinking: I should do X.

===TEST_START===
This is the content.
It has multiple lines.
===TEST_END===

More thinking.
"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(test_content)
        temp_path = f.name

    try:
        extracted = extract_delimited(temp_path, "===TEST_START===", "===TEST_END===")
        print(f"Extracted: '{extracted}'")
        assert extracted == "This is the content.\nIt has multiple lines."
        print("Test passed!")
    finally:
        import os
        os.unlink(temp_path)
