#!/usr/bin/env python3
"""
Merge ULP podcast mappings into external resources YAML.

Takes Gemini's podcast mappings and merges them with existing resources,
handling deduplication and relevance updates.

Usage:
    .venv/bin/python scripts/merge_podcast_mappings.py \
        --existing docs/resources/external_resources.yaml \
        --podcasts docs/resources/podcasts/ulp_mapping.yaml \
        --output docs/resources/external_resources.yaml
"""

import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def load_yaml(file_path: Path) -> Dict:
    """Load YAML file."""
    with file_path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict, file_path: Path):
    """Save YAML file."""
    with file_path.open('w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def get_relevance_priority(relevance: str) -> int:
    """Get numeric priority for relevance level (higher is better)."""
    priorities = {'high': 3, 'medium': 2, 'low': 1}
    return priorities.get(relevance, 0)


def should_replace_podcast(existing: Dict, new: Dict) -> bool:
    """
    Determine if new podcast entry should replace existing one.

    Replace if:
    - New has higher relevance
    - Same relevance but new has better match_reason
    """
    existing_priority = get_relevance_priority(existing.get('relevance', 'low'))
    new_priority = get_relevance_priority(new.get('relevance', 'low'))

    if new_priority > existing_priority:
        return True

    # Same relevance - prefer one with match_reason
    if new_priority == existing_priority:
        if new.get('match_reason') and not existing.get('match_reason'):
            return True

    return False


def deduplicate_resources(resources: List[Dict], resource_type: str) -> List[Dict]:
    """
    Deduplicate resources by URL or episode_id.

    For podcasts: dedupe by episode_id
    For others: dedupe by url
    Keep entry with highest relevance.
    """
    if not resources:
        return []

    # Group by unique key
    unique_key = 'episode_id' if resource_type == 'podcasts' else 'url'
    seen = {}

    for resource in resources:
        key_value = resource.get(unique_key)
        if not key_value:
            continue

        if key_value not in seen:
            seen[key_value] = resource
        else:
            # Keep the one with higher relevance
            if should_replace_podcast(seen[key_value], resource):
                seen[key_value] = resource

    return list(seen.values())


def merge_podcast_into_module(module_resources: Dict, podcast: Dict) -> bool:
    """
    Merge a single podcast episode into module resources.

    Returns True if added/updated, False if skipped.
    """
    # Ensure podcasts array exists
    if 'podcasts' not in module_resources:
        module_resources['podcasts'] = []

    podcasts = module_resources['podcasts']
    episode_id = podcast['episode_id']

    # Check if episode already exists
    existing_idx = None
    for idx, existing in enumerate(podcasts):
        if existing.get('episode_id') == episode_id:
            existing_idx = idx
            break

    # Create podcast entry from ULP mapping format
    podcast_entry = {
        'episode_id': podcast['episode_id'],
        'title': podcast['title'],
        'url': podcast['url'],
        'relevance': podcast['relevance']
    }

    # Add match_reason if present
    if 'match_reason' in podcast:
        podcast_entry['match_reason'] = podcast['match_reason']

    if existing_idx is not None:
        # Episode exists - check if we should update
        existing = podcasts[existing_idx]
        if should_replace_podcast(existing, podcast_entry):
            podcasts[existing_idx] = podcast_entry
            return True
        return False
    else:
        # New episode - add it
        podcasts.append(podcast_entry)
        return True


def merge_mappings(existing_path: Path, podcasts_path: Path) -> Dict:
    """
    Merge podcast mappings into existing resources.

    Returns updated resources dictionary.
    """
    # Load both files
    existing_data = load_yaml(existing_path)
    podcasts_data = load_yaml(podcasts_path)

    # Get resources dict (create if doesn't exist)
    resources = existing_data.get('resources', {})

    # Track statistics
    stats = {
        'modules_updated': 0,
        'modules_created': 0,
        'episodes_added': 0,
        'episodes_updated': 0,
        'episodes_skipped': 0
    }

    # Process each mapping
    for mapping in podcasts_data.get('mappings', []):
        module_id = mapping['module_id']
        recommended_episodes = mapping.get('recommended_episodes', [])

        if not recommended_episodes:
            continue

        # Get or create module entry
        if module_id not in resources:
            resources[module_id] = {}
            stats['modules_created'] += 1

        module_resources = resources[module_id]
        module_modified = False

        # Merge each recommended episode
        for episode in recommended_episodes:
            added = merge_podcast_into_module(module_resources, episode)
            if added:
                if 'podcasts' in module_resources:
                    # Check if this was an update or addition
                    episode_ids = [p.get('episode_id') for p in module_resources['podcasts']]
                    if episode_ids.count(episode['episode_id']) > 1:
                        stats['episodes_updated'] += 1
                    else:
                        stats['episodes_added'] += 1
                module_modified = True
            else:
                stats['episodes_skipped'] += 1

        if module_modified:
            stats['modules_updated'] += 1

        # Deduplicate podcasts in this module
        if 'podcasts' in module_resources:
            module_resources['podcasts'] = deduplicate_resources(
                module_resources['podcasts'],
                'podcasts'
            )

    # Update metadata
    existing_data['resources'] = resources
    existing_data['generated_at'] = datetime.now().strftime('%Y-%m-%d')

    return existing_data, stats


def main():
    parser = argparse.ArgumentParser(
        description="Merge ULP podcast mappings into external resources"
    )
    parser.add_argument(
        '--existing',
        type=Path,
        required=True,
        help="Path to existing external_resources.yaml"
    )
    parser.add_argument(
        '--podcasts',
        type=Path,
        required=True,
        help="Path to ulp_mapping.yaml (Gemini's podcast mappings)"
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help="Output path for merged YAML"
    )

    args = parser.parse_args()

    # Validate input files exist
    if not args.existing.exists():
        print(f"❌ Error: Existing resources file not found: {args.existing}")
        return 1

    if not args.podcasts.exists():
        print(f"❌ Error: Podcast mappings file not found: {args.podcasts}")
        return 1

    print(f"🔄 Merging podcast mappings...")
    print(f"  📄 Existing: {args.existing}")
    print(f"  🎧 Podcasts: {args.podcasts}")
    print(f"  📤 Output: {args.output}")
    print()

    # Merge
    merged_data, stats = merge_mappings(args.existing, args.podcasts)

    # Save
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_yaml(merged_data, args.output)

    # Report
    print("📊 Merge Summary:")
    print(f"  ✨ Modules created: {stats['modules_created']}")
    print(f"  🔄 Modules updated: {stats['modules_updated']}")
    print(f"  ➕ Episodes added: {stats['episodes_added']}")
    print(f"  🔄 Episodes updated: {stats['episodes_updated']}")
    print(f"  ⏭️  Episodes skipped: {stats['episodes_skipped']}")
    print()
    print("✅ Merge complete!")

    return 0


if __name__ == '__main__':
    exit(main())
