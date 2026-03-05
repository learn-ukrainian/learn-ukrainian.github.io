#!/usr/bin/env python3
"""Fix B2 template activity hints and generic vocabulary in plan files.

Replaces the boilerplate activity pattern (reading+essay-response+true-false)
with module-specific activity hints derived from each plan's content_outline
and grammar fields.

Replaces generic vocabulary (термін/поняття/процес/метод) with the first 4
terms found in the plan's content_outline points.
"""
import yaml
import re
import sys
from pathlib import Path

PLAN_DIR = Path("curriculum/l2-uk-en/plans/b2")

# Template pattern to detect
TEMPLATE_ACTIVITIES = [
    {"type": "reading", "focus": "Аналіз тексту", "items": 4},
    {"type": "essay-response", "focus": "Практичне застосування"},
    {"type": "true-false", "focus": "Перевірка розуміння", "items": 8},
]

GENERIC_VOCAB = ["термін (term)", "поняття (concept)", "процес (process)", "метод (method)"]

# Activity type templates by plan focus
ACTIVITY_TEMPLATES = {
    "grammar": [
        {"type": "quiz", "focus_template": "Identify {grammar_topic} in sentences", "items": 12},
        {"type": "fill-in", "focus_template": "Complete sentences using {grammar_topic}", "items": 10},
        {"type": "match-up", "focus_template": "Match {section_2} examples to categories", "items": 12},
        {"type": "error-correction", "focus_template": "Find and fix errors in {grammar_topic}", "items": 8},
        {"type": "group-sort", "focus_template": "Classify examples by {section_3}", "items": 12},
        {"type": "essay-response", "focus_template": "Write paragraph using {grammar_topic} correctly"},
    ],
    "phraseology": [
        {"type": "match-up", "focus_template": "Match idioms to their meanings", "items": 15},
        {"type": "group-sort", "focus_template": "Classify idioms by {section_2}", "items": 12},
        {"type": "fill-in", "focus_template": "Complete sentences with the correct idiom", "items": 10},
        {"type": "quiz", "focus_template": "Choose the correct meaning of each idiom", "items": 12},
        {"type": "error-correction", "focus_template": "Fix incorrect idiom usage", "items": 8},
        {"type": "essay-response", "focus_template": "Use 5+ idioms in a coherent paragraph"},
    ],
    "vocabulary": [
        {"type": "match-up", "focus_template": "Match terms to definitions", "items": 15},
        {"type": "group-sort", "focus_template": "Sort vocabulary by {section_2}", "items": 12},
        {"type": "fill-in", "focus_template": "Complete sentences with domain vocabulary", "items": 10},
        {"type": "quiz", "focus_template": "Choose the correct term for each context", "items": 12},
        {"type": "fill-in", "focus_template": "Use terms in professional context", "items": 8},
        {"type": "essay-response", "focus_template": "Write using 8+ domain-specific terms"},
    ],
    "style": [
        {"type": "match-up", "focus_template": "Match text samples to register types", "items": 12},
        {"type": "group-sort", "focus_template": "Classify features by {section_2}", "items": 12},
        {"type": "fill-in", "focus_template": "Rewrite sentences in target register", "items": 10},
        {"type": "quiz", "focus_template": "Identify register of text samples", "items": 12},
        {"type": "error-correction", "focus_template": "Fix register-inappropriate language", "items": 8},
        {"type": "essay-response", "focus_template": "Write text in specified register style"},
    ],
    "skills": [
        {"type": "fill-in", "focus_template": "Complete {section_2} with appropriate language", "items": 10},
        {"type": "quiz", "focus_template": "Choose the best response for each scenario", "items": 12},
        {"type": "match-up", "focus_template": "Match situations to appropriate language", "items": 12},
        {"type": "error-correction", "focus_template": "Fix inappropriate register in {section_3}", "items": 8},
        {"type": "fill-in", "focus_template": "Complete professional text with correct forms", "items": 8},
        {"type": "essay-response", "focus_template": "Produce {section_2} for given scenario"},
    ],
    "checkpoint": [
        {"type": "quiz", "focus_template": "Review: {grammar_topic}", "items": 15},
        {"type": "fill-in", "focus_template": "Comprehensive: apply learned structures", "items": 12},
        {"type": "match-up", "focus_template": "Match concepts from covered modules", "items": 12},
        {"type": "group-sort", "focus_template": "Classify examples by module topic", "items": 10},
        {"type": "error-correction", "focus_template": "Find errors across all covered topics", "items": 10},
        {"type": "essay-response", "focus_template": "Integrative writing task combining all topics"},
    ],
}

# Map focus values to template keys
FOCUS_MAP = {
    "grammar": "grammar",
    "phraseology": "phraseology",
    "vocabulary": "vocabulary",
    "style": "style",
    "skills": "skills",
    "practical": "skills",
    "checkpoint": "checkpoint",
}


def has_template_activities(plan):
    hints = plan.get("activity_hints", [])
    if len(hints) != 3:
        return False
    types = [h.get("type") for h in hints]
    return types == ["reading", "essay-response", "true-false"]


def has_generic_vocab(plan):
    vocab = plan.get("vocabulary_hints", {}).get("required", [])
    if not vocab or len(vocab) < 4:
        return False
    first_four = [str(v).strip() for v in vocab[:4]]
    return all(any(g in f for g in ["термін (term)", "поняття (concept)", "процес (process)", "метод (method)"]) for f in first_four)


def extract_section_titles(plan):
    sections = []
    for s in plan.get("content_outline", []):
        title = s.get("section", "")
        # Clean: take the part before the parenthetical translation
        clean = re.sub(r'\s*\(.*?\)\s*$', '', title)
        clean = re.sub(r'^[^:]+:\s*', '', clean)  # Remove prefix before colon
        sections.append(clean.strip() if clean.strip() else title)
    return sections


def extract_grammar_summary(plan):
    grammar = plan.get("grammar", [])
    if grammar:
        return grammar[0] if isinstance(grammar[0], str) else str(grammar[0])
    # Fallback: use title
    return plan.get("title", "topic")


def extract_content_terms(plan):
    """Extract Ukrainian terms from content_outline points for vocabulary replacement."""
    terms = []
    term_pattern = re.compile(r"[а-яА-ЯіІїЇєЄґҐ''ʼ-]+(?:\s+[а-яА-ЯіІїЇєЄґҐ''ʼ-]+)?")

    for section in plan.get("content_outline", []):
        for point in section.get("points", []):
            # Look for terms in quotes or after colons
            # Pattern: 'term' or «term» or term (translation)
            quoted = re.findall(r"[«'']([^»'']+)[»'']", str(point))
            for q in quoted:
                q = q.strip()
                if len(q) > 2 and len(q) < 40 and re.search(r'[а-яіїєґ]', q):
                    if q not in terms and q not in ["а", "та", "не", "що", "як", "до", "на"]:
                        terms.append(q)

    return terms[:8]  # Return up to 8 terms


def generate_activities(plan):
    focus = plan.get("focus", "grammar")
    template_key = FOCUS_MAP.get(focus, "grammar")
    templates = ACTIVITY_TEMPLATES[template_key]

    sections = extract_section_titles(plan)
    grammar_topic = extract_grammar_summary(plan)

    activities = []
    for tmpl in templates:
        activity = {"type": tmpl["type"]}

        focus_str = tmpl["focus_template"]
        # Replace placeholders
        focus_str = focus_str.replace("{grammar_topic}", grammar_topic)
        if len(sections) > 1:
            focus_str = focus_str.replace("{section_2}", sections[1])
        else:
            focus_str = focus_str.replace("{section_2}", grammar_topic)
        if len(sections) > 2:
            focus_str = focus_str.replace("{section_3}", sections[2])
        else:
            focus_str = focus_str.replace("{section_3}", grammar_topic)

        activity["focus"] = focus_str
        if "items" in tmpl:
            activity["items"] = tmpl["items"]

        activities.append(activity)

    return activities


def fix_vocab(plan):
    """Replace generic vocab with terms from content_outline."""
    vocab = plan.get("vocabulary_hints", {})
    required = vocab.get("required", [])

    if len(required) < 4:
        return required

    # Find where generic entries are
    generic_indices = []
    for i, entry in enumerate(required):
        entry_str = str(entry).strip()
        if any(g in entry_str for g in GENERIC_VOCAB):
            generic_indices.append(i)

    if not generic_indices:
        return required

    # Extract content-specific terms
    content_terms = extract_content_terms(plan)

    if not content_terms:
        # Can't replace — remove generic entries instead
        return [r for i, r in enumerate(required) if i not in generic_indices]

    # Replace generic entries with content terms
    new_required = list(required)
    for idx, gi in enumerate(generic_indices):
        if idx < len(content_terms):
            term = content_terms[idx]
            new_required[gi] = f"{term} — key term from module content"
        else:
            new_required[gi] = None  # Mark for removal

    return [r for r in new_required if r is not None]


def process_plan_file(filepath, dry_run=False):
    """Process a single plan file. Returns (activities_fixed, vocab_fixed)."""
    with open(filepath) as f:
        content = f.read()

    plan = yaml.safe_load(content)
    if not plan:
        return False, False

    activities_fixed = False
    vocab_fixed = False

    # Fix activities
    if has_template_activities(plan):
        new_activities = generate_activities(plan)

        # Replace in the raw content using string manipulation to preserve formatting
        # Find the activity_hints section
        lines = content.split('\n')
        new_lines = []
        in_activities = False
        skip_until_next_key = False

        for line in lines:
            if line.startswith('activity_hints:'):
                in_activities = True
                new_lines.append('activity_hints:')
                # Add new activities
                for act in new_activities:
                    new_lines.append(f"- type: {act['type']}")
                    # Quote focus if it contains special chars
                    focus_val = act['focus']
                    if ':' in focus_val or "'" in focus_val:
                        focus_val = f'"{focus_val}"'
                    new_lines.append(f"  focus: {focus_val}")
                    if 'items' in act:
                        new_lines.append(f"  items: {act['items']}")
                skip_until_next_key = True
                continue

            if skip_until_next_key:
                # Skip old activity lines until we hit a new top-level key
                if line and not line.startswith(' ') and not line.startswith('-'):
                    skip_until_next_key = False
                    new_lines.append(line)
                elif line.startswith('- type:') or line.startswith('  '):
                    continue  # Skip old activity content
                elif line == '':
                    continue  # Skip blank lines in activity section
                else:
                    skip_until_next_key = False
                    new_lines.append(line)
                continue

            new_lines.append(line)

        content = '\n'.join(new_lines)
        activities_fixed = True

    # Fix vocabulary
    if has_generic_vocab(plan):
        new_required = fix_vocab(plan)

        # Replace in raw content
        lines = content.split('\n')
        new_lines = []
        in_required = False
        generic_count = 0
        replaced_count = 0

        for line in lines:
            if '  required:' in line and not line.strip().startswith('#'):
                in_required = True
                new_lines.append(line)
                continue

            if in_required:
                if line.strip().startswith('- ') and any(g.split('(')[0].strip() in line for g in GENERIC_VOCAB):
                    # This is a generic vocab line — replace with new entry
                    if replaced_count < len(new_required) - (len(plan.get('vocabulary_hints', {}).get('required', [])) - 4):
                        # Skip — we'll let the non-generic entries through
                        pass
                    replaced_count += 1
                    # Find the replacement
                    new_idx = generic_count
                    if new_idx < len(new_required):
                        entry = new_required[new_idx]
                        if entry and not any(g in str(entry) for g in GENERIC_VOCAB):
                            new_lines.append(f"  - {entry}")
                        # else skip this entry entirely
                    generic_count += 1
                    continue
                elif line.strip().startswith('- '):
                    new_lines.append(line)
                    continue
                elif line.strip().startswith('recommended:'):
                    in_required = False
                    new_lines.append(line)
                    continue
                elif line.strip() == '' or (not line.startswith(' ')):
                    in_required = False
                    new_lines.append(line)
                    continue
                else:
                    new_lines.append(line)
                    continue

            new_lines.append(line)

        content = '\n'.join(new_lines)
        vocab_fixed = True

    if (activities_fixed or vocab_fixed) and not dry_run:
        with open(filepath, 'w') as f:
            f.write(content)

    return activities_fixed, vocab_fixed


def main():
    dry_run = '--dry-run' in sys.argv

    plan_files = sorted(PLAN_DIR.glob("*.yaml"))

    total_act = 0
    total_vocab = 0

    for pf in plan_files:
        act_fixed, vocab_fixed = process_plan_file(pf, dry_run=dry_run)
        slug = pf.stem

        if act_fixed or vocab_fixed:
            fixes = []
            if act_fixed:
                fixes.append("activities")
                total_act += 1
            if vocab_fixed:
                fixes.append("vocabulary")
                total_vocab += 1
            action = "WOULD FIX" if dry_run else "FIXED"
            print(f"  {action} {slug}: {', '.join(fixes)}")

    print(f"\nTotal: {total_act} activity fixes, {total_vocab} vocabulary fixes")
    if dry_run:
        print("(dry run — no files modified)")


if __name__ == "__main__":
    main()
