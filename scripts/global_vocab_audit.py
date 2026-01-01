#!/usr/bin/env python3
"""
Global Vocabulary Audit
-----------------------
Audits all YAML vocabulary files across the curriculum.
"""

import sys
import argparse
from pathlib import Path
from validate_vocab_yaml import validate_file

def audit_level(level_dir):
    print(f"\nScanning {level_dir}...")
    vocab_dir = level_dir / "vocabulary"
    if not vocab_dir.exists():
        # Fallback to recursively finding vocabulary folders?
        # Current structure: l2-uk-en/{level}/vocabulary/*.yaml
        print(f"  ⚠️ No vocabulary folder found in {level_dir}")
        return 0, 0

    files = sorted(list(vocab_dir.glob("*.yaml")))
    passed = 0
    failed = 0
    
    for f in files:
        if validate_file(f):
            passed += 1
        else:
            failed += 1
            
    return passed, failed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', type=str, help="Level to audit (a1, a2, etc) or 'all'", default='all')
    args = parser.parse_args()
    
    root = Path("curriculum/l2-uk-en")
    if not root.exists():
        print("Root directory not found.")
        sys.exit(1)
        
    levels = ["a1", "a2", "b1", "b2", "c1", "c2"]
    if args.level != 'all':
        levels = [args.level]
        
    total_passed = 0
    total_failed = 0
    
    for lvl in levels:
        lvl_dir = root / lvl
        if lvl_dir.exists():
            p, f = audit_level(lvl_dir)
            total_passed += p
            total_failed += f
            
    print("-" * 40)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    
    if total_failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
