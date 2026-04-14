import React from 'react';
import type { ReactNode } from 'react';
import styles from './LevelLanding.module.css';
import LiveStatus from './LiveStatus';

type ModuleItem = {
  num: number;
  title: string;
  slug: string;
  sub?: string;
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
  modules: UnitGroup[] | OldModuleItem[];
};

function ModuleCard({ mod, level, color }: { mod: ModuleItem; level: string; color: string }) {
  const statusIcons: Record<string, string> = {
    done: '\u2705',
    active: '\u25B6\uFE0F',
    todo: '',
    locked: '\uD83D\uDD12',
  };

  const numClass = [
    styles.moduleNum,
    mod.status === 'done' ? styles.numDone : '',
    mod.status === 'active' ? styles.numActive : '',
    mod.status === 'todo' || mod.status === 'locked' ? styles.numTodo : '',
  ].filter(Boolean).join(' ');

  const itemClass = [
    styles.moduleItem,
    mod.status === 'locked' ? styles.moduleLocked : '',
  ].filter(Boolean).join(' ');

  const numStyle = mod.status === 'active'
    ? { borderColor: color, color: color }
    : mod.status === 'done'
    ? {}
    : {};

  const inner = (
    <div className={itemClass}>
      <div className={numClass} style={numStyle}>
        {String(mod.num).padStart(2, '0')}
      </div>
      <div className={styles.moduleInfo}>
        <div className={styles.moduleTitle}>{mod.title}</div>
        {mod.sub && <div className={styles.moduleSub}>{mod.sub}</div>}
      </div>
      <div className={styles.moduleStatus}>
        {level.toLowerCase() === 'a1' && (mod.status === 'done' || mod.status === 'active')
          ? <LiveStatus track={level.toLowerCase()} num={mod.num} fallback={mod.status} />
          : statusIcons[mod.status]}
      </div>
    </div>
  );

  if (mod.status === 'done' || mod.status === 'active') {
    return <a href={`/${level.toLowerCase()}/${mod.slug}/`} style={{ textDecoration: 'none', color: 'inherit' }}>{inner}</a>;
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

  // Color defaults per level
  const defaultColors: Record<string, string> = {
    a1: '#2E7D32', a2: '#1565C0', b1: '#E65100', b2: '#C62828',
    c1: '#6A1B9A', c2: '#8D6E00', hist: '#BF360C', bio: '#0D47A1',
    istorio: '#880E4F', lit: '#4A148C', oes: '#33691E', ruth: '#004D40',
    folk: '#33691E', 'b2-pro': '#455A64', 'c1-pro': '#37474F',
  };
  const color = props.color || defaultColors[level.toLowerCase()] || '#0057B8';

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
  const darkerColor = adjustColor(color, -40);

  return (
    <div className={styles.container}>
      {/* Hero */}
      <div className={styles.hero} style={{ background: `linear-gradient(135deg, ${color}, ${darkerColor})` }}>
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
          <h3>Your Progress</h3>
          <span>{doneCount} of {moduleCount} completed ({pct}%)</span>
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
              <ModuleCard key={mod.num} mod={mod} level={level} color={color} />
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

function adjustColor(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, Math.max(0, ((num >> 16) & 0xff) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0xff) + amount));
  const b = Math.min(255, Math.max(0, (num & 0xff) + amount));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}
