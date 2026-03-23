<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [Pedagogical quality] [critical]
  Location: `A quick note on stress: сестр**а**, бабус**я**, дідус**ь**, дочк**а**, сім'**я** — stress falls on the last syllable in all of these.`
  Issue: Factually incorrect claim. The word "бабуся" is stressed on the second syllable (`у`), not the last. The soft sign `ь` in "дідусь" is not a vowel and cannot carry stress. Teaching A1 learners that these are all stressed on the last syllable will cement incorrect pronunciation.
  Fix: Completely rewrite this note. Only group words that actually share the stress pattern (e.g., `сестра́`, `сім'я́`, `дочка́`), and explain the softening effect of `ь` separately.
- FIX: [Structural integrity] [critical]
  Location: `### Додаткові слова з уроку` (Table)
  Issue: Extreme hallucinations in the vocabulary table data. Nouns "брати" (brothers) and "Діти" (children) are labeled as verbs (`дієсл.`). Possessive pronouns ("мій", "моя", "моє") have their grammatical metadata ("masculine", "feminine", "Possessive Pronouns") pasted into the English translation column.
  Fix: Correct the POS for "брати" and "Діти" to `ім.`. Change the translations for "мій/моя/моє" to "my".
- FIX: [Linguistic accuracy] [major]
  Location: `> — У тебе́ є бра́ти чи сестри́?` and `> — Так, у мене́ є...`
  Issue: Added manual stress marks are incorrect. Nominative plural of sister is `се́стри` (stress on the first syllable). `сестри́` is Genitive singular. `у мене́` should be `у ме́не`.
  Fix: Remove all manual acute accents from the text. Let the deterministic downstream tool handle stress annotation as designed.
- FIX: [Exercise quality] [major]
  Location: `:::fill-in` (Мій, моя чи моє?)
  Issue: The activity hint explicitly dictated: `Options: мій/моя/моє/мої or твій/твоя/твоє/твої.` The generator included items requiring "його" and "її" as answers, ignoring the constraint.
  Fix: Replace the two items testing "його" and "її" with items testing the "мій" and "твій" paradigms.

- FIX (Linguistic): - **Errors found:**
  1. **Factual Phonetics Error (Hallucination)**: The text claims `A quick note on stress: сестр**а**, бабус**я**, дідус**ь**, дочк**а**, сім'**я** — stress falls on the last syllable in all of these.` This is completely false. The stress in "бабуся" falls on the second syllable (`бабу́ся`). Furthermore, highlighting the soft sign `ь` in "дідусь" while discussing syllables shows a fundamental misunderstanding, as `ь` is a consonant modifier, not a vowel.
  2. **Incorrect Stre
</correction_directive>