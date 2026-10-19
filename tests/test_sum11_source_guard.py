"""Keep Soviet-occupation СУМ-11 out of tracked verification inputs."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide, pytest.mark.reads_content]

ROOT = Path(__file__).resolve().parents[1]
SCOPES = (
    ":(glob)curriculum/**",
    ":(glob)scripts/data/**",
    ":(glob)scripts/build/phases/**",
    ":(glob)scripts/build/universal_rules/**",
    ":(glob)scripts/review/prompts/**",
    ":(glob)agents_extensions/shared/skills/**",
    ":(glob)agents_extensions/shared/rules/**",
    ":(glob)site/src/lib/lexicon/**",
    ":(glob)scripts/lexicon/**",
    ":(glob)scripts/projects/open_model_data/**",
    ":(exclude,glob)curriculum/**/_archive/**",
    ":(exclude)scripts/data/stress_overrides.yaml",  # Owned by the separate gloss-source branch.
)
# Exact approved lines: edits or new references require renewed review.
RULE_CONTEXT_LINES = {
    "scripts/review/prompts/lesson-review.md.j2": frozenset({
        "`search_definitions` (SUM-11) is available for Sovietization context only;",
    }),
    "scripts/review/prompts/lesson-rereview.md.j2": frozenset({
        "`search_definitions` (SUM-11) is available for Sovietization context only;",
    }),
    # Contrast-only caveat in the review-dimension prompt and its generated template.
    "scripts/build/phases/linear-review-dim.md": frozenset({
        "C. **Sovietization flag (decolonization, naturalness).** СУМ-11 is contrast-only and may appear",
    }),
    "scripts/build/phases/linear-review-dim.generated.md": frozenset({
        "- **C. Sovietization (decolonization, naturalness).** СУМ-11 is contrast-only:",
    }),
    # Tool identity, Sovietization audit, and contrastive context; no modern verification.
    "agents_extensions/shared/rules/mcp-sources-and-dictionaries.md": frozenset({
        "- `mcp__sources__search_definitions` — СУМ-11 (127K entries) — Soviet-era explanatory dictionary (1970–1980). **⚠️ NOT a verification authority for modern Ukrainian.** Used for detecting Soviet colonization artifacts (`sovietization_risk` 0/1/2, keywords) and surfacing contrastive Soviet occupation context. For modern meaning, use СУМ-20 / ВТС; for authentic historical Ukrainian, use Грінченко.",
        "## Historical Oppression & Decolonized Lexicography: Grinchenko vs СУМ-11 vs СУМ-20",
        "2. **СУМ-11 (1970–1980) — Soviet Totalitarian Occupation:**",
        "## Sovietization caveat & Soviet Colonization Context (СУМ-11) — issue #1659",
        "СУМ-11 (1970–1980) was published under Soviet occupation and late-Soviet ideological",
        "**Role of СУМ-11 in the project:**",
        "2. **Contrastive Colonization Context:** In Word Atlas / lexicon tools, СУМ-11 entries are surfaced explicitly as `soviet_colonization_context` (`Радянський окупаційний контекст`), showing learners how the Soviet regime distorted meanings, forced Russian calques, or added ideological baggage.",
        "3. **NEVER a Verification Authority:** Do NOT verify Ukrainian headwords, stress, or definitions with СУМ-11. Modern semantic verification belongs to **СУМ-20** (`sum20ua.com`, `newsum`) and **ВТС** (Великий тлумачний словник); historical authentic grounding belongs to **Грінченко** (1907); stress belongs to **ULIF** and СУМ-20.",
        "Every `search_definitions` result row carries:",
        "`.venv/bin/python scripts/audit/sum11_sovietization_scan.py --db data/sources.db`.",
        "Audit report at `audit/sum11_sovietization_scan_<DATE>.md`.",
        "| **СУМ-11** | 127K (7,152 flagged Sovietized — #1659) | Ukrainian explanatory (definitions, citations) | `data/sources.db` FTS5 |",
        "Source: [bakustarver/ukr-dictionaries-list-opensource](https://github.com/bakustarver/ukr-dictionaries-list-opensource) (СУМ-11, Балла, Фразеологічний)",
    }),
    # Always-loaded core: the contrast-only prohibition and the historical-dictionaries context line.
    "agents_extensions/shared/rules/core.md": frozenset({
        "- Use СУМ-11 (`search_definitions`) only for Sovietization detection and contrastive occupation context, never normative verification or proof of meaning, stress or existence. Preserve historical layers and surface СУМ-11 as `soviet_colonization_context` with `sovietization_risk`, `sovietization_keywords` and ideological markers, alongside modern standards and pre-Soviet witnesses. When `sovietization_risk > 0` or evaluating dictionary entries, never reproduce СУМ-11 definitions as modern standard Ukrainian; use modern authorities for definitions and Грінченко for pre-Soviet attestation. Missing modern meaning stays flagged unresolved, never an invented gloss. <!-- p5-soviet: U22 -->",
        "- Exclude by source and role, not date: Russian-language sources and the Soviet normative dictionary (P5) never set meaning, norm or stress; modern norms follow P5; historical layers stay, in context; approved Ukrainian authorities of any era bind. Preserve and contextualize historical dictionaries: Грінченко as authentic pre-Soviet attestation produced under imperial bans; СУМ-11 as Soviet occupation, censorship and Russification, displayed under `soviet_colonization_context` with risk and markers; СУМ-20/ВТС/ULIF as the contemporary standard. <!-- p9-sources: Q16 -->",
    }),
    # Prohibitions and contrast-only use.
    "agents_extensions/shared/rules/non-negotiable-rules.md": frozenset({
        "The project has VESUM (6.7M forms), СУМ-20, ВТС, Грінченко (67K), ЕСУМ, Monitor API, full code corpus, deterministic scripts. **Use them.** (СУМ-11 is strictly for Sovietization detection and contrastive colonization context — NEVER for modern Ukrainian verification).",
        "| Definitions / modern meaning | `query_sum20`, `search_slovnyk_me`, `search_grinchenko_1907`, `search_esum` (`search_definitions` is Soviet СУМ-11: use only for Soviet colonization analysis) |",
    }),
    # Prohibitions and contrastive context.
    "agents_extensions/shared/rules/ukrainian-linguistics.md": frozenset({
        "   - **`search_definitions` is СУМ-11, not an authority for modern Ukrainian.** СУМ-11 was compiled under Soviet occupation (1970–1980) and reflects late-Soviet censorship, ideological framing, and forced Russification. **We do NOT verify Ukrainian words, stress, or definitions with СУМ-11.** Its role is twofold:",
        "     2. **Surfacing contrastive Soviet occupation context:** in the Word Atlas / dictionary tools, СУМ-11 text is surfaced under `soviet_colonization_context` so learners can see how the Soviet regime distorted definitions or suppressed authentic Ukrainian senses, compared against modern standard (СУМ-20, ВТС, ULIF) and pre-Soviet witnesses (Грінченко). Never cite СУМ-11 as proof of standard Ukrainian.",
        "     2. **СУМ-11 (1970–1980):** compiled under **Soviet totalitarian occupation, censorship, and Russification**. We do not erase it; we surface it under `soviet_colonization_context` with its `sovietization_risk` and ideological markers to expose Soviet editorial interference, artificial archaisms, and forced Russian convergence.",
    }),
}
# Existing source inventories, historical contrast/audit checks, and rejected answers.
# Keep exact lines so changes and new verification uses remain subject to the guard.
OPEN_MODEL_CONTEXT_LINES = {
    'scripts/projects/open_model_data/audit_dataset_acceptance.py': frozenset({
        '"""Check 5: Epic Rules 3 & 4 (СУМ-11 distortion boundary, translation dictionaries, approved authorities)."""',
        '"max_sum11_negative_inferences": 0,',
        '"max_sum11_normative_violations": 0,',
        '"sum 11",',
        '"sum-11",',
        '"sum11",',
        '"sum11_negative_inferences": len(sum11_negative_inference_hits),',
        '"sum11_normative_violations": len(sum11_normative_hits),',
        '"zero_soviet_sum11",',
        '"сум 11",',
        '"сум-11",',
        '"сум11",',
        '# 2. Check for negative inference from СУМ-11 absence',
        '# A compound citation containing Soviet SUM-11 is never an approved modern authority',
        '# Check for СУМ-11 cited in metadata, authorities, or affirmative body text',
        '# If not contrastive, already captured in sum11_normative_hits above',
        '# In contrastive context, SUM-11 citation is valid only if an independent, modern approved authority is also present',
        '5. Source rules (Epic rules 3 & 4: Soviet СУМ-11 distortion rules, translation dictionaries, approved authorities)',
        'SOVIET_SUM11_ALIASES = [',
        'and not any(alias in a.lower() for alias in SOVIET_SUM11_ALIASES)',
        'auth_has_sum11 = any(alias in auth_lower for alias in SOVIET_SUM11_ALIASES)',
        'f"Condemning words based on СУМ-11 absence in {len(sum11_negative_inference_hits)} records (0 allowed)"',
        'f"Line {r.line_number}: claims word is wrong/rare because absent from СУМ-11"',
        'f"Line {r.line_number}: contrastive СУМ-11 citation lacks approved modern Ukrainian authority"',
        'failures.append(f"Citing СУМ-11 as normative source in {len(sum11_normative_hits)} records (0 allowed)")',
        'has_sum11_in_sources = any(any(alias in s for alias in SOVIET_SUM11_ALIASES) for s in all_sources_lower)',
        'if (has_sum11_in_sources or has_affirmative_citation) and not is_contrastive_context:',
        'if auth_has_sum11:',
        'if sum11_negative_inference_hits:',
        'if sum11_normative_hits:',
        'sum11_negative_inference_hits = []',
        'sum11_negative_inference_hits.append(',
        'sum11_normative_hits = []',
        'sum11_normative_hits.append(f"Line {r.line_number}: cites Soviet СУМ-11 as normative authority")',
    }),
    'scripts/projects/open_model_data/freeze_phase3_p1_universe.py': frozenset({
        '"lexical_sum11": "normative_lexical",',
    }),
    'scripts/projects/open_model_data/generate_grammar_signoff_8342.py': frozenset({
        '"soviet_sum11_violations": 0,',
        '"zero_soviet_sum11",',
        '"zero_soviet_sum11_influence": True,',
    }),
    'scripts/projects/open_model_data/holdings_manifest.py': frozenset({
        'id="sum11_contrast",',
        'origin="СУМ-11 digitisation (see register entry sum11)",',
        'register_id="sum11",',
        'selection="SELECT * FROM sum11 ORDER BY id",',
    }),
    'scripts/projects/open_model_data/inventory_existing_assets.py': frozenset({
        '("sum11", "СУМ-11", "human_authored_source", "sum11/chunks.jsonl"),',
    }),
    'scripts/projects/open_model_data/language_contact_detector.py': frozenset({
        '("sum11", "word", "СУМ-11"),',
    }),
    'scripts/projects/open_model_data/package_unified_dataset.py': frozenset({
        '| **Decolonization & Reasoning** | {domain_counts.get("decolonization", 0):,} | Deep anti-calque reasoning against Sovietized lexicography (СУМ-11). |',
    }),
    'scripts/projects/open_model_data/phase3_recovery_contracts.py': frozenset({
        '"lexical_sum11": 127069,',
    }),
    'scripts/projects/open_model_data/phase3_source_universe.py': frozenset({
        '"lexical_sum11": "sum11",',
    }),
    'scripts/projects/open_model_data/profiles/default.yaml': frozenset({
        'max_sum11_negative_inferences: 0',
        'max_sum11_normative_violations: 0',
    }),
    'scripts/projects/open_model_data/review_build/README.md': frozenset({
        '`modern`, `sum11`, `ua_gec`, `textbook`, `forbidden`). All citation triples must',
        'filenames. SUM-11 citations are refused as `sum11_role`; Russification contrast',
    }),
    'scripts/projects/open_model_data/review_build/roles.py': frozenset({
        'require(entry["role"] in {"modern", "sum11", "ua_gec", "textbook", "forbidden"}, "role_spec")',
        'require(spec["role"] != "sum11" and citation.source_id != "sum11", "sum11_role")',
    }),
    'scripts/projects/open_model_data/seeds_history.py': frozenset({
        '"2. Радянська інтервенція: введення слова «мисль» у СУМ-11 мало на меті виправдати російські кальки «образ мислей», «політ мислі».",',
        'historical_suppression_note="СУМ-11 визнав «галстук» літературним словом (піонерський галстук), витісняючи питоме «краватка».",',
        'historical_suppression_note="СУМ-11 висунув «трясовину» на перший план через максимальну схожість із російським словом.",',
        'historical_suppression_note="СУМ-11 подав «мисль» як рівноправний синонім до «думка», наводячи штучні цитати для підтвердження «спільного фонду».",',
        'historical_suppression_note="СУМ-11 подав «салфетка» поруч із «серветка», штучно створюючи видимість спільного кореня.",',
        'historical_suppression_note="СУМ-11 поставив «зонтик» на перше місце під російським тиском.",',
    }),
    'scripts/projects/open_model_data/seeds_participles.py': frozenset({
        'dpo_rejected="Форма «працюючий» цілком правильна, оскільки суфікс -юч- є слов\'янським і законно утворює дієприкметники в СУМ-11.",',
        'historical_suppression_note="СУМ-11 визнав «знаючий» літературним словом, витісняючи самобутні синоніми «тямущий» та «обізнаний».",',
        'historical_suppression_note="СУМ-11 визнав «пануючий» нормативним за рахунок пригнічення класичного «панівний».",',
        'historical_suppression_note="СУМ-11 визнав «хвилюючий» допустимим, нівелюючи витончені художні синоніми «зворушливий» та «бентежний».",',
        'historical_suppression_note="СУМ-11 фіксував «слідуючий» із позначкою «рідко», хоча в мові радянських установ воно панувало безроздільно.",',
    }),
    'scripts/projects/open_model_data/seeds_phraseology.py': frozenset({
        'historical_suppression_note="СУМ-11 визнав «бути правим» нормативним під тиском російської мови.",',
        'historical_suppression_note="СУМ-11 визнав «кидатися в очі» варіантом норми, копіюючи російську метафору.",',
        'historical_suppression_note="СУМ-11 калькував «задавати тон» для політичних статей.",',
    }),
    'scripts/projects/open_model_data/seeds_polysemy.py': frozenset({
        'dpo_rejected="Вислів «я рахую, що...» цілком допустимий у літературній мові, оскільки в СУМ-11 дієслово «рахувати» зафіксоване в значенні «мати якусь думку, міркувати».",',
        'dpo_rejected="Обидва слова рівноправні, бо в радянському словнику СУМ-11 «болільник» наведено без жодних обмежень.",',
        'dpo_rejected="Оскільки в СУМ-11 для слова «вірний» наведено значення «який відповідає дійсності; правильний», цей вислів є цілком законним.",',
        'historical_suppression_note="СУМ-11 дозволив слово «білет» для транспорту («автобусний білет»), руйнуючи традиційну українську терміносистему.",',
        'historical_suppression_note="СУМ-11 дозволив слово «розкривати» для книг і зошитів, дублюючи російське вживання за рахунок витіснення питомого «розгортати».",',
        'historical_suppression_note="СУМ-11 допускав слово «показник» у значенні дороговказу, змазуючи функціональну диференціацію суфіксів -ник і -чик.",',
        'historical_suppression_note="СУМ-11 допустив вживання «положення» для соціальних обставин під тиском канцеляризмів УРСР.",',
        'historical_suppression_note="СУМ-11 допустив дієслово «тушити» як синонім до «гасити», руйнуючи чітку кулінарну й фізичну межу.",',
        'historical_suppression_note="СУМ-11 зафіксував «получатися» як розмовне слово під прямим тиском російськомовного мовного середовища.",',
        'historical_suppression_note="СУМ-11 звів обидва дієслова до повної взаємозамінності, ігноруючи високий суспільно-політичний реєстр дієслова «обирати».",',
        'historical_suppression_note="СУМ-11 кодифікував «башня» як синонім до вежі, попри чужість цього фонетичного комплексу народній мові.",',
        'historical_suppression_note="СУМ-11 нівелював багатогранність слів «галузь» і «царина», копіюючи російське використання «області» у будь-яких абстрактних сполученнях.",',
        'historical_suppression_note="СУМ-11 нівелював різницю між словами «відносини», «стосунки» та «відношення», підганяючи їх під єдиний шаблон «отношения».",',
        'historical_suppression_note="СУМ-11 об\'єднав «відчиняти» й «відкривати» під одним широким значенням дієслова «відкривати», копіюючи російську лексичну структуру.",',
        'historical_suppression_note="СУМ-11 подав «мішати» у значенні «чинити перешкоди» як розмовне припустиме, орієнтуючись на російську семантичну структуру.",',
        'historical_suppression_note="СУМ-11 під впливом російського зразка додав до слова «білизна» перше значення «білий колір», створивши семантичний парадокс.",',
        'historical_suppression_note="СУМ-11 штучно поєднав значення лічби й судження під одним гаслом «рахувати», витісняючи питоме розмежування для наближення до російської полісемії.",',
    }),
    'scripts/projects/open_model_data/seeds_prepositions.py': frozenset({
        'historical_suppression_note="СУМ-11 визнав зворот «на протязі» часовим під тиском російської мови, породивши комічну двозначність про холодний вітер.",',
        'historical_suppression_note="СУМ-11 зафіксував вживання «завдяки» для небажаних наслідків, копіюючи російське розмовне змішування.",',
        'historical_suppression_note="СУМ-11 надав слову «біля» значення приблизної кількості, дублюючи функції російського прийменника «около».",',
    }),
    'scripts/projects/open_model_data/seeds_restitution.py': frozenset({
        'dpo_rejected="Слово «пилосос» є загальноприйнятим літературним словом, зафіксованим у радянському Словнику української мови (СУМ-11). Також як синоніми можна вживати «порохосмок» або «вакуум».",',
        'historical_suppression_note="СУМ-11 ввів покруч «розстрочка» під тиском радянської торговельної документації.",',
        'historical_suppression_note="СУМ-11 надав слову «переключати» статус основного технічного терміна під впливом російської номенклатури, витісняючи питоме «перемикати».",',
        'historical_suppression_note="СУМ-11 насаджував термін «накладна плата» / «накладений платіж», витісняючи стандартизоване в 1920-х роках слово «післяплата».",',
        'historical_suppression_note="СУМ-11 поставив «переписку» на перше місце за російським зразком.",',
        'historical_suppression_note="У 1930-х роках радянські термінологічні бюлетені та згодом СУМ-11 закріплювали спільні з російською мовою форми, витісняючи питомі українські аналоги 1920-х років.",',
    }),
    'scripts/projects/open_model_data/seeds_voice.py': frozenset({
        'historical_suppression_note="СУМ-11 допустив вживання дієслова «попередити» у значенні «унеможливити лихо», копіюючи російське «предупредить».",',
    }),
    'scripts/projects/open_model_data/v4_differential_soviet_miner.py': frozenset({
        '"""Adjudicate a single sum11 entry flagged with sovietization_risk > 0."""',
        '"FROM sum11 WHERE sovietization_risk > 0 ORDER BY id"',
        '"candidate_id": f"soviet.cand.{hashlib.sha256(f\'sum11:{entry.id}:{norm}\'.encode()).hexdigest()[:16]}",',
        '"sum11_id": entry.id,',
        '"sum11_risk_pool": {',
        '"total_entries": TOTAL_SUM11_RISK_POOL,',
        '# 5. Default Standard Living Ukrainian (Flagged only by incidental quote in СУМ-11)',
        '# Ingest from sources.db sum11',
        'Contrasts Soviet СУМ-11 entries flagged under `sovietization_risk > 0` against',
        'TOTAL_SUM11_RISK_POOL = 7152',
        'candidate = adjudicate_sum11_entry(',
        'class Sum11RiskEntry:',
        'def adjudicate_sum11_entry(',
        'entry = Sum11RiskEntry(',
        'entry: Sum11RiskEntry,',
        'parser = argparse.ArgumentParser(description="Mine and adjudicate differential Soviet candidates from СУМ-11.")',
        'print(f"Ingested {len(rows)} entries with sovietization_risk > 0 from sum11.")',
    }),
    'scripts/projects/open_model_data/v4_evaluate_decolonization.py': frozenset({
        '"сум-11",',
    }),
    'scripts/projects/open_model_data/v4_production_shards_assembly.py': frozenset({
        'f"2. Нормативний статус: Калькованість терміна не є перешкодою для його нормативного закріплення в СУМ-11.\\n"',
    }),
    'scripts/projects/open_model_data/v4_verify_trajectory_claims.py': frozenset({
        '"""Verify if a term falls into the alphabetical range of a СУМ-11 volume.',
        '"SELECT * FROM sum11 WHERE word = ? OR instr(\'|\' || word || \'|\', \'|\' || ? || \'|\') > 0 LIMIT 1",',
        '"SUM-11 cannot verify modern meaning or register, including mixed modern/Soviet citations",',
        '"SUM-11 only supports historical attestation and cannot certify modern meaning."),',
        '"SUM-11 presence and risk flags cannot verify a suppression narrative; independent evidence required",',
        '"claim_type": "SUM11_MODERN_EVIDENCE_REFUSED",',
        '"error": "Legacy SUM-11 claims are historical checks only; modern semantic evidence unresolved",',
        '"error": "SUM-11 outside soviet_colonization_context; modern semantic evidence unresolved",',
        '"source": "СУМ-11 (1970–1980)",',
        '"sum11_claims_verified": sum11_claims,',
        '# Check general СУМ-11 citations in step',
        '# Check СУМ-11 headword citation in suppression note',
        '# Check СУМ-11 stylistic label claims: e.g. ремарка «рідко», «заст.», «діал.»',
        '# Check СУМ-11 volume and year citations in reasoning steps',
        '# Check СУМ-11 volume and year citations: e.g. "СУМ-11 (т. 6, 1975)"',
        '# D.1 СУМ-11 Volume and Year verification',
        '# D.2 СУМ-11 Stylistic Label verification',
        '# D.3 СУМ-11 Sovietization / Codification Context verification',
        '2. СУМ-11 (data/sources.db): Soviet historical attestation only, never modern semantic evidence.',
        'ClaimType.SUM11_HEADWORD,',
        'ClaimType.SUM11_SOVIETIZATION,',
        'ClaimType.SUM11_STYLISTIC,',
        'ClaimType.SUM11_VOLUME_YEAR,',
        'SUM11_HEADWORD = "SUM11_HEADWORD"',
        'SUM11_SOVIETIZATION = "SUM11_SOVIETIZATION"',
        'SUM11_STYLISTIC = "SUM11_STYLISTIC"',
        'SUM11_VOLUMES: dict[int, dict[str, Any]] = {',
        'SUM11_VOLUME_YEAR = "SUM11_VOLUME_YEAR"',
        'claim, False, "Not in sum11", f"Cited term «{claim.term}» does not exist in sources.db sum11 table"',
        'claim, False, "Not in sum11", f"Term «{claim.term}» does not exist in sum11 table"',
        'claim_text=f"CoT step asserts stylistic label «{lbl}» in СУМ-11 for «{t_word}»",',
        'claim_text=f"CoT step cites СУМ-11 presence/treatment for «{term_c}»",',
        'claim_text=f"CoT step cites СУМ-11 vol. {vol_num}" + (f", year {year_num}" if year_num else ""),',
        'claim_text=f"Suppression note cites СУМ-11 presence for «{s_term}»",',
        'claim_text=f"Suppression note cites СУМ-11 vol. {vol_num}"',
        'claim_type=ClaimType.SUM11_HEADWORD,',
        'claim_type=ClaimType.SUM11_SOVIETIZATION,',
        'claim_type=ClaimType.SUM11_STYLISTIC,',
        'claim_type=ClaimType.SUM11_VOLUME_YEAR,',
        'def get_sum11_entry(self, word: str) -> dict[str, Any] | None:',
        'def is_term_in_sum11_volume(term: str, volume: int) -> bool:',
        'elif claim.claim_type == ClaimType.SUM11_HEADWORD:',
        'elif claim.claim_type == ClaimType.SUM11_SOVIETIZATION:',
        'elif claim.claim_type == ClaimType.SUM11_STYLISTIC:',
        'elif claim.claim_type == ClaimType.SUM11_VOLUME_YEAR:',
        'entry = self.get_sum11_entry(claim.term)',
        'f"Term «{term}» does not fall within alphabetical coverage of СУМ-11 volume {vol}",',
        'f"СУМ-11 entry for «{claim.term}» does not contain claimed stylistic label «{label}»",',
        'f"СУМ-11 has exactly 11 volumes, but volume {vol} was claimed",',
        'f"СУМ-11 volume {vol} was published in {vol_meta[\'year\']}, but trajectory claimed year {year}",',
        'if norm in self._sum11_cache:',
        'if not is_term_in_sum11_volume(term, vol):',
        'if not rejection_reasons and any(claim.claim_type.name.startswith("SUM11_") for claim in claims):',
        'if not t or volume not in SUM11_VOLUMES:',
        'if re.search(r"СУМ-11|СУМ\\s*\\(?1970–1980\\)?|Словник української мови в 11 томах", step):',
        'if vol not in SUM11_VOLUMES:',
        'reason.get("claim_type") == "SUM11_MODERN_EVIDENCE_REFUSED"',
        'return self._sum11_cache[norm]',
        'self._sum11_cache: dict[str, dict[str, Any] | None] = {}',
        'self._sum11_cache[norm] = None',
        'self._sum11_cache[norm] = res',
        'sum11_claims += 1',
        'sum11_claims = 0',
        'vol_meta = SUM11_VOLUMES[vol]',
    }),
    'scripts/projects/open_model_data/v5_build_dialect_historical_protection_suite.py': frozenset({
        '# All targets verified strictly clean of SUM-11 headwords, inflected lemmas, and defined subentries',
    }),
    'scripts/projects/open_model_data/v5_evaluation_harness.py': frozenset({
        '# 3c. Direct introductory attribution phrases: "За <Entities>," (e.g. "За СУМ-11, це правильно.")',
        '# 4b. Bare parenthetical citations: "(СУМ-11)", "(ВЕСУМ)", "(Словник української мови)", "(«СУМ-20»)", "(ВЕСУМ, p. 25; СУМ)"',
        "# Modern decolonized СУМ-20 only (Bilodid's Russian-Soviet occupation СУМ-11 permanently purged, Issue #8054).",
        "# Modern decolonized СУМ-20 only. Bilodid's Russian-Soviet occupation СУМ-11 (1970–1980)",
        "# Permanent Quarantine: Bilodid's Russian-Soviet occupation СУМ-11 (1970–1980)",
    }),
    'scripts/projects/open_model_data/v5_mine_dialect_corpus.py': frozenset({
        '"""Mine attributed passages; SUM-11 labels describe historical editorial treatment only."""',
        '"Historical quotation preservation only. SUM-11 editorial labels do not establish "',
        '"do not use their definitions or labels to produce modern answers. SUM-11 SFT candidates are withheld."),',
        '"source": "СУМ-11 (1970–1980)",',
        '# 1. Mine sum11 literature citations tagged "діал." (classic Ukrainian literature only)',
        '# B. Standardize Arabic numeral volume fields in SUM-11 format: ", 1, 1955" -> ", I, 1955"',
        'SELECT * FROM sum11',
        'description=("Mine dialect candidates and evaluate preservation. SUM-11 quotations are historical contrast; "',
        'source_db="sum11_literary_citation",',
    }),
    'scripts/projects/open_model_data/verify_phase3_source_universe_freeze.py': frozenset({
        '"lexical_sum11",',
    }),
}
RULE_CONTEXT_LINES.update(OPEN_MODEL_CONTEXT_LINES)

# Normalize to stripped lines: exemptions match regardless of leading/trailing whitespace,
# same as the raw lines git grep reports.
RULE_CONTEXT_LINES = {
    path: frozenset(line.strip() for line in lines) for path, lines in RULE_CONTEXT_LINES.items()
}

# Exact reviewed lines in scripts/lexicon: occupation contrast and exclusion only.
LEXICON_CONTEXT_LINES = {
    'scripts/lexicon/audit_sum11_relations.py': frozenset({
        '"""Reproduce the read-only #8990 stored СУМ-11 relation and source audit."""',
        'if not isinstance(section, dict) or "СУМ-11" not in json.dumps(section, ensure_ascii=False):',
        'matches = [source for source in source_list if isinstance(source, str) and "СУМ-11" in source]',
        '_write_tsv(out_dir / "sum11-held-relations.tsv", held)',
        '_write_tsv(out_dir / "sum11-confirmed-relations.tsv", confirmed)',
        'with (out_dir / "sum11-held-sources.tsv").open("w", encoding="utf-8", newline="") as stream:',
        'parser.add_argument("--audit-doc", type=Path, default=ROOT / "docs" / "lexicon" / "sum11-reference-audit.md")',
    }),
    'scripts/lexicon/admit_fmu_boosters.py': frozenset({
        'and zero Soviet СУМ-11 usage.',
    }),
    'scripts/lexicon/admit_textbook_book_glossary.py': frozenset({
        '"(СУМ-20/ВТС, never СУМ-11) + learner English gloss (dmklinger UK->EN, "',
        'never СУМ-11 (docs/runbooks/word-atlas-entry-model.md, #7453);',
    }),
    'scripts/lexicon/census_atlas_6371_textbook_leftover.py': frozenset({
        '"Oneshot approved glosses are SUM-11 Ukrainian dumps. They are **not**",',
        '"from a committed inventory. Refuse invented lemmas, oneshot SUM-11 "',
        'rows carry SUM-11 Ukrainian dumps and therefore stay residual unless a',
    }),
    'scripts/lexicon/curated_ohoiko_ulp_repromote.py': frozenset({
        'from СУМ-20 and Великий тлумачний словник (ВТС) — СУМ-11 (Soviet-era) is',
        'never to СУМ-11 — matching the public ``_definition_cards`` source order',
        'СУМ-11 (Soviet-era) is banned on Atlas, including as inventory gloss fill',
    }),
    'scripts/lexicon/curated_textbook_jsonl_repromote.py': frozenset({
        '# СУМ-11 bulk-SQL gloss fill, so this filter now runs before the gloss fetch',
        'never to СУМ-11 — matching the public ``_definition_cards`` source order',
        'СУМ-11 (Soviet-era) is banned on Atlas, including as inventory gloss fill',
        'СУМ-20/ВТС gloss). СУМ-11 (Soviet-era) is banned, including as gloss fill',
    }),
    'scripts/lexicon/enrich_manifest.py': frozenset({
        'raise ValueError(f"newly enriched entry {lemma!r} has an unflagged СУМ-11 citation: {violation}")',
        '# СУМ-11 (Soviet-era dictionary) is intentionally excluded — decolonization',
        '(СУМ-11, the Soviet-era dictionary, is excluded — decolonization decision',
        'already-excluded Soviet-era СУМ-11, which is at least Ukrainian-language. This',
        'СУМ-11 (the Soviet-era dictionary, 1970-80) is intentionally NEVER used as a',
        'СУМ-11 source (decolonization decision 2026-06-26). For inflected-form entries it',
    }),
    'scripts/lexicon/heritage_classifier.py': frozenset({
        '"SELECT MAX(sovietization_risk) FROM sum11 WHERE lower(word) = ?",',
        '"SELECT definition, text FROM sum11 WHERE lower(word) = ? LIMIT 3",',
        '_sum11_sovietization_risk(',
        'cols = {row[1] for row in conn.execute("PRAGMA table_info(sum11);").fetchall()}',
        'def _source_sum11_has_flag_columns(db_path: str | Path | None = None) -> bool:',
        'def _sum11_has_flag_columns(conn: SQLiteConnection) -> bool:',
        'def _sum11_has_flag_columns_for_db(',
        'def _sum11_sovietization_risk(definition: str, text: str) -> int:',
        'def _sum11_sovietization_risk_for_term(',
        'from scripts.audit.sum11_sovietization_scan import classify_entry',
        'has_flag_columns = _source_sum11_has_flag_columns(db_path)',
        'return _sum11_has_flag_columns(conn)',
        'return _sum11_has_flag_columns_for_db(',
        'sovietization_risk = _sum11_sovietization_risk_for_term(term, db_path=db_path)',
    }),
    'scripts/lexicon/load_relation_candidates.py': frozenset({
        'Soviet-era СУМ-11 is never headword evidence (rule #M-6). No prefix or body',
    }),
    'scripts/lexicon/migrate_sum11_sovietization.py': frozenset({
        '"""Apply missing ``sum11`` sovietization schema pieces.',
        '"""Idempotently add and populate СУМ-11 Sovietization flags.',
        '"ALTER TABLE sum11 "',
        '"Add sum11.sovietization_* columns if needed and populate them "',
        '"CREATE INDEX IF NOT EXISTS idx_sum11_sovietization "',
        '"ON sum11(sovietization_risk) WHERE sovietization_risk > 0",',
        '"ensure idx_sum11_sovietization",',
        '"using scripts/audit/sum11_sovietization_scan.py logic."',
        '.venv/bin/python scripts/lexicon/migrate_sum11_sovietization.py --db data/sources.db',
        '``scripts.audit.sum11_sovietization_scan.classify_entry`` through the scan',
        'actions = ensure_sum11_sovietization_columns(conn, dry_run=args.dry_run)',
        'cols = _sum11_columns(conn)',
        'def _sum11_columns(conn: sqlite3.Connection) -> set[str]:',
        'def ensure_sum11_sovietization_columns(',
        'from scripts.audit.sum11_sovietization_scan import scan_and_update, write_audit_report',
        'it applies the ``sum11`` flag columns when absent, then reuses',
        'raise sqlite3.OperationalError("missing required table: sum11")',
        'rows = conn.execute("PRAGMA table_info(sum11);").fetchall()',
    }),
    'scripts/lexicon/ohoiko_paired_headword_split.py': frozenset({
        '# instead of inventing or СУМ-11 gloss-filling (#7458).',
        'СУМ-11 (Soviet-era) is banned, including as gloss fill (#7453, operator',
    }),
    'scripts/lexicon/promote_grow_candidates.py': frozenset({
        '"approved_gloss.text looks like a СУМ-11 stub (дієпр / див. / те саме, що) and is not learner English"',
        '# distinguish СУМ-11 cross-ref rows from other Cyrillic definitions.',
        '# СУМ-11 cross-ref / participle stubs are never learner-English anchors (#5411).',
        '2. СУМ-11 stub shapes (``дієпр`` / ``див.`` / ``те саме, що``) with no Latin',
        'Fail-closed for #5411: refuses Cyrillic/non-English anchors, СУМ-11 stubs,',
        '_SUM11_STUB_MARKER_RE = re.compile(',
        'if latin_n == 0 and _SUM11_STUB_MARKER_RE.search(text):',
        'if reason == "sum11_stub_gloss":',
        'return "sum11_stub_gloss"',
    }),
    'scripts/lexicon/source_attribution.py': frozenset({
        '# Soviet-era СУМ-11 is contrast-only (rule #M-6): published evidence citing it is',
        'raise ValueError(f"cannot count withheld СУМ-11 citations in {name}")',
        'raise ValueError("cannot compute a safe СУМ-11 citation withholding projection")',
    }),
    'scripts/lexicon/thin_page_report.py': frozenset({
        '``sum11`` is excluded (rendered pages drop SUM-11 definition cards) and',
        'exempts form stubs, excludes SUM-11 definition cards, and applies a special',
    }),
    'scripts/lexicon/triage_needs_review.py': frozenset({
        '# Soviet-era СУМ-11 is never a gloss or hit source (rule #M-6).',
    }),
}
RULE_CONTEXT_LINES.update(LEXICON_CONTEXT_LINES)

# These UI modules display and quarantine historical evidence rather than verify it.
CONTEXT_ONLY_FILES = {
    "site/src/lib/lexicon/heritage-severity.ts": "Historical warning labels and context only.",
    "site/src/lib/lexicon/word-atlas-article-model.ts": "Routes SUM-11 cards to Soviet context, excluding modern definitions.",
}

# Tracked temporary exceptions; issue #8964 will re-source and remove both.
TEMPORARY_EXCEPTIONS = {
    "site/src/lib/lexicon/curated-heteronyms.ts": "#8964: re-source the generated heteronym dataset.",
    "scripts/lexicon/enrich_heteronyms.py": "#8964: replace SUM-11 heteronym enrichment inputs.",
    "scripts/lexicon/sum20_lookup.py": "#8964: replace SUM-11 contrast lookup inputs.",
    **{
        f"scripts/lexicon/curated_heteronyms_batch{suffix}.py": "#8964: re-source curated heteronym inputs."
        for suffix in ("", *(str(n) for n in range(2, 14)))
    },
}


def _is_exempt(path: str, source_line: str) -> bool:
    """True if a matched line is an approved contrast-only/context reference.

    Matching is exact-line (after stripping surrounding whitespace), never substring:
    a line that reuses approved wording plus an added verification citation must NOT
    be exempt.
    """
    if path in CONTEXT_ONLY_FILES or path in TEMPORARY_EXCEPTIONS:
        return True
    return source_line.strip() in RULE_CONTEXT_LINES.get(path, frozenset())


def _source_references(revision: str | None = None, *, root: Path = ROOT) -> list[str]:
    cmd = [
        "git", "grep", "-n", "-I", "-i", "-E",
        "-e", r"(СУМ|SUM)[-‐‑‒–— ]?11|search_definitions",
    ]
    if revision:
        cmd.append(revision)
    cmd.extend(("--", *SCOPES))
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode in (0, 1), result.stderr
    references = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 3 if revision else 2)
        path = parts[1] if revision else parts[0]
        source_line = parts[-1]
        if _is_exempt(path, source_line):
            continue
        references.append(line)
    return references


def test_sum11_is_not_a_tracked_verification_source() -> None:
    revision = os.environ.get("SUM11_GUARD_REV") or None
    references = _source_references(revision)
    assert not references, "СУМ-11 is contrast-only; remove verification inputs:\n" + "\n".join(references)


def test_temporary_exceptions_are_limited_to_issue_8964() -> None:
    assert set(TEMPORARY_EXCEPTIONS) == {
        "site/src/lib/lexicon/curated-heteronyms.ts",
        "scripts/lexicon/enrich_heteronyms.py",
        "scripts/lexicon/sum20_lookup.py",
        "scripts/lexicon/curated_heteronyms_batch.py",
        "scripts/lexicon/curated_heteronyms_batch2.py",
        "scripts/lexicon/curated_heteronyms_batch3.py",
        "scripts/lexicon/curated_heteronyms_batch4.py",
        "scripts/lexicon/curated_heteronyms_batch5.py",
        "scripts/lexicon/curated_heteronyms_batch6.py",
        "scripts/lexicon/curated_heteronyms_batch7.py",
        "scripts/lexicon/curated_heteronyms_batch8.py",
        "scripts/lexicon/curated_heteronyms_batch9.py",
        "scripts/lexicon/curated_heteronyms_batch10.py",
        "scripts/lexicon/curated_heteronyms_batch11.py",
        "scripts/lexicon/curated_heteronyms_batch12.py",
        "scripts/lexicon/curated_heteronyms_batch13.py",
    }
    assert all("#8964" in reason for reason in TEMPORARY_EXCEPTIONS.values())
    tracked = subprocess.run(
        ["git", "ls-files", "--", *TEMPORARY_EXCEPTIONS], cwd=ROOT,
        capture_output=True, text=True, check=True, timeout=30,
    ).stdout.splitlines()
    assert set(tracked) == set(TEMPORARY_EXCEPTIONS)


def test_approved_contrast_only_line_is_exempt() -> None:
    path = "scripts/build/phases/linear-review-dim.generated.md"
    approved = next(iter(RULE_CONTEXT_LINES[path]))
    assert _is_exempt(path, approved)


def test_approved_line_with_added_verification_citation_is_reported() -> None:
    """A line reusing approved contrast-only wording plus a smuggled-in verification
    citation must fail the guard — exact-line matching, not substring."""
    path = "scripts/build/phases/linear-review-dim.generated.md"
    approved = next(iter(RULE_CONTEXT_LINES[path]))
    smuggled = approved + " cite СУМ-11 to verify modern word meaning"
    assert not _is_exempt(path, smuggled)


def test_changing_an_approved_line_fails_the_guard() -> None:
    path = "scripts/build/phases/linear-review-dim.md"
    approved = next(iter(RULE_CONTEXT_LINES[path]))
    altered = approved.replace("contrast-only", "contrast-only, mostly")
    assert not _is_exempt(path, altered)


def test_approved_line_matches_regardless_of_surrounding_whitespace() -> None:
    path = "scripts/build/phases/linear-review-dim.md"
    approved = next(iter(RULE_CONTEXT_LINES[path]))
    assert _is_exempt(path, "  " + approved + "  ")


def test_new_lexicon_verification_use_fails_scanner(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    lexicon = tmp_path / "scripts" / "lexicon"
    lexicon.mkdir(parents=True)
    for name in ("new_verifier.py", "x_heteronym_verify.py"):
        (lexicon / name).write_text("definition = search_definitions(word)\n", encoding="utf-8")
    subprocess.run(["git", "add", "scripts/lexicon"], cwd=tmp_path, check=True, timeout=30)
    references = _source_references(root=tmp_path)
    assert len(references) == 2
    assert {line.split(":", 1)[0] for line in references} == {
        "scripts/lexicon/new_verifier.py", "scripts/lexicon/x_heteronym_verify.py"
    }


@pytest.mark.parametrize("name", ["new_verifier.py", "v4_decolonization_reasoning.py"])
def test_new_open_model_verification_use_fails_scanner(tmp_path: Path, name: str) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    project = tmp_path / "scripts" / "projects" / "open_model_data"
    project.mkdir(parents=True)
    (project / name).write_text("definition = search_definitions(word)\n", encoding="utf-8")
    subprocess.run(["git", "add", "scripts/projects/open_model_data"], cwd=tmp_path, check=True, timeout=30)
    assert _source_references(root=tmp_path) == [
        f"scripts/projects/open_model_data/{name}:1:definition = search_definitions(word)"
    ]
