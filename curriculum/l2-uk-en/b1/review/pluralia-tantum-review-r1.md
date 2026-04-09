## Linguistic Scan
Found linguistic errors:
- "дверями" — Factually incorrect form presented as a standard alternative. VESUM confirms this form does not exist. The only standard forms are "дверима" (most common) and "дверми".
- "штан" — Factually incorrect form presented as a zero-ending genitive plural of "штани". VESUM confirms the only correct form is "штанів".
- "приймати форму" — Calque from Russian "принимать форму". In standard Ukrainian, grammar parts "набувають форми" or "мають форму".

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-identify-pluralia-tantum-which-nouns-exist-only-in -->` - Correctly placed after Section 1. Matches hint 1.
- `<!-- INJECT_ACTIVITY: group-sort-categories -->` - **ERROR**: Hallucinated marker, not present in the plan's hints. Also misplaced (cannot ask students to sort by singularia tantum before the concept is introduced).
- `<!-- INJECT_ACTIVITY: fill-in-genitive -->` - Correctly placed after Section 3. Matches hint 2.
- `<!-- INJECT_ACTIVITY: match-instrumental-forms -->` - Correctly placed after Section 3. Matches hint 4.
- `<!-- INJECT_ACTIVITY: fill-in-cases-of-pluralia-tantum-nouns -->` - **ERROR**: Hallucinated marker, not present in the plan's hints.
- `<!-- INJECT_ACTIVITY: group-sort-sort-nouns-into-pluralia-tantum-singularia-tantum-and-both-numbers -->` - Correctly placed after Section 5. Matches hint 3.
- `<!-- INJECT_ACTIVITY: error-correction-fix-agreement-errors-with-pluralia-tantum -->` - Correctly placed after Section 6. Matches hint 5.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed plan point in Section 3: "роковини (anniversary)" is entirely absent. Missed proper noun examples "Дунай" and "Харків" (swapped them for "Київ" and "Одеса"). Missed explicit citation of "Заболотний" and "Глазова" in the prose. |
| 2. Linguistic accuracy | 7/10 | Taught incorrect grammatical forms. Claims "штан" is a valid zero-ending genitive plural form for "штани". Claims "дверями" is a valid standard instrumental form for "двері". Minor Russian calque "приймати форму". |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical flow. Beautiful contrastive structure with singularia tantum. Fantastic explanations of the phonetic alternations (rules are clearly grounded in previous modules). |
| 4. Vocabulary coverage | 10/10 | All required vocabulary integrated seamlessly into context, not as bare lists. |
| 5. Exercise quality | 8/10 | The core exercises are great, but the writer generated 7 markers instead of the requested 5, injecting two unprompted and poorly timed activities (`group-sort-categories` and `fill-in-cases-of-pluralia-tantum-nouns`). |
| 6. Engagement & tone | 10/10 | Highly encouraging teacher persona, very natural flow without corporate gamification. |
| 7. Structural integrity | 9/10 | Word count is outstanding (4390 words), but the writer accidentally printed the plan's word target instruction directly into a header: `## Відмінювання (~700 words)`. |
| 8. Cultural accuracy | 10/10 | Strong emphasis on the authentic traditional "-ми" endings. Fully decolonized approach. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue is a natural, contextualized, real-world situation (packing boxes) that brilliantly highlights plural adjectives with pluralia tantum nouns. |

## Findings
[Linguistic accuracy] [Critical]
Location: "Іноді слова можуть мати паралельні форми, як **штани** *(trousers)*, які в родовому відмінку можуть бути «штанів» або просто «штан» (нульове закінчення)."
Issue: "штан" does not exist as a genitive plural of "штани" in Ukrainian ("штанів" is the only correct form). Presenting it as a legitimate grammatical rule is a factual error.
Fix: Remove the sentence entirely as the zero-ending logic is already sufficiently illustrated by "Карпат" and "воріт".

[Linguistic accuracy] [Critical]
Location: "Форми із закінченнями «-ами» або «-ями» («грошима», «воротами», «дверями») також є правильними" and "Ви можете голосно грюкнути «дверима» або «дверями»."
Issue: "дверями" is not a standard instrumental form for "двері" (only "дверима" or "дверми"). Presenting it as a standard modern alternative is factually incorrect.
Fix: Replace the "дверями" example with "санями" across the paragraph, and clarify that "двері" strictly retains its traditional ending.

[Linguistic accuracy] [Minor]
Location: "усі слова навколо них також повинні приймати форму множини." (and 2 other instances)
Issue: "приймати форму" is a calque from Russian "принимать форму". Standard Ukrainian prefers "набувати форми" or "мати форму".
Fix: Change to "мати форму".

[Plan adherence] [Major]
Location: "До цієї ж категорії впевнено та логічно належать важливі державні політичні **вибори** *(elections)* та романтичні весільні **заручини** *(engagement)*."
Issue: The plan explicitly required teaching `роковини (anniversary)` in this section, but it was omitted.
Fix: Add "та пам'ятні роковини (anniversary)" to the list.

[Plan adherence] [Major]
Location: "Наприклад, столиця **Київ** *(Kyiv)*, сонячна **Одеса** *(Odesa)*, найвища гора **Говерла** *(Hoverla)* та ім'я **Оксана** *(Oksana)*"
Issue: The plan specifically instructed using `Дунай` and `Харків` as examples. The writer swapped them for `Київ` and `Одеса`.
Fix: Restore `Дунай` and `Харків`.

[Plan adherence] [Minor]
Location: "Як зазначають українські підручники" and "У шкільному підручнику авторки Литвінової"
Issue: The plan requested references to Заболотний and Глазова, which were omitted from the text's explicit attribution.
Fix: Explicitly name the authors matching the plan outline.

[Exercise quality] [Major]
Location: `<!-- INJECT_ACTIVITY: group-sort-categories -->` and `<!-- INJECT_ACTIVITY: fill-in-cases-of-pluralia-tantum-nouns -->`
Issue: The writer hallucinated two extra activity markers that were not requested in the `activity_hints`.
Fix: Remove the extra markers.

[Structural integrity] [Minor]
Location: `## Відмінювання (~700 words)`
Issue: The plan's internal prompt instruction `(~700 words)` leaked into the final header.
Fix: Remove the word count from the header.

## Verdict: REVISE
The module contains critical linguistic errors (teaching non-existent word forms like "штан" and "дверями") and leaked internal prompt text into the headers. It must be revised before shipping.

<fixes>
- find: "біля високих «воріт», серед мальовничих **Карпат** *(Carpathians)*. Іноді слова можуть мати паралельні форми, як **штани** *(trousers)*, які в родовому відмінку можуть бути «штанів» або просто «штан» (нульове закінчення). Оскільки ці специфічні іменники не належать до жодної стандартної відміни"
  replace: "біля високих «воріт», серед мальовничих **Карпат** *(Carpathians)*. Оскільки ці специфічні іменники не належать до жодної стандартної відміни"
- find: "Ви можете голосно грюкнути «дверима» або «дверями». Ви можете стояти машиною перед «ворітьми» або «воротами». У чому полягає різниця між цими паралельними формами? Форми «грішми», «ворітьми» та «дверима» є глибоко традиційними"
  replace: "Ви можете їхати «саньми» або «санями». Ви можете стояти машиною перед «ворітьми» або «воротами». У чому полягає різниця між цими паралельними формами? Форми «грішми», «ворітьми» та «саньми» є глибоко традиційними"
- find: "Форми із закінченнями «-ами» або «-ями» («грошима», «воротами», «дверями») також є правильними стандартними сучасними варіантами."
  replace: "Форми із закінченнями «-ами» або «-ями» («грошима», «воротами», «санями») також є правильними стандартними сучасними варіантами."
- find: "Іншим чудовим прикладом є слово «сани» — в орудному відмінку ви можете їхати «саньми» або «санями»."
  replace: "Щодо слова «двері», то воно завжди зберігає традиційне закінчення: ми кажемо «дверима»."
- find: "усі слова навколо них також повинні приймати форму множини."
  replace: "усі слова навколо них також повинні мати форму множини."
- find: "В орудному відмінку воно обов'язково приймає те саме виразне історичне закінчення «-ми»:"
  replace: "В орудному відмінку воно обов'язково має те саме виразне історичне закінчення «-ми»:"
- find: "він все одно зобов'язаний прийняти форму множини."
  replace: "він все одно зобов'язаний мати форму множини."
- find: "До цієї ж категорії впевнено та логічно належать важливі державні політичні **вибори** *(elections)* та романтичні весільні **заручини** *(engagement)*."
  replace: "До цієї ж категорії впевнено та логічно належать важливі державні політичні **вибори** *(elections)*, романтичні весільні **заручини** *(engagement)* та пам'ятні **роковини** *(anniversary)*."
- find: "Наприклад, столиця **Київ** *(Kyiv)*, сонячна **Одеса** *(Odesa)*, найвища гора **Говерла** *(Hoverla)* та ім'я **Оксана** *(Oksana)*"
  replace: "Наприклад, столиця **Київ** *(Kyiv)*, річка **Дунай** *(Danube)*, найвища гора **Говерла** *(Hoverla)*, місто **Харків** *(Kharkiv)* та ім'я **Оксана** *(Oksana)*"
- find: "Як зазначають українські підручники, до жодної відміни не належать незмінювані запозичені слова, як-от **таксі** *(taxi)*"
  replace: "Як зазначає підручник О. Заболотного для шостого класу, до жодної відміни не належать незмінювані запозичені слова, як-от **таксі** *(taxi)*"
- find: "У шкільному підручнику авторки Литвінової для шостого класу їх так і називають:"
  replace: "У підручниках О. Литвінової (6 клас) та О. Глазової (10 клас) їх так і називають:"
- find: "<!-- INJECT_ACTIVITY: group-sort-categories -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in-cases-of-pluralia-tantum-nouns -->"
  replace: ""
- find: "## Відмінювання (~700 words)"
  replace: "## Відмінювання"
</fixes>
