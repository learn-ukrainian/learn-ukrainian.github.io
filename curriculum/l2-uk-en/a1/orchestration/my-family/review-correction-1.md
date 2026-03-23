<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [DIMENSION 2. Linguistic accuracy] [SEVERITY: critical]
  Location: `Діало́ги (Dialogues)` -> "У тебе́ є бра́ти чи сестри́?", "Як йо́го зва́ти?", "Це моя сестра Катя́"
  Issue: The writer manually inserted stress marks (which should be handled by a deterministic tool) and placed them incorrectly, resulting in severe morphological errors. `бра́ти` is the verb "to take", whereas the plural noun is `брати́`. `сестри́` is the genitive singular, whereas the nominative plural is `се́стри`. `йо́го` should be `його́`. `Катя́` should be `Ка́тя`.
  Fix: Remove all manual stress marks (`´`) from the markdown prose to prevent breaking parsing tools and to eliminate these linguistic errors.
- FIX: [DIMENSION 5. Exercise quality] [SEVERITY: major]
  Location: All exercise blocks (`:::quiz`, `:::match-up`, `:::fill-in`)
  Issue: The generated exercises actively ignore the specific `focus` instructions from the plan's `activity_hints`.
  Fix: Rewrite all exercises to align with the plan: the quiz must practice answering "У тебе є...?", the match-up must test family relationships (e.g., "тато моєї мами" -> "дідусь"), the first fill-in must test possessive pronouns, and the second fill-in must be a comprehensive family introduction dialogue.
- FIX: [DIMENSION 1. Plan adherence] [SEVERITY: major]
  Location: Entire module
  Issue: The module word count (~850 words) is nearly 30% below the target budget of 1200 words.
  Fix: Expand the pedagogical explanations, add more dialogue examples to the first section, and flesh out the cultural notes to reach the target word count.
- NOTE: [DIMENSION 4. Vocabulary coverage] [SEVERITY: minor]
  Location: `Сім'я (Family Vocabulary)`
  Issue: The recommended words `дружина` (wife) and `чоловік` (husband) are entirely omitted from the instructional prose.
  Fix: Introduce `дружина` and `чоловік` naturally into the vocabulary explanations or within the dialogues.

- FIX (Linguistic): Errors found:
1. **Incorrect manual stress marks causing morphological errors:** The writer manually added acute accents (`´`) for stress throughout the text. Not only does this violate the pipeline rule that stress annotation is handled by a deterministic tool, but several stress marks are placed on the wrong syllables, changing the word's meaning or grammatical case:
   - `бра́ти` — Used in the text as the plural of brother ("У тебе́ є бра́ти..."). This is a critical error. `бра́ти` (stress on
</correction_directive>