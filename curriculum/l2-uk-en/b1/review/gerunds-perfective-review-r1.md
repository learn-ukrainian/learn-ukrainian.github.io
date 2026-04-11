## Linguistic Scan
Linguistic errors found:
- **Russianisms / Calques:** 12 instances of the calque `Давайте` + verb (e.g. "Давайте розглянемо" замість "Розгляньмо").
- **Russianisms (Active Participles):** `надихаючий` (not in VESUM) -> `надихальний`, `розслаблюючу` (not in VESUM) -> `розслаблювальну`.
- **Lexical calques:** `зустрічаються у текстах` -> `трапляються у текстах`; `слідкуйте за` -> `стежте за`; `виступає в ролі` -> `слугує` або `є`.
- **Semantic error:** `питання` замість `запитання` (відповів на всі питання викладача).
- **Critical Factual Error:** The text hallucinates that the suffix `-ши` ends in a consonant sound (`приголосний звук від суфікса «-ши»`) and therefore forces the reflexive particle `-ся`. In reality, `-ши` ends in the vowel `и`, and therefore gerunds always take the particle `-сь` (e.g., `розбігшись`).

## Exercise Check
- All required exercises from the plan's `activity_hints` are represented by `<!-- INJECT_ACTIVITY: {id} -->` markers. 
- The generated markers are evenly distributed immediately following the relevant grammatical explanations, which correctly tests the skill that was just taught.
- Note: The plan specified exactly 6 `activity_hints`, but the writer generated 12 markers (e.g. adding `aspect-choice-quiz`, `fill-in-gerund-aspect`, etc.). This is acceptable as it increases practice density, but it is technically double the requested count.
- The logic and placement of the markers perfectly align with the pedagogical flow.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | The module flawlessly executes the plan. The difference between `одночасність` and `різночасність` is clear, and all vocabulary is used naturally. |
| 2. Linguistic accuracy | 7/10 | Deductions for 12 instances of `Давайте + дієслово`, using active participles (`надихаючий`, `розслаблюючу`), calques (`зустрічаються`, `слідкуйте`, `виступає в ролі`), and a critical phonetic error about `-ши` ending in a consonant. |
| 3. Pedagogical quality | 9/10 | Excellent use of narrative (detective story) and logical contrast pairs to teach aspect. 1 point deducted because the phonetic hallucination about `-ши` ending in a consonant and taking `-ся` will severely confuse learners. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words (e.g., `повернувшись`, `прокинувшись`, `дізнавшись`) are perfectly integrated. |
| 5. Exercise quality | 9/10 | Excellent placement of markers directly after concepts. Deduct 1 point for generating 12 markers when only 6 were requested in the plan, causing over-saturation. |
| 6. Engagement & tone | 10/10 | Highly engaging. The examples are vivid, and the explanation of the "dangling participle" is conversational and genuinely helpful. |
| 7. Structural integrity | 10/10 | Clean markdown, all required sections present. The word count is a robust 4872 words, far exceeding the 4000-word target. |
| 8. Cultural accuracy | 10/10 | Explicitly decolonizes the grammar by directly contrasting correct Ukrainian forms with Russian-style active participles (`прочитавший студент`), explaining why they are wrong. |
| 9. Dialogue & conversation quality | 10/10 | The police station dialogue is crisp, professional, and efficiently demonstrates sequential gerund logic in a realistic setting. |

## Findings

[Linguistic accuracy] [Critical]
Location: Section "Творення дієприслівників доконаного виду": "Якщо ж перед зворотною часткою раптом стоїть приголосний звук від суфікса «-ши», вона теоретично залишається у своїй повній формі «-ся»."
Issue: Phonetic and morphological hallucination. The suffix "-ши" ends in the vowel "и", not a consonant. Thus, the reflexive particle after any gerund suffix (-чи, -вши, -ши) is ALWAYS "-сь" (e.g., розбігшись), never "-ся".
Fix: Correct the text to explain that "-ши" also ends in a vowel, so it takes the "-сь" particle.

[Linguistic accuracy] [Major]
Location: Throughout the text (12 instances, e.g., "Давайте обережно розкладемо", "Давайте на мить згадаємо", "Давайте критично проаналізуємо").
Issue: Systematic use of the Russian calque "Давайте" + infinitive/future instead of the correct Ukrainian synthetic imperative mood (розкладімо, згадаймо, проаналізуймо).
Fix: Replace all "Давайте + дієслово" constructions with the correct synthetic imperative form.

[Linguistic accuracy] [Major]
Location: Section "Читання та вільне письмо": "Уявіть, що ви повинні обов'язково написати невеликий надихаючий звіт..." and "**Слухаючи** *(Listening to)* тиху та розслаблюючу класичну музику..."
Issue: Usage of active participles ending in -учий/-ючий ("надихаючий", "розслаблюючу"), which are Russianisms.
Fix: Replace with "надихальний" and "розслаблювальну".

[Linguistic accuracy] [Minor]
Location: Section "Читання та вільне письмо": "слідкуйте за правильним логічним узгодженням"
Issue: "Слідкувати" means to follow tracks or spy; for logic and rules, the correct word is "стежити".
Fix: Change "слідкуйте" to "стежте".

[Linguistic accuracy] [Minor]
Location: Section "Дієприслівник vs підрядне речення": "студент дуже швидко відповів на всі питання свого викладача."
Issue: In the context of a teacher asking things, "запитання" is the correct term.
Fix: Change "питання" to "запитання".

[Linguistic accuracy] [Minor]
Location: Sections "Творення" and "Дієприслівник vs підрядне речення": "зустрічаються у реальних текстах", "будете постійно зустрічати їх"
Issue: Calque from Russian "встречаться" in the context of encountering words/phenomena in texts. Correct is "трапляються" or "натраплятимете на".
Fix: Replace "зустрічаються" with "трапляються" and "зустрічати" with "натраплятимете на".

[Linguistic accuracy] [Minor]
Location: Various sections ("виступає в ролі необхідної попередньої умови", "Він виступає як супровідний паралельний процес", "підметом виступає іменник дощ").
Issue: Calque from Russian "выступать в роли" in contexts where "бути" or "слугувати" is needed.
Fix: Replace with "слугує", "функціонує як", or "є".

## Verdict: REVISE
The module covers the plan wonderfully and has excellent structural and pedagogical pacing. However, it contains a critical phonetic mistake regarding gerund suffixes, several Russian active participles, and systematic overuse of the "Давайте" calque. These issues must be fixed before the module can ship. 

<fixes>
- find: "Якщо ж перед зворотною часткою раптом стоїть приголосний звук від суфікса «-ши», вона теоретично залишається у своїй повній формі «-ся». Проте такі складні конструкції зустрічаються у реальних текстах вкрай рідко."
  replace: "Оскільки суфікс «-ши» також закінчується на голосний звук, після нього зворотна частка так само має форму «-сь» (наприклад, розбігшись). Проте такі складні конструкції з приголосними основами трапляються у реальних текстах вкрай рідко."
- find: "Давайте обережно розкладемо цю звичайну життєву ситуацію на окремі, зрозумілі етапи."
  replace: "Обережно розкладімо цю звичайну життєву ситуацію на окремі, зрозумілі етапи."
- find: "Давайте на мить згадаємо нашу попередню граматичну тему, де ми дуже докладно вивчали недоконаний вид."
  replace: "На мить згадаймо нашу попередню граматичну тему, де ми дуже докладно вивчали недоконаний вид."
- find: "Давайте тепер розглянемо практичний життєвий приклад, щоб надійно закріпити всі ці необхідні теоретичні знання."
  replace: "Тепер розгляньмо практичний життєвий приклад, щоб надійно закріпити всі ці необхідні теоретичні знання."
- find: "Давайте візьмемо для нашого аналізу дуже показову пару речень про звичайні ранкові гігієнічні процедури у ванній кімнаті."
  replace: "Візьмімо для нашого аналізу дуже показову пару речень про звичайні ранкові гігієнічні процедури у ванній кімнаті."
- find: "Давайте порівняємо два дуже схожих, але різних за своєю правильністю речення."
  replace: "Порівняймо два дуже схожих, але різних за своєю правильністю речення."
- find: "Давайте разом розглянемо класичний приклад такої граматичної трансформації."
  replace: "Разом розгляньмо класичний приклад такої граматичної трансформації."
- find: "Давайте критично проаналізуємо дуже поширене, але неправильне речення, яке часто будують іноземці:"
  replace: "Критично проаналізуймо дуже поширене, але неправильне речення, яке часто будують іноземці:"
- find: "Давайте знайдемо головну частину: тут підметом виступає іменник **дощ** *(rain)*, а основним присудком є дієслово **почався** *(started)*."
  replace: "Знайдімо головну частину: тут підметом є іменник **дощ** *(rain)*, а основним присудком — дієслово **почався** *(started)*."
- find: "Давайте дуже уважно проаналізуємо цей детективний текст, щоб глибоко зрозуміти стилістичну роль наших нових граматичних форм."
  replace: "Дуже уважно проаналізуймо цей детективний текст, щоб глибоко зрозуміти стилістичну роль наших нових граматичних форм."
- find: "Тепер давайте разом розберемося, як саме їх правильно утворювати."
  replace: "Тепер розберімося разом, як саме їх правильно утворювати."
- find: "Давайте уважно подивимося на кілька конкретних і дуже зрозумілих прикладів."
  replace: "Уважно подивімося на кілька конкретних і дуже зрозумілих прикладів."
- find: "Щоб ще краще і глибше відчути цей строгий, формальний ритм послідовних завершених дій, давайте уявимо серйозну розмову у міському поліцейському відділку."
  replace: "Щоб ще краще і глибше відчути цей строгий, формальний ритм послідовних завершених дій, уявімо серйозну розмову у міському поліцейському відділку."
- find: "Уявіть, що ви повинні обов'язково написати невеликий надихаючий звіт про ваш «Найпродуктивніший ранок»."
  replace: "Уявіть, що ви повинні обов'язково написати невеликий надихальний звіт про ваш «Найпродуктивніший ранок»."
- find: "**Слухаючи** *(Listening to)* тиху та розслаблюючу класичну музику, я працював над проєктом дуже зосереджено та максимально ефективно."
  replace: "**Слухаючи** *(Listening to)* тиху та розслаблювальну класичну музику, я працював над проєктом дуже зосереджено та максимально ефективно."
- find: "Обов'язково та дуже уважно слідкуйте за правильним логічним узгодженням у кожному вашому реченні."
  replace: "Обов'язково та дуже уважно стежте за правильним логічним узгодженням у кожному вашому реченні."
- find: "студент дуже швидко відповів на всі питання свого викладача."
  replace: "студент дуже швидко відповів на всі запитання свого викладача."
- find: "Ви будете постійно зустрічати їх у класичній літературі, свіжих аналітичних новинах, серйозних офіційних документах"
  replace: "Ви постійно натраплятимете на них у класичній літературі, свіжих аналітичних новинах, серйозних офіційних документах"
- find: "Перший дієприслівник належить саме до доконаного виду, і він виступає в ролі необхідної попередньої умови для подальших подій."
  replace: "Перший дієприслівник належить саме до доконаного виду, і він слугує необхідною попередньою умовою для подальших подій."
- find: "Він виступає як супровідний паралельний процес, який відбувається одночасно із основною дією сніданку."
  replace: "Він функціонує як супровідний паралельний процес, який відбувається одночасно із основною дією сніданку."
</fixes>
