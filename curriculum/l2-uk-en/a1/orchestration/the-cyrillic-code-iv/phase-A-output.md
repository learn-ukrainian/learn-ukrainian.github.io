ꬠthought
CRITICAL INSTRUCTION 1: I need to prioritize specific tools (like `read_file`, `list_directory`, `grep_search`) over generic shell commands.
CRITICAL INSTRUCTION 2: Before making tool calls T, think and explicitly list out any related tools for the task at hand. You can only execute a set of tools T if all other tools in the list are either more generic or cannot be used for the task at hand.

Related tools: `read_file`, `run_shell_command`, `grep_search`.
I need to read the content of specific files to gather context for the research and meta outline. `read_file` is the most specific and appropriate tool for this.

Files to read:
1. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-cyrillic-code-iv.yaml` (Plan file)
2. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-iv.yaml` (Meta file)
3. `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` (Level quick-ref)
4. `/Users/krisztiankoos/projects/learn-ukrainian/docs/l2-uk-en/state-standard-2024-mapping.yaml` (State Standard mapping)

Let's read these four files concurrently. I will only use `read_file`. The other tools are more generic or not applicable.
T = { `read_file` (x4) }
All other tools are more generic or not applicable for just reading files. Let's execute.
I will read them all now.
> 1. Plan file: `curriculum/l2-uk-en/plans/a1/the-cyrillic-code-iv.yaml`
> 2. Meta file: `curriculum/l2-uk-en/a1/meta/the-cyrillic-code-iv.yaml`
> 3. Quick-ref: `claude_extensions/quick-ref/A1.md`
> 4. State standard: `docs/l2-uk-en/state-standard-2024-mapping.yaml`
Wait, does `curriculum/l2-uk-en/a1/meta/the-cyrillic-code-iv.yaml` exist? Yes, it's mentioned in the prompt. If not, `read_file` will tell me. Same for the others. I will use relative paths from the workspace root.
Wait, let's use the absolute paths provided in the prompt just to be safe.
1. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-cyrillic-code-iv.yaml`
2. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-iv.yaml`
3. `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md`
4. `/Users/krisztiankoos/projects/learn-ukrainian/docs/l2-uk-en/state-standard-2024-mapping.yaml` (wait, I don't know the exact path for this one. The prompt says `docs/l2-uk-en/state-standard-2024-mapping.yaml`, so I will use that relative to the project root, or absolute). Let's use absolute for all.
Project root: `/Users/krisztiankoos/projects/learn-ukrainian`
Let's call `read_file` four times.ꬡ
ꬠthought
CRITICAL INSTRUCTION 1: I am prioritizing the output generation as plain text. Tools have been used specifically for gathering necessary information (`read_file`).
CRITICAL INSTRUCTION 2: Before making tool calls T, I would explicitly list related tools. Right now, no further tool calls are required because I have all the context to generate the output exactly as instructed in the prompt. I will just synthesize the data and construct the final text response.

Task Instructions Reminder:
- Create Research Notes + Meta Outline in one pass.
- Format requirements:
```
===RESEARCH_START===
...
===RESEARCH_END===

===META_OUTLINE_START===
...
===META_OUTLINE_END===
```
- Module: `the-cyrillic-code-iv`
- State standard mapped: `§4.1.1` (alphabet), `§4.1.2` (apostrophe), `§4.1.3` (soft sign), `§4.1.4` (vowel/consonant).
- Vocabulary frequency: `чай`, `яблуко`, `ще`, `їжа`, `день`, `сім'я`, `Львів`, `Європа`, `центр`, `щастя`, `м'яч`, `факт`, `ґанок`.
- Common learner errors: 
  1. Iotated vowels: treating them always as one sound vs. two. 
  2. Soft sign vs Apostrophe: confusing their functions (Ь softens, apostrophe blocks softening).
  3. Щ: confusing it with Ш.
- Cultural hooks: Ї as a symbol of resistance. Ґ history (repressed in 1933, restored in 1990).
- Cross references: Builds on `a1-03 (The Cyrillic Code III)`. Prepares for `a1-05 (Syllables and Word Division)`.

For Meta Outline:
Target 1200 words.
Sections in plan:
- Вступ (150)
- Злиті звуки (250) -> let's make it 300 to match meta file or adjust
- Йотовані голосні (350)
- М'який знак та апостроф (250)
- Дигріфи та Ґ (150)
- Підсумок (100)
Total words = 150 + 250 + 350 + 250 + 150 + 100 = 1250 words. Perfect (~1200).

Let's refine the outline:
```yaml
content_outline:
  - title: "Вступ — Introduction"
    slug: introduction
    words: 150
    points:
      - "Welcome the learner: they already know 23 letters. Only 10 letters, 2 digraphs, and 1 apostrophe remain to complete the alphabet."
      - "Diagnostic check: Read 5 familiar words using previously learned letters to build confidence."
  - title: "Злиті звуки та рідкісні букви — Affricates, Digraphs & Ґ"
    slug: affricates-digraphs
    words: 300
    points:
      - "Introduce Ц as a single 'ts' sound (like cats), not two separate consonants. Example: центр."
      - "Introduce Щ as a uniquely Ukrainian double sound (sh+ch). Contrast with Ш. Example: ще."
      - "Introduce Ф as 'f', noting its use mostly in borrowed words. Example: факт."
      - "Explain digraphs ДЖ (like 'jungle') and ДЗ (no English equivalent). Examples: джаз, дзвін."
      - "Introduce Ґ as the hard 'g', noting its rarity and history. Example: ґанок."
  - title: "Йотовані голосні — Iotated Vowels Я, Ю, Є, Ї, Й"
    slug: iotated-vowels
    words: 350
    points:
      - "Explain the 'dual nature' principle: two sounds at the beginning or after a vowel, but one sound (softening) after a consonant."
      - "Introduce Я (/ja/) and Ю (/ju/) with high-frequency examples (яблуко, я, юнак)."
      - "Introduce Є (/je/), anchoring to the cultural concept of Європа."
      - "Introduce Ї (/ji/). Emphasize it ALWAYS makes two sounds and NEVER softens. Mention its use as a symbol of Ukrainian resistance."
      - "Introduce Й as a short consonant that never forms a syllable alone. Example: чай."
  - title: "М'який знак та апостроф — Soft Sign & Apostrophe"
    slug: modifiers
    words: 250
    points:
      - "Define the soft sign (Ь) as a modifier that palatalizes the preceding consonant, not an independent sound. Examples: день, Львів."
      - "Explain the apostrophe (') as a blocker: it prevents softening and keeps the /j/ in the following iotated vowel. Examples: сім'я, м'яч."
      - "Summarize the core rule: Ь softens what comes before it, while the apostrophe blocks softening."
  - title: "Підсумок: Весь алфавіт — The Full Alphabet"
    slug: summary-alphabet
    words: 150
    points:
      - "Present the complete 33-letter Cyrillic alphabet in proper order."
      - "Self-check 1: Which letter always makes two sounds? (Ї)"
      - "Self-check 2: What does the apostrophe do? (Blocks softening)"
      - "Self-check 3: How is Щ different from Ш? (Щ is sh+ch)"
      - "Bridge to next module: a1-05 (Syllables and Word Division)."
```

Let's put together the final response. Keep text generation pure and adhere to constraints.
Only output the required blocks. Do not add intro/outro text.
Research section should have the State Standard mapping correctly cited.

```
===RESEARCH_START===

# Дослідження: The Cyrillic Code IV

## State Standard Reference
§4.1.1: "Ukrainian alphabet"
§4.1.2: "Apostrophe usage"
§4.1.3: "Soft sign (м'який знак)"
Alignment: Introduces the final 10 letters of the alphabet, digraphs, the apostrophe, and the concept of palatalization via the soft sign and iotated vowels. Completes foundational literacy required for reading and phonetic competence at A1.

## Vocabulary Frequency
| Word | Notes | Key collocations |
|------|-------|------------------|
| чай | Top 500 word, simple CVC | пити чай, чорний чай |
| день | Top 50 word, demonstrates Ь | добрий день |
| ще | High-frequency function word, demonstrates Щ | ще раз, що ще |
| сім'я | High-frequency, demonstrates apostrophe | моя сім'я |
| Європа | High-frequency proper noun, demonstrates Є | жити в Європі |
| факт | Internationalism, demonstrates Ф | цікавий факт |

## Cultural Hooks
1. **The Letter Ї as Resistance:** Ї is uniquely Ukrainian. During the full-scale invasion, drawing the letter Ї in occupied territories became a popular symbol of resistance and Ukrainian identity.
2. **The Repressed Letter Ґ:** The hard G (Ґ) was officially removed from the Ukrainian alphabet by Soviet authorities in 1933 to make Ukrainian closer to Russian. It was officially restored in 1990.

## Common Learner Errors
1. **Iotated Vowels as Single Sounds Everywhere** → Learners often pronounce Я as [ja] even after consonants (e.g., trying to say м'ясо without the apostrophe instead of softening).
2. **Confusing Ь and Apostrophe** → Using Ь to separate sounds or apostrophe to soften. Rule: Ь softens, Apostrophe blocks softening.
3. **Mispronouncing Щ as Ш** → Pronouncing "ще" like "ше". Щ is always a double sound (sh+ch).

## Cross-References
- Builds on: a1-03 (The Cyrillic Code III)
- Prepares for: a1-05 (Syllables and Word Division)

## Notes for Content Writing
- This is the final alphabet module. Celebrate the learner's achievement of unlocking the full 33-letter alphabet!
- English scaffolding is mandatory here to explain the abstract concepts of palatalization (softening) and the "dual nature" of iotated vowels.
- Avoid verb conjugation or imperative forms. Keep all examples to basic nouns, noun phrases, or simple "Це + noun" structures.
- IPA should only be provided for the first occurrence of a new word.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - title: "Вступ — Introduction"
    slug: introduction
    words: 150
    points:
      - "Welcome the learner: they already know 23 letters. Only 10 letters, 2 digraphs, and 1 apostrophe remain to complete the alphabet."
      - "Diagnostic check: Read 5 familiar words using previously learned letters to build confidence."
      - "Set expectations: Grammar and mechanics will be explained in English, with examples in Ukrainian."
  - title: "Злиті звуки та рідкісні букви — Affricates, Digraphs & Ґ"
    slug: affricates-digraphs
    words: 300
    points:
      - "Introduce Ц as a single 'ts' sound (like cats), not two separate consonants. Example: центр."
      - "Introduce Щ as a uniquely Ukrainian double sound (sh+ch). Contrast with Ш. Example: ще."
      - "Introduce Ф as 'f', noting its use mostly in borrowed words. Example: факт."
      - "Explain digraphs ДЖ (like 'jungle') and ДЗ (no English equivalent). Examples: джаз, дзвін."
      - "Introduce Ґ as the hard 'g', noting its rarity and history. Example: ґанок."
  - title: "Йотовані голосні — Iotated Vowels Я, Ю, Є, Ї, Й"
    slug: iotated-vowels
    words: 350
    points:
      - "Explain the 'dual nature' principle: two sounds at the beginning or after a vowel, but one sound (softening) after a consonant."
      - "Introduce Я (/ja/) and Ю (/ju/) with high-frequency examples (яблуко, я, юнак)."
      - "Introduce Є (/je/), anchoring to the cultural concept of Європа."
      - "Introduce Ї (/ji/). Emphasize it ALWAYS makes two sounds and NEVER softens. Mention its use as a symbol of Ukrainian resistance."
      - "Introduce Й as a short consonant that never forms a syllable alone. Example: чай."
  - title: "М'який знак та апостроф — Soft Sign & Apostrophe"
    slug: modifiers
    words: 250
    points:
      - "Define the soft sign (Ь) as a modifier that palatalizes the preceding consonant, not an independent sound. Examples: день, Львів."
      - "Explain the apostrophe (') as a blocker: it prevents softening and keeps the /j/ in the following iotated vowel. Examples: сім'я, м'яч."
      - "Summarize the core rule: Ь softens what comes before it, while the apostrophe blocks softening."
  - title: "Підсумок: Весь алфавіт — The Full Alphabet"
    slug: summary-alphabet
    words: 150
    points:
      - "Present the complete 33-letter Cyrillic alphabet in proper order."
      - "Self-check 1: Which letter always makes two sounds? (Ї)"
      - "Self-check 2: What does the apostrophe do? (Blocks softening)"
      - "Self-check 3: How is Щ different from Ш? (Щ is sh+ch)"
      - "Bridge to next module: a1-05 (Syllables and Word Division)."
===META_OUTLINE_END===
```

Review against constraints:
- Text output only? Yes.
- No files modified? Yes.
- Word budget sums to 1200 words? 150 + 300 + 350 + 250 + 150 = 1200. Yes.
- English for instructions? Yes.
- Metalinguistic approach: Yes.

Looks good to go.ꬡ===RESEARCH_START===

# Дослідження: The Cyrillic Code IV

## State Standard Reference
§4.1.1: "Ukrainian alphabet"
§4.1.2: "Apostrophe usage"
§4.1.3: "Soft sign (м'який знак)"
Alignment: Introduces the final 10 letters of the alphabet, digraphs, the apostrophe, and the concept of palatalization via the soft sign and iotated vowels. Completes the foundational literacy prerequisite for A1 phonetic competence.

## Vocabulary Frequency
| Word | Notes | Key collocations |
|------|-------|------------------|
| чай | Top 500 word, simple CVC | пити чай, чорний чай |
| день | Top 50 word, demonstrates Ь | добрий день |
| ще | High-frequency function word, demonstrates Щ | ще раз, що ще |
| сім'я | High-frequency, demonstrates apostrophe | моя сім'я |
| Європа | High-frequency proper noun, demonstrates Є | жити в Європі |
| факт | Internationalism, demonstrates Ф | цікавий факт |

## Cultural Hooks
1. **The Letter Ї as Resistance:** Ї is uniquely Ukrainian. During the full-scale invasion, drawing the letter Ї in occupied territories became a powerful symbol of resistance and Ukrainian identity.
2. **The Repressed Letter Ґ:** The hard G (Ґ) was officially removed from the Ukrainian alphabet by Soviet authorities in 1933 to artificially bring Ukrainian closer to Russian. It was proudly restored in 1990.

## Common Learner Errors
1. **Iotated Vowels as Single Sounds Everywhere** → Learners often try to pronounce Я as [ja] even after consonants instead of letting it soften the preceding consonant. 
2. **Confusing Ь and Apostrophe** → Using Ь to separate sounds or using the apostrophe to soften. The rule must be clear: Ь softens, Apostrophe blocks softening.
3. **Mispronouncing Щ as Ш** → Pronouncing "ще" like "ше". Щ is always a double sound (sh+ch) in Ukrainian.

## Cross-References
- Builds on: a1-03 (The Cyrillic Code III)
- Prepares for: a1-05 (Syllables and Word Division)

## Notes for Content Writing
- This is the final alphabet module. Frame it as a major victory — the learner is unlocking the full 33-letter alphabet!
- English scaffolding is absolutely mandatory here to explain abstract concepts like palatalization (softening) and the "dual nature" of iotated vowels.
- Avoid all verb conjugations or imperative forms. Keep examples strictly to basic nouns, noun phrases, or simple "Це + noun" previews.
- Only provide IPA for the first occurrence of a new word. 

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - title: "Вступ — Introduction"
    slug: introduction
    words: 150
    points:
      - "Welcome the learner: they already know 23 letters. Only 10 letters, 2 digraphs, and 1 apostrophe remain to complete the alphabet."
      - "Diagnostic check: Read 5 familiar words using previously learned letters to build confidence."
      - "Set expectations: Grammar and mechanics will be explained in English, with examples in Ukrainian."
  - title: "Злиті звуки та рідкісні букви — Affricates, Digraphs & Ґ"
    slug: affricates-digraphs
    words: 300
    points:
      - "Introduce Ц as a single 'ts' sound (like cats), not two separate consonants. Example: центр."
      - "Introduce Щ as a uniquely Ukrainian double sound (sh+ch). Contrast with Ш. Example: ще."
      - "Introduce Ф as 'f', noting its use mostly in borrowed words. Example: факт."
      - "Explain digraphs ДЖ (like 'jungle') and ДЗ (no English equivalent). Examples: джаз, дзвін."
      - "Introduce Ґ as the hard 'g', noting its rarity and history. Example: ґанок."
  - title: "Йотовані голосні — Iotated Vowels Я, Ю, Є, Ї, Й"
    slug: iotated-vowels
    words: 350
    points:
      - "Explain the 'dual nature' principle: two sounds at the beginning or after a vowel, but one sound (softening) after a consonant."
      - "Introduce Я (/ja/) and Ю (/ju/) with high-frequency examples (яблуко, я, юнак)."
      - "Introduce Є (/je/), anchoring to the cultural concept of Європа."
      - "Introduce Ї (/ji/). Emphasize it ALWAYS makes two sounds and NEVER softens. Mention its use as a symbol of Ukrainian resistance."
      - "Introduce Й as a short consonant that never forms a syllable alone. Example: чай."
  - title: "М'який знак та апостроф — Soft Sign & Apostrophe"
    slug: modifiers
    words: 250
    points:
      - "Define the soft sign (Ь) as a modifier that palatalizes the preceding consonant, not an independent sound. Examples: день, Львів."
      - "Explain the apostrophe (') as a blocker: it prevents softening and keeps the /j/ in the following iotated vowel. Examples: сім'я, м'яч."
      - "Summarize the core rule: Ь softens what comes before it, while the apostrophe blocks softening."
  - title: "Підсумок: Весь алфавіт — The Full Alphabet"
    slug: summary-alphabet
    words: 150
    points:
      - "Present the complete 33-letter Cyrillic alphabet in proper order."
      - "Self-check 1: Which letter always makes two sounds? (Ї)"
      - "Self-check 2: What does the apostrophe do? (Blocks softening)"
      - "Self-check 3: How is Щ different from Ш? (Щ is sh+ch)"
      - "Bridge to next module: a1-05 (Syllables and Word Division)."
===META_OUTLINE_END===
