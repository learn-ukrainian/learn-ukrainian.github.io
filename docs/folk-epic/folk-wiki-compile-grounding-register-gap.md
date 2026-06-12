# Folk wiki compile — systemic grounding + register gap (Session 17 finding)

> **Status:** OPEN finding, shared compile-infra (orchestrator lane). Discovered 2026-06-12 while
> compiling the **first** folk wiki of the 6-wiki backlog (`bylyny-kyivskoho-tsyklu`). The bylyny wiki
> was **parked, not shipped** — its content/framing are strong (factual_accuracy 9–10, ukrainian_
> perspective 9), but it fails the compile `--review` gate on `source_grounding` AND `register`, and
> the root causes are **systemic to `scripts/wiki/compile.py` for folk/seminar wikis** — they will
> recur on every one of the 6 un-wikified folk dossiers, so the fix belongs in the compile pipeline,
> not in per-wiki hand-surgery.

## What happened (bylyny wiki, reproducible)
`compile.py --track folk --slug bylyny-kyivskoho-tsyklu --writer gpt-5.5 --review` →
`MIN 6.0/10`, failing `source_grounding` (codex 5→6). After I hand-added 3 sources + re-pointed 14
citations, a clean `--review-only` → `MIN 5.0/10`, failing **both** `register` (gemini, REJECT 5) and
`source_grounding` (codex, REVISE 6). Two distinct systemic causes:

### 1. Registry under-retrieval → forced over-citation → `source_grounding` fail
The compile's dense retrieval built a **6-source registry** that **omitted the scholarly chunks the
dossier explicitly grounds on**. It retrieved ЕУ `feaa5fa7_c0620` but missed:
- **ЕУ `feaa5fa7_c0619`** — the chunk that actually contains «дружинний епос… **не зберігся до наших
  днів на Україні**», the старини-North note, the genre-traces list (лірницька пісня про Іллю, дума про
  Олексія Поповича, Джурило в коломийках/весільних, Михайло й Золоті Ворота), and the XVI-c.
  documentary memory (Бельський/Гербіній/Рей/Лясота + Чижевський's дума-displacement).
- **Чижевський `wave4-chyzhevsky-istoriia-lit_c0163`** — the XVI–XVII documentary chain (Кміта 1574,
  Лясота 1594, Сарніцький 1585, Чоботок, XVII-c. travelers).
- **Попович `wave7-popovych-narys-kultury_c0176`** — the lost-variants anchor («ці твори безнадійно
  втрачені»).

Lacking `[S#]` anchors for these facts, the writer attached ~14 true, corpus-grounded claims to the
one broad source it *did* have (ЕУ c0620) → `source_grounding` correctly flagged the misattributions.
**All three omitted chunks are listed verbatim in the dossier's §4/§10 with chunk_ids.**

**Durable fix:** seed the wiki source registry from the dossier's already-cited chunk_ids (the dossier
§4/§10 list them). The grounding the reviewer demands is *already in the dossier* — the compile just
isn't carrying it forward into the registry.

### 2. Writer register tics + no quote-exemption → `register` fail (and review variance)
The `register` (gemini) dim went **PASS 10 → REJECT 5** across two runs on near-identical content
(reviewer variance), but the second pass is the more correct one — the flagged issues are **real and
pre-existing** in the writer's output:
- **`вербатимний`** (used ~5×) — an English import (`verbatim`); standard Ukrainian is **`дослівний`**.
  This is the **same writer coinage tic logged in Session 11** (вербатимний→дослівний). The folk
  MODULE writer rules already forbid it; the **wiki writer prompt does not**.
- **`приближенням`** (CRITICAL russianism) → `наближенням`; **`виступає`** copula calque → `постає/є`.
- **Verbatim-quote russianisms** — `акомпаньямент` (ЕУ's 1940s spelling), `в кругу` (Білецький via ЕУ):
  these are inside **attributed verbatim quotes**, where the register gate **should exempt them** —
  exactly the blockquote-exemption already shipped for the module vesum gate (**#2998**). The wiki
  `register` reviewer has no equivalent exemption, so it penalizes faithful historical quotation.

**Durable fix:** (a) port the folk/seminar register discipline (the `вербатимний→дослівний` class +
russianism list) into the **wiki** writer prompt, not only the module writer; (b) exempt attributed
verbatim `«…»`/blockquote spans from the wiki `register` russianism gate (mirror #2998); (c) note the
gemini `register`-dim variance (10→5) — a single pass is not reliable, consistent with prior handoff
notes on gemini reviewer variance.

## Why parked, not hand-fixed
The durable fix is a **re-compile** (seeded registry + register-hardened writer prompt), which would
**overwrite any prose hand-fix**. Hand-patching one wiki to green through stochastic codex/gemini gates
is low-leverage, non-durable, and the issues recur ×6. The dossier (#15, the session's primary
deliverable) shipped clean (PR #3033); this finding + fix-spec is the wiki deliverable.

## Recommended sequence (orchestrator / compile lane)
1. **Seed the wiki registry from dossier chunk_ids** (`compile.py` — folk/seminar path). Highest leverage.
2. **Port register discipline to the wiki writer prompt** (вербатимний→дослівний + russianism list).
3. **Exempt attributed verbatim quotes from the wiki `register` gate** (mirror module #2998).
4. Then **batch-recompile the 6 gap wikis**: bylyny-kyivskoho-tsyklu, kobzarstvo-lirnytstvo,
   dumy-sotsialno-pobutovi, holosinnya, vesilni-pisni, zhnyvarski-obzhynkovi-pisni.

Until (1)–(3) land, folk wikis require per-wiki hand-surgery to pass `--review`, which does not scale.
