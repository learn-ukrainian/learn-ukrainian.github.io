## Linguistic Scan
- `## Мені подобається: Давальний відмінок досвідника...` contains `досвідника`, which is not attested in the provided VESUM data and did not return a dictionary entry in local lookup.
- `Мені дуже подобається тепле літо і море.` has wrong agreement: with the coordinated nominative subject `тепле літо і море`, the verb should be plural.
- `Наприклад, дієслова «бачити», «знати», «любити» та «чекати» мають прямий додаток.` plus `...ми використовуємо тільки знахідний відмінок.` teaches an overbroad rule. Local dictionary lookup for `чекати` gives `кого, чого, що, на кого — що`, so it is not accusative-only.
- `У першому випадку людина є об text об'єктом дії...` contains a broken mixed-language fragment.

## Exercise Check
All 4 planned activity markers are present:
- `fill-in-dative-verbs`
- `match-up-podobatysia`
- `true-false-age`
- `quiz-dative-vs-accusative`

They are correctly placed after the relevant teaching sections and are spread evenly through the module. No inline DSL exercise blocks are present, so exercise logic beyond marker placement is not observable here.

Issue found:
- The `match-up` marker still has raw scaffold text after it: `[match-up, Match подобатися sentences to their English equivalents (reversed subject mapping), 8 items]`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned H2 sections are present and each `activity_hints` item has a corresponding marker, but the final comparison section overstates `чекати` as accusative-only. |
| 2. Linguistic accuracy | 5/10 | Critical defects: non-standard `досвідника`, wrong agreement in `Мені дуже подобається тепле літо і море`, broken `об text об'єктом`, and the false accusative-only rule for `чекати`. |
| 3. Pedagogical quality | 6/10 | The module gives many examples, but it undermines its own `подобатися` agreement rule with `Мені дуже подобається тепле літо і море` and presents `чекати` too categorically. |
| 4. Vocabulary coverage | 9/10 | All required plan vocabulary appears in prose, including `допомагати`, `дякувати`, `дзвонити`, `радити`, `заважати`, `подобатися`, `відповідати`, `рік`, `роки`, `років`. |
| 5. Exercise quality | 8/10 | All 4 planned markers are present, correctly sequenced, and aligned to the taught sections; however the `match-up` marker still has raw scaffold text after it. |
| 6. Engagement & tone | 8/10 | The volunteer-day, preference, and age scenarios keep the lesson concrete, and the tone stays teacherly rather than gamified. |
| 7. Structural integrity | 6/10 | All core sections are present and the pipeline word count is 3070, but there is a visible formatting artifact `об text об'єктом` and leftover scaffold text after one activity marker. |
| 8. Cultural accuracy | 9/10 | The module explains Ukrainian structures on their own terms and does not rely on Russian comparison framing. |
| 9. Dialogue & conversation quality | 8/10 | The age dialogue is a natural gift-buying scenario and the `подобатися` exchange is multi-turn rather than purely transactional. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Мені подобається: Давальний відмінок досвідника (The Experiencer Dative with подобатися) (~550 words)`  
Issue: `досвідника` is not standard Ukrainian grammar terminology here and is not attested in the provided VESUM data or local dictionary lookup.  
Fix: Replace the heading with a standard formulation, e.g. `Давальний відмінок з подобатися`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Мені дуже подобається тепле літо і море.`  
Issue: The verb is singular even though the nominative subject is coordinated (`тепле літо і море`), so this contradicts the module’s own agreement explanation.  
Fix: Change `подобається` to `подобаються`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Наприклад, дієслова «бачити», «знати», «любити» та «чекати» мають прямий додаток.` and `...тому ми використовуємо тільки знахідний відмінок.`  
Issue: This teaches a false rule. Local dictionary lookup for `чекати` gives `кого, чого, що, на кого — що`, so `чекати` is not accusative-only.  
Fix: Remove `чекати` from the accusative-only claim or explicitly note that it can also govern other patterns.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: `У першому випадку людина є об text об'єктом дії, а в другому — отримувачем.`  
Issue: `text` is a stray formatting artifact inside a Ukrainian sentence.  
Fix: Delete `text` so the sentence reads `є об'єктом дії`.

[EXERCISE QUALITY] [SEVERITY: minor]  
Location: `<!-- INJECT_ACTIVITY: match-up-podobatysia --> [match-up, Match подобатися sentences to their English equivalents (reversed subject mapping), 8 items]`  
Issue: Raw scaffold metadata remains visible after the marker.  
Fix: Leave only the marker.

## Verdict: REVISE
The module is structurally complete and the activity coverage is in place, but it contains multiple critical linguistic inaccuracies and one major formatting artifact. These are targeted, patchable defects, so this is a revise-not-reject case.

<fixes>
- find: "## Мені подобається: Давальний відмінок досвідника (The Experiencer Dative with подобатися) (~550 words)"
  replace: "## Мені подобається: Давальний відмінок з подобатися (The Experiencer Dative with подобатися) (~550 words)"
- find: "Мені дуже подобається тепле літо і море."
  replace: "Мені дуже подобаються тепле літо і море."
- find: "Наприклад, дієслова «бачити», «знати», «любити» та «чекати» мають прямий додаток."
  replace: "Наприклад, дієслова «бачити», «знати» та «любити» мають прямий додаток. Дієслово «чекати» часто вживається зі знахідним, але можливі й інші моделі керування."
- find: "У цих ситуаціях дія прямо спрямована на людину, тому ми використовуємо тільки знахідний відмінок."
  replace: "У цих прикладах дія прямо спрямована на людину, тому ми використовуємо знахідний відмінок."
- find: "У першому випадку людина є об text об'єктом дії, а в другому — отримувачем."
  replace: "У першому випадку людина є об'єктом дії, а в другому — отримувачем."
- find: "<!-- INJECT_ACTIVITY: match-up-podobatysia --> [match-up, Match подобатися sentences to their English equivalents (reversed subject mapping), 8 items]"
  replace: "<!-- INJECT_ACTIVITY: match-up-podobatysia -->"
</fixes>