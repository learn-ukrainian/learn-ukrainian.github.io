import React from 'react';
import type { ReactNode } from 'react';
import styles from './Home.module.css';
import curriculumStats from '../data/curriculum-stats.json';
import ChromeText from '../lib/i18n/ChromeText';
import { CHROME_STRINGS, type ChromeKey } from '../lib/i18n/chrome';

/** Get module count from curriculum.yaml-generated stats */
function mc(level: string): number {
  return (curriculumStats as Record<string, any>)[level.toLowerCase()]?.modules ?? 0;
}

function HomepageHeader() {
  return (
    <header className={`${styles.heroBanner}`}>
      <div className="container" style={{maxWidth: '1200px', margin: '0 auto', padding: '0 20px'}}>
        <h1 className="hero__title" style={{color: 'white', fontSize: '3.5rem', fontWeight: 800, textShadow: '0 2px 20px rgba(0, 0, 0, 0.3)', marginBottom: '0.5rem', marginTop: '0'}}>
          Learn Ukrainian
        </h1>
        <p className="hero__subtitle" style={{color: 'rgba(255, 255, 255, 0.95)', fontSize: '1.4rem', maxWidth: '600px', margin: '0 auto'}}>
          Мова – душа народу • Language is the soul of a nation
        </p>
        <div className={styles.buttons}>
          <a className={styles.primaryButton} href="/a1/">
            <ChromeText k="home.heroStart" />
          </a>
          <a className={styles.secondaryButton} href="#levels">
            <ChromeText k="home.heroViewLevels" />
          </a>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  titleKey: ChromeKey;
  emoji: string;
  description: ReactNode;
};

const totalModules = (curriculumStats as any)._total?.toLocaleString?.() ?? '';

const FeatureList: FeatureItem[] = [
  { titleKey: 'home.featTheoryT', emoji: '📚', description: <ChromeText k="home.featTheoryD" /> },
  { titleKey: 'home.featInteractiveT', emoji: '🎮', description: <ChromeText k="home.featInteractiveD" /> },
  { titleKey: 'home.featCultureT', emoji: '🌍', description: <ChromeText k="home.featCultureD" /> },
  {
    titleKey: 'home.featPathwayT',
    emoji: '🎓',
    description: (
      <>
        <ChromeText k="home.featPathwayD" /> {totalModules} <ChromeText k="home.featPathwayModules" />
      </>
    ),
  },
];

function Feature({ titleKey, emoji, description }: FeatureItem) {
  return (
    <div style={{flex: '1 1 250px'}}>
      <div className={styles.featureCard}>
        <div className={styles.featureEmoji}>{emoji}</div>
        <h3 style={{margin: '0.5rem 0'}}><ChromeText k={titleKey} /></h3>
        <p style={{margin: 0}}>{description}</p>
      </div>
    </div>
  );
}

function LevelCard({ level, nameKey, descKey, modules, color, preview }: {
  level: string;
  nameKey: ChromeKey;
  descKey: ChromeKey;
  modules: number;
  color: string;
  preview?: boolean;
}) {
  return (
    <div style={{flex: '1 1 300px', marginBottom: '1.5rem'}}>
      <a href={`/${level.toLowerCase()}/`} className={styles.levelLink}>
        <div className={styles.levelCard} data-level={level.toLowerCase()}>
          <span className={styles.levelBadge} style={{ background: color }}>
            {level}
          </span>
          {preview && (
            <span style={{
              marginLeft: '8px', fontSize: '0.65rem', fontWeight: 700,
              letterSpacing: '0.06em', padding: '2px 8px', borderRadius: '999px',
              border: `1px solid ${color}`, color, verticalAlign: 'middle',
            }}>
              <ChromeText k="label.preview" />
            </span>
          )}
          <h3 style={{marginTop: '10px'}}><ChromeText k={nameKey} /></h3>
          <p style={{margin: '0 0 1rem 0'}}><ChromeText k={descKey} /></p>
          <span className={styles.moduleCount}>{modules} <ChromeText k="stats.modules" /></span>
        </div>
      </a>
    </div>
  );
}

export default function Home(): ReactNode {
  return (
    <div className="home-wrapper" style={{margin: '0', width: '100%', padding: '0'}}>
      <HomepageHeader />
      <main>
        <section className={styles.features}>
          <div className="container" style={{maxWidth: '1200px', margin: '0 auto', padding: '0 20px'}}>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '20px'}}>
              {FeatureList.map((props, idx) => (
                <Feature key={idx} {...props} />
              ))}
            </div>
          </div>
        </section>

        <section id="levels" className={styles.levels}>
          <div className="container" style={{maxWidth: '1200px', margin: '0 auto', padding: '0 20px'}}>
            <h2 className={styles.sectionTitle} style={{marginTop: 0}}>
              <ChromeText k="home.secCoreLevels" />
            </h2>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '20px'}}>
              <LevelCard level="A1" nameKey="level.a1.name" descKey="level.a1.desc" modules={mc('a1')} color="#2E7D32" />
              <LevelCard level="A2" nameKey="level.a2.name" descKey="level.a2.desc" modules={mc('a2')} color="#1565C0" />
              <LevelCard level="B1" nameKey="level.b1.name" descKey="level.b1.desc" modules={mc('b1')} color="#E65100" />
              <LevelCard level="B2" nameKey="level.b2.name" descKey="level.b2.desc" modules={mc('b2')} color="#C2185B" preview />
              <LevelCard level="C1" nameKey="level.c1.name" descKey="level.c1.desc" modules={mc('c1')} color="#7B1FA2" />
              <LevelCard level="C2" nameKey="level.c2.name" descKey="level.c2.desc" modules={mc('c2')} color="#C62828" />
            </div>

            <h2 className={styles.sectionTitle} style={{marginTop: '4rem'}}>
              <ChromeText k="home.secSpecTracks" />
            </h2>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '20px'}}>
              <LevelCard level="HIST" nameKey="level.hist.name" descKey="level.hist.desc" modules={mc('hist')} color="#795548" />
              <LevelCard level="ISTORIO" nameKey="level.istorio.name" descKey="level.istorio.desc" modules={mc('istorio')} color="#6D4C41" />
              <LevelCard level="BIO" nameKey="level.bio.name" descKey="level.bio.desc" modules={mc('bio')} color="#607D8B" />
              <LevelCard level="B2-PRO" nameKey="level.b2pro.name" descKey="level.b2pro.desc" modules={mc('b2-pro')} color="#455A64" />
              <LevelCard level="C1-PRO" nameKey="level.c1pro.name" descKey="level.c1pro.desc" modules={mc('c1-pro')} color="#37474F" />
              <LevelCard level="LIT" nameKey="level.lit.name" descKey="level.lit.desc" modules={mc('lit')} color="#5D4037" />
              <LevelCard level="FOLK" nameKey="level.folk.name" descKey="level.folk.desc" modules={mc('folk')} color="#A4133C" preview />
            </div>

            <h2 className={styles.sectionTitle} style={{marginTop: '4rem'}}>
              <ChromeText k="home.secSeminars" />
            </h2>
            <p className={styles.sectionSubtitle}>
              <ChromeText k="home.secSeminarsSub" />
            </p>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center'}}>
              <LevelCard level="OES" nameKey="level.oes.name" descKey="level.oes.desc" modules={103} color="#8D6E63" />
              <LevelCard level="RUTH" nameKey="level.ruth.name" descKey="level.ruth.desc" modules={115} color="#A1887F" />
            </div>
          </div>
        </section>

        <section className={styles.cta}>
          <div className="container" style={{maxWidth: '1200px', margin: '0 auto', padding: '0 20px'}}>
            <div className={styles.ctaContent}>
              <h2 style={{marginTop: 0}}><ChromeText k="home.ctaTitle" /></h2>
              <p><ChromeText k="home.ctaBody" /></p>
              <a className={styles.primaryButton} href="/a1/">
                <ChromeText k="home.ctaBtn" />
              </a>
            </div>
          </div>
        </section>
      </main>

      {/* Footer is rendered by CourseLayout — no duplicate needed here */}
    </div>
  );
}
