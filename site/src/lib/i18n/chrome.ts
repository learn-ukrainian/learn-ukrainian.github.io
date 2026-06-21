/**
 * Chrome Locale Runtime — interface (chrome) strings only.
 *
 * Per ADR docs/decisions/2026-06-21-chrome-locale-runtime-i18n.md and issue #3671.
 *
 * SCOPE BOUNDARY (immersion rule #M-13): this dictionary holds ONLY navigation /
 * UI chrome strings — the scaffolding that lets a learner operate the site. It
 * MUST NOT contain teaching content, dialogue, vocab glosses, primary-source
 * texts, work titles, author names, genre headers, lemmas, or attributions —
 * those are authored Ukrainian and stay Ukrainian regardless of this toggle.
 *
 * Default for this track (l2-uk-en = "Ukrainian for English speakers"): chrome
 * follows the user's own browser locale; English is the no-JS / non-`uk` fallback
 * so absolute beginners can navigate. Ukrainian chrome is auto-selected only for
 * `uk*` browsers, or chosen explicitly via the toggle. The LEARNING CONTENT is
 * always Ukrainian — this toggle never touches it.
 */

export type ChromeLocale = 'uk' | 'en';

/** No-JS / non-Ukrainian-browser fallback. See ADR "Default language". */
export const DEFAULT_CHROME_LOCALE: ChromeLocale = 'en';

export const CHROME_LOCALE_STORAGE_KEY = 'lu-chrome-locale';

// English is the source-of-truth key set (`as const` gives the ChromeKey union).
const en = {
  // Global nav / header / footer
  'nav.home': 'Home',
  'nav.a1': 'A1',
  'nav.a2': 'A2',
  'nav.b1': 'B1 Preview',
  'nav.atlas': 'Word Atlas',
  'nav.readings': 'Reading reference',
  'nav.search': 'Search',
  'nav.github': 'GitHub',
  'nav.menu': 'Menu',
  'a11y.skip': 'Skip to content',
  'sidebar.lessons': 'Lessons',
  'sidebar.levelNav': 'Lessons in this level',
  'footer.courseHeading': 'Course',
  'footer.externalHeading': 'External',
  'footer.mission1':
    'Self-study is welcome here, but the best learning happens with trained native Ukrainian teachers. These materials support practice; they do not replace devoted teachers.',
  'footer.mission2':
    'Pedagogical inspiration comes in part from Ukrainian Lessons and the public teaching work of Anna Ohoiko, with gratitude for inspiration and help. Course content here is independently written: it is not copied from ULP or Anna Ohoiko-authored books and does not imply formal endorsement.',

  // Generic labels
  'label.previous': 'Previous',
  'label.next': 'Next',
  'label.preview': 'PREVIEW',
  'label.module': 'Module',
  'label.lesson': 'Lesson',

  // Hero / landing stats
  'stats.modules': 'modules',
  'stats.targetWords': 'target words',
  'stats.hours': 'hours',
  'progress.title': 'Your Progress',
  'progress.buildStatus': 'Build Status',
  'progress.completed': 'completed',
  'progress.of': 'of',
  'status.available': 'available',
  'status.planned': 'planned',
  'status.reviewed': 'reviewed',
  'group.modules': 'Modules',
  'planned.unit': 'planned modules',
  'planned.title': 'Planned module',
  'planned.sub': 'Mapped curriculum slot; not released for study yet.',

  // CEFR badge descriptors
  'badge.beginner': 'Beginner',
  'badge.elementary': 'Elementary',
  'badge.intermediate': 'Intermediate',
  'badge.upperIntermediate': 'Upper-Intermediate',
  'badge.advanced': 'Advanced',
  'badge.mastery': 'Mastery',

  // Homepage
  'home.heroStart': 'Start Learning (A1)',
  'home.heroViewLevels': 'View All Levels',
  'home.featTheoryT': 'Theory-First Approach',
  'home.featTheoryD':
    'Deep grammar explanations, cultural context, and historical insights. Understand the why behind the language.',
  'home.featInteractiveT': 'Interactive Activities',
  'home.featInteractiveD':
    'Quizzes, matching exercises, fill-in-the-blank, and more. Practice what you learn with engaging activities.',
  'home.featCultureT': 'Cultural Immersion',
  'home.featCultureD':
    'Authentic materials, folklore, literature, and a decolonization lens. Learn Ukrainian in its full cultural context.',
  'home.featPathwayT': 'Complete A1–C2 Pathway',
  'home.featPathwayD': 'From absolute beginner to native-level proficiency.',
  'home.featPathwayModules': 'modules aligned with CEFR and Ukrainian State Standards.',
  'home.secCoreLevels': 'Core Levels',
  'home.secSpecTracks': 'Specialization Tracks',
  'home.secSeminars': 'Linguistic Seminars',
  'home.secSeminarsSub': 'Advanced historical linguistics for scholars and enthusiasts',
  'home.ctaTitle': 'Ready to Start?',
  'home.ctaBody': 'Begin your Ukrainian journey today with our comprehensive curriculum.',
  'home.ctaBtn': 'Start with A1',

  // Level card names (core)
  'level.a1.name': 'Beginner',
  'level.a1.desc': 'Cyrillic alphabet, basic phrases, practical scenarios',
  'level.a2.name': 'Elementary',
  'level.a2.desc': 'All 7 cases, verb aspects, practical scenarios',
  'level.b1.name': 'Intermediate',
  'level.b1.desc': 'Aspect mastery, motion verbs, communication skills',
  'level.b2.name': 'Upper-Intermediate',
  'level.b2.desc': 'Passive voice, registers, professional basics',
  'level.c1.name': 'Advanced',
  'level.c1.desc': 'Stylistics, literature, complex grammar',
  'level.c2.name': 'Mastery',
  'level.c2.desc': 'Native-level proficiency',
  // Level card names (specialization)
  'level.hist.name': 'History',
  'level.hist.desc': 'Ukrainian history from origins to present',
  'level.istorio.name': 'Historiography',
  'level.istorio.desc': 'Primary sources, imperial mechanisms, interethnic relations',
  'level.bio.name': 'Biographies',
  'level.bio.desc': 'Notable Ukrainians through history',
  'level.b2pro.name': 'Professional',
  'level.b2pro.desc': 'Business communication, technical domains',
  'level.c1pro.name': 'Professional Mastery',
  'level.c1pro.desc': 'Executive, academic, specialized',
  'level.lit.name': 'Literature',
  'level.lit.desc': 'Ukrainian classics and literary analysis',
  'level.folk.name': 'Folklore',
  'level.folk.desc':
    'Decolonized survey of Ukrainian folk culture — song, ritual, epic, prose, material culture',
  'level.oes.name': 'Old East Slavic',
  'level.oes.desc': "Language of Kyivan Rus' (X–XIII century)",
  'level.ruth.name': 'Ruthenian',
  'level.ruth.desc': 'Middle Ukrainian (XIV–XVIII century)',

  // Search page
  'search.eyebrow': 'Find a page',
  'search.subtitle': 'Static client-side search for lessons, tracks, Word Atlas entries, and references.',
  'search.label': 'Search lessons, tracks, and reference pages',
  'search.placeholder': 'Try gender, колядки, вікно, etymology…',
  'search.loadingCode': 'Loading',
  'search.loadingBody': 'Preparing the local index.',
  'search.errorCode': 'Error',
  'search.errorTitle': 'Search could not run.',
  'search.errorBody':
    'The static page is still available. Use the course links below while the search script recovers.',
  'search.emptyCode': 'No Results',
  'search.emptyTitle': 'No matching pages.',
  'search.emptyBody':
    'Try a broader term, a Ukrainian lemma, or open A1, B1 Preview, Word Atlas, or Etymology directly.',
  'search.suggested': 'Suggested Pages',
  'search.hint': 'Start with a broad query or use the shortcuts.',

  // Route-state / 404 cards
  'state.eyebrow': 'Learner state',
  'state.subtitle':
    'A clear route state keeps learners oriented instead of dropping them into a generic docs page.',
  'state.notFoundTitle': 'This page is not part of the public learner UI.',
  'state.notFoundBody':
    'The route may be hidden, not published, or not generated yet. Use an available course surface instead of guessing around draft paths.',
  'state.missingTitle': 'The route exists, but the lesson content is not ready.',
  'state.missingBody':
    'Learners should get a plain explanation and a path back to an available track.',
  'state.emptyTitle': 'The reference template has an empty state.',
  'state.emptyBody':
    'Atlas and reference indexes should communicate when a filter or future dataset has no records.',

  // Lesson companion rail
  'companion.coreCode': 'Core lesson',
  'companion.seminarCode': 'Seminar',
  'companion.coreTitle': 'Learner Path',
  'companion.seminarTitle': 'Source-Heavy Reading',
  'companion.coreBody':
    'Use the lesson tab first, then vocabulary, activities, and resources. Dialogue and tables are styled for repeated practice.',
  'companion.seminarBody':
    'Read for evidence, context, and interpretation. Source notes and workbook tasks stay visible as part of the seminar frame.',

  // Readings (Хрестоматія) landing
  'readings.eyebrow': 'Reference · Primary sources',
  'readings.subtitle':
    'The full original texts the seminars teach from. Lessons study excerpts and link here for the complete work.',
  'readings.intro':
    'A reference library of primary sources — the complete original texts the seminars study in excerpts. Every text is public domain, reproduced verbatim with its source cited. Lessons in any track link here for the full work.',
  'readings.searchLabel': 'Search the reading reference',
  'readings.searchPlaceholder': 'Search a text, genre, or author…',
  'readings.empty': 'No matches. Try another word.',
} as const;

export type ChromeKey = keyof typeof en;

// Ukrainian must cover every ChromeKey — a missing key is a compile error.
const uk: Record<ChromeKey, string> = {
  'nav.home': 'Головна',
  'nav.a1': 'A1',
  'nav.a2': 'A2',
  'nav.b1': 'B1 (анонс)',
  'nav.atlas': 'Атлас слів',
  'nav.readings': 'Хрестоматія',
  'nav.search': 'Пошук',
  'nav.github': 'GitHub',
  'nav.menu': 'Меню',
  'a11y.skip': 'Перейти до вмісту',
  'sidebar.lessons': 'Уроки',
  'sidebar.levelNav': 'Уроки цього рівня',
  'footer.courseHeading': 'Курс',
  'footer.externalHeading': 'Зовнішні ресурси',
  'footer.mission1':
    'Самостійне навчання тут вітається, але найкраще воно відбувається з кваліфікованими вчителями — носіями української мови. Ці матеріали підтримують практику, проте не заміняють відданих учителів.',
  'footer.mission2':
    'Педагогічне натхнення частково походить від Ukrainian Lessons і публічної викладацької праці Анни Огойко — із вдячністю за натхнення та допомогу. Зміст курсу тут написано незалежно: його не скопійовано з ULP чи книжок авторства Анни Огойко, і він не означає офіційного схвалення.',

  'label.previous': 'Назад',
  'label.next': 'Далі',
  'label.preview': 'АНОНС',
  'label.module': 'Модуль',
  'label.lesson': 'Урок',

  'stats.modules': 'модулів',
  'stats.targetWords': 'цільових слів',
  'stats.hours': 'годин',
  'progress.title': 'Ваш прогрес',
  'progress.buildStatus': 'Стан збірки',
  'progress.completed': 'завершено',
  'progress.of': 'з',
  'status.available': 'доступно',
  'status.planned': 'заплановано',
  'status.reviewed': 'перевірено',
  'group.modules': 'Модулі',
  'planned.unit': 'заплановані модулі',
  'planned.title': 'Запланований модуль',
  'planned.sub': 'Передбачений слот у програмі; ще не випущено для навчання.',

  'badge.beginner': 'Початковий',
  'badge.elementary': 'Базовий',
  'badge.intermediate': 'Середній',
  'badge.upperIntermediate': 'Вище середнього',
  'badge.advanced': 'Просунутий',
  'badge.mastery': 'Досконалість',

  'home.heroStart': 'Почати навчання (A1)',
  'home.heroViewLevels': 'Усі рівні',
  'home.featTheoryT': 'Підхід «теорія передусім»',
  'home.featTheoryD':
    'Глибокі пояснення граматики, культурний контекст та історичні відомості. Зрозумійте, чому мова саме така.',
  'home.featInteractiveT': 'Інтерактивні завдання',
  'home.featInteractiveD':
    'Тести, завдання на відповідність, заповнення пропусків та інше. Закріплюйте вивчене цікавими вправами.',
  'home.featCultureT': 'Культурне занурення',
  'home.featCultureD':
    'Автентичні матеріали, фольклор, література та деколонізаційна оптика. Вивчайте українську в її повному культурному контексті.',
  'home.featPathwayT': 'Повний шлях A1–C2',
  'home.featPathwayD': 'Від абсолютного початківця до рівня носія мови.',
  'home.featPathwayModules': 'модулів за CEFR і Державним стандартом України.',
  'home.secCoreLevels': 'Основні рівні',
  'home.secSpecTracks': 'Спеціалізовані напрями',
  'home.secSeminars': 'Мовознавчі семінари',
  'home.secSeminarsSub': 'Поглиблена історична лінгвістика для науковців та ентузіастів',
  'home.ctaTitle': 'Готові почати?',
  'home.ctaBody': 'Розпочніть свою українську подорож сьогодні з нашою повною програмою.',
  'home.ctaBtn': 'Почати з A1',

  'level.a1.name': 'Початковий',
  'level.a1.desc': 'Кирилиця, базові фрази, практичні ситуації',
  'level.a2.name': 'Базовий',
  'level.a2.desc': 'Усі 7 відмінків, види дієслів, практичні ситуації',
  'level.b1.name': 'Середній',
  'level.b1.desc': 'Опанування виду, дієслова руху, навички спілкування',
  'level.b2.name': 'Вище середнього',
  'level.b2.desc': 'Пасивний стан, регістри, основи професійного мовлення',
  'level.c1.name': 'Просунутий',
  'level.c1.desc': 'Стилістика, література, складна граматика',
  'level.c2.name': 'Досконалість',
  'level.c2.desc': 'Володіння на рівні носія',
  'level.hist.name': 'Історія',
  'level.hist.desc': 'Історія України від витоків до сьогодення',
  'level.istorio.name': 'Історіографія',
  'level.istorio.desc': 'Першоджерела, імперські механізми, міжетнічні відносини',
  'level.bio.name': 'Біографії',
  'level.bio.desc': 'Видатні українці в історії',
  'level.b2pro.name': 'Професійний',
  'level.b2pro.desc': 'Ділове спілкування, технічні галузі',
  'level.c1pro.name': 'Професійна досконалість',
  'level.c1pro.desc': 'Керівне, академічне, спеціалізоване мовлення',
  'level.lit.name': 'Література',
  'level.lit.desc': 'Українська класика та літературний аналіз',
  'level.folk.name': 'Фольклор',
  'level.folk.desc':
    'Деколонізований огляд української народної культури — пісня, обряд, епос, проза, матеріальна культура',
  'level.oes.name': 'Давня східнослов’янська',
  'level.oes.desc': 'Мова Київської Русі (X–XIII ст.)',
  'level.ruth.name': 'Руська',
  'level.ruth.desc': 'Середньоукраїнська мова (XIV–XVIII ст.)',

  'search.eyebrow': 'Знайти сторінку',
  'search.subtitle': 'Статичний пошук на боці клієнта — уроки, напрями, статті Атласу слів і довідники.',
  'search.label': 'Шукайте уроки, напрями та довідкові сторінки',
  'search.placeholder': 'Спробуйте: рід, колядки, вікно, етимологія…',
  'search.loadingCode': 'Завантаження',
  'search.loadingBody': 'Готуємо локальний покажчик.',
  'search.errorCode': 'Помилка',
  'search.errorTitle': 'Пошук не вдалося запустити.',
  'search.errorBody':
    'Статична сторінка все одно доступна. Скористайтеся посиланнями на курси нижче, поки пошук відновлюється.',
  'search.emptyCode': 'Немає результатів',
  'search.emptyTitle': 'Немає відповідних сторінок.',
  'search.emptyBody':
    'Спробуйте загальніший запит, українську лему або відкрийте A1, B1 (анонс), Атлас слів чи Етимологію напряму.',
  'search.suggested': 'Рекомендовані сторінки',
  'search.hint': 'Почніть із загального запиту або скористайтеся посиланнями.',

  'state.eyebrow': 'Стан сторінки',
  'state.subtitle':
    'Чіткий стан маршруту тримає учня зорієнтованим, а не кидає його на загальну сторінку документації.',
  'state.notFoundTitle': 'Цієї сторінки немає в публічному інтерфейсі курсу.',
  'state.notFoundBody':
    'Маршрут може бути прихованим, неопублікованим або ще не згенерованим. Скористайтеся доступним розділом курсу замість здогадок про чернеткові шляхи.',
  'state.missingTitle': 'Маршрут існує, але вміст уроку ще не готовий.',
  'state.missingBody':
    'Учень має отримати просте пояснення і шлях назад до доступного напряму.',
  'state.emptyTitle': 'Довідковий шаблон має порожній стан.',
  'state.emptyBody':
    'Атлас і довідкові покажчики мають повідомляти, коли фільтр чи майбутній набір даних не має записів.',

  'companion.coreCode': 'Базовий урок',
  'companion.seminarCode': 'Семінар',
  'companion.coreTitle': 'Шлях учня',
  'companion.seminarTitle': 'Читання з джерелами',
  'companion.coreBody':
    'Спочатку вкладка уроку, далі лексика, завдання та ресурси. Діалоги й таблиці оформлено для повторюваної практики.',
  'companion.seminarBody':
    'Читайте задля свідчень, контексту й інтерпретації. Примітки до джерел і завдання робочого зошита лишаються видимими як частина семінарської рамки.',

  'readings.eyebrow': 'Довідник · Першоджерела',
  'readings.subtitle':
    'Повні оригінальні тексти, з яких викладають семінари. Уроки опрацьовують уривки й посилаються сюди на повний твір.',
  'readings.intro':
    'Довідкова бібліотека першоджерел — повні оригінальні тексти, які семінари вивчають уривками. Кожен текст у суспільному надбанні, відтворений дослівно із зазначеним джерелом. Уроки будь-якого напряму посилаються сюди на повний твір.',
  'readings.searchLabel': 'Шукати у хрестоматії',
  'readings.searchPlaceholder': 'Шукайте текст, жанр або автора…',
  'readings.empty': 'Немає збігів. Спробуйте інше слово.',
};

export const CHROME_STRINGS = { en, uk } satisfies Record<ChromeLocale, Record<ChromeKey, string>>;

/** Both locale variants for a key — used by ChromeText for FOUC-safe dual-render. */
export function chromeBoth(key: ChromeKey): Record<ChromeLocale, string> {
  return { en: CHROME_STRINGS.en[key], uk: CHROME_STRINGS.uk[key] };
}
