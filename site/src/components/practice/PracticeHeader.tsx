import type { ReactNode } from 'react';
import ChromeText from '../../lib/i18n/ChromeText';
import type { CefrLevel } from '../../lib/lexicon/levels';
import type { CustomSet } from '../../lib/lexicon/custom-decks';

export interface PracticeHeaderProps {
  currentLevel: CefrLevel;
  onSelectLevel: (level: CefrLevel) => void;
  streakDays: number;
  dueTodayCount: number;
  newCardsDueCount: number;
  hasActiveSnapshot: boolean;
  onStartSession: () => void;
  onRestartSession: () => void;
  onOpenSettings: () => void;
  activeDeckLabel: string;
  activeDeckItemCount?: number;
  dailyDeckNode?: ReactNode;
  chromeLocale?: 'uk' | 'en';
  loading?: boolean;
}

const PUBLISHED_LEVELS: CefrLevel[] = ['A1', 'A2', 'B1', 'B2', 'C1'];

export default function PracticeHeader({
  currentLevel,
  onSelectLevel,
  streakDays,
  dueTodayCount,
  newCardsDueCount,
  hasActiveSnapshot,
  onStartSession,
  onRestartSession,
  onOpenSettings,
  activeDeckLabel,
  activeDeckItemCount,
  dailyDeckNode,
  chromeLocale = 'uk',
  loading = false,
}: PracticeHeaderProps) {
  return (
    <header className="k3-practice-header" data-testid="practice-header" style={{ marginBottom: '1.5rem' }}>
      {/* Top Row: Brand / Level Pills / Stats / Settings Toggle */}
      <div
        className="k3-header-top-bar"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          paddingBottom: '1rem',
          borderBottom: '1px solid var(--sl-color-gray-5, rgba(255,255,255,0.1))',
        }}
      >
        {/* Level selector pills */}
        <div
          className="k3-level-selector"
          role="radiogroup"
          aria-label={chromeLocale === 'uk' ? 'Рівень складності' : 'Proficiency level'}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          {PUBLISHED_LEVELS.map((lvl) => (
            <button
              key={lvl}
              type="button"
              className={`btn btn-sm ${lvl === currentLevel ? 'btn-accent' : ''}`}
              data-testid={`practice-level-chip-${lvl}`}
              aria-checked={lvl === currentLevel}
              role="radio"
              onClick={() => onSelectLevel(lvl)}
              style={{
                fontWeight: lvl === currentLevel ? 700 : 500,
                padding: '0.35rem 0.75rem',
                borderRadius: '9999px',
              }}
            >
              {lvl}
            </button>
          ))}
          {activeDeckLabel && activeDeckLabel !== currentLevel ? (
            <span
              className="k3-active-deck-chip"
              data-testid="practice-active-deck-chip"
              style={{
                fontSize: '0.8rem',
                padding: '0.25rem 0.6rem',
                background: 'var(--sl-color-accent-low, rgba(99, 102, 241, 0.15))',
                border: '1px solid var(--sl-color-accent)',
                borderRadius: '9999px',
                color: 'var(--sl-color-accent-high, #818cf8)',
                marginLeft: '0.5rem',
              }}
            >
              {activeDeckLabel}
              {activeDeckItemCount !== undefined ? ` (${activeDeckItemCount})` : ''}
            </span>
          ) : null}
        </div>

        {/* Stats: Streak & Due counters & Settings button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            className="k3-stat-badge"
            data-testid="practice-streak-counter"
            title={chromeLocale === 'uk' ? 'Днів практики поспіль' : 'Consecutive practice days'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontSize: '0.9rem',
              fontWeight: 600,
              color: streakDays > 0 ? '#f59e0b' : 'var(--sl-color-gray-3)',
            }}
          >
            <span aria-hidden="true">🔥</span>
            <span>{streakDays} {chromeLocale === 'uk' ? 'дн.' : 'days'}</span>
          </div>

          <div
            className="k3-stat-badge"
            data-testid="practice-due-counter"
            title={chromeLocale === 'uk' ? 'Карток на повторення сьогодні' : 'Cards due today'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontSize: '0.9rem',
              fontWeight: 600,
            }}
          >
            <span aria-hidden="true">⏱️</span>
            <span>{dueTodayCount} {chromeLocale === 'uk' ? 'до повторення' : 'due'}</span>
          </div>

          <button
            type="button"
            className="btn btn-sm k3-settings-btn"
            data-testid="practice-settings-toggle"
            aria-label={chromeLocale === 'uk' ? 'Налаштування та синхронізація' : 'Settings and sync'}
            onClick={onOpenSettings}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.65rem',
              borderRadius: '6px',
            }}
          >
            <span aria-hidden="true">⚙️</span>
            <span>{chromeLocale === 'uk' ? 'Налаштування' : 'Settings'}</span>
          </button>
        </div>
      </div>

      {/* Words of the Day engagement banner */}
      {dailyDeckNode ? (
        <div style={{ marginTop: '1rem', marginBottom: '1rem' }}>
          {dailyDeckNode}
        </div>
      ) : null}

      {/* Primary Session CTA Bar */}
      <div
        className="k3-session-bar"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          marginTop: '1rem',
        }}
      >
        <button
          type="button"
          className="btn btn-accent k3-session-primary"
          data-testid="practice-start-session"
          disabled={loading}
          onClick={onStartSession}
          style={{
            fontSize: '1.05rem',
            padding: '0.65rem 1.5rem',
            fontWeight: 600,
            borderRadius: '8px',
          }}
        >
          <ChromeText k={hasActiveSnapshot ? 'practice.sessionResume' : 'practice.sessionStart'} />
        </button>
        {hasActiveSnapshot ? (
          <button
            type="button"
            className="btn k3-session-reset"
            data-testid="practice-reset-session"
            data-reset-mode="mixed"
            onClick={onRestartSession}
            style={{
              fontSize: '0.95rem',
              padding: '0.65rem 1.1rem',
              borderRadius: '8px',
            }}
          >
            <ChromeText k="practice.sessionRestart" />
          </button>
        ) : null}
      </div>
    </header>
  );
}
