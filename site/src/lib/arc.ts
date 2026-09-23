/** Types and helpers for the generated arc data (`site/src/data/arc-<level>.json`, #8397). */

import type { ChromeKey } from './i18n/chrome';

export type ArcState = 'planned' | 'plan_reviewed' | 'built' | 'reviewed';

export type ArcScope = {
  letters: number;
  grammar_points: number;
  core_lemmas: number;
};

export type ArcPosition = {
  position: number;
  slug: string;
  phase: string;
  title_uk: string | null;
  title_en: string;
  job: string;
  skills: string[];
  is_checkpoint: boolean;
  est_lessons: number;
  lessons: number | null;
  built_lessons: number[];
  lesson_numbers: number[];
  lesson_titles: string[];
  scope: ArcScope | null;
  state: ArcState;
  previous_edition_href: string | null;
};

export type ArcData = { level: string; positions: ArcPosition[] };

/** Chrome key for each state; `planned` and `reviewed` reuse the existing status keys. */
export const ARC_STATE_KEY: Record<ArcState, ChromeKey> = {
  planned: 'status.planned',
  plan_reviewed: 'arc.state.plan_reviewed',
  built: 'arc.state.built',
  reviewed: 'status.reviewed',
};

export function moduleHref(level: string, slug: string): string {
  return `/${level}/${slug}/`;
}

export function lessonHref(level: string, slug: string, n: number): string {
  return `/${level}/${slug}/${n}/`;
}

/** Positions grouped by `phase`, in first-seen (arc) order. */
export function groupByPhase(positions: ArcPosition[]): { phase: string; items: ArcPosition[] }[] {
  const groups = new Map<string, ArcPosition[]>();
  for (const position of positions) {
    const items = groups.get(position.phase) ?? [];
    items.push(position);
    groups.set(position.phase, items);
  }
  return [...groups].map(([phase, items]) => ({ phase, items }));
}
