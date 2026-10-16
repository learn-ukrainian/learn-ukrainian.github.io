import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';

const FILE = `${'a'.repeat(64)}.wav`;
let instances: FakeAudio[];
const UK_VOICE = { lang: 'uk-UA', localService: true, name: 'Ukrainian' } as SpeechSynthesisVoice;
class FakeUtterance {
  lang = '';
  voice: SpeechSynthesisVoice | null = null;
  onstart: (() => void) | null = null;
  onend: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(public text: string) {}
}
let speech: EventTarget & { getVoices: ReturnType<typeof vi.fn>; speak: ReturnType<typeof vi.fn>; cancel: ReturnType<typeof vi.fn> };
class FakeAudio {
  src: string;
  paused = false;
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
  speech = Object.assign(new EventTarget(), { getVoices: vi.fn(() => [UK_VOICE]), speak: vi.fn((value: FakeUtterance) => value.onstart?.()), cancel: vi.fn() });
  vi.stubGlobal('speechSynthesis', speech);
  vi.stubGlobal('SpeechSynthesisUtterance', FakeUtterance);
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({
    schemaVersion: 1, entries: { 'автобус': { file: FILE }, 'аеропорт': { file: FILE } },
  }) }));
  document.documentElement.dataset.chromeLocale = 'uk';
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

async function player() { return (await import('../../src/components/PronunciationPlayer')).default; }

describe('#10706 audio:', () => {
  it.each(['ended', 'pause'] as const)('native %s restores Play and its late callbacks cannot end the retry', async (event) => {
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    await waitFor(() => expect(instances).toHaveLength(1));
    fireEvent.click(screen.getByRole('button'));
    await screen.findByRole('button', { name: 'Stop pronunciation' });
    const old = instances[0];
    const lateEnd = old.onended!;
    const latePause = old.onpause!;
    const lateError = old.onerror!;
    old.paused = true;
    (event === 'ended' ? lateEnd : latePause)();
    expect(screen.getByRole('button')).toHaveTextContent('Play pronunciation');
    fireEvent.click(screen.getByRole('button'));
    await screen.findByRole('button', { name: 'Stop pronunciation' });
    lateEnd();
    latePause();
    lateError();
    expect(screen.getByRole('button')).toHaveTextContent('Stop pronunciation');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
  });

  it('speech start, end and error arriving after unmount cannot affect a new player', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('no manifest'));
    speech.speak.mockImplementation(() => {});
    const Player = await player();
    const old = render(<Player lemma="автобус" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    const pending = speech.speak.mock.calls[0][0];
    const lateStart = pending.onstart;
    const lateEnd = pending.onend;
    const lateError = pending.onerror;
    old.unmount();
    render(<Player lemma="аеропорт" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    speech.speak.mock.calls[1][0].onstart();
    lateStart();
    lateEnd();
    lateError();
    expect(screen.getByRole('button')).toHaveTextContent('Stop pronunciation');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    expect(speech.cancel).toHaveBeenCalledOnce();
  });

  it.each(['malformed JSON', 'invalid schema', 'array entries'])('handles %s without autoplay or repeated lookup', async (fault) => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => {
      if (fault === 'malformed JSON') throw new SyntaxError('invalid JSON');
      return fault === 'invalid schema' ? { schemaVersion: 2, entries: {} } : { schemaVersion: 1, entries: [] };
    } } as Response);
    const Player = await player();
    const first = render(<Player lemma="автобус" locale="en" fallback="hide" />);
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    await Promise.resolve();
    first.unmount();
    render(<Player lemma="автобус" locale="en" fallback="disable" />);
    await waitFor(() => expect(screen.getByRole('button')).toBeDisabled());
    expect(fetch).toHaveBeenCalledOnce();
    expect(instances).toHaveLength(0);
    expect(speech.speak).not.toHaveBeenCalled();
  });

  it('does not request or expose playback for an empty lemma', async () => {
    const Player = await player();
    const view = render(<Player lemma="" locale="en" />);
    expect(view.container.querySelector('button')).toHaveAttribute('hidden');
    expect(fetch).not.toHaveBeenCalled();
    expect(instances).toHaveLength(0);
  });

  it.each(['pagehide', 'astro:before-swap'])('cancels pending playback on %s and ignores its late completion', async (event) => {
    const Player = await player();
    const view = render(<Player lemma="автобус" locale="en" />);
    await waitFor(() => expect(instances).toHaveLength(1));
    let finish!: () => void;
    instances[0].play.mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }));
    fireEvent.click(screen.getByRole('button'));
    (event === 'pagehide' ? window : document).dispatchEvent(new Event(event));
    expect(instances[0].pause).toHaveBeenCalled();
    expect(instances[0].currentTime).toBe(0);
    finish();
    await Promise.resolve();
    expect(screen.getByRole('button')).toHaveTextContent('Play pronunciation');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    view.unmount();
  });

  it('exposes a busy Stop action while native playback is pending', async () => {
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    await waitFor(() => expect(instances).toHaveLength(1));
    let start!: () => void;
    instances[0].play.mockImplementationOnce(() => new Promise<void>((resolve) => { start = resolve; }));
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('button')).toHaveAccessibleName('Stop pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    start();
    await screen.findByRole('button', { name: 'Stop pronunciation' });
  });

  it('exposes a busy Stop action and cancels pending speech on a second activation', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('no manifest'));
    speech.speak.mockImplementation(() => {});
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    const pending = speech.speak.mock.calls[0][0];
    expect(screen.getByRole('button')).toHaveAccessibleName('Stop pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    fireEvent.click(screen.getByRole('button'));
    expect(speech.cancel).toHaveBeenCalledOnce();
    expect(screen.getByRole('button')).toHaveTextContent('Play pronunciation');
    pending.onstart?.();
    expect(screen.getByRole('button')).toHaveTextContent('Play pronunciation');
    fireEvent.click(screen.getByRole('button'));
    speech.speak.mock.calls[1][0].onstart();
    expect(screen.getByRole('button')).toHaveTextContent('Stop pronunciation');
  });

  it.each(['error then rejection', 'rejection then error'])('a failed attempt cannot override a successful same-mounted retry: %s', async (ordering) => {
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    await waitFor(() => expect(instances).toHaveLength(1));
    let reject!: (error: Error) => void;
    instances[0].play.mockImplementationOnce(() => new Promise<void>((_resolve, fail) => { reject = fail; }));
    fireEvent.click(screen.getByRole('button'));
    const lateError = instances[0].onerror!;
    if (ordering === 'error then rejection') lateError();
    else reject(new Error('aborted'));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Audio unavailable. Try again.'));
    fireEvent.click(screen.getByRole('button'));
    await screen.findByRole('button', { name: 'Stop pronunciation' });
    if (ordering === 'error then rejection') reject(new Error('late rejection'));
    else lateError();
    await Promise.resolve();
    expect(screen.getByRole('button')).toHaveTextContent('Stop pronunciation');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
  });
});

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
    fireEvent.click(await screen.findByRole('button', { name: 'Stop pronunciation' }));
    expect(instances[0].pause).toHaveBeenCalled();
    expect(screen.getByRole('button')).toHaveTextContent('Play pronunciation');
  });

  it.each(['missing', '__proto__'])('does not treat %s as a WAV entry', async (lemma) => {
    const Player = await player();
    render(<Player lemma={lemma} />);
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    expect(screen.getByRole('button')).toBeVisible();
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
    await waitFor(() => expect(instances.flatMap((audio) => audio.play.mock.calls)).toHaveLength(2));
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
  expect(screen.getByRole('button')).toBeVisible();
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


describe('on-device Ukrainian speech', () => {
  beforeEach(() => { vi.mocked(fetch).mockRejectedValue(new Error('no manifest')); });

  it('shows an uncovered lemma, speaks only on click, and cancels on second click', async () => {
    const Player = await player();
    render(<Player lemma="авто́бус" locale="en" />);
    const button = screen.getByRole('button', { name: 'Play pronunciation' });
    expect(button).toBeVisible();
    expect(button.closest('[data-pronunciation-lemma]')).toHaveAttribute('lang', 'uk');
    expect(button).toHaveAttribute('lang', 'en');
    expect(speech.speak).not.toHaveBeenCalled();
    fireEvent.click(button);
    expect(speech.speak).toHaveBeenCalledOnce();
    const utterance = speech.speak.mock.calls[0][0];
    expect(utterance).toMatchObject({ text: 'авто́бус', lang: 'uk-UA', voice: UK_VOICE });
    const lateError = utterance.onerror;
    fireEvent.click(await screen.findByRole('button', { name: 'Stop pronunciation' }));
    expect(speech.cancel).toHaveBeenCalledOnce();
    lateError();
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    expect(button).toHaveTextContent('Play pronunciation');
  });

  it('accepts online or remote Ukrainian voices for Windows Edge and Chrome', async () => {
    speech.getVoices.mockReturnValue([{lang: 'en-US', localService: true}, {...UK_VOICE, localService: false}]);
    const Player = await player();
    render(<Player lemma="автобус" locale="uk" />);
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).toHaveBeenCalledOnce();
    const utterance = speech.speak.mock.calls[0][0];
    expect(utterance.voice).toMatchObject({ lang: 'uk-UA', localService: false });
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
  });

  it.each(['en', 'uk'] as const)('rejects non-Ukrainian voices with %s feedback and allows retry', async (locale) => {
    speech.getVoices.mockReturnValue([{lang: 'en-US', localService: true}]);
    const Player = await player();
    render(<Player lemma="автобус" locale={locale} />);
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toHaveTextContent(locale === 'en'
      ? 'Audio unavailable. Try again.' : 'Аудіо недоступне. Спробуйте ще раз.');
    speech.getVoices.mockReturnValue([UK_VOICE]);
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).toHaveBeenCalledOnce();
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
  });

  it('supports opus, webm, and mp3 audio entries in addition to wav', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({
      schemaVersion: 1, entries: { 'автобус': { file: `${'b'.repeat(64)}.opus` } },
    }) } as Response);
    const Player = await player();
    render(<Player lemma="автобус" />);
    const button = await screen.findByRole('button', { name: 'Послухати вимову' });
    fireEvent.click(button);
    expect(instances[0].src).toMatch(new RegExp(`/audio/pronunciation/${'b'.repeat(64)}\\.opus$`));
  });

  it('supports sharded 2-char prefix directory paths for opus audio', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({
      schemaVersion: 1, entries: { 'автобус': { file: `ab/${'a'.repeat(64)}.opus` } },
    }) } as Response);
    const Player = await player();
    render(<Player lemma="автобус" />);
    const button = await screen.findByRole('button', { name: 'Послухати вимову' });
    fireEvent.click(button);
    expect(instances[0].src).toMatch(new RegExp(`/audio/pronunciation/ab/${'a'.repeat(64)}\\.opus$`));
  });

  it('computes deterministic lemmaAudioPath using web crypto', async () => {
    const { lemmaAudioPath } = await import('../../src/lib/lexicon/pronunciation-player');
    const path = await lemmaAudioPath('авто́бус', 'opus', true);
    expect(path).toMatch(/^[a-f0-9]{2}\/[a-f0-9]{64}\.opus$/);
    const flatPath = await lemmaAudioPath('автобус', 'opus', false);
    expect(flatPath).toMatch(/^[a-f0-9]{64}\.opus$/);
    expect(path).toBe(`${flatPath.slice(0, 2)}/${flatPath}`);
  });

  it('does not autoplay when voices arrive before any playback request', async () => {
    speech.getVoices.mockReturnValue([]);
    const Player = await player();
    render(<Player lemma="автобус" />);
    speech.getVoices.mockReturnValue([UK_VOICE]);
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(speech.speak).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).toHaveBeenCalledOnce();
  });

  it('#10706 F3 waits for a late catalog without claiming unavailability or needing another click', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('no manifest'));
    speech.getVoices.mockReturnValue([]);
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    expect(screen.getByRole('button')).toHaveAccessibleName('Stop pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(speech.speak).not.toHaveBeenCalled();
    speech.getVoices.mockReturnValue([UK_VOICE]);
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(speech.speak).toHaveBeenCalledOnce();
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(speech.speak).toHaveBeenCalledOnce();
  });

  it('#10706 F3 a late non-Ukrainian catalog reports known absence and allows a later retry', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('no manifest'));
    speech.getVoices.mockReturnValue([]);
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    speech.getVoices.mockReturnValue([{ ...UK_VOICE, lang: 'en-US' }]);
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(screen.getByRole('status')).toHaveTextContent('Audio unavailable. Try again.');
    expect(screen.getByRole('button')).toHaveAccessibleName('Play pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
    expect(speech.speak).not.toHaveBeenCalled();
    speech.getVoices.mockReturnValue([UK_VOICE]);
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(speech.speak).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).toHaveBeenCalledOnce();
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
  });

  it('#10706 F3 a late catalog playback exception is an actual failure, not a stuck pending request', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('no manifest'));
    speech.getVoices.mockReturnValue([]);
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    speech.getVoices.mockReturnValue([UK_VOICE]);
    speech.speak.mockImplementation(() => { throw new Error('engine failed'); });
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(screen.getByRole('status')).toHaveTextContent('Audio unavailable. Try again.');
    expect(screen.getByRole('button')).toHaveAccessibleName('Play pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
  });

  it.each(['cancel', 'unmount', 'new presentation', 'pagehide', 'astro:before-swap'])('#10706 F3 late voices cannot resurrect after %s', async (transition) => {
    vi.mocked(fetch).mockRejectedValue(new Error('no manifest'));
    speech.getVoices.mockReturnValue([]);
    const Player = await player();
    const view = render(<Player lemma="автобус" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('button')).toHaveAccessibleName('Stop pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    if (transition === 'cancel') fireEvent.click(screen.getByRole('button'));
    else if (transition === 'unmount') view.unmount();
    else if (transition === 'new presentation') view.rerender(<Player key="next" lemma="автобус" locale="en" />);
    else (transition === 'pagehide' ? window : document).dispatchEvent(new Event(transition));
    speech.getVoices.mockReturnValue([UK_VOICE]);
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(speech.speak).not.toHaveBeenCalled();
  });

  it('cancels exclusively, ignores stale callbacks, and cancels on lemma change/unmount', async () => {
    const Player = await player();
    const view = render(<><Player lemma="автобус" /><Player lemma="аеропорт" /></>);
    fireEvent.click(screen.getAllByRole('button')[0]);
    const lateEnd = speech.speak.mock.calls[0][0].onend;
    fireEvent.click(screen.getAllByRole('button')[1]);
    expect(speech.cancel).toHaveBeenCalledOnce();
    lateEnd();
    expect(screen.getAllByRole('button')[1]).toHaveTextContent('Зупинити відтворення');
    view.rerender(<Player lemma="автобус" />);
    expect(speech.cancel).toHaveBeenCalledTimes(2);
    fireEvent.click(screen.getByRole('button'));
    view.rerender(<Player lemma="аеропорт" />);
    expect(speech.cancel).toHaveBeenCalledTimes(3);
    fireEvent.click(screen.getByRole('button'));
    view.unmount();
    expect(speech.cancel).toHaveBeenCalledTimes(4);
  });

  it('resets on speech completion and reports engine errors', async () => {
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    speech.speak.mock.calls[0][0].onend();
    expect(screen.getByRole('button')).toHaveTextContent('Play pronunciation');
    fireEvent.click(screen.getByRole('button'));
    speech.speak.mock.calls[1][0].onerror();
    expect(screen.getByRole('status')).toHaveTextContent('Audio unavailable. Try again.');
  });

  it('reports unsupported browsers without throwing', async () => {
    vi.stubGlobal('speechSynthesis', undefined);
    vi.stubGlobal('SpeechSynthesisUtterance', undefined);
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('status')).toHaveTextContent('Audio unavailable. Try again.');
  });

  it('speaks an Atlas headword and cancels when the article leaves', async () => {
    document.body.innerHTML = '<article data-word-atlas><span data-pronunciation-lemma="автобус"><button hidden></button><span role="status"></span></span><span lang="en">bus</span></article>';
    const { mountAtlasPronunciation, unmountAtlasPronunciation } = await import('../../src/lib/lexicon/pronunciation-player');
    mountAtlasPronunciation();
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak.mock.calls[0][0].text).toBe('автобус');
    unmountAtlasPronunciation();
    expect(speech.cancel).toHaveBeenCalledOnce();
    document.body.innerHTML = '';
  });
});

describe('CDN distribution and resilient fallback', () => {
  const CDN_URL = 'https://cdn.learn-ukrainian.org/word-atlas-audio';

  beforeEach(() => {
    vi.stubEnv('PUBLIC_AUDIO_CDN_URL', CDN_URL);
  });

  it('uses CDN base URL for manifest-backed audio entries', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        schemaVersion: 1,
        entries: { 'автобус': { file: `12/${'c'.repeat(64)}.opus` } },
      }),
    } as Response);
    const Player = await player();
    render(<Player lemma="автобус" />);
    const button = await screen.findByRole('button', { name: 'Послухати вимову' });
    fireEvent.click(button);
    expect(instances[0].src).toBe(`${CDN_URL}/12/${'c'.repeat(64)}.opus`);
    expect(instances[0].play).toHaveBeenCalledOnce();
  });

  it('falls back to speech synthesis exactly once when CDN audio fails with both onerror and play rejection', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        schemaVersion: 1,
        entries: { 'автобус': { file: `12/${'c'.repeat(64)}.opus` } },
      }),
    } as Response);
    const Player = await player();
    render(<Player lemma="автобус" locale="uk" />);
    const button = await screen.findByRole('button', { name: 'Послухати вимову' });

    // Simulate browser behavior on 404 / decode failure: play() rejects AND onerror fires
    instances[0].play.mockImplementation(async () => {
      instances[0].onerror?.();
      throw new Error('404 Not Found');
    });

    fireEvent.click(button);
    await waitFor(() => expect(speech.speak).toHaveBeenCalled());

    // Critical assertion for Finding 1: speech.speak must be called EXACTLY ONCE, never queued twice
    expect(speech.speak).toHaveBeenCalledOnce();
    const utterance = speech.speak.mock.calls[0][0];
    expect(utterance).toMatchObject({ text: 'автобус', lang: 'uk-UA' });
  });

  it('derives on-demand CDN audio path and falls back to speech synthesis on 404 when manifest is missing', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('manifest 404'));
    const Player = await player();
    render(<Player lemma="автобус" locale="uk" />);

    // Wait for on-demand lemmaAudioPath derivation and audio attachment
    await waitFor(() => expect(instances).toHaveLength(1));
    expect(instances[0].src.startsWith(`${CDN_URL}/`)).toBe(true);
    expect(instances[0].src.slice(CDN_URL.length + 1)).toMatch(/^[a-f0-9]{2}\/[a-f0-9]{64}\.opus$/);

    // When clicked, audio.play() fails (simulating CDN clip not yet synthesized)
    instances[0].play.mockImplementation(async () => {
      instances[0].onerror?.();
      throw new Error('404 Not Found');
    });

    const button = screen.getByRole('button', { name: 'Послухати вимову' });
    fireEvent.click(button);
    await waitFor(() => expect(speech.speak).toHaveBeenCalledTimes(1));
    expect(speech.speak).toHaveBeenCalledOnce();
  });

  it('derives on-demand CDN audio path when manifest exists but lemma is not in manifest', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        schemaVersion: 1,
        entries: { 'інше_слово': { file: `12/${'c'.repeat(64)}.opus` } },
      }),
    } as Response);
    const Player = await player();
    render(<Player lemma="автобус" locale="uk" />);

    // Wait for on-demand derivation since lemma is omitted from manifest
    await waitFor(() => expect(instances).toHaveLength(1));
    expect(instances[0].src.startsWith(`${CDN_URL}/`)).toBe(true);
    expect(instances[0].src.slice(CDN_URL.length + 1)).toMatch(/^[a-f0-9]{2}\/[a-f0-9]{64}\.opus$/);
  });
});


it('does not let an old WAV play completion stop a restarted clip', async () => {
  const Player = await player();
  render(<Player lemma="автобус" locale="en" />);
  await waitFor(() => expect(instances).toHaveLength(1));
  let finish!: () => void;
  instances[0].play.mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }));
  const button = screen.getByRole('button');
  fireEvent.click(button);
  fireEvent.click(button);
  fireEvent.click(button);
  const restarted = instances.at(-1)!;
  restarted.pause.mockClear();
  finish();
  await screen.findByRole('button', { name: 'Stop pronunciation' });
  expect(restarted.pause).not.toHaveBeenCalled();
});

it('keeps speech and explicit WAV playback exclusive in both directions', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({ schemaVersion: 1, entries: {'автобус': {file: FILE}} }) } as Response);
  const Player = await player();
  const view = render(<><Player lemma="автобус" /><Player lemma="аеропорт" /></>);
  await waitFor(() => expect(instances).toHaveLength(1));
  const [wav, tts] = screen.getAllByRole('button');
  fireEvent.click(tts);
  fireEvent.click(wav);
  expect(speech.cancel).toHaveBeenCalledOnce();
  fireEvent.click(tts);
  expect(instances[0].pause).toHaveBeenCalled();
  expect(wav).toHaveTextContent('Послухати вимову');
  view.unmount();
  expect(speech.cancel).toHaveBeenCalledTimes(2);
});

describe('graceful audio fallback (#8378)', () => {
  const RATING_LABELS = Object.fromEntries(
    ['again', 'hard', 'good', 'easy'].map((k) => [k, { en: k, uk: k }])
  ) as any;
  const INTERVAL_PREVIEWS = { again: '1d', hard: '2d', good: '4d', easy: '7d' };

  it('hides Flashcard audio button when audioFallback="hide" and pronunciation manifest returns 404', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404 } as Response);
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    render(
      <Flashcard
        card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус', subtitle: 'іменник' }}
        chromeLocale="en"
        ratingLabels={RATING_LABELS}
        intervalPreviews={INTERVAL_PREVIEWS}
        onRate={vi.fn()}
        audioFallback="hide"
      />
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    const button = document.querySelector('[data-pronunciation-lemma] button');
    expect(button).toHaveAttribute('hidden');
    expect(screen.getByText('іменник')).toBeVisible();
  });

  it('hides Flashcard audio button when audioFallback="hide" and pronunciation manifest has no entries', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ schemaVersion: 1, entries: {} }),
    } as Response);
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    render(
      <Flashcard
        card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус' }}
        chromeLocale="en"
        ratingLabels={RATING_LABELS}
        intervalPreviews={INTERVAL_PREVIEWS}
        onRate={vi.fn()}
        audioFallback="hide"
      />
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    const button = document.querySelector('[data-pronunciation-lemma] button');
    expect(button).toHaveAttribute('hidden');
  });

  it('disables Flashcard audio button when audioFallback="disable" and manifest 404s', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404 } as Response);
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    render(
      <Flashcard
        card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус' }}
        chromeLocale="en"
        ratingLabels={RATING_LABELS}
        intervalPreviews={INTERVAL_PREVIEWS}
        onRate={vi.fn()}
        audioFallback="disable"
      />
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    const button = screen.getByRole('button', { name: 'Play pronunciation' });
    expect(button).toBeVisible();
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-disabled', 'true');
  });

  it('disables Flashcard audio button when audioFallback="disable" and manifest loads but entry is missing', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ schemaVersion: 1, entries: {} }),
    } as Response);
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    render(
      <Flashcard
        card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус' }}
        chromeLocale="en"
        ratingLabels={RATING_LABELS}
        intervalPreviews={INTERVAL_PREVIEWS}
        onRate={vi.fn()}
        audioFallback="disable"
      />
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    const button = screen.getByRole('button', { name: 'Play pronunciation' });
    expect(button).toBeVisible();
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-disabled', 'true');
  });

  it('falls back to speech synthesis by default on Flashcards when manifest 404s', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404 } as Response);
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    render(
      <Flashcard
        card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус', subtitle: 'іменник' }}
        chromeLocale="en"
        ratingLabels={RATING_LABELS}
        intervalPreviews={INTERVAL_PREVIEWS}
        onRate={vi.fn()}
      />
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    const button = screen.getByRole('button', { name: 'Play pronunciation' });
    expect(button).toBeVisible();
    expect(button).not.toBeDisabled();
    fireEvent.click(button);
    expect(speech.speak).toHaveBeenCalledOnce();
  });

  it('renders enabled and visible Flashcard audio button when manifest contains clip', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        schemaVersion: 1,
        entries: { 'автобус': { file: FILE } },
      }),
    } as Response);
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    render(
      <Flashcard
        card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус' }}
        chromeLocale="en"
        ratingLabels={RATING_LABELS}
        intervalPreviews={INTERVAL_PREVIEWS}
        onRate={vi.fn()}
      />
    );
    const button = await screen.findByRole('button', { name: 'Play pronunciation' });
    expect(button).toBeVisible();
    expect(button).not.toBeDisabled();
    expect(button).not.toHaveAttribute('hidden');
    fireEvent.click(button);
    expect(instances[0].play).toHaveBeenCalledOnce();
  });

  it('does not retry manifest fetch repeatedly across multiple cards after a 404 error', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404 } as Response);
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    render(
      <>
        <Flashcard
          card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус' }}
          chromeLocale="en"
          ratingLabels={RATING_LABELS}
          intervalPreviews={INTERVAL_PREVIEWS}
          onRate={vi.fn()}
        />
        <Flashcard
          card={{ front: 'аеропорт', back: 'airport', pronunciationLemma: 'аеропорт' }}
          chromeLocale="en"
          ratingLabels={RATING_LABELS}
          intervalPreviews={INTERVAL_PREVIEWS}
          onRate={vi.fn()}
        />
      </>
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    // Verify fetch was only called once, not twice
    expect(fetch).toHaveBeenCalledOnce();
  });

  it('retries manifest fetch on subsequent mounts after a transient network failure (not 404)', async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new TypeError('Failed to fetch'));
    const { default: Flashcard } = await import('../../src/components/PracticeFlashcard');
    const { unmount } = render(
      <Flashcard
        card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус' }}
        chromeLocale="en"
        ratingLabels={RATING_LABELS}
        intervalPreviews={INTERVAL_PREVIEWS}
        onRate={vi.fn()}
      />
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    unmount();

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        schemaVersion: 1,
        entries: { 'автобус': { file: FILE } },
      }),
    } as Response);

    render(
      <Flashcard
        card={{ front: 'автобус', back: 'bus', pronunciationLemma: 'автобус' }}
        chromeLocale="en"
        ratingLabels={RATING_LABELS}
        intervalPreviews={INTERVAL_PREVIEWS}
        onRate={vi.fn()}
      />
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  });
});


describe('#10706 A3 finite startup', () => {
  afterEach(() => { vi.useRealTimers(); });
  it('D01 empty catalog expires at 10000ms through the rendered consumer', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('no manifest'));
    speech.getVoices.mockReturnValue([]);
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(9999);
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    vi.advanceTimersByTime(1);
    expect(screen.getByRole('button')).toHaveAccessibleName('Play pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
    expect(screen.getByRole('status')).toHaveTextContent('Audio did not start. Try again.');
    speech.getVoices.mockReturnValue([UK_VOICE]);
    speech.dispatchEvent(new Event('voiceschanged'));
    expect(speech.speak).not.toHaveBeenCalled();
  });
});

describe('#10706 A3 startup controls (injected availability, not native proof)', () => {
  afterEach(() => { vi.useRealTimers(); });
  async function speechPlayer(empty = true, locale: 'en' | 'uk' = 'en') {
    vi.mocked(fetch).mockRejectedValue(new Error('no manifest'));
    speech.getVoices.mockReturnValue(empty ? [] : [UK_VOICE]);
    speech.speak.mockImplementation(() => {});
    const Player = await player();
    const view = render(<Player lemma="автобус" locale={locale} />);
    vi.useFakeTimers();
    return view;
  }
  function pending() {
    expect(screen.getByRole('button')).toHaveAccessibleName('Stop pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
  }
  function expired() {
    expect(screen.getByRole('button')).toHaveAccessibleName('Play pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
    expect(screen.getByRole('status')).toHaveTextContent('Audio did not start. Try again.');
  }
  function voices() {
    speech.getVoices.mockReturnValue([UK_VOICE]);
    speech.dispatchEvent(new Event('voiceschanged'));
  }
  it('D02 an empty event before activation neither starts nor spends the budget', async () => {
    await speechPlayer();
    speech.dispatchEvent(new Event('voiceschanged'));
    vi.advanceTimersByTime(20000);
    expect(speech.speak).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(9999);
    pending();
    vi.advanceTimersByTime(1);
    expired();
  });
  it('D03 repeated empty events never restart the original budget', async () => {
    await speechPlayer();
    fireEvent.click(screen.getByRole('button'));
    for (const elapsed of [3000, 4000, 2999]) {
      vi.advanceTimersByTime(elapsed);
      speech.dispatchEvent(new Event('voiceschanged'));
      pending();
    }
    vi.advanceTimersByTime(1);
    expired();
    expect(speech.speak).not.toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
  });
  it('D04 a voice at 9999 can start, select Ukrainian explicitly and survive the boundary', async () => {
    await speechPlayer();
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(9999);
    voices();
    expect(speech.speak).toHaveBeenCalledOnce();
    const utterance: FakeUtterance = speech.speak.mock.calls[0][0];
    expect(utterance).toMatchObject({ text: 'автобус', lang: 'uk-UA', voice: UK_VOICE });
    utterance.onstart?.();
    vi.advanceTimersByTime(20000);
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
    expect(screen.getByRole('button')).toHaveAccessibleName('Stop pronunciation');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    expect(vi.getTimerCount()).toBe(0);
  });
  it('D05 voices after expiry remain silent until a fresh explicit retry', async () => {
    await speechPlayer();
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(10000);
    expired();
    voices();
    voices();
    expect(speech.speak).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).toHaveBeenCalledOnce();
    vi.advanceTimersByTime(9999);
    pending();
    vi.advanceTimersByTime(1);
    expired();
  });
  it.each(['cancel', 'pagehide', 'astro:before-swap', 'dispose'])('D06 %s clears the timer and suppresses late voices', async (action) => {
    const view = await speechPlayer();
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(9999);
    if (action === 'cancel') fireEvent.click(screen.getByRole('button'));
    else if (action === 'dispose') view.unmount();
    else (action === 'pagehide' ? window : document).dispatchEvent(new Event(action));
    expect(vi.getTimerCount()).toBe(0);
    voices();
    vi.advanceTimersByTime(10000);
    expect(speech.speak).not.toHaveBeenCalled();
    if (action !== 'dispose') {
      expect(screen.getByRole('button')).toHaveAccessibleName('Play pronunciation');
      expect(screen.getByRole('status')).toBeEmptyDOMElement();
    }
  });
  it('D07 supersession clears only the old budget and keeps the new attempt pending', async () => {
    const first = await speechPlayer();
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(9000);
    const Player = await player();
    const second = render(<Player lemma="аеропорт" locale="en" />);
    fireEvent.click(second.getByText('Play pronunciation'));
    expect(first.container.querySelector('button')).toHaveAttribute('aria-busy', 'false');
    expect(vi.getTimerCount()).toBe(1);
    vi.advanceTimersByTime(1000);
    expect(second.container.querySelector('button')).toHaveAttribute('aria-busy', 'true');
    first.unmount();
    vi.advanceTimersByTime(9000);
    expired();
  });
  it('D08 expired speech callbacks cannot resurrect or terminate a same-mounted retry', async () => {
    await speechPlayer(false);
    fireEvent.click(screen.getByRole('button'));
    const old: FakeUtterance = speech.speak.mock.calls[0][0];
    const callbacks = [old.onstart!, old.onend!, old.onerror!];
    vi.advanceTimersByTime(10000);
    expired();
    expect(speech.cancel).toHaveBeenCalledOnce();
    expect([old.onstart, old.onend, old.onerror]).toEqual([null, null, null]);
    fireEvent.click(screen.getByRole('button'));
    callbacks.forEach((callback) => callback());
    pending();
    vi.advanceTimersByTime(9999);
    pending();
    vi.advanceTimersByTime(1);
    expired();
    expect(speech.cancel).toHaveBeenCalledTimes(2);
  });
  it('D09 submitted speech with no start or error expires and cancels the queue once', async () => {
    await speechPlayer(false);
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).toHaveBeenCalledOnce();
    vi.advanceTimersByTime(9999);
    pending();
    vi.advanceTimersByTime(1);
    expired();
    vi.advanceTimersByTime(20000);
    expect(speech.cancel).toHaveBeenCalledOnce();
  });
  it('D10 preloaded speech starting at 9999 is never timed out while playing', async () => {
    await speechPlayer(false);
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(9999);
    const utterance: FakeUtterance = speech.speak.mock.calls[0][0];
    utterance.onstart?.();
    vi.advanceTimersByTime(20000);
    expect(screen.getByRole('button')).toHaveAccessibleName('Stop pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    expect(speech.cancel).not.toHaveBeenCalled();
    utterance.onend?.();
    expect(screen.getByRole('button')).toHaveAccessibleName('Play pronunciation');
    expect(vi.getTimerCount()).toBe(0);
  });
  it('D11 duplicate usable events submit once and do not renew the pre-start budget', async () => {
    await speechPlayer();
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(7000);
    voices();
    voices();
    expect(speech.speak).toHaveBeenCalledOnce();
    vi.advanceTimersByTime(2999);
    pending();
    vi.advanceTimersByTime(1);
    expired();
  });
  it('D12 genuine errors retain distinct localized feedback and same-mounted retries', async () => {
    await speechPlayer(false, 'uk');
    fireEvent.click(screen.getByRole('button'));
    speech.speak.mock.calls[0][0].onerror();
    expect(screen.getByRole('status')).toHaveTextContent('Аудіо недоступне. Спробуйте ще раз.');
    expect(vi.getTimerCount()).toBe(0);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    vi.advanceTimersByTime(10000);
    expect(screen.getByRole('status')).toHaveTextContent('Відтворення не почалося. Спробуйте ще раз.');
    expect(screen.getByRole('button')).toHaveAccessibleName('Послухати вимову');
    expect(screen.getByRole('status')).toHaveAttribute('lang', 'uk');
  });
  async function mediaPlayer(cdn = false) {
    if (cdn) vi.stubEnv('PUBLIC_AUDIO_CDN_URL', 'https://audio.example');
    speech.speak.mockImplementation(() => {});
    const Player = await player();
    render(<Player lemma="автобус" locale="en" />);
    await waitFor(() => expect(instances).toHaveLength(1));
    vi.useFakeTimers();
    return instances[0];
  }
  it.each(['resolve', 'reject'] as const)('D13 stalled media expires, resets and ignores late %s during a fresh retry', async (settlement) => {
    const media = await mediaPlayer();
    let resolve!: () => void;
    let reject!: (error: Error) => void;
    media.play.mockImplementationOnce(() => new Promise<void>((ok, fail) => { resolve = ok; reject = fail; }));
    fireEvent.click(screen.getByRole('button'));
    media.currentTime = 3;
    vi.advanceTimersByTime(9999);
    pending();
    vi.advanceTimersByTime(1);
    expired();
    expect(media.pause).toHaveBeenCalledOnce();
    expect(media.currentTime).toBe(0);
    // Each retry creates a fresh native element; control its pending promise too.
    class PendingAudio extends FakeAudio { play = vi.fn(() => new Promise<void>(() => {})); }
    vi.stubGlobal('Audio', PendingAudio);
    fireEvent.click(screen.getByRole('button'));
    expect(instances).toHaveLength(2);
    if (settlement === 'resolve') resolve(); else reject(new Error('late rejection'));
    await Promise.resolve();
    pending();
    expect(speech.speak).not.toHaveBeenCalled();
    vi.advanceTimersByTime(9999);
    pending();
    vi.advanceTimersByTime(1);
    expired();
  });
  it('D13 media play resolution at 9999 clears startup expiry', async () => {
    const media = await mediaPlayer();
    let resolve!: () => void;
    media.play.mockImplementationOnce(() => new Promise<void>((ok) => { resolve = ok; }));
    fireEvent.click(screen.getByRole('button'));
    vi.advanceTimersByTime(9999);
    resolve();
    await Promise.resolve();
    vi.advanceTimersByTime(20000);
    expect(screen.getByRole('button')).toHaveAccessibleName('Stop pronunciation');
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
  });
  it.each(['expire', 'start'] as const)('D14 CDN pre-start fallback shares remaining budget: %s', async (outcome) => {
    const media = await mediaPlayer(true);
    let resolve!: () => void;
    media.play.mockImplementationOnce(() => new Promise<void>((ok) => { resolve = ok; }));
    fireEvent.click(screen.getByRole('button'));
    const error = media.onerror!;
    vi.advanceTimersByTime(7000);
    error();
    error();
    expect(speech.speak).toHaveBeenCalledOnce();
    resolve();
    await Promise.resolve();
    pending();
    vi.advanceTimersByTime(2999);
    pending();
    if (outcome === 'start') speech.speak.mock.calls[0][0].onstart();
    vi.advanceTimersByTime(1);
    if (outcome === 'expire') expired();
    else {
      expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
      expect(screen.getByRole('status')).toBeEmptyDOMElement();
    }
    vi.advanceTimersByTime(20000);
    expect(speech.speak).toHaveBeenCalledOnce();
  });
  it.each(['expire', 'start'] as const)('D14 started CDN fallback opens exactly one fresh speech budget: %s', async (outcome) => {
    const media = await mediaPlayer(true);
    fireEvent.click(screen.getByRole('button'));
    await Promise.resolve();
    vi.advanceTimersByTime(20000);
    const error = media.onerror!;
    error();
    pending();
    expect(speech.speak).toHaveBeenCalledOnce();
    expect(media.pause).toHaveBeenCalled();
    expect(media.currentTime).toBe(0);
    vi.advanceTimersByTime(9999);
    error();
    pending();
    const utterance: FakeUtterance = speech.speak.mock.calls[0][0];
    const lateStart = utterance.onstart!;
    if (outcome === 'start') lateStart();
    vi.advanceTimersByTime(1);
    if (outcome === 'expire') { expired(); lateStart(); expired(); }
    else {
      expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
      expect(screen.getByRole('status')).toBeEmptyDOMElement();
    }
    error();
    vi.advanceTimersByTime(20000);
    expect(speech.speak).toHaveBeenCalledOnce();
    expect(speech.cancel).toHaveBeenCalledTimes(outcome === 'expire' ? 1 : 0);
    expect(vi.getTimerCount()).toBe(0);
  });
});
