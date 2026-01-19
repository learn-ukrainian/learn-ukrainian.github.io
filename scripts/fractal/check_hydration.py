#!/usr/bin/env python3
"""
Fractal Hydration Checker
Usage: python scripts/fractal/check_hydration.py --hydrate [meta_file]
Checks if a module has a 'content_outline'. If not, recommends the Architect Skill.
"""

import sys
import os
import yaml
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=1000)

def find_template(focus, level):
    """Locate the correct template based on focus and level."""
    # This logic mirrors the project conventions
    template_dir = Path("docs/l2-uk-en/templates")
    
    # Priority 1: Specific Focus + Level (e.g., c1-biography)
    candidates = [
        f"{level}-{focus}-module-template.md",
        f"{focus}-module-template.md",
        f"{level}-module-template.md",
        "module-template.md"
    ]
    
    for c in candidates:
        path = template_dir / c
        print(f"DEBUG: Checking {path} (Exists: {path.exists()})")
        if path.exists():
            return path
    return None

def hydrate_module(meta_path):
    """
    Check if module needs hydration.
    If yes, print instructions for the Agent to call the Architect.
    """
    path = Path(meta_path)
    if not path.exists():
        print(f"Error: File not found {path}")
        sys.exit(1)

    data = load_yaml(path)
    
    # Check if hydration is needed
    if 'content_outline' in data and data['content_outline']:
        print(f"✅ Module {path.name} is already hydrated.")
        return

    print(f"⚠️  Module {path.name} needs hydration (missing content_outline).")
    
    # Resolve details for Architect
    focus = data.get('focus', 'general')
    # Extract level from module ID or path (e.g., b2-hist -> b2)
    level = "b2" # Default fallback
    if 'module' in data and '-' in data['module']:
        level = data['module'].split('-')[0]
    
    template_path = find_template(focus, level)
    
    if not template_path:
        print(f"❌ Error: Could not find template for focus='{focus}', level='{level}'")
        sys.exit(1)
        
    print("\n=== ARCHITECT SKILL INSTRUCTIONS ===")
    print(f"1. Activate Skill: 'architect'")
    print(f"2. Instruction: 'Hydrate {meta_path} using template {template_path}'")
    print("====================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fractal Orchestrator")
    parser.add_argument("--hydrate", help="Path to meta YAML file to check/hydrate")
    
    args = parser.parse_args()
    
    if args.hydrate:
        hydrate_module(args.hydrate)
    else:
        parser.print_help()
