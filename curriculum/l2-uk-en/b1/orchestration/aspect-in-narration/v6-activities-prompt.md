<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-in-narration.yaml` file for module **6: Вид у розповіді** (b1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-aspect-analysis -->`
- `<!-- INJECT_ACTIVITY: group-sort-connectors -->`
- `<!-- INJECT_ACTIVITY: fill-in-aspect-narrative -->`
- `<!-- INJECT_ACTIVITY: match-aspect-logic -->`
- `<!-- INJECT_ACTIVITY: error-correction-narrative -->`
- `<!-- INJECT_ACTIVITY: open-writing-narrative -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify each verb in a narrative as тло (background/impf) or подія (foreground/pf)
    and explain why
  items: 10
  type: quiz
- focus: Choose the correct aspect (impf or pf) for verbs in a narrative passage based
    on their narrative function
  items: 8
  type: fill-in
- focus: Sort temporal connectors into background-connectors (тим часом, поки) and
    foreground-connectors (потім, раптом, нарешті)
  items: 8
  type: group-sort
- focus: Find aspect errors in narrative passages — background verbs that should be
    impf, event verbs that should be pf
  items: 6
  type: error-correction
- focus: Match narrative functions (setting, turning point, simultaneous action, sequential
    chain) to the correct aspect
  items: 8
  type: match-up
- focus: Write a short story (8-10 sentences) about an unexpected event — weave background
    (impf) and foreground (pf) deliberately
  items: 6
  type: open-writing


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

- pos: noun:n
  translation: background (narrative layer — imperfective)
  word: тло
- pos: noun phrase
  translation: foreground (narrative layer — perfective events)
  word: передній план
- pos: noun:f
  translation: narrative, story
  word: розповідь
- pos: noun:n
  translation: short story, narration
  word: оповідання
- pos: noun:m
  translation: narrator
  word: оповідач
- pos: noun:f
  translation: event (foreground — usually perfective)
  word: подія
- pos: noun:m
  translation: description (background — usually imperfective)
  word: опис
- pos: adv
  translation: at first, initially (sequential connector)
  word: спочатку
- pos: adv
  translation: then, afterwards (sequential connector)
  word: потім
- pos: adv
  translation: suddenly (event marker — perfective)
  word: раптом
- pos: adv
  translation: finally, at last (sequential endpoint)
  word: нарешті
- pos: adv phrase
  translation: meanwhile (simultaneous background)
  word: тим часом
- pos: adv
  translation: simultaneously (parallel actions — impf)
  word: одночасно
- pos: adv
  translation: sequentially (chain of events — pf)
  word: послідовно
- pos: noun:f
  translation: sequence (of events)
  word: послідовність
- pos: noun:m
  translation: memory, recollection
  word: спогад
- pos: conj
  translation: while (background connector)
  word: поки
- pos: adv phrase
  translation: after that (sequential connector)
  word: після цього
- pos: adv
  translation: then, at that time
  word: тоді


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Тест: тло чи подія?

When you tell a story, you are not just reciting a list of actions. A truly compelling narrative is a carefully layered construction of time. In Ukrainian, we build this structure primarily using the grammatical aspect of the verb. Every story has two distinct dimensions: the state of "being" and the moment of "happening". The state of being is your narrative background, the continuous reality where your characters exist. The happening is the sequence of events, the sudden changes, and the plot developments that push the story forward. Mastering the Ukrainian language means understanding how to weave these two layers together. You must learn to paint the scenery with the imperfective aspect and drive the action with the perfective aspect. This delicate balance creates a natural rhythm that native speakers feel instinctively. Without this rhythm, your story will sound unnaturally rushed or confusingly static.

Був теплий літній вечір. Сонце повільно сідало за обрій, і небо ставало темно-червоним. Ми сиділи на терасі ресторану і пили холодний лимонад. Навколо тихо грала приємна музика, а люди за сусідніми столиками розмовляли. Ніщо не віщувало біди. Раптом десь далеко пролунав вибух. Я здригнувся і випустив склянку з рук. Вона впала на підлогу і розбилася. Музика одразу стихла. Всі відвідувачі підвелися зі своїх місць і подивилися в бік вулиці. Ми зрозуміли, що наш вечір закінчився.

> *It was a warm summer evening. The sun was slowly setting over the horizon, and the sky was turning dark red. We were sitting on the terrace of a restaurant and drinking cold lemonade. Pleasant music was playing quietly around us, and people at neighboring tables were conversing. Nothing foreshadowed trouble. Suddenly, an explosion sounded somewhere far away. I flinched and dropped the glass from my hands. It fell onto the floor and shattered. The music immediately died down. All the patrons stood up from their seats and looked toward the street. We realized that our evening had ended.*

Read the short story above again and pay close attention to the verbs. Did you notice how the first half of the text feels completely different from the second half? The story begins by describing a continuous, unbroken state of affairs. The sun was setting, we were sitting, people were talking, and music was playing. These are ongoing actions without a clear beginning or end in the context of that moment. They form the atmospheric background of the narrative, which we call **тло** (background). Then, this peaceful atmosphere is suddenly broken by a sequence of completed actions. The explosion sounded, I flinched, the glass dropped, the music stopped, and everyone stood up. These are the interruptions, the actual plot points that happen sequentially, one after another. This chain of events is the foreground of the story, or **передній план** (foreground).

<!-- INJECT_ACTIVITY: quiz-aspect-analysis -->

To better understand this grammatical concept, imagine that storytelling is like directing a live theater play. Before the actors even start delivering their lines, you need to set up the stage. You arrange the furniture, adjust the lighting, and perhaps add the continuous sound of rain playing quietly in the background. This stage set is your imperfective aspect. It creates the physical environment, the ongoing mood, and the context for everything else. The play only truly begins when the actors step onto the stage and start doing things. Someone enters the room, delivers a secret letter, steals a document, or dramatically faints. These specific actors' actions are your perfective aspect. They are the dynamic, finalized events that change the situation. If you use the wrong aspect, it is like having the static stage props suddenly move around on their own.

Тло розповіді — це завжди недоконаний вид. Воно виконує виключно описову функцію. За допомогою тла ми показуємо статику, паралельні процеси, стан природи або емоційний стан головних героїв. Тло завжди відповідає на питання «що відбувалося в цей час?». Передній план розповіді — це завжди доконаний вид. Він має чітку динамічну функцію. Передній план показує конкретні послідовні події, які мають логічний результат і рухають сюжет уперед. Він відповідає на питання «що сталося потім?».

What happens if you decide to only use one aspect for an entire story? A narrative built entirely on background verbs feels stagnant and repetitive. Imagine reading: "We were sitting. We were drinking. We were looking at the street." This is a notoriously boring story because there is no plot, only an eternal state of waiting where nothing ever resolves. On the other hand, a story built entirely on foreground verbs feels incredibly dry. Imagine reading: "I stood up. I arrived at the house. I said the words. I left the room." This sounds exactly like a formal police report. It gives the listener the raw facts in a strict chronological sequence, but it completely lacks emotion or atmosphere. The true beauty of a Ukrainian narrative lies in the sharp contrast between the two.

Let us look at a logical constraint regarding aspect choices. Why do we naturally describe the evening using an imperfective verb, rather than attempting to use a perfective equivalent?

**Був теплий вечір.** — *It was a warm evening.*

If you force a perfective verb into a purely background description, you completely change its inherent meaning. If you somehow managed to use a perfective form to describe the presence of the evening, it would mean "A warm evening occurred, finished completely, and produced a final result." That contradicts the fundamental idea of a narrative setting. A setting surrounds the actual events; it does not happen as a sudden event itself. Therefore, atmospheric conditions and ongoing states cannot logically be perfective without turning into abrupt occurrences.

:::info
**The Rhythm of Storytelling**
Native Ukrainian speakers switch between aspects instinctively to control the pacing of their stories. Using the imperfective aspect slows the narrative down, allowing the listener to absorb the rich details of the environment. Switching to the perfective aspect speeds the story up, delivering a rapid sequence of action.
:::

## Тло: недоконаний вид у наративі

When you begin telling a story, you rarely jump straight into the action. Before the main character makes a decision or a dramatic event occurs, you need to establish the physical environment. This is the first primary function of the imperfective aspect in a narrative: setting the atmosphere. By using imperfective verbs like **стояти** (to stand), **світити** (to shine), or **шуміти** (to make noise), you create the sensory texture of the past. These verbs do not describe events that started and finished; rather, they describe ongoing states that existed before the story even began and continued as the events unfolded.

Коли оповідач хоче занурити читача в атмосферу, він використовує дієслова недоконаного виду для опису природи, погоди або інтер'єру. Надворі було дуже холодно, і з неба падав сніг. У старій кімнаті тихо тріщав вогонь, а на столі стояла гаряча кава. Усі ці дії не мають чіткого початку або кінця, вони просто існують у просторі і створюють настрій.

> *When a narrator wants to immerse the reader in the atmosphere, they use imperfective verbs to describe nature, weather, or an interior. It was very cold outside, and snow was falling from the sky. In the old room, the fire crackled quietly, and hot coffee stood on the table. All these actions do not have a clear beginning or end; they simply exist in the space and create a mood.*

The second function of the imperfective background is to show simultaneous actions. Life rarely happens in a strict, isolated sequence where one thing finishes before the next begins. Often, multiple continuous processes happen at exactly the same time, layering on top of each other. In Ukrainian, you express this synchronicity by pairing two or more imperfective verbs. Because neither action is presented as completed, they stretch out parallel to one another. This is essential for describing bustling scenes or the general domestic harmony of a household before a disruption occurs.

Ми часто описуємо паралельні процеси, щоб показати загальну картину життя. Поки батько уважно читав газету, мати готувала вечерю на кухні. Діти гралися у дворі, а собака спав біля дверей. Жодна з цих дій не перериває іншу; вони протікають одночасно, формуючи спільний фоновий ритм для майбутніх подій.

Beyond the physical environment, the narrative background also encompasses the internal landscape of your characters. Feelings, thoughts, and mental states usually serve as the emotional background for external actions. This is the third function of the imperfective aspect. When a character is worried, confused, or contemplating a decision, these states are continuous. They color the character's perception of the events unfolding around them. Using the imperfective aspect for mental states emphasizes that the emotion was an ongoing condition, not a sudden reaction.

Емоційний стан головного героя також є частиною тла, тому ми передаємо його через недоконаний вид. Він дуже хвилювався перед зустріччю і постійно дивився на годинник. Вона не розуміла, що відбувається, і просто чекала на допомогу друзів. Ці почуття тривали певний час, створюючи психологічну напругу.

:::info
**Mental States as Background**
Verbs like **знати** (to know), **розуміти** (to understand), and **думати** (to think) are almost exclusively used in the imperfective aspect when setting a scene. Knowing or understanding is inherently a continuous state.
:::

To weave these ongoing actions and states together smoothly, you need the grammar of duration. Ukrainian uses specific temporal connectors to signal that actions belong to the background layer. Connectors like **тим часом** (meanwhile), **у цей час** (at this time), and **поки** (while) naturally pair with imperfective verbs. They explicitly instruct the listener to interpret the following verb as a continuous process that overlaps with other elements of the story. Using these words helps you construct complex sentences without losing the logical flow.

Ці спеціальні слова допомагають нам організувати простір і час у тексті. Наприклад, ми можемо сказати: тим часом у сусідній кімнаті хтось голосно розмовляв. Або ж: у цей час надворі йшов дощ. Сполучник «поки» ідеально об'єднує дві фонові дії: поки я прибирав у квартирі, мій брат слухав музику. Завдяки цим маркерам читач одразу розуміє перспективу.

Sometimes, the background of your story is not just what was happening at that exact moment, but what used to happen all the time. This is the habitual background. To establish the "status quo" or the normal routine before an unexpected event changes everything, you use the imperfective aspect along with frequency markers. Words like **зазвичай** (usually), **увесь час** (all the time), and **раніше** (previously) signal that you are describing a deeply ingrained habit. This creates a baseline of normality that makes the eventual plot twist more impactful.

Раніше я завжди вставав о шостій годині ранку і йшов на пробіжку до парку. Зазвичай місто ще міцно спало, і вулиці були порожніми. Я увесь час слухав один і той самий подкаст під час бігу. Це була моя типова рутина, яка повторювалася щодня, поки одного разу не сталося дещо несподіване.

A common mistake for language learners is accidentally using a perfective verb when they intend to describe the background. This is the "accidental perfective" trap, and it fundamentally alters the meaning of your sentence. If you want to describe the weather as a continuous setting, you must say «дув вітер» (the wind was blowing). If you mistakenly use the perfective form «подув вітер», you transform the wind from a static atmospheric condition into a sudden, dynamic event. The perfective version forces the wind into the foreground. It implies that the wind suddenly started blowing right at that moment, changing the course of the story.

Різниця між двома видами є критичною для розуміння загальної ситуації в історії. Якщо ви скажете «надворі йшов дощ», ви просто описуєте погоду як декорацію для вашого оповідання. Але якщо ви скажете «надворі пішов дощ», дія миттєво стає подією. Це означає, що дощ раптово почався саме зараз, і герої повинні шукати укриття. Випадковий доконаний вид повністю ламає статичність фону.

> *The difference between the two aspects is critical for understanding the general situation in the story. If you say "it was raining outside," you are simply describing the weather as a decoration for your short story. But if you say "it started raining outside," the action instantly becomes an event. This means that the rain suddenly started right now, and the characters must look for shelter. An accidental perfective aspect completely breaks the static nature of the background.*

:::tip
**Aspect Check**
If you can logically add "suddenly" to your sentence without changing the core meaning, you have likely created a foreground event. Background descriptions rarely happen "suddenly."
:::

To truly master the imperfective background, you must practice building scenes without relying on events. Imagine you need to describe a quiet evening in a small Ukrainian town, like Berezhany or Kolomyia. Your goal is to write a paragraph using exclusively background verbs. Focus entirely on the atmosphere, the parallel activities of the townspeople, and the general mood. Describe how the old streetlamps were glowing, how the distant sound of a train was echoing, and how the locals were strolling through the main square. By temporarily banning perfective verbs from your writing, you force your brain to engage with the descriptive power of the imperfective aspect.

Уявіть собі старовинне українське містечко пізнього вечора, наче це ваш особистий спогад. Сонце повільно сідало за високі пагорби, і на вузьких вулицях ставало темніше. Місцеві жителі неквапливо гуляли площею, а з відчинених вікон лунала музика. Старі ліхтарі м'яко світили, освітлюючи кам'яну бруківку. Ніхто нікуди не поспішав, і час ніби зупинився. Спробуйте самостійно написати подібний текст, фокусуючись лише на процесах.

Ultimately, the imperfective aspect in a narrative is all about controlling the rhythm and the "vibe" of your story. When you rely on imperfective verbs, you deliberately slow down time. You invite your listener to pause, look around, and focus on the sensory details of the environment. You anchor the reader in the specific space and emotional reality of your characters before the plot disrupts their world. The background is the wide, expansive canvas upon which the actual story will eventually be painted.

Недоконаний вид працює як потужний кінематографічний інструмент, який ефективно уповільнює час і дозволяє нам уважно роздивитися деталі. Він зовсім не штовхає історію вперед, а розширює її вглиб. Завдяки йому ми можемо фізично відчути атмосферу, почути звуки навколишнього світу та зрозуміти емоції людей. Це фундамент, без якого будь-яка пригода здаватиметься штучною.

We have spent considerable time setting the stage, adjusting the lighting, and establishing the mood. But a stage set, no matter how beautifully described, is not a story on its own. A narrative requires action, consequence, and change. If the imperfective background is the wide canvas and the subtle shading, what is the brush that draws the sharp, defining lines of the plot? To turn a static scene into a compelling tale, we must introduce the foreground, and that requires a complete shift in our aspect strategy.

## Передній план: доконаний вид у наративі

The foreground (**передній план**) is the engine of your narrative. While the background sets the scene, the foreground consists of the actual events that move the plot forward. The primary tool for constructing this layer is the perfective aspect (доконаний вид). When you switch to the perfective aspect, you signal that the setting phase is over and the action has begun.

Найважливіша функція доконаного виду в розповіді — це створення послідовного ланцюжка подій. Кожне дієслово доконаного виду працює як годинник, який рухає час уперед. Коли ви використовуєте ці дієслова, кроки відбуваються послідовно — одна дія повністю завершується до початку наступної. Наприклад: «Він відчинив двері, зайшов до хати і ввімкнув світло». Тут ми маємо три окремі кроки сюжетотворення. Персонаж не міг увімкнути світло, поки не зайшов до хати. Ця послідовність створює динаміку і показує, що історія розвивається. Без доконаного виду ваша розповідь залишилася б статичною картиною.

> *The most important function of the perfective aspect in a narrative is creating a sequential chain of events. Each perfective verb acts like a clock that moves time forward. When you use these verbs, steps happen sequentially — one action completely finishes before the next one begins. For example: "He opened the door, walked into the house, and turned on the light." Here we have three separate steps of plot building. The character could not turn on the light until he had walked into the house. This sequence creates dynamics and shows that the story is developing. Without the perfective aspect, your narrative would remain a static picture.*

Another critical function of the perfective aspect is introducing a turning point. This is the exact moment when the established, peaceful background is suddenly interrupted by a new, unforeseen event. A story without turning points is just a long, monotonous description of a situation. The turning point is what forces your characters into action and drives the narrative forward.

Часто зміна фонового опису на подію супроводжується словом «раптом». Це слово є ідеальним маркером для доконаного виду, оскільки вказує на несподівану зміну ситуації. Подивіться на цей приклад: «Ми спокійно гуляли порожнім парком, і раптом пішов сильний дощ». Перша частина речення описує тривалий процес і спокійну атмосферу. Але друга частина миттєво руйнує цей спокій. Дієслово «пішов» перетворює дощ на раптову подію, яка змушує героїв швидко реагувати і змінювати свої плани.

The third major function of the foreground layer is delivering a decisive result. Perfective verbs are used to show actions that permanently alter the state of the story world. They act as the punctuation marks of your plot, confirming that a character's attempt has finally reached a conclusion. Without these conclusive actions, your story would feel unfinished.

Доконаний вид також фіксує результати дій, які мають критичне значення для фіналу історії. Це **точки неповернення** (points of no return) у вашому сюжеті. Наприклад: «Після довгих роздумів вона нарешті ухвалила рішення залишитися». У цьому реченні немає опису тривалого процесу мислення чи **сумнівів** (doubts). Є лише остаточний факт, який назавжди змінює життя персонажа. Використання недоконаного виду («вона ухвалювала рішення») означало б, що вона все ще вагається, і ми досі не знаємо кінцевого результату.

:::info
**Grammar box**
When you use a perfective verb to show a result, you are telling the listener: "This action is completely done, and its consequences are now a permanent part of our story's reality."
:::

To link these foreground events smoothly and logically, you need the right temporal connectors. Since the foreground layer is entirely about sequence and progression, you must use adverbs that clearly signal the passage of time from one completed step to the next. These words act as the glue that holds your plot together.

Граматика послідовності обов'язково вимагає спеціальних слів-зв'язок. Щоб з'єднати події переднього плану, ми використовуємо такі слова: «спочатку», «потім», «після цього» та «нарешті». Ці конектори природно поєднуються з дієсловами доконаного виду, тому що вибудовують чітку хронологію. «Спочатку я подзвонив у двері. Після цього я почекав хвилину. Потім спробував відкрити замок. І нарешті зрозумів, що вдома нікого немає». Цей ланцюжок неможливо побудувати за допомогою слів «тим часом» або «поки», які належать до фонового шару.

Let's see collaborative storytelling in action. Notice how one speaker sets the scene using the imperfective aspect, while the other eagerly interrupts to deliver the main events using the perfective aspect.

> — **Юлія:** Того вечора було дуже тихо. Ми сиділи в кав'ярні, пили каву і дивилися у вікно. *(That evening was very quiet. We were sitting in the cafe, drinking coffee and looking out the window.)*
> — **Катерина:** І раптом у двері зайшов Максим! Він одразу побачив нас і підійшов до столика. *(And suddenly Maksym walked through the door! He immediately saw us and came up to the table.)*
> — **Юлія:** Так, я пам'ятаю. Він виглядав дуже схвильованим, а його руки помітно тремтіли. *(Yes, I remember. He looked very excited, and his hands were noticeably shaking.)*
> — **Катерина:** Він кинув сумку на стілець і голосно сказав: «Я знайшов нову роботу!». *(He threw his bag on the chair and said loudly: "I found a new job!")*

<!-- INJECT_ACTIVITY: group-sort-connectors -->

Now that you understand how both layers function, the real art of storytelling is weaving them together. A narrative that shifts gracefully between background descriptions and foreground events keeps the reader engaged.

Справжня майстерність розповіді полягає у правильному чергуванні двох видів дієслів. Розглянемо такий абзац. «Була глибока ніч. Місто вже давно спало. Раптом хтось голосно постукав у двері. Я миттю прокинувся, встав з ліжка і підійшов до вікна». Перші два речення створюють атмосферу спокою за допомогою недоконаного виду («була», «спало»). Це наше тло. Наступні дії несподівано розбивають цю тишу. Дієслова доконаного виду («постукав», «прокинувся», «встав», «підійшов») створюють швидкий ланцюжок реакцій. Контраст між статичним фоном і динамічними подіями робить сцену напруженою.

> *True storytelling mastery lies in the correct alternation of the two verb aspects. Let's look at this paragraph. "It was deep night. The city had long been sleeping. Suddenly someone knocked loudly on the door. I instantly woke up, got out of bed, and went to the window." The first two sentences create an atmosphere of calm using the imperfective aspect ("була", "спало"). This is our background. The subsequent actions unexpectedly shatter this silence. The perfective verbs ("постукав", "прокинувся", "встав", "підійшов") create a rapid chain of reactions. The contrast between the static background and the dynamic events makes the scene tense.*

Your choice of aspect dictates the overall pacing and emotional rhythm of your story. Using too many perfective verbs in a row makes the narrative feel frantic, rushed, and remarkably similar to a list of facts. Adding imperfective "padding" slows things down and makes the world feel immersive, breathable, and natural.

Вибір виду безпосередньо впливає на темп вашої історії. Якщо ви використаєте виключно дієслова доконаного виду («я прийшов, сів, поїв, написав лист і ліг спати»), текст звучатиме як **сухий поліцейський звіт** (dry police report). Події відбуваються занадто швидко, і читач не встигає відчути атмосферу. Щоб історія стала живою, її потрібно «уповільнити» за допомогою недоконаного виду. Додайте опис кімнати, вашого настрою чи погоди за вікном. Цей фоновий матеріал дає читачеві **простір для уяви** (room for imagination) перед наступною подією.

:::tip
**Quick tip**
Think of imperfective verbs as breathing room for your story. They allow the listener to mentally process the scene before the perfective verbs drive the plot forward again.
:::

<!-- INJECT_ACTIVITY: fill-in-aspect-narrative -->
<!-- INJECT_ACTIVITY: match-aspect-logic -->

Let's listen to two writers discussing how to fix the pacing of a short story draft. They realize that adding more imperfective background can completely transform the emotional impact of the final events.

> — **Остап:** Цей фінал звучить занадто сухо. Головний герой просто зайшов у кімнату, побачив лист і заплакав. *(This ending sounds too dry. The main character just walked into the room, saw the letter, and cried.)*
> — **Марія:** Згодна, тут є лише голі події. Нам потрібно додати більше недоконаного виду, щоб створити емоційну напругу. *(I agree, there are only bare events here. We need to add more imperfective aspect to create emotional tension.)*
> — **Остап:** Може, опишемо порожню кімнату? Що там відбувалося до його приходу? *(Maybe we describe the empty room? What was happening there before his arrival?)*
> — **Марія:** Точно. Напиши, що у відкрите вікно дув вітер, а на столі самотньо горіла лампа. *(Exactly. Write that the wind was blowing into the open window, and a lamp was burning lonely on the table.)*
> — **Остап:** Супер. Тоді його доконані дії наприкінці здаватимуться набагато драматичнішими. *(Super. Then his perfective actions at the end will seem much more dramatic.)*

## Підсумок: аспект як наративний інструмент

Narrative flow is the rhythmic shifting between aspects. 

Уміння розповідати історії українською мовою — це не просто правильне використання словника чи граматики. Це здатність свідомо керувати ритмом розповіді за допомогою виду дієслова. Коли ви обираєте між доконаним і недоконаним видом, ви не просто вибираєте форму слова. Ви вирішуєте, який саме шар реальності ви зараз будуєте для свого слухача. Недоконаний вид створює простір, де можна дихати, оглядатися довкола і відчувати атмосферу. Доконаний вид штовхає цей світ уперед, змушуючи події відбуватися, змінюючи статус-кво. Рівень B1 означає, що ви більше не використовуєте види навмання. Ви робите цей вибір свідомо, розуміючи, що кожен перехід від тла до події змінює емоційний стан вашої історії. Цей ритмічний перехід — від спокійного спостереження до стрімкої дії — робить вашу мову по-справжньому природною.

> *The ability to tell stories in Ukrainian is not just about using the right vocabulary or grammar. It is the ability to consciously control the rhythm of the narrative using verb aspect. When you choose between the perfective and imperfective aspect, you are not just picking a word form. You are deciding exactly which layer of reality you are currently building for your listener. The imperfective aspect creates a space where you can breathe, look around, and feel the atmosphere. The perfective aspect pushes this world forward, making events happen and changing the status quo. The B1 level means you no longer use aspects randomly. You make this choice consciously, understanding that every transition from background to event changes the emotional state of your story. This rhythmic transition — from calm observation to rapid action — is what makes your speech truly natural.*

Let's see how this works in practice. Compare two versions of the same morning.

Версія перша: «Я прокинувся о сьомій годині. Я встав з ліжка, пішов на кухню і випив каву. Потім я одягнувся і вийшов на вулицю». Це класичний ланцюжок доконаних дієслів. Текст звучить як швидкий, сухий звіт про виконані завдання. Ми бачимо лише факти. Версія друга: «Я прокинувся о сьомій годині. У кімнаті було тепло, а за вікном ішов дрібний дощ. Я пішов на кухню. Поки я пив каву, я думав про свої плани на день. Потім я швидко одягнувся і вийшов на вулицю». Тут ми додали недоконаний вид («було», «ішов», «пив», «думав»). Різниця між «я випив каву» та «я пив каву» кардинально змінює фокус. Перше — це просто факт завершеної дії. Друге — це процес, під час якого герой міг думати, мріяти або спостерігати за дощем. Ця кінематографічна атмосфера виникає саме завдяки правильному чергуванню видів.

> *Version one: "I woke up at seven o'clock. I got out of bed, went to the kitchen, and drank coffee. Then I got dressed and went outside." This is a classic chain of perfective verbs. The text sounds like a fast, dry report of completed tasks. We only see facts. Version two: "I woke up at seven o'clock. It was warm in the room, and a light rain was falling outside. I went to the kitchen. While I was drinking coffee, I thought about my plans for the day. Then I quickly got dressed and went outside." Here we added the imperfective aspect ("was", "was falling", "was drinking", "thought"). The difference between "I drank coffee" (pf) and "I was drinking coffee" (impf) radically changes the focus. The first is simply a fact of a completed action. The second is a process during which the character could think, dream, or watch the rain. This cinematic atmosphere arises precisely thanks to the correct alternation of aspects.*

One of the most frequent mistakes learners make is "aspect pollution." This happens when you accidentally insert a perfective verb into a block of text that is purely meant for background description.

Уявіть, що ви створюєте спокійну сцену: «Сонце яскраво світило, пташки співали у саду, легкий вітерець грався листям». Усе це — недоконаний вид, ідеальне тло. І раптом ви додаєте: «Почався гарний день». Дієслово «почався» — доконаного виду. Воно миттєво руйнує статику і сигналізує про подію. Слухач очікує, що зараз щось станеться. Якщо ви просто хотіли описати стан, слід було використати недоконаний вид: «Починався гарний день». Послідовність у межах одного шару є надзвичайно важливою. Якщо ви малюєте тло, залишайтеся в недоконаному виді, поки не будете готові ввести реальну подію.

> *Imagine you are creating a calm scene: "The sun was shining brightly, the birds were singing in the garden, a light breeze was playing with the leaves." All of this is the imperfective aspect, an ideal background. And suddenly you add: "A beautiful day started" (pf). The verb "почався" (started) is perfective. It instantly destroys the static feel and signals an event. The listener expects that something is about to happen right now. If you just wanted to describe a state, you should have used the imperfective aspect: "A beautiful day was starting." Consistency within a single layer is extremely important. If you are painting a background, stay in the imperfective aspect until *

Another common issue arises when learners try to tell a story about a specific, one-time chain of events using only imperfective verbs. Because imperfective verbs in the past tense naturally convey repetition, your specific story suddenly sounds like a habit.

Якщо ви скажете: «Вчора вранці я вставав, одягався і виходив з дому», носій мови буде здивований. Такі дієслова звучать як регулярна дія або навіть як повторюваний сон. Це означає: «Я мав звичку вставати, одягатися...». Щоб передати конкретні кроки в унікальному сюжеті, ви зобов'язані використати доконаний вид: «Я встав, одягнувся і вийшов». Недоконаний вид не може рухати сюжет уперед; він може лише описувати те, що зазвичай відбувалося на тлі інших подій.

> *If you say: "Yesterday morning I was getting up, getting dressed, and leaving the house" (all impf), a native speaker will be surprised. Such verbs sound like a regular action or even like a recurring dream. It means: "I used to have a habit of getting up, getting dressed...". To convey specific steps in a unique plot, you are obliged to use the perfective aspect: "I got up, got dressed, and left." The imperfective aspect cannot move the plot forward; it can only describe what usually happened in the background of other events.*

:::tip
**Quick tip**
If you want to say "first I did A, then I did B," those actions are practically always perfective. Sequential steps in a story require completion to trigger the next step.
:::

English speakers, heavily influenced by the English Simple Past tense, often over-use the perfective aspect. English uses "I walked," "I saw," "I said" for both events and background contexts, making it tempting to translate everything as a perfective chain.

Якщо ви постійно використовуєте лише доконаний вид, ваша історія страждає від монотонності. Вона нагадує сухий перелік фактів: прийшов, побачив, сказав, пішов. Читач або слухач швидко втомлюється від такого ритму, бо йому бракує візуальних деталей і простору для емоцій. Щоб розірвати цей ланцюг, вам потрібно навмисно робити описові паузи. Додавайте речення недоконаного виду, які пояснюють, що відбувалося навколо, що ви відчували або про що думали в той момент. Ці паузи дають вашій аудиторії можливість по-справжньому зануритися в атмосферу вашої розповіді.

> *If you constantly use only the perfective aspect, your story suffers from monotony. It resembles a dry list of facts: came, saw, said, left. The reader or listener quickly tires of such a rhythm because it lacks visual details and space for emotions. To break this chain, you need to intentionally make descriptive pauses. Add imperfective sentences that explain what was happening around you, what you were feeling, or what you were thinking at that moment. These pauses give your audience the opportunity to truly immerse themselves in the atmosphere of your narrative.*

:::note
**Did you know?**
Ukrainian writers masterfully use imperfective verbs right before the climax of a story to build suspense. By stretching out the description of the setting, they delay the inevitable perfective action, keeping the reader on the edge of their seat.
:::

<!-- INJECT_ACTIVITY: error-correction-narrative -->
<!-- INJECT_ACTIVITY: open-writing-narrative -->

Let's summarize the key principles of using aspect as a narrative tool. A compelling story requires both layers.

Для створення фону ми використовуємо недоконаний вид. Це процес, стан, опис природи, емоцій або паралельні дії. Тло не рухає час уперед, воно ніби розширює конкретний момент. Часові конектори, такі як «тим часом», «поки» та «у цей час», природно поєднуються з тривалими діями. Для розвитку сюжету ми використовуємо доконаний вид. Це послідовність дій, конкретні результати або раптові несподівані події, які змінюють ситуацію. Кожне таке дієслово — це новий крок в історії. Конектори «спочатку», «потім», «раптом» та «нарешті» вимагають завершеності дії, щоб перейти до наступної.

> *To create a background, we use the imperfective aspect. This is a process, a state, a description of nature, emotions, or parallel actions. The background does not move time forward; it seems to expand a specific moment. Time connectors like "meanwhile," "while," and "at that time" naturally combine with continuous actions. For plot development, we use the perfective aspect. This is a sequence of actions, specific results, or sudden unexpected events that change the situation. Each such verb is a new step in the story. The connectors "at first," "then," "suddenly," and "finally" require the completion of an action to move on to the next one.*

Before sharing your story, ask yourself a few control questions.

*   Чи описав я атмосферу за допомогою недоконаного виду, щоб слухач міг уявити сцену?
*   Чи є в моїй історії чіткий ланцюжок доконаних дієслів, що рухають сюжет уперед?
*   Чи правильно я використав часові конектори, наприклад, розрізняючи «потім» для послідовних подій та «тим часом» для паралельних процесів?

> * *Did I describe the atmosphere using the imperfective aspect so the listener could imagine the scene?*
> * *Is there a clear chain of perfective verbs in my story that moves the plot forward?*
> * *Did I use time connectors correctly, for example, distinguishing "then" for sequential events and "meanwhile" for parallel processes?*

 But aspect isn't only about telling stories; it is also about controlling interactions in the present moment. Now that you can tell a story, how do you change someone else's behavior? In our next module, we will explore Aspect in Imperatives. You will learn the profound difference between the urgent prohibition **Не відкривай!** (Don't open it!) and the direct command **Відкрий!** (Open it!), and discover how your choice of aspect dictates the nuance, politeness, and urgency of your commands.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-in-narration
level: b1

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: B1 (Module 6)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
