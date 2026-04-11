## Linguistic Scan
1 semantic error found: «Я бачив це» is incorrectly translated as "I was looking at it". "Бачити" is a stative verb meaning "to see", whereas "to look" is "дивитися". This is a critical semantic error.

## Exercise Check
Activity markers are present and match the plan's inventory. However, `aspect-sorting-process-result` and `identify-aspect-in-sentences` are injected at the end of Section 2. This places them *before* the perfective aspect has been introduced in Section 3, forcing learners to sort and identify concepts they haven't been taught yet.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | Missing English translations in 3 section headings. Mandatory references (Заболотний, ULP) and recommended vocabulary (одноразовий, концепція) are omitted from the text. |
| 2. Linguistic accuracy | 7/10 | The text incorrectly translates "Я бачив це" as "I was looking at it". "Бачити" means "to see"; "to look" is "дивитися". |
| 3. Pedagogical quality | 6/10 | Quizzes testing both aspects are placed at the end of Section 2, before the perfective aspect is taught in Section 3. |
| 4. Vocabulary coverage | 7/10 | All required vocabulary is included, but recommended words "одноразовий" and "концепція" are missing. |
| 5. Exercise quality | 9/10 | Activity markers match the plan exactly in number and focus, though their placement needs fixing (deducted in Pedagogy). |
| 6. Engagement & tone | 10/10 | Excellent teacher persona. The movie vs. "The End" screen analogy is highly effective. |
| 7. Structural integrity | 8/10 | Excellent word count (2478 words), but missing English translations in headings breaks structural consistency with the plan. |
| 8. Cultural accuracy | 10/10 | Explains aspect natively without comparing it directly to Russian, using standard Ukrainian pedagogical tricks ("Що робити?"). |
| 9. Dialogue & conversation quality | 10/10 | The football match dialogue perfectly demonstrates the grammar points in a natural context. |

## Findings
[Plan adherence] [Major]
Location: Section headings
Issue: The plan specifies English translations in the H2 headings, but 3 out of 4 headings omitted them.
Fix: Add the English translations to the headings for Sections 1, 2, and 4.

[Pedagogical quality] [Critical]
Location: End of Section 2
Issue: Activity markers `aspect-sorting-process-result` and `identify-aspect-in-sentences` are placed before the perfective aspect is taught, meaning learners cannot successfully complete them.
Fix: Move these two markers to the end of Section 3.

[Linguistic accuracy] [Critical]
Location: Section 4, paragraph 1: "«Я бачив це» *(I saw this, I was looking at it)*"
Issue: "Бачити" means "to see", not "to look". Translating it as "I was looking at it" teaches incorrect vocabulary (confusing it with "дивитися").
Fix: Change the translation to "I saw this" and adjust the perfective translation to "I spotted it, I caught sight of it".

[Plan adherence] [Major]
Location: Entire text
Issue: Mandatory references (Заболотний Grade 6, ULP) and recommended vocabulary ('одноразовий', 'концепція') are missing.
Fix: Integrate the references and missing vocabulary naturally into the prose.

## Verdict: REVISE
The text is highly engaging and explains the concept well, but suffers from a critical pedagogical sequencing error (testing before teaching) and a critical semantic mistranslation of "бачити". Applying the fixes will bring it fully up to standard.

<fixes>
- find: "## Що таке вид дієслова?"
  replace: "## Що таке вид дієслова? (What is Verb Aspect?)"
- find: "## Недоконаний вид: Процес і повторення"
  replace: "## Недоконаний вид: Процес і повторення (Imperfective: Process & Repetition)"
- find: "## Порівняння пар: Бачимо різницю"
  replace: "## Порівняння пар: Бачимо різницю (Comparing Pairs: Seeing the Difference)"
- find: "<!-- INJECT_ACTIVITY: aspect-sorting-process-result -->\n<!-- INJECT_ACTIVITY: identify-aspect-in-sentences -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: match-up-context-aspect -->"
  replace: "<!-- INJECT_ACTIVITY: aspect-sorting-process-result -->\n<!-- INJECT_ACTIVITY: identify-aspect-in-sentences -->\n<!-- INJECT_ACTIVITY: match-up-context-aspect -->"
- find: "«Я бачив це» *(I saw this, I was looking at it)* versus «Я побачив це» *(I spotted it)*."
  replace: "«Я бачив це» *(I saw this)* versus «Я побачив це» *(I spotted it, I caught sight of it)*."
- find: "When Ukrainian children learn grammar in school, they do not memorize long lists"
  replace: "When Ukrainian children learn grammar in school textbooks (like Заболотний for Grade 6), they do not memorize long lists"
- find: "Keep this in mind, and you will navigate Ukrainian verbs with confidence."
  replace: "Keep this in mind, and you will navigate Ukrainian verbs with confidence. For further listening, resources like the Ukrainian Lessons Podcast (ULP) offer excellent audio practice for verb aspects."
- find: "The concept of aspect is not about time at all."
  replace: "This **концепція** (concept) of aspect is not about time at all."
- find: "It describes a **завершена дія** (completed action)."
  replace: "It describes a **завершена дія** (completed action) or an **одноразовий** (single, one-time) event."
</fixes>