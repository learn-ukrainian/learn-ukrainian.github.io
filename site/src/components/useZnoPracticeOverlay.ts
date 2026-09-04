import { useEffect, useState } from 'react';
import { loadZnoDeck, type ZnoPracticeDeck } from './ZnoPractice';

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

/**
 * Hover/active ZNO deck overlay for the Practice hub (UI stays in LexiconPractice).
 *
 * #7671: a deck's full task content is no longer eagerly bundled — opening one
 * loads its dedicated chunk via `loadZnoDeck`, so `activeZnoDeck` starts `null`
 * for the id just selected until that load resolves (`activeZnoDeckLoading`
 * tracks that gap for the caller's loading affordance).
 *
 * #7673 CF: a rejected chunk load (offline, stale deploy after a redeploy
 * shifts asset hashes) must not leave `activeZnoDeckLoading` stuck `true`
 * forever — `activeZnoDeckError` surfaces that failure and `retryActiveZnoDeck`
 * lets the caller retry the same deck without leaving the overlay.
 */
export function useZnoPracticeOverlay() {
  const [hoveredZnoDeckId, setHoveredZnoDeckId] = useState<ZnoPracticeDeck['deckId'] | null>(null);
  const [activeZnoDeckId, setActiveZnoDeckId] = useState<ZnoPracticeDeck['deckId'] | null>(null);
  const [activeZnoDeck, setActiveZnoDeck] = useState<ZnoPracticeDeck | null>(null);
  const [activeZnoDeckError, setActiveZnoDeckError] = useState(false);
  const [retryToken, setRetryToken] = useState(0);

  useEffect(() => {
    // Reset synchronously so a still-loading new id never renders under the
    // previously loaded deck's content (or a previous id's error).
    setActiveZnoDeck(null);
    setActiveZnoDeckError(false);
    if (!activeZnoDeckId) return;
    let cancelled = false;
    loadZnoDeck(activeZnoDeckId)
      .then((deck) => {
        if (!cancelled) setActiveZnoDeck(deck);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        console.error(`[practice] failed to load ZNO deck "${activeZnoDeckId}"`, err);
        setActiveZnoDeckError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [activeZnoDeckId, retryToken]);

  return {
    hoveredZnoDeckId,
    setHoveredZnoDeckId,
    activeZnoDeckId,
    setActiveZnoDeckId,
    activeZnoDeck,
    activeZnoDeckLoading: activeZnoDeckId !== null && activeZnoDeck === null && !activeZnoDeckError,
    activeZnoDeckError,
    retryActiveZnoDeck: () => setRetryToken((n) => n + 1),
  };
}
