import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';

const FILE = `${'a'.repeat(64)}.wav`;
let instances: FakeAudio[];
const UK_VOICE = { lang: 'uk-UA', localService: true, name: 'Ukrainian' } as SpeechSynthesisVoice;
class FakeUtterance {
  lang = '';
  voice: SpeechSynthesisVoice | null = null;
  onend: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(public text: string) {}
}
let speech: { getVoices: ReturnType<typeof vi.fn>; speak: ReturnType<typeof vi.fn>; cancel: ReturnType<typeof vi.fn> };
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
  speech = { getVoices: vi.fn(() => [UK_VOICE]), speak: vi.fn(), cancel: vi.fn() };
  vi.stubGlobal('speechSynthesis', speech);
  vi.stubGlobal('SpeechSynthesisUtterance', FakeUtterance);
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
    fireEvent.click(screen.getByRole('button', { name: 'Stop pronunciation' }));
    expect(speech.cancel).toHaveBeenCalledOnce();
    lateError();
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    expect(button).toHaveTextContent('Play pronunciation');
  });

  it.each(['en', 'uk'] as const)('rejects English and remote voices with %s feedback and allows retry', async (locale) => {
    speech.getVoices.mockReturnValue([{lang: 'en-US', localService: true}, {...UK_VOICE, localService: false}]);
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

  it('handles voices arriving after mount without autoplay', async () => {
    speech.getVoices.mockReturnValue([]);
    const Player = await player();
    render(<Player lemma="автобус" />);
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).not.toHaveBeenCalled();
    speech.getVoices.mockReturnValue([UK_VOICE]);
    window.dispatchEvent(new Event('voiceschanged'));
    expect(speech.speak).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button'));
    expect(speech.speak).toHaveBeenCalledOnce();
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
  instances[0].pause.mockClear();
  finish();
  await Promise.resolve();
  expect(instances[0].pause).not.toHaveBeenCalled();
  expect(button).toHaveTextContent('Stop pronunciation');
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
