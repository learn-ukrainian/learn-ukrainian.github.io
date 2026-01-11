#!/usr/bin/env python3
"""
YAML Structure Normalizer

Scans for activity YAML files that incorrectly use a dictionary root with an 'activities' key,
and converts them to the standard root-list format.

Usage:
    python3 scripts/normalize_yaml_structure.py
"""

import yaml
from pathlib import Path
import sys

def normalize_file(file_path: Path) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if data is None:
            return False
            
        # Check if root is dict with 'activities' key
        if isinstance(data, dict) and 'activities' in data:
            activities = data['activities']
            
            if not isinstance(activities, list):
                print(f"⚠️  {file_path.name}: 'activities' key exists but value is not a list. Skipping.")
                return False
                
            # Rewrite as list
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(activities, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            
            return True
            
        return False
        
    except Exception as e:
        print(f"❌ Error processing {file_path.name}: {e}")
        return False

def main():
    base_dir = Path('curriculum/l2-uk-en')
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']
    
    total_fixed = 0
    checked = 0
    
    print("🔍 Scanning for legacy YAML structures...")
    
    for level in levels:
        act_dir = base_dir / level / 'activities'
        if not act_dir.exists():
            continue
            
        for yaml_file in act_dir.glob('*.yaml'):
            checked += 1
            if normalize_file(yaml_file):
                print(f"  ✅ Fixed structure: {yaml_file.name}")
                total_fixed += 1
                
    print(f"\nChecked {checked} files.")
    print(f"Normalized {total_fixed} files.")

if __name__ == "__main__":
    main()
