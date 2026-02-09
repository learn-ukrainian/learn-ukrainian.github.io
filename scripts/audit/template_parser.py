"""
Template parsing and resolution logic.

Handles:
1. Resolving which template applies to a given module ID/metadata.
2. Parsing the markdown template file to extract structural requirements.
"""

import os
import re
import yaml
from functools import lru_cache
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class TemplateStructure:
    """Holds the structural requirements parsed from a template file."""
    template_name: str
    level: str = "unknown"
    pedagogy: str = "Standard"
    required_sections: List[str] = field(default_factory=list)
    optional_sections: List[str] = field(default_factory=list)
    forbidden_headers: List[str] = field(default_factory=lambda: [
        "Activities", "Вправи", "Активності",
        "Vocabulary", "Словник",
        "External Resources", "Зовнішні ресурси"
    ])
    section_order: List[str] = field(default_factory=list)
    required_callouts: List[str] = field(default_factory=list)
    min_word_count: Optional[int] = None
    description: str = ""


@lru_cache(maxsize=1)
def _load_template_mappings(mapping_file_path: str) -> Dict:
    """Cache the template mappings file content."""
    with open(mapping_file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def resolve_template(module_id: str, meta: Dict) -> str:
    """
    Resolve which template file to use for a given module.
    
    Args:
        module_id: The module ID (e.g., 'a1-01', 'b2-110')
        meta: The module's metadata dictionary
        
    Returns:
        Path to the template file relative to project root
    """
    # Find project root
    current_file = Path(__file__).resolve()
    # scripts/audit/template_parser.py -> scripts/audit -> scripts -> root
    project_root = current_file.parent.parent.parent
    
    mapping_file = project_root / "docs" / "l2-uk-en" / "template_mappings.yaml"
    
    # Extract level from module_id - handle track levels like b2-hist, c1-bio
    # Pattern: level-slug or track-level-slug
    parts = module_id.lower().split('-')
    if len(parts) >= 2 and parts[0] in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        # Check if second part is a known track suffix
        if parts[1] in ['hist', 'bio', 'pro']:
            module_level = f"{parts[0]}-{parts[1]}"
        else:
            module_level = parts[0]
    elif parts[0] == 'lit':
        module_level = 'lit'
    else:
        module_level = parts[0]

    if not mapping_file.exists():
        # Fallback to hardcoded logic if mapping file is missing
        return f"docs/l2-uk-en/templates/{module_level}-module-template.md"

    config = _load_template_mappings(str(mapping_file))
    mappings = config.get('mappings', [])
    
    for rule in mappings:
        # Check if level matches (if specified in rule)
        rule_level = rule.get('level', '').lower()
        if rule_level and rule_level != module_level:
            continue

        # Check by metadata field
        if 'meta_field' in rule:
            field_name = rule['meta_field']
            expected_value = rule['value']
            
            if meta and str(meta.get(field_name, '')).lower() == str(expected_value).lower():
                return f"docs/l2-uk-en/templates/{rule['template']}"
                
        # Check by ID pattern
        elif 'pattern' in rule:
            pattern = rule['pattern']
            if re.search(pattern, module_id, re.IGNORECASE):
                return f"docs/l2-uk-en/templates/{rule['template']}"
                
    # Fallback to level default
    return f"docs/l2-uk-en/templates/{module_level}-module-template.md"


@lru_cache(maxsize=32)
def parse_template(template_path: str) -> Optional[TemplateStructure]:
    """
    Parse a markdown template file to extract structural rules.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        TemplateStructure object or None if parsing fails
    """
    # Find project root to resolve relative path if needed
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    full_path = project_root / template_path
    
    if not full_path.exists():
        # Try absolute path just in case
        full_path = Path(template_path)
        if not full_path.exists():
            return None
            
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract metadata block
    # Looks for <!-- TEMPLATE_METADATA: ... -->
    match = re.search(r'<!--\s*TEMPLATE_METADATA:\s*\n(.*?)\n-->', content, re.DOTALL)
    
    template_name = Path(template_path).name
    level = template_name.split('-')[0] if '-' in template_name else "unknown"
    
    if not match:
        return TemplateStructure(template_name=template_name, level=level)
        
    yaml_block = match.group(1)
    try:
        data = yaml.safe_load(yaml_block)
        
        return TemplateStructure(
            template_name=template_name,
            level=level,
            pedagogy=data.get('pedagogy', 'Standard'),
            required_sections=data.get('required_sections', []),
            optional_sections=data.get('optional_sections', []),
            forbidden_headers=data.get('forbidden_headers', [
                "Activities", "Вправи", "Активності",
                "Vocabulary", "Словник",
                "External Resources", "Зовнішні ресурси"
            ]),
            section_order=data.get('section_order', []),
            required_callouts=data.get('required_callouts', []),
            min_word_count=data.get('min_word_count'),
            description=data.get('description', '')
        )
    except yaml.YAMLError:
        return TemplateStructure(template_name=template_name, level=level)
