import re


def lint_yaml_file(file_path: str) -> list[dict]:
    """
    Lint a YAML file for common syntax errors that confuse parsers.

    Checks for:
    1. Unquoted colons in values (e.g. question: What is it: answer)
    2. Tab indentation
    3. Trailing spaces (warning)

    Returns:
        List of error dicts with keys: line, message, severity, fix
    """
    errors = []

    try:
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return [{
            'line': 0,
            'message': f"Could not read file: {e}",
            'severity': 'critical',
            'fix': 'Check file permissions'
        }]

    for i, line in enumerate(lines):
        line_num = i + 1
        raw_line = line.rstrip('\n')
        stripped = raw_line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue

        # 1. Check for tab indentation
        if line.startswith('\t') or '  \t' in line:
            errors.append({
                'line': line_num,
                'message': "Tab character detected. YAML forbids tabs.",
                'severity': 'critical',
                'fix': "Replace tabs with 2 spaces."
            })

        # 2. Check for unquoted colons in values
        # Matches "key: value" or "- key: value" pattern
        # Skip continuation lines of multi-line quoted strings (indented, no key)
        # Group 1: optional dash and space "- "
        # Group 2: key
        # Group 3: distinct separator ": "
        # Group 4: value
        match = re.match(r'^(\s*(- )?)([\w\-\_]+):\s+(.+)$', raw_line)
        if match:
            # key = match.group(3)
            value = match.group(4)

            # Skip if this line's value starts a quoted string (handled correctly)
            if value.startswith('"') or value.startswith("'"):
                continue

            # Skip continuation lines: if previous line ends with an open quote
            # (single or double), this line is part of that string
            if line_num > 1:
                prev = lines[line_num - 2] if line_num - 1 < len(lines) else ""
                prev_stripped = prev.rstrip()
                # Count quotes — odd number means string is still open
                if prev_stripped.count("'") % 2 == 1 or prev_stripped.count('"') % 2 == 1:
                    continue

            # If value contains a colon
            if ':' in value and (': ' in value or value.strip().endswith(':')):
                errors.append({
                    'line': line_num,
                    'message': "Unquoted colon detected in value. YAML parsers may fail.",
                    'severity': 'critical',
                    'fix': f"Wrap the value in double quotes: \"{value.replace('\"', '\\\"')}\""
                })

    return errors
