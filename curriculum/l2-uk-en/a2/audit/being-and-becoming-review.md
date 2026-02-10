# Рецензія: Being and Becoming

**Level:** A2 | **Module:** 6
**Overall Score:** 8.6/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Most required words present; 'письменник', 'актор', 'директор' used but missing from vocabulary.yaml]
- Grammar scope: [clean - Future tense introduced as planned]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear progression, good explanations. |
| 2 | Coherence | 8/10 | <7 | Contradiction between "Use feminitives" tip and "Мама працює економістом" example. |
| 3 | Relevance | 10/10 | <7 | Highly relevant professional vocabulary. |
| 4 | Educational | 9/10 | <7 | Concept of "Role vs Identity" well explained. |
| 5 | Language | 8/10 | <8 | "більше двадцять років" (grammar error); "Новина в тому" (awkward phrasing). |
| 6 | Pedagogy | 9/10 | <7 | Solid PPP structure. |
| 7 | Immersion | 8/10 | <6 | Good mix, though English meta-text is dominant in explanations. |
| 8 | Activities | 8/10 | <7 | One unjumble item has grammar error; inconsistent gender usage in one item. |
| 9 | Richness | 9/10 | <6 | High word count, detailed examples. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Friendly tone. |
| 11 | LLM Fingerprint | 8/10 | <7 | "This shift is subtle but very important" (typical filler). |
| 12 | Linguistic Accuracy | 8/10 | <9 | **CRITICAL**: Incorrect IPA stress for `лікар`, `вчитель`, `лікарка`, `вчителька`. |

**Weighted Overall:** (13.5 + 8 + 10 + 10.8 + 8.8 + 10.8 + 8 + 10.4 + 8.1 + 11.7 + 8 + 12) / 14.0 = **8.57/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [list] "Новина в тому" (The news is...) -> "Справа в тому..." or "Важливо те..."
- Grammar scope: [CLEAN]
- Activity errors: [list] Unjumble item "більше двадцять років" (case error).
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: IPA Stress Errors (Critical)
- **Location**: `vocabulary.yaml`
- **Original**:
    - `лікар`: `/lʲikˈar/`
    - `вчитель`: `/ʋt͡ʃˈɪtɛlʲ/` (stress on 2nd syll in IPA usually marked before it? No, IPA stress is `'` before the stressed syllable. `/ʋt͡ʃˈɪtɛlʲ/` puts stress on `ɪ`. Wait. `вчи́тель` has stress on `и`. So `/ʋt͡ʃˈɪtɛlʲ/` IS correct? No, `ʋt͡ʃ` is onset. Stress mark `'` precedes the syllable. `/ʋt͡ʃˈɪtɛlʲ/` means stress on `tel`? No, stress mark is before `ɪ`. So `ɪ` is stressed. Wait. `вчитель` [ʋt͡ʃˈɪtɛlʲ]. If stress is on `и`, it is `ʋt͡ʃˈɪ`. Yes. Okay, let me re-verify `лікар`).
    - `лікар`: `/lʲikˈar/`. Stress mark before `a`. Means stress on `ar`. **WRONG**. Should be `/lʲˈikar/` or `/lʲikˈar/`? Ukrainian is `лі́кар`. Stress on 1st.
    - `лікарка`: `/lʲikˈarka/`. Stress mark before `a` (2nd). Means `лі-КАР-ка`. **WRONG**. Should be `ЛІ-кар-ка`.
    - `вчителька`: `/ʋt͡ʃˈɪtɛlʲka/`. Stress before `ɪ`. `вчи́телька`. This one actually looks correct if `'` is before `ɪ`.
- **Problem**: Incorrect stress placement teaches wrong pronunciation.
- **Fix**: Update IPA to reflect root stress where appropriate. `лікар` -> `/lʲˈikar/`. `лікарка` -> `/lʲˈikarka/`.

### Issue 2: Grammar Error (Case Governance)
- **Location**: `activities/06-being-and-becoming.yaml` (Unjumble item 11)
- **Original**: "Він був директором цієї школи більше двадцять років"
- **Problem**: `більше` (more than) usually requires Genitive (`більше двадцяти років`) or construction `понад двадцять років`. `більше двадцять` sounds broken/illiterate.
- **Fix**: Change item to: `понад`, `двадцять`, `років`... OR change `двадцять` to `двадцяти`.

### Issue 3: Inconsistency with Pedagogy
- **Location**: `activities/06-being-and-becoming.yaml` (Practice 2, Item 5) & `a2-06.md` (Practice 2)
- **Original**: "Мама (економіст) у банку. -> Мама працює економістом..."
- **Problem**: The module explicitly advises: "When describing a woman, use the feminine form... Consistency is key". Using `економістом` (masc) for `Мама` contradicts this immediate advice.
- **Fix**: Change example to "Мама (економістка)... -> Мама працює економісткою..." OR use a profession with a more established feminitive like "менеджерка" or "вчителька".

### Issue 4: Vocabulary Gaps
- **Location**: `vocabulary.yaml` vs Content
- **Problem**: Words `письменник` (masc), `актор`, `директор` (masc) are used in text/activities but missing from `vocabulary.yaml` lemmas. Only feminitives or other forms are present.
- **Fix**: Add missing lemmas.

### Issue 5: Phrasing Calque
- **Location**: `a2-06.md` Section "The Verb To Be"
- **Original**: "Новина в тому, що для минулого..."
- **Problem**: "The news is that..." is not a standard Ukrainian transition here.
- **Fix**: "Важливо те, що..." or "Справа в тому, що..." or just "Але для минулого..."

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? No
- Instructions clear? Yes
- Quick wins? Yes, transformation drills are straightforward.
- Ukrainian scary? No
- Come back tomorrow? Yes

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 8/10 → 9+/10
**What to fix:**
1. **vocabulary.yaml**:
   - `лікар`: Change `/lʲikˈar/` → `/lʲˈikar/`
   - `лікарка`: Change `/lʲikˈarka/` → `/lʲˈikarka/`
   - Add lemma `письменник` (m).
   - Add lemma `актор` (m).
   - Add lemma `директор` (m).

### Activities: 8/10 → 9+/10
**What to fix:**
1. **activities/06-being-and-becoming.yaml**:
   - Item "Він був директором... більше двадцять років": Change `більше` to `понад`. Or change `двадцять` to `двадцяти`. (Recommend `понад двадцять років` as it keeps the numeral simple).
   - Item "Мама (економіст)...": Change to "Мама (економістка)..." and answer "економісткою".

### Coherence & Language: 8/10 → 9/10
**What to fix:**
1. **a2-06.md**:
   - Section "The Verb To Be": Change "Новина в тому, що..." → "Важливо пам'ятати, що..."
   - Section "Practice 2": Update the "Мама (економіст)" line to match the activity fix ("економістка" -> "економісткою").

## Verdict

**FAIL**

The module is structurally sound and educational, but contains critical errors in IPA stress (teaching wrong pronunciation) and grammar (case governance in activity), plus an internal pedagogical contradiction regarding feminitives. These must be fixed before release.