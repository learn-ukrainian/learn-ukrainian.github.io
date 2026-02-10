# Рецензія: The Locative: Where Things Are

**Level:** A1 | **Module:** 13
**Overall Score:** 8.0/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Most required words used. Extra words: вухо, муха, війна, ліжко]
- Grammar scope: [Minor creep: Ordinal Locative 'другому', Future Perfective 'Зустрінемося']
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good cultural hooks (Shevchenko, Maidan). |
| 2 | Coherence | 8/10 | <7 | Clear explanations, but one euphony rule example contradicts the rule. |
| 3 | Relevance | 9/10 | <7 | Essential skill for navigation. |
| 4 | Educational | 8/10 | <7 | Solid core, but missing the "Neuter -ko -> -u" rule despite using it. |
| 5 | Language | 8/10 | <8 | Euphony error in text example; 'при Марії' is awkward for A1. |
| 6 | Pedagogy | 7/10 | <7 | Confusion between 'park/partsi' rule and 'parku' exception; missing 'lizhko' rule. |
| 7 | Immersion | 8/10 | <6 | Good usage of Ukrainian context. |
| 8 | Activities | 7/10 | <7 | Multiple euphony errors in answer keys (forcing 'у' after vowels). |
| 9 | Richness | 9/10 | <6 | Good variety of examples. |
| 10 | Beginner Safety | 8/10 | <7 | Generally safe, though 'partsi/parku' might confuse. |
| 11 | LLM Fingerprint | 8/10 | <7 | No major hallucinations, mostly natural. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Euphony rules misapplied in text and activities. |

**Weighted Overall:** (8*1.5 + 8*1 + 9*1 + 8*1.2 + 8*1.1 + 7*1.2 + 8*1 + 7*1.3 + 9*0.9 + 8*1.3 + 8*1 + 8*1.5) / 14.0 = **7.96/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [Minor: 'другому' (ordinal locative)]
- Activity errors: [Euphony mismatches in 3 items]
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Euphony Error in Presentation
- **Location**: Line 77 / Section "The Euphony Rule"
- **Original**: "Use **у** if the previous word ends in a consonant and the next word starts with a consonant: *Він працює **у** школі.*"
- **Problem**: The word `працює` ends in a vowel /e/, not a consonant. Therefore, the rule "Use **у**... if previous word ends in consonant" is not met by the example. The correct euphony here would actually be `в` (Vowel + `в` + Consonant).
- **Fix**: Change example to: "*Він жив **у** школі.*" or "*Брат **у** школі.*" (Ends in consonant).

### Issue 2: Awkward Example "при Марії"
- **Location**: Line 47 / Section "Locative Case Endings"
- **Original**: "Марі**я** → при Марі**ї**"
- **Problem**: While grammatically correct, `при` (at/by/during) is not the primary spatial preposition taught here (в/на). Location "in/on Maria" is weird.
- **Fix**: Replace with `лінія → на лінії` (on the line) or `станція → на станції` (at the station). Keep `армія → в армії`.

### Issue 3: Missing Rule for Neuter -ko
- **Location**: Line 159 / Section "Production"
- **Original**: "Мій телефон **на ліжку**."
- **Problem**: The student was taught "Neuter ends in -i" (вікно -> на вікні). `Ліжко` ends in -o, but becomes `ліжку`. This follows the unstated rule that neuters in `-ко` often take `-у`. Without explanation, this looks like an error to a student who learned `ліжці` (k->ts + i) or `ліжкі`.
- **Fix**: Add a [!note] or explanation in Presentation: "Note: Neuter nouns ending in **-ко** (like **ліжко**, **яблуко**) often take **-u** in the Locative: **на ліжку**."

### Issue 4: Activity Euphony Errors
- **Location**: Activities File, `type: fill-in`, `title: Preposition Choice`
- **Original**: "Ми ___ Львові. Answer: у", "Діти ___ школі. Answer: у", "Ми ___ центрі. Answer: у"
- **Problem**: In all these cases, the previous word ends in a vowel (`Ми`, `Діти`). The euphony rule dictates `в` (Vowel + `в` + Consonant). The answer key forces `у`, which creates a hiatus and is less natural.
- **Fix**: Change the subject to end in a consonant to justify `у`, e.g., "Брат ___ Львові", "Син ___ школі", "Він ___ центрі".

## Fix Plan to Reach 9/10

### Language & Linguistic Accuracy: 8/10 → 9/10

**What to fix:**
1.  Line 77 (`13-the-locative-where-things-are.md`): Change "Він працює у школі" → "Він жив у школі" to match the consonant rule.
2.  Line 47 (`13-the-locative-where-things-are.md`): Replace "Марія → при Марії" with "станція → на станції".

### Pedagogy: 7/10 → 9/10

**What to fix:**
1.  Section "Locative Case Endings" (`13-the-locative-where-things-are.md`): Add a note about the `-ko` -> `-u` exception for neuters, or change the Production example `на ліжку` to `на вікні` or `на кріслі` (chair - `крісло` -> `кріслі`). Changing the example is easier: "Мій телефон **на столі**" or "**на кріслі**".

### Activities: 7/10 → 9/10

**What to fix:**
1.  Activity `Preposition Choice` (`13-the-locative-where-things-are.yaml`):
    - Change "Ми ___ Львові" → "Брат ___ Львові" (Corrects answer `у`).
    - Change "Діти ___ школі" → "Син ___ школі" (Corrects answer `у`).
    - Change "Ми ___ центрі" → "Він ___ центрі" (Corrects answer `у`).
    - Change "Де діти? — Вони ___ школі" (Quiz item 5) → "Де учень? — Він ___ школі" (Corrects answer `у`).

### Projected Overall After Fixes

```
(9*1.5 + 8*1 + 9*1 + 9*1.2 + 9*1.1 + 9*1.2 + 8*1 + 9*1.3 + 9*0.9 + 8*1.3 + 8*1 + 9*1.5) / 14.0 = 8.75 -> 9.0 (rounded)
```

## Verdict

**FAIL**

The module is solid in concept but suffers from sloppy application of euphony rules (teaching one thing but examples doing another, or answer keys being incorrect). The "Neuter -ko" exception in the production task is also a pedagogical trap. These must be fixed to ensure the learner isn't confused by contradictory rules.