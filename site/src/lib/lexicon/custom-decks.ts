/**
 * Custom Decks & Virtual Special Sets Engine for Practice Hub.
 * Local-First IndexedDB/localStorage implementation with 3-way tombstone support.
 * See ADR-015 for design specification.
 */

import type { PracticeClozeItem } from './srs';

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

export const CUSTOM_SETS_STORAGE_KEY = 'learn_ukrainian_custom_sets_v1';
export const DEVICE_ID_KEY = 'learn_ukrainian_device_id';

export function getDeviceId(): string {
  if (typeof window === 'undefined') return 'server_ssr';
  let deviceId = localStorage.getItem(DEVICE_ID_KEY);
  if (!deviceId) {
    deviceId = `dev_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`;
    localStorage.setItem(DEVICE_ID_KEY, deviceId);
  }
  return deviceId;
}

import teacherClozeData from '../../data/lexicon-teacher-cloze.json';

const defaultTeacherLemmas: string[] = Array.from(
  new Set(
    ((teacherClozeData as { cloze?: Array<{ lemmaId?: string; lemma?: string }> }).cloze ?? [])
      .map((c) => c.lemmaId || c.lemma)
      .filter((k): k is string => Boolean(k)),
  ),
);

/**
 * Returns the built-in, read-only Virtual Special Deck for Teacher Lesson Intake.
 * Derived dynamically from manifest metadata — 0 KB extra user storage.
 */
export function getTeacherLessonVirtualDeck(
  entries?: Array<{ lemma: string; sources?: string[] }>,
): CustomSet {
  const teacherLemmas =
    entries && entries.length > 0
      ? entries
          .filter(
            (e) =>
              e.sources &&
              (e.sources.includes('teacher_lesson') || e.sources.includes('private_teacher_lesson')),
          )
          .map((e) => e.lemma)
      : defaultTeacherLemmas;

  return {
    id: 'virtual_teacher_lesson',
    title: 'Teacher Lesson Collection (610+440)',
    description: 'Special vocabulary deck curated from your private teacher-lesson intake.',
    lemma_keys: teacherLemmas,
    created_at: '2026-07-24T00:00:00.000Z',
    updated_at: new Date().toISOString(),
    device_id: 'system',
    revision: 1,
  };
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
