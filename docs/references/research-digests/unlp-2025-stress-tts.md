# Context-Aware Lexical Stress Prediction and Phonemization for Ukrainian TTS

Source: Senyk, Paniv, Lukianchuk & Robeiko, UNLP 2025 — https://aclanthology.org/2025.unlp-1.11/

Compact per-record digest for research-registry id `unlp-2025-stress-tts`.
Paraphrase and pointers only; no paper tables, figures, or verbatim passages are
reproduced here. Read the full source at the link above.

## Finding

The paper releases the first public sentence-level lexical-stress benchmark for
Ukrainian (about a thousand hand-annotated sentences, several thousand unique word
forms, and a substantial share of stress-ambiguous and out-of-vocabulary words) and
studies two ways to place stress in context: a byte-level neural grapheme-to-phoneme
model trained on synthetically stress-labelled text, and a dictionary tool that
disambiguates heteronyms using part-of-speech and grammatical features of the retrieved
word forms.

The result that matters for us is that on the ambiguous-word slice the dictionary +
POS method is the stronger performer, while the best sentence-level stress accuracy
comes from a hybrid that combines the neural model with the dictionary as a fallback.
In other words, the neural model does not win on heteronyms; a dictionary-plus-context
path (which we already have via our stress dictionary) is the right backbone, with a
model used only for out-of-vocabulary forms.

The paper also releases a rule-based phonemizer: an ordered regex pipeline emitting an
IPA inventory of just over fifty phonemes, reporting low word error rates on clean
input against a naive letter-to-phoneme baseline. It cleanly separates stress placement
from phonemization, which matches our need to mark stress first and phonemize second.

## Reported limitations (carry forward)

- The phonemizer operates strictly at the word level and does **not** handle
  abbreviations or numerical expressions — our sentence audio must pre-expand numbers
  and abbreviations before phonemizing.
- Neither pipeline accounts for non-standard varieties such as regional dialects.
- Ambiguous-word performance is limited by sparse coverage in automatically labelled
  training data; heteronym coverage is the authors' own stated future direction.

## Adoption boundary (do not overclaim)

Retained as a **quality benchmark and method reference only**. Integration is
**deferred**: it is blocked by the user-gated #4696 engine-versus-recorded-audio
decision, and the upstream repository's license must be verified before any code or
data reuse — the paper body states public availability but prints no license string,
so reuse is not yet cleared.
