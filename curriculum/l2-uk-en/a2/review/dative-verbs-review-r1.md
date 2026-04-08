## Linguistic Scan
Found linguistic errors: English calques ("критичне слово", "виклику людини") and Russianism ("давайте" as imperative).

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-focus-completing-sentences-with-correct-dative-noun-pronoun-forms-after-help-thank-call -->` placed correctly after Section 1. Matches plan.
- `<!-- INJECT_ACTIVITY: match-up-focus-matching-ukrainian-sentences-to-english-i-like-equivalents-to-cement-the-subject-object-shift -->` placed correctly after Section 2. Matches plan.
- `<!-- INJECT_ACTIVITY: true-false-focus-judging-the-correctness-of-age-expressions-dative-form-correct-year-noun-agreement -->` placed correctly after Section 3. Matches plan.
- `<!-- INJECT_ACTIVITY: quiz-focus-choosing-between-dative-and-accusative-for-the-noun-pronoun-after-specific-verbs-e-g -->` placed correctly after Section 4. Matches plan.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module follows the plan perfectly, covering all required points, but missed incorporating the `recommended` vocabulary block. |
| 2. Linguistic accuracy | 7/10 | Contains an English calque ("абсолютно критичне слово" for absolutely critical), a poor translation ("слова для виклику людини" for calling a person), and a common Russianism ("давайте" instead of the true imperative "розгляньмо"). |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical flow. The contrast between English direct objects and Ukrainian dative experiencers is explained clearly with great examples. |
| 4. Vocabulary coverage | 7/10 | All required vocabulary is used effectively in context, but all five `recommended` words (довіряти, вибачати, посміхатися, співчувати, заздрити) are completely missing from the prose. |
| 5. Exercise quality | 10/10 | Placeholders match the `activity_hints` from the plan exactly in type, focus, and count, and are positioned logically after their respective sections. |
| 6. Engagement & tone | 9/10 | The tone is encouraging, but slightly robotic in the dialogue. Phrasing like "Сьогодні ми вивчаємо дуже важливу тему" is natural for an instructor. |
| 7. Structural integrity | 9/10 | Good use of headings and structure. Word count is high. However, the first dialogue is structurally flawed (a monologue formatted with a repeated speaker name). |
| 8. Cultural accuracy | 10/10 | Excellent point on `благодарить` vs `дякувати`, explicitly correcting a common Russian interference error. |
| 9. Dialogue & conversation quality | 6/10 | The first "dialogue" repeats "— **Волонтер:**" on every single line of a continuous monologue instead of showing an interaction between the volunteer and the people they are helping. |

## Findings

[Dialogue & conversation quality] [critical]
Location: `> — **Волонтер:** Сьогодні я багато і важко працюю...`
Issue: The plan requested a dialogue with "Speakers: Волонтер, Різні люди". The generated text is a monologue by the Volunteer, weirdly formatted with the speaker's name repeated on every line.
Fix: Rewrite as a true dialogue involving the Volunteer and the people they are helping.

[Linguistic accuracy] [critical]
Location: `Це абсолютно критичне слово для ввічливого спілкування.`
Issue: English calque (Semantic False Friend). "Критичний" in Ukrainian means critical (in a negative sense, e.g. "критичний стан") or analytical ("критичне мислення"), not "essential/crucial".
Fix: Change to "Це надзвичайно важливе слово".

[Linguistic accuracy] [critical]
Location: `Цікавий приклад — це слова для виклику людини. *(An interesting example is words for calling a person.)*`
Issue: English calque. "Виклик" means "a challenge" or "a formal summons" (like calling an ambulance). It does not mean "calling a person by phone or by voice" in this context.
Fix: Change to "дієслова зі значенням «кликати»".

[Linguistic accuracy] [critical]
Location: `Давайте детально розглянемо...`, `Давайте подивимося...`, `Давайте уважно подивимося...`
Issue: Russianism/Calque. Using "давайте" + 1st person plural/infinitive is a direct translation of Russian "давайте посмотрим". The proper Ukrainian form is the imperative mood (розгляньмо, подивімося).
Fix: Change to `Детально розгляньмо`, `Подивімося`, `Уважно подивімося`.

[Vocabulary coverage] [major]
Location: Throughout the prose
Issue: None of the recommended vocabulary words (довіряти, вибачати, посміхатися, співчувати, заздрити) were included.
Fix: Add a short paragraph introducing these verbs and demonstrating that they also govern the dative case.

## Verdict: REVISE
The module is pedagogically strong but suffers from several linguistic calques (English and Russian influence), misses the recommended vocabulary entirely, and has a poorly formatted dialogue. These issues require targeted fixes before passing.

<fixes>
- find: |
    > — **Волонтер:** Сьогодні я багато і важко працюю. *(Today I work a lot and hard.)*
    > — **Волонтер:** Я **допомагаю сусідці** *(I help the neighbor)* Олені прибирати великий парк.
    > — **Волонтер:** Потім я **дзвоню другові** *(I call the friend)* Івану.
    > — **Волонтер:** Він швидко приніс свіжу воду та смачну їжу. *(He quickly brought fresh water and tasty food.)*
    > — **Волонтер:** Я щиро **дякую йому** *(I thank him)* за цю велику допомогу!
  replace: |
    > — **Волонтер:** Олено, я зараз **допомагаю сусідці** *(I help the neighbor)* прибирати великий парк. Тобі потрібна допомога?
    > — **Олена:** Ні, я вже все зробила. Але я **раджу тобі** *(I advise you)* трохи відпочити.
    > — **Волонтер:** Добре, тоді я **дзвоню другові** *(I call the friend)* Івану. Він має принести воду.
    > — **Іван:** Привіт! Я вже тут. Тримай свіжу воду та смачну їжу.
    > — **Волонтер:** Я щиро **дякую тобі** *(I thank you)* за цю велику допомогу!
- find: "Це абсолютно критичне слово для ввічливого спілкування. *(This is an absolutely critical word for polite communication.)*"
  replace: "Це надзвичайно важливе слово для ввічливого спілкування. *(This is an extremely important word for polite communication.)*"
- find: "Цікавий приклад — це слова для виклику людини. *(An interesting example is words for calling a person.)*"
  replace: "Цікавий приклад — це дієслова зі значенням «кликати». *(An interesting example is verbs with the meaning 'to call/summon'.)*"
- find: "Давайте детально розглянемо дієслово допомагати *(to help)*."
  replace: "Детально розгляньмо дієслово допомагати *(to help)*."
- find: "Давайте подивимося, як люди говорять про вік у реальному житті. *(Let's see how people talk about age in real life.)*"
  replace: "Подивімося, як люди говорять про вік у реальному житті. *(Let's see how people talk about age in real life.)*"
- find: "Давайте уважно подивимося на ці відмінки разом. *(Let's look carefully at these cases together.)*"
  replace: "Уважно подивімося на ці відмінки разом. *(Let's look carefully at these cases together.)*"
- find: "Завжди швидко **відповідай мамі** *(answer mom)*, коли вона щось питає."
  replace: |
    Завжди швидко **відповідай мамі** *(answer mom)*, коли вона щось питає.
    Інші корисні дієслова з давальним відмінком: **довіряти** *(to trust)*, **вибачати** *(to forgive)*, **посміхатися** *(to smile)*, **співчувати** *(to sympathize)*, та **заздрити** *(to envy)*. Я **довіряю другові** *(I trust my friend)*. Вона щиро **посміхається дитині** *(she smiles at the child)*.
</fixes>
