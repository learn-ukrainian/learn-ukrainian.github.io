# UNLP 2025 + 2026 — findings mapped to this project

> Read 2026-07-11 (atlas driver session, user-directed). Proceedings:
> [UNLP 2025](https://aclanthology.org/volumes/2025.unlp-1/) ·
> [UNLP 2026](https://aclanthology.org/volumes/2026.unlp-1/). UNLP 2026 was
> held in Lviv, 2026-05-29/30; the 2026 shared task was multi-domain document QA.

## Directly actionable for us

| Paper | Year | Finding | Accountable owner | Adoption action | Status |
| --- | --- | --- | --- | --- | --- |
| [Context-Aware Lexical Stress Prediction and Phonemization for Ukrainian TTS](https://aclanthology.org/2025.unlp-1.11/) (Senyk) | 2025 | Sentence-level stress prediction (homographs) + benchmark — the quality anchor for example-sentence audio; single-word audio drives off our own stress dictionary. | Atlas/practice #4700 under #4387 | Adopted as a quality benchmark only. | Deferred until the user-gated #4696 engine/recorded-audio decision. |
| [Automated CEFR-Level Assignment for Ukrainian Texts](https://aclanthology.org/2026.unlp-1.18/) (Kanishcheva) | 2026 | Textbook-derived A1–B2 difficulty classifier; explicit-linguistic-feature RF (F1 .576) beats XLM-R and GPT-5.5 — deterministic features win. | core-quality #4274; implementation #4952 | Phase 1 deterministic, interpretable, advisory feature extraction. | Active in #4952; calibration and gating deferred. |
| [Gold-Standard Benchmark for Ukrainian Proficiency in LLMs](https://aclanthology.org/2026.unlp-1.12/) (Galeshchuk) | 2026 | Linguist-built grammar/orthography benchmark; LLM ceiling 59.6% — hard evidence for verify-against-VESUM doctrine; complementary axis to our tool-grounded factuality. | eval-harness #4913 | Adopted as evidence for grammar/orthography evaluation and VESUM verification. | Queued within existing #4913 scope. |
| [How Far Can Prompting Go for Minimal-Edit Ukrainian GEC?](https://aclanthology.org/2026.unlp-1.13/) (Karpo & Chernodub) | 2026 | Gemini 3.1-Pro F0.5=69.22 ≈ 90% of fine-tuned SOTA; **minimal-edit prompts IN UKRAINIAN beat English prompts**. | eval-harness #4913 | Adopted as a Ukrainian-language, minimal-edit prompt-design constraint for a later reviewer/fixer change. | Not implemented here. |
| [ZNO-Vision: multimodal benchmark from ЗНО](https://aclanthology.org/2025.unlp-1.2/) (Paniv) | 2025 | 4,300+ expert exam questions, 12 disciplines + cultural-knowledge tests; most models below baseline. | corpus-channels #4706; issue #4702 | Adoption is active through the licensed task-intake plan. | Active through #4702. |
| [Prompt-Based OCR for Old Ukrainian Texts](https://aclanthology.org/2026.unlp-1.7/) (Chaplynskyi) | 2026 | Opus 4.7 (max thinking) = 2.5% CER on 1605-06 manuscripts; released aligned dataset. | corpus-channels #4706 | Reference candidate only. | Deferred pending a scoped, provenance/licensing-reviewed heritage intake need. |
| [Mining Native Ukrainian Paraphrases](https://aclanthology.org/2026.unlp-1.17/) (Fesenko) | 2026 | News-mined native paraphrases > LLM-generated for lexical variation. | Atlas/practice #4387 | Prefer verified native Ukrainian pairs over LLM generation when rights permit. | Deferred until a scoped source intake. |
| [OmniGEC](https://aclanthology.org/2025.unlp-1.17/) (Kovalchuk) | 2025 | Silver multilingual GEC data incl. Ukrainian. | eval-harness #4913 | Positioning/reference only. | Deferred pending a separately scoped, user-approved contribution/outreach issue. |
| [Kobza corpus + Modern-LiBERTa](https://aclanthology.org/2025.unlp-1.14/) (Haltiuk) | 2025 | ~60B-token Ukrainian corpus; first long-context (8k) Ukrainian encoder. | backend #4920 under #4387 | Architecture/reference candidate only. | Deferred to backend design. |
| [UAlign](https://aclanthology.org/2025.unlp-1.4/) (Kravchenko) | 2025 | Public UA/EN parallel alignment benchmark (moral/ethical); UA-vs-EN alignment gap measured. | eval-harness #4913 | Not adopted for current corpus use; retained as an evaluation-adjacency reference. | Deferred after sensitive-content and fit review. |
| [End-to-End Ukrainian RAG, local deployment](https://aclanthology.org/2026.unlp-1.19/) (Trokhymovych) | 2026 | Hybrid search + small fine-tuned Ukrainian model on constrained hardware, 2nd in shared task. | backend #4920 | Reference architecture candidate. | Deferred to backend design. |
| [SimIdioms](https://aclanthology.org/2026.unlp-1.5/) (Petruniv) | 2026 | Ukrainian idiom translation corpus/benchmark. | Atlas/practice #4387 | Potential idiom enrichment. | Deferred pending dataset licensing/provenance and a dedicated scope. |

## Noted, lower priority

This section is reference-only and makes no adoption or implementation commitment in the current scope.

- [Vuyko Mistral: dialectal (Hutsul) translation](https://aclanthology.org/2025.unlp-1.10/) + [Hutsul ASR scaling](https://aclanthology.org/2026.unlp-1.16/) — dialect handling; possible future heritage/register research.
- [Synonym-attack robustness](https://aclanthology.org/2025.unlp-1.15/) — distractor-quality caution.
- [UD treebank for parliamentary speech](https://aclanthology.org/2025.unlp-1.7/) — morphosyntax resource.
- 2025 shared task cluster (manipulation detection on Telegram), gender-bias/sentiment/NER papers, custom tokenizers, entropy, sign-language dataset, MT-metric validity studies, dictionary-based speculative decoding (Syvokon, 2026.unlp-1.15), disinfo narrative graphs — not on the critical path.

## No-shows worth knowing
- **No TTS engine papers in either year** — engine choice happens outside UNLP
  (StyleTTS2-ukrainian, robinhad/ukrainian-tts, Azure uk-UA; see #4696).
- No CEFR work in 2025; it appeared in 2026 (above).
