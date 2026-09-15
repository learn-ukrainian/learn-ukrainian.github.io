"""Curated heteronym dataset (Batch 6) for Word Atlas (#8039, #4387).

This module defines 32 curated heteronym lemmas (64 distinct variants)
expanding the curated heteronym SSOT from 168 to 200 lemmas.

Decolonization & Lexicographical Invariants:
1. Modern standard baseline: Academic СУМ-20 / ВТС / ULIF authorities.
2. Authentic pre-Soviet witness: Грінченко (1907–1909), compiled/published
   under Tsarist Russian imperial bans (Valuev Circular 1863, Ems Ukaz 1876).
3. Soviet colonization context: СУМ-11 (1970–1980) documented transparently
   under `soviet_colonization_context` with `sovietization_risk` and historical notes
   without erasing lexical history.
4. Clean morphology and phonology: Every variant is verified in VESUM (clean view).
"""

from typing import Any

CURATED_HETERONYMS_BATCH_6: dict[str, list[dict[str, Any]]] = {
  "гукнути": [
    {
      "headword": "гу́кнути",
      "short_label": "вигукнути, відгукнутися (розм.)",
      "gloss": "to shout, echo, make an echoing sound, call out casually",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "distinction_note": "Не плутати з омографом «гукну́ти» (наголос на кінцевому -ну́ти: голосно покликати когось, закликати).",
      "meaning": {
        "definitions": [
          "Однократне до гу́кати; вигукнути, лунко зазвучати."
        ],
        "source": "СУМ-20 (20522)"
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
      "headword": "гукну́ти",
      "short_label": "покликати, закликати когось",
      "gloss": "to call, shout out to summon someone, invite aloud",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "distinction_note": "Не плутати з омографом «гу́кнути» (наголос на першому складі: однокр. до гу́кати, лунко вигукнути).",
      "meaning": {
        "definitions": [
          "Однократне до гука́ти; покликати, закликати когось."
        ],
        "source": "СУМ-20 (20523)"
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
      "headword": "ба́лувати",
      "short_label": "пестити, розпещувати, потурати примхам",
      "gloss": "to pamper, spoil, indulge someone's whims (e.g. балувати дітей)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "балува́ти",
      "short_label": "гуляти на балах, бенкетувати (заст.)",
      "gloss": "to revel, feast, attend balls (Хто змолоду балує, той під старість старцює)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ди́хання",
      "short_label": "дихання, газообмін; подих (стандартне літер.)",
      "gloss": "respiration, breathing process, gas exchange; breath, breeze (standard literary form)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "диха́ння",
      "short_label": "те саме, що ди́хання (діал., заст.)",
      "gloss": "dialectal accentual variant of ди́хання (same meaning: respiration, breath; attested dialectally and in Grinchenko 1907)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ко́втнути",
      "short_label": "ударити кулаком (діал.)",
      "gloss": "to punch, strike with a fist (dialectal single blow, related to ко́втати)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ковтну́ти",
      "short_label": "проковтнути рідину або їжу",
      "gloss": "to swallow, take a gulp, drink a mouthful",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "підсу́мковий",
      "short_label": "стосовний до сумки для набоїв (військ., іст.)",
      "gloss": "related to an ammunition pouch or cartridge box (from підсу́мок - cartridge box, ammo pouch)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "підсумко́вий",
      "short_label": "який підбиває підсумки; завершальний",
      "gloss": "summary, final, conclusive, resulting (from пі́дсумок - sum, total, outcome, summary)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "родо́вий",
      "short_label": "родовий лад / родовий відмінок (лінгв.)",
      "gloss": "clan-related, ancestral; genitive case (grammar: родовий відмінок)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "distinction_note": "У значенні «стосовний до роду, родовий відмінок» нормативна практика закріпила наголос «родо́вий», хоча академічний СУМ-20 (стаття 100032) фіксує подвійний наголос «РОДО́ВИ́Й 1». Окрема стаття СУМ-20 (100033) фіксує «родови́й 2» (рідко) для пологів.",
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
      "headword": "родови́й",
      "short_label": "стосовний до пологів (мед., акуш., рідко)",
      "gloss": "natal, obstetric, relating to labor and childbirth (родові перейми, пологові)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "distinction_note": "Не плутати з «родо́вий» (наголос на другому складі: родовий відмінок, родовий лад). В українській мові для пологів природнішим і рекомендованим є термін «полого́вий» (пологовий будинок, пологова діяльність).",
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
      "headword": "свя́чений",
      "short_label": "освячений (дієприкм.)",
      "gloss": "blessed, consecrated, sanctified (passive participle of святити)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "свяче́ний",
      "short_label": "свячена вода / свячене (прикм./імен.)",
      "gloss": "holy, ritual, consecrated (свячена вода - holy water; свячене - blessed Easter food)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "сі́яння",
      "short_label": "розсівання насіння (агротехн.)",
      "gloss": "sowing, seeding, spreading grain in field",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "сія́ння",
      "short_label": "сяйво, випромінювання світла (поет.)",
      "gloss": "radiance, shining, brilliant glow (= ся́ння, from сіяти/сяяти)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-poetic",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "сі́яти",
      "short_label": "кидати зерно в ґрунт; розсипати",
      "gloss": "to sow seeds, scatter grain in ground; drizzle (rain)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "сія́ти",
      "short_label": "випромінювати світло, сяяти (поет.)",
      "gloss": "to shine, radiate light, gleam, sparkle (= ся́яти, сяти; attested in Grinchenko 1907)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "authentic-poetic",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ска́лити",
      "short_label": "показувати зуби, вишкірятися",
      "gloss": "to bare one's teeth, grin maliciously, sneer (скалити зуби)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "скали́ти",
      "short_label": "занозити скалкою (діал.)",
      "gloss": "to get a wood splinter in skin (attested in Grinchenko 1907: 'Ноги собі скалить')",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "слі́дувати",
      "short_label": "іти слідом, прямувати",
      "gloss": "to follow behind, accompany, move along a route",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "слідува́ти",
      "short_label": "слідкувати за кимось, вистежувати (діал.)",
      "gloss": "to track down, keep watch, follow tracks closely (attested in Grinchenko 1907)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "соля́ний",
      "short_label": "соляна кислота (хім.)",
      "gloss": "hydrochloric (chemistry: соляна кислота - hydrochloric acid)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "соляни́й",
      "short_label": "стосовний до солі, мінералу (соляні копальні)",
      "gloss": "saline, salt-bearing, containing salt (e.g. соляний розчин, соляні промисли)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "спі́рний",
      "short_label": "дискусійний, сумнівний, предмет спору",
      "gloss": "disputed, debatable, contentious, controversial (causing argument/dispute)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "distinction_note": "Не плутати з народним автентичним «спірни́й» (наголос на кінці: спорий, швидкий, продуктивний у роботі).",
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
      "headword": "спірни́й",
      "short_label": "спорий, швидкий, плідний у праці (фольк.)",
      "gloss": "swift, efficient, productive, fast-moving in work (e.g. спірний кінь, спірна праця; attested in Grinchenko 1907)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-folklorism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "distinction_note": "Не плутати з абстрактним юридичним «спі́рний» (наголос на корені: спірне питання).",
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
      "headword": "сполу́чний",
      "short_label": "з'єднувальний; сполучна тканина (анат.)",
      "gloss": "connecting, connective, binding; linking (e.g. сполучна тканина - connective tissue, сполучний звук)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "сполучни́й",
      "short_label": "сумісний, суміщуваний з чим-небудь",
      "gloss": "combinable, compatible, joinable (able to be connected or reconciled with something)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ста́рший",
      "short_label": "віком більший; головніший за рангом",
      "gloss": "older, elder; senior in rank or status",
      "pos": "adjective",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "старши́й",
      "short_label": "начальник, керівник, ватажок (імен.)",
      "gloss": "chief, elder, leader, commander, headman (substantive noun; e.g. козацький старший; Grinchenko 1907)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "сто́янка",
      "short_label": "відстояне молоко, вершки (розм.)",
      "gloss": "settled standing milk, layer of cream (attested in Grinchenko 1907)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "стоя́нка",
      "short_label": "місце зупинки, парковка; табір",
      "gloss": "parking lot, halting place, camp of ancient humans (archaeology: первісна стоянка)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "су́дний",
      "short_label": "Судний день; судочинство (заст.)",
      "gloss": "Judgement Day, Doomsday (реліг. Судний день); judicial, court-related",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "судни́й",
      "short_label": "придатний, годний, міцний (діал.)",
      "gloss": "suitable, fit, sturdy, serviceable (attested in Grinchenko 1907: 'полотно судне')",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "тве́рдити",
      "short_label": "стверджувати, запевняти в чомусь",
      "gloss": "to assert, maintain, state confidently, assure (впевнено висловлювати)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "тверди́ти",
      "short_label": "повторювати одне й те саме, завчати",
      "gloss": "to repeat repeatedly, reiterate; recite or rehearse to memorize (завчати, зубрити)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "типо́вий",
      "short_label": "характерний, показний, зразковий",
      "gloss": "typical, characteristic, representative of a group or kind",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "distinction_note": "Не плутати з технічним терміном «типови́й» (наголос на кінці: спроєктований за зразком, типовий проєкт).",
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
      "headword": "типови́й",
      "short_label": "стандартизований за зразком (техн.)",
      "gloss": "standardized, model-based, type-designed (e.g. типовий проєкт будинку)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "distinction_note": "Не плутати з якісним значенням «типо́вий» (характерний приклад, типовий випадок).",
      "meaning": {
        "definitions": [
          "(техн., спец.) Виконаний за певним зразком, стандартом; серійний (типовий будинок)."
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
      "headword": "у́ступ",
      "short_label": "частина тексту, уривок, абзац (книжн.)",
      "gloss": "passage of text, excerpt, paragraph (in a book or article)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "усту́п",
      "short_label": "виступ, тераса, східець у скелі чи мурі",
      "gloss": "ledge, step, terrace, rock shelf; bench in mining",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "хлі́бець",
      "short_label": "маленька хлібина, буханець",
      "gloss": "small loaf of bread, bun, roll (e.g. випікати хлібці)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "хлібе́ць",
      "short_label": "хлібчик, посіви зернових (пестл., фольк.)",
      "gloss": "dear bread, young standing grain crops in fields (diminutive/poetic, attested in folk songs: 'Хіба зелениться хлібець серед поля')",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-folklorism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "хре́щений",
      "short_label": "охрещений (дієприкм.)",
      "gloss": "baptized, christened (passive past participle of хрестити; e.g. дитина, ще не хрещена)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "хреще́ний",
      "short_label": "хрещений батько / мати; християнин",
      "gloss": "godparent (хрещений батько, хрещена мати), christened Christian person (хрещений люд)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ці́лик",
      "short_label": "прицільне пристосування на зброї",
      "gloss": "rear sight, sighting notch on a firearm or artillery barrel",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ціли́к",
      "short_label": "цілина; непорушений пласт породи",
      "gloss": "virgin land, unbroken unplowed steppe; pillar of unmined rock (attested in Grinchenko 1907: 'Цілик = цілина')",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ці́лити",
      "short_label": "наводити зброю в ціль, мітити",
      "gloss": "to aim at a target, take aim, point a weapon (Цілив у ворону...)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ціли́ти",
      "short_label": "зцілювати, лікувати (заст., нар.-поет.)",
      "gloss": "to heal, cure, restore health (attested in Grinchenko 1907: 'Цілити - исцелять')",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "укра́їна",
      "short_label": "прикордонна земля, порубіжжя (іст., заст.)",
      "gloss": "frontier region, border territory (historical appellative in medieval chronicles)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "украї́на",
      "short_label": "країна, рідний край (іст., фольк.)",
      "gloss": "homeland, native land, country of the people (in Ukrainian folk epics and chronicles)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "authentic-folklorism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "о́пал",
      "short_label": "опалення, паливо (розм., рідко)",
      "gloss": "heating, fuel for fire (from палити / опалювати)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "опа́л",
      "short_label": "коштовний камінь кремнезему (мінер.)",
      "gloss": "opal gemstone (hydrated silica mineral with iridescent play of colors)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ро́зказ",
      "short_label": "наказ, веління (заст., фольк.)",
      "gloss": "order, command, mandate, decree (attested in Grinchenko 1907: 'Розказ = наказ')",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "розка́з",
      "short_label": "розповідь, оповідання (розм.)",
      "gloss": "tale, narrative, story, telling (colloquial verbal noun from розказувати)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ві́дклад",
      "short_label": "геологічний осад, нашарування порід",
      "gloss": "geological deposit, sediment, stratum (formation of settled rock or minerals)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відкла́д",
      "short_label": "відстрочка, перенесення часу (заст.)",
      "gloss": "postponement, adjournment, delay (attested in Grinchenko 1907: 'Одклад не йде в лад')",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "authentic-historism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "за́мір",
      "short_label": "намір, задум, план",
      "gloss": "intention, aim, plan, purpose (e.g. здійснити свій замір)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
        "historical_note": "Збережено в Словнику Бориса Грінченка (1907–1909), виданому всупереч репресивним заборонам Російської імперії."
      }
    },
    {
      "headword": "замі́р",
      "short_label": "вимірювання приладами (техн.)",
      "gloss": "measurement, gauging, survey, sounding with measuring tools",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ба́йковий",
      "short_label": "пошитий з байки, м'якої тканини (текст.)",
      "gloss": "flannelette, baize (soft brushed cotton fabric; e.g. байкова ковдра, байкова сорочка)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "байко́вий",
      "short_label": "стосовний до байки як літературного жанру (літ.)",
      "gloss": "fable-related, fabulist (relating to literary fable genre; e.g. байковий сюжет)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "бри́кнути",
      "short_label": "упасти, перекинутися (розм.)",
      "gloss": "to tumble down, fall over, flop down (colloquial)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "брикну́ти",
      "short_label": "брикнути ногою чи копитом, хвицнути",
      "gloss": "to buck, kick out with a hoof or leg once (e.g. кінь брикнув)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "жа́лоба",
      "short_label": "скарга, невдоволення (заст., прост.)",
      "gloss": "complaint, grievance, lawsuit (archaic/vernacular, attested in Grinchenko 1907: 'ЖАлоба = скарга')",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-archaism",
        "warning_severity": "treasured",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "жало́ба",
      "short_label": "траур, сум за померлим, чорний одяг",
      "gloss": "mourning, grief, bereavement, funeral black attire (attested in Grinchenko 1907: 'ЖалОба = траур')",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
  ]
}
