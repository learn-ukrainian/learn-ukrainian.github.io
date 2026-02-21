#!/usr/bin/env python3
"""
⚠️  DEPRECATED - DO NOT USE IN BUILD PIPELINE

This script is no longer used. Resources are now injected directly during
MDX/JSON generation from external_resources.yaml, not written to markdown files.

The new architecture (Issue #354):
- generate_mdx.py loads external_resources.yaml and injects resources at build time
- generate_json.py adds external_resources field to JSON output
- Markdown files no longer contain [!resources] sections (single source of truth: YAML)

This script is kept for reference/debugging only and will be deleted in future cleanup.

Migration completed: Jan 2, 2026
See: Issue #354 - Refactor Resources from Markdown Architecture

---

OLD DOCUMENTATION (for reference):

Generate [!resources] markdown sections from YAML.

Reads external_resources.yaml and regenerates [!resources] callout blocks
in curriculum markdown files with consistent formatting and sorting.

Usage:
    # Dry run (show changes without writing)
    .venv/bin/python scripts/generate_resource_sections.py \
        --input docs/resources/external_resources.yaml \
        --curriculum curriculum/l2-uk-en/ \
        --dry-run

    # Execute (write files)
    .venv/bin/python scripts/generate_resource_sections.py \
        --input docs/resources/external_resources.yaml \
        --curriculum curriculum/l2-uk-en/
"""

import argparse
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Emoji icons per resource type
RESOURCE_ICONS = {
    'podcasts': '🎧',
    'youtube': '📺',
    'articles': '📖',
    'books': '📚',
    'websites': '🌐'
}

# Resource type display names
RESOURCE_NAMES = {
    'podcasts': 'Podcasts',
    'youtube': 'YouTube',
    'articles': 'Articles',
    'books': 'Books',
    'websites': 'Websites'
}

# Relevance priority (for sorting)
RELEVANCE_PRIORITY = {'high': 3, 'medium': 2, 'low': 1}


def load_yaml(file_path: Path) -> Dict:
    """Load YAML file."""
    with file_path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_module_file_path(module_id: str, curriculum_path: Path) -> Optional[Path]:
    """
    Find markdown file for module_id.

    module_id format: {level}-{number}-{slug}
    Example: a1-07-questions-and-negation
    """
    # Extract level from module_id
    parts = module_id.split('-', 1)
    if len(parts) < 2:
        return None

    level = parts[0]
    filename = parts[1] + '.md'

    # Check level directory
    level_dir = curriculum_path / level
    if not level_dir.exists():
        return None

    # Find file
    file_path = level_dir / filename
    if file_path.exists():
        return file_path

    return None


def sort_resources(resources: List[Dict]) -> List[Dict]:
    """
    Sort resources by relevance (high first) then title (alphabetical).

    Returns sorted copy.
    """
    def sort_key(resource):
        relevance = resource.get('relevance', 'low')
        priority = RELEVANCE_PRIORITY.get(relevance, 0)
        title = resource.get('title', '')
        return (-priority, title.lower())  # Negative priority for descending order

    return sorted(resources, key=sort_key)


def format_podcast_entry(podcast: Dict) -> str:
    """Format a podcast resource as markdown list item."""
    title = podcast.get('title', 'Unknown')
    url = podcast.get('url', '')
    match_reason = podcast.get('match_reason', '')
    description = podcast.get('description', match_reason)

    # Format: - [Title](URL) — Description
    if description:
        return f"- [{title}]({url}) — {description}"
    else:
        return f"- [{title}]({url})"


def format_youtube_entry(video: Dict) -> str:
    """Format a YouTube resource as markdown list item."""
    title = video.get('title', 'Unknown')
    url = video.get('url', '')
    channel = video.get('channel', '')
    description = video.get('description', channel)

    # Format: - [Title](URL) — Channel/Description
    if description:
        return f"- [{title}]({url}) — {description}"
    else:
        return f"- [{title}]({url})"


def format_article_entry(article: Dict) -> str:
    """Format an article resource as markdown list item."""
    title = article.get('title', 'Unknown')
    url = article.get('url', '')
    source = article.get('source', '')
    description = article.get('description', source)

    # Format: - [Title](URL) — Description/Source
    if description:
        return f"- [{title}]({url}) — {description}"
    else:
        return f"- [{title}]({url})"


def format_book_entry(book: Dict) -> str:
    """Format a book resource as markdown list item."""
    title = book.get('title', 'Unknown')
    author = book.get('author', 'Unknown')
    pages = book.get('pages', '')
    description = book.get('description', '')

    # Format: - Title by Author (pages: X-Y) — Description
    parts = [f"{title} by {author}"]
    if pages:
        parts.append(f"(pages: {pages})")
    if description:
        parts.append(f"— {description}")

    return f"- {' '.join(parts)}"


def format_website_entry(website: Dict) -> str:
    """Format a website resource as markdown list item."""
    title = website.get('title', 'Unknown')
    url = website.get('url', '')
    source = website.get('source', '')
    description = website.get('description', source)

    # Format: - [Title](URL) — Description/Source
    if description:
        return f"- [{title}]({url}) — {description}"
    else:
        return f"- [{title}]({url})"


def generate_resources_section(module_resources: Dict) -> str:
    """
    Generate [!resources] callout block from module resources.

    Returns formatted markdown string.
    """
    lines = []
    lines.append("> [!resources] 🔗 External Resources")
    lines.append(">")

    # Resource types in order
    resource_types = ['podcasts', 'youtube', 'articles', 'books', 'websites']

    for resource_type in resource_types:
        items = module_resources.get(resource_type, [])
        if not items:
            continue

        # Sort items
        sorted_items = sort_resources(items)

        # Add section header
        icon = RESOURCE_ICONS[resource_type]
        name = RESOURCE_NAMES[resource_type]
        lines.append(f"> **{icon} {name}:**")

        # Format each item
        for item in sorted_items:
            if resource_type == 'podcasts':
                formatted = format_podcast_entry(item)
            elif resource_type == 'youtube':
                formatted = format_youtube_entry(item)
            elif resource_type == 'articles':
                formatted = format_article_entry(item)
            elif resource_type == 'books':
                formatted = format_book_entry(item)
            elif resource_type == 'websites':
                formatted = format_website_entry(item)
            else:
                continue

            lines.append(f"> {formatted}")

        # Add blank line between sections
        lines.append(">")

    # Remove trailing blank line
    if lines[-1] == ">":
        lines.pop()

    return '\n'.join(lines)


def find_resources_section(content: str) -> Optional[Tuple[int, int]]:
    """
    Find [!resources] section in markdown content.

    Returns (start_idx, end_idx) or None if not found.
    """
    # Find start of resources block
    start_match = re.search(r'> \[!resources\]', content)
    if not start_match:
        return None

    start_idx = start_match.start()

    # Find end of resources block (first line not starting with >)
    lines = content[start_idx:].split('\n')
    end_offset = 0
    for i, line in enumerate(lines):
        # If we hit a non-'>' line or another section, that's the end
        if line.strip() and not line.strip().startswith('>'):
            end_offset = sum(len(l) + 1 for l in lines[:i])
            break
    else:
        # Resources block goes to end of file
        end_offset = len(content[start_idx:])

    end_idx = start_idx + end_offset

    return (start_idx, end_idx)


def replace_resources_section(content: str, new_section: str) -> str:
    """
    Replace existing [!resources] section with new one.

    If section doesn't exist, appends to end of file.
    """
    section_location = find_resources_section(content)

    if section_location:
        start_idx, end_idx = section_location
        # Replace existing section
        return content[:start_idx] + new_section + '\n' + content[end_idx:]
    else:
        # Append to end of file
        if not content.endswith('\n'):
            content += '\n'
        content += '\n' + new_section + '\n'
        return content


def generate_for_module(module_id: str, module_resources: Dict, curriculum_path: Path, dry_run: bool = False) -> bool:
    """
    Generate resources section for a single module.

    Returns True if successful, False otherwise.
    """
    # Find module file
    file_path = get_module_file_path(module_id, curriculum_path)
    if not file_path:
        print(f"  ⚠️  Module file not found: {module_id}")
        return False

    # Read current content
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ❌ Error reading {file_path}: {e}")
        return False

    # Generate new section
    new_section = generate_resources_section(module_resources)

    # Replace section
    new_content = replace_resources_section(content, new_section)

    # Check if content changed
    if new_content == content:
        print(f"  ⏭️  No changes: {module_id}")
        return True

    if dry_run:
        print(f"  🔄 Would update: {module_id}")
        print(f"     Preview:")
        for line in new_section.split('\n')[:5]:
            print(f"       {line}")
        if len(new_section.split('\n')) > 5:
            print(f"       ... ({len(new_section.split('\n')) - 5} more lines)")
        return True
    else:
        # Write updated content
        try:
            file_path.write_text(new_content, encoding='utf-8')
            print(f"  ✅ Updated: {module_id}")
            return True
        except Exception as e:
            print(f"  ❌ Error writing {file_path}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate [!resources] sections from YAML"
    )
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help="Path to external_resources.yaml"
    )
    parser.add_argument(
        '--curriculum',
        type=Path,
        required=True,
        help="Path to curriculum directory (e.g., curriculum/l2-uk-en/)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be changed without writing files"
    )
    parser.add_argument(
        '--modules',
        nargs='*',
        help="Optional: specific module IDs to generate (e.g., a1-07 b1-06)"
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ Error: Input file not found: {args.input}")
        return 1

    if not args.curriculum.exists():
        print(f"❌ Error: Curriculum directory not found: {args.curriculum}")
        return 1

    print(f"📝 Generating resource sections...")
    print(f"  📄 Input: {args.input}")
    print(f"  📚 Curriculum: {args.curriculum}")
    if args.dry_run:
        print(f"  🔍 Mode: DRY RUN (no files will be modified)")
    print()

    # Load resources
    data = load_yaml(args.input)
    resources = data.get('resources', {})

    # Filter modules if specified
    if args.modules:
        filtered = {}
        for module_id in resources.keys():
            if any(module_id.startswith(pattern) for pattern in args.modules):
                filtered[module_id] = resources[module_id]
        resources = filtered
        print(f"📋 Filtered to {len(resources)} modules matching: {args.modules}\n")

    # Generate for each module
    updated = 0
    skipped = 0
    errors = 0

    for module_id, module_resources in resources.items():
        success = generate_for_module(module_id, module_resources, args.curriculum, args.dry_run)
        if success:
            if "Would update" in str(success) or "Updated" in str(success):
                updated += 1
            else:
                skipped += 1
        else:
            errors += 1

    # Summary
    print(f"\n📊 Generation Summary:")
    print(f"  ✅ Updated: {updated}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Errors: {errors}")
    print(f"\n{'🔍 Dry run complete!' if args.dry_run else '✅ Generation complete!'}")

    return 0


if __name__ == '__main__':
    exit(main())
