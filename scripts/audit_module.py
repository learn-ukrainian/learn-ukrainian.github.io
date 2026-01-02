#!/usr/bin/env python3
"""
Module Audit CLI

Audits curriculum module files for quality, grammar constraints,
activity requirements, and pedagogical standards.

Usage:
    python3 scripts/audit_module.py <file.md> [file2.md ...]
    python3 scripts/audit_module.py <file.md> --validate-grammar  # With LLM grammar check

Options:
    --validate-grammar    Enable LLM-based grammar validation (requires GEMINI_API_KEY)
"""

import sys
import argparse
from audit import audit_module


def validate_grammar_with_llm(file_path: str) -> list[dict]:
    """
    Validate grammar using Gemini API (optional, requires GEMINI_API_KEY).
    
    Returns list of grammar issues found, or empty list if validation passes.
    """
    import os
    import json
    import re
    from pathlib import Path
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("  ⚠️ GEMINI_API_KEY not set. Skipping LLM grammar validation.")
        print("     Set: export GEMINI_API_KEY='your-key'")
        return []
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("  ⚠️ google-generativeai not installed. Skipping grammar validation.")
        print("     Install: pip install google-generativeai")
        return []
    
    # Load content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Detect level from path
    level = "B1"
    level_match = re.search(r'/([abc][12])/', file_path.lower())
    if level_match:
        level = level_match.group(1).upper()
    
    # Load system prompt
    prompt_path = Path(__file__).parent / 'audit' / 'ukrainian_grammar_validator_prompt.md'
    if not prompt_path.exists():
        print(f"  ⚠️ Grammar validator prompt not found: {prompt_path}")
        return []
    
    system_prompt = prompt_path.read_text(encoding='utf-8')
    
    # Extract Ukrainian sentences to validate (skip metadata, tables, code)
    sentences = []
    in_frontmatter = False
    for line in content.split('\n'):
        stripped = line.strip()
        # Skip frontmatter, code blocks, tables, headers, empty lines
        if stripped == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if stripped.startswith('|') or stripped.startswith('```'):
            continue
        if stripped.startswith('#'):
            continue
        if not stripped:
            continue
        # Check if line contains Cyrillic (Ukrainian content)
        if re.search(r'[\u0400-\u04FF]', stripped):
            sentences.append(stripped[:500])  # Limit length
    
    if not sentences:
        print("  ℹ️ No Ukrainian sentences found to validate.")
        return []
    
    # Sample sentences if too many (keep validation fast/cheap)
    import random
    max_sentences = 20
    if len(sentences) > max_sentences:
        sentences = random.sample(sentences, max_sentences)
    
    print(f"  🔍 Validating {len(sentences)} Ukrainian sentences with Gemini...")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        system_instruction=system_prompt,
        generation_config={
            'temperature': 0.1,
            'response_mime_type': 'application/json'
        }
    )
    
    issues = []
    for sentence in sentences[:10]:  # Validate up to 10 for speed
        user_prompt = f"""
Validate this sentence for grammar correctness:

**Sentence:** {sentence}
**Level:** {level}
**Context:** Curriculum module content

If there are issues, return {"is_real_error": true} with details.
If it's correct or pedagogically acceptable, return {"is_real_error": false}.
Respond in JSON format as specified.
"""
        try:
            response = model.generate_content(user_prompt)
            result = json.loads(response.text)
            if result.get('is_real_error'):
                issues.append({
                    'sentence': sentence[:100],
                    'error_type': result.get('error_type', 'unknown'),
                    'severity': result.get('severity', 'minor'),
                    'explanation': result.get('explanation_en', ''),
                    'recommendation': result.get('recommendation', '')
                })
        except Exception as e:
            print(f"  ⚠️ Validation error: {e}")
            continue
    
    return issues


def print_grammar_issues(issues: list[dict]) -> None:
    """Print grammar validation results."""
    if not issues:
        print("  ✅ LLM Grammar Check: No critical issues found")
        return
    
    print(f"\n  ⚠️ LLM Grammar Check: {len(issues)} issue(s) found:")
    for i, issue in enumerate(issues, 1):
        severity_icon = "❌" if issue['severity'] == 'critical' else "⚠️"
        print(f"    {severity_icon} [{issue['error_type']}] {issue['sentence'][:60]}...")
        if issue.get('explanation'):
            print(f"       → {issue['explanation'][:100]}")
        if issue.get('recommendation'):
            print(f"       Fix: {issue['recommendation'][:80]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Audit curriculum module files for quality and standards."
    )
    parser.add_argument("files", nargs="*", help="Module file(s) to audit")
    parser.add_argument(
        "--validate-grammar",
        action="store_true",
        help="Enable LLM-based grammar validation (requires GEMINI_API_KEY)"
    )
    
    args = parser.parse_args()
    
    if not args.files:
        print("Usage: python3 scripts/audit_module.py <file.md> [file2.md ...] [--validate-grammar]")
        sys.exit(1)

    any_failure = False
    for file_path in args.files:
        print(f"\n{'='*40}")
        
        # Run standard audit
        success = audit_module(file_path)
        
        # Run optional LLM grammar validation
        if args.validate_grammar:
            issues = validate_grammar_with_llm(file_path)
            print_grammar_issues(issues)
            # Critical grammar issues cause failure
            if any(i['severity'] == 'critical' for i in issues):
                success = False
        
        if not success:
            any_failure = True

    if any_failure:
        sys.exit(1)
    else:
        sys.exit(0)
