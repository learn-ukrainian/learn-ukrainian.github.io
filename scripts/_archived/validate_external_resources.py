#!/usr/bin/env python3
"""
Validate external resources YAML structure and content.

Checks for:
- Required fields
- Valid relevance levels
- Duplicate URLs
- Module IDs exist in curriculum
- Podcast episode IDs exist in database
- Optional URL health checks

Usage:
    .venv/bin/python scripts/validate_external_resources.py \
        docs/resources/external_resources.yaml

    # With URL health check (slow)
    .venv/bin/python scripts/validate_external_resources.py \
        docs/resources/external_resources.yaml \
        --check-urls
"""

import argparse
import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


VALID_RELEVANCE = {'high', 'medium', 'low'}
VALID_RESOURCE_TYPES = {'youtube', 'podcasts', 'articles', 'books', 'websites'}

# Required fields per resource type
REQUIRED_FIELDS = {
    'youtube': {'title', 'url', 'channel', 'relevance'},
    'podcasts': {'episode_id', 'title', 'url', 'relevance'},
    'articles': {'title', 'url', 'source', 'relevance'},
    'books': {'title', 'author', 'relevance'},
    'websites': {'title', 'url', 'source', 'relevance'}
}


class ValidationError:
    """Represents a validation error."""
    def __init__(self, module_id: str, resource_type: str, message: str):
        self.module_id = module_id
        self.resource_type = resource_type
        self.message = message

    def __str__(self):
        return f"[{self.module_id}] {self.resource_type}: {self.message}"


class ValidationWarning:
    """Represents a validation warning."""
    def __init__(self, module_id: str, resource_type: str, message: str):
        self.module_id = module_id
        self.resource_type = resource_type
        self.message = message

    def __str__(self):
        return f"[{self.module_id}] {self.resource_type}: {self.message}"


class ExternalResourcesValidator:
    """Validates external resources YAML."""

    def __init__(self, resources_path: Path, curriculum_path: Path, podcast_db_path: Path):
        self.resources_path = resources_path
        self.curriculum_path = curriculum_path
        self.podcast_db_path = podcast_db_path

        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationWarning] = []

        # Load data
        self.resources_data = self._load_yaml(resources_path)
        self.valid_modules = self._load_valid_modules()
        self.valid_episode_ids = self._load_valid_episode_ids()

    def _load_yaml(self, path: Path) -> Dict:
        """Load YAML file."""
        try:
            with path.open('r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML syntax: {e}")
            exit(1)

    def _load_valid_modules(self) -> Set[str]:
        """Load all valid module IDs from curriculum."""
        valid = set()
        levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']

        for level in levels:
            level_dir = self.curriculum_path / level
            if not level_dir.exists():
                continue

            for md_file in level_dir.glob('*.md'):
                # Extract module_id from filename
                # Example: 07-questions-and-negation.md -> a1-07-questions-and-negation
                filename = md_file.stem
                module_id = f"{level}-{filename}"
                valid.add(module_id)

        return valid

    def _load_valid_episode_ids(self) -> Set[str]:
        """Load all valid podcast episode IDs from database."""
        if not self.podcast_db_path.exists():
            return set()

        try:
            with self.podcast_db_path.open('r', encoding='utf-8') as f:
                episodes = json.load(f)
                # podcast_db.json is an array of episodes
                if isinstance(episodes, list):
                    return {ep.get('id') for ep in episodes if ep.get('id')}
                # Legacy format: dict with 'episodes' key
                elif isinstance(episodes, dict):
                    return set(episodes.get('episodes', {}).keys())
                return set()
        except Exception as e:
            print(f"⚠️  Warning: Could not load podcast DB: {e}")
            return set()

    def validate_required_fields(self, module_id: str, resource_type: str, resource: Dict):
        """Check that all required fields are present."""
        required = REQUIRED_FIELDS.get(resource_type, set())
        missing = required - set(resource.keys())

        if missing:
            self.errors.append(ValidationError(
                module_id,
                resource_type,
                f"Missing required fields: {', '.join(missing)}"
            ))

    def validate_relevance(self, module_id: str, resource_type: str, resource: Dict):
        """Check that relevance is valid."""
        relevance = resource.get('relevance')
        if relevance and relevance not in VALID_RELEVANCE:
            self.errors.append(ValidationError(
                module_id,
                resource_type,
                f"Invalid relevance '{relevance}' (must be: {', '.join(VALID_RELEVANCE)})"
            ))

    def validate_episode_id(self, module_id: str, resource: Dict):
        """Check that podcast episode_id exists in database."""
        episode_id = resource.get('episode_id')
        if episode_id and episode_id not in self.valid_episode_ids:
            self.errors.append(ValidationError(
                module_id,
                'podcasts',
                f"Episode ID '{episode_id}' not found in podcast database"
            ))

    def validate_youtube_url(self, module_id: str, resource: Dict):
        """Check YouTube URL format."""
        url = resource.get('url', '')
        if not url:
            return

        # Check standard YouTube URL patterns
        patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/'
        ]

        if not any(re.search(pattern, url) for pattern in patterns):
            self.warnings.append(ValidationWarning(
                module_id,
                'youtube',
                f"Non-standard YouTube URL format: {url}"
            ))

    def validate_duplicate_urls(self, module_id: str, resources: Dict):
        """Check for duplicate URLs within a module."""
        seen_urls = defaultdict(list)

        for resource_type in ['youtube', 'podcasts', 'articles', 'books', 'websites']:
            items = resources.get(resource_type, [])
            for item in items:
                url = item.get('url')
                if url:
                    seen_urls[url].append(resource_type)

        # Report duplicates
        for url, types in seen_urls.items():
            if len(types) > 1:
                self.errors.append(ValidationError(
                    module_id,
                    'all',
                    f"Duplicate URL in {', '.join(types)}: {url}"
                ))

    def validate_high_relevance_description(self, module_id: str, resource_type: str, resource: Dict):
        """Warn if high-relevance resource lacks description."""
        if resource.get('relevance') == 'high':
            # Check for description field (or match_reason for podcasts)
            has_desc = resource.get('description') or resource.get('match_reason')
            if not has_desc and resource_type in ['articles', 'websites']:
                self.warnings.append(ValidationWarning(
                    module_id,
                    resource_type,
                    f"High-relevance resource lacks description: {resource.get('title', 'unknown')}"
                ))

    def validate_resource_count(self, module_id: str, resource_type: str, resources: List[Dict]):
        """Warn if too many resources of one type."""
        if len(resources) > 10:
            self.warnings.append(ValidationWarning(
                module_id,
                resource_type,
                f"More than 10 resources ({len(resources)}) - consider reducing"
            ))

    def validate_module_exists(self, module_id: str):
        """Check that module ID exists in curriculum."""
        if module_id not in self.valid_modules:
            self.errors.append(ValidationError(
                module_id,
                'module',
                "Module ID does not exist in curriculum"
            ))

    def validate(self) -> bool:
        """
        Run all validation checks.

        Returns True if valid (no errors), False otherwise.
        """
        resources = self.resources_data.get('resources', {})

        for module_id, module_resources in resources.items():
            # Validate module exists
            self.validate_module_exists(module_id)

            # Validate duplicate URLs
            self.validate_duplicate_urls(module_id, module_resources)

            # Validate each resource type
            for resource_type in VALID_RESOURCE_TYPES:
                items = module_resources.get(resource_type, [])

                # Check resource count
                if items:
                    self.validate_resource_count(module_id, resource_type, items)

                # Validate each resource
                for resource in items:
                    self.validate_required_fields(module_id, resource_type, resource)
                    self.validate_relevance(module_id, resource_type, resource)
                    self.validate_high_relevance_description(module_id, resource_type, resource)

                    # Type-specific validations
                    if resource_type == 'podcasts':
                        self.validate_episode_id(module_id, resource)
                    elif resource_type == 'youtube':
                        self.validate_youtube_url(module_id, resource)

        return len(self.errors) == 0

    def report(self):
        """Print validation report."""
        print("\n" + "="*60)
        print("📋 Validation Report")
        print("="*60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        print(f"\n{'='*60}")
        print(f"Summary: {len(self.errors)} errors, {len(self.warnings)} warnings")

        if self.errors:
            print("❌ Validation FAILED")
        else:
            print("✅ Validation PASSED")

        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Validate external resources YAML"
    )
    parser.add_argument(
        'resources_file',
        type=Path,
        help="Path to external_resources.yaml"
    )
    parser.add_argument(
        '--curriculum',
        type=Path,
        default=Path('curriculum/l2-uk-en'),
        help="Path to curriculum directory (default: curriculum/l2-uk-en)"
    )
    parser.add_argument(
        '--podcast-db',
        type=Path,
        default=Path('docs/resources/podcasts/podcast_db.json'),
        help="Path to podcast database (default: docs/resources/podcasts/podcast_db.json)"
    )
    parser.add_argument(
        '--check-urls',
        action='store_true',
        help="Check URL health (slow - makes HTTP requests)"
    )

    args = parser.parse_args()

    if not args.resources_file.exists():
        print(f"❌ Error: Resources file not found: {args.resources_file}")
        return 1

    print(f"🔍 Validating: {args.resources_file}")
    print(f"📚 Curriculum: {args.curriculum}")
    print(f"🎧 Podcast DB: {args.podcast_db}")

    # Create validator
    validator = ExternalResourcesValidator(
        args.resources_file,
        args.curriculum,
        args.podcast_db
    )

    # Run validation
    is_valid = validator.validate()

    # Print report
    validator.report()

    # TODO: Implement --check-urls if flag is set
    if args.check_urls:
        print("⚠️  URL health check not yet implemented")

    # Exit with appropriate code
    return 0 if is_valid else 1


if __name__ == '__main__':
    exit(main())
