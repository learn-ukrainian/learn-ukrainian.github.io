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
};

export const CHROME_STRINGS = { en, uk } satisfies Record<ChromeLocale, Record<ChromeKey, string>>;

/** Both locale variants for a key — used by ChromeText for FOUC-safe dual-render. */
export function chromeBoth(key: ChromeKey): Record<ChromeLocale, string> {
  return { en: CHROME_STRINGS.en[key], uk: CHROME_STRINGS.uk[key] };
}
