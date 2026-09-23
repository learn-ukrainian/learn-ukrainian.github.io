import React from 'react';
import type { ReactNode } from 'react';
import layout from './LevelLanding.module.css';
import styles from './ArcLanding.module.css';
import ChromeText, { ChromeDual } from '../lib/i18n/ChromeText';
import { formatLessonCount } from '../lib/i18n/chrome';
import { ARC_STATE_KEY, groupByPhase, moduleHref, type ArcPosition } from '../lib/arc';

type ArcLandingProps = {
  level: string;
  positions: ArcPosition[];
  /** Link to the previous edition of the level, shown once under the heading. */
  previousEditionHref?: string;
};

export function ArcStateBadge({ state }: { state: ArcPosition['state'] }): ReactNode {
  return (
    <span className={[styles.badge, styles[state]].join(' ')} data-state={state}>
      <ChromeText k={ARC_STATE_KEY[state]} />
    </span>
  );
}

export function ArcLessonCount({ count }: { count: number }): ReactNode {
  const both = formatLessonCount(count);
  return <ChromeDual en={both.en} uk={both.uk} />;
}

function ArcRow({ level, position }: { level: string; position: ArcPosition }): ReactNode {
  return (
    <a className={[layout.moduleItem, layout.moduleLink].join(' ')} href={moduleHref(level, position.slug)}>
      <div className={[layout.moduleNum, layout.numTodo].join(' ')}>{String(position.position).padStart(2, '0')}</div>
      <div className={layout.moduleInfo}>
        <div className={layout.moduleTitle}>
          {position.title_uk
            ? <span lang="uk">{position.title_uk}</span>
            : <span lang="en" className={styles.titleEn}>{position.title_en}</span>}
          {position.is_checkpoint && <span className={styles.checkpoint}><ChromeText k="arc.checkpoint" /></span>}
        </div>
        <div className={layout.moduleSub}>{position.job}</div>
      </div>
      <div className={styles.meta}>
        {position.lessons !== null && <ArcLessonCount count={position.lessons} />}
        <ArcStateBadge state={position.state} />
      </div>
    </a>
  );
}

export default function ArcLanding({ level, positions, previousEditionHref }: ArcLandingProps): ReactNode {
  return (
    <div className={layout.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>{level.toUpperCase()}</h1>
        <p className={styles.summary}>
          {positions.length} <ChromeText k="stats.modules" />
        </p>
        {previousEditionHref && (
          <a className={styles.previous} href={previousEditionHref}>
            <ChromeText k="home.track.a1Previous" />
          </a>
        )}
      </header>
      {groupByPhase(positions).map((group) => (
        <section key={group.phase}>
          <div className={layout.unitTitle}>{group.phase}</div>
          <div className={layout.moduleList}>
            {group.items.map((position) => (
              <ArcRow key={position.slug} level={level} position={position} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
