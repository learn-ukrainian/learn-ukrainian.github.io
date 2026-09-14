"""Batch heteronyms expansion dataset for #8039 batch 2 (epic #4387).

Admitted next-tier high-frequency heteronyms (30-50 lemma batch, following the
first 40-lemma admission in curated_heteronyms_batch.py / PR #8043). Selection
method: `enrich_heteronyms.py --scan` residual (467 candidates - 40 curated =
427) filtered to lemmas (a) already present as approved/public articles in
`atlas.db`, (b) whose SUM-11 headword pair carries genuinely distinct stress
positions (not a regex/duplicate-head artifact), and (c) whose CEFR band is
A1/A2/B1 -- i.e. lemmas already taught in the core curriculum, the natural
"already in the live catalog, highest-frequency" cut. Senses verified against
the actual СУМ-11 dictionary body text (not guessed); stress positions
spot-checked against the ULIF-derived `ukrainian-word-stress` oracle via
`mcp__sources__verify_stress` for ambiguous/less-common items.

Two lemmas (наречений, підліток) attest a SUM-11 double-accent notation for
their rarer sense (indicating an attested alternate stress); the alternate
reading is used as that sense's headword so the pair remains a genuine
two-way stress contrast rather than an artifact of the accent notation.
"""

from __future__ import annotations

from typing import Any

CURATED_HETERONYMS_BATCH_2: dict[str, list[dict[str, Any]]] = {
    "дякувати": [
        {
            "headword": "дя́кувати",
            "short_label": "дякувати комусь (A1)",
            "gloss": "to thank, express gratitude, be grateful for something",
            "pos": "verb",
            "cefr": "A1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "дякува́ти",
            "short_label": "бути дяком (розм., рідко)",
            "gloss": "to serve as a church deacon (regional, rare)",
            "pos": "verb",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "кре́дит",
            "short_label": "бухгалтерський термін (спец., B2)",
            "gloss": "credit (accounting: the credit side of a ledger account, opposite of debit)",
            "pos": "noun",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "креди́т",
            "short_label": "позика, надання в борг (A2)",
            "gloss": "credit, loan (money or goods lent, to be repaid)",
            "pos": "noun",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "на́бір",
            "short_label": "у борг (діал., розм.)",
            "gloss": "on credit, without paying immediately (dialectal adverb)",
            "pos": "adverb",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "набі́р",
            "short_label": "комплект, зарахування (A2)",
            "gloss": "set, kit, collection; recruitment, enrollment (of workers/students)",
            "pos": "noun",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "обла́днання",
            "short_label": "устаткування (A1)",
            "gloss": "equipment, machinery, apparatus (collective noun)",
            "pos": "noun",
            "cefr": "A1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "обладна́ння",
            "short_label": "дія: облаштування (B2)",
            "gloss": "the act of equipping, outfitting, fitting out (a workplace, room)",
            "pos": "noun",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "послу́хати",
            "short_label": "вислухати (A1)",
            "gloss": "to listen to, hear out; to examine by listening (e.g. with a stethoscope)",
            "pos": "verb",
            "cefr": "A1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "послуха́ти",
            "short_label": "слухатися (заст.)",
            "gloss": "to obey, listen to and follow (archaic imperfective)",
            "pos": "verb",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ре́чення",
            "short_label": "граматична одиниця (A1)",
            "gloss": "sentence (grammatical unit)",
            "pos": "noun",
            "cefr": "A1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "рече́ння",
            "short_label": "короткий вислів (рідко)",
            "gloss": "a brief expression, a short set of words forming a saying (rare)",
            "pos": "noun",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ро́змір",
            "short_label": "величина, номер одягу (A1)",
            "gloss": "size, dimension; measurement (of clothing, shoes, quantities)",
            "pos": "noun",
            "cefr": "A1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "розмі́р",
            "short_label": "частка за помел (заст., діал.)",
            "gloss": "miller's toll (a portion of ground grain kept as payment)",
            "pos": "noun",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "тра́нспорт",
            "short_label": "перевезення (A1)",
            "gloss": "transport, transportation (means of conveyance; industry)",
            "pos": "noun",
            "cefr": "A1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "транспо́рт",
            "short_label": "бухгалтерський термін (C1)",
            "gloss": "carry-over (of a sum to the next page, in bookkeeping)",
            "pos": "noun",
            "cefr": "C1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ті́кати",
            "short_label": "цокати, про годинник (розм.)",
            "gloss": "to tick (of a clock or clockwork mechanism)",
            "pos": "verb",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "тіка́ти",
            "short_label": "утікати (A2)",
            "gloss": "to run away, flee, escape",
            "pos": "verb",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "за́хідний",
            "short_label": "стосується заходу-сторони світу (A2)",
            "gloss": "western, pertaining to the west (compass direction)",
            "pos": "adjective",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "захі́дний",
            "short_label": "призахідний, про сонце (діал.)",
            "gloss": "pertaining to sunset, west-facing (of the setting sun; dialectal)",
            "pos": "adjective",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "осно́вний",
            "short_label": "хімічний термін: лужний (спец., B2)",
            "gloss": "basic (chemistry: alkaline, opposite of acidic); pertaining to warp threads (weaving)",
            "pos": "adjective",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "основни́й",
            "short_label": "головний, найважливіший (A2)",
            "gloss": "main, primary, fundamental",
            "pos": "adjective",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "пере́їзд",
            "short_label": "залізничний переїзд (B1)",
            "gloss": "crossing point, level crossing (where a road crosses a railway)",
            "pos": "noun",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "переї́зд",
            "short_label": "переселення (A2)",
            "gloss": "the act of moving, relocating (to a new home, city)",
            "pos": "noun",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "по́слуга",
            "short_label": "допомога, сервіс (A2)",
            "gloss": "service, favor (a helpful act done for someone)",
            "pos": "noun",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "послу́га",
            "short_label": "служіння (заст.)",
            "gloss": "servitude, service in an old subordinate sense (archaic)",
            "pos": "noun",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "пра́вильний",
            "short_label": "вірний, безпомилковий (A2)",
            "gloss": "correct, right; regular",
            "pos": "adjective",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "прави́льний",
            "short_label": "технічний термін: вирівнювальний (спец., C1)",
            "gloss": "pertaining to leveling/straightening machinery (industrial term)",
            "pos": "adjective",
            "cefr": "C1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "про́бувати",
            "short_label": "намагатися, випробовувати (A2)",
            "gloss": "to try, attempt, test",
            "pos": "verb",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "пробува́ти",
            "short_label": "перебувати, мешкати (B2)",
            "gloss": "to be located, stay, dwell somewhere (temporarily)",
            "pos": "verb",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ра́зовий",
            "short_label": "одноразовий (A2)",
            "gloss": "one-time, single-use, disposable",
            "pos": "adjective",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "разови́й",
            "short_label": "грубого помелу (борошно, регіон.)",
            "gloss": "coarsely ground (of flour); made from such flour",
            "pos": "adjective",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ри́бний",
            "short_label": "стосується риби (A2)",
            "gloss": "fish-related, of fish (market, food, industry)",
            "pos": "adjective",
            "cefr": "A2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "рибни́й",
            "short_label": "багатий на рибу (про водойму, B2)",
            "gloss": "rich in fish (of a body of water)",
            "pos": "adjective",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ва́рення",
            "short_label": "дія: варити (рідко)",
            "gloss": "the act of cooking, boiling (deverbal noun, rare)",
            "pos": "noun",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "варе́ння",
            "short_label": "солодка страва з ягід (B1)",
            "gloss": "jam, preserves (fruit or berries cooked in syrup)",
            "pos": "noun",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ви́лазити",
            "short_label": "облазити скрізь (розм., B2)",
            "gloss": "to have crawled all over, visited everywhere (colloquial perfective)",
            "pos": "verb",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "вила́зити",
            "short_label": "вибиратися (B1)",
            "gloss": "to climb out, crawl out, get out",
            "pos": "verb",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ви́микати",
            "short_label": "виривати з корінням (діал.)",
            "gloss": "to pull out, uproot (dialectal, of plants)",
            "pos": "verb",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "вимика́ти",
            "short_label": "вимикати світло/струм (B1)",
            "gloss": "to switch off, turn off, disconnect",
            "pos": "verb",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ви́никати",
            "short_label": "обійти все (розм., B2)",
            "gloss": "to go around visiting everywhere (colloquial perfective)",
            "pos": "verb",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "виника́ти",
            "short_label": "з'являтися, зароджуватися (B1)",
            "gloss": "to arise, emerge, occur",
            "pos": "verb",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "ві́дділ",
            "short_label": "підрозділ установи (B1)",
            "gloss": "department, division, section (of an institution)",
            "pos": "noun",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "відді́л",
            "short_label": "спадкова частка майна (заст.)",
            "gloss": "one's share of inherited family property (archaic)",
            "pos": "noun",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "квітко́вий",
            "short_label": "ботанічний термін (спец., B2)",
            "gloss": "flowering (botanical: producing flowers, e.g. angiosperms)",
            "pos": "adjective",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "квіткови́й",
            "short_label": "стосується квітів (B1)",
            "gloss": "flower-related, floral (e.g. flower shop, floral scent)",
            "pos": "adjective",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "на́голос",
            "short_label": "фонетичний наголос (B1)",
            "gloss": "stress, accent (phonetic emphasis on a syllable)",
            "pos": "noun",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "наго́лос",
            "short_label": "голосно (діал.)",
            "gloss": "loudly, aloud (dialectal adverb)",
            "pos": "adverb",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "наре́чений",
            "short_label": "названий (заст.)",
            "gloss": "named, called (archaic passive participle of наректи)",
            "pos": "verb",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "нарече́ний",
            "short_label": "жених (B1)",
            "gloss": "fiancé, bridegroom",
            "pos": "noun",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "обхо́дити",
            "short_label": "обходити щось (B1)",
            "gloss": "to go around, walk around, circumvent, avoid",
            "pos": "verb",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "обходи́ти",
            "short_label": "обійти геть усе (розм., B2)",
            "gloss": "to have gone around, visited everywhere (colloquial perfective)",
            "pos": "verb",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "обхо́дитися",
            "short_label": "обходитися без чогось (B1)",
            "gloss": "to manage, get by, do without something",
            "pos": "verb",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "обходи́тися",
            "short_label": "звикнути (розм., B2)",
            "gloss": "to get used to, become accustomed to (colloquial perfective)",
            "pos": "verb",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "пе́ред",
            "short_label": "прийменник (B1)",
            "gloss": "before, in front of (preposition, governs instrumental/accusative)",
            "pos": "preposition",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "пере́д",
            "short_label": "передня частина (B2)",
            "gloss": "the front part, façade (of a garment, building, etc.)",
            "pos": "noun",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "покли́кати",
            "short_label": "гукнути когось (B1)",
            "gloss": "to call, summon (someone) once",
            "pos": "verb",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "поклика́ти",
            "short_label": "вигукувати (поет., B2)",
            "gloss": "to cry out, shout repeatedly (literary/poetic)",
            "pos": "verb",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "пі́дліток",
            "short_label": "підліток 12-16 років (B1)",
            "gloss": "teenager, adolescent (12-16 years old)",
            "pos": "noun",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "підлі́ток",
            "short_label": "пташеня-літун (поет., рідко)",
            "gloss": "fledgling (a young bird that has just learned to fly)",
            "pos": "noun",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "скла́дний",
            "short_label": "статурний, гарної будови (заст.)",
            "gloss": "well-proportioned, shapely (of a figure/body; archaic/literary)",
            "pos": "adjective",
            "cefr": None,
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "складни́й",
            "short_label": "непростий, з кількох частин (B1)",
            "gloss": "complex, composite, difficult (consisting of several parts)",
            "pos": "adjective",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "хара́ктерний",
            "short_label": "вольовий, впертий (розм., B2)",
            "gloss": "strong-willed, stubborn (of a person's character; colloquial)",
            "pos": "adjective",
            "cefr": "B2",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
            "headword": "характе́рний",
            "short_label": "типовий, властивий (B1)",
            "gloss": "characteristic, typical",
            "pos": "adjective",
            "cefr": "B1",
            "heritage_status": {
                "classification": "standard",
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "warning_severity": None,
                "calque_warning": None
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
    ]
}
