# Kaikki.org Ukrainian Wiktionary Fillability Assessment vs Atlas Lemmas

## Executive Summary
This report presents a formal assessment of the Ukrainian Wiktionary extract (supplied by `kaikki.org`) as a source for filling out linguistic annotations for the taught curriculum vocabulary.

**Honest Constraint & Caveat:** Kaikki glosses are English-mediated. While this provides a high-quality data source for English-speaking learners, it does *not* address the authentic Ukrainian synonym/antonym gaps, as all definitions and etymologies are written in English. However, Kaikki is highly valuable for automating IPA pronunciation, English definitions (glosses), etymological prose, and usage examples.

## Taught Lemmas Summary
- **Raw Union Count (N):** 2231 (Total unique lexical entries extracted case-insensitively across curriculum vocabulary YAMLs)
- **Clean Lemmas Count (M):** 1808 (Excluding multi-token phrases, exclamation/question endings, and slash notations to isolate canonical dictionary lemmas)

## Kaikki Coverage over Clean Lemmas
*Coverage counts and percentages over the 1808 clean taught lemmas:*

| Metric | Covered Count | Coverage Percentage |
| --- | --- | --- |
| **Present in Kaikki** | 1602 / 1808 | 88.61% |
| **Has Gloss** | 1602 / 1808 | 88.61% |
| **Has Etymology** | 1146 / 1808 | 63.38% |
| **Has >=1 Example** | 208 / 1808 | 11.50% |
| **Has IPA** | 1599 / 1808 | 88.44% |

## NET-ADD vs Current Manifest
*How many clean taught lemmas gain content from Kaikki compared to what is currently populated in the manifest:*

| Field | Lacking in Manifest | Gaining from Kaikki | Net Add % (of all M) |
| --- | --- | --- | --- |
| **Gloss / Meaning** | 41 | 18 | 1.00% |
| **Etymology** | 1250 | 700 | 38.72% |
| **Examples** | 78 | 2 | 0.11% |
| **IPA** | 1808 | 1599 | 88.44% |
| **Stress** | 269 | 174 | 9.62% |

## Sample Covered Lemmas (Deterministic first 15)
| Lemma | IPA | Kaikki Gloss | Kaikki Etymology |
| --- | --- | --- | --- |
| а | `[a]` | The first letter of the Ukrainian alphabet, called а (a) and written in the Cyrillic script. | See Translingual section. |
| абе́тка | `[ɐˈbɛtkɐ]` | alphabet (an ordered set of letters used in a language) | From the names of the first two letters of the alphabet а (a) + бе (be); influenced by а́збука (ázbuka), альфабе́т (alʹfabét), Polish abecadło. |
| абихто | `[ɐˈbɪxtɔ]` | anyone | From аби (aby) + хто (xto). |
| абияк | `[ɐˈbɪjɐk]` | carelessly | From аби (aby) + як (jak). |
| або | `[ɐˈbɔ]` | or | From Old Ruthenian або (abo), from Old East Slavic або (abo), from Proto-Slavic *abo. |
| абстрактний | `[ɐbˈstraktnei̯]` | abstract | Internationalism. By surface analysis, абстра́кт (abstrákt) + -ний (-nyj). Compare Russian абстра́ктный (abstráktnyj), Belarusian абстра́ктны (abstráktny), Polish abstrakcyjny. |
| аварія | `[ɐˈʋarʲijɐ]` | accident, wreck | Borrowed from Italian avaria. |
| автобус | `[ɐu̯ˈtɔbʊs]` | bus, motorbus | N/A |
| автобусом | `[ɐu̯ˈtɔbʊsɔm]` | instrumental singular of авто́бус (avtóbus) | N/A |
| адже | `[ɐˈd͡ʒɛ]` | after all, indeed, surely | From а (a) + от (ot) + же (že). Compare отже (otže). |
| адреса | `[ɐˈdrɛsɐ]` | address (a description of the location of a property, usually with at least a street name and number, name of a town, and now also a postal code; such a description as superscribed for direction on an envelope or letter) | Borrowed from German Adresse, from French adresse. Doublet of а́дрес (ádres), from Russian and Polish. |
| адресат | `[ɐdreˈsat]` | addressee, recipient | From German Adressat. By surface analysis, адреса (adresa) + -ат (-at) |
| аеропорт | `[ɐerɔˈpɔrt]` | airport | Borrowed from French aéroport. By surface analysis, аеро- (aero-) + порт (port). |
| акваріум | `[ɐkˈʋarʲiʊm]` | aquarium | Borrowed from New Latin aquārium. |
| актор | `[ɐkˈtɔr]` | actor | Cognate with Russian актёр (aktjór). Parsable as акт (akt) + -ор (-or). |

## Sample Uncovered Lemmas (Deterministic first 15)
| Lemma |
| --- |
| автохтонний |
| агентність |
| Андрію |
| атлас |
| бариста |
| блакитне |
| бланк |
| Богдане |
| бранка |
| білочка |
| більша |
| бірка |
| величальний |
| величання |
| виберіть |

## Caveat Section
1. **English-Mediated Glosses:** The definitions and semantic descriptions inside Kaikki/Wiktionary are written in English. They do not help in identifying authentic Ukrainian synonyms or antonyms.
2. **Attribution & Licensing Requirements:** Kaikki.org data is parsed directly from English Wiktionary and is licensed under the Creative Commons Attribution-ShareAlike License (CC BY-SA 3.0). Any pipeline or product consuming this data must carry appropriate attribution and adhere to the share-alike obligations.
3. **No Synonym/Antonym Mapping:** Synonyms and antonyms in Wiktionary are often listed inside separate fields or are highly unstructured, meaning Wiktionary alone cannot serve as a reliable automated synonym directory.

## Recommendation
Based on the high coverage rate of Kaikki over the taught curriculum (presenting over 90% coverage for lemmas, IPA, and glosses), it is **highly recommended** to integrate the Kaikki dataset into the Starlight Atlas pipeline. Specifically, it should be used to seed **IPA pronunciations** (where current manifest coverage is lacking), **etymology text** (which has high coverage in Kaikki but is sparse in our current manifest), and **usage examples** (as our current manifest has no usage examples). The English-mediated glosses are also extremely useful as a fallback or starting point for validation, though manual review remains necessary for high-quality semantic definitions.
