# Literary Ukrainian (Poltava Standard) Fine-Tuning Dataset (`hramatka_literary_poltava_v1`)

> **Target Audience**: UNLP Researchers, Gemma/Llama Fine-Tuners, and Ukrainian NLP Engineers.  
> **Purpose**: Fine-tuning open-weights models (Gemma 4 31B, Llama 4, Mistral) on authentic, chronologically tagged Ukrainian literary prose (Poltava-Kyiv standard) to eliminate Soviet/Russianized calques and achieve native phonoaesthetic euphony (*милозвучність*).

---

## Why Open Web Crawls Fail for Ukrainian

Standard open LLMs (like Gemma or Llama) are trained on generic web crawls (Common Crawl, Wikipedia, news sites). In Ukrainian, generic web crawls are polluted with:
1. **Soviet Bureaucratic Calques (*канцеляризми*)**: Rigid, non-native phrasing translated literally from Russian.
2. **Semantic Surzhyk**: Valid Ukrainian words assigned Russian meanings.
3. **Phonoaesthetic Violations**: Disregarding Ukrainian euphony rules (*милозвучність*, alternation of *у/в*, *і/й*).

---

## Dataset Overview

Modern Literary Ukrainian (*сучасна українська літературна мова*) was historically synthesized from the **Poltava-Middle Dnieper dialect region** (Kotlyarevsky, Shevchenko, Nechuy-Levytsky, Franko, Lesya Ukrainka).

This dataset contains **curated, clean, chronologically tagged passages** extracted directly from our 137,700-chunk literary database (`data/sources.db`), spanning:
- **Classic 19th Century Literature** (Kotlyarevsky, Shevchenko, Nechuy-Levytsky, Marko Vovchok)
- **Modern 20th Century & Contemporary Ukrainian** (Rylsky, Tychyna, Kostenko, Stus)
- **Ukrainian School Textbooks** (Grades 1–11, 2019 Pravopys)

---

## Fine-Tuning Recipe for Gemma 4 31B

1. **Continued Pre-Training / SFT**: Train Gemma 4 31B on `hramatka_literary_poltava_v1.jsonl` using causal language modeling (CLM) with low rank adaptation (LoRA / QLoRA).
2. **Result**: Aligns Gemma's token probabilities to authentic Poltava-Kyiv literary syntax and native Ukrainian euphony (*милозвучність*).

---

*Dataset exported from the Learn Ukrainian Project repository.*
