# Content Review: greetings-and-politeness

**Track:** a1 | **Sequence:** 8
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: 2375, target: 1200)
**Verdict:** B

## Plan Adherence
| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Greet people appropriately by time of day | YES | Basic Greetings (Вітання) | Добрий ранок/день/вечір with time ranges |
| Choose correctly between Ти and Ви | YES | Formal vs. Informal | Clear cultural explanation with examples |
| Use basic politeness expressions | YES | Politeness Magic Words | Дякую, Будь ласка, Вибачте, Перепрошую all covered |
| Introduce yourself and respond | YES | Introductions (Знайомство) | Як вас/тебе звати? + Мене звати... + Дуже приємно |

### Vocabulary Coverage
| Required Word | In Prose? | In Vocab YAML? | In Activities? |
|--------------|-----------|----------------|----------------|
| привіт | YES | YES | YES (quiz, group-sort) |
| добрий ранок | YES | YES | YES (match-up, anagram) |
| добрий день | YES | YES | YES (quiz, fill-in) |
| добрий вечір | YES | YES | YES (match-up, anagram) |
| до побачення | YES | YES | YES (quiz, fill-in, match-up) |
| дякую | YES | YES | YES (quiz, fill-in, anagram) |
| будь ласка | YES | YES | YES (quiz, fill-in, true-false) |
| вибачте | YES | YES | YES (quiz, fill-in, anagram) |
| перепрошую | YES | YES | YES (match-up, true-false) |
| дуже приємно | YES | YES (as separate words) | NO (not directly tested) |

All 10 required vocabulary items present in prose. 9/10 in activities (дуже приємно not directly tested as a standalone activity item but appears in dialogues).

### Plan Section Alignment
| Plan Section | Content Section | Match? |
|-------------|-----------------|--------|
| Вітання (Greetings) | Basic Greetings (Вітання) | YES (name adjusted) |
| Ти і Ви (T-V distinction) | Formal vs. Informal: 'Ти' and 'Ви' | YES |
| Ввічливість (Politeness) | Politeness Magic Words (Ввічливість) | YES |
| Знайомство (Introductions) | Introductions (Знайомство) | YES |
| Діалоги (Dialogues) | Merged into Introductions subsection | PARTIAL -- plan has it as separate section, content absorbs it |
| (no plan equivalent) | Summary and Self-Check | Present in meta outline |

The plan's "Діалоги" section (250 words) was absorbed into the Introductions section rather than being a standalone H2. This is a structural deviation but the content is present.

## Linguistic Accuracy
| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| Verb conjugation in examples | MEDIUM | Lines 73-87 | Multiple Ukrainian sentences use conjugated verbs: "Що ти робиш?", "Де ти?", "Що ви робите?" These are verb forms (робиш, робите) that are formally FORBIDDEN at this stage per grammar constraints. However, these appear as memorized phrase chunks in dialogues, not as taught grammar. |
| Genitive case form in examples | MEDIUM | Line 54 | "Гарного дня!" uses genitive case (гарного), which is a fixed farewell formula. Technically beyond scope but acceptable as a memorized chunk. |
| Accusative/genitive in "за допомогу" | LOW | Line 109 | "Дякую за допомогу!" uses accusative case in a set phrase. Acceptable as a chunk. |
| All Ukrainian verified by VESUM | -- | Whole module | 78/83 unique words verified (94%). Only unverified: proper names (Анна, Марія, Оксана, Олена, Іван) -- all legitimate. |

## Pedagogical Quality
**Lesson Quality Score:** 8/10

**Tier-1 "Would I Continue?" Test:**
- Did I feel overwhelmed? PASS -- pacing is very comfortable, phrases introduced gradually
- Were instructions clear? PASS -- consistently clear English scaffolding
- Did I get quick wins? PASS -- learner can say Привіт! after the first paragraph
- Was Ukrainian scary? PASS -- every Ukrainian phrase has an English translation
- Would I come back tomorrow? PASS -- practical, immediately usable phrases

**Score: 5/5 = Lesson Quality 10/10 on tier rubric, adjusted to 8 for concerns:**
The module has excellent warmth and encouragement. However, it's 2x the target length (2375 vs 1200), and the example phrase lists are excessive. Each subsection includes 5-10 example phrases where 3-4 would suffice. This padding makes the module feel repetitive rather than deeper. The dialogues section is well done with three distinct scenarios.

## Activities Quality
| Activity | Type | Issues |
|----------|------|--------|
| Basic Greetings & Politeness | quiz | 8 items, all correct, good distractor quality |
| English to Ukrainian Match | match-up | 8 pairs, all correct. "Добраніч" included but not formally taught in prose. |
| Situations: True or False | true-false | 8 items, well-designed situational questions |
| Spelling Check | anagram | 8 items, letter counts verified, all correct |
| Sort the Phrases | group-sort | 9 items in 3 groups. "Добраніч" in farewells -- introduced only in activities, not prose. |
| Complete the Conversation | fill-in | 8 items, all correct, good conversational contexts |
| Match to the Situation | match-up | 8 pairs, excellent situational matching |
| Culture and Meaning | true-false | 8 items. "Смачного" tested but not in plan vocabulary_hints. |

**Activity variety:** 6 unique types (quiz, match-up, true-false, anagram, group-sort, fill-in) -- excellent.

**Vocabulary in activities not in plan:**
- "Добраніч" (good night) appears in activities and vocabulary YAML but is not in plan's vocabulary_hints (neither required nor recommended). It's a natural extension but technically unauthorized.
- "Смачного" (bon appetit) appears in activities and vocabulary YAML but not in plan's vocabulary_hints. Same concern.
- "Так", "Ні", "Погано", "Нормально", "Чудово", "На здоров'я", "Па-па" appear in vocabulary YAML but are not in plan's vocabulary_hints. The vocabulary YAML includes 20 items but several are outside the plan's authorized list.

## Engagement
| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | 4 | 3 | PASS |
| Tables | 0 | -- | Missing (could use tables for greeting overview) |
| Videos embedded | 0/0 | -- | N/A |

## Issues Found

### CRITICAL (blocks deployment)
(none)

### HIGH (should fix before deployment)
1. **Vocabulary YAML exceeds plan scope**: The vocabulary YAML includes 7 items not in plan vocabulary_hints (Так, Ні, Погано, Нормально, Чудово, Смачного, На здоров'я, Добраніч, Па-па). While some (Так, Ні) are natural additions for a greetings module, the plan says "Do NOT add vocabulary items beyond this list." These should either be added to the plan or removed from the YAML.
2. **Conjugated verb forms in examples**: The Ти/Ви section includes "Що ти робиш?", "Що ви робите?" which use conjugated verb forms (робиш, робите). Grammar constraints say verb conjugation is FORBIDDEN. These should be replaced with allowed patterns (e.g., "Ти добре?" / "Ви добре?" which are already present).

### MEDIUM (fix if possible)
1. **Missing "Діалоги" as standalone section**: The plan has "Діалоги (Dialogues)" as a separate section with 250 words. The content merges dialogues into the Introductions section. Consider splitting into its own H2 for plan compliance.
2. **No grammar tables**: The module uses no tables at all -- greetings overview, Ти/Ви comparison, and politeness phrases would benefit from table format for quick reference.
3. **Excessive example lists**: Each subsection has 5-10 example phrases in dash-separated lists. At A1, 3-4 examples per concept would provide adequate practice without overwhelming. Trim to reduce the 2x-target word count.

### LOW (informational)
1. **Добраніч inconsistency**: "Добраніч" appears in activities and vocabulary but never in the lesson prose. The module prose teaches "Добрий вечір" for evening but doesn't distinguish it from the bedtime greeting.
2. **Richness score low**: Screen-result.json shows richness at 51/95 with 0 cultural callouts and 0 collocations noted. Adding 1-2 cultural callout boxes about Ukrainian greeting customs would improve this.

## Grade Justification

Grade B. The module is warm, clear, and pedagogically sound for a beginner greeting module. All plan objectives are fully covered with excellent activities. The two HIGH issues -- unauthorized vocabulary items in the YAML and conjugated verb forms in examples -- require fixes but don't undermine the core learning experience. The conjugated forms (робиш, робите) are particularly concerning because they violate the explicit grammar constraints for this sequence position. The excessive phrase repetition inflates the module to 2x target, which could be trimmed for a tighter learning experience.
