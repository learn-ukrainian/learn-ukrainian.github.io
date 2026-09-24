# Brown-UK (БрУК) Source Attribution & Provenance Record

**Dataset Component:** `grammar_v1`
**Governing Issue:** [#8342](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8342)
**Governing Specification:** [`docs/projects/open-model-data/GRAMMAR_DATASET_SPEC_8342.md`](../../../docs/projects/open-model-data/GRAMMAR_DATASET_SPEC_8342.md) § 2.5
**Acceptance Profile:** [`scripts/projects/open_model_data/profiles/grammar_8342.yaml`](../../../scripts/projects/open_model_data/profiles/grammar_8342.yaml)

---

## 1. Upstream Work & Attribution Citation

The negative control instances in `grammar_v1` (protective authentic clean controls) incorporate verified literary and journalistic sentences extracted from the **Brown-UK** corpus:

- **Work:** Brown-UK (БрУК) — Корпус сучасної української мови на засадах Браунівського корпусу / Великий електронний корпус української мови (ВЕКРА)
- **Creators / Maintainers:** Марія Шведова, Андрій Рисін, Василь Старко та співавтори корпусного проєкту
- **Source Repository:** [brown-uk/corpus](https://github.com/brown-uk/corpus)
- **Release Reference:** Brown-UK Corpus of Contemporary Ukrainian (Good-rating subcorpus)
- **License:** [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
- **License Notice:** © 2017–2026 Brown-UK Project contributors. Licensed under CC BY-NC-SA 4.0.

---

## 2. Licensing Compliance & Rights Architecture (SPEC § 2.5)

In accordance with project licensing policy (decision 2026-04-19: permanent open-source educational resource with zero commercialization) and SPEC § 2.5:

1. **Per-Source Row Licensing:**
   - Rather than imposing a single blanket license overlay across disparate source materials, rights and notices are tracked **per individual record**.
   - Every sentence derived from Brown-UK carries `license: "CC BY-NC-SA 4.0"` and `source_corpus: "brown_uk"` in its top-level record and within `source_metadata`.
   - Every sentence derived from UA-GEC carries `license: "CC BY 4.0"` and `source_corpus: "ua_gec_2.0"`.
2. **No Blanket Overlay on CC BY 4.0 (CC BY 4.0 § 2(a)(5)(b)):**
   - No dataset-level ShareAlike or NonCommercial wrapper is placed over CC BY 4.0 text.
3. **Explicit Pre-Release Verification:**
   - This document formalizes and verifies the explicit per-source attribution record required by SPEC § 2.5 (line 111) prior to shard release.

---

## 3. Partitioning, Firewall & Split Isolation

To preserve benchmark firewall integrity and prevent cross-split leakage:
1. **Document-Level Hash Partitioning:**
   - Brown-UK documents are partitioned deterministically by `int(SHA256(doc_id), 16) % 10`.
   - Documents with $h \pmod{10} == 0$ are assigned strictly to evaluation (`eval`).
   - Documents with $h \pmod{10} \ne 0$ are assigned strictly to training (`train`).
   - **0 shared documents** between training and evaluation splits.
2. **Official Held-Out Test Firewall:**
   - Every sentence is screened against the official test set (`gec-fluency.test.m2`). Sentences with exact matches or Jaccard similarity $\ge 0.80$ to the test partition are unconditionally excluded.

---

## 4. Per-Document Source Inventory (50 Documents)

The table below catalogs all 50 source documents from the curated Brown-UK control pool (`brown_uk_negative_control_eval.jsonl`), indicating genre classification, publication details, and delivered sentence counts in `grammar_v1`:

| # | Document ID | Category / Genre | Source Description & Publication | Year | Partition | Delivered Sentences | License |
|---|:---|:---|:---|:---:|:---:|:---:|:---|
| 1 | `A_Chas_Kyivshchyny_Karpiuk_Khochete_znaty_anhliysku_shukayte_movni_tabory_2016` | A (Преса: новини/репортажі) | Газета «Час Київщини», ст. Карп'юк | 2016 | Train | 8 | CC BY-NC-SA 4.0 |
| 2 | `A_Chas_Kyivshchyny_Zakrevskyi_I_radi_b_obyednatysia_2016` | A (Преса: новини/репортажі) | Газета «Час Київщини», ст. Закревський | 2016 | Train | 8 | CC BY-NC-SA 4.0 |
| 3 | `A_Chas_Kyivshchyny_Zakrevskyi_Informatsiynyi_shlahbaum_vid_oblasnoho_avtodoru_2016` | A (Преса: новини/репортажі) | Газета «Час Київщини», ст. Закревський | 2016 | Train | 8 | CC BY-NC-SA 4.0 |
| 4 | `A_Chornomorski_novyny_Boiko-Ozherediva_Torknutysia_vysokykh_istyn_2012` | A (Преса: новини/репортажі) | Газета «Чорноморські новини», ст. Бойко-Ожередова | 2012 | Train | 10 | CC BY-NC-SA 4.0 |
| 5 | `A_Chornomorski_novyny_Sokil_Reverans_pered_ahresorom._Tretii_2015` | A (Преса: новини/репортажі) | Газета «Чорноморські новини», ст. Сокіл | 2015 | Train | 5 | CC BY-NC-SA 4.0 |
| 6 | `A_Detektor_Media_Bakhteyev_Peredvyborcha_reklama_vichna_i_neznyshchenna_2018` | A (Преса: новини/репортажі) | Видання «Детектор Медіа», ст. Бахтєєв | 2018 | Eval | 10 | CC BY-NC-SA 4.0 |
| 7 | `B_AXIOS_1_2015` | B (Преса: публіцистика) | Журнал «AXIOS», випуск 1 | 2015 | Train | 7 | CC BY-NC-SA 4.0 |
| 8 | `B_AXIOS_2_2015` | B (Преса: публіцистика) | Журнал «AXIOS», випуск 2 | 2015 | Train | 9 | CC BY-NC-SA 4.0 |
| 9 | `B_AXIOS_3_2015` | B (Преса: публіцистика) | Журнал «AXIOS», випуск 3 | 2015 | Train | 7 | CC BY-NC-SA 4.0 |
| 10 | `B_Bendyk_Misiolohiia_1_2013` | B (Преса: публіцистика) | Публіцистика, Бендик, «Місіологія», ч. 1 | 2013 | Train | 5 | CC BY-NC-SA 4.0 |
| 11 | `B_Bendyk_Misiolohiia_2_2013` | B (Преса: публіцистика) | Публіцистика, Бендик, «Місіологія», ч. 2 | 2013 | Train | 8 | CC BY-NC-SA 4.0 |
| 12 | `B_Gudziak_Den_nezalezhnosti_2016` | B (Преса: публіцистика) | Борис Ґудзяк, промова до Дня незалежності | 2016 | Train | 8 | CC BY-NC-SA 4.0 |
| 13 | `C_Balandiukh_Virusy_hrypu_sunut_zi_skhodu_2016` | C (Преса: огляди/критика) | Огляд, Баландюх, ст. про віруси грипу | 2016 | Train | 6 | CC BY-NC-SA 4.0 |
| 14 | `C_Dushar_Iz_trepetom_prystupim_Prymitky_vid_redaktora_1_2016` | C (Преса: огляди/критика) | Редакторські примітки, Душар, ч. 1 | 2016 | Train | 10 | CC BY-NC-SA 4.0 |
| 15 | `C_Dushar_Iz_trepetom_prystupim_Prymitky_vid_redaktora_2_2016` | C (Преса: огляди/критика) | Редакторські примітки, Душар, ч. 2 | 2016 | Train | 7 | CC BY-NC-SA 4.0 |
| 16 | `C_Ivanyk_Esperanto_Mova_milioniv_2016` | C (Преса: огляди/критика) | Огляд, Іваник, «Есперанто — мова мільйонів» | 2016 | Train | 7 | CC BY-NC-SA 4.0 |
| 17 | `C_Karavanska_Stylna_knyzhka_dlia_panianky_2015` | C (Преса: огляди/критика) | Оксана Караванська, «Стильна книжка для панянки» | 2015 | Train | 10 | CC BY-NC-SA 4.0 |
| 18 | `C_Kuskal_Yak_adaptuvatysia_2018` | C (Преса: огляди/критика) | Практичний огляд, Кускал, «Як адаптуватися» | 2018 | Train | 11 | CC BY-NC-SA 4.0 |
| 19 | `D_Andrukhovych_Iak_vlashtovano_tsei_svit_2016` | D (Есеїстика/філософія) | Юрій Андрухович, «Як влаштовано цей світ» | 2016 | Train | 9 | CC BY-NC-SA 4.0 |
| 20 | `D_Humeniuk_Maidan_Takhrir_1_2015` | D (Есеїстика/філософія) | Гуменюк, «Майдан Тахрір», ч. 1 | 2015 | Eval | 11 | CC BY-NC-SA 4.0 |
| 21 | `D_Kalytko_Richka_yak_symvol_viry_2013` | D (Есеїстика/філософія) | Катерина Калитко, «Річка як символ віри» | 2013 | Train | 6 | CC BY-NC-SA 4.0 |
| 22 | `D_Kunsht_Chernov_Muzyka_na_dotyk_2016` | D (Есеїстика/філософія) | Журнал «Куншт», Чернов, «Музика на дотик» | 2016 | Train | 10 | CC BY-NC-SA 4.0 |
| 23 | `D_Lemko_1_Tsikavynky_z_istoriyi_Lvova_2011` | D (Есеїстика/краєзнавство) | Ілько Лемко, «Цікавинки з історії Львова», ч. 1 | 2011 | Train | 2 | CC BY-NC-SA 4.0 |
| 24 | `D_Lemko_2_Tsikavynky_z_istoriyi_Lvova_2011` | D (Есеїстика/краєзнавство) | Ілько Лемко, «Цікавинки з історії Львова», ч. 2 | 2011 | Train | 5 | CC BY-NC-SA 4.0 |
| 25 | `E_Lvov_Pro_deiaki_pytannia_praktyky_zastosuvannia_Zakonu_Ukrainy_2015` | E (Практичні коментарі) | Юридичний коментар, Львов, аналіз практики закону | 2015 | Train | 2 | CC BY-NC-SA 4.0 |
| 26 | `E_Orhanizatsiya_roboty_litnikh_shkil_dlya_obdarovanykh_ditey_2013` | E (Методичні посібники) | Методичні рекомендації щодо літніх шкіл | 2013 | Train | 8 | CC BY-NC-SA 4.0 |
| 27 | `F_Askaniya_Nova_turystychna_perlyna_Khersonshchyny_2014` | F (Популярні знання) | Краєзнавчий нарис, «Асканія-Нова» | 2014 | Train | 7 | CC BY-NC-SA 4.0 |
| 28 | `F_Batiy_Ukrayina_Slavetni_hetmany_ta_inshi_postati_kozatskoyi_doby_2010` | F (Біографії/мемуари) | Я. Батій, «Славетні гетьмани та постаті козаччини» | 2010 | Eval | 9 | CC BY-NC-SA 4.0 |
| 29 | `F_Bedenko_Knyha_yunoho_biznesmena_1_2014` | F (Популярні знання) | Беденко, «Книга юного бізнесмена», ч. 1 | 2014 | Train | 9 | CC BY-NC-SA 4.0 |
| 30 | `F_Bedenko_Knyha_yunoho_biznesmena_2_2014` | F (Популярні знання) | Беденко, «Книга юного бізнесмена», ч. 2 | 2014 | Train | 8 | CC BY-NC-SA 4.0 |
| 31 | `F_Bedenko_Knyha_yunoho_biznesmena_3_2014` | F (Популярні знання) | Беденко, «Книга юного бізнесмена», ч. 3 | 2014 | Train | 6 | CC BY-NC-SA 4.0 |
| 32 | `F_Biolohiya_dlia_dopytlyvykh_Ohuz_Nezvychaini_fakty_iz_zhyttia_zvychainykh_yizhachkiv_2013` | F (Популярні знання) | Огуз, «Незвичайні факти із життя їжачків» | 2013 | Train | 6 | CC BY-NC-SA 4.0 |
| 33 | `G_Artemenko_Intelektualna_systema_analizu_ekskursiynykh_marshrutiv_2015` | G (Наукові статті) | Артеменко, система аналізу екскурсійних маршрутів | 2015 | Eval | 8 | CC BY-NC-SA 4.0 |
| 34 | `G_Babak_Infomatsiine_zabezpechennia_monitoryngu_2015` | G (Наукові статті) | Бабак, інформаційне забезпечення моніторингу | 2015 | Pool Reserve | 0 | CC BY-NC-SA 4.0 |
| 35 | `G_Beznosyk_Udoskonalennia_pravovoho_statusu_orhaniv_samoorhanizatsiyi_naselennia_2011` | G (Наукові статті) | Безносик, правовий статус органів самоорганізації | 2011 | Train | 7 | CC BY-NC-SA 4.0 |
| 36 | `G_Bohutskyi_Dynamika_kulturotvorennia_yak_obyekt_doslidzhennia_2014` | G (Наукові статті) | Богуцький, динаміка культуротворення | 2014 | Train | 9 | CC BY-NC-SA 4.0 |
| 37 | `G_Boliukh_Morfolohichna_diahnostyka_metastaziv_u_limfovuzlakh_shyi_ta_seredostinnia_2010` | G (Медичні дослідження) | Болюх, морфологічна діагностика метастазів | 2010 | Eval | 2 | CC BY-NC-SA 4.0 |
| 38 | `G_Bondaruk_Stan_ta_problemy_rozvytku_lisovoyi_sertyfikatsiyi_2011` | G (Наукові статті) | Бондарук, проблеми розвитку лісової сертифікації | 2011 | Train | 5 | CC BY-NC-SA 4.0 |
| 39 | `H_Akhtemiychuk_Operatyvna_khirurhiya_ta_topohrafichna_anatomiya_1_2010` | H (Підручники/фахові) | Ахтемійчук, «Оперативна хірургія», ч. 1 | 2010 | Train | 8 | CC BY-NC-SA 4.0 |
| 40 | `H_Akhtemiychuk_Operatyvna_khirurhiya_ta_topohrafichna_anatomiya_2_2010` | H (Підручники/фахові) | Ахтемійчук, «Оперативна хірургія», ч. 2 | 2010 | Train | 7 | CC BY-NC-SA 4.0 |
| 41 | `H_Albul_Osnovy_operatyvno-rozshukovoyi_diyalnosti_1_2016` | H (Підручники/фахові) | Альбул, основи оперативно-розшукової діяльності, ч. 1 | 2016 | Train | 2 | CC BY-NC-SA 4.0 |
| 42 | `H_Albul_Osnovy_operatyvno-rozshukovoyi_diyalnosti_3_2016` | H (Підручники/фахові) | Альбул, основи оперативно-розшукової діяльності, ч. 3 | 2016 | Train | 5 | CC BY-NC-SA 4.0 |
| 43 | `H_Anderson_Biolohiya_1_2017` | H (Підручники/фахові) | Андерсон, підручник з біології, ч. 1 | 2017 | Train | 9 | CC BY-NC-SA 4.0 |
| 44 | `H_Anderson_Biolohiya_2_2017` | H (Підручники/фахові) | Андерсон, підручник з біології, ч. 2 | 2017 | Train | 9 | CC BY-NC-SA 4.0 |
| 45 | `I_Andrukhovych_Sofiia_Feliks_Avstriya_2014` | I (Художня проза) | Софія Андрухович, роман «Фелікс Австрія» | 2014 | Train | 8 | CC BY-NC-SA 4.0 |
| 46 | `I_Andrusyak_Hoydalka_2015` | I (Художня проза) | Іван Андрусяк, «Гойдалка» | 2015 | Train | 6 | CC BY-NC-SA 4.0 |
| 47 | `I_Babkina_1_Sonia_2013` | I (Художня проза) | Катерина Бабкіна, «Соня» | 2013 | Train | 9 | CC BY-NC-SA 4.0 |
| 48 | `I_Babkina_Shapochka_i_Kyt_2015` | I (Художня проза) | Катерина Бабкіна, «Шапочка і Кит» | 2015 | Train | 10 | CC BY-NC-SA 4.0 |
| 49 | `I_Bachynskyi_Detektyvy_v_Arteku_1_2014` | I (Художня проза) | Андрій Бачинський, «Детективи в Артеку», ч. 1 | 2014 | Eval | 9 | CC BY-NC-SA 4.0 |
| 50 | `I_Bachynskyi_Detektyvy_v_Arteku_2_2014` | I (Художня проза) | Андрій Бачинський, «Детективи в Артеку», ч. 2 | 2014 | Train | 9 | CC BY-NC-SA 4.0 |

**Totals:**
- **Training Slice:** 43 documents, 315 delivered sentences.
- **Evaluation Slice:** 6 documents, 49 delivered sentences.
- **Reserve Pool:** 1 document (`G_Babak_Infomatsiine_zabezpechennia_monitoryngu_2015`), 0 delivered sentences.
- **Grand Total:** 50 cataloged source documents, 364 delivered sentences under CC BY-NC-SA 4.0.

---

## 5. Record-Level Verification Schema

Every record in the component shards carries explicit attribution fields verifying its origin:

```json
{
  "doc_id": "D_Kalytko_Richka_yak_symvol_viry_2013",
  "doc_name": "D_Kalytko_Richka_yak_symvol_viry_2013.txt",
  "source_corpus": "brown_uk",
  "license": "CC BY-NC-SA 4.0",
  "source_metadata": {
    "doc_id": "D_Kalytko_Richka_yak_symvol_viry_2013",
    "doc_name": "D_Kalytko_Richka_yak_symvol_viry_2013.txt",
    "source_corpus": "brown_uk",
    "license": "CC BY-NC-SA 4.0",
    "attribution": "Brown-UK (БрУК): Corpus of Contemporary Ukrainian, CC BY-NC-SA 4.0",
    "authority": "Brown-UK (БрУК) / VESUM / Український правопис (2019)"
  }
}
```
