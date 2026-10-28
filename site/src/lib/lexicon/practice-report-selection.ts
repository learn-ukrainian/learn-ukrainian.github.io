import type { TeacherDeck, TeacherDeckEntry } from './teacher-deck';
import type { TeacherPresentation } from './teacher-deck-srs';
import type { PracticeSelection } from './srs';
import { publicRecordId } from './practice-report';
export function selectionReport(selection: PracticeSelection): { records: object[]; type: string; item: string } {
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

  return { records: valid ? [...(drill ? [drill] : []), selection.lemma, selection.indexItem] : [], type: ['choice', 'antonym', 'homonym'].includes(mode) || (!drill && mode !== 'flashcards' && mode !== 'matching') ? 'meaning-choice' : mode, item: expected };
}

export function teacherReport(deck: TeacherDeck, entry: TeacherDeckEntry, presentation: TeacherPresentation) {
  const drill = presentation.type === 'cloze' ? deck.clozeById.get(presentation.clozeId)
    : presentation.type === 'grammar' ? deck.grammarById.get(presentation.itemId)?.item : null;
  const missing = (presentation.type === 'cloze' || presentation.type === 'grammar') && !drill;
  const setId = presentation.type === 'grammar' ? presentation.setId : undefined;
  const setValid = !setId || (drill && 'sets' in drill && drill.sets.some((set) => set.setId === setId));
  return {
    records: missing || !setValid || (drill && drill.entryId !== entry.entryId) ? [] : [...(drill ? [drill] : []), entry],
    type: `teacher:${presentation.type}${presentation.type === 'grammar' ? `:${presentation.mode}` : ''}`,
    item: `${publicRecordId(drill ?? entry)}${setId ? `:${setId}` : ''}`,
  };
}
