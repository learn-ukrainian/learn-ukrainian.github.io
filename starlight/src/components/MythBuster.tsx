import React from 'react';

interface MythBusterProps {
  claim: string;
  claimSource?: string;
  truth: string;
  truthSource?: string;
}

/**
 * Myth vs truth callout for seminar tracks.
 * Presents an imperial/Soviet claim alongside Ukrainian evidence.
 *
 * Usage in MDX:
 *   <MythBuster
 *     claim="Ukrainian is a dialect of Russian"
 *     claimSource="Russian imperial historiography"
 *     truth="Ukrainian has distinct phonology, grammar, and vocabulary..."
 *     truthSource="Shevelov, A Historical Phonology of the Ukrainian Language"
 *   />
 */
export default function MythBuster({ claim, claimSource, truth, truthSource }: MythBusterProps) {
  return (
    <div className="myth-box">
      <div className="myth-box-header">
        <span aria-hidden="true">&#x1F6A8;</span>
        <span>Myth vs Truth</span>
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
