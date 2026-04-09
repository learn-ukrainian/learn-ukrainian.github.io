## Linguistic Scan
Errors found:
1. Grammatical case error (missing Instrumental after "називати"): «ми називаємо таке обличчя бліде» (should be блідим).
2. Lexical confusion / Paronym error: «значний фізичний ріст» (the correct word for human height is "зріст", as correctly taught in the rest of the text). Additionally, «називаємо їх словом високий» is awkward and lacks proper agreement.
3. Adjective agreement mismatch: «Здоровий... колір... описується словом рум'яне». The word "колір" is masculine, but "рум'яне" is neuter (as it conceptually applies to "обличчя"). 
4. Grammatical case error with copula: «Хлопчик буде ваш племінник» is colloquially understood but lacks the normative Instrumental case for the predicate ("буде племінником") or a clearer nominative structure ("це ваш племінник").

## Exercise Check
- All 6 plan `activity_hints` are matched by corresponding `INJECT_ACTIVITY` markers placed chronologically after their respective teaching sections. 
- However, an extra duplicate `group-sort` marker was injected at the end of the module (before the self-check). This is redundant and does not correspond to a unique plan hint. 
- The dialogue beautifully serves as a practical setup for the adjective agreement motivation outlined in the plan.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Covers all requested sections and vocabulary. Incorporates pedagogical points from textbooks perfectly, e.g., «Заболотний Grade 7 p.251 — план твору-опису» is explicitly implemented in "Опис людини: як писати портрет" (зачин, основна частина, кінцівка). |
| 2. Linguistic accuracy | 8/10 | Good overall vocabulary usage, but contains grammatical case and agreement errors: «ми називаємо таке обличчя бліде» instead of *блідим*, «колір... описується теплим словом рум'яне» (gender mismatch), and a paronym error «фізичний ріст» instead of *зріст*. |
| 3. Pedagogical quality | 10/10 | Exceptional. Explanations are deep, contextualized, and provide clear syntactic models. E.g., providing three exact sentence models for describing character: «Вона — людина чуйна», «За характером він дуже стриманий», «Йому властиво завжди допомагати». |
| 4. Vocabulary coverage | 10/10 | Flawless integration of both required and recommended vocabulary. Words are introduced naturally in the prose, e.g., «Якщо людина має дуже міцну будову тіла... ми об'єктивно називаємо її словом кремезний». |
| 5. Exercise quality | 9/10 | All markers are correctly placed after their teaching concepts, but an extra, redundant `<!-- INJECT_ACTIVITY: group-sort -->` marker was erroneously injected at the very end of the text. |
| 6. Engagement & tone | 10/10 | The tone is warm, encouraging, and highly professional. Sentences like «Розуміння цих лексичних нюансів дозволить вам вибирати ідеальне слово для кожної ситуації» create excellent teacher-student rapport. |
| 7. Structural integrity | 10/10 | Word count is 4696, comfortably exceeding the 4000-word target. Headers exactly match the plan outline. No structural artifacts or dangling sentences. |
| 8. Cultural accuracy | 10/10 | Masterfully explains the cultural dimensions of language: «В українській глибокій культурній традиції... зовнішність персонажа ніколи не існує просто сама по собі... Вона завжди є своєрідним, дуже прозорим вікном у складний внутрішній світ». Precision regarding in-law terminology is culturally perfect. |
| 9. Dialogue & conversation quality | 10/10 | The wedding dialogue is natural, multi-turn, and perfectly illustrates the plan's adjective agreement requirement: «старший брат Михайло», «молодша сестра Олена», «найдобріша жінка». Excellent use of the Vocative case («Михайле», «Ганно Петрівно»). |

## Findings
[2. Linguistic accuracy] [Critical]
Location: Section "Зовнішність людини", paragraph 4: «Якщо ж шкіра від природи дуже світла і позбавлена пігменту, ми називаємо таке обличчя **бліде** *(pale)*.»
Issue: Grammatical case error. The verb "називати" requires the Instrumental case for the secondary predicate. It must be "блідим".
Fix: Change «бліде» to «блідим».

[2. Linguistic accuracy] [Critical]
Location: Section "Зовнішність людини", paragraph 2: «Якщо чоловік або жінка має значний фізичний ріст, ми називаємо їх словом **високий** *(tall)*.»
Issue: Lexical error / Paronym. The correct term for human height is "зріст", not "ріст". Furthermore, «називаємо їх словом високий» lacks proper agreement for plural "їх".
Fix: Rewrite to «Якщо чоловік або жінка має великий зріст, ми кажемо, що вони **високі** *(tall)*.»

[2. Linguistic accuracy] [Critical]
Location: Section "Зовнішність людини", paragraph 4: «Здоровий, яскравий рожевий колір щік, який часто свідчить про молодість, описується теплим словом **рум'яне** *(rosy)*.»
Issue: Gender mismatch. The masculine subject "колір" is described with the neuter adjective "рум'яне".
Fix: Rephrase to connect the adjective to "обличчя": «Обличчя зі здоровим рожевим кольором щік, який часто свідчить про молодість, ми називаємо **рум'яним** *(rosy)*.»

[2. Linguistic accuracy] [Critical]
Location: Section "Родина і родичі", paragraph 2: «Хлопчик буде ваш **племінник** *(nephew)*, а дівчинка — ваша **племінниця** *(niece)*.»
Issue: Grammatical case error. "Буде" as a copula generally requires the Instrumental case ("буде вашим племінником"), or it should be rephrased as a definition. 
Fix: Rephrase to «Хлопчик — це ваш **племінник**...»

[5. Exercise quality] [Major]
Location: Section "Підсумок: людина у словах", before paragraph 2: `<!-- INJECT_ACTIVITY: group-sort -->`
Issue: Duplicate activity marker. This activity was already injected in the previous section.
Fix: Delete the redundant marker.

## Verdict: REVISE
The module is exceptionally well-written, rich in cultural detail, and exceeds the word count target. However, it contains several grammatical case and agreement errors that violate the linguistic accuracy dimension. These specific errors must be fixed via deterministic replacement before the module can be published.

<fixes>
- find: "Якщо ж шкіра від природи дуже світла і позбавлена пігменту, ми називаємо таке обличчя **бліде** *(pale)*."
  replace: "Якщо ж шкіра від природи дуже світла і позбавлена пігменту, ми називаємо таке обличчя **блідим** *(pale)*."
- find: "Якщо чоловік або жінка має значний фізичний ріст, ми називаємо їх словом **високий** *(tall)*."
  replace: "Якщо чоловік або жінка має великий зріст, ми кажемо, що вони **високі** *(tall)*."
- find: "Здоровий, яскравий рожевий колір щік, який часто свідчить про молодість, описується теплим словом **рум'яне** *(rosy)*."
  replace: "Обличчя зі здоровим рожевим кольором щік, який часто свідчить про молодість, ми називаємо **рум'яним** *(rosy)*."
- find: "Хлопчик буде ваш **племінник** *(nephew)*, а дівчинка — ваша **племінниця** *(niece)*."
  replace: "Хлопчик — це ваш **племінник** *(nephew)*, а дівчинка — ваша **племінниця** *(niece)*."
- find: |
    **кличний відмінок** *(vocative case)*.

    <!-- INJECT_ACTIVITY: group-sort -->

    Тепер настав час для самостійної перевірки ваших знань.
  replace: |
    **кличний відмінок** *(vocative case)*.

    Тепер настав час для самостійної перевірки ваших знань.
</fixes>
