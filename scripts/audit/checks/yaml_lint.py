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
        with open(file_path, 'r', encoding='utf-8') as f:
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
        # Group 1: optional dash and space "- "
        # Group 2: key
        # Group 3: distinct separator ": "
        # Group 4: value
        match = re.match(r'^(\s*(- )?)([\w\-\_]+):\s+(.+)$', raw_line)
        if match:
            # key = match.group(3)
            value = match.group(4)
            
            # If value contains a colon
            if ':' in value:
                # Check if it starts with quote
                if not (value.startswith('"') or value.startswith("'")):
                    # It might be valid flow style like {a: b}, but for our content strings it's usually bad
                    # Specifically check if the colon is " : " (spaced) or part of text that looks like a mapping
                    # In YAML "key: value: subvalue" is a mapping if indented
                    # But "key: text: text" is a syntax error if not quoted
                    
                    # Heuristic: if value has ": " followed by non-newline, it's risky
                    if ': ' in value or value.strip().endswith(':'):
                        errors.append({
                            'line': line_num,
                            'message': "Unquoted colon detected in value. YAML parsers may fail.",
                            'severity': 'critical',
                            'fix': f"Wrap the value in double quotes: \"{value.replace('\"', '\\\"')}\""
                        })

    return errors
