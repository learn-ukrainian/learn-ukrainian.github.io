import React from 'react';
import type { ReactNode } from 'react';
import styles from './Home.module.css';
import curriculumStats from '../data/curriculum-stats.json';

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
          <a
            className={styles.primaryButton}
            href="/a1/">
            Start Learning (A1)
          </a>
          <a
            className={styles.secondaryButton}
            href="#levels">
            View All Levels
          </a>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  title: string;
  emoji: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Theory-First Approach',
    emoji: '📚',
    description: (
      <>
        Deep grammar explanations, cultural context, and historical insights.
        Understand the <strong>why</strong> behind the language.
      </>
    ),
  },
  {
    title: 'Interactive Activities',
    emoji: '🎮',
    description: (
      <>
        Quizzes, matching exercises, fill-in-the-blank, and more.
        Practice what you learn with engaging activities.
      </>
    ),
  },
  {
    title: 'Cultural Immersion',
    emoji: '🌍',
    description: (
      <>
        Authentic materials, folklore, literature, and a decolonization lens.
        Learn Ukrainian in its full cultural context.
      </>
    ),
  },
  {
    title: 'Complete A1-C2 Pathway',
    emoji: '🎓',
    description: (
      <>
        From absolute beginner to native-level proficiency.
        {(curriculumStats as any)._total.toLocaleString()} modules aligned with CEFR and Ukrainian State Standards.
      </>
    ),
  },
];

function Feature({ title, emoji, description }: FeatureItem) {
  return (
    <div style={{flex: '1 1 250px'}}>
      <div className={styles.featureCard}>
        <div className={styles.featureEmoji}>{emoji}</div>
        <h3 style={{margin: '0.5rem 0'}}>{title}</h3>
        <p style={{margin: 0}}>{description}</p>
      </div>
    </div>
  );
}

function LevelCard({ level, name, description, modules, color }: {
  level: string;
  name: string;
  description: string;
  modules: number;
  color: string;
}) {
  return (
    <div style={{flex: '1 1 300px', marginBottom: '1.5rem'}}>
      <a href={`/${level.toLowerCase()}/`} className={styles.levelLink}>
        <div className={styles.levelCard} data-level={level.toLowerCase()}>
          <span className={styles.levelBadge} style={{ background: color }}>
            {level}
          </span>
          <h3 style={{marginTop: '10px'}}>{name}</h3>
          <p style={{margin: '0 0 1rem 0'}}>{description}</p>
          <span className={styles.moduleCount}>{modules} modules</span>
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
              Core Levels
            </h2>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '20px'}}>
              <LevelCard
                level="A1"
                name="Beginner"
                description="Cyrillic alphabet, basic phrases, practical scenarios"
                modules={mc('a1')}
                color="#2E7D32"
              />
              <LevelCard
                level="A2"
                name="Elementary"
                description="All 7 cases, verb aspects, practical scenarios"
                modules={mc('a2')}
                color="#1565C0"
              />
              <LevelCard
                level="B1"
                name="Intermediate"
                description="Aspect mastery, motion verbs, communication skills"
                modules={mc('b1')}
                color="#E65100"
              />
              <LevelCard
                level="B2"
                name="Upper-Intermediate"
                description="Passive voice, registers, professional basics"
                modules={mc('b2')}
                color="#C2185B"
              />
              <LevelCard
                level="C1"
                name="Advanced"
                description="Stylistics, literature, complex grammar"
                modules={mc('c1')}
                color="#7B1FA2"
              />
              <LevelCard
                level="C2"
                name="Mastery"
                description="Native-level proficiency"
                modules={mc('c2')}
                color="#C62828"
              />
            </div>

            <h2 className={styles.sectionTitle} style={{marginTop: '4rem'}}>
              Specialization Tracks
            </h2>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '20px'}}>
              <LevelCard
                level="HIST"
                name="History"
                description="Ukrainian history from origins to present"
                modules={mc('hist')}
                color="#795548"
              />
              <LevelCard
                level="ISTORIO"
                name="Historiography"
                description="Primary sources, imperial mechanisms, interethnic relations"
                modules={mc('istorio')}
                color="#6D4C41"
              />
              <LevelCard
                level="BIO"
                name="Biographies"
                description="Notable Ukrainians through history"
                modules={mc('bio')}
                color="#607D8B"
              />
              <LevelCard
                level="B2-PRO"
                name="Professional"
                description="Business communication, technical domains"
                modules={mc('b2-pro')}
                color="#455A64"
              />
              <LevelCard
                level="C1-PRO"
                name="Professional Mastery"
                description="Executive, academic, specialized"
                modules={mc('c1-pro')}
                color="#37474F"
              />
              <LevelCard
                level="LIT"
                name="Literature"
                description="Ukrainian classics and literary analysis"
                modules={mc('lit')}
                color="#5D4037"
              />
            </div>

            <h2 className={styles.sectionTitle} style={{marginTop: '4rem'}}>
              Linguistic Seminars
            </h2>
            <p className={styles.sectionSubtitle}>
              Advanced historical linguistics for scholars and enthusiasts
            </p>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center'}}>
              <LevelCard
                level="OES"
                name="Old East Slavic"
                description="Language of Kyivan Rus' (X-XIII century)"
                modules={103}
                color="#8D6E63"
              />
              <LevelCard
                level="RUTH"
                name="Ruthenian"
                description="Middle Ukrainian (XIV-XVIII century)"
                modules={115}
                color="#A1887F"
              />
            </div>
          </div>
        </section>

        <section className={styles.cta}>
          <div className="container" style={{maxWidth: '1200px', margin: '0 auto', padding: '0 20px'}}>
            <div className={styles.ctaContent}>
              <h2 style={{marginTop: 0}}>Ready to Start?</h2>
              <p>Begin your Ukrainian journey today with our comprehensive curriculum.</p>
              <a
                className={styles.primaryButton}
                href="/a1/">
                Start with A1
              </a>
            </div>
          </div>
        </section>
      </main>

      {/* Footer is rendered by Starlight's Footer.astro override — no duplicate needed here */}
    </div>
  );
}
