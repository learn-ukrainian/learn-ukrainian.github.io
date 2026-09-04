/**
 * Custom Decks & Virtual Special Sets Engine for Practice Hub.
 * Local-First IndexedDB/localStorage implementation with 3-way tombstone support.
 * See ADR-015 for design specification.
 */

import type { PracticeClozeItem } from './srs';
import teacherTableData from '../../data/lexicon-teacher-table-deck.json';
// #7671: pre-derived at build time (scripts/generate-teacher-lesson-keys.ts) from the
// same filterTeacherClozeItems rule applied to the ~6.8MB lexicon-teacher-cloze.json
// source. Importing that raw source here used to bundle the entire file into this
// client-only island just to compute a lemma-key list — this small (~60KB) derived
// file is the deduplicated result, and the actual teacher-cloze content is served
// separately, on demand, as the practice-cloze.teacher.json runtime shard.
import defaultTeacherLemmasData from '../../data/lexicon-teacher-lesson-keys.json';
import { filterTeacherClozeItems } from './teacher-cloze-filter';

export { filterTeacherClozeItems };

export interface CustomSet {
  id: string;
  title: string;
  description?: string;
  lemma_keys: string[];
  cloze_items?: PracticeClozeItem[];
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  device_id: string;
  revision: number;
}

export interface VirtualSpecialSet extends CustomSet {
  titleUk: string;
}

export const CUSTOM_SETS_STORAGE_KEY = 'learn_ukrainian_custom_sets_v1';
export const DEVICE_ID_KEY = 'learn_ukrainian_device_id';

let inMemoryDeviceId: string | null = null;

/**
 * Returns one session-stable fallback id when localStorage is blocked
 * (private browsing, SecurityError) so saves do not crash on the first write.
 */
function newDeviceId(): string {
  if (!inMemoryDeviceId) {
    inMemoryDeviceId = `dev_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`;
  }
  return inMemoryDeviceId;
}

export function getDeviceId(): string {
  if (typeof window === 'undefined') return 'server_ssr';
  try {
    const stored = localStorage.getItem(DEVICE_ID_KEY);
    if (stored) return stored;
    const deviceId = newDeviceId();
    localStorage.setItem(DEVICE_ID_KEY, deviceId);
    return deviceId;
  } catch (err) {
    console.warn('localStorage unavailable; using in-memory device id', err);
    return newDeviceId();
  }
}

const defaultTeacherLemmas: string[] = defaultTeacherLemmasData;

const lowercaseLemmaKeySetCache = new WeakMap<readonly string[], ReadonlySet<string>>();

/**
 * Returns a stable, case-normalized membership set for one deck's immutable key list.
 * Practice selection performs this lookup for every candidate, so rebuilding the set
 * there turns a curated deck into quadratic work.
 */
export function getCachedLowercaseLemmaKeySet(keys: readonly string[]): ReadonlySet<string> {
  const cached = lowercaseLemmaKeySetCache.get(keys);
  if (cached) return cached;
  const normalized = new Set(keys.map((key) => key.toLowerCase()));
  lowercaseLemmaKeySetCache.set(keys, normalized);
  return normalized;
}

const defaultTeacherLessonVirtualDeck: CustomSet = {
  id: 'virtual_teacher_lesson',
  title: 'Curated Deck',
  description: 'Special vocabulary deck curated from your private teacher-lesson intake.',
  lemma_keys: defaultTeacherLemmas,
  created_at: '2026-07-24T00:00:00.000Z',
  updated_at: '2026-07-24T00:00:00.000Z',
  device_id: 'system',
  revision: 1,
};

const defaultTeacherTableVirtualDeck: VirtualSpecialSet = {
  id: teacherTableData.id,
  title: teacherTableData.title,
  titleUk: teacherTableData.titleUk,
  description: teacherTableData.description,
  lemma_keys: teacherTableData.lemma_keys,
  created_at: '2026-08-11T00:00:00.000Z',
  updated_at: '2026-08-11T00:00:00.000Z',
  device_id: 'system',
  revision: 1,
};

/**
 * Source tags used by `lexicon-teacher-curated-membership.json` (#6544).
 * Older filter names (`teacher_lesson` / `private_teacher_lesson`) match zero
 * members — keep this list aligned with the membership file's real vocabulary.
 */
export const TEACHER_CURATED_MEMBERSHIP_SOURCES = ['teacher_inventory', 'homework'] as const;

function isTeacherCuratedMembershipSource(source: string): boolean {
  return (TEACHER_CURATED_MEMBERSHIP_SOURCES as readonly string[]).includes(source);
}

/**
 * Returns the built-in, read-only Virtual Special Deck for Teacher Lesson Intake.
 * Its module data is cached — 0 KB extra user storage or hot-path JSON scans.
 *
 * TODO(#6544): operator decision — whether the local ~1k practice-admission
 * subset should be its own selectable deck vs this ~5k Curated Deck union.
 */
export function getTeacherLessonVirtualDeck(
  entries?: Array<{ lemma: string; sources?: string[] }>,
): CustomSet {
  if (!entries || entries.length === 0) return defaultTeacherLessonVirtualDeck;

  const teacherLemmas = entries
    .filter((e) => e.sources?.some(isTeacherCuratedMembershipSource))
    .map((e) => e.lemma);

  return {
    ...defaultTeacherLessonVirtualDeck,
    lemma_keys: teacherLemmas,
    updated_at: new Date().toISOString(),
  };
}

/**
 * Returns the built-in Practice set extracted only from the teacher master
 * table. It intentionally has no cloze or broader Curated Deck membership.
 */
export function getTeacherTableVirtualDeck(): VirtualSpecialSet {
  return defaultTeacherTableVirtualDeck;
}

export function readLocalCustomSets(): CustomSet[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(CUSTOM_SETS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((s) => !s.deleted_at) : [];
  } catch {
    return [];
  }
}

export function saveLocalCustomSet(set: Omit<CustomSet, 'device_id' | 'revision' | 'updated_at'> & { id?: string }): CustomSet {
  const all = readLocalCustomSetsAllInternal();
  const now = new Date().toISOString();
  const deviceId = getDeviceId();

  const id = set.id || `set_${Math.random().toString(36).substring(2, 9)}_${Date.now()}`;
  const existingIdx = all.findIndex((s) => s.id === id);

  const updatedSet: CustomSet = {
    id,
    title: set.title,
    description: set.description || '',
    lemma_keys: set.lemma_keys,
    cloze_items: set.cloze_items || (existingIdx >= 0 ? all[existingIdx].cloze_items : undefined),
    created_at: existingIdx >= 0 ? all[existingIdx].created_at : now,
    updated_at: now,
    device_id: deviceId,
    revision: existingIdx >= 0 ? (all[existingIdx].revision || 0) + 1 : 1,
  };

  if (existingIdx >= 0) {
    all[existingIdx] = updatedSet;
  } else {
    all.push(updatedSet);
  }

  writeLocalCustomSetsAllInternal(all);
  return updatedSet;
}

export function deleteLocalCustomSet(id: string): void {
  const all = readLocalCustomSetsAllInternal();
  const set = all.find((s) => s.id === id);
  if (set) {
    set.deleted_at = new Date().toISOString();
    set.updated_at = set.deleted_at;
    set.revision = (set.revision || 0) + 1;
    writeLocalCustomSetsAllInternal(all);
  }
}

function readLocalCustomSetsAllInternal(): CustomSet[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(CUSTOM_SETS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeLocalCustomSetsAllInternal(sets: CustomSet[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(CUSTOM_SETS_STORAGE_KEY, JSON.stringify(sets));
  } catch (err) {
    console.warn('Failed to write custom sets to localStorage', err);
  }
}
