## Linguistic Scan
No linguistic errors found. I did not find Russianisms, Surzhyk, paronym misuse, or Russian letters (`ы, э, ё, ъ`). The forms `виш`, `абітурієнт`, feminine profession nouns, and `випускаються` are attested, so I am not flagging them.

## Exercise Check
Five `INJECT_ACTIVITY` markers appear in the prose:

- `fill-in-complete-sentences-about-education-and-work-using` after the education section
- `fill-in-complex-sentences` after the work dialogue
- `true-false-culture-complex` after the work section
- `match-up-match-education-career-situations-to-appropriate-responses-using-complex-sentences` in the future-plans section
- `quiz-choose-the-correct-complex-sentence-type-for-work-education-scenarios` at the end

Checks:

- The four planned activity types are represented, but there are 5 markers for 4 planned hints because of an extra unplanned fill-in marker.
- Marker placement is mostly after teaching, but the work section clusters two markers together at the end.
- No inline DSL exercise blocks are present, so there is no exercise logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All three planned H2 sections and the law/career-counseling dialogue are present, but the education vocabulary point omits `залік` (0 occurrences in the content), and the first section is already labeled `(~780 words)` against the 700-word plan. |
| 2. Linguistic accuracy | 9/10 | No Russianisms/Surzhyk/paronym errors found, and no Russian letters appear. The only accuracy issue is a misleading English gloss: `they "put it together": **скласти іспит**`. |
| 3. Pedagogical quality | 6/10 | Example density is good, but the module repeatedly front-loads English theory before practice: `After finishing our education...`; it also contradicts its own later guidance by first using `Молоді люди вступають в **університет**...` and then teaching `Ми завжди кажемо "вступати до"...`. |
| 4. Vocabulary coverage | 8/10 | All required plan words appear naturally, and recommended items also appear (`керівник`, `співбесіда`, `магістратур-`), but `залік` from the education vocabulary list is missing. |
| 5. Exercise quality | 6/10 | Coverage is close, but there are 5 markers for 4 planned activities, and `<!-- INJECT_ACTIVITY: fill-in-complex-sentences -->` is an extra unplanned fill-in marker. |
| 6. Engagement & tone | 5/10 | The voice is functional but padded with filler and overclaiming: `Ця фраза є дуже популярною в Україні.` and `Тепер ви можете вільно та впевнено розповідати про свою кар'єру...` |
| 7. Structural integrity | 8/10 | All planned H2 headings are present and ordered, markdown is mostly clean, and pipeline word count is 2808, but redundant metacommentary and the extra activity marker weaken the structure. |
| 8. Cultural accuracy | 7/10 | The counseling dialogue fits the plan well, but `Сучасна школа часто називається гімназія або ліцей.` is overgeneralized and imprecise about Ukrainian school types. |
| 9. Dialogue & conversation quality | 7/10 | Dialogues are named and situational, but the party dialogue stays close to an interview script; e.g. `Ким ви працюєте?... А що ви робите на роботі?` with the flat answer `Я створюю проєкти.` |

## Findings
[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Сучасна школа часто називається гімназія або ліцей. ... Молоді люди вступають в **університет** (university) або інститут.`  
Issue: This opening is both culturally imprecise and internally inconsistent with the later rule `Ми завжди кажемо "вступати до"...`.  
Fix: Rewrite the school-types sentence more accurately and align the case pattern with the later explanation: `... вступають до **університету** ...`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Щоб завершити етап, студент повинен успішно скласти **іспит** (exam).`  
Issue: The plan’s education-vocabulary point includes `залік`, but the prose never introduces it.  
Fix: Add `залік` here alongside `іспит`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Also, Ukrainians don't "take" or "make" an exam, they "put it together": **скласти іспит** (to pass an exam).`  
Issue: The English gloss is misleading and teaches a bad mnemonic.  
Fix: Replace it with a plain explanation that Ukrainian says `скласти іспит`, not a literal equivalent of English `take/make an exam`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `After finishing our education, the next big step is finding a job. When we talk about our professional life, we need a specific set of vocabulary to describe our daily routine. Let's look at how to introduce your job and workplace in Ukrainian using essential terms.`  
Issue: This is inflated English setup before an A2 Ukrainian section; it delays practice and contributes to the module’s word-budget drift. The same problem recurs in the future-plans intro and the English recap before the final summary.  
Fix: Replace these English scaffolding paragraphs with short transition lines.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in-complex-sentences -->`  
Issue: This is an extra unplanned fill-in marker. The plan has one fill-in activity hint, not two.  
Fix: Remove this marker.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `Ця фраза є дуже популярною в Україні.` and `Тепер ви можете вільно та впевнено розповідати про свою кар'єру українською мовою.`  
Issue: Both lines are low-information filler; the second also overpromises learner ability.  
Fix: Replace them with concrete, non-hype phrasing.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `— **Олена:** Я створюю проєкти. Якщо проєкт складний, ми працюємо командою.`  
Issue: The answer is flat and generic, which makes the party dialogue sound like an interview prompt rather than a natural exchange.  
Fix: Give Olena one concrete, profession-specific detail before the conditional sentence.

## Verdict: REVISE
Multiple major findings require correction, and several dimensions are below 9. This is not a rebuild-level failure, but it is not ready to ship.

<fixes>
- find: |
    Сучасна школа часто називається гімназія або ліцей. Після школи починається вища освіта. Молоді люди вступають в **університет** (university) або інститут.
  replace: |
    В Україні серед закладів середньої освіти є школи, гімназії та ліцеї. Після школи починається вища освіта. Молоді люди вступають до **університету** (university) або інституту.
- find: |
    Щоб завершити етап, студент повинен успішно скласти **іспит** (exam). Після цього він може здобути гарну освіту та почати **працювати** (to work).
  replace: |
    Щоб завершити етап, студент повинен успішно скласти **іспит** (exam) або отримати **залік** (course credit). Після цього він може здобути гарну освіту та почати **працювати** (to work).
- find: |
    Also, Ukrainians don't "take" or "make" an exam, they "put it together": **скласти іспит** (to pass an exam).
  replace: |
    Also, in Ukrainian you say **скласти іспит** (to pass an exam), not a literal equivalent of English "take" or "make" an exam.
- find: |
    After finishing our education, the next big step is finding a job. When we talk about our professional life, we need a specific set of vocabulary to describe our daily routine. Let's look at how to introduce your job and workplace in Ukrainian using essential terms.
  replace: |
    Тепер подивімося, як українською розповідати про роботу, посаду й робоче місце.
- find: |
    When we talk about our plans, we use complex sentences with **якщо** (if). Building a career starts at an **університет** (university) with good **освіта** (education).
  replace: |
    Тепер подивімося, як за допомогою **якщо** говорити про майбутні плани в навчанні та роботі.
- find: |
    Using complex sentences elevates your basic Ukrainian. By connecting simple ideas, you can express your thoughts clearly and professionally in any situation.
  replace: |
    Складні речення допомагають поєднувати прості ідеї й точніше висловлюватися про навчання та роботу.
- find: |
    <!-- INJECT_ACTIVITY: fill-in-complex-sentences -->
  replace: ""
- find: |
    Ця фраза є дуже популярною в Україні.
  replace: |
    Це базова модель для розмови про навчання.
- find: |
    Тепер ви можете вільно та впевнено розповідати про свою кар'єру українською мовою.
  replace: |
    Тепер ви можете точніше розповідати про навчання й кар'єру українською мовою.
- find: |
    — **Олена:** Я створюю проєкти. Якщо проєкт складний, ми працюємо командою. *(I create projects. If a project is complex, we work as a team.)*
  replace: |
    — **Олена:** Я проєктую житлові комплекси й готую креслення. Якщо проєкт складний, ми працюємо командою. *(I design residential complexes and prepare drawings. If a project is complex, we work as a team.)*
</fixes>