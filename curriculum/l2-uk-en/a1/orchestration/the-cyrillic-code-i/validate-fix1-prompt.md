        # Fix 7 issue(s) in `the-cyrillic-code-i`

        ### Fix 1: DECODABILITY
**What:** [DECODABILITY_M1] 'Приголосна' in 'Перші склади' contains unknown letter(s): П, г, и, о, р
**How to fix:** Replace words containing unknown letters with words using only А, М, Л, У, Н, С. Or move the content to a later module.
**Context (line 111):** ``

### Fix 2: DECODABILITY
**What:** [DECODABILITY_M1] 'З' in 'Перші склади' contains unknown letter(s): З
**How to fix:** Replace words containing unknown letters with words using only А, М, Л, У, Н, С. Or move the content to a later module.
**Context (line 111):** ``

### Fix 3: DECODABILITY
**What:** [DECODABILITY_M1] 'літерою' in 'Перші склади' contains unknown letter(s): е, о, р, т, ю, і
**How to fix:** Replace words containing unknown letters with words using only А, М, Л, У, Н, С. Or move the content to a later module.
**Context (line 111):** ``

### Fix: Gate `Words` FAIL — 1443/2000 (raw: 1670)
**Action:** Expand content in the shortest sections. Add examples, explanations, or practice scenarios.

### Fix: Gate `Density` FAIL — 1 < 6

### Fix: Gate `Pedagogy` FAIL — 7 violations

### Fix: Gate `Immersion` FAIL — 3.9% LOW (target 5-15% (M01))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Other Audit Failures

```
❌ Match the Letters
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (78% overlap): "Which Cyrillic character looks like an English «C» but permanently sounds like an «S»?". Shares significant keywords with sentence at index 71.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-i-audit.log for details)
```


## Constraints (do NOT violate while fixing)

DECODABILITY (M1 — 6 known letters: А, М, Л, У, Н, С):
- Words in reading drills MUST use ONLY these 6 letters (e.g., мама, сума, луна, мул, нам)
- Words with unknown letters (кіт, вода, привіт) may appear ONLY as labelled vocabulary with immediate English translation: «Привіт!» (Hello!)
- Video example words for the letter being taught (ананас for А) are fine — they are heard, not read

GRAMMAR BAN (no verbs exist yet in the student's knowledge):
- NO imperative forms: Слухайте, Читайте, Повторюйте, Пишіть, Дивіться — ALL BANNED
- NO verb conjugation of any kind (present, past, future)
- Classroom instructions MUST be in English: 'Listen carefully', 'Read aloud', 'Repeat after the video'
- Allowed Ukrainian structures: bare nouns only (мама, сума, луна)

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)', 'consonants (приголосні)'
- Section headings MUST be bilingual as shown in the content_outline (e.g., '## Голосні — Vowels')
- NEVER write Ukrainian-only section headers or explanatory prose — the student cannot read it yet


DECODABLE VOCABULARY (M1 — only letters: А, Л, М, Н, С, У):
Use ONLY these words in activities and reading drills. Any word with a letter
outside this set will FAIL the decodability audit gate.

Available words: мама, сума, луна, мул, нам, нас, сам, ум, масла, мала

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

