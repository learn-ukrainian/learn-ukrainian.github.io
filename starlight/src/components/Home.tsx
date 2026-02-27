import React from 'react';
import type { ReactNode } from 'react';
import styles from './Home.module.css';

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
        1,468 modules aligned with CEFR and Ukrainian State Standards.
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
                modules={44}
                color="#2E7D32"
              />
              <LevelCard
                level="A2"
                name="Elementary"
                description="All 7 cases, verb aspects, practical scenarios"
                modules={71}
                color="#1565C0"
              />
              <LevelCard
                level="B1"
                name="Intermediate"
                description="Aspect mastery, motion verbs, communication skills"
                modules={94}
                color="#E65100"
              />
              <LevelCard
                level="B2"
                name="Upper-Intermediate"
                description="Passive voice, registers, professional basics"
                modules={95}
                color="#C2185B"
              />
              <LevelCard
                level="C1"
                name="Advanced"
                description="Stylistics, literature, complex grammar"
                modules={108}
                color="#7B1FA2"
              />
              <LevelCard
                level="C2"
                name="Mastery"
                description="Native-level proficiency"
                modules={101}
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
                modules={140}
                color="#795548"
              />
              <LevelCard
                level="ISTORIOHRAFIIA"
                name="Historiography"
                description="Primary sources, imperial mechanisms, interethnic relations"
                modules={136}
                color="#6D4C41"
              />
              <LevelCard
                level="BIO"
                name="Biographies"
                description="Notable Ukrainians through history"
                modules={172}
                color="#607D8B"
              />
              <LevelCard
                level="B2-PRO"
                name="Professional"
                description="Business communication, technical domains"
                modules={40}
                color="#455A64"
              />
              <LevelCard
                level="C1-PRO"
                name="Professional Mastery"
                description="Executive, academic, specialized"
                modules={50}
                color="#37474F"
              />
              <LevelCard
                level="LIT"
                name="Literature"
                description="Ukrainian classics and literary analysis"
                modules={217}
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
                modules={100}
                color="#8D6E63"
              />
              <LevelCard
                level="RUTH"
                name="Ruthenian"
                description="Middle Ukrainian (XIV-XVIII century)"
                modules={100}
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

      <footer className={styles.siteFooter}>
        <div className="container" style={{maxWidth: '1200px', margin: '0 auto', padding: '0 20px'}}>
          <div className={styles.footerLinks}>
            <div className={styles.footerCol}>
              <h4>Learn</h4>
              <ul>
                <li><a href="/a1/">A1 - Beginner</a></li>
                <li><a href="/a2/">A2 - Elementary</a></li>
                <li><a href="/b1/">B1 - Intermediate</a></li>
              </ul>
            </div>
            <div className={styles.footerCol}>
              <h4>Advanced</h4>
              <ul>
                <li><a href="/b2/">B2 - Upper-Intermediate</a></li>
                <li><a href="/c1/">C1 - Advanced</a></li>
                <li><a href="/c2/">C2 - Mastery</a></li>
              </ul>
            </div>
            <div className={styles.footerCol}>
              <h4>Tracks</h4>
              <ul>
                <li><a href="/hist/">HIST - History</a></li>
                <li><a href="/bio/">BIO - Biographies</a></li>
                <li><a href="/lit/">LIT - Literature</a></li>
              </ul>
            </div>
            <div className={styles.footerCol}>
              <h4>More</h4>
              <ul>
                <li><a href="https://github.com/learn-ukrainian/learn-ukrainian.github.io" target="_blank" rel="noopener">GitHub</a></li>
              </ul>
            </div>
          </div>
          <div className={styles.footerCopyright}>
            Learn Ukrainian © 2026 — Слава Україні! 🇺🇦
          </div>
        </div>
      </footer>
    </div>
  );
}
