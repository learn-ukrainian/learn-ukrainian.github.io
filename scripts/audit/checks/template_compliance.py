"""
Template compliance validation checks.

Validates that modules follow the structural requirements of their assigned templates.
Implements 3-level validation:
- Level 1 (CRITICAL): Required sections, forbidden headers
- Level 2 (WARNING): Section order
- Level 3 (INFO): Content patterns, callouts

Related Issues:
- #398: Clean MD Standard enforcement
- #389: Final testing support
"""

import re
from typing import Optional
from ..template_parser import TemplateStructure


def check_template_compliance(
    content: str,
    meta: dict,
    template: TemplateStructure
) -> list[dict]:
    """
    Validate module compliance with its designated template.
    
    Args:
        content: Full module markdown content
        meta: Module metadata from meta/{slug}.yaml
        template: Template structure requirements
    
    Returns:
        List of violation dictionaries with:
        - type: Violation type code
        - severity: CRITICAL, WARNING, or INFO
        - line: Line number where violation occurs
        - issue: Description of the problem
        - fix: How to resolve it
    """
    violations = []
    
    # Level 1: Required sections and forbidden headers (CRITICAL)
    violations.extend(_check_required_sections(content, meta, template))
    violations.extend(_check_forbidden_headers(content, template))
    
    # Level 2: Section order (WARNING)
    violations.extend(_check_section_order(content, template))
    
    # Level 3: Content patterns (INFO)
    violations.extend(_check_required_callouts(content, template))
    
    return violations


def _check_required_sections(content: str, meta: dict, template: TemplateStructure) -> list[dict]:
    """
    Check that all required sections from template are present, not empty, and unique.
    
    Severity: CRITICAL (causes FAIL)
    """
    violations = []
    
    if not template.required_sections:
        return violations
    
    # Extract sections with content ranges
    sections_data = _extract_sections_with_content(content)
    present_headers = [s['header'].lower() for s in sections_data]
    
    vital_status = meta.get('vital_status', 'deceased').lower()
    
    for required in template.required_sections:
        alt_names = [name.strip() for name in required.split('|')]
        found_alts = []
        
        # Determine preferred and forbidden names based on vital status for biographies
        preferred_name = None
        forbidden_name = None
        
        if len(alt_names) > 1 and template.level == 'c1' and 'biography' in template.template_name:
            if 'living' in vital_status:
                if 'Сучасний етап' in alt_names: preferred_name = 'Сучасний етап'
                if 'Останні роки' in alt_names: forbidden_name = 'Останні роки'
                if 'Вплив' in alt_names: preferred_name = 'Вплив'
                if 'Спадщина' in alt_names: forbidden_name = 'Спадщина'
            else:
                if 'Останні роки' in alt_names: preferred_name = 'Останні роки'
                if 'Сучасний етап' in alt_names: forbidden_name = 'Сучасний етап'
                if 'Спадщина' in alt_names: preferred_name = 'Спадщина'
                if 'Вплив' in alt_names: forbidden_name = 'Вплив'

        for alt in alt_names:
            # Stricter matching: must be the whole header or a clear synonym
            # We match if the alias is the WHOLE header or if it's a known common abbreviation
            for s in sections_data:
                header_lower = s['header'].lower()
                alt_lower = alt.lower()
                
                # Direct match or alias is the whole header
                if alt_lower == header_lower:
                    found_alts.append(s)
                # Flexible match (e.g., "Grammar" matches "## Grammar Theory")
                # but NOT "Need More Practice?" matching "Practice"
                elif alt_lower in header_lower and "practice?" not in header_lower:
                    # Check if this alias is a substring of another requirement
                    # If so, we only allow an EXACT match for this alias to avoid collisions
                    is_substring_of_other_req = False
                    for other_req in template.required_sections:
                        if other_req == required:
                            continue
                        if alt_lower in other_req.lower() and len(other_req) > len(alt_lower):
                            is_substring_of_other_req = True
                            break
                    
                    if is_substring_of_other_req and alt_lower != header_lower:
                        continue
                        
                    found_alts.append(s)
        
        # Check if forbidden name is used
        if forbidden_name:
            for s in sections_data:
                if forbidden_name.lower() == s['header'].lower():
                    violations.append({
                        'type': 'FORBIDDEN_HEADER_TONE',
                        'severity': 'CRITICAL',
                        'line': s['line'],
                        'issue': f"Header '## {s['header']}' is inappropriate for a {vital_status} person. Use '## {preferred_name}' instead.",
                        'fix': f"Rename '## {s['header']}' to '## {preferred_name}' to maintain correct biographical tone."
                    })

        if not found_alts:
            display_name = preferred_name if preferred_name else alt_names[0]
            violations.append({
                'type': 'MISSING_REQUIRED_SECTION',
                'severity': 'CRITICAL',
                'line': 0,
                'issue': f"Missing required section '{display_name}' per template '{template.template_name}'",
                'fix': f"Add '## {display_name}' section as specified in docs/l2-uk-en/templates/{template.template_name}.md"
            })
        else:
            # Check for duplicates (Issue mentioned by user)
            # Skip for metalanguage templates - they intentionally have multiple related sections
            # (e.g., Parts of Speech, Seven Cases, Basic Sentence Terms are all valid in same module)
            is_metalanguage = 'metalanguage' in template.template_name.lower()
            if len(found_alts) > 1 and not is_metalanguage:
                # Filter to unique header texts to avoid flagging same header twice if multi-line or something
                unique_headers = list(set(s['header'] for s in found_alts))
                if len(unique_headers) > 1:
                    violations.append({
                        'type': 'DUPLICATE_SYNONYMOUS_HEADERS',
                        'severity': 'CRITICAL',
                        'line': found_alts[0]['line'],
                        'issue': f"Multiple aliases for '{required}' found: {', '.join(unique_headers)}",
                        'fix': f"Keep only one version of the header (preferably the primary one or the one with more content)."
                    })
            
            # Check for empty sections (Issue mentioned by user)
            for i, section in enumerate(found_alts):
                # Clean content: remove whitespace, markdown comments, and horizontal rules
                clean_body = section['body'].strip()
                clean_body = re.sub(r'<!--.*?-->', '', clean_body, flags=re.DOTALL)
                clean_body = re.sub(r'^[\s\-_*]+$', '', clean_body, flags=re.MULTILINE)
                
                if not clean_body.strip():
                    # If the section is empty, but the NEXT section is a sub-section 
                    # (higher level number, e.g., H3 under H2), then it's a parent container.
                    
                    # Find the index of this section in the global sections_data
                    global_idx = -1
                    for idx, s in enumerate(sections_data):
                        if s['line'] == section['line'] and s['header'] == section['header']:
                            global_idx = idx
                            break
                    
                    is_parent = False
                    if global_idx != -1 and global_idx + 1 < len(sections_data):
                        next_section = sections_data[global_idx + 1]
                        if next_section['level'] > section['level']:
                            is_parent = True
                    
                    if not is_parent:
                        violations.append({
                            'type': 'EMPTY_REQUIRED_SECTION',
                            'severity': 'CRITICAL',
                            'line': section['line'],
                            'issue': f"Required section '## {section['header']}' is empty",
                            'fix': f"Populate the section with meaningful content or generate it if it's a mandatory placeholder."
                        })
    
    return violations


def _extract_sections_with_content(content: str) -> list[dict]:
    """
    Extract section headers and their associated content bodies.
    """
    sections = []
    lines = content.split('\n')
    
    # 1. First, find all header positions
    header_indices = []
    in_frontmatter = False
    frontmatter_count = 0
    
    for i, line in enumerate(lines):
        if line.strip() == '---':
            if i == 0 or (i > 0 and not any(lines[j].strip() for j in range(i))):
                in_frontmatter = True
                frontmatter_count += 1
                continue
            elif in_frontmatter:
                in_frontmatter = False
                frontmatter_count += 1
                continue
        
        if in_frontmatter:
            continue
            
        match = re.match(r'^(#+)\s+(.+)$', line.strip()) # Detect H1, H2, H3, H4...
        if match:
            level = len(match.group(1))
            header_text = match.group(2).strip()
            header_indices.append((i, header_text, level))
            
    # 2. Extract content between headers
    for i in range(len(header_indices)):
        start_idx, header_text, level = header_indices[i]
        end_idx = header_indices[i+1][0] if i+1 < len(header_indices) else len(lines)
        
        body = '\n'.join(lines[start_idx+1 : end_idx])
        
        sections.append({
            'header': header_text,
            'level': level,
            'line': start_idx + 1,
            'body': body
        })
        
    return sections


def _check_forbidden_headers(content: str, template: TemplateStructure) -> list[dict]:
    """
    Check for forbidden headers per Clean MD standard (Issue #398).
    
    Severity: CRITICAL (causes FAIL)
    
    Note: This duplicates check_forbidden_headers() from markdown_format.py
    but is included here for template-specific context and future extensibility.
    """
    violations = []
    
    lines = content.split('\n')
    in_frontmatter = False
    frontmatter_count = 0
    
    for line_num, line in enumerate(lines, 1):
        # Skip frontmatter
        if line.strip() == '---':
            frontmatter_count += 1
            if frontmatter_count == 1:
                in_frontmatter = True
            elif frontmatter_count == 2:
                in_frontmatter = False
            continue
        
        if in_frontmatter:
            continue
        
        # Check for forbidden headers (H2 level)
        for forbidden in template.forbidden_headers:
            pattern = rf'^##\s+{re.escape(forbidden)}\s*$'
            if re.match(pattern, line.strip(), re.IGNORECASE):
                violations.append({
                    'type': 'FORBIDDEN_HEADER',
                    'severity': 'CRITICAL',
                    'line': line_num,
                    'issue': f"Forbidden header '## {forbidden}' violates Clean MD standard (Issue #398)",
                    'fix': f"Remove '## {forbidden}' header. Template '{template.template_name}' specifies this section is auto-injected from YAML sidecars."
                })
                break
    
    return violations


def _check_section_order(content: str, template: TemplateStructure) -> list[dict]:
    """
    Check that sections appear in the template-specified order.
    
    Severity: WARNING (doesn't cause FAIL, but indicates poor structure)
    """
    violations = []
    
    if not template.section_order:
        return violations  # No order requirements defined yet
    
    # Extract sections with their line numbers
    sections_with_lines = _extract_sections_with_lines(content)
    
    # Map template order to a sequence
    expected_order = {section: idx for idx, section in enumerate(template.section_order)}
    
    # Check if sections appear in expected order
    last_position = -1
    for section, line_num in sections_with_lines:
        # Find this section in expected order
        position = expected_order.get(section, -1)
        
        if position != -1 and position < last_position:
            violations.append({
                'type': 'SECTION_OUT_OF_ORDER',
                'severity': 'WARNING',
                'line': line_num,
                'issue': f"Section '{section}' appears out of order per template '{template.template_name}'",
                'fix': f"Move '## {section}' to appear after expected preceding sections. See template for correct order."
            })
        
        if position != -1:
            last_position = position
    
    return violations


def _check_required_callouts(content: str, template: TemplateStructure) -> list[dict]:
    """
    Check for required callout boxes (e.g., [!myth-buster] in history modules).
    
    Severity: INFO (doesn't cause FAIL, but indicates missing enrichment)
    """
    violations = []
    
    if not template.required_callouts:
        return violations  # No callout requirements
    
    for callout_type in template.required_callouts:
        pattern = rf'\[!{re.escape(callout_type)}\]'
        
        if not re.search(pattern, content, re.IGNORECASE):
            violations.append({
                'type': 'MISSING_REQUIRED_CALLOUT',
                'severity': 'INFO',
                'line': 0,
                'issue': f"Missing required callout '[!{callout_type}]' per template '{template.template_name}'",
                'fix': f"Add a `> [!{callout_type}]` box as specified in the template. This enhances module quality."
            })
    
    return violations


def _extract_section_headers(content: str) -> list[str]:
    """
    Extract all H1/H2 section headers from content.
    
    Returns list of header text (without # symbols)
    """
    headers = []
    lines = content.split('\n')
    in_frontmatter = False
    frontmatter_count = 0
    
    for i, line in enumerate(lines):
        # Skip only the first frontmatter block if it starts at the top
        if line.strip() == '---':
            if i == 0 or (i > 0 and not any(lines[j].strip() for j in range(i))):
                # Start of frontmatter at the top
                in_frontmatter = True
                frontmatter_count += 1
                continue
            elif in_frontmatter:
                # End of frontmatter
                in_frontmatter = False
                frontmatter_count += 1
                continue
        
        if in_frontmatter:
            continue
        
        # Match H1 or H2
        match = re.match(r'^#{1,2}\s+(.+)$', line.strip())
        if match:
            headers.append(match.group(1).strip())
    
    return headers


def _extract_sections_with_lines(content: str) -> list[tuple[str, int]]:
    """
    Extract all H1/H2 section headers with their line numbers.
    
    Returns list of (header_text, line_num) tuples
    """
    sections = []
    lines = content.split('\n')
    in_frontmatter = False
    frontmatter_count = 0
    
    for line_num, line in enumerate(lines, 1):
        # Skip only the first frontmatter block if it starts at the top
        # (line_num is 1-indexed, so 0-indexed index is line_num-1)
        if line.strip() == '---':
            i = line_num - 1
            if i == 0 or (i > 0 and not any(lines[j].strip() for j in range(i))):
                # Start of frontmatter at the top
                in_frontmatter = True
                frontmatter_count += 1
                continue
            elif in_frontmatter:
                # End of frontmatter
                in_frontmatter = False
                frontmatter_count += 1
                continue
        
        if in_frontmatter:
            continue
        
        # Match H1 or H2
        match = re.match(r'^#{1,2}\s+(.+)$', line.strip())
        if match:
            sections.append((match.group(1).strip(), line_num))
    
    return sections
