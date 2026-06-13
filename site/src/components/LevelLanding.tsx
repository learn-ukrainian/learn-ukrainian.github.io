import React from 'react';
import type { ReactNode } from 'react';
import styles from './LevelLanding.module.css';
import LiveStatus from './LiveStatus';

type ModuleItem = {
  num: number;
  title: string;
  titleEn?: string;   // Optional English title shown beneath the Ukrainian one
  slug: string;
  sub?: string;
  subEn?: string;     // Optional English sub shown beneath the Ukrainian one
  status: 'done' | 'active' | 'todo' | 'locked';
};

type UnitGroup = {
  unit: string;
  items: ModuleItem[];
};

type OldModuleItem = {
  num: number;
  title: string;
  slug: string;
  status: 'ready' | 'qa' | 'wip' | 'planned';
  isCheckpoint?: boolean;
};

type LevelLandingProps = {
  level: string;
  title?: string;
  levelName?: string; // backwards compat
  subtitle?: string;
  introduction?: string; // backwards compat
  moduleCount?: number;
  wordTarget?: number;
  totalPlanned?: number; // backwards compat
  hours?: number;
  color?: string;
  progressTitle?: string;
  progressDescription?: string;
  modules: UnitGroup[] | OldModuleItem[];
};

// Tracks whose module links are suppressed on the landing page (built modules
// render as locked). Folk was un-hidden 2026-06-14 for the preview/seminar-test
// launch (reverses orchestrator #3027); its 3 built modules are now clickable.
const HIDDEN_MODULE_LINK_TRACKS = new Set<string>();

function ModuleCard({ mod, level, color }: { mod: ModuleItem; level: string; color: string }) {
  const levelKey = level.toLowerCase();
  const shouldHideLink = HIDDEN_MODULE_LINK_TRACKS.has(levelKey);
  const moduleStatus = shouldHideLink && (mod.status === 'done' || mod.status === 'active')
    ? 'locked'
    : mod.status;
  const statusIcons: Record<string, string> = {
    done: '\u2705',
    active: '\u25B6\uFE0F',
    todo: '',
    locked: '\uD83D\uDD12',
  };

  const numClass = [
    styles.moduleNum,
    moduleStatus === 'done' ? styles.numDone : '',
    moduleStatus === 'active' ? styles.numActive : '',
    moduleStatus === 'todo' || moduleStatus === 'locked' ? styles.numTodo : '',
  ].filter(Boolean).join(' ');

  const itemClass = [
    styles.moduleItem,
    moduleStatus === 'locked' ? styles.moduleLocked : '',
  ].filter(Boolean).join(' ');

  const numStyle = moduleStatus === 'active'
    ? { borderColor: color, color: color }
    : moduleStatus === 'done'
    ? {}
    : {};

  const inner = (
    <div className={itemClass}>
      <div className={numClass} style={numStyle}>
        {String(mod.num).padStart(2, '0')}
      </div>
      <div className={styles.moduleInfo}>
        <div className={styles.moduleTitle}>
          {mod.title}
          {mod.titleEn && <span className={styles.moduleTitleEn}> · {mod.titleEn}</span>}
        </div>
        {mod.sub && <div className={styles.moduleSub}>{mod.sub}</div>}
        {mod.subEn && <div className={styles.moduleSubEn}>{mod.subEn}</div>}
      </div>
      <div className={styles.moduleStatus}>
        {levelKey === 'a1' && (moduleStatus === 'done' || moduleStatus === 'active')
          ? <LiveStatus track={levelKey} num={mod.num} fallback={moduleStatus} />
          : statusIcons[moduleStatus]}
      </div>
    </div>
  );

  if ((moduleStatus === 'done' || moduleStatus === 'active') && !shouldHideLink) {
    return <a href={`/${levelKey}/${mod.slug}/`} style={{ textDecoration: 'none', color: 'inherit' }}>{inner}</a>;
  }
  return inner;
}

export default function LevelLanding(props: LevelLandingProps): ReactNode {
  const {
    level,
    subtitle,
    introduction,
    hours,
  } = props;

  const displayTitle = props.title || props.levelName || level;
  const displaySub = subtitle || introduction;
  const totalModules = props.moduleCount || props.totalPlanned || 0;
  const wordTarget = props.wordTarget || 0;

  // Color defaults per track. These are gradient/background tokens; the
  // solid accent map below is used where CSS requires an actual color.
  const defaultColors: Record<string, string> = {
    a1: 'var(--lu-id-a1)', a2: 'var(--lu-id-a2)', b1: 'var(--lu-id-b1)',
    b2: 'var(--lu-id-b2)', c1: 'var(--lu-id-c1)', c2: 'var(--lu-id-c2)',
    hist: 'var(--lu-id-hist)', bio: 'var(--lu-id-bio)',
    istorio: 'var(--lu-id-istorio)', lit: 'var(--lu-id-lit)',
    oes: 'var(--lu-id-oes)', ruth: 'var(--lu-id-ruth)',
    folk: 'var(--lu-id-folk)', 'b2-pro': 'var(--lu-id-b2-pro)',
    'c1-pro': 'var(--lu-id-c1-pro)', 'lit-drama': 'var(--lu-id-lit-drama)',
    'lit-essay': 'var(--lu-id-lit-essay)', 'lit-fantastika': 'var(--lu-id-lit-fantastika)',
    'lit-hist-fic': 'var(--lu-id-lit-hist-fic)', 'lit-humor': 'var(--lu-id-lit-humor)',
    'lit-war': 'var(--lu-id-lit-war)', 'lit-youth': 'var(--lu-id-lit-youth)',
  };
  const color = props.color || defaultColors[level.toLowerCase()] || 'var(--lu-id-core)';
  const accentColor = getAccentColor(level);

  // Normalize modules: support both old flat array and new grouped format
  let unitGroups: UnitGroup[];
  if (props.modules.length > 0 && 'unit' in props.modules[0]) {
    unitGroups = props.modules as UnitGroup[];
  } else {
    // Old format: flat array → single group
    const oldMods = props.modules as OldModuleItem[];
    const statusMap: Record<string, ModuleItem['status']> = {
      ready: 'done', qa: 'active', wip: 'todo', planned: 'locked',
    };
    unitGroups = [{
      unit: 'Modules',
      items: oldMods.map(m => ({
        num: m.num,
        title: m.title,
        slug: m.slug,
        status: statusMap[m.status] || 'locked',
      })),
    }];
  }

  const doneCount = unitGroups.reduce((acc, g) => acc + g.items.filter(m => m.status === 'done').length, 0);
  const moduleCount = totalModules || unitGroups.reduce((acc, g) => acc + g.items.length, 0);
  const pct = moduleCount > 0 ? Math.round((doneCount / moduleCount) * 100) : 0;
  const heroBackground = getHeroBackground(color, accentColor);
  const progressTitle = props.progressTitle ?? 'Your Progress';
  const progressDescription = props.progressDescription ?? `${doneCount} of ${moduleCount} completed (${pct}%)`;

  return (
    <div className={styles.container}>
      {/* Hero */}
      <div className={styles.hero} style={{ background: heroBackground }}>
        <span className={styles.badge}>{level.toUpperCase()} — {getBadgeLabel(level)}</span>
        <h1 className={styles.heroTitle}>{displayTitle}</h1>
        {displaySub && <div className={styles.heroSub}>{displaySub}</div>}
        <div className={styles.heroStats}>
          <span>{'\uD83D\uDCD6'} {moduleCount} modules</span>
          {wordTarget > 0 && <span>{'\uD83D\uDCAC'} {wordTarget.toLocaleString()} target words</span>}
          {hours && <span>{'\u23F1'} ~{hours} hours</span>}
        </div>
      </div>

      {/* Progress */}
      <div className={styles.progressSection}>
        <div className={styles.progressHeader}>
          <h3>{progressTitle}</h3>
          <span>{progressDescription}</span>
        </div>
        <div className={styles.progressBar}>
          <div className={styles.progressFill} style={{ width: `${pct}%`, background: color }} />
        </div>
      </div>

      {/* Module list by unit */}
      {unitGroups.map((group, gi) => (
        <div key={gi}>
          <div className={styles.unitTitle}>{group.unit}</div>
          <div className={styles.moduleList}>
            {group.items.map(mod => (
              <ModuleCard key={mod.num} mod={mod} level={level} color={accentColor} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function getBadgeLabel(level: string): string {
  const labels: Record<string, string> = {
    A1: 'Beginner', A2: 'Elementary', B1: 'Intermediate',
    B2: 'Upper-Intermediate', C1: 'Advanced', C2: 'Mastery',
  };
  return labels[level.toUpperCase()] || level;
}

function getAccentColor(level: string): string {
  const accents: Record<string, string> = {
    a1: '#0057B8', a2: '#0057B8', b1: '#0057B8', b2: '#0057B8',
    c1: '#0057B8', c2: '#0057B8', 'b2-pro': '#0057B8', 'c1-pro': '#0057B8',
    folk: '#A4133C',
    hist: '#BF360C', istorio: '#BF360C',
    bio: '#4E342E', oes: '#4E342E', ruth: '#4E342E',
    lit: '#4A148C', 'lit-drama': '#4A148C', 'lit-essay': '#4A148C',
    'lit-fantastika': '#4A148C', 'lit-hist-fic': '#4A148C',
    'lit-humor': '#4A148C', 'lit-war': '#4A148C', 'lit-youth': '#4A148C',
  };
  return accents[level.toLowerCase()] || '#0057B8';
}

function getHeroBackground(color: string, fallbackColor: string): string {
  if (/^#[0-9a-f]{6}$/i.test(color)) {
    return `linear-gradient(135deg, ${color}, ${adjustColor(color, -40)})`;
  }
  return color || `linear-gradient(135deg, ${fallbackColor}, ${adjustColor(fallbackColor, -40)})`;
}

function adjustColor(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, Math.max(0, ((num >> 16) & 0xff) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0xff) + amount));
  const b = Math.min(255, Math.max(0, (num & 0xff) + amount));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}
