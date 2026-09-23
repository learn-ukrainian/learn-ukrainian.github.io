import React from 'react';
import type { ReactNode } from 'react';
import layout from './LevelLanding.module.css';
import styles from './ArcLanding.module.css';
import ChromeText, { ChromeDual } from '../lib/i18n/ChromeText';
import { ArcLessonCount, ArcStateBadge } from './ArcLanding';
import { formatArcScopeCount, type ArcScopeKind } from '../lib/i18n/chrome';
import { lessonHref, type ArcPosition } from '../lib/arc';

type ArcModuleProps = {
  level: string;
  position: ArcPosition;
};

export function ArcScopeCount({ kind, count }: { kind: ArcScopeKind; count: number }): ReactNode {
  const both = formatArcScopeCount(kind, count);
  return <ChromeDual en={both.en} uk={both.uk} />;
}

export default function ArcModule({ level, position }: ArcModuleProps): ReactNode {
  const { scope } = position;
  return (
    <div className={layout.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>
          {position.title_uk
            ? <span lang="uk">{position.title_uk}</span>
            : <span lang="en">{position.title_en}</span>}
        </h1>
        <p className={styles.summary}>{position.job}</p>
        <p className={styles.summary}>
          <ArcStateBadge state={position.state} />
          {position.is_checkpoint && <span className={styles.checkpoint}><ChromeText k="arc.checkpoint" /></span>}
        </p>
      </header>

      {scope && (
        <ul className={styles.scope}>
          <li><ArcScopeCount kind="letters" count={scope.letters} /></li>
          <li><ArcScopeCount kind="grammarPoints" count={scope.grammar_points} /></li>
          <li><ArcScopeCount kind="coreLemmas" count={scope.core_lemmas} /></li>
        </ul>
      )}

      {position.lessons !== null && (
        <section>
          <h2>
            <ChromeText k="sidebar.lessons" /> · <ArcLessonCount count={position.lessons} />
          </h2>
          <ol className={styles.lessonList}>
            {position.lesson_titles.map((title, index) => {
              const n = index + 1;
              return (
                <li key={n}>
                  {position.built_lessons.includes(n)
                    ? <a href={lessonHref(level, position.slug, n)} lang="uk">{title}</a>
                    : <span className={styles.lessonPlanned} lang="uk">{title}</span>}
                </li>
              );
            })}
          </ol>
        </section>
      )}

      {position.previous_edition_href && (
        <p>
          <a href={position.previous_edition_href}><ChromeText k="home.track.a1Previous" /></a>
        </p>
      )}
    </div>
  );
}
