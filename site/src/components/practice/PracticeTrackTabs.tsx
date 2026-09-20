export type PracticeTrackId = 'all' | 'vocab' | 'grammar' | 'courses';

export interface PracticeTrackTabsProps {
  activeTrack: PracticeTrackId;
  onSelectTrack: (track: PracticeTrackId) => void;
  chromeLocale?: 'uk' | 'en';
}

export default function PracticeTrackTabs({
  activeTrack,
  onSelectTrack,
  chromeLocale = 'uk',
}: PracticeTrackTabsProps) {
  const tabs = [
    {
      id: 'all' as const,
      labelUk: 'Всі треки',
      labelEn: 'All Tracks',
      icon: '⚡',
      testid: 'practice-track-tab-all',
    },
    {
      id: 'vocab' as const,
      labelUk: 'Трек 1: Словниковий запас',
      labelEn: 'Track 1: Vocabulary',
      icon: '📖',
      testid: 'practice-track-tab-vocab',
    },
    {
      id: 'grammar' as const,
      labelUk: 'Трек 2: Граматика та механіки',
      labelEn: 'Track 2: Grammar & Mechanics',
      icon: '🧩',
      testid: 'practice-track-tab-grammar',
    },
    {
      id: 'courses' as const,
      labelUk: 'Трек 3: Курси та ЗНО / НМТ',
      labelEn: 'Track 3: Courses & Exams',
      icon: '🎓',
      testid: 'practice-track-tab-courses',
    },
  ];

  return (
    <nav
      className="k3-track-tabs"
      data-testid="practice-track-tabs"
      role="tablist"
      aria-label={chromeLocale === 'uk' ? 'Навігація по треках' : 'Track navigation'}
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.5rem',
        marginBottom: '1.25rem',
        padding: '0.35rem',
        background: 'var(--sl-color-gray-6, rgba(255, 255, 255, 0.04))',
        borderRadius: '8px',
        border: '1px solid var(--sl-color-gray-5, rgba(255, 255, 255, 0.08))',
      }}
    >
      {tabs.map((tab) => {
        const isActive = activeTrack === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={`btn btn-sm ${isActive ? 'btn-accent' : ''}`}
            data-testid={tab.testid}
            onClick={() => onSelectTrack(tab.id)}
            style={{
              padding: '0.4rem 0.85rem',
              borderRadius: '6px',
              fontWeight: isActive ? 700 : 500,
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              cursor: 'pointer',
            }}
          >
            <span aria-hidden="true">{tab.icon}</span>
            <span>{chromeLocale === 'uk' ? tab.labelUk : tab.labelEn}</span>
          </button>
        );
      })}
    </nav>
  );
}
