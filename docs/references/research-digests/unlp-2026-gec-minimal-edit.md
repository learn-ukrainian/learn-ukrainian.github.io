# How Far Can Prompting Go for Minimal-Edit Ukrainian GEC?

Source: Karpo & Chernodub, UNLP 2026 — https://aclanthology.org/2026.unlp-1.13/

Compact per-record digest for research-registry id `unlp-2026-gec-minimal-edit`.
Paraphrase and pointers only; the published prompt and its exemplars are **not**
reproduced here. Read the full source at the link above.

## Finding

The paper studies minimal-edit Ukrainian grammatical error correction with prompting
alone, evaluated span-level with a Ukrainian adaptation of ERRANT. Its best prompted
configuration (minimal-edit framing, few-shot, an LLM-optimised prompt written in
Ukrainian) closes most of the gap from earlier prompted baselines to fine-tuned
state of the art. Two design points transfer to our reviewer/fixer work:

- **Minimal-edit framing.** The system prompt is organised around a sixteen-category
  error taxonomy (spelling, punctuation, and grammar sub-types such as case, gender,
  number, aspect, tense, voice, preposition, participle, comparison, conjunction, and
  a catch-all) plus strict rules: make the smallest possible change, never substitute
  synonyms or rephrase, preserve quote style and capitalisation, and if in doubt do not
  change. This is exactly the framing a fixer needs so it stops rewriting authorial voice.
- **Prompt language.** The minimal-edit instructions are in Ukrainian because the
  rules they encode are language-specific; the authors report the Claude model family
  in particular benefits from Ukrainian prompts even without examples.

## Five Ukrainian-specific over-correction patterns (their headline caution)

The paper attributes the top false-positive sources to heuristics calibrated to
English, and names five recurring over-corrections we should suppress explicitly in a
fixer: en-dash over-normalisation outside direct speech; reformatting quotation-mark
dialogue into dash style; synonym or register substitution; meddling with phonetically
conditioned preposition alternation (the в/у and з/із/зі families); and collapsing
acceptable morphological variants into one preferred form.

## Two traps to respect

- **Low-frequency-category recall trap.** Under an aggressively conservative prompt,
  several low-frequency grammar categories (preposition, verb voice, conjunction)
  collapse to near-zero recall — the model, told to be cautious, abandons them. A
  strict minimal-edit pass therefore needs a separate, less-conservative check so real
  errors in these categories are not silently skipped.
- **Cross-family non-transfer.** A prompt optimised on one model family degraded
  another; heavy rule-lists do not port across model families. This matches our
  route-by-model-fit policy: give our Claude-lane reviewer Ukrainian-native minimal-edit
  instructions, not an over-tuned rule dump ported from another family.

## Reusable plumbing

Per-sentence correction as one validated call, with document markers passed through
verbatim and a strict-JSON schema constraining the output to a single corrected-sentence
field — deterministic and replayable. Useful for any sentence-level correction step.

## Adoption boundary (do not overclaim)

**Deferred.** The research is documented, but no dedicated stream-owned implementation
issue and no validated prompt/code consumer exist yet. A child issue under the
eval-harness stream epic #4913 must be created before adoption; #4913 is itself the
stream epic, not a child implementation issue for this work.
