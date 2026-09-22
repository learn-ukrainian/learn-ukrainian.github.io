import { useEffect, useRef } from 'react';
import { mountPronunciationPlayer } from '../lib/lexicon/pronunciation-player';

interface PronunciationPlayerProps {
  /**
   * @schemaDescription Ukrainian source lemma for on-device speech or an optional local clip.
   * @ukrainianText true
   */
  lemma: string;
  /** @schemaDescription Chrome locale; defaults to the document locale. */
  locale?: 'en' | 'uk';
  /**
   * @schemaDescription Fallback behavior when audio clip or manifest is unavailable:
   * 'speech' (default, for Word Atlas) falls back to on-device SpeechSynthesis.
   * 'hide' (for Flashcards) keeps the audio button hidden.
   * 'disable' renders the audio button disabled.
   */
  fallback?: 'speech' | 'hide' | 'disable';
}

/** A small controller also boots this markup on SSR-only Atlas pages. */
export default function PronunciationPlayer({ lemma, locale, fallback = 'speech' }: PronunciationPlayerProps) {
  const root = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (root.current) return mountPronunciationPlayer(root.current);
  }, [lemma, locale, fallback]);
  return (
    <span
      ref={root}
      data-pronunciation-lemma={lemma}
      data-locale={locale}
      data-fallback={fallback === 'speech' ? undefined : fallback}
      style={{ display: 'inline-block', fontSize: '1rem' }}
    >
      <button type="button" hidden style={{ minHeight: 44, padding: '0.4rem 0.7rem', cursor: 'pointer' }} />
      <span role="status" aria-live="polite" style={{ fontSize: '0.85rem' }} />
    </span>
  );
}
