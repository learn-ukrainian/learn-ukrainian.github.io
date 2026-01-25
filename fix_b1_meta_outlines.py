#!/usr/bin/env python3
"""
Fix B1 meta.yaml content_outline sections to match template structures.
"""

import yaml
from pathlib import Path

# Modules that need fixing
GRAMMAR_MODULES = [
    "06-aspect-complete-system",
    "11-aspect-in-imperatives",
    "12-aspect-pairs-essential-40",
    "13-work-week-aspect-in-action",
    "14-aspect-integration-practice",
    "16-motion-verbs-full-system",
    "17-motion-coming-going",
    "18-motion-passing-crossing",
    "19-motion-starting-returning",
    "20-motion-approaching-departing",
    "21-motion-figurative-uses",
    "22-motion-full-prefix-integration",
    "23-motion-patterns-other-verbs",
    "24-motion-practice-integration",
]

CHECKPOINT_MODULES = [
    "15-checkpoint-aspect-mastery",
    "25-checkpoint-motion-verbs",
]

def get_grammar_outline(title: str, topic_points: list) -> list:
    """Generate TTT outline for grammar modules."""
    return [
        {
            "section": "Тест",
            "words": 150,
            "points": [f"Diagnostic contrast for {title.lower()}", "No explanation, just observation", "Engage critical thinking"]
        },
        {
            "section": "Пояснення",
            "words": 800,
            "points": topic_points
        },
        {
            "section": "Практика",
            "words": 400,
            "points": ["Decision-making framework", "Comparative examples", "Common mistakes section"]
        },
        {
            "section": "Діалоги",
            "words": 150,
            "points": ["5-6 authentic dialogues", "Grammar in natural context", "Various situations"]
        }
    ]

def get_checkpoint_outline(phase_name: str, module_range: str) -> list:
    """Generate outline for checkpoint modules."""
    return [
        {
            "section": "Огляд",
            "words": 150,
            "points": [f"Comprehensive review of M{module_range}", "Skill groups from phase", "Self-assessment preview"]
        },
        {
            "section": "Skill Sections",
            "words": 800,
            "points": ["Model examples for each skill", "Scaffolded practice", "Self-check criteria"]
        },
        {
            "section": "Інтеграційне завдання",
            "words": 150,
            "points": ["Extended integrated practice", "All skills combined", "Production task"]
        },
        {
            "section": "Підсумок",
            "words": 100,
            "points": ["Readiness checklist", "Next phase preview"]
        }
    ]

# Topic-specific points for each grammar module
GRAMMAR_TOPICS = {
    "06-aspect-complete-system": ["Complete aspect system overview", "НДВ vs ДВ functions", "Usage contexts with examples", "Aspect in different tenses"],
    "11-aspect-in-imperatives": ["НДВ commands (process, permission)", "ДВ commands (result, instruction)", "Polite requests", "Negative commands"],
    "12-aspect-pairs-essential-40": ["40 essential aspect pairs", "Formation patterns (prefix, suffix)", "Suppletive pairs", "Bi-aspectual verbs"],
    "13-work-week-aspect-in-action": ["Aspect in workplace context", "Plans and tasks (ДВ)", "Progress reports (НДВ)", "Weekly communication patterns"],
    "14-aspect-integration-practice": ["Temporal conjunctions with aspect", "Narratives with mixed aspects", "Complex cases", "Production tasks"],
    "16-motion-verbs-full-system": ["Unidirectional vs multidirectional", "14 motion verb pairs", "Contrastive analysis", "Less common pairs"],
    "17-motion-coming-going": ["Prefix при- (arrival)", "Prefix ви- (exit)", "Prefix в-/у- (entry)", "Contrastive practice"],
    "18-motion-passing-crossing": ["Prefix пере- (crossing)", "Prefix про- (passing through)", "Prefix об- (going around)", "Path prepositions"],
    "19-motion-starting-returning": ["Prefix по- (start of motion)", "Prefix за- (stop by)", "Prefix роз- (dispersal)", "Beginning vs returning"],
    "20-motion-approaching-departing": ["Prefix під- (approach)", "Prefix від- (departure)", "Prefix до- (reaching)", "Directional nuances"],
    "21-motion-figurative-uses": ["Abstract motion (час іде)", "Metaphorical uses", "Idiomatic expressions", "Literary contexts"],
    "22-motion-full-prefix-integration": ["All 10 prefixes integrated", "Complex motion descriptions", "Prefix combinations", "Natural narratives"],
    "23-motion-patterns-other-verbs": ["Motion patterns with non-motion verbs", "Productive prefixes", "Analogical extensions", "Semantic patterns"],
    "24-motion-practice-integration": ["Extended practice", "All motion patterns", "Production tasks", "Readiness for checkpoint"],
}

def fix_meta_file(slug: str, is_checkpoint: bool = False):
    """Fix a single meta.yaml file."""
    meta_path = Path(f"curriculum/l2-uk-en/b1/meta/{slug}.yaml")

    if not meta_path.exists():
        print(f"⚠️  Skipping {slug} - file not found")
        return

    # Load existing meta
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = yaml.safe_load(f)

    # Fix word_target
    if is_checkpoint:
        meta['word_target'] = 1200
    else:
        meta['word_target'] = 1500

    # Fix content_outline
    if is_checkpoint:
        # Extract module range from title or slug
        if "aspect" in slug:
            module_range = "06-14"
            phase = "B1.1 Aspect"
        else:  # motion
            module_range = "16-24"
            phase = "B1.2 Motion"
        meta['content_outline'] = get_checkpoint_outline(phase, module_range)
    else:
        # Get topic points from dictionary or use generic
        topic_points = GRAMMAR_TOPICS.get(slug, ["Grammar explanation", "Usage contexts", "Examples and tables"])
        title = meta.get('title', '')
        meta['content_outline'] = get_grammar_outline(title, topic_points)

    # Write back
    with open(meta_path, 'w', encoding='utf-8') as f:
        yaml.dump(meta, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"✅ Fixed {slug}")

def main():
    print("Fixing B1 meta.yaml files...\n")

    print("Grammar modules (14):")
    for slug in GRAMMAR_MODULES:
        fix_meta_file(slug, is_checkpoint=False)

    print("\nCheckpoint modules (2):")
    for slug in CHECKPOINT_MODULES:
        fix_meta_file(slug, is_checkpoint=True)

    print(f"\n✅ Fixed 16 meta.yaml files")
    print("\nNext: Run audit to verify fixes")

if __name__ == "__main__":
    main()
