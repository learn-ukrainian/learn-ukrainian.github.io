"""
Content Purity Checker

Detects automated generation artifacts in LESSON content only:
- Duplicate long sentences (over 50 chars)
- Robotic repetition of templates

Activities are SUPPOSED to use lesson content, so no cross-file checks.
"""

import re
from typing import List, Dict
from pathlib import Path

def get_word_set(text: str) -> set:
    """Extract set of unique words from text."""
    # Remove markdown, punctuation, and YAML syntax
    text = re.sub(r'[*_#:\-\-\[\]{{`|`}}]', ' ', text) # Added pipe |
    words = re.findall(r'[а-яіїєґА-ЯІЇЄҐA-Za-z]+', text.lower())
    # Keep words > 3 chars to ignore common particles
    return {w for w in words if len(w) > 3}

def check_duplicate_sentences(content: str, yaml_content: str = "") -> List[Dict]:
    """
    Find sentences with high word overlap within lesson content.
    Activities are SUPPOSED to use lesson content, so no cross-file check.
    """
    violations = []

    # Internal Purity Check (within Lesson MD only)
    text = re.sub(r'^---.*?---\n', '', content, flags=re.DOTALL)
    sentence_pattern = re.compile(r'(?<=[.!?])\s+')
    lesson_sentences = [s.strip() for s in sentence_pattern.split(text) if len(s.strip()) > 50]

    seen_sets = []
    for idx, s in enumerate(lesson_sentences):
        words = get_word_set(s)
        if len(words) < 5: continue

        for prev_idx, prev_raw, prev_words in seen_sets:
            intersection = words.intersection(prev_words)
            union = words.union(prev_words)
            similarity = len(intersection) / len(union) if union else 0

            # STRICTER Threshold: 0.5 (50% word overlap is suspicious for different sentences)
            if similarity > 0.5:
                display_s = s[:100] + "..." if len(s) > 100 else s
                violations.append({
                    'type': 'CONTENT_REDUNDANCY',
                    'severity': 'error',
                    'issue': f"Redundant information detected in lesson ({similarity*100:.0f}% overlap): \"{display_s}\". Shares significant keywords with sentence at index {prev_idx}.",
                    'fix': "Remove redundant paragraphs. Ensure each section adds new unique value."
                })
                break
        seen_sets.append((idx, s, words))

    return violations

def check_robotic_structure(content: str) -> List[Dict]:
    """
    Detects robotic repetition of sentence structures.
    """
    violations = []
    body = re.sub(r'^---.*?---\n', '', content, flags=re.DOTALL)
    
    sentences = re.split(r'(?<=[.!?])\s+', body)
    clean_sentences = []
    for s in sentences:
        s = s.strip()
        # Ignore list items, headers, short lines, AND TABLES
        if len(s) < 20 or s.startswith('-') or s.startswith('>') or s.startswith('*') or s.startswith('#') or s.startswith('|'):
            continue
        clean_sentences.append(re.sub(r'^[-*]\s+', '', s).strip())
    
    window_size = 4
    for i in range(len(clean_sentences) - window_size):
        window = clean_sentences[i : i+window_size]
        starters = []
        for s in window:
            words = s.split()
            if len(words) >= 2:
                starters.append(f"{words[0]} {words[1]}".lower())
        
        if len(starters) >= 3:
            from collections import Counter
            counts = Counter(starters)
            if counts:
                most_common, count = counts.most_common(1)[0]
                if count >= 3:
                    violations.append({
                        'type': 'ROBOTIC_STRUCTURE',
                        'severity': 'warning',
                        'issue': f"Robotic structure: {count} sentences start with '{most_common}...'.",
                        'fix': "Vary sentence structure."
                    })
                    break 
    return violations

def check_content_purity(content: str, yaml_content: str = "") -> List[Dict]:
    """Main entry point for purity checks."""
    violations = []
    violations.extend(check_duplicate_sentences(content, yaml_content))
    violations.extend(check_robotic_structure(content))
    return violations