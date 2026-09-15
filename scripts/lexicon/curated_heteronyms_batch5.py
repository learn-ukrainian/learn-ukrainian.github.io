"""Batch heteronyms expansion dataset for #8039 batch 5 (epic #4387).

Decolonized dictionary evidence: modern Ukrainian standard (СУМ-20 / ВТС),
authentic pre-Soviet witness (Грінченко 1907 under Tsarist imperial bans),
and Soviet colonization context (СУМ-11 1970–1980) attached for transparency.
Expands curated heteronyms SSOT from 136 to 168 lemmas.
"""

from __future__ import annotations

from typing import Any

CURATED_HETERONYMS_BATCH_5: dict[str, list[dict[str, Any]]] = {
  "копний": [
    {
      "headword": "ко́пний",
      "short_label": "громадський, судновий (іст.)",
      "gloss": "communal, related to Ukrainian traditional community court (kopny sud)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "копни́й",
      "short_label": "пов'язаний з копою (снопів, сіна)",
      "gloss": "relating to a shock of sheaves (kopa) or hay mound",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ла́нець",
      "short_label": "голодранець, лайливе (розм.)",
      "gloss": "ragamuffin, scamp, tramp (colloquial)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "лане́ць",
      "short_label": "ланцюг (заст.)",
      "gloss": "chain, small chain (archaic)",
      "pos": "noun",
      "cefr": None,
      "heritage_status": {
        "classification": "authentic-archaism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "soviet_colonization_context": None
    }
  ],
  "лучити": [
    {
      "headword": "лу́чити",
      "short_label": "цілити, влучати (розм.)",
      "gloss": "to aim, hit the mark, strike a target (e.g. Лучив корову, а попав ворону)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЛУ́ЧИТИ, чу, чиш, недок. і док., перех. і без додатка, розм. Цілитися в кого-, що-небудь. Лучив корову, а попав ворону (Номис, 1864, № 1784); // Те саме, що влуча́ти 1.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "headword": "лучи́ти",
      "short_label": "єднати, сполучати (діал.)",
      "gloss": "to unite, join, link, connect together (cf. сполучати, злучити)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "лю́дний",
      "short_label": "багатолюдний (A2)",
      "gloss": "crowded, populous, full of people",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "людни́й",
      "short_label": "привітний, людяний (рідко)",
      "gloss": "affable, humane, hospitable, sociable",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "о́пій",
      "short_label": "опіум, болезаспокійливий сік (B1)",
      "gloss": "opium, narcotic analgesic substance dried from poppy heads",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "О́ПІЙ, ю, ч. Висушений молочний сік з недозрілих маківок, який є сильним наркотиком; використовується в медицині як болезаспокійливий і снотворний засіб.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "headword": "опі́й",
      "short_label": "опой, запалення копит у коней (вет.)",
      "gloss": "equine hoof inflammation, founder / excessive watering sickness in horses (vet., cf. Грінченко: хвороба у тварин від гарячого пойла)",
      "pos": "noun",
      "cefr": None,
      "heritage_status": {
        "classification": "authentic-historism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "пла́вний",
      "short_label": "гладкий, рівномірний (B1)",
      "gloss": "smooth, flowing, fluent, continuous, without abrupt jerks",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "плавни́й",
      "short_label": "плавучий; стосовний до плавнів (B2)",
      "gloss": "floating, drifting, buoyant (e.g. плавна сітка, cf. Грінченко: пловучій); relating to river floodplains, marshlands (plavni)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "пла́тина",
      "short_label": "хімічний елемент Pt (B1)",
      "gloss": "platinum (noble precious metal)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПЛА́ТИНА, и, ж. Хімічний елемент сірувато-білого кольору, благородний метал. ПЛАТИ́НА, и, ж., діал. Хустка. У хвіртку входить старий диякон з речами, належними до хрещення, зав’язаними в платину (Васильч., III, 1960, 24).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "headword": "плати́на",
      "short_label": "хустка, платок (діал.)",
      "gloss": "kerchief, headscarf, traditional cloth (dialectal / folk, cf. Грінченко: платок; плат, полотно)",
      "pos": "noun",
      "cefr": None,
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "пла́тний",
      "short_label": "який оплачується (A2)",
      "gloss": "paid, fee-paying, commercial, salaried",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "платни́й",
      "short_label": "платіжний, здатний платити (рідко)",
      "gloss": "payable, solvent, related to payment capabilities",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "плодо́вий",
      "short_label": "фруктовий, садовий (B1)",
      "gloss": "fruit-bearing, pomological (e.g. плодові дерева, плодовий сад)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "плодови́й",
      "short_label": "родючий, плодючий (рідко)",
      "gloss": "fertile, fruitful, fecund",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "поворо́тний",
      "short_label": "обертовий, вирішальний (B1)",
      "gloss": "turning, pivotal, revolving, rotating (e.g. поворотний пункт)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "поворотни́й",
      "short_label": "зворотний, який повертається (рідко)",
      "gloss": "returnable, reversible, returning",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "поки́дати",
      "short_label": "пошпурити все (док.)",
      "gloss": "to throw all or multiple items, hurl (perfective)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "покида́ти",
      "short_label": "залишати, кидати (недок., A2)",
      "gloss": "to abandon, leave behind, forsake, desert (imperfective)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "по́кій",
      "short_label": "спокій, тиша (B1)",
      "gloss": "peace, tranquility, rest, quietness, spiritual composure",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "покі́й",
      "short_label": "кімната, покої (A2)",
      "gloss": "room, chamber, apartment (usually in plural покої)",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "поми́лувати",
      "short_label": "приголубити, попестити (док., B1)",
      "gloss": "to caress, cuddle, pet, pamper (perfective)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "помилува́ти",
      "short_label": "пробачити провину (док., B1)",
      "gloss": "to pardon, grant clemency, have mercy, forgive (perfective)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "по́між",
      "short_label": "поряд, підряд (діал.)",
      "gloss": "side by side, consecutively, in a row (dialectal / archaic)",
      "pos": "adverb",
      "cefr": None,
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "помі́ж",
      "short_label": "між, серед (прийм., A2)",
      "gloss": "between, among, amidst (preposition)",
      "pos": "preposition",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "поно́сити",
      "short_label": "ганьбити, лаяти (недок., B2)",
      "gloss": "to revile, slander, disparage, abuse verbally (imperfective)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "поноси́ти",
      "short_label": "носити деякий час (док., A2)",
      "gloss": "to carry or wear for a while (perfective)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "по́рання",
      "short_label": "господарювання, догляд біля хати (B1)",
      "gloss": "household chores, tidying, tending near hearth or livestock (from поратися)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ПО́РАННЯ, я, с. Дія за знач. по́рати і по́ратися. В хаті і надворі.. Скрізь порання: печуть, варять, Вимітають, миють… (Шевч., I, 1963, 316).",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в радянський окупаційний період (СУМ-11, 1970–1980). Подано для історичного аналізу радянського редакторського втручання та ідеологічного зміщення."
      }
    },
    {
      "headword": "пора́ння",
      "short_label": "ранок, рання пора (діал.)",
      "gloss": "early morning, dawn, early time of day (cf. поранок; ВТС та СУМ-20 ст. 86498)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "похі́дний",
      "short_label": "табірний, експедиційний (B1)",
      "gloss": "marching, camp, field, expeditionary (relating to a march/campaign, e.g. похідний порядок, похідна кухня)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "похідни́й",
      "short_label": "утворений, деривативний (B1)",
      "gloss": "derived, secondary, derivative (e.g. похідне слово, похідна величина, похідна функція в математиці)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "при́кладний",
      "short_label": "зразковий, доладний (рідко)",
      "gloss": "exemplary, model, neatly fitting",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "прикладни́й",
      "short_label": "ужитковий, практичний (B1)",
      "gloss": "applied, practical (e.g. прикладна наука, прикладне мистецтво)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "при́лавок",
      "short_label": "лава в традиційній хаті (етногр.)",
      "gloss": "traditional built-in wall bench in a Ukrainian village house",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-ethnographism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "прила́вок",
      "short_label": "торговельний стіл у крамниці (A2)",
      "gloss": "shop counter, sales stall, service desk",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "при́мітка",
      "short_label": "прикмета, знак (діал.)",
      "gloss": "sign, omen, distinctive trait (dialectal)",
      "pos": "noun",
      "cefr": None,
      "heritage_status": {
        "classification": "authentic-dialectism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "примі́тка",
      "short_label": "коментар, виноска в тексті (A2)",
      "gloss": "note, footnote, explanatory annotation, remark",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "пробі́гати",
      "short_label": "побігати певний час (док., B1)",
      "gloss": "to run around for a certain time (perfective)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "пробіга́ти",
      "short_label": "бігти повз, мчати (недок., A2)",
      "gloss": "to run past, traverse by running, flit across (imperfective)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "про́бування",
      "short_label": "тестування, куштування (B1)",
      "gloss": "trying, tasting, testing, sampling (from пробувати)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "пробува́ння",
      "short_label": "перебування, проживання (B2)",
      "gloss": "sojourn, stay, residence, dwelling (from пробувати/перебувати)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "прови́діння",
      "short_label": "передбачення (B1)",
      "gloss": "foresight, clairvoyance, premonition, anticipation",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "провиді́ння",
      "short_label": "Боже Провидіння (B2)",
      "gloss": "Providence, divine governance, supreme destiny",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "про́від",
      "short_label": "керівництво; електричний дріт, кабель (B1)",
      "gloss": "1. leadership, guidance, steering committee, direction; 2. electrical wire, cable, conductor conduit",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "прові́д",
      "short_label": "провадження, здійснення (B2)",
      "gloss": "action of conducting, carrying out, conveyance, leading, guidance action (from проводити; gen. прово́ду)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "проки́датися",
      "short_label": "кидатися певний час (рідко)",
      "gloss": "to toss, fling, or throw repeatedly for a while (rare)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "прокида́тися",
      "short_label": "будитися, переривати сон (A1)",
      "gloss": "to wake up, awaken, arouse from sleep",
      "pos": "verb",
      "cefr": "A1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "про́клятий",
      "short_label": "підданий прокльону (дієприкм., B1)",
      "gloss": "cursed, damned (passive past participle of проклясти)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "прокля́тий",
      "short_label": "клятий, ненависний (B1)",
      "gloss": "damned, hateful, detestable, wretched, confounded",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "про́лог",
      "short_label": "житійний збірник (іст., церк.)",
      "gloss": "synaxarion, menologium, collection of short saints' lives",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "authentic-historism",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
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
      "headword": "проло́г",
      "short_label": "вступ до твору (B1)",
      "gloss": "prologue, preface, literary introduction, prelude",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ра́порт",
      "short_label": "офіційне повідомлення, звіт (B1)",
      "gloss": "official report, military dispatch, report to superiors",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "рапо́рт",
      "short_label": "повторюваний елемент візерунка (B2)",
      "gloss": "pattern repeat, recurring unit in textile or ornamental design",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "рефле́кторний",
      "short_label": "відбивальний, пов'язаний з рефлектором (B2)",
      "gloss": "reflector-related, specular, reflective (e.g. рефлекторна лампа)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "рефлекто́рний",
      "short_label": "мимовільний, нервовий рефлекс (B1)",
      "gloss": "reflexive, involuntary, neurological reflex-based (e.g. рефлекторний рух)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "розві́дник",
      "short_label": "військовий розвідник, скаут (A2)",
      "gloss": "reconnaissance scout, intelligence agent, scout plane/vessel",
      "pos": "noun",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "розвідни́к",
      "short_label": "фахівець розведення зубців пилки (спец.)",
      "gloss": "saw set specialist, saw setter",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "розді́льний",
      "short_label": "поетапний, відокремлений (A2)",
      "gloss": "separate, distinct, fractional, step-by-step (e.g. роздільний збір сміття)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "роздільни́й",
      "short_label": "розмежувальний (роздільна здатність, роздільний знак)",
      "gloss": "dividing, resolving, separating (e.g. роздільна здатність - resolution)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "са́пати",
      "short_label": "сопіти, важко дихати (недок., B1)",
      "gloss": "to breathe heavily, pant, snort, wheeze (from сап/сопіти)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "сапа́ти",
      "short_label": "полоти бур'ян сапою (недок., A2)",
      "gloss": "to hoe, weed with a hoe, loosen soil with a hoe (from сапа)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
}
