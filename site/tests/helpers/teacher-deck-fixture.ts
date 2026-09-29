/**
 * Small teacher-table deck fixture in the documented artifact schema
 * (docs/practice/teacher-deck-artifacts.md): `practice-deck.teacher.json` +
 * `practice-cloze.teacher.json`, schema version 1.
 */
import type { TeacherDeckEntry } from '@site/src/lib/lexicon/teacher-deck';

export const FIXTURE_DECK_ID = 'virtual_teacher_table';

interface Row {
  uk: string;
  teacherEn: string;
  en?: string;
  production?: boolean;
  conflicts?: number[];
  aspect?: 'imperf' | 'perf';
}

/** firstSeen = index + 1 (the last row is the newest). */
export const FIXTURE_ROWS: Row[] = [
  { uk: 'Справедливий', teacherEn: 'Fair' },
  { uk: 'Витирати', teacherEn: 'To wipe (impf)', en: 'To wipe (impf.)', aspect: 'imperf' },
  { uk: 'Витерти', teacherEn: 'To wipe (perf)', en: 'To wipe (pf.)', aspect: 'perf' },
  { uk: 'Явно', teacherEn: 'Obviously', production: false, conflicts: [4] },
  { uk: 'Очевидно', teacherEn: 'Obviously; evidently', production: false, conflicts: [3] },
  { uk: 'Таємно', teacherEn: 'Secretly' },
  { uk: 'Чверть', teacherEn: 'Quarter' },
  { uk: 'Підприємець', teacherEn: 'Entrepreneur' },
  { uk: 'Тарган', teacherEn: 'Cockroach' },
  { uk: 'Рогівка', teacherEn: 'Cornea' },
  { uk: 'Камера спостереження', teacherEn: 'Surveillance camera' },
  { uk: 'Цілодобово', teacherEn: 'Around the clock' },
];

export function fixtureEntryId(index: number): string {
  return `tt-${String(index).padStart(12, '0')}`;
}

function choice(index: number, direction: 'recognition' | 'production', rows: Row[]) {
  const entryId = fixtureEntryId(index);
  const row = rows[index]!;
  const label = (r: Row) => (direction === 'recognition' ? r.en ?? r.teacherEn : r.uk);
  const others = [1, 2, 3]
    .map((offset) => (index + offset * 3) % rows.length)
    .filter((other) => other !== index);
  return {
    choiceId: `${entryId}:${direction}:choice`,
    direction: direction === 'recognition' ? 'uk-en' : 'en-uk',
    prompt: direction === 'recognition' ? row.uk : row.en ?? row.teacherEn,
    options: [
      { entryId, label: label(row), kind: 'answer' },
      ...others.map((other) => ({ entryId: fixtureEntryId(other), label: label(rows[other]!), kind: 'distractor' })),
    ],
  };
}

export interface FixtureOptions {
  deckVersion?: string;
  rows?: Row[];
  /** Entry indexes (0-based) that get cloze and grammar items. */
  drillIndexes?: number[];
}

export function buildFixturePayloads(options: FixtureOptions = {}) {
  const rows = options.rows ?? FIXTURE_ROWS;
  const deckVersion = options.deckVersion ?? 'teacher-v1-fixture0001';
  const drillIndexes = new Set(options.drillIndexes ?? [0]);
  const cloze: Record<string, unknown>[] = [];
  const stress: Record<string, unknown>[] = [];
  const classify: Record<string, unknown>[] = [];

  const entries: TeacherDeckEntry[] = rows.map((row, index) => {
    const entryId = fixtureEntryId(index);
    const hasProduction = row.production !== false;
    const drilled = drillIndexes.has(index);
    const clozeIds: string[] = [];
    const grammarItems: { mode: 'stress' | 'classify'; id: string }[] = [];
    if (drilled) {
      for (const sentenceIndex of [0, 1]) {
        const clozeId = `${entryId}:cloze:${sentenceIndex}`;
        clozeIds.push(clozeId);
        cloze.push({
          clozeId,
          entryId,
          cardId: `${entryId}:cloze`,
          lemmaId: row.uk.toLowerCase(),
          lemma: row.uk,
          sentenceFrameId: `tframe_${index}_${sentenceIndex}`,
          sentence: sentenceIndex === 0 ? 'Його рішення були ___.' : 'Це було ___ рішення.',
          blankCase: 'context',
          form: sentenceIndex === 0 ? 'справедливими' : 'справедливе',
          caseRule: { code: 'document-context', labelUk: 'Контекст з документа', labelEn: 'Teacher lesson sentence' },
          options: [
            { optionId: 'opt_ans', label: sentenceIndex === 0 ? 'справедливими' : 'справедливе', lemmaId: 'x', entryId, kind: 'answer' },
            { optionId: 'opt_dec_0', label: 'низькими', lemmaId: 'y', entryId: fixtureEntryId(6), kind: 'distractor' },
            { optionId: 'opt_dec_1', label: 'прихованими', lemmaId: 'z', entryId: fixtureEntryId(7), kind: 'distractor' },
            { optionId: 'opt_dec_2', label: 'розкішними', lemmaId: 'w', entryId: fixtureEntryId(8), kind: 'distractor' },
          ],
          source: 'teacher-lesson',
          attribution: { source: 'teacher-lesson', label: "Teacher's lesson", locator: '2026-06-12' },
        });
      }
      stress.push({
        stressId: `${entryId}:stress`,
        lemmaId: 'справедливий',
        lemma: 'справедливий',
        stressed: 'справедли́вий',
        unstressed: 'справедливий',
        stressIndex: 8,
        nuclei: [
          { index: 3, label: 'а' },
          { index: 5, label: 'е' },
          { index: 8, label: 'и' },
          { index: 10, label: 'и' },
        ],
        source: 'ukrainian-word-stress',
        entryId,
        cardId: `${entryId}:grammar`,
      });
      grammarItems.push({ mode: 'stress', id: `${entryId}:stress` });
      classify.push({
        classifyId: `${entryId}:classify`,
        lemmaId: 'справедливий',
        lemma: 'справедливий',
        sets: [
          {
            setId: 'pos',
            setLabelUk: 'частина мови',
            answer: 'adjective',
            answerLabelUk: 'прикметник',
            options: [
              { value: 'noun', labelUk: 'іменник' },
              { value: 'adjective', labelUk: 'прикметник' },
              { value: 'verb', labelUk: 'дієслово' },
            ],
          },
        ],
        source: 'VESUM',
        entryId,
        cardId: `${entryId}:grammar`,
      });
      grammarItems.push({ mode: 'classify', id: `${entryId}:classify` });
    }
    return {
      entryId,
      key: row.uk.toLowerCase(),
      uk: row.uk,
      en: row.en ?? row.teacherEn,
      teacherEn: row.teacherEn,
      aspect: row.aspect ? { value: row.aspect, basis: 'agree', lemma: row.uk.toLowerCase() } : null,
      firstSeen: index + 1,
      multiword: row.uk.includes(' '),
      sourceRows: [index + 1],
      sourceKeys: [row.uk],
      atlas: { slug: row.uk.toLowerCase(), pos: null, identityConflict: false },
      conflicts: (row.conflicts ?? []).map(fixtureEntryId),
      aspectPartners: [],
      matching: true,
      cards: {
        recognition: { cardId: `${entryId}:recognition`, choice: choice(index, 'recognition', rows) as never },
        production: hasProduction
          ? { cardId: `${entryId}:production`, choice: choice(index, 'production', rows) as never }
          : null,
        cloze: clozeIds.length > 0 ? { cardId: `${entryId}:cloze`, clozeIds } : null,
        grammar: grammarItems.length > 0 ? { cardId: `${entryId}:grammar`, items: grammarItems } : null,
      },
    };
  });

  const deck = {
    schema: 'atlas-practice-teacher-deck',
    schemaVersion: 1,
    deckId: FIXTURE_DECK_ID,
    deckVersion,
    level: 'teacher',
    source: 'teacher-table',
    cardKinds: ['recognition', 'production', 'cloze', 'grammar'],
    clozeFile: 'practice-cloze.teacher.json',
    entries,
    stress,
    paradigm: [],
    classify,
    synonym: [],
  };
  const clozeFile = {
    schema: 'atlas-practice-teacher-cloze',
    schemaVersion: 1,
    deckId: FIXTURE_DECK_ID,
    deckVersion,
    level: 'teacher',
    source: 'teacher-lessons+textbooks',
    cloze,
  };
  return { deck, cloze: clozeFile };
}
