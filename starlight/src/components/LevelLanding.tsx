import React from 'react';
import type { ReactNode } from 'react';
import styles from './LevelLanding.module.css';

/** Level color palette — matches Home.tsx LevelCard colors */
const LEVEL_COLORS: Record<string, string> = {
  a1: '#2E7D32',
  a2: '#1565C0',
  b1: '#E65100',
  b2: '#C2185B',
  c1: '#7B1FA2',
  c2: '#C62828',
  hist: '#795548',
  istorio: '#6D4C41',
  bio: '#607D8B',
  'b2-pro': '#455A64',
  'c1-pro': '#37474F',
  lit: '#4E342E',
  oes: '#5D4037',
  ruth: '#3E2723',
};

type ModuleItem = {
  num: number;
  title: string;
  slug: string;
  status: 'ready' | 'qa' | 'wip' | 'planned';
  isCheckpoint?: boolean;
};

type LevelLandingProps = {
  level: string;
  levelName: string;
  subtitle?: string;
  introduction?: string;
  modules: ModuleItem[];
  totalPlanned: number;
};

function ModuleCard({ mod, color, level }: { mod: ModuleItem; color: string; level: string }) {
  const statusEmoji = {
    ready: '\u2705',
    qa: '\uD83D\uDD0D',
    wip: '\uD83D\uDEA7',
    planned: '\uD83D\uDCCB',
  }[mod.status];

  const isClickable = mod.status === 'ready' || mod.status === 'qa';
  const cardClass = [
    styles.card,
    mod.status === 'planned' ? styles.cardPlanned : '',
    isClickable ? styles.cardReady : '',
    mod.isCheckpoint ? styles.checkpoint : '',
  ].filter(Boolean).join(' ');

  const inner = (
    <div className={cardClass}>
      <div className={styles.num} style={{ background: mod.status === 'planned' ? '#ccc' : color }}>
        {mod.num}
      </div>
      <div className={styles.info}>
        <p className={styles.title}>{mod.title}</p>
      </div>
      <span className={styles.status}>{statusEmoji}</span>
    </div>
  );

  if (isClickable) {
    return <a href={`/${level}/${mod.slug}/`} style={{ textDecoration: 'none', color: 'inherit' }}>{inner}</a>;
  }
  return inner;
}

export default function LevelLanding({
  level,
  levelName,
  subtitle,
  introduction,
  modules,
  totalPlanned,
}: LevelLandingProps): ReactNode {
  const color = LEVEL_COLORS[level.toLowerCase()] || '#0057B7';
  const readyCount = modules.filter(m => m.status === 'ready' || m.status === 'qa').length;
  const pct = totalPlanned > 0 ? Math.round((readyCount / totalPlanned) * 100) : 0;

  // Split into regular modules and checkpoints for visual grouping
  const headerGradient = `linear-gradient(135deg, ${color} 0%, ${adjustColor(color, -30)} 100%)`;

  return (
    <div>
      <div className={styles.header} style={{ background: headerGradient }}>
        <h1 className={styles.headerTitle}>{levelName}</h1>
        {subtitle && <p className={styles.headerSub}>{subtitle}</p>}
      </div>

      <div className={styles.progress}>
        <span className={styles.progressLabel}>{readyCount} / {totalPlanned}</span>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${pct}%`, background: color }}
          />
        </div>
        <span className={styles.progressLabel}>{pct}%</span>
      </div>

      {introduction && <p className={styles.intro}>{introduction}</p>}

      <h2 className={styles.sectionTitle}>Modules</h2>
      <div className={styles.grid}>
        {modules.map(mod => (
          <ModuleCard key={mod.num} mod={mod} color={color} level={level.toLowerCase()} />
        ))}
      </div>
    </div>
  );
}

/** Darken a hex color by amount (negative = darker) */
function adjustColor(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, Math.max(0, ((num >> 16) & 0xff) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0xff) + amount));
  const b = Math.min(255, Math.max(0, (num & 0xff) + amount));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}
