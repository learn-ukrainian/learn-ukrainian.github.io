import type { ReactNode } from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">
          {siteConfig.tagline}
        </p>
        <div className={styles.buttons}>
          <Link
            className={clsx('button button--lg', styles.primaryButton)}
            to="/docs/a1">
            Start Learning (A1)
          </Link>
          <Link
            className={clsx('button button--lg', styles.secondaryButton)}
            to="#levels">
            View All Levels
          </Link>
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
        618 modules aligned with CEFR and Ukrainian State Standards.
      </>
    ),
  },
];

function Feature({ title, emoji, description }: FeatureItem) {
  return (
    <div className={clsx('col col--3')}>
      <div className={styles.featureCard}>
        <div className={styles.featureEmoji}>{emoji}</div>
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

function LevelCard({ level, name, description, modules, color, isTrack }: {
  level: string;
  name: string;
  description: string;
  modules: number;
  color: string;
  isTrack?: boolean;
}) {
  return (
    <div className={clsx('col col--4')}>
      <Link to={`/docs/${level.toLowerCase()}`} className={styles.levelLink}>
        <div className={styles.levelCard}>
          <span className={styles.levelBadge} style={{ background: color }}>
            {level}
          </span>
          <Heading as="h3">{name}</Heading>
          <p>{description}</p>
          <span className={styles.moduleCount}>{modules} modules</span>
        </div>
      </Link>
    </div>
  );
}

export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title="Learn Ukrainian"
      description="A comprehensive A1-C2 Ukrainian language curriculum with interactive lessons, cultural context, and theory-first learning.">
      <HomepageHeader />
      <main>
        <section className={styles.features}>
          <div className="container">
            <div className="row">
              {FeatureList.map((props, idx) => (
                <Feature key={idx} {...props} />
              ))}
            </div>
          </div>
        </section>

        <section id="levels" className={styles.levels}>
          <div className="container">
            <Heading as="h2" className={styles.sectionTitle}>
              Core Levels
            </Heading>
            <div className="row">
              <LevelCard
                level="A1"
                name="Beginner"
                description="Cyrillic alphabet, basic phrases, simple grammar"
                modules={34}
                color="#2E7D32"
              />
              <LevelCard
                level="A2"
                name="Elementary"
                description="All 7 cases, verb aspects, comparison"
                modules={58}
                color="#1565C0"
              />
              <LevelCard
                level="B1"
                name="Intermediate"
                description="Aspect mastery, motion verbs, complex sentences"
                modules={91}
                color="#E65100"
              />
              <LevelCard
                level="B2"
                name="Upper-Intermediate"
                description="Grammar mastery, phraseology, history, biographies"
                modules={145}
                color="#C2185B"
              />
              <LevelCard
                level="C1"
                name="Advanced"
                description="Academic focus, stylistics, folk culture, literature"
                modules={196}
                color="#7B1FA2"
              />
              <LevelCard
                level="C2"
                name="Mastery"
                description="Stylistic perfection, literary mastery, professional prep"
                modules={100}
                color="#C62828"
              />
            </div>

            <Heading as="h2" className={clsx(styles.sectionTitle, 'margin-top--lg')}>
              Specialization Tracks
            </Heading>
            <div className="row">
              <LevelCard
                level="LIT"
                name="Literature"
                description="Classical Ukrainian literature and philological analysis"
                modules={30}
                color="#5D4037"
                isTrack
              />
            </div>
          </div>
        </section>

        <section className={styles.cta}>
          <div className="container">
            <div className={styles.ctaContent}>
              <Heading as="h2">Ready to Start?</Heading>
              <p>Begin your Ukrainian journey today with our comprehensive curriculum.</p>
              <Link
                className="button button--primary button--lg"
                to="/docs/a1">
                Start with A1
              </Link>
            </div>
          </div>
        </section>

      </main>
    </Layout>
  );
}
