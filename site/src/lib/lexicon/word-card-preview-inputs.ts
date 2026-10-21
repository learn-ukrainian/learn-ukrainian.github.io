import type { EntryRecord } from './atlas-data-source';
import type { PreviewCard } from './word-card-preview';
import { loadWordCardRelease, type LoadedRelease, type ReleaseCard, type ReleasePin } from './word-card-release';

export const publicReleasePin = {
  release_version: 'v0.1.0-pilot', provenance: 'producer-declared',
  dataset_sha256: '45bd9c9325a3b4221c86d1663d784e96a7edc096674415445d37113f793189e6',
  manifest_sha256: 'ca182bf5829f3ed4daa80c2394eb87e28879c3f1dc5088eef689f495b97e4f75',
} satisfies ReleasePin;

export type PreviewInput = {
  name: string; card: PreviewCard | ReleaseCard | LoadedRelease; current: EntryRecord | null;
  fingerprint: string; source: string; generatedAt: string; manifestVersion: string;
};

/** Build-time selection only. Public input never consults controlled records or a current pointer. */
export function releasePreviewInputs(config: {
  enabled: boolean; controlled: boolean; artifactPath?: string; pin?: string;
}): PreviewInput[] {
  if (!config.enabled) return [];
  const pin = config.controlled ? config.pin : config.pin || JSON.stringify(publicReleasePin);
  const release = loadWordCardRelease({ ...config, pin, public: !config.controlled });
  const publicPinMatches = release.kind !== 'release' || config.controlled ||
    Object.entries(publicReleasePin).every(([key, value]) => release.pin[key as keyof ReleasePin] === value);
  if (release.kind !== 'release' || !publicPinMatches) return [{
    name: 'release', card: { kind: 'unavailable', keys: null, claimantId: null,
      reason: !publicPinMatches ? 'Public release pin mismatch' : release.kind === 'unavailable' ? release.reason : 'Release disabled' },
    current: null, fingerprint: '', source: 'Configured release refused', generatedAt: '', manifestVersion: '',
  }];
  const common = { current: null, fingerprint: release.pin.dataset_sha256,
    source: `${release.pin.provenance} release ${release.pin.release_version}`, generatedAt: '', manifestVersion: release.pin.release_version };
  return [{ ...common, name: 'release', card: release }, ...release.rows.map(row => ({
    ...common, name: `release/${row.card_id}`,
    card: { kind: 'release-card', row, pin: release.pin, withdrawalNotice: release.withdrawalNotice } satisfies ReleaseCard,
  }))];
}
