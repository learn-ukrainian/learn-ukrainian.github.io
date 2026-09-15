"""Curated heteronym dataset (Batch 7) for Word Atlas (#8039, #4387).

This module defines 32 curated heteronym lemmas (64 distinct variants)
expanding the curated heteronym SSOT from 200 to 232 lemmas.

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

CURATED_HETERONYMS_BATCH_7: dict[str, list[dict[str, Any]]] = {
  "банник": [
    {
      "headword": "ба́нник",
      "short_label": "артилерійський банник / щітка для гармати",
      "gloss": "artillery bore brush, swab, cannon cleaning sponge on rammer",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "банни́к",
      "short_label": "банщик, працівник або відвідувач лазні (діал.)",
      "gloss": "bathhouse attendant, bather, bath keeper (dial.)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "бере́жений",
      "short_label": "збережений, якого берегли / пасивний дієприкметник",
      "gloss": "guarded, kept safe, preserved, protected (participle of берегти)",
      "pos": "participle",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "береже́ний",
      "short_label": "обачний, обережний; «береженого й Бог береже»",
      "gloss": "cautious, wary, careful, prudent; (as noun) a cautious person",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "бу́ритися",
      "short_label": "хвилюватися, бунтувати / (безос.) збиратися на бурю (діал.)",
      "gloss": "to rage, become agitated, rebel, ferment; (impers.) to brew a storm (dial.)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
      },
      "pronunciation": {
        "ipa": "[ˈburɪtɪsʲɐ]"
      },
      "stress": {
        "form": "бу́ритися",
        "source": "Грінченко (1907) / ВТС",
        "url": "https://slovnyk.me/dict/vts/буритися"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Означає «хвилюватися, обурюватися, бунтувати» (Іван Франко: «народ по селах буриться») або безособово «збиратися на бурю» (Борис Грінченко: «хмариться, буриться»). Не плутати з технічним дієсловом «бури́тися» (про свердловину чи шпур: піддаватися бурінню).",
      "meaning": {
        "definitions": [
          "Хвилюватися, обурюватися, бунтувати; безос. збиратися на бурю (діал.)."
        ],
        "source": "Грінченко (1907) / ВТС / СУМ-11"
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
      "headword": "бури́тися",
      "short_label": "буритися (про свердловину, шпур; пас. до бурити)",
      "gloss": "to be drilled, bored (passive of бурити - e.g. a well or borehole)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
      },
      "pronunciation": {
        "ipa": "[bʊˈrɪtɪsʲɐ]"
      },
      "stress": {
        "form": "бури́тися",
        "source": "ВТС / СУМ-11",
        "url": "https://slovnyk.me/dict/vts/буритися"
      },
      "morphology": {
        "pos": "дієслово",
        "paradigm": {
          "kind": "verb",
          "aspect": "недоконаний"
        }
      },
      "distinction_note": "Пасивний стан до технічного дієслова «бури́ти»: висвердлюватися буром (буриться свердловина, буриться шпур). Не плутати з дієсловом «бу́ритися» (хвилюватися або збиратися на бурю).",
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
      "headword": "ва́жниця",
      "short_label": "поважна особа / важлива справа (розм., ірон.)",
      "gloss": "important person, dignitary (ironic); important matter/affair",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "важни́ця",
      "short_label": "підставка для підважування воза (чумацька) / вагарня",
      "gloss": "wagon jack, lever support for greasing wagon wheels (chumak); weighing station",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "валко́вий",
      "short_label": "пов'язаний з валком/циліндром (техн.: валкова косарка)",
      "gloss": "roller-equipped, cylindrical, roll-based (валкова дробарка, валкова косарка)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "валкови́й",
      "short_label": "візник, який іде з валкою (обозом)",
      "gloss": "carter, wagon-train driver (a driver travelling with a wagon train / convoy)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
      },
      "pronunciation": {
        "ipa": "[wɐlkɔˈwɪj]"
      },
      "stress": {
        "form": "валкови́й",
        "source": "ВТС / СУМ-11",
        "url": "https://slovnyk.me/dict/vts/валковий"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Означає візника, який іде з валкою (обозом). Не плутати з технічним прикметником «валко́вий» (механізм із валками/циліндрами).",
      "meaning": {
        "definitions": [
          "Візник, який іде з валкою (обозом)."
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
      "headword": "випра́вний",
      "short_label": "якого можна виправити, піддатний виправленню",
      "gloss": "rectifiable, remediable, correctable, capable of being mended",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "виправни́й",
      "short_label": "виправні роботи, виправна колонія / регуляційний",
      "gloss": "correctional, disciplinary, penal; regulatory (river-training, coastal)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ви́пробуваний",
      "short_label": "перевірений досвідом, загартований, надійний (минулий час)",
      "gloss": "tested, time-proven, reliable, seasoned, veteran (past passive participle)",
      "pos": "participle",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "випро́буваний",
      "short_label": "той, що проходить випробування в даний момент (теперішній час)",
      "gloss": "undergoing testing, currently being trialed/tested (present passive participle)",
      "pos": "participle",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "ви́щати",
      "short_label": "робитися, ставати вищим",
      "gloss": "to grow higher, become taller, rise higher (ставати вищим)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "вища́ти",
      "short_label": "верещати, пронизливо кричати, вищати від болю чи люті",
      "gloss": "to shriek, screech, squeak, scream with high-pitched sound",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відбі́гати",
      "short_label": "закінчити бігати / відбігати ноги (док. вид)",
      "gloss": "to finish running, complete a run; (idiom) to tire out one's legs (perf.)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відбіга́ти",
      "short_label": "бігти геть, віддалятися бігом (недок. вид)",
      "gloss": "to run away, retreat running, rush away (imperf. corresponding to відбігти)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відбі́рний",
      "short_label": "найкращий, добірний, першосортний",
      "gloss": "select, choice, prime quality, top-grade, hand-picked (synonym to добірний)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відбірни́й",
      "short_label": "призначений для відбору (відбірна комісія, турнір)",
      "gloss": "qualifying, screening, sorting, selection-oriented (відбірна комісія, відбірні матчі)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відва́льний",
      "short_label": "пов'язаний з відвалом породи/шлаку (гірн.)",
      "gloss": "spoil-bank, dump-related (відвальний шлак - slag dump material)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відвальни́й",
      "short_label": "призначений для відвалювання (відвальний міст, плуг)",
      "gloss": "moldboard, dumping, earth-moving, soil-clearing (відвальний міст, відвальний плуг)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відли́вний",
      "short_label": "пов'язаний з морським відливом/відпливом (відливні години)",
      "gloss": "ebb-related, tidal outflow, low-tide (відливні години - low tide hours)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відливни́й",
      "short_label": "литий (відливні вироби) / водовідливний (відливний насос)",
      "gloss": "cast, molded (foundry products); drainage, water-pumping (відливний насос)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відру́бний",
      "short_label": "відокремлений, ізольований, самітний (хутір відрубний)",
      "gloss": "isolated, separate, detached, secluded (відрубний хутір - isolated farmstead)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "відрубни́й",
      "short_label": "земельний відруб (іст., селянські реформи)",
      "gloss": "relating to historical peasant land parcels (odrub) segregated from communal tenure",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "вугро́вий",
      "short_label": "пов'язаний з акне / висипанням вугрів на шкірі",
      "gloss": "acne-related, comedonal, pimple-related (вугровий висип - acne rash)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "вугрови́й",
      "short_label": "пов'язаний з рибою вугром (вугровий промисел)",
      "gloss": "eel-related, anguillid (вугровий промисел - eel fishing, eel industry)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "га́ванський",
      "short_label": "портовий, пов'язаний з морською гаванню",
      "gloss": "harbor-related, haven-related, port-related (гаванські споруди - harbor structures)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "гава́нський",
      "short_label": "стосовний до Гавани на Кубі (гава́нська сигара)",
      "gloss": "Havanese, Havana-related (capital of Cuba; e.g. Havana cigar)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "гребі́нник",
      "short_label": "кормова злакова трава (ботаніка: Cynosurus)",
      "gloss": "crested dog's-tail grass (botany: Cynosurus L., family Poaceae)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "гребінни́к",
      "short_label": "ремісник, який виготовляє гребінці",
      "gloss": "comb-maker, artisan craftsman making hair combs",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "дозві́льний",
      "short_label": "вільний від праці, присвячений відпочинку (дозвільний час)",
      "gloss": "leisure-related, unoccupied, idle, spare (дозвільний час - leisure hours)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "дозвільни́й",
      "short_label": "дозвільний документ / дозвільна система (дозвіл на діяльність)",
      "gloss": "permissive, regulatory, licensing, authorization-related (дозвільний документ - permit)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "домо́вий",
      "short_label": "житловий, хатній (домова книга, домові податки)",
      "gloss": "residential, domestic, household-related (домова книга - residence registry book)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
      },
      "pronunciation": {
        "ipa": "[dɔˈmɔwɪj]"
      },
      "stress": {
        "form": "домо́вий",
        "source": "ВТС / СУМ-11",
        "url": "https://slovnyk.me/dict/vts/домовий"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Прикметник до «дім» — пов'язаний із житловим будинком (домова книга, домова рада). Не плутати з іменником «домови́й» (міфологічний хатній дух).",
      "meaning": {
        "definitions": [
          "Стосовний до житлового будинку або домашнього господарства; домашній (домова книга)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДОМО́ВИЙ, а, е. 1. Стос. до дому (у 1-3 знач.). Домова книга. 2. Те саме, що дома́шній 2.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в класичній літературі (І. Франко, Леся Українка, І. Карпенко-Карий) та СУМ-11. У Грінченка (1907–1909) зафіксовано подвійний акцент «домОвИй» всупереч імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    },
    {
      "headword": "домови́й",
      "short_label": "хатній дух, домовик у народній демонології",
      "gloss": "house spirit, domestic goblin, brownie (equivalent to домовик)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
      },
      "pronunciation": {
        "ipa": "[dɔmɔˈwɪj]"
      },
      "stress": {
        "form": "домови́й",
        "source": "ВТС / СУМ-11",
        "url": "https://slovnyk.me/dict/vts/домовий"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Іменник народної демонології: дух оселі (те саме, що домови́к). Не плутати з прикметником «домо́вий» (домова книга).",
      "meaning": {
        "definitions": [
          "Персонаж слов'янської народної міфології; хатній дух, охоронець оселі (домовик)."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ДОМОВИ́Й, во́го, ч. Те саме, що домови́к.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано у творах П. Грабовського та СУМ-11. Традиційний персонаж української народної міфології."
      }
    }
  ],
  "досвідний": [
    {
      "headword": "до́свідний",
      "short_label": "експериментальний, дослідний (досвідне поле, дослід)",
      "gloss": "experimental, empirical, trial (досвідне поле - experimental field station)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "досвідни́й",
      "short_label": "досвідчений, бувалий, який має життєвий досвід (рідко)",
      "gloss": "experienced, seasoned, practiced, wise (synonym to досвідчений)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "жа́бник",
      "short_label": "зневажливе прізвисько плавця на мілководді",
      "gloss": "puddle-wader, shallow-water paddler (pejorative nickname)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "жабни́к",
      "short_label": "трав'яниста рослина (ботаніка: Filago L. / Caltha)",
      "gloss": "marsh marigold or cudweed plant (botany: Filago L. or Caltha palustris)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "жиро́вий",
      "short_label": "картярський термін у народних іграх / масть",
      "gloss": "trump-suit, winning card suit in folk games; (arch.) out of wedlock",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "жирови́й",
      "short_label": "жирова тканина, ліпідний / багатий на жир",
      "gloss": "fatty, lipid, adipose, rich in fats (жирова тканина, жирові кислоти)",
      "pos": "adjective",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "жму́ритися",
      "short_label": "мружити очі, щуритися від сонця чи світла",
      "gloss": "to squint, narrow/half-close one's eyes against glare or light",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "жмури́тися",
      "short_label": "грати в жмурки (хованки), бути ведучим",
      "gloss": "to play hide-and-seek / blind man's buff (to be the seeker / blindfolded player)",
      "pos": "verb",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "заві́зний",
      "short_label": "перевантажений справами, дуже зайнятий (розм.)",
      "gloss": "overloaded with work, extremely busy, preoccupied (dial./colloq.)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "завізни́й",
      "short_label": "імпортований, привезений з інших регіонів (не місцевий)",
      "gloss": "imported, brought in from outside, non-local (завізне насіння, завізні товари)",
      "pos": "adjective",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "за́городка",
      "short_label": "загін для тварин / зменшене до за́города",
      "gloss": "corral, small animal pen, paddock (diminutive of за́города)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "загоро́дка",
      "short_label": "низька перегородка, парканчик, бар'єр",
      "gloss": "low partition, screen, lightweight dividing fence/barrier",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "загу́кати",
      "short_label": "почати шуміти, лунко гудіти, видавати гук/глухий гул",
      "gloss": "to begin to rumble, roar, boom, echo (hollow sound, inanimate or bird call)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "загука́ти",
      "short_label": "голосно покликати людину / вигукнути окрик / заспівати",
      "gloss": "to call out to someone, summon aloud, begin shouting/cheering; to break into song",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "за́знаний",
      "short_label": "пережитий на власному досвіді (пасивний дієприкметник)",
      "gloss": "experienced, felt, tasted, endured (past passive participle from зазнати)",
      "pos": "participle",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "зазна́ний",
      "short_label": "зарозумілий, пихатий, який виявляє зазнайство (розм.)",
      "gloss": "arrogant, conceited, haughty, boastful (showing зазнайство)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "за́купка",
      "short_label": "куплений товар, придбана річ (заст., розм.)",
      "gloss": "purchased goods, bought merchandise, purchase items (arch./colloq.)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "заку́пка",
      "short_label": "процес придбання / закупівля товарів чи сировини",
      "gloss": "procurement, purchasing, bulk buying (action equivalent to закупівля)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "за́мішка",
      "short_label": "густа борошняна страва, каша з кукурудзяного чи житнього борошна",
      "gloss": "thick porridge, scalded cornmeal or rye mush (traditional dish)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "замі́шка",
      "short_label": "сум'яття, плутанина / перешкода, затримка у справі",
      "gloss": "confusion, turmoil, embarrassment, hitch, muddle, delay",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "за́рубка",
      "short_label": "насічка, карб на дереві або знарядді (сокирою, ножем)",
      "gloss": "notch, nick, cut, kerf, axe mark on timber (made with axe or blade)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "зару́бка",
      "short_label": "підрубування вугільного пласта врубовою машиною (гірн.)",
      "gloss": "undercutting, kerfing, cutting slot in coal seam with mining cutter",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "зати́скати",
      "short_label": "замучити стисканням, тиснути до втоми в обіймах (док. вид)",
      "gloss": "to torment by excessive squeezing/hugging, squeeze tightly to exhaustion (perf.)",
      "pos": "verb",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "затиска́ти",
      "short_label": "стискати в кулаці/лещатах, притискати міцно (недок. вид)",
      "gloss": "to squeeze, clamp, grip tight in fist or vise, compress, stifle (imperf. to затиснути)",
      "pos": "verb",
      "cefr": "A2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "за́тулка",
      "short_label": "заслінка в печі, металева чи чавунна затулка",
      "gloss": "stove shutter, oven damper, iron cover for traditional Ukrainian hearth",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
      "headword": "зату́лка",
      "short_label": "прісноводний черевоногий молюск із кришечкою (зоол.: Valvata)",
      "gloss": "valve snail, operculate snail (zoology: genus Valvata, family Valvatidae)",
      "pos": "noun",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
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
          "animacy": "animate"
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
      "headword": "значко́вий",
      "short_label": "картографічний метод умовних значків / символьний",
      "gloss": "symbol-based, badge-related; cartographic symbol method (значковий метод на картах)",
      "pos": "adjective",
      "cefr": "B2",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
      },
      "pronunciation": {
        "ipa": "[znɐt͡ʃˈkɔwɪj]"
      },
      "stress": {
        "form": "значко́вий",
        "source": "ВТС / СУМ-11",
        "url": "https://slovnyk.me/dict/vts/значковий"
      },
      "morphology": {
        "pos": "прикметник",
        "paradigm": {
          "kind": "adjective"
        }
      },
      "distinction_note": "Прикметник до «значо́к» — умовний знак або символ на карті (значковий метод у тематичних атласах). Не плутати з іменником «значкови́й» (козацький старшинський чин або носій прапора).",
      "meaning": {
        "definitions": [
          "Прикметник до значо́к; картографічний спосіб позначення об'єктів за допомогою умовних значків."
        ],
        "source": "ВТС / СУМ-11"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗНАЧКО́ВИЙ, а, е. Прикм. до значо́к 1, 2. Значковий метод [у історико-етнографічних атласах] застосовується найчастіше для передачі географічного розміщення й характеристики явищ, локалізованих у певних місцях.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в науковій літературі та СУМ-11."
      }
    },
    {
      "headword": "значкови́й",
      "short_label": "значковий товариш (козацький старшинський чин) / прапороносець",
      "gloss": "Cossack officer rank / banner bearer (значковий товариш in Hetmanate era, ensign)",
      "pos": "noun",
      "cefr": "B1",
      "heritage_status": {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True
      },
      "pronunciation": {
        "ipa": "[znɐt͡ʃkɔˈwɪj]"
      },
      "stress": {
        "form": "значкови́й",
        "source": "Грінченко (1907) / ВТС",
        "url": "https://slovnyk.me/dict/vts/значковий"
      },
      "morphology": {
        "pos": "іменник",
        "paradigm": {
          "kind": "noun",
          "gender": "masculine",
          "animacy": "animate"
        }
      },
      "distinction_note": "Історичний військовий термін часів Гетьманщини: молодший старшинський чин «значковий товариш» (Котляревський: «Значкові товариші...»), або козацький прапороносець полку. Не плутати з картографічним прикметником «значко́вий».",
      "meaning": {
        "definitions": [
          "Іст. Козацький чин значкового товариша в Гетьманщині; козак, що носив полковий значок (прапорець); церковний прапороносець."
        ],
        "source": "Грінченко (1907) / ВТС"
      },
      "soviet_colonization_context": {
        "source": "СУМ-11 (1970–1980)",
        "definition": "ЗНАЧКОВИ́Й, во́го, ч., рідко. Той, хто несе який-небудь церковний знак... // військ., заст. Звання, що надавалось у реєстровому козацькому війську з другої половини XVII століття.",
        "sovietization_risk": 0,
        "keywords": [],
        "historical_note": "Зафіксовано в СУМ-11 з ілюстраціями з М. Старицького та І. Котляревського. Автентичний історичний ужиток козацького чину «значковий товариш» засвідчено також у Словнику Бориса Грінченка (1907–1909), укладеному та виданому всупереч антиукраїнським імперським заборонам (Валуєвський циркуляр 1863 р., Емський указ 1876 р.)."
      }
    }
  ]
}
