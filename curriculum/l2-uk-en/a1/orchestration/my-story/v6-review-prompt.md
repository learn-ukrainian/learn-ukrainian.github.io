<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 52: My Story (A1, A1.8 [Past, Future, Graduation])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-052
level: A1
sequence: 52
slug: my-story
version: '1.2'
title: My Story
subtitle: Я народився, я живу, я буду... — your life in three tenses
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Combine all three tenses (past, present, future) in one coherent narrative
- Tell a simple life story: where you were born, where you live, what you plan
- Use time expressions to signal tense shifts
- Understand a short biography read aloud or in text
dialogue_situations:
- setting: Grandparent telling their life story — Я народився в селі (n, village).
    Ходив у школу (f). Зараз живу в місті (n, city). Працюю в лікарні (f, hospital).
    Буду відпочивати на дачі (f, dacha).
  speakers:
  - Дідусь/Бабуся
  - Онуки
  motivation: Three tenses with село(n), школа(f), місто(n), лікарня(f), дача(f)
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — Getting to know someone deeply: — Розкажи про себе! — Я народився
    в Канаді, у Торонто. — А зараз ти живеш тут? — Так, зараз я живу в Києві. — Чому
    ти переїхав? — Я хотів вивчати українську. Мої бабуся і дідусь з України. — А
    що ти будеш робити далі? — Я буду працювати тут і вчити мову. — Чудово! Успіхів
    тобі! All three tenses in one conversation.'
  - 'Dialogue 2 — Anna''s story: — Я народилася у Львові. Там я вчилася в школі. —
    Потім я переїхала в Київ і закінчила університет. — Зараз я працюю вчителькою
    і живу в центрі міста. — А що далі? — Я буду подорожувати! Я хочу побачити Японію.
    — І ти будеш вчити японську? — Може! Але спочатку — українська для тебе! Past
    → present → future flow.'
- section: Три часи разом (Three Tenses Together)
  words: 300
  points:
  - 'Life story structure: PAST (минулий час): Я народився/народилася в... Я жив/жила
    в... Я вчився/вчилася... Я працював/працювала... PRESENT (теперішній час): Зараз
    я живу в... Я працюю... Я вивчаю... Я люблю... FUTURE (майбутній час): Я буду
    працювати... Я буду вивчати... Я буду жити...'
  - 'Signal words that mark tense shifts: Past: раніше (before), у дитинстві (in childhood),
    коли я був/була маленьким/маленькою (when I was little). Present: зараз (now),
    сьогодні (today), цього року (this year). Future: потім (then), далі (further),
    наступного року (next year). These words help the listener know which tense is
    coming.'
- section: Моя історія (My Story)
  words: 300
  points:
  - 'Model story — Taras''s life: Я народився в Одесі у тисяча дев''ятсот дев''яносто
    п''ятому році. Я жив там з батьками і сестрою. Я ходив у школу і любив математику.
    Потім я переїхав у Київ і вчився в університеті. Зараз я живу в Києві. Я працюю
    програмістом. Я люблю свою роботу. У вільний час я граю у футбол і читаю книжки.
    Далі я буду подорожувати. Я буду вивчати англійську. І я буду жити в Києві — це
    моє місто! Past (народився, жив, ходив) → Present (живу, працюю) → Future (буду
    подорожувати).'
  - 'Your turn — tell YOUR story: Start: Я народився/народилася в [city/country].
    Past: Я жив/жила... Я вчився/вчилася... Я працював/працювала... Present: Зараз
    я живу... Я працюю... Я вивчаю українську, тому що... Future: Я буду... Я хочу...
    Use at least 3 past verbs, 3 present verbs, and 3 future constructions.'
- section: Summary
  words: 300
  points:
  - 'Three tenses — one story: Past: -в/-ла/-ло/-ли (gender endings). Я народився.
    Я жила. Present: person endings. Я живу. Ти працюєш. Вона вивчає. Future: буду
    + infinitive. Я буду працювати. Вона буде жити. Signal words: раніше → past, зараз
    → present, далі → future. Life story vocabulary: народитися (to be born), жити
    (to live), вчитися (to study), переїхати (to move), подорожувати (to travel).
    Self-check: Write your life story in 8-10 sentences using all three tenses.'
vocabulary_hints:
  required:
  - народитися (to be born)
  - жити (to live)
  - вчитися (to study)
  - переїхати (to move)
  - зараз (now)
  - раніше (before/earlier)
  - далі (further/next)
  - розповідати (to tell/narrate)
  recommended:
  - подорожувати (to travel)
  - закінчити (to finish/graduate)
  - дитинство (childhood, n)
  - університет (university, m)
  - програміст (programmer, m)
  - успіх (success, m)
  - мрія (dream, f)
  - батьки (parents, pl)
activity_hints:
- type: ordering
  focus: Put the life events in logical chronological order
  items:
  - Я народився в Торонто.
  - У дитинстві я жив з батьками.
  - Потім я вчився в університеті.
  - Зараз я живу в Києві і працюю програмістом.
  - Далі я буду подорожувати.
- type: fill-in
  focus: Use signal words to determine the correct tense
  items:
  - Раніше я {жив|живу|буду жити} в Канаді.
  - Зараз я {працюю|працював|буду працювати} в університеті.
  - Далі я {буду вивчати|вивчав|вивчаю} українську мову.
  - У дитинстві вона {любила|любить|буде любити} читати.
  - Сьогодні ми {живемо|жили|будемо жити} в Україні.
- type: matching
  focus: Match the life event verb to the correct tense category
  pairs:
  - народився: Минулий час (Past)
  - переїхала: Минулий час (Past)
  - живу: Теперішній час (Present)
  - працюю: Теперішній час (Present)
  - буду подорожувати: Майбутній час (Future)
  - будемо вчитися: Майбутній час (Future)
- type: fill-in
  focus: Complete a biography combining all three tenses
  items:
  - Я {народилася|народився|народилися} у Львові.
  - Там я {вчилася|вчився|вчилися} в школі.
  - Зараз я {працюю|працювала|буду працювати} вчителькою.
  - Наступного року я {буду подорожувати|подорожувала|подорожую}.
connects_to:
- a1-053 (Health)
prerequisites:
- a1-051 (My Plans)
grammar:
- 'All three tenses combined: past (-в/-ла), present (person endings), future (буду
  + inf)'
- 'Tense-shift signal words: раніше, зараз, далі'
- 'Life story verbs: народитися, жити, вчитися, переїхати'
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: All three tenses combined in narrative — capstone grammar for A1.

</plan_content>

## Generated Content

<generated_module_content>
## Dialogues

Learning a language is about connecting with people. You already know how to state simple facts about yourself: your name, your country, and your profession. Now, it is time to move from simple facts to a cohesive narrative. A life story spans across time. You need to talk about where you were born, what you do now, and what you plan for the future. By combining the past, present, and future tenses, you can share your unique journey. 

When getting to know someone deeply, you will ask about their past and their plans. Read this interview between two friends.

> **Олег:** **Розкажи про себе!** *(Tell about yourself!)*
> **Марко:** **Я народився в Канаді, у Торонто.** *(I was born in Canada, in Toronto.)*
> **Олег:** **А зараз ти живеш тут?** *(And now do you live here?)*
> **Марко:** **Так, зараз я живу в Києві.** *(Yes, now I live in Kyiv.)*
> **Олег:** **Чому ти переїхав?** *(Why did you move?)*
> **Марко:** **Я хотів вивчати українську.** *(I wanted to study Ukrainian.)* **Мої бабуся і дідусь з України.** *(My grandmother and grandfather are from Ukraine.)*
> **Олег:** **А що ти будеш робити далі?** *(And what will you do next?)*
> **Марко:** **Я буду працювати тут і вчити мову.** *(I will work here and study the language.)*
> **Олег:** **Чудово! Успіхів тобі!** *(Wonderful! Success to you!)*

Notice how Marko moves smoothly through time. He starts in the past with **народився** (was born). Then, he uses the present tense **живу** (I live) to describe his current situation. Finally, he shifts to the future tense with **буду працювати** (I will work). In just a few sentences, he paints a complete picture of his life using three different grammatical timeframes.

Now, let us read Anna's story. She talks about her education and her career path.

> **Максим:** **Анно, розкажи свою історію.** *(Anna, tell your story.)*
> **Анна:** **Я народилася у Львові.** *(I was born in Lviv.)* **Там я вчилася в школі.** *(There I studied in school.)*
> **Максим:** **А університет?** *(And university?)*
> **Анна:** **Потім я переїхала в Київ і закінчила університет.** *(Then I moved to Kyiv and finished university.)*
> **Максим:** **Ким ти працюєш?** *(What do you work as?)*
> **Анна:** **Зараз я працюю вчителькою і живу в центрі міста.** *(Now I work as a teacher and live in the city center.)*
> **Максим:** **А що далі?** *(And what next?)*
> **Анна:** **Я буду подорожувати!** *(I will travel!)* **Я хочу побачити Японію.** *(I want to see Japan.)*
> **Максим:** **І ти будеш вчити японську?** *(And you will study Japanese?)*
> **Анна:** **Може! Але спочатку — українська для тебе!** *(Maybe! But first — Ukrainian for you!)*

Anna explains her sequence of life events clearly: Birth, School, University, Job, and Future Dream. Because Anna is a woman, she uses feminine past tense endings: **народилася** (was born), **вчилася** (studied), and **переїхала** (moved). Each stage of her life requires a specific grammatical form to show exactly when it happened.

## Три часи разом (Three Tenses Together)

To tell your biography, you need a "Time Line" that combines three main structures. First, the Past Tense (**Минулий час**). This uses gendered endings: **-в** for masculine, and **-ла** for feminine. Second, the Present Tense (**Теперішній час**). This uses person endings, like **-ю** or **-єш**. Third, the Compound Future Tense (**Майбутній час**). This uses the auxiliary verb **буду** plus an infinitive. Together, they organize your story.

Let us look at a grandparent telling their life story to their grandchildren. This perfectly demonstrates the Past Tense.

> **Дідусь:** **Я народився в селі.** *(I was born in a village.)*
> **Онук:** **Там була школа?** *(Was there a school there?)*
> **Дідусь:** **Так, я ходив у школу.** *(Yes, I went to school.)*

The verb **народитися** means "to be born". It is almost always used in the past tense. A man says **я народився**, and a woman says **я народилася**. Other key verbs are **жити** (to live) and **вчитися** (to study).
*   **Він жив у селі.** (He lived in a village.)
*   **Вона жила у місті.** (She lived in a city.)
*   **Я вчився в університеті.** (I studied at the university. — masculine)

Next, you ground your story in the present. Use the adverb **зараз** (now) to show you are talking about today. The Present Tense uses endings that match the person speaking.
*   **Зараз я живу в місті.** (Now I live in a city.)
*   **Зараз я працюю в лікарні.** (Now I work in a hospital.)
*   **Я вивчаю українську мову.** (I study the Ukrainian language.)

These actions are happening right now in your timeline. 

Finally, you look forward. The Future Tense describes your plans and dreams. Use the words **потім** (then) and **далі** (further) to signal a shift into the future. Form the future by taking **буду** (I will) and adding an infinitive verb.
*   **Потім я буду жити в Одесі.** (Then I will live in Odesa.)
*   **Далі ми будемо подорожувати.** (Further we will travel.)
*   **Я буду відпочивати на дачі.** (I will rest at the dacha.)

Signal words are crucial. They tell the listener which tense is coming before you even say the verb. Here is a table of the most important signal words for your life story:

| Signal Word | Meaning | Tense Trigger |
| :--- | :--- | :--- |
| **раніше** | before / earlier | Past |
| **у дитинстві** | in childhood | Past |
| **коли я був маленьким** | when I was little (masc) | Past |
| **зараз** | now | Present |
| **сьогодні** | today | Present |
| **цього року** | this year | Present |
| **потім** | then | Future |
| **далі** | further / next | Future |
| **наступного року** | next year | Future |

If you start a sentence with **раніше**, your listener automatically expects a past tense verb.

<!-- INJECT_ACTIVITY: matching-tense-category -->

<!-- INJECT_ACTIVITY: fill-in-signal-words -->

## Моя історія (My Story)

Now, read a complete model story. This is Taras's life. Notice how he connects simple sentences into a full biography.

*   **Я народився в Одесі у тисяча дев'ятсот дев'яносто п'ятому році.** (I was born in Odesa in nineteen ninety-five.)
*   **Я жив там з батьками і сестрою.** (I lived there with parents and sister.)
*   **Я ходив у школу і любив математику.** (I went to school and loved math.)
*   **Потім я переїхав у Київ і вчився в університеті.** (Then I moved to Kyiv and studied in the university.)
*   **Зараз я живу в Києві.** (Now I live in Kyiv.)
*   **Я працюю програмістом.** (I work as a programmer.)
*   **Я люблю свою роботу.** (I love my work.)
*   **У вільний час я граю у футбол і читаю книжки.** (In free time I play football and read books.)
*   **Далі я буду подорожувати.** (Next I will travel.)
*   **Я буду вивчати англійську.** (I will study English.)
*   **І я буду жити в Києві — це моє місто!** (And I will live in Kyiv — this is my city!)

Taras's story uses a clear structure taught in Ukrainian schools. It has three parts. First is the **Зачин** (Introduction) — he states his birth and childhood. Second is the **Основна частина** (Main Part) — he describes his current life, job, and hobbies. Third is the **Кінцівка** (Conclusion) — he shares his future plans and his feelings about his city.

A key verb for storytelling is **переїхати** (to move). It acts as a bridge between locations and times in your life. Another important verb is **закінчити** (to finish / to graduate). When you talk about the future, you can mention a **мрія** (dream). Using **переїхати** physically changes the setting of your narrative from your past home to your present home.

Now it is your turn to tell your story. You will write a short biography of 8 to 10 sentences. Follow these steps. Start with the past. Use these sentence starters:
*   **Я народився в...** (I was born in...) or **Я народилася в...** (for women).
*   **Я жив у...** (I lived in...) or **Я жила у...**
*   **Я вчився в...** (I studied in...) or **Я вчилася в...**
*   **Я працював...** (I worked...) or **Я працювала...**

Then, move to the present.
*   **Зараз я живу в...** (Now I live in...)
*   **Я працюю...** (I work...)
*   **Я вивчаю українську...** (I study Ukrainian...)

Finally, finish with the future.
*   **Далі я буду...** (Next I will...)
*   **Я хочу...** (I want...)

Use at least three past verbs, three present verbs, and three future constructions.

<!-- INJECT_ACTIVITY: ordering-life-events -->

<!-- INJECT_ACTIVITY: fill-in-biography-combined -->

## Summary

You can now tell a complete life story. The three-tense system is your timeline. Here is a final recap:

| Tense | Form | Example |
| :--- | :--- | :--- |
| **Минулий** (Past) | **-в** (m), **-ла** (f), **-ли** (pl) | **Я народився.** (I was born.) / **Я жила.** (I lived.) |
| **Теперішній** (Present) | **-ю**, **-єш**, **-є** (person endings) | **Я живу.** (I live.) / **Ти працюєш.** (You work.) |
| **Майбутній** (Future) | **буду**, **будеш**, **буде** + infinitive | **Я буду працювати.** (I will work.) |

Let us check your core vocabulary for this module. You need these eight words to narrate your journey:
*   **народитися** (to be born): **Я народився в Америці.** (I was born in America.)
*   **жити** (to live): **Ми живемо в місті.** (We live in the city.)
*   **вчитися** (to study): **Вона вчиться в школі.** (She studies at school.)
*   **переїхати** (to move): **Я хочу переїхати в Україну.** (I want to move to Ukraine.)
*   **зараз** (now): **Зараз він працює.** (Now he is working.)
*   **раніше** (before / earlier): **Раніше я жив там.** (Before I lived there.)
*   **далі** (further / next): **Що ти будеш робити далі?** (What will you do next?)
*   **розповідати** (to tell / narrate): **Я люблю розповідати історії.** (I love to tell stories.)

Before you finish this module, use this self-check checklist:
*   Can you state where you were born using the correct gender agreement (**народився** or **народилася**)?
*   Can you use the word **зараз** to describe your current job or study?
*   Can you list two things you will do next year using **буду**?
*   Do you know the difference between **раніше** (before) and **потім** (then)?
*   Have you written your own 8-10 sentence narrative using all three tenses?
</generated_module_content>

**PIPELINE NOTE — Word count: 1722 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 141 words | Not found: 9 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Америці — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Анно — NOT IN VESUM
  ✗ Канаді — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Одесі — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Торонто — NOT IN VESUM
  ✗ Японію — NOT IN VESUM

All 141 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
