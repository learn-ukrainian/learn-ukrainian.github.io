# Green Team Review: reading-grammar-rules

## Module Info
- Level: B1 M03
- Type: Bridge (Metalanguage)
- Reviewer: Green Team (Independent)

## "Did I Learn?" Test
1. **Did I learn something new?** Pass — The distinction between "кінець" (physical end) and "закінчення" (grammatical ending) was a specific, useful nuance I hadn't considered.
2. **Was the explanation clear?** Pass — The breakdown of patterns like "X використовується..." was logical and easy to follow.
3. **Could I apply this in conversation?** Pass — I feel equipped to ask "Що означає це слово?" or discuss "розмовна мова".
4. **Was I appropriately challenged?** Pass — The heavy use of Ukrainian for meta-explanations is a good challenge for B1.0.
5. **Did the teacher voice guide me?** Pass — The tone is encouraging ("Вітаю вас, колего!") and guides through potential confusion well.

**Teaching Quality: 9/10**

## Dimension Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Experience Quality | 9/10 | Feels like a genuine seminar on how to learn, not just a list of rules. |
| 2 | Coherence | 10/10 | Excellent logical progression from "why" to "patterns" to "practice". |
| 3 | Relevance | 10/10 | Highly relevant for independent learning; gives the learner tools to fish. |
| 4 | Educational | 9/10 | Strong mix of TTT and PPP; explicit instruction on learning strategies. |
| 5 | Language | 9/10 | Meets the 80% immersion target effectively; English used only for necessary scaffolding. |
| 6 | Pedagogy | 9/10 | Good focus on "decoding" and pattern recognition. |
| 7 | Immersion | 8/10 | Good, but some English callouts could arguably be simple Ukrainian at this stage. |
| 8 | Activities | 7/10 | Some distractors are too childish for B1; one instruction verb is untested in theory. |
| 9 | Richness | 9/10 | Excellent cultural references (Smotrytsky, Ohiienko). |
| 10 | Humanity | 10/10 | "Вітаю вас, колего!", "Увага! Тут студенти часто роблять помилку." |
| 11 | LLM Fingerprint | 9/10 | Mostly natural, though "Це величезний крок..." is a bit cliché. |
| 12 | Linguistic Accuracy | 8/10 | Promoting suffix "-тель" is risky; "даний час" is stylistically poor. |
| 13 | Propaganda Filter | 10/10 | Celebrates Ukrainian linguistic history (Smotrytsky). |
| 14 | Semantic Nuance | 10/10 | Excellent distinction between style and register. |

**Overall: 9.1/10**

## Issues Found

### Issue 1: [MAJOR] Missing IPA in Vocabulary
- **Location:** `curriculum/l2-uk-en/b1/vocabulary/reading-grammar-rules.yaml`
- **Quote:** N/A (Missing data)
- **Problem:** The vocabulary file contains `lemma`, `translation`, etc., but is completely missing `ipa` fields. Project standards require IPA for all B1 vocabulary.
- **Fix:** Run the enrichment script or manually add IPA transcriptions for all items.

### Issue 2: [MINOR] Risky Suffix Recommendation
- **Location:** Section "Діалог 4: Словотвір та корені"
- **Quote:** «В українській це часто суфікс -ник, -ач або **-тель**.»
- **Problem:** Listing **-тель** as a top-3 productive agent suffix is misleading. While present in standard words (*вчитель*, *вихователь*), it is far less productive than *-ець* and often flags Russian calques in learner speech (*строїтель*, *покупатель*, *водитель*). Promoting it early encourages Surzhyk.
- **Fix:** Replace «-тель» with «-ець» (e.g., *фахівець*, *знавець*, *продавець*).

### Issue 3: [MINOR] Missing Instruction Verb in Theory
- **Location:** Activities vs. Text
- **Quote:** Activity `match-up` uses «**Вставте**», but the text section "Дієслова для виконання вправ" lists «Заповніть» but not «Вставте».
- **Problem:** The activity tests a verb that was not explicitly taught in the theory section, violating the "Explain then Practice" flow for specific vocabulary.
- **Fix:** Add «Вставте» to the "Дії структурування" list in the text.

### Issue 4: [MINOR] Stylistic Calque "Даний"
- **Location:** Section "Вправа на «декодування»"
- **Quote:** «**Даний** час вживається для позначення регулярної...»
- **Problem:** Usage of "даний" as "this/present" (calque from Russian "данный") is considered poor style in modern Ukrainian (should be "цей" or "нинішній"). While it might mimic old academic texts, using it as a model sentence without comment risks teaching bad style.
- **Fix:** Change to «**Цей** час вживається...» or add a note that "даний" is common in older texts but discouraged in modern ones.

### Issue 5: [MINOR] Weak Activity Distractors
- **Location:** Activity `quiz`
- **Quote:** Distractors for "маркер": «Фломастер для виділення тексту», «Оцінка за тест».
- **Problem:** Distractors are too obvious and childish for a B1 adult learner. They don't test linguistic understanding, just common sense.
- **Fix:** Use plausible linguistic distractors, e.g., "Частина слова", "Розділовий знак".

## Strengths
- **Meta-Cognition:** The module effectively teaches *how to learn* Ukrainian using Ukrainian resources, which is high-leverage.
- **Cultural Depth:** Integrating Smotrytsky and Ohiienko into a grammar module adds excellent depth and avoids dry theory.
- **Practical Analysis:** The "Did I Learn?" concepts (difference between *ending* and *end*) are very practical for avoiding common learner mistakes.

## Summary
A strong, pedagogically sound module that serves as an excellent bridge to B1 learning. The content is engaging, human, and culturally rich. However, the **missing IPA data** in the vocabulary file is a significant technical oversight that must be fixed. Minor adjustments to the linguistic examples (avoiding "-тель", fixing "даний") will polish the linguistic accuracy to the required standard.
