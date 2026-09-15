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
  ],
  "дякувати": [
    {
      "lemma": "дякувати",
      "url_slug": "дякувати",
      "headword": "дя́кувати",
      "short_label": "дякувати комусь (A1)",
      "gloss": "to thank, express gratitude, be grateful for something",
      "pos": "verb",
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
        "ipa": "[ˈdʲakuwɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "дя́кувати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «дякува́ти» (наголос на третьому складі: бути дяком, церковна посада)."
    },
    {
      "lemma": "дякувати",
      "url_slug": "дякувати",
      "headword": "дякува́ти",
      "short_label": "бути дяком (розм., рідко)",
      "gloss": "to serve as a church deacon (regional, rare)",
      "pos": "verb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[dʲɐkuˈwatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "дякува́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «дя́кувати» (наголос на першому складі: висловлювати подяку)."
    }
  ],
  "кредит": [
    {
      "lemma": "кредит",
      "url_slug": "кредит",
      "headword": "кре́дит",
      "short_label": "бухгалтерський термін (спец., B2)",
      "gloss": "credit (accounting: the credit side of a ledger account, opposite of debit)",
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
        "ipa": "[ˈkrɛdɪt]",
        "source": "VESUM"
      },
      "stress": {
        "form": "кре́дит",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "кре́дит",
              "plural": "кре́дити"
            },
            "родовий": {
              "singular": "кре́диту",
              "plural": "кре́дитів"
            },
            "давальний": {
              "singular": "кре́диту / кре́дитові",
              "plural": "кре́дитам"
            },
            "знахідний": {
              "singular": "кре́дит",
              "plural": "кре́дити"
            },
            "орудний": {
              "singular": "кре́дитом",
              "plural": "кре́дитами"
            },
            "місцевий": {
              "singular": "(у) кре́диті",
              "plural": "кре́дитах"
            },
            "кличний": {
              "singular": "кре́дите",
              "plural": "кре́дити"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "дебет (протилежне)"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «креди́т» (наголос на другому складі: позика, надання в борг)."
    },
    {
      "lemma": "кредит",
      "url_slug": "кредит",
      "headword": "креди́т",
      "short_label": "позика, надання в борг (A2)",
      "gloss": "credit, loan (money or goods lent, to be repaid)",
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
        "ipa": "[krɛˈdɪt]",
        "source": "VESUM"
      },
      "stress": {
        "form": "креди́т",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "креди́т",
              "plural": "креди́ти"
            },
            "родовий": {
              "singular": "креди́ту",
              "plural": "креди́тів"
            },
            "давальний": {
              "singular": "креди́ту / креди́тові",
              "plural": "креди́там"
            },
            "знахідний": {
              "singular": "креди́т",
              "plural": "креди́ти"
            },
            "орудний": {
              "singular": "креди́том",
              "plural": "креди́тами"
            },
            "місцевий": {
              "singular": "(у) креди́ті",
              "plural": "креди́тах"
            },
            "кличний": {
              "singular": "креди́те",
              "plural": "креди́ти"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "позика",
            "заборгованість"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «кре́дит» (наголос на першому складі: бухгалтерський термін)."
    }
  ],
  "набір": [
    {
      "lemma": "набір",
      "url_slug": "набір",
      "headword": "на́бір",
      "short_label": "у борг (діал., розм.)",
      "gloss": "on credit, without paying immediately (dialectal adverb)",
      "pos": "adverb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈnabʲir]",
        "source": "VESUM"
      },
      "stress": {
        "form": "на́бір",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «набі́р» (наголос на другому складі: комплект або зарахування)."
    },
    {
      "lemma": "набір",
      "url_slug": "набір",
      "headword": "набі́р",
      "short_label": "комплект, зарахування (A2)",
      "gloss": "set, kit, collection; recruitment, enrollment (of workers/students)",
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
        "ipa": "[nɐˈbʲir]",
        "source": "VESUM"
      },
      "stress": {
        "form": "набі́р",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "набі́р",
              "plural": "набо́ри"
            },
            "родовий": {
              "singular": "набо́ру",
              "plural": "набо́рів"
            },
            "давальний": {
              "singular": "набо́ру / набо́рові",
              "plural": "набо́рам"
            },
            "знахідний": {
              "singular": "набі́р",
              "plural": "набо́ри"
            },
            "орудний": {
              "singular": "набо́ром",
              "plural": "набо́рами"
            },
            "місцевий": {
              "singular": "(у) набо́рі",
              "plural": "набо́рах"
            },
            "кличний": {
              "singular": "набо́ре",
              "plural": "набо́ри"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "комплект",
            "набор (рос. калька — уникати)"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «на́бір» (наголос на першому складі: у борг, без грошей; діал.)."
    }
  ],
  "обладнання": [
    {
      "lemma": "обладнання",
      "url_slug": "обладнання",
      "headword": "обла́днання",
      "short_label": "устаткування (A1)",
      "gloss": "equipment, machinery, apparatus (collective noun)",
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
        "ipa": "[ɔˈbɫadnɐnnʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "обла́днання",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "обла́днання",
              "plural": "обла́днання"
            },
            "родовий": {
              "singular": "обла́днання",
              "plural": "обла́днань"
            },
            "давальний": {
              "singular": "обла́днанню",
              "plural": "обла́днанням"
            },
            "знахідний": {
              "singular": "обла́днання",
              "plural": "обла́днання"
            },
            "орудний": {
              "singular": "обла́днанням",
              "plural": "обла́днаннями"
            },
            "місцевий": {
              "singular": "обла́днанні",
              "plural": "обла́днаннях"
            },
            "кличний": {
              "singular": "обла́днання",
              "plural": "обла́днання"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «обладна́ння» (наголос на третьому складі: дія — облаштування приміщення)."
    },
    {
      "lemma": "обладнання",
      "url_slug": "обладнання",
      "headword": "обладна́ння",
      "short_label": "дія: облаштування (B2)",
      "gloss": "the act of equipping, outfitting, fitting out (a workplace, room)",
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
        "ipa": "[ɔbɫɐˈdnannʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "обладна́ння",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "обладна́ння",
              "plural": "обладна́ння"
            },
            "родовий": {
              "singular": "обладна́ння",
              "plural": "обладна́нь"
            },
            "давальний": {
              "singular": "обладна́нню",
              "plural": "обладна́нням"
            },
            "знахідний": {
              "singular": "обладна́ння",
              "plural": "обладна́ння"
            },
            "орудний": {
              "singular": "обладна́нням",
              "plural": "обладна́ннями"
            },
            "місцевий": {
              "singular": "обладна́нні",
              "plural": "обладна́ннях"
            },
            "кличний": {
              "singular": "обладна́ння",
              "plural": "обладна́ння"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «обла́днання» (наголос на другому складі: устаткування, механізми)."
    }
  ],
  "послухати": [
    {
      "lemma": "послухати",
      "url_slug": "послухати",
      "headword": "послу́хати",
      "short_label": "вислухати (A1)",
      "gloss": "to listen to, hear out; to examine by listening (e.g. with a stethoscope)",
      "pos": "verb",
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
        "ipa": "[pɔˈsɫuxɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "послу́хати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «послуха́ти» (наголос на третьому складі: слухатися, заст.)."
    },
    {
      "lemma": "послухати",
      "url_slug": "послухати",
      "headword": "послуха́ти",
      "short_label": "слухатися (заст.)",
      "gloss": "to obey, listen to and follow (archaic imperfective)",
      "pos": "verb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[pɔsɫuˈxatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "послуха́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «послу́хати» (наголос на другому складі: вислухати кого-небудь)."
    }
  ],
  "речення": [
    {
      "lemma": "речення",
      "url_slug": "речення",
      "headword": "ре́чення",
      "short_label": "граматична одиниця (A1)",
      "gloss": "sentence (grammatical unit)",
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
        "ipa": "[ˈrɛt͡ʃɛnnʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ре́чення",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ре́чення",
              "plural": "ре́чення"
            },
            "родовий": {
              "singular": "ре́чення",
              "plural": "ре́чень"
            },
            "давальний": {
              "singular": "ре́ченню",
              "plural": "ре́ченням"
            },
            "знахідний": {
              "singular": "ре́чення",
              "plural": "ре́чення"
            },
            "орудний": {
              "singular": "ре́ченням",
              "plural": "ре́ченнями"
            },
            "місцевий": {
              "singular": "ре́ченні",
              "plural": "ре́ченнях"
            },
            "кличний": {
              "singular": "ре́чення",
              "plural": "ре́чення"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «рече́ння» (наголос на другому складі: короткий вислів, рідко)."
    },
    {
      "lemma": "речення",
      "url_slug": "речення",
      "headword": "рече́ння",
      "short_label": "короткий вислів (рідко)",
      "gloss": "a brief expression, a short set of words forming a saying (rare)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[rɛˈt͡ʃɛnnʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "рече́ння",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "рече́ння",
              "plural": "рече́ння"
            },
            "родовий": {
              "singular": "рече́ння",
              "plural": "рече́нь"
            },
            "давальний": {
              "singular": "рече́нню",
              "plural": "рече́нням"
            },
            "знахідний": {
              "singular": "рече́ння",
              "plural": "рече́ння"
            },
            "орудний": {
              "singular": "рече́нням",
              "plural": "рече́ннями"
            },
            "місцевий": {
              "singular": "рече́нні",
              "plural": "рече́ннях"
            },
            "кличний": {
              "singular": "рече́ння",
              "plural": "рече́ння"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «ре́чення» (наголос на першому складі: граматичне речення)."
    }
  ],
  "розмір": [
    {
      "lemma": "розмір",
      "url_slug": "розмір",
      "headword": "ро́змір",
      "short_label": "величина, номер одягу (A1)",
      "gloss": "size, dimension; measurement (of clothing, shoes, quantities)",
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
        "ipa": "[ˈrɔzmʲir]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ро́змір",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ро́змір",
              "plural": "ро́зміри"
            },
            "родовий": {
              "singular": "ро́зміру",
              "plural": "ро́змірів"
            },
            "давальний": {
              "singular": "ро́зміру / ро́змірові",
              "plural": "ро́змірам"
            },
            "знахідний": {
              "singular": "ро́змір",
              "plural": "ро́зміри"
            },
            "орудний": {
              "singular": "ро́зміром",
              "plural": "ро́змірами"
            },
            "місцевий": {
              "singular": "(у) ро́змірі",
              "plural": "ро́змірах"
            },
            "кличний": {
              "singular": "ро́зміре",
              "plural": "ро́зміри"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «розмі́р» (наголос на другому складі: частка борошна за помел, заст., діал.)."
    },
    {
      "lemma": "розмір",
      "url_slug": "розмір",
      "headword": "розмі́р",
      "short_label": "частка за помел (заст., діал.)",
      "gloss": "miller's toll (a portion of ground grain kept as payment)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[rɔˈzmʲir]",
        "source": "VESUM"
      },
      "stress": {
        "form": "розмі́р",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "розмі́р",
              "plural": "розмі́ри"
            },
            "родовий": {
              "singular": "розмі́ру",
              "plural": "розмі́рів"
            },
            "давальний": {
              "singular": "розмі́ру / розмі́рові",
              "plural": "розмі́рам"
            },
            "знахідний": {
              "singular": "розмі́р",
              "plural": "розмі́ри"
            },
            "орудний": {
              "singular": "розмі́ром",
              "plural": "розмі́рами"
            },
            "місцевий": {
              "singular": "(у) розмі́рі",
              "plural": "розмі́рах"
            },
            "кличний": {
              "singular": "розмі́ре",
              "plural": "розмі́ри"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «ро́змір» (наголос на першому складі: величина, номер одягу)."
    }
  ],
  "транспорт": [
    {
      "lemma": "транспорт",
      "url_slug": "транспорт",
      "headword": "тра́нспорт",
      "short_label": "перевезення (A1)",
      "gloss": "transport, transportation (means of conveyance; industry)",
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
        "ipa": "[ˈtranspɔrt]",
        "source": "VESUM"
      },
      "stress": {
        "form": "тра́нспорт",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "тра́нспорт",
              "plural": "тра́нспорти"
            },
            "родовий": {
              "singular": "тра́нспорту",
              "plural": "тра́нспортів"
            },
            "давальний": {
              "singular": "тра́нспорту / тра́нспортові",
              "plural": "тра́нспортам"
            },
            "знахідний": {
              "singular": "тра́нспорт",
              "plural": "тра́нспорти"
            },
            "орудний": {
              "singular": "тра́нспортом",
              "plural": "тра́нспортами"
            },
            "місцевий": {
              "singular": "(у) тра́нспорті",
              "plural": "тра́нспортах"
            },
            "кличний": {
              "singular": "тра́нспорте",
              "plural": "тра́нспорти"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «транспо́рт» (наголос на другому складі: бухгалтерський термін)."
    },
    {
      "lemma": "транспорт",
      "url_slug": "транспорт",
      "headword": "транспо́рт",
      "short_label": "бухгалтерський термін (C1)",
      "gloss": "carry-over (of a sum to the next page, in bookkeeping)",
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
        "ipa": "[trɐˈnspɔrt]",
        "source": "VESUM"
      },
      "stress": {
        "form": "транспо́рт",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "транспо́рт",
              "plural": "транспо́рти"
            },
            "родовий": {
              "singular": "транспо́рту",
              "plural": "транспо́ртів"
            },
            "давальний": {
              "singular": "транспо́рту / транспо́ртові",
              "plural": "транспо́ртам"
            },
            "знахідний": {
              "singular": "транспо́рт",
              "plural": "транспо́рти"
            },
            "орудний": {
              "singular": "транспо́ртом",
              "plural": "транспо́ртами"
            },
            "місцевий": {
              "singular": "(у) транспо́рті",
              "plural": "транспо́ртах"
            },
            "кличний": {
              "singular": "транспо́рте",
              "plural": "транспо́рти"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «тра́нспорт» (наголос на першому складі: перевезення, транспортна галузь)."
    }
  ],
  "тікати": [
    {
      "lemma": "тікати",
      "url_slug": "тікати",
      "headword": "ті́кати",
      "short_label": "цокати, про годинник (розм.)",
      "gloss": "to tick (of a clock or clockwork mechanism)",
      "pos": "verb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈtʲikɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ті́кати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «тіка́ти» (наголос на другому складі: утікати, рятуватися втечею)."
    },
    {
      "lemma": "тікати",
      "url_slug": "тікати",
      "headword": "тіка́ти",
      "short_label": "утікати (A2)",
      "gloss": "to run away, flee, escape",
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
        "ipa": "[tʲiˈkatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "тіка́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «ті́кати» (наголос на першому складі: рівномірно постукувати, про годинник)."
    }
  ],
  "західний": [
    {
      "lemma": "західний",
      "url_slug": "західний",
      "headword": "за́хідний",
      "short_label": "стосується заходу-сторони світу (A2)",
      "gloss": "western, pertaining to the west (compass direction)",
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
        "ipa": "[ˈzaxʲidnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "за́хідний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «захі́дний» (наголос на другому складі: призахідний, про сонце, діал.)."
    },
    {
      "lemma": "західний",
      "url_slug": "західний",
      "headword": "захі́дний",
      "short_label": "призахідний, про сонце (діал.)",
      "gloss": "pertaining to sunset, west-facing (of the setting sun; dialectal)",
      "pos": "adjective",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[zɐˈxʲidnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "захі́дний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «за́хідний» (наголос на першому складі: стосується заходу-сторони світу)."
    }
  ],
  "основний": [
    {
      "lemma": "основний",
      "url_slug": "основний",
      "headword": "осно́вний",
      "short_label": "хімічний термін: лужний (спец., B2)",
      "gloss": "basic (chemistry: alkaline, opposite of acidic); pertaining to warp threads (weaving)",
      "pos": "adjective",
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
        "ipa": "[ɔˈsnɔwnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "осно́вний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «основни́й» (наголос на третьому складі: головний, найважливіший)."
    },
    {
      "lemma": "основний",
      "url_slug": "основний",
      "headword": "основни́й",
      "short_label": "головний, найважливіший (A2)",
      "gloss": "main, primary, fundamental",
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
        "ipa": "[ɔsnɔˈwnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "основни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «осно́вний» (наголос на другому складі: хімічний термін «лужний», спец.)."
    }
  ],
  "переїзд": [
    {
      "lemma": "переїзд",
      "url_slug": "переїзд",
      "headword": "пере́їзд",
      "short_label": "залізничний переїзд (B1)",
      "gloss": "crossing point, level crossing (where a road crosses a railway)",
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
        "ipa": "[pɛˈrɛjizd]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пере́їзд",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "пере́їзд",
              "plural": "пере́їзди"
            },
            "родовий": {
              "singular": "пере́їзду",
              "plural": "пере́їздів"
            },
            "давальний": {
              "singular": "пере́їзду / пере́їздові",
              "plural": "пере́їздам"
            },
            "знахідний": {
              "singular": "пере́їзд",
              "plural": "пере́їзди"
            },
            "орудний": {
              "singular": "пере́їздом",
              "plural": "пере́їздами"
            },
            "місцевий": {
              "singular": "(у) пере́їзді",
              "plural": "пере́їздах"
            },
            "кличний": {
              "singular": "пере́їзде",
              "plural": "пере́їзди"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «переї́зд» (наголос на третьому складі: переселення, переїзд до нового дому)."
    },
    {
      "lemma": "переїзд",
      "url_slug": "переїзд",
      "headword": "переї́зд",
      "short_label": "переселення (A2)",
      "gloss": "the act of moving, relocating (to a new home, city)",
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
        "ipa": "[pɛrɛˈjizd]",
        "source": "VESUM"
      },
      "stress": {
        "form": "переї́зд",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "переї́зд",
              "plural": "переї́зди"
            },
            "родовий": {
              "singular": "переї́зду",
              "plural": "переї́здів"
            },
            "давальний": {
              "singular": "переї́зду / переї́здові",
              "plural": "переї́здам"
            },
            "знахідний": {
              "singular": "переї́зд",
              "plural": "переї́зди"
            },
            "орудний": {
              "singular": "переї́здом",
              "plural": "переї́здами"
            },
            "місцевий": {
              "singular": "(у) переї́зді",
              "plural": "переї́здах"
            },
            "кличний": {
              "singular": "переї́зде",
              "plural": "переї́зди"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «пере́їзд» (наголос на другому складі: місце перетину дороги й залізниці)."
    }
  ],
  "послуга": [
    {
      "lemma": "послуга",
      "url_slug": "послуга",
      "headword": "по́слуга",
      "short_label": "допомога, сервіс (A2)",
      "gloss": "service, favor (a helpful act done for someone)",
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
        "ipa": "[ˈpɔsɫuɦɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "по́слуга",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "по́слуга",
              "plural": "по́слуги"
            },
            "родовий": {
              "singular": "по́слуги",
              "plural": "по́слуг"
            },
            "давальний": {
              "singular": "по́слузі",
              "plural": "по́слугам"
            },
            "знахідний": {
              "singular": "по́слугу",
              "plural": "по́слуги"
            },
            "орудний": {
              "singular": "по́слугою",
              "plural": "по́слугами"
            },
            "місцевий": {
              "singular": "по́слузі",
              "plural": "по́слугах"
            },
            "кличний": {
              "singular": "по́слуго",
              "plural": "по́слуги"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "допомога",
            "сприяння"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «послу́га» (наголос на другому складі: служіння, заст.)."
    },
    {
      "lemma": "послуга",
      "url_slug": "послуга",
      "headword": "послу́га",
      "short_label": "служіння (заст.)",
      "gloss": "servitude, service in an old subordinate sense (archaic)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[pɔˈsɫuɦɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "послу́га",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "послу́га",
              "plural": "послу́ги"
            },
            "родовий": {
              "singular": "послу́ги",
              "plural": "послу́г"
            },
            "давальний": {
              "singular": "послу́зі",
              "plural": "послу́гам"
            },
            "знахідний": {
              "singular": "послу́гу",
              "plural": "послу́ги"
            },
            "орудний": {
              "singular": "послу́гою",
              "plural": "послу́гами"
            },
            "місцевий": {
              "singular": "послу́зі",
              "plural": "послу́гах"
            },
            "кличний": {
              "singular": "послу́го",
              "plural": "послу́ги"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «по́слуга» (наголос на першому складі: допомога, сервіс)."
    }
  ],
  "правильний": [
    {
      "lemma": "правильний",
      "url_slug": "правильний",
      "headword": "пра́вильний",
      "short_label": "вірний, безпомилковий (A2)",
      "gloss": "correct, right; regular",
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
        "ipa": "[ˈprawɪɫʲnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пра́вильний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «прави́льний» (наголос на другому складі: технічний термін — вирівнювальний, спец.)."
    },
    {
      "lemma": "правильний",
      "url_slug": "правильний",
      "headword": "прави́льний",
      "short_label": "технічний термін: вирівнювальний (спец., C1)",
      "gloss": "pertaining to leveling/straightening machinery (industrial term)",
      "pos": "adjective",
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
        "ipa": "[prɐˈwɪɫʲnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "прави́льний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «пра́вильний» (наголос на першому складі: вірний, безпомилковий)."
    }
  ],
  "пробувати": [
    {
      "lemma": "пробувати",
      "url_slug": "пробувати",
      "headword": "про́бувати",
      "short_label": "намагатися, випробовувати (A2)",
      "gloss": "to try, attempt, test",
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
        "ipa": "[ˈprɔbuwɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "про́бувати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «пробува́ти» (наголос на третьому складі: перебувати, мешкати десь тимчасово)."
    },
    {
      "lemma": "пробувати",
      "url_slug": "пробувати",
      "headword": "пробува́ти",
      "short_label": "перебувати, мешкати (B2)",
      "gloss": "to be located, stay, dwell somewhere (temporarily)",
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
        "ipa": "[prɔbuˈwatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пробува́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «про́бувати» (наголос на першому складі: намагатися, випробовувати)."
    }
  ],
  "разовий": [
    {
      "lemma": "разовий",
      "url_slug": "разовий",
      "headword": "ра́зовий",
      "short_label": "одноразовий (A2)",
      "gloss": "one-time, single-use, disposable",
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
        "ipa": "[ˈrazɔwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ра́зовий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «разови́й» (наголос на останньому складі: грубого помелу, про борошно, регіон.)."
    },
    {
      "lemma": "разовий",
      "url_slug": "разовий",
      "headword": "разови́й",
      "short_label": "грубого помелу (борошно, регіон.)",
      "gloss": "coarsely ground (of flour); made from such flour",
      "pos": "adjective",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[rɐzɔˈwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "разови́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «ра́зовий» (наголос на першому складі: одноразовий)."
    }
  ],
  "рибний": [
    {
      "lemma": "рибний",
      "url_slug": "рибний",
      "headword": "ри́бний",
      "short_label": "стосується риби (A2)",
      "gloss": "fish-related, of fish (market, food, industry)",
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
        "ipa": "[ˈrɪbnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ри́бний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «рибни́й» (наголос на другому складі: багатий на рибу, про водойму)."
    },
    {
      "lemma": "рибний",
      "url_slug": "рибний",
      "headword": "рибни́й",
      "short_label": "багатий на рибу (про водойму, B2)",
      "gloss": "rich in fish (of a body of water)",
      "pos": "adjective",
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
        "ipa": "[rɪˈbnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "рибни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «ри́бний» (наголос на першому складі: стосується риби)."
    }
  ],
  "варення": [
    {
      "lemma": "варення",
      "url_slug": "варення",
      "headword": "ва́рення",
      "short_label": "дія: варити (рідко)",
      "gloss": "the act of cooking, boiling (deverbal noun, rare)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwarɛnnʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ва́рення",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ва́рення",
              "plural": "ва́рення"
            },
            "родовий": {
              "singular": "ва́рення",
              "plural": "ва́рень"
            },
            "давальний": {
              "singular": "ва́ренню",
              "plural": "ва́ренням"
            },
            "знахідний": {
              "singular": "ва́рення",
              "plural": "ва́рення"
            },
            "орудний": {
              "singular": "ва́ренням",
              "plural": "ва́реннями"
            },
            "місцевий": {
              "singular": "ва́ренні",
              "plural": "ва́реннях"
            },
            "кличний": {
              "singular": "ва́рення",
              "plural": "ва́рення"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «варе́ння» (наголос на другому складі: солодка страва з ягід)."
    },
    {
      "lemma": "варення",
      "url_slug": "варення",
      "headword": "варе́ння",
      "short_label": "солодка страва з ягід (B1)",
      "gloss": "jam, preserves (fruit or berries cooked in syrup)",
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
        "ipa": "[wɐˈrɛnnʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "варе́ння",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "варе́ння",
              "plural": "варе́ння"
            },
            "родовий": {
              "singular": "варе́ння",
              "plural": "варе́нь"
            },
            "давальний": {
              "singular": "варе́нню",
              "plural": "варе́нням"
            },
            "знахідний": {
              "singular": "варе́ння",
              "plural": "варе́ння"
            },
            "орудний": {
              "singular": "варе́нням",
              "plural": "варе́ннями"
            },
            "місцевий": {
              "singular": "варе́нні",
              "plural": "варе́ннях"
            },
            "кличний": {
              "singular": "варе́ння",
              "plural": "варе́ння"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "конфітюр",
            "джем"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ва́рення» (наголос на першому складі: дія за значенням «варити», рідко)."
    }
  ],
  "вилазити": [
    {
      "lemma": "вилазити",
      "url_slug": "вилазити",
      "headword": "ви́лазити",
      "short_label": "облазити скрізь (розм., B2)",
      "gloss": "to have crawled all over, visited everywhere (colloquial perfective)",
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
        "ipa": "[ˈwɪɫɐzɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́лазити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «вила́зити» (наголос на другому складі: вибиратися, злазити звідкись)."
    },
    {
      "lemma": "вилазити",
      "url_slug": "вилазити",
      "headword": "вила́зити",
      "short_label": "вибиратися (B1)",
      "gloss": "to climb out, crawl out, get out",
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
        "ipa": "[wɪˈɫazɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "вила́зити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «ви́лазити» (наголос на першому складі: облазити скрізь, розм.)."
    }
  ],
  "вимикати": [
    {
      "lemma": "вимикати",
      "url_slug": "вимикати",
      "headword": "ви́микати",
      "short_label": "виривати з корінням (діал.)",
      "gloss": "to pull out, uproot (dialectal, of plants)",
      "pos": "verb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwɪmɪkɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́микати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «вимика́ти» (наголос на третьому складі: вимикати світло чи струм)."
    },
    {
      "lemma": "вимикати",
      "url_slug": "вимикати",
      "headword": "вимика́ти",
      "short_label": "вимикати світло/струм (B1)",
      "gloss": "to switch off, turn off, disconnect",
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
        "ipa": "[wɪmɪˈkatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "вимика́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «ви́микати» (наголос на першому складі: виривати з корінням, діал.)."
    }
  ],
  "виникати": [
    {
      "lemma": "виникати",
      "url_slug": "виникати",
      "headword": "ви́никати",
      "short_label": "обійти все (розм., B2)",
      "gloss": "to go around visiting everywhere (colloquial perfective)",
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
        "ipa": "[ˈwɪnɪkɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́никати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «виника́ти» (наголос на третьому складі: з'являтися, зароджуватися)."
    },
    {
      "lemma": "виникати",
      "url_slug": "виникати",
      "headword": "виника́ти",
      "short_label": "з'являтися, зароджуватися (B1)",
      "gloss": "to arise, emerge, occur",
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
        "ipa": "[wɪnɪˈkatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "виника́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «ви́никати» (наголос на першому складі: обійти все, розм.)."
    }
  ],
  "відділ": [
    {
      "lemma": "відділ",
      "url_slug": "відділ",
      "headword": "ві́дділ",
      "short_label": "підрозділ установи (B1)",
      "gloss": "department, division, section (of an institution)",
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
        "ipa": "[ˈwʲiddʲiɫ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ві́дділ",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ві́дділ",
              "plural": "ві́дділи"
            },
            "родовий": {
              "singular": "ві́дділу",
              "plural": "ві́дділів"
            },
            "давальний": {
              "singular": "ві́дділу / ві́дділові",
              "plural": "ві́дділам"
            },
            "знахідний": {
              "singular": "ві́дділ",
              "plural": "ві́дділи"
            },
            "орудний": {
              "singular": "ві́дділом",
              "plural": "ві́дділами"
            },
            "місцевий": {
              "singular": "(у) ві́дділі",
              "plural": "ві́дділах"
            },
            "кличний": {
              "singular": "ві́дділе",
              "plural": "ві́дділи"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «відді́л» (наголос на другому складі: спадкова частка майна, заст.)."
    },
    {
      "lemma": "відділ",
      "url_slug": "відділ",
      "headword": "відді́л",
      "short_label": "спадкова частка майна (заст.)",
      "gloss": "one's share of inherited family property (archaic)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wʲiˈddʲiɫ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відді́л",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "відді́л",
              "plural": "відді́ли"
            },
            "родовий": {
              "singular": "відді́лу",
              "plural": "відді́лів"
            },
            "давальний": {
              "singular": "відді́лу / відді́лові",
              "plural": "відді́лам"
            },
            "знахідний": {
              "singular": "відді́л",
              "plural": "відді́ли"
            },
            "орудний": {
              "singular": "відді́лом",
              "plural": "відді́лами"
            },
            "місцевий": {
              "singular": "(у) відді́лі",
              "plural": "відді́лах"
            },
            "кличний": {
              "singular": "відді́ле",
              "plural": "відді́ли"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «ві́дділ» (наголос на першому складі: підрозділ установи)."
    }
  ],
  "квітковий": [
    {
      "lemma": "квітковий",
      "url_slug": "квітковий",
      "headword": "квітко́вий",
      "short_label": "ботанічний термін (спец., B2)",
      "gloss": "flowering (botanical: producing flowers, e.g. angiosperms)",
      "pos": "adjective",
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
        "ipa": "[kwʲiˈtkɔwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "квітко́вий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «квіткови́й» (наголос на останньому складі: стосується квітів, квітковий магазин)."
    },
    {
      "lemma": "квітковий",
      "url_slug": "квітковий",
      "headword": "квіткови́й",
      "short_label": "стосується квітів (B1)",
      "gloss": "flower-related, floral (e.g. flower shop, floral scent)",
      "pos": "adjective",
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
        "ipa": "[kwʲitkɔˈwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "квіткови́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «квітко́вий» (наголос на другому складі: ботанічний термін, спец.)."
    }
  ],
  "наголос": [
    {
      "lemma": "наголос",
      "url_slug": "наголос",
      "headword": "на́голос",
      "short_label": "фонетичний наголос (B1)",
      "gloss": "stress, accent (phonetic emphasis on a syllable)",
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
        "ipa": "[ˈnaɦɔɫɔs]",
        "source": "VESUM"
      },
      "stress": {
        "form": "на́голос",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "на́голос",
              "plural": "на́голоси"
            },
            "родовий": {
              "singular": "на́голосу",
              "plural": "на́голосів"
            },
            "давальний": {
              "singular": "на́голосу / на́голосові",
              "plural": "на́голосам"
            },
            "знахідний": {
              "singular": "на́голос",
              "plural": "на́голоси"
            },
            "орудний": {
              "singular": "на́голосом",
              "plural": "на́голосами"
            },
            "місцевий": {
              "singular": "(у) на́голосі",
              "plural": "на́голосах"
            },
            "кличний": {
              "singular": "на́голосе",
              "plural": "на́голоси"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «наго́лос» (наголос на другому складі: голосно, гучно, діал.)."
    },
    {
      "lemma": "наголос",
      "url_slug": "наголос",
      "headword": "наго́лос",
      "short_label": "голосно (діал.)",
      "gloss": "loudly, aloud (dialectal adverb)",
      "pos": "adverb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[nɐˈɦɔɫɔs]",
        "source": "VESUM"
      },
      "stress": {
        "form": "наго́лос",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «на́голос» (наголос на першому складі: фонетичне виділення складу)."
    }
  ],
  "наречений": [
    {
      "lemma": "наречений",
      "url_slug": "наречений",
      "headword": "наре́чений",
      "short_label": "названий (заст.)",
      "gloss": "named, called (archaic passive participle of наректи)",
      "pos": "verb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[nɐˈrɛt͡ʃɛnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "наре́чений",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієприкметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «нарече́ний» (наголос на третьому складі: жених)."
    },
    {
      "lemma": "наречений",
      "url_slug": "наречений",
      "headword": "нарече́ний",
      "short_label": "жених (B1)",
      "gloss": "fiancé, bridegroom",
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
        "ipa": "[nɐrɛˈt͡ʃɛnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "нарече́ний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "нарече́ний",
              "plural": "нарече́ні"
            },
            "родовий": {
              "singular": "нарече́ного",
              "plural": "нарече́них"
            },
            "давальний": {
              "singular": "нарече́ному",
              "plural": "нарече́ним"
            },
            "знахідний": {
              "singular": "нарече́ного",
              "plural": "нарече́них"
            },
            "орудний": {
              "singular": "нарече́ним",
              "plural": "нарече́ними"
            },
            "місцевий": {
              "singular": "(на) нарече́ному",
              "plural": "нарече́них"
            },
            "кличний": {
              "singular": "нарече́ний",
              "plural": "нарече́ні"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «наре́чений» (наголос на другому складі: дієприкметник «названий», заст.)."
    }
  ],
  "обходити": [
    {
      "lemma": "обходити",
      "url_slug": "обходити",
      "headword": "обхо́дити",
      "short_label": "обходити щось (B1)",
      "gloss": "to go around, walk around, circumvent, avoid",
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
        "ipa": "[ɔˈbxɔdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "обхо́дити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «обходи́ти» (наголос на третьому складі: обійти геть усе, розм.)."
    },
    {
      "lemma": "обходити",
      "url_slug": "обходити",
      "headword": "обходи́ти",
      "short_label": "обійти геть усе (розм., B2)",
      "gloss": "to have gone around, visited everywhere (colloquial perfective)",
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
        "ipa": "[ɔbxɔˈdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "обходи́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «обхо́дити» (наголос на другому складі: обходити щось, уникати)."
    }
  ],
  "обходитися": [
    {
      "lemma": "обходитися",
      "url_slug": "обходитися",
      "headword": "обхо́дитися",
      "short_label": "обходитися без чогось (B1)",
      "gloss": "to manage, get by, do without something",
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
        "ipa": "[ɔˈbxɔdɪtɪsʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "обхо́дитися",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «обходи́тися» (наголос на третьому складі: звикнути, розм.)."
    },
    {
      "lemma": "обходитися",
      "url_slug": "обходитися",
      "headword": "обходи́тися",
      "short_label": "звикнути (розм., B2)",
      "gloss": "to get used to, become accustomed to (colloquial perfective)",
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
        "ipa": "[ɔbxɔˈdɪtɪsʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "обходи́тися",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «обхо́дитися» (наголос на другому складі: обходитися без чогось)."
    }
  ],
  "перед": [
    {
      "lemma": "перед",
      "url_slug": "перед",
      "headword": "пе́ред",
      "short_label": "прийменник (B1)",
      "gloss": "before, in front of (preposition, governs instrumental/accusative)",
      "pos": "preposition",
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
        "ipa": "[ˈpɛrɛd]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пе́ред",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прийменник",
        "paradigm": {
          "kind": "preposition"
        }
      },
      "distinction_note": "Не плутати з омографом «пере́д» (наголос на другому складі: передня частина чогось, іменник)."
    },
    {
      "lemma": "перед",
      "url_slug": "перед",
      "headword": "пере́д",
      "short_label": "передня частина (B2)",
      "gloss": "the front part, façade (of a garment, building, etc.)",
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
        "ipa": "[pɛˈrɛd]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пере́д",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "пере́д",
              "plural": "пере́ди"
            },
            "родовий": {
              "singular": "пе́реду",
              "plural": "пере́дів"
            },
            "давальний": {
              "singular": "пе́реду / пере́дові",
              "plural": "пере́дам"
            },
            "знахідний": {
              "singular": "пере́д",
              "plural": "пере́ди"
            },
            "орудний": {
              "singular": "пере́дом",
              "plural": "пере́дами"
            },
            "місцевий": {
              "singular": "(у) пере́ді",
              "plural": "пере́дах"
            },
            "кличний": {
              "singular": "пере́де",
              "plural": "пере́ди"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «пе́ред» (наголос на першому складі: прийменник «перед»)."
    }
  ],
  "покликати": [
    {
      "lemma": "покликати",
      "url_slug": "покликати",
      "headword": "покли́кати",
      "short_label": "гукнути когось (B1)",
      "gloss": "to call, summon (someone) once",
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
        "ipa": "[pɔˈkɫɪkɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "покли́кати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з недоконаним омографом «поклика́ти» (наголос на третьому складі: вигукувати, поет.)."
    },
    {
      "lemma": "покликати",
      "url_slug": "покликати",
      "headword": "поклика́ти",
      "short_label": "вигукувати (поет., B2)",
      "gloss": "to cry out, shout repeatedly (literary/poetic)",
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
        "ipa": "[pɔkɫɪˈkatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "поклика́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з доконаним омографом «покли́кати» (наголос на другому складі: гукнути когось один раз)."
    }
  ],
  "підліток": [
    {
      "lemma": "підліток",
      "url_slug": "підліток",
      "headword": "пі́дліток",
      "short_label": "підліток 12-16 років (B1)",
      "gloss": "teenager, adolescent (12-16 years old)",
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
        "ipa": "[ˈpʲidɫʲitɔk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пі́дліток",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "пі́дліток",
              "plural": "пі́длітки"
            },
            "родовий": {
              "singular": "пі́длітка",
              "plural": "пі́длітків"
            },
            "давальний": {
              "singular": "пі́дліткові / пі́длітку",
              "plural": "пі́дліткам"
            },
            "знахідний": {
              "singular": "пі́длітка",
              "plural": "пі́длітків"
            },
            "орудний": {
              "singular": "пі́длітком",
              "plural": "пі́длітками"
            },
            "місцевий": {
              "singular": "(у) пі́дліткові / пі́длітку",
              "plural": "пі́длітках"
            },
            "кличний": {
              "singular": "пі́длітку",
              "plural": "пі́длітки"
            }
          }
        }
      },
      "distinction_note": "Не плутати з рідкісним омографом «підлі́ток» (наголос на другому складі: пташеня-літун, поет.)."
    },
    {
      "lemma": "підліток",
      "url_slug": "підліток",
      "headword": "підлі́ток",
      "short_label": "пташеня-літун (поет., рідко)",
      "gloss": "fledgling (a young bird that has just learned to fly)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[pʲiˈdɫʲitɔk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "підлі́ток",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "підлі́ток",
              "plural": "підлі́тки"
            },
            "родовий": {
              "singular": "підлі́тка",
              "plural": "підлі́тків"
            },
            "давальний": {
              "singular": "підлі́ткові / підлі́тку",
              "plural": "підлі́ткам"
            },
            "знахідний": {
              "singular": "підлі́тка",
              "plural": "підлі́тків"
            },
            "орудний": {
              "singular": "підлі́тком",
              "plural": "підлі́тками"
            },
            "місцевий": {
              "singular": "(у) підлі́ткові / підлі́тку",
              "plural": "підлі́тках"
            },
            "кличний": {
              "singular": "підлі́тку",
              "plural": "підлі́тки"
            }
          }
        }
      },
      "distinction_note": "Не плутати зі звичайним омографом «пі́дліток» (наголос на першому складі: хлопчик або дівчинка 12-16 років)."
    }
  ],
  "складний": [
    {
      "lemma": "складний",
      "url_slug": "складний",
      "headword": "скла́дний",
      "short_label": "статурний, гарної будови (заст.)",
      "gloss": "well-proportioned, shapely (of a figure/body; archaic/literary)",
      "pos": "adjective",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈskɫadnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "скла́дний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «складни́й» (наголос на останньому складі: непростий, з кількох частин)."
    },
    {
      "lemma": "складний",
      "url_slug": "складний",
      "headword": "складни́й",
      "short_label": "непростий, з кількох частин (B1)",
      "gloss": "complex, composite, difficult (consisting of several parts)",
      "pos": "adjective",
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
        "ipa": "[skɫɐˈdnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "складни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «скла́дний» (наголос на першому складі: статурний, гарної будови тіла, заст.)."
    }
  ],
  "характерний": [
    {
      "lemma": "характерний",
      "url_slug": "характерний",
      "headword": "хара́ктерний",
      "short_label": "вольовий, впертий (розм., B2)",
      "gloss": "strong-willed, stubborn (of a person's character; colloquial)",
      "pos": "adjective",
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
        "ipa": "[xɐˈraktɛrnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "хара́ктерний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «характе́рний» (наголос на третьому складі: типовий, властивий)."
    },
    {
      "lemma": "характерний",
      "url_slug": "характерний",
      "headword": "характе́рний",
      "short_label": "типовий, властивий (B1)",
      "gloss": "characteristic, typical",
      "pos": "adjective",
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
        "ipa": "[xɐrɐˈktɛrnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "характе́рний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «хара́ктерний» (наголос на другому складі: вольовий, впертий, розм.)."
    }
  ],
  "господарський": [
    {
      "lemma": "господарський",
      "url_slug": "господарський",
      "headword": "госпо́дарський",
      "short_label": "належний господареві (B1)",
      "gloss": "of/belonging to the master of the house or estate; personal, domestic",
      "pos": "adjective",
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
        "ipa": "[ɦɔˈspɔdɐrsʲkɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "госпо́дарський",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "панський",
            "хазяйський"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «господа́рський» (наголос на третьому складі: пов'язаний з господарством, економікою)."
    },
    {
      "lemma": "господарський",
      "url_slug": "господарський",
      "headword": "господа́рський",
      "short_label": "пов'язаний з господарством (B1)",
      "gloss": "of/relating to the economy, farming, or management of an estate/enterprise",
      "pos": "adjective",
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
        "ipa": "[ɦɔspɔˈdarsʲkɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "господа́рський",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "економічний",
            "хазяйновитий"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «госпо́дарський» (наголос на другому складі: належний господареві, особистий)."
    }
  ],
  "замковий": [
    {
      "lemma": "замковий",
      "url_slug": "замковий",
      "headword": "за́мковий",
      "short_label": "прикм. до за́мок (B1)",
      "gloss": "of/relating to a castle or fortress",
      "pos": "adjective",
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
        "ipa": "[ˈzamkɔwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "за́мковий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "фортечний"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «замкови́й» (наголос на останньому складі: пов'язаний із замко́м на дверях)."
    },
    {
      "lemma": "замковий",
      "url_slug": "замковий",
      "headword": "замкови́й",
      "short_label": "прикм. до замо́к (B1)",
      "gloss": "of/relating to a door lock or padlock",
      "pos": "adjective",
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
        "ipa": "[zɐmkɔˈwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "замкови́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "дверний"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «за́мковий» (наголос на першому складі: пов'язаний із за́мком-фортецею)."
    }
  ],
  "верхом": [
    {
      "lemma": "верхом",
      "url_slug": "верхом",
      "headword": "ве́рхом",
      "short_label": "по верхній частині (B1)",
      "gloss": "along/over the top of something; filled to the brim, heaped over the rim",
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
        "ipa": "[ˈwɛrxɔm]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ве́рхом",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «верхо́м» (наголос на другому складі, рідко: те саме, що «верхи» -- сидячи на коні)."
    },
    {
      "lemma": "верхом",
      "url_slug": "верхом",
      "headword": "верхо́м",
      "short_label": "сидячи на коні (рідко, B1)",
      "gloss": "mounted, astride, on horseback (rare synonym of верхи)",
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
        "ipa": "[wɛˈrxɔm]",
        "source": "VESUM"
      },
      "stress": {
        "form": "верхо́м",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "верхи"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ве́рхом» (наголос на першому складі: по верхній частині чого-небудь, з верхом)."
    }
  ],
  "вибухати": [
    {
      "lemma": "вибухати",
      "url_slug": "вибухати",
      "headword": "вибуха́ти",
      "short_label": "вибухати, розриватися (A2)",
      "gloss": "to explode, detonate with great force; (of feelings, events) to erupt suddenly",
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
        "ipa": "[wɪbuˈxatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "вибуха́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "розриватися",
            "детонувати"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ви́бухати» (наголос на першому складі, док., розм.: раптом сказати все одразу)."
    },
    {
      "lemma": "вибухати",
      "url_slug": "вибухати",
      "headword": "ви́бухати",
      "short_label": "раптом усе сказати (розм., B1)",
      "gloss": "to blurt out, say everything suddenly (colloquial, perfective)",
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
        "ipa": "[ˈwɪbuxɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́бухати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «вибуха́ти» (наголос на третьому складі, недок.: розриватися з силою і звуком)."
    }
  ],
  "вивозити": [
    {
      "lemma": "вивозити",
      "url_slug": "вивозити",
      "headword": "виво́зити",
      "short_label": "везти геть, експортувати (A2)",
      "gloss": "to carry/take out of a place; (also) to export goods to another country",
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
        "ipa": "[wɪˈwɔzɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "виво́зити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "експортувати"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ви́возити» (наголос на першому складі, док.: вивезти все за кілька разів; розм. забруднити одяг)."
    },
    {
      "lemma": "вивозити",
      "url_slug": "вивозити",
      "headword": "ви́возити",
      "short_label": "забруднити, вивезти все (розм., B1)",
      "gloss": "to remove/carry away entirely by repeated trips; (colloquial) to get one's clothes dirty while working",
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
        "ipa": "[ˈwɪwɔzɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́возити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «виво́зити» (наголос на другому складі, недок.: везти геть, експортувати)."
    }
  ],
  "виганяти": [
    {
      "lemma": "виганяти",
      "url_slug": "виганяти",
      "headword": "виганя́ти",
      "short_label": "проганяти, виводити геть (A2)",
      "gloss": "to drive out, expel, evict (people); to drive/take livestock out to pasture",
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
        "ipa": "[wɪɦɐˈnʲatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "виганя́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "проганяти",
            "виводити"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ви́ганяти» (наголос на першому складі, док., рідко: набігатися по багатьох місцях; інший корінь -- від «ганяти», не «гнати»)."
    },
    {
      "lemma": "виганяти",
      "url_slug": "виганяти",
      "headword": "ви́ганяти",
      "short_label": "набігатися (рідко, розм.)",
      "gloss": "to have spent time running about to many places (rare, colloquial; from ганяти, unrelated to виганяти/гнати)",
      "pos": "verb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwɪɦɐnʲɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́ганяти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «виганя́ти» (наголос на третьому складі, недок.: проганяти когось геть, виганяти худобу на пасовище)."
    }
  ],
  "вилітати": [
    {
      "lemma": "вилітати",
      "url_slug": "вилітати",
      "headword": "виліта́ти",
      "short_label": "вилітати, відправлятися (A2)",
      "gloss": "to fly out, take off, depart by air; (colloquial) to be expelled, fired",
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
        "ipa": "[wɪɫʲiˈtatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "виліта́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "відлітати"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ви́літати» (наголос на першому складі, док.: пробути якийсь час літаючи)."
    },
    {
      "lemma": "вилітати",
      "url_slug": "вилітати",
      "headword": "ви́літати",
      "short_label": "пробути якийсь час у польоті (B1)",
      "gloss": "to spend time flying, fly around for a while (delimitative perfective)",
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
        "ipa": "[ˈwɪɫʲitɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́літати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «виліта́ти» (наголос на третьому складі, недок.: вилітати, відправлятися в політ)."
    }
  ],
  "витягати": [
    {
      "lemma": "витягати",
      "url_slug": "витягати",
      "headword": "витяга́ти",
      "short_label": "тягнучи, виймати (A2)",
      "gloss": "to pull out, extract, stretch out; to help someone out of a difficult situation",
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
        "ipa": "[wɪtʲɐˈɦatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "витяга́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "виймати",
            "видобувати"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ви́тягати» (наголос на першому складі, док.: вибрати щось звідкись за кілька разів)."
    },
    {
      "lemma": "витягати",
      "url_slug": "витягати",
      "headword": "ви́тягати",
      "short_label": "вибрати за кілька разів (B1)",
      "gloss": "to pick out/draw out repeatedly, several times (perfective)",
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
        "ipa": "[ˈwɪtʲɐɦɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́тягати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «витяга́ти» (наголос на третьому складі, недок.: тягнучи, виймати, розтягувати)."
    }
  ],
  "відкликання": [
    {
      "lemma": "відкликання",
      "url_slug": "відкликання",
      "headword": "відкли́кання",
      "short_label": "позбавлення повноважень (B2)",
      "gloss": "recall, withdrawal (of deputies, ambassadors, officials from their post)",
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
        "ipa": "[wʲiˈdkɫɪkɐnnʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відкли́кання",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "відкли́кання",
              "plural": "відкли́кання"
            },
            "родовий": {
              "singular": "відкли́кання",
              "plural": "відкли́кань"
            },
            "давальний": {
              "singular": "відкли́канню",
              "plural": "відкли́канням"
            },
            "знахідний": {
              "singular": "відкли́кання",
              "plural": "відкли́кання"
            },
            "орудний": {
              "singular": "відкли́канням",
              "plural": "відкли́каннями"
            },
            "місцевий": {
              "singular": "(у) відкли́канні / відкли́канню",
              "plural": "відкли́каннях"
            },
            "кличний": {
              "singular": "відкли́кання",
              "plural": "відкли́кання"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "звільнення",
            "усунення"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «відклика́ння» (наголос на третьому складі: здатність відкликатися, відгук на поклик)."
    },
    {
      "lemma": "відкликання",
      "url_slug": "відкликання",
      "headword": "відклика́ння",
      "short_label": "відгук на поклик (B2)",
      "gloss": "responsiveness; the act of answering a call (per the verb відклика́тися)",
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
        "ipa": "[wʲidkɫɪˈkannʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відклика́ння",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "відклика́ння",
              "plural": "відклика́ння"
            },
            "родовий": {
              "singular": "відклика́ння",
              "plural": "відклика́нь"
            },
            "давальний": {
              "singular": "відклика́нню",
              "plural": "відклика́нням"
            },
            "знахідний": {
              "singular": "відклика́ння",
              "plural": "відклика́ння"
            },
            "орудний": {
              "singular": "відклика́нням",
              "plural": "відклика́ннями"
            },
            "місцевий": {
              "singular": "(у) відклика́нні / відклика́нню",
              "plural": "відклика́ннях"
            },
            "кличний": {
              "singular": "відклика́ння",
              "plural": "відклика́ння"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «відкли́кання» (наголос на другому складі: позбавлення повноважень депутата, посла)."
    }
  ],
  "відповідний": [
    {
      "lemma": "відповідний",
      "url_slug": "відповідний",
      "headword": "відпові́дний",
      "short_label": "підхожий, належний (A2)",
      "gloss": "suitable, appropriate, corresponding (fitting for a given case)",
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
        "ipa": "[wʲidpɔˈwʲidnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відпові́дний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "підхожий",
            "належний"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «відповідни́й» (наголос на останньому складі: даний у відповідь -- відповідний лист)."
    },
    {
      "lemma": "відповідний",
      "url_slug": "відповідний",
      "headword": "відповідни́й",
      "short_label": "даний у відповідь (B2)",
      "gloss": "given in reply/response (e.g. an answering letter or diplomatic note)",
      "pos": "adjective",
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
        "ipa": "[wʲidpɔwʲiˈdnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "відповідни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «відпові́дний» (наголос на третьому складі: підхожий, належний для якогось випадку)."
    }
  ],
  "вітряний": [
    {
      "lemma": "вітряний",
      "url_slug": "вітряний",
      "headword": "ві́тряний",
      "short_label": "з вітром (A2)",
      "gloss": "windy (accompanied by wind); (figuratively, of a person) flighty, frivolous",
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
        "ipa": "[ˈwʲitrɐnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ві́тряний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "буряний"
          ]
        },
        "antonyms": {
          "source": "СУМ-11",
          "items": [
            "тихий",
            "безвітряний"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «вітряни́й» (наголос на останньому складі: що діє за допомогою вітру -- вітряний млин)."
    },
    {
      "lemma": "вітряний",
      "url_slug": "вітряний",
      "headword": "вітряни́й",
      "short_label": "що діє вітром (B1)",
      "gloss": "wind-powered (e.g. a windmill)",
      "pos": "adjective",
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
        "ipa": "[wʲitrɐˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "вітряни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «ві́тряний» (наголос на першому складі: з вітром, вітряна погода)."
    }
  ],
  "водяний": [
    {
      "lemma": "водяний",
      "url_slug": "водяний",
      "headword": "водя́ний",
      "short_label": "водянистий (B1)",
      "gloss": "watery, diluted, waterlogged (of soil, food); rich in water",
      "pos": "adjective",
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
        "ipa": "[wɔˈdʲanɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "водя́ний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "водянистий"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «водяни́й» (наголос на останньому складі: пов'язаний з водою -- водяний млин, водяний спорт)."
    },
    {
      "lemma": "водяний",
      "url_slug": "водяний",
      "headword": "водяни́й",
      "short_label": "пов'язаний з водою (A2)",
      "gloss": "aquatic, water-related, water-powered (of mills, sports, plants/animals); (dated, as a noun) a water spirit",
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
        "ipa": "[wɔdʲɐˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "водяни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "водний"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «водя́ний» (наголос на другому складі: водянистий, багатий на воду)."
    }
  ],
  "воловий": [
    {
      "lemma": "воловий",
      "url_slug": "воловий",
      "headword": "во́ловий",
      "short_label": "прикм. до во́ло (діал.)",
      "gloss": "relating to воло -- the crop (craw) of a bird; (dialectal, folk) relating to a goiter",
      "pos": "adjective",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈwɔɫɔwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "во́ловий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «воло́вий» (наголос на другому складі: прикметник до «віл» -- волова шкура, воловий плуг)."
    },
    {
      "lemma": "воловий",
      "url_slug": "воловий",
      "headword": "воло́вий",
      "short_label": "прикм. до віл (B1)",
      "gloss": "of/relating to an ox (ox-hide, ox-drawn, ox-meat); (figuratively) extremely strong, tough",
      "pos": "adjective",
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
        "ipa": "[wɔˈɫɔwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "воло́вий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «во́ловий» (наголос на першому складі, діал.: прикметник до «воло» -- воло птаха або зоб)."
    }
  ],
  "гукати": [
    {
      "lemma": "гукати",
      "url_slug": "гукати",
      "headword": "гу́кати",
      "short_label": "видавати гучний звук (розм., B1)",
      "gloss": "to make a loud, sharp sound; to hoot (of trains, thunder)",
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
        "ipa": "[ˈɦukɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "гу́кати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «гука́ти» (наголос на другому складі: голосно кликати когось, звертатися до когось)."
    },
    {
      "lemma": "гукати",
      "url_slug": "гукати",
      "headword": "гука́ти",
      "short_label": "голосно кликати (A2)",
      "gloss": "to call out loudly, summon; to shout at someone",
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
        "ipa": "[ɦuˈkatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "гука́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "кликати",
            "гукнути"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «гу́кати» (наголос на першому складі, розм.: видавати гучний, різкий звук -- про грім, потяг)."
    }
  ],
  "випробування": [
    {
      "lemma": "випробування",
      "url_slug": "випробування",
      "headword": "ви́пробування",
      "short_label": "процес перевірки, тестування (A2)",
      "gloss": "the act or process of testing, trying (something) out (act per значенням «ви́пробувати»)",
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
        "ipa": "[ˈwɪprɔbʊwɐnʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́пробування",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ви́пробування",
              "plural": "ви́пробування"
            },
            "родовий": {
              "singular": "ви́пробування",
              "plural": "ви́пробувань"
            },
            "давальний": {
              "singular": "ви́пробуванню",
              "plural": "ви́пробуванням"
            },
            "знахідний": {
              "singular": "ви́пробування",
              "plural": "ви́пробування"
            },
            "орудний": {
              "singular": "ви́пробуванням",
              "plural": "ви́пробуваннями"
            },
            "місцевий": {
              "singular": "(на/у) ви́пробуванні / ви́пробуванню",
              "plural": "ви́пробуваннях"
            },
            "кличний": {
              "singular": "ви́пробування",
              "plural": "ви́пробування"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «випро́бування» (наголос на другому складі: перевірка якостей, властивостей когось/чогось, іспит; тяжкі переживання, лихо)."
    },
    {
      "lemma": "випробування",
      "url_slug": "випробування",
      "headword": "випро́бування",
      "short_label": "іспит; тяжке переживання (B1)",
      "gloss": "a test, trial, examination of someone's/something's qualities or properties; (also) an ordeal, hardship, tribulation",
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
        "ipa": "[wɪˈprɔbʊwɐnʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "випро́бування",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "випро́бування",
              "plural": "випро́бування"
            },
            "родовий": {
              "singular": "випро́бування",
              "plural": "випро́бувань"
            },
            "давальний": {
              "singular": "випро́буванню",
              "plural": "випро́буванням"
            },
            "знахідний": {
              "singular": "випро́бування",
              "plural": "випро́бування"
            },
            "орудний": {
              "singular": "випро́буванням",
              "plural": "випро́буваннями"
            },
            "місцевий": {
              "singular": "(на/у) випро́буванні / випро́буванню",
              "plural": "випро́буваннях"
            },
            "кличний": {
              "singular": "випро́бування",
              "plural": "випро́бування"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «ви́пробування» (наголос на першому складі: дія за значенням «ви́пробувати», процес тестування)."
    }
  ],
  "гладкий": [
    {
      "lemma": "гладкий",
      "url_slug": "гладкий",
      "headword": "гла́дкий",
      "short_label": "рівний, без нерівностей (A2)",
      "gloss": "smooth, even, without bumps or folds",
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
        "ipa": "[ˈɦɫadkɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "гла́дкий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "рівний"
          ]
        },
        "antonyms": {
          "source": "СУМ-11",
          "items": [
            "шорсткий",
            "нерівний"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «гладки́й» (наголос на другому складі: вгодований, ситий, повний тілом)."
    },
    {
      "lemma": "гладкий",
      "url_slug": "гладкий",
      "headword": "гладки́й",
      "short_label": "вгодований, ситий (B1)",
      "gloss": "plump, corpulent, well-fed",
      "pos": "adjective",
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
        "ipa": "[ɦɫɐˈdkɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "гладки́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "вгодований",
            "ситий"
          ]
        },
        "antonyms": {
          "source": "СУМ-11",
          "items": [
            "худий"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «гла́дкий» (наголос на першому складі: рівний, без нерівностей і виступів)."
    }
  ],
  "діяння": [
    {
      "lemma": "діяння",
      "url_slug": "діяння",
      "headword": "ді́яння",
      "short_label": "дія, вчинок (B1)",
      "gloss": "a deed, act, action; (plural) conduct, deeds",
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
        "ipa": "[ˈdʲijɐnnʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ді́яння",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ді́яння",
              "plural": "ді́яння"
            },
            "родовий": {
              "singular": "ді́яння",
              "plural": "ді́янь"
            },
            "давальний": {
              "singular": "ді́янню",
              "plural": "ді́янням"
            },
            "знахідний": {
              "singular": "ді́яння",
              "plural": "ді́яння"
            },
            "орудний": {
              "singular": "ді́янням",
              "plural": "ді́яннями"
            },
            "місцевий": {
              "singular": "(у) ді́янні / ді́янню",
              "plural": "ді́яннях"
            },
            "кличний": {
              "singular": "ді́яння",
              "plural": "ді́яння"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "дія",
            "вчинок"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «дія́ння» (наголос на другому складі, рел.: церковне читання про діяння апостолів)."
    },
    {
      "lemma": "діяння",
      "url_slug": "діяння",
      "headword": "дія́ння",
      "short_label": "церк. читання про апостолів",
      "gloss": "(religious) the church reading of the Acts of the Apostles; «Діяння апостолів» = the Acts of the Apostles",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[dʲiˈjannʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "дія́ння",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "дія́ння",
              "plural": "дія́ння"
            },
            "родовий": {
              "singular": "дія́ння",
              "plural": "дія́нь"
            },
            "давальний": {
              "singular": "дія́нню",
              "plural": "дія́нням"
            },
            "знахідний": {
              "singular": "дія́ння",
              "plural": "дія́ння"
            },
            "орудний": {
              "singular": "дія́нням",
              "plural": "дія́ннями"
            },
            "місцевий": {
              "singular": "(у) дія́нні / дія́нню",
              "plural": "дія́ннях"
            },
            "кличний": {
              "singular": "дія́ння",
              "plural": "дія́ння"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «ді́яння» (наголос на першому складі: дія, вчинок, учинки людини)."
    }
  ],
  "добродійство": [
    {
      "lemma": "добродійство",
      "url_slug": "добродійство",
      "headword": "добро́дійство",
      "short_label": "шановне товариство (заст., збірн.)",
      "gloss": "the esteemed folk, ladies and gentlemen (archaic collective address term; see добродій)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured",
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[dɔˈbrɔdʲijstwɔ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "добро́дійство",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "добро́дійство",
              "plural": "добро́дійства"
            },
            "родовий": {
              "singular": "добро́дійства",
              "plural": "добро́дійств"
            },
            "давальний": {
              "singular": "добро́дійству",
              "plural": "добро́дійствам"
            },
            "знахідний": {
              "singular": "добро́дійство",
              "plural": "добро́дійства"
            },
            "орудний": {
              "singular": "добро́дійством",
              "plural": "добро́дійствами"
            },
            "місцевий": {
              "singular": "(у) добро́дійстві / добро́дійству",
              "plural": "добро́дійствах"
            },
            "кличний": {
              "singular": "добро́дійство",
              "plural": "добро́дійства"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «доброді́йство» (наголос на третьому складі, розм.: доброчинність, добра справа)."
    },
    {
      "lemma": "добродійство",
      "url_slug": "добродійство",
      "headword": "доброді́йство",
      "short_label": "доброчинність (розм., B2)",
      "gloss": "beneficence, charity; a good/charitable deed (= добродіяння)",
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
        "ipa": "[dɔbrɔˈdʲijstwɔ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "доброді́йство",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "доброді́йство",
              "plural": "доброді́йства"
            },
            "родовий": {
              "singular": "доброді́йства",
              "plural": "доброді́йств"
            },
            "давальний": {
              "singular": "доброді́йству",
              "plural": "доброді́йствам"
            },
            "знахідний": {
              "singular": "доброді́йство",
              "plural": "доброді́йства"
            },
            "орудний": {
              "singular": "доброді́йством",
              "plural": "доброді́йствами"
            },
            "місцевий": {
              "singular": "(у) доброді́йстві / доброді́йству",
              "plural": "доброді́йствах"
            },
            "кличний": {
              "singular": "доброді́йство",
              "plural": "доброді́йства"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "добродіяння",
            "доброчинність"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «добро́дійство» (наголос на другому складі, заст., збірн.: шановне товариство, зверт. форма)."
    }
  ],
  "духовий": [
    {
      "lemma": "духовий",
      "url_slug": "духовий",
      "headword": "духо́вий",
      "short_label": "духовний (діал.)",
      "gloss": "spiritual (dialectal synonym of духовний)",
      "pos": "adjective",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[duˈxɔwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "духо́вий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «духови́й» (наголос на останньому складі: пов'язаний із духовими інструментами або жаром -- духовий оркестр, духова шафа)."
    },
    {
      "lemma": "духовий",
      "url_slug": "духовий",
      "headword": "духови́й",
      "short_label": "духові інструменти, жарова піч (A2)",
      "gloss": "wind-instrument-related (of music); operated by hot air (e.g. an oven)",
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
        "ipa": "[duxɔˈwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "духови́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "жаровий"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «духо́вий» (наголос на другому складі, діал.: духовний, пов'язаний із духом)."
    }
  ],
  "забігати": [
    {
      "lemma": "забігати",
      "url_slug": "забігати",
      "headword": "забі́гати",
      "short_label": "почати бігати (B1)",
      "gloss": "to begin running about (bounded perfective)",
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
        "ipa": "[zɐˈbʲiɦɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "забі́гати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «забіга́ти» (наголос на третьому складі, недок.: заходити ненадовго, забігати наперед)."
    },
    {
      "lemma": "забігати",
      "url_slug": "забігати",
      "headword": "забіга́ти",
      "short_label": "заходити ненадовго (A2)",
      "gloss": "to run into somewhere briefly; to drop by; to run ahead",
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
        "ipa": "[zɐbʲiˈɦatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "забіга́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "заходити",
            "навідуватися"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «забі́гати» (наголос на другому складі, док.: почати бігати)."
    }
  ],
  "загорода": [
    {
      "lemma": "загорода",
      "url_slug": "загорода",
      "headword": "за́города",
      "short_label": "загін для худоби (B1)",
      "gloss": "an enclosed pen for keeping domestic animals or birds",
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
        "ipa": "[ˈzaɦɔrɔdɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "за́города",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "за́города",
              "plural": "за́городи"
            },
            "родовий": {
              "singular": "за́городи",
              "plural": "за́город"
            },
            "давальний": {
              "singular": "за́городі",
              "plural": "за́городам"
            },
            "знахідний": {
              "singular": "за́городу",
              "plural": "за́городи"
            },
            "орудний": {
              "singular": "за́городою",
              "plural": "за́городами"
            },
            "місцевий": {
              "singular": "(у) за́городі",
              "plural": "за́городах"
            },
            "кличний": {
              "singular": "за́городо",
              "plural": "за́городи"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "загін",
            "кошара"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «загоро́да» (наголос на третьому складі: тин, паркан, огорожа)."
    },
    {
      "lemma": "загорода",
      "url_slug": "загорода",
      "headword": "загоро́да",
      "short_label": "тин, огорожа (B1)",
      "gloss": "a fence, wall, or similar barrier that encloses something",
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
        "ipa": "[zɐɦɔˈrɔdɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "загоро́да",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "загоро́да",
              "plural": "загоро́ди"
            },
            "родовий": {
              "singular": "загоро́ди",
              "plural": "загоро́д"
            },
            "давальний": {
              "singular": "загоро́ді",
              "plural": "загоро́дам"
            },
            "знахідний": {
              "singular": "загоро́ду",
              "plural": "загоро́ди"
            },
            "орудний": {
              "singular": "загоро́дою",
              "plural": "загоро́дами"
            },
            "місцевий": {
              "singular": "(у) загоро́ді",
              "plural": "загоро́дах"
            },
            "кличний": {
              "singular": "загоро́до",
              "plural": "загоро́ди"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "тин",
            "паркан",
            "огорожа"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «за́города» (наголос на першому складі: загороджена ділянка для худоби)."
    }
  ],
  "запальний": [
    {
      "lemma": "запальний",
      "url_slug": "запальний",
      "headword": "запа́льний",
      "short_label": "пов'язаний із запалом (спец., B2)",
      "gloss": "relating to a fuse or ignition charge (special/military term)",
      "pos": "adjective",
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
        "ipa": "[zɐˈpaɫʲnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "запа́льний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «запальни́й» (наголос на останньому складі: запалювальний; перен. запальна людина -- гарячкувата, схильна до захоплення)."
    },
    {
      "lemma": "запальний",
      "url_slug": "запальний",
      "headword": "запальни́й",
      "short_label": "запалювальний; гарячкуватий (B1)",
      "gloss": "incendiary; (figuratively) rousing, passionate, quick-tempered; (medical) inflammatory",
      "pos": "adjective",
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
        "ipa": "[zɐpɐɫʲˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "запальни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "палкий",
            "гарячкуватий"
          ]
        },
        "antonyms": {
          "source": "СУМ-11",
          "items": [
            "спокійний",
            "стриманий"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «запа́льний» (наголос на другому складі, спец.: пов'язаний із запалом -- запальний гніт)."
    }
  ],
  "затока": [
    {
      "lemma": "затока",
      "url_slug": "затока",
      "headword": "зато́ка",
      "short_label": "бухта (A2)",
      "gloss": "a bay, gulf (part of a sea, lake, or river that cuts into land)",
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
        "ipa": "[zɐˈtɔkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "зато́ка",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "зато́ка",
              "plural": "зато́ки"
            },
            "родовий": {
              "singular": "зато́ки",
              "plural": "зато́к"
            },
            "давальний": {
              "singular": "зато́ці",
              "plural": "зато́кам"
            },
            "знахідний": {
              "singular": "зато́ку",
              "plural": "зато́ки"
            },
            "орудний": {
              "singular": "зато́кою",
              "plural": "зато́ками"
            },
            "місцевий": {
              "singular": "(у) зато́ці",
              "plural": "зато́ках"
            },
            "кличний": {
              "singular": "зато́ко",
              "plural": "зато́ки"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "бухта",
            "лиман"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «за́тока» (наголос на першому складі, діал.: слизький схил дороги, куди сповзають сани)."
    },
    {
      "lemma": "затока",
      "url_slug": "затока",
      "headword": "за́тока",
      "short_label": "слизький схил дороги (діал.)",
      "gloss": "(dialectal) a slippery downhill stretch of road where sledges slide off",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈzatɔkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "за́тока",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "за́тока",
              "plural": "за́токи"
            },
            "родовий": {
              "singular": "за́токи",
              "plural": "за́ток"
            },
            "давальний": {
              "singular": "за́тоці",
              "plural": "за́токам"
            },
            "знахідний": {
              "singular": "за́току",
              "plural": "за́токи"
            },
            "орудний": {
              "singular": "за́токою",
              "plural": "за́токами"
            },
            "місцевий": {
              "singular": "(у) за́тоці",
              "plural": "за́токах"
            },
            "кличний": {
              "singular": "за́токо",
              "plural": "за́токи"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «зато́ка» (наголос на другому складі: частина моря чи озера, що вдається в сушу; бухта)."
    }
  ],
  "збігатися": [
    {
      "lemma": "збігатися",
      "url_slug": "збігатися",
      "headword": "збіга́тися",
      "short_label": "сходитися, збігатися в часі (A2)",
      "gloss": "to run together, converge from different directions; to coincide (in time, opinion); (of fabric) to shrink",
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
        "ipa": "[zbʲiˈɦatɪsʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "збіга́тися",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "сходитися",
            "збиратися"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «збі́гатися» (наголос на першому складі, док., заст./розм.: набігатися по багатьох місцях, стомитися від бігу)."
    },
    {
      "lemma": "збігатися",
      "url_slug": "збігатися",
      "headword": "збі́гатися",
      "short_label": "набігатися (заст., розм.)",
      "gloss": "(archaic) to have visited many places running about; (colloquial) to tire oneself out from running",
      "pos": "verb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈzbʲiɦɐtɪsʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "збі́гатися",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «збіга́тися» (наголос на другому складі, недок.: сходитися докупи, збігатися в часі)."
    }
  ],
  "землянин": [
    {
      "lemma": "землянин",
      "url_slug": "землянин",
      "headword": "земля́нин",
      "short_label": "мешканець Землі (A2)",
      "gloss": "an inhabitant of planet Earth, Earthling",
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
        "ipa": "[zɛˈmɫʲanɪn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "земля́нин",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "note": "клас іменників на -анин/-янин: у множині суфікс -ин зникає",
          "cases": {
            "називний": {
              "singular": "земля́нин",
              "plural": "земля́ни"
            },
            "родовий": {
              "singular": "земля́нина",
              "plural": "земля́н"
            },
            "давальний": {
              "singular": "земля́нинові / земля́нину",
              "plural": "земля́нам"
            },
            "знахідний": {
              "singular": "земля́нина",
              "plural": "земля́н"
            },
            "орудний": {
              "singular": "земля́нином",
              "plural": "земля́нами"
            },
            "місцевий": {
              "singular": "на земля́нині / земля́нинові / земля́нину",
              "plural": "земля́нах"
            },
            "кличний": {
              "singular": "земля́нине",
              "plural": "земля́ни"
            }
          }
        }
      },
      "sections": {
        "antonyms": {
          "source": "СУМ-11",
          "items": [
            "інопланетянин"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «земляни́н» (наголос на останньому складі, заст.: селянин)."
    },
    {
      "lemma": "землянин",
      "url_slug": "землянин",
      "headword": "земляни́н",
      "short_label": "селянин (заст.)",
      "gloss": "a peasant, countryman (archaic synonym of селянин)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured",
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[zɛmɫʲɐˈnɪn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "земляни́н",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "note": "форми множини для цього застарілого значення рідко фіксуються окремо",
          "cases": {
            "називний": {
              "singular": "земляни́н",
              "plural": null
            },
            "родовий": {
              "singular": "земляни́на",
              "plural": null
            },
            "давальний": {
              "singular": "земляни́нові / земляни́ну",
              "plural": null
            },
            "знахідний": {
              "singular": "земляни́на",
              "plural": null
            },
            "орудний": {
              "singular": "земляни́ном",
              "plural": null
            },
            "місцевий": {
              "singular": "на земляни́ні / земляни́нові / земляни́ну",
              "plural": null
            },
            "кличний": {
              "singular": "земляни́не",
              "plural": null
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "селянин"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «земля́нин» (наголос на другому складі: мешканець планети Земля)."
    }
  ],
  "ковтати": [
    {
      "lemma": "ковтати",
      "url_slug": "ковтати",
      "headword": "ковта́ти",
      "short_label": "проковтнути їжу (A1)",
      "gloss": "to swallow (move food/drink from the mouth to the stomach)",
      "pos": "verb",
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
        "ipa": "[kɔˈwtatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ковта́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "глитати"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ко́втати» (наголос на першому складі, діал.: битися, стукатися)."
    },
    {
      "lemma": "ковтати",
      "url_slug": "ковтати",
      "headword": "ко́втати",
      "short_label": "битися, стукатися (діал.)",
      "gloss": "(dialectal) to knock, hit, bang against something",
      "pos": "verb",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈkɔwtɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́втати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «ковта́ти» (наголос на другому складі: проковтнути їжу чи напій)."
    }
  ],
  "колон": [
    {
      "lemma": "колон",
      "url_slug": "колон",
      "headword": "ко́лон",
      "short_label": "віршовий рядок (спец., C1)",
      "gloss": "a colon -- a rhythmic unit of verse or prose sharing one rhythmic stress (literary/prosody term)",
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
        "ipa": "[ˈkɔɫɔn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́лон",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "cases": {
            "називний": {
              "singular": "ко́лон",
              "plural": "ко́лони"
            },
            "родовий": {
              "singular": "ко́лона",
              "plural": "ко́лонів"
            },
            "давальний": {
              "singular": "ко́лону / ко́лонові",
              "plural": "ко́лонам"
            },
            "знахідний": {
              "singular": "ко́лон",
              "plural": "ко́лони"
            },
            "орудний": {
              "singular": "ко́лоном",
              "plural": "ко́лонами"
            },
            "місцевий": {
              "singular": "(у) ко́лоні / ко́лону / ко́лонові",
              "plural": "ко́лонах"
            },
            "кличний": {
              "singular": "ко́лоне",
              "plural": "ко́лони"
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «коло́н» (наголос на другому складі: селянин-орендар у Римській імперії або середньовіччі)."
    },
    {
      "lemma": "колон",
      "url_slug": "колон",
      "headword": "коло́н",
      "short_label": "селянин-орендар (іст., C1)",
      "gloss": "a colonus -- a Roman or medieval tenant peasant farmer (historical term)",
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
        "ipa": "[kɔˈɫɔn]",
        "source": "VESUM"
      },
      "stress": {
        "form": "коло́н",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "note": "тварин./анімат. відмінювання (родовий = знахідний)",
          "cases": {
            "називний": {
              "singular": "коло́н",
              "plural": "коло́ни"
            },
            "родовий": {
              "singular": "коло́на",
              "plural": "коло́нів"
            },
            "давальний": {
              "singular": "коло́ну / коло́нові",
              "plural": "коло́нам"
            },
            "знахідний": {
              "singular": "коло́на",
              "plural": "коло́нів"
            },
            "орудний": {
              "singular": "коло́ном",
              "plural": "коло́нами"
            },
            "місцевий": {
              "singular": "(у) коло́ні / коло́ну / коло́нові",
              "plural": "коло́нах"
            },
            "кличний": {
              "singular": "коло́не",
              "plural": "коло́ни"
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "орендар"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ко́лон» (наголос на першому складі: віршовий рядок, ритмічна одиниця тексту)."
    }
  ],
  "колючий": [
    {
      "lemma": "колючий",
      "url_slug": "колючий",
      "headword": "ко́лючий",
      "short_label": "яким колють (B1)",
      "gloss": "which pricks/is used for piercing (of an organ or device); causing a sharp, piercing pain sensation",
      "pos": "adjective",
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
        "ipa": "[ˈkɔɫʲut͡ʃɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́лючий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «колю́чий» (наголос на другому складі: колючий терен, колюча борода; перен. дошкульний)."
    },
    {
      "lemma": "колючий",
      "url_slug": "колючий",
      "headword": "колю́чий",
      "short_label": "з колючками, дошкульний (A2)",
      "gloss": "prickly, thorny, covered with thorns/spines; (figuratively) sharp-tongued, biting",
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
        "ipa": "[kɔˈɫʲut͡ʃɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "колю́чий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "дошкульний"
          ]
        },
        "antonyms": {
          "source": "СУМ-11",
          "items": [
            "гладенький",
            "м'який"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ко́лючий» (наголос на першому складі: яким колють, гострий -- колючий апарат, колючий біль)."
    }
  ],
  "копати": [
    {
      "lemma": "копати",
      "url_slug": "копати",
      "headword": "ко́пати",
      "short_label": "бити ногою (A1)",
      "gloss": "to kick, strike with the foot; (of animals) to buck, kick",
      "pos": "verb",
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
        "ipa": "[ˈkɔpɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́пати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «копа́ти» (наголос на другому складі: розпушувати землю заступом чи лопатою)."
    },
    {
      "lemma": "копати",
      "url_slug": "копати",
      "headword": "копа́ти",
      "short_label": "розпушувати землю (A1)",
      "gloss": "to dig (loosen soil with a spade or shovel)",
      "pos": "verb",
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
        "ipa": "[kɔˈpatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "копа́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "розпушувати"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ко́пати» (наголос на першому складі: бити, штовхати ногою)."
    }
  ],
  "коханий": [
    {
      "lemma": "коханий",
      "url_slug": "коханий",
      "headword": "ко́ханий",
      "short_label": "плеканий, доглянутий (поет., рідко)",
      "gloss": "lovingly tended, cultivated (archaic/poetic passive participle of ко́хати in its \"to tend, cultivate\" sense, e.g. of flowers)",
      "pos": "adjective",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured",
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈkɔxɐnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́ханий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «коха́ний» (наголос на другому складі: той, кого кохають; милий, любий)."
    },
    {
      "lemma": "коханий",
      "url_slug": "коханий",
      "headword": "коха́ний",
      "short_label": "той, кого кохають (A1)",
      "gloss": "beloved; darling, sweetheart (the person one loves)",
      "pos": "adjective",
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
        "ipa": "[kɔˈxanɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "коха́ний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "милий",
            "любий"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ко́ханий» (наголос на першому складі, поет., рідко: плеканий, доглянутий -- дієприкметник до «кохати» квіти)."
    }
  ],
  "ведмежина": [
    {
      "lemma": "ведмежина",
      "url_slug": "ведмежина",
      "headword": "ведме́жина",
      "short_label": "ведмеже м'ясо (рідко)",
      "gloss": "bear meat (= ведмежатина)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wɛˈdmɛʒɪnɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ведме́жина",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "note": "переважно вживається в однині",
          "cases": {
            "називний": {
              "singular": "ведме́жина",
              "plural": null
            },
            "родовий": {
              "singular": "ведме́жини",
              "plural": null
            },
            "давальний": {
              "singular": "ведме́жині",
              "plural": null
            },
            "знахідний": {
              "singular": "ведме́жину",
              "plural": null
            },
            "орудний": {
              "singular": "ведме́жиною",
              "plural": null
            },
            "місцевий": {
              "singular": "(у) ведме́жині",
              "plural": null
            },
            "кличний": {
              "singular": "ведме́жино",
              "plural": null
            }
          }
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "ведмежатина"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ведмежи́на» (наголос на третьому складі: дикий кущ родини трояндових з темно-червоними ягодами)."
    },
    {
      "lemma": "ведмежина",
      "url_slug": "ведмежина",
      "headword": "ведмежи́на",
      "short_label": "дикий кущ з ягодами (рідко)",
      "gloss": "a wild shrub of the rose family (Rosaceae) with dark-red edible berries; the berries themselves",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": null,
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[wɛdmɛˈʒɪnɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ведмежи́на",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "note": "переважно вживається в однині",
          "cases": {
            "називний": {
              "singular": "ведмежи́на",
              "plural": null
            },
            "родовий": {
              "singular": "ведмежи́ни",
              "plural": null
            },
            "давальний": {
              "singular": "ведмежи́ні",
              "plural": null
            },
            "знахідний": {
              "singular": "ведмежи́ну",
              "plural": null
            },
            "орудний": {
              "singular": "ведмежи́ною",
              "plural": null
            },
            "місцевий": {
              "singular": "(у) ведмежи́ні",
              "plural": null
            },
            "кличний": {
              "singular": "ведмежи́но",
              "plural": null
            }
          }
        }
      },
      "distinction_note": "Не плутати з омографом «ведме́жина» (наголос на другому складі: ведмеже м'ясо)."
    }
  ],
  "вигідний": [
    {
      "lemma": "вигідний",
      "url_slug": "вигідний",
      "headword": "ви́гідний",
      "short_label": "прибутковий (A2)",
      "gloss": "profitable, beneficial (from which one can gain a benefit or profit)",
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
        "ipa": "[ˈwɪɦʲidnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́гідний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "прибутковий",
            "корисний"
          ]
        },
        "antonyms": {
          "source": "СУМ-11",
          "items": [
            "невигідний",
            "збитковий"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «вигі́дний» (наголос на другому складі: зручний для користування, приємний)."
    },
    {
      "lemma": "вигідний",
      "url_slug": "вигідний",
      "headword": "вигі́дний",
      "short_label": "зручний (A2)",
      "gloss": "comfortable, convenient (to use), pleasant",
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
        "ipa": "[wɪˈɦʲidnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "вигі́дний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "sections": {
        "synonyms": {
          "source": "СУМ-11",
          "items": [
            "зручний",
            "приємний"
          ]
        },
        "antonyms": {
          "source": "СУМ-11",
          "items": [
            "незручний"
          ]
        }
      },
      "distinction_note": "Не плутати з омографом «ви́гідний» (наголос на першому складі: прибутковий, який дає користь чи прибуток)."
    }
  ],
  "вигідність": [
    {
      "lemma": "вигідність",
      "url_slug": "вигідність",
      "headword": "ви́гідність",
      "short_label": "прибутковість, користь (B1)",
      "gloss": "profitability, commercial advantage, financial benefit",
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
        "ipa": "[ˈwɪɦʲidnʲisʲtʲ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ви́гідність",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «вигі́дність» (наголос на другому складі: зручність, комфортні умови)."
    },
    {
      "lemma": "вигідність",
      "url_slug": "вигідність",
      "headword": "вигі́дність",
      "short_label": "зручність, комфорт (B1)",
      "gloss": "convenience, comfort, suitability of conditions",
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
        "ipa": "[wɪˈɦʲidnʲisʲtʲ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "вигі́дність",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «ви́гідність» (наголос на першому складі: матеріальна вигода, прибутковість)."
    }
  ],
  "комірник": [
    {
      "lemma": "комірник",
      "url_slug": "комірник",
      "headword": "комі́рник",
      "short_label": "квартирант, пожилець (розм.)",
      "gloss": "lodger, tenant, roomer",
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
        "ipa": "[kɔˈmʲirnɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "комі́рник",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "істота"
        }
      },
      "distinction_note": "Не плутати з омографом «комірни́к» (наголос на третьому складі: завідувач комори чи складу)."
    },
    {
      "lemma": "комірник",
      "url_slug": "комірник",
      "headword": "комірни́к",
      "short_label": "завідувач складу, комори (B1)",
      "gloss": "storekeeper, warehouseman, stock controller",
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
        "ipa": "[kɔmʲirˈnɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "комірни́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "істота"
        }
      },
      "distinction_note": "Не плутати з омографом «комі́рник» (наголос на другому складі: квартира́нт, пожилець)."
    }
  ],
  "копнути": [
    {
      "lemma": "копнути",
      "url_slug": "копнути",
      "headword": "ко́пнути",
      "short_label": "вдарити ногою (A2)",
      "gloss": "to kick once, give a kick with foot",
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
        "ipa": "[ˈkɔpnutɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́пнути",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «копну́ти» (наголос на другому складі: однократна дія від копати лопатою чи землерийним знаряддям)."
    },
    {
      "lemma": "копнути",
      "url_slug": "копнути",
      "headword": "копну́ти",
      "short_label": "вдарити лопатою, розкопати (A2)",
      "gloss": "to dig once, make a single stroke with a spade",
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
        "ipa": "[kɔpˈnutɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "копну́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «ко́пнути» (наголос на першому складі: вдарити ногою, копнути м'яч)."
    }
  ],
  "копчений": [
    {
      "lemma": "копчений",
      "url_slug": "копчений",
      "headword": "ко́пчений",
      "short_label": "дієприкметник: оброблений димом (B1)",
      "gloss": "smoked (passive participle: subjected to the smoking process)",
      "pos": "adjective",
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
        "ipa": "[ˈkɔpt͡ʃenɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́пчений",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «копче́ний» (наголос на другому складі: якісний прикметник, копчена риба, копчена ковбаса)."
    },
    {
      "lemma": "копчений",
      "url_slug": "копчений",
      "headword": "копче́ний",
      "short_label": "прикметник: копчені вироби (A2)",
      "gloss": "smoked (adjective: prepared by smoking, e.g. smoked sausage, fish)",
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
        "ipa": "[kɔpˈt͡ʃɛnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "копче́ний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «ко́пчений» (наголос на першому складі: віддієслівний дієприкметник від коптити)."
    }
  ],
  "крижовий": [
    {
      "lemma": "крижовий",
      "url_slug": "крижовий",
      "headword": "крижо́вий",
      "short_label": "хрестоподібний (заст. B2)",
      "gloss": "cruciform, cross-shaped (e.g. crossways, cruciform church plan; archaic)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured",
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[krɪˈʒɔwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "крижо́вий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «крижови́й» (наголос на третьому складі: анатомічний термін, пов'язаний з крижами хребта)."
    },
    {
      "lemma": "крижовий",
      "url_slug": "крижовий",
      "headword": "крижови́й",
      "short_label": "анатомічний: відділ хребта (B1)",
      "gloss": "sacral (anatomical: of/pertaining to the sacrum or sacral spine)",
      "pos": "adjective",
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
        "ipa": "[krɪʒɔˈwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "крижови́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «крижо́вий» (наголос на другому складі: хрестоподібний, у формі хреста)."
    }
  ],
  "денник": [
    {
      "lemma": "денник",
      "url_slug": "денник",
      "headword": "де́нник",
      "short_label": "щоденник (зах., заст.)",
      "gloss": "diary, personal daily journal (regional/archaic)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured",
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈdɛnːɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "де́нник",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «денни́к» (наголос на другому складі: ізольоване стійло для коня у стайні)."
    },
    {
      "lemma": "денник",
      "url_slug": "денник",
      "headword": "денни́к",
      "short_label": "стійло для коня в стайні (B1)",
      "gloss": "horse box, single enclosed stall in a stable",
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
        "ipa": "[dɛnˈnɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "денни́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «де́нник» (наголос на першому складі: щоденник у західноукраїнській традиції)."
    }
  ],
  "линути": [
    {
      "lemma": "линути",
      "url_slug": "линути",
      "headword": "ли́нути",
      "short_label": "летіти, ширяти, линути в думках (поет. B1)",
      "gloss": "to soar, fly, rush smoothly, float (of birds, sound, time; imperfective)",
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
        "ipa": "[ˈlɪnutɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ли́нути",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «лину́ти» (наголос на другому складі: линути раз, хлюпнути, доконаний вид)."
    },
    {
      "lemma": "линути",
      "url_slug": "линути",
      "headword": "лину́ти",
      "short_label": "хлюпнути, однократно лити (док. B1)",
      "gloss": "to pour once, splash once (instantaneous/perfective of лити)",
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
        "ipa": "[lɪˈnutɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "лину́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «ли́нути» (наголос на першому складі: летіти, ширяти, линути у вирій, недоконаний вид)."
    }
  ],
  "лікарський": [
    {
      "lemma": "лікарський",
      "url_slug": "лікарський",
      "headword": "лі́карський",
      "short_label": "належний лікареві (A2)",
      "gloss": "physician's, doctor's (e.g. doctor's visit, physician's coat)",
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
        "ipa": "[ˈlʲikɐrsʲkɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "лі́карський",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «ліка́рський» (наголос на другому складі: цілющий, лікувальний, аптечний)."
    },
    {
      "lemma": "лікарський",
      "url_slug": "лікарський",
      "headword": "ліка́рський",
      "short_label": "цілющий, лікувальний (A2)",
      "gloss": "medicinal, curative, pharmaceutical (e.g. medicinal herbs, healing plants)",
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
        "ipa": "[lʲiˈkarsʲkɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ліка́рський",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «лі́карський» (наголос на першому складі: пов'язаний з професією чи особою лікаря)."
    }
  ],
  "масниця": [
    {
      "lemma": "масниця",
      "url_slug": "масниця",
      "headword": "ма́сниця",
      "short_label": "свято проводів зими (A2)",
      "gloss": "Masnytsia (traditional Ukrainian pre-Lenten carnival festival, pancake/butter week)",
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
        "ipa": "[ˈmasnɪt͡sʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ма́сниця",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «масни́ця» (наголос на другому складі: діжка або глечик для збивання масла)."
    },
    {
      "lemma": "масниця",
      "url_slug": "масниця",
      "headword": "масни́ця",
      "short_label": "діжка для збивання масла (B2)",
      "gloss": "butter churn, tub used for churning fresh butter",
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
        "ipa": "[mɐsˈnɪt͡sʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "масни́ця",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «ма́сниця» (наголос на першому складі: свято зустрічі весни та проводів зими)."
    }
  ],
  "милування": [
    {
      "lemma": "милування",
      "url_slug": "милування",
      "headword": "ми́лування",
      "short_label": "помилування, пощада (B1)",
      "gloss": "act of sparing, pardoning, granting of mercy/clemency",
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
        "ipa": "[ˈmɪɫʊwɐnʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ми́лування",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "середній",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «милува́ння» (наголос на третьому складі: пестощі, ніжність або захоплення красою)."
    },
    {
      "lemma": "милування",
      "url_slug": "милування",
      "headword": "милува́ння",
      "short_label": "пестощі, захоплення красою (B1)",
      "gloss": "caressing, tender affection; or aesthetic contemplation, admiring gaze",
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
        "ipa": "[mɪɫʊˈwanʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "милува́ння",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "середній",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «ми́лування» (наголос на першому складі: дія за значенням ми́лувати, дарування пощади)."
    }
  ],
  "милувати": [
    {
      "lemma": "милувати",
      "url_slug": "милувати",
      "headword": "ми́лувати",
      "short_label": "жаліти, дарувати пощаду (B1)",
      "gloss": "to spare, show mercy, pardon, refrain from harming",
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
        "ipa": "[ˈmɪɫʊwɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ми́лувати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «милува́ти» (наголос на третьому складі: пестити, ніжити, ласкати)."
    },
    {
      "lemma": "милувати",
      "url_slug": "милувати",
      "headword": "милува́ти",
      "short_label": "пестити, ніжити (B1)",
      "gloss": "to caress, fondle, cuddle, treat affectionately",
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
        "ipa": "[mɪɫʊˈwatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "милува́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «ми́лувати» (наголос на першому складі: жаліти, дарувати пощаду, не завдавати шкоди)."
    }
  ],
  "мильниця": [
    {
      "lemma": "мильниця",
      "url_slug": "мильниця",
      "headword": "ми́льниця",
      "short_label": "підставка для мила (A1)",
      "gloss": "soap dish, soap case",
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
        "ipa": "[ˈmɪlʲnɪt͡sʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ми́льниця",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «мильни́ця» (наголос на другому складі: багаторічна трав'яниста рослина мильнянка, діалектне)."
    },
    {
      "lemma": "мильниця",
      "url_slug": "мильниця",
      "headword": "мильни́ця",
      "short_label": "рослина мильнянка (діал. B2)",
      "gloss": "soapwort plant (Saponaria officinalis, dialectal)",
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
        "ipa": "[mɪlʲˈnɪt͡sʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "мильни́ця",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «ми́льниця» (наголос на першому складі: коробочка або підставка для туалетного мила)."
    }
  ],
  "надмір": [
    {
      "lemma": "надмір",
      "url_slug": "надмір",
      "headword": "на́дмір",
      "short_label": "надлишок, зайвина (B1)",
      "gloss": "excess, surplus, profusion (e.g. surplus of water, excess of happiness)",
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
        "ipa": "[ˈnadmʲir]",
        "source": "VESUM"
      },
      "stress": {
        "form": "на́дмір",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «надмі́р» (наголос на другому складі: прислівник — надміру, занадто)."
    },
    {
      "lemma": "надмір",
      "url_slug": "надмір",
      "headword": "надмі́р",
      "short_label": "надміру, занадто (присл. B1)",
      "gloss": "excessively, overly, too much (synonymous with надмі́ру)",
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
        "ipa": "[nɐdˈmʲir]",
        "source": "VESUM"
      },
      "stress": {
        "form": "надмі́р",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «на́дмір» (наголос на першому складі: іменник — надлишок, зайвина)."
    }
  ],
  "названий": [
    {
      "lemma": "названий",
      "url_slug": "названий",
      "headword": "на́званий",
      "short_label": "якому дали ім'я чи назву (A2)",
      "gloss": "named, called, titled (passive participle: given a name)",
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
        "ipa": "[ˈnazwɐnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "на́званий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «назва́ний» (наголос на другому складі: прийомний, названий брат, названа мати)."
    },
    {
      "lemma": "названий",
      "url_slug": "названий",
      "headword": "назва́ний",
      "short_label": "прийомний, названий брат (B1)",
      "gloss": "adoptive, foster, sworn (e.g. sworn brother, foster parents)",
      "pos": "adjective",
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
        "ipa": "[nɐzˈwanɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "назва́ний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «на́званий» (наголос на першому складі: охарактеризований певним іменем чи назвою)."
    }
  ],
  "накидка": [
    {
      "lemma": "накидка",
      "url_slug": "накидка",
      "headword": "на́кидка",
      "short_label": "націнка, надбавка до плати (B2)",
      "gloss": "surcharge, fee increase, extra charge (action of adding to payment)",
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
        "ipa": "[ˈnakɪdkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "на́кидка",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «наки́дка» (наголос на другому складі: верхній одяг без рукавів або покривало на подушку чи ліжко)."
    },
    {
      "lemma": "накидка",
      "url_slug": "накидка",
      "headword": "наки́дка",
      "short_label": "плащ без рукавів, покривало (A2)",
      "gloss": "cape, cloak, loose sleeveless wrap, or decorative coverlet/throw",
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
        "ipa": "[nɐˈkɪdkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "наки́дка",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «на́кидка» (наголос на першому складі: надбавка до плати чи ціни, націнка)."
    }
  ],
  "наносити": [
    {
      "lemma": "наносити",
      "url_slug": "наносити",
      "headword": "нано́сити",
      "short_label": "вкривати шаром, креслити (B1)",
      "gloss": "to apply a layer/coat, plot on a map, deposit drift (paint, marks, sediment)",
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
        "ipa": "[nɐˈnɔsɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "нано́сити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «наноси́ти» (наголос на третьому складі: доконаний вид, наносити багато речей або води)."
    },
    {
      "lemma": "наносити",
      "url_slug": "наносити",
      "headword": "наноси́ти",
      "short_label": "принести у великій кількості (A2)",
      "gloss": "to bring/carry in large quantities (e.g. bring lots of water or firewood)",
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
        "ipa": "[nɐnɔˈsɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "наноси́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «нано́сити» (наголос на другому складі: недоконаний вид, покривати шаром або позначати на карті)."
    }
  ],
  "нападати": [
    {
      "lemma": "нападати",
      "url_slug": "нападати",
      "headword": "напа́дати",
      "short_label": "випасти у великій кількості (док. B1)",
      "gloss": "to fall and accumulate in quantity (e.g. fallen snow, leaves; perfective)",
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
        "ipa": "[nɐˈpadɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "напа́дати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «напада́ти» (наголос на третьому складі: атакувати, штурмувати, недоконаний вид)."
    },
    {
      "lemma": "нападати",
      "url_slug": "нападати",
      "headword": "напада́ти",
      "short_label": "атакувати, штурмувати (недок. A2)",
      "gloss": "to attack, assault, initiate an aggression (imperfective)",
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
        "ipa": "[nɐpɐˈdatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "напада́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «напа́дати» (наголос на другому складі: нападати купою, випасти у великій кількості, доконаний вид)."
    }
  ],
  "натискати": [
    {
      "lemma": "натискати",
      "url_slug": "натискати",
      "headword": "нати́скати",
      "short_label": "напхати, щільно набити (B2)",
      "gloss": "to cram, stuff full, pack tightly into a confined space",
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
        "ipa": "[nɐˈtɪskɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "нати́скати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «натиска́ти» (наголос на третьому складі: тиснути на кнопку чи клавішу)."
    },
    {
      "lemma": "натискати",
      "url_slug": "натискати",
      "headword": "натиска́ти",
      "short_label": "тиснути на кнопку, клавішу (A1)",
      "gloss": "to press, click, depress (a button, key, switch, or lever)",
      "pos": "verb",
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
        "ipa": "[nɐtɪsˈkatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "натиска́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «нати́скати» (наголос на другому складі: щільно напхати, набити купою)."
    }
  ],
  "націнка": [
    {
      "lemma": "націнка",
      "url_slug": "націнка",
      "headword": "на́цінка",
      "short_label": "сума надбавки до ціни (B1)",
      "gloss": "amount of markup, monetary sum added to increase price (the markup value)",
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
        "ipa": "[ˈnat͡sʲinkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "на́цінка",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «наці́нка» (наголос на другому складі: дія за значенням націнити — підвищення цін)."
    },
    {
      "lemma": "націнка",
      "url_slug": "націнка",
      "headword": "наці́нка",
      "short_label": "підвищення ціни, дія націнювання (B2)",
      "gloss": "act of raising prices, price increase action (action noun to націнити / націнювати)",
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
        "ipa": "[nɐˈt͡sʲinkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "наці́нка",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «на́цінка» (наголос на першому складі: сума, на яку підвищено ціну, торговельна надбавка)."
    }
  ],
  "нескладний": [
    {
      "lemma": "нескладний",
      "url_slug": "нескладний",
      "headword": "нескла́дний",
      "short_label": "незграбний, незлагоджений (B1)",
      "gloss": "discordant, clumsy, disjointed, incoherent (lacking harmony, proportion, or logic)",
      "pos": "adjective",
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
        "ipa": "[nɛˈskɫadnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "нескла́дний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «нескладни́й» (наголос на третьому складі: простий, нескладний для виконання)."
    },
    {
      "lemma": "нескладний",
      "url_slug": "нескладний",
      "headword": "нескладни́й",
      "short_label": "простий, неважкий (A2)",
      "gloss": "simple, uncomplicated, not difficult, easy to perform",
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
        "ipa": "[nɛskɫɐdˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "нескладни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «нескла́дний» (наголос на другому складі: незграбний, позбавлений гармонії чи логіки)."
    }
  ],
  "обруч": [
    {
      "lemma": "обруч",
      "url_slug": "обруч",
      "headword": "о́бруч",
      "short_label": "поруч, поряд (присл., рідко B2)",
      "gloss": "alongside, nearby, side by side (rare/conversational adverb synonymous with поруч)",
      "pos": "adverb",
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
        "ipa": "[ˈɔbrut͡ʃ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "о́бруч",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «обру́ч» (наголос на другому складі: іменник — круглий обід, кільце, гімнастичний чи бондарський снаряд)."
    },
    {
      "lemma": "обруч",
      "url_slug": "обруч",
      "headword": "обру́ч",
      "short_label": "кільце, обід, спортивний снаряд (A2)",
      "gloss": "hoop, rim, metal/wooden circular band (e.g. for a barrel or gymnastic hula hoop)",
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
        "ipa": "[ɔˈbrut͡ʃ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "обру́ч",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «о́бруч» (наголос на першому складі: прислівник — поруч, поряд)."
    }
  ],
  "осад": [
    {
      "lemma": "осад",
      "url_slug": "осад",
      "headword": "о́сад",
      "short_label": "гуща на дні, неприємний настрій (B1)",
      "gloss": "sediment, dregs, precipitate; emotional aftertaste of bitterness",
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
        "ipa": "[ˈɔsɐd]",
        "source": "VESUM"
      },
      "stress": {
        "form": "о́сад",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «оса́д» (наголос на другому складі: ярус, поверх будинку в давніх текстах)."
    },
    {
      "lemma": "осад",
      "url_slug": "осад",
      "headword": "оса́д",
      "short_label": "поверх, ярус споруди (заст.)",
      "gloss": "story, floor, architectural tier of a building (archaic)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured",
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ɔˈsad]",
        "source": "VESUM"
      },
      "stress": {
        "form": "оса́д",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «о́сад» (наголос на першому складі: тверді часточки на дні або неприємний душевний настрій)."
    }
  ],
  "парний": [
    {
      "lemma": "парний",
      "url_slug": "парний",
      "headword": "па́рний",
      "short_label": "у парі, парні числа (A1)",
      "gloss": "paired, twin; even (of numbers: divisible by two)",
      "pos": "adjective",
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
        "ipa": "[ˈparnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "па́рний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «парни́й» (наголос на другому складі: щойно надоєний, теплий, насичений парою)."
    },
    {
      "lemma": "парний",
      "url_slug": "парний",
      "headword": "парни́й",
      "short_label": "щойно надоєний, теплий (B1)",
      "gloss": "fresh-milked, steamy warm, humid (e.g. fresh warm milk, sultry air)",
      "pos": "adjective",
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
        "ipa": "[pɐrˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "парни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «па́рний» (наголос на першому складі: парні предмети, парні числа)."
    }
  ],
  "перебігати": [
    {
      "lemma": "перебігати",
      "url_slug": "перебігати",
      "headword": "перебі́гати",
      "short_label": "пробігати певний час (док. B2)",
      "gloss": "to spend/run through a period of time running (e.g. run barefoot through winter; perfective)",
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
        "ipa": "[pɛrɛˈbʲiɦɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "перебі́гати",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «перебіга́ти» (наголос на четвертому складі: пересуватися бігом з місця на місце, перетинати вулицю, недоконаний вид)."
    },
    {
      "lemma": "перебігати",
      "url_slug": "перебігати",
      "headword": "перебіга́ти",
      "short_label": "перетинати бігом (недок. A2)",
      "gloss": "to run across, cross by running (e.g. cross the street, move between shelters; imperfective)",
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
        "ipa": "[pɛrɛbʲiˈɦatɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "перебіга́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «перебі́гати» (наголос на третьому складі: бігати протягом певного часу, доконаний вид)."
    }
  ],
  "переводити": [
    {
      "lemma": "переводити",
      "url_slug": "переводити",
      "headword": "перево́дити",
      "short_label": "переміщати, марнувати (недок. A2)",
      "gloss": "to lead across, transfer; squander, waste (e.g. waste money/food; imperfective)",
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
        "ipa": "[pɛrɛˈwɔdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "перево́дити",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «переводи́ти» (наголос на четвертому складі: провести багатьох чи всіх людей кудись, доконаний вид)."
    },
    {
      "lemma": "переводити",
      "url_slug": "переводити",
      "headword": "переводи́ти",
      "short_label": "провести багатьох або всіх (док. B2)",
      "gloss": "to escort, lead across, or guide many/all people to a destination (perfective)",
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
        "ipa": "[pɛrɛwɔˈdɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "переводи́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «перево́дити» (наголос на третьому складі: переводити через дорогу або марнувати ресурси, недоконаний вид)."
    }
  ],
  "переломний": [
    {
      "lemma": "переломний",
      "url_slug": "переломний",
      "headword": "переломни́й",
      "short_label": "вирішальний, поворотний (B1)",
      "gloss": "turning-point, watershed, decisive, critical (e.g. turning point in history)",
      "pos": "adjective",
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
        "ipa": "[pɛrɛɫɔmˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "переломни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «перело́мний» (наголос на третьому складі: оптичний термін, що стосується заломлення світла чи хвиль)."
    },
    {
      "lemma": "переломний",
      "url_slug": "переломний",
      "headword": "перело́мний",
      "short_label": "фізичний: заломлювальний (B2)",
      "gloss": "refractive, refracting (physical: relating to refraction of rays/waves)",
      "pos": "adjective",
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
        "ipa": "[pɛrɛˈɫɔmnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "перело́мний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «переломни́й» (наголос на четвертому складі: вирішальний, визначальний для зміни напрямку розвитку)."
    }
  ],
  "переносний": [
    {
      "lemma": "переносний",
      "url_slug": "переносний",
      "headword": "перено́сний",
      "short_label": "метафоричний, алегоричний (A2)",
      "gloss": "figurative, metaphorical (e.g. metaphorical meaning, figurative sense)",
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
        "ipa": "[pɛrɛˈnɔsnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "перено́сний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «переносни́й» (наголос на четвертому складі: портативний, який можна переносити з місця на місце)."
    },
    {
      "lemma": "переносний",
      "url_slug": "переносний",
      "headword": "переносни́й",
      "short_label": "портативний, рухомий (A2)",
      "gloss": "portable, movable, transportable (e.g. portable computer, portable stove)",
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
        "ipa": "[pɛrɛnɔˈsnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "переносни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «перено́сний» (наголос на третьому складі: образний, ужитий у переносному значенні)."
    }
  ],
  "пересічний": [
    {
      "lemma": "пересічний",
      "url_slug": "пересічний",
      "headword": "пересі́чний",
      "short_label": "звичайний, середній (B1)",
      "gloss": "average, ordinary, typical (e.g. average citizen, median level)",
      "pos": "adjective",
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
        "ipa": "[pɛrɛˈsʲit͡ʃnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пересі́чний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «пересічни́й» (наголос на четвертому складі: геометрія чи планування, який перетинається з чимось)."
    },
    {
      "lemma": "пересічний",
      "url_slug": "пересічний",
      "headword": "пересічни́й",
      "short_label": "який перетинається (B2)",
      "gloss": "intersecting, transversal (e.g. intersecting streets, intersecting lines)",
      "pos": "adjective",
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
        "ipa": "[pɛrɛsʲiˈt͡ʃnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пересічни́й",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «пересі́чний» (наголос на третьому складі: звичайний, пересічний громадянин)."
    }
  ],
  "печений": [
    {
      "lemma": "печений",
      "url_slug": "печений",
      "headword": "пе́чений",
      "short_label": "дієприкметник: щойно спечений (B1)",
      "gloss": "baked (passive participle: prepared by baking in an oven)",
      "pos": "adjective",
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
        "ipa": "[ˈpɛt͡ʃenɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пе́чений",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «пече́ний» (наголос на другому складі: якісний прикметник, печена картопля, печене м'ясо)."
    },
    {
      "lemma": "печений",
      "url_slug": "печений",
      "headword": "пече́ний",
      "short_label": "прикметник: печені страви (A1)",
      "gloss": "baked, roasted (adjective: of food products, e.g. baked potato, roasted apples)",
      "pos": "adjective",
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
        "ipa": "[pɛˈt͡ʃɛnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пече́ний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «пе́чений» (наголос на першому складі: віддієслівний дієприкметник від пекти)."
    }
  ],
  "писнути": [
    {
      "lemma": "писнути",
      "url_slug": "писнути",
      "headword": "пи́снути",
      "short_label": "тонко пищати, писнути раз (A2)",
      "gloss": "to squeak, peep once (of a mouse, bird, or quiet whimper)",
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
        "ipa": "[ˈpɪsnutɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пи́снути",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «писну́ти» (наголос на другому складі: швидко написати кілька слів або рядків)."
    },
    {
      "lemma": "писнути",
      "url_slug": "писнути",
      "headword": "писну́ти",
      "short_label": "написати кілька слів (A2)",
      "gloss": "to drop a line, jot down, write a brief note",
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
        "ipa": "[pɪsˈnutɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "писну́ти",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «пи́снути» (наголос на першому складі: видати тонкий писк, тихо писнути)."
    }
  ],
  "підданий": [
    {
      "lemma": "підданий",
      "url_slug": "підданий",
      "headword": "пі́дданий",
      "short_label": "який зазнав впливу (B1)",
      "gloss": "subjected to, exposed to (e.g. subjected to criticism, tested by fire)",
      "pos": "adjective",
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
        "ipa": "[ˈpʲidːɐnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пі́дданий",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «підда́ний» (наголос на другому складі: громадянин чи підвладний правителя монархії)."
    },
    {
      "lemma": "підданий",
      "url_slug": "підданий",
      "headword": "підда́ний",
      "short_label": "громадянин монархії (B1)",
      "gloss": "subject of a realm, citizen of a monarchical state",
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
        "ipa": "[pʲidˈdanɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "підда́ний",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "істота"
        }
      },
      "distinction_note": "Не плутати з омографом «пі́дданий» (наголос на першому складі: дієприкметник, підданий випробуванню чи дії)."
    }
  ],
  "пікнік": [
    {
      "lemma": "пікнік",
      "url_slug": "пікнік",
      "headword": "пі́кнік",
      "short_label": "людина кремезної статури (заст. B2)",
      "gloss": "person of pyknic/stocky build, stocky individual with broad frame (archaic constitutional type)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured",
        "calque_warning": null
      },
      "pronunciation": {
        "ipa": "[ˈpʲiknʲik]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пі́кнік",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "істота"
        }
      },
      "distinction_note": "Не плутати з омографом «пікні́к» (наголос на другому складі: розважальна заміська прогулянка з частуванням)."
    },
    {
      "lemma": "пікнік",
      "url_slug": "пікнік",
      "headword": "пікні́к",
      "short_label": "відпочинок на природі (A1)",
      "gloss": "picnic, leisure outing with an outdoor meal",
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
        "ipa": "[pʲikˈnʲik]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пікні́к",
        "source": "ukrainian-word-stress"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «пі́кнік» (наголос на першому складі: людина міцної, кремезної статури)."
    }
  ],
  "копний": [
    {
      "lemma": "копний",
      "url_slug": "копний",
      "headword": "ко́пний",
      "short_label": "громадський, судновий (іст.)",
      "gloss": "communal, related to Ukrainian traditional community court (kopny sud)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[ˈkɔpnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ко́пний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «копни́й» (наголос на другому складі: не в'їжджений після снігопаду шлях).",
      "meaning": {
        "definitions": [
          "Громадський, судновий; прикм. до копа́ (традиційний сільський суд громади)."
        ],
        "source": "СУМ-20 (44007)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "КОПНИ́Й, а́, е́, заст. Прикм. до копа́ 4. — У нас коли скликають на копу, то скликають потиху, передаючи з хати до хати копне знамено (Фр., VI, 1951, 25). КО́ПНИЙ, а, е, розм. Не в’їжджений після снігопаду (про шлях). За лісом він не повернув до свого села, а пішов копною дорогою до тієї самотньої хатинки, де жила Мар’яна (Стельмах, II, 1962, 398).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "копний",
      "url_slug": "копний",
      "headword": "копни́й",
      "short_label": "не в'їжджений після снігопаду (про шлях)",
      "gloss": "untravelled after snowfall (of a winter road or path; kopna doroha)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[kɔpˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "копни́й",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «ко́пний» (наголос на першому складі: пов'язаний з копою як традиційною сільською громадою чи копним судом).",
      "meaning": {
        "definitions": [
          "Не в'їжджений після снігопаду (про шлях)."
        ],
        "source": "СУМ-20 (44008)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "КОПНИ́Й, а́, е́, заст. Прикм. до копа́ 4. — У нас коли скликають на копу, то скликають потиху, передаючи з хати до хати копне знамено (Фр., VI, 1951, 25). КО́ПНИЙ, а, е, розм. Не в’їжджений після снігопаду (про шлях). За лісом він не повернув до свого села, а пішов копною дорогою до тієї самотньої хатинки, де жила Мар’яна (Стельмах, II, 1962, 398).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "ланець": [
    {
      "lemma": "ланець",
      "url_slug": "ланець",
      "headword": "ла́нець",
      "short_label": "голодранець, лайливе (розм.)",
      "gloss": "ragamuffin, scamp, tramp (colloquial)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈlɑnɛtsʲ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ла́нець",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "істота"
        }
      },
      "distinction_note": "Не плутати з омографом «лане́ць» (наголос на другому складі: застаріла назва ланцюга).",
      "meaning": {
        "definitions": [
          "Одягнена в лахміття людина; старець, бродяга. Уживається як лайливе слово."
        ],
        "source": "СУМ-20 (46738)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛА́НЕЦЬ, нця, ч., розм. 1. Одягнена в лахміття людина; старець. Забравши деяких Троянців, Осмалених, як гиря, ланців, П’ятами з Трої накивав [Еней] (Котл., І, 1952, 65); — Я гоноровий шляхтич.., у мене є голка, щоб не ходить обірванцем, а ти гольтіпака, ланець, безштанько (Стор., І, 1957, 132); // Надзвичайно бідна людина; бідняк. Дивувалися й завидували Чіпці люди не менше Грицька. \"І як-таки за",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "ланець",
      "url_slug": "ланець",
      "headword": "лане́ць",
      "short_label": "ланцюг (заст.)",
      "gloss": "chain, small chain (archaic)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[lɐˈnɛtsʲ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "лане́ць",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «ла́нець» (наголос на першому складі: розмовне голодранець, шахрай).",
      "meaning": {
        "definitions": [
          "Ланцюг."
        ],
        "source": "СУМ-20 (46739)"
      },
      "soviet_colonization_context": null
    }
  ],
  "лучити": [
    {
      "lemma": "лучити",
      "url_slug": "лучити",
      "headword": "лу́чити",
      "short_label": "цілити, влучати (розм.)",
      "gloss": "to aim, hit the mark, strike a target (e.g. Лучив корову, а попав ворону)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈlutʃɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "лу́чити",
        "source": "СУМ-20 (48618)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «лучи́ти» (наголос на другому складі: єднати, сполучати докупи).",
      "meaning": {
        "definitions": [
          "Цілитися в кого-, що-небудь; влучати."
        ],
        "source": "СУМ-20 (48618)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛУ́ЧИТИ, чу, чиш, недок. і док., перех. і без додатка, розм. Цілитися в кого-, що-небудь. Лучив корову, а попав ворону (Номис, 1864, № 1784); // Те саме, що влуча́ти 1.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "лучити",
      "url_slug": "лучити",
      "headword": "лучи́ти",
      "short_label": "єднати, сполучати (діал.)",
      "gloss": "to unite, join, link, connect together (cf. сполучати, злучити)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[luˈtʃɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "лучи́ти",
        "source": "СУМ-20 (48619)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «лу́чити» (наголос на першому складі: цілити, влучати в ціль).",
      "meaning": {
        "definitions": [
          "Єднати, з'єднувати."
        ],
        "source": "СУМ-20 (48619)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛУЧИ́ТИСЯ², чу́ся, чи́шся, недок., діал. Єднатися. Нечуваний економічний гніт у панській Польщі лучив селян з робітниками.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "людний": [
    {
      "lemma": "людний",
      "url_slug": "людний",
      "headword": "лю́дний",
      "short_label": "багатолюдний (A2)",
      "gloss": "crowded, populous, full of people",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈlʲudnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "лю́дний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «людни́й» (наголос на другому складі: уважний до людей, людяний, привітний).",
      "meaning": {
        "definitions": [
          "Те саме, що багатолю́дний; наповнений людьми."
        ],
        "source": "СУМ-20 (48724)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛЮ́ДНИЙ, а, е. Те саме, що багатолю́дний. Збори були людні — зібралося ціле село (Рад. Укр., 31. III 1950, 2); [Галя:] Мені здається, добре б було учителькою стати… От, хоч і тут… Містечко тут велике, людне (Мирний, V, 1955, 157); Спинився [Саїд Алі] біля найбільш людної чайхани (Ле, Міжгір’я, 1953, 18); Який же він [шлях до міста] гучний, та людний, та порохний! (Вовчок, І, 1955, 288); Є у мене з",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "людний",
      "url_slug": "людний",
      "headword": "людни́й",
      "short_label": "привітний, людяний (рідко)",
      "gloss": "affable, humane, hospitable, sociable",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[lʲudˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "людни́й",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «лю́дний» (наголос на першому складі: багатолюдний, повний людей).",
      "meaning": {
        "definitions": [
          "Який перебуває серед людей, у товаристві; привітний, людяний."
        ],
        "source": "СУМ-20 (48725)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛЮ́ДНИЙ, а, е. Те саме, що багатолю́дний. Збори були людні — зібралося ціле село (Рад. Укр., 31. III 1950, 2); [Галя:] Мені здається, добре б було учителькою стати… От, хоч і тут… Містечко тут велике, людне (Мирний, V, 1955, 157); Спинився [Саїд Алі] біля найбільш людної чайхани (Ле, Міжгір’я, 1953, 18); Який же він [шлях до міста] гучний, та людний, та порохний! (Вовчок, І, 1955, 288); Є у мене з",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "опій": [
    {
      "lemma": "опій",
      "url_slug": "опій",
      "headword": "о́пій",
      "short_label": "опіум, болезаспокійливий сік (B1)",
      "gloss": "opium, narcotic analgesic substance dried from poppy heads",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈɔpij]",
        "source": "VESUM"
      },
      "stress": {
        "form": "о́пій",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «опі́й» (наголос на другому складі: ветеринарне запалення копит коней від надмірного напування).",
      "meaning": {
        "definitions": [
          "Згущений молочний сік недозрілих головок опійного маку; сильний наркотик."
        ],
        "source": "СУМ-20 (66548)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "О́ПІЙ, ю, ч. Висушений молочний сік з недозрілих маківок, який є сильним наркотиком; використовується в медицині як болезаспокійливий і снотворний засіб.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "опій",
      "url_slug": "опій",
      "headword": "опі́й",
      "short_label": "опой, запалення копит у коней (вет.)",
      "gloss": "equine hoof inflammation, founder / excessive watering sickness in horses (vet., cf. Грінченко: хвороба у тварин від гарячого пойла)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-historism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[ɔˈpij]",
        "source": "VESUM"
      },
      "stress": {
        "form": "опі́й",
        "source": "СУМ-20 (66549)"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «о́пій» (наголос на першому складі: опіум, лікарська/наркотична речовина).",
      "meaning": {
        "definitions": [
          "Ревматичне запалення копит у коней, спричинене напуванням розгарячілих тварин."
        ],
        "source": "СУМ-20 (66549)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "О́ПІЙ, ю, ч. Висушений молочний сік з недозрілих маківок. [СУМ-11 не фіксує опі́й, зафіксовано в Грінченка 1907 та СУМ-20 ст. 66549].",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "плавний": [
    {
      "lemma": "плавний",
      "url_slug": "плавний",
      "headword": "пла́вний",
      "short_label": "гладкий, рівномірний (B1)",
      "gloss": "smooth, flowing, fluent, continuous, without abrupt jerks",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈplɑu̯nɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пла́вний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «плавни́й» (наголос на другому складі: плавучий, сплавний; або стосовний до плавнів — річкових заплав).",
      "meaning": {
        "definitions": [
          "Рівний, без різких переходів, нешвидкий (про рухи, звуки, мову і т. ін.)."
        ],
        "source": "СУМ-20 (78497)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ВНИЙ, а, е. Рівний, без різких переходів, нешвидкий (про рухи, звуки, мову і т. ін.).",
        "sovietization_risk": 1,
        "keywords": [
          "соціалістичн"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "плавний",
      "url_slug": "плавний",
      "headword": "плавни́й",
      "short_label": "плавучий; стосовний до плавнів (B2)",
      "gloss": "floating, drifting, buoyant (e.g. плавна сітка, cf. Грінченко: пловучій); relating to river floodplains, marshlands (plavni)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[plɐu̯ˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "плавни́й",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «пла́вний» (наголос на першому складі: рівномірний, плавний рух чи звук).",
      "meaning": {
        "definitions": [
          "Здатний рухатися у воді, пристосований до плавання; водоплавний, плавучий."
        ],
        "source": "СУМ-20 (78498)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ВНИЙ, а, е. Рівний, без різких переходів, нешвидкий (про рухи, звуки, мову і т. ін.).",
        "sovietization_risk": 1,
        "keywords": [
          "соціалістичн"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "платина": [
    {
      "lemma": "платина",
      "url_slug": "платина",
      "headword": "пла́тина",
      "short_label": "хімічний елемент Pt (B1)",
      "gloss": "platinum (noble precious metal)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈplɑtɪnɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пла́тина",
        "source": "СУМ-20 (78711)"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «плати́на» (наголос на другому складі: народно-діалектна назва хустки).",
      "meaning": {
        "definitions": [
          "Хімічний елемент з атомним номером 78, благородний метал сріблясто-білого кольору."
        ],
        "source": "СУМ-20 (78711)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ТИНА, и, ж. Хімічний елемент сірувато-білого кольору, благородний метал. ПЛАТИ́НА, и, ж., діал. Хустка. У хвіртку входить старий диякон з речами, належними до хрещення, зав’язаними в платину (Васильч., III, 1960, 24).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "платина",
      "url_slug": "платина",
      "headword": "плати́на",
      "short_label": "хустка, платок (діал.)",
      "gloss": "kerchief, headscarf, traditional cloth (dialectal / folk, cf. Грінченко: платок; плат, полотно)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[plɐˈtɪnɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "плати́на",
        "source": "СУМ-20 (78712)"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «пла́тина» (наголос на першому складі: благородний метал платина). Не плутати з російським словом «плотина» (українською: «гребля», «гатка»).",
      "meaning": {
        "definitions": [
          "Хустка."
        ],
        "source": "СУМ-20 (78712)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛАТИ́НА, и, ж., діал. Хустка. У хвіртку входить старий диякон з речами, належними до хрещення, зав’язаними в платину (Васильч., III, 1960, 24).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "платний": [
    {
      "lemma": "платний",
      "url_slug": "платний",
      "headword": "пла́тний",
      "short_label": "який оплачується (A2)",
      "gloss": "paid, fee-paying, commercial, salaried",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈplɑtnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пла́тний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «платни́й» (наголос на другому складі: платіжний, придатний до сплати).",
      "meaning": {
        "definitions": [
          "Який здійснюється, надається за плату; за користування яким стягується плата."
        ],
        "source": "СУМ-20 (78729)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ТНИЙ, а, е. 1. Який дається, надається за плату; який підлягає оплаті. Платна відпустка; Платні заняття; Платні лекції. 2. Який одержує плату, винагороду за роботу, послугу і т. ін. — Два-три роки мине, заким буду платна вчителька (Коб., III, 1956, 362); Правда: нема в нас того звичаю, аби свідок був платний. Свідоцтво — сусідська річ (Март., Тв., 1954, 210). ПЛАТНИ́Й, а́, е́, розм. 1. Який ро",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "платний",
      "url_slug": "платний",
      "headword": "платни́й",
      "short_label": "платіжний, здатний платити (рідко)",
      "gloss": "payable, solvent, related to payment capabilities",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[plɐtˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "платни́й",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «пла́тний» (наголос на першому складі: послуга чи вхід за плату).",
      "meaning": {
        "definitions": [
          "Який може, спроможний заплатити, розплатитися; платоспроможний."
        ],
        "source": "СУМ-20 (78730)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ТНИЙ, а, е. 1. Який дається, надається за плату; який підлягає оплаті. Платна відпустка; Платні заняття; Платні лекції. 2. Який одержує плату, винагороду за роботу, послугу і т. ін. — Два-три роки мине, заким буду платна вчителька (Коб., III, 1956, 362); Правда: нема в нас того звичаю, аби свідок був платний. Свідоцтво — сусідська річ (Март., Тв., 1954, 210). ПЛАТНИ́Й, а́, е́, розм. 1. Який ро",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "плодовий": [
    {
      "lemma": "плодовий",
      "url_slug": "плодовий",
      "headword": "плодо́вий",
      "short_label": "фруктовий, садовий (B1)",
      "gloss": "fruit-bearing, pomological (e.g. плодові дерева, плодовий сад)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[plɔˈdɔwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "плодо́вий",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «плодови́й» (наголос на третьому складі: плідний, родючий).",
      "meaning": {
        "definitions": [
          "Прикм. до плід; який дає їстівні плоди (про дерева, кущі)."
        ],
        "source": "СУМ-20 (79018)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛОДО́ВИЙ, а, е. 1. Прикм. до плід 1. Плодовий м’якуш столових гарбузів становить за вагою (в середньому) 73% (Укр. страви, 1957, 209); // Пригот. з плодів. Готове плодове та ягідне вино зберігають в сухому підвальному приміщенні при температурі 5-12 градусів (Колг. Укр., 7, 1956, 41); // У якому містяться органи розмноження, запліднення. Плодове тіло гриба. 2. Який дає їстівні плоди. Наш народ ша",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "плодовий",
      "url_slug": "плодовий",
      "headword": "плодови́й",
      "short_label": "родючий, плодючий (рідко)",
      "gloss": "fertile, fruitful, fecund",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[plɔdɔˈwɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "плодови́й",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «плодо́вий» (наголос на другому складі: пов'язаний із фруктовими плодами та садом).",
      "meaning": {
        "definitions": [
          "Прикм. до плід (зародок людини або тварини в утробі матері)."
        ],
        "source": "СУМ-20 (79019)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛОДО́ВИЙ, а, е. 1. Прикм. до плід 1. Плодовий м’якуш столових гарбузів становить за вагою (в середньому) 73% (Укр. страви, 1957, 209); // Пригот. з плодів. Готове плодове та ягідне вино зберігають в сухому підвальному приміщенні при температурі 5-12 градусів (Колг. Укр., 7, 1956, 41); // У якому містяться органи розмноження, запліднення. Плодове тіло гриба. 2. Який дає їстівні плоди. Наш народ ша",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "поворотний": [
    {
      "lemma": "поворотний",
      "url_slug": "поворотний",
      "headword": "поворо́тний",
      "short_label": "обертовий, вирішальний (B1)",
      "gloss": "turning, pivotal, revolving, rotating (e.g. поворотний пункт)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔwɔˈrɔtnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "поворо́тний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «поворотни́й» (наголос на останньому складі: зворотний, реверсивний).",
      "meaning": {
        "definitions": [
          "Який служить для повертання чого-небудь; переломний, який докорінно змінює щось; зворотний."
        ],
        "source": "СУМ-20 (80540)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОВОРО́ТНИЙ, а, е. 1. Який служить для повертання чого-небудь. При складних рельєфах шляхів і великій протяжності ліній тяговий трос підвішується на підтримуючих роликах, на поворотах встановлюються спеціальні поворотні ролики (Наука.., 6, 1956, 22). 2. перен. Який докорінно змінює щось; переломний. Великий Жовтень став поворотним пунктом в історії людства, в долі всіх народів нашої країни (Ком. У",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "поворотний",
      "url_slug": "поворотний",
      "headword": "поворотни́й",
      "short_label": "зворотний, який повертається (рідко)",
      "gloss": "returnable, reversible, returning",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔwɔrɔtˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "поворотни́й",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «поворо́тний» (наголос на передостанньому складі: обертовий або вирішальний момент).",
      "meaning": {
        "definitions": [
          "Те саме, що поворотки́й; спритний, моторний, верткий."
        ],
        "source": "СУМ-20 (80541)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОВОРО́ТНИЙ, а, е. 1. Який служить для повертання чого-небудь. При складних рельєфах шляхів і великій протяжності ліній тяговий трос підвішується на підтримуючих роликах, на поворотах встановлюються спеціальні поворотні ролики (Наука.., 6, 1956, 22). 2. перен. Який докорінно змінює щось; переломний. Великий Жовтень став поворотним пунктом в історії людства, в долі всіх народів нашої країни (Ком. У",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "покидати": [
    {
      "lemma": "покидати",
      "url_slug": "покидати",
      "headword": "поки́дати",
      "short_label": "пошпурити все (док.)",
      "gloss": "to throw all or multiple items, hurl (perfective)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔˈkɪdɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "поки́дати",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «покида́ти» (наголос на третьому складі: недоконане дієслово «залишати когось/щось»).",
      "meaning": {
        "definitions": [
          "Кинути все або багато чого-небудь, багатьох; кинути без догляду (док.)."
        ],
        "source": "СУМ-20 (82829)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОКИ́ДАТИ, аю, аєш, док., перех. 1. Кинути все або багато чого-небудь, всіх або багатьох. Ватя підвелася навшпиньки, нарвала яблук і покидала їх на траву (Н.-Лев., IV, 1956, 121); Тепер всі як один покидали ложки (Головко, II, 1957, 239); // Абияк, недбало кинути все або багато чого-небудь. Спасибі, Петро оборонив, і відра позбирав, що я з ляку покидала, та проводив мене знов до криниці (Кв.-Осн.,",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "покидати",
      "url_slug": "покидати",
      "headword": "покида́ти",
      "short_label": "залишати, кидати (недок., A2)",
      "gloss": "to abandon, leave behind, forsake, desert (imperfective)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔkɪˈdɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "покида́ти",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «поки́дати» (наголос на другому складі: доконане дієслово «пошпурити багато речей»).",
      "meaning": {
        "definitions": [
          "Вирушаючи кудись, залишати кого-, що-небудь; кидати, іти від когось (недок.)."
        ],
        "source": "СУМ-20 (82830)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОКИ́ДАТИ, аю, аєш, док., перех. 1. Кинути все або багато чого-небудь, всіх або багатьох. Ватя підвелася навшпиньки, нарвала яблук і покидала їх на траву (Н.-Лев., IV, 1956, 121); Тепер всі як один покидали ложки (Головко, II, 1957, 239); // Абияк, недбало кинути все або багато чого-небудь. Спасибі, Петро оборонив, і відра позбирав, що я з ляку покидала, та проводив мене знов до криниці (Кв.-Осн.,",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "покій": [
    {
      "lemma": "покій",
      "url_slug": "покій",
      "headword": "по́кій",
      "short_label": "спокій, тиша (B1)",
      "gloss": "peace, tranquility, rest, quietness, spiritual composure",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈpɔkij]",
        "source": "VESUM"
      },
      "stress": {
        "form": "по́кій",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «покі́й» (наголос на другому складі: кімната, світлиця, панські покої).",
      "meaning": {
        "definitions": [
          "Відсутність руху і шуму; тиша; душевна рівновага, спокій."
        ],
        "source": "СУМ-20 (82852)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́КІЙ, ко́ю, ч., заст. 1. Відсутність руху і шуму; тиша. Південь наближавсь, Угамувався мир дібровний; В таємних надрах лісу став Покій, словами невимовний (Щог., Поезії, 1958, 320); // Тихе, мирне життя, згода. [Петро:] Він те [закон] установлює, дбаючи про мир та покій у сім’ ї, а ще більше він дбає про всесвітній мир (Мирний, V, 1955, 177); // Мир, примирення. Візьміть назад свої гостинці, Одп",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "покій",
      "url_slug": "покій",
      "headword": "покі́й",
      "short_label": "кімната, покої (A2)",
      "gloss": "room, chamber, apartment (usually in plural покої)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔˈkij]",
        "source": "VESUM"
      },
      "stress": {
        "form": "покі́й",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «по́кій» (наголос на першому складі: спокій, мир, тиша).",
      "meaning": {
        "definitions": [
          "Те саме, що кімна́та; пишне, багате житлове приміщення."
        ],
        "source": "СУМ-20 (82853)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́КІЙ, ко́ю, ч., заст. 1. Відсутність руху і шуму; тиша. Південь наближавсь, Угамувався мир дібровний; В таємних надрах лісу став Покій, словами невимовний (Щог., Поезії, 1958, 320); // Тихе, мирне життя, згода. [Петро:] Він те [закон] установлює, дбаючи про мир та покій у сім’ ї, а ще більше він дбає про всесвітній мир (Мирний, V, 1955, 177); // Мир, примирення. Візьміть назад свої гостинці, Одп",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "помилувати": [
    {
      "lemma": "помилувати",
      "url_slug": "помилувати",
      "headword": "поми́лувати",
      "short_label": "приголубити, попестити (док., B1)",
      "gloss": "to caress, cuddle, pet, pamper (perfective)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔˈmɪluwɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "поми́лувати",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «помилува́ти» (наголос на третьому складі: пробачити провину, дарувати життя чи помилування).",
      "meaning": {
        "definitions": [
          "Скасувати або пом'якшити кару, до якої засуджено; проявити милосердя (док. до ми́лувати)."
        ],
        "source": "СУМ-20 (84248)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОМИ́ЛУВАТИ, ую, уєш, док., перех. 1. Простити кому-небудь провину, виявити поблажливість до когось. Краще десять винних помилувати, ніж одного невинного покарати (Укр.. присл.., 1963, 145); Її серце чує, що, коли син прийде, припаде до ніг старого, повиниться у всьому, — батько і помилує, і пожалує (Мирний, IV, 1955, 42); Ганні здалося, ніби в голосі його вже звучить прохання помилувати, простити",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "помилувати",
      "url_slug": "помилувати",
      "headword": "помилува́ти",
      "short_label": "пробачити провину (док., B1)",
      "gloss": "to pardon, grant clemency, have mercy, forgive (perfective)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔmɪluˈwɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "помилува́ти",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «поми́лувати» (наголос на другому складі: пригорнути, попестити).",
      "meaning": {
        "definitions": [
          "Пестити, голубити якийсь час (док. до милува́ти)."
        ],
        "source": "СУМ-20 (84249)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОМИ́ЛУВАТИ, ую, уєш, док., перех. 1. Простити кому-небудь провину, виявити поблажливість до когось. Краще десять винних помилувати, ніж одного невинного покарати (Укр.. присл.., 1963, 145); Її серце чує, що, коли син прийде, припаде до ніг старого, повиниться у всьому, — батько і помилує, і пожалує (Мирний, IV, 1955, 42); Ганні здалося, ніби в голосі його вже звучить прохання помилувати, простити",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "поміж": [
    {
      "lemma": "поміж",
      "url_slug": "поміж",
      "headword": "по́між",
      "short_label": "поряд, підряд (діал.)",
      "gloss": "side by side, consecutively, in a row (dialectal / archaic)",
      "pos": "adverb",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[ˈpɔm⁽ʲ⁾iʒ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "по́між",
        "source": "Грінченко (1907)"
      },
      "morphology": {
        "pos": "прислівник",
        "paradigm": {
          "kind": "adverb"
        }
      },
      "distinction_note": "Не плутати з омографом «помі́ж» (наголос на другому складі: поширений прийменник «між», «серед»).",
      "meaning": {
        "definitions": [
          "Поряд; підряд (присл.)."
        ],
        "source": "СУМ-20 (84284)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́МІЖ, присл., діал. 1. Поряд. 2. Підряд. У трьох дворах поміж вигинула скотина (Сл. Гр.). ПОМІ́Ж, рідше ПОМЕ́ЖИ, прийм. Уживається з род., знах. і оруд. відмінками. Сполучення з пом́іж виражають: Просторові відношення 1. з оруд., рідше з род. і знах. в. Уживається при означенні просторового розташування предмета або вияву дії посередині чого-небудь. І ще довго потім було чуть музики та співи між",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "поміж",
      "url_slug": "поміж",
      "headword": "помі́ж",
      "short_label": "між, серед (прийм., A2)",
      "gloss": "between, among, amidst (preposition)",
      "pos": "preposition",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔˈm⁽ʲ⁾iʒ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "помі́ж",
        "source": "СУМ-20 / ВТС"
      },
      "morphology": {
        "pos": "прийменник",
        "paradigm": {
          "kind": "preposition"
        }
      },
      "distinction_note": "Не плутати з омографом «по́між» (наголос на першому складі: діалектний прислівник «поряд», «підряд»).",
      "meaning": {
        "definitions": [
          "Уживається при означенні розташування або дії посередині чого-небудь; серед, між (прийм.)."
        ],
        "source": "СУМ-20 (84285)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́МІЖ, присл., діал. 1. Поряд. 2. Підряд. У трьох дворах поміж вигинула скотина (Сл. Гр.). ПОМІ́Ж, рідше ПОМЕ́ЖИ, прийм. Уживається з род., знах. і оруд. відмінками. Сполучення з пом́іж виражають: Просторові відношення 1. з оруд., рідше з род. і знах. в. Уживається при означенні просторового розташування предмета або вияву дії посередині чого-небудь. І ще довго потім було чуть музики та співи між",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "поносити": [
    {
      "lemma": "поносити",
      "url_slug": "поносити",
      "headword": "поно́сити",
      "short_label": "ганьбити, лаяти (недок., B2)",
      "gloss": "to revile, slander, disparage, abuse verbally (imperfective)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔˈnɔsɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "поно́сити",
        "source": "СУМ-20 (84983)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «поноси́ти» (наголос на третьому складі: доконане дієслово «носити деякий час»).",
      "meaning": {
        "definitions": [
          "Лаяти, ганьбити, паплюжити кого-небудь."
        ],
        "source": "СУМ-20 (233385)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОНО́СИТИ, о́шу, о́сиш, недок., перех., рідко. Лаяти, судити кого-небудь. То ж поносили сусіди ту саму сусідку, якій ще недавнечко й стежку до свого двору промітали… (Л. Янов., І, 1959, 305); — Що ми — послідні які, що вона поносить нас, увесь рід? (Мирний, IV, 1955, 58). ПОНОСИ́ТИ, ошу́, о́сиш, док., перех. 1. Носити що-небудь якийсь час. Вже Олена дружечок збира, коровайниці вже досі діжу по хат",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "поносити",
      "url_slug": "поносити",
      "headword": "поноси́ти",
      "short_label": "носити деякий час (док., A2)",
      "gloss": "to carry or wear for a while (perfective)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔnɔˈsɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "поноси́ти",
        "source": "СУМ-20 (84984)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «поно́сити» (наголос на другому складі: лаяти, ганьбити).",
      "meaning": {
        "definitions": [
          "Носити що-небудь якийсь час; перенести багато чогось куди-небудь."
        ],
        "source": "СУМ-20 (84984)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОНО́СИТИ, о́шу, о́сиш, недок., перех., рідко. Лаяти, судити кого-небудь. То ж поносили сусіди ту саму сусідку, якій ще недавнечко й стежку до свого двору промітали… (Л. Янов., І, 1959, 305); — Що ми — послідні які, що вона поносить нас, увесь рід? (Мирний, IV, 1955, 58). ПОНОСИ́ТИ, ошу́, о́сиш, док., перех. 1. Носити що-небудь якийсь час. Вже Олена дружечок збира, коровайниці вже досі діжу по хат",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "порання": [
    {
      "lemma": "порання",
      "url_slug": "порання",
      "headword": "по́рання",
      "short_label": "господарювання, догляд біля хати (B1)",
      "gloss": "household chores, tidying, tending near hearth or livestock (from поратися)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈpɔrɐnʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "по́рання",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "середній",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «пора́ння» (наголос на другому складі: рання пора, ранок, поранок).",
      "meaning": {
        "definitions": [
          "Дія за знач. по́рати і по́ратися (робота біля худоби, по господарству)."
        ],
        "source": "СУМ-20 (86497)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́РАННЯ, я, с. Дія за знач. по́рати і по́ратися. В хаті і надворі.. Скрізь порання: печуть, варять, Вимітають, миють… (Шевч., I, 1963, 316).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "порання",
      "url_slug": "порання",
      "headword": "пора́ння",
      "short_label": "ранок, рання пора (діал.)",
      "gloss": "early morning, dawn, early time of day (cf. поранок; ВТС та СУМ-20 ст. 86498)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[pɔˈrɑnʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пора́ння",
        "source": "СУМ-20 (86498)"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "середній",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «по́рання» (наголос на першому складі: хатня праця біля печі чи худоби, від «поратися»).",
      "meaning": {
        "definitions": [
          "Рання, ранкова пора."
        ],
        "source": "СУМ-20 (86498)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́РАННЯ, я, с. Дія за знач. по́рати і по́ратися. [СУМ-11 не виділяє пора́ння окремою статтею; зафіксовано у ВТС та СУМ-20 ст. 86498].",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "похідний": [
    {
      "lemma": "похідний",
      "url_slug": "похідний",
      "headword": "похі́дний",
      "short_label": "табірний, експедиційний (B1)",
      "gloss": "marching, camp, field, expeditionary (relating to a march/campaign, e.g. похідний порядок, похідна кухня)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔˈx⁽ʲ⁾idnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "похі́дний",
        "source": "СУМ-20 (88947)"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «похідни́й» (наголос на закінченні: утворений від іншого, дериват, похідна величина чи функція).",
      "meaning": {
        "definitions": [
          "Стос. до походу; який буває в поході, польовий (похідна кухня, похідний намет)."
        ],
        "source": "СУМ-20 (88947)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОХІ́ДНИЙ, а, е. 1. Стос. до походу (у 1, 3 знач.); який буває, виробляється в поході.",
        "sovietization_risk": 1,
        "keywords": [
          "ленін",
          "маркс"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "похідний",
      "url_slug": "похідний",
      "headword": "похідни́й",
      "short_label": "утворений, деривативний (B1)",
      "gloss": "derived, secondary, derivative (e.g. похідне слово, похідна величина, похідна функція в математиці)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔx⁽ʲ⁾idˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "похідни́й",
        "source": "СУМ-20 (88948)"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «похі́дний» (наголос на другому складі: стосовний до військового походу чи експедиції).",
      "meaning": {
        "definitions": [
          "Утворений, виведений з іншого первинного (похідне слово, похідна функція)."
        ],
        "source": "СУМ-20 (88948)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОХІ́ДНИЙ, а, е. ... 2. Утворений від іншого, вторинний.",
        "sovietization_risk": 1,
        "keywords": [
          "ленін",
          "маркс"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "прикладний": [
    {
      "lemma": "прикладний",
      "url_slug": "прикладний",
      "headword": "при́кладний",
      "short_label": "зразковий, доладний (рідко)",
      "gloss": "exemplary, model, neatly fitting",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈprɪkɫɐdnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "при́кладний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «прикладни́й» (наголос на третьому складі: практичний, ужитковий — прикладне мистецтво, прикладна лінгвістика).",
      "meaning": {
        "definitions": [
          "Доладний, підхожий, показний (діал.)."
        ],
        "source": "СУМ-20 (91203)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРИ́КЛАДНИЙ, а, е, діал. Доладний. Весела, чудовна місцина! Кращої і прикладнішої назви, як Веселий Кут, не можна було пригадати їй (Мирний, III, 1954, 293); Силував [Славко] свій мозок придумати якусь фразу.. Мозок працював сильно, але прикладні думки не приходили (Март., Тв., 1954, 368). ПРИКЛАДНИ́Й, а, е. Який має практичне значення, не теоретичний. — Я поважаю тільки науку прикладну, соціальну",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "прикладний",
      "url_slug": "прикладний",
      "headword": "прикладни́й",
      "short_label": "ужитковий, практичний (B1)",
      "gloss": "applied, practical (e.g. прикладна наука, прикладне мистецтво)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɪkɫɐdˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "прикладни́й",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «при́кладний» (наголос на першому складі: зразковий, доладний).",
      "meaning": {
        "definitions": [
          "Який має практичне значення, не теоретичний (прикладна лінгвістика, прикладні науки)."
        ],
        "source": "СУМ-20 (91204)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРИ́КЛАДНИЙ, а, е, діал. Доладний. Весела, чудовна місцина! Кращої і прикладнішої назви, як Веселий Кут, не можна було пригадати їй (Мирний, III, 1954, 293); Силував [Славко] свій мозок придумати якусь фразу.. Мозок працював сильно, але прикладні думки не приходили (Март., Тв., 1954, 368). ПРИКЛАДНИ́Й, а, е. Який має практичне значення, не теоретичний. — Я поважаю тільки науку прикладну, соціальну",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "прилавок": [
    {
      "lemma": "прилавок",
      "url_slug": "прилавок",
      "headword": "при́лавок",
      "short_label": "лава в традиційній хаті (етногр.)",
      "gloss": "traditional built-in wall bench in a Ukrainian village house",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-ethnographism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[ˈprɪɫɐwɔk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "при́лавок",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «прила́вок» (наголос на другому складі: торговельний стіл у крамниці).",
      "meaning": {
        "definitions": [
          "Частина нерухомої лави в традиційній українській хаті під стіною від дверей до кутка."
        ],
        "source": "СУМ-20 (91373)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРИ́ЛАВОК, вка, ч. Частина нерухомої лави в українській хаті під стіною від дверей до кутка. Я за піч так і вхопилась, а потім і сіла на прилавок (Барв., Опов.., 1902, 83); Соломія склала на прилавку перемиті миски та полумиски (Н.-Лев., VI, 1966, 400). ПРИЛА́ВОК, вка, ч. Спеціальний стіл для торгівлі в крамниці, буфеті, на базарі і т. ін. Оттак думаючи, я був уже на Бернардинській площі, де здовж",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "прилавок",
      "url_slug": "прилавок",
      "headword": "прила́вок",
      "short_label": "торговельний стіл у крамниці (A2)",
      "gloss": "shop counter, sales stall, service desk",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɪˈɫɑwɔk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "прила́вок",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «при́лавок» (наголос на першому складі: нерухома лава в українській оселі).",
      "meaning": {
        "definitions": [
          "Спеціальний стіл для торгівлі в крамниці, буфеті або на ринку."
        ],
        "source": "СУМ-20 (91374)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРИ́ЛАВОК, вка, ч. Частина нерухомої лави в українській хаті під стіною від дверей до кутка. Я за піч так і вхопилась, а потім і сіла на прилавок (Барв., Опов.., 1902, 83); Соломія склала на прилавку перемиті миски та полумиски (Н.-Лев., VI, 1966, 400). ПРИЛА́ВОК, вка, ч. Спеціальний стіл для торгівлі в крамниці, буфеті, на базарі і т. ін. Оттак думаючи, я був уже на Бернардинській площі, де здовж",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "примітка": [
    {
      "lemma": "примітка",
      "url_slug": "примітка",
      "headword": "при́мітка",
      "short_label": "прикмета, знак (діал.)",
      "gloss": "sign, omen, distinctive trait (dialectal)",
      "pos": "noun",
      "cefr": null,
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[ˈprɪm⁽ʲ⁾itkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "при́мітка",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «примі́тка» (наголос на другому складі: пояснення чи коментар у тексті).",
      "meaning": {
        "definitions": [
          "Прикмета, розпізнавальний знак."
        ],
        "source": "СУМ-20 (91636)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРИ́МІТКА, и, ж., діал. Прикмета. У нас примітка така: вгадуєш, як сонце заходить, — коли червоно — буде вітер (Сл. Гр.); Подивиться [баба], які примітки на небі: чи ясні зірки — то то вже на мороз; чи торгають — то на вітер; чи з вухами місяць — то вже на люту зиму (Дн. Чайка, Тв., 1960, 28). ◊ Бра́ти (взя́ти) в при́мітку — помічати. Співає пташка, і ніхто Не взяв її в примітку! (Кост., І, 1967,",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "примітка",
      "url_slug": "примітка",
      "headword": "примі́тка",
      "short_label": "коментар, виноска в тексті (A2)",
      "gloss": "note, footnote, explanatory annotation, remark",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɪˈm⁽ʲ⁾itkɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "примі́тка",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "жіночий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «при́мітка» (наголос на першому складі: народна прикмета).",
      "meaning": {
        "definitions": [
          "Короткий запис, пояснення або коментар до тексту; виноска."
        ],
        "source": "СУМ-20 (91637)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРИ́МІТКА, и, ж., діал. Прикмета. У нас примітка така: вгадуєш, як сонце заходить, — коли червоно — буде вітер (Сл. Гр.); Подивиться [баба], які примітки на небі: чи ясні зірки — то то вже на мороз; чи торгають — то на вітер; чи з вухами місяць — то вже на люту зиму (Дн. Чайка, Тв., 1960, 28). ◊ Бра́ти (взя́ти) в при́мітку — помічати. Співає пташка, і ніхто Не взяв її в примітку! (Кост., І, 1967,",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "пробігати": [
    {
      "lemma": "пробігати",
      "url_slug": "пробігати",
      "headword": "пробі́гати",
      "short_label": "побігати певний час (док., B1)",
      "gloss": "to run around for a certain time (perfective)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔˈbʲiɦɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пробі́гати",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «пробіга́ти» (наголос на третьому складі: недоконане дієслово «бігти повз або крізь щось»).",
      "meaning": {
        "definitions": [
          "Побігати певний час; бігаючи, пропустити або проґавити щось (док.)."
        ],
        "source": "СУМ-20 (93472)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРОБІ́ГАТИ, аю, аєш, док. 1. неперех. Бігати якийсь час. Макар пробігав по багнюці і під дощем дві години (Смолич, І, 1947, 149). 2. перех., розм. Бігаючи, пропустити, упустити що-небудь. [Марта:] Добридень вам, Горпино Корніївно! Ой, вибачте мені, кумцю-голубцю! Бігала з бубликами та трохи не пробігала ваших святих іменин (Н.-Лев., II, 1956, 504). ПРОБІГА́ТИ, а́ю, а́єш, недок., ПРОБІ́ГТИ, біжу́,",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "пробігати",
      "url_slug": "пробігати",
      "headword": "пробіга́ти",
      "short_label": "бігти повз, мчати (недок., A2)",
      "gloss": "to run past, traverse by running, flit across (imperfective)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔbʲiˈɦɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пробіга́ти",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «пробі́гати» (наголос на другому складі: доконане дієслово «бігати якийсь час»).",
      "meaning": {
        "definitions": [
          "Бігом пересуватися звідкись кудись; швидко проходити (про час, відстань) (недок.)."
        ],
        "source": "СУМ-20 (93473)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРОБІ́ГАТИ, аю, аєш, док. 1. неперех. Бігати якийсь час. Макар пробігав по багнюці і під дощем дві години (Смолич, І, 1947, 149). 2. перех., розм. Бігаючи, пропустити, упустити що-небудь. [Марта:] Добридень вам, Горпино Корніївно! Ой, вибачте мені, кумцю-голубцю! Бігала з бубликами та трохи не пробігала ваших святих іменин (Н.-Лев., II, 1956, 504). ПРОБІГА́ТИ, а́ю, а́єш, недок., ПРОБІ́ГТИ, біжу́,",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "пробування": [
    {
      "lemma": "пробування",
      "url_slug": "пробування",
      "headword": "про́бування",
      "short_label": "тестування, куштування (B1)",
      "gloss": "trying, tasting, testing, sampling (from пробувати)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈprɔbuwɐnʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "про́бування",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "середній",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «пробува́ння» (наголос на третьому складі: перебування, проживання десь).",
      "meaning": {
        "definitions": [
          "Дія за знач. про́бувати (випробовування, спроба, дегустація)."
        ],
        "source": "СУМ-20 (93561)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́БУВАННЯ, я, с. Дія за знач. про́бувати. ПРОБУВА́ННЯ, я, с. 1. Стан за знач. пробува́ти. Він поглядав на столик, на розгорнуту книжку, на сліди недавнього материного пробування в гостиній (Н.-Лев., VI, 1966, 19); Чи знайоме вам те гостре, до фізичного болю гостре почуття нудьги за рідною країною, яким обкипає серце від довгого пробування на чужині? (Коцюб., І, 1955, 177). 2. у сполуч. із сл. мі",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "пробування",
      "url_slug": "пробування",
      "headword": "пробува́ння",
      "short_label": "перебування, проживання (B2)",
      "gloss": "sojourn, stay, residence, dwelling (from пробувати/перебувати)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔbuˈwɑnʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пробува́ння",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "середній",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «про́бування» (наголос на першому складі: дія зі значенням «тестувати/куштувати на смак»).",
      "meaning": {
        "definitions": [
          "Перебування де-небудь; проживання, стан за знач. пробува́ти."
        ],
        "source": "СУМ-20 (93562)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́БУВАННЯ, я, с. Дія за знач. про́бувати. ПРОБУВА́ННЯ, я, с. 1. Стан за знач. пробува́ти. Він поглядав на столик, на розгорнуту книжку, на сліди недавнього материного пробування в гостиній (Н.-Лев., VI, 1966, 19); Чи знайоме вам те гостре, до фізичного болю гостре почуття нудьги за рідною країною, яким обкипає серце від довгого пробування на чужині? (Коцюб., І, 1955, 177). 2. у сполуч. із сл. мі",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "провидіння": [
    {
      "lemma": "провидіння",
      "url_slug": "провидіння",
      "headword": "прови́діння",
      "short_label": "передбачення (B1)",
      "gloss": "foresight, clairvoyance, premonition, anticipation",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔˈwɪd⁽ʲ⁾inʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "прови́діння",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "середній",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «провиді́ння» (наголос на третьому складі: Боже Провидіння, вища небесна воля).",
      "meaning": {
        "definitions": [
          "Дія за знач. прови́діти (передбачення, здатність бачити майбутнє)."
        ],
        "source": "СУМ-20 (93681)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРОВИ́ДІННЯ, я, с. Дія за знач. прови́діти. Не слід вбачати в цьому звертанні Хмельницького до Росії акт якогось провидіння, властиве тільки йому розуміння історичних шляхів свого народу. Тяжіння до возз’єднання з єдиновірною Росією жило давно і в народі, і серед інтелігенції (Довж., III, 1960, 80). ПРОВИДІ́ННЯ, я, с. За релігійними віруваннями — дія уявної надприродної істоти, бога; вища сила.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "провидіння",
      "url_slug": "провидіння",
      "headword": "провиді́ння",
      "short_label": "Боже Провидіння (B2)",
      "gloss": "Providence, divine governance, supreme destiny",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔwɪˈd⁽ʲ⁾inʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "провиді́ння",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "середній",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «прови́діння» (наголос на другому складі: здатність передбачати події).",
      "meaning": {
        "definitions": [
          "Вища божественна сила, промисел Божий; найвища сила, що керує світом."
        ],
        "source": "СУМ-20 (93682)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРОВИ́ДІННЯ, я, с. Дія за знач. прови́діти. Не слід вбачати в цьому звертанні Хмельницького до Росії акт якогось провидіння, властиве тільки йому розуміння історичних шляхів свого народу. Тяжіння до возз’єднання з єдиновірною Росією жило давно і в народі, і серед інтелігенції (Довж., III, 1960, 80). ПРОВИДІ́ННЯ, я, с. За релігійними віруваннями — дія уявної надприродної істоти, бога; вища сила.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "провід": [
    {
      "lemma": "провід",
      "url_slug": "провід",
      "headword": "про́від",
      "short_label": "керівництво; електричний дріт, кабель (B1)",
      "gloss": "1. leadership, guidance, steering committee, direction; 2. electrical wire, cable, conductor conduit",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈprɔw⁽ʲ⁾id]",
        "source": "VESUM"
      },
      "stress": {
        "form": "про́від",
        "source": "СУМ-20 (93707)"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «прові́д» (наголос на другому складі, родовий прово́ду: дія за значенням проводити, провадження чи супровід).",
      "meaning": {
        "definitions": [
          "Керівництво, організаторська діяльність; також електричний дріт, кабельна лінія."
        ],
        "source": "СУМ-20 (93707)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́ВІД, воду, ч. 1. Те саме, що су́провід... 3. Металевий дріт (перев. ізольований), признач. для передавання електричного струму.",
        "sovietization_risk": 2,
        "keywords": [
          "більшов",
          "комсомол",
          "ленін"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "провід",
      "url_slug": "провід",
      "headword": "прові́д",
      "short_label": "провадження, здійснення (B2)",
      "gloss": "action of conducting, carrying out, conveyance, leading, guidance action (from проводити; gen. прово́ду)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔˈw⁽ʲ⁾id]",
        "source": "VESUM"
      },
      "stress": {
        "form": "прові́д",
        "source": "СУМ-20 (93708)"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «про́від» (наголос на першому складі: керівний орган чи електричний дріт).",
      "meaning": {
        "definitions": [
          "Те саме, що прове́дення (проводи в армію, проводи зими; проведення заходу)."
        ],
        "source": "СУМ-20 (93708)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́ВІД, воду, ч. Дія за знач. проводи́ти.",
        "sovietization_risk": 2,
        "keywords": [
          "більшов",
          "комсомол",
          "ленін"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "прокидатися": [
    {
      "lemma": "прокидатися",
      "url_slug": "прокидатися",
      "headword": "проки́датися",
      "short_label": "кидатися певний час (рідко)",
      "gloss": "to toss, fling, or throw repeatedly for a while (rare)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔˈkɪdɐtɪsʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "проки́датися",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «прокида́тися» (наголос на третьому складі: прокидатися від сну).",
      "meaning": {
        "definitions": [
          "Кидатися якийсь час; пограти в карти чи кістки певний час (док.)."
        ],
        "source": "СУМ-20 (94615)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРОКИ́ДАТИСЯ, аюся, аєшся, док., рідко. Кидатися (у 2, 4, 6 знач.) якийсь час. ПРОКИДА́ТИСЯ, а́юся, а́єшся, недок., ПРОКИ́НУТИСЯ, нуся, нешся, док. 1. Переставати спати, дрімати; пробуджуватися від сну; будитися, просипатися. Спав [Котигорошко] день, спав ніч, прокидається, — прив’язаний (Укр.. казки, 1951, 96); Вночі прокидаюсь, сідаю на ліжко й напружено слухаю (Коцюб., ІІ,1955,231); Прокидаєтьс",
        "sovietization_risk": 1,
        "keywords": [
          "ленін"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "прокидатися",
      "url_slug": "прокидатися",
      "headword": "прокида́тися",
      "short_label": "будитися, переривати сон (A1)",
      "gloss": "to wake up, awaken, arouse from sleep",
      "pos": "verb",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔkɪˈdɑtɪsʲɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "прокида́тися",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «проки́датися» (наголос на другому складі: метатися або кидатися якийсь час).",
      "meaning": {
        "definitions": [
          "Переставати спати, пробуджуватися від сну (недок.)."
        ],
        "source": "СУМ-20 (94616)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРОКИ́ДАТИСЯ, аюся, аєшся, док., рідко. Кидатися (у 2, 4, 6 знач.) якийсь час. ПРОКИДА́ТИСЯ, а́юся, а́єшся, недок., ПРОКИ́НУТИСЯ, нуся, нешся, док. 1. Переставати спати, дрімати; пробуджуватися від сну; будитися, просипатися. Спав [Котигорошко] день, спав ніч, прокидається, — прив’язаний (Укр.. казки, 1951, 96); Вночі прокидаюсь, сідаю на ліжко й напружено слухаю (Коцюб., ІІ,1955,231); Прокидаєтьс",
        "sovietization_risk": 1,
        "keywords": [
          "ленін"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "проклятий": [
    {
      "lemma": "проклятий",
      "url_slug": "проклятий",
      "headword": "про́клятий",
      "short_label": "підданий прокльону (дієприкм., B1)",
      "gloss": "cursed, damned (passive past participle of проклясти)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈprɔklʲɐtɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "про́клятий",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «прокля́тий» (наголос на другому складі: розмовний прикметник «клятий, ненависний, мерзенний»).",
      "meaning": {
        "definitions": [
          "Пасивний дієприкметник до проклясти́; підданий прокляттю."
        ],
        "source": "СУМ-20 (94661)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́КЛЯТИЙ, ПРО́КЛЯТ, а, е. Дієпр. пас. мин. ч. до прокля́сти́. Проклятій від матері не треба жити меж людьми… земля не здержить… (Кв.-Осн., II, 1956, 456); Кров висисає оте остогиджене, Прокляте нишком шиття, Що паненя, вередливе, зманіжене, Вишвирне геть на сміття (Граб., І, 1959, 52); *У порівн. [Микита:] Вони щасливі, їх доля сміється, їх доля дбає; а я, мов проклятий, мов матір’ю проплаканий,",
        "sovietization_risk": 1,
        "keywords": [
          "ленін",
          "пролетар"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "проклятий",
      "url_slug": "проклятий",
      "headword": "прокля́тий",
      "short_label": "клятий, ненависний (B1)",
      "gloss": "damned, hateful, detestable, wretched, confounded",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔˈklʲɑtɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "прокля́тий",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «про́клятий» (наголос на першому складі: дієприкметник «той, кого прокляли»).",
      "meaning": {
        "definitions": [
          "Якого проклинають, ненавидять; клятий, нестерпний (прикм.)."
        ],
        "source": "СУМ-20 (94662)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́КЛЯТИЙ, ПРО́КЛЯТ, а, е. Дієпр. пас. мин. ч. до прокля́сти́. Проклятій від матері не треба жити меж людьми… земля не здержить… (Кв.-Осн., II, 1956, 456); Кров висисає оте остогиджене, Прокляте нишком шиття, Що паненя, вередливе, зманіжене, Вишвирне геть на сміття (Граб., І, 1959, 52); *У порівн. [Микита:] Вони щасливі, їх доля сміється, їх доля дбає; а я, мов проклятий, мов матір’ю проплаканий,",
        "sovietization_risk": 1,
        "keywords": [
          "ленін",
          "пролетар"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "пролог": [
    {
      "lemma": "пролог",
      "url_slug": "пролог",
      "headword": "про́лог",
      "short_label": "житійний збірник (іст., церк.)",
      "gloss": "synaxarion, menologium, collection of short saints' lives",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true,
        "warning_severity": "treasured"
      },
      "pronunciation": {
        "ipa": "[ˈprɔɫɔɦ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "про́лог",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «проло́г» (наголос на другому складі: літературний або театральний вступ).",
      "meaning": {
        "definitions": [
          "Давній церковнослов'янський збірник житій святих та повчань за календарем; синаксар."
        ],
        "source": "СУМ-20 (94908)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́ЛОГ, а, ч., літ., іст. Так звані житія святих, подані відповідно до днів їх поминання. Наявність творів південнослов’янської житійної літератури в рукописних прологах, четьях-мінеях,.. псалтирях, місяцесловах.. сприяла їх поширенню та популяризації (Рад. літ-во, 11, 1971, 40). ПРОЛО́Г, а, ч. Вступна частина літературного або музичного твору. Дії [п’єс XVIII ст.] передує звичайно пролог, що в з",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "пролог",
      "url_slug": "пролог",
      "headword": "проло́г",
      "short_label": "вступ до твору (B1)",
      "gloss": "prologue, preface, literary introduction, prelude",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[prɔˈɫɔɦ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "проло́г",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «про́лог» (наголос на першому складі: давній збірник житій святих).",
      "meaning": {
        "definitions": [
          "Вступна частина літературного, драматичного чи музичного твору; початок чого-небудь."
        ],
        "source": "СУМ-20 (94909)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́ЛОГ, а, ч., літ., іст. Так звані житія святих, подані відповідно до днів їх поминання. Наявність творів південнослов’янської житійної літератури в рукописних прологах, четьях-мінеях,.. псалтирях, місяцесловах.. сприяла їх поширенню та популяризації (Рад. літ-во, 11, 1971, 40). ПРОЛО́Г, а, ч. Вступна частина літературного або музичного твору. Дії [п’єс XVIII ст.] передує звичайно пролог, що в з",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "рапорт": [
    {
      "lemma": "рапорт",
      "url_slug": "рапорт",
      "headword": "ра́порт",
      "short_label": "офіційне повідомлення, звіт (B1)",
      "gloss": "official report, military dispatch, report to superiors",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈrɑpɔrt]",
        "source": "VESUM"
      },
      "stress": {
        "form": "ра́порт",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «рапо́рт» (наголос на другому складі: елемент орнаменту тканини чи килима).",
      "meaning": {
        "definitions": [
          "Усне або письмове офіційне повідомлення чи донесення начальству, керівництву."
        ],
        "source": "СУМ-20 (98173)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РА́ПОРТ, у, ч. 1. Усне або письмове офіційне повідомлення про що-небудь вищій інстанції, керівництву. Всю ніч Кутузов приймав генералів, що один за одним, з’являлися з рапортами (Кочура, Зол. грамота, 1960, 302); Політрук вислухав короткий рапорт ординарця з батальйону про призначення старшого лейтенанта, товариша Билини, командиром роти (Ле, Право.., 1957, 163); Йшов [дід] простоволосий, повторюю",
        "sovietization_risk": 1,
        "keywords": [
          "піонер",
          "соціалістичн"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "рапорт",
      "url_slug": "рапорт",
      "headword": "рапо́рт",
      "short_label": "повторюваний елемент візерунка (B2)",
      "gloss": "pattern repeat, recurring unit in textile or ornamental design",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɐˈpɔrt]",
        "source": "VESUM"
      },
      "stress": {
        "form": "рапо́рт",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "неістота"
        }
      },
      "distinction_note": "Не плутати з омографом «ра́порт» (наголос на першому складі: військове або службове донесення).",
      "meaning": {
        "definitions": [
          "Базовий повторюваний елемент візерунка чи орнаменту на тканині, шпалерах, килимі."
        ],
        "source": "СУМ-20 (98174)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РА́ПОРТ, у, ч. 1. Усне або письмове офіційне повідомлення про що-небудь вищій інстанції, керівництву. Всю ніч Кутузов приймав генералів, що один за одним, з’являлися з рапортами (Кочура, Зол. грамота, 1960, 302); Політрук вислухав короткий рапорт ординарця з батальйону про призначення старшого лейтенанта, товариша Билини, командиром роти (Ле, Право.., 1957, 163); Йшов [дід] простоволосий, повторюю",
        "sovietization_risk": 1,
        "keywords": [
          "піонер",
          "соціалістичн"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "рефлекторний": [
    {
      "lemma": "рефлекторний",
      "url_slug": "рефлекторний",
      "headword": "рефле́кторний",
      "short_label": "відбивальний, пов'язаний з рефлектором (B2)",
      "gloss": "reflector-related, specular, reflective (e.g. рефлекторна лампа)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɛˈflɛktɔrnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "рефле́кторний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «рефлекто́рний» (наголос на третьому складі: пов'язаний із нервовим рефлексом або мимовільною реакцією).",
      "meaning": {
        "definitions": [
          "Стос. до рефлектора як оптичного приладу або відбивача світла/тепла."
        ],
        "source": "СУМ-20 (99152)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РЕФЛЕ́КТОРНИЙ, а, е. Стос. до рефлектора. РЕФЛЕКТО́РНИЙ, а, е. Стос. до рефлексу (у 1 знач.). Інстинктивна поведінка являє собою не що інше, як ланцюговий рефлекс, тобто ряд послідовних рефлекторних рухів (Психол., 1956, 15); У наш час класична рефлекторна теорія поповнилася дуже важливими новими фактами (Знання.., 4, 1971, 13); // Який відбувається, проходить і т. ін. мимовільно, несвідомо. ∆ Реф",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "рефлекторний",
      "url_slug": "рефлекторний",
      "headword": "рефлекто́рний",
      "short_label": "мимовільний, нервовий рефлекс (B1)",
      "gloss": "reflexive, involuntary, neurological reflex-based (e.g. рефлекторний рух)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɛflɛkˈtɔrnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "рефлекто́рний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «рефле́кторний» (наголос на другому складі: пов'язаний з оптичним рефлектором/відбивачем).",
      "meaning": {
        "definitions": [
          "Пов'язаний з біологічним або фізіологічним рефлексом; мимовільний."
        ],
        "source": "СУМ-20 (99153)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РЕФЛЕ́КТОРНИЙ, а, е. Стос. до рефлектора. РЕФЛЕКТО́РНИЙ, а, е. Стос. до рефлексу (у 1 знач.). Інстинктивна поведінка являє собою не що інше, як ланцюговий рефлекс, тобто ряд послідовних рефлекторних рухів (Психол., 1956, 15); У наш час класична рефлекторна теорія поповнилася дуже важливими новими фактами (Знання.., 4, 1971, 13); // Який відбувається, проходить і т. ін. мимовільно, несвідомо. ∆ Реф",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "розвідник": [
    {
      "lemma": "розвідник",
      "url_slug": "розвідник",
      "headword": "розві́дник",
      "short_label": "військовий розвідник, скаут (A2)",
      "gloss": "reconnaissance scout, intelligence agent, scout plane/vessel",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɔzˈw⁽ʲ⁾idnɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "розві́дник",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "істота"
        }
      },
      "distinction_note": "Не плутати з омографом «розвідни́к» (наголос на третьому складі: майстер із розведення зубців пилки).",
      "meaning": {
        "definitions": [
          "Військовослужбовець розвідки; агент розвідувальної служби або розвідувальний апарат."
        ],
        "source": "СУМ-20 (100470)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РОЗВІ́ДНИК, а, ч. 1. Той, хто займається розвідкою або перебуває у розвідці ( див. ро́зві́дка³ 1, 2). Коли хто-небудь з розвідників відповідав нечітко або не уточнив в час розвідки якоїсь деталі, Степан Юхимович дуже сердився (Збан., Над Десною, 1951, 10); Треба спочатку послати в Яблуневію розвідників, які б вивідали, що за сили у ворога і де вони розташовані (Донч., V, 1957, 184). 2. Літак для п",
        "sovietization_risk": 1,
        "keywords": [
          "комуністичн"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "розвідник",
      "url_slug": "розвідник",
      "headword": "розвідни́к",
      "short_label": "фахівець розведення зубців пилки (спец.)",
      "gloss": "saw set specialist, saw setter",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɔzw⁽ʲ⁾idˈnɪk]",
        "source": "VESUM"
      },
      "stress": {
        "form": "розвідни́к",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "чоловічий",
          "animacy": "істота"
        }
      },
      "distinction_note": "Не плутати з омографом «розві́дник» (наголос на другому складі: військовий розвідник, дізнавач).",
      "meaning": {
        "definitions": [
          "Фахівець або інструмент для розведення зубців пилки."
        ],
        "source": "СУМ-20 (100471)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РОЗВІ́ДНИК, а, ч. 1. Той, хто займається розвідкою або перебуває у розвідці ( див. ро́зві́дка³ 1, 2). Коли хто-небудь з розвідників відповідав нечітко або не уточнив в час розвідки якоїсь деталі, Степан Юхимович дуже сердився (Збан., Над Десною, 1951, 10); Треба спочатку послати в Яблуневію розвідників, які б вивідали, що за сили у ворога і де вони розташовані (Донч., V, 1957, 184). 2. Літак для п",
        "sovietization_risk": 1,
        "keywords": [
          "комуністичн"
        ],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "роздільний": [
    {
      "lemma": "роздільний",
      "url_slug": "роздільний",
      "headword": "розді́льний",
      "short_label": "поетапний, відокремлений (A2)",
      "gloss": "separate, distinct, fractional, step-by-step (e.g. роздільний збір сміття)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɔzˈd⁽ʲ⁾ilʲnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "розді́льний",
        "source": "СУМ-20 (100936)"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «роздільни́й» (наголос на третьому складі: спеціалізований термін у виразах «роздільна здатність», «роздільний знак»).",
      "meaning": {
        "definitions": [
          "Який ділиться на послідовні етапи або частини; відокремлений, самостійний (роздільне харчування, роздільний збір)."
        ],
        "source": "СУМ-20 (100936)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РОЗДІ́ЛЬНИЙ, а, е. 1. Який ділиться на послідовні етапи або частини. Роздільне збирання зернових культур сприяє економії праці на сушінні і очистці зерна, зменшує втрати врожаю (Наука.., 8, 1956, 29); // Який полягає у здійсненні таких етапів. Збирання гречки провадиться роздільним способом (Хлібороб Укр., 7, 1973, 22). 2. Який діє, відбувається і т. ін. окремо від чогось іншого; відокремлений. У",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "роздільний",
      "url_slug": "роздільний",
      "headword": "роздільни́й",
      "short_label": "розмежувальний (роздільна здатність, роздільний знак)",
      "gloss": "dividing, resolving, separating (e.g. роздільна здатність - resolution)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɔzd⁽ʲ⁾ilʲˈnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "роздільни́й",
        "source": "ВТС / ULIF"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «розді́льний» (наголос на другому складі: роздільний санвузол, роздільне харчування).",
      "meaning": {
        "definitions": [
          "Який служить для розмежування або вимірювання чіткості (роздільна здатність, розділовий/роздільний знак)."
        ],
        "source": "ВТС / ULIF"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РОЗДІ́ЛЬНИЙ, а, е. 1. Який ділиться на послідовні етапи або частини. Роздільне збирання зернових культур сприяє економії праці на сушінні і очистці зерна, зменшує втрати врожаю (Наука.., 8, 1956, 29); // Який полягає у здійсненні таких етапів. Збирання гречки провадиться роздільним способом (Хлібороб Укр., 7, 1973, 22). 2. Який діє, відбувається і т. ін. окремо від чогось іншого; відокремлений. У",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "сапати": [
    {
      "lemma": "сапати",
      "url_slug": "сапати",
      "headword": "са́пати",
      "short_label": "сопіти, важко дихати (недок., B1)",
      "gloss": "to breathe heavily, pant, snort, wheeze (from сап/сопіти)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈsɑpɐtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "са́пати",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «сапа́ти» (наголос на другому складі: полоти бур'ян сапою на городі).",
      "meaning": {
        "definitions": [
          "Видавати носом свистячі звуки, важко дихати; сопіти."
        ],
        "source": "ВТС / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СА́ПАТИ, аю, аєш, недок. 1. Видавати носом свистячі звуки, важко дихаючи. Борис ішов звільна,.. сапаючи (Фр., III, 1950, 86); Хома сердито сапав (Коцюб., II, 1955, 85); Було чути лише, як шелестить на деревах листя та важко сапають коні (Тют., Вир, 1964, 338). 2. чим і без додатка, перен. Утворювати свистячі звуки, випускаючи газ, пару і т. ін. (про механізми, машини). Він [паровий млин] то дихав",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "сапати",
      "url_slug": "сапати",
      "headword": "сапа́ти",
      "short_label": "полоти бур'ян сапою (недок., A2)",
      "gloss": "to hoe, weed with a hoe, loosen soil with a hoe (from сапа)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sɐˈpɑtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "сапа́ти",
        "source": "ВТС / ULIF"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «са́пати» (наголос на першому складі: важко сопіти носом).",
      "meaning": {
        "definitions": [
          "Полоти бур'ян, підпушувати ґрунт сапою (недок.)."
        ],
        "source": "ВТС / ULIF"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СА́ПАТИ, аю, аєш, недок. 1. Видавати носом свистячі звуки, важко дихаючи. Борис ішов звільна,.. сапаючи (Фр., III, 1950, 86); Хома сердито сапав (Коцюб., II, 1955, 85); Було чути лише, як шелестить на деревах листя та важко сапають коні (Тют., Вир, 1964, 338). 2. чим і без додатка, перен. Утворювати свистячі звуки, випускаючи газ, пару і т. ін. (про механізми, машини). Він [паровий млин] то дихав",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "гукнути": [
    {
      "lemma": "гукнути",
      "url_slug": "гукнути",
      "headword": "гу́кнути",
      "short_label": "гуркнути, гримнути, лунко вибухнути",
      "gloss": "to boom, crash, roar, thud, rumble (гуркнути; resound with a crash, thud, blast or loud horn)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈɦuknʊtɪ]"
      },
      "stress": {
        "form": "гу́кнути",
        "source": "СУМ-20 (20522)",
        "url": "https://sum20ua.com/?wordid=20522"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Означає «гуркнути, видати гуркіт чи глухий звук» (Орфографічний словник: гу́кнути = гуркнути; наприклад, гукнули гармати). Не плутати з «гукну́ти» (наголос на кінці: крикнути, покликати когось).",
      "meaning": {
        "definitions": [
          "(гуркнути) Однократне до гу́кати; видати глухий гуркіт, гримнути, лунко зазвучати (про гармати, поїзд, гаківниці)."
        ],
        "source": "СУМ-20 (20522) / Орфографічний словник"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ГУ́КНУ́ТИ, гу́кну́, гу́кне́ш, док., розм. Однокр. до гу́кати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "гукнути",
      "url_slug": "гукнути",
      "headword": "гукну́ти",
      "short_label": "крикнути, покликати когось голосним окриком",
      "gloss": "to shout, cry out, call to summon someone (крикнути, покликати; shout aloud to call a person)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ɦʊkˈnutɪ]"
      },
      "stress": {
        "form": "гукну́ти",
        "source": "СУМ-20 (20523)",
        "url": "https://sum20ua.com/?wordid=20523"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Означає «крикнути, покликати людину голосним окриком» (Орфографічний словник: гукну́ти = крикнути, покликати). Не плутати з «гу́кнути» (наголос на першому складі: гуркнути, лунко зазвучати).",
      "meaning": {
        "definitions": [
          "(крикнути, покликати) Однократне до гука́ти; голосно крикнути, озватися або покликати кого-небудь."
        ],
        "source": "СУМ-20 (20523) / Орфографічний словник"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ГУКНУ́ТИ, ну́, не́ш, док., кого і без прям. дод. Однокр. до гука́ти 1.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "балувати": [
    {
      "lemma": "балувати",
      "url_slug": "балувати",
      "headword": "ба́лувати",
      "short_label": "пестити, розпещувати, потурати примхам",
      "gloss": "to pamper, spoil, indulge someone's whims (e.g. балувати дітей)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈbɑlʊwɐtɪ]"
      },
      "stress": {
        "form": "ба́лувати",
        "source": "СУМ-20 (2480)",
        "url": "https://sum20ua.com/?wordid=2480"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «балува́ти» (наголос на -ва́ти: гуляти на балах, бенкетувати).",
      "meaning": {
        "definitions": [
          "Надмірно пестити когось, потурати чиїмось бажанням і примхам; виявляти надмірну увагу."
        ],
        "source": "СУМ-20 (2480)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БА́ЛУВАТИ, ую, уєш, недок., перех. 1. Надмірно пестити когось, потурати кому-небудь в його бажаннях і примхах.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "балувати",
      "url_slug": "балувати",
      "headword": "балува́ти",
      "short_label": "гуляти на балах, бенкетувати (заст.)",
      "gloss": "to revel, feast, attend balls (Хто змолоду балує, той під старість старцює)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[bɐlʊˈwɑtɪ]"
      },
      "stress": {
        "form": "балува́ти",
        "source": "СУМ-20 (2481)",
        "url": "https://sum20ua.com/?wordid=2481"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з дієсловом «ба́лувати» (наголос на першому складі: пестити, розпещувати).",
      "meaning": {
        "definitions": [
          "(розм., заст.) Гуляти на балах; бенкетувати, розкошувати."
        ],
        "source": "СУМ-20 (2481) / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БАЛУВА́ТИ, у́ю, у́єш, недок., розм. Гуляти на балах; бенкетувати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), виданому всупереч імперським російським заборонам українського слова (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "дихання": [
    {
      "lemma": "дихання",
      "url_slug": "дихання",
      "headword": "ди́хання",
      "short_label": "дихання, газообмін; подих (стандартне літер.)",
      "gloss": "respiration, breathing process, gas exchange; breath, breeze (standard literary form)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈdɪxɐnʲːɐ]"
      },
      "stress": {
        "form": "ди́хання",
        "source": "СУМ-20 (22439)",
        "url": "https://sum20ua.com/?wordid=22439"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "neuter",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Стандартний нормативний наголос на першому складі (ди́хання). Охоплює як фізіологічний газообмін, так і значення подиху чи віяння.",
      "meaning": {
        "definitions": [
          "1. Процес поглинання кисню і виділення вуглекислоти живими організмами (газообмін). 2. Подих, подув, віяння; наближення, настання чого-небудь."
        ],
        "source": "СУМ-20 (22439)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДИ́ХАННЯ, я, с. 1. Процес поглинання кисню і виділення вуглекислоти живими організмами; газообмін... 2. Віддих, подих...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "дихання",
      "url_slug": "дихання",
      "headword": "диха́ння",
      "short_label": "те саме, що ди́хання (діал., заст.)",
      "gloss": "dialectal accentual variant of ди́хання (same meaning: respiration, breath; attested dialectally and in Grinchenko 1907)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[dɪˈxanʲːɐ]"
      },
      "stress": {
        "form": "диха́ння",
        "source": "СУМ-20 (22440)",
        "url": "https://sum20ua.com/?wordid=22440"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "neuter",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Діалектний наголошений варіант слова «ди́хання» з наголосом на другому складі (СУМ-20, стаття 22440: діал. Ди́хання; зафіксовано також у Грінченка 1907). Не утворює окремого семантичного значення від літературного «ди́хання».",
      "meaning": {
        "definitions": [
          "(діал.) Те саме, що ди́хання (акцентний діалектний варіант)."
        ],
        "source": "СУМ-20 (22440) / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДИХА́ННЯ, я, с., діал. Ди́хання.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.), а також у СУМ-11 як діалектний варіант."
      }
    }
  ],
  "ковтнути": [
    {
      "lemma": "ковтнути",
      "url_slug": "ковтнути",
      "headword": "ко́втнути",
      "short_label": "ударити кулаком (діал.)",
      "gloss": "to punch, strike with a fist (dialectal single blow, related to ко́втати)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈkɔu̯tnʊtɪ]"
      },
      "stress": {
        "form": "ко́втнути",
        "source": "СУМ-20 (42582)",
        "url": "https://sum20ua.com/?wordid=42582"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з загальновживаним «ковтну́ти» (наголос на -ну́ти: проковтнути рідину або їжу).",
      "meaning": {
        "definitions": [
          "(діал.) Однократне до ко́втати; вдарити, стукнути кулаком."
        ],
        "source": "СУМ-20 (42582)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "КО́ВТНУТИ, ну, неш, док., діал. Однокр. до ко́втати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "ковтнути",
      "url_slug": "ковтнути",
      "headword": "ковтну́ти",
      "short_label": "проковтнути рідину або їжу",
      "gloss": "to swallow, take a gulp, drink a mouthful",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[kɔu̯tˈnutɪ]"
      },
      "stress": {
        "form": "ковтну́ти",
        "source": "СУМ-20 (42583)",
        "url": "https://sum20ua.com/?wordid=42583"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з діалектним «ко́втнути» (наголос на першому складі: вдарити кулаком).",
      "meaning": {
        "definitions": [
          "Однократне до ковта́ти; зробити один ковток рідини або їжі; випити."
        ],
        "source": "СУМ-20 (42583)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "КОВТНУ́ТИ, ну́, не́ш, док., що, чого і без прям. дод. 1. Однокр. до ковта́ти 1.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "підсумковий": [
    {
      "lemma": "підсумковий",
      "url_slug": "підсумковий",
      "headword": "підсу́мковий",
      "short_label": "стосовний до сумки для набоїв (військ., іст.)",
      "gloss": "related to an ammunition pouch or cartridge box (from підсу́мок - cartridge box, ammo pouch)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pidˈsumkɔwɪj]"
      },
      "stress": {
        "form": "підсу́мковий",
        "source": "СУМ-11 / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з «підсумко́вий» (наголос на третьому складі: який підбиває підсумки, заключний; від пі́дсумок).",
      "meaning": {
        "definitions": [
          "(військ., іст.) Прикм. до підсу́мок (поясна шкіряна сумка для патронів, набоїв)."
        ],
        "source": "СУМ-11 / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПІДСУ́МКОВИЙ, а, е. Прикм. до підсу́мок (патронташ, сумка для набоїв).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "підсумковий",
      "url_slug": "підсумковий",
      "headword": "підсумко́вий",
      "short_label": "який підбиває підсумки; завершальний",
      "gloss": "summary, final, conclusive, resulting (from пі́дсумок - sum, total, outcome, summary)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pidsʊmˈkɔwɪj]"
      },
      "stress": {
        "form": "підсумко́вий",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з «підсу́мковий» (наголос на другому складі: стосовний до військової сумки для набоїв — підсу́мка).",
      "meaning": {
        "definitions": [
          "1. Прикм. до пі́дсумок (сума, результат). 2. Який містить або підбиває підсумки; завершальний, заключний (підсумковий звіт, підсумкова таблиця)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПІДСУМКО́ВИЙ, а, е. 1. Прикм. до пі́дсумок. 2. Завершальний, заключний. Підсумковий огляд художньої самодіяльності.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "родовий": [
    {
      "lemma": "родовий",
      "url_slug": "родовий",
      "headword": "родо́вий",
      "short_label": "родовий лад / родовий відмінок (лінгв.)",
      "gloss": "clan-related, ancestral; genitive case (grammar: родовий відмінок)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɔˈdɔwɪj]"
      },
      "stress": {
        "form": "родо́вий",
        "source": "СУМ-20 (100032)",
        "url": "https://sum20ua.com/?wordid=100032"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Словники (Орфографічний словник, СУМ-20) фіксують подвійний наголос «родо́ви́й» для значень, пов'язаних із родом та граматичним відмінком (родо́вий / родови́й відмінок, родо́вий / родови́й лад від «рід»). Форма з кінцевим наголосом «родови́й» має також окреме (рідкісне) значення, стосовне до пологів (родові́ перейми, частіше: полого́вий). Отже, кінцевий наголос «родови́й» не є виключним маркером пологів, оскільки вживається і щодо роду.",
      "meaning": {
        "definitions": [
          "1. Який існував під час життя людей родами; родовий лад. 2. Прикм. до рід (родова спадщина). 3. Лінгв. Родовий відмінок."
        ],
        "source": "СУМ-20 (100032)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РОДО́ВИ́Й, о́ва́, о́ве́. 1. Який існував під час життя людей родами... 2. Прикм. до рід...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11), де також зафіксовано подвійний наголос (РОДО́ВИ́Й)."
      }
    },
    {
      "lemma": "родовий",
      "url_slug": "родовий",
      "headword": "родови́й",
      "short_label": "стосовний до пологів (мед., акуш., рідко)",
      "gloss": "natal, obstetric, relating to labor and childbirth (родові перейми, пологові)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɔdɔˈwɪj]"
      },
      "stress": {
        "form": "родови́й",
        "source": "СУМ-20 (100033)",
        "url": "https://sum20ua.com/?wordid=100033"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Словники фіксують «родови́й» (рідко) у значенні, стосовному до пологів (родові перейми; частіше й природніше: «полого́вий»). Водночас кінцевий наголос «родови́й» уживається і в значенні «родовий лад, родовий відмінок» поряд із «родо́вий», тому кінцевий наголос сам по собі не розмежовує ці значення абсолютно.",
      "meaning": {
        "definitions": [
          "(рідко, мед., акуш.) Стосовний до родів, пологів; зв'язаний із процесом народження дитини (родові перейми; частіше: пологовий)."
        ],
        "source": "СУМ-20 (100033)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РОДОВИ́Й, а́, е́, рідко. Стос. до родів (у 1 знач.).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11) з позначкою рідко; у сучасній українській практиці переважає термін полого́вий."
      }
    }
  ],
  "свячений": [
    {
      "lemma": "свячений",
      "url_slug": "свячений",
      "headword": "свя́чений",
      "short_label": "освячений (дієприкм.)",
      "gloss": "blessed, consecrated, sanctified (passive participle of святити)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈsʲwɑt͡ʃenɪj]"
      },
      "stress": {
        "form": "свя́чений",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "дієприкметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з прикметником/іменником «свяче́ний» (свячена вода, свячене).",
      "meaning": {
        "definitions": [
          "Дієприкм. пас. мин. ч. до святи́ти; освячений обрядом."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СВЯ́ЧЕНИЙ, а, е. Дієпр. пас. мин. ч. до святи́ти.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11). Релігійна лексика зазнавала цензурних обмежень у тлумаченнях. Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "свячений",
      "url_slug": "свячений",
      "headword": "свяче́ний",
      "short_label": "свячена вода / свячене (прикм./імен.)",
      "gloss": "holy, ritual, consecrated (свячена вода - holy water; свячене - blessed Easter food)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sʲwɐˈt͡ʃɛnɪj]"
      },
      "stress": {
        "form": "свяче́ний",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з віддієслівним дієприкметником «свя́чений» (наголос на першому складі).",
      "meaning": {
        "definitions": [
          "Прикм. до святити; свячена вода; у знач. ім. свяче́не: освячена великодня їжа."
        ],
        "source": "ВТС / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СВЯЧЕ́НИЙ, а, е. Прикм. до святи́ти. Свячена вода; свячене.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), створеному в умовах заборон української мови в Російській імперії (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "сіяння": [
    {
      "lemma": "сіяння",
      "url_slug": "сіяння",
      "headword": "сі́яння",
      "short_label": "розсівання насіння (агротехн.)",
      "gloss": "sowing, seeding, spreading grain in field",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈsʲijɐnʲːɐ]"
      },
      "stress": {
        "form": "сі́яння",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "neuter",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з омографом «сія́ння» (наголос на -я́-: сяйво, випромінювання світла).",
      "meaning": {
        "definitions": [
          "Дія за значенням сі́яти; розсівання зерна, насіння у ґрунт."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СІ́ЯННЯ, я, с. Дія за знач. сі́яти 1.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "сіяння",
      "url_slug": "сіяння",
      "headword": "сія́ння",
      "short_label": "сяйво, випромінювання світла (поет.)",
      "gloss": "radiance, shining, brilliant glow (= ся́ння, from сіяти/сяяти)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-poetic",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sʲiˈjanʲːɐ]"
      },
      "stress": {
        "form": "сія́ння",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "neuter",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з агротехнічним терміном «сі́яння» (наголос на першому складі: сівба зерна).",
      "meaning": {
        "definitions": [
          "(поет.) Те саме, що ся́йво, ся́ння; яскраве світло, випромінюване чим-небудь."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СІЯ́ННЯ, я, с., рідко. Дія за знач. сія́ти 2; сяйво.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "сіяти": [
    {
      "lemma": "сіяти",
      "url_slug": "сіяти",
      "headword": "сі́яти",
      "short_label": "кидати зерно в ґрунт; розсипати",
      "gloss": "to sow seeds, scatter grain in ground; drizzle (rain)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈsʲijɐtɪ]"
      },
      "stress": {
        "form": "сі́яти",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з поетичним омографом «сія́ти» (наголос на -я́-: світити, сяяти).",
      "meaning": {
        "definitions": [
          "Розкидати зерно, насіння по зораній землі; дрібно сипати, накрапати."
        ],
        "source": "ВТС / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СІ́ЯТИ, сію, сієш, недок., перех. і неперех. 1. Розкидати або заробляти в ґрунт насіння для вирощування рослин.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості. Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "сіяти",
      "url_slug": "сіяти",
      "headword": "сія́ти",
      "short_label": "випромінювати світло, сяяти (поет.)",
      "gloss": "to shine, radiate light, gleam, sparkle (= ся́яти, сяти; attested in Grinchenko 1907)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "authentic-poetic",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sʲiˈjɑtɪ]"
      },
      "stress": {
        "form": "сія́ти",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з хліборобським словом «сі́яти» (наголос на першому складі: сіяти хліб).",
      "meaning": {
        "definitions": [
          "(поет., нар.-піс.) Те саме, що ся́яти; випромінювати світло, блищати."
        ],
        "source": "ВТС / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СІЯ́ТИ, я́ю, я́єш, недок., рідко. Те саме, що ся́яти.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "скалити": [
    {
      "lemma": "скалити",
      "url_slug": "скалити",
      "headword": "ска́лити",
      "short_label": "показувати зуби, вишкірятися",
      "gloss": "to bare one's teeth, grin maliciously, sneer (скалити зуби)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈskɑlɪtɪ]"
      },
      "stress": {
        "form": "ска́лити",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з діалектним «скали́ти» (наголос на -и́-: занозити скалкою).",
      "meaning": {
        "definitions": [
          "Розсуваючи губи, показувати зуби; скалити зуби, глузувати."
        ],
        "source": "ВТС / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СКА́ЛИТИ, лю, лиш, недок., перех. 1. Розсуваючи губи, відкривати, показувати зуби...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості. Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "скалити",
      "url_slug": "скалити",
      "headword": "скали́ти",
      "short_label": "занозити скалкою (діал.)",
      "gloss": "to get a wood splinter in skin (attested in Grinchenko 1907: 'Ноги собі скалить')",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[skɐˈlɪtɪ]"
      },
      "stress": {
        "form": "скали́ти",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з літературним «ска́лити» (наголос на першому складі: скалити зуби).",
      "meaning": {
        "definitions": [
          "(діал.) Занозити шкіру тріскою, скалкою; колоти скалками."
        ],
        "source": "Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СКА́ЛИ́ТИ, лю́, ли́ш, недок., діал. Занозити.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "слідувати": [
    {
      "lemma": "слідувати",
      "url_slug": "слідувати",
      "headword": "слі́дувати",
      "short_label": "іти слідом, прямувати",
      "gloss": "to follow behind, accompany, move along a route",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈsʲlʲidʊwɐtɪ]"
      },
      "stress": {
        "form": "слі́дувати",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з діалектним «слідува́ти» (наголос на кінці: слідкувати за слідами). Увага: канцеляризм «слідує зробити» є калькою з рос. 'следует'; правильно: 'слід', 'варто', 'належить'.",
      "meaning": {
        "definitions": [
          "Іти, їхати слідом за кимось; прямувати визначеним шляхом."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СЛІ́ДУВАТИ, дую, дуєш, недок. 1. Іти, їхати, рухатися слідом за ким-, чим-небудь...",
        "sovietization_risk": 1,
        "keywords": [
          "канцелярська калька"
        ],
        "historical_note": "У радянський період через вплив російської мови поширилося ненормативне вживання дієслова у безособовому значенні 'слідує' (замість питомих 'слід', 'належить', 'треба')."
      }
    },
    {
      "lemma": "слідувати",
      "url_slug": "слідувати",
      "headword": "слідува́ти",
      "short_label": "слідкувати за кимось, вистежувати (діал.)",
      "gloss": "to track down, keep watch, follow tracks closely (attested in Grinchenko 1907)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sʲlʲidʊˈwɑtɪ]"
      },
      "stress": {
        "form": "слідува́ти",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з літературним «слі́дувати» (наголос на першому складі: прямувати слідом).",
      "meaning": {
        "definitions": [
          "(діал., розм.) Те саме, що слідкува́ти; стежити за кимось, пильнувати сліди."
        ],
        "source": "Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СЛІДУВА́ТИ, у́ю, у́єш, недок., розм. Те саме, що слідкува́ти.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "соляний": [
    {
      "lemma": "соляний",
      "url_slug": "соляний",
      "headword": "соля́ний",
      "short_label": "соляна кислота (хім.)",
      "gloss": "hydrochloric (chemistry: соляна кислота - hydrochloric acid)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sɔˈlʲɑnɪj]"
      },
      "stress": {
        "form": "соля́ний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з загальним словом «соляни́й» (наголос на закінченні: соляний стовп, соляні шахти).",
      "meaning": {
        "definitions": [
          "(хім.) У сполученні: соля́на кислота́ (хлористоводнева кислота HCl)."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СОЛЯ́НИЙ, а, е: Соляна кислота...",
        "sovietization_risk": 1,
        "keywords": [
          "термінологічна калька"
        ],
        "historical_note": "У сучасній українській хімічній термінології рекомендовано науковий термін 'хлоридна кислота' поряд із традиційним тривіальним 'соляна кислота'."
      }
    },
    {
      "lemma": "соляний",
      "url_slug": "соляний",
      "headword": "соляни́й",
      "short_label": "стосовний до солі, мінералу (соляні копальні)",
      "gloss": "saline, salt-bearing, containing salt (e.g. соляний розчин, соляні промисли)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sɔlʲɐˈnɪj]"
      },
      "stress": {
        "form": "соляни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з хімічним терміном «соля́ний» (соляна кислота).",
      "meaning": {
        "definitions": [
          "Прикм. до сіль; який містить сіль або призначений для видобутку, зберігання солі."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СОЛЯНИ́Й, а́, е́. 1. Прикм. до сіль 1.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "спірний": [
    {
      "lemma": "спірний",
      "url_slug": "спірний",
      "headword": "спі́рний",
      "short_label": "дискусійний, сумнівний, предмет спору",
      "gloss": "disputed, debatable, contentious, controversial (causing argument/dispute)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈsʲpirnɪj]"
      },
      "stress": {
        "form": "спі́рний",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «дискусійний, не вирішений» (від «спір»). Словники (зокрема ВТС) фіксують також паралельний подвійний наголос «спі́рни́й» у значенні «спорий, продуктивний» (від «спор»). Тому кореневий наголос «спі́рний» може перетинатися з обома значеннями, тоді як виключно кінцевий наголос «спірни́й» позначає лише продуктивність та швидкість.",
      "meaning": {
        "definitions": [
          "Який викликає спір, суперечку; не вирішений остаточно; дискусійний."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СПІ́РНИЙ, а, е. 1. Який викликає спір...",
        "sovietization_risk": 1,
        "keywords": [
          "партійні суперечки",
          "ідеологічний контекст"
        ],
        "historical_note": "У СУМ-11 ілюстративна база рясніла цитатами про партійні з'їзди та ідеологічні суперечки радянського періоду."
      }
    },
    {
      "lemma": "спірний",
      "url_slug": "спірний",
      "headword": "спірни́й",
      "short_label": "спорий, швидкий, плідний у праці (фольк.)",
      "gloss": "swift, efficient, productive, fast-moving in work (e.g. спірний кінь, спірна праця; attested in Grinchenko 1907)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-folklorism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sʲpirˈnɪj]"
      },
      "stress": {
        "form": "спірни́й",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «спорий, швидкий, продуктивний» (від «спор»). Словники (ВТС) фіксують для цього значення подвійний наголос «спі́рни́й» (спі́рна або спірна́ праця), тоді як для значення «дискусійний» (від «спір») нормативним є лише кореневий наголос «спі́рний».",
      "meaning": {
        "definitions": [
          "(розм., фольк.) Те саме, що спо́рий; швидкий, успішний, продуктивний (про роботу або коня)."
        ],
        "source": "Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СПІ́РНИ́Й, а, е, розм. Те саме, що спо́рий.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), виданому всупереч антиукраїнським імперським указам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "сполучний": [
    {
      "lemma": "сполучний",
      "url_slug": "сполучний",
      "headword": "сполу́чний",
      "short_label": "з'єднувальний; сполучна тканина (анат.)",
      "gloss": "connecting, connective, binding; linking (e.g. сполучна тканина - connective tissue, сполучний звук)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[spɔˈlut͡ʃnɪj]"
      },
      "stress": {
        "form": "сполу́чний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з «сполучни́й» (наголос на кінці: сумісний, суміщуваний з чим-небудь).",
      "meaning": {
        "definitions": [
          "Який скріплює, з'єднує що-небудь; призначений для сполучення (сполучний матеріал, сполучна тканина); грам. сполучний звук, сполучні слова."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СПОЛУ́ЧНИЙ, а, е. 1. Який скріплює, з’єднує, зв’язує що-небудь... 3. уроч. Тісно зближений, згуртований; єдиний. 'Віднині і навіки з Москвою сполучні будьмо!'",
        "sovietization_risk": 2,
        "keywords": [
          "ідеологічна пропаганда",
          "Москва"
        ],
        "historical_note": "У СУМ-11 до суто технічного та анатомічного прикметника 'сполучний' було штучно додано урочисте ідеологічне значення братерства з Москвою для радянської політичної індоктринації."
      }
    },
    {
      "lemma": "сполучний",
      "url_slug": "сполучний",
      "headword": "сполучни́й",
      "short_label": "сумісний, суміщуваний з чим-небудь",
      "gloss": "combinable, compatible, joinable (able to be connected or reconciled with something)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[spɔlʊt͡ʃˈnɪj]"
      },
      "stress": {
        "form": "сполучни́й",
        "source": "СУМ-11 / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з «сполу́чний» (наголос на другому складі: який сполучає або скріплює). «Сполучни́й» означає сумісний, суміщуваний, який можна сполучити.",
      "meaning": {
        "definitions": [
          "Який можна поєднувати, суміщати з чим-небудь; сумісний, сполучний із чимось."
        ],
        "source": "СУМ-11 / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СПОЛУЧНИ́Й, а́, е́. Який можна поєднувати, суміщати з чим-небудь. (Цитата з В. Леніна, т. 25).",
        "sovietization_risk": 1,
        "keywords": [
          "цитата Леніна"
        ],
        "historical_note": "У СУМ-11 єдиною ілюстрацією вживання цього слова слугувала цитата з творів В. І. Леніна."
      }
    }
  ],
  "старший": [
    {
      "lemma": "старший",
      "url_slug": "старший",
      "headword": "ста́рший",
      "short_label": "віком більший; головніший за рангом",
      "gloss": "older, elder; senior in rank or status",
      "pos": "adjective",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈstɑrʃɪj]"
      },
      "stress": {
        "form": "ста́рший",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з іменниковим званням чи посадою «старши́й» (наголос на -ши́й: начальник, козацький ватажок).",
      "meaning": {
        "definitions": [
          "Вищий ступінь до старий; який має більше років; старший за рангом чи становищем."
        ],
        "source": "ВТС / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СТА́РШИЙ, а, е. 1. Вищ. ст. до стари́й 1, 2.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості. Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "старший",
      "url_slug": "старший",
      "headword": "старши́й",
      "short_label": "начальник, керівник, ватажок (імен.)",
      "gloss": "chief, elder, leader, commander, headman (substantive noun; e.g. козацький старший; Grinchenko 1907)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[stɐrˈʃɪj]"
      },
      "stress": {
        "form": "старши́й",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Не плутати з якісним прикметником «ста́рший» (наголос на першому складі: старший брат).",
      "meaning": {
        "definitions": [
          "(іст., розм.) Начальник, очільник громади або військового загону; козацький старший."
        ],
        "source": "Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СТАРШИ́Й, о́го, ч., розм. Те саме, що керівни́к, нача́льник.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), виданому всупереч заборонам української мови царською владою (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "стоянка": [
    {
      "lemma": "стоянка",
      "url_slug": "стоянка",
      "headword": "сто́янка",
      "short_label": "відстояне молоко, вершки (розм.)",
      "gloss": "settled standing milk, layer of cream (attested in Grinchenko 1907)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈstɔjɐnkɐ]"
      },
      "stress": {
        "form": "сто́янка",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з загальновідомим словом «стоя́нка» (наголос на -я́-: парковка, табір первісних людей).",
      "meaning": {
        "definitions": [
          "(розм., діал.) Відстояне молоко; шар вершків на відстояному молоці."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СТО́ЯНКА, и, ж., розм. 1. Те саме, що Відсто́яне молоко́...",
        "sovietization_risk": 1,
        "keywords": [
          "колгоспні цитати"
        ],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "стоянка",
      "url_slug": "стоянка",
      "headword": "стоя́нка",
      "short_label": "місце зупинки, парковка; табір",
      "gloss": "parking lot, halting place, camp of ancient humans (archaeology: первісна стоянка)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[stɔˈjɑnkɐ]"
      },
      "stress": {
        "form": "стоя́нка",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з побутовим діалектним «сто́янка» (наголос на першому складі: відстояне молоко).",
      "meaning": {
        "definitions": [
          "1. Місце, відведене для паркування транспорту. 2. Археол. Поселення первісної людини."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СТОЯ́НКА, и, ж. 1. Дія за знач. стоя́ти 1, 4, 11...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "судний": [
    {
      "lemma": "судний",
      "url_slug": "судний",
      "headword": "су́дний",
      "short_label": "Судний день; судочинство (заст.)",
      "gloss": "Judgement Day, Doomsday (реліг. Судний день); judicial, court-related",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈsudnɪj]"
      },
      "stress": {
        "form": "су́дний",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з народним «судни́й» (наголос на кінці: придатний, міцний, годящий).",
      "meaning": {
        "definitions": [
          "1. Реліг. Судний день (Страшний суд). 2. Заст. Стосовний до судочинства."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СУ́ДНИЙ, а, е, СУ́ДНІЙ, я, є, заст. 1. Стос. до суду...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11). Релігійні значення супроводжувалися цензурними ремарками."
      }
    },
    {
      "lemma": "судний",
      "url_slug": "судний",
      "headword": "судни́й",
      "short_label": "придатний, годний, міцний (діал.)",
      "gloss": "suitable, fit, sturdy, serviceable (attested in Grinchenko 1907: 'полотно судне')",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[sʊdˈnɪj]"
      },
      "stress": {
        "form": "судни́й",
        "source": "Грінченко (1907)"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з релігійним та судовим словом «су́дний» (Судний день).",
      "meaning": {
        "definitions": [
          "(діал.) Годний, придатний для вжитку; міцний (про полотно, одяг чи річ)."
        ],
        "source": "Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СУДНИ́Й, а́, е́, діал. Придатний для вжитку, годящий.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), виданому всупереч репресивним указам Російської імперії (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "твердити": [
    {
      "lemma": "твердити",
      "url_slug": "твердити",
      "headword": "тве́рдити",
      "short_label": "стверджувати, запевняти в чомусь",
      "gloss": "to assert, maintain, state confidently, assure (впевнено висловлювати)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈtwɛrdɪtɪ]"
      },
      "stress": {
        "form": "тве́рдити",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з «тверди́ти» (наголос на другому складі: повторювати одне й те саме, завчати, зубрити).",
      "meaning": {
        "definitions": [
          "Впевнено висловлювати що-небудь, настійливо говорити, запевняючи в чомусь."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ТВЕ́РДИТИ, джу, диш, недок., перех., із спол. що. Впевнено висловлювати що-небудь, настійливо говорити, запевняючи в чомусь.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "твердити",
      "url_slug": "твердити",
      "headword": "тверди́ти",
      "short_label": "повторювати одне й те саме, завчати",
      "gloss": "to repeat repeatedly, reiterate; recite or rehearse to memorize (завчати, зубрити)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[twɛrˈdɪtɪ]"
      },
      "stress": {
        "form": "тверди́ти",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з «тве́рдити» (наголос на першому складі: впевнено висловлювати, запевняти в чомусь).",
      "meaning": {
        "definitions": [
          "1. Говорити, повторювати те саме. 2. (заст.) Багато разів повторювати що-небудь, щоб вивчити, запам'ятати (завчати, зубрити)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ТВЕРДИ́ТИ, джу́, ди́ш, недок., перех. 1. Говорити, повторювати те саме. 2. заст. Багато разів повторювати що-небудь, щоб вивчити, запам’ятати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "типовий": [
    {
      "lemma": "типовий",
      "url_slug": "типовий",
      "headword": "типо́вий",
      "short_label": "характерний, показовий, показний",
      "gloss": "typical, characteristic, representative of a kind (характерний, показовий)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[tɪˈpɔwɪj]"
      },
      "stress": {
        "form": "типо́вий",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «характерний, показовий, який виражає найістотніші риси» (типовий приклад, типовий випадок). Не плутати з «типови́й» (наголос на кінці: виконаний за зразком, зразковий, серійний: типовий проєкт).",
      "meaning": {
        "definitions": [
          "Який виражає найістотніші риси певної групи людей, явищ; характерний, показовий."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ТИПО́ВИЙ, а, е. 1. Який відзначається ознаками, властивими якій-небудь сукупності осіб, явищ...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "типовий",
      "url_slug": "типовий",
      "headword": "типови́й",
      "short_label": "виконаний за зразком, зразковий, стандартизований (техн.)",
      "gloss": "standardized, model-based, type-designed (зразковий; виконаний за зразком: типовий проєкт)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[tɪpɔˈwɪj]"
      },
      "stress": {
        "form": "типови́й",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «виконаний за певним зразком чи стандартом, зразковий, серійний» (ВТС / Орфографічний словник: типови́й = зразковий; типовий проєкт). Не плутати з «типо́вий» (наголос на другому складі: характерний, показовий).",
      "meaning": {
        "definitions": [
          "(техн., спец.) Виконаний за певним зразком, стандартом; серійний (типовий будинок, типовий проєкт)."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ТИПОВИ́Й, а́, е́. Прикм. до тип 4; серійний, виконаний за зразком.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "уступ": [
    {
      "lemma": "уступ",
      "url_slug": "уступ",
      "headword": "у́ступ",
      "short_label": "частина тексту, уривок, абзац (книжн.)",
      "gloss": "passage of text, excerpt, paragraph (in a book or article)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈustup]"
      },
      "stress": {
        "form": "у́ступ",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з «усту́п» (наголос на другому складі: східець, виступ у скелі чи мурі, уступ у шахті).",
      "meaning": {
        "definitions": [
          "(книжн.) Частина тексту; уривок, абзац."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "У́СТУП, у, ч., книжн. Частина тексту; уривок, абзац.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "уступ",
      "url_slug": "уступ",
      "headword": "усту́п",
      "short_label": "виступ, тераса, східець у скелі чи мурі",
      "gloss": "ledge, step, terrace, rock shelf; bench in mining",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ʊsˈtup]"
      },
      "stress": {
        "form": "усту́п",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з «у́ступ» (наголос на першому складі: частина тексту, уривок, абзац).",
      "meaning": {
        "definitions": [
          "1. Виступ або виїмка в чому-небудь, що нагадує східець (у горах, скелі, мурі). 2. (спец.) Частина вибою."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "УСТУ́П, у, ч. 1. Виступ або виїмка в чому-небудь, що нагадує східець... // спец. Частина вибою.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "хлібець": [
    {
      "lemma": "хлібець",
      "url_slug": "хлібець",
      "headword": "хлі́бець",
      "short_label": "маленька хлібина, буханець",
      "gloss": "small loaf of bread, bun, roll (e.g. випікати хлібці)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈxlʲibɛt͡sʲ]"
      },
      "stress": {
        "form": "хлі́бець",
        "source": "СУМ-11 / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з «хлібе́ць» (родовий хлібця́: пестливе до хліб у народних піснях — зелені посіви зернових на полі).",
      "meaning": {
        "definitions": [
          "Невелика хлібина; буханець (також м'ясний хлібець як кулінарний виріб)."
        ],
        "source": "СУМ-11 / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ХЛІ́БЕЦЬ, бця, ч. Невелика хлібина; // Невеликий хліб з м’ясного фаршу.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "хлібець",
      "url_slug": "хлібець",
      "headword": "хлібе́ць",
      "short_label": "хлібчик, посіви зернових (пестл., фольк.)",
      "gloss": "dear bread, young standing grain crops in fields (diminutive/poetic, attested in folk songs: 'Хіба зелениться хлібець серед поля')",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-folklorism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[xlʲiˈbɛt͡sʲ]"
      },
      "stress": {
        "form": "хлібе́ць",
        "source": "СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з «хлі́бець» (родовий хлі́бця: окрема невелика хлібина).",
      "meaning": {
        "definitions": [
          "Зменш.-пестл. до хліб; хлібчик, зернові посіви на полі в народнопоетичній творчості."
        ],
        "source": "СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ХЛІБЕ́ЦЬ, бця́, ч. Зменш.-пестл. до хліб 1-3. Нема, бачите, рідної неньки, нікому було і шматочок хлібця дать небозі... Хіба зелениться Хлібець серед поля.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "хрещений": [
    {
      "lemma": "хрещений",
      "url_slug": "хрещений",
      "headword": "хре́щений",
      "short_label": "охрещений (дієприкм.)",
      "gloss": "baptized, christened (passive past participle of хрестити; e.g. дитина, ще не хрещена)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈxrɛʃt͡ʃenɪj]"
      },
      "stress": {
        "form": "хре́щений",
        "source": "СУМ-11 / ВТС"
      },
      "morphology": {
        "pos": "дієприкметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з прикметником/іменником «хреще́ний» (хрещений батько, хрещена мати).",
      "meaning": {
        "definitions": [
          "Дієприкм. пас. мин. ч. до хрести́ти; над яким здійснено обряд хрещення."
        ],
        "source": "СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ХРЕ́ЩЕНИЙ, а, е. Дієпр. пас. мин. ч. до хрести́ти. Він, браття, ще не хрещений — не сміє благословення вірним уділяти.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11). Релігійна обрядова термінологія зазнавала ідеологічної цензури."
      }
    },
    {
      "lemma": "хрещений",
      "url_slug": "хрещений",
      "headword": "хреще́ний",
      "short_label": "хрещений батько / мати; християнин",
      "gloss": "godparent (хрещений батько, хрещена мати), christened Christian person (хрещений люд)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[xrɛˈʃt͡ʃɛnɪj]"
      },
      "stress": {
        "form": "хреще́ний",
        "source": "СУМ-11 / ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з дієприкметником «хре́щений» (наголос на першому складі: охрещений у церкві).",
      "meaning": {
        "definitions": [
          "1. Який прийняв християнство; православний християнин. 2. У сполученнях: хрещений батько, хрещена мати (духовні батьки)."
        ],
        "source": "СУМ-11 / ВТС / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ХРЕЩЕ́НИЙ, а́, е́. 1. Який був підданий обряду хрещення... 2. Стос. до обряду хрещення... // у знач. ім. хреще́ні, них, мн. Ті (чоловік і жінка), хто бере участь в обряді хрещення в ролі духовних батька та матері.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), виданому всупереч репресивним заборонам Російської імперії (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "цілик": [
    {
      "lemma": "цілик",
      "url_slug": "цілик",
      "headword": "ці́лик",
      "short_label": "прицільне пристосування на зброї",
      "gloss": "rear sight, sighting notch on a firearm or artillery barrel",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈt͡sʲilɪk]"
      },
      "stress": {
        "form": "ці́лик",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з аграрним та гірничим «ціли́к» (наголос на кінці: цілина, незаймана земля).",
      "meaning": {
        "definitions": [
          "(військ., техн.) Пристосування на зброї для наведення на ціль."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЦІ́ЛИК, а, ч., спец. Найпростіше прицільне пристосування на стволі зброї...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "цілик",
      "url_slug": "цілик",
      "headword": "ціли́к",
      "short_label": "цілина; непорушений пласт породи",
      "gloss": "virgin land, unbroken unplowed steppe; pillar of unmined rock (attested in Grinchenko 1907: 'Цілик = цілина')",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[t͡sʲiˈlɪk]"
      },
      "stress": {
        "form": "ціли́к",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з прицільним пристроєм «ці́лик» (наголос на першому складі).",
      "meaning": {
        "definitions": [
          "1. Діал. Цілина, незаймана земля. 2. Гірн. Частина пласта корисної копалини, залишена непорушеною."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЦІЛИ́К, а́, ч. 1. гірн. Частина пласта корисної копалини... 2. діал. Цілина.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "цілити": [
    {
      "lemma": "цілити",
      "url_slug": "цілити",
      "headword": "ці́лити",
      "short_label": "наводити зброю в ціль, мітити",
      "gloss": "to aim at a target, take aim, point a weapon (Цілив у ворону...)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈt͡sʲilɪtɪ]"
      },
      "stress": {
        "form": "ці́лити",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з архаїчним «ціли́ти» (наголос на -ли́ти: зцілювати, зціляти рани).",
      "meaning": {
        "definitions": [
          "Спрямовувати зброю або погляд на який-небудь об'єкт; намагатися влучити."
        ],
        "source": "ВТС / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЦІ́ЛИТИ, лю, лиш, недок. 1. Те саме, що ці́литися.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості. Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "цілити",
      "url_slug": "цілити",
      "headword": "ціли́ти",
      "short_label": "зцілювати, лікувати (заст., нар.-поет.)",
      "gloss": "to heal, cure, restore health (attested in Grinchenko 1907: 'Цілити - исцелять')",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[t͡sʲiˈlɪtɪ]"
      },
      "stress": {
        "form": "ціли́ти",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з військовим та побутовим «ці́лити» (наголос на першому складі: цілити в мішень).",
      "meaning": {
        "definitions": [
          "(заст., нар.-поет.) Повертати здоров'я, зцілювати рани чи хвороби; лікувати."
        ],
        "source": "Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЦІЛИ́ТИ, лю́, ли́ш, недок., заст. Лікувати, зціляти.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), укладеному всупереч антиукраїнським царським указам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "україна": [
    {
      "lemma": "україна",
      "url_slug": "україна",
      "headword": "укра́їна",
      "short_label": "прикордонна земля, порубіжжя (іст., заст.)",
      "gloss": "frontier region, border territory (historical appellative in medieval chronicles)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ʊˈkrɑjinɐ]"
      },
      "stress": {
        "form": "укра́їна",
        "source": "СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з власним ім'ям держави та народнопоетичним загальним словом «украї́на» (наголос на -ї́-: рідна країна, земля народу).",
      "meaning": {
        "definitions": [
          "(іст., заст.) Територія уздовж меж князівства або держави; прикордонний край."
        ],
        "source": "СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "УКРА́ЇНА, и, ж., заст. Територія уздовж меж держави, біля її краю.",
        "sovietization_risk": 2,
        "keywords": [
          "імперський міф",
          "окраина"
        ],
        "historical_note": "Російська імперська та радянська історіографія однобічно абсолютизували значення 'укра́їна = окраїна', намагаючись звести назву цілого народу до периферії Московської держави. У питомій традиції паралельно побутував фольклорний омограф украї́на (країна, рідний край)."
      }
    },
    {
      "lemma": "україна",
      "url_slug": "україна",
      "headword": "украї́на",
      "short_label": "країна, рідний край (іст., фольк.)",
      "gloss": "homeland, native land, country of the people (in Ukrainian folk epics and chronicles)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "authentic-folklorism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ʊkrɐˈjinɐ]"
      },
      "stress": {
        "form": "украї́на",
        "source": "ВТС / Грінченко (1907)"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Загальна назва рідної країни у думах та піснях («в нашій славній україні»), яка стала власною назвою держави Україна.",
      "meaning": {
        "definitions": [
          "(іст., нар.-поет.) Рідний край, земля, батьківщина українського народу (у думах: 'в нашій славній україні')."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "УКРАЇ́НА, и, ж., нар.-поет. Країна, земля.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), укладеному в часи дії антиукраїнських урядових заборон Російської імперії (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "опал": [
    {
      "lemma": "опал",
      "url_slug": "опал",
      "headword": "о́пал",
      "short_label": "опалення, паливо (розм., рідко)",
      "gloss": "heating, fuel for fire (from палити / опалювати)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈɔpɐl]"
      },
      "stress": {
        "form": "о́пал",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з мінералогічним терміном «опа́л» (наголос на другому складі: дорогоцінний камінь).",
      "meaning": {
        "definitions": [
          "(розм., рідко) Те саме, що опа́лення; паливо для обігріву приміщення."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "О́ПАЛ, у, ч., рідко. 1. Те саме, що опа́лення 1. Там йому дають кімнату.. з опалом, з світлом (Сл. Гр.).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "опал",
      "url_slug": "опал",
      "headword": "опа́л",
      "short_label": "коштовний камінь кремнезему (мінер.)",
      "gloss": "opal gemstone (hydrated silica mineral with iridescent play of colors)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ɔˈpɑl]"
      },
      "stress": {
        "form": "опа́л",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з віддієслівним побутовим словом «о́пал» (наголос на першому складі: обігрів або паливо).",
      "meaning": {
        "definitions": [
          "(мінер.) Мінерал, напівдорогоцінний камінь із райдужним відблиском світла."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ОПА́Л, у, ч. Мінерал класу силікатів, що є напівдорогоцінним каменем.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "розказ": [
    {
      "lemma": "розказ",
      "url_slug": "розказ",
      "headword": "ро́зказ",
      "short_label": "наказ, веління (заст., фольк.)",
      "gloss": "order, command, mandate, decree (attested in Grinchenko 1907: 'Розказ = наказ')",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈrɔzkɐz]"
      },
      "stress": {
        "form": "ро́зказ",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з розмовним «розка́з» (наголос на кінці: розповідь, казка).",
      "meaning": {
        "definitions": [
          "(заст., фольк.) Те саме, що нака́з; обов'язкове до виконання розпорядження або веління."
        ],
        "source": "Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РО́ЗКАЗ, у, ч., заст. Наказ. Пан не дозволяв і на годину кидати ліса...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), виданому всупереч репресивним заборонам Російської імперії (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "розказ",
      "url_slug": "розказ",
      "headword": "розка́з",
      "short_label": "розповідь, оповідання (розм.)",
      "gloss": "tale, narrative, story, telling (colloquial verbal noun from розказувати)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[rɔzˈkɑz]"
      },
      "stress": {
        "form": "розка́з",
        "source": "ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з архаїчним «ро́зказ» (наголос на першому складі: розпорядження, наказ).",
      "meaning": {
        "definitions": [
          "(розм.) Дія за знач. розка́зувати; розповідь, оповідка."
        ],
        "source": "ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "РОЗКА́З, у, ч., розм. Дія за знач. розка́зувати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "відклад": [
    {
      "lemma": "відклад",
      "url_slug": "відклад",
      "headword": "ві́дклад",
      "short_label": "геологічний осад, нашарування порід",
      "gloss": "geological deposit, sediment, stratum (formation of settled rock or minerals)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈwidkɫɐd]"
      },
      "stress": {
        "form": "ві́дклад",
        "source": "СУМ-20 (12717)",
        "url": "https://sum20ua.com/?wordid=12717"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з юридичним та побутовим «відкла́д» (наголос на кінці: перенесення терміну, відстрочка).",
      "meaning": {
        "definitions": [
          "(геол.) Гірська порода або шар мінералів, утворений осадом речовин у воді чи повітрі."
        ],
        "source": "СУМ-20 (12717)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІ́ДКЛАД, у, ч., спец. Те, що відклалося внаслідок осідання у воді органічних речовин, мінералів...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "відклад",
      "url_slug": "відклад",
      "headword": "відкла́д",
      "short_label": "відстрочка, перенесення часу (заст.)",
      "gloss": "postponement, adjournment, delay (attested in Grinchenko 1907: 'Одклад не йде в лад')",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[widˈkɫɑd]"
      },
      "stress": {
        "form": "відкла́д",
        "source": "СУМ-20 (12718)",
        "url": "https://sum20ua.com/?wordid=12718"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з геологічним терміном «ві́дклад» (наголос на першому складі: осад).",
      "meaning": {
        "definitions": [
          "(заст., рідко) Те саме, що відклада́ння; відстрочення виконання якоїсь справи."
        ],
        "source": "СУМ-20 (12718) / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДКЛА́Д, у, ч., рідко. Те саме, що відклада́ння.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), укладеному всупереч антиукраїнським указам царської влади (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "замір": [
    {
      "lemma": "замір",
      "url_slug": "замір",
      "headword": "за́мір",
      "short_label": "намір, задум, план",
      "gloss": "intention, aim, plan, purpose (e.g. здійснити свій замір)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈzɑmir]"
      },
      "stress": {
        "form": "за́мір",
        "source": "СУМ-20 (30686)",
        "url": "https://sum20ua.com/?wordid=30686"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з технічним терміном «замі́р» (наголос на другому складі: дія за значенням заміряти).",
      "meaning": {
        "definitions": [
          "Задум, бажання зробити щось; намір, мета."
        ],
        "source": "СУМ-20 (30686)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗА́МІР, у, ч. Задум, бажання зробити щось; намір.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "замір",
      "url_slug": "замір",
      "headword": "замі́р",
      "short_label": "вимірювання приладами (техн.)",
      "gloss": "measurement, gauging, survey, sounding with measuring tools",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈmir]"
      },
      "stress": {
        "form": "замі́р",
        "source": "СУМ-20 (30687)",
        "url": "https://sum20ua.com/?wordid=30687"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з загальновживаним словом «за́мір» (наголос на першому складі: життєвий намір чи план).",
      "meaning": {
        "definitions": [
          "(техн., спец.) Визначення величини чого-небудь за допомогою спеціального приладу або мірки."
        ],
        "source": "СУМ-20 (30687)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАМІ́Р, у, ч., спец. Дія за знач. замі́ряти.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "байковий": [
    {
      "lemma": "байковий",
      "url_slug": "байковий",
      "headword": "ба́йковий",
      "short_label": "пошитий з байки, м'якої тканини (текст.)",
      "gloss": "flannelette, baize (soft brushed cotton fabric; e.g. байкова ковдра, байкова сорочка)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈbɑjkɔwɪj]"
      },
      "stress": {
        "form": "ба́йковий",
        "source": "СУМ-20 (2319)",
        "url": "https://sum20ua.com/?wordid=2319"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з літературознавчим терміном «байко́вий» (наголос на другому складі: стосовний до літературної байки, байкарський).",
      "meaning": {
        "definitions": [
          "Прикм. до ба́йка (м'яка бавовняна тканина з начосом); пошитий із байки."
        ],
        "source": "СУМ-20 (2319) / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БА́ЙКОВИЙ, а, е. Прикм. до ба́йка²; // Зробл., пошитий з байки.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "байковий",
      "url_slug": "байковий",
      "headword": "байко́вий",
      "short_label": "стосовний до байки як літературного жанру (літ.)",
      "gloss": "fable-related, fabulist (relating to literary fable genre; e.g. байковий сюжет)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[bɐjˈkɔwɪj]"
      },
      "stress": {
        "form": "байко́вий",
        "source": "СУМ-20 (2320)",
        "url": "https://sum20ua.com/?wordid=2320"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з текстильним «ба́йковий» (наголос на першому складі: байкова сорочка, байкова тканина).",
      "meaning": {
        "definitions": [
          "(літ.) Прикм. до ба́йка (повчальний алегоричний віршований або прозовий твір)."
        ],
        "source": "СУМ-20 (2320)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БАЙКО́ВИЙ, а, е. Прикм. до ба́йка¹ 1. Ще в Греції існувала байкова традиція...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "брикнути": [
    {
      "lemma": "брикнути",
      "url_slug": "брикнути",
      "headword": "бри́кнути",
      "short_label": "упасти, перекинутися (розм.)",
      "gloss": "to tumble down, fall over, flop down (colloquial)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈbrɪknʊtɪ]"
      },
      "stress": {
        "form": "бри́кнути",
        "source": "СУМ-20 (5513)",
        "url": "https://sum20ua.com/?wordid=5513"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «брикну́ти» (наголос на -ну́ти: брикнути копитом, хвицати).",
      "meaning": {
        "definitions": [
          "(розм.) Упасти, перекинутися; раптово повалитися додолу."
        ],
        "source": "СУМ-20 (5513)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БРИ́КНУТИ, ну, неш, док., розм. Упасти, перекинутися.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "брикнути",
      "url_slug": "брикнути",
      "headword": "брикну́ти",
      "short_label": "брикнути ногою чи копитом, хвицнути",
      "gloss": "to buck, kick out with a hoof or leg once (e.g. кінь брикнув)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[brɪkˈnutɪ]"
      },
      "stress": {
        "form": "брикну́ти",
        "source": "СУМ-20 (5514)",
        "url": "https://sum20ua.com/?wordid=5514"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Не плутати з розмовним «бри́кнути» (наголос на першому складі: раптово впасти, повалитися).",
      "meaning": {
        "definitions": [
          "Однократне до брика́ти; ударити ногою або копита́ми назад; хвицнути."
        ],
        "source": "СУМ-20 (5514)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БРИКНУ́ТИ, ну́, не́ш, док. Однокр. до брика́ти.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    }
  ],
  "жалоба": [
    {
      "lemma": "жалоба",
      "url_slug": "жалоба",
      "headword": "жа́лоба",
      "short_label": "скарга, невдоволення (заст., прост.)",
      "gloss": "complaint, grievance, lawsuit (archaic/vernacular, attested in Grinchenko 1907: 'ЖАлоба = скарга')",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-archaism",
        "warning_severity": "treasured",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈʒɑlɔbɐ]"
      },
      "stress": {
        "form": "жа́лоба",
        "source": "СУМ-20 (26713)",
        "url": "https://sum20ua.com/?wordid=26713"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з загальновживаним словом скорботи «жало́ба» (наголос на другому складі: траур, туга за померлим).",
      "meaning": {
        "definitions": [
          "(прост., заст.) Висловлення невдоволення з приводу чогось; скарга, судова претензія."
        ],
        "source": "СУМ-20 (26713) / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЖА́ЛОБА, и, ж., розм. Висловлення невдоволення з приводу чогось; скарга.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), укладеному всупереч царським указам, що забороняли українську мову (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "жалоба",
      "url_slug": "жалоба",
      "headword": "жало́ба",
      "short_label": "траур, сум за померлим, чорний одяг",
      "gloss": "mourning, grief, bereavement, funeral black attire (attested in Grinchenko 1907: 'ЖалОба = траур')",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ʒɐˈlɔbɐ]"
      },
      "stress": {
        "form": "жало́ба",
        "source": "СУМ-20 (26714)",
        "url": "https://sum20ua.com/?wordid=26714"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Не плутати з архаїчним словом «жа́лоба» (наголос на першому складі: судова скарга або ремство).",
      "meaning": {
        "definitions": [
          "1. Глибокий сум, туга за померлим; траур. 2. Чорний одяг або пов'язка на знак скорботи."
        ],
        "source": "СУМ-20 (26714) / Грінченко (1907)"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЖАЛО́БА, и, ж. 1. Глибокий сум, скорбота за померлим; траур...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "банник": [
    {
      "lemma": "банник",
      "url_slug": "банник",
      "headword": "ба́нник",
      "short_label": "артилерійський банник / щітка для гармати",
      "gloss": "artillery bore brush, swab, cannon cleaning sponge on rammer",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈbɑnːɪk]"
      },
      "stress": {
        "form": "ба́нник",
        "source": "ВТС / СУМ-11",
        "url": "https://slovnyk.me/dict/vts/банник"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Означає «циліндрична щітка на довгому держаку для чищення та змащування дула гармати чи міномета». Не плутати з «банни́к» (наголос на кінці: банщик, працівник або відвідувач лазні).",
      "meaning": {
        "definitions": [
          "Циліндричної форми щітка на держаку для прочищання і змащування каналу ствола гармати або міномета."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БА́ННИК, а, ч. Циліндричної форми щітка на довгому держаку для прочищання і змащування дула гармати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11). Наведено для лексикографічної прозорості."
      }
    },
    {
      "lemma": "банник",
      "url_slug": "банник",
      "headword": "банни́к",
      "short_label": "банщик, працівник або відвідувач лазні (діал.)",
      "gloss": "bathhouse attendant, bather, bath keeper (dial.)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[bɐnˈnɪk]"
      },
      "stress": {
        "form": "банни́к",
        "source": "ВТС / СУМ-11",
        "url": "https://slovnyk.me/dict/vts/банник"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Діалектне та класичне літературне (Іван Франко): «банщик, працівник або відвідувач лазні». Не плутати з військовим терміном «ба́нник» (артилерійська щітка).",
      "meaning": {
        "definitions": [
          "Банщик; працівник лазні або відвідувач, що париться в лазні (діал.)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БАННИ́К, а, ч., діал. Банщик.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Засвідчено в класичній українській літературі (І. Франко). Зафіксовано в СУМ-11."
      }
    }
  ],
  "бережений": [
    {
      "lemma": "бережений",
      "url_slug": "бережений",
      "headword": "бере́жений",
      "short_label": "збережений, якого берегли / пасивний дієприкметник",
      "gloss": "guarded, kept safe, preserved, protected (participle of берегти)",
      "pos": "participle",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[beˈrɛʒenɪj]"
      },
      "stress": {
        "form": "бере́жений",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієприкметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Дієприкметник до «берегти́»: той, кого або що зберігають, оберігають від шкоди. Не плутати з якісним прикметником «береже́ний» (обачний, розважливий).",
      "meaning": {
        "definitions": [
          "Дієприкм. пас. до берегти́; збережений, захищений, охоронений."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БЕРЕ́ЖЕНИЙ, а, е. Дієпр. пас. теп. ч. до берегти́ 1, 2.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "бережений",
      "url_slug": "бережений",
      "headword": "береже́ний",
      "short_label": "обачний, обережний; «береженого й Бог береже»",
      "gloss": "cautious, wary, careful, prudent; (as noun) a cautious person",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[bereˈʒɛnɪj]"
      },
      "stress": {
        "form": "береже́ний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «обережний, обачний, розсудливий» (народне прислів'я: «береже́ного й Бог береже́»). Не плутати з віддієслівним дієприкметником «бере́жений».",
      "meaning": {
        "definitions": [
          "Який усього остерігається; обережний, обачний; у знач. ім. береже́ний: обережна людина."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БЕРЕЖЕ́НИЙ, а, е. Який усього остерігається; обережний, обачний; // у знач. ім. береже́ний, ного, ч. Обережна, уважна, обачна людина.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11). Широко побутує в українських народних пареміях."
      }
    }
  ],
  "буритися": [
    {
      "lemma": "буритися",
      "url_slug": "буритися",
      "headword": "бу́ритися",
      "short_label": "руйнуватися, обвалюватися / (діал.) хвилюватися, бурхати",
      "gloss": "to crumble, collapse, fall down; (dial.) to rage, stir up, ferment",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈburɪtɪsʲɐ]"
      },
      "stress": {
        "form": "бу́ритися",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Означає «руйнуватися, завалюватися» (від бурити), а також у діалектному мовленні та класиці (Франко, Грінченко) «хвилюватися, бунтувати; збиратися на бурю: хмариться, буриться». Не плутати з гірничим «бури́тися» (про свердловину чи шпур).",
      "meaning": {
        "definitions": [
          "Руйнуватися, завалюватися; (діал.) обурюватися, хвилюватися; безл. збиратися на бурю."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БУ́РИТИСЯ, риться, недок., діал. 1. Хвилюватися. 2. перев. безос. Збиратися на бурю.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "буритися",
      "url_slug": "буритися",
      "headword": "бури́тися",
      "short_label": "буритися (про свердловину, шпур; пас. до бурити)",
      "gloss": "to be drilled, bored (passive of бурити - e.g. a well or borehole)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[bʊˈrɪtɪsʲɐ]"
      },
      "stress": {
        "form": "бури́тися",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Пасивний стан до технічного дієслова «бури́ти»: висвердлюватися буром (буриться свердловина, буриться шпур). Не плутати з «бу́ритися» (руйнуватися або хвилюватися).",
      "meaning": {
        "definitions": [
          "Пас. до бури́ти; піддаватися свердлінню за допомогою бура."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "БУРИ́ТИСЯ, бу́риться, недок. Пас. до бури́ти.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "важниця": [
    {
      "lemma": "важниця",
      "url_slug": "важниця",
      "headword": "ва́жниця",
      "short_label": "поважна особа / важлива справа (розм., ірон.)",
      "gloss": "important person, dignitary (ironic); important matter/affair",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈwɑʒnɪt͡sʲɐ]"
      },
      "stress": {
        "form": "ва́жниця",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Розмовне або іронічне: поважна персона (Номис: «А що він за важниця!») або фразеологізм «яка́ ва́жниця!» (дрібниця, пусте). Не плутати з «важни́ця» (чумацький інструмент або вагарня).",
      "meaning": {
        "definitions": [
          "Поважна, значна особа (розм., ірон.); важлива справа (у вигуку: яка́ ва́жниця!)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВА́ЖНИЦЯ, і, ж., розм. 1. Поважна, значна особа. 2. Важлива справа.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано у фольклорних збірниках М. Номиса (1864) та СУМ-11."
      }
    },
    {
      "lemma": "важниця",
      "url_slug": "важниця",
      "headword": "важни́ця",
      "short_label": "підставка для підважування воза (чумацька) / вагарня",
      "gloss": "wagon jack, lever support for greasing wagon wheels (chumak); weighing station",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wɐʒˈnɪt͡sʲɐ]"
      },
      "stress": {
        "form": "важни́ця",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Історичний чумацький термін: підставка чи важіль під віз при змащуванні коліс, або приміщення з вагами (вагарня). Не плутати з «ва́жниця» (поважна особа).",
      "meaning": {
        "definitions": [
          "Підставка для підважування воза під час змащування коліс (чумац., заст.); приміщення або місце з вагами для зважування."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВАЖНИ́ЦЯ, і, ж., заст. 1. Підставка для підважування воза під час змащування коліс. 2. Те саме, що вагівни́ця.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Автентичний етнографічний термін чумацького побуту. Зафіксовано в СУМ-11."
      }
    }
  ],
  "валковий": [
    {
      "lemma": "валковий",
      "url_slug": "валковий",
      "headword": "валко́вий",
      "short_label": "пов'язаний з валком/циліндром (техн.: валкова косарка)",
      "gloss": "roller-equipped, cylindrical, roll-based (валкова дробарка, валкова косарка)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wɐlˈkɔwɪj]"
      },
      "stress": {
        "form": "валко́вий",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Технічний прикметник до «вало́к» (циліндрична обертова деталь машини: валкова косарка, валкові дробарки). Не плутати з «валкови́й» (візник в обозі).",
      "meaning": {
        "definitions": [
          "Який має у своїй будові або механізмі обертові циліндричні валки."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВАЛКО́ВИЙ, а, е. Який має в своєму механізмові валок, валки (див. вало́к⁴).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "валковий",
      "url_slug": "валковий",
      "headword": "валкови́й",
      "short_label": "візник у валці, старший обозу (імен./прикм.)",
      "gloss": "wagon-train driver, carter, convoy teamster; relating to a wagon train (валка)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wɐlkɔˈwɪj]"
      },
      "stress": {
        "form": "валкови́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Означає візника, що їде з валкою (обозом), або керівника валки возів. Не плутати з технічним «валко́вий» (механізм із циліндрами).",
      "meaning": {
        "definitions": [
          "Візник, що рухається з валкою (обозом); той, хто керує рухом валки возів."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВАЛКОВИ́Й, во́го, ч. Візник, який іде з валкою (у 1 знач.), обозом.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в класичній літературі (П. Куліш, Олесь Гончар) та СУМ-11."
      }
    }
  ],
  "виправний": [
    {
      "lemma": "виправний",
      "url_slug": "виправний",
      "headword": "випра́вний",
      "short_label": "якого можна виправити, піддатний виправленню",
      "gloss": "rectifiable, remediable, correctable, capable of being mended",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wɪˈprɑwnɪj]"
      },
      "stress": {
        "form": "випра́вний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Якісний прикметник: якого можна виправити, усунути чи переробити (про помилку, ґандж, поведінку). Не плутати з «виправни́й» (виправні роботи, виправні споруди).",
      "meaning": {
        "definitions": [
          "Якого можна виправити, переробити; який піддається виправленню."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВИПРА́ВНИЙ, а, е. Якого можна виправити, який піддається виправленню.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в СУМ-11."
      }
    },
    {
      "lemma": "виправний",
      "url_slug": "виправний",
      "headword": "виправни́й",
      "short_label": "виправні роботи, виправна колонія / регуляційний",
      "gloss": "correctional, disciplinary, penal; regulatory (river-training, coastal)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wɪprɐwˈnɪj]"
      },
      "stress": {
        "form": "виправни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Відносний прикметник: стосовний до покарання й перевиховання (виправні роботи, виправний заклад) або гідротехнічного регулювання річища (виправні споруди). Не плутати з «випра́вний» (піддатний виправленню).",
      "meaning": {
        "definitions": [
          "Стосовний до перевиховання правопорушників (виправні роботи, заклади); призначений для гідротехнічного регулювання річок (виправні споруди)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВИПРАВНИ́Й, а́, е́. Стос. до виправлення чого-небудь. Виправні споруди; виправно-трудовий.",
        "sovietization_risk": 1,
        "keywords": [
          "виправно-трудовий",
          "радянська пенітенціарна система"
        ],
        "historical_note": "У СУМ-11 термін тісно пов'язаний із радянською табірною термінологією («виправно-трудовий»). У сучасній правовій системі України нормативним є кримінально-виконавче законодавство."
      }
    }
  ],
  "випробуваний": [
    {
      "lemma": "випробуваний",
      "url_slug": "випробуваний",
      "headword": "ви́пробуваний",
      "short_label": "перевірений досвідом, загартований, надійний (минулий час)",
      "gloss": "tested, time-proven, reliable, seasoned, veteran (past passive participle)",
      "pos": "participle",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈwɪprɔbʊwɐnɪj]"
      },
      "stress": {
        "form": "ви́пробуваний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієприкметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Дієприкметник минулого часу доконаного виду від «ви́пробувати»: перевірений на практиці, загартований («випробуваний друг», «випробувані ліки»). Не плутати з процесом «випро́буваний» (той, кого випробовують зараз).",
      "meaning": {
        "definitions": [
          "Який пройшов випробування; надійний, перевірений ділом або часом."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВИ́ПРОБУВАНИЙ, а, е. 1. Дієпр. пас. мин. ч. до ви́пробувати... випробуваний війною офіцер Збройних Сил Радянського Союзу.",
        "sovietization_risk": 1,
        "keywords": [
          "Збройні Сили Радянського Союзу"
        ],
        "historical_note": "У СУМ-11 стаття ілюстрована радянською військово-патріотичною пропагандою. Сучасне нормативне значення — загальномовне, позаідеологічне."
      }
    },
    {
      "lemma": "випробуваний",
      "url_slug": "випробуваний",
      "headword": "випро́буваний",
      "short_label": "той, що проходить випробування в даний момент (теперішній час)",
      "gloss": "undergoing testing, currently being trialed/tested (present passive participle)",
      "pos": "participle",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wɪˈprɔbʊwɐnɪj]"
      },
      "stress": {
        "form": "випро́буваний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієприкметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Дієприкметник недоконаного виду до «випро́бувати»: той, що досліджується або тестується просто зараз. Не плутати з доконаним «ви́пробуваний» (уже перевірений, надійний).",
      "meaning": {
        "definitions": [
          "Дієприкм. пас. теп. ч. до випро́бувати; той, над ким або чим здійснюється випробування."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВИПРО́БУВАНИЙ, а, е. Дієпр. пас. теп. ч. до випро́бувати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "вищати": [
    {
      "lemma": "вищати",
      "url_slug": "вищати",
      "headword": "ви́щати",
      "short_label": "робитися, ставати вищим",
      "gloss": "to grow higher, become taller, rise higher (ставати вищим)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈwɪʃt͡ʃɐtɪ]"
      },
      "stress": {
        "form": "ви́щати",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Означає «робитися вищим, зростати вгору» (Нечуй-Левицький: «Стіжки в току вищають, усе ніби ростуть, як гори»). Не плутати зі звуконаслідувальним «вища́ти» (видавати писк, верещати).",
      "meaning": {
        "definitions": [
          "Ставати, робитися вищим; підніматися заввишки."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВИ́ЩАТИ, аю, аєш, недок. Ставати, робитися вищим.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано у творах класиків української літератури (І. Нечуй-Левицький) та СУМ-11."
      }
    },
    {
      "lemma": "вищати",
      "url_slug": "вищати",
      "headword": "вища́ти",
      "short_label": "верещати, пронизливо кричати, вищати від болю чи люті",
      "gloss": "to shriek, screech, squeak, scream with high-pitched sound",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wɪˈʃt͡ʃɑtɪ]"
      },
      "stress": {
        "form": "вища́ти",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Означає «видавати тонкі, різкі, пронизливі звуки, верещати» (Коцюбинський: «— Ти підеш мені зараз! — вищала вона тонким голосом»). Не плутати з «ви́щати» (рости вгору).",
      "meaning": {
        "definitions": [
          "Видавати уривчасті, різкі, високі звуки; пронизливо кричати, верещати."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВИЩА́ТИ, щу́, щи́ш, недок. Видавати уривчасті, різкі, пронизливі звуки.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в класичній літературі (М. Коцюбинський) та СУМ-11."
      }
    }
  ],
  "відбігати": [
    {
      "lemma": "відбігати",
      "url_slug": "відбігати",
      "headword": "відбі́гати",
      "short_label": "закінчити бігати / відбігати ноги (док. вид)",
      "gloss": "to finish running, complete a run; (idiom) to tire out one's legs (perf.)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidˈbʲiɦɐtɪ]"
      },
      "stress": {
        "form": "відбі́гати",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Доконаний вид: завершити біг або стомити ноги («я вже своє відбігав», «відбігати ноги»). Не плутати з недоконаним «відбіга́ти» (бігом віддалятися геть).",
      "meaning": {
        "definitions": [
          "Закінчити бігати, вичерпати сили на біг; втомити ноги біганиною."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДБІ́ГАТИ, аю, аєш, док. Закінчити бігати, бути вже не в змозі бігати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "відбігати",
      "url_slug": "відбігати",
      "headword": "відбіга́ти",
      "short_label": "бігти геть, віддалятися бігом (недок. вид)",
      "gloss": "to run away, retreat running, rush away (imperf. corresponding to відбігти)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidbʲiˈɦɑtɪ]"
      },
      "stress": {
        "form": "відбіга́ти",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Недоконаний вид до «відбігти»: бігом віддалятися від когось або чогось. Не плутати з доконаним «відбі́гати» (закінчити біганину).",
      "meaning": {
        "definitions": [
          "Бігом віддалятися від кого-, чого-небудь; швидко відходити."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДБІГА́ТИ, а́ю, а́єш, недок., ВІДБІ́ГТИ, іжу́, іжи́ш... док. 1. неперех. Бігом віддалятися від кого-, чого-небудь.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "відбірний": [
    {
      "lemma": "відбірний",
      "url_slug": "відбірний",
      "headword": "відбі́рний",
      "short_label": "найкращий, добірний, першосортний",
      "gloss": "select, choice, prime quality, top-grade, hand-picked (synonym to добірний)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidˈbʲirnɪj]"
      },
      "stress": {
        "form": "відбі́рний",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «найкращий за якістю, старанно відібраний, добірний» (відбірне зерно, відбірні вояки). Не плутати з функціональним «відбірни́й» (призначений для відбору: відбірна комісія).",
      "meaning": {
        "definitions": [
          "Те саме, що добі́рний; першосортний, найкращий із загальної маси."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДБІ́РНИЙ, а, е, рідко. Те саме, що добі́рний 1; найкращий.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "відбірний",
      "url_slug": "відбірний",
      "headword": "відбірни́й",
      "short_label": "призначений для відбору (відбірна комісія, турнір)",
      "gloss": "qualifying, screening, sorting, selection-oriented (відбірна комісія, відбірні матчі)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidbʲirˈnɪj]"
      },
      "stress": {
        "form": "відбірни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Функціональний прикметник: призначений для процедури відбору (відбірна комісія, відбірна машина, відбірний тур). Не плутати з якісним «відбі́рний» (найвищої якості).",
      "meaning": {
        "definitions": [
          "Призначений або створений для здійснення відбору кого-, чого-небудь."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДБІРНИ́Й, а́, е́. Признач. для відбору кого-, чого-небудь. Відбірна комісія; Відбірна машина.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "відвальний": [
    {
      "lemma": "відвальний",
      "url_slug": "відвальний",
      "headword": "відва́льний",
      "short_label": "пов'язаний з відвалом породи/шлаку (гірн.)",
      "gloss": "spoil-bank, dump-related (відвальний шлак - slag dump material)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidˈwɑlʲnɪj]"
      },
      "stress": {
        "form": "відва́льний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Стосується насипу відходів або породи — відва́лу (відвальний шлак). Не плутати з «відвальни́й» (призначений для відвалювання ґрунту: відвальний міст, відвальний плуг).",
      "meaning": {
        "definitions": [
          "Стосовний до насипу відходів, породи чи шлаку (відвалу) у гірничій справі."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДВА́ЛЬНИЙ, а, е. Стос. до відвалу (в 3 знач.). Розробку відвального шлаку треба збільшити.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "відвальний",
      "url_slug": "відвальний",
      "headword": "відвальни́й",
      "short_label": "призначений для відвалювання (відвальний міст, плуг)",
      "gloss": "moldboard, dumping, earth-moving, soil-clearing (відвальний міст, відвальний плуг)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidwɐlʲˈnɪj]"
      },
      "stress": {
        "form": "відвальни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає механізм або деталь для відкидання й відгортання землі, породи (відвальний міст, відвальний леміш). Не плутати з «відва́льний» (який міститься у відвалі).",
      "meaning": {
        "definitions": [
          "Призначений для переміщення, відгортання або скидання розкритої породи чи землі."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДВАЛЬНИ́Й, а́, е́. Признач. для відвалювання. У залізорудних кар’єрах працюють відвальні мости.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "відливний": [
    {
      "lemma": "відливний",
      "url_slug": "відливний",
      "headword": "відли́вний",
      "short_label": "пов'язаний з морським відливом/відпливом (відливні години)",
      "gloss": "ebb-related, tidal outflow, low-tide (відливні години - low tide hours)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidˈlɪwnɪj]"
      },
      "stress": {
        "form": "відли́вний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Стосується морського відпливу/відливу (періодичного спаду рівня моря: відливні години). Не плутати з «відливни́й» (литий виріб або водовідливний насос).",
      "meaning": {
        "definitions": [
          "Прикметник до відплив/відлив (періодичний спад рівня морської води)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДЛИ́ВНИЙ, а, е, рідко. Прикм. до відли́в 2. Відливні години.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "відливний",
      "url_slug": "відливний",
      "headword": "відливни́й",
      "short_label": "литий (відливні вироби) / водовідливний (відливний насос)",
      "gloss": "cast, molded (foundry products); drainage, water-pumping (відливний насос)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidlɪwˈnɪj]"
      },
      "stress": {
        "form": "відливни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «виготовлений литтям (відливні деталі)» або «призначений для відкачування рідини (відливний насос)». Не плутати з «відли́вний» (морський відплив).",
      "meaning": {
        "definitions": [
          "Виготовлений способом лиття (відливні вироби); призначений для викачування води або рідини."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДЛИВНИ́Й, а́, е́. 1. Признач. для відливання рідини. Відливний насос. 2. Вигот. литтям. Відливні вироби.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "відрубний": [
    {
      "lemma": "відрубний",
      "url_slug": "відрубний",
      "headword": "відру́бний",
      "short_label": "відокремлений, ізольований, самітний (хутір відрубний)",
      "gloss": "isolated, separate, detached, secluded (відрубний хутір - isolated farmstead)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidˈrubnɪj]"
      },
      "stress": {
        "form": "відру́бний",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «відокремлений, самітний, розміщений окремо від інших (хутір відрубний; відрубний звичай)». Не плутати з «відрубни́й» (земельний відруб).",
      "meaning": {
        "definitions": [
          "Який перебуває або розміщений окремо від інших; відокремлений, осібний."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДРУ́БНИЙ, а, е. 1. Який перебував, міститься окремо або відокремлений від чого-небудь.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "відрубний",
      "url_slug": "відрубний",
      "headword": "відрубни́й",
      "short_label": "земельний відруб (іст., селянські реформи)",
      "gloss": "relating to historical peasant land parcels (odrub) segregated from communal tenure",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʲidrubˈnɪj]"
      },
      "stress": {
        "form": "відрубни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Історичний аграрний термін: стосовний до відрубу — земельної ділянки, виділеної у приватну власність селянина з общинного володіння під час Столипінської реформи. Не плутати з якісним «відру́бний» (ізольований).",
      "meaning": {
        "definitions": [
          "Іст. Прикметник до відру́б (земельна ділянка, виділена з общинного володіння в приватну власність)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВІДРУБНИ́Й, а́, е́. 1. Стос. до відрубу (в 2 знач.). 2. іст. Прикм. до відру́б 3.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "вугровий": [
    {
      "lemma": "вугровий",
      "url_slug": "вугровий",
      "headword": "вугро́вий",
      "short_label": "пов'язаний з акне / висипанням вугрів на шкірі",
      "gloss": "acne-related, comedonal, pimple-related (вугровий висип - acne rash)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʊˈɦrɔwɪj]"
      },
      "stress": {
        "form": "вугро́вий",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Медичний термін: стосовний до шкірних вугрів (акне, запалення сальних залоз: вугровий висип). Не плутати з іхтіологічним «вугрови́й» (пов'язаний з рибою вугром).",
      "meaning": {
        "definitions": [
          "Прикметник до вуго́р (запальний вузлик або комедон на шкірі); вугровий висип."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВУГРО́ВИЙ, а, е. Прикм. до вуго́р¹ (висип).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "вугровий",
      "url_slug": "вугровий",
      "headword": "вугрови́й",
      "short_label": "пов'язаний з рибою вугром (вугровий промисел)",
      "gloss": "eel-related, anguillid (вугровий промисел - eel fishing, eel industry)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[wʊɦrɔˈwɪj]"
      },
      "stress": {
        "form": "вугрови́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Іхтіологічний та промисловий прикметник: стосовний до прісноводної або морської риби вуго́р (вугровий промисел, вугрове м'ясо). Не плутати з дерматологічним «вугро́вий» (акне).",
      "meaning": {
        "definitions": [
          "Прикметник до риби вуго́р; пов'язаний з виловом або переробкою вугрів."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ВУГРОВИ́Й, а́, е́. Прикм. до вуго́р² (риба).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "гаванський": [
    {
      "lemma": "гаванський",
      "url_slug": "гаванський",
      "headword": "га́ванський",
      "short_label": "портовий, пов'язаний з морською гаванню",
      "gloss": "harbor-related, haven-related, port-related (гаванські споруди - harbor structures)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈɦɑwɐnʲsʲkɪj]"
      },
      "stress": {
        "form": "га́ванський",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Прикметник до «га́вань» — морська або річкова затока для стоянки суден (гаванські крани, набережна, гаванські споруди). Не плутати з топонімічним «гава́нський» (стосовний до столиці Куби Гавани).",
      "meaning": {
        "definitions": [
          "Прикметник до га́вань; призначений для облаштування або обслуговування гавані."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ГА́ВАНСЬКИЙ, а, е. Прикм. до га́вань.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "гаванський",
      "url_slug": "гаванський",
      "headword": "гава́нський",
      "short_label": "стосовний до Гавани на Кубі (гава́нська сигара)",
      "gloss": "Havanese, Havana-related (capital of Cuba; e.g. Havana cigar)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ɦɐˈwɑnʲsʲkɪj]"
      },
      "stress": {
        "form": "гава́нський",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Топонімічний прикметник: стосовний до міста Гава́на на Кубі та кубинських сигар (гаванські сигари). Не плутати з портовим терміном «га́ванський».",
      "meaning": {
        "definitions": [
          "Прикметник до назви столиці Куби Гава́на; гаванський тютюн, гаванські сигари."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ГАВА́НСЬКИЙ, а, е, розм. Прикм. до гава́на.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "гребінник": [
    {
      "lemma": "гребінник",
      "url_slug": "гребінник",
      "headword": "гребі́нник",
      "short_label": "кормова злакова трава (ботаніка: Cynosurus)",
      "gloss": "crested dog's-tail grass (botany: Cynosurus L., family Poaceae)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ɦreˈbʲinʲːɪk]"
      },
      "stress": {
        "form": "гребі́нник",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Ботанічна назва злакової трави Cynosurus L. (гребінник звичайний). Не плутати з назвою професії «гребінни́к» (майстер гребінців).",
      "meaning": {
        "definitions": [
          "Однорічна або багаторічна кормова лучна трава родини злакових (Cynosurus L.)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ГРЕБІ́ННИК, а, ч. (Cynosurus L.). Однорічна чи багаторічна кормова рослина родини злакових.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "гребінник",
      "url_slug": "гребінник",
      "headword": "гребінни́к",
      "short_label": "ремісник, який виготовляє гребінці",
      "gloss": "comb-maker, artisan craftsman making hair combs",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ɦrebʲinʲˈnɪk]"
      },
      "stress": {
        "form": "гребінни́к",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Традиційна назва майстра, що вирізає та продає дерев'яні чи рогові гребінці й гребінки. Не плутати з ботанічним «гребі́нник» (трава).",
      "meaning": {
        "definitions": [
          "Ремісник, майстер, що виготовляє гребінці та гребінки."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ГРЕБІННИ́К, а́, ч. Той, що виробляє гребінки, гребінці (у 1 знач.).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "дозвільний": [
    {
      "lemma": "дозвільний",
      "url_slug": "дозвільний",
      "headword": "дозві́льний",
      "short_label": "вільний від праці, присвячений відпочинку (дозвільний час)",
      "gloss": "leisure-related, unoccupied, idle, spare (дозвільний час - leisure hours)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[dɔzʲˈwʲilʲnɪj]"
      },
      "stress": {
        "form": "дозві́льний",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «вільний, не зайнятий працею; пов'язаний із проведенням дозвілля» (Леся Українка: «дозвільний час»). Не плутати з юридичним терміном «дозвільни́й» (дозвільний документ).",
      "meaning": {
        "definitions": [
          "Вільний, не зайнятий якою-небудь роботою чи працею; присвячений відпочинку."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДОЗВІ́ЛЬНИЙ, а, е. Вільний, не зайнятий якою-небудь працею.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "дозвільний",
      "url_slug": "дозвільний",
      "headword": "дозвільни́й",
      "short_label": "дозвільний документ / дозвільна система (дозвіл на діяльність)",
      "gloss": "permissive, regulatory, licensing, authorization-related (дозвільний документ - permit)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[dɔzʲwʲilʲˈnɪj]"
      },
      "stress": {
        "form": "дозвільни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Офіційно-діловий прикметник: такий, що надає або містить юридичний дозвіл (дозвільний документ, дозвільна система). Не плутати з рекреаційним «дозві́льний» (дозвілля).",
      "meaning": {
        "definitions": [
          "Який містить або надає офіційний дозвіл на здійснення певної діяльності."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДОЗВІЛЬНИ́Й, а́, е́. Який містить дозвіл на здійснення чого-небудь. Дозвільний документ.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "домовий": [
    {
      "lemma": "домовий",
      "url_slug": "домовий",
      "headword": "до́мовий",
      "short_label": "житловий, хатній (домова книга, домовий комітет)",
      "gloss": "residential, domestic, household-related (домова книга - residence registry book)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈdɔmɔwɪj]"
      },
      "stress": {
        "form": "до́мовий",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Прикметник до «дім» — пов'язаний із житловим будинком (домова книга, домовий комітет). В академічних словниках фіксується також варіант наголосу домо́вий (Грінченко: «домОвИй»). Не плутати з іменником «домо́вий» / «домови́й» (міфологічний хатній дух).",
      "meaning": {
        "definitions": [
          "Стосовний до житлового будинку або домашнього господарства."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДОМО́ВИЙ, а, е. 1. Стос. до дому (у 1-3 знач.). Домова книга.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "домовий",
      "url_slug": "домовий",
      "headword": "домо́вий",
      "short_label": "хатній дух, домовик у народній демонології",
      "gloss": "house spirit, domestic goblin, brownie (equivalent to домовик)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[dɔˈmɔwɪj]"
      },
      "stress": {
        "form": "домо́вий",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Іменник народної демонології: дух оселі (те саме, що домови́к). В усній традиції та літературі трапляється також варіант із кінцевим наголосом домови́й. Не плутати з відносним прикметником «до́мовий» (домова книга).",
      "meaning": {
        "definitions": [
          "Персонаж слов'янської народної міфології; добрий або бешкетний хатній дух, охоронець оселі (домовик)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДОМОВИ́Й, во́го, ч. Те саме, що домови́к.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в класичній літературі (П. Гулак-Артемовський) та СУМ-11."
      }
    }
  ],
  "досвідний": [
    {
      "lemma": "досвідний",
      "url_slug": "досвідний",
      "headword": "до́свідний",
      "short_label": "експериментальний, дослідний (досвідне поле, дослід)",
      "gloss": "experimental, empirical, trial (досвідне поле - experimental field station)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈdɔsʲwʲidnɪj]"
      },
      "stress": {
        "form": "до́свідний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «заснований на експериментах або призначений для проведення дослідів» (досвідне поле, досвідне господарство). Не плутати з якісним «досвідни́й» (досвідчений, мудрий життєвим досвідом).",
      "meaning": {
        "definitions": [
          "Заснований на науковому експерименті або призначений для здійснення дослідів."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДО́СВІДНИЙ, а, е. 1. Заснований на досвіді (у 2 знач.). Досвідне пізнання. 2. Признач. для ведення дослідів. Досвідні машини.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "досвідний",
      "url_slug": "досвідний",
      "headword": "досвідни́й",
      "short_label": "досвідчений, бувалий, який має життєвий досвід (рідко)",
      "gloss": "experienced, seasoned, practiced, wise (synonym to досвідчений)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[dɔsʲwʲidˈnɪj]"
      },
      "stress": {
        "form": "досвідни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «досвідчений, бувалий, знаючий» (Франко: «Мій батько досвідний чоловік і радо служить громаді»). Не плутати з експериментальним «до́свідний».",
      "meaning": {
        "definitions": [
          "Який має багатий життєвий або фаховий досвід; досвідчений."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДОСВІДНИ́Й, а́, е́, рідко. Який має життєвий досвід; досвідчений.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано у творах Івана Франка та СУМ-11."
      }
    }
  ],
  "жабник": [
    {
      "lemma": "жабник",
      "url_slug": "жабник",
      "headword": "жа́бник",
      "short_label": "зневажливе прізвисько плавця на мілководді",
      "gloss": "puddle-wader, shallow-water paddler (pejorative nickname)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈʒɑbnɪk]"
      },
      "stress": {
        "form": "жа́бник",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Зневажливе прізвисько людини, яка бовтається на мілині серед жаб і жабуриння. Не плутати з лучною рослиною «жабни́к».",
      "meaning": {
        "definitions": [
          "Зневажливе прізвисько людини, що бовтається чи плаває у неглибокій багнистій воді."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЖА́БНИК, а, ч., зневажл. Прізвисько людини, яка бовтається або плаває у неглибокій воді.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "жабник",
      "url_slug": "жабник",
      "headword": "жабни́к",
      "short_label": "трав'яниста рослина (ботаніка: Filago L. / Caltha)",
      "gloss": "marsh marigold or cudweed plant (botany: Filago L. or Caltha palustris)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ʒɐbˈnɪk]"
      },
      "stress": {
        "form": "жабни́к",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Ботанічна назва трав'янистої рослини Filago L. (родини айстрових) або водяного жовтцю (Caltha palustris). Не плутати з глузливим прізвиськом «жа́бник».",
      "meaning": {
        "definitions": [
          "Трав'яниста рослина роду Filago або Caltha palustris, поширена на вологих луках і берегах річок."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЖАБНИ́К, у́, ч. (Filago L.). Багаторічна трав’яниста рослина родини жовтцевих [айстрових].",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "жировий": [
    {
      "lemma": "жировий",
      "url_slug": "жировий",
      "headword": "жиро́вий",
      "short_label": "картярський термін у народних іграх / масть",
      "gloss": "trump-suit, winning card suit in folk games; (arch.) out of wedlock",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ʒɪˈrɔwɪj]"
      },
      "stress": {
        "form": "жиро́вий",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Картярський та етнографічний прикметник до «жир» (масть або виграшна комбінація в картах). У Грінченка також значення: позашлюбний («жирова дочка»). Не плутати з біохімічним «жирови́й» (складений із жиру).",
      "meaning": {
        "definitions": [
          "Прикметник до жир (масть або козир у картярських іграх); фольклорний термін."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЖИРО́ВИЙ, а, е. Прикм. до жир² (картярська масть).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "жировий",
      "url_slug": "жировий",
      "headword": "жирови́й",
      "short_label": "жирова тканина, ліпідний / багатий на жир",
      "gloss": "fatty, lipid, adipose, rich in fats (жирова тканина, жирові кислоти)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ʒɪrɔˈwɪj]"
      },
      "stress": {
        "form": "жирови́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Загальновживаний біологічний та кулінарний термін: складений із жиру або багатий на жири (жирова клітковина, жирові відкладення). Не плутати з картярським «жиро́вий».",
      "meaning": {
        "definitions": [
          "Складений із жиру або багатий на жири; пов'язаний із ліпідами та їхнім обміном."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЖИРОВИ́Й, а́, е́. 1. Прикм. до жир¹. Жирові продукти; жирова тканина.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "жмуритися": [
    {
      "lemma": "жмуритися",
      "url_slug": "жмуритися",
      "headword": "жму́ритися",
      "short_label": "мружити очі, щуритися від сонця чи світла",
      "gloss": "to squint, narrow/half-close one's eyes against glare or light",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈʒmurɪtɪsʲɐ]"
      },
      "stress": {
        "form": "жму́ритися",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Означає «стуляти повіки, напівзаплющувати очі від світла; мружитися». Не плутати з дитячою грою «жмури́тися» (бути тим, хто шукає у хованках).",
      "meaning": {
        "definitions": [
          "Стуляти повіки, напівзаплющувати очі від сонця, вітру або посмішки; мружитися."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЖМУ́РИТИСЯ, рюся, ришся; недок. Стуляючи повіки, частково прикривати очі.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "жмуритися",
      "url_slug": "жмуритися",
      "headword": "жмури́тися",
      "short_label": "грати в жмурки (хованки), бути ведучим",
      "gloss": "to play hide-and-seek / blind man's buff (to be the seeker / blindfolded player)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ʒmʊˈrɪtɪsʲɐ]"
      },
      "stress": {
        "form": "жмури́тися",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Означає бути ведучим у дитячій грі в жмурки (хованки): заплющити очі або зав'язати їх хусткою і шукати інших гравців. Не плутати з «жму́ритися» (мружити повіки).",
      "meaning": {
        "definitions": [
          "Зав'язати або стулити очі й шукати інших учасників народної дитячої гри в жмурки (хованки)."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЖМУРИ́ТИСЯ, жмурю́ся, жму́ришся, недок. Зав’язати очі і ловити або відшукувати інших учасників гри в жмурки.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "завізний": [
    {
      "lemma": "завізний",
      "url_slug": "завізний",
      "headword": "заві́зний",
      "short_label": "перевантажений справами, дуже зайнятий (розм.)",
      "gloss": "overloaded with work, extremely busy, preoccupied (dial./colloq.)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈwʲiznɪj]"
      },
      "stress": {
        "form": "заві́зний",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Розмовне й народне: дуже завантажений роботою чи замовленнями (Грінченко: «Чи ви завізні? Може б мені чоботи пошили?»). Не плутати з «завізни́й» (імпортований з інших країв).",
      "meaning": {
        "definitions": [
          "Дуже зайнятий роботою, перевантажений клопотами чи справами (розм.)."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАВІ́ЗНИЙ, а, е, розм. 1. Дуже зайнятий, завантажений.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "завізний",
      "url_slug": "завізний",
      "headword": "завізни́й",
      "short_label": "імпортований, привезений з інших регіонів (не місцевий)",
      "gloss": "imported, brought in from outside, non-local (завізне насіння, завізні товари)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐwʲizˈnɪj]"
      },
      "stress": {
        "form": "завізни́й",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Означає «доставлений, привезений або імпортований ззовні; протилежне до місцевий» (завізне зерно, завізні матеріали). Не плутати з розмовним «заві́зний» (заклопотаний).",
      "meaning": {
        "definitions": [
          "Завезений, доставлений з іншої місцевості чи країни; нерідний, немісцевий."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАВІЗНИ́Й, а́, е́. Завезений, привезений звідки-небудь; протилежне місцевий.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "загородка": [
    {
      "lemma": "загородка",
      "url_slug": "загородка",
      "headword": "за́городка",
      "short_label": "загін для тварин / зменшене до за́города",
      "gloss": "corral, small animal pen, paddock (diminutive of за́города)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈzɑɦɔrɔdkɐ]"
      },
      "stress": {
        "form": "за́городка",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Зменшене до за́города: обгороджене місце, стійбище або хлівчик для утримання худоби чи птиці. Не плутати з легкою кімнатною перегородкою «загоро́дка».",
      "meaning": {
        "definitions": [
          "Зменшене до за́города; загін або обгороджене місце для свійських тварин."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗА́ГОРОДКА, и, ж. Зменш. до за́города. Коли в загородці стих галас, лоша вже не так мотало головою.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "загородка",
      "url_slug": "загородка",
      "headword": "загоро́дка",
      "short_label": "низька перегородка, парканчик, бар'єр",
      "gloss": "low partition, screen, lightweight dividing fence/barrier",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐɦɔˈrɔdkɐ]"
      },
      "stress": {
        "form": "загоро́дка",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Означає низьку легку огорожу, кімнатний бар'єр чи дерев'яну перегородку. Не плутати з загоном для тварин «за́городка».",
      "meaning": {
        "definitions": [
          "Низька або невелика огорожа, легкий паркан чи внутрішня перегородка в будівлі."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАГОРО́ДКА, и, ж. Низька або невелика загоро́да (у 1 знач.).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "загукати": [
    {
      "lemma": "загукати",
      "url_slug": "загукати",
      "headword": "загу́кати",
      "short_label": "почати шуміти, лунко гудіти, видавати гук/глухий гул",
      "gloss": "to begin to rumble, roar, boom, echo (hollow sound, inanimate or bird call)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈɦukɐtɪ]"
      },
      "stress": {
        "form": "загу́кати",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Почати видавати лункий, глухий гул, шуміти (ліс загукав, буря загукала, птах загукав у болоті). Не плутати з покликанням людини «загука́ти» (голосно гукнути, покликати).",
      "meaning": {
        "definitions": [
          "Почати видавати лункий гул, шум або глухі монотонні звуки (про природу, птахів чи механізми)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАГУ́КАТИ, аю, аєш, док., розм. 1. неперех. Почати гукати, видавати гук, шум і т. ін.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "загукати",
      "url_slug": "загукати",
      "headword": "загука́ти",
      "short_label": "голосно покликати людину / вигукнути окрик / заспівати",
      "gloss": "to call out to someone, summon aloud, begin shouting/cheering; to break into song",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐɦʊˈkɑtɪ]"
      },
      "stress": {
        "form": "загука́ти",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Означає «голосно крикнути, покликати когось голосним окриком» (Т. Шевченко: «Загукали, повалили...»; Грінченко: «Феся загукала»). Не плутати з природним гулом «загу́кати».",
      "meaning": {
        "definitions": [
          "Почати кликати когось на повний голос або вигукувати слова; голосно озватися; (фолькл.) заспівати."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАГУКА́ТИ, а́ю, а́єш, док. Почати гукати, вигукувати які-небудь слова, звуки.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "зазнаний": [
    {
      "lemma": "зазнаний",
      "url_slug": "зазнаний",
      "headword": "за́знаний",
      "short_label": "пережитий на власному досвіді (пасивний дієприкметник)",
      "gloss": "experienced, felt, tasted, endured (past passive participle from зазнати)",
      "pos": "participle",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈzɑznɐnɪj]"
      },
      "stress": {
        "form": "за́знаний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієприкметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Пасивний дієприкметник до «зазна́ти»: пережитий, випробуваний на собі (зазнане щастя, зазнані страждання). Не плутати з розмовним прикметником «зазна́ний» (пихатий).",
      "meaning": {
        "definitions": [
          "Дієприкм. пас. до зазна́ти; пізнаний або пережитий на власному життєвому досвіді."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗА́ЗНАНИЙ, а, е. Дієпр. пас. мин. ч. до зазна́ти. Вона лежала і сподівалася, що воно прийде знов, те чисте, зазнане в юності кохання.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "зазнаний",
      "url_slug": "зазнаний",
      "headword": "зазна́ний",
      "short_label": "зарозумілий, пихатий, який виявляє зазнайство (розм.)",
      "gloss": "arrogant, conceited, haughty, boastful (showing зазнайство)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐzˈnɑnɪj]"
      },
      "stress": {
        "form": "зазна́ний",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Розмовний якісний прикметник: сповнений чванливості, зарозумілий, який виявляє зазнайство. Не плутати з віддієслівним дієприкметником «за́знаний».",
      "meaning": {
        "definitions": [
          "Який виявляє зазнайство; пихатий, гордовитий, зарозумілий (розм.)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАЗНА́НИЙ, а, е, розм. Який виявляє зазнайство. — Бачились ми не раз і не два. Я була боязка: багатир!.. А він мені, було, й кричить: «Геть з дороги!» Отакий зазнаний був!",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "закупка": [
    {
      "lemma": "закупка",
      "url_slug": "закупка",
      "headword": "за́купка",
      "short_label": "куплений товар, придбана річ (заст., розм.)",
      "gloss": "purchased goods, bought merchandise, purchase items (arch./colloq.)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈzɑkʊpkɐ]"
      },
      "stress": {
        "form": "за́купка",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Означає куплений товар чи річ (результат придбання: «сховала свої закупки»). Не плутати з процесом закупівлі «заку́пка».",
      "meaning": {
        "definitions": [
          "Те, що куплене; придбаний товар, речі, купівля (заст., розм.)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗА́КУПКА, и, ж., заст. Те, що куплене; куплений товар. Вона сховала всі свої закупки.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в класичній літературі (Леся Українка) та СУМ-11."
      }
    },
    {
      "lemma": "закупка",
      "url_slug": "закупка",
      "headword": "заку́пка",
      "short_label": "процес придбання / закупівля товарів чи сировини",
      "gloss": "procurement, purchasing, bulk buying (action equivalent to закупівля)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈkupkɐ]"
      },
      "stress": {
        "form": "заку́пка",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Означає процес закупівлі сировини чи товарів (те саме, що закупівля; у сучасній мові рекомендовано нормативне «закупівля»). Не плутати з купленими товарами «за́купка».",
      "meaning": {
        "definitions": [
          "Дія за значенням закупити; організоване оптове придбання товарів або продукції."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАКУ́ПКА, и, ж. Те саме, що закупі́вля. Система державних закупок повинна бути спрямована...",
        "sovietization_risk": 1,
        "keywords": [
          "державні закупки",
          "планова економіка"
        ],
        "historical_note": "У радянський період термін «державні закупки» використовувався як інструмент планової економіки та вилучення сільськогосподарської продукції. У сучасній нормативній мові переважає форма «закупівля»."
      }
    }
  ],
  "замішка": [
    {
      "lemma": "замішка",
      "url_slug": "замішка",
      "headword": "за́мішка",
      "short_label": "густа борошняна страва, каша з кукурудзяного чи житнього борошна",
      "gloss": "thick porridge, scalded cornmeal or rye mush (traditional dish)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈzɑmʲiʃkɐ]"
      },
      "stress": {
        "form": "за́мішка",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Традиційна українська страва: каша з борошна, запареного окропом і звареного в казанку. Не плутати з сум'яттям чи затримкою «замі́шка».",
      "meaning": {
        "definitions": [
          "Традиційна народна страва з борошна, завареного окропом і звареного в окропі."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗА́МІШКА, и, ж. 1. Рідка або густа страва з борошна, запареного окропом і звареного.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в етнографічних джерелах та СУМ-11."
      }
    },
    {
      "lemma": "замішка",
      "url_slug": "замішка",
      "headword": "замі́шка",
      "short_label": "сум'яття, плутанина / перешкода, затримка у справі",
      "gloss": "confusion, turmoil, embarrassment, hitch, muddle, delay",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈmʲiʃkɐ]"
      },
      "stress": {
        "form": "замі́шка",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Означає «несподівана плутанина, сум'яття, збентеження або затримка у русі» (Драгоманов: «Замішка зробилась»; Грінченко: «Багато буде замішки»). Не плутати з кулінарною «за́мішка».",
      "meaning": {
        "definitions": [
          "Сум'яття, безладдя, замішання серед людей; перешкода чи затримка."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАМІ́ШКА, и, ж., розм. 1. Те саме, що заміша́ння 2. 2. Перешкода, перепона; затримка.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "зарубка": [
    {
      "lemma": "зарубка",
      "url_slug": "зарубка",
      "headword": "за́рубка",
      "short_label": "насічка, карб на дереві або знарядді (сокирою, ножем)",
      "gloss": "notch, nick, cut, kerf, axe mark on timber (made with axe or blade)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈzɑrʊbkɐ]"
      },
      "stress": {
        "form": "за́рубка",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Повсякденне й ремісниче: насічка, карб або позначка на дереві, зроблені сокирою чи ножем («зарубка на пам'ять»). Не плутати з дією підрубування пласта комбайном «зару́бка».",
      "meaning": {
        "definitions": [
          "Виїмка або спеціальна насічка, карб, зроблений гострим знаряддям на дереві чи камені."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗА́РУБКА, и, ж. Виїмка взагалі або спеціальна позначка на чому-небудь, зроблена сокирою, ножем чи іншим знаряддям.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "зарубка",
      "url_slug": "зарубка",
      "headword": "зару́бка",
      "short_label": "підрубування вугільного пласта врубовою машиною (гірн.)",
      "gloss": "undercutting, kerfing, cutting slot in coal seam with mining cutter",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈrubkɐ]"
      },
      "stress": {
        "form": "зару́бка",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Гірничий виробничий процес: прорізання щілини або підсікання пласта корисної копалини врубовою машиною чи комбайном. Не плутати з сокирною насічкою «за́рубка».",
      "meaning": {
        "definitions": [
          "Гірн. Дія за значенням зарубувати; утворення зарубу у вугільному або соляному пласті."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАРУ́БКА, и, ж., гірн. Те саме, що зару́бування. Широке застосування врубових машин...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський індустріальний період (СУМ-11)."
      }
    }
  ],
  "затискати": [
    {
      "lemma": "затискати",
      "url_slug": "затискати",
      "headword": "зати́скати",
      "short_label": "замучити стисканням, тиснути до втоми в обіймах (док. вид)",
      "gloss": "to torment by excessive squeezing/hugging, squeeze tightly to exhaustion (perf.)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈtɪskɐtɪ]"
      },
      "stress": {
        "form": "зати́скати",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "доконаний"
        }
      },
      "distinction_note": "Доконаний вид: замучити, давлячи чи міцно обіймаючи. Не плутати з тривалим недоконаним затисканням у кулаку чи лещатах «затиска́ти».",
      "meaning": {
        "definitions": [
          "Док. Замучити, давлячи, мнучи, міцно тиснучи в обіймах (розм.)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАТИ́СКАТИ, аю, аєш, дек. [док.], перех., розм. Замучити, давлячи, мнучи, обіймаючи і т. ін.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    },
    {
      "lemma": "затискати",
      "url_slug": "затискати",
      "headword": "затиска́ти",
      "short_label": "стискати в кулаці/лещатах, притискати міцно (недок. вид)",
      "gloss": "to squeeze, clamp, grip tight in fist or vise, compress, stifle (imperf. to затиснути)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐtɪsʲˈkɑtɪ]"
      },
      "stress": {
        "form": "затиска́ти",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Недоконаний вид до «затиснути»: тримати стиснутим у кулаці, закріплювати в лещатах (Грінченко: «Впіймав горобця та й затискає в кулаку»). Не плутати з доконаним «зати́скати» (замучити обіймами).",
      "meaning": {
        "definitions": [
          "Недок. Міцно стискати щось рукою чи пальцями; закріплювати лещатами або гвинтом."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАТИСКА́ТИ, а́ю, а́єш... недок., ЗАТИ́СНУТИ, ну, неш... док. 1. Міцно охоплюючи або тримаючи, стискати.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ],
  "затулка": [
    {
      "lemma": "затулка",
      "url_slug": "затулка",
      "headword": "за́тулка",
      "short_label": "заслінка в печі, металева чи чавунна затулка",
      "gloss": "stove shutter, oven damper, iron cover for traditional Ukrainian hearth",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈzɑtʊlkɐ]"
      },
      "stress": {
        "form": "за́тулка",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Побутове слово: заслінка, якою закривають отвір варильної або хлібної печі (чавунна затулка). Не плутати з зоологічним молюском «зату́лка».",
      "meaning": {
        "definitions": [
          "Металевий або дерев'яний щиток, заслінка для затуляння челюстей печі (розм.)."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗА́ТУЛКА, и, ж., розм. Те саме, що за́слінка. Розпучливий брязкіт чавунних затулок...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "lemma": "затулка",
      "url_slug": "затулка",
      "headword": "зату́лка",
      "short_label": "прісноводний черевоногий молюск із кришечкою (зоол.: Valvata)",
      "gloss": "valve snail, operculate snail (zoology: genus Valvata, family Valvatidae)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[zɐˈtulkɐ]"
      },
      "stress": {
        "form": "зату́лка",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "feminine",
          "animacy": "inanimate"
        }
      },
      "distinction_note": "Зоологічний таксон: рід прісноводних равликів Valvata, устя раковини яких закривається твердою круглою кришечкою. Не плутати з пічною заслінкою «за́тулка».",
      "meaning": {
        "definitions": [
          "Зоол. Рід невеликих прісноводних черевоногих молюсків з округлою раковиною та щільною захисною кришечкою."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗАТУ́ЛКА, и, ж., зоол. Рід черевоногих молюсків, які мають округло-дзигоподібну раковину з кришечкою...",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11)."
      }
    }
  ],
  "значковий": [
    {
      "lemma": "значковий",
      "url_slug": "значковий",
      "headword": "зна́чковий",
      "short_label": "картографічний метод умовних значків / символьний",
      "gloss": "symbol-based, badge-related; cartographic symbol method (значковий метод на картах)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈznɑt͡ʃkɔwɪj]"
      },
      "stress": {
        "form": "зна́чковий",
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Картографічний та науковий прикметник до «значо́к» — умовне позначення об'єктів на карті (значковий метод у тематичних атласах). Не плутати з козацьким званням «значкови́й» товариш.",
      "meaning": {
        "definitions": [
          "Прикметник до значо́к; картографічний спосіб нанесення інформації за допомогою умовних значків."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗНАЧКО́ВИЙ [зна́чковий], а, е. Прикм. до значо́к 1, 2. Значковий метод застосовується найчастіше.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський період (СУМ-11). У радянських джерелах наголос значко́вий зазначено як паралельний до зна́чковий."
      }
    },
    {
      "lemma": "значковий",
      "url_slug": "значковий",
      "headword": "значкови́й",
      "short_label": "значковий товариш (козацький старшинський чин) / прапороносець",
      "gloss": "Cossack officer rank / banner bearer (значковий товариш in Hetmanate era, ensign)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[znɐt͡ʃkɔˈwɪj]"
      },
      "stress": {
        "form": "значкови́й",
        "source": "Грінченко (1907) / ВТС"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Історичний військовий термін часів Гетьманщини: молодший старшинський чин «значковий товариш» (Котляревський: «Значкові товариші...»), або козацький прапороносець полку. Не плутати з картографічним «зна́чковий».",
      "meaning": {
        "definitions": [
          "Іст. Козацький чин значкового товариша в Гетьманщині; козак, що носив полковий значок (прапорець)."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗНАЧКОВИ́Й, во́го, ч., рідко. Той, хто несе який-небудь церковний [або військовий] знак.",
        "sovietization_risk": 1,
        "keywords": [
          "церковний знак",
          "витіснення козацького чину"
        ],
        "historical_note": "У СУМ-11 козацький термін штучно зведено до церковного прапороносця («рідко. Той, хто несе церковний знак»). Справжнє історичне значення значкового товариша збережено у Грінченка (1907–1909) всупереч імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
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
