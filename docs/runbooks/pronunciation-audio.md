# Pronunciation audio (#4696)

The build generates **200 eligible A1 practice lemmas**, with a hard maximum of
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

Run the ordinary site build after generation. The Pages workflow executes these
steps before its build, so ignored audio is included in the deployed artifact.
The Pages workflow caches the voice under its pinned revision; restored files
still undergo checksum verification on every run.
Local builds without generation offer no pronunciation buttons. No browser TTS,
remote speech API, microphone access or autoplay is used.

## Engine and licenses

- Runtime: **Piper `piper-tts==1.3.0`**, GPL-3.0-or-later, as declared in the
  [published package metadata](https://pypi.org/project/piper-tts/1.3.0/).
- Voice: **`uk_UA-ukrainian_tts-medium`**, speaker `lada` (ID 0), mono PCM16,
  22,050 Hz. This text-input model supports combining acute stress marks.
- Model repository: [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices),
  MIT repository license; pinned revision
  `1162a9173d0ce503555aed757976b7a9912eae4c`.
- The voice's [model card](https://huggingface.co/rhasspy/piper-voices/blob/1162a9173d0ce503555aed757976b7a9912eae4c/uk/uk_UA/ukrainian_tts/medium/MODEL_CARD)
  identifies its dataset as CC0.
- Neural Piper installed and generated the slice; the espeak-ng fallback was not
  needed. The runtime stays in the build environment; the site serves WAVs and
  JSON only.

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

The player uses the same manifest on practice flashcards and Atlas headwords.
Uncovered lemmas, an absent manifest or unsafe filenames produce no play button.
Audio fetch/decode/play failures produce localized feedback and allow a retry.
Playback is explicit, only one player runs at a time, and changing a card or
leaving an article stops it. Atlas SSR pages use the same small DOM controller
as React pages, without hydrating the whole article or shipping its catalog.
The practice player sits outside the card's flip button beside its subtitle;
keyboard activation cannot flip or rate a card. Ukrainian chrome uses only
Ukrainian player labels; English chrome is supported for beginners.

## Verification and remaining pronunciation evidence

```sh
/absolute/path/to/shared/project/python -m pytest tests/test_pronunciation_generator.py -q
cd site
npx vitest run tests/unit/pronunciation-player.test.tsx
```

The tiny `tests/fixtures/audio/pronunciation.wav` is a Piper-generated clip of
`або`, using the stress oracle's reading; it tests WAV handling, not Ukrainian
correctness. It has the same voice provenance as above. Tests cover selection,
exclusions, caps, invalid output, atomic publication, playback failure, lifecycle,
locale, SSR startup and card activation isolation.

**Listening mode stays disabled.** Valid WAVs and source-verified synthesis text
prove the pipeline, not the pronunciation of the resulting sound. Before enabling
listening or claiming pronunciation certification, a Ukrainian-qualified reviewer
must independently listen to held-out clips selected from the generated manifest,
check word identity and stress against the source, and report the checked count,
errors and remaining coverage. Any wrong-word or stress finding blocks that
claim; retain the disabled listening mode and correct/re-evaluate the affected
engine/input. This PR's owner retains that residual evidence on #4696 rather than
closing it as full Atlas audio coverage.
