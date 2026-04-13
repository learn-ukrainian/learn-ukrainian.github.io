## Linguistic Scan
- Location: `**Quick tip** — The phrase «без сумніву» is a fantastic conversational filler to agree enthusiastically with someone.`
  Issue: `без сумніву` expresses certainty, not enthusiastic agreement.
- Location: `The correct, natural Ukrainian prepositions for proximity are exclusively **біля** and **коло**.`
  Issue: Factually wrong. `возле` is a Russicism, but Ukrainian also has other natural proximity words; `поблизу` is attested in SУМ/VESUM.

## Exercise Check
Markers found in generated content: 6 total. Plan expects 4 activities.

The four unique marker IDs do match the plan semantically:
- `fill-in-complete-location-descriptions-with-correct-genitive-form`
- `quiz-choose-or-to-complete-everyday-sentences`
- `match-up-match-ukrainian-prepositional-phrases-to-their-english-equivalents`
- `true-false-judge-whether-preposition-noun-form-combinations-are-grammatically-correct`

Issues:
- `quiz-choose-or-to-complete-everyday-sentences` appears right after the `для` section, but the learner has not yet been taught `без` and `біля`.
- `quiz-...` and `true-false-...` are both duplicated at the end, so the marker count is wrong and the exercises cluster in the last section.
- No inline DSL exercise blocks are present; only markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Core plan content is covered well with concrete examples such as `для сестри`, `для Марії`, `без хліба`, `без олівця`, `коло дороги`, and location forms with `станції/лікарні/площі`. But the generated content cites neither listed reference: extracted-content search gives `Заболотний = 0`, `ULP = 0`, `ukrainianlessons.com = 0`. |
| 2. Linguistic accuracy | 7/10 | Most case forms are correct, but the note `The correct, natural Ukrainian prepositions for proximity are exclusively **біля** and **коло**` is factually wrong; `поблизу` is attested in SУМ/VESUM. |
| 3. Pedagogical quality | 7/10 | There are many examples, but two meta-notes mis-teach nuance: the `for` tip uses the muddled contrast `going for a meeting`, and `без сумніву` is explained as enthusiastic agreement rather than certainty. |
| 4. Vocabulary coverage | 9/10 | All required plan words appear in prose: `призначення`, `відпочинок`, `допомога`, `сумнів`, `будинок`, `зупинка`, `бібліотека`, `лікарня`, `площа`, `станція`. Recommended `навчання`, `церква`, `вокзал`, and `річка` also appear. |
| 5. Exercise quality | 4/10 | The four unique marker IDs match the plan, but the content contains 6 markers total: `quiz-choose-or-to-complete-everyday-sentences` is placed before `без` and `біля` are taught, and both `quiz` and `true-false` are duplicated at the end. |
| 6. Engagement & tone | 5/10 | Some teacherly lines work, but `speak pure, beautiful Ukrainian` and `Genitive Preposition Toolkit ... unlock a massive amount of expressive power` drift into purity rhetoric and corporate filler. |
| 7. Structural integrity | 9/10 | All three planned H2 sections are present and ordered correctly; pipeline word count is 3266, above the 2000 target; markdown is clean. |
| 8. Cultural accuracy | 5/10 | The anti-Russicism note overreaches into prescriptive purity language: `Ми ніколи не кажемо це слово` and `Справжня українська мова завжди звучить красиво і без помилок`. |
| 9. Dialogue & conversation quality | 8/10 | The module uses named speakers and real situations (camping, directions, packing), and the camping/pharmacy dialogues fit the plan’s scenario. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: opening of the module; extracted-content search shows `Заболотний = 0`, `ULP = 0`, `ukrainianlessons.com = 0`  
Issue: The plan explicitly lists two references, but the prose never integrates or cites them.  
Fix: Add one brief sentence in the opening explanation linking the rule to `Заболотний Grade 5, §31` and `Ukrainian Lessons`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `**Quick tip** — When translating the English word "for"... if it means "going to an event" (like "going for a meeting"), Ukrainian uses **на** + Accusative.`  
Issue: The contrast is muddled and the English example is unclear. It risks teaching an imprecise rule instead of a clean contrast like `для роботи` vs `на зустріч`.  
Fix: Replace the note with a direct contrast between `для + Genitive` for purpose/recipient and `на + Accusative` for events.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `**Quick tip** — The phrase «без сумніву» is a fantastic conversational filler to agree enthusiastically with someone.`  
Issue: This misdefines the phrase. `без сумніву` marks certainty/confidence, not enthusiastic agreement.  
Fix: Rewrite the note to explain that it signals certainty and give a short example.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-everyday-sentences -->` after the `для` section, and the four-marker block at the end of the module  
Issue: The quiz marker is placed before `без` and `біля` are taught, and the quiz/true-false markers are duplicated later, giving 6 markers for 4 planned activities.  
Fix: Change the early marker to the match-up activity, keep the true-false marker after section 2, and trim the final block to only the remaining location fill-in plus the final mixed quiz.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `The correct, natural Ukrainian prepositions for proximity are exclusively **біля** and **коло**.`  
Issue: This is factually wrong. `возле` is non-standard here, but Ukrainian also has other natural proximity words; `поблизу` is attested.  
Fix: Replace the note with a standard-vs-Russicism explanation that recommends `біля`, `коло`, or `поблизу` depending on context.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: `It is crucial to consciously filter this out of your vocabulary if you want to speak pure, beautiful Ukrainian.` / `Ми ніколи не кажемо це слово.` / `Справжня українська мова завжди звучить красиво і без помилок.`  
Issue: The module shifts from a valid anti-Russicism note into purity rhetoric and absolute claims about how Ukrainians speak.  
Fix: Replace the paragraph with neutral guidance about choosing standard Ukrainian forms without shaming mixed-language speakers.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `To wrap up this grammar topic, you now have a highly versatile and powerful "Genitive Preposition Toolkit" at your disposal. ... unlock a massive amount of expressive power...`  
Issue: This is gamified/corporate filler rather than teacherly explanation.  
Fix: Replace it with a plain summary of what `для`, `без`, `біля`, `навпроти`, and `коло` let the learner say.

## Verdict: REVISE
REVISE. There is a critical factual claim in the decolonization note, plus major issues with exercise sequencing/duplication, reference integration, and tone. Several dimensions fall below 9 and there are explicit fixable errors, so this cannot pass.

<fixes>
- find: |
    Look closely at the small words in the dialogue above: **для** (for), **без** (without), and **біля** (near). These three prepositions are incredibly common in everyday Ukrainian and form the backbone of basic communication. They all share one strict grammatical rule: they always demand the Genitive case (родовий відмінок). Whenever you use these prepositions, the noun, adjective, or pronoun that follows them must change its ending. In this section, we will focus entirely on the preposition **для**.
  replace: |
    Look closely at the small words in the dialogue above: **для** (for), **без** (without), and **біля** (near). These three prepositions are incredibly common in everyday Ukrainian and form the backbone of basic communication. They all share one strict grammatical rule: they always demand the Genitive case (родовий відмінок). Whenever you use these prepositions, the noun, adjective, or pronoun that follows them must change its ending. In this section, we will focus entirely on the preposition **для**. This matches the presentation in Заболотний Grade 5, §31 and in Ukrainian Lessons' overview of Ukrainian prepositions.

- find: |
    :::note
    **Quick tip** — When translating the English word "for", you must be careful to choose the correct Ukrainian equivalent based on context. If "for" means "for the purpose of" or "intended for someone", you should use **для** + Genitive. However, if it means "going to an event" (like "going for a meeting"), Ukrainian uses **на** + Accusative.
    :::
  replace: |
    :::note
    **Quick tip** — Use **для** + Genitive for purpose or recipient: **для роботи**, **для мами**. If you are going **to** an event or meeting, Ukrainian usually uses **на** + Accusative: **на зустріч**, **на концерт**.
    :::

- find: |
    :::note
    **Quick tip** — The phrase «без сумніву» is a fantastic conversational filler to agree enthusiastically with someone.
    :::
  replace: |
    :::note
    **Quick tip** — The phrase «без сумніву» expresses certainty or confidence: **Без сумніву, це добра ідея.**
    :::

- find: |
    <!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-everyday-sentences -->
  replace: |
    <!-- INJECT_ACTIVITY: match-up-match-ukrainian-prepositional-phrases-to-their-english-equivalents -->

- find: |
    <!-- INJECT_ACTIVITY: fill-in-complete-location-descriptions-with-correct-genitive-form -->
    <!-- INJECT_ACTIVITY: match-up-match-ukrainian-prepositional-phrases-to-their-english-equivalents -->
    <!-- INJECT_ACTIVITY: true-false-judge-whether-preposition-noun-form-combinations-are-grammatically-correct -->
    <!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-everyday-sentences -->
  replace: |
    <!-- INJECT_ACTIVITY: fill-in-complete-location-descriptions-with-correct-genitive-form -->
    <!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-everyday-sentences -->

- find: |
    :::tip
    **Decolonization note** — When speaking Ukrainian, you must completely avoid the word **возле**. This is a Russianism and a very common error in Surzhyk. The correct, natural Ukrainian prepositions for proximity are exclusively **біля** and **коло**.
    :::

    Many learners who have had previous exposure to Russian, or who hear a mixed language on the streets, might accidentally use the preposition **возле**. It is crucial to consciously filter this out of your vocabulary if you want to speak pure, beautiful Ukrainian. Using **біля** or **коло** immediately signals that you are speaking correctly.

    Ми ніколи не кажемо це слово. Українці завжди чекають своїх друзів біля театру або коло кінотеатру. Це просте правило є дуже важливим для чистої та правильної мови. Я залишив свою нову машину біля великого будинку. Справжня українська мова завжди звучить красиво і без помилок.

    > *We never say this word. Ukrainians always wait for their friends near the theater or by the cinema. This simple rule is very important for clean and correct language. I left my new car near the large building. Real Ukrainian language always sounds beautiful and without mistakes.*
  replace: |
    :::tip
    **Usage note** — The word **возле** is a Russian form, so in standard Ukrainian it is better to use Ukrainian proximity words such as **біля**, **коло**, or **поблизу**, depending on context and style.
    :::

    Learners may still hear **возле** in mixed speech. The useful rule is simple: in standard Ukrainian, choose a Ukrainian form that fits the context.

    Українці природно кажуть **біля театру**, **коло кінотеатру** або **поблизу будинку**. Зосередьтеся на виборі стандартної української форми, а не на риториці про "чисту" мову.

- find: |
    To wrap up this grammar topic, you now have a highly versatile and powerful "Genitive Preposition Toolkit" at your disposal. By mastering **для** for purpose, **без** for absence, and the spatial group of **біля**, **навпроти**, and **коло** for location, you can confidently describe a wide range of everyday situations. These small words unlock a massive amount of expressive power in A2 Ukrainian and serve as the foundation for navigating the physical world around you.
  replace: |
    To wrap up this grammar topic, **для** helps you express purpose or recipient, **без** shows absence, and **біля**, **навпроти**, and **коло** help you describe location. Together these patterns let you explain everyday needs, missing items, and where places or objects are.
</fixes>