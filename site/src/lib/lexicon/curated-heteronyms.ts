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
      "distinction_note": "Не плутати з омографом «копни́й» (наголос на другому складі: пов'язаний з копою як мірою снопів або сіна).",
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
      "short_label": "пов'язаний з копою (снопів, сіна)",
      "gloss": "relating to a shock of sheaves (kopa) or hay mound",
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
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛА́НЕЦЬ, нця, ч., розм. 1. Одягнена в лахміття людина; старець. Забравши деяких Троянців, Осмалених, як гиря, ланців, П’ятами з Трої накивав [Еней] (Котл., І, 1952, 65); — Я гоноровий шляхтич.., у мене є голка, щоб не ходить обірванцем, а ти гольтіпака, ланець, безштанько (Стор., І, 1957, 132); // Надзвичайно бідна людина; бідняк. Дивувалися й завидували Чіпці люди не менше Грицька. \"І як-таки за",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    }
  ],
  "лучити": [
    {
      "lemma": "лучити",
      "url_slug": "лучити",
      "headword": "лу́чити",
      "short_label": "єднати, сполучати",
      "gloss": "to connect, unite, link, combine",
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
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «лучи́ти» (наголос на другому складі: цілитися, влучати в ціль).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛУ́ЧИТИ, чу, чиш, недок. і док., перех. і без додатка, розм. Цілитися в кого-, що-небудь. Лучив корову, а попав ворону (Номис, 1864, № 1784); Почали шари вкидати У ящик, хто куди хотів. Хто там за різку — кидай вправо, Хто проти неї — вліво луч (Мирний, V, 1955, 292); // Те саме, що влуча́ти 1. Уже стискає міцно коло ворог, Кулі чітко лучать в панцир (Еллан, І, 1958, 75); Юнак з того робочого порі",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "лучити",
      "url_slug": "лучити",
      "headword": "лучи́ти",
      "short_label": "цілити, влучати",
      "gloss": "to hit the target, aim, strike a mark",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[luˈtʃɪtɪ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "лучи́ти",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Не плутати з омографом «лу́чити» (наголос на першому складі: сполучати, з'єднувати докупи).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛУ́ЧИТИ, чу, чиш, недок. і док., перех. і без додатка, розм. Цілитися в кого-, що-небудь. Лучив корову, а попав ворону (Номис, 1864, № 1784); Почали шари вкидати У ящик, хто куди хотів. Хто там за різку — кидай вправо, Хто проти неї — вліво луч (Мирний, V, 1955, 292); // Те саме, що влуча́ти 1. Уже стискає міцно коло ворог, Кулі чітко лучать в панцир (Еллан, І, 1958, 75); Юнак з того робочого порі",
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
      "short_label": "опіум (B1)",
      "gloss": "opium, narcotic substance",
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
      "distinction_note": "Не плутати з омографом «опі́й» (наголос на другому складі: застаріле пиятика, запій).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "О́ПІЙ, ю, ч. Висушений молочний сік з недозрілих маківок, який є сильним наркотиком; використовується в медицині як болезаспокійливий і снотворний засіб. — Ви знаєте, се поле — капітал. З цього маку можна би робити прегарний опій (Мак., Вибр., 1954, 316); Ми сиділи в потайному кафе, де можна мати надзвичайну чорну каву, дві-три люльки опію і контрабандне вино \"Кров землі\" (Ю. Янов., II, 1958, 77);",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "опій",
      "url_slug": "опій",
      "headword": "опі́й",
      "short_label": "пиятика, запій (заст.)",
      "gloss": "binge drinking, drunken stupor, debauch (archaic)",
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
        "ipa": "[ɔˈpij]",
        "source": "VESUM"
      },
      "stress": {
        "form": "опі́й",
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
      "distinction_note": "Не плутати з омографом «о́пій» (наголос на першому складі: опіум, наркотична речовина).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "О́ПІЙ, ю, ч. Висушений молочний сік з недозрілих маківок, який є сильним наркотиком; використовується в медицині як болезаспокійливий і снотворний засіб. — Ви знаєте, се поле — капітал. З цього маку можна би робити прегарний опій (Мак., Вибр., 1954, 316); Ми сиділи в потайному кафе, де можна мати надзвичайну чорну каву, дві-три люльки опію і контрабандне вино \"Кров землі\" (Ю. Янов., II, 1958, 77);",
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
      "gloss": "smooth, flowing, fluent, continuous",
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
      "distinction_note": "Не плутати з омографом «плавни́й» (наголос на другому складі: пов'язаний з плавнями — заплавами річок).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ВНИЙ, а, е. Рівний, без різких переходів, нешвидкий (про рухи, звуки, мову і т. ін.). Дужими і плавними помахами рук Олеся впевнено розрізала воду (Донч., VI, 1957, 74); Читати [лекцію] слід плавною, добірною і дохідливою мовою (Ковінька, Чому я не сокіл.., 1961, 49); Плавний танець; Плавне гальмування; // Який поступово, без різких змін переходить з одного стану в інший. Процес становлення но",
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
      "short_label": "стосовний до плавнів (річкових заплав)",
      "gloss": "relating to river floodplains, marshlands, reed-beds (plavni)",
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
      "distinction_note": "Не плутати з омографом «пла́вний» (наголос на першому складі: рівномірний, плавний рух).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ВНИЙ, а, е. Рівний, без різких переходів, нешвидкий (про рухи, звуки, мову і т. ін.). Дужими і плавними помахами рук Олеся впевнено розрізала воду (Донч., VI, 1957, 74); Читати [лекцію] слід плавною, добірною і дохідливою мовою (Ковінька, Чому я не сокіл.., 1961, 49); Плавний танець; Плавне гальмування; // Який поступово, без різких змін переходить з одного стану в інший. Процес становлення но",
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
      "distinction_note": "Не плутати з омографом «плати́на» (наголос на другому складі: діалектна назва греблі чи гатки).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ТИНА, и, ж. Хімічний елемент сірувато-білого кольору, благородний метал, який відзначається великою ковкістю й тягучістю і використовується для виготовлення коштовних виробів, лабораторного хімічного посуду тощо. У природі платина подібно до золота зустрічається в розсипах у вигляді крупинок (Заг. хімія, 1955, 619). ПЛАТИ́НА, и, ж., діал. Хустка. У хвіртку входить старий диякон з речами, належ",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "платина",
      "url_slug": "платина",
      "headword": "плати́на",
      "short_label": "гребля, гатка (діал.)",
      "gloss": "dam, dike, weir (dialectal / archaic)",
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
      "distinction_note": "Не плутати з омографом «пла́тина» (наголос на першому складі: благородний метал платина).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ТИНА, и, ж. Хімічний елемент сірувато-білого кольору, благородний метал, який відзначається великою ковкістю й тягучістю і використовується для виготовлення коштовних виробів, лабораторного хімічного посуду тощо. У природі платина подібно до золота зустрічається в розсипах у вигляді крупинок (Заг. хімія, 1955, 619). ПЛАТИ́НА, и, ж., діал. Хустка. У хвіртку входить старий диякон з речами, належ",
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
      "gloss": "household chores, tidying, livestock tending (from поратися)",
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
      "distinction_note": "Не плутати з омографом «пора́ння» (наголос на другому складі: дія за значенням «поранити», влучне ураження).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́РАННЯ, я, с. Дія за знач. по́рати і по́ратися. В хаті і надворі.. Скрізь порання: печуть, варять, Вимітають, миють… (Шевч., I, 1963, 316); Коли пішли з дому пан і панич, почалося щоденне порання (Мирний, III, 1954, 155); Весна означала тут.. роботу на грядках, від якої ввечері не можна було випростати спину, виснажливе порання в кухні біля обідів для сапальників (Вільде, Сестри.., 1958, 11); Пі",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "lemma": "порання",
      "url_slug": "порання",
      "headword": "пора́ння",
      "short_label": "поранення, ураження (рідко)",
      "gloss": "wounding, inflicting a injury, striking a target",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[pɔˈrɑnʲːɐ]",
        "source": "VESUM"
      },
      "stress": {
        "form": "пора́ння",
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
      "distinction_note": "Не плутати з омографом «по́рання» (наголос на першому складі: щоденна хатня праця біля печі чи худоби).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́РАННЯ, я, с. Дія за знач. по́рати і по́ратися. В хаті і надворі.. Скрізь порання: печуть, варять, Вимітають, миють… (Шевч., I, 1963, 316); Коли пішли з дому пан і панич, почалося щоденне порання (Мирний, III, 1954, 155); Весна означала тут.. роботу на грядках, від якої ввечері не можна було випростати спину, виснажливе порання в кухні біля обідів для сапальників (Вільде, Сестри.., 1958, 11); Пі",
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
      "headword": "по́хідний",
      "short_label": "табірний, експедиційний (B1)",
      "gloss": "marching, camp, field, expeditionary (relating to a march/campaign)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": false,
        "russian_shadow": false,
        "vesum_attested": true
      },
      "pronunciation": {
        "ipa": "[ˈpɔx⁽ʲ⁾idnɪj]",
        "source": "VESUM"
      },
      "stress": {
        "form": "по́хідний",
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «похі́дний» (наголос на другому складі: утворений від іншого, дериват, похідна функція).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОХІ́ДНИЙ, а, е. 1. Стос. до походу (у 1, 3 знач.); який буває, виробляється в поході. Школа червоних командирів проходила повз штаб з піснями, в повному похідному порядку (Довж., І, 1958, 212); Своїх хлопців.. Яресько не особливо переобтяжував маршировками на толоці, більше дбав про те, щоб стріляли добре та похідних пісень співали краще за інших (Гончар, II, 1959, 243); Мандрівка на лижах зміцню",
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
      "headword": "похі́дний",
      "short_label": "утворений, деривативний (B1)",
      "gloss": "derived, secondary, derivative (e.g. похідне слово, похідна величина)",
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
        "source": "СУМ-20"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «по́хідний» (наголос на першому складі: похідне спорядження, військовий похід).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПОХІ́ДНИЙ, а, е. 1. Стос. до походу (у 1, 3 знач.); який буває, виробляється в поході. Школа червоних командирів проходила повз штаб з піснями, в повному похідному порядку (Довж., І, 1958, 212); Своїх хлопців.. Яресько не особливо переобтяжував маршировками на толоці, більше дбав про те, щоб стріляли добре та похідних пісень співали краще за інших (Гончар, II, 1959, 243); Мандрівка на лижах зміцню",
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
      "short_label": "керівництво, лідерство (B1)",
      "gloss": "leadership, guidance, steering committee, direction",
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
      "distinction_note": "Не плутати з омографом «прові́д» (наголос на другому складі: електричний кабель, дріт або прове́дення).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́ВІД, воду, ч. 1. Те саме, що су́провід. Петрусь під проводом баби Василихи одного гарного осіннього дня вирушив здобувати світ (Фр., IV, 1950, 31); Двері вагона відчинилися, і під проводом вартового двоє цивільних внесли велике цебро (Досв., Вибр., 1959, 168); // рідко. Те саме, що акомпанеме́нт 1. Я берусь положити їх [вірші] на голос із проводом двох балабайок (Сам., II, 1958, 307); // За ре",
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
      "short_label": "електричний кабель, дріт (A2)",
      "gloss": "wire, electrical wire, cable, conducting conduit",
      "pos": "noun",
      "cefr": "A2",
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
      "distinction_note": "Не плутати з омографом «про́від» (наголос на першому складі: організаційне керівництво чи лідерство).",
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПРО́ВІД, воду, ч. 1. Те саме, що су́провід. Петрусь під проводом баби Василихи одного гарного осіннього дня вирушив здобувати світ (Фр., IV, 1950, 31); Двері вагона відчинилися, і під проводом вартового двоє цивільних внесли велике цебро (Досв., Вибр., 1959, 168); // рідко. Те саме, що акомпанеме́нт 1. Я берусь положити їх [вірші] на голос із проводом двох балабайок (Сам., II, 1958, 307); // За ре",
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
        "source": "ВТС / СУМ-11"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Не плутати з омографом «розді́льний» (наголос на другому складі: роздільний санвузол, роздільне харчування).",
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
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "СА́ПАТИ, аю, аєш, недок. 1. Видавати носом свистячі звуки, важко дихаючи. Борис ішов звільна,.. сапаючи (Фр., III, 1950, 86); Хома сердито сапав (Коцюб., II, 1955, 85); Було чути лише, як шелестить на деревах листя та важко сапають коні (Тют., Вир, 1964, 338). 2. чим і без додатка, перен. Утворювати свистячі звуки, випускаючи газ, пару і т. ін. (про механізми, машини). Він [паровий млин] то дихав",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
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
