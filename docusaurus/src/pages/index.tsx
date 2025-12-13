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
          <span className={styles.heroSubtitle}>Theory-First</span> Ukrainian Language Learning
        </p>
        <div className={styles.buttons}>
          <Link
            className={clsx('button button--lg', styles.primaryButton)}
            to="/docs/a1">
            Start Learning
          </Link>
          <Link
            className={clsx('button button--lg', styles.secondaryButton)}
            to="/docs/intro">
            View Curriculum
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
        480 modules aligned with CEFR and Ukrainian State Standards.
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

function LevelCard({ level, name, description, modules, color }: {
  level: string;
  name: string;
  description: string;
  modules: number;
  color: string;
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

        <section className={styles.levels}>
          <div className="container">
            <Heading as="h2" className={styles.sectionTitle}>
              Choose Your Level
            </Heading>
            <div className="row">
              <LevelCard
                level="A1"
                name="Beginner"
                description="Cyrillic alphabet, basic phrases, simple grammar"
                modules={30}
                color="#2E7D32"
              />
              <LevelCard
                level="A2"
                name="Elementary"
                description="All 7 cases, verb aspects, comparison"
                modules={50}
                color="#1565C0"
              />
              <LevelCard
                level="B1"
                name="Intermediate"
                description="Aspect mastery, motion verbs, complex sentences"
                modules={80}
                color="#E65100"
              />
              <LevelCard
                level="B2"
                name="Upper-Intermediate"
                description="Literature, academic, professional contexts"
                modules={125}
                color="#C2185B"
              />
              <LevelCard
                level="C1"
                name="Advanced"
                description="Full complexity, specialized topics"
                modules={115}
                color="#7B1FA2"
              />
              <LevelCard
                level="C2"
                name="Mastery"
                description="Native-level proficiency"
                modules={80}
                color="#C62828"
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
