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
  en: { play: 'Play pronunciation', stop: 'Stop pronunciation', error: 'Audio unavailable. Try again.', expired: 'Audio did not start. Try again.' },
  uk: { play: 'Послухати вимову', stop: 'Зупинити відтворення', error: 'Аудіо недоступне. Спробуйте ще раз.', expired: 'Відтворення не почалося. Спробуйте ще раз.' },
};

let manifestUnavailable = false;

export function resetManifestCacheForTesting(): void {
  manifestRequest = undefined;
  manifestUnavailable = false;
}

function manifest(): Promise<Manifest> {
  if (manifestUnavailable) {
    return Promise.reject(new Error('audio manifest unavailable'));
  }
  if (!manifestRequest) {
    manifestRequest = fetch(`${getAudioBase()}manifest.json`).then(async (response) => {
      if (response.status === 404) {
        manifestUnavailable = true;
        throw new Error('audio manifest unavailable');
      }
      if (!response.ok) {
        throw new Error('audio manifest fetch failed');
      }
      try {
        const value = await response.json();
        if (value?.schemaVersion !== 1 || !value.entries || typeof value.entries !== 'object' || Array.isArray(value.entries)) {
          manifestUnavailable = true;
          throw new Error('invalid audio manifest');
        }
        return value;
      } catch (err) {
        manifestUnavailable = true;
        throw err;
      }
    }).catch((error) => {
      manifestRequest = undefined;
      throw error;
    });
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
  let cancelVoiceWait: (() => void) | undefined;
  let disposed = false;
  let audio: HTMLAudioElement | undefined;
  let isCdn = false;
  let phase: 'idle' | 'pending' | 'playing' = 'idle';
  let audioUsed = false;
  let audioSource = '';
  let failure: 'error' | 'expired' | undefined;
  let startupTimer: number | undefined;
  let attempt = 0;
  let fallbackHandledAttempt = 0;
  const copy = () => COPY[(root.dataset.locale || document.documentElement.dataset.chromeLocale) === 'en' ? 'en' : 'uk'];
  const label = () => {
    const locale = copy() === COPY.en ? 'en' : 'uk';
    button.lang = status.lang = locale;
    button.textContent = phase === 'idle' ? copy().play : copy().stop;
    button.setAttribute('aria-busy', String(phase === 'pending'));
    status.textContent = failure ? copy()[failure] : '';
  };
  const stop = () => {
    attempt++;
    window.clearTimeout(startupTimer);
    cancelVoiceWait?.();
    if (active === stop) active = undefined;
    if (utterance) {
      utterance.onstart = utterance.onend = utterance.onerror = null;
      utterance = undefined;
      synthesis.cancel();
    }
    if (audio) {
      audio.onended = audio.onpause = audio.onerror = null;
      audio.pause();
      audio.currentTime = 0;
    }
    phase = 'idle';
    label();
  };
  const failed = (reason: 'error' | 'expired' = 'error') => {
    if (disposed) return;
    failure = reason;
    stop();
  };
  const startBudget = (current: number) => {
    startupTimer = window.setTimeout(() => {
      if (!disposed && current === attempt && phase === 'pending') failed('expired');
    }, 10000);
  };
  const speakWithSynthesis = (current: number) => {
    if (disposed || current !== attempt) return;
    if (!synthesis || !window.SpeechSynthesisUtterance) { failed(); return; }
    const voices = synthesis.getVoices();
    // An empty catalog can still be loading; the API has no catalog-complete flag.
    if (voices.length === 0) {
      if (!cancelVoiceWait) {
        const voicesChanged = () => {
          if (disposed || current !== attempt) return;
          try { speakWithSynthesis(current); } catch { failed(); }
        };
        synthesis.addEventListener('voiceschanged', voicesChanged);
        cancelVoiceWait = () => {
          synthesis.removeEventListener('voiceschanged', voicesChanged);
          cancelVoiceWait = undefined;
        };
      }
      return;
    }
    cancelVoiceWait?.();
    const ukVoices = voices.filter((v) => v.lang.toLowerCase().startsWith('uk'));
    const voice = ukVoices.find((v) => v.localService) ?? ukVoices[0];
    if (!voice) { failed(); return; }
    if (synthesis?.speaking || utterance) {
      synthesis?.cancel();
      utterance = undefined;
    }
    utterance = new SpeechSynthesisUtterance(spoken);
    utterance.lang = 'uk-UA';
    utterance.voice = voice;
    utterance.onstart = () => {
      if (disposed || current !== attempt) return;
      window.clearTimeout(startupTimer);
      phase = 'playing';
      label();
    };
    utterance.onend = () => {
      if (disposed || current !== attempt) return;
      window.clearTimeout(startupTimer);
      utterance = undefined;
      if (active === stop) active = undefined;
      attempt++;
      phase = 'idle';
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
      if (audio) {
        audio.onended = audio.onpause = audio.onerror = null;
        audio.pause();
        audio.currentTime = 0;
      }
      if (phase === 'playing') startBudget(current);
      phase = 'pending';
      label();
      try { speakWithSynthesis(current); } catch { failed(); }
    } else {
      failed();
    }
  };
  const click = async (event: Event) => {
    event.stopPropagation();
    if (phase !== 'idle') { stop(); return; }
    active?.();
    active = stop;
    failure = undefined;
    phase = 'pending';
    label();
    const current = ++attempt;
    startBudget(current);
    try {
      if (audio) {
        if (audioUsed) {
          // Media events carry no attempt ID; retries need their own native element.
          audio.onended = audio.onpause = audio.onerror = null;
          audio.removeAttribute('src');
          audio.load();
          audio = new Audio(audioSource);
          audio.preload = 'none';
        }
        audioUsed = true;
        const media = audio;
        const finished = () => {
          if (disposed || current !== attempt) return;
          window.clearTimeout(startupTimer);
          attempt++;
          if (active === stop) active = undefined;
          phase = 'idle';
          label();
        };
        media.onended = finished;
        media.onpause = () => { if (phase === 'playing' && media.paused) finished(); };
        media.onerror = () => handlePlaybackFailure(current, isCdn);
        media.currentTime = 0;
        await media.play();
        if (disposed || current !== attempt || active !== stop || fallbackHandledAttempt === current) {
          media.pause();
          return;
        }
        window.clearTimeout(startupTimer);
        phase = 'playing';
        label();
      } else {
        speakWithSynthesis(current);
      }
    } catch {
      handlePlaybackFailure(current, isCdn);
    }
  };
  const keydown = (event: KeyboardEvent) => event.stopPropagation();
  root.lang = 'uk';
  const fallback = (root.dataset.fallback as 'speech' | 'hide' | 'disable') || 'speech';
  const applyFallbackState = () => {
    if (disposed || audio) return;
    if (fallback === 'hide') {
      button.hidden = true;
    } else if (fallback === 'disable') {
      button.hidden = !lemma;
      button.disabled = true;
      button.setAttribute('aria-disabled', 'true');
    } else {
      button.hidden = !lemma;
      button.disabled = false;
      button.removeAttribute('aria-disabled');
    }
  };
  if (fallback === 'hide') {
    button.hidden = true;
  } else {
    button.hidden = !lemma;
    button.disabled = false;
    button.removeAttribute('aria-disabled');
  }
  label();
  status.textContent = '';
  button.addEventListener('click', click);
  button.addEventListener('keydown', keydown);
  window.addEventListener('pagehide', stop);
  document.addEventListener('astro:before-swap', stop);
  const localeObserver = new MutationObserver(label);
  localeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-chrome-locale'] });
  if (lemma) {
    const attachAudio = (file: string, fromCdn: boolean) => {
      audioSource = `${getAudioBase()}${file}`;
      audio = new Audio(audioSource);
      isCdn = fromCdn;
      audio.preload = 'none';
      audio.onerror = () => {
        if (!fromCdn) failed();
      };
      label();
      button.hidden = false;
      button.disabled = false;
      button.removeAttribute('aria-disabled');
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
          } else if (!disposed && !audio) {
            applyFallbackState();
          }
        }).catch(() => {
          if (!disposed && !audio) applyFallbackState();
        });
      } else {
        applyFallbackState();
      }
    }).catch(() => {
      if (disposed) return;
      const cdn = getCdnBase();
      if (cdn) {
        void lemmaAudioPath(lemma).then((path) => {
          if (!disposed && !audio && path) {
            attachAudio(path, true);
          } else if (!disposed && !audio) {
            applyFallbackState();
          }
        }).catch(() => {
          if (!disposed && !audio) applyFallbackState();
        });
      } else {
        applyFallbackState();
      }
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
    window.removeEventListener('pagehide', stop);
    document.removeEventListener('astro:before-swap', stop);
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
