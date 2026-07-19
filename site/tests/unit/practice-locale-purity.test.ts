// @vitest-environment happy-dom
/**
 * Practice chrome locale purity (#5503 / #5376 family).
 *
 * Chrome must be one locale at a time (en | uk). A1 may keep English glosses
 * inside activity item content, but never slash-dual chrome labels.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';
import { CHROME_STRINGS, type ChromeKey } from '@site/src/lib/i18n/chrome';

const ROOT = process.cwd();

function readSrc(rel: string): string {
  return readFileSync(resolve(ROOT, rel), 'utf8');
}

const PRACTICE_SOURCES = [
  'src/components/LexiconPractice.tsx',
  'src/components/PracticeSessionSummary.tsx',
  'src/components/PracticeFlashcard.tsx',
  'src/components/PracticeDailyDeck.tsx',
  'src/components/PracticeErrorBoundary.tsx',
  'src/components/PracticeFormRail.tsx',
] as const;

describe('practice chrome locale purity (#5503)', () => {
  test('no a1Bilingual dual-chrome helpers remain', () => {
    for (const rel of PRACTICE_SOURCES) {
      const src = readSrc(rel);
      expect(src, rel).not.toMatch(/a1Bilingual/);
      expect(src, rel).not.toMatch(/PracticeChromeLabel[\s\S]{0,80}btn-sub/);
    }
  });

  test('LexiconPractice does not force dual chrome via A1 || chromeLocale for chrome aria/placeholders', () => {
    const src = readSrc('src/components/LexiconPractice.tsx');
    // Region aria must key off chromeLocale, not showEnglishSubtitles dual slash.
    expect(src).toContain("CHROME_STRINGS[chromeLocale]['practice.ariaLabel']");
    expect(src).not.toMatch(
      /aria-label=\{showEnglishSubtitles \? ["']Практика слів дня \/ Words/,
    );
    // Cloze chrome placeholder is pure locale-keyed, not slash-dual.
    expect(src).toContain("CHROME_STRINGS[chromeLocale]['practice.typeWord']");
    expect(src).not.toMatch(/введіть слово \/ type the word/);
    // Progress aria is pure locale-keyed.
    expect(src).toContain("CHROME_STRINGS[chromeLocale]['practice.progress']");
    expect(src).not.toMatch(/Прогрес \$\{progressLabel\} \/ Progress/);
  });

  test('showEnglishSubtitles is documented as content-only (A1 item glosses)', () => {
    const src = readSrc('src/components/LexiconPractice.tsx');
    expect(src).toMatch(/Content glosses only/);
    expect(src).toMatch(
      /const showEnglishSubtitles = learnerLevel === 'A1' \|\| chromeLocale === 'en'/,
    );
  });

  test('session summary and error boundary use ChromeText/ChromeDual, not slash duals', () => {
    const summary = readSrc('src/components/PracticeSessionSummary.tsx');
    expect(summary).toContain('ChromeText');
    expect(summary).not.toMatch(/btn-sub/);
    expect(summary).not.toMatch(/\/ Correct/);
    expect(summary).not.toMatch(/showEnglishSubtitles/);

    const boundary = readSrc('src/components/PracticeErrorBoundary.tsx');
    expect(boundary).toContain('ChromeDual');
    expect(boundary).toContain('ChromeText');
    expect(boundary).not.toMatch(/btn-sub/);
    expect(boundary).not.toMatch(/\/ We could/);
  });

  test('flashcard rating labels are pure chromeLocale (no dual EN subtitle under UK)', () => {
    const src = readSrc('src/components/PracticeFlashcard.tsx');
    expect(src).toContain('ratingLabels[rating][chromeLocale]');
    expect(src).not.toMatch(/btn-sub/);
    expect(src).not.toMatch(/showEnglishSubtitles/);
  });

  test('pure-locale practice.* keys exist in both en and uk', () => {
    const purityKeys: ChromeKey[] = [
      'practice.ariaLabel',
      'practice.typeWord',
      'practice.anotherSession',
      'practice.done',
      'practice.correctCount',
      'practice.lapsedCount',
      'practice.advancedToReview',
      'practice.willRepeatNext',
      'practice.retry',
      'practice.loadError',
      'practice.loadErrorReload',
      'practice.poolMiss',
      'practice.progress',
    ];
    for (const key of purityKeys) {
      expect(CHROME_STRINGS.en[key].trim().length).toBeGreaterThan(0);
      expect(CHROME_STRINGS.uk[key].trim().length).toBeGreaterThan(0);
      // Values must not themselves be slash-dual strings.
      expect(CHROME_STRINGS.en[key]).not.toMatch(/ \/ /);
      expect(CHROME_STRINGS.uk[key]).not.toMatch(/ \/ /);
    }
  });
});
