import os

import ruamel.yaml

user_a2_tail = """
      # A2.9 [Metalanguage Bridge & Foundation]
      - metalanguage-words-and-cases
      - metalanguage-verbs-and-time
      - metalanguage-sentences-and-classroom
      - metalanguage-phonetics
      - metalanguage-morphology
      - metalanguage-syntax-cases
      # A2.10 [Refinement and Graduation]
      - a2-comprehensive-review
      - a2-practice-exam
      - a2-finale
"""

user_b1 = """
      # B1.1 [Baselines & Morphophonemics]
      - b1-baseline-past-present
      - b1-baseline-future-aspect
      - people-and-relationships
      - alternation-vowels
      - alternation-consonants-nouns
      - alternation-consonants-verbs
      - simplification-consonants
      - noun-subclasses-masculine
      - noun-subclasses-hissing
      - noun-subclasses-feminine
      - pluralia-tantum
      - health-at-the-doctor
      - checkpoint-morphophonemics
      # B1.2 [Verbs]
      - conditionals-real
      - conditionals-unreal
      - imperative-nuances
      - verbal-nouns
      - reflexive-verbs-nuances
      - passive-voice-intro
      - verb-formation-suffixes
      - daily-life-and-routines
      - checkpoint-verbs
      # B1.3 [Motion Verb Universe]
      - prepositions-spatial-review
      - motion-base-review
      - motion-prefixes-arrival
      - motion-prefixes-departure
      - motion-prefixes-in-out
      - motion-prefixes-transit
      - motion-prefixes-around
      - motion-flight-swim
      - figurative-motion
      - traveling-ukraine
      - checkpoint-motion
      # B1.4 [Degrees of Comparison & Word Formation]
      - adjectives-comparative
      - adjectives-superlative
      - adjectives-suppletive
      - adverbs-comparison-formation
      - word-formation-adjectives
      - word-formation-nouns
      - shopping-and-services
      - checkpoint-comparison
      # B1.5 [Advanced Case Usages & Prepositions]
      - genitive-nuances
      - dative-nuances
      - instrumental-nuances
      - vocative-formal
      - prepositions-temporal
      - prepositions-cause-purpose
      - cases-with-ordinal-numerals
      - cases-with-quantity-expressions
      - advanced-pronouns
      - housing-and-renting
      - checkpoint-cases
      # B1.6 [Participles & Gerunds]
      - participles-active
      - participles-passive
      - participle-phrases
      - short-form-adjectives
      - gerunds-imperfective
      - gerunds-perfective
      - gerund-phrases
      - education-and-university
      - checkpoint-participles
      # B1.7 [Complex Syntax]
      - complex-compound
      - complex-subordinate-object
      - complex-subordinate-relative
      - complex-subordinate-time
      - complex-subordinate-reason
      - complex-subordinate-condition
      - complex-subordinate-purpose
      - complex-subordinate-concess
      - reported-speech
      - leisure-culture-festivals
      - checkpoint-syntax
      # B1.8 [Text and Register]
      - text-register-formal
      - text-register-informal
      - text-compression
      - double-negation
      - introductory-words
      - nature-and-environment
      - reading-literature
      - checkpoint-text-register
      # B1.9 [Synthesis & Graduation]
      - narrative-mastery
      - debate-and-opinion
      - society-and-media
      - comprehensive-b1-review
      - practice-exam-reading
      - practice-exam-writing
      - b1-finale
"""

def parse_structure(text):
    structure = []
    current_phase = ""
    for line in text.strip().split('\n'):
        line = line.strip()
        if line.startswith("#"):
            current_phase = line.replace("#", "").strip()
        elif line.startswith("-"):
            slug = line.split("-", 1)[1].strip()
            structure.append((slug, current_phase))
    return structure

a2_parsed = parse_structure(user_a2_tail)
b1_parsed = parse_structure(user_b1)

b1_slugs = [s for s, p in b1_parsed]

yaml_handler = ruamel.yaml.YAML()
yaml_handler.preserve_quotes = True
yaml_handler.indent(mapping=2, sequence=4, offset=2)

manifest_path = "curriculum/l2-uk-en/curriculum.yaml"
with open(manifest_path, encoding="utf-8") as f:
    manifest = yaml_handler.load(f)

# Update B1 modules in curriculum.yaml
manifest["levels"]["b1"]["modules"] = b1_slugs
with open(manifest_path, "w", encoding="utf-8") as f:
    yaml_handler.dump(manifest, f)
print("curriculum.yaml updated with B1 modules.")

# Function to update plans
def update_plans(parsed_struct, level_str, plan_dir):
    for slug, phase in parsed_struct:
        fpath = os.path.join(plan_dir, f"{slug}.yaml")
        if not os.path.exists(fpath):
            print(f"Warning: {fpath} not found.")
            continue

        with open(fpath, encoding="utf-8") as f:
            plan = yaml_handler.load(f)

        plan["phase"] = phase

        with open(fpath, "w", encoding="utf-8") as f:
            yaml_handler.dump(plan, f)

# A2 tail update
update_plans(a2_parsed, "A2", "curriculum/l2-uk-en/plans/a2")
# B1 full update
update_plans(b1_parsed, "B1", "curriculum/l2-uk-en/plans/b1")

print("Plan phases updated.")
