/** Shared controller for React practice cards and SSR-only Atlas articles. */
function getCdnBase(): string {
  return (import.meta.env.PUBLIC_AUDIO_CDN_URL || '').replace(/\/$/, '');
}

function getAudioBase(): string {
  const cdn = getCdnBase();
  return cdn ? `${cdn}/` : `${(import.meta.env.BASE_URL || '').replace(/\/$/, '')}/audio/pronunciation/`;
}
type Manifest = { schemaVersion: number; entries: Record<string, { file: string }> };
let manifestRequest: Promise<Manifest> | undefined;
let active: (() => void) | undefined;
const mounted = new WeakMap<HTMLElement, () => void>();

const COPY = {
  en: { play: 'Play pronunciation', stop: 'Stop pronunciation', error: 'Audio unavailable. Try again.' },
  uk: { play: 'Послухати вимову', stop: 'Зупинити відтворення', error: 'Аудіо недоступне. Спробуйте ще раз.' },
};

function manifest(): Promise<Manifest> {
  if (!manifestRequest) {
    manifestRequest = fetch(`${getAudioBase()}manifest.json`).then(async (response) => {
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

export async function lemmaAudioPath(lemma: string, ext = 'opus', shard = true): Promise<string> {
  const key = pronunciationKey(lemma);
  if (typeof crypto === 'undefined' || !crypto.subtle) return '';
  const hashBuf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(key));
  const hex = Array.from(new Uint8Array(hashBuf)).map((b) => b.toString(16).padStart(2, '0')).join('');
  return shard ? `${hex.slice(0, 2)}/${hex}.${ext}` : `${hex}.${ext}`;
}

export function mountPronunciationPlayer(root: HTMLElement): () => void {
  mounted.get(root)?.();
  const button = root.querySelector('button')!;
  const status = root.querySelector<HTMLElement>('[role="status"]')!;
  const rawSpoken = (root.dataset.pronunciationLemma ?? '').trim();
  const headerStress = root.parentElement?.querySelector('.word-stress')?.textContent?.replace(/[[\]]/g, '').trim();
  const spoken = headerStress || rawSpoken;
  const lemma = pronunciationKey(rawSpoken);
  const synthesis = window.speechSynthesis;
  let utterance: SpeechSynthesisUtterance | undefined;
  let disposed = false;
  let audio: HTMLAudioElement | undefined;
  let isCdn = false;
  let playing = false;
  let hasError = false;
  let attempt = 0;
  let fallbackHandledAttempt = 0;
  const copy = () => COPY[(root.dataset.locale || document.documentElement.dataset.chromeLocale) === 'en' ? 'en' : 'uk'];
  const label = () => {
    const locale = copy() === COPY.en ? 'en' : 'uk';
    button.lang = status.lang = locale;
    button.textContent = playing ? copy().stop : copy().play;
    status.textContent = hasError ? copy().error : '';
  };
  const stop = () => {
    attempt++;
    if (active === stop) active = undefined;
    if (utterance) {
      utterance.onend = utterance.onerror = null;
      utterance = undefined;
      synthesis.cancel();
    }
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
  const speakWithSynthesis = (current: number) => {
    if (disposed || current !== attempt) return;
    const voices = synthesis?.getVoices() ?? [];
    const ukVoices = voices.filter((v) => v.lang.toLowerCase().startsWith('uk'));
    const voice = ukVoices.find((v) => v.localService) ?? ukVoices[0];
    if (!voice || !window.SpeechSynthesisUtterance) { failed(); return; }
    if (synthesis?.speaking || utterance) {
      synthesis?.cancel();
      utterance = undefined;
    }
    utterance = new SpeechSynthesisUtterance(spoken);
    utterance.lang = 'uk-UA';
    utterance.voice = voice;
    utterance.onend = () => {
      if (disposed || current !== attempt) return;
      utterance = undefined;
      if (active === stop) active = undefined;
      playing = false;
      label();
    };
    utterance.onerror = () => {
      if (!disposed && current === attempt) failed();
    };
    synthesis.speak(utterance);
  };
  const handlePlaybackFailure = (current: number, fromCdnFallback: boolean) => {
    if (disposed || current !== attempt) return;
    if (fallbackHandledAttempt === current) return;
    fallbackHandledAttempt = current;
    if (fromCdnFallback) {
      speakWithSynthesis(current);
    } else {
      failed();
    }
  };
  const click = async (event: Event) => {
    event.stopPropagation();
    if (playing) { stop(); return; }
    active?.();
    active = stop;
    hasError = false;
    playing = true;
    label();
    const current = ++attempt;
    try {
      if (audio) {
        audio.currentTime = 0;
        await audio.play();
        if (disposed || !playing || active !== stop) audio.pause();
      } else {
        speakWithSynthesis(current);
      }
    } catch {
      handlePlaybackFailure(current, isCdn);
    }
  };
  const keydown = (event: KeyboardEvent) => event.stopPropagation();
  root.lang = 'uk';
  button.hidden = !lemma;
  label();
  status.textContent = '';
  button.addEventListener('click', click);
  button.addEventListener('keydown', keydown);
  const localeObserver = new MutationObserver(label);
  localeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-chrome-locale'] });
  if (lemma) {
    const attachAudio = (file: string, fromCdn: boolean) => {
      audio = new Audio(`${getAudioBase()}${file}`);
      isCdn = fromCdn;
      audio.preload = 'none';
      audio.onended = () => { attempt++; playing = false; label(); };
      audio.onpause = () => { attempt++; playing = false; label(); };
      audio.onerror = () => {
        if (fromCdn) {
          if (playing) {
            handlePlaybackFailure(attempt, true);
          }
        } else {
          failed();
        }
      };
      label();
      button.hidden = false;
    };
    manifest().then((value) => {
      if (disposed) return;
      const entry = Object.hasOwn(value.entries, lemma) ? value.entries[lemma] : undefined;
      const cdn = getCdnBase();
      if (entry && /^([a-f0-9]{2}\/)?[a-f0-9]{64}\.(opus|webm|mp3|wav)$/.test(entry.file)) {
        attachAudio(entry.file, Boolean(cdn));
      } else if (cdn) {
        void lemmaAudioPath(lemma).then((path) => {
          if (!disposed && !audio && path) {
            attachAudio(path, true);
          }
        }).catch(() => { /* Optional on-demand audio falls back to synthesis */ });
      }
    }).catch(() => {
      const cdn = getCdnBase();
      if (disposed || !cdn) return;
      void lemmaAudioPath(lemma).then((path) => {
        if (!disposed && !audio && path) {
          attachAudio(path, true);
        }
      }).catch(() => { /* Optional on-demand audio falls back to synthesis */ });
    });
  }
  const cleanup = () => {
    disposed = true;
    stop();
    if (audio) {
      audio.onended = audio.onpause = audio.onerror = null;
      if (active === stop) active = undefined;
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
