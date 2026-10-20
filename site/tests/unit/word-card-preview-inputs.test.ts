import { afterEach, describe, expect, it, vi } from 'vitest';
import { resolve } from 'node:path';
import * as loader from '../../src/lib/lexicon/word-card-release';
import { publicReleasePin, releasePreviewInputs } from '../../src/lib/lexicon/word-card-preview-inputs';
import { pins } from '../fixtures/word-card-preview/release-controls';

const controlled = { enabled: true, controlled: true, artifactPath: resolve('tests/fixtures/word-card-preview/release-jsonl'), pin: JSON.stringify(pins.jsonl) };
afterEach(() => vi.restoreAllMocks());
describe('public and controlled build selection', () => {
  it('returns before loading when disabled', () => {
    const spy = vi.spyOn(loader, 'loadWordCardRelease');
    expect(releasePreviewInputs({ ...controlled, enabled: false })).toEqual([]);
    expect(spy).not.toHaveBeenCalled();
  });
  it('retains explicit controls, including both literal identities', () => {
    const inputs = releasePreviewInputs(controlled);
    expect(inputs.map(input => input.name)).toEqual(['release', 'release/wc_0123456789ab', 'release/wc_0123456789ac', 'word/fixture-head']);
    expect(inputs.every(input => input.current === null)).toBe(true);
    expect(inputs[1]?.card).toMatchObject({ kind: 'release-card', row: { status: 'CERTIFIED' }, pin: pins.jsonl });
    // Same-spelling cards share one grouped page as separate numbered entries, in release order.
    expect(inputs[3]?.card).toMatchObject({ kind: 'release-page', pin: pins.jsonl, page: { key: 'fixture-head', entries: [
      { ordinal: 1, row: { card_id: 'wc_0123456789ab' } }, { ordinal: 2, row: { card_id: 'wc_0123456789ac' } }] } });
  });
  it('refuses synthetic provenance in public mode before reading artifacts', () => {
    const inputs = releasePreviewInputs({ ...controlled, controlled: false });
    expect(inputs).toHaveLength(1);
    expect(inputs[0]?.card).toMatchObject({ kind: 'unavailable', reason: 'Synthetic provenance forbidden in public preview' });
  });
  it('uses the frozen public pin and never falls back to fixtures when real bytes are absent', () => {
    const spy = vi.spyOn(loader, 'loadWordCardRelease');
    expect(releasePreviewInputs({ enabled: true, controlled: false })[0]?.card).toMatchObject({ kind: 'unavailable', reason: 'Incomplete release configuration' });
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ public: true, pin: JSON.stringify(publicReleasePin) }));
    expect(releasePreviewInputs({ enabled: true, controlled: true })[0]?.card).toMatchObject({ reason: 'Release not configured' });
  });
  it('enumerates public rows only when all immutable pin fields match', () => {
    const release = loader.loadWordCardRelease(controlled);
    if (release.kind !== 'release') throw Error('Missing test release');
    const spy = vi.spyOn(loader, 'loadWordCardRelease').mockReturnValue({ ...release, pin: publicReleasePin });
    const inputs = releasePreviewInputs({ enabled: true, controlled: false });
    expect(inputs.map(input => [input.name, input.fingerprint, input.manifestVersion])).toEqual([
      ['release', publicReleasePin.dataset_sha256, 'v0.1.0-pilot'],
      ['release/wc_0123456789ab', publicReleasePin.dataset_sha256, 'v0.1.0-pilot'],
      ['release/wc_0123456789ac', publicReleasePin.dataset_sha256, 'v0.1.0-pilot'],
      ['word/fixture-head', publicReleasePin.dataset_sha256, 'v0.1.0-pilot'],
    ]);
    spy.mockReturnValue({ ...release, pin: { ...publicReleasePin, dataset_sha256: '0'.repeat(64) } });
    expect(releasePreviewInputs({ enabled: true, controlled: false })[0]?.card).toMatchObject({ reason: 'Public release pin mismatch' });
    spy.mockReturnValue({ kind: 'disabled' });
    expect(releasePreviewInputs({ enabled: true, controlled: false })[0]?.card).toMatchObject({ reason: 'Release disabled' });
  });
});
