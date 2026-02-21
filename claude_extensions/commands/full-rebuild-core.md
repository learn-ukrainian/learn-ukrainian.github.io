# Atomic Core Rebuild Workflow (v2.4)

> **Objective:** Hit Scholar-level word counts (3000-6000) while preventing CLI context crashes.
> **Philosophy:** Atomic turns. Shared state on disk. Resumable execution.

## 🚀 Usage

```
/full-rebuild-core {level} {num} --turn=[1|2|3a|3b|3.1|3.5|4|5]
/full-rebuild-core {level} {num} --from=[TURN]
```

## 📋 Turns & State Detection

The system detects completed turns by checking files on disk. 

| Turn | Name | Artifact | Logic |
|---|---|---|---|
| **1** | **Research** | `research/{slug}.md` | **Blocking.** Finds 3+ cultural anchors and State Standard refs. |
| **2** | **Meta** | `meta/{slug}.yaml` | Establish H2 structure. Set approximate word counts. |
| **3a** | **Hydration P1** | `{slug}.md` | Write first 50% of narrative (~2500 words). **STOP.** |
| **3b** | **Hydration P2** | `{slug}.md` | Write remaining 50% + # Підсумок. Total target: 1.5x Floor. |
| **3.1** | **Polish** | `{slug}.md` | **Linguistic pass.** Fix gender, cases, and robotic filler. |
| **3.5** | **Sync** | `meta/{slug}.yaml` | **Technical Alignment.** Run `sync_meta_outline.py`. |
| **4** | **YAML** | `activities/` + `vocab/` | Generate sidecars based *only* on the new narrative. |
| **5** | **Review** | `review/{slug}.md` | Final Quality Gate using `review-content-v4`. |

---

## 🛠 Stability & Rigor (Armor)

1. **Clean Slate Mandate**: IGNORE existing content in `.md` files. Always build fresh from the plan to ensure narrative flow.
2. **Model Enforcement**: 
   - Core A/B: gemini-3-flash-preview.
   - Scholar (B2+): gemini-3-pro-preview.
3. **Typography**: ALWAYS use angular quotes «...». Never straight quotes.
4. **Fact Allocation**: Every unique fact/quote must appear in exactly ONE H2 section.

## 🏁 Success Criteria
- **Naturalness:** 10/10.
- **Richness:** 95%+.
- **Audit:** Clean PASS.
