        # Fix 0 issue(s) in `the-cyrillic-code-ii`

        ### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-ii-audit.log for details)
```


## Constraints (do NOT violate while fixing)

DECODABILITY (M2 — 14 known letters: А О У М Л Н С + К И І Р В Т Е):
- Reading drills MUST use ONLY these 14 letters (e.g., кіт, молоко, місто, рис, сир, тато, вікно, він)
- Still unknown: Б, Д, П, З, Г, Ґ, Х, Ж, Ш, Ч, Й, Щ, Я, Ю, Є, Ь, Ї, Ц, Ф
- Words needing unknown letters require immediate English translation

GRAMMAR BAN (no verbs exist yet):
- NO imperative forms — ALL BANNED. Use English for instructions.
- NO verb conjugation of any kind
- Allowed: bare nouns, noun phrases using known letters

METALANGUAGE:
- All terminology English-first with Ukrainian in parentheses


DECODABLE VOCABULARY (M2 — only letters: І, А, В, Е, И, К, Л, М, Н, О, Р, С, Т, У):
Use ONLY these words in activities, reading drills, AND prose examples.
Any word with a letter outside this set will FAIL the decodability audit gate.
Video key words from the plan's pronunciation_videos section are exempt
(they are heard, not read), but must NOT appear in prose reading examples.

Available words: кіт, тато, рис, сир, місто, море, метро, ліс, вікно, стіл, молоко, кіно, око, слово, літо, масло, ніс, він, вона, рука, вік

If you need a word not on this list, check that ALL its letters are in the
allowed set above. Words with unknown letters need English translation.


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-ii.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

