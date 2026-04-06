✅ Message sent to Gemini (ID: 28324) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28324...
📨 Message #28324
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-c1-academic-style-markers-final
   Time: 2026-04-06T09:04:13.657596+00:00

============================================================

You are a HARSH adversarial reviewer of a academic brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: c1, Slug: academic-style-markers, Round: final

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

# Академічна C1: Маркери академічного стилю

<!-- wiki-meta
slug: academic-style-markers
domain: academic/c1
tracks: [c1, c2]
sources: [6-klas-ukrmova-avramenko-2023_s0243, 8-klas-ukrmova-avramenko-2025_s0132, 11-klas-ukrmova-zabolotnyi-2019_s0289, 11-klas-ukrmova-zabolotnyi-2019_s0277, 10-klas-ukrmova-karaman-2018_s0408, 7-klas-ukrmova-avramenko-2024_s0128, 7-klas-ukrmova-avramenko-2024_s0237, 11-klas-ukrajinska-mova-avramenko-2019_s0295, 11-klas-ukrmova-zabolotnyi-2019_s0365, 5-klas-ukrmova-avramenko-2022_s0074, 7-klas-ukrmova-avramenko-2024_s0234, 7-klas-ukrmova-zabolotnyi-2024_s0119, 9-klas-ukrajinska-mova-avramenko-2017_s0101, 9-klas-ukrajinska-mova-voron-2017_s0049, 9-klas-ukrajinska-mova-voron-2017_s0307, 9-klas-ukrajinska-mova-zabolotnij-2017_s0338, 9-klas-ukrmova-zabolotnyi-2017_s0338, 10-klas-ukrajinska-mova-zabolotnij-2018_s0215, 10-klas-ukrmova-karaman-2018_s0121, 10-klas-ukrmova-karaman-2018_s0314, 11-klas-ukrajinska-mova-avramenko-2019_s0062, 11-klas-ukrajinska-mova-avramenko-2019_s0109, 11-klas-ukrajinska-mova-avramenko-2019_s0110, 11-klas-ukrajinska-mova-avramenko-2019_s0258, 11-klas-ukrajinska-mova-glazova-2019_s0049, 11-klas-ukrajinska-mova-glazova-2019_s0136, 11-klas-ukrajinska-mova-glazova-2019_s0137, 11-klas-ukrajinska-mova-glazova-2019_s0139, 11-klas-ukrajinska-mova-glazova-2019_s0141, 11-klas-ukrajinska-mova-glazova-2019_s0325, 1-klas-bukvar-zaharijchuk-2025-1_s0049, 4-klas-ukrmova-zaharijchuk_s0044, 4-klas-ukrmova-zaharijchuk_s0045, 4-klas-ukrmova-zaharijchuk_s0092, 4-klas-ukrmova-zaharijchuk_s0145, 4-klas-ukrmova-zaharijchuk_s0148, 4-klas-ukrmova-zaharijchuk_s0187, 4-klas-ukrmova-zaharijchuk_s0191, 5-klas-ukrlit-zabolotnyi-2022_s0044, 5-klas-ukrmova-avramenko-2022_s0022, 5-klas-ukrmova-avramenko-2022_s0025, 5-klas-ukrmova-avramenko-2022_s0026, 5-klas-ukrmova-avramenko-2022_s0034]
compiled: 2026-04-06
-->

## Академічний контекст (Academic Context)

Науковий стиль мовлення є функціональним стилем, що обслуговує сфери освіти, науки і техніки (Джерело: 6-klas-ukrmova-avramenko-2023_s0243). Його вивчення є наріжним каменем у курсі української мови, починаючи від середньої школи і закінчуючи університетським рівнем. Основна функція наукового стилю — інформативна, тобто повідомлення, пояснення, обґрунтування, класифікація понять та систематизація знань (Джерело: 10-klas-ukrmova-karaman-2018_s0408).

Він є стандартом для н

## Instructions
1. Read the critique carefully.
2. Identify which SPECIFIC sections need rewriting to address the critique.
3. Output the COMPLETE article with those sections rewritten.
4. Do NOT remove or degrade sections that scored well.
5. Do NOT add commentary — output ONLY the article markdown.

## Current article

# Академічна C1: Маркери академічного стилю

<!-- wiki-meta
slug: academic-style-markers
domain: academic/c1
tracks: [c1, c2]
sources: [6-klas-ukrmova-avramenko-2023_s0243, 8-klas-ukrmova-avramenko-2025_s0132, 11-klas-ukrmova-zabolotnyi-2019_s0289, 11-klas-ukrmova-zabolotnyi-2019_s0277, 10-klas-ukrmova-karaman-2018_s0408, 7-klas-ukrmova-avramenko-2024_s0128, 7-klas-ukrmova-avramenko-2024_s0237, 11-klas-ukrajinska-mova-avramenko-2019_s0295, 11-klas-ukrmova-zabolotnyi-2019_s0365, 5-klas-ukrmova-avramenko-2022_s0074, 7-klas-ukrmova-avramenko-2024_s0234, 7-klas-ukrmova-zabolotnyi-2024_s0119, 9-klas-ukrajinska-mova-avramenko-2017_s0101, 9-klas-ukrajinska-mova-voron-2017_s0049, 9-klas-ukrajinska-mova-voron-2017_s0307, 9-klas-ukrajinska-mova-zabolotnij-2017_s0338, 9-klas-ukrmova-zabolotnyi-2017_s0338, 10-klas-ukrajinska-mova-zabolotnij-2018_s0215, 10-klas-ukrmova-karaman-2018_s0121, 10-klas-ukrmova-karaman-2018_s0314, 11-klas-ukrajinska-mova-avramenko-2019_s0062, 11-klas-ukrajinska-mova-avramenko-2019_s0109, 11-klas-ukrajinska-mova-avramenko-2019_s0110, 11-klas-ukrajinska-mova-avramenko-2019_s0258, 11-klas-ukrajinska-mova-glazova-2019_s0049, 11-klas-ukrajinska-mova-glazova-2019_s0136, 11-klas-ukrajinska-mova-glazova-2019_s0137, 11-klas-ukrajinska-mova-glazova-2019_s0139, 11-klas-ukrajinska-mova-glazova-2019_s0141, 11-klas-ukrajinska-mova-glazova-2019_s0325, 1-klas-bukvar-zaharijchuk-2025-1_s0049, 4-klas-ukrmova-zaharijchuk_s0044, 4-klas-ukrmova-zaharijchuk_s0045, 4-klas-ukrmova-zaharijchuk_s0092, 4-klas-ukrmova-zaharijchuk_s0145, 4-klas-ukrmova-zaharijchuk_s0148, 4-klas-ukrmova-zaharijchuk_s0187, 4-klas-ukrmova-zaharijchuk_s0191, 5-klas-ukrlit-zabolotnyi-2022_s0044, 5-klas-ukrmova-avramenko-2022_s0022, 5-klas-ukrmova-avramenko-2022_s0025, 5-klas-ukrmova-avramenko-2022_s0026, 5-klas-ukrmova-avramenko-2022_s0034]
compiled: 2026-04-06
-->

## Академічний контекст (Academic Context)

Науковий стиль мовлення є функціональним стилем, що обслуговує сфери освіти, науки і техніки (Джерело: 6-klas-ukrmova-avramenko-2023_s0243). Його вивчення є наріжним каменем у курсі української мови, починаючи від середньої школи і закінчуючи університетським рівнем. Основна функція наукового стилю — інформативна, тобто повідомлення, пояснення, обґрунтування, класифікація понять та систематизація знань (Джерело: 10-klas-ukrmova-karaman-2018_s0408).

Він є стандартом для написання кваліфікаційних робіт (дисертацій, монографій), наукових статей, доповідей, тез, рецензій, а також підручників та навчальних посібників (Джерело: 10-klas-ukrmova-karaman-2018_s0408). Відтак, володіння маркерами академічного стилю на рівні C1–C2 означає здатність продукувати фахові тексти, що відповідають вимогам українського наукового дискурсу.

## Основний зміст (Main Content)

Академічний стиль в українській мові характеризується набором чітких лексичних, морфологічних та синтаксичних маркерів, спрямованих на досягнення максимальної точності, логічності та об'єктивності викладу (Джерело: 9-klas-ukrajinska-mova-voron-2017_s0049).

### Загальні риси: Точність, логічність, безобразність

Науковий текст вимагає строгої відповідності фактам та логічної послідовності викладу. Це досягається через:
*   **Точність та аргументованість**: Кожне твердження має бути підкріплене доказом або посиланням на джерело. Структура тексту часто підпорядкована схемі: **теза → аргументи → висновок** (Джерело: 6-klas-ukrmova-avramenko-2023_s0243).
*   **Об'єктивність**: Авторська позиція має бути нейтральною, що виключає використання емоційно-забарвленої лексики та експресивних синтаксичних конструкцій (Джерело: 9-klas-ukrajinska-mova-avramenko-2017_s0101).
*   **Використання термінології**: Вживання наукових термінів є обов'язковим для точності викладу (Джерело: 9-klas-ukrajinska-mova-voron-2017_s0049).
*   **Книжна фразеологія**: Вживаються фразеологізми книжного характеру, що позбавлені образності та емоційного забарвлення. Вони надають тексту чіткості й лаконічності (Джерело: 11-klas-ukrmova-zabolotnyi-2019_s0277).
    *   *Приклади:* `сформулювати правило`, `брати участь`, `набирати чинності` (Джерело: 11-klas-ukrmova-zabolotnyi-2019_s0277).

### Синтаксис академічного тексту: Перевага активним та безособовим конструкціям

Синтаксис є найважливішим маркером академічного стилю в українській мові. На відміну від російської мови, де пасивні конструкції є поширеними, сучасна українська наукова мова тяжіє до активних та безособових конструкцій, що підкреслюють дію або її результат, а не пасивний стан об'єкта.

#### Конструкції на `-но`, `-то` як маркер безособової результативності

Центральним елементом українського академічного синтаксису є широке використання безособових дієслівних форм на **-но, -то**.

*   **Призначення**: Вони використовуються для того, щоб зосередити увагу не на виконавцеві, а на самій дії, її завершенні та результаті (Джерело: 7-klas-ukrmova-zabolotnyi-2024_s0119). Це надає викладу об'єктивного характеру.
*   **Структура**: Ці форми є незмінними і виступають головним членом (присудком) в односкладних безособових реченнях, при якому немає і не може бути підмета (Джерело: 7-klas-ukrmova-avramenko-2024_s0128, 11-klas-ukrajinska-mova-glazova-2019_s0139).
    *   *Приклад:* `Книжку було прочитано.` (Джерело: 7-klas-ukrmova-avramenko-2024_s0128)
    *   *Приклад:* `Рішення ухвалено одноголосно.` (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0109)
    *   *Приклад:* `На основі штучного інтелекту (ШІ) створено багато інструментів.` (Джерело: 7-klas-ukrmova-zabolotnyi-2024_s0119)

*   **Ключове правило: заборона на вказівку діяча**: Введення в речення з формою на `-но, -то` виконавця дії в орудному відмінку є **грубим порушенням** мовної норми (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0109, 11-klas-ukrajinska-mova-glazova-2019_s0139).
    *   ❌ **Помилково**: `Іспит складено студентом.`
    *   ✅ **Правильно**: `Іспит складено.` або `Студент склав іспит.` (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0109)
*   **Виняток (знаряддя дії)**: Орудний відмінок можливий, якщо він позначає не виконавця, а знаряддя дії.
    *   *Приклад:* `Лист написано олівцем.` (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0109)

#### Стилістична перевага `-но`, `-то` над пасивними дієприкметниками

В академічному та діловому стилях конструкції на `-но, -то` є бажаними замість пасивних дієприкметників у ролі присудка.
*   **Порівняйте**:
| Менш бажано (пасивний дієприкметник) | Стилістично краще (форма на -но, -то) | Джерело |
| :--- | :--- | :--- |
| `Ці слова вимовлені тихо.` | `Ці слова вимовлено тихо.` | `11-klas-ukrajinska-mova-avramenko-2019_s0109` |
| `Ухвала прийнята одноголосно.` | `Ухвалу прийнято одноголосно.` | `11-klas-ukrajinska-mova-avramenko-2019_s0110` |
| `Шкільний конкурс продовжений на місяць.` | `Шкільний конкурс продовжено на місяць.`| `11-klas-ukrajinska-mova-glazova-2019_s0141` |

Пасивні дієприкметники природніше вживати в ролі означення: `вимовлені слова`, `книжка, підписана автором` (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0110).

#### Уникнення пасивних конструкцій з дієсловами на `-ся`

Сучасна українська мовна норма, особливо в науковому стилі, вимагає уникати пасивних конструкцій з дієсловами на `-ся`, де діяч стоїть в орудному відмінку. Такі конструкції вважаються кальками з російської мови.

*   **Порівняйте**:
| ❌ Помилково (калька з російської) | ✅ Правильно (активна конструкція) | Джерело |
| :--- | :--- | :--- |
| `Учнями пишуться твори.` | `Учні пишуть твори.` | `11-klas-ukrajinska-mova-avramenko-2019_s0110` |
| `Депутатами приймаються закони.` | `Депутати приймають закони.` | `11-klas-ukrajinska-mova-avramenko-2019_s0110` |
| `Проте деякими дослідниками глобальне потепління не визнається...` | `Проте деякі дослідники не визнають глобальне потепління...` | `11-klas-ukrajinska-mova-glazova-2019_s0136` |

Як альтернативу, можна використовувати **неозначено-особові речення**, де діяч не називається, але мислиться як група людей: `Присудок підкреслюють двома рисками` (замість `Присудок підкреслюється...`) (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0110).

### Лексичні та морфологічні маркери

*   **Віддієслівні іменники**: Характерним є вживання іменників на `-ння`, `-ття`, що позначають опредметнену дію: `дослідження`, `вивчення`, `використання`, `визначення`, `порівняння` (Джерело: 9-klas-ukrajinska-mova-voron-2017_s0049).
*   **Аналітичні форми ступенів порівняння**: Форми прикметників з `більш` і `менш` (`більш досконалий`, `менш глибокий`) мають книжний відтінок і є характерними для наукового стилю (Джерело: 11-klas-ukrmova-zabolotnyi-2019_s0289).
*   **Нейтральні форми дієслів**: Вживаються повні, нейтральні форми дієслів (`жити`, `питає`, `беремо`), а не їхні коротші розмовні або поетичні відповідники (`жить`, `пита`, `берем`) (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0258).

## Типові помилки L2 (Common L2 Errors)

Володіння академічним стилем вимагає подолання кількох типових помилок, що часто виникають у носіїв інших мов, зокрема англійської та російської.

| ❌ Помилково | ✅ Правильно | Пояснення |
| :--- | :--- | :--- |
| `Звіт було написано менеджером.` | `Менеджер написав звіт.` <br> або <br> `Звіт було написано.` | **Помилка**: Вживання діяча в орудному відмінку з конструкцією на `-но, -то`. **Причина**: Пряме перенесення пасивної конструкції з англійської ("The report was written *by* the manager"). Українська граматика категорично забороняє таку модель (Джерела: 11-klas-ukrajinska-mova-avramenko-2019_s0109, 11-klas-ukrajinska-mova-glazova-2019_s0139). |
| `Новий закон розглядається парламентом.` | `Парламент розглядає новий закон.` <br> або <br> `Новий закон розглядають.` | **Помилка**: Вживання пасивної конструкції на `-ся` з діячем в орудному відмінку. **Причина**: Калька з російської мови (`Закон рассматривается парламентом`). Сучасна українська норма вимагає активних або неозначено-особових конструкцій (Джерела: 11-klas-ukrajinska-mova-avramenko-2019_s0110, 11-klas-ukrajinska-mova-glazova-2019_s0136). |
| `Результати експерименту вже опубліковані.` | `Результати експерименту вже опубліковано.` | **Помилка**: Вживання пасивного дієприкметника в ролі присудка. **Причина**: Хоча це не настільки груба помилка, як попередні, форма на `-но` є стилістично кращою для академічного тексту, оскільки вона наголошує на результаті дії, що є ключовим для науки (Джерела: 11-klas-ukrajinska-mova-avramenko-2019_s0110, 11-klas-ukrajinska-mova-glazova-2019_s0141). |
| `Цей аргумент сильніший.` | `Цей аргумент є більш сильним.` | **Помилка**: Вживання простої (синтетичної) форми вищого ступеня порівняння. **Причина**: Хоча форма `сильніший` є абсолютно правильною, аналітична форма `більш сильний` має виразний книжний, формальний відтінок, що є доречним в академічному письмі (Джерело: 11-klas-ukrmova-zabolotnyi-2019_s0289). |
| `Ми розглянем це питання в наступному розділі.` | `Ми розглянемо це питання в наступному розділі.` | **Помилка**: Вживання короткої, розмовної форми дієслова. **Причина**: Скорочені форми дієслів (`розглянем`, `робим`) є характерними для розмовного стилю. Академічне письмо вимагає вживання повних, нейтральних форм (`розглянемо`, `робимо`) (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0258). |

## Деколонізаційні застереження (Decolonization Notes)

Питання пасивних конструкцій є одним з ключових полів деколонізації українського синтаксису. Протягом тривалого часу українська мова перебувала під впливом російської, що призвело до поширення нехарактерних для неї синтаксичних моделей.

**Ключова відмінність**: В основі лежить фундаментальна риса українського синтаксису — перевага активного стану. Як зазначає О. Авраменко: **«Особливістю української мови є те, що в центрі уваги завжди перебуває особистість, а не процес. Якщо російською *дело рассматривается, вопрос обсуждается*, то українською — *розглядають справу, обговорюють питання*.»** (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0110).

1.  **Пасив на `-ся` — це русизм**: Конструкції типу `стаття пишеться автором`, `проблема досліджується вченими` є прямими кальками з російської мови. Вони є проявом "канцеляриту" — знеособленого, бюрократичного мовлення, яке активно викорінюється з сучасної української мови. Українська мова, тяжіючи до динамізму, віддає перевагу активним конструкціям (`

============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18320 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a academic brief for the Ukrainian language curriculum ...
Dimension scores:
1. Factual: 7/10 — The article falsely claims that using the synthetic degree of comparison (`сильніший`) is an error in academic style, labeling it a mistake in the table. In reality, both simple and compound forms are acceptable in scientific style (as per Glazova 11 kl., p. 29), and the synthetic form is often preferred to avoid "більш/менш" overuse. 
2. Language: 6/10 — The article explicitly condemns the use of passive `-ся` constructions, yet hypocritically uses them in its own text to explain the rules: "Вони використовуються для того", "діяч не називається, але мислиться".
3. Decolonization: 5/10 — The article violates the core decolonization rule of not presenting Ukrainian through a "like Russian but..." framing. It explicitly centers Russian ("На відміну від російської мови, де пасивні конструкції є поширеними...") and quotes Avramenko's direct comparison to Russian, which undermines the goal of teaching Ukrainian on its own terms.
4. Completeness: 8/10 — Covers the major markers (lexicon, syntax, `-но/-то`), but the article literally cuts off mid-sentence at the very end (`віддає перевагу активним конструкціям (`).
5. Actionable: 5/10 — The brief explains *what* the academic style is, but provides absolutely zero actionable exercises, sequences, or drills for a module writer to actually implement. It is pure theory.

**Overall: 6.2/10**

<fixes>
old: Синтаксис є найважливішим маркером академічного стилю в українській мові. На відміну від російської мови, де пасивні конструкції є поширеними, сучасна українська наукова мова тяжіє до активних та безособових конструкцій, що підкреслюють дію або її результат, а не пасивний стан об'єкта.
new: Синтаксис є найважливішим маркером академічного стилю в українській мові. Сучасна українська наукова мова органічно тяжіє до активних та безособових конструкцій, що підкреслюють дію або її результат, а не пасивний стан об'єкта.
---
old: *   **Призначення**: Вони використовуються для того, щоб зосередити увагу не на виконавцеві, а на самій дії, її завершенні та результаті (Джерело: 7-klas-ukrmova-zabolotnyi-2024_s0119). Це надає викладу об'єктивного характеру.
new: *   **Призначення**: Їх використовують для того, щоб зосередити увагу не на виконавцеві, а на самій дії, її завершенні та результаті (Джерело: 7-klas-ukrmova-zabolotnyi-2024_s0119). Це надає викладу об'єктивного характеру.
---
old: де діяч не називається, але мислиться як група людей:
new: де діяча не називають, але мислять як групу людей:
---
old: *   **Аналітичні форми ступенів порівняння**: Форми прикметників з `більш` і `менш` (`більш досконалий`, `менш глибокий`) мають книжний відтінок і є характерними для наукового стилю (Джерело: 11-klas-ukrmova-zabolotnyi-2019_s0289).
new: *   **Ступені порівняння**: В академічному тексті функціонують як прості (`глибший`), так і складені (`більш глибокий`) форми. Важливо уникати гібридних помилок (`більш глибший`) та надмірного використання конструкцій із `більш/менш`, що часто маскує кальки (Джерела: 11-klas-ukrmova-zabolotnyi-2019_s0289, 11-klas-ukrajinska-mova-glazova-2019_s0029).
---
old: | `Цей аргумент сильніший.` | `Цей аргумент є більш сильним.` | **Помилка**: Вживання простої (синтетичної) форми вищого ступеня порівняння. **Причина**: Хоча форма `сильніший` є абсолютно правильною, аналітична форма `більш сильний` має виразний книжний, формальний відтінок, що є доречним в академічному письмі (Джерело: 11-klas-ukrmova-zabolotnyi-2019_s0289). |
new: | `Цей аргумент є більш сильнішим.` | `Цей аргумент сильніший.` <br> або <br> `Цей аргумент є більш сильним.` | **Помилка**: Подвійне вираження ступеня порівняння або надмірне захоплення аналітичними формами. **Причина**: В українському академічному стилі вживають як прості (синтетичні), так і складені (аналітичні) форми. Однак проста форма (`сильніший`) є дуже природною, тоді як зловживання словами `більш/менш` часто є наслідком іншомовного впливу (Джерела: 11-klas-ukrmova-zabolotnyi-2019_s0289, 11-klas-ukrajinska-mova-glazova-2019_s0029). |
---
old: **Ключова відмінність**: В основі лежить фундаментальна риса українського синтаксису — перевага активного стану. Як зазначає О. Авраменко: **«Особливістю української мови є те, що в центрі уваги завжди перебуває особистість, а не процес. Якщо російською *дело рассматривается, вопрос обсуждается*, то українською — *розглядають справу, обговорюють питання*.»** (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0110).

1.  **Пасив на `-ся` — це русизм**: Конструкції типу `стаття пишеться автором`, `проблема досліджується вченими` є прямими кальками з російської мови. Вони є проявом "канцеляриту" — знеособленого, бюрократичного мовлення, яке активно викорінюється з сучасної української мови. Українська мова, тяжіючи до динамізму, віддає перевагу активним конструкціям (`
new: **Ключова питома риса**: В основі лежить фундаментальна властивість українського синтаксису — динамізм та перевага активного стану. Як зазначає О. Авраменко: **«Особливістю української мови є те, що в центрі уваги завжди перебуває особистість, а не процес...»** Тому природно говорити: *розглядають справу, обговорюють питання* (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0110).

1.  **Позбавлення канцелярського пасиву**: Конструкції типу `стаття пишеться автором`, `проблема досліджується вченими` є проявом штучного "канцеляриту" — знеособленого мовлення, яке суперечить духу української мови. Сучасний стандарт передбачає повернення до природного синтаксису: віддавайте перевагу активним конструкціям (`автор пише статтю`, `вчені досліджують проблему`).
---
INSERT AFTER: віддавайте перевагу активним конструкціям (`автор пише статтю`, `вчені досліджують проблему`).

### Практичні кроки для авторів модулів (Actionable Guidance)

Для успішної інтеграції цієї теми у навчальні модулі рівня C1, використовуйте такі типи активностей:
1.  **Transformation Drills (Трансформація)**: Дайте студентам речення з канцелярським пасивом на `-ся` та попросіть переробити їх на активні або безособові (на `-но`, `-то`).
    *   *Завдання*: Перетворіть "Цей факт підтверджується багатьма дослідженнями".
    *   *Очікувано*: "Цей факт підтверджено багатьма дослідженнями" або "Багато досліджень підтверджують цей факт".
2.  **Editing/Proofreading (Редагування)**: Створіть фрагмент "поганого" наукового тексту, перенасиченого русизмами, пасивом та емоційною лексикою. Студенти мають знайти і виправити стилістичні помилки.
3.  **Corpus Research (Робота з корпусом)**: Дайте завдання знайти 5 прикладів використання безособових форм на `-но, -то` в реальних українських наукових статтях або у Вікіпедії.
</fixes>


────────────────────────────────────────
✅ Gemini finished (6630 chars)
✅ Message sent to Claude (ID: 28326)
✓ Message 28326 acknowledged
   Auto-acknowledged reply #28326 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-c1-academic-style-markers-final' — skipping GH posting (review saved to orchestration/)
✓ Message 28324 acknowledged
