# Executive Presentation: Ukrainian Hramatka Model Qualification Benchmark & Harness Elevation (July 2026)

> **Prepared for**: Lead Architecture Review & Presentation  
> **Evaluation Date**: July 23, 2026  
> **Benchmark Corpus**: Level-Playing-Field Lviv Rent Anchor (*«Як ми шукали квартиру у Львові»*, B1 45-minute lesson)  
> **Independent Cross-Family Judges**: Sol (`gpt-5.6-sol`) & Claude Opus (`claude-opus-4-8`)  
> **Live Web Dashboard**: [http://127.0.0.1:8892/index.html](http://127.0.0.1:8892/index.html)  
> **Architectural Record**: [ADR 012: Open Model Harness Elevation](file:///Users/krisztiankoos/projects/learn-ukrainian/docs/architecture/ADR_012_OPEN_MODEL_HARNESS_ELEVATION.md)

---

## Executive Summary & Strategic Position

To select the primary AI teacher models for the **Learn Ukrainian** curriculum platform, we conducted a fair, level-playing-field qualification benchmark (`zno-textbook-drill-v1`). Every candidate model was assigned the exact same B1 anchor text (*«Як ми шукали квартиру у Львові»*, ~350 words) and tasked with generating a complete 45-minute B1 Ukrainian lesson (6–8 distinct activities).

### **Key Findings & Release Policy**:
1. **Gemini 3.6 Flash & 3.1 Pro Are Ready**: Both models achieved **10/10** and **9.5/10 PASS** scores with zero Russianisms, deep B1 comparative degree pedagogy, and flawless native Ukrainian.
2. **Open Models (Gemma 4 31B) Need Harness Elevation Before Release**: Gemma 4 31B achieved 100% correct answer keys and zero Russianisms, but post-hoc prompt repairs (Tours 3 & 4) only patched surface issues. Open models require an upgraded **Harness V3** (with strict item density constraints and closed metalanguage vocabularies) to achieve 10/10 PASS natively. **Release is paused until Harness V3 is fully deployed.**
3. **Poolside Laguna S 2.1 Cannot Be Elevated**: Laguna S 2.1 suffered a catastrophic **3.5/10 FAIL**. Its pre-training weights contain severe Russian/Surzhyk contamination (*затем*, *перечисленого*, *незважно* presented as Ukrainian truth) and fake metalanguage (*«речник»* for noun). **Laguna S 2.1 is permanently rejected for language content generation.**

---

## Final Qualification Scorecard

| Model Seat | Provider / Route | Raw Score (Tour 2) | Elevated Score (Tour 3/4) | Final Release Status | Latency | Key Findings & Decolonization Profile |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| 🥇 **Gemini 3.6 Flash** | Google Agy | **10.0 / 10** | **10.0 / 10** | **APPROVED FOR RELEASE ✅** | **12s** | **#1 Production Champion**. Flawless native Ukrainian, zero Russianisms, deep B1 comparative morphology instruction (`дешевша`, `найдивніша`, `ніж`/`за`). |
| 🥈 **Gemini 3.1 Pro** | Google Agy | **9.0 / 10** | **9.5 / 10** | **APPROVED FOR RELEASE ✅** | **45s** | **High-Quality Deep Seat**. 100% Ukrainian immersion, 8/8 activities valid. 1-iteration repair fixed minor neuter agreement (`ближче`). |
| 🥉 **Gemma 4 31B** | OpenRouter | **8.0 / 10** | **8.2 / 10** | **HARNESS ELEVATION IN PROGRESS ⚙️** | **25s** | **Open Model Champion**. Zero Russianisms, 100% correct keys. Release paused pending Harness V3 density & metalanguage guardrails. |
| ❌ **Poolside Laguna S 2.1 (Fast)** | Poolside / Opencode | **3.5 / 10** | **3.5 / 10** | **PERMANENTLY REJECTED ❌** | **28s** | **Hard Fail**. Teaches Russianisms as *correct answer-key truth* (`затем`, `перечисленого`), invents fake terms (*«прибутковий сполучник»*), misnames parts of speech (*«речник»*). |

---

## Why Laguna S 2.1 Cannot Be Improved

Our analysis confirmed that Poolside Laguna S 2.1 cannot be elevated through prompt engineering:
- **Corrupted Pre-Training Weights**: Laguna was trained primarily on code and general web text. Its Ukrainian token representation is heavily contaminated with Russian syntax and Surzhyk.
- **Durable Error Generation**: It confidently asserts false grammatical claims (e.g. claiming locative *підлозі* is wrong, or claiming *в Києві* is ungrammatical) and invents non-existent terms (*«прибутковий сполучник»*).
- **Architectural Decision**: Do not waste compute or fine-tuning effort trying to fix Laguna's language weights. Document this finding for UNLP researchers.

---

## Action Plan for Harness Elevation (Gemma 4 31B)

To elevate Gemma 4 31B to 10/10 PASS natively without post-hoc repairs, we are implementing **Harness V3**:
1. **Activity Density Lock**: Enforce 8 distinct activity types with $\ge 5$ items per activity (preventing activity collapse).
2. **Metalanguage Guardrails**: Provide explicit closed lists of Ukrainian grammatical terms (`іменник`, `сполучник`, etc.) and prohibit Latin script in phonetic rules.
3. **Real B1 Morphosyntax Repair Schema**: Direct the `error-correction` module to test real B1 morphosyntax errors rather than text recall.
4. **Open Fine-Tuning Dataset**: Exported `hramatka-uk-pedagogy-v1` dataset at `data/datasets/hramatka_uk_pedagogy_v1/` for UNLP researchers to fine-tune open-weights models directly up to Gemini level.

---

*Report generated automatically from Hramatka Authoring Benchmark v2 test runs (July 23, 2026).*
