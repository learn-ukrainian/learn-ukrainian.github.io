import { type RefObject } from 'react';
import ChromeText from '../../lib/i18n/ChromeText';
import type { CustomSet } from '../../lib/lexicon/custom-decks';
import { getTeacherTableVirtualDeck } from '../../lib/lexicon/custom-decks';

export interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  chromeLocale: 'uk' | 'en';
  isDriveConfigured: boolean;
  isDriveSyncing: boolean;
  driveSyncMsg: string | null;
  onGoogleDriveSync: () => void;
  selectedDeckFilter: string;
  learnerLevel: string;
  customSets: CustomSet[];
  onRequestDeckSwitch: (id: string) => void;
  onOpenCustomDeckManager: () => void;
  secondaryToolsRef?: RefObject<HTMLDetailsElement | null>;
}

export default function SettingsDrawer({
  isOpen,
  onClose,
  chromeLocale,
  isDriveConfigured,
  isDriveSyncing,
  driveSyncMsg,
  onGoogleDriveSync,
  selectedDeckFilter,
  learnerLevel,
  customSets,
  onRequestDeckSwitch,
  onOpenCustomDeckManager,
  secondaryToolsRef,
}: SettingsDrawerProps) {
  return (
    <>
      {/* Slide-over Drawer Backdrop */}
      {isOpen ? (
        <div
          className="k3-settings-backdrop"
          data-testid="practice-settings-backdrop"
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(2px)',
            zIndex: 998,
          }}
        />
      ) : null}

      {/* Slide-over Drawer Container */}
      <aside
        className={`k3-settings-drawer ${isOpen ? 'open' : ''}`}
        data-testid="practice-settings-drawer"
        role="dialog"
        aria-modal={isOpen}
        aria-label={chromeLocale === 'uk' ? 'Налаштування практики' : 'Practice settings'}
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: 'min(480px, 90vw)',
          background: 'var(--sl-color-gray-6, #18181b)',
          borderLeft: '1px solid var(--sl-color-gray-5, #27272a)',
          boxShadow: isOpen ? '-4px 0 24px rgba(0, 0, 0, 0.4)' : 'none',
          zIndex: 999,
          transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.25s ease-in-out',
          overflowY: 'auto',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}
      >
        {/* Drawer Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 id="settings-drawer-title" style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>
            ⚙️ {chromeLocale === 'uk' ? 'Налаштування та інструменти' : 'Settings & Tools'}
          </h3>
          <button
            type="button"
            className="btn btn-sm"
            data-testid="settings-drawer-close"
            aria-label={chromeLocale === 'uk' ? 'Закрити налаштування' : 'Close settings'}
            onClick={onClose}
            style={{ fontSize: '1.2rem', padding: '0.2rem 0.6rem', lineHeight: 1 }}
          >
            ✕
          </button>
        </div>

        {/* Secondary Tools Details Container (preserves DOM contract and data-testid) */}
        <details
          ref={secondaryToolsRef}
          className="k3-practice-sources"
          data-testid="practice-secondary-tools"
          open={isOpen}
          style={{ width: '100%' }}
        >
          <summary style={{ cursor: 'pointer', fontWeight: 600, padding: '0.5rem 0' }}>
            <ChromeText k="practice.secondaryToolsTitle" />
          </summary>
          <div className="k3-practice-sources-content" style={{ marginTop: '0.75rem' }}>
            {/* Google Drive Cloud Sync */}
            {isDriveConfigured ? (
              <div
                className="k3-drive-sync-bar"
                data-testid="practice-drive-sync-section"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  padding: '1rem',
                  background: 'var(--sl-color-gray-5, rgba(255,255,255,0.05))',
                  borderRadius: '8px',
                  marginBottom: '1rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="btn btn-sm"
                    data-testid="practice-drive-sync-btn"
                    style={{
                      background: 'var(--lu-accent-blue, #2563eb)',
                      color: '#fff',
                      borderRadius: '8px',
                      padding: '0.4rem 0.8rem',
                      fontWeight: 600,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                    }}
                    onClick={onGoogleDriveSync}
                    disabled={isDriveSyncing}
                  >
                    <span>☁️</span>
                    <span>
                      {isDriveSyncing
                        ? (chromeLocale === 'uk' ? 'Синхронізація...' : 'Syncing...')
                        : (chromeLocale === 'uk' ? 'Увійти та синхронізувати з Google Drive' : 'Sign in & sync with Google Drive')}
                    </span>
                  </button>
                  {driveSyncMsg ? (
                    <span style={{ fontSize: '0.85rem', color: 'var(--lu-text-muted)' }}>
                      {driveSyncMsg}
                    </span>
                  ) : null}
                </div>
                <p
                  style={{
                    fontSize: '0.8rem',
                    color: 'var(--lu-text-muted, #94a3b8)',
                    margin: '0.2rem 0 0',
                    lineHeight: 1.4,
                  }}
                >
                  {chromeLocale === 'uk'
                    ? '🔒 Синхронізація використовує лише приватний appDataFolder вашого Google Drive. Без доступу до особистих файлів чи сторонніх баз даних.'
                    : '🔒 Sync uses only your private Google Drive appDataFolder. No access to personal files or external databases.'}
                </p>
              </div>
            ) : null}

            {/* Deck Filter & Custom Sets */}
            <div
              className="k3-deck-filter-bar"
              style={{
                padding: '0.75rem 1rem',
                background: 'var(--lu-bg-card, rgba(255,255,255,0.05))',
                borderRadius: '12px',
                border: '1px solid var(--lu-border, rgba(255,255,255,0.1))',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                }}
              >
                <span style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>
                  {chromeLocale === 'uk' ? '📚 Колоди та добірки слів' : '📚 Word Decks & Collections'}
                </span>
                <button
                  type="button"
                  className="btn btn-sm btn-accent"
                  onClick={onOpenCustomDeckManager}
                  style={{ fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}
                >
                  ⚙️ {chromeLocale === 'uk' ? 'Менеджер колод / Імпорт' : 'Manage Decks / Import'}
                </button>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                <button
                  type="button"
                  className={`btn btn-sm ${selectedDeckFilter === 'all' ? 'btn-primary shadow-md' : 'btn-ghost'}`}
                  onClick={() => onRequestDeckSwitch('all')}
                  style={selectedDeckFilter === 'all' ? { border: '2px solid #3b82f6', fontWeight: 800 } : {}}
                >
                  {selectedDeckFilter === 'all' ? '✓ ' : ''}🌐{' '}
                  {chromeLocale === 'uk' ? `Всі слова (${learnerLevel})` : `All Words (${learnerLevel})`}
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${selectedDeckFilter === 'virtual_teacher_lesson' ? 'btn-primary shadow-md' : 'btn-ghost'}`}
                  onClick={() => onRequestDeckSwitch('virtual_teacher_lesson')}
                  style={selectedDeckFilter === 'virtual_teacher_lesson' ? { border: '2px solid #3b82f6', fontWeight: 800 } : {}}
                >
                  {selectedDeckFilter === 'virtual_teacher_lesson' ? '✓ ' : ''}🎓{' '}
                  {chromeLocale === 'uk' ? 'Відібрана добірка' : 'Curated Deck'}
                </button>
                <button
                  type="button"
                  data-testid="practice-deck-teacher-table"
                  className={`btn btn-sm ${selectedDeckFilter === 'virtual_teacher_table' ? 'btn-primary shadow-md' : 'btn-ghost'}`}
                  onClick={() => onRequestDeckSwitch('virtual_teacher_table')}
                  style={selectedDeckFilter === 'virtual_teacher_table' ? { border: '2px solid #3b82f6', fontWeight: 800 } : {}}
                >
                  {selectedDeckFilter === 'virtual_teacher_table' ? '✓ ' : ''}📋{' '}
                  {chromeLocale === 'uk' ? getTeacherTableVirtualDeck().titleUk : getTeacherTableVirtualDeck().title}
                </button>
                {customSets.map((set) => (
                  <button
                    key={set.id}
                    type="button"
                    className={`btn btn-sm ${selectedDeckFilter === set.id ? 'btn-primary shadow-md' : 'btn-ghost'}`}
                    onClick={() => onRequestDeckSwitch(set.id)}
                    style={selectedDeckFilter === set.id ? { border: '2px solid #3b82f6', fontWeight: 800 } : {}}
                  >
                    {selectedDeckFilter === set.id ? '✓ ' : ''}⭐ {set.title} ({set.lemma_keys.length})
                  </button>
                ))}
              </div>
            </div>
          </div>
        </details>
      </aside>
    </>
  );
}
