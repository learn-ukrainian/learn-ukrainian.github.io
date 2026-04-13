## Linguistic Scan
- **Critical factual grammar error:** In **Магія української фонології**, the paragraph beginning `"Now we move to consonant alternations, specifically the first palatalization..."` mislabels the alternation `г/з, к/ц, х/с` before `-і` as **first palatalization**. The plan explicitly calls for the true first-palatalization patterns `г/ж, к/ч, х/ш` with examples like `нога/ніжка`, `рука/ручка`, and those examples never appear.
- **Major overstatement:** In **Милозвучність мови: евфонія**, the claims `"it is a strict grammatical rule that every speaker follows"` and repeated `"you must use"` wording are too absolute. **Правопис 2019** allows rhythmic/stylistic deviations in `у/в` and `і/й` usage: [§23](https://2019.pravopys.net/sections/23/), [§24](https://2019.pravopys.net/sections/24/).

## Exercise Check
Markers: 4/4 present, correctly placed, and aligned with the plan: `quiz-case-identification`, `fill-in-phonological-alternations`, `match-up-euphony-choice`, `error-correction-euphony`.

Informational only, not scored against the writer: the downstream `activities/a2-bridge.yaml` currently defines `quiz-case-identification`, `fill-in-phonological-alternations`, and `match-up-euphony-choice`, but not `error-correction-euphony`, so that marker would not inject at publish time.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The four planned sections and A2 roadmap are present, but the plan point `'the first palatalization (г/ж, к/ч, х/ш) ... (нога/ніжка, рука/ручка)'` is not actually taught; instead the module says `"«г» becomes «з», «к» becomes «ц», and «х» becomes «с»."` I also searched `Заболотний` / `§1-10` in the module and found 0 matches, so the planned reference is not integrated. |
| 2. Linguistic accuracy | 7/10 | The Ukrainian examples are mostly clean, but the phonology section factually misidentifies `"г/з, к/ц, х/с"` before `-і` as `"the first palatalization"`, which teaches the wrong grammatical label. |
| 3. Pedagogical quality | 7/10 | Example density is good, but the euphony section teaches preferences as absolutes: `"it is a strict grammatical rule that every speaker follows"` and repeated `"you must use"` phrasing oversimplify the standard-language rule set. |
| 4. Vocabulary coverage | 9/10 | All required plan vocabulary appears in context: `відмінок`, `називний`, `знахідний`, `місцевий`, `кличний`, `чергування`, `голосний`, `приголосний`, `наголос`; recommended `милозвучність`, `система`, and `правило` also appear naturally. |
| 5. Exercise quality | 9/10 | The planned exercise markers are correctly distributed after the sections they test, and each marker matches the plan’s activity type/focus. |
| 6. Engagement & tone | 7/10 | The teacher voice is generally warm, but `"immediately marks you as a foreigner"` is harsher than the target persona, and some of the encouragement leans into hype rather than instruction. |
| 7. Structural integrity | 10/10 | All four H2 headings are present and ordered correctly, markdown is clean, and the pipeline word count is 2777, safely above the 2000-word target. |
| 8. Cultural accuracy | 6/10 | Two passages explain Ukrainian through Russian: `"Unlike in Russian..."` and `"stands in stark contrast to Russian..."`; that framing cuts against the decolonized standard. |
| 9. Dialogue & conversation quality | 7/10 | The opening scene is plausible and speakers are named, but `"Привіт, Оксано!"` to a teacher and `"Що ви робите тут?"` make the exchange feel staged rather than natural. |

## Findings
- [PLAN ADHERENCE] [SEVERITY: critical]  
Location: **Магія української фонології** — `"Now we move to consonant alternations, specifically the first palatalization. ... «г» becomes «з», «к» becomes «ц», and «х» becomes «с»."`  
Issue: This teaches the wrong label. `г/з, к/ц, х/с` before `-і` in case forms is not the first palatalization, and the planned `г/ж, к/ч, х/ш` examples (`нога/ніжка`, `рука/ручка`) never appear.  
Fix: Rewrite the paragraph to distinguish the case-form alternation `г/з, к/ц, х/с` from the first palatalization and add the planned examples `нога — ніжка`, `рука — ручка`.

- [PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: **Милозвучність мови: евфонія** — `"This euphonic alternation is not just an optional stylistic choice; it is a strict grammatical rule that every speaker follows."` Also the `у/в`, `і/й`, and `з/зі/із` paragraphs use repeated `"must use"` wording.  
Issue: The explanation is too absolute for A2. **Правопис 2019** treats these as standard milozvuchnist preferences with permitted deviations for rhythm/style; the current wording over-corrects learners.  
Fix: Replace `"strict grammatical rule"` / `"must use"` with `"usually preferred in standard usage"` and keep the examples. Sources: [§23](https://2019.pravopys.net/sections/23/), [§24](https://2019.pravopys.net/sections/24/).

- [CULTURAL ACCURACY] [SEVERITY: major]  
Location: **Пригадуємо відмінки** — `"Unlike in Russian, where the vocative has largely disappeared..."` and `"immediately marks you as a foreigner."` Also **Милозвучність мови: евфонія** — `"stands in stark contrast to Russian..."`  
Issue: The module repeatedly explains Ukrainian through Russian and adds shaming language, which conflicts with the project’s decolonized standard and the encouraging-teacher persona.  
Fix: Reframe both passages in Ukrainian-on-its-own-terms language and delete the `"foreigner"` wording.

- [DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: **Пригадуємо відмінки** — `"Привіт, Оксано!"` and `"Що ви робите тут?"`  
Issue: For a first-day teacher-student exchange, the register is off and the question is unnatural; it reads like a forced grammar demo.  
Fix: Make the greeting polite and replace the teacher’s question with a natural prompt such as `Розкажіть трохи про себе`.

- [PLAN ADHERENCE] [SEVERITY: major]  
Location: **Пригадуємо відмінки** — grammar box introducing the case mnemonic.  
Issue: The plan reference `Заболотний Grade 5, §1-10` is never cited. I searched `Заболотний` and `§1-10` in the module and found 0 matches.  
Fix: Tie the mnemonic box to the planned school-textbook reference, e.g. by naming `Заболотний Grade 5, §1-10`.

## Verdict: REVISE
REVISE — the module is structurally solid and mostly fluent, but it contains one critical factual grammar error, several major overstatements in the euphony teaching, and avoidable cultural/dialogue problems.

<fixes>
- find: |
    > — **Викладач:** Добрий день! Ласкаво просимо до рівня А2. *(Good afternoon! Welcome to the A2 level.)*
    > — **Новий студент:** Привіт, Оксано! Дякую. Я — новий студент. *(Hi, Oksana! Thank you. I am a new student.)*
    > — **Викладач:** Дуже приємно. Що ви робите тут? *(Nice to meet you. What are you doing here?)*
    > — **Новий студент:** Я вивчаю українську мову. Я живу в Києві. *(I am studying the Ukrainian language. I live in Kyiv.)*
    > — **Викладач:** Чудово! Ви вже добре говорите. *(Wonderful! You already speak well.)*
  replace: |
    > — **Викладач:** Добрий день! Ласкаво просимо до рівня А2. *(Good afternoon! Welcome to the A2 level.)*
    > — **Новий студент:** Доброго дня, пані Оксано! Дякую. Я — новий студент. *(Good afternoon, Ms. Oksana! Thank you. I am a new student.)*
    > — **Викладач:** Дуже приємно. Розкажіть трохи про себе. *(Nice to meet you. Tell me a little about yourself.)*
    > — **Новий студент:** Я вивчаю українську мову. Я живу в Києві. *(I am studying the Ukrainian language. I live in Kyiv.)*
    > — **Викладач:** Чудово! Ви вже добре говорите. *(Wonderful! You already speak well.)*

- find: |
    The Vocative case is a living, essential feature of the Ukrainian language. Unlike in Russian, where the vocative has largely disappeared from modern speech, failing to use the Vocative in Ukrainian when addressing someone sounds incredibly unnatural and immediately marks you as a foreigner. It is a beautiful marker of the language's unique identity.
  replace: |
    The Vocative case is a living, essential feature of the Ukrainian language. Failing to use the Vocative when addressing someone sounds unnatural and noticeably non-native in many everyday situations. It is an important marker of Ukrainian speech culture.

- find: |
    Now we move to consonant alternations, specifically the first palatalization. This is a crucial rule for feminine nouns ending in «-а» or «-я». When these nouns are put into the Dative or **місцевий** (locative) cases, the ending changes to «-і». But Ukrainian phonetics strongly dislikes pronouncing the hard consonants «г», «к», or «х» right before the soft vowel «і». Therefore, these consonants soften and mutate: «г» becomes «з», «к» becomes «ц», and «х» becomes «с».
  replace: |
    Now we move to consonant alternations in noun forms. For many feminine nouns ending in «-а» or «-я», the Dative and **місцевий** (locative) forms in «-і» trigger the alternations «г/з», «к/ц», and «х/с»: «нога — нозі», «рука — руці», «муха — мусі». This is different from the first palatalization, which produces alternations like «г/ж», «к/ч», and «х/ш» in word formation, for example «нога — ніжка» and «рука — ручка».

- find: |
    Ukrainian students learn a fun mnemonic phrase in school to remember the exact order of the seven cases. The first letter of each word matches the first letter of a case:
  replace: |
    Ukrainian school textbooks, including Заболотний Grade 5, §1-10, use a fun mnemonic phrase to help learners remember the exact order of the seven cases. The first letter of each word matches the first letter of a case:

- find: |
    This euphonic alternation is not just an optional stylistic choice; it is a strict grammatical rule that every speaker follows. For example, Ukrainian naturally breaks up groups of three consonants to keep the melody alive. This is a fundamental law of the language, which stands in stark contrast to Russian, where heavy, unbroken consonant clusters are entirely normal and expected.
  replace: |
    These euphonic alternations are a strong tendency of standard Ukrainian and an important part of natural-sounding speech. For example, Ukrainian often breaks up difficult consonant clusters to keep a phrase easier to pronounce. Writers may occasionally depart from the preferred pattern for rhythm, style, or emphasis.

- find: |
    The most common euphonic alternation you will encounter involves the prepositions and prefixes «у» and «в». To maintain the melodic rhythm of your speech, you must choose between them based entirely on the surrounding sounds. If you are placing the preposition between two consonants, or if you are at the very beginning of a sentence before a **приголосний** (consonant), you must use «у». This inserts a necessary vowel break and makes the phrase much easier to pronounce. Conversely, if you are placing the preposition between two vowels, or immediately after a **голосний** (vowel) and before a consonant, you should use «в» to avoid vowel collision.
  replace: |
    The most common euphonic alternation you will encounter involves the prepositions and prefixes «у» and «в». In standard usage, you usually choose between them based on the surrounding sounds. Between two consonants, or at the very beginning of a sentence before a **приголосний** (consonant), «у» is often preferred. Between two vowels, or after a **голосний** (vowel) before a consonant, «в» is often preferred to avoid vowel collision.

- find: |
    You will apply this exact same melodic logic to the conjunctions «і» and «й», which both mean "and". When you connect words or ideas, the language demands a smooth, uninterrupted transition. You should use «і» when you are connecting two words that end and begin with consonants, or when you are starting a new phrase right after a pause in speech. On the other hand, you must use «й» when the word immediately before it ends in a vowel. This is especially important if the next word also starts with a vowel, preventing an awkward pause.
  replace: |
    You will apply this exact same melodic logic to the conjunctions «і» and «й», which both mean "and". In standard usage, «і» is usually preferred when you are connecting two words that end and begin with consonants, or when you are starting a new phrase after a pause in speech. «й» is usually preferred after a vowel, especially if the next word also starts with a vowel, because it helps the phrase flow more smoothly.

- find: |
    Finally, the preposition meaning "with" or "from" changes its form to match its phonetic environment. The basic, default form is «з», which you will use before most single consonants or before vowels. However, if the following word starts with a difficult consonant cluster—especially those beginning with sibilant sounds like «с», «ш», or «з»—you must use «зі». This adds a crucial vowel break. Furthermore, you can use the form «із» between specific, heavy groups of consonants to perfectly maintain the rhythmic balance of the whole sentence.
  replace: |
    Finally, the preposition meaning "with" or "from" changes its form to match its phonetic environment. The basic form is «з», which you will hear before many single consonants and before vowels. Before difficult consonant clusters—especially those beginning with sibilant sounds like «с», «ш», or «з»—speakers often prefer «зі» to make the phrase easier to pronounce. The form «із» also appears before some heavy consonant groups to maintain a smoother rhythm.
</fixes>