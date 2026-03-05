        # Fix 1 issue(s) in `the-cyrillic-code-i`

        ### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-i-audit.log for details)
```


## Constraints (do NOT violate while fixing)

DECODABILITY (M1 — 7 known letters: А, О, У, М, Л, Н, С):
- Words in reading drills MUST use ONLY these 7 letters (e.g., мама, сом, сон, масло, ананас)
- Words with unknown letters (кіт, вода, привіт) may appear ONLY as labelled vocabulary with immediate English translation: «Привіт!» (Hello!)
- Video example words for the letter being taught (ананас for А) are fine — they are heard, not read

GRAMMAR BAN (no verbs exist yet in the student's knowledge):
- NO imperative forms: Слухайте, Читайте, Повторюйте, Пишіть, Дивіться — ALL BANNED
- NO verb conjugation of any kind (present, past, future)
- Classroom instructions MUST be in English: 'Listen carefully', 'Read aloud', 'Repeat after the video'
- Allowed Ukrainian structures: bare nouns only (мама, сом, масло)

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)', 'consonants (приголосні)'
- Section headings MUST be bilingual as shown in the content_outline (e.g., '## Голосні — Vowels')
- NEVER write Ukrainian-only section headers or explanatory prose — the student cannot read it yet


DECODABLE VOCABULARY (M1 — only letters: А, Л, М, Н, О, С, У):
Use ONLY these words in activities, reading drills, AND prose examples.
Any word with a letter outside this set will FAIL the decodability audit gate.
Video key words from the plan's pronunciation_videos section are exempt
(they are heard, not read), but must NOT appear in prose reading examples.

Available words: мама, сом, сон, оса, масло, сосна, насос, лама, смола, ананас, нам, нас, сам, мало, слон

If you need a word not on this list, check that ALL its letters are in the
allowed set above. Words with unknown letters need English translation.


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-i.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-i.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

