import { teacherOptionDisplay } from './teacher-deck-options';
import type { HeritagePracticePresentation } from './practice-activity-adapters';
import type { TeacherDeck, TeacherDeckEntry } from './teacher-deck';
import type { TeacherPresentation } from './teacher-deck-srs';
import type { PracticeSelection } from './srs';
import { publicRecordId } from './practice-report';
export function selectionReport(selection: PracticeSelection, heritageKind: HeritagePracticePresentation['kind'] = 'mc'): { records: object[]; type: string; item: string } {
  const mode = selection.mode;
  const drill = mode === 'cloze' ? selection.cloze : mode === 'stress' ? selection.stress
    : mode === 'classify' ? selection.classify : mode === 'paradigm' ? selection.paradigm
    : mode === 'synonym' ? selection.synonym : mode === 'paronym' ? selection.paronym
    : mode === 'heritage' ? selection.heritage : mode === 'imperative' ? selection.imperative : undefined;
  const lemma = publicRecordId(selection.lemma);
  const id = drill && publicRecordId(drill);
  const set = mode === 'classify' ? selection.classify?.sets.find((s) => s.setId === selection.classifySetId) : null;
  const suffix = id ? `:${id}${set ? `:${set.setId}` : ''}` : '';
  const expected = `${lemma}:${mode}${suffix}`;
  const valid = lemma && publicRecordId(selection.indexItem) === lemma && selection.itemId === expected
    && (mode !== 'classify' || set) && (!drill || (id && (!('lemmaId' in drill) || drill.lemmaId === lemma)));

  const board = mode === 'matching' || (mode === 'heritage' && heritageKind === 'match-up');
  const records = !valid ? [] : board ? [drill ?? selection.lemma] : [...(drill ? [drill] : []), selection.lemma, selection.indexItem];
  const type = ['choice', 'antonym', 'homonym'].includes(mode) || (!drill && mode !== 'flashcards' && mode !== 'matching')
    ? 'meaning-choice' : mode === 'matching' ? 'matching-pair' : mode === 'heritage' ? `heritage:${heritageKind}` : mode;
  return { records, type, item: board ? publicRecordId(drill ?? selection.lemma) ?? '' : expected };
}

export function teacherReport(deck: TeacherDeck, entry: TeacherDeckEntry, presentation: TeacherPresentation) {
  const drill = presentation.type === 'cloze' ? deck.clozeById.get(presentation.clozeId)
    : presentation.type === 'grammar' ? deck.grammarById.get(presentation.itemId)?.item : null;
  const missing = (presentation.type === 'cloze' || presentation.type === 'grammar') && !drill;
  const setId = presentation.type === 'grammar' ? presentation.setId : undefined;
  const setValid = !setId || (drill && 'sets' in drill && drill.sets.some((set) => set.setId === setId));
  let type: string = presentation.type;
  let absentChoice = false;
  if (presentation.type === 'recognition-choice' || presentation.type === 'production-choice') {
    const choice = presentation.type === 'recognition-choice' ? entry.cards.recognition.choice : entry.cards.production?.choice;
    absentChoice = !choice;
    if (choice) {
      const labels = choice.options.map((option) => teacherOptionDisplay(option.label, choice.direction === 'uk-en' ? 'en' : 'uk'));
      if (new Set(labels).size !== labels.length) type = presentation.type === 'recognition-choice' ? 'recognition-flashcard' : 'production-flashcard';
    }
  }
  return {
    records: absentChoice || missing || !setValid || (drill && drill.entryId !== entry.entryId) ? [] : [...(drill ? [drill] : []), entry],
    type: `teacher:${type}${presentation.type === 'grammar' ? `:${presentation.mode}` : ''}`,
    item: `${publicRecordId(drill ?? entry)}${setId ? `:${setId}` : ''}`,
  };
}
