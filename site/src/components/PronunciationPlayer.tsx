import { useEffect, useRef } from 'react';
import { mountPronunciationPlayer } from '../lib/lexicon/pronunciation-player';

interface PronunciationPlayerProps {
  /**
   * @schemaDescription Source lemma to look up in the generated pronunciation slice.
   * @ukrainianText true
   */
  lemma: string;
  /** @schemaDescription Chrome locale; defaults to the document locale. */
  locale?: 'en' | 'uk';
}

/** A small controller also boots this markup on SSR-only Atlas pages. */
export default function PronunciationPlayer({ lemma, locale }: PronunciationPlayerProps) {
  const root = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (root.current) return mountPronunciationPlayer(root.current);
  }, [lemma, locale]);
  return (
    <span ref={root} data-pronunciation-lemma={lemma} data-locale={locale} style={{ display: 'inline-block', fontSize: '1rem' }}>
      <button type="button" hidden style={{ minHeight: 44, padding: '0.4rem 0.7rem', cursor: 'pointer' }} />
      <span role="status" aria-live="polite" style={{ fontSize: '0.85rem' }} />
    </span>
  );
}
