import type {
  PracticeMode,
  PracticeRating,
  PracticeSelection,
  ReviewLogEntry,
} from './srs';

/**
 * §6b «Ваші слабкі відмінки» — weak-area detection.
 *
 * Pure, React-free, unit-testable helpers that turn the local SRS review log into a
 * ranked list of weaknesses (by grammatical case, practice mode, or heritage kind),
 * plus the predicate that filters a focus session's candidate pool to one weakness.
 *
 * Everything here is client-side: the review log already lives in localStorage
 * (see `ReviewLogEntry`), so no server round-trip is needed.
 */

export type WeakAreaDimension = 'case' | 'mode' | 'heritage';

export interface WeakArea {
  dimension: WeakAreaDimension;
  /** Machine key: case slug (`genitive`), `PracticeMode`, or heritage kind. */
  key: string;
  /** Ukrainian display label for the chip. */
  label: string;
  attempts: number;
  misses: number;
  lapseRate: number;
}

export interface ComputeWeakAreasOptions {
  /** Override the recency window (defaults to `WEAK_AREA_REVIEW_WINDOW`). */
  window?: number;
}

/**
 * How many of the most-recent reviews feed the lapse-rate estimate.
 *
 * Rationale: practice sessions are 10–20 items, and a returning learner runs a handful
 * per week. 200 reviews ≈ the last ~1–2 weeks of practice — recent enough to reflect the
 * learner's *current* ability (not a case they mastered months ago) yet large enough that
 * a single bad session doesn't dominate the estimate. Older reviews are ignored so a
 * long-since-fixed weakness stops surfacing.
 */
export const WEAK_AREA_REVIEW_WINDOW = 200;

/**
 * Minimum total reviews in the window before ANY chips are shown. Below this a learner
 * is too new for the signal to be meaningful — showing chips would be noise. Named +
 * tested per the §6b "no noise for new learners" requirement.
 */
export const WEAK_AREA_MIN_TOTAL_REVIEWS = 20;

/** Minimum attempts on a single bucket before it can qualify as weak (reliability floor). */
export const WEAK_AREA_MIN_BUCKET_ATTEMPTS = 5;

/** A bucket is "weak" once its miss rate reaches this fraction. */
export const WEAK_AREA_MIN_LAPSE_RATE = 0.3;

/** Cap on chips rendered per surface, so the home never clutters. */
export const WEAK_AREA_MAX_CHIPS = 4;

/**
 * Ratings that count as a "miss" for lapse-rate purposes: `again` (clear failure) and
 * `hard` (struggled). A cloze case-miss is recorded as `hard` (see `submitCloze`), so it
 * MUST count here — otherwise the very signal that defines a weak case would be invisible.
 */
const MISS_RATINGS: ReadonlySet<PracticeRating> = new Set<PracticeRating>(['again', 'hard']);

const CASE_LABELS_UK: Record<string, string> = {
  nominative: 'називний',
  genitive: 'родовий',
  dative: 'давальний',
  accusative: 'знахідний',
  instrumental: 'орудний',
  locative: 'місцевий',
  vocative: 'кличний',
};

const MODE_LABELS_UK: Partial<Record<PracticeMode, string>> = {
  flashcards: 'флешкартки',
  matching: 'добір пар',
  choice: 'вибір',
  cloze: 'пропуски',
  paradigm: 'форми',
  stress: 'наголос',
  heritage: 'спадщина',
  synonym: 'синоніми',
  classify: 'групи',
  paronym: 'пароніми',
};

const HERITAGE_KIND_LABELS_UK: Record<string, string> = {
  lexical: 'лексична спадщина',
  sense_restricted: 'звужене значення',
};

export function caseLabelUk(caseKey: string): string {
  return CASE_LABELS_UK[caseKey] ?? caseKey;
}

interface Bucket {
  dimension: WeakAreaDimension;
  key: string;
  attempts: number;
  misses: number;
}

function labelFor(dimension: WeakAreaDimension, key: string): string {
  if (dimension === 'case') return caseLabelUk(key);
  if (dimension === 'mode') return MODE_LABELS_UK[key as PracticeMode] ?? key;
  return HERITAGE_KIND_LABELS_UK[key] ?? key;
}

function bump(map: Map<string, Bucket>, dimension: WeakAreaDimension, key: string, miss: boolean): void {
  const mapKey = `${dimension}:${key}`;
  const bucket = map.get(mapKey) ?? { dimension, key, attempts: 0, misses: 0 };
  bucket.attempts += 1;
  if (miss) bucket.misses += 1;
  map.set(mapKey, bucket);
}

/**
 * Compute the learner's weak areas from their review log.
 *
 * Buckets the most-recent `window` reviews by case (cloze `blankCase`), mode, and
 * heritage kind; keeps only buckets with enough attempts and a high-enough miss rate;
 * returns them ranked by miss rate. Ordering is deterministic (stable), so the same log
 * always yields the same chips.
 */
export function computeWeakAreas(
  reviews: ReviewLogEntry[],
  options: ComputeWeakAreasOptions = {},
): WeakArea[] {
  const window = options.window ?? WEAK_AREA_REVIEW_WINDOW;
  const recent = window > 0 ? reviews.slice(-window) : reviews;
  if (recent.length < WEAK_AREA_MIN_TOTAL_REVIEWS) return [];

  const buckets = new Map<string, Bucket>();
  for (const review of recent) {
    const miss = MISS_RATINGS.has(review.rating);
    bump(buckets, 'mode', review.mode, miss);
    if (review.mode === 'cloze' && review.blankCase) {
      bump(buckets, 'case', review.blankCase, miss);
    }
    if (review.mode === 'heritage' && review.heritageKind) {
      bump(buckets, 'heritage', review.heritageKind, miss);
    }
  }

  const weak: WeakArea[] = [];
  for (const bucket of buckets.values()) {
    if (bucket.attempts < WEAK_AREA_MIN_BUCKET_ATTEMPTS) continue;
    const lapseRate = bucket.misses / bucket.attempts;
    if (lapseRate < WEAK_AREA_MIN_LAPSE_RATE) continue;
    weak.push({
      dimension: bucket.dimension,
      key: bucket.key,
      label: labelFor(bucket.dimension, bucket.key),
      attempts: bucket.attempts,
      misses: bucket.misses,
      lapseRate,
    });
  }

  // Deterministic ranking: worst miss rate first, then most attempts (more evidence),
  // then dimension + key alphabetically so ties never reorder between renders.
  return weak.sort(
    (left, right) =>
      right.lapseRate - left.lapseRate ||
      right.attempts - left.attempts ||
      left.dimension.localeCompare(right.dimension) ||
      left.key.localeCompare(right.key),
  );
}

/** Weak grammatical cases only, capped — the «Ваші слабкі відмінки» chip set. */
export function weakCaseChips(
  reviews: ReviewLogEntry[],
  options: ComputeWeakAreasOptions = {},
): WeakArea[] {
  return computeWeakAreas(reviews, options)
    .filter((area) => area.dimension === 'case')
    .slice(0, WEAK_AREA_MAX_CHIPS);
}

/** Minimal shape a candidate needs to be matched against a weakness. */
type WeaknessCandidate = Pick<PracticeSelection, 'mode' | 'cloze' | 'heritage'>;

/**
 * Does a session candidate belong to the given weakness? This is the poolFilter predicate
 * a focus session composes on top of the normal session constraints — reusing the #4673
 * `poolFilter` hook rather than building a parallel session-start path.
 */
export function matchesWeakness(candidate: WeaknessCandidate, weakness: WeakArea): boolean {
  switch (weakness.dimension) {
    case 'case':
      return candidate.cloze?.blankCase === weakness.key;
    case 'heritage':
      return candidate.heritage?.kind === weakness.key;
    case 'mode':
      return candidate.mode === weakness.key;
    default:
      return false;
  }
}

/** The practice mode a focus session should open in to surface a given weakness. */
export function focusModeForWeakness(weakness: WeakArea): PracticeMode | 'mixed' {
  if (weakness.dimension === 'case') return 'cloze';
  if (weakness.dimension === 'heritage') return 'heritage';
  return weakness.key as PracticeMode;
}
