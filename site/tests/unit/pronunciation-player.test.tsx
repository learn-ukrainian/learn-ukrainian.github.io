import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';

const FILE = `${'a'.repeat(64)}.wav`;
let instances: FakeAudio[];
class FakeAudio {
  src: string;
  preload = '';
  currentTime = 0;
  onended: (() => void) | null = null;
  onpause: (() => void) | null = null;
  onerror: (() => void) | null = null;
  play = vi.fn().mockResolvedValue(undefined);
  pause = vi.fn(() => this.onpause?.());
  load = vi.fn();
  removeAttribute = vi.fn();
  constructor(src: string) { this.src = src; instances.push(this); }
}

beforeEach(() => {
  vi.resetModules();
  instances = [];
  vi.stubGlobal('Audio', FakeAudio);
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({
    schemaVersion: 1, entries: { 'автобус': { file: FILE }, 'аеропорт': { file: FILE } },
  }) }));
  document.documentElement.dataset.chromeLocale = 'uk';
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function player() { return (await import('../../src/components/PronunciationPlayer')).default; }

describe('pronunciation player', () => {
  it('loads the manifest once, plays only on demand and stops', async () => {
    const Player = await player();
    render(<Player lemma="авто́бус" locale="en" />);
    const button = await screen.findByRole('button', { name: 'Play pronunciation' });
    expect(instances[0].play).not.toHaveBeenCalled();
    expect(instances[0].preload).toBe('none');
    fireEvent.click(button);
    expect(instances[0].play).toHaveBeenCalledOnce();
    expect(instances[0].src).toMatch(new RegExp(`/audio/pronunciation/${FILE}$`));
    fireEvent.click(screen.getByRole('button', { name: 'Stop pronunciation' }));
    expect(instances[0].pause).toHaveBeenCalled();
    expect(screen.getByRole('button')).toHaveTextContent('Play pronunciation');
  });

  it.each(['missing', '__proto__'])('offers no unavailable audio for %s', async (lemma) => {
    const Player = await player();
    render(<Player lemma={lemma} />);
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    expect(screen.queryByRole('button')).toBeNull();
    expect(instances).toHaveLength(0);
  });

  it('rejects traversal and remote asset paths', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({schemaVersion: 1, entries: {'автобус': {file: '../bad.wav'}}}) } as Response);
    const Player = await player();
    render(<Player lemma="автобус" />);
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    expect(instances).toHaveLength(0);
  });

  it('handles playback rejection with Ukrainian-only feedback and retry', async () => {
    const Player = await player();
    render(<Player lemma="автобус" locale="uk" />);
    const button = await screen.findByRole('button', { name: 'Послухати вимову' });
    instances[0].play.mockRejectedValueOnce(new Error('blocked'));
    fireEvent.click(button);
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Аудіо недоступне. Спробуйте ще раз.'));
    fireEvent.click(button);
    await waitFor(() => expect(instances[0].play).toHaveBeenCalledTimes(2));
    expect(screen.getByRole('status')).toHaveTextContent('');
  });

  it('cancels on lemma changes and unmount', async () => {
    const Player = await player();
    const view = render(<Player lemma="автобус" />);
    fireEvent.click(await screen.findByRole('button', { name: 'Послухати вимову' }));
    view.rerender(<Player lemma="аеропорт" />);
    await waitFor(() => expect(instances).toHaveLength(2));
    expect(instances[0].pause).toHaveBeenCalled();
    expect(instances[0].removeAttribute).toHaveBeenCalledWith('src');
    view.unmount();
    expect(instances[1].pause).toHaveBeenCalled();
    expect(fetch).toHaveBeenCalledOnce();
  });

  it('stops the previous player and responds to locale changes', async () => {
    const Player = await player();
    render(<><Player lemma="автобус" /><Player lemma="аеропорт" /></>);
    await waitFor(() => expect(screen.getAllByRole('button')).toHaveLength(2));
    fireEvent.click(screen.getAllByRole('button')[0]);
    instances[0].currentTime = 0.3;
    fireEvent.click(screen.getAllByRole('button')[1]);
    expect(instances[0].pause).toHaveBeenCalled();
    expect(instances[0].currentTime).toBe(0);
    document.documentElement.dataset.chromeLocale = 'en';
    await screen.findByRole('button', { name: 'Stop pronunciation' });
  });

  it('boots prerendered Atlas markup without hydrating the article', async () => {
    document.body.innerHTML = '<article data-word-atlas><span data-pronunciation-lemma="автобус"><button hidden></button><span role="status"></span></span></article>';
    const { mountAtlasPronunciation, mountPronunciationPlayer } = await import('../../src/lib/lexicon/pronunciation-player');
    mountAtlasPronunciation();
    mountAtlasPronunciation();
    fireEvent.click(await screen.findByRole('button', { name: 'Послухати вимову' }));
    expect(instances).toHaveLength(1);
    expect(instances[0].play).toHaveBeenCalledOnce();
    // Return the standalone fixture's controller to the same clean state as React unmount.
    mountPronunciationPlayer(document.querySelector('[data-pronunciation-lemma]')!)();
    document.body.innerHTML = '';
  });

  it('does not flip or rate a practice card when activated', async () => {
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    const rate = vi.fn();
    render(<Flashcard card={{front: 'автобус', back: 'bus', pronunciationLemma: 'автобус'}}
      chromeLocale="en" ratingLabels={Object.fromEntries(['again', 'hard', 'good', 'easy'].map(k => [k, {en: k, uk: k}])) as any}
      intervalPreviews={{again: '', hard: '', good: '', easy: ''}} onRate={rate} />);
    const button = await screen.findByRole('button', {name: 'Play pronunciation'});
    fireEvent.click(button);
    fireEvent.keyDown(button, {key: 'Enter'});
    expect(document.querySelector('[data-activity="flashcard"]')).toHaveAttribute('data-flipped', 'false');
    expect(rate).not.toHaveBeenCalled();
  });
});

it('matches Atlas casing, stress marks and apostrophe variants', async () => {
  const { pronunciationKey } = await import('../../src/lib/lexicon/pronunciation-player');
  expect(pronunciationKey('Інтерне́т')).toBe('інтернет');
  expect(pronunciationKey('п’ять')).toBe("п'ять");
  expect(pronunciationKey('пʼять')).toBe("п'ять");
  const Player = await player();
  render(<Player lemma="Авто́бус" locale="en" />);
  await screen.findByRole('button', {name: 'Play pronunciation'});
});

it('handles a missing manifest without an unhandled rejection', async () => {
  vi.mocked(fetch).mockResolvedValue({ok: false} as Response);
  const Player = await player();
  const view = render(<Player lemma="автобус" />);
  await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
  expect(screen.queryByRole('button')).toBeNull();
  view.unmount();
});

it('reports a missing or undecodable WAV after manifest lookup', async () => {
  const Player = await player();
  render(<Player lemma="автобус" locale="en" />);
  fireEvent.click(await screen.findByRole('button', {name: 'Play pronunciation'}));
  instances[0].onerror?.();
  expect(screen.getByRole('status')).toHaveTextContent('Audio unavailable. Try again.');
  expect(screen.getByRole('button')).toHaveTextContent('Play pronunciation');
});

it('ignores a late play rejection after another player takes over', async () => {
  const Player = await player();
  render(<><Player lemma="автобус" /><Player lemma="аеропорт" /></>);
  await waitFor(() => expect(screen.getAllByRole('button')).toHaveLength(2));
  let reject!: (error: Error) => void;
  instances[0].play.mockImplementationOnce(() => new Promise((_, fail) => { reject = fail; }));
  fireEvent.click(screen.getAllByRole('button')[0]);
  fireEvent.click(screen.getAllByRole('button')[1]);
  reject(new Error('late rejection'));
  await waitFor(() => expect(instances[0].pause).toHaveBeenCalled());
  expect(screen.getAllByRole('status')[0]).toHaveTextContent('');
});

it('updates an existing error when chrome changes to Ukrainian', async () => {
  document.documentElement.dataset.chromeLocale = 'en';
  const Player = await player();
  render(<Player lemma="автобус" />);
  await screen.findByRole('button', {name: 'Play pronunciation'});
  instances[0].onerror?.();
  expect(screen.getByRole('status')).toHaveTextContent('Audio unavailable. Try again.');
  document.documentElement.dataset.chromeLocale = 'uk';
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Аудіо недоступне. Спробуйте ще раз.'));
});

it('wires a real Atlas lemma article to the player outside its heading', async () => {
  const {default: Article} = await import('../../src/lexicon/WordAtlasArticle');
  const {articleProps} = await import('../helpers/word-atlas-record');
  render(<Article {...articleProps({lemma: 'автобус', url_slug: 'автобус', entry_type: 'lemma', pos: 'noun', gloss: 'bus', course_usage: []})} />);
  const button = await screen.findByRole('button', {name: 'Послухати вимову'});
  expect(button.closest('h1')).toBeNull();
  fireEvent.click(button);
  expect(instances[0].play).toHaveBeenCalledOnce();
});
