/** Shared controller for React practice cards and SSR-only Atlas articles. */
const BASE = `${import.meta.env.BASE_URL.replace(/\/$/, '')}/audio/pronunciation/`;
type Manifest = { schemaVersion: number; entries: Record<string, { file: string }> };
let manifestRequest: Promise<Manifest> | undefined;
let active: HTMLAudioElement | undefined;
const mounted = new WeakMap<HTMLElement, () => void>();

const COPY = {
  en: { play: 'Play pronunciation', stop: 'Stop pronunciation', error: 'Audio unavailable. Try again.' },
  uk: { play: 'Послухати вимову', stop: 'Зупинити відтворення', error: 'Аудіо недоступне. Спробуйте ще раз.' },
};

function manifest(): Promise<Manifest> {
  if (!manifestRequest) {
    manifestRequest = fetch(`${BASE}manifest.json`).then(async (response) => {
      if (!response.ok) throw new Error('audio manifest unavailable');
      const value = await response.json();
      if (value?.schemaVersion !== 1 || !value.entries || typeof value.entries !== 'object' || Array.isArray(value.entries)) {
        throw new Error('invalid audio manifest');
      }
      return value;
    }).catch((error) => { manifestRequest = undefined; throw error; });
  }
  return manifestRequest;
}

export function pronunciationKey(lemma: string): string {
  return lemma.toLowerCase().replace(/[\u0300\u0301]/g, '').replace(/[’ʼ]/g, "'").trim().normalize('NFC');
}

export function mountPronunciationPlayer(root: HTMLElement): () => void {
  mounted.get(root)?.();
  const button = root.querySelector('button')!;
  const status = root.querySelector<HTMLElement>('[role="status"]')!;
  const lemma = pronunciationKey(root.dataset.pronunciationLemma ?? '');
  let disposed = false;
  let audio: HTMLAudioElement | undefined;
  let playing = false;
  let hasError = false;
  let attempt = 0;
  const copy = () => COPY[(root.dataset.locale || document.documentElement.dataset.chromeLocale) === 'en' ? 'en' : 'uk'];
  const label = () => {
    button.textContent = playing ? copy().stop : copy().play;
    status.textContent = hasError ? copy().error : '';
  };
  const stop = () => {
    attempt++;
    audio?.pause();
    if (audio) audio.currentTime = 0;
    playing = false;
    label();
  };
  const failed = () => {
    if (disposed) return;
    hasError = true;
    stop();
  };
  const click = async (event: Event) => {
    event.stopPropagation();
    if (!audio) return;
    if (playing) { stop(); return; }
    if (active && active !== audio) active.pause();
    active = audio;
    hasError = false;
    playing = true;
    label();
    const current = ++attempt;
    try {
      await audio.play();
      if (disposed || !playing || active !== audio) audio.pause();
    } catch {
      if (!disposed && current === attempt) failed();
    }
  };
  const keydown = (event: KeyboardEvent) => event.stopPropagation();
  button.hidden = true;
  status.textContent = '';
  button.addEventListener('click', click);
  button.addEventListener('keydown', keydown);
  const localeObserver = new MutationObserver(label);
  localeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-chrome-locale'] });
  if (lemma) void manifest().then((value) => {
    if (disposed) return;
    const entry = Object.hasOwn(value.entries, lemma) ? value.entries[lemma] : undefined;
    if (!entry || !/^[a-f0-9]{64}\.wav$/.test(entry.file)) return;
    audio = new Audio(`${BASE}${entry.file}`);
    audio.preload = 'none';
    audio.onended = () => { attempt++; playing = false; label(); };
    audio.onpause = () => { attempt++; playing = false; label(); };
    audio.onerror = failed;
    label();
    button.hidden = false;
  }).catch(() => { /* No assets: no false promise of playback outside this slice. */ });
  const cleanup = () => {
    disposed = true;
    stop();
    if (audio) {
      audio.onended = audio.onpause = audio.onerror = null;
      if (active === audio) active = undefined;
      audio.removeAttribute('src');
      audio.load();
    }
    button.removeEventListener('click', click);
    button.removeEventListener('keydown', keydown);
    localeObserver.disconnect();
    mounted.delete(root);
  };
  mounted.set(root, cleanup);
  return cleanup;
}

export function mountAtlasPronunciation(): void {
  document.querySelectorAll<HTMLElement>('[data-word-atlas] [data-pronunciation-lemma]').forEach((root) => {
    if (!mounted.has(root)) mountPronunciationPlayer(root);
  });
}

export function unmountAtlasPronunciation(): void {
  document.querySelectorAll<HTMLElement>('[data-word-atlas] [data-pronunciation-lemma]').forEach((root) => mounted.get(root)?.());
}
