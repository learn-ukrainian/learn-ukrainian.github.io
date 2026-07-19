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
  'nav.b1': 'B1',
  'nav.b2': 'B2',
  'nav.dailyWords': 'Words of the Day',
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
  'label.reference': 'Reference',
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
  'status.released': 'Released',
  'status.preview': 'Preview',
  'status.longRange': 'Long-range',
  'status.plannedSeminar': 'Planned seminar',
  'status.previewLive': 'Preview · 3 of 42 live',
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

  // Homepage index.astro (real route `/`)
  'home.eyebrow': 'Course ladder and reference tools',
  'home.introHeading': 'Start with A1. Continue through A2 and B1. Move into B2 when you are ready.',
  'home.introBody':
    'The released course path is A1, then A2, then B1, then B2. B2 is open for upper-intermediate study while additional evaluator review continues separately. Word Atlas supports the course as a reference tool, not as a separate course track. Seminar tracks are listed for context, but they are not public entry points yet.',
  'home.actionStartA1': 'Start A1',
  'home.actionOpenB1Preview': 'Open B1',
  'home.actionOpenB2': 'Open B2',
  'home.roadmapA1': 'Released beginner course',
  'home.roadmapA2': 'Released continuation course',
  'home.roadmapB1': 'Released intermediate course',
  'home.roadmapB2': 'Released upper-intermediate course',
  'home.roadmapAtlasDesc': 'Reference tool',
  'home.roadmapSeminars': 'Seminars',
  'home.roadmapSeminarsNote': 'Not promoted yet',
  'home.availableNow': 'Available Now',
  'home.cardA1Desc':
    '55 modules for sounds, reading, first conversations, everyday needs, and an A1 finale.',
  'home.cardA2Desc':
    '69 modules take learners from the A2 bridge through everyday situations, cases, aspect, and the A2 finale.',
  'home.cardB1Desc':
    '94 released modules take learners through Ukrainian-led intermediate grammar, communication, checkpoints, and a B1 practice exam.',
  'home.cardB2Desc':
    '93 released modules cover advanced syntax, register, professional communication, lexicology, and the B2 final exam.',
  'home.cardAtlasDesc':
    'A learner reference that goes beyond a lexicon: meanings, morphology, usage, etymology where available, and course links.',
  'home.cardReadingsDesc':
    'A searchable library of full primary-source texts that any seminar links into for close reading. Public-domain, verbatim, and sourced.',
  'home.courseMapHeading': 'Course Map',
  'home.courseMapBody':
    'This map separates released courses, preview work, and future inventory. The recommended learner path is A1 first, then A2, then B1, then B2. Seminar tracks are shown for context only and are not promoted as learner entry points yet.',
  'home.courseLadder': 'Course Ladder',
  'home.seminarTracks': 'Seminar Tracks',
  'home.track.beginner': 'Beginner Course',
  'home.track.preIntermediate': 'Pre-Intermediate Course',
  'home.track.intermediate': 'Intermediate Course',
  'home.track.intermediatePreview': 'Intermediate Course',
  'home.track.upperIntermediate': 'Upper-Intermediate Course',
  'home.track.advanced': 'Advanced Course',
  'home.track.mastery': 'Mastery Course',
  'home.seminar.folk': 'Folklore & Oral Tradition',
  'home.seminar.hist': 'History Of Ukraine',
  'home.seminar.lit': 'Ukrainian Literature',
  'home.seminar.litEssay': 'Essays',
  'home.seminar.litHistFic': 'Historical Fiction',
  'home.seminar.litFantastika': 'Fantastika',
  'home.seminar.litWar': 'War Literature',
  'home.seminar.litHumor': 'Humor',
  'home.seminar.litYouth': 'Youth Literature',
  'home.seminar.litDrama': 'Drama',
  'home.seminar.ruth': 'Ruthenian Baroque',

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
    'Try a broader term, a Ukrainian lemma, or open A1, B1, B2, Word Atlas, or Etymology directly.',
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

  // Practice dashboard (K3 redesign)
  'practice.title': 'Practice',
  'practice.heroTitle': 'Practice Ukrainian',
  'practice.heroSubtitle': 'Daily set',
  'practice.start': 'Start',
  'practice.resume': 'Resume',
  'practice.restart': 'Restart',
  'practice.next': 'Next',
  'practice.showWords': 'Show words',
  'practice.hideWords': 'Hide words',
  'practice.statusDue': 'Due',
  'practice.statusNew': 'New',
  'practice.statusDone': 'Done',
  'practice.streak': 'Streak',
  'practice.tapToFlip': 'Tap to flip',
  'practice.rateRecall': 'Rate how easy it was to recall',
  'practice.openInAtlas': 'Open in Atlas',
  'practice.level': 'Level',
  'practice.modesTitle': 'Modes',
  'practice.focusTitle': 'Focus',
  'practice.stats': 'Stats',
  'practice.score': 'Score',
  'practice.nextDue': 'Next due',
  'practice.voiceSlot': 'Voice practice coming soon',
  'practice.c2Soon': 'C2 · soon',
  'practice.mixedDetail': 'Mixed practice',
  'practice.sessionTitle': 'Session',
  'practice.sessionSizeLabel': 'Session size',
  'practice.sessionStart': 'Start session',
  'practice.sessionResume': 'Resume session',
  'practice.sessionSize10': '10',
  'practice.sessionSize20': '20',
  'practice.sessionSizeUntilZero': 'Until clear',
  'practice.rail.source': 'Source',
  'practice.rail.actual': 'Your answer',
  'practice.verdict.correct': 'Correct',
  'practice.verdict.wrong': 'Wrong',
  'practice.verdict.calque': 'Calque',
  'practice.wordsTitle': 'Words of the day',

  // Practice session chrome residuals (#5355)
  'practice.sessionComplete': 'Session complete',
  'practice.sessionProgress': 'Session',
  'practice.focusPractice': 'Focus practice:',
  'practice.clearFocus': 'Clear focus ×',
  'practice.loading': 'Loading…',
  'practice.home': '← Home',
  'practice.noCards': 'No cards to practice yet.',
  'practice.nextArrow': 'Next →',
  'practice.clozePreparing': 'Cloze exercises for this level are still being prepared. Try flashcards, matching, or multiple choice.',
  'practice.heritagePreparing': 'Heritage exercises for this level are still being prepared.',
  'practice.paronymPreparing': 'Paronym exercises for this level are still being prepared.',
  'practice.allCaughtUp': 'All cards are reviewed for now.',
  'practice.noMatchCards': 'No cards available for matching right now.',
  'practice.noChoiceCards': 'No cards available for multiple choice right now.',
  'practice.chooseCorrect': 'Choose the correct answer',
  'practice.chooseParonym': 'Choose the correct paronym.',
  'practice.openInAtlasTab': 'Open in Atlas (new tab)',
  'practice.openInAtlasArrow': 'Open in Atlas →',
  'practice.chooseNative': 'Choose the native Ukrainian word.',
  'practice.sentenceWith': 'Sentence with',
  'practice.check': 'Check',
  'practice.clozeOptionsFailed': 'Cloze options failed validation.',
  'practice.sourcePrefix': 'Source:',
  'practice.orChoose': 'Or choose',

  // Word Atlas entry chrome (#5435 reverse habit loop)
  'atlas.practiceThisWord': 'Practice this word →',
  'atlas.practiceUnavailable': 'Not in the practice pool yet',
} as const;

export type ChromeKey = keyof typeof en;

// Ukrainian must cover every ChromeKey — a missing key is a compile error.
const uk: Record<ChromeKey, string> = {
  'nav.home': 'Головна',
  'nav.a1': 'A1',
  'nav.a2': 'A2',
  'nav.b1': 'B1',
  'nav.b2': 'B2',
  'nav.dailyWords': 'Слова дня',
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
  'label.reference': 'Довідник',
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
  'status.released': 'Випущено',
  'status.preview': 'Анонс',
  'status.longRange': 'Довгостроково',
  'status.plannedSeminar': 'Запланований семінар',
  'status.previewLive': 'Анонс · 3 з 42 доступні',
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

  'home.eyebrow': 'Драбина курсу та довідкові інструменти',
  'home.introHeading': 'Почніть з A1. Продовжіть A2 і B1. Переходьте до B2, коли будете готові.',
  'home.introBody':
    'Випущений шлях курсу — A1, потім A2, потім B1, потім B2. B2 відкритий для навчання на рівні вище середнього, а додаткова експертна оцінка триває окремо. Атлас слів підтримує курс як довідковий інструмент, а не як окремий навчальний напрям. Семінарські напрями подано для контексту, але вони ще не є публічними точками входу.',
  'home.actionStartA1': 'Почати A1',
  'home.actionOpenB1Preview': 'Відкрити B1',
  'home.actionOpenB2': 'Відкрити B2',
  'home.roadmapA1': 'Випущений початковий курс',
  'home.roadmapA2': 'Випущений курс-продовження',
  'home.roadmapB1': 'Випущений середній курс',
  'home.roadmapB2': 'Випущений курс вище середнього рівня',
  'home.roadmapAtlasDesc': 'Довідковий інструмент',
  'home.roadmapSeminars': 'Семінари',
  'home.roadmapSeminarsNote': 'Ще не просувається',
  'home.availableNow': 'Доступно зараз',
  'home.cardA1Desc':
    '55 модулів про звуки, читання, перші розмови, повсякденні потреби та фінал A1.',
  'home.cardA2Desc':
    '69 модулів ведуть учнів від містка A2 через повсякденні ситуації, відмінки, вид і фінал A2.',
  'home.cardB1Desc':
    '94 випущені модулі ведуть учнів через середню граматику, комунікацію, контрольні точки та пробний екзамен B1 українською.',
  'home.cardB2Desc':
    '93 випущені модулі охоплюють складний синтаксис, регістри, професійну комунікацію, лексикологію та фінальний іспит B2.',
  'home.cardAtlasDesc':
    'Довідник для учня, що виходить за межі словника: значення, морфологія, вживання, етимологія за наявності та посилання на курс.',
  'home.cardReadingsDesc':
    'Пошукова бібліотека повних текстів першоджерел, на які посилається будь-який семінар для детального читання. У суспільному надбанні, дослівно, із зазначеним джерелом.',
  'home.courseMapHeading': 'Карта програми',
  'home.courseMapBody':
    'Ця карта розділяє випущені курси, анонсовану роботу та майбутній інвентар. Рекомендований шлях учня — спочатку A1, потім A2, потім B1, потім B2. Семінарські напрями показано лише для контексту й не просуваються як точки входу для учнів.',
  'home.courseLadder': 'Драбина курсу',
  'home.seminarTracks': 'Семінарські напрями',
  'home.track.beginner': 'Початковий курс',
  'home.track.preIntermediate': 'Курс перед середнім рівнем',
  'home.track.intermediate': 'Середній курс',
  'home.track.intermediatePreview': 'Середній курс',
  'home.track.upperIntermediate': 'Курс вище середнього рівня',
  'home.track.advanced': 'Просунутий курс',
  'home.track.mastery': 'Курс досконалості',
  'home.seminar.folk': 'Фольклор і усна традиція',
  'home.seminar.hist': 'Історія України',
  'home.seminar.lit': 'Українська література',
  'home.seminar.litEssay': 'Есеї',
  'home.seminar.litHistFic': 'Історична белетристика',
  'home.seminar.litFantastika': 'Фантастика',
  'home.seminar.litWar': 'Військова література',
  'home.seminar.litHumor': 'Гумор',
  'home.seminar.litYouth': 'Молодіжна література',
  'home.seminar.litDrama': 'Драма',
  'home.seminar.ruth': 'Рутенське бароко',

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
    'Спробуйте загальніший запит, українську лему або відкрийте A1, B1, B2, Атлас слів чи Етимологію напряму.',
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

  // Practice dashboard (K3 redesign)
  'practice.title': 'Практика',
  'practice.heroTitle': 'Практикуйте українську',
  'practice.heroSubtitle': 'Щоденний набір',
  'practice.start': 'Почати',
  'practice.resume': 'Продовжити',
  'practice.restart': 'Спочатку',
  'practice.next': 'Далі',
  'practice.showWords': 'Показати слова',
  'practice.hideWords': 'Приховати слова',
  'practice.statusDue': 'На повторення',
  'practice.statusNew': 'Нові',
  'practice.statusDone': 'Вивчено',
  'practice.streak': 'Днів поспіль',
  'practice.tapToFlip': 'Натисніть, щоб перевернути',
  'practice.rateRecall': 'Оцініть, наскільки легко згадалось',
  'practice.openInAtlas': 'Відкрити в Атласі',
  'practice.level': 'Рівень',
  'practice.modesTitle': 'Режими',
  'practice.focusTitle': 'Фокус',
  'practice.stats': 'Статистика',
  'practice.score': 'Рахунок',
  'practice.nextDue': 'Наступне повторення',
  'practice.voiceSlot': 'Вимова — незабаром',
  'practice.c2Soon': 'C2 · скоро',
  'practice.mixedDetail': 'Змішана практика',
  'practice.sessionTitle': 'Заняття',
  'practice.sessionSizeLabel': 'Розмір заняття',
  'practice.sessionStart': 'Почати заняття',
  'practice.sessionResume': 'Продовжити заняття',
  'practice.sessionSize10': '10',
  'practice.sessionSize20': '20',
  'practice.sessionSizeUntilZero': 'Доки не закінчаться',
  'practice.rail.source': 'Джерело',
  'practice.rail.actual': 'Ваша відповідь',
  'practice.verdict.correct': 'Правильно',
  'practice.verdict.wrong': 'Неправильно',
  'practice.verdict.calque': 'Калька',
  'practice.wordsTitle': 'Слова дня',

  // Practice session chrome residuals (#5355)
  'practice.sessionComplete': 'Сесію завершено',
  'practice.sessionProgress': 'Сесія',
  'practice.focusPractice': 'Фокусне тренування:',
  'practice.clearFocus': 'Скинути фокус ×',
  'practice.loading': 'Завантажуємо…',
  'practice.home': '← Додому',
  'practice.noCards': 'Поки що немає карток для практики.',
  'practice.nextArrow': 'Далі →',
  'practice.clozePreparing': 'Вправи з пропусками для цього рівня ще готуються. Спробуйте флешкартки, добір пар або вибір.',
  'practice.heritagePreparing': 'Вправи зі спадщини для цього рівня ще готуються.',
  'practice.paronymPreparing': 'Вправи з паронімами для цього рівня ще готуються.',
  'practice.allCaughtUp': 'Усі картки на зараз повторено.',
  'practice.noMatchCards': 'Зараз немає карток для добору пар.',
  'practice.noChoiceCards': 'Зараз немає карток для вибору відповіді.',
  'practice.chooseCorrect': 'Оберіть правильну відповідь',
  'practice.chooseParonym': 'Оберіть правильний паронім.',
  'practice.openInAtlasTab': 'Відкрити в Атласі (нова вкладка)',
  'practice.openInAtlasArrow': 'Відкрити в Атласі →',
  'practice.chooseNative': 'Оберіть питоме українське слово.',
  'practice.sentenceWith': 'Речення з',
  'practice.check': 'Перевірити',
  'practice.clozeOptionsFailed': 'Варіанти для пропуску не пройшли перевірку.',
  'practice.sourcePrefix': 'Джерело:',
  'practice.orChoose': 'Або оберіть',

  // Word Atlas entry chrome (#5435 reverse habit loop)
  'atlas.practiceThisWord': 'Практикувати це слово →',
  'atlas.practiceUnavailable': 'Ще немає в наборі практики',
};

export const CHROME_STRINGS = { en, uk } satisfies Record<ChromeLocale, Record<ChromeKey, string>>;

/** Both locale variants for a key — used by ChromeText for FOUC-safe dual-render. */
export function chromeBoth(key: ChromeKey): Record<ChromeLocale, string> {
  return { en: CHROME_STRINGS.en[key], uk: CHROME_STRINGS.uk[key] };
}
