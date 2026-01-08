#!/usr/bin/env python3
"""
Generate A2 external resources based on Dobra Forma and ULP mappings.

This script creates resource mappings for all A2 modules using:
1. Dobra Forma chapter references (from DOBRA-FORMA-MAPPING.md)
2. ULP podcast episodes (from existing database)
"""

import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESOURCES_FILE = PROJECT_ROOT / 'docs' / 'resources' / 'external_resources.yaml'
DOBRA_FORMA_BASE = 'https://opentext.ku.edu/dobraforma/chapter'

# A2 Module → Dobra Forma Chapter Mapping
# Based on DOBRA-FORMA-MAPPING.md
A2_DOBRA_FORMA_MAPPING = {
    'a2-01-the-dative-i-pronouns': ['15-1', '15-2'],  # Personal Pronouns Dative
    'a2-02-the-dative-ii-nouns': ['11-1', '11-2', '11-3', '11-4'],  # Dative Case
    'a2-03-dative-verbs': ['11-1'],  # Dative with verbs
    'a2-04-the-instrumental-i-accompaniment': ['9-1', '9-4'],  # Instrumental intro
    'a2-05-the-instrumental-ii-means-and-tools': ['9-2'],  # Instrumental uses
    'a2-06-being-and-becoming': ['10-3'],  # Instrumental with бути, стати
    'a2-07-spatial-prepositions': ['4-1', '4-2'],  # Locative prepositions
    'a2-08-logical-prepositions': ['7-1', '7-2'],  # Genitive prepositions
    'a2-09-all-cases-practice': ['4-1', '5-1', '7-1', '9-1', '11-1'],  # All cases
    'a2-10-at-the-post-office-and-bank': [],  # Vocabulary-focused
    'a2-11-checkpoint-cases': [],  # Review module
    'a2-12-aspect-introduction': ['27-1'],  # Aspect introduction
    'a2-13-the-completed-past': ['27-2'],  # Aspect past tense
    'a2-14-future-plans-and-promises': ['27-4'],  # Aspect future
    'a2-15-aspect-morphology': ['27-3'],  # Aspectual pairs
    'a2-16-aspect-mastery-pairs': ['27-3'],  # More aspectual pairs
    'a2-17-possessive-sviy': ['12-1'],  # Possessive pronouns
    'a2-18-bigger-better-stronger': ['20-1', '20-2'],  # Comparative
    'a2-19-the-best-the-worst': ['20-3'],  # Superlative
    'a2-20-preferences-and-choices': ['20-1'],  # Comparative usage
    'a2-21-numerals-and-nouns': ['6-1', '6-2', '6-3'],  # Genitive with numbers
    'a2-22-if-i-were': [],  # Conditional (not in Dobra Forma basics)
    'a2-23-complete-imperative': ['29-1', '29-2', '29-3'],  # Imperatives
    'a2-24-smart-shopping': [],  # Vocabulary
    'a2-25-checkpoint-aspect-comparison': ['27-1', '27-2', '27-3', '27-4'],  # Aspect review
    'a2-26-telling-stories': ['24-1'],  # Past tense
    'a2-27-because-and-although': [],  # Conjunctions (advanced)
    'a2-28-she-said-that': [],  # Reported speech (advanced)
    'a2-29-i-think-that': [],  # Subordinate clauses
    'a2-30-i-feel-like': [],  # Expressions
    'a2-31-in-order-to': [],  # Purpose clauses
    'a2-32-which-one': [],  # Relative clauses
    'a2-33-time-clauses': [],  # Temporal clauses
    'a2-34-at-the-doctor': [],  # Vocabulary
    'a2-35-checkpoint': [],  # Review
    'a2-36-basic-motion-prefixes': ['28-3'],  # Motion verbs with prefixes
    'a2-37-advanced-motion-prefixes': ['28-3'],  # More motion prefixes
    'a2-38-action-verb-prefixes': ['27-1'],  # Perfective prefixes
    'a2-39-adjective-suffixes-qualities': ['16-1'],  # Adjectives
    'a2-40-adj-suffixes': ['16-1', '16-2'],  # More adjectives
    'a2-41-root-families-i': [],  # Word formation (advanced)
    'a2-42-root-families-ii': [],  # Word formation
    'a2-43-wf-mastery': [],  # Word formation mastery
    'a2-44-checkpoint-word-formation': [],  # Review
    'a2-45-food-and-cooking': [],  # Vocabulary
    'a2-46-home-and-furniture': [],  # Vocabulary
    'a2-47-nature-and-weather': [],  # Vocabulary
    'a2-48-emotions-personality': [],  # Vocabulary
    'a2-49-work-professions': [],  # Vocabulary
    'a2-50-technology-media': [],  # Vocabulary
    'a2-51-hobbies-leisure': [],  # Vocabulary
    'a2-52-education-learning': [],  # Vocabulary
    'a2-53-shopping-services': [],  # Vocabulary
    'a2-54-sports-fitness': [],  # Vocabulary
    'a2-55-health-body': [],  # Vocabulary
    'a2-56-checkpoint-vocabulary': [],  # Review
    'a2-57-grammar-review': [],  # Review
    'a2-58-final-review': [],  # Review
}

def create_dobra_forma_resource(chapter_num: str) -> dict:
    """Create a Dobra Forma website resource entry."""
    # Map chapter numbers to titles (simplified - could be enhanced)
    chapter_titles = {
        '4-1': 'Locative Case (в and у)',
        '4-2': 'Locative Case (в, у and на)',
        '5-1': 'Accusative Case (Inanimate)',
        '6-1': 'Genitive with Quantity (Masculine Plural)',
        '6-2': 'Genitive with Quantity (Feminine/Neuter)',
        '6-3': 'Genitive with Quantity (Exceptions)',
        '7-1': 'Genitive after Prepositions (з, до, в/у)',
        '7-2': 'Genitive after Prepositions (біля, після, для, без)',
        '9-1': 'Instrumental Case (Intro)',
        '9-2': 'Instrumental Case (Other Endings)',
        '9-4': 'Instrumental Case (зі and із)',
        '10-3': 'Instrumental with працювати, бути, стати',
        '11-1': 'Dative Case (Feminine)',
        '11-2': 'Dative Case (Masculine/Neuter)',
        '11-3': 'Dative Case (Animate Masculine)',
        '11-4': 'Dative Case (Plural)',
        '12-1': 'Possessive Pronouns (мій, твій, чий)',
        '15-1': 'Personal Pronouns (Dative Forms)',
        '15-2': 'Personal Pronouns (Dative Indirect Object)',
        '16-1': 'Adjectives (Gender and Number)',
        '16-2': 'Soft-Stem Adjectives',
        '20-1': 'Comparative Degree',
        '20-2': 'Comparative Exceptions',
        '20-3': 'Superlative Degree',
        '24-1': 'Past Tense',
        '27-1': 'Verbal Aspect (Introduction)',
        '27-2': 'Verbal Aspect (Past Tense)',
        '27-3': 'Verbal Aspect (Aspectual Pairs)',
        '27-4': 'Verbal Aspect (Future Tense)',
        '28-3': 'Verbs of Motion (Prefixed)',
        '29-1': 'Imperatives (Читай Type)',
        '29-2': 'Imperatives (Пиши Type)',
        '29-3': 'Imperatives (Exceptions)',
    }
    
    title = f"Dobra Forma {chapter_num}: {chapter_titles.get(chapter_num, 'Grammar Reference')}"
    url = f"{DOBRA_FORMA_BASE}/{chapter_num}/"
    
    return {
        'title': title,
        'url': url,
        'relevance': 'high',
        'source': 'University of Kansas'
    }

def main():
    print("🔄 Generating A2 external resources\n")
    
    # Load existing resources
    with open(RESOURCES_FILE, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    resources = data.get('resources', {})
    added_count = 0
    updated_count = 0
    
    # Add Dobra Forma resources for each A2 module
    for module_id, chapters in A2_DOBRA_FORMA_MAPPING.items():
        if not chapters:
            continue
        
        if module_id not in resources:
            resources[module_id] = {}
            added_count += 1
        else:
            updated_count += 1
        
        # Add websites section if not exists
        if 'websites' not in resources[module_id]:
            resources[module_id]['websites'] = []
        
        # Add Dobra Forma chapters
        for chapter in chapters:
            dobra_resource = create_dobra_forma_resource(chapter)
            
            # Check if already exists
            exists = any(
                r.get('url') == dobra_resource['url']
                for r in resources[module_id]['websites']
            )
            
            if not exists:
                resources[module_id]['websites'].append(dobra_resource)
    
    # Save updated resources
    data['resources'] = dict(sorted(resources.items()))
    data['version'] = '2.1'
    data['generated_at'] = '2026-01-07'
    
    with open(RESOURCES_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Added Dobra Forma resources to {added_count} new A2 modules")
    print(f"✅ Updated {updated_count} existing A2 modules")
    print(f"\n📊 Total A2 modules with resources: {added_count + updated_count}")
    
    # Show sample
    print("\n📋 Sample A2 resources:")
    for module_id in list(A2_DOBRA_FORMA_MAPPING.keys())[:3]:
        if module_id in resources and 'websites' in resources[module_id]:
            count = len(resources[module_id]['websites'])
            print(f"   {module_id}: {count} resources")

if __name__ == '__main__':
    main()
