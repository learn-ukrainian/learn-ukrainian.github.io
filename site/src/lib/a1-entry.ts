import arc from '../data/arc-a1.json';
import type { ArcPosition } from './arc';
import type { ChromeKey } from './i18n/chrome';

type Publication = Pick<ArcPosition, 'position' | 'lesson_numbers' | 'built_lessons'>;

/** A beginner needs the whole opening module, not a published lesson later in the arc.
 * built_lessons comes from the arc generator's existing page + passed-gates check.
 */
export function deriveA1PrimaryHref(positions: readonly Publication[]): '/a1/' | '/a1-v1/' {
  const first = positions.find((position) => position.position === 1);
  return first && first.lesson_numbers.length > 0
    && first.lesson_numbers.every((number) => first.built_lessons.includes(number))
    ? '/a1/' : '/a1-v1/';
}

type Edition = {
  id: string;
  href: string;
  titleKey: ChromeKey;
  actionKey: ChromeKey;
  navKey: ChromeKey;
  descriptionKey: ChromeKey;
  statusKey: ChromeKey;
};

export const a1PrimaryHref = deriveA1PrimaryHref(arc.positions);
export const a1NewIsPrimary = a1PrimaryHref === '/a1/';
const current = {
  id: 'a1', href: '/a1/',
  titleKey: a1NewIsPrimary ? 'home.track.a1New' : 'home.track.a1Preparing',
  actionKey: a1NewIsPrimary ? 'home.actionStartA1' : 'home.actionPreviewA1',
  navKey: a1NewIsPrimary ? 'nav.a1' : 'home.track.a1Preparing',
  descriptionKey: a1NewIsPrimary ? 'home.cardA1PublishedDesc' : 'home.cardA1Desc',
  statusKey: a1NewIsPrimary ? 'status.available' : 'status.planned',
} satisfies Edition;
export const a1PreviousEdition = {
  id: 'a1-v1', href: '/a1-v1/',
  titleKey: a1NewIsPrimary ? 'home.track.a1Previous' : 'home.track.a1Available',
  actionKey: 'home.actionOpenA1Previous',
  navKey: a1NewIsPrimary ? 'nav.a1Previous' : 'nav.a1',
  descriptionKey: 'home.cardA1PreviousDesc', statusKey: 'status.released',
} satisfies Edition;

export const a1PrimaryEdition = a1NewIsPrimary ? current : a1PreviousEdition;
export const a1SecondaryEdition = a1NewIsPrimary ? a1PreviousEdition : current;

export function levelEntryHref(level: string): string {
  return level.toLowerCase() === 'a1' ? a1PrimaryHref : `/${level.toLowerCase()}/`;
}
