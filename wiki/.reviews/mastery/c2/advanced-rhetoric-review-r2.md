✅ Message sent to Gemini (ID: 28255) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28255...
📨 Message #28255
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-c2-advanced-rhetoric-r2
   Time: 2026-04-05T23:43:32.048748+00:00

============================================================

You are a HARSH adversarial reviewer of a academic brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: c2, Slug: advanced-rhetoric, Round: 2

## Review Rubric (score EACH dimension 1-10, then average)

1. **Factual accuracy** — every claim must have evidence from sources. Vague or unsourced claims → deduct points.
2. **Ukrainian language quality** — check for Russianisms (кон→кін), surzhyk (шо→що), calques (приймати душ→брати душ). Even ONE Russianism = max 7/10.
3. **Decolonization** — is Ukrainian presented on its own terms? Any 'like Russian but...' framing = max 6/10.
4. **Completeness** — does it cover ALL aspects a module writer needs? Missing sections or shallow treatment → deduct.
5. **Actionable guidance** — can a writer actually USE this? Generic advice like 'teach it well' = max 5/10. Must have specific examples, sequences, exercises.

## Rules
- Score each dimension separately, then give weighted average.
- Be honest. If the article is excellent, say so. 10/10 IS possible.
- 9/10 = excellent with minor issues. 8/10 = good. 7/10 = needs work.
- Output a <fixes> block with specific changes. If the article is clean, output <fixes></fixes> (empty).
- Do NOT invent problems. Fabricated issues waste rebuild cycles.

## Fix syntax

Two formats are available:

**1. Replace existing text** (for corrections, rewording):
Use a SHORT anchor (1-2 sentences max) for the old: text. Do NOT paste massive paragraphs — they break exact matching.
```
old: short exact text to find
new: replacement text
```

**2. Insert new content** (for missing sections, added examples):
Use INSERT AFTER with a short anchor from the article, then the new text to add.
```
INSERT AFTER: short anchor text that exists in the article
NEW TEXT: the new content to insert after the anchor
```

Separate multiple fixes with `---`.

## Output format

Dimension scores:
1. Factual: X/10 — [evidence]
2. Language: X/10 — [evidence]
3. Decolonization: X/10 — [evidence]
4. Completeness: X/10 — [evidence]
5. Actionable: X/10 — [evidence]

**Overall: X/10**

<fixes>
old: exact text to find in the article
new: replacement text
---
INSERT AFTER: anchor text in article
NEW TEXT: content to add after the anchor
</fixes>

## Article to review

# Майстерність C2: Поглиблена риторика

<!-- wiki-meta
slug: advanced-rhetoric
domain: mastery/c2
tracks: [c2]
sources: [10-klas-ukrmova-glazova-2018_s0116, 11-klas-ukrajinska-mova-voron-2019_s0243, 11-klas-ukrajinska-mova-voron-2019_s0219, 11-klas-ukrajinska-mova-avramenko-2019_s0014, 11-klas-ukrajinska-mova-glazova-2019_s0331, 11-klas-ukrajinska-mova-voron-2019_s0108, 10-klas-ukrajinska-mova-zabolotnij-2018_s0075, 10-klas-ukrmova-zabolotnyi-2018_s0075, 11-klas-ukrajinska-mova-voron-2019_s0093, 10-klas-ukrajinska-mova-avramenko-2018_s0090, 11-klas-ukrajinska-mova-avramenko-2019_s0013, 11-klas-ukrajinska-mova-glazova-2019_s0090, 11-klas-ukrajinska-mova-glazova-2019_s0159, 11-klas-ukrajinska-mova-voron-2019_s0048, 11-klas-ukrajinska-mova-voron-2019_s0103, 11-klas-ukrajinska-mova-voron-2019_s0148, 9-klas-ukrajinska-mova-voron-2017_s0110, 10-klas-ukrajinska-mova-avramenko-2018_s0089, 10-klas-ukrajinska-mova-avramenko-2018_s0111, 10-klas-ukrajinska-mova-zabolotnij-2018_s0060, 10-klas-ukrajinska-mova-zabolotnij-2018_s0064, 10-klas-ukrajinska-mova-zabolotnij-2018_s0072, 10-klas-ukrajinska-mova-zabolotnij-2018_s0080, 10-klas-ukrajinska-mova-zabolotnij-2018_s0086, 10-klas-ukrajinska-mova-zabolotnij-2018_s0102, 10-klas-ukrajinska-mova-zabolotnij-2018_s0253, 10-klas-ukrajinska-mova-zabolotnij-2018_s0263, 11-klas-ukrajinska-mova-avramenko-2019_s0294, 11-klas-ukrajinska-mova-glazova-2019_s0093, 11-klas-ukrajinska-mova-glazova-2019_s0111, 11-klas-ukrajinska-mova-glazova-2019_s0247, 11-klas-ukrajinska-mova-glazova-2019_s0250, 11-klas-ukrajinska-mova-glazova-2019_s0283, 11-klas-ukrajinska-mova-glazova-2019_s0308, 11-klas-ukrajinska-mova-glazova-2019_s0331]
compiled: 2026-04-06
-->

## Академічний контекст (Academic Context)

Риторика, або мистецтво красномовства, є однією з найдавніших гуманітарних дисциплін, що сягає корінням античної Греції та Риму. В українській інтелектуальній традиції вона посідає особливе місце, будучи невіддільною частиною філософії, права та богослов'я. Її розвиток в Україні можна простежити від часів Київської Русі, де найяскравішим зразком ораторського мистецтва є «Слово про закон і благодать» митрополита Іларіона (XI ст.). Цей твір, виголошений у присутності княжого двору, демонструє не лише глибокий патріотизм та історичну свідомість, але й досконале володіння складними фігурами візантійської риторики (voron, 2019, `s0103`).

Новий пошт

## Instructions
1. Read the critique carefully.
2. Identify which SPECIFIC sections need rewriting to address the critique.
3. Output the COMPLETE article with those sections rewritten.
4. Do NOT remove or degrade sections that scored well.
5. Do NOT add commentary — output ONLY the article markdown.

## Current article

# Майстерність C2: Поглиблена риторика

<!-- wiki-meta
slug: advanced-rhetoric
domain: mastery/c2
tracks: [c2]
sources: [10-klas-ukrmova-glazova-2018_s0116, 11-klas-ukrajinska-mova-voron-2019_s0243, 11-klas-ukrajinska-mova-voron-2019_s0219, 11-klas-ukrajinska-mova-avramenko-2019_s0014, 11-klas-ukrajinska-mova-glazova-2019_s0331, 11-klas-ukrajinska-mova-voron-2019_s0108, 10-klas-ukrajinska-mova-zabolotnij-2018_s0075, 10-klas-ukrmova-zabolotnyi-2018_s0075, 11-klas-ukrajinska-mova-voron-2019_s0093, 10-klas-ukrajinska-mova-avramenko-2018_s0090, 11-klas-ukrajinska-mova-avramenko-2019_s0013, 11-klas-ukrajinska-mova-glazova-2019_s0090, 11-klas-ukrajinska-mova-glazova-2019_s0159, 11-klas-ukrajinska-mova-voron-2019_s0048, 11-klas-ukrajinska-mova-voron-2019_s0103, 11-klas-ukrajinska-mova-voron-2019_s0148, 9-klas-ukrajinska-mova-voron-2017_s0110, 10-klas-ukrajinska-mova-avramenko-2018_s0089, 10-klas-ukrajinska-mova-avramenko-2018_s0111, 10-klas-ukrajinska-mova-zabolotnij-2018_s0060, 10-klas-ukrajinska-mova-zabolotnij-2018_s0064, 10-klas-ukrajinska-mova-zabolotnij-2018_s0072, 10-klas-ukrajinska-mova-zabolotnij-2018_s0080, 10-klas-ukrajinska-mova-zabolotnij-2018_s0086, 10-klas-ukrajinska-mova-zabolotnij-2018_s0102, 10-klas-ukrajinska-mova-zabolotnij-2018_s0253, 10-klas-ukrajinska-mova-zabolotnij-2018_s0263, 11-klas-ukrajinska-mova-avramenko-2019_s0294, 11-klas-ukrajinska-mova-glazova-2019_s0093, 11-klas-ukrajinska-mova-glazova-2019_s0111, 11-klas-ukrajinska-mova-glazova-2019_s0247, 11-klas-ukrajinska-mova-glazova-2019_s0250, 11-klas-ukrajinska-mova-glazova-2019_s0283, 11-klas-ukrajinska-mova-glazova-2019_s0308, 11-klas-ukrajinska-mova-glazova-2019_s0331]
compiled: 2026-04-06
-->

## Академічний контекст (Academic Context)

Риторика, або мистецтво красномовства, є однією з найдавніших гуманітарних дисциплін, що сягає корінням античної Греції та Риму. В українській інтелектуальній традиції вона посідає особливе місце, будучи невіддільною частиною філософії, права та богослов'я. Її розвиток в Україні можна простежити від часів Київської Русі, де найяскравішим зразком ораторського мистецтва є «Слово про закон і благодать» митрополита Іларіона (XI ст.). Цей твір, виголошений у присутності княжого двору, демонструє не лише глибокий патріотизм та історичну свідомість, але й досконале володіння складними фігурами візантійської риторики (voron, 2019, `s0103`).

Новий поштовх розвитку риторики дала Києво-Могилянська академія у XVII-XVIII ст. Риторичний курс Феофана Прокоповича, що складався з десяти книг, був фундаментальною працею, яка систематизувала класичні риторичні школи для українського студентства. Прокопович розглядав риторику як «царицю мистецтв», що виконує соціально-організаційну, культурно-освітню та когнітивну функції (voron, 2019, `s0108`). Він виступав проти надмірностей барокового стилю та схоластики, наголошуючи на раціоналізмі, ясності думки та відповідності стилю «вимогам справи і часу».

На рівні С2 володіння українською мовою вимагає не просто знання риторичних прийомів, а глибокого розуміння риторики як системи мислення та комунікативної стратегії. Це перехід від *що* сказати до *як* сказати, *чому* саме так, і з яким *ефектом*. У сучасному українському академічному та професійному середовищі риторика є ключовою компетенцією для юристів, політиків, науковців, журналістів та менеджерів — усіх, чиїм професійним інструментом є слово (glazova, 2018, `s0025`). Мета на рівні С2 — досягти такого рівня майстерності, коли риторичні інструменти застосовуються не механічно, а інтуїтивно, стаючи природним продовженням думки мовця.

## Основний зміст (Main Content)

На рівні С2 вивчення риторики переходить від описового до аналітико-синтетичного етапу. Мовець повинен не лише ідентифікувати та використовувати риторичні фігури, але й конструювати цілісні комунікативні стратегії, виходячи з мети, аудиторії та контексту.

### І. Класичний канон як операційна система мовця

Класична риторика, узагальнена Цицероном та іншими, пропонує п'ять етапів ораторської діяльності, які на рівні С2 слід розглядати як гнучку, ітеративну модель, а не лінійну інструкцію.

1.  **Інвенція (Inventio):** Пошук і добір матеріалу. На цьому етапі майстерність полягає не стільки у знаходженні фактів, скільки у формуванні *топосів* (topos) — загальних місць, аргументативних моделей. Це здатність побачити в конкретній ситуації універсальну проблему (справедливість, вибір, обов'язок) і побудувати на цьому переконливу аргументацію. Інвенція на рівні С2 — це не просто збір даних, а розробка концептуальної рамки виступу (voron, 2019, `s0048`; zabolotnij, 2018, `s0086`).

2.  **Диспозиція (Dispositio):** Розташування матеріалу. Класична структура (вступ, виклад, розробка, висновки) залишається актуальною. Однак майстерність С2 полягає у варіативності. Це вміння почати не з тези, а з провокативного питання чи несподіваної історії, щоб захопити увагу; вміння розташувати найсильніший аргумент наприкінці (клімакс) або на початку (антиклімакс) залежно від психологічного стану аудиторії; вміння свідомо порушити логічну послідовність задля емоційного ефекту.

3.  **Елокуція (Elocutio):** Словесне оформлення думки. Це серце риторичної майстерності. На рівні С2 мова йде про свідомий вибір стилістичного регістру та віртуозне володіння виражальними засобами. «Промова без тропів і риторичних фігур пісна, нею важко зацікавити аудиторію» (avramenko, 2019, `s0013`). Завдання — не просто «прикрасити» мову, а використати фігури та тропи як інструменти точного впливу на емоційну та інтелектуальну сфери слухача.

4.  **Меморія (Memoria):** Запам'ятовування промови. На рівні С2 це не зубріння тексту. Це глибоке внутрішнє засвоєння структури, ключових думок та переходів. Це дозволяє мовцю говорити вільно, «відривати очі від тексту», встановлюючи зоровий контакт із залом, і водночас не втрачати логічної нитки (voron, 2017, `s0110`). Імпровізація стає можливою саме на базі міцної, але гнучкої внутрішньої структури.

5.  **Акція (Actio):** Виголошення промови. Це синтез усіх попередніх етапів. Майстерність полягає в керуванні невербальними засобами: інтонацією, темпом, паузами, жестами, мімікою, поглядом. Уміння зробити паузу перед важливою інформацією, знизити голос для створення напруги (прийом «тихий голос»), використати крок уперед для підсилення тези — усе це відрізняє досвідченого оратора (avramenko, 2018, `s0090`; zabolotnij, 2018, `s0080`).

### ІІ. Тріада Арістотеля як інструмент аналізу та впливу

Арістотелівська тріада — **Логос, Етос, Пафос** — є фундаментальною для розуміння механізмів переконання. На рівні С2 вона перетворюється на практичний інструмент для конструювання та аналізу будь-якого публічного висловлювання.

*   **Логос (Λόγος):** Звернення до розуму, логіки. Це не лише правильність фактів та бездоганність силогізмів. Це також ясність структури, прозорість аргументації, використання точних визначень. «Правильно визначайте слова, і ви звільните світ від половини непорозумінь» (Декарт, цит. за zabolotnij, 2018, `s0075`). На С2 це вміння виявляти логічні помилки та софізми в аргументації опонентів (zabolotnij, 2018, `s0253`).

*   **Етос (ἦθος):** Звернення до авторитету, характеру, моральних якостей мовця. Ефективність промови визначається не лише тим, *що* сказано, але й *хто* це говорить. Етос формується ще до початку промови і залежить від репутації, чесноти, доброзичливості та компетентності мовця. Феофан Прокопович визначав чесноти ритора як мудрість, справедливість, хоробрість, поміркованість (voron, 2019, `s0043`). Створення та підтримка позитивного етосу (іміджу) є критично важливим (zabolotnij, 2018, `s0072`). Це довіра, яку мовець повинен заслужити.

*   **Пафос (Πάθος):** Звернення до емоцій, почуттів аудиторії. Це здатність викликати у слухачів радість, гнів, співчуття, надію, страх. Пафос досягається не лише через емоційно забарвлену лексику, а й через використання образів, історій, метафор та інших художніх засобів. Феофан Прокопович присвятив почуттям цілий розділ свого курсу, вважаючи, що оратор має бути «сильним і багатослівним у зворушенні» (voron, 2019, `s0108`).

### ІІІ. Арсенал Елокуції: Стратегічне застосування виражальних засобів

На рівні С2 розгляд тропів і фігур виходить за межі простої класифікації. Кожен засіб аналізується з погляду його комунікативної функції.

*   **Риторичне запитання та риторичне звертання:** Це не просто питання без відповіді чи звертання до відсутніх. Це потужні інструменти для активізації уваги, структурування думки та надання мовленню емоційності. Риторичне запитання («Чи знаєте ви, як її провалити?») створює інтригу і запрошує слухача до співтворчості, тоді як пряма констатація є менш ефективною (avramenko, 2019, `s0013`). Риторичне звертання («Боговибрана, благословенна Полтаво!») створює урочистий, піднесений настрій (glazova, 2019, `s0247`).

*   **Антитеза:** Протиставлення (напр., `жорстоке — ніжне`, `минуле — майбутнє`) слугує для створення гострого, яскравого образу через несподіване зіткнення понять. Мета антитези — не просто показати різницю, а підкреслити взаємозв'язок протилежностей, поглибити розуміння явища (glazova, 2019, `s0159`). Назви творів, як «Війна і мир», є класичним прикладом цього прийому.

*   **Градація:** Поступове підсилення або послаблення емоційного напруження чи значущості. Це дозволяє керувати емоційним станом аудиторії, вести її від простого до складного, від спокійного до збудженого стану.

*   **Тропи (Метафора, метонімія, гіпербола):** На рівні С2 метафора розглядається не як прикраса, а як інструмент мислення, спосіб зрозуміти одне явище через інше. Використання тропів («провалити співбесіду», «виграти у двобої») активізує увагу слухачів значно сильніше, ніж безособові конструкції (avramenko, 2019, `s0014`). Демосфен активно використовував метафору та гіперболу, що робило його промови надзвичайно жвавими та переконливими (voron, 2019, `s0093`).

## Тонкощі та нюанси (Subtleties)

Володіння риторикою на рівні майстерності передбачає розуміння тонких аспектів, які часто залишаються поза увагою на нижчих рівнях.

*   **Керування аудиторією (Audience Management):** Це не лише встановлення зорового контакту, а й здатність «читати» аудиторію в реальному часі. Треба відчути, коли слухачі стомлені, коли втрачають інтерес, і негайно реагувати: зробити відступ, розповісти доречний жарт, змінити темп мовлення або поставити несподіване запитання (avramenko, 2018, `s0090`). Помітивши неуважних слухачів, досвідчений оратор може на деякий час зосередити на них погляд, що зазвичай допомагає відновити контакт (zabolotnij, 2018, `s0080`).

*   **Комунікативна стратегія і тактика:** Будь-яка ефективна комунікація передбачає вибір мовцем певної моделі поведінки (стратегії) для досягнення мети. Реалізація цієї стратегії відбувається через комунікативні тактики — сукупність конкретних кроків (мовленнєвих вчинків) у процесі взаємодії (avramenko, 2018, `s0111`). Наприклад, у ситуації конфлікту стратегією може бути «пошук компромісу», а тактиками — «визнання часткової правоти опонента», «переведення розмови в конструктивне русло», «апеляція до спільних цінностей».

*   **Етичний вимір: Риторика vs Демагогія:** На рівні С2 критично важливо розрізняти переконання та маніпуляцію. Демагогія використовує ті самі інструменти, що й риторика (пафос, пишномовність), але з корисливою метою, обманюючи аудиторію брехливими обіцянками та спекулюючи на її потребах (glazova, 2019, `s0308`). Майстер-ритор не лише уникає демагогії сам, але й уміє розпізнавати та протидіяти їй, аналізуючи логічні помилки та приховані мотиви опонента (zabolotnij, 2018, `s0253`). Осуджувати слід не особу, а її вчинки, і робити це з великою обережністю та на основі перевірених фактів (glazova, 2019, `s0250`).

## Наукові дискусії (Scholarly Debates)

Внутрішня дискусія в риториці стосується балансу між її компонентами та методами.

*   **Структура vs. Імпровізація:** Наскільки детально слід готувати текст виступу? Одні оратори почуваються впевнено, лише маючи перед собою повний текст, інші блискуче виступають, спираючись на короткий план чи тези (voron, 2017, `s0110`). Ця дилема не має єдиного розв'язання і залежить від індивідуальних особливостей мовця, типу виступу та аудиторії. На рівні С2 завдання полягає в тому, щоб знайти власний оптимальний баланс, який дозволя

============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18311 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a academic brief for the Ukrainian language curriculum ...
Dimension scores:
1. Factual: 9/10 — The historical context (Hilarion, Kyiv-Mohyla) and classical framework (Cicero, Aristotle) are accurate, well-integrated, and properly sourced. No obvious factual errors.
2. Language: 7/10 — Contains classic calques and Russianisms: "мова йде про" (instead of "йдеться про"), "дала поштовх" (instead of "надала поштовху"), and stylistically heavy gerunds ("будучи"). The text also abruptly cuts off mid-word at the very end ("дозволя").
3. Decolonization: 10/10 — Excellent framing. Bypasses Russian rhetorical traditions entirely, rooting the discipline deeply in Ukrainian intellectual history (Kyiv-Mohyla, Prokopovych, Hilarion). 
4. Completeness: 5/10 — The document is literally incomplete, cutting off mid-sentence at the end. It lacks a concluding synthesis.
5. Actionable: 4/10 — Highly theoretical. It effectively describes what C2 rhetoric *is*, but provides almost zero actionable guidance, activity types, or structural recommendations for a curriculum writer to actually build a module.

**Overall: 7/10**

<fixes>
old: будучи невіддільною частиною філософії, права та богослов'я.
new: як невіддільна частина філософії, права та богослов'я.
---
old: Новий поштовх розвитку риторики дала Києво-Могилянська академія
new: Нового поштовху розвитку риторики надала Києво-Могилянська академія
---
old: На рівні С2 мова йде про свідомий вибір стилістичного регістру
new: На рівні С2 йдеться про свідомий вибір стилістичного регістру
---
old: який дозволя
new: який дозволяє вільно й переконливо взаємодіяти з аудиторією.

## Практичні рекомендації для розробників модулів (Actionable Guidelines)

Для ефективного навчання риторики на рівні C2 модулі повинні містити такі типи активностей:
1. **Деконструкція текстів (Reverse Engineering):** Аналіз історичних та сучасних українських промов (наприклад, виступів дисидентів, сучасних публічних інтелектуалів) з метою виявлення топосів, фігур та тропів.
2. **Риторичні трансформації:** Вправи на переписування нейтрального або академічного тексту з використанням різних риторичних стратегій і тактик (наприклад, адаптація наукової статті для широкої аудиторії з використанням пафосу та етосу).
3. **Керовані дебати та софістика:** Практика виявлення логічних хиб і маніпуляцій у текстах опонентів, а також конструювання власної аргументації з використанням градації та антитези.
4. **Імпровізація за структурою:** Завдання на виголошення промови без підготовки тексту (розвиток Меморії та Акції), спираючись лише на внутрішню структуру інвенції та диспозиції.
</fixes>


────────────────────────────────────────
✅ Gemini finished (2559 chars)
✅ Message sent to Claude (ID: 28256)
✓ Message 28256 acknowledged
   Auto-acknowledged reply #28256 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-c2-advanced-rhetoric-r2' — skipping GH posting (review saved to orchestration/)
✓ Message 28255 acknowledged
