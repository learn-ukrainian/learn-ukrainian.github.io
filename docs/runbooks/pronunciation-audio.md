# Pronunciation audio (#4696)

The default publish path is **on-device Ukrainian TTS** for Practice and Atlas,
using `window.speechSynthesis` and `SpeechSynthesisUtterance` with `lang = 'uk-UA'`.
Operator GO (2026-09-06) permits pronunciation playback; there is no storage for
bulk WAV libraries. Pages does not run Piper or require generated clips.

This follows Clozemaster's iOS system-voice approach, rather than downloading a
clip library. Its [voice setup guide](https://docs.clozemaster.com/article/22-how-do-i-download-text-to-speech-tts-voices-on-ios)
points to Settings → Accessibility → Spoken Content (Read & Speak on newer iOS)
→ Voices. Install a Ukrainian Apple system voice there, then retry playback in
iPhone Safari. Availability depends on which voices Safari exposes through
[`getVoices()`](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/getVoices).

## Optional local Piper pipeline (#7717)

The optional local generator selects **200 eligible A1 practice lemmas**, with a hard maximum of
500 per invocation. It uses the hydrated `practice-lexemes.A1.json`, removes
duplicate normalized lemmas and preserves hydrated deck order. Keys fold case,
stress marks and apostrophe variants just like the practice deck. The existing stress oracle
(`scripts.verification.stress`, ULIF-derived dictionary and repository overrides)
receives the lexeme POS and must return one unambiguous reading. Single-syllable
Ukrainian words use their unmarked surface because there is no stress-position
choice. Other ambiguous, unknown and invalid inputs are
recorded as exclusions before the cap; they are never given guessed stress.
The manifest records the source deck version, SHA-256, source row count, selected
count, exclusions and stress dictionary provenance. This is a bounded slice,
not coverage of the whole Practice Hub or Atlas.

## Generate and build

From the repository root in a dispatch worktree:

```sh
make pronunciation-setup PYTHON=/absolute/path/to/shared/project/python
make pronunciation-audio PYTHON=/absolute/path/to/shared/project/python
# Optional smaller smoke (hard maximum remains 500):
make pronunciation-audio PYTHON=/absolute/path/to/shared/project/python PRONUNCIATION_LIMIT=5
```

`pronunciation-setup` installs into ignored `batch_state/tts-runtime` using pip's
`--target`; it does not create a virtualenv or change the shared interpreter.
The stress package is installed without its optional Stanza dependency: the
existing dictionary oracle uses marisa-trie directly and does not run NLP models.
`pronunciation-audio` hydrates the current practice deck and downloads missing
model files from a pinned revision, checking both SHA-256 values. Subsequent
runs use the local model. For an offline run after hydration/download:

```sh
/absolute/path/to/shared/project/python -m scripts.audio.generate_pronunciation --limit 200
```

For a local WAV experiment, run the ordinary site build after generation.
Generated WAVs and manifests remain ignored local assets; do not generate or
commit bulk WAVs for Pages, or add Piper to the Pages build. A build without
these assets still offers on-device pronunciation. No remote speech API,
microphone access or autoplay is used.

## Optional engine and licenses

- Runtime: **Piper `piper-tts==1.3.0`**, GPL-3.0-or-later, as declared in the
  [published package metadata](https://pypi.org/project/piper-tts/1.3.0/).
- Voice: **`uk_UA-ukrainian_tts-medium`**, speaker `lada` (ID 0), mono PCM16,
  22,050 Hz. This text-input model supports combining acute stress marks.
- Model repository: [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices),
  MIT repository license; pinned revision
  `1162a9173d0ce503555aed757976b7a9912eae4c`.
- The voice's [model card](https://huggingface.co/rhasspy/piper-voices/blob/1162a9173d0ce503555aed757976b7a9912eae4c/uk/uk_UA/ukrainian_tts/medium/MODEL_CARD)
  identifies its dataset as CC0.
- The optional Piper runtime stays in the local generation environment; only
  its WAVs and JSON are consumed by the player when explicitly present.

Model and config checksums are pinned in the generator. The manifest records
runtime/voice/speaker/model/dictionary provenance. Synthesis noise can produce
different WAV bytes on repeat runs: source selection is deterministic; bitwise
identical waveforms are not promised.

## Publication and playback

WAV filenames are their SHA-256. A versioned `manifest-<sha256>.json` and the
current `manifest.json` are published only after every selected clip validates.
A failed run preserves the previous current manifest; unreferenced WAVs are not
published through it. Generated assets and runtime/model caches are ignored.
Build in a fresh output tree to avoid retaining old unreferenced generations.
No LFS configuration or bulk audio is committed.

The same player serves practice flashcards and Atlas headwords. A nonempty lemma
gets a visible button immediately, even if the optional manifest is missing or
invalid. An explicitly present safe WAV entry can be used instead of speech;
otherwise a click speaks only the source Ukrainian lemma, never its English
gloss. The spoken headword is marked `lang="uk"` in the UI.

For speech, each click rechecks available voices and selects an installed Ukrainian voice
(`uk*`), preferring local system voices while allowing browser online Ukrainian voices
(such as Microsoft Polina on Windows Edge and Google Ukrainian on Chrome). It never falls
back to a non-Ukrainian voice. Unsupported browsers and audio/speech failures use the same
feedback. Button and status labels follow the chrome locale.

Playback is explicit and exclusive across speech and pre-recorded audio clips (`.opus`, `.webm`,
`.mp3`, `.wav`, optionally served via `PUBLIC_AUDIO_CDN_URL`). Stop, changing a
card, or leaving an article cancels speech or pauses the audio. Atlas SSR pages
use the same small DOM controller as React pages, without hydrating the whole
article or shipping its catalog.
The practice player sits outside the card's flip button beside its subtitle;
keyboard activation cannot flip or rate a card. Ukrainian chrome uses only
Ukrainian player labels; English chrome is supported for beginners.

## Batch Opus synthesis and Hugging Face CDN distribution (#7873)

Phase 2 introduces scalable bulk audio distribution using high-efficiency OGG/Opus encoding
and permanent Cloudflare edge caching backed by Hugging Face Datasets:

1. **Audio Compression**: Encoded at 24 kbps mono VBR (24 kHz) via `ffmpeg` with `libopus`.
   Audio files average ~1.5–3 KB per word (~60 MB for 25,000 words), offering >92% bandwidth
   reduction compared to raw PCM16 WAVs.
2. **Deterministic Lemma Hashing**: Client and generation pipeline compute the identical
   SHA-256 hash from normalized lemma text (`pronunciationKey` / `lemma_digest`). Files are
   organized with a 2-character directory prefix (`audio/xx/{hash}.opus`) to prevent single-directory
   inode scaling issues.
3. **Zero-Manifest On-Demand Fetch**: When `PUBLIC_AUDIO_CDN_URL` is configured, browser clients
   compute `lemmaAudioPath(lemma)` via `crypto.subtle.digest` and fetch clips directly without
   downloading multi-megabyte JSON manifests.
4. **Resilient Fallback**: If an audio clip is missing (404) or network fails, `PronunciationPlayer`
   transparently falls back to on-device Ukrainian speech synthesis.
5. **Batch Generation**:
   ```sh
   /absolute/path/to/project/python -m scripts.audio.batch_synthesize_opus --manifest batch_state/manifest_batch18.json --limit 500 --download-model
   ```
6. **Hugging Face Hub Sync**:
   ```sh
   /absolute/path/to/project/python -m scripts.audio.sync_hf_dataset --local-dir batch_state/audio_opus --repo-id learn-ukrainian/word-atlas-audio
   ```

## Verification and remaining pronunciation evidence

```sh
/absolute/path/to/shared/project/python -m pytest tests/test_pronunciation_generator.py tests/test_batch_synthesize_opus.py tests/test_sync_hf_dataset.py -q
cd site
npx vitest run tests/unit/pronunciation-player.test.tsx
```

The tiny `tests/fixtures/audio/pronunciation.wav` is a Piper-generated clip of
`або`, using the stress oracle's reading; it tests WAV handling, not Ukrainian
correctness. It has the same voice provenance as above. Tests cover selection,
exclusions, caps, invalid output, atomic publication, playback failure, lifecycle,
locale, SSR startup and card activation isolation. Player tests also cover missing
manifests, Ukrainian voice selection, missing/late voices, speech cancellation,
completion/errors, non-Ukrainian voice rejection, and remote/online Ukrainian voice acceptance.

**Listening mode stays disabled.** Valid WAVs and source-verified synthesis text
prove the pipeline, not the pronunciation of the resulting sound. Before enabling
listening or claiming pronunciation certification, a Ukrainian-qualified reviewer
must independently listen to held-out clips selected from the generated manifest,
check word identity and stress against the source, and report the checked count,
errors and remaining coverage. Any wrong-word or stress finding blocks that
claim; retain the disabled listening mode and correct/re-evaluate the affected
engine/input. The release owner retains that residual evidence on #4696; device voice
availability and pronunciation quality require real-device listening evidence.
Mocked browser tests establish controller behavior, not audible correctness.
