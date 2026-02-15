# Review: Структура речення

**Level:** B1 | **Module:** M04
**Overall Score:** 9.0/10
**Status:** ✅ PASS
**Reviewed:** 2026-02-14

## Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| Experience Quality | 9/10 | Excellent analogies (architecture/house) make abstract grammar concrete and understandable. |
| Coherence | 10/10 | Logical progression from sentence members to sentence types to punctuation. |
| Relevance | 10/10 | Directly addresses the module goal; establishing the terminology is crucial for future grammar modules. |
| Educational | 9/10 | Strong "Why it matters" section; the "Syntactic Parsing" cultural context is very motivating. |
| Language | 10/10 | Natural, idiomatic Ukrainian. Dialogues feel authentic and lively. |
| Pedagogy | 9/10 | Clear PPP structure. Examples are well-chosen to illustrate the rules. |
| Immersion | 10/10 | Meets the B1 bridge target; English is used only where necessary for clarity. |
| Activities | 8/10 | Good variety, but one activity introduces a term ("Службова частина мови") not explicitly taught in the text. |
| Richness | 8/10 | Cultural callouts regarding the "National Standard" of underlining are excellent. |
| Humanity | 10/10 | The "Architect" persona is engaging and encouraging. |
| LLM Fingerprint | 9/10 | Writing feels bespoke and tailored, avoiding generic "In this module" filler. |
| Linguistic Accuracy | 8/10 | Generally high, but the "Direct Object" definition is slightly too absolute (ignoring Genitive of negation), and one header is misleading. |

## Summary

This is a strong, well-structured module that effectively gamifies the potentially dry topic of syntactic analysis by framing it as "architecture." The cultural context regarding the Ukrainian school tradition of parsing is a brilliant touch that adds depth and motivation. The explanations are clear, the analogies work well, and the language quality is high. A few minor linguistic simplifications and one misleading header need correction to ensure precision, but overall, it is a high-quality bridge module.

## Issues Found

### Issue 1: Misleading Header Terminology
**Location:** `curriculum/l2-uk-en/b1/sentence-structure.md`, section "Підмет (Subject)", Callout `[!tip]`
**Original:** «Пасивність чи активність?»
**Problem:** The tip explains that "Мені холодно" is an impersonal construction where "Мені" is an object, not a subject. However, the header "Passivity or Activity?" suggests a discussion of Passive Voice (Пасивний стан), which is a different grammatical concept. This might confuse learners who know grammatical terms.
**Suggested Fix:** Rename the header to "Підмет чи додаток?" or "Безособові конструкції"
**Severity:** minor

### Issue 2: Overly Absolute Rule (Direct Object)
**Location:** `curriculum/l2-uk-en/b1/sentence-structure.md`, section "Додаток (Object)"
**Original:** «Він завжди стоїть у Знахідному відмінку без прийменника (Accusative without preposition).»
**Problem:** While correct for the majority of cases at this level, strictly speaking, a direct object can also be in the Genitive case (Genitive of negation, e.g., "не бачу змісту", or partitive, e.g., "купив хліба"). Using "завжди" (always) sets the learner up for confusion later.
**Suggested Fix:** Change to: «Він найчастіше стоїть у Знахідному відмінку без прийменника (або в Родовому при запереченні).» or simply remove "завжди".
**Severity:** minor

### Issue 3: Undefined Term in Activity
**Location:** `curriculum/l2-uk-en/b1/activities/sentence-structure.yaml`, Activity `match-up`
**Original:** «right: 'Службова частина мови (і, а, але, що)'»
**Problem:** The term "Службова частина мови" (Service part of speech) is used in the definition for "Сполучник", but this specific meta-term is not introduced in the module text. The text only defines conjunctions functionally ("Слова, які з'єднують...").
**Suggested Fix:** Change the definition to match the text's functional approach: «right: 'Слово, що з'єднує частини речення (і, а, але, що)'».
**Severity:** minor

## Recommendation

✅ PASS — High-quality bridge module with effective architectural metaphor and culturally embedded content. Three minor issues should be addressed but none are blocking.
