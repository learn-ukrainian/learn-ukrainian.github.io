#!/usr/bin/env python3
"""
Score resource-module pairs for automated mapping.

This script implements the 4-dimension relevance scoring algorithm:
1. Grammar/Topic Match (0-25): Keyword overlap
2. CEFR Level Match (0-25): Level distance
3. Content Type Alignment (0-25): Resource type vs module type
4. Source Priority Bonus (0-25): ULP gets +25

Total score 0-100 → Priority 1-5 (or no mapping if score < threshold)

Usage:
    .venv/bin/python scripts/score_resource_module_pairs.py \
        --threshold 30 \
        --output docs/resources/ukrainianlessons/resource_module_scores.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


# CEFR level hierarchy
CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']


def calculate_topic_match(resource: Dict, module: Dict) -> Tuple[int, str]:
    """
    Calculate topic/grammar match score (0-25).

    Uses weighted keyword matching:
    - Title keywords have higher weight than topic keywords
    - Module title words are prioritized for relevance

    Compares:
    - Resource topics/title keywords vs module topics/title keywords
    - Resource vocabulary overlap with module vocabulary
    """
    # Extract keywords from resource with weights
    resource_title_words = set()
    resource_topic_words = set()

    # From resource title (higher weight)
    if 'title' in resource:
        title_words = re.sub(r'[^\w\s]', ' ', resource['title'].lower()).split()
        resource_title_words.update(title_words)

    # From resource topics
    if 'topics' in resource:
        for topic in resource['topics']:
            resource_topic_words.update(topic.lower().split())

    # Extract keywords from module with weights
    module_title_words = set()
    module_topic_words = set()

    # From module title (higher weight)
    if 'title' in module:
        title_words = re.sub(r'[^\w\s]', ' ', module['title'].lower()).split()
        module_title_words.update(title_words)

    # From module topics
    if 'topics' in module:
        for topic in module['topics']:
            module_topic_words.update(topic.lower().split())

    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or',
                  'ukrainian', 'lesson', 'module', 'guide', 'learning', 'practice',
                  'warm', 'up', 'presentation', 'production', 'cultural', 'insight', 'need', 'more'}

    resource_title_words -= stop_words
    resource_topic_words -= stop_words
    module_title_words -= stop_words
    module_topic_words -= stop_words

    # Semantic keyword expansion for better matching
    # Add related terms to improve topic relevance
    semantic_expansions = {
        'alphabet': {'cyrillic', 'letters', 'script'},
        'cyrillic': {'alphabet', 'letters'},
        'case': {'accusative', 'genitive', 'dative', 'instrumental', 'locative', 'vocative'},
        'tense': {'past', 'future', 'present'},
        'aspect': {'perfective', 'imperfective', 'verb', 'verbs'}
    }

    # Expand resource keywords
    expanded_resource_title = resource_title_words.copy()
    expanded_resource_topic = resource_topic_words.copy()
    for word in resource_title_words | resource_topic_words:
        if word in semantic_expansions:
            expanded_resource_title.update(semantic_expansions[word])
            expanded_resource_topic.update(semantic_expansions[word])

    # Expand module keywords
    expanded_module_title = module_title_words.copy()
    expanded_module_topic = module_topic_words.copy()
    for word in module_title_words | module_topic_words:
        if word in semantic_expansions:
            expanded_module_title.update(semantic_expansions[word])
            expanded_module_topic.update(semantic_expansions[word])

    # Use expanded keywords for matching
    resource_title_words = expanded_resource_title
    resource_topic_words = expanded_resource_topic
    module_title_words = expanded_module_title
    module_topic_words = expanded_module_topic

    # Calculate weighted overlap
    # Title-to-title match = weight 3
    # Title-to-topic match = weight 2
    # Topic-to-topic match = weight 1

    title_title_match = resource_title_words & module_title_words
    title_topic_match = (resource_title_words & module_topic_words) | (resource_topic_words & module_title_words)
    topic_topic_match = resource_topic_words & module_topic_words

    # Calculate weighted score
    weighted_overlap = (len(title_title_match) * 3 +
                       len(title_topic_match) * 2 +
                       len(topic_topic_match) * 1)

    # Total possible weight (all keywords matched at highest weight)
    all_resource_words = resource_title_words | resource_topic_words
    all_module_words = module_title_words | module_topic_words
    max_possible = len(all_resource_words | all_module_words) * 3

    if max_possible == 0:
        return 0, "No keywords to compare"

    # Normalized score (0-1)
    similarity = weighted_overlap / max_possible if max_possible > 0 else 0

    # Score mapping (weighted similarity → Score 0-25)
    all_matches = title_title_match | title_topic_match | topic_topic_match

    if similarity >= 0.4:  # 40%+ weighted overlap
        score = 25
        reason = f"Exact match: {title_title_match or all_matches}"
    elif similarity >= 0.25:  # 25-40% overlap
        score = 20
        reason = f"Core match: {title_title_match or all_matches}"
    elif similarity >= 0.15:  # 15-25% overlap
        score = 15
        reason = f"Partial match: {all_matches}"
    elif similarity >= 0.05:  # 5-15% overlap
        score = 10
        reason = f"Tangential: {all_matches}"
    else:
        score = 0
        reason = f"No meaningful overlap"

    return score, reason


def infer_ulp_level(episode_id: str) -> str:
    """
    Infer CEFR level from ULP episode ID.

    ULP-001 to ULP-050 = A1 (Season 1)
    ULP-051 to ULP-100 = A2 (Season 2)
    ULP-101 to ULP-150 = B1 (Season 3)
    ULP-151 to ULP-200 = B2 (Season 4)
    ULP-201+ = B2 (advanced)
    """
    if not episode_id.startswith('ULP-'):
        return 'A1'  # Default

    try:
        num = int(episode_id.split('-')[1])
        if num <= 50:
            return 'A1'
        elif num <= 100:
            return 'A2'
        elif num <= 150:
            return 'B1'
        else:
            return 'B2'
    except (IndexError, ValueError):
        return 'A1'  # Default fallback


def calculate_level_match(resource_level: str, module_level: str) -> Tuple[int, str]:
    """
    Calculate CEFR level match score (0-25).

    Same level: 25
    ±1 level: 20
    ±2 levels: 10
    ±3+ levels: 0
    """
    if resource_level not in CEFR_LEVELS or module_level not in CEFR_LEVELS:
        return 0, f"Invalid level: {resource_level} vs {module_level}"

    resource_idx = CEFR_LEVELS.index(resource_level)
    module_idx = CEFR_LEVELS.index(module_level)
    distance = abs(resource_idx - module_idx)

    if distance == 0:
        return 25, "Same level"
    elif distance == 1:
        return 20, "Adjacent level (±1)"
    elif distance == 2:
        return 10, "±2 levels"
    else:
        return 0, f"±{distance} levels (too distant)"


def calculate_content_alignment(resource: Dict, module: Dict) -> Tuple[int, str]:
    """
    Calculate content type alignment score (0-25).

    Perfect: 25 (e.g., grammar resource → grammar module)
    Strong: 20 (e.g., podcast → any module as listening practice)
    Moderate: 15 (e.g., vocabulary list → vocabulary module)
    Weak: 10 (e.g., cultural article → grammar module)
    Misaligned: 0
    """
    resource_type = resource.get('content_type', 'unknown')
    module_topics = module.get('topics', [])
    module_title = module.get('title', '').lower()

    # Determine module type from topics/title
    module_type = 'general'
    if any(t in module_title for t in ['grammar', 'aspect', 'case', 'tense', 'passive', 'participle']):
        module_type = 'grammar'
    elif any(t in module_title for t in ['vocabulary', 'vocab', 'words']):
        module_type = 'vocabulary'
    elif any(t in module_title for t in ['culture', 'history', 'tradition', 'region', 'music', 'cinema']):
        module_type = 'cultural'
    elif any(t in module_title for t in ['checkpoint', 'integration', 'practice']):
        module_type = 'integration'

    # Alignment rules
    if resource_type == 'guide' and module_type == 'grammar':
        return 25, "Perfect: Grammar guide → Grammar module"
    elif resource_type == 'vocabulary_list' and module_type == 'vocabulary':
        return 25, "Perfect: Vocabulary list → Vocabulary module"
    elif resource_type == 'cultural_guide' and module_type == 'cultural':
        return 25, "Perfect: Cultural content → Cultural module"
    elif resource_type in ['guide', 'reference'] and module_type in ['grammar', 'vocabulary']:
        return 20, "Strong: Reference material → Study module"
    elif resource_type == 'phrasebook':
        return 20, "Strong: Phrasebook useful for all levels"
    elif resource_type == 'cultural_guide' and module_type != 'cultural':
        return 10, "Weak: Cultural content for non-cultural module"
    elif resource_type in ['methodology', 'resource_guide']:
        return 15, "Moderate: Meta-learning content"
    else:
        return 15, f"Moderate: {resource_type} → {module_type}"


def calculate_source_priority(resource: Dict) -> Tuple[int, str]:
    """
    Calculate source priority bonus (0-25).

    Ukrainian Lessons (ULP/FMU/blog): 25
    Trusted external sources: 15
    General resources: 10
    """
    source = resource.get('source', '')
    url = resource.get('url', '')
    episode_id = resource.get('episode_id', resource.get('id', ''))

    # Check if Ukrainian Lessons content
    if 'ukrainianlessons.com' in url or episode_id.startswith('ULP-') or episode_id.startswith('FMU-'):
        return 25, "Ukrainian Lessons (priority source)"
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 15, "YouTube (trusted video)"
    elif any(trusted in url.lower() for trusted in ['ukrainian', 'learn', 'language', 'grammar']):
        return 15, "Trusted external source"
    else:
        return 10, "General resource"


def score_pair(resource: Dict, module: Dict) -> Dict:
    """
    Calculate total relevance score for a resource-module pair.

    Returns dict with:
    - total_score (0-100)
    - priority (1-5 or None)
    - breakdown (dict with dimension scores and reasons)
    """
    # Calculate each dimension
    topic_score, topic_reason = calculate_topic_match(resource, module)

    # Infer level for ULP episodes if not specified
    resource_level = resource.get('suggested_level')
    if not resource_level:
        episode_id = resource.get('id', resource.get('episode_id', ''))
        resource_level = infer_ulp_level(episode_id)

    level_score, level_reason = calculate_level_match(
        resource_level or 'A1',
        module.get('level', 'A1')
    )
    content_score, content_reason = calculate_content_alignment(resource, module)
    source_score, source_reason = calculate_source_priority(resource)

    # IMPORTANT: Require minimum topic relevance
    # Don't map resources that have no topic connection, even if same level + ULP source
    if topic_score < 12:  # Must have better than tangential match (filters weak single-word matches)
        return {
            'total_score': 0,
            'priority': None,
            'breakdown': {
                'topic_match': {'score': topic_score, 'reason': f"REJECTED: {topic_reason}"},
                'level_match': {'score': level_score, 'reason': level_reason},
                'content_alignment': {'score': content_score, 'reason': content_reason},
                'source_priority': {'score': source_score, 'reason': source_reason}
            }
        }

    # Total score
    total_score = topic_score + level_score + content_score + source_score

    # Map score to priority
    if total_score >= 90:
        priority = 1  # Critical/Essential
    elif total_score >= 75:
        priority = 2  # High
    elif total_score >= 60:
        priority = 3  # Moderate
    elif total_score >= 45:
        priority = 4  # General
    elif total_score >= 30:
        priority = 5  # Culture/Background
    else:
        priority = None  # Below threshold - don't map

    return {
        'total_score': total_score,
        'priority': priority,
        'breakdown': {
            'topic_match': {'score': topic_score, 'reason': topic_reason},
            'level_match': {'score': level_score, 'reason': level_reason},
            'content_alignment': {'score': content_score, 'reason': content_reason},
            'source_priority': {'score': source_score, 'reason': source_reason}
        }
    }


def load_resources() -> List[Dict]:
    """Load all resources from blog_db.json and podcast_db.json."""
    resources = []

    # Load blog articles
    blog_path = Path('docs/resources/ukrainianlessons/blog_db.json')
    if blog_path.exists():
        with open(blog_path, 'r', encoding='utf-8') as f:
            blog_data = json.load(f)
            resources.extend(blog_data['articles'])
            print(f"  Loaded {len(blog_data['articles'])} blog articles")

    # Load podcast episodes (filter to ULP only)
    podcast_path = Path('docs/resources/podcasts/podcast_db.json')
    if podcast_path.exists():
        with open(podcast_path, 'r', encoding='utf-8') as f:
            podcast_data = json.load(f)
            ulp_episodes = [ep for ep in podcast_data if ep.get('id', '').startswith('ULP-')]
            resources.extend(ulp_episodes)
            print(f"  Loaded {len(ulp_episodes)} ULP podcast episodes")

    return resources


def load_modules() -> Dict[str, Dict]:
    """Load module metadata from module_metadata.json."""
    metadata_path = Path('docs/resources/ukrainianlessons/module_metadata.json')

    with open(metadata_path, 'r', encoding='utf-8') as f:
        modules = json.load(f)

    print(f"  Loaded {len(modules)} modules")
    return modules


def score_all_pairs(resources: List[Dict], modules: Dict[str, Dict], threshold: int) -> Dict:
    """
    Score all resource-module pairs and filter by threshold.

    Returns dict: {module_id: [list of scored resources]}
    """
    results = {}
    total_pairs = len(resources) * len(modules)
    processed = 0
    above_threshold = 0

    print(f"\n📊 Scoring {total_pairs:,} resource-module pairs...")
    print(f"   Threshold: {threshold} points\n")

    for module_id, module_data in modules.items():
        module_results = []

        for resource in resources:
            scoring = score_pair(resource, module_data)

            # Only keep if above threshold
            if scoring['total_score'] >= threshold:
                module_results.append({
                    'resource_id': resource.get('id', resource.get('episode_id', 'unknown')),
                    'resource_title': resource.get('title', 'Untitled'),
                    'resource_url': resource.get('url', ''),
                    'score': scoring['total_score'],
                    'priority': scoring['priority'],
                    'breakdown': scoring['breakdown']
                })
                above_threshold += 1

            processed += 1
            if processed % 10000 == 0:
                print(f"   Processed {processed:,}/{total_pairs:,} pairs ({above_threshold:,} above threshold)")

        # Sort by score (highest first)
        module_results.sort(key=lambda x: x['score'], reverse=True)

        if module_results:
            results[module_id] = module_results

    print(f"\n✅ Completed scoring!")
    print(f"   Total pairs evaluated: {total_pairs:,}")
    print(f"   Pairs above threshold: {above_threshold:,}")
    print(f"   Modules with mappings: {len(results)}/{len(modules)}")

    return results


def save_results(results: Dict, output_path: Path):
    """Save scored results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved results to {output_path}")


def print_summary(results: Dict):
    """Print summary statistics."""
    print("\n📈 Summary by Priority:")

    priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for module_id, mappings in results.items():
        for mapping in mappings:
            priority = mapping['priority']
            if priority:
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

    print(f"   Priority 1 (Critical): {priority_counts[1]:,} mappings")
    print(f"   Priority 2 (High): {priority_counts[2]:,} mappings")
    print(f"   Priority 3 (Moderate): {priority_counts[3]:,} mappings")
    print(f"   Priority 4 (General): {priority_counts[4]:,} mappings")
    print(f"   Priority 5 (Culture): {priority_counts[5]:,} mappings")
    print(f"\n   Total: {sum(priority_counts.values()):,} mappings")


def main():
    parser = argparse.ArgumentParser(description='Score resource-module pairs')
    parser.add_argument('--threshold', type=int, default=30,
                        help='Minimum score threshold (default: 30)')
    parser.add_argument('--output', type=str,
                        default='docs/resources/ukrainianlessons/resource_module_scores.json',
                        help='Output file path')

    args = parser.parse_args()

    print("🔍 Ukrainian Lessons Resource Mapping - Automated Scoring\n")

    # Load data
    print("📂 Loading data...")
    resources = load_resources()
    modules = load_modules()

    # Score all pairs
    results = score_all_pairs(resources, modules, args.threshold)

    # Save results
    output_path = Path(args.output)
    save_results(results, output_path)

    # Print summary
    print_summary(results)

    print("\n✅ Scoring complete!")
    print(f"\n📝 Next steps:")
    print(f"   1. Review Priority 1 mappings (manual verification required)")
    print(f"   2. Spot-check 10% of Priority 2-3 mappings")
    print(f"   3. Update external_resources.yaml with approved mappings")


if __name__ == '__main__':
    main()
