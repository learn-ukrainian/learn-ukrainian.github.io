import type { ReactNode } from 'react';
import {
  ZNO_PRACTICE_DECK_META,
  type ZnoPracticeDeckMeta,
} from '../ZnoPractice';
import { ZNO_MODE_META } from '../useZnoPracticeOverlay';
import { CHROME_STRINGS, type ChromeKey } from '../../lib/i18n/chrome';

export interface CoursesTrackProps {
  chromeLocale: 'uk' | 'en';
  onSelectZnoDeck: (deckId: string) => void;
  onSelectCulturePractice: () => void;
  onHoverZnoDeck?: (deckId: string | null) => void;
  onHoverCultureDeck?: (hovered: boolean) => void;
}

export const CULTURE_DECK_META = {
  title: 'Культура мовлення',
  en: 'Culture of Speech',
  step: 'Збагачення',
  stepEn: 'Enrichment',
  description: 'Виправляйте типові помилки та суржик у реченнях із живого вжитку.',
  descriptionEn: 'Correct typical mistakes and surzhyk in authentic context.',
  accent: 'teal' as const,
  itemCount: 42,
};

export const COURSE_SUBTITLE_KEYS: Record<string, ChromeKey> = {
  'zno-stress': 'practice.courses.subtitle.zno-stress',
  'zno-paronym': 'practice.courses.subtitle.zno-paronym',
  'zno-lexical-norm': 'practice.courses.subtitle.zno-lexical-norm',
  'zno-morphological-norm': 'practice.courses.subtitle.zno-morphological-norm',
  'zno-syntactic-norm': 'practice.courses.subtitle.zno-syntactic-norm',
  'zno-orthography': 'practice.courses.subtitle.zno-orthography',
  'zno-morphology': 'practice.courses.subtitle.zno-morphology',
  'zno-syntax': 'practice.courses.subtitle.zno-syntax',
  'zno-phonetics': 'practice.courses.subtitle.zno-phonetics',
  'culture-error-correction': 'practice.courses.subtitle.culture',
};

function modeCountAccessibleSuffix(count: number, chromeLocale: 'uk' | 'en'): string {
  if (chromeLocale === 'en') {
    return count === 1 ? ' item' : ' items';
  }
  const tail = count % 100;
  if (tail >= 11 && tail <= 14) return ' завдань';
  if (count % 10 === 1) return ' завдання';
  if (count % 10 >= 2 && count % 10 <= 4) return ' завдання';
  return ' завдань';
}

export default function CoursesTrack({
  chromeLocale,
  onSelectZnoDeck,
  onSelectCulturePractice,
  onHoverZnoDeck,
  onHoverCultureDeck,
}: CoursesTrackProps) {
  return (
    <section
      className="k3-track k3-track-courses"
      aria-labelledby="track-courses-title"
      data-testid="practice-track-courses"
    >
      <div className="k3-track-header">
        <div className="k3-track-title-row">
          <h3 id="track-courses-title" className="k3-track-title">
            {chromeLocale === 'uk' ? '🎓 Тематичні курси та ЗНО / НМТ' : '🎓 Thematic Courses & Exams'}
          </h3>
          <span className="k3-track-badge">{chromeLocale === 'uk' ? 'Трек 3' : 'Track 3'}</span>
        </div>
        <p className="k3-track-desc">
          {chromeLocale === 'uk'
            ? 'Підготовка до державного тестування ЗНО / НМТ та культура українського мовлення'
            : 'Preparation for state ZNO / NMT exams and Ukrainian speech culture'}
        </p>
      </div>

      <div
        className="k3-mode-grid"
        role="group"
        aria-label={chromeLocale === 'uk' ? 'Тематичні курси та ЗНО' : 'Thematic courses and exam modes'}
      >
        {ZNO_PRACTICE_DECK_META.map((znoDeck) => {
          const meta = ZNO_MODE_META[znoDeck.deckId];
          const modeCount = znoDeck.itemCount;
          const subtitleKey = COURSE_SUBTITLE_KEYS[znoDeck.deckId];
          const subtitle = subtitleKey && chromeLocale === 'en' ? CHROME_STRINGS.en[subtitleKey] : undefined;
          return (
            <button
              key={znoDeck.deckId}
              type="button"
              className="k3-mode-card"
              data-mode={znoDeck.deckId}
              data-zno-deck="true"
              data-accent={meta?.accent ?? 'teal'}
              data-mode-count={modeCount}
              data-testid={`practice-zno-card-${znoDeck.deckId}`}
              aria-describedby="mode-detail-line"
              onMouseEnter={() => onHoverZnoDeck?.(znoDeck.deckId)}
              onMouseLeave={() => onHoverZnoDeck?.(null)}
              onFocus={() => onHoverZnoDeck?.(znoDeck.deckId)}
              onBlur={() => onHoverZnoDeck?.(null)}
              onClick={() => onSelectZnoDeck(znoDeck.deckId)}
            >
              <span
                className="k3-mode-card-difficulty-badge"
                data-testid={`practice-course-difficulty-${znoDeck.deckId}`}
              >
                {CHROME_STRINGS[chromeLocale]['practice.courses.badgeExam']}
              </span>
              <span className="k3-mode-title">{znoDeck.title}</span>
              {subtitle ? (
                <span
                  className="k3-mode-subtitle"
                  data-testid={`practice-course-subtitle-${znoDeck.deckId}`}
                >
                  {subtitle}
                </span>
              ) : null}
              <span className="k3-mode-step">{chromeLocale === 'uk' ? 'ЗНО / НМТ' : 'ZNO / NMT'}</span>
              <span className="k3-mode-desc">
                {chromeLocale === 'uk' ? meta?.description : meta?.descriptionEn}
              </span>
              {znoDeck.thinDeck ? (
                <span className="k3-mode-empty-note" data-testid={`practice-zno-thin-${znoDeck.deckId}`}>
                  {chromeLocale === 'uk' ? 'Невелика добірка' : 'Compact deck'}
                </span>
              ) : null}
              <span
                className="k3-mode-count"
                data-testid={`practice-mode-count-${znoDeck.deckId}`}
              >
                <span aria-hidden="true">{modeCount}</span>
                <span className="sr-only">
                  {modeCountAccessibleSuffix(modeCount, chromeLocale)}
                </span>
              </span>
            </button>
          );
        })}

        {/* Culture of Speech Deck */}
        <button
          key="culture-error-correction"
          type="button"
          className="k3-mode-card"
          data-mode="culture-error-correction"
          data-accent={CULTURE_DECK_META.accent}
          data-mode-count={CULTURE_DECK_META.itemCount}
          data-testid="practice-card-culture"
          aria-describedby="mode-detail-line"
          onMouseEnter={() => onHoverCultureDeck?.(true)}
          onMouseLeave={() => onHoverCultureDeck?.(false)}
          onFocus={() => onHoverCultureDeck?.(true)}
          onBlur={() => onHoverCultureDeck?.(false)}
          onClick={onSelectCulturePractice}
        >
          <span
            className="k3-mode-card-difficulty-badge"
            data-testid="practice-course-difficulty-culture-error-correction"
          >
            {CHROME_STRINGS[chromeLocale]['practice.courses.badgeCulture']}
          </span>
          <span className="k3-mode-title">
            {CULTURE_DECK_META.title}
          </span>
          {chromeLocale === 'en' ? (
            <span
              className="k3-mode-subtitle"
              data-testid="practice-course-subtitle-culture-error-correction"
            >
              {CHROME_STRINGS.en['practice.courses.subtitle.culture']}
            </span>
          ) : null}
          <span className="k3-mode-step">
            {chromeLocale === 'uk' ? CULTURE_DECK_META.step : CULTURE_DECK_META.stepEn}
          </span>
          <span className="k3-mode-desc">
            {chromeLocale === 'uk' ? CULTURE_DECK_META.description : CULTURE_DECK_META.descriptionEn}
          </span>
          <span
            className="k3-mode-count"
            data-testid="practice-mode-count-culture-error-correction"
          >
            <span aria-hidden="true">{CULTURE_DECK_META.itemCount}</span>
            <span className="sr-only">
              {modeCountAccessibleSuffix(CULTURE_DECK_META.itemCount, chromeLocale)}
            </span>
          </span>
        </button>
      </div>
    </section>
  );
}
