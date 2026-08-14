import { useMemo, useState } from 'react';
import { ZNO_PRACTICE_DECKS, type ZnoPracticeDeck } from './ZnoPractice';

export type ZnoModeMeta = {
  description: string;
  descriptionEn: string;
  accent: 'blue' | 'teal' | 'purple' | 'orange';
};

export const ZNO_MODE_META: Record<ZnoPracticeDeck['deckId'], ZnoModeMeta> = {
  'zno-stress': {
    description: 'Тренуйте наголос на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Practise stress placement with official ZNO and NMT items.',
    accent: 'teal',
  },
  'zno-paronym': {
    description: 'Розрізняйте пароніми на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Distinguish paronyms with official ZNO and NMT items.',
    accent: 'purple',
  },
  'zno-lexical-norm': {
    description: 'Закріплюйте лексичну норму на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Reinforce lexical norms with official ZNO and NMT items.',
    accent: 'orange',
  },
  'zno-morphological-norm': {
    description: 'Закріплюйте морфологічну норму на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Reinforce morphological norms with official ZNO and NMT items.',
    accent: 'purple',
  },
  'zno-syntactic-norm': {
    description: 'Закріплюйте синтаксичну норму на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Reinforce syntactic norms with official ZNO and NMT items.',
    accent: 'teal',
  },
  'zno-orthography': {
    description: 'Тренуйте орфографію на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Practise orthography with official ZNO and NMT items.',
    accent: 'blue',
  },
  'zno-morphology': {
    description: 'Закріплюйте морфологію на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Reinforce morphology with official ZNO and NMT items.',
    accent: 'purple',
  },
  'zno-syntax': {
    description: 'Тренуйте синтаксис і розділові знаки на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Practise syntax and punctuation with official ZNO and NMT items.',
    accent: 'teal',
  },
  'zno-phonetics': {
    description: 'Тренуйте фонетику на офіційних завданнях ЗНО та НМТ.',
    descriptionEn: 'Practise phonetics with official ZNO and NMT items.',
    accent: 'orange',
  },
};

/** Hover/active ZNO deck overlay for the Practice hub (UI stays in LexiconPractice). */
export function useZnoPracticeOverlay() {
  const [hoveredZnoDeckId, setHoveredZnoDeckId] = useState<ZnoPracticeDeck['deckId'] | null>(null);
  const [activeZnoDeckId, setActiveZnoDeckId] = useState<ZnoPracticeDeck['deckId'] | null>(null);
  const activeZnoDeck = useMemo(
    () => ZNO_PRACTICE_DECKS.find((candidate) => candidate.deckId === activeZnoDeckId) ?? null,
    [activeZnoDeckId],
  );
  return {
    hoveredZnoDeckId,
    setHoveredZnoDeckId,
    activeZnoDeckId,
    setActiveZnoDeckId,
    activeZnoDeck,
  };
}
