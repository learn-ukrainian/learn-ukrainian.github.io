#!/usr/bin/env python3
"""
Audit Implementation Coverage of Core Vocabulary

Compares the "Blueprint" (CURRICULUM-PLAN.md) against the 
"Building" (Activities YAML and Markdown prose).
"""

import re
import sys
import yaml
from pathlib import Path
from collections import defaultdict

def extract_plan_vocab(project_root):
    """Returns dict: {(level, module_num): [words]}"""
    plan_dir = project_root / "docs" / "l2-uk-en"
    plan_files = list(plan_dir.glob("*-CURRICULUM-PLAN.md"))
    
    plan_vocab = {}
    module_pattern = re.compile(r'#### Module\s+(\d+):')
    vocab_pattern = re.compile(r'\*\*Vocabulary\s+\(\d+\s+words\):\*\*\n(.*?)(?=\n\n|\n#|\Z)', re.DOTALL)

    for plan_file in plan_files:
        level = plan_file.name.split("-")[0].lower()
        content = plan_file.read_text(encoding='utf-8')
        parts = re.split(r'(?=#### Module)', content)
        
        for part in parts:
            m_match = module_pattern.search(part)
            v_match = vocab_pattern.search(part)
            if m_match and v_match:
                module_num = int(m_match.group(1))
                raw_vocab = v_match.group(1).strip()
                clean_vocab = re.sub(r'\(.*?\)', '', raw_vocab)
                words = [w.strip().lower() for w in clean_vocab.split(',') if w.strip()]
                plan_vocab[(level, module_num)] = words
    return plan_vocab

def get_module_files(project_root, level, module_num):
    """Finds .md and activities.yaml for a given module."""
    level_dir = project_root / "curriculum" / "l2-uk-en" / level
    if not level_dir.exists():
        return None, None
        
    md_files = list(level_dir.glob(f"{module_num:02d}-*.md"))
    if not md_files:
        md_files = list(level_dir.glob(f"module-{module_num:02d}.md"))
        
    if not md_files:
        return None, None
        
    md_file = md_files[0]
    # Check new and legacy activity paths
    act_file = level_dir / "activities" / (md_file.stem + ".yaml")
    if not act_file.exists():
        act_file = level_dir / (md_file.stem + ".activities.yaml")
        
    return md_file, act_file if act_file.exists() else None

def audit_coverage():
    project_root = Path(__file__).parent.parent
    plan_vocab = extract_plan_vocab(project_root)
    
    if not plan_vocab:
        print("❌ No vocabulary found in plans.")
        return

    results = []
    
    for (level, module_num), expected_words in plan_vocab.items():
        md_file, act_file = get_module_files(project_root, level, module_num)
        
        if not md_file:
            continue
            
        md_text = md_file.read_text(encoding='utf-8').lower()
        act_text = ""
        if act_file:
            act_text = act_file.read_text(encoding='utf-8').lower()
            
        used_in_lesson = []
        used_in_activities = []
        
        for word in expected_words:
            pattern = re.compile(rf'(?<![а-яіїєґ]){re.escape(word)}(?![а-яіїєґ])')
            
            if pattern.search(md_text):
                used_in_lesson.append(word)
            if act_text and pattern.search(act_text):
                used_in_activities.append(word)
                
        total = len(expected_words)
        lesson_rate = (len(used_in_lesson) / total) * 100 if total > 0 else 0
        act_rate = (len(used_in_activities) / total) * 100 if total > 0 else 0
        
        results.append({
            'id': f"{level.upper()}-{module_num:02d}",
            'total': total,
            'lesson_rate': lesson_rate,
            'act_rate': act_rate,
            'missing': [w for w in expected_words if w not in used_in_lesson and w not in used_in_activities]
        })

    results.sort(key=lambda x: x['id'])
    
    print(f"\n{'Module':<10} | {'Total':<6} | {'Lesson %':<10} | {'Activity %':<10} | {'Status'}")
    print("-" * 60)
    
    for r in results:
        status = "✅" if r['lesson_rate'] >= 50 and r['act_rate'] >= 80 else "❌"
        if r['total'] == 0: status = "⚪"
        print(f"{r['id']:<10} | {r['total']:<6} | {r['lesson_rate']:>8.1f}% | {r['act_rate']:>9.1f}% | {status}")
        
        if status == "❌" and r['missing']:
            print(f"   └─ Missing: {', '.join(r['missing'][:10])}{'...' if len(r['missing']) > 10 else ''}")

if __name__ == "__main__":
    audit_coverage()
