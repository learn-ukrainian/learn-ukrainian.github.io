"""
Template parser for structural compliance validation.

Extracts structural requirements from module templates to enable
automated validation of module compliance.

Usage:
    from scripts.audit.template_parser import parse_template, resolve_template
    
    template_path = resolve_template("b2-71", {"focus": "history"})
    structure = parse_template(template_path)
    # Use structure to validate module
"""

import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TemplateStructure:
    """Structural requirements extracted from a template."""
    
    # Template identity
    template_name: str
    level: str  # a1, a2, b1, b2, c1, c2, lit
    
    # Section requirements
    required_sections: list[str] = field(default_factory=list)  # H1/H2 headers
    optional_sections: list[str] = field(default_factory=list)
    section_order: list[str] = field(default_factory=list)  # Expected order
    
    # Forbidden headers (Clean MD standard, Issue #398)
    forbidden_headers: list[str] = field(default_factory=lambda: [
        "Activities", "Вправи", "Активності",
        "Vocabulary", "Словник",
        "External Resources", "Зовнішні ресурси"
    ])
    
    # Content requirements
    pedagogy: Optional[str] = None  # PPP, TTT, CBI, TBL
    min_word_count: Optional[int] = None
    required_callouts: list[str] = field(default_factory=list)  # e.g., [!myth-buster]
    
    # Additional metadata
    description: str = ""


def resolve_template(module_id: str, meta: dict) -> str:
    """
    Resolve which template a module should follow.
    
    Args:
        module_id: Module identifier (e.g., "b2-71", "a1-05")
        meta: Module metadata from meta/{slug}.yaml
    
    Returns:
        Template filename (e.g., "b2-history-module-template.md")
    
    Raises:
        ValueError: If no template mapping matches
    """
    mappings_path = Path("docs/l2-uk-en/template_mappings.yaml")
    
    with mappings_path.open('r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    for rule in config.get('mappings', []):
        # Check pattern-based rules
        if 'pattern' in rule:
            if re.match(rule['pattern'], module_id):
                return rule['template']
        
        # Check meta-field based rules
        if 'meta_field' in rule:
            field_name = rule['meta_field']
            expected_value = rule['value']
            actual_value = meta.get(field_name)
            
            if actual_value == expected_value:
                return rule['template']
    
    # No match found
    raise ValueError(f"No template mapping found for module '{module_id}' with meta: {meta}")


def parse_template(template_path: str) -> TemplateStructure:
    """
    Extract structural requirements from a template markdown file.
    
    Args:
        template_path: Relative path to template (e.g., "b2-history-module-template.md")
    
    Returns:
        TemplateStructure with extracted requirements
    
    Raises:
        FileNotFoundError: If template doesn't exist
    """
    full_path = Path("docs/l2-uk-en/templates") / template_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"Template not found: {full_path}")
    
    with full_path.open('r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract template name and level
    template_name = full_path.stem
    level = _extract_level(template_name)
    
    # Initialize structure
    structure = TemplateStructure(
        template_name=template_name,
        level=level
    )
    
    # Try to extract metadata from HTML comment block
    metadata = _extract_metadata_block(content)
    if metadata:
        structure.required_sections = metadata.get('required_sections', [])
        structure.optional_sections = metadata.get('optional_sections', [])
        structure.pedagogy = metadata.get('pedagogy')
        structure.min_word_count = metadata.get('min_word_count')
        structure.required_callouts = metadata.get('required_callouts', [])
        structure.description = metadata.get('description', '')
    else:
        # Fallback: Infer from template content (Phase 2 implementation)
        structure = _infer_from_content(content, structure)
    
    return structure


def _extract_level(template_name: str) -> str:
    """Extract level from template name."""
    if template_name.startswith('a1-'):
        return 'a1'
    elif template_name.startswith('a2-'):
        return 'a2'
    elif template_name.startswith('b1-'):
        return 'b1'
    elif template_name.startswith('b2-'):
        return 'b2'
    elif template_name.startswith('c1-'):
        return 'c1'
    elif template_name.startswith('c2-'):
        return 'c2'
    elif template_name.startswith('lit-'):
        return 'lit'
    else:
        return 'unknown'


def _extract_metadata_block(content: str) -> Optional[dict]:
    """
    Extract TEMPLATE_METADATA from HTML comment block.
    
    Format:
        <!--
        TEMPLATE_METADATA:
          required_sections:
            - "Вступ"
          pedagogy: "CBI"
        -->
    """
    # Pattern to match HTML comment with TEMPLATE_METADATA
    pattern = r'<!--\s*TEMPLATE_METADATA:\s*\n(.*?)\n\s*-->'
    
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    if not match:
        return None
    
    yaml_content = match.group(1)
    
    try:
        # Parse YAML content
        metadata = yaml.safe_load(yaml_content)
        return metadata
    except yaml.YAMLError:
        return None


def _infer_from_content(content: str, structure: TemplateStructure) -> TemplateStructure:
    """
    Infer structural requirements from template content.
    
    This is a fallback for templates without explicit metadata blocks.
    Looks for common patterns in the template markdown.
    """
    # TODO: Phase 2 implementation
    # For now, just return the structure as-is
    # In Phase 2, we'll parse the template content to extract:
    # - Section headers (## patterns)
    # - Pedagogy hints (PPP/TTT/CBI references)
    # - Word count requirements
    # - Required callout patterns
    
    return structure
