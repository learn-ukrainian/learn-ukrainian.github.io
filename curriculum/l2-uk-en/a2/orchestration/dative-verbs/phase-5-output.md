===REVIEW_START===
# Рецензія: Dative Verbs

**Level:** A2 | **Module:** 3
**Overall Score:** 6.9/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS] All outline sections present.
- Vocabulary: [FAIL] Missing required words from plan: "симпатизувати", "вистачати". The `vocabulary.yaml` file contains many unrelated words not in the text (e.g., дні тижня, дощ, героїня, важок, курити).
- Grammar scope: [PASS] Follows scope well.
- Objectives: [PASS] Objectives addressed.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 6/10 | <7 | Broken activity ("Complete the Story") makes the practice section confusing and frustrating. |
| 2 | Coherence | 8/10 | <7 | Explanations are logical and flow well. |
| 3 | Relevance | 9/10 | <7 | Topic is essential for A2. |
| 4 | Educational | 6/10 | <7 | The "ранити" error teaches the wrong meaning for a word. |
| 5 | Language | 8/10 | <8 | Generally natural, but the "ранити" error is critical. |
| 6 | Pedagogy | 6/10 | <7 | Activities have grammatical errors (subject-verb agreement). |
| 7 | Immersion | 8/10 | <6 | Good balance of English explanation and Ukrainian examples. |
| 8 | Activities | 3/10 | <7 | One activity is completely broken with nonsensical gaps and grammar errors. |
| 9 | Richness | 7/10 | <6 | Content is good, but vocabulary file is noisy/hallucinated. |
| 10 | Beginner Safety | 6/10 | <7 | Users will fail the cloze activity due to bugged questions, leading to frustration. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally human-sounding, but the broken activity is a typical LLM generation artifact. |
| 12 | Linguistic Accuracy | 8/10 | <9 | "Ранити" definition error; "Батьки" (pl) with singular verbs in activity. |

**Weighted Overall:** (6*1.5 + 8*1.0 + 9*1.0 + 6*1.2 + 8*1.1 + 6*1.2 + 8*1.0 + 3*1.3 + 7*0.9 + 6*1.3 + 8*1.0 + 8*1.5) / 14.0 = **6.86/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] Multiple errors in `cloze` activity "Complete the Story".
- Beginner safety: 3/5 (Frustrated by broken activity)

## Critical Issues Found

### Issue 1: Dangerous Typo (Wrong Definition)
- **Location**: Section "Presentation", Subsection "Dative + Accusative Verbs"
- **Original**: "verbs of communication like **розповідати** (to tell) and **ранити** (to advise)."
- **Problem**: **ранити** means "to wound" or "to hurt". The word for "to advise" is **радити**. This teaches students to say "I wound you" instead of "I advise you".
- **Fix**: Change "**ранити**" to "**радити**".

### Issue 2: Broken Cloze Activity (Nonsense Gaps)
- **Location**: Activity `cloze` titled "Complete the Story", Gap 1
- **Original**: "Щодня вона {Йому|Його|Він} учням нові теми."
- **Problem**: The gap options are pronouns, but the sentence structure requires a verb (e.g., "пояснює"). The resulting sentence "Щодня вона Він учням..." is nonsense.
- **Fix**: Change options to verbs, e.g., `{пояснює|пояснювати|пояснюється}`.

### Issue 3: Broken Cloze Activity (Subject-Verb Agreement)
- **Location**: Activity `cloze` titled "Complete the Story", Paragraph 1
- **Original**: "Батьки {каже|говорить|розповідає} Марії за хорошу роботу."
- **Problem**: Subject "Батьки" is plural. All options ("каже", "говорить", "розповідає") are singular. No correct answer exists.
- **Fix**: Change options to plural forms: `{дякують|кажуть|говорить}`. (Also "дякують" fits the context "за роботу" better than "кажуть").

### Issue 4: Broken Cloze Activity (Case Government)
- **Location**: Activity `cloze` titled "Complete the Story", Paragraph 1
- **Original**: "Директор {дякує|дякувати} їй нову методику."
- **Problem**: "Дякувати" requires Dative person + "за" + Accusative thing. The sentence has direct Accusative thing "нову методику" without "за". "Директор дякує їй нову методику" is grammatically incorrect.
- **Fix**: Rephrase sentence to "Директор {дякує} їй за нову методику." or change verb to "презентує" (presents).

### Issue 5: Broken Cloze Activity (Semantic Nonsense)
- **Location**: Activity `cloze` titled "Complete the Story", Paragraph 1
- **Original**: "Марія {дозволяють|дозволяти|дозволяється} колегам свій досвід."
- **Problem**: "Марія allow her experience to colleagues" makes no sense. Plus, "Марія" (singular) has no matching singular verb option (options are pl, inf, refl).
- **Fix**: Change sentence to something logical like "Марія {передає} колегам свій досвід" (transmits) or change options to fit context.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Text | "**ранити** (to advise)" | "**радити** (to advise)" | Lexical Error |
| Activity | "Батьки {каже}..." | "Батьки {кажуть}..." | Grammar (Agreement) |
| Activity | "дякує їй нову методику" | "дякує їй **за** нову методику" | Grammar (Government) |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Fail (Activity blocks progress)
- Ukrainian scary? Pass
- Come back tomorrow? Fail (Broken tools decrease trust)

## Fix Plan to Reach 9/10

### Text Content: 8/10 → 10/10

**What to fix:**
1. Section "Presentation": Change "**ранити** (to advise)" → "**радити** (to advise)" — Prevents teaching a dangerous false friend.

### Activities: 3/10 → 9/10

**What to fix:**
1. Activity `cloze` ("Complete the Story"): Rewrite the **entire** activity passage and options. The current generation is incoherent.
   - **Suggested Passage**: "Марія працює вчителькою. Щодня вона {пояснює|пояснювати|пояснюється} учням нові теми. Коли учень не розуміє, вона {допомагає|заважає|дякує} йому. Марія {любить|пробачає|знає} своїх учнів — вони старанні. Батьки {дякують|каже|говорить} Марії за хорошу роботу. Директор {дає|дякувати|бере} їй премію за нову методику. Марія {передає|дозволяти|дозволяється} колегам свій досвід."
   - Ensure every gap has exactly one grammatically and semantically correct answer.

### Vocabulary: 7/10 → 9/10

**What to fix:**
1. `vocabulary.yaml`: Remove unrelated words (дощ, важок, героїня, дні тижня). Ensure list matches the content (допомагати, дякувати, вірити, радити, etc.).

### Projected Overall After Fixes

With "Activities" raised to 9 and "Language" to 10:
Overall ≈ **9.2/10**

## Verification Summary

- Content lines read: All
- Activity items checked: 11 activities
- Issues found: 5 critical issues
- Naturalness score recommendation: 9/10 (after text fix)

## Verdict

**FAIL**

The module fails primarily due to a completely broken "Complete the Story" activity which contains nonsense gaps, grammatical agreement errors, and case government violations. Additionally, the text defines "to advise" as "ранити" (to wound), which is a critical lexical error.

===REVIEW_END===
