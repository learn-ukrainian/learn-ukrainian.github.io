#!/usr/bin/env python3
"""
Extract external resources from curriculum markdown files.

Parses [!resources] callout blocks and converts to YAML format.

Usage:
    .venv/bin/python scripts/extract_external_resources.py \\
        --curriculum curriculum/l2-uk-en/ \\
        --output docs/resources/external_resources.yaml
"""

import argparse
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def classify_resource_type(url: str) -> str:
    """Classify resource type based on URL pattern."""
    url_lower = url.lower()

    # YouTube
    if 'youtube.com/watch' in url_lower or 'youtu.be/' in url_lower:
        return 'youtube'

    # Podcasts (ULP or FMU)
    if 'ukrainianlessons.com/lesson/' in url_lower or '/fmu' in url_lower:
        return 'podcasts'

    # Articles (Ukrainian Lessons or other content sites)
    if 'ukrainianlessons.com' in url_lower or 'wikipedia.org' in url_lower:
        return 'articles'

    # Default to websites for other URLs
    return 'websites'


def extract_title_url_from_markdown_link(text: str) -> Optional[tuple]:
    """Extract title and URL from markdown link format: [Title](URL)."""
    match = re.search(r'\[([^\]]+)\]\(([^\)]+)\)', text)
    if match:
        return (match.group(1).strip(), match.group(2).strip())
    return None


def parse_resources_section(content: str) -> List[Dict]:
    """
    Parse [!resources] callout block and extract resources.

    Returns list of resource dicts with: type, title, url, source, relevance
    """
    resources = []

    # Find the start of [!resources] block
    start_idx = content.find('> [!resources]')
    if start_idx == -1:
        return resources

    # Extract from start until we hit a non-'>' line (next section)
    lines = content[start_idx:].split('\n')
    resource_lines = []
    for line in lines[1:]:  # Skip the [!resources] header line
        # Stop if we hit a markdown heading or a line not starting with '>'
        if line.strip() and not line.strip().startswith('>'):
            break
        if line.strip().startswith('>'):
            resource_lines.append(line)

    # Extract each line that contains a link
    for line in resource_lines:
        line = line.strip()
        if not line.startswith('>'):
            continue

        line = line[1:].strip()  # Remove leading '>'

        # Skip empty lines
        if not line:
            continue

        # Remove emoji and bullet point (but keep text after **)
        # Handle format: **Category:** [link] OR - [link]
        line = re.sub(r'^[📖📺🎧🌐📚\-\*\s]+', '', line)
        # Also remove **Header:** prefix if present
        line = re.sub(r'^\*\*[^*]+\*\*:?\s*', '', line)

        # Extract link
        link_data = extract_title_url_from_markdown_link(line)
        if not link_data:
            continue

        title, url = link_data

        # Extract description (after " — ")
        description = ""
        if ' — ' in line:
            parts = line.split(' — ', 1)
            if len(parts) == 2:
                description = parts[1].strip()

        # Classify resource type
        resource_type = classify_resource_type(url)

        # Extract source/channel
        source = description if description else "Unknown"

        # Create resource entry
        resource = {
            'title': title,
            'url': url,
            'relevance': 'high',  # Default to high for existing resources
        }

        # Add type-specific fields
        if resource_type == 'youtube':
            resource['channel'] = source
        elif resource_type == 'podcasts':
            # Extract episode_id from URL if possible
            episode_match = re.search(r'/lesson/(\d+)', url)
            if episode_match:
                resource['episode_id'] = f"ULP-{int(episode_match.group(1)):03d}"
            fmu_match = re.search(r'/fmu(\d+)', url)
            if fmu_match:
                resource['episode_id'] = f"FMU-{int(fmu_match.group(1)):03d}"
        elif resource_type in ['articles', 'websites']:
            resource['source'] = source
            if description and description != source:
                resource['description'] = description

        resources.append({'type': resource_type, 'data': resource})

    return resources


def get_module_id_from_path(file_path: Path) -> str:
    """
    Extract module_id from file path.

    Example: curriculum/l2-uk-en/a1/07-questions-and-negation.md
    Returns: a1-07-questions-and-negation
    """
    # Get level from parent directory
    level = file_path.parent.name  # e.g., 'a1', 'b1'

    # Get filename without extension
    filename = file_path.stem  # e.g., '07-questions-and-negation'

    # Combine level and filename
    return f"{level}-{filename}"


def extract_resources_from_file(file_path: Path) -> Optional[Dict]:
    """Extract resources from a single markdown file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ⚠️  Error reading {file_path}: {e}")
        return None

    # Check if file has resources section
    if '[!resources]' not in content:
        return None

    # Extract resources
    resources = parse_resources_section(content)
    if not resources:
        return None

    # Group by type
    grouped = {
        'youtube': [],
        'podcasts': [],
        'articles': [],
        'books': [],
        'websites': []
    }

    for item in resources:
        resource_type = item['type']
        grouped[resource_type].append(item['data'])

    # Remove empty types
    grouped = {k: v for k, v in grouped.items() if v}

    return grouped


def main():
    parser = argparse.ArgumentParser(
        description="Extract external resources from curriculum markdown files"
    )
    parser.add_argument(
        '--curriculum',
        type=Path,
        required=True,
        help="Path to curriculum directory (e.g., curriculum/l2-uk-en/)"
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help="Output YAML file path (e.g., docs/resources/external_resources.yaml)"
    )
    parser.add_argument(
        '--modules',
        nargs='*',
        help="Optional: specific module IDs to extract (e.g., a1-07 b1-06)"
    )

    args = parser.parse_args()

    # Find all markdown files
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
    all_files = []

    for level in levels:
        level_dir = args.curriculum / level
        if not level_dir.exists():
            continue
        all_files.extend(sorted(level_dir.glob('*.md')))

    print(f"🔍 Found {len(all_files)} markdown files")

    # Filter by module IDs if specified
    if args.modules:
        filtered_files = []
        for file_path in all_files:
            module_id = get_module_id_from_path(file_path)
            # Check if any specified module matches
            for pattern in args.modules:
                if module_id.startswith(pattern):
                    filtered_files.append(file_path)
                    break
        all_files = filtered_files
        print(f"📋 Filtered to {len(all_files)} modules matching: {args.modules}")

    # Extract resources
    resources_by_module = {}
    extracted_count = 0
    skipped_count = 0

    for file_path in all_files:
        module_id = get_module_id_from_path(file_path)

        resources = extract_resources_from_file(file_path)

        if resources:
            resources_by_module[module_id] = resources
            total_items = sum(len(v) for v in resources.items())
            print(f"  ✅ {module_id}: {total_items} resources")
            extracted_count += 1
        else:
            skipped_count += 1

    # Create output structure
    output = {
        'version': '1.0',
        'generated_at': datetime.now().strftime('%Y-%m-%d'),
        'resources': resources_by_module
    }

    # Write YAML
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8') as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"\n📊 Extraction Summary:")
    print(f"  ✅ Extracted: {extracted_count} modules")
    print(f"  ⏭️  Skipped: {skipped_count} modules (no resources)")
    print(f"  📄 Output: {args.output}")
    print(f"\n✅ Extraction complete!")


if __name__ == '__main__':
    main()
