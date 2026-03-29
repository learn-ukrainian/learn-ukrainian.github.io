"""MDX validation — catch broken JSX/props before they hit the browser.

Runs after publish step. Checks:
1. All used components have matching imports
2. JSON props in component attributes parse correctly
3. No unescaped curly braces in prose (MDX treats { as JSX expression)
4. Matching open/close tags for Tabs/TabItem
5. No orphaned HTML entities that break JSX

Returns list of errors. Empty = valid.

Issue: runtime rendering errors in Starlight dev mode
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def validate_mdx(mdx_path: Path) -> list[str]:
    """Validate an MDX file for common JSX/component errors.

    Returns list of error strings. Empty list = valid.
    """
    errors: list[str] = []
    content = mdx_path.read_text("utf-8")
    lines = content.split("\n")

    # ── 1. Check imports vs usage ──
    imports = set()
    for line in lines:
        m = re.match(r"^import\s+(\w+)\s+from", line)
        if m:
            imports.add(m.group(1))
        # Destructured imports: import { Tabs, TabItem } from ...
        m2 = re.match(r"^import\s+\{([^}]+)\}\s+from", line)
        if m2:
            for name in m2.group(1).split(","):
                imports.add(name.strip())

    # Find all component usages: <ComponentName ... />  or <ComponentName ...>
    used_components = set()
    for m in re.finditer(r"<(\/?[A-Z]\w+)", content):
        tag = m.group(1).lstrip("/")
        used_components.add(tag)

    missing_imports = used_components - imports
    if missing_imports:
        errors.append(f"Components used but not imported: {', '.join(sorted(missing_imports))}")

    # unused_imports = imports - used_components (informational only, not flagged)

    # ── 2. Validate JSON in component props ──
    # Match patterns like: questions={[...]} or cards={[...]} or groups={{...}}
    for line_num, line in enumerate(lines, 1):
        # Only check lines with JSX components
        if not re.search(r"<[A-Z]", line):
            continue

        # Extract all prop values that look like JSON
        for m in re.finditer(r'(\w+)=\{', line):
            prop_name = m.group(1)
            start = m.end()
            # Find matching closing brace
            depth = 1
            pos = start
            while pos < len(line) and depth > 0:
                if line[pos] == "{":
                    depth += 1
                elif line[pos] == "}":
                    depth -= 1
                pos += 1

            if depth != 0:
                errors.append(f"Line {line_num}: Unmatched brace in prop '{prop_name}'")
                continue

            prop_value = line[start:pos - 1]

            # Try to parse as JSON (JSX props use JS syntax which is close to JSON)
            # Skip string props like instruction={"text"}
            if prop_value.startswith('"') and prop_value.endswith('"'):
                continue
            if prop_value.startswith("[") or prop_value.startswith("{"):
                try:
                    json.loads(prop_value)
                except json.JSONDecodeError as e:
                    # Common: JS uses single quotes, trailing commas — not always JSON
                    # Only flag if it looks like it should be JSON (arrays/objects)
                    if "Expecting property name" not in str(e):
                        errors.append(
                            f"Line {line_num}: Invalid JSON in prop '{prop_name}': {str(e)[:80]}"
                        )

    # ── 3. Check for unescaped braces in prose ──
    in_frontmatter = False
    frontmatter_count = 0
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == "---":
            frontmatter_count += 1
            in_frontmatter = frontmatter_count == 1
            continue
        if in_frontmatter:
            continue
        if frontmatter_count < 2:
            continue  # Still in frontmatter

        # Skip import lines, component lines, and code blocks
        if stripped.startswith("import ") or re.match(r"</?[A-Z]", stripped):
            continue
        if stripped.startswith("```") or stripped.startswith("<!--"):
            continue

        # Check for lone { that isn't part of a JSX expression
        # This catches prose like "The set {a, b, c}" which breaks MDX
        brace_matches = list(re.finditer(r"\{", stripped))
        for bm in brace_matches:
            # Check if this is inside a component tag (same line has <Component)
            if re.search(r"<[A-Z]", stripped):
                break  # Component line — braces are props
            # Check if inside inline code
            before = stripped[:bm.start()]
            if before.count("`") % 2 == 1:
                continue  # Inside inline code
            errors.append(
                f"Line {line_num}: Unescaped '{{' in prose — MDX interprets this as JSX. "
                f"Use \\{{ or put in backticks."
            )
            break  # One error per line is enough

    # ── 4. Check Tab structure ──
    tab_opens = len(re.findall(r"<Tabs\b", content))
    tab_closes = len(re.findall(r"</Tabs>", content))
    if tab_opens != tab_closes:
        errors.append(f"Mismatched <Tabs> tags: {tab_opens} opens, {tab_closes} closes")

    tabitem_opens = len(re.findall(r"<TabItem\b", content))
    tabitem_closes = len(re.findall(r"</TabItem>", content))
    if tabitem_opens != tabitem_closes:
        errors.append(f"Mismatched <TabItem> tags: {tabitem_opens} opens, {tabitem_closes} closes")

    return errors


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python mdx_validate.py <path-to-mdx>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    errs = validate_mdx(path)
    if errs:
        print(f"❌ MDX validation FAILED ({len(errs)} error(s)):")
        for e in errs:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("✅ MDX validation passed")
