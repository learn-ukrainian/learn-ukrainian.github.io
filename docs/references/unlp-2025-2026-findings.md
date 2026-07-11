# UNLP 2025 + 2026 — findings mapped to this project

> Read 2026-07-11 (atlas driver session, user-directed). Proceedings:
> [UNLP 2025](https://aclanthology.org/volumes/2025.unlp-1/) ·
> [UNLP 2026](https://aclanthology.org/volumes/2026.unlp-1/). UNLP 2026 was
> held in Lviv, 2026-05-29/30; the 2026 shared task was multi-domain document QA.

## Directly actionable for us

| Paper | Year | What it gives us | Lane / ticket |
| --- | --- | --- | --- |
| [Context-Aware Lexical Stress Prediction and Phonemization for Ukrainian TTS](https://aclanthology.org/2025.unlp-1.11/) (Senyk) | 2025 | Sentence-level stress prediction (homographs) + benchmark — the quality anchor for example-sentence audio; single-word audio drives off our own stress dictionary | TTS plan on #4696 |
| [Automated CEFR-Level Assignment for Ukrainian Texts](https://aclanthology.org/2026.unlp-1.18/) (Kanishcheva) | 2026 | Textbook-derived A1–B2 difficulty classifier; explicit-linguistic-feature RF (F1 .576) beats XLM-R and GPT-5.5 — deterministic features win | Candidate module-text difficulty gate; possible author outreach (our graded corpus is the same shape, ~10× scale) |
| [Gold-Standard Benchmark for Ukrainian Proficiency in LLMs](https://aclanthology.org/2026.unlp-1.12/) (Galeshchuk) | 2026 | Linguist-built grammar/orthography benchmark; LLM ceiling 59.6% — hard evidence for verify-against-VESUM doctrine; complementary axis to our tool-grounded factuality | #4913; also strengthens the outreach pitch (#4947) |
| [How Far Can Prompting Go for Minimal-Edit Ukrainian GEC?](https://aclanthology.org/2026.unlp-1.13/) (Karpo & Chernodub) | 2026 | Gemini 3.1-Pro F0.5=69.22 ≈ 90% of fine-tuned SOTA; **minimal-edit prompts IN UKRAINIAN beat English prompts** | Reviewer-as-fixer + russianism-gate prompts should be UA-language, minimal-edit framed |
| [ZNO-Vision: multimodal benchmark from ЗНО](https://aclanthology.org/2025.unlp-1.2/) (Paniv) | 2025 | 4,300+ expert exam questions, 12 disciplines + cultural-knowledge tests; most models below baseline | We already ingest zno_tasks (#4702); benchmark methodology relevant to #4913 |
| [Prompt-Based OCR for Old Ukrainian Texts](https://aclanthology.org/2026.unlp-1.7/) (Chaplynskyi) | 2026 | Opus 4.7 (max thinking) = 2.5% CER on 1605-06 manuscripts; released aligned dataset | Corpus-intake OCR recipe benchmark; released corpus = potential RUTH/ISTORIO heritage vein |
| [Mining Native Ukrainian Paraphrases](https://aclanthology.org/2026.unlp-1.17/) (Fesenko) | 2026 | News-mined native paraphrases > LLM-generated for lexical variation | Practice distractors / synonym legs (echoes our Ukrajinet #1657 finding) |
| [OmniGEC](https://aclanthology.org/2025.unlp-1.17/) (Kovalchuk) | 2025 | Silver multilingual GEC data incl. UK | Positioning reference for our teacher-edit-pairs contribution (gold, pedagogy-graded, calque-focused) — #4947 |
| [Kobza corpus + Modern-LiBERTa](https://aclanthology.org/2025.unlp-1.14/) (Haltiuk) | 2025 | ~60B-token UK corpus; first long-context (8k) UK encoder | Backend-phase candidates (retrieval/reranking); resource landscape |
| [UAlign](https://aclanthology.org/2025.unlp-1.4/) (Kravchenko) | 2025 | Public UA/EN parallel alignment benchmark (moral/ethical); UA-vs-EN alignment gap measured | #4913 adjacent; caution: sensitive content |
| [End-to-End Ukrainian RAG, local deployment](https://aclanthology.org/2026.unlp-1.19/) (Trokhymovych) | 2026 | Hybrid search + small fine-tuned UK model on constrained hardware, 2nd in shared task | Reference architecture for backend (#4920) |
| [SimIdioms](https://aclanthology.org/2026.unlp-1.5/) (Petruniv) | 2026 | UK idiom translation corpus/benchmark | Atlas idioms enrichment vein |

## Noted, lower priority
- [Vuyko Mistral: dialectal (Hutsul) translation](https://aclanthology.org/2025.unlp-1.10/) + [Hutsul ASR scaling](https://aclanthology.org/2026.unlp-1.16/) — dialect handling; heritage/register work someday.
- [Synonym-attack robustness](https://aclanthology.org/2025.unlp-1.15/) — distractor-quality caution.
- [UD treebank for parliamentary speech](https://aclanthology.org/2025.unlp-1.7/) — morphosyntax resource.
- 2025 shared task cluster (manipulation detection on Telegram), gender-bias/sentiment/NER papers, custom tokenizers, entropy, sign-language dataset, MT-metric validity studies, dictionary-based speculative decoding (Syvokon, 2026.unlp-1.15), disinfo narrative graphs — not on the critical path.

## No-shows worth knowing
- **No TTS engine papers in either year** — engine choice happens outside UNLP
  (StyleTTS2-ukrainian, robinhad/ukrainian-tts, Azure uk-UA; see #4696).
- No CEFR work in 2025; it appeared in 2026 (above).
