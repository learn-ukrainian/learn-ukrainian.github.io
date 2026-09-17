import { useEffect, useState } from 'react';

export type ChromeLocale = 'en' | 'uk';

/** Same storage key as CourseLayout.astro chrome-locale runtime (#3671). */
export const CHROME_LOCALE_STORAGE_KEY = 'lu-chrome-locale';

/** Dispatched on <html> when the УКР/ENG toggle flips (optional; dataset mutation also works). */
export const CHROME_LOCALE_EVENT = 'lu-chrome-locale';

export function readChromeLocale(): ChromeLocale {
  if (typeof document === 'undefined') return 'en';
  return document.documentElement.dataset.chromeLocale === 'uk' ? 'uk' : 'en';
}

/**
 * Live site chrome locale. Activity island chrome must follow the header
 * УКР/ENG toggle (`data-chrome-locale`), not the bake-time `isUkrainian={false}`
 * prop stamped into MDX.
 */
export function useChromeLocale(): ChromeLocale {
  const [locale, setLocale] = useState<ChromeLocale>(() => readChromeLocale());

  useEffect(() => {
    const el = document.documentElement;
    const sync = () => setLocale(readChromeLocale());
    sync();
    const obs = new MutationObserver(sync);
    obs.observe(el, { attributes: true, attributeFilter: ['data-chrome-locale'] });
    el.addEventListener(CHROME_LOCALE_EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      obs.disconnect();
      el.removeEventListener(CHROME_LOCALE_EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  return locale;
}

/**
 * Resolve activity chrome language. Live chrome locale wins over the legacy
 * MDX `isUkrainian` bake so the toggle actually switches button/step labels.
 */
export function useActivityIsUkrainian(_bakedProp?: boolean): boolean {
  return useChromeLocale() === 'uk';
}

/**
 * For A1 bilingual instruction strings authored as `UA — EN`, show the side
 * matching chrome locale. Plain single-language instructions pass through.
 */
export function chromeFacingBilingual(text: string | undefined, locale: ChromeLocale): string | undefined {
  if (!text) return text;
  const parts = text.split(/\s+—\s+/);
  if (parts.length < 2) return text;
  const ua = parts[0]?.trim() ?? '';
  const en = parts.slice(1).join(' — ').trim();
  if (!ua || !en) return text;
  const uaHasCyrillic = /[\u0400-\u04FF]/.test(ua);
  const enHasLatin = /[A-Za-z]/.test(en);
  if (!uaHasCyrillic || !enHasLatin) return text;
  return locale === 'uk' ? ua : en;
}
