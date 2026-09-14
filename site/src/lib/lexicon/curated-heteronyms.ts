/**
 * Curated heteronym disambiguation dataset for Word Atlas client-side shell (#8022).
 *
 * NOTE: This is an interim client-side bridge for entries whose runtime shards
 * in the pinned release asset (ATLAS_TREE_ASSET_ID) have not yet been rebuilt
 * with `record.entry.heteronyms`.
 *
 * Once a new release asset containing enriched `record.entry.heteronyms` is
 * generated and pinned, `getEffectiveHeteronyms(record)` automatically yields
 * to `record.entry.heteronyms` and ignores this fallback.
 *
 * All linguistic data herein is exported directly from `scripts/lexicon/enrich_heteronyms.py`,
 * verified against VESUM (morphology/paradigms), СУМ-11/СУМ-20 (definitions and distinctions),
 * and PULS (CEFR levels), and validated by `tests/test_enrich_heteronyms.py`.
 */

import type { EntryRecord } from "./atlas-data-source";
import type { LexiconEntry } from "./atlasDb";

export const CURATED_HETERONYMS: Record<string, LexiconEntry[]> = {
  "город": [
    {
      "lemma": "город",
      "url_slug": "город",
      "headword": "горо́д",
      "short_label": "ділянка землі (A2)",
      "gloss": "vegetable garden, garden plot",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ɦɔˈrɔd]",
        "source": "VESUM"
      },
      "stress": {
        "form": "горо́д",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "горо́д",
              "plural": "горо́ди"
            },
            "родовий": {
              "singular": "горо́ду",
              "plural": "городі́в"
            },
            "давальний": {
              "singular": "горо́дові / горо́ду",
              "plural": "горо́дам"
            },
            "знахідний": {
              "singular": "горо́д",
              "plural": "горо́ди"
            },
            "орудний": {
              "singular": "горо́дом",
              "plural": "горо́дами"
            },
            "місцевий": {
              "singular": "на горо́ді / горо́ду",
              "plural": "горо́дах"
            },
            "кличний": {
              "singular": "горо́де",
              "plural": "горо́ди"
            }
          }
        },
        "stress": {
          "source": "ukrainian-word-stress",
          "forms": {
            "городу": "горо́ду",
            "городом": "горо́дом",
            "городі": "горо́ді",
            "городе": "горо́де",
            "городи": "горо́ди",
            "городів": "городі́в",
            "городам": "горо́дам",
            "городами": "горо́дами",
            "городах": "горо́дах"
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-20",
          "items": [
            "грядка",
            "городчик"
          ]
        },
        "idioms": {
          "items": [
            {
              "phrase": "город ( рідше тин) городити",
              "definition": "Починати якусь копітку справу.",
              "source": "Фразеологічний словник української мови"
            },
            {
              "phrase": "камінь у чийсь город",
              "definition": "Недоброзичливий натяк кому-небудь.",
              "source": "Фразеологічний словник української мови"
            }
          ],
          "source": "Фразеологічний словник української мови"
        },
        "proverbs": {
          "items": [
            {
              "text": "В хаті гульки, а в городі ані цибульки",
              "gloss": "Глум з господині, що гуляє, а не пильнує господарства.",
              "source": "Приповідки або українсько-народня філософія"
            },
            {
              "text": "Мій город, як моя комора",
              "gloss": "Огородина в літі помагає багато в харчі.",
              "source": "Приповідки або українсько-народня філософія"
            },
            {
              "text": "Не лазь у городи, бо наробиш шкоди",
              "gloss": "До чужого діла не мішайся, бо не знаєш його.",
              "source": "Приповідки або українсько-народня філософія"
            }
          ],
          "source": "Приповідки або українсько-народня філософія"
        }
      },
      "examples": [
        {
          "uk": "На вихідни́х ми бу́демо працюва́ти на горо́ді.",
          "en": "On the weekend, we will work in the vegetable garden.",
          "source": "Anna Ohoiko",
          "locator": "ohoiko-1000-words entry 168"
        }
      ],
      "distinction_note": "Не плутати з омографом «го́род» (наголос на першому складі: застаріле «місто», фортеця)."
    },
    {
      "lemma": "город",
      "url_slug": "город",
      "headword": "го́род",
      "short_label": "заст. місто",
      "gloss": "city, town, fortified settlement (archaic)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured",
        "attestations": [
          {
            "source": "esum",
            "ref": "город:1:570",
            "word": "город",
            "detail": "город (заст. розм.) «місто», город (< огород) «квітник біля хати»"
          }
        ]
      },
      "pronunciation": {
        "ipa": "[ˈɦɔrɔd]",
        "source": "kaikki/Wiktionary (CC BY-SA 3.0)"
      },
      "stress": {
        "form": "го́род",
        "source": "kaikki/Wiktionary (CC BY-SA 3.0)"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "го́род",
              "plural": "городи́"
            },
            "родовий": {
              "singular": "го́рода (го́роду)",
              "plural": "городі́в"
            },
            "давальний": {
              "singular": "го́родові / го́роду",
              "plural": "города́м"
            },
            "знахідний": {
              "singular": "го́род",
              "plural": "городи́"
            },
            "орудний": {
              "singular": "го́родом",
              "plural": "города́ми"
            },
            "місцевий": {
              "singular": "у го́роді",
              "plural": "города́х"
            },
            "кличний": {
              "singular": "го́роде",
              "plural": "городи́"
            }
          }
        },
        "stress": {
          "source": "Правописний словник Голоскевича (1929)",
          "forms": {
            "города": "го́рода",
            "городу": "го́роду",
            "городом": "го́родом",
            "городі": "го́роді",
            "городи": "городи́",
            "городів": "городі́в",
            "городам": "города́м",
            "городами": "города́ми",
            "городах": "города́х"
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11: Те саме, що → місто",
          "items": [
            "місто"
          ]
        }
      },
      "examples": [
        {
          "uk": "В тім городі жила Дидона, А город звався Карфаген.",
          "en": "In that city lived Dido, and the city was called Carthage.",
          "source": "Іван Котляревський, «Енеїда»",
          "locator": "Котл., І, 1952, 71"
        }
      ],
      "distinction_note": "Не плутати з сучасним словом «горо́д» (наголос на другому складі: ділянка землі біля хати для вирощування овочів)."
    }
  ],
  "замок": [
    {
      "lemma": "замок",
      "url_slug": "замок",
      "headword": "за́мок",
      "short_label": "палац, фортеця",
      "gloss": "castle, fortress, palace",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈzamɔk]",
        "source": "kaikki/Wiktionary"
      },
      "stress": {
        "form": "за́мок",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "за́мок",
              "plural": "замки́"
            },
            "родовий": {
              "singular": "за́мку",
              "plural": "замкі́в"
            },
            "давальний": {
              "singular": "за́мку / за́мкові",
              "plural": "замка́м"
            },
            "знахідний": {
              "singular": "за́мок",
              "plural": "замки́"
            },
            "орудний": {
              "singular": "за́мком",
              "plural": "замка́ми"
            },
            "місцевий": {
              "singular": "у за́мку",
              "plural": "замка́х"
            },
            "кличний": {
              "singular": "за́мку",
              "plural": "замки́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-20 / Караванський",
          "items": [
            "фортеця",
            "твердиня",
            "палац",
            "цитадель"
          ]
        }
      },
      "examples": [
        {
          "uk": "Старовинний за́мок височів над долиною.",
          "en": "The ancient castle towered over the valley.",
          "source": "СУМ-11"
        }
      ],
      "distinction_note": "Не плутати з омографом «замо́к» (наголос на другому складі: пристрій для замикання дверей)."
    },
    {
      "lemma": "замок",
      "url_slug": "замок",
      "headword": "замо́к",
      "short_label": "пристрій для замикання",
      "gloss": "lock (door lock, padlock)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈmɔk]",
        "source": "kaikki/Wiktionary"
      },
      "stress": {
        "form": "замо́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "замо́к",
              "plural": "замки́"
            },
            "родовий": {
              "singular": "замка́",
              "plural": "замкі́в"
            },
            "давальний": {
              "singular": "замку́ / замко́ві",
              "plural": "замка́м"
            },
            "знахідний": {
              "singular": "замо́к",
              "plural": "замки́"
            },
            "орудний": {
              "singular": "замко́м",
              "plural": "замка́ми"
            },
            "місцевий": {
              "singular": "у замку́",
              "plural": "замка́х"
            },
            "кличний": {
              "singular": "замку́",
              "plural": "замки́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-20",
          "items": [
            "колодка",
            "засув",
            "клямка"
          ]
        }
      },
      "examples": [
        {
          "uk": "Він замкнув двері на замо́к.",
          "en": "He locked the door with a lock.",
          "source": "СУМ-11"
        }
      ],
      "distinction_note": "Не плутати з омографом «за́мок» (наголос на першому складі: фортеця або середньовічний палац)."
    }
  ],
  "атлас": [
    {
      "lemma": "атлас",
      "url_slug": "атлас",
      "headword": "а́тлас",
      "short_label": "збірник карт",
      "gloss": "atlas (bound collection of maps)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈatɫɐs]",
        "source": "VESUM"
      },
      "stress": {
        "form": "а́тлас",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "а́тлас",
              "plural": "а́тласи"
            },
            "родовий": {
              "singular": "а́тласу",
              "plural": "а́тласів"
            },
            "давальний": {
              "singular": "а́тласу / а́тласові",
              "plural": "а́тласам"
            },
            "знахідний": {
              "singular": "а́тлас",
              "plural": "а́тласи"
            },
            "орудний": {
              "singular": "а́тласом",
              "plural": "а́тласами"
            },
            "місцевий": {
              "singular": "в а́тласі",
              "plural": "а́тласах"
            },
            "кличний": {
              "singular": "а́тласе",
              "plural": "а́тласи"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "збірник карт",
            "альбом карт",
            "географічний атлас"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «атла́с» (наголос на другому складі: шовкова тканина)."
    },
    {
      "lemma": "атлас",
      "url_slug": "атлас",
      "headword": "атла́с",
      "short_label": "тканина",
      "gloss": "satin (glossy silk fabric)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ɐtˈɫas]",
        "source": "VESUM"
      },
      "stress": {
        "form": "атла́с",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "атла́с",
              "plural": "атла́си"
            },
            "родовий": {
              "singular": "атла́су",
              "plural": "атла́сів"
            },
            "давальний": {
              "singular": "атла́су / атла́сові",
              "plural": "атла́сам"
            },
            "знахідний": {
              "singular": "атла́с",
              "plural": "атла́си"
            },
            "орудний": {
              "singular": "атла́сом",
              "plural": "атла́сами"
            },
            "місцевий": {
              "singular": "в атла́сі",
              "plural": "атла́сах"
            },
            "кличний": {
              "singular": "атла́се",
              "plural": "атла́си"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "шовк",
            "сатин",
            "шовкова тканина"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «а́тлас» (наголос на першому складі: збірник географічних або анатомічних карт)."
    }
  ],
  "обід": [
    {
      "lemma": "обід",
      "url_slug": "обід",
      "headword": "о́бід",
      "short_label": "у колеса",
      "gloss": "rim, felly (outer wooden or metal rim of a wheel)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈɔbʲid]",
        "source": "VESUM"
      },
      "stress": {
        "form": "о́бід",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "о́бід",
              "plural": "о́боди"
            },
            "родовий": {
              "singular": "о́бода",
              "plural": "о́бодів"
            },
            "давальний": {
              "singular": "о́бодові / о́боду",
              "plural": "о́бодам"
            },
            "знахідний": {
              "singular": "о́бід",
              "plural": "о́боди"
            },
            "орудний": {
              "singular": "о́бодом",
              "plural": "о́бодами"
            },
            "місцевий": {
              "singular": "на о́боді",
              "plural": "на о́бодах"
            },
            "кличний": {
              "singular": "о́боде",
              "plural": "о́боди"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "обруч",
            "колесо"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «обі́д» (наголос на другому складі: прийом їжі або ланч)."
    },
    {
      "lemma": "обід",
      "url_slug": "обід",
      "headword": "обі́д",
      "short_label": "споживання їжі (A1)",
      "gloss": "lunch, dinner, midday meal",
      "pos": "noun",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[oˈbʲid]",
        "source": "VESUM"
      },
      "stress": {
        "form": "обі́д",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "обі́д",
              "plural": "обі́ди"
            },
            "родовий": {
              "singular": "обі́ду",
              "plural": "обі́дів"
            },
            "давальний": {
              "singular": "обі́дові / обі́ду",
              "plural": "обі́дам"
            },
            "знахідний": {
              "singular": "обі́д",
              "plural": "обі́ди"
            },
            "орудний": {
              "singular": "обі́дом",
              "plural": "обі́дами"
            },
            "місцевий": {
              "singular": "на обі́ді / по обі́ду",
              "plural": "на обі́дах"
            },
            "кличний": {
              "singular": "обі́де",
              "plural": "обі́ди"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-20",
          "items": [
            "трапеза",
            "ланч",
            "полуденок"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «о́бід» (наголос на першому складі: зовнішнє кільце колеса)."
    }
  ],
  "орган": [
    {
      "lemma": "орган",
      "url_slug": "орган",
      "headword": "о́рган",
      "short_label": "частина тіла / установа (A1)",
      "gloss": "organ (body part or state institution/publication)",
      "pos": "noun",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈɔrɦɐn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "о́рган",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "о́рган",
              "plural": "о́ргани"
            },
            "родовий": {
              "singular": "о́ргана / о́ргану",
              "plural": "о́рганів"
            },
            "давальний": {
              "singular": "о́ргану / о́рганові",
              "plural": "о́рганам"
            },
            "знахідний": {
              "singular": "о́рган",
              "plural": "о́ргани"
            },
            "орудний": {
              "singular": "о́рганом",
              "plural": "о́рганами"
            },
            "місцевий": {
              "singular": "в о́ргані",
              "plural": "в о́рганах"
            },
            "кличний": {
              "singular": "о́ргане",
              "plural": "о́ргани"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "інституція",
            "установа",
            "відомство"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «орга́н» (наголос на другому складі: духовий клавішний музичний інструмент)."
    },
    {
      "lemma": "орган",
      "url_slug": "орган",
      "headword": "орга́н",
      "short_label": "музичний інструмент (B1)",
      "gloss": "pipe organ (keyboard wind instrument)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ɔrˈɦan]",
        "source": "VESUM"
      },
      "stress": {
        "form": "орга́н",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "орга́н",
              "plural": "орга́ни"
            },
            "родовий": {
              "singular": "орга́на",
              "plural": "орга́нів"
            },
            "давальний": {
              "singular": "орга́ну / орга́нові",
              "plural": "орга́нам"
            },
            "знахідний": {
              "singular": "орга́н",
              "plural": "орга́ни"
            },
            "орудний": {
              "singular": "орга́ном",
              "plural": "орга́нами"
            },
            "місцевий": {
              "singular": "на орга́ні",
              "plural": "на орга́нах"
            },
            "кличний": {
              "singular": "орга́не",
              "plural": "орга́ни"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "духовий інструмент"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «о́рган» (наголос на першому складі: частина тіла або державна установа)."
    }
  ],
  "музика": [
    {
      "lemma": "музика",
      "url_slug": "музика",
      "headword": "му́зика",
      "short_label": "вид мистецтва (A1)",
      "gloss": "music (art form, melody, organized sounds)",
      "pos": "noun",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈmuzɪkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "му́зика",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "му́зика",
              "plural": "му́зики"
            },
            "родовий": {
              "singular": "му́зики",
              "plural": "му́зик"
            },
            "давальний": {
              "singular": "му́зиці",
              "plural": "му́зикам"
            },
            "знахідний": {
              "singular": "му́зику",
              "plural": "му́зики"
            },
            "орудний": {
              "singular": "му́зикою",
              "plural": "му́зиками"
            },
            "місцевий": {
              "singular": "у му́зиці",
              "plural": "у му́зиках"
            },
            "кличний": {
              "singular": "му́зико",
              "plural": "му́зики"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "мелодія",
            "композиція"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «музи́ка» (наголос на другому складі: музикант, виконавець)."
    },
    {
      "lemma": "музика",
      "url_slug": "музика",
      "headword": "музи́ка",
      "short_label": "музикант, виконавець (B1)",
      "gloss": "musician, instrumentalist, folk performer",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[muˈzɪkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "музи́ка",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "музи́ка",
              "plural": "музи́ки"
            },
            "родовий": {
              "singular": "музи́ки",
              "plural": "музи́к"
            },
            "давальний": {
              "singular": "музи́ці",
              "plural": "музи́кам"
            },
            "знахідний": {
              "singular": "музи́ку",
              "plural": "музи́к"
            },
            "орудний": {
              "singular": "музи́кою",
              "plural": "музи́ками"
            },
            "місцевий": {
              "singular": "при музи́ці",
              "plural": "при музи́ках"
            },
            "кличний": {
              "singular": "музи́ко",
              "plural": "музи́ки"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "музикант",
            "інструменталіст",
            "грач"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «му́зика» (наголос на першому складі: вид мистецтва або мелодія)."
    }
  ],
  "ніколи": [
    {
      "lemma": "ніколи",
      "url_slug": "ніколи",
      "headword": "ні́коли",
      "short_label": "немає часу (A1)",
      "gloss": "there is no time (predicative)",
      "pos": "adverb",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈnʲikɔlɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ні́коли",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник / предикатив",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «ніко́ли» (наголос на другому складі: за жодних обставин, в ніякий час)."
    },
    {
      "lemma": "ніколи",
      "url_slug": "ніколи",
      "headword": "ніко́ли",
      "short_label": "у жодному разі (A1)",
      "gloss": "never, at no time",
      "pos": "adverb",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[nʲiˈkɔlɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ніко́ли",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «ні́коли» (наголос на першому складі: немає вільного часу)."
    }
  ],
  "нікуди": [
    {
      "lemma": "нікуди",
      "url_slug": "нікуди",
      "headword": "ні́куди",
      "short_label": "немає куди йти (B1)",
      "gloss": "nowhere to go (there is no place to go, predicative)",
      "pos": "adverb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈnʲikudɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ні́куди",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник / предикатив",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «ніку́ди» (наголос на другому складі: до жодного місця)."
    },
    {
      "lemma": "нікуди",
      "url_slug": "нікуди",
      "headword": "ніку́ди",
      "short_label": "у жодне місце (B1)",
      "gloss": "nowhere, to nowhere, not anywhere",
      "pos": "adverb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[nʲiˈkudɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ніку́ди",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «ні́куди» (наголос на першому складі: немає куди подітися)."
    }
  ],
  "вигода": [
    {
      "lemma": "вигода",
      "url_slug": "вигода",
      "headword": "ви́года",
      "short_label": "зручність, комфорт (B1)",
      "gloss": "convenience, comfort, amenity (facilities, comfortable living)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwɪɦɔdɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́года",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ви́года",
              "plural": "ви́годи"
            },
            "родовий": {
              "singular": "ви́годи",
              "plural": "ви́гід"
            },
            "давальний": {
              "singular": "ви́годі",
              "plural": "ви́годам"
            },
            "знахідний": {
              "singular": "ви́году",
              "plural": "ви́годи"
            },
            "орудний": {
              "singular": "ви́годою",
              "plural": "ви́годами"
            },
            "місцевий": {
              "singular": "у ви́годі",
              "plural": "у ви́годах"
            },
            "кличний": {
              "singular": "ви́годо",
              "plural": "ви́годи"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "комфорт",
            "затишок",
            "зручність"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «виго́да» (наголос на другому складі: матеріальний зиск, користь, прибуток)."
    },
    {
      "lemma": "вигода",
      "url_slug": "вигода",
      "headword": "виго́да",
      "short_label": "користь, прибуток (B1)",
      "gloss": "profit, advantage, gain, benefit",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wɪˈɦɔdɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "виго́да",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "виго́да",
              "plural": "виго́ди"
            },
            "родовий": {
              "singular": "виго́ди",
              "plural": "вигі́д"
            },
            "давальний": {
              "singular": "виго́ді",
              "plural": "виго́дам"
            },
            "знахідний": {
              "singular": "виго́ду",
              "plural": "виго́ди"
            },
            "орудний": {
              "singular": "виго́дою",
              "plural": "виго́дами"
            },
            "місцевий": {
              "singular": "у виго́ді",
              "plural": "у виго́дах"
            },
            "кличний": {
              "singular": "виго́до",
              "plural": "виго́ди"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-20",
          "items": [
            "користь",
            "зиск",
            "прибуток"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ви́года» (наголос на першому складі: зручність, комфортні умови життя)."
    }
  ],
  "заклад": [
    {
      "lemma": "заклад",
      "url_slug": "заклад",
      "headword": "за́клад",
      "short_label": "установа, організація (B1)",
      "gloss": "institution, establishment, facility (school, organisation)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈzɑkɫɐd]",
        "source": "VESUM"
      },
      "stress": {
        "form": "за́клад",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "за́клад",
              "plural": "за́клади"
            },
            "родовий": {
              "singular": "за́кладу",
              "plural": "за́кладів"
            },
            "давальний": {
              "singular": "за́кладу / за́кладові",
              "plural": "за́кладам"
            },
            "знахідний": {
              "singular": "за́клад",
              "plural": "за́клади"
            },
            "орудний": {
              "singular": "за́кладом",
              "plural": "за́кладами"
            },
            "місцевий": {
              "singular": "у за́кладі",
              "plural": "у за́кладах"
            },
            "кличний": {
              "singular": "за́кладе",
              "plural": "за́клади"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "установа",
            "підприємство",
            "інституція"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «закла́д» (наголос на другому складі: парі або грошова застава)."
    },
    {
      "lemma": "заклад",
      "url_slug": "заклад",
      "headword": "закла́д",
      "short_label": "парі / застава (B2)",
      "gloss": "wager, bet, pledge, pawn (monetary stake or pawned asset)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[zɐˈkɫɑd]",
        "source": "VESUM"
      },
      "stress": {
        "form": "закла́д",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "закла́д",
              "plural": "закла́ди"
            },
            "родовий": {
              "singular": "закла́ду",
              "plural": "закла́дів"
            },
            "давальний": {
              "singular": "закла́ду / закла́дові",
              "plural": "закла́дам"
            },
            "знахідний": {
              "singular": "закла́д",
              "plural": "закла́ди"
            },
            "орудний": {
              "singular": "закла́дом",
              "plural": "закла́дами"
            },
            "місцевий": {
              "singular": "у закла́ді",
              "plural": "у закла́дах"
            },
            "кличний": {
              "singular": "закла́де",
              "plural": "закла́ди"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "парі",
            "застава"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «за́клад» (наголос на першому складі: навчальний чи громадський заклад)."
    }
  ],
  "електрик": [
    {
      "lemma": "електрик",
      "url_slug": "електрик",
      "headword": "еле́ктрик",
      "short_label": "блакитний колір (B2)",
      "gloss": "electric blue (vibrant light blue color shade)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ɛˈlɛktrɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "еле́ктрик",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "еле́ктрик",
              "plural": "еле́ктрики"
            },
            "родовий": {
              "singular": "еле́ктрика",
              "plural": "еле́ктриків"
            },
            "давальний": {
              "singular": "еле́ктрику",
              "plural": "еле́ктрикам"
            },
            "знахідний": {
              "singular": "еле́ктрик",
              "plural": "еле́ктрики"
            },
            "орудний": {
              "singular": "еле́ктриком",
              "plural": "еле́ктриками"
            },
            "місцевий": {
              "singular": "в еле́ктрику",
              "plural": "в еле́ктриках"
            },
            "кличний": {
              "singular": "еле́ктрику",
              "plural": "еле́ктрики"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "блакитний колір",
            "яскраво-синій"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «електри́к» (наголос на останньому складі: спеціаліст із електрообладнання)."
    },
    {
      "lemma": "електрик",
      "url_slug": "електрик",
      "headword": "електри́к",
      "short_label": "фахівець з електрики (B1)",
      "gloss": "electrician, electrical technician",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ɛlɛkˈtrɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "електри́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "електри́к",
              "plural": "електрики́"
            },
            "родовий": {
              "singular": "електрика́",
              "plural": "електрикі́в"
            },
            "давальний": {
              "singular": "електрику́ / електрико́ві",
              "plural": "електрика́м"
            },
            "знахідний": {
              "singular": "електрика́",
              "plural": "електрикі́в"
            },
            "орудний": {
              "singular": "електрико́м",
              "plural": "електрика́ми"
            },
            "місцевий": {
              "singular": "на електрику́",
              "plural": "на електрика́х"
            },
            "кличний": {
              "singular": "електри́ку",
              "plural": "електрики́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "електромонтер",
            "електротехнік"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «еле́ктрик» (наголос на другому складі: блакитно-синій колір)."
    }
  ],
  "підсумок": [
    {
      "lemma": "підсумок",
      "url_slug": "підсумок",
      "headword": "пі́дсумок",
      "short_label": "результат, висновок (A2)",
      "gloss": "summary, total, summation, overall result",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈpʲidsumɔk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пі́дсумок",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "пі́дсумок",
              "plural": "пі́дсумки"
            },
            "родовий": {
              "singular": "пі́дсумку",
              "plural": "пі́дсумків"
            },
            "давальний": {
              "singular": "пі́дсумку / пі́дсумкові",
              "plural": "пі́дсумкам"
            },
            "знахідний": {
              "singular": "пі́дсумок",
              "plural": "пі́дсумки"
            },
            "орудний": {
              "singular": "пі́дсумком",
              "plural": "пі́дсумками"
            },
            "місцевий": {
              "singular": "у пі́дсумку",
              "plural": "у пі́дсумках"
            },
            "кличний": {
              "singular": "пі́дсумку",
              "plural": "пі́дсумки"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "результат",
            "висновок",
            "баланс"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «підсу́мок» (наголос на другому складі: військова сумка для набоїв)."
    },
    {
      "lemma": "підсумок",
      "url_slug": "підсумок",
      "headword": "підсу́мок",
      "short_label": "сумка для набоїв (B2)",
      "gloss": "cartridge pouch, ammo pouch (soldier's belt pouch for bullets)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[pʲidˈsumɔk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "підсу́мок",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "підсу́мок",
              "plural": "підсу́мки"
            },
            "родовий": {
              "singular": "підсу́мка",
              "plural": "підсу́мків"
            },
            "давальний": {
              "singular": "підсу́мку / підсу́мкові",
              "plural": "підсу́мкам"
            },
            "знахідний": {
              "singular": "підсу́мок",
              "plural": "підсу́мки"
            },
            "орудний": {
              "singular": "підсу́мком",
              "plural": "підсу́мками"
            },
            "місцевий": {
              "singular": "у підсу́мку",
              "plural": "у підсу́мках"
            },
            "кличний": {
              "singular": "підсу́мку",
              "plural": "підсу́мки"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "ладунка",
            "патронташ"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «пі́дсумок» (наголос на першому складі: остаточний висновок або результат)."
    }
  ],
  "правило": [
    {
      "lemma": "правило",
      "url_slug": "правило",
      "headword": "пра́вило",
      "short_label": "норма, настанова (A1)",
      "gloss": "rule, regulation, principle, prescribed code of conduct",
      "pos": "noun",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈprɑwɪɫɔ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пра́вило",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "пра́вило",
              "plural": "пра́вила"
            },
            "родовий": {
              "singular": "пра́вила",
              "plural": "пра́вил"
            },
            "давальний": {
              "singular": "пра́вилу / пра́вилові",
              "plural": "пра́вилам"
            },
            "знахідний": {
              "singular": "пра́вило",
              "plural": "пра́вила"
            },
            "орудний": {
              "singular": "пра́вилом",
              "plural": "пра́вилами"
            },
            "місцевий": {
              "singular": "у пра́вилі",
              "plural": "у пра́вилах"
            },
            "кличний": {
              "singular": "пра́вило",
              "plural": "пра́вила"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "закон",
            "норма",
            "припис"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «прави́ло» (наголос на другому складі: кермо човна чи інструмент вирівнювання)."
    },
    {
      "lemma": "правило",
      "url_slug": "правило",
      "headword": "прави́ло",
      "short_label": "кермо / будівельна рейка (B2)",
      "gloss": "rudder, helm, straightedge guide, leveling rule",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[prɐˈwɪɫɔ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "прави́ло",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "прави́ло",
              "plural": "прави́ла"
            },
            "родовий": {
              "singular": "прави́ла",
              "plural": "прави́л"
            },
            "давальний": {
              "singular": "прави́лу / прави́лові",
              "plural": "прави́лам"
            },
            "знахідний": {
              "singular": "прави́ло",
              "plural": "прави́ла"
            },
            "орудний": {
              "singular": "прави́лом",
              "plural": "прави́лами"
            },
            "місцевий": {
              "singular": "на прави́лі",
              "plural": "на прави́лах"
            },
            "кличний": {
              "singular": "прави́ло",
              "plural": "прави́ла"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "кермо",
            "стерно",
            "рейка"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «пра́вило» (наголос на першому складі: закон, настанова, обов'язкова вимога)."
    }
  ],
  "дерен": [
    {
      "lemma": "дерен",
      "url_slug": "дерен",
      "headword": "де́рен",
      "short_label": "кущ або ягоди (кизил, B2)",
      "gloss": "cornel, dogwood (Cornus shrub or its edible red fruit)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈdɛrɛn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "де́рен",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "де́рен",
              "plural": "де́рени"
            },
            "родовий": {
              "singular": "де́рну / де́рену",
              "plural": "де́ренів"
            },
            "давальний": {
              "singular": "де́рну / де́ренові",
              "plural": "де́ренам"
            },
            "знахідний": {
              "singular": "де́рен",
              "plural": "де́рени"
            },
            "орудний": {
              "singular": "де́рном / де́реном",
              "plural": "де́ренами"
            },
            "місцевий": {
              "singular": "у де́рені",
              "plural": "у де́ренах"
            },
            "кличний": {
              "singular": "де́рене",
              "plural": "де́рени"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "кизил",
            "свидина"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «дере́н» (наголос на другому складі: верхній шар землі з корінням трави)."
    },
    {
      "lemma": "дерен",
      "url_slug": "дерен",
      "headword": "дере́н",
      "short_label": "пласт землі з травою (дернина, B2)",
      "gloss": "turf, sod (surface layer of soil densely matted with roots)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[dɛˈrɛn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "дере́н",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "дере́н",
              "plural": "дерни́"
            },
            "родовий": {
              "singular": "дерну́",
              "plural": "дерні́в"
            },
            "давальний": {
              "singular": "дерну́ / дерно́ві",
              "plural": "дерна́м"
            },
            "знахідний": {
              "singular": "дере́н",
              "plural": "дерни́"
            },
            "орудний": {
              "singular": "дерно́м",
              "plural": "дерна́ми"
            },
            "місцевий": {
              "singular": "у дерну́",
              "plural": "у дерна́х"
            },
            "кличний": {
              "singular": "дерну́",
              "plural": "дерни́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "дернина",
            "мурава"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «де́рен» (наголос на першому складі: кущ кизилу чи його плоди)."
    }
  ],
  "ірис": [
    {
      "lemma": "ірис",
      "url_slug": "ірис",
      "headword": "і́рис",
      "short_label": "квітка (півники, B1)",
      "gloss": "iris (flowering perennial plant with sword-shaped leaves)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈirɪs]",
        "source": "VESUM"
      },
      "stress": {
        "form": "і́рис",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "і́рис",
              "plural": "і́риси"
            },
            "родовий": {
              "singular": "і́рису",
              "plural": "і́рисів"
            },
            "давальний": {
              "singular": "і́рисові / і́рису",
              "plural": "і́рисам"
            },
            "знахідний": {
              "singular": "і́рис",
              "plural": "і́риси"
            },
            "орудний": {
              "singular": "і́рисом",
              "plural": "і́рисами"
            },
            "місцевий": {
              "singular": "в і́рисі",
              "plural": "в і́рисах"
            },
            "кличний": {
              "singular": "і́рисе",
              "plural": "і́риси"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "півники",
            "касатик"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «іри́с» (наголос на другому складі: цукерка-тягучка або райдужка ока)."
    },
    {
      "lemma": "ірис",
      "url_slug": "ірис",
      "headword": "іри́с",
      "short_label": "цукерка / райдужка ока (B1)",
      "gloss": "toffee candy (chewy caramel sweets); anatomical iris of the eye",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[iˈrɪs]",
        "source": "VESUM"
      },
      "stress": {
        "form": "іри́с",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "іри́с",
              "plural": "іри́си"
            },
            "родовий": {
              "singular": "іри́су / іри́са",
              "plural": "іри́сів"
            },
            "давальний": {
              "singular": "іри́сові / іри́су",
              "plural": "іри́сам"
            },
            "знахідний": {
              "singular": "іри́с",
              "plural": "іри́си"
            },
            "орудний": {
              "singular": "іри́сом",
              "plural": "іри́сами"
            },
            "місцевий": {
              "singular": "в іри́сі",
              "plural": "в іри́сах"
            },
            "кличний": {
              "singular": "іри́се",
              "plural": "іри́си"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "тягучка",
            "райдужка"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «і́рис» (наголос на першому складі: квітка півники)."
    }
  ],
  "колос": [
    {
      "lemma": "колос",
      "url_slug": "колос",
      "headword": "ко́лос",
      "short_label": "суцвіття злаків (B1)",
      "gloss": "ear of grain, spike (fruiting head of wheat, rye, or barley)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈkɔɫɔs]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́лос",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ко́лос",
              "plural": "колоски́ / коло́сся"
            },
            "родовий": {
              "singular": "ко́лоса",
              "plural": "колоскі́в / коло́сся"
            },
            "давальний": {
              "singular": "ко́лосові / ко́лосу",
              "plural": "колоска́м"
            },
            "знахідний": {
              "singular": "ко́лос",
              "plural": "колоски́"
            },
            "орудний": {
              "singular": "ко́лосом",
              "plural": "колоска́ми"
            },
            "місцевий": {
              "singular": "у ко́лосі",
              "plural": "у колоска́х"
            },
            "кличний": {
              "singular": "ко́лосе",
              "plural": "колоски́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "колосок",
            "суцвіття"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «коло́с» (наголос на другому складі: гігантська статуя або велетенська постать)."
    },
    {
      "lemma": "колос",
      "url_slug": "колос",
      "headword": "коло́с",
      "short_label": "велетень, гігант (B2)",
      "gloss": "colossus (statue of gigantic size, giant figure or entity)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[kɔˈɫɔs]",
        "source": "VESUM"
      },
      "stress": {
        "form": "коло́с",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "коло́с",
              "plural": "коло́си"
            },
            "родовий": {
              "singular": "коло́са",
              "plural": "коло́сів"
            },
            "давальний": {
              "singular": "коло́сові / коло́су",
              "plural": "коло́сам"
            },
            "знахідний": {
              "singular": "коло́са",
              "plural": "коло́сів"
            },
            "орудний": {
              "singular": "коло́сом",
              "plural": "коло́сами"
            },
            "місцевий": {
              "singular": "на коло́сі",
              "plural": "на коло́сах"
            },
            "кличний": {
              "singular": "коло́се",
              "plural": "коло́си"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "гігант",
            "велетень",
            "титан"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ко́лос» (наголос на першому складі: зернове суцвіття на стеблі)."
    }
  ],
  "бубон": [
    {
      "lemma": "бубон",
      "url_slug": "бубон",
      "headword": "бу́бон",
      "short_label": "музичний інструмент (B1)",
      "gloss": "tambourine, tambour (frame drum percussion instrument)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈbubɔn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "бу́бон",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "бу́бон",
              "plural": "бу́бни"
            },
            "родовий": {
              "singular": "бу́бна",
              "plural": "бу́бнів"
            },
            "давальний": {
              "singular": "бу́бнові / бу́бну",
              "plural": "бу́бнам"
            },
            "знахідний": {
              "singular": "бу́бон",
              "plural": "бу́бни"
            },
            "орудний": {
              "singular": "бу́бном",
              "plural": "бу́бнами"
            },
            "місцевий": {
              "singular": "у бу́бні",
              "plural": "у бу́бнах"
            },
            "кличний": {
              "singular": "бу́бне",
              "plural": "бу́бни"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "тамбурин",
            "бубонець"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «бубо́н» (наголос на другому складі: запалений лімфатичний вузол)."
    },
    {
      "lemma": "бубон",
      "url_slug": "бубон",
      "headword": "бубо́н",
      "short_label": "запалена залоза (C1)",
      "gloss": "bubo (inflamed and swollen lymph node, esp. groin/armpit)",
      "pos": "noun",
      "cefr": "C1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[buˈbɔn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "бубо́н",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "бубо́н",
              "plural": "бубо́ни"
            },
            "родовий": {
              "singular": "бубо́на",
              "plural": "бубо́нів"
            },
            "давальний": {
              "singular": "бубо́ну / бубо́нові",
              "plural": "бубо́нам"
            },
            "знахідний": {
              "singular": "бубо́н",
              "plural": "бубо́ни"
            },
            "орудний": {
              "singular": "бубо́ном",
              "plural": "бубо́нами"
            },
            "місцевий": {
              "singular": "у бубо́ні",
              "plural": "у бубо́нах"
            },
            "кличний": {
              "singular": "бубо́не",
              "plural": "бубо́ни"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "лімфаденіт",
            "пухлина"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «бу́бон» (наголос на першому складі: ударний музичний інструмент)."
    }
  ],
  "терен": [
    {
      "lemma": "терен",
      "url_slug": "терен",
      "headword": "те́рен",
      "short_label": "колючий кущ (B1)",
      "gloss": "blackthorn, sloe (spiny wild plum shrub Prunus spinosa)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈtɛrɛn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "те́рен",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "те́рен",
              "plural": "те́рни"
            },
            "родовий": {
              "singular": "те́рну",
              "plural": "те́рнів"
            },
            "давальний": {
              "singular": "те́рну / те́рнові",
              "plural": "те́рнам"
            },
            "знахідний": {
              "singular": "те́рен",
              "plural": "те́рни"
            },
            "орудний": {
              "singular": "те́рном",
              "plural": "те́рнами"
            },
            "місцевий": {
              "singular": "у те́рні",
              "plural": "у те́рнах"
            },
            "кличний": {
              "singular": "те́рне",
              "plural": "те́рни"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "тернина",
            "терновий кущ"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «тере́н» (наголос на другому складі: місцевість, територія або простір)."
    },
    {
      "lemma": "терен",
      "url_slug": "терен",
      "headword": "тере́н",
      "short_label": "територія, простір (B1)",
      "gloss": "territory, terrain, tract of land, field of activity",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[tɛˈrɛn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "тере́н",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "тере́н",
              "plural": "терени́"
            },
            "родовий": {
              "singular": "тере́ну",
              "plural": "терені́в"
            },
            "давальний": {
              "singular": "тере́ну / тере́нові",
              "plural": "терена́м"
            },
            "знахідний": {
              "singular": "тере́н",
              "plural": "терени́"
            },
            "орудний": {
              "singular": "тере́ном",
              "plural": "терена́ми"
            },
            "місцевий": {
              "singular": "на тере́ні",
              "plural": "на терена́х"
            },
            "кличний": {
              "singular": "тере́не",
              "plural": "терени́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "територія",
            "місцевість",
            "земля"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «те́рен» (наголос на першому складі: колючий чагарник із синіми ягодами)."
    }
  ],
  "артикул": [
    {
      "lemma": "артикул",
      "url_slug": "артикул",
      "headword": "арти́кул",
      "short_label": "тип товару / стаття (B2)",
      "gloss": "article, clause, SKU, product code or commodity type",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ɐrˈtɪkuɫ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "арти́кул",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "арти́кул",
              "plural": "арти́кули"
            },
            "родовий": {
              "singular": "арти́кулу",
              "plural": "арти́кулів"
            },
            "давальний": {
              "singular": "арти́кулу / арти́кулові",
              "plural": "арти́кулам"
            },
            "знахідний": {
              "singular": "арти́кул",
              "plural": "арти́кули"
            },
            "орудний": {
              "singular": "арти́кулом",
              "plural": "арти́кулами"
            },
            "місцевий": {
              "singular": "в арти́кулі",
              "plural": "в арти́кулах"
            },
            "кличний": {
              "singular": "арти́куле",
              "plural": "арти́кули"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "параграф",
            "стаття",
            "номенклатура"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «артику́л» (наголос на останньому складі: військова вправа зі зброєю)."
    },
    {
      "lemma": "артикул",
      "url_slug": "артикул",
      "headword": "артику́л",
      "short_label": "військовий прийом зі зброєю (C1)",
      "gloss": "manual of arms, firearm drill movement",
      "pos": "noun",
      "cefr": "C1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ɐrtɪˈkuɫ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "артику́л",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "артику́л",
              "plural": "артику́ли"
            },
            "родовий": {
              "singular": "артику́лу",
              "plural": "артику́лів"
            },
            "давальний": {
              "singular": "артику́лу / артику́лові",
              "plural": "артику́лам"
            },
            "знахідний": {
              "singular": "артику́л",
              "plural": "артику́ли"
            },
            "орудний": {
              "singular": "артику́лом",
              "plural": "артику́лами"
            },
            "місцевий": {
              "singular": "в артику́лі",
              "plural": "в артику́лах"
            },
            "кличний": {
              "singular": "артику́ле",
              "plural": "артику́ли"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "стройовий прийом",
            "вправа з рушницею"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «арти́кул» (наголос на другому складі: стаття або товарний код)."
    }
  ],
  "вирок": [
    {
      "lemma": "вирок",
      "url_slug": "вирок",
      "headword": "ви́рок",
      "short_label": "судове рішення (B1)",
      "gloss": "verdict, court sentence, judicial decision on guilt/penalty",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwɪrɔk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́рок",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ви́рок",
              "plural": "ви́роки"
            },
            "родовий": {
              "singular": "ви́року",
              "plural": "ви́років"
            },
            "давальний": {
              "singular": "ви́року / ви́рокові",
              "plural": "ви́рокам"
            },
            "знахідний": {
              "singular": "ви́рок",
              "plural": "ви́роки"
            },
            "орудний": {
              "singular": "ви́роком",
              "plural": "ви́роками"
            },
            "місцевий": {
              "singular": "у ви́року",
              "plural": "у ви́роках"
            },
            "кличний": {
              "singular": "ви́року",
              "plural": "ви́роки"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "рішення суду",
            "ухвала",
            "присуд"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «виро́к» (наголос на другому складі: коловорот води або вир)."
    },
    {
      "lemma": "вирок",
      "url_slug": "вирок",
      "headword": "виро́к",
      "short_label": "малий вир у воді (B2)",
      "gloss": "little whirlpool, vortex, eddy (diminutive of вир)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wɪˈrɔk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "виро́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "виро́к",
              "plural": "вирки́"
            },
            "родовий": {
              "singular": "вирка́ / вирку́",
              "plural": "виркі́в"
            },
            "давальний": {
              "singular": "вирку́ / вирко́ві",
              "plural": "вирка́м"
            },
            "знахідний": {
              "singular": "виро́к",
              "plural": "вирки́"
            },
            "орудний": {
              "singular": "вирко́м",
              "plural": "вирка́ми"
            },
            "місцевий": {
              "singular": "у вирку́",
              "plural": "у вирка́х"
            },
            "кличний": {
              "singular": "вирку́",
              "plural": "вирки́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "вир",
            "коловорот",
            "водоворот"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ви́рок» (наголос на першому складі: судова ухвала про покарання)."
    }
  ],
  "варений": [
    {
      "lemma": "варений",
      "url_slug": "варений",
      "headword": "ва́рений",
      "short_label": "дієприкметник (зварений, A2)",
      "gloss": "boiled, cooked (passive past participle of варити)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwɑrɛnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ва́рений",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієприкметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з якісним прикметником «варе́ний» (наголос на другому складі: який зазнав термічної обробки)."
    },
    {
      "lemma": "варений",
      "url_slug": "варений",
      "headword": "варе́ний",
      "short_label": "прикметник (A2)",
      "gloss": "boiled (adjective: prepared by boiling, e.g. варене м'ясо)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wɐˈrɛnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "варе́ний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з дієприкметником «ва́рений» (наголос на першому складі)."
    }
  ],
  "ремінь": [
    {
      "lemma": "ремінь",
      "url_slug": "ремінь",
      "headword": "ре́мінь",
      "short_label": "пояс для одягу (A2)",
      "gloss": "leather belt, waist strap, harness band",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈrɛmʲinʲ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ре́мінь",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ре́мінь",
              "plural": "ре́мені"
            },
            "родовий": {
              "singular": "ре́меня",
              "plural": "ре́менів"
            },
            "давальний": {
              "singular": "ре́меневі / ре́меню",
              "plural": "ре́меням"
            },
            "знахідний": {
              "singular": "ре́мінь",
              "plural": "ре́мені"
            },
            "орудний": {
              "singular": "ре́менем",
              "plural": "ре́менями"
            },
            "місцевий": {
              "singular": "на ре́мені",
              "plural": "на ре́менях"
            },
            "кличний": {
              "singular": "ре́меню",
              "plural": "ре́мені"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "пояс",
            "пасок"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ремі́нь» (наголос на другому складі: вичинена шкіра або сировина)."
    },
    {
      "lemma": "ремінь",
      "url_slug": "ремінь",
      "headword": "ремі́нь",
      "short_label": "вичинена шкіра (матеріал, B2)",
      "gloss": "dressed leather, hide material, shoemaker's leather goods",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[rɛˈmʲinʲ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ремі́нь",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ремі́нь",
              "plural": "ремені́"
            },
            "родовий": {
              "singular": "ременю́",
              "plural": "ремені́в"
            },
            "давальний": {
              "singular": "ременю́ / ремене́ві",
              "plural": "ременя́м"
            },
            "знахідний": {
              "singular": "ремі́нь",
              "plural": "ремені́"
            },
            "орудний": {
              "singular": "ременем́",
              "plural": "ременя́ми"
            },
            "місцевий": {
              "singular": "у ремені́",
              "plural": "у ременя́х"
            },
            "кличний": {
              "singular": "ременю́",
              "plural": "ремені́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "шкіра",
            "юхта",
            "шевський товар"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ре́мінь» (наголос на першому складі: пояс або ремінець для штанів)."
    }
  ],
  "кулик": [
    {
      "lemma": "кулик",
      "url_slug": "кулик",
      "headword": "ку́лик",
      "short_label": "болотяний птах (B2)",
      "gloss": "snipe, sandpiper, wader (marsh or shore bird Charadrii)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈkulɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ку́лик",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ку́лик",
              "plural": "ку́лики"
            },
            "родовий": {
              "singular": "ку́лика",
              "plural": "ку́ликів"
            },
            "давальний": {
              "singular": "ку́ликові / ку́лику",
              "plural": "ку́ликам"
            },
            "знахідний": {
              "singular": "ку́лика",
              "plural": "ку́ликів"
            },
            "орудний": {
              "singular": "ку́ликом",
              "plural": "ку́ликами"
            },
            "місцевий": {
              "singular": "на ку́ликові",
              "plural": "на ку́ликах"
            },
            "кличний": {
              "singular": "ку́лику",
              "plural": "ку́лики"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "болотяний птах",
            "бекас"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «кули́к» (наголос на другому складі: невеликий мішечок або кульок)."
    },
    {
      "lemma": "кулик",
      "url_slug": "кулик",
      "headword": "кули́к",
      "short_label": "невеликий мішечок (B2)",
      "gloss": "small sack, small bag (diminutive of куль)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[kuˈlɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "кули́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "кули́к",
              "plural": "кулики́"
            },
            "родовий": {
              "singular": "кулика́",
              "plural": "куликі́в"
            },
            "давальний": {
              "singular": "кулику́ / кулико́ві",
              "plural": "кулика́м"
            },
            "знахідний": {
              "singular": "кули́к",
              "plural": "кулики́"
            },
            "орудний": {
              "singular": "кулико́м",
              "plural": "кулика́ми"
            },
            "місцевий": {
              "singular": "у кулику́",
              "plural": "у кулика́х"
            },
            "кличний": {
              "singular": "кулику́",
              "plural": "кулики́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "мішечок",
            "кульок",
            "торбинка"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ку́лик» (наголос на першому складі: болотяний перелітний птах)."
    }
  ],
  "малинівка": [
    {
      "lemma": "малинівка",
      "url_slug": "малинівка",
      "headword": "мали́нівка",
      "short_label": "пташка вільшанка (B2)",
      "gloss": "European robin (redbreast songbird Erithacus rubecula)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[mɐˈlɪnʲiu̯kɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "мали́нівка",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "мали́нівка",
              "plural": "мали́нівки"
            },
            "родовий": {
              "singular": "мали́нівки",
              "plural": "мали́нівок"
            },
            "давальний": {
              "singular": "мали́нівці",
              "plural": "мали́нівкам"
            },
            "знахідний": {
              "singular": "мали́нівку",
              "plural": "мали́нівок"
            },
            "орудний": {
              "singular": "мали́нівкою",
              "plural": "мали́нівками"
            },
            "місцевий": {
              "singular": "на мали́нівці",
              "plural": "на мали́нівках"
            },
            "кличний": {
              "singular": "мали́нівко",
              "plural": "мали́нівки"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "вільшанка",
            "пташка"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «малині́вка» (наголос на передостанньому складі: алкогольна настоянка на малині)."
    },
    {
      "lemma": "малинівка",
      "url_slug": "малинівка",
      "headword": "малині́вка",
      "short_label": "малинова настоянка (B2)",
      "gloss": "raspberry liqueur / brandy (sweet spirit infused with raspberries)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[mɐlɪˈnʲiu̯kɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "малині́вка",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "малині́вка",
              "plural": "малині́вки"
            },
            "родовий": {
              "singular": "малині́вки",
              "plural": "малині́вок"
            },
            "давальний": {
              "singular": "малині́вці",
              "plural": "малині́вкам"
            },
            "знахідний": {
              "singular": "малині́вку",
              "plural": "малині́вки"
            },
            "орудний": {
              "singular": "малині́вкою",
              "plural": "малині́вками"
            },
            "місцевий": {
              "singular": "у малині́вці",
              "plural": "у малині́вках"
            },
            "кличний": {
              "singular": "малині́вко",
              "plural": "малині́вки"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "наливка",
            "малинова настоянка"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «мали́нівка» (наголос на другому складі: співоча пташка вільшанка)."
    }
  ],
  "рудник": [
    {
      "lemma": "рудник",
      "url_slug": "рудник",
      "headword": "ру́дник",
      "short_label": "рудокоп, шахтар (B2)",
      "gloss": "miner, ore-digger (worker who extracts ore in a mine)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈrudnɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ру́дник",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ру́дник",
              "plural": "ру́дники"
            },
            "родовий": {
              "singular": "ру́дника",
              "plural": "ру́дників"
            },
            "давальний": {
              "singular": "ру́дникові / ру́днику",
              "plural": "ру́дникам"
            },
            "знахідний": {
              "singular": "ру́дника",
              "plural": "ру́дників"
            },
            "орудний": {
              "singular": "ру́дником",
              "plural": "ру́дниками"
            },
            "місцевий": {
              "singular": "на ру́дникові",
              "plural": "на ру́дниках"
            },
            "кличний": {
              "singular": "ру́днику",
              "plural": "ру́дники"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "рудокоп",
            "шахтар",
            "гірник"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «рудни́к» (наголос на другому складі: гірниче підприємство або шахта)."
    },
    {
      "lemma": "рудник",
      "url_slug": "рудник",
      "headword": "рудни́к",
      "short_label": "копальня, шахта (B1)",
      "gloss": "ore mine, pit (mining enterprise/excavation where ore is extracted)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[rudˈnɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "рудни́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "рудни́к",
              "plural": "рудники́"
            },
            "родовий": {
              "singular": "рудника́",
              "plural": "рудникі́в"
            },
            "давальний": {
              "singular": "руднику́ / руднико́ві",
              "plural": "рудника́м"
            },
            "знахідний": {
              "singular": "рудни́к",
              "plural": "рудники́"
            },
            "орудний": {
              "singular": "руднико́м",
              "plural": "рудника́ми"
            },
            "місцевий": {
              "singular": "на руднику́",
              "plural": "на рудника́х"
            },
            "кличний": {
              "singular": "руднику́",
              "plural": "рудники́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "копальня",
            "шахта",
            "рудня"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ру́дник» (наголос на першому складі: робітник-гірник, що добуває руду)."
    }
  ],
  "поділ": [
    {
      "lemma": "поділ",
      "url_slug": "поділ",
      "headword": "по́діл",
      "short_label": "розподіл, ділення (B1)",
      "gloss": "division, partition, distribution, apportionment",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈpɔdʲil]",
        "source": "VESUM"
      },
      "stress": {
        "form": "по́діл",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "по́діл",
              "plural": "по́діли"
            },
            "родовий": {
              "singular": "по́ділу",
              "plural": "по́ділів"
            },
            "давальний": {
              "singular": "по́ділу / по́ділові",
              "plural": "по́ділам"
            },
            "знахідний": {
              "singular": "по́діл",
              "plural": "по́діли"
            },
            "орудний": {
              "singular": "по́ділом",
              "plural": "по́ділами"
            },
            "місцевий": {
              "singular": "у по́ділі",
              "plural": "у по́ділах"
            },
            "кличний": {
              "singular": "по́діле",
              "plural": "по́діли"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "розподіл",
            "розмежування",
            "ділення"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «поді́л» (наголос на другому складі: низовина, поділ сукні чи район Києва)."
    },
    {
      "lemma": "поділ",
      "url_slug": "поділ",
      "headword": "поді́л",
      "short_label": "низ одягу / низовина (Поділ, B1)",
      "gloss": "garment hem, skirt bottom; lowland valley; Podil (historic Kyiv district)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[pɔˈdʲil]",
        "source": "VESUM"
      },
      "stress": {
        "form": "поді́л",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "поді́л",
              "plural": "подо́ли"
            },
            "родовий": {
              "singular": "подо́лу",
              "plural": "подо́лів"
            },
            "давальний": {
              "singular": "подо́лу / подо́лові",
              "plural": "подо́лам"
            },
            "знахідний": {
              "singular": "поді́л",
              "plural": "подо́ли"
            },
            "орудний": {
              "singular": "подо́лом",
              "plural": "подо́лами"
            },
            "місцевий": {
              "singular": "на подо́лі",
              "plural": "на подо́лах"
            },
            "кличний": {
              "singular": "подо́ле",
              "plural": "подо́ли"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "низ сукні",
            "низовина"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «по́діл» (наголос на першому складі: акт розмежування або розподілу частин)."
    }
  ],
  "зимівник": [
    {
      "lemma": "зимівник",
      "url_slug": "зимівник",
      "headword": "зимі́вник",
      "short_label": "зимувальник (людина, B2)",
      "gloss": "winterer (person who spends the winter on an expedition/remote outpost)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[zɪˈmʲiu̯nɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "зимі́вник",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "зимі́вник",
              "plural": "зимі́вники"
            },
            "родовий": {
              "singular": "зимі́вника",
              "plural": "зимі́вників"
            },
            "давальний": {
              "singular": "зимі́вникові / зимі́внику",
              "plural": "зимі́вникам"
            },
            "знахідний": {
              "singular": "зимі́вника",
              "plural": "зимі́вників"
            },
            "орудний": {
              "singular": "зимі́вником",
              "plural": "зимі́вниками"
            },
            "місцевий": {
              "singular": "на зимі́вникові",
              "plural": "на зимі́вниках"
            },
            "кличний": {
              "singular": "зимі́внику",
              "plural": "зимі́вники"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "зимувальник",
            "полярник"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «зимівни́к» (наголос на останньому складі: козацький хутір або приміщення для зимівлі)."
    },
    {
      "lemma": "зимівник",
      "url_slug": "зимівник",
      "headword": "зимівни́к",
      "short_label": "козацький хутір / зимівля (B2)",
      "gloss": "winter quarters, Cossack winter homestead, livestock shelter",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[zɪmʲiu̯ˈnɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "зимівни́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "зимівни́к",
              "plural": "зимівники́"
            },
            "родовий": {
              "singular": "зимівника́",
              "plural": "зимівникі́в"
            },
            "давальний": {
              "singular": "зимівнику́ / зимівнико́ві",
              "plural": "зимівника́м"
            },
            "знахідний": {
              "singular": "зимівни́к",
              "plural": "зимівники́"
            },
            "орудний": {
              "singular": "зимівнико́м",
              "plural": "зимівника́ми"
            },
            "місцевий": {
              "singular": "у зимівнику́",
              "plural": "у зимівника́х"
            },
            "кличний": {
              "singular": "зимівнику́",
              "plural": "зимівники́"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "хутір",
            "зимівля",
            "козацьке поселення"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «зимі́вник» (наголос на другому складі: людина, яка проводить зимівлю)."
    }
  ],
  "нізвідки": [
    {
      "lemma": "нізвідки",
      "url_slug": "нізвідки",
      "headword": "ні́звідки",
      "short_label": "немає звідки взяти (B1)",
      "gloss": "there is nowhere to get from, no source available (predicative)",
      "pos": "adverb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈnʲizwʲidkɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ні́звідки",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник / предикатив",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «нізві́дки» (наголос на другому складі: з жодного місця, нізвідкіля)."
    },
    {
      "lemma": "нізвідки",
      "url_slug": "нізвідки",
      "headword": "нізві́дки",
      "short_label": "з жодного місця (B1)",
      "gloss": "from nowhere, out of thin air, from no location",
      "pos": "adverb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[nʲizˈwʲidkɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "нізві́дки",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «ні́звідки» (наголос на першому складі: немає джерела, звідки щось узяти)."
    }
  ],
  "ніяк": [
    {
      "lemma": "ніяк",
      "url_slug": "ніяк",
      "headword": "ні́як",
      "short_label": "немає можливості (A2)",
      "gloss": "there is no way to do it, impossible (predicative)",
      "pos": "adverb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈnʲijɑk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ні́як",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник / предикатив",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «нія́к» (наголос на другому складі: жодним чином, зовсім не)."
    },
    {
      "lemma": "ніяк",
      "url_slug": "ніяк",
      "headword": "нія́к",
      "short_label": "жодним чином (A2)",
      "gloss": "in no way, by no means, not at all",
      "pos": "adverb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[nʲiˈjɑk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "нія́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «ні́як» (наголос на першому складі: немає способу щось здійснити)."
    }
  ],
  "значити": [
    {
      "lemma": "значити",
      "url_slug": "значити",
      "headword": "зна́чити",
      "short_label": "мати значення (B1)",
      "gloss": "to mean, signify, denote, matter (to have importance/sense)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈznɑt͡ʃɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "зна́чити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «значи́ти» (наголос на другому складі: ставити позначки, мітки на деревах чи товарах)."
    },
    {
      "lemma": "значити",
      "url_slug": "значити",
      "headword": "значи́ти",
      "short_label": "ставити мітки (позначати, B2)",
      "gloss": "to mark, tag, label, brand (make visible marks on timber, cattle, etc.)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[znɐˈt͡ʃɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "значи́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «зна́чити» (наголос на першому складі: мати зміст або значення)."
    }
  ],
  "пахнути": [
    {
      "lemma": "пахнути",
      "url_slug": "пахнути",
      "headword": "па́хнути",
      "short_label": "мати запах (недок., B1)",
      "gloss": "to smell, have an aroma, emit fragrance (continuous state)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈpɑxnʊtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "па́хнути",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «пахну́ти» (наголос на суфіксі: раптово повіяти або війнути запахом)."
    },
    {
      "lemma": "пахнути",
      "url_slug": "пахнути",
      "headword": "пахну́ти",
      "short_label": "раптово повіяти / війнути (док., B2)",
      "gloss": "to waft, blow once, puff suddenly with wind or scent (semelfactive)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[pɐxˈnutɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пахну́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «па́хнути» (наголос на першому складі: виділяти запах, пахощі)."
    }
  ],
  "викидати": [
    {
      "lemma": "викидати",
      "url_slug": "викидати",
      "headword": "викида́ти",
      "short_label": "викидати назовні (недок., B1)",
      "gloss": "to throw out, discard, get rid of (habitual/continuous action)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wɪkɪˈdɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "викида́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «ви́кидати» (наголос на префіксі: викинути все геть за кілька разів)."
    },
    {
      "lemma": "викидати",
      "url_slug": "викидати",
      "headword": "ви́кидати",
      "short_label": "викинути все геть (док., B2)",
      "gloss": "to throw out all/everything, discard completely (cumulative completed action)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwɪkɪdɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́кидати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «викида́ти» (наголос на суфіксі: позбуватися речей)."
    }
  ],
  "вибігати": [
    {
      "lemma": "вибігати",
      "url_slug": "вибігати",
      "headword": "вибіга́ти",
      "short_label": "вибігати звідкись (недок., B1)",
      "gloss": "to run out, emerge running (continuous/habitual running out)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wɪbʲiˈɦɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "вибіга́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «ви́бігати» (наголос на префіксі: здобути щось клопотами й біганиною)."
    },
    {
      "lemma": "вибігати",
      "url_slug": "вибігати",
      "headword": "ви́бігати",
      "short_label": "здобути біганиною (док., B2)",
      "gloss": "to run all over, obtain by tireless running or exhaust through running",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwɪbʲiɦɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́бігати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «вибіга́ти» (наголос на суфіксі: бігом залишати приміщення)."
    }
  ],
  "збігати": [
    {
      "lemma": "збігати",
      "url_slug": "збігати",
      "headword": "збіга́ти",
      "short_label": "спускатися бігом / минати (недок., B1)",
      "gloss": "to run down, elapse (of time), boil over (liquids)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[zbʲiˈɦɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "збіга́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «збі́гати» (наголос на префіксі: швидко піти кудись і повернутися)."
    },
    {
      "lemma": "збігати",
      "url_slug": "збігати",
      "headword": "збі́гати",
      "short_label": "сходити туди й назад (док., B1)",
      "gloss": "to make a quick trip and return, pop over somewhere quickly",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈzbʲiɦɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "збі́гати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «збіга́ти» (наголос на суфіксі: спускатися бігом або спливати про час)."
    }
  ],
  "заходити": [
    {
      "lemma": "заходити",
      "url_slug": "заходити",
      "headword": "захо́дити",
      "short_label": "проникати / заходити в гості (недок., A2)",
      "gloss": "to come in, enter, drop by, visit; to set (of celestial bodies)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[zɐˈxɔdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "захо́дити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «заходи́ти» (наголос на суфіксі: почати ходити туди-сюди або закрокувати)."
    },
    {
      "lemma": "заходити",
      "url_slug": "заходити",
      "headword": "заходи́ти",
      "short_label": "почати ходити (закрокувати, док., B2)",
      "gloss": "to begin walking, pace back and forth (inceptive completed action)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[zɐxɔˈdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "заходи́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «захо́дити» (наголос на корені: заходити в дім або сідати за горизонт)."
    }
  ],
  "переходити": [
    {
      "lemma": "переходити",
      "url_slug": "переходити",
      "headword": "перехо́дити",
      "short_label": "перетинати шлях (недок., A2)",
      "gloss": "to cross, pass over, transition across (habitual/continuous crossing)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[pɛrɛˈxɔdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "перехо́дити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «переходи́ти» (наголос на суфіксі: втомитися від надмірної ходьби)."
    },
    {
      "lemma": "переходити",
      "url_slug": "переходити",
      "headword": "переходи́ти",
      "short_label": "втомитися від ходьби (док., B2)",
      "gloss": "to walk excessively, tire out by walking, overwalk",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[pɛrɛxɔˈdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "переходи́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «перехо́дити» (наголос на корені: переходити дорогу або межу)."
    }
  ],
  "доходити": [
    {
      "lemma": "доходити",
      "url_slug": "доходити",
      "headword": "дохо́дити",
      "short_label": "досягати межі (недок., B1)",
      "gloss": "to reach, arrive at, attain, ripen gradually",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[dɔˈxɔdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "дохо́дити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «доходи́ти» (наголос на суфіксі: завершити ходіння або знесилитися)."
    },
    {
      "lemma": "доходити",
      "url_slug": "доходити",
      "headword": "доходи́ти",
      "short_label": "закінчити ходьбу (док., B2)",
      "gloss": "to finish walking, walk to the very end, exhaust by walking",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[dɔxɔˈdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "доходи́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «дохо́дити» (наголос на корені: діставатися пункту призначення)."
    }
  ],
  "відносити": [
    {
      "lemma": "відносити",
      "url_slug": "відносити",
      "headword": "відно́сити",
      "short_label": "нести кудись геть (недок., B1)",
      "gloss": "to carry away, bear off, refer to (continuous carrying)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wʲidˈnɔsɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відно́сити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «відноси́ти» (наголос на суфіксі: зносити одяг або завершити носити)."
    },
    {
      "lemma": "відносити",
      "url_slug": "відносити",
      "headword": "відноси́ти",
      "short_label": "зносити / завершити носити (док., B2)",
      "gloss": "to wear out (clothing), finish wearing, carry for a prescribed period",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wʲidnɔˈsɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відноси́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «відно́сити» (наголос на корені: переносити щось в інше місце)."
    }
  ],
  "відкидати": [
    {
      "lemma": "відкидати",
      "url_slug": "відкидати",
      "headword": "відкида́ти",
      "short_label": "відхиляти, не приймати (недок., B1)",
      "gloss": "to reject, cast aside, dismiss, discard (opinions, offers)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wʲidkɪˈdɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відкида́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «відки́дати» (наголос на корені: відкинути все лопатою за кілька прийомів)."
    },
    {
      "lemma": "відкидати",
      "url_slug": "відкидати",
      "headword": "відки́дати",
      "short_label": "відкинути все за кілька разів (док., B2)",
      "gloss": "to shovel away, throw off in batches (snow, soil; cumulative completed action)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwʲidkɪdɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відки́дати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «відкида́ти» (наголос на суфіксі: відхиляти пропозицію або сумніви)."
    }
  ],
  "сунути": [
    {
      "lemma": "сунути",
      "url_slug": "сунути",
      "headword": "су́нути",
      "short_label": "рухати, пересувати (недок., B1)",
      "gloss": "to shove, push, slide along, advance in a mass (continuous motion)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈsunʊtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "су́нути",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «суну́ти» (наголос на суфіксі: різко всунути або тицьнути щось)."
    },
    {
      "lemma": "сунути",
      "url_slug": "сунути",
      "headword": "суну́ти",
      "short_label": "швидко всунути / тицьнути (док., B2)",
      "gloss": "to shove once quickly, jab, thrust suddenly (semelfactive completed action)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[suˈnutɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "суну́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «су́нути» (наголос на корені: повільно пересувати щось або наступати)."
    }
  ]
};

export function getEffectiveHeteronyms(
  record: EntryRecord | null | undefined,
): LexiconEntry[] | null {
  if (record?.entry?.heteronyms && record.entry.heteronyms.length > 1) {
    return record.entry.heteronyms;
  }
  const slug = (record?.slug || record?.entry?.lemma || "").toLowerCase().trim();
  if (slug && CURATED_HETERONYMS[slug]) {
    return CURATED_HETERONYMS[slug];
  }
  return null;
}
