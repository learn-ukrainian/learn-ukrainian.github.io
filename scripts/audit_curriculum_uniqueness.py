#!/usr/bin/env python3
"""
Audit Curriculum Plans for Vocabulary Uniqueness

Scans all CURRICULUM-PLAN.md files and identifies words listed as 
'Core Vocabulary' in more than one module.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

def audit_uniqueness():
    project_root = Path(__file__).parent.parent
    plan_dir = project_root / "docs" / "l2-uk-en"
    plan_files = sorted(plan_dir.glob("*-CURRICULUM-PLAN.md"))
    
    if not plan_files:
        print("❌ No curriculum plans found.")
        return

    # Map: word -> list of (level, module_num, module_title)
    global_vocab = defaultdict(list)
    
    # Regex to find Module headers and Vocabulary blocks
    # Supporting both "Module 01" and "Module 1" formats
    module_pattern = re.compile(r'#### Module\s+(\d+):\s*(.+)')
    vocab_pattern = re.compile(r'\*\*Vocabulary\s+\(\d+\s+words\):\*\*\n(.*?)(?=\n\n|\n#|\Z)', re.DOTALL)

    for plan_file in plan_files:
        level = plan_file.name.split("-")[0]
        content = plan_file.read_text(encoding='utf-8')
        
        # Split content by Module headers to keep context
        parts = re.split(r'(?=#### Module)', content)
        
        for part in parts:
            module_match = module_pattern.search(part)
            if not module_match:
                continue
                
            module_num = int(module_match.group(1))
            module_title = module_match.group(2).strip()
            
            vocab_match = vocab_pattern.search(part)
            if not vocab_match:
                continue
                
            # Clean and split words
            raw_vocab = vocab_match.group(1).strip()
            # Remove parentheses like (this)
            clean_vocab = re.sub(r'\(.*?\)', '', raw_vocab)
            # Split by comma and clean whitespace
            words = [w.strip().lower() for w in clean_vocab.split(',') if w.strip()]
            
            for word in words:
                global_vocab[word].append({
                    'level': level,
                    'module': module_num,
                    'title': module_title
                })

    # Identify duplicates
    duplicates = {word: locs for word, locs in global_vocab.items() if len(locs) > 1}
    
    if not duplicates:
        print("✅ SUCCESS: No duplicate vocabulary found across curriculum plans.")
        sys.exit(0)

    print(f"⚠️  FOUND {len(duplicates)} DUPLICATE WORDS IN CURRICULUM PLANS:\n")
    print(f"{'Word':<20} | {'First Intro':<25} | {'Subsequent Appears'}")
    print("-" * 80)
    
    for word in sorted(duplicates.keys()):
        locs = duplicates[word]
        # Sort by level and module to find the "true" first intro
        locs.sort(key=lambda x: (x['level'], x['module']))
        
        first = locs[0]
        others = locs[1:]
        
        first_str = f"{first['level']}-{first['module']:02d} ({first['title'][:10]}...)"
        others_str = ", ".join([f"{o['level']}-{o['module']:02d}" for o in others])
        
        print(f"{word:<20} | {first_str:<25} | {others_str}")

    print("\nTotal Unique Words in Plan:", len(global_vocab))
    sys.exit(1)

if __name__ == "__main__":
    audit_uniqueness()
