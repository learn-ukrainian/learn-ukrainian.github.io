import { loadPinnedWordCardRelease, type WordCardReleaseInput } from './word-card-preview-inputs';
import type { ReleasePin } from './word-card-release';

export const wordCardRoute = '/lexicon/card/';

/** Only authenticated release rows enter static routing. The card ID is the stable
 * URL segment. The version identifies the exact contents at that URL for this build. */
export function canonicalWordCards(config: WordCardReleaseInput, trustedPin?: ReleasePin) {
  if (config.controlled) return [];
  const release = loadPinnedWordCardRelease(config, trustedPin);
  if (release.kind !== 'release') return [];
  return release.rows.filter(row => row.status === 'CERTIFIED').map(row => ({
    path: `${wordCardRoute}${row.card_id}/`,
    row,
  }));
}

export function canonicalWordCardBuildInput(): WordCardReleaseInput {
  return {
    enabled: process.env.ATLAS_WORD_CARD_PREVIEW === '1',
    controlled: process.env.PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS === '1',
    artifactPath: process.env.ATLAS_WORD_CARD_RELEASE_PATH,
    pin: process.env.ATLAS_WORD_CARD_RELEASE_PIN,
  };
}

export type CanonicalWordCard = ReturnType<typeof canonicalWordCards>[number];
