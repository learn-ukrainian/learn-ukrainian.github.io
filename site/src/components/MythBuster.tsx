import React from 'react';

interface MythBusterProps {
  /**
   * @schemaDescription Title shown in the myth-box header.
   * @ukrainianText true
   */
  title?: string;
  /**
   * @schemaDescription Claim value consumed by this component.
   * @ukrainianText true
   */
  claim: string;
  /**
   * @schemaDescription Claim Source value consumed by this component.
   * @ukrainianText false
   */
  claimSource?: string;
  /**
   * @schemaDescription Truth value consumed by this component.
   * @ukrainianText true
   */
  truth: string;
  /**
   * @schemaDescription Truth Source value consumed by this component.
   * @ukrainianText false
   */
  truthSource?: string;
}

/**
 * Myth-box callout for seminar and folk tracks.
 * Presents an imperial/Soviet claim alongside Ukrainian evidence.
 *
 * Usage in MDX:
 *   <MythBuster
 *     title="Руйнуємо міф"
 *     claim="Ukrainian is a dialect of Russian"
 *     claimSource="Russian imperial historiography"
 *     truth="Ukrainian has distinct phonology, grammar, and vocabulary..."
 *     truthSource="Shevelov, A Historical Phonology of the Ukrainian Language"
 *   />
 */
export default function MythBuster({ title = 'Руйнуємо міф', claim, claimSource, truth, truthSource }: MythBusterProps) {
  return (
    <div className="myth-box">
      <div className="myth-box-header">
        <span aria-hidden="true">&#x2694;</span>
        <span>{title}</span>
      </div>
      <div className="myth-claim">
        {claim}
        {claimSource && <div className="myth-source">{claimSource}</div>}
      </div>
      <div className="myth-truth">
        {truth}
        {truthSource && <div className="myth-source">{truthSource}</div>}
      </div>
    </div>
  );
}
