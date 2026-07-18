import ChromeText from '../lib/i18n/ChromeText';
import type { ChromeLocale } from '../lib/i18n/chrome';

export type FormRailVerdict = 'idle' | 'correct' | 'wrong' | 'calque';

export interface PracticeFormRailEntry {
  /** Accessible label for the value (not necessarily visible). */
  label: string;
  /** Visible value rendered in the rail cell. */
  value: string;
}

export interface PracticeFormRailProps {
  source: PracticeFormRailEntry;
  actual: PracticeFormRailEntry;
  verdict: FormRailVerdict;
  chromeLocale: ChromeLocale;
}

export default function PracticeFormRail({
  source,
  actual,
  verdict,
  chromeLocale,
}: PracticeFormRailProps) {
  const verdictKey =
    verdict === 'correct'
      ? 'practice.verdict.correct'
      : verdict === 'calque'
        ? 'practice.verdict.calque'
        : verdict === 'wrong'
          ? 'practice.verdict.wrong'
          : null;
  return (
    <div
      className={`practice-form-rail verdict-${verdict}`}
      role="status"
      aria-live="polite"
      data-testid="practice-form-rail"
      data-verdict={verdict}
      data-chrome-locale={chromeLocale}
    >
      <div className="practice-form-rail-row">
        <div className="practice-form-rail-cell rail-source">
          <span className="rail-cell-label">
            <ChromeText k="practice.rail.source" />
          </span>
          <span className="rail-cell-value" lang="uk" aria-label={source.label}>
            {source.value}
          </span>
        </div>
        <div className="practice-form-rail-separator" aria-hidden="true">
          →
        </div>
        <div className="practice-form-rail-cell rail-actual">
          <span className="rail-cell-label">
            <ChromeText k="practice.rail.actual" />
          </span>
          <span className="rail-cell-value" lang="uk" aria-label={actual.label}>
            {actual.value}
          </span>
        </div>
      </div>
      {verdictKey ? (
        <p className="practice-form-rail-status" data-testid="practice-form-rail-status">
          <ChromeText k={verdictKey} />
        </p>
      ) : null}
    </div>
  );
}
