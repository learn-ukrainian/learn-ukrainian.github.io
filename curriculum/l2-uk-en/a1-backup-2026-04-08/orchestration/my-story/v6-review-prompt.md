<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 52: My Story (A1, A1.8 [Past, Future, Graduation])
**Writer:** Claude
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

Two people meet at a language school in Kyiv. One has lived here for years; the other just arrived. They want to know each other's full story — where they come from, what they do now, and what comes next.

> — **Окса́на:** Розкажи́ про себе́! *(Tell me about yourself!)*
> — **Макси́м:** Я народи́вся в Кана́ді, у Торо́нто. *(I was born in Canada, in Toronto.)*
> — **Оксана:** А за́раз ти живе́ш тут? *(And now you live here?)*
> — **Максим:** Так, зараз я живу́ в Ки́єві. *(Yes, now I live in Kyiv.)*
> — **Оксана:** Чо́му ти переї́хав? *(Why did you move?)*
> — **Максим:** Я хоті́в вивча́ти украї́нську. *(I wanted to study Ukrainian.)* Мої́ бабу́ся і діду́сь з Украї́ни. *(My grandma and grandpa are from Ukraine.)*
> — **Оксана:** А що ти бу́деш роби́ти да́лі? *(And what will you do next?)*
> — **Максим:** Я бу́ду працюва́ти тут і вчи́ти мо́ву. *(I will work here and learn the language.)*
> — **Оксана:** Чудо́во! У́спіхів тобі́! *(Wonderful! Best of luck!)*

All three tenses appear in this single conversation. **Народився** (was born) — past. **Живу** (live) — present. **Буду працювати** (will work) — future. Maksym moves naturally from his childhood in Canada, through his present life in Kyiv, to his future plans. That is the shape of every life story.

Now hear Anna tell her story — from birth to future dreams.

> — **А́нна:** Я народи́лася у Льво́ві. *(I was born in Lviv.)* Там я вчи́лася в шко́лі. *(I studied at school there.)*
> — **Коле́га:** А по́тім? *(And then?)*
> — **Анна:** Потім я переї́хала в Ки́їв. *(Then I moved to Kyiv.)* Я закі́нчи́ла університе́т. *(I finished university.)*
> — **Колега:** А зараз? *(And now?)*
> — **Анна:** Зараз я працю́ю вчи́телькою. *(Now I work as a teacher.)* Я живу в це́нтрі мі́ста. *(I live in the city centre.)*
> — **Колега:** А що далі? *(And what's next?)*
> — **Анна:** Я буду подорожува́ти! *(I will travel!)* Я хо́чу поба́чити Япо́нію. *(I want to see Japan.)*
> — **Колега:** І ти будеш вчити япо́нську? *(And you'll learn Japanese?)*
> — **Анна:** Мо́же! Але́ споча́тку — украї́нська для тебе́! *(Maybe! But first — Ukrainian for you!)*

Notice how Anna's story flows: past (**народилася**, **вчилася**, **переїхала**, **закінчила**) → present (**працюю**, **живу**) → future (**буду подорожувати**). The story moves forward in time, just like Maksym's. Past events first, then what is true now, then dreams. That is the shape of every life story in Ukrainian.

## Три часи́ ра́зом (Three Tenses Together)

Every life story has three parts. Here is the scaffold you need:

**МИНУ́ЛИЙ ЧАС** (past tense) — things that already happened:
- **Я народився** / **народилася** в... *(I was born in...)*
- **Я жив** / **жила́** в... *(I lived in...)*
- **Я вчи́вся** / **вчилася**... *(I studied...)*
- **Я працюва́в** / **працюва́ла**... *(I worked...)*

**ТЕПЕ́РІШНІЙ ЧАС** (present tense) — what is true right now:
- **Зараз я живу** в... *(Now I live in...)*
- **Я працюю**... *(I work...)*
- **Я вивча́ю**... *(I study/am learning...)*
- **Я люблю́**... *(I love...)*

**МАЙБУ́ТНІЙ ЧАС** (future tense) — what will come:
- **Я буду працювати**... *(I will work...)*
- **Я буду вивчати**... *(I will study...)*
- **Я буду жи́ти**... *(I will live...)*

Look at the past tense forms closely. Gender matters: **-в** for masculine (**я народивСЯ**) and **-ла** for feminine (**я народиЛАся**). Three more pairs: **жив** / **жила**, **вчився** / **вчилася**, **працював** / **працювала**. A man says **я народився**, a woman says **я народилася** — the ending always tells you.

Signal words are the listener's roadmap. They tell the listener which tense is coming before the verb arrives:

**Past signals:** **рані́ше** (before/earlier), **у дити́нстві** (in childhood), **тоді́** (back then).
**Present signals:** **зараз** (now), **сього́дні** (today), **цього́ ро́ку** (this year).
**Future signals:** **потім** (then/later), **далі** (further/next), **насту́пного року** (next year), **ско́ро** (soon).

Compare this pair: **Раніше я жив у Канаді** *(Before, I lived in Canada)* vs. **Зараз я живу в Украї́ні** *(Now I live in Ukraine)*. Same verb root **жи-**, opposite tense, different signal word. The signal word does the work.

Ukrainian speakers use **А потім...** *(And then...)* to move from past to present and **А далі...** *(And next...)* to move from present to future. These two phrases are the hinges of every life story. Try it: **Я народився в Оде́сі. А потім я переїхав у Київ. А далі — я буду подорожувати!** *(I was born in Odesa. And then I moved to Kyiv. And next — I will travel!)*

<!-- INJECT_ACTIVITY: fill-in-signal-words -->

## Моя́ істо́рія (My Story)

Now read a full model story. Taras is a programmer from Odesa who moved to Kyiv. Read his story and notice how all three tenses flow together naturally.

:::note
**Тара́с розповіда́є** *(Taras tells his story)*

**Я народився в Одесі.** *(I was born in Odesa.)* **Я жив там з батька́ми і сестро́ю.** *(I lived there with my parents and sister.)* **У дитинстві я ходи́в у шко́лу.** *(In childhood I went to school.)* **Я люби́в матема́тику.** *(I loved maths.)* **Потім я переїхав у Київ.** *(Then I moved to Kyiv.)* **Я вчився в університе́ті.** *(I studied at university.)*

**Зараз я живу в Києві.** *(Now I live in Kyiv.)* **Я працюю програмі́стом.** *(I work as a programmer.)* **Я люблю свою́ робо́ту.** *(I love my job.)* **На дозві́ллі я гра́ю у футбо́л.** *(In my free time I play football.)* **Я чита́ю книжки́.** *(I read books.)*

**Далі я буду подорожувати.** *(Next I will travel.)* **Я буду вивчати англі́йську.** *(I will study English.)* **І я буду жити в Києві.** *(And I will live in Kyiv.)* **Це моє́ мі́сто!** *(This is my city!)*
:::

The tense shifts are clear. Past verbs: **народився**, **жив**, **ходив**, **любив**, **переїхав**, **вчився**. Present verbs: **живу**, **працюю**, **люблю**, **граю**, **читаю**. Future constructions: **буду подорожувати**, **буду вивчати**, **буду жити**. Each block has its own signal word: **у дитинстві** and **потім** for the past, **зараз** for the present, **далі** for the future.

<!-- INJECT_ACTIVITY: ordering-life-events -->

Now your turn. Tell YOUR story using the same scaffold:

**Past** — start with: **Я народився** / **народилася** в [місто/краї́на]. Then add: **Я жив/жила...** **Я вчився/вчилася...** Use at least three past verbs with the correct gender ending (**-в** or **-ла**).

**Present** — shift with **зараз**: **Зараз я живу...** **Я працюю...** **Я вивчаю українську.** Why are you learning? **Я вивчаю українську, тому́ що...** *(I'm studying Ukrainian because...)*

**Future** — shift with **далі**: **Я буду...** **Я хочу...** Use at least three **буду** + infinitive constructions.

Target: 8–10 sentences. Use **раніше** / **зараз** / **далі** to signal each tense shift. Remember: past verbs change by gender (**-в** for he, **-ла** for she), present verbs change by person (**я живу**, **ти живеш**), and future always uses **буду** + infinitive.

<!-- INJECT_ACTIVITY: fill-in-biography -->

## Summary

Three tenses — three patterns. Here they are side by side.

**Минулий час** (past tense) — add **-в** (masculine), **-ла** (feminine), **-ло** (neuter), or **-ли** (plural) to the verb stem:
- **народи́в-ся** / **народи́ла-ся** *(was born)*
- **жи-в** / **жи-ла** *(lived)*
- **вчи-в-ся** / **вчи-ла-ся** *(studied)*

**Теперішній час** (present tense) — person endings:
- **я живу**, **ти живеш**, **він/вона́ живе́**
- **ми живемо́**, **ви живете́**, **вони́ живу́ть**

**Майбутній час** (future tense) — **буду** + infinitive:
- **я буду подорожувати** *(I will travel)*
- **ти будеш працювати** *(you will work)*
- **він/вона бу́де вивчати** *(he/she will study)*

At A1, future tense always uses **буду** + infinitive — never a single conjugated form.

**Signal words — quick reference:**

**МИНУЛИЙ:** **раніше** *(earlier)*, **у дитинстві** *(in childhood)*, **тоді** *(back then)*, **потім** *(then, narrating past sequence)*.
**ТЕПЕРІШНІЙ:** **зараз** *(now)*, **сьогодні** *(today)*, **цього року** *(this year)*.
**МАЙБУТНІЙ:** **далі** *(next)*, **потім** *(then, pointing forward)*, **наступного року** *(next year)*, **скоро** *(soon)*.

:::tip
The word **потім** can signal a past sequence OR a future plan — context tells you which!
:::

**Life story vocabulary** — words every story needs:

- **народи́тися** *(to be born)* — я народився / народилася
- **жити** *(to live)* — я жив / жила / живу / буду жити
- **вчи́тися** *(to study)* — я вчився / вчилася / буду вчитися
- **переї́хати** *(to move/relocate)* — я переїхав / переїхала
- **подорожувати** *(to travel)* — я буду подорожувати
- **закі́нчи́ти** *(to finish/graduate)* — я закі́нчи́в / закінчила
- **розповіда́ти** *(to tell/narrate)* — я розповіда́ю / буду розповідати

<!-- INJECT_ACTIVITY: matching-verb-tense -->

**Deterministic word count: 1208 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

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
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
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

Verified: 119 words | Not found: 49 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Кана — NOT IN VESUM
  ✗ Канаді — NOT IN VESUM
  ✗ Льво — NOT IN VESUM
  ✗ Макси — NOT IN VESUM
  ✗ Оде — NOT IN VESUM
  ✗ Одесі — NOT IN VESUM
  ✗ Окса — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Украї — NOT IN VESUM
  ✗ Япо — NOT IN VESUM
  ✗ англі — NOT IN VESUM
  ✗ деш — NOT IN VESUM
  ✗ дозві — NOT IN VESUM
  ✗ закі — NOT IN VESUM
  ✗ зом — NOT IN VESUM
  ✗ йську — NOT IN VESUM
  ✗ лася — NOT IN VESUM
  ✗ ллі — NOT IN VESUM
  ✗ матема — NOT IN VESUM
  ✗ нна — NOT IN VESUM
  ✗ нстві — NOT IN VESUM
  ✗ нська — NOT IN VESUM
  ✗ нську — NOT IN VESUM
  ✗ нто — NOT IN VESUM
  ✗ нтрі — NOT IN VESUM
  ✗ нчи — NOT IN VESUM
  ✗ нію — NOT IN VESUM
  ✗ переї — NOT IN VESUM
  ✗ пного — NOT IN VESUM
  ✗ поба — NOT IN VESUM
  ✗ подорожува — NOT IN VESUM
  ✗ працюва — NOT IN VESUM
  ✗ рія — NOT IN VESUM
  ✗ ско — NOT IN VESUM
  ✗ споча — NOT IN VESUM
  ✗ спіхів — NOT IN VESUM
  ✗ телькою — NOT IN VESUM
  ✗ тися — NOT IN VESUM
  ✗ тку — NOT IN VESUM
  ✗ украї — NOT IN VESUM
  ✗ університе — NOT IN VESUM
  ✗ футбо — NOT IN VESUM
  ✗ хав — NOT IN VESUM
  ✗ чити — NOT IN VESUM
  ✗ шко — NOT IN VESUM
  ✗ япо — NOT IN VESUM
  ✗ єві — NOT IN VESUM
  ✗ істо — NOT IN VESUM

All 119 other words are confirmed to exist in VESUM.

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
