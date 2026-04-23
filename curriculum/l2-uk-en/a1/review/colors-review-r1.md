# V6 Aggregate Review — Per-Dimension Independent Reviewer

Overall Score: 4.8/10
Weighted Average: 6.4/10
**Status:** FAIL

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Factual | 7.4/10 | - Українською: `Adjectives in Ukrainian are strictly divided into these hard and soft groups.` English: The packet supports teaching two inflection patterns for color adjectives in this lesson, but... |
| 2. Language | 5.8/10 | - Українською: У модулі системно змішано англійську з українською: `This first conversation features Natalka...`, `такі форми використовуються naturally in conversation`, `a direct відповідь is exp... |
| 3. Decolonization | 8.8/10 | - Українською: «В українській мові ми активно вчимо пару слів для цього кольору: «синій» та «блакитний». «Синій» — це глибокий колір. Ми кажемо «синє море» або «синє чорнило». Натомість «блакитний»... |
| 4. Completeness | 8.3/10 | - Українською: Контракт: `Мовленнєва рамка: \`Якого кольору...?\` + коротка відповідь одним прикметником` Модуль: `«Якого кольору олівець? — Червоний.»`, `«Якого кольору сукня? — Червона.»`, `«Яког... |
| 5. Actionable | 4.9/10 | - Українською: `For example: «Якого кольору олівець? — Червоний.», «Якого кольору сукня? — Червона.», and «Якого кольору вікно? — Біле.»` English: This is one of the few places where the learner ge... |
| 6. Naturalness | 4.8/10 | - Українською: Модуль системно звучить як перекладена мета-розповідь, а не як живе українське пояснення: "This first conversation features Natalka selecting flowers for a special event.", "We will... |
| 7. Plan Adherence | 6.8/10 | - Українською: Порядок розділів збігається з планом: `## Діалоги`, `## Кольори`, `## Синій ≠ блакитний`, `## Підсумок`. English: The section order follows the contract exactly. - Українською: Розді... |
| 8. Honesty | 4.8/10 | - Українською: У writer prompt є пряме правило: uncertain claims must be marked with `<!-- VERIFY -->`; також сказано “Never invent. Silent invention is the worst failure mode.” У модулі немає жодн... |
| 9. Dialogue | 5.8/10 | - Українською: Найприродніше місце в розділі: `— **Наталка:** А ці квіти? Якого вони кольору?` / `— **Продавець:** Це білі лілії. Вони дуже свіжі.` English: This is the one exchange that actually s... |

## Findings
[FACTUAL] [SEVERITY: major]
Location: `Adjectives in Ukrainian are strictly divided into these hard and soft groups.`
Issue: Українською: Це надто широке граматичне узагальнення. Контракт і `pedagogy/a1/colors.md` тут підтверджують лише навчальну рамку для кольорів: тверда група `-ий` проти м'якої `-ій`, з акцентом на `синій`. Формула `strictly divided` про всі прикметники виходить за межі підтвердженого.
English: This is an overgeneralization. The source supports a lesson-specific contrast for color adjectives, not a universal statement about the entire adjective system.
Fix: Замінити на формулювання, обмежене рамкою цього уроку: “For this lesson, color adjectives are presented through two inflection patterns: hard and soft groups.”
[FACTUAL] [SEVERITY: minor]
Location: `When someone's hair turns grey with age, we do not use «сірий» (the color of a stone or an animal). Instead, we use the specific adjective for hair and say «сиве волосся» (grey hair).`
Issue: Українською: Правильний чанк `сиве волосся` подано вірно, але речення перебільшує: пакет дає позитивну норму `сиве волосся`, а не доводить категоричну заборону `сірий`; вставка про “stone or an animal” також не має опори в джерелах.
English: The target collocation is correct, but the wording is too absolute and adds an unsupported gloss.
Fix: Пом'якшити до описової норми: “When describing grey hair, Ukrainian normally uses «сиве волосся».”
[LANGUAGE] [SEVERITY: major]
Location: Діалоги / `This first conversation features Natalka selecting flowers for a special event. She speaks with a seller to find the perfect combination of bright spring colors.`
Issue: Українською: Англомовний вступ у середині українського модуля порушує мовну чистоту й звучить як редакторська метанарація, а не як навчальний текст українською.
English: The section opener is in English instead of clean Ukrainian.
Fix: `У першому діалозі Наталка вибирає квіти для особливої події. Вона розмовляє з продавцем і добирає гарне поєднання весняних кольорів.`
[LANGUAGE] [SEVERITY: major]
Location: Діалоги / `The adjective in «жовті соняшники» explicitly uses the plural ending, and такі форми використовуються naturally in conversation. When asking якого кольору? (what color?), a direct відповідь is expected, often без a full sentence.`
Issue: Українською: Це мішанина англійської й української в одному поясненні; така подача неприродна і не може вважатися чистою українською.
English: This is direct code-switching inside a grammar explanation.
Fix: `У словосполученні «жовті соняшники» прикметник ужито у формі множини, і в розмові така форма звучить природно. На запитання «Якого кольору?» часто відповідають коротко, без повного речення.`
[LANGUAGE] [SEVERITY: major]
Location: Кольори / `We will look at 12 базових кольорів, поділених на дві групи за типами прикметників. Most of these belong to the hard group. Ця Тверда група follows the exact same \`-ий/-а/-е/-і\` gender agreement pattern you already know.`
Issue: Українською: Пояснення знову ламане, з англійським синтаксисом і код-міксом; `Ця Тверда група follows...` мовно неприйнятне.
English: The sentence is not valid clean Ukrainian.
Fix: `Розгляньмо 12 базових кольорів, поділених на дві групи за типами прикметників. Більшість із них належить до твердої групи. Ця тверда група має той самий зразок узгодження: \`-ий/-а/-е/-і\`.`
[LANGUAGE] [SEVERITY: major]
Location: Синій ≠ блакитний / `Наш прапор — синьо-жовтий, де є жовтий колір.`
Issue: Українською: Зворот `де є жовтий колір` неідіоматичний і звучить як буквальний переклад.
English: This is clumsy translationese.
Fix: `Наш прапор — синьо-жовтий.`
[LANGUAGE] [SEVERITY: major]
Location: Підсумок / `The base noun «колір» is masculine, but it changes form here.`
Issue: Українською: Граматичний коментар подано англійською, ще й через неприродне для українського пояснення формулювання `base noun`.
English: The grammar note should be written in proper Ukrainian.
Fix: `Іменник «колір» — чоловічого роду, але у формулі «Якого кольору?» він стоїть у формі родового відмінка.`
[DECOLONIZATION] [SEVERITY: major]
Location: `Синій ≠ блакитний` / “The word «голубий» is simply a synonym, but we use «блакитний».”
Issue: Українською: Це не російсько-центричне пояснення напряму, але воно все одно зсуває рамку в бік оборонного «відсікання» слова замість українсько-центричного опису норми. За контрактом тут потрібне пасивне впізнавання `голубий` як словникового синоніма поза модулем, а не формула «ми вживаємо `блакитний`», яка звучить як жорстке витіснення.
English: This avoids an explicit Russian comparison, but it still frames the topic as lexical policing rather than Ukrainian-first description. The contract requires passive recognition, not blanket exclusion.
Fix: Замінити на нейтральне українсько-центричне формулювання: `У цьому модулі активно вживаємо «блакитний»; слово «голубий», якщо трапиться поза модулем, досить пасивно впізнавати як словниковий синонім.`
[COMPLETENESS] [SEVERITY: major]
Location: `## Діалоги` — перший діалог має `«А ці квіти? Якого вони кольору?» → «Це білі лілії.»`; другий діалог від `«Мені потрібна чорна сукня.»` до `«У нього сиве волосся.»` не містить жодної короткої репліки-відповіді на `Якого кольору?`.
Issue: Українською: Контракт вимагає, щоб кольори в діалогах входили через запитання `Якого кольору?` і коротку відповідь; у модулі ця рамка добре пояснена в секції `Кольори`, але недостатньо відпрацьована саме в діалоговій практиці, особливо в другому діалозі.
English: The speech frame is taught, but not sufficiently realized inside the contracted dialogues.
Fix: Додати в обидва діалоги по 1-2 обміни з короткими відповідями типу `Якого кольору троянди? — Червоні.` / `Якого кольору светр? — Білий.` і завершити перший діалог реплікою `Загорнути букет?`.
[COMPLETENESS] [SEVERITY: minor]
Location: `## Підсумок` — `* **Опишіть 3 речі:** Give short descriptive answers for three items near you...`
Issue: Українською: Контрактовий self-check вимагає `опишіть 3 речі у вашій кімнаті`, але модуль розширює завдання до будь-яких речей `near you`, тому конкретний кімнатний сценарій не зафіксований.
English: The recap task drifts from the contracted “in your room” scenario.
Fix: Уточнити вправу як опис саме трьох речей у кімнаті, бажано з одним прикладом на кшталт `Кімната біла. Стіл коричневий. Крісло сіре.`
[ACTIONABLE] [SEVERITY: critical]
Location: `## Кольори / "<!-- INJECT_ACTIVITY: quiz-what-color -->"`; same pattern in `fill-in-color-agreement`, `quiz-blue-vs-lightblue`, `match-up-appearance`, `group-sort-hard-soft`
Issue: Українською: Тут немає вправ, лише технічні маркери. Учень не бачить запитання, не має кроків, не дає відповіді і не виконує жодної дії, хоча контракт вимагає вправ після кожного блоку.
English: The required learner tasks are missing from the rendered lesson.
Fix: Замінити кожен `INJECT_ACTIVITY` на коротку вправу з 3-5 пунктами, зразком відповіді й чіткою дією для учня.
[ACTIONABLE] [SEVERITY: major]
Location: `## Діалоги / "This first conversation features Natalka selecting flowers for a special event. She speaks with a seller to find the perfect combination of bright spring colors."`
Issue: Українською: Це анонс сцени, а не навчальна інструкція. Учневі не сказано, що саме зробити з діалогом: знайти форму, дати коротку відповідь, повторити репліку, підставити інше слово.
English: The paragraph narrates content instead of directing learner behavior.
Fix: Перед діалогом дати завдання з послідовністю дій: знайти три відповіді на `Якого кольору?`, виписати одну форму множини, повторити діалог з іншими назвами квітів.
[ACTIONABLE] [SEVERITY: major]
Location: `## Діалоги / "Діалог на ринку часто вимагає чітких та коротких відповідей."` and `## Кольори / "Learning «синій» now prepares you for other soft adjectives later."`
Issue: Українською: Це загальні поради без учнівського ходу. Вони не дають ні мовного зразка, ні міні-вправи, ні перевірки, тому не допомагають виконати конкретну дію.
English: These are generic meta-comments, not usable teaching moves.
Fix: Кожен такий `tip` треба перетворити на мікрозавдання з 2-3 репліками або міні-дрилом.
[ACTIONABLE] [SEVERITY: major]
Location: `## Підсумок / "Your primary tool for communication is the question «Якого кольору...?». The base noun «колір» is masculine, but it changes form here."`
Issue: Українською: Блок знову пояснює правило абстрактно, хоча контракт вимагає послідовність `коротка відповідь -> повне речення`. Конкретна дія з'являється лише в кінцевому self-check, а не одразу після пояснення.
English: The learner is told about the pattern instead of being led through it step by step.
Fix: Одразу після цього місця дати три кроки: коротка відповідь, повне речення, власний приклад з предметом у кімнаті.
[NATURALNESS] [SEVERITY: critical]
Location: Діалоги / "This first conversation features Natalka selecting flowers for a special event. She speaks with a seller to find the perfect combination of bright spring colors."
Issue: Українською: Це чиста англомовна підводка з рекламно-шаблонним тоном. Так не починає український навчальний модуль.
English: It reads like AI scene-setting, not teacher prose.
Fix: "У першому діалозі Наталка вибирає квіти для букета й питає про їхній колір."
[NATURALNESS] [SEVERITY: major]
Location: Діалоги / "The phrase «мені подобаються» is a ready-made expression for personal preferences. The adjective in «жовті соняшники» explicitly uses the plural ending, and такі форми використовуються naturally in conversation."
Issue: Українською: Речення ламане, з англійським синтаксисом і механічною термінологією на кшталт "explicitly uses". Воно звучить не як українське пояснення, а як сирий машинний мікс.
English: The code-switching is especially unnatural here.
Fix: "Вислів «мені подобаються» краще запам'ятати як готову мовну модель. У словосполученні «жовті соняшники» маємо форму множини, і в живому мовленні вона звучить природно."
[NATURALNESS] [SEVERITY: major]
Location: Кольори / "When asking about the color of an object in Ukrainian, we use the phrase якого кольору? (what color?). In natural speech, the immediate response is often just the adjective. This provides a clear short відповідь before building a full sentence."
Issue: Українською: Уся підводка побудована як переклад з англійської. Формула "clear short відповідь" неприродна й псує довіру до тексту.
Fix: "Коли питаємо про колір, уживаємо формулу «Якого кольору?». У відповіді часто досить одного слова: «Червоний», «Червона», «Біле»."
[NATURALNESS] [SEVERITY: major]
Location: Кольори / "We will look at 12 базових кольорів, podілених на дві групи за типами прикметників. Most of these belong to the hard group. Ця Тверда група follows the exact same `-ий/-а/-е/-і` gender agreement pattern you already know."
Issue: Українською: Це суцільна штучна мішанина мов і термінів. Український викладач скаже простіше й суцільно однією мовою.
Fix: "Розгляньмо 12 базових кольорів. Більшість із них належить до твердої групи й змінюється за зразком `-ий/-а/-е/-і`."
[NATURALNESS] [SEVERITY: major]
Location: Синій ≠ блакитний / "В українській мові ми активно вчимо пару слів для цього кольору: «синій» та «блакитний»."
Issue: Українською: "активно вчимо пару слів" звучить канцелярсько й неприродно. Тут потрібне просте пояснення різниці, а не методичний штамп.
Fix: "В українській мові розрізняємо дві назви цього кольору: «синій» і «блакитний»."
[NATURALNESS] [SEVERITY: critical]
Location: Підсумок / "To master the vocabulary in this lesson, you must apply the grammar concepts from a previous module («модуль»)."
Issue: Українською: Це жорстка перекладна інструкція з англомовним ритмом. У підсумку вона звучить особливо неживо й формально.
English: The summary opens like a workbook translation, not natural Ukrainian pedagogy.
Fix: "Щоб упевнено вживати ці слова, повторімо узгодження прикметників із іменниками."
[NATURALNESS] [SEVERITY: major]
Location: Підсумок / "Your primary tool for communication is the question «Якого кольору...?». The base noun «колір» is masculine, but it changes form here."
Issue: Українською: Формули "primary tool for communication" і "base noun" неприродні для українського навчального стилю. Це не пояснення, а технічний переказ.
Fix: "Головна мовна формула цього модуля — «Якого кольору...?». Після неї зазвичай відповідаємо коротко: «зелений», «біла», «сіре»."
[PLAN_ADHERENCE] [SEVERITY: major]
Location: `## Діалоги`: `— **Наталка:** А ці квіти? Якого вони кольору?` / `— **Продавець:** Це білі лілії. Вони дуже свіжі.`; далі перший діалог закінчується на `— **Наталка:** Так. Додайте ще зелене листя, будь ласка.` і відразу починається `Next, Dmytro and Liza...`
Issue: Українською: План вимагає, щоб кольори входили через `Якого кольору?` + коротку відповідь, і прямо задає фінальний хід `— Добре, загорнути букет?`. У модулі питання змінене на `Якого вони кольору?`, відповідь розгорнута, а репліка про загортання букета відсутня до переходу в другий діалог.
English: The first dialogue drifts from the planned prompt-response shape and omits the bouquet-wrapping close.
Fix: Переписати обмін як коротку модель `Якого кольору? — Білі/Червоні` і додати завершення `— Добре, загорнути букет? — Так, будь ласка.`
[PLAN_ADHERENCE] [SEVERITY: major]
Location: `## Діалоги`: `— **Дмитро:** Який одяг ти шукаєш?` / `— **Ліза:** Мені потрібна чорна сукня. А ти?` / `— **Дмитро:** Цей білий светр і коричневі черевики.`
Issue: Українською: За контрактом функція другого діалогу має містити `короткі відповіді на "Якого кольору?"`; у наведеному уривку таких питань і коротких відповідей немає, лише перелік предметів одягу.
English: Dialogue 2 covers the right nouns and appearance chunks, but not the planned question-answer drill.
Fix: Додати щонайменше один обмін на кшталт `— Якого кольору сукня? — Чорна. — А светр? — Білий.`
[PLAN_ADHERENCE] [SEVERITY: major]
Location: `## Діалоги` — фактичний обсяг близько `376` слів при плані `270–330`.
Issue: Українською: Розділ перевищує верхню межу бюджету на приблизно 46 слів. Перевищення створюють додані англомовні вступи й пояснювальні вставки, яких план не вимагає.
English: The dialogues section is materially over budget.
Fix: Прибрати англомовні вступні абзаци й стиснути пояснення після діалогів, щоб повернутися в межі `270–330` слів.
[PLAN_ADHERENCE] [SEVERITY: minor]
Location: `## Синій ≠ блакитний` — фактичний обсяг близько `333` слів при плані `270–330`.
Issue: Українською: Розділ трохи виходить за ліміт.
English: This section is only slightly over the budget.
Fix: Скоротити 3-5 слів, найпростіше прибравши частину англомовного дубляжу.
[HONESTY] [SEVERITY: major]
Location: `## Діалоги` / “This first conversation features Natalka selecting flowers for a special event. She speaks with a seller to find the perfect combination of bright spring colors.”
Issue: Українською: Контракт задає квітковий ринок і вибір букета, але не “special event” і не “bright spring colors”. Це домислене сценічне оформлення без опори на надані джерела.
English: Unsupported scene embellishment.
Fix: Replace with neutral framing grounded in the contract, or add `<!-- VERIFY -->`.
[HONESTY] [SEVERITY: critical]
Location: `## Діалоги` / “За мотивами вірша про сонце, мені подобаються жовті соняшники.”
Issue: Українською: Контракт каже “за мотивами вірша про кольори з підручника Большакової”, а модуль упевнено підміняє це на “вірша про сонце”. Це вже виглядає як вигадана source-like detail без перевірки.
English: The module changes the source framing from “poem about colors” to “poem about the sun” without support.
Fix: Restore the contract wording or add `<!-- VERIFY -->` at the sentence.
[HONESTY] [SEVERITY: major]
Location: `## Кольори` / “Adjectives in Ukrainian are strictly divided into these hard and soft groups.”
Issue: Українською: Це надто сильне, некваліфіковане правило. Вікі для цього модуля справді протиставляє тверду й м’яку групу на прикладі `синій`, але не вимагає такої абсолютної формули “strictly divided”.
English: Overstated certainty where the source supports a teaching contrast, not a hard universal claim.
Fix: Hedge the claim or cite an explicit authority; otherwise mark `<!-- VERIFY -->`.
[HONESTY] [SEVERITY: major]
Location: `## Синій ≠ блакитний` and `## Підсумок` / “We do not use the standard word for brown when talking about eyes.” / “You must use «карі очі»...” / “always use «русяве волосся»...” / “exactly how native speakers talk.”
Issue: Українською: Джерела підтримують ці сполуки як готові природні чанки для A1, але модуль перетворює це на абсолютні заборони й безапеляційні норми. За правилом honesty тут треба було або пом’якшити формулювання, або позначити зону ризику через `<!-- VERIFY -->`.
English: The source supports preferred collocations, not categorical “must/always/exactly” language.
Fix: Rephrase as “natural/preferred chunks at A1” or add `<!-- VERIFY -->`.
[DIALOGUE] [SEVERITY: critical]
Location: `## Діалоги` / `— **Наталка:** За мотивами вірша про сонце, мені подобаються жовті соняшники.`
Issue: Українською: Це не репліка покупчині на ринку, а вбудована методична примітка. Фраза звучить штучно й одразу робить сцену "підручниковою".  
English: This is prompt language disguised as dialogue.
Fix: `— **Наталка:** Мені подобаються жовті соняшники.`
[DIALOGUE] [SEVERITY: critical]
Location: `## Діалоги` / `— **Продавець:** Чудово! У вас є синя ваза для них?`
Issue: Українською: Порушена побутова логіка сцени: продавець не питає покупця, чи має той вазу, а зазвичай пропонує загорнути букет або додати щось до нього.  
English: The turn-taking is not socially plausible for this setting.
Fix: `— **Продавець:** Чудово! Додати ще зелене листя?` + `— **Наталка:** Так, будь ласка. У мене є синя ваза.`
[DIALOGUE] [SEVERITY: major]
Location: `## Діалоги` / `— **Дмитро:** Цей білий светр і коричневі черевики.`
Issue: Українською: Це звучить як перелік лексики під картинкою, а не як відповідь у живій розмові. Діалог через це стає drill-like.  
English: The line is a label list, not natural speech.
Fix: `— **Дмитро:** Шукаю білий светр і коричневі черевики.`

## Verdict: REJECT
MIN score gate = 4.8/10; driving dimension(s): Naturalness, Honesty.

<fixes>
- find: Adjectives in Ukrainian are strictly divided into these hard and soft groups.
    Learning «синій» now prepares you for other soft adjectives later.
  replace: 'For this lesson, color adjectives are presented through two inflection
    patterns: hard and soft groups. Learning «синій» now prepares you for other soft
    adjectives later.'
- find: When someone's hair turns grey with age, we do not use «сірий» (the color
    of a stone or an animal). Instead, we use the specific adjective for hair and
    say «сиве волосся» (grey hair).
  replace: When describing grey hair, Ukrainian normally uses «сиве волосся».
- find: This first conversation features Natalka selecting flowers for a special event.
    She speaks with a seller to find the perfect combination of bright spring colors.
  replace: У першому діалозі Наталка вибирає квіти для особливої події. Вона розмовляє
    з продавцем і добирає гарне поєднання весняних кольорів.
- find: The adjective in «жовті соняшники» explicitly uses the plural ending, and
    такі форми використовуються naturally in conversation. When asking якого кольору?
    (what color?), a direct відповідь is expected, often без a full sentence.
  replace: У словосполученні «жовті соняшники» прикметник ужито у формі множини, і
    в розмові така форма звучить природно. На запитання «Якого кольору?» часто відповідають
    коротко, без повного речення.
- find: We will look at 12 базових кольорів, поділених на дві групи за типами прикметників.
    Most of these belong to the hard group. Ця Тверда група follows the exact same
    `-ий/-а/-е/-і` gender agreement pattern you already know.
  replace: 'Розгляньмо 12 базових кольорів, поділених на дві групи за типами прикметників.
    Більшість із них належить до твердої групи. Ця тверда група має той самий зразок
    узгодження: `-ий/-а/-е/-і`.'
- find: Наш прапор — синьо-жовтий, де є жовтий колір.
  replace: Наш прапор — синьо-жовтий.
- find: The base noun «колір» is masculine, but it changes form here.
  replace: Іменник «колір» — чоловічого роду, але у формулі «Якого кольору?» він стоїть
    у формі родового відмінка.
- find: The word «голубий» is simply a synonym, but we use «блакитний». This is worth
    knowing for quick recognition of colors.
  replace: У цьому модулі активно вживаємо «блакитний»; слово «голубий», якщо трапиться
    поза модулем, досить пасивно впізнавати як словниковий синонім до «блакитний».
- insert_after: '> — **Наталка:** Так. Додайте ще зелене листя, будь ласка. *(Yes.
    Add some green leaves, please.)*'
  text: '> — **Наталка:** Якого кольору троянди? *(What color are the roses?)*

    > — **Продавець:** Червоні. *(Red.)*

    > — **Наталка:** А лілії? *(And the lilies?)*

    > — **Продавець:** Білі. Загорнути букет? *(White. Shall I wrap the bouquet?)*'
- insert_after: '> — **Ліза:** Надворі холодно. Тобі треба сіре пальто. *(It is cold
    outside. You need a grey coat.)*'
  text: '> — **Ліза:** Якого кольору светр? *(What color is the sweater?)*

    > — **Дмитро:** Білий. *(White.)*

    > — **Дмитро:** А сукня? *(And the dress?)*

    > — **Ліза:** Чорна. *(Black.)*'
- insert_after: '* **Опишіть 3 речі:** Give short descriptive answers for three items
    near you, ensuring the color adjective matches the noun''s gender. For example,
    you could say «Моя книга червона».'
  text: '* **У вашій кімнаті:** Зробіть цю вправу саме з трьома речами у вашій кімнаті:
    «Кімната біла», «Стіл коричневий», «Крісло сіре».'
- find: This first conversation features Natalka selecting flowers for a special event.
    She speaks with a seller to find the perfect combination of bright spring colors.
  replace: 'Завдання перед діалогом: знайти три відповіді на `Якого кольору?`, виписати
    одну форму множини, потім повторити діалог з іншими назвами квітів.'
- find: '<!-- INJECT_ACTIVITY: quiz-what-color -->'
  replace: '### Вправа: `Якого кольору?` 1. олівець — `Червоний.` 2. сукня — `Чорна.`
    3. вікно — `Біле.` 4. Далі: дати свою коротку відповідь для слів `светр`, `книга`,
    `листя`.'
- find: '<!-- INJECT_ACTIVITY: fill-in-color-agreement -->'
  replace: '### Вправа: Заповнити форму кольору. 1. син__ книга 2. червон__ стіл 3.
    біл__ вікно 4. сір__ пальто 5. зелен__ квіти.'
- find: '<!-- INJECT_ACTIVITY: quiz-blue-vs-lightblue -->'
  replace: '### Вправа: `Синій` чи `блакитний`? 1. небо 2. море 3. чорнило 4. прапор.
    Після вибору сказати повне речення: `Небо блакитне.`'
- find: '<!-- INJECT_ACTIVITY: match-up-appearance -->'
  replace: '### Вправа: Зіставити вираз і контекст. 1. `карі очі` 2. `русяве волосся`
    3. `сиве волосся` A. людина старшого віку B. світло-коричневе волосся C. brown
    eyes.'
- find: '<!-- INJECT_ACTIVITY: group-sort-hard-soft -->'
  replace: '### Вправа: Розподілити слова на дві групи. Тверда група: `червоний`,
    `жовтий`, `зелений`, `білий`, `чорний`, `сірий`, `блакитний`. М''яка група: `синій`.'
- find: Діалог на ринку часто вимагає чітких та коротких відповідей.
  replace: 'Вправа: дати три короткі відповіді без повного речення. `троянди? — Червоні.`
    `лілії? — Білі.` `листя? — Зелене.`'
- find: This first conversation features Natalka selecting flowers for a special event.
    She speaks with a seller to find the perfect combination of bright spring colors.
  replace: У першому діалозі Наталка вибирає квіти для букета й питає про їхній колір.
- find: The phrase «мені подобаються» is a ready-made expression for personal preferences.
    The adjective in «жовті соняшники» explicitly uses the plural ending, and такі
    форми використовуються naturally in conversation.
  replace: Вислів «мені подобаються» краще запам'ятати як готову мовну модель. У словосполученні
    «жовті соняшники» маємо форму множини, і в живому мовленні вона звучить природно.
- find: When asking about the color of an object in Ukrainian, we use the phrase якого
    кольору? (what color?). In natural speech, the immediate response is often just
    the adjective. This provides a clear short відповідь before building a full sentence.
  replace: 'Коли питаємо про колір, уживаємо формулу «Якого кольору?». У відповіді
    часто досить одного слова: «Червоний», «Червона», «Біле».'
- find: We will look at 12 базових кольорів, podілених на дві групи за типами прикметників.
    Most of these belong to the hard group. Ця Тверда група follows the exact same
    `-ий/-а/-е/-і` gender agreement pattern you already know.
  replace: Розгляньмо 12 базових кольорів. Більшість із них належить до твердої групи
    й змінюється за зразком `-ий/-а/-е/-і`.
- find: 'В українській мові ми активно вчимо пару слів для цього кольору: «синій»
    та «блакитний».'
  replace: 'В українській мові розрізняємо дві назви цього кольору: «синій» і «блакитний».'
- find: To master the vocabulary in this lesson, you must apply the grammar concepts
    from a previous module («модуль»).
  replace: Щоб упевнено вживати ці слова, повторімо узгодження прикметників із іменниками.
- find: Your primary tool for communication is the question «Якого кольору...?». The
    base noun «колір» is masculine, but it changes form here.
  replace: 'Головна мовна формула цього модуля — «Якого кольору...?». Після неї зазвичай
    відповідаємо коротко: «зелений», «біла», «сіре».'
- find: '— **Наталка:** А ці квіти? Якого вони кольору? *(And these flowers? What
    color are they?)*

    > — **Продавець:** Це білі лілії. Вони дуже свіжі. *(These are white lilies. They
    are very fresh.)*'
  replace: '— **Наталка:** Якого кольору ці лілії? *(What color are these lilies?)*

    > — **Продавець:** Білі. *(White.)*'
- find: '— **Продавець:** Чудово! У вас є синя ваза для них? *(Wonderful! Do you have
    a blue vase for them?)*

    > — **Наталка:** Так. Додайте ще зелене листя, будь ласка. *(Yes. Add some green
    leaves, please.)*'
  replace: '— **Продавець:** Чудово. Добре, загорнути букет? *(Wonderful. Shall I
    wrap the bouquet?)*

    > — **Наталка:** Так, будь ласка. Додайте ще зелене листя. *(Yes, please. Add
    some green leaves too.)*'
- find: '— **Дмитро:** Який одяг ти шукаєш? *(What clothes are you looking for?)*

    > — **Ліза:** Мені потрібна чорна сукня. А ти? *(I need a black dress. And you?)*

    > — **Дмитро:** Цей білий светр і коричневі черевики. *(This white sweater and
    brown shoes.)*

    > — **Ліза:** Надворі холодно. Тобі треба сіре пальто. *(It is cold outside. You
    need a grey coat.)*'
  replace: '— **Дмитро:** Якого кольору сукня для вечірки? *(What color is the dress
    for the party?)*

    > — **Ліза:** Чорна. А твій светр? *(Black. And your sweater?)*

    > — **Дмитро:** Білий. А черевики коричневі. *(White. And the shoes are brown.)*

    > — **Ліза:** Добре. Пальто сіре. *(Good. The coat is grey.)*'
- find: This first conversation features Natalka selecting flowers for a special event.
    She speaks with a seller to find the perfect combination of bright spring colors.
  replace: ''
- find: Next, Dmytro and Liza are putting together an outfit from a friend's wardrobe.
    They also share a brief physical description to help recognize a guest.
  replace: ''
- find: This first conversation features Natalka selecting flowers for a special event.
    She speaks with a seller to find the perfect combination of bright spring colors.
  replace: 'This first conversation shows Natalka choosing flowers at a market. <!--
    VERIFY: if ''special event'' or ''bright spring colors'' is intended, cite the
    source -->'
- find: За мотивами вірша про сонце, мені подобаються жовті соняшники.
  replace: 'За мотивами вірша про кольори, мені подобаються жовті соняшники. <!--
    VERIFY: if the source is specifically a poem about the sun, cite it -->'
- find: Adjectives in Ukrainian are strictly divided into these hard and soft groups.
    Learning «синій» now prepares you for other soft adjectives later.
  replace: 'For this module, it is enough to contrast the hard pattern with the soft
    pattern in «синій». <!-- VERIFY: if making a broader rule about all Ukrainian
    adjectives, cite an authority -->'
- find: You must use «карі очі» for brown eyes, rather than the basic adjective. When
    describing hair, always use «русяве волосся» for light-brown hair and «сиве волосся»
    for grey hair. These combinations are not literal translations, but they are exactly
    how native speakers talk.
  replace: 'At A1, prefer the ready-made chunks «карі очі», «русяве волосся», and
    «сиве волосся». <!-- VERIFY: avoid categorical ''must/always/exactly how native
    speakers talk'' unless cited -->'
- find: '> — **Наталка:** За мотивами вірша про сонце, мені подобаються жовті соняшники.
    *(Inspired by a poem about the sun, I like yellow sunflowers.)*'
  replace: '> — **Наталка:** Мені подобаються жовті соняшники. *(I like the yellow
    sunflowers.)*'
- find: '> — **Продавець:** Чудово! У вас є синя ваза для них? *(Wonderful! Do you
    have a blue vase for them?)*

    > — **Наталка:** Так. Додайте ще зелене листя, будь ласка. *(Yes. Add some green
    leaves, please.)*'
  replace: '> — **Продавець:** Чудово! Додати ще зелене листя? *(Wonderful! Shall
    I add some green leaves?)*

    > — **Наталка:** Так, будь ласка. У мене є синя ваза. *(Yes, please. I have a
    blue vase.)*'
- find: '> — **Дмитро:** Цей білий светр і коричневі черевики. *(This white sweater
    and brown shoes.)*'
  replace: '> — **Дмитро:** Шукаю білий светр і коричневі черевики. *(I''m looking
    for a white sweater and brown shoes.)*'
</fixes>
